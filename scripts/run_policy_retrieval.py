#!/usr/bin/env python3
"""KISS v0 policy-retrieval runner.

Runs ONE real payer-policy-retrieval attempt for a single ground-truth row and
writes a REAL structured trajectory to two flat files:

  runs/<name>.jsonl      one JSON object per step
  runs/<name>.meta.json  row + agent target + automatic oracle + human label

The "agent" makes a genuine decision: it ranks a candidate set of payer-domain
policy URLs by keyword relevance to the row (payer / plan / line-of-business /
procedure) and selects the top-ranked candidate. The candidate set contains the
true policy AND at least one plausible-but-wrong payer policy, and the true one
is NOT labeled/handed to the agent. A bad ranking CAN pick wrong -> the oracle
can then return correct=false.

The selected URL is then fetched over the real network (status, content-type,
bytes, sha256 recorded), and the oracle is computed by comparison to ground
truth. Nothing is hardcoded.

Usage:
  python scripts/run_policy_retrieval.py \
      --row data/policy_platform/kiss_row_uhc_27447.json \
      --out runs/run_0001
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import requests

# Ensure repo root is importable so `synthetic_harness` resolves when run from
# anywhere.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from synthetic_harness.kiss_oracle import compute_oracle  # noqa: E402

USER_AGENT = "orthoappeals-kiss-policy-retrieval/0.1"
FETCH_TIMEOUT = 45

# CPT 27447 = total knee arthroplasty; expand the code to human keywords the
# selection policy can actually match against filenames/paths.
CPT_KEYWORDS = {
    "27447": ["knee", "arthroplasty", "joint", "surgery"],
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def build_candidates(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble the honest candidate set from the snapshot.

    Includes the true target and every declared distractor, SHUFFLED into a
    single list with NO correctness labels exposed to the ranker. Order is
    deterministic (sorted by url) so the true answer is not trivially first.
    """
    gt = row["ground_truth"]
    candidates: list[dict[str, Any]] = [{"url": gt["target_url"]}]
    for d in row.get("distractors", []):
        candidates.append({"url": d["url"]})
    # Deterministic, answer-agnostic ordering.
    candidates.sort(key=lambda c: c["url"])
    return candidates


def score_candidate(url: str, row: dict[str, Any]) -> float:
    """Real relevance score: keyword overlap between the row's query terms and
    the candidate URL. No knowledge of which candidate is correct.
    """
    r = row["row"]
    query_terms = set()
    for field in (r.get("payer"), r.get("plan"), r.get("line_of_business"), r.get("state")):
        query_terms.update(_tokenize(str(field)))
    query_terms.update(CPT_KEYWORDS.get(str(r.get("cpt")), []))
    # Map line-of-business to the payer's URL taxonomy the way a human would:
    # commercial policies live under comm-medical-drug, Medicare Advantage under
    # medadv-mp. This is domain knowledge, not answer knowledge.
    lob = str(r.get("line_of_business", "")).lower()
    if "commercial" in lob:
        query_terms.update(["comm", "medical", "drug"])
    if "medicare" in lob:
        query_terms.update(["medadv", "mp"])

    url_terms = set(_tokenize(url))
    overlap = query_terms & url_terms
    return float(len(overlap))


def rank_and_select(
    candidates: list[dict[str, Any]], row: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scored = []
    for c in candidates:
        s = score_candidate(c["url"], row)
        scored.append({"url": c["url"], "score": s})
    # Stable tie-break by url so selection is deterministic and reproducible.
    scored.sort(key=lambda x: (-x["score"], x["url"]))
    return scored[0], scored


def fetch(url: str) -> dict[str, Any]:
    """Perform a REAL HTTP GET and record the observed facts."""
    try:
        resp = requests.get(
            url, timeout=FETCH_TIMEOUT, headers={"User-Agent": USER_AGENT}
        )
        body = resp.content
        return {
            "url": url,
            "status": resp.status_code,
            "content_type": resp.headers.get("content-type"),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "status": None,
            "content_type": None,
            "bytes": 0,
            "sha256": None,
            "error": str(exc),
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", required=True, help="path to ground-truth row json")
    ap.add_argument(
        "--out",
        required=True,
        help="output stem, e.g. runs/run_0001 (writes .jsonl and .meta.json)",
    )
    ap.add_argument(
        "--verify-truth",
        action="store_true",
        help="also fetch the ground-truth doc to strengthen the oracle with a "
        "sha256 comparison (extra network call).",
    )
    args = ap.parse_args()

    row_path = Path(args.row)
    row = json.loads(row_path.read_text())

    out_stem = Path(args.out)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_stem.with_suffix(".jsonl")
    meta_path = Path(str(out_stem) + ".meta.json")

    steps: list[dict[str, Any]] = []

    def log_step(action: str, args_val: Any, obs: str, self_verdict: str) -> None:
        steps.append(
            {
                "i": len(steps),
                "action": action,
                "args": args_val,
                "obs": obs,
                "self_verdict": self_verdict,
            }
        )

    # Step 0: load_row
    r = row["row"]
    log_step(
        "load_row",
        {"path": str(row_path)},
        f"payer={r['payer']} plan={r['plan']} lob={r['line_of_business']} "
        f"state={r['state']} cpt={r['cpt']}",
        "row loaded",
    )

    # Step 1: build_candidates
    candidates = build_candidates(row)
    log_step(
        "build_candidates",
        {"urls": [c["url"] for c in candidates]},
        f"{len(candidates)} candidate policy URLs (answer NOT labeled)",
        "candidates assembled",
    )

    # Step 2: rank + select
    top, scored = rank_and_select(candidates, row)
    selected_url = top["url"]
    log_step(
        "rank_select",
        {"ranking": scored},
        f"selected {selected_url} (score={top['score']})",
        "best keyword-relevance match chosen",
    )

    # Step 3: fetch (REAL network)
    fetched = fetch(selected_url)
    log_step(
        "fetch",
        {"url": selected_url},
        f"status={fetched['status']} content_type={fetched['content_type']} "
        f"bytes={fetched['bytes']} error={fetched['error']}",
        "policy document appears reachable"
        if fetched["status"] == 200
        else "fetch did not return 200",
    )

    # Step 4: inspect
    log_step(
        "inspect",
        {
            "status": fetched["status"],
            "content_type": fetched["content_type"],
            "sha256": fetched["sha256"],
        },
        f"sha256={fetched['sha256']}",
        "looks like a policy PDF"
        if (fetched["content_type"] or "").startswith("application/pdf")
        else "content-type not a policy document",
    )

    # Optional: fetch ground-truth doc to strengthen oracle with sha256.
    gt = row["ground_truth"]
    gt_sha = None
    if args.verify_truth:
        gt_fetch = fetch(gt["target_url"])
        gt_sha = gt_fetch["sha256"]
        log_step(
            "verify_truth_fetch",
            {"url": gt["target_url"]},
            f"ground-truth sha256={gt_sha} status={gt_fetch['status']}",
            "ground-truth doc fetched for hash comparison",
        )

    # Step 5: return_policy
    log_step(
        "return_policy",
        {"url": selected_url},
        f"agent returns {selected_url}",
        "final answer",
    )

    # Compute the automatic oracle (never hardcoded).
    oracle = compute_oracle(
        ground_truth_url=gt["target_url"],
        selected_url=selected_url,
        fetch_status=fetched["status"],
        fetch_content_type=fetched["content_type"],
        fetch_sha256=fetched["sha256"],
        ground_truth_sha256=gt_sha,
        policy_content_types=("application/pdf",),
    )

    meta = {
        "row": r,
        "payer": r["payer"],
        "plan": r["plan"],
        "cpt": str(r["cpt"]),
        "target": selected_url,
        "fetch": fetched,
        "oracle": {
            "correct": oracle["correct"],
            "reachable": oracle["reachable"],
            "reward": oracle["reward"],
        },
        "oracle_detail": {
            k: oracle[k]
            for k in ("url_match", "sha256_checked", "observed_status", "observed_content_type")
        },
        "ground_truth": {
            "target_url": gt["target_url"],
            "doc_id": gt["doc_id"],
            "provenance": row.get("provenance", {}).get("source"),
        },
        "label": {"fail_state": None, "failure_type": None, "expert_action": None},
    }

    # Write the two flat files.
    with jsonl_path.open("w") as f:
        for s in steps:
            f.write(json.dumps(s) + "\n")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"wrote {jsonl_path} ({len(steps)} steps)")
    print(f"wrote {meta_path}")
    print(f"selected: {selected_url}")
    print(f"oracle: {meta['oracle']}")

    if fetched["error"]:
        # Real unreachability is a legitimate outcome (reward -1); surface it but
        # do not fake reachability. Non-zero exit only on a hard crash, not here.
        print(f"NOTE: fetch error recorded honestly: {fetched['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
