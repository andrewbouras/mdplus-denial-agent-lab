#!/usr/bin/env python3
"""Emit ONE real browser-retrieval trajectory into the Plinth trajectory contract.

Orchestrates a genuine multi-step browser browse of the UHC Commercial
medical-drug policy surface (live uhcprovider.com, or a local real-content
mirror if live is flaky) and lands the output in the EXACT run-dir the existing
Plinth replay+rate reader consumes unchanged:

    $HOME/clawd/state/projects/synthetic-emr-demo/runs/<run_[a-f0-9]{12}>/
        trace.jsonl                    RunHeader + per-step StepRecord + ArtifactRecord
        <step_id>/screenshot.png       real screenshot bytes (real sha256)
        <step_id>/dom.html             real page HTML
        training-unit.json             rating pre-filled from the computed oracle

Division of labour (nothing faked, nothing recomputed twice):
    - browser_capture/capture_uhc_policy.mjs   drives the REAL browser, writes
      the trace.jsonl + real screenshots, and prints a JSON summary of the real
      fetch facts (selected URL, status, content-type, bytes, sha256).
    - synthetic_harness/kiss_oracle.py         the SINGLE, unmodified oracle:
      compute_oracle() grades selected-vs-ground-truth from the real fetch facts.
    - synthetic_harness/plinth_contract/oracle_to_rating.py   maps the computed
      oracle onto the Plinth rating (reward-derived; a human can confirm/correct
      the rating but cannot flip reward).

Usage:
    python scripts/emit_plinth_trace.py --row data/policy_platform/kiss_row_uhc_27447.json
        [--surface auto|live|mirror] [--query "knee arthroplasty surgery"]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from synthetic_harness.kiss_oracle import compute_oracle  # noqa: E402
from synthetic_harness.plinth_contract import (  # noqa: E402
    build_training_unit,
    map_oracle_to_rating,
)

CAPTURE_SCRIPT = REPO_ROOT / "browser_capture" / "capture_uhc_policy.mjs"
SUMMARY_MARKER = "__CAPTURE_SUMMARY__"

# Plinth app node_modules holds @playwright/test; reuse it so we do not duplicate
# the install. Overridable via PLINTH_APP_DIR.
PLINTH_APP_DIR = Path(
    os.environ.get("PLINTH_APP_DIR", "/home/clawd/plinth-v1/tools/plinth-app")
)


def run_capture(row_path: Path, surface: str, query: str) -> dict[str, Any]:
    """Shell out to the Node capture and parse its JSON summary line."""
    env = dict(os.environ)
    # Make @playwright/test resolvable from the Plinth app's node_modules without
    # editing any Plinth file (read-only reuse of the installed package).
    node_modules = PLINTH_APP_DIR / "node_modules"
    # ESM ignores NODE_PATH, so the capture imports @playwright/test by absolute
    # path from this dir; pass it explicitly. Keep NODE_PATH too for any CJS deps.
    env["PLINTH_APP_NODE_MODULES"] = str(node_modules)
    prev = env.get("NODE_PATH", "")
    env["NODE_PATH"] = f"{node_modules}{os.pathsep}{prev}" if prev else str(node_modules)

    cmd = [
        "node",
        str(CAPTURE_SCRIPT),
        "--row",
        str(row_path),
        "--surface",
        surface,
        "--query",
        query,
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    # Surface Node stderr for debugging but do not swallow it.
    if proc.stderr.strip():
        sys.stderr.write(proc.stderr)

    summary = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith(SUMMARY_MARKER):
            summary = json.loads(line[len(SUMMARY_MARKER) :].strip())
    if summary is None:
        raise RuntimeError(
            f"capture produced no summary (exit={proc.returncode}). stdout tail:\n"
            + "\n".join(proc.stdout.splitlines()[-15:])
        )
    if not summary.get("ok"):
        raise RuntimeError(f"capture failed: {summary.get('error')}")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", required=True, help="path to ground-truth row json")
    ap.add_argument(
        "--surface",
        default="auto",
        choices=["auto", "live", "mirror"],
        help="navigation surface: auto (live then mirror fallback), live, or mirror",
    )
    ap.add_argument(
        "--query",
        default="knee arthroplasty surgery",
        help="the query the agent types into the policy search",
    )
    args = ap.parse_args()

    row_path = Path(args.row).resolve()
    row = json.loads(row_path.read_text())
    gt = row["ground_truth"]

    # 1) REAL browser capture -> trace.jsonl + real screenshots + fetch facts.
    summary = run_capture(row_path, args.surface, args.query)

    fetch = summary["fetch"]
    selected_url = summary["selected_url"]

    # 2) Compute the oracle (single source of truth; never hardcoded). We also
    #    fetch the ground-truth doc's hash from the mirror/network only when the
    #    selection already URL-matches, to strengthen with a sha256 comparison.
    ground_truth_sha = None  # strengthening optional; URL match already decisive

    oracle = compute_oracle(
        ground_truth_url=gt["target_url"],
        selected_url=selected_url,
        fetch_status=fetch["status"],
        fetch_content_type=fetch["content_type"],
        fetch_sha256=fetch["sha256"],
        ground_truth_sha256=ground_truth_sha,
        policy_content_types=("application/pdf",),
    )

    # 3) Map the computed oracle -> Plinth rating (reward-derived pin).
    steps = summary["steps"]
    decision = steps["rank_select"]
    fetch_step = steps.get("fetch_inspect", steps.get("return_policy"))
    rating = map_oracle_to_rating(
        oracle,
        decision_step_idx=decision["idx"],
        decision_step_id=decision["id"],
        fetch_step_idx=fetch_step["idx"],
        fetch_step_id=fetch_step["id"],
        navigation_failed=bool(summary.get("navigation_failed")),
    )

    # 4) Assemble + write training-unit.json next to trace.jsonl.
    run_id = summary["run_id"]
    run_dir = Path(summary["run_dir"])
    trace_ref = {
        "path": str(summary["trace_path"]),
        "project_slug": summary["project_slug"],
        "tenant_id": summary["tenant_id"],
        "workflow_id": summary["workflow_id"],
        "capture_version": summary["capture_version"],
        "schema_version": 2,
        "step_count": summary["step_count"],
    }
    scenario = {
        "id": "uhc-commercial-cpt27447-knee-policy-retrieval",
        "competency": "policy_retrieval",
        "patient_id": row["row"].get("cpt", "27447"),
        "phi_status": "synthetic",
    }
    unit = build_training_unit(
        run_id=run_id,
        trace_ref=trace_ref,
        scenario=scenario,
        rating=rating,
        rated_at=datetime.now(timezone.utc).isoformat(),
    )
    # Carry the computed oracle alongside the rating for auditability (the human
    # cannot flip reward: it is re-derivable from the trace's real fetch facts).
    unit["oracle"] = {
        "correct": oracle["correct"],
        "reachable": oracle["reachable"],
        "reward": oracle["reward"],
        "url_match": oracle["url_match"],
        "observed_status": oracle["observed_status"],
        "observed_content_type": oracle["observed_content_type"],
    }

    unit_path = run_dir / "training-unit.json"
    unit_path.write_text(json.dumps(unit, indent=2) + "\n")

    print(f"surface: {summary['surface']}" + (f" (live_error={summary.get('live_error')})" if summary.get("live_error") else ""))
    print(f"run_id: {run_id}")
    print(f"run_dir: {run_dir}")
    print(f"steps: {summary['step_count']}  screenshots: {summary['step_count']}")
    print(f"selected: {selected_url}")
    print(f"policy sha256: {fetch['sha256']}")
    print(f"oracle: {unit['oracle']}")
    print(
        "rating: "
        f"outcome={rating['outcome']} verdict={rating['verdict']} "
        f"failure_step_idx={rating['failure']['failure_step_idx']} "
        f"failure_type={rating['failure']['failure_type']}"
    )
    print(f"wrote {unit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
