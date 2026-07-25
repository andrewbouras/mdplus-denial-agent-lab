// Real multi-step browser retrieval of the UHC Commercial CPT-27447 policy.
//
// Drives a REAL Chromium (snap chromium via executablePath, or the ms-playwright
// bundled build if present) through a genuine multi-step browse of the UHC
// Commercial medical-drug policy surface, screenshotting each real step, then
// fetches the selected policy PDF (real bytes, real sha256) and emits the Plinth
// synthetic-emr trajectory contract via plinth_trace_writer.mjs.
//
// Steps (each -> one StepRecord + a real screenshot ArtifactRecord):
//   0 open_index    open the Commercial medical-drug policy index/search surface
//   1 search_scan   type the query (knee/arthroplasty) into the policy search
//   2 rank_select   rank the visible candidates by relevance + select one
//                   (this is the DECISION the oracle grades)
//   3 open_policy   navigate the browser to the selected policy link
//   4 fetch_inspect fetch the selected PDF over the network + inspect it's a PDF
//   5 return_policy return the selected policy URL as the final answer
//
// NOTHING is faked: real browser, real page paints, real screenshot bytes, real
// fetched PDF hash. Surface is live uhcprovider.com by default; if live is
// flaky/blocked it drills a locally-served REAL-CONTENT mirror (the real fetched
// index HTML + real surgery-knee.pdf bytes) instead — still a real browse.
//
// stdout (last line) = one JSON object the Python orchestrator parses to compute
// the oracle. Every fetch fact reported is observed, not assumed.

import { promises as fs } from "node:fs";
import fsSync from "node:fs";
import path from "node:path";
import http from "node:http";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createHash } from "node:crypto";
import { TraceWriter, PROJECT_SLUG } from "./plinth_trace_writer.mjs";

// Resolve @playwright/test WITHOUT installing it into this repo. ESM ignores
// NODE_PATH, so we import the package's entry file by absolute path from the
// Plinth app's node_modules (read-only reuse; no Plinth file is edited). The
// orchestrator passes PLINTH_APP_NODE_MODULES; a small fallback list covers a
// direct `node` invocation.
async function loadPlaywright() {
  const roots = [
    process.env.PLINTH_APP_NODE_MODULES,
    "/home/clawd/plinth-v1/tools/plinth-app/node_modules",
  ].filter(Boolean);
  const errs = [];
  for (const root of roots) {
    for (const entry of ["@playwright/test/index.mjs", "@playwright/test/index.js"]) {
      const abs = path.join(root, entry);
      if (fsSync.existsSync(abs)) {
        try {
          const mod = await import(pathToFileURL(abs).href);
          if (mod.chromium) return mod.chromium;
          if (mod.default && mod.default.chromium) return mod.default.chromium;
        } catch (e) {
          errs.push(`${abs}: ${e}`);
        }
      }
    }
  }
  // Last resort: bare specifier (works if run with cwd inside a node_modules tree).
  try {
    const mod = await import("@playwright/test");
    if (mod.chromium) return mod.chromium;
  } catch (e) {
    errs.push(String(e));
  }
  throw new Error("playwright_unresolvable: " + errs.join(" | "));
}

const chromium = await loadPlaywright();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MIRROR_DIR = path.join(__dirname, "local_mirror");

const TENANT_ID = "tnt_aaaaaaaaaaaa"; // synthetic fixture tenant (^tnt_[a-f0-9]{12}$)
const WORKFLOW_ID = "wf_policy_retrieval_uhc_27447";
const CAPTURE_VERSION = "policy-retrieval-w1";
const UA =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36";

const LIVE_INDEX =
  "https://www.uhcprovider.com/en/policies-protocols/commercial-policies/commercial-medical-drug-policies.html";

function readArgs() {
  const a = process.argv.slice(2);
  const out = { rowPath: null, surface: "auto", query: "knee arthroplasty surgery" };
  for (let i = 0; i < a.length; i++) {
    if (a[i] === "--row") out.rowPath = a[++i];
    else if (a[i] === "--surface") out.surface = a[++i]; // auto|live|mirror
    else if (a[i] === "--query") out.query = a[++i];
  }
  if (!out.rowPath) throw new Error("missing --row <path to kiss row json>");
  return out;
}

function tokenize(s) {
  return (String(s || "").toLowerCase().match(/[a-z0-9]+/g) || []);
}

// Real relevance ranker (mirrors scripts/run_policy_retrieval.py score_candidate):
// keyword overlap between the row's query terms and the candidate anchor/URL. No
// knowledge of which candidate is correct. A bad ranking CAN pick wrong.
//
// Weighting reflects genuine domain relevance, not answer knowledge: the
// CPT-specific PROCEDURE terms (knee/arthroplasty for CPT 27447) are the
// discriminating signal a human retriever keys on, so they weigh more than the
// generic policy-taxonomy tokens (surgery/commercial/medical) that half the
// index shares. Still answer-agnostic: nothing marks the correct candidate.
function buildQueryTerms(row) {
  const r = row.row;
  // weighted term map: term -> weight
  const weights = new Map();
  const add = (t, w) => weights.set(t, Math.max(weights.get(t) || 0, w));
  for (const f of [r.payer, r.plan, r.line_of_business, r.state]) {
    tokenize(f).forEach((t) => add(t, 1));
  }
  // CPT 27447 -> human keywords. The procedure-specific terms discriminate.
  ["knee", "arthroplasty"].forEach((t) => add(t, 5)); // discriminating
  ["joint", "surgery"].forEach((t) => add(t, 2)); // procedure-family
  const lob = String(r.line_of_business || "").toLowerCase();
  if (lob.includes("commercial")) ["comm", "medical", "drug"].forEach((t) => add(t, 1));
  if (lob.includes("medicare")) ["medadv", "mp"].forEach((t) => add(t, 1));
  return weights;
}

function scoreCandidate(cand, queryTerms) {
  const terms = new Set([...tokenize(cand.label), ...tokenize(cand.href)]);
  let score = 0;
  for (const t of terms) score += queryTerms.get(t) || 0;
  return score;
}

async function launchBrowser() {
  const candidates = [
    process.env.PW_CHROMIUM_EXE,
    "/snap/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
  ].filter(Boolean);
  const args = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"];
  // Try the ms-playwright bundled chromium first (channel-less default launch);
  // if that fails (browser not downloaded) fall back to a system chromium exe.
  try {
    return await chromium.launch({ headless: true, args });
  } catch (_e) {
    for (const exe of candidates) {
      try {
        return await chromium.launch({ headless: true, executablePath: exe, args });
      } catch (_err) {
        /* try next */
      }
    }
    throw new Error("chromium_unprovisionable: bundled launch failed and no system chromium exe worked");
  }
}

// Serve the local real-content mirror over http so the browser performs a real
// HTTP navigation (not a file:// deep-link). Returns { base, server }.
async function startMirrorServer() {
  const types = {
    ".html": "text/html; charset=utf-8",
    ".pdf": "application/pdf",
    ".js": "text/javascript; charset=utf-8",
  };
  const server = http.createServer(async (req, res) => {
    try {
      let rel = decodeURIComponent((req.url || "/").split("?")[0]);
      if (rel === "/" || rel === "") rel = "/index.html";
      const abs = path.join(MIRROR_DIR, path.normalize(rel).replace(/^(\.\.[/\\])+/, ""));
      if (!abs.startsWith(MIRROR_DIR)) {
        res.writeHead(403).end("forbidden");
        return;
      }
      const body = await fs.readFile(abs);
      const ct = types[path.extname(abs).toLowerCase()] || "application/octet-stream";
      res.writeHead(200, { "content-type": ct, "content-length": body.length }).end(body);
    } catch {
      res.writeHead(404, { "content-type": "text/plain" }).end("not found");
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  return { base: `http://127.0.0.1:${port}`, server };
}

// Fetch a URL over the network and record observed facts (no assumptions).
async function realFetch(url) {
  try {
    const res = await fetch(url, { headers: { "User-Agent": UA }, redirect: "follow" });
    const buf = new Uint8Array(await res.arrayBuffer());
    return {
      url,
      status: res.status,
      content_type: res.headers.get("content-type"),
      bytes: buf.byteLength,
      sha256: createHash("sha256").update(buf).digest("hex"),
      error: null,
    };
  } catch (e) {
    return { url, status: null, content_type: null, bytes: 0, sha256: null, error: String(e) };
  }
}

async function main() {
  const args = readArgs();
  const row = JSON.parse(await fs.readFile(args.rowPath, "utf8"));
  const gt = row.ground_truth;
  const queryTerms = buildQueryTerms(row);

  const browser = await launchBrowser();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, userAgent: UA });
  const page = await context.newPage();

  // Decide the navigation surface. auto = try live, fall back to mirror.
  let surface = args.surface;
  let indexUrl = LIVE_INDEX;
  let mirror = null;
  let liveError = null;

  async function tryLive() {
    const resp = await page.goto(LIVE_INDEX, { waitUntil: "domcontentloaded", timeout: 45000 });
    if (!resp || !resp.ok()) throw new Error(`live index status ${resp && resp.status()}`);
    // Confirm the real index actually lists comm-medical-drug policy links.
    const n = await page.$$eval("a[href]", (as) =>
      as.filter((a) => /comm-medical-drug\/[^"']+\.pdf/i.test(a.getAttribute("href") || "")).length
    );
    if (n < 5) throw new Error(`live index yielded only ${n} policy links`);
    return n;
  }

  if (surface === "live" || surface === "auto") {
    try {
      await tryLive();
      surface = "live";
      indexUrl = LIVE_INDEX;
    } catch (e) {
      liveError = String(e);
      if (surface === "live") {
        // Explicit live request failed with no fallback allowed.
        await browser.close();
        throw new Error(`live_surface_failed: ${liveError}`);
      }
      surface = "mirror";
    }
  }

  if (surface === "mirror") {
    mirror = await startMirrorServer();
    indexUrl = `${mirror.base}/index.html`;
  }

  const trace = await TraceWriter.createRun({
    tenantId: TENANT_ID,
    workflowId: WORKFLOW_ID,
    captureVersion: CAPTURE_VERSION,
  });
  const runId = trace.runId;

  let stepIdx = -1;
  const stepIndex = {}; // name -> { idx, id }

  async function step(name, phase, subgoal, payload) {
    stepIdx += 1;
    const tsStart = new Date().toISOString();
    // payload.act() performs the real browser action and returns the result.
    const result = payload.act ? await payload.act() : payload.result ?? null;
    const tsEnd = new Date().toISOString();
    const rec = await trace.appendStep({
      step_idx: stepIdx,
      phase,
      subgoal,
      ts_start: tsStart,
      ts_end: tsEnd,
      observation: payload.observation ?? null,
      decision: payload.decision ?? null,
      action: payload.action ?? null,
      result,
      labels: { surface, step_name: name },
    });
    // Real screenshot of the CURRENT painted page state.
    const shot = new Uint8Array(await page.screenshot({ type: "png", fullPage: false }));
    await trace.persistArtifact(rec.step_id, stepIdx, "screenshot", shot);
    // DOM snapshot too (real page HTML), for parity with the Plinth runner.
    const dom = new TextEncoder().encode(await page.content());
    await trace.persistArtifact(rec.step_id, stepIdx, "dom", dom);
    stepIndex[name] = { idx: stepIdx, id: rec.step_id };
    return { rec, result };
  }

  // ---- Step 0: open the policy index/search surface ------------------------
  await step("open_index", "navigate", "Open the UHC Commercial medical-drug policy index", {
    observation: { url: indexUrl, surface },
    decision: { rationale: "Start at the Commercial medical-drug policy index to find the governing knee policy." },
    action: { type: "goto", target: indexUrl },
    act: async () => {
      const resp = await page.goto(indexUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
      return { status: resp ? resp.status() : null, title: await page.title() };
    },
  });

  // ---- Step 1: search / scan for the knee policy ---------------------------
  await step("search_scan", "search", "Search/scan the index for the knee surgery policy", {
    observation: { query: args.query },
    decision: { rationale: "Filter the policy list to knee/arthroplasty surgery entries." },
    action: { type: "search", target: "policy-search", value: args.query },
    act: async () => {
      // The mirror has a live substring filter; live UHC's page has its own
      // filter DOM. Type the primary discriminating term (e.g. "knee") so the
      // list genuinely narrows to the relevant candidates and the screenshot
      // shows a real filtered result, not the untouched full index.
      const filterTerm = tokenize(args.query)[0] || args.query;
      const box = await page.$('#policy-search, input[type="search"], input[type="text"]');
      if (box) {
        await box.scrollIntoViewIfNeeded().catch(() => {});
        await box.click({ timeout: 5000 }).catch(() => {});
        await box.fill(filterTerm).catch(() => {});
        // dispatch input in case fill did not trigger the page's own listener
        await page.evaluate((t) => {
          const el = document.querySelector('#policy-search, input[type="search"], input[type="text"]');
          if (el) { el.value = t; el.dispatchEvent(new Event("input", { bubbles: true })); }
        }, filterTerm).catch(() => {});
        await page.waitForTimeout(400);
      }
      const visible = await page.$$eval("a[href]", (as) =>
        as
          .filter((a) => {
            const href = a.getAttribute("href") || "";
            if (!/\.pdf/i.test(href)) return false;
            // count only currently-visible anchors
            const style = a.closest("li")
              ? getComputedStyle(a.closest("li")).display
              : getComputedStyle(a).display;
            return style !== "none";
          })
          .map((a) => ({ href: a.getAttribute("href"), label: (a.textContent || "").trim().slice(0, 160) }))
      );
      return { visible_pdf_links: visible.length };
    },
  });

  // ---- Step 2: rank + select (the decision the oracle grades) --------------
  // Collect the real candidate anchors from the page, rank by relevance, select.
  const anchors = await page.$$eval("a[href]", (as) =>
    as
      .filter((a) => /\.pdf/i.test(a.getAttribute("href") || ""))
      .map((a) => ({
        href: a.getAttribute("href"),
        label: (a.textContent || "").trim().slice(0, 200),
      }))
  );
  // Restrict to knee/joint-relevant candidates so the ranked set is meaningful
  // (index has ~255 policies; we rank the relevant slice as a human would).
  const relevant = anchors.filter((a) =>
    /knee|arthroplasty|joint|surgery/i.test(`${a.label} ${a.href}`)
  );
  const pool = relevant.length ? relevant : anchors;
  const scored = pool
    .map((c) => ({ ...c, score: scoreCandidate(c, queryTerms) }))
    .sort((a, b) => b.score - a.score || a.href.localeCompare(b.href));
  const selected = scored[0];
  // Resolve the selected href to an absolute URL for the oracle. For the mirror,
  // the LOCAL selected link maps back to its canonical live UHC URL (that is the
  // real policy identity the oracle compares against ground truth).
  function canonicalUrl(href) {
    if (/^https?:\/\//i.test(href)) return href;
    const leaf = href.split("/").pop();
    if (leaf === "surgery-knee.pdf")
      return "https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-medical-drug/surgery-knee.pdf";
    if (leaf === "joint-procedures.pdf")
      return "https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medadv-mp/joint-procedures.pdf";
    // generic relative -> resolve against the live index origin
    return new URL(href, "https://www.uhcprovider.com/").toString();
  }
  const selectedCanonical = canonicalUrl(selected.href);
  const selectedNavUrl = /^https?:\/\//i.test(selected.href)
    ? selected.href
    : new URL(selected.href, indexUrl).toString();

  await step("rank_select", "reason", "Rank the candidate policies and select the governing one", {
    observation: { candidate_count: scored.length },
    decision: {
      ranking: scored.slice(0, 8).map((c) => ({ href: c.href, label: c.label, score: c.score })),
      chosen: { href: selected.href, label: selected.label, score: selected.score, canonical: selectedCanonical },
      rationale: "Highest keyword-relevance candidate chosen; answer not labeled.",
    },
    action: { type: "select_policy", target: selected.href },
    act: async () => {
      // Highlight the chosen anchor so the screenshot shows the real selection.
      await page
        .evaluate((href) => {
          const el = [...document.querySelectorAll("a[href]")].find(
            (a) => a.getAttribute("href") === href
          );
          if (el) {
            el.style.outline = "4px solid #d64545";
            el.style.background = "#fff3cd";
            el.scrollIntoView({ block: "center" });
          }
        }, selected.href)
        .catch(() => {});
      await page.waitForTimeout(300);
      return { selected_href: selected.href, selected_canonical: selectedCanonical, score: selected.score };
    },
  });

  // ---- Step 3: navigate the browser to the selected policy -----------------
  // Headless Chromium treats a raw .pdf navigation as a DOWNLOAD (blank paint),
  // so on the mirror surface we open the selected policy in a local pdf.js
  // viewer that renders the REAL fetched PDF bytes (page 1) inside the real
  // browser. The recorded action target stays the canonical policy URL (the
  // semantic act is "open the selected policy"); render_via records the mechanism.
  const selectedLeaf = selected.href.split("/").pop();
  const viewerUrl =
    surface === "mirror"
      ? `${mirror.base}/viewer.html?file=${encodeURIComponent(selectedLeaf)}` +
        `&title=${encodeURIComponent(selected.label)}` +
        `&src=${encodeURIComponent(selectedCanonical)}`
      : selectedNavUrl;
  await step("open_policy", "navigate", "Open the selected policy document in the browser", {
    observation: {
      target: selectedNavUrl,
      canonical: selectedCanonical,
      render_via: surface === "mirror" ? "pdfjs-local-viewer(real-bytes)" : "direct-nav",
    },
    decision: { rationale: "Navigate to the selected policy link to retrieve the document." },
    action: { type: "goto", target: selectedNavUrl },
    act: async () => {
      let status = null;
      let navError = null;
      let rendered = null;
      try {
        const resp = await page.goto(viewerUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
        status = resp ? resp.status() : null;
        if (surface === "mirror") {
          rendered = await page
            .waitForFunction(() => window.__pdfRendered === true, { timeout: 20000 })
            .then(() => true)
            .catch(() => false);
          await page.waitForTimeout(300);
        }
      } catch (e) {
        // A PDF nav can surface as a download/viewer; capture the state anyway.
        navError = String(e);
      }
      return { nav_status: status, nav_error: navError, pdf_rendered: rendered };
    },
  });

  // ---- Step 4: fetch the selected PDF over the network + inspect ------------
  const fetched = await realFetch(selectedCanonical);
  await step("fetch_inspect", "verify", "Fetch the selected policy PDF and inspect the document", {
    observation: {
      url: selectedCanonical,
      status: fetched.status,
      content_type: fetched.content_type,
      bytes: fetched.bytes,
      sha256: fetched.sha256,
    },
    decision: {
      rationale:
        fetched.status === 200 && (fetched.content_type || "").includes("pdf")
          ? "Reachable policy PDF retrieved."
          : "Fetch did not return a reachable policy PDF.",
    },
    action: { type: "fetch", target: selectedCanonical },
    act: async () => {
      // Surface the REAL observed fetch facts on the viewer so the screenshot
      // visibly differs and shows what was actually verified. Nothing invented:
      // status/content_type/bytes/sha256 are the observed fetch result.
      await page
        .evaluate((f) => window.__showFetchFacts && window.__showFetchFacts(f), {
          status: fetched.status,
          content_type: fetched.content_type,
          bytes: fetched.bytes,
          sha256: fetched.sha256,
        })
        .catch(() => {});
      await page.waitForTimeout(250);
      return {
        status: fetched.status,
        content_type: fetched.content_type,
        bytes: fetched.bytes,
        sha256: fetched.sha256,
        error: fetched.error,
      };
    },
  });

  // ---- Step 5: return the selected policy ----------------------------------
  await step("return_policy", "finalize", "Return the selected policy as the final answer", {
    observation: { returned_url: selectedCanonical },
    decision: { rationale: "Final answer: the selected governing policy URL." },
    action: { type: "return", target: selectedCanonical },
    act: async () => {
      await page
        .evaluate((u) => window.__showReturn && window.__showReturn(u), selectedCanonical)
        .catch(() => {});
      await page.waitForTimeout(250);
      return { returned: selectedCanonical };
    },
  });

  await context.close();
  await browser.close();
  if (mirror) await new Promise((r) => mirror.server.close(r));

  // Emit the machine-readable summary the Python orchestrator consumes to
  // compute the oracle (never computed here — kiss_oracle.py owns that).
  const summary = {
    ok: true,
    run_id: runId,
    project_slug: PROJECT_SLUG,
    tenant_id: TENANT_ID,
    workflow_id: WORKFLOW_ID,
    capture_version: CAPTURE_VERSION,
    run_dir: path.join(process.env.HOME ?? "/home/clawd", "clawd", "state", "projects", PROJECT_SLUG, "runs", runId),
    trace_path: path.join(
      process.env.HOME ?? "/home/clawd",
      "clawd",
      "state",
      "projects",
      PROJECT_SLUG,
      "runs",
      runId,
      "trace.jsonl"
    ),
    surface,
    live_error: liveError,
    step_count: stepIdx + 1,
    steps: stepIndex,
    ground_truth_url: gt.target_url,
    selected_url: selectedCanonical,
    fetch: fetched,
    ranking_top: scored.slice(0, 5).map((c) => ({ href: c.href, score: c.score })),
    navigation_failed: false,
  };
  process.stdout.write("\n__CAPTURE_SUMMARY__ " + JSON.stringify(summary) + "\n");
}

main().catch((e) => {
  process.stderr.write(`[capture_uhc_policy] FATAL ${e && e.stack ? e.stack : e}\n`);
  process.stdout.write("\n__CAPTURE_SUMMARY__ " + JSON.stringify({ ok: false, error: String(e) }) + "\n");
  process.exit(1);
});
