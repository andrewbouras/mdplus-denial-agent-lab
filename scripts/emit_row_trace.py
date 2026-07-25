#!/usr/bin/env python3
"""Emit ONE real Plinth trajectory for a seed_review_39 spec row (any mode).

Generalizes scripts/emit_plinth_trace.py to the whole 39-row set. Shells the
generalized capture (browser_capture/capture_policy_row.mjs), then computes the
automatic oracle from the REAL fetch facts and writes training-unit.json into the
Plinth run-dir the replay reader consumes.

Modes (from the row's human-reviewed retrievability):
    public            real fetch -> oracle reward +1 when host+path match ground
                      truth and the doc is reachable (PDF or HTML content-type).
    login_gated       honest dead-end -> reward -1 (login-gated portal).
    no_public_policy  honest dead-end -> reward -1 (no public policy).

Usage:
    python scripts/emit_row_trace.py --spec data/policy_platform/seed_review_39_spec.json --id bm_0058
    python scripts/emit_row_trace.py --row /tmp/one_row.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
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

CAPTURE_SCRIPT = REPO_ROOT / "browser_capture" / "capture_policy_row.mjs"
SUMMARY_MARKER = "__CAPTURE_SUMMARY__"
PLINTH_APP_DIR = Path(os.environ.get("PLINTH_APP_DIR", "/home/clawd/plinth-v1/tools/plinth-app"))


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def run_capture(row_path: Path) -> dict[str, Any]:
    env = dict(os.environ)
    node_modules = PLINTH_APP_DIR / "node_modules"
    env["PLINTH_APP_NODE_MODULES"] = str(node_modules)
    prev = env.get("NODE_PATH", "")
    env["NODE_PATH"] = f"{node_modules}{os.pathsep}{prev}" if prev else str(node_modules)
    cmd = ["node", str(CAPTURE_SCRIPT), "--row", str(row_path)]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.stderr.strip():
        sys.stderr.write(proc.stderr)
    summary = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith(SUMMARY_MARKER):
            summary = json.loads(line[len(SUMMARY_MARKER):].strip())
    if summary is None:
        raise RuntimeError(
            f"capture produced no summary (exit={proc.returncode}). stdout tail:\n"
            + "\n".join(proc.stdout.splitlines()[-15:])
        )
    if not summary.get("ok"):
        raise RuntimeError(f"capture failed: {summary.get('error')}")
    return summary


def load_row(args) -> dict[str, Any]:
    if args.row:
        return json.loads(Path(args.row).read_text())
    spec = json.loads(Path(args.spec).read_text())
    for r in spec["rows"]:
        if r["id"] == args.id:
            return r
    raise SystemExit(f"row id {args.id} not found in {args.spec}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", help="path to seed_review_39_spec.json")
    ap.add_argument("--id", help="row id (bm_XXXX) when using --spec")
    ap.add_argument("--row", help="path to a single-row json (alternative to --spec/--id)")
    args = ap.parse_args()
    if not args.row and not (args.spec and args.id):
        raise SystemExit("provide --row OR (--spec AND --id)")

    row = load_row(args)
    mode = row["retrievability"]

    # Write the single row to a temp file the Node capture consumes.
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(row, tf)
        row_tmp = Path(tf.name)

    try:
        summary = run_capture(row_tmp)
    finally:
        row_tmp.unlink(missing_ok=True)

    steps = summary["steps"]

    if mode == "public":
        fetch = summary["fetch"]
        kind = summary.get("doc_kind") or row.get("doc_kind")
        policy_cts = ("application/pdf",) if kind == "pdf" else ("text/html",)
        oracle = compute_oracle(
            ground_truth_url=row["target_url"],
            selected_url=summary["selected_url"],
            fetch_status=fetch["status"],
            fetch_content_type=fetch["content_type"],
            fetch_sha256=fetch["sha256"],
            policy_content_types=policy_cts,
        )
        decision = steps["rank_select"]
        fetch_step = steps["fetch_inspect"]
        nav_failed = bool(summary.get("navigation_failed"))
    else:
        # Honest dead-end: nothing publicly retrievable -> reward -1, computed
        # (no ground-truth URL, no reachable policy fetch).
        oracle = compute_oracle(
            ground_truth_url="",
            selected_url=None,
            fetch_status=None,
            fetch_content_type=None,
        )
        decision = steps.get("search_scan", steps.get("open_task"))
        fetch_step = steps.get("honest_stop", decision)
        nav_failed = False

    rating = map_oracle_to_rating(
        oracle,
        decision_step_idx=decision["idx"],
        decision_step_id=decision["id"],
        fetch_step_idx=fetch_step["idx"],
        fetch_step_id=fetch_step["id"],
        navigation_failed=nav_failed,
    )

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
        "id": f"{slug(row['payer'])}-{slug(row['plan_type'])}-cpt{row.get('cpt','27447')}-knee-policy-retrieval",
        "competency": "policy_retrieval",
        "patient_id": row.get("cpt", "27447"),
        "phi_status": "synthetic",
    }
    unit = build_training_unit(
        run_id=run_id,
        trace_ref=trace_ref,
        scenario=scenario,
        rating=rating,
        rated_at=datetime.now(timezone.utc).isoformat(),
    )
    unit["oracle"] = {
        "correct": oracle["correct"],
        "reachable": oracle["reachable"],
        "reward": oracle["reward"],
        "url_match": oracle["url_match"],
        "observed_status": oracle["observed_status"],
        "observed_content_type": oracle["observed_content_type"],
    }
    # Carry row identity for the sheet-synced UI (which run backs which row).
    unit["row"] = {
        "id": row["id"],
        "payer": row["payer"],
        "plan_type": row["plan_type"],
        "cpt": row.get("cpt", "27447"),
        "retrievability": mode,
        "reviewer": row.get("reviewer"),
        "target_url": row.get("target_url"),
    }

    unit_path = run_dir / "training-unit.json"
    unit_path.write_text(json.dumps(unit, indent=2) + "\n")

    print(f"row: {row['id']}  mode: {mode}")
    print(f"run_id: {run_id}")
    print(f"run_dir: {run_dir}")
    print(f"steps: {summary['step_count']}")
    print(f"selected: {summary.get('selected_url')}")
    if summary.get("fetch"):
        print(f"fetch: status={summary['fetch']['status']} ct={summary['fetch']['content_type']} bytes={summary['fetch']['bytes']}")
    print(f"oracle: {unit['oracle']}")
    print(f"rating: outcome={rating['outcome']} verdict={rating['verdict']} failure_step_idx={rating['failure']['failure_step_idx']}")
    print(f"wrote {unit_path}")
    # Machine-readable tail for the batch driver.
    print("__EMIT_RESULT__ " + json.dumps({
        "row_id": row["id"], "mode": mode, "run_id": run_id,
        "run_dir": str(run_dir), "reward": oracle["reward"],
        "reviewer": row.get("reviewer"),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
