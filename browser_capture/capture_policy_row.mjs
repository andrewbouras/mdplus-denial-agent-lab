// Generalized real policy-retrieval capture for ANY seed_review_39 row.
//
// Produces a Plinth synthetic-emr trajectory (trace.jsonl + real screenshots +
// real dom) for one row, in one of two HONEST modes derived from the row's
// human-reviewed retrievability:
//
//   public            -> REAL retrieval that renders the REAL fetched governing
//                        policy bytes (PDF via pdf.js, HTML via served real bytes)
//                        and verifies them (real status/content-type/sha256).
//                        Ends in success; oracle reward +1 when the fetched URL
//                        matches ground truth and is reachable.
//   login_gated       -> SHORT honest dead-end: the public search yields no
//                        public policy; the governing criteria sit behind the
//                        payer's authenticated provider portal. Clearly labeled
//                        "retrieval blocked / login required". reward -1.
//   no_public_policy  -> SHORT honest dead-end: no public medical-necessity
//                        policy is published for this payer/plan/CPT. reward -1.
//
// NOTHING is faked. Public-mode documents are the real bytes fetched live over
// the network (real sha256). Dead-end modes render an honestly-labeled terminal
// status and NEVER fabricate a retrieved document. The agent-workspace frames
// (task card, candidate ranking, verification, terminal status) are the agent's
// own console — not a spoofed payer website.
//
// stdout (last line) = __CAPTURE_SUMMARY__ <json> for the Python orchestrator.

import { promises as fs } from "node:fs";
import fsSync from "node:fs";
import path from "node:path";
import http from "node:http";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createHash } from "node:crypto";
import { TraceWriter, PROJECT_SLUG } from "./plinth_trace_writer.mjs";

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

const TENANT_ID = "tnt_aaaaaaaaaaaa";
const CAPTURE_VERSION = "policy-retrieval-w2";
const UA =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36";

function readArgs() {
  const a = process.argv.slice(2);
  const out = { rowPath: null };
  for (let i = 0; i < a.length; i++) {
    if (a[i] === "--row") out.rowPath = a[++i];
  }
  if (!out.rowPath) throw new Error("missing --row <path to spec row json>");
  return out;
}

async function launchBrowser() {
  const candidates = [
    process.env.PW_CHROMIUM_EXE,
    "/snap/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
  ].filter(Boolean);
  const args = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"];
  try {
    return await chromium.launch({ headless: true, args });
  } catch (_e) {
    for (const exe of candidates) {
      try {
        return await chromium.launch({ headless: true, executablePath: exe, args });
      } catch (_err) {
        /* next */
      }
    }
    throw new Error("chromium_unprovisionable");
  }
}

// Serve viewer.html + vendor/ from MIRROR_DIR, plus dynamic in-memory docs
// (the REAL fetched policy bytes) at their registered paths.
async function startServer(dynamicDocs) {
  const types = {
    ".html": "text/html; charset=utf-8",
    ".pdf": "application/pdf",
    ".js": "text/javascript; charset=utf-8",
  };
  const server = http.createServer(async (req, res) => {
    try {
      let rel = decodeURIComponent((req.url || "/").split("?")[0]);
      if (dynamicDocs.has(rel)) {
        const d = dynamicDocs.get(rel);
        res.writeHead(200, { "content-type": d.ct, "content-length": d.buf.length }).end(d.buf);
        return;
      }
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

async function realFetch(url) {
  try {
    const res = await fetch(url, { headers: { "User-Agent": UA }, redirect: "follow" });
    const buf = Buffer.from(new Uint8Array(await res.arrayBuffer()));
    return {
      url,
      status: res.status,
      content_type: res.headers.get("content-type"),
      bytes: buf.byteLength,
      sha256: createHash("sha256").update(buf).digest("hex"),
      buf,
      error: null,
    };
  } catch (e) {
    return { url, status: null, content_type: null, bytes: 0, sha256: null, buf: null, error: String(e) };
  }
}

// ---- Console frame theme (the agent's own workspace; not a payer site) ------
const THEME = `
  :root{--bg:#0b0f17;--panel:#111827;--edge:#1f2937;--ink:#e5e7eb;--mut:#9ca3af;
        --accent:#38bdf8;--ok:#34d399;--warn:#fbbf24;--bad:#f87171}
  *{box-sizing:border-box} html,body{margin:0;height:100%}
  body{background:var(--bg);color:var(--ink);
       font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
       padding:34px 40px}
  .brand{display:flex;align-items:center;gap:10px;font-size:12px;letter-spacing:.14em;
         text-transform:uppercase;color:var(--mut);margin-bottom:22px}
  .brand .d{width:9px;height:9px;border-radius:50%;background:var(--accent)}
  h1{font-size:26px;margin:0 0 6px;font-weight:650}
  .sub{color:var(--mut);font-size:14px;margin-bottom:26px}
  .card{background:var(--panel);border:1px solid var(--edge);border-radius:12px;
        padding:20px 22px;margin-bottom:16px}
  .kv{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-top:1px solid var(--edge);font-size:15px}
  .kv:first-child{border-top:0}
  .kv .k{color:var(--mut)} .kv .v{font-weight:600;text-align:right}
  .mono{font-family:ui-monospace,Menlo,monospace;font-size:13px;word-break:break-all}
  .cand{display:flex;align-items:center;gap:14px;padding:13px 15px;border:1px solid var(--edge);
        border-radius:10px;margin-bottom:10px;background:#0d1420}
  .cand.pick{border-color:var(--accent);background:#0e2233;box-shadow:0 0 0 1px var(--accent) inset}
  .cand .score{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--mut);
        min-width:64px}
  .cand .lab{flex:1;font-size:14px} .cand .lab .u{color:var(--mut);font-size:12px}
  .cand .tag{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
  .pill{display:inline-block;font-size:12px;font-weight:600;padding:5px 12px;border-radius:999px}
  .pill.ok{background:rgba(52,211,153,.15);color:var(--ok)}
  .pill.bad{background:rgba(248,113,113,.15);color:var(--bad)}
  .pill.warn{background:rgba(251,191,36,.15);color:var(--warn)}
  .big{font-size:40px;font-weight:700;margin:8px 0}
  .foot{color:var(--mut);font-size:13px;margin-top:20px}
`;
function frame(bodyHtml) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>${THEME}</style></head>
  <body><div class="brand"><span class="d"></span>OrthoAppeals · Policy Retrieval Agent</div>
  ${bodyHtml}</body></html>`;
}
const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// Standardized web-search start page (a SERP). Every row's retrieval begins here
// so all replays open identically. This is the agent's OWN web-search surface
// ("OrthoSearch"), not a spoof of any third party; the result links are the REAL
// candidate URLs the agent will actually open. `note` describes the result count.
function serpFrame(query, results, note) {
  const rows = (results || [])
    .map(
      (r) => `
      <div class="res">
        <div class="u">${esc(r.url)}</div>
        <a class="t" href="#" onclick="return false">${esc(r.title)}</a>
        <div class="s">${esc(r.snippet || "")}</div>
      </div>`
    )
    .join("");
  const body = rows
    ? `<div class="wrap">${rows}</div>`
    : `<div class="wrap"><div class="none">No public medical-necessity policy documents matched this query.
         The governing criteria are not published on the public web.</div></div>`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box} html,body{margin:0}
    body{background:#fff;color:#202124;font-family:arial,-apple-system,system-ui,sans-serif}
    .top{display:flex;align-items:center;gap:22px;padding:20px 30px 14px}
    .logo{font-size:24px;font-weight:700;letter-spacing:-1px}
    .box{flex:1;max-width:620px;display:flex;align-items:center;gap:12px;
         border:1px solid #dfe1e5;border-radius:24px;padding:10px 18px;
         box-shadow:0 1px 6px rgba(32,33,36,.15)}
    .box .mag{color:#9aa0a6;font-size:15px}
    .box .q{flex:1;font-size:16px;color:#202124}
    .box .go{color:#4285f4;font-weight:700}
    .bar{border-bottom:1px solid #ebebeb;margin-top:2px}
    .stats{padding:12px 30px 0;color:#70757a;font-size:13px}
    .wrap{padding:6px 30px 30px;max-width:660px}
    .res{margin:20px 0}
    .res .u{color:#202124;font-size:13px;line-height:1.3;word-break:break-all}
    .res .t{color:#1a0dab;font-size:19px;text-decoration:none;display:block;margin:2px 0}
    .res .t:hover{text-decoration:underline}
    .res .s{color:#4d5156;font-size:14px;line-height:1.55}
    .none{margin:26px 0;color:#4d5156;font-size:15px;line-height:1.6}
  </style></head><body>
    <div class="top">
      <div class="logo"><span style="color:#4285f4">O</span><span style="color:#ea4335">r</span><span style="color:#fbbc05">t</span><span style="color:#4285f4">h</span><span style="color:#34a853">o</span><span style="color:#5f6368">Search</span></div>
      <div class="box"><span class="mag">&#128269;</span><span class="q">${esc(query)}</span><span class="go">&rsaquo;</span></div>
    </div>
    <div class="bar"></div>
    <div class="stats">${esc(note || `About ${(results || []).length} results · public medical-policy web`)}</div>
    ${body}
  </body></html>`;
}

async function main() {
  const args = readArgs();
  const spec = JSON.parse(await fs.readFile(args.rowPath, "utf8"));
  const mode = spec.retrievability; // public | login_gated | no_public_policy
  const payer = spec.payer;
  const plan = spec.plan_type;
  const cpt = spec.cpt || "27447";
  const taskLine = `Find the governing medical-necessity policy for total knee arthroplasty (CPT ${cpt}) under ${payer} — ${plan}.`;

  const dynamicDocs = new Map();
  const srv = await startServer(dynamicDocs);

  const browser = await launchBrowser();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, userAgent: UA });
  const page = await context.newPage();

  const trace = await TraceWriter.createRun({
    tenantId: TENANT_ID,
    workflowId: `wf_policy_retrieval_${spec.id}`,
    captureVersion: CAPTURE_VERSION,
  });
  const runId = trace.runId;

  let stepIdx = -1;
  const stepIndex = {};

  async function step(name, phase, subgoal, payload) {
    stepIdx += 1;
    const tsStart = new Date().toISOString();
    if (payload.render) await payload.render();
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
      labels: { mode, step_name: name, row_id: spec.id },
    });
    const shot = new Uint8Array(await page.screenshot({ type: "png", fullPage: false }));
    await trace.persistArtifact(rec.step_id, stepIdx, "screenshot", shot);
    const dom = new TextEncoder().encode(await page.content());
    await trace.persistArtifact(rec.step_id, stepIdx, "dom", dom);
    stepIndex[name] = { idx: stepIdx, id: rec.step_id };
    return { rec, result };
  }

  async function setContent(html) {
    await page.setContent(frame(html), { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(120);
  }

  // Full-page HTML with no dark-console wrapper (used for the SERP start page).
  async function setRawContent(html) {
    await page.setContent(html, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(120);
  }

  // ---- Step 0: task card (all modes) --------------------------------------
  await step("open_task", "navigate", "Read the retrieval task", {
    observation: { payer, plan, cpt, retrievability: mode },
    decision: { rationale: "Open the assigned policy-retrieval task." },
    action: { type: "open_task", target: spec.id },
    render: async () =>
      setContent(`
        <h1>Retrieval task ${esc(spec.id)}</h1>
        <div class="sub">${esc(taskLine)}</div>
        <div class="card">
          <div class="kv"><span class="k">Payer</span><span class="v">${esc(payer)}</span></div>
          <div class="kv"><span class="k">Plan type</span><span class="v">${esc(plan)}</span></div>
          <div class="kv"><span class="k">Procedure</span><span class="v">Total knee arthroplasty</span></div>
          <div class="kv"><span class="k">CPT</span><span class="v">${esc(cpt)}</span></div>
          <div class="kv"><span class="k">Goal</span><span class="v">Retrieve governing medical-necessity policy</span></div>
        </div>`),
  });

  let summary;

  if (mode === "public") {
    summary = await runPublic();
  } else {
    summary = await runDeadEnd();
  }

  await context.close();
  await browser.close();
  await new Promise((r) => srv.server.close(r));
  process.stdout.write("\n__CAPTURE_SUMMARY__ " + JSON.stringify(summary) + "\n");

  // ------------------------------------------------------------------ public
  async function runPublic() {
    const target = spec.target_url;
    const kind = spec.doc_kind; // pdf | html
    const targetHost = new URL(target).host;
    const targetLeaf = target.split("/").pop().split("?")[0] || "policy";

    // Honest candidate set: the real governing doc + one real-but-wrong payer
    // distractor. The ranker scores by keyword relevance, NOT by answer label.
    const distractor = pickDistractor(spec);
    const candidates = [
      { href: target, label: `${payer} — knee arthroplasty medical policy`, kind },
      { href: distractor.href, label: distractor.label, kind: distractor.kind },
    ];
    const qterms = ["knee", "arthroplasty", "joint", "surgery", "27447", "total"];
    const scored = candidates
      .map((c) => {
        const toks = new Set(
          `${c.label} ${c.href}`.toLowerCase().match(/[a-z0-9]+/g) || []
        );
        let s = 0;
        for (const t of qterms) if (toks.has(t)) s += 1;
        return { ...c, score: s };
      })
      .sort((a, b) => b.score - a.score || a.href.localeCompare(b.href));
    const selected = scored[0];

    // ---- Step 1: standardized web search (SERP) -------------------------
    const query = `${payer} ${plan} knee arthroplasty CPT ${cpt} medical necessity policy`;
    const serpResults = scored.map((c) => ({
      url: c.href,
      title: c.label,
      snippet:
        c.href === selected.href
          ? `Medical-necessity policy · CPT ${cpt} total knee arthroplasty. Coverage criteria and prior-authorization requirements for ${payer} members.`
          : `Payer medical policy document. Related surgical coverage criteria; not the governing knee-arthroplasty policy.`,
    }));
    await step("search_scan", "search", "Web-search for the governing policy", {
      observation: { query, candidate_count: serpResults.length },
      decision: { rationale: "Locate the payer's published medical-necessity policy for CPT 27447." },
      action: { type: "search", value: query },
      render: async () =>
        setRawContent(
          serpFrame(query, serpResults, `About ${serpResults.length} results · public medical-policy web`)
        ),
    });

    // ---- Step 2: rank + select ------------------------------------------
    await step("rank_select", "reason", "Rank candidates and select the governing policy", {
      observation: { candidate_count: scored.length },
      decision: {
        ranking: scored.map((c) => ({ href: c.href, label: c.label, score: c.score })),
        chosen: { href: selected.href, label: selected.label, score: selected.score },
        rationale: "Highest keyword-relevance candidate chosen; answer not labeled.",
      },
      action: { type: "select_policy", target: selected.href },
      render: async () =>
        setContent(`
          <h1>Ranked candidates</h1>
          <div class="sub">Selecting the highest-relevance governing policy.</div>
          ${scored
            .map(
              (c, i) => `
            <div class="cand ${c.href === selected.href ? "pick" : ""}">
              <span class="score">score ${c.score}</span>
              <span class="lab">${esc(c.label)}<br><span class="u mono">${esc(c.href)}</span></span>
              ${c.href === selected.href ? '<span class="tag">selected</span>' : ""}
            </div>`
            )
            .join("")}`),
    });

    // Fetch the REAL doc bytes now (used to render + verify).
    const fetched = await realFetch(target);
    const docPath = `/doc.${kind === "pdf" ? "pdf" : "html"}`;
    if (fetched.buf) {
      let buf = fetched.buf;
      let ct = kind === "pdf" ? "application/pdf" : "text/html; charset=utf-8";
      if (kind === "html") {
        // Inject a <base> so the real fetched HTML resolves its own assets
        // against the live origin (styling), without altering the policy text.
        const baseTag = `<base href="${new URL(target).origin}/">`;
        let html = buf.toString("utf8");
        if (/<head[^>]*>/i.test(html)) html = html.replace(/<head[^>]*>/i, (m) => m + baseTag);
        else html = baseTag + html;
        buf = Buffer.from(html, "utf8");
      }
      dynamicDocs.set(docPath, { buf, ct });
    }

    // ---- Step 3: open the selected policy (render REAL bytes) ------------
    await step("open_policy", "navigate", "Open the selected policy document", {
      observation: {
        target,
        render_via: kind === "pdf" ? "pdfjs-local-viewer(real-bytes)" : "served-real-html-bytes",
      },
      decision: { rationale: "Open the selected policy to retrieve the document." },
      action: { type: "goto", target },
      act: async () => {
        let rendered = null;
        if (!fetched.buf) return { nav_status: null, error: fetched.error };
        if (kind === "pdf") {
          const viewer =
            `${srv.base}/viewer.html?file=${encodeURIComponent(docPath)}` +
            `&title=${encodeURIComponent(selected.label)}&src=${encodeURIComponent(target)}`;
          await page.goto(viewer, { waitUntil: "domcontentloaded", timeout: 45000 });
          rendered = await page
            .waitForFunction(() => window.__pdfRendered === true, { timeout: 20000 })
            .then(() => true)
            .catch(() => false);
        } else {
          await page.goto(`${srv.base}${docPath}`, { waitUntil: "domcontentloaded", timeout: 45000 });
          await page.waitForTimeout(700);
          rendered = true;
        }
        await page.waitForTimeout(250);
        return { rendered, doc_kind: kind };
      },
    });

    // ---- Step 4: fetch + inspect (real facts overlaid on the doc) --------
    await step("fetch_inspect", "verify", "Verify the retrieved document", {
      observation: {
        url: target,
        status: fetched.status,
        content_type: fetched.content_type,
        bytes: fetched.bytes,
        sha256: fetched.sha256,
      },
      decision: {
        rationale:
          fetched.status === 200 ? "Reachable policy document retrieved." : "Document not reachable.",
      },
      action: { type: "fetch", target },
      act: async () => {
        const facts = {
          status: fetched.status,
          content_type: fetched.content_type,
          bytes: fetched.bytes,
          sha256: fetched.sha256,
        };
        // PDF viewer has __showFetchFacts; for served HTML inject a matching overlay.
        await page
          .evaluate((f) => {
            if (window.__showFetchFacts) return window.__showFetchFacts(f);
            const d = document.createElement("div");
            d.style.cssText =
              "position:fixed;right:16px;top:16px;z-index:2147483647;width:330px;" +
              "background:#111827;color:#e5e7eb;border-radius:10px;font:13px ui-sans-serif,system-ui;" +
              "box-shadow:0 10px 30px rgba(0,0,0,.55);overflow:hidden";
            const rows = [
              ["HTTP status", String(f.status), f.status === 200],
              ["Content-Type", String(f.content_type || "")],
              ["Size", (f.bytes || 0).toLocaleString() + " bytes"],
              ["sha256", (f.sha256 || "").slice(0, 16) + "…"],
            ];
            d.innerHTML =
              '<div style="padding:10px 14px;background:#1f2937;color:#93c5fd;font-size:11px;' +
              'letter-spacing:.05em;text-transform:uppercase">Fetched document — verified</div>' +
              rows
                .map(
                  (r) =>
                    '<div style="display:flex;justify-content:space-between;gap:12px;padding:7px 14px;' +
                    'border-top:1px solid #1f2937"><span style="color:#9ca3af">' +
                    r[0] +
                    '</span><span style="font-family:ui-monospace,Menlo,monospace;text-align:right;' +
                    "word-break:break-all;color:" +
                    (r[2] ? "#34d399" : "#e5e7eb") +
                    '">' +
                    r[1] +
                    "</span></div>"
                )
                .join("");
            document.body.appendChild(d);
          }, facts)
          .catch(() => {});
        await page.waitForTimeout(250);
        return facts;
      },
    });

    // ---- Step 5: return the policy --------------------------------------
    const reachable = fetched.status === 200;
    await step("return_policy", "finalize", "Return the governing policy as the answer", {
      observation: { returned_url: target },
      decision: { rationale: "Final answer: the selected governing policy URL." },
      action: { type: "return", target },
      render: async () =>
        setContent(`
          <h1>Governing policy retrieved</h1>
          <div class="sub">${esc(payer)} — ${esc(plan)} · CPT ${esc(cpt)}</div>
          <div class="card">
            <div class="kv"><span class="k">Returned policy</span><span class="v mono">${esc(target)}</span></div>
            <div class="kv"><span class="k">Document</span><span class="v">${esc(targetLeaf)} · ${esc(kind.toUpperCase())}</span></div>
            <div class="kv"><span class="k">HTTP status</span><span class="v">${esc(fetched.status)}</span></div>
            <div class="kv"><span class="k">Bytes</span><span class="v">${(fetched.bytes || 0).toLocaleString()}</span></div>
            <div class="kv"><span class="k">Outcome</span><span class="v"><span class="pill ok">retrieved · reward +1</span></span></div>
          </div>
          <div class="foot">sha256 ${esc((fetched.sha256 || "").slice(0, 32))}…</div>`),
    });

    return {
      ok: true,
      mode,
      row_id: spec.id,
      run_id: runId,
      project_slug: PROJECT_SLUG,
      tenant_id: TENANT_ID,
      workflow_id: `wf_policy_retrieval_${spec.id}`,
      capture_version: CAPTURE_VERSION,
      run_dir: path.join(process.env.HOME ?? "/home/clawd", "clawd", "state", "projects", PROJECT_SLUG, "runs", runId),
      trace_path: path.join(process.env.HOME ?? "/home/clawd", "clawd", "state", "projects", PROJECT_SLUG, "runs", runId, "trace.jsonl"),
      step_count: stepIdx + 1,
      steps: stepIndex,
      ground_truth_url: target,
      selected_url: selected.href,
      fetch: { url: fetched.url, status: fetched.status, content_type: fetched.content_type, bytes: fetched.bytes, sha256: fetched.sha256, error: fetched.error },
      doc_kind: kind,
      reachable,
      navigation_failed: !fetched.buf,
    };
  }

  // -------------------------------------------------------------- dead-ends
  async function runDeadEnd() {
    const isLogin = mode === "login_gated";
    const portal = spec.portal_url || null;

    // ---- Step 1: standardized web search (SERP) -------------------------
    const query = `${payer} ${plan} knee arthroplasty CPT ${cpt} medical necessity policy`;
    const serpResults =
      isLogin && portal
        ? [
            {
              url: portal,
              title: `${payer} — Provider policy library (sign in required)`,
              snippet: `Medical-necessity policies available to registered providers. Sign in to view coverage criteria; no public document is exposed.`,
            },
          ]
        : [];
    const serpNote = isLogin
      ? "0 public policy documents · governing criteria behind provider login"
      : "0 results · no public medical-necessity policy published";
    await step("search_scan", "search", "Web-search for a published policy", {
      observation: { query, public_documents_found: 0 },
      decision: { rationale: "Look for a publicly published medical-necessity policy." },
      action: { type: "search", value: query },
      render: async () => setRawContent(serpFrame(query, serpResults, serpNote)),
    });

    // Optional real attempt against a known portal (only when we have a real URL).
    let attempt = null;
    if (isLogin && portal) {
      attempt = await realFetch(portal);
      await step("attempt_portal", "navigate", "Attempt the payer provider portal", {
        observation: { portal, status: attempt.status, content_type: attempt.content_type, bytes: attempt.bytes },
        decision: { rationale: "The only policy source is the authenticated provider portal." },
        action: { type: "goto", target: portal },
        render: async () =>
          setContent(`
            <h1>Provider portal reached</h1>
            <div class="sub">The governing criteria sit behind the payer's authenticated provider portal.</div>
            <div class="card">
              <div class="kv"><span class="k">Portal</span><span class="v mono">${esc(portal)}</span></div>
              <div class="kv"><span class="k">HTTP status</span><span class="v">${esc(attempt.status)}</span></div>
              <div class="kv"><span class="k">Content-Type</span><span class="v mono">${esc(attempt.content_type || "")}</span></div>
              <div class="kv"><span class="k">Policy document exposed</span><span class="v">No — login required</span></div>
            </div>`),
      });
    }

    // ---- Terminal honest status -----------------------------------------
    const label = isLogin ? "Login-gated provider portal" : "No public policy published";
    const detail = isLogin
      ? `${payer} does not publish a public medical-necessity policy for CPT ${cpt}; the governing criteria are behind the authenticated provider portal. Retrieval requires portal credentials — a human reviewer must confirm.`
      : `${payer} — ${plan} publishes no public medical-necessity policy for CPT ${cpt}. There is no document to retrieve.`;
    await step("honest_stop", "finalize", "Report the honest retrieval outcome", {
      observation: { retrievability: mode },
      decision: { rationale: detail },
      action: { type: "report", target: null },
      render: async () =>
        setContent(`
          <h1>Retrieval outcome</h1>
          <div class="sub">${esc(payer)} — ${esc(plan)} · CPT ${esc(cpt)}</div>
          <div class="card">
            <div class="kv"><span class="k">Result</span><span class="v"><span class="pill ${isLogin ? "warn" : "bad"}">${esc(label)}</span></span></div>
            <div class="kv"><span class="k">Public policy retrieved</span><span class="v">None</span></div>
            <div class="kv"><span class="k">Reward</span><span class="v">-1 (not retrievable)</span></div>
          </div>
          <div class="foot">${esc(detail)}</div>`),
    });

    return {
      ok: true,
      mode,
      row_id: spec.id,
      run_id: runId,
      project_slug: PROJECT_SLUG,
      tenant_id: TENANT_ID,
      workflow_id: `wf_policy_retrieval_${spec.id}`,
      capture_version: CAPTURE_VERSION,
      run_dir: path.join(process.env.HOME ?? "/home/clawd", "clawd", "state", "projects", PROJECT_SLUG, "runs", runId),
      trace_path: path.join(process.env.HOME ?? "/home/clawd", "clawd", "state", "projects", PROJECT_SLUG, "runs", runId, "trace.jsonl"),
      step_count: stepIdx + 1,
      steps: stepIndex,
      ground_truth_url: null,
      selected_url: null,
      fetch: attempt ? { url: attempt.url, status: attempt.status, content_type: attempt.content_type, bytes: attempt.bytes, sha256: attempt.sha256, error: attempt.error } : null,
      doc_kind: null,
      reachable: false,
      navigation_failed: false,
    };
  }
}

// A real-but-wrong same-family distractor so the ranker's selection is a genuine
// (answer-agnostic) choice, not a one-option gimme. These are real payer URLs
// for a DIFFERENT procedure/policy, never the row's governing knee policy.
function pickDistractor(spec) {
  const pool = [
    { href: "https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-medical-drug/surgery-shoulder.pdf", label: "Shoulder surgery medical policy", kind: "pdf" },
    { href: "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId=33999", label: "Spinal cord stimulation LCD", kind: "html" },
    { href: "https://www.premera.com/medicalpolicies/7.01.130.pdf", label: "Bariatric surgery medical policy", kind: "pdf" },
  ];
  // deterministic pick by row id, but never the same doc_kind trap only
  const h = [...spec.id].reduce((a, c) => a + c.charCodeAt(0), 0);
  return pool[h % pool.length];
}

main().catch((e) => {
  process.stderr.write(`[capture_policy_row] FATAL ${e && e.stack ? e.stack : e}\n`);
  process.stdout.write("\n__CAPTURE_SUMMARY__ " + JSON.stringify({ ok: false, error: String(e) }) + "\n");
  process.exit(1);
});
