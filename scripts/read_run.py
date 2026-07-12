#!/usr/bin/env python3
"""KISS v0 thin reader/labeler for a stored policy-retrieval trajectory.

  python scripts/read_run.py runs/run_0001

Prints the human-readable steps and the automatic oracle verdict. With label
flags it writes a supplemental HUMAN label into meta.json's `label` block and
re-saves. The human label NEVER overwrites the automatic `oracle` block.

  python scripts/read_run.py runs/run_0001 \
      --label-fail-state wrong_variant \
      --failure-type selection_error \
      --expert-action "should have picked comm-medical-drug/surgery-knee.pdf"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _paths(stem: str) -> tuple[Path, Path]:
    p = Path(stem)
    jsonl_path = p.with_suffix(".jsonl")
    meta_path = Path(str(p) + ".meta.json")
    return jsonl_path, meta_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run", help="run stem, e.g. runs/run_0001")
    ap.add_argument("--label-fail-state", dest="fail_state", default=None)
    ap.add_argument("--failure-type", dest="failure_type", default=None)
    ap.add_argument("--expert-action", dest="expert_action", default=None)
    args = ap.parse_args()

    jsonl_path, meta_path = _paths(args.run)
    if not jsonl_path.exists() or not meta_path.exists():
        print(f"missing run files: {jsonl_path} / {meta_path}")
        return 1

    meta = json.loads(meta_path.read_text())

    print("=" * 68)
    print(f"RUN {args.run}")
    print(
        f"  payer={meta.get('payer')} plan={meta.get('plan')} "
        f"cpt={meta.get('cpt')}"
    )
    print(f"  agent target: {meta.get('target')}")
    print("-" * 68)
    print("STEPS")
    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            s = json.loads(line)
            print(f"  [{s['i']}] {s['action']}")
            print(f"       obs: {s.get('obs')}")
            print(f"       self_verdict: {s.get('self_verdict')}")
    print("-" * 68)
    o = meta.get("oracle", {})
    print("ORACLE (automatic, computed from ground truth)")
    print(
        f"  correct={o.get('correct')}  reachable={o.get('reachable')}  "
        f"reward={o.get('reward')}"
    )
    gt = meta.get("ground_truth", {})
    if gt:
        print(f"  ground_truth: {gt.get('target_url')} (doc_id={gt.get('doc_id')})")
    print("-" * 68)

    # Optional human labeling (supplements, never overwrites oracle).
    label_touched = any(
        v is not None
        for v in (args.fail_state, args.failure_type, args.expert_action)
    )
    if label_touched:
        label = meta.setdefault(
            "label",
            {"fail_state": None, "failure_type": None, "expert_action": None},
        )
        if args.fail_state is not None:
            label["fail_state"] = args.fail_state
        if args.failure_type is not None:
            label["failure_type"] = args.failure_type
        if args.expert_action is not None:
            label["expert_action"] = args.expert_action
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        print("HUMAN LABEL written (oracle left untouched):")
        print(f"  {label}")
    else:
        print(f"HUMAN LABEL (unchanged): {meta.get('label')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
