#!/usr/bin/env python3
"""Verify: grep the retrieval prompt log for every answer-key URL and host.

Zero matches is the pass condition. The forbidden list is built from the key
itself, so a key edit widens the check automatically.

This deliberately scans PROMPTS only. A URL the model found by searching the
open web is the measurement, not a leak, and it lives in the tool trace.

    python3 scripts/policy_eval/verify_no_leak.py --run-id demo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import RUNS_DIR, load_key, read_jsonl  # noqa: E402
from policy_eval.leakcheck import key_url_inventory, scan_text  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()

    run_dir = RUNS_DIR / args.run_id
    prompt_log = run_dir / "retrieval_prompts.jsonl"
    if not prompt_log.exists():
        print(f"missing {prompt_log}", file=sys.stderr)
        return 2

    key = load_key()
    inv = key_url_inventory(key)
    prompts = read_jsonl(prompt_log)
    queries_path = run_dir / "queries.jsonl"
    blob_targets = {
        f"prompt:{p['row_id']}": p["prompt"] for p in prompts
    }
    if queries_path.exists():
        blob_targets["queries.jsonl"] = queries_path.read_text()

    total_hits = 0
    print(f"run:          {args.run_id}")
    print(f"prompts:      {len(prompts)}")
    print(
        f"forbidden:    {len(inv['urls'])} key URLs, {len(inv['hosts'])} key hosts, "
        f"{len(inv['doc_ids'])} key document ids"
    )
    print("-" * 70)
    for label, text in sorted(blob_targets.items()):
        hits = scan_text(text, inv)
        total_hits += len(hits)
        status = "CLEAN" if not hits else f"LEAK x{len(hits)}"
        print(f"  {status:<10} {label}")
        for h in hits:
            print(f"      {h['kind']}: {h['value']}")
    print("-" * 70)
    print(f"hosts checked: {', '.join(inv['hosts'])}")
    print(f"TOTAL MATCHES: {total_hits}")
    if total_hits:
        print("LEAK CHECK FAILED. The run is void.", file=sys.stderr)
        return 1
    print("LEAK CHECK PASSED: zero matches for every key URL, host and document id.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
