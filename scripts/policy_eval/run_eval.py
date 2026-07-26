#!/usr/bin/env python3
"""End-to-end driver for the policy-retrieval eval.

Stages, each writing an inspectable artifact under runs/<run_id>/:

  0. denominators   derive from the key, assert against rubric 0.2, abort on drift
  1. queries.jsonl  the leak-free question set (six fields per row, nothing else)
  2. retrieval.jsonl + retrieval_prompts.jsonl + retrieval_tool_trace.jsonl
                    the isolated model attempt, its tool calls, and the exact
                    CLI invocation in retrieval_meta.json
  3. leak check     zero key URLs, hosts or document ids in any prompt
  4. grades.jsonl + aggregate.json   Stage A deterministic, Stage B only where
                    Stage A is not decisive
  5. report.txt     rubric section 7 verbatim, gated on shape

Cost discipline: prove the pipeline on 2 rows. The full cold run over all 39
rows is task T005 and is not run from here by default.

    python3 scripts/policy_eval/run_eval.py --run-id demo --limit 2 \
        --model claude-haiku-4-5 --adjudicator-model claude-haiku-4-5 \
        --partial-note "2-row plumbing proof"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval import emit_queries, grade, report, retrieve  # noqa: E402
from policy_eval.common import RUNS_DIR, load_key  # noqa: E402
from policy_eval.denominators import denominators  # noqa: E402
from policy_eval.leakcheck import key_url_inventory, scan_text  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--rows", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--model", default=retrieve.DEFAULT_MODEL)
    ap.add_argument("--adjudicator-model", default=None)
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--partial-note", default=None)
    args = ap.parse_args()
    adj = args.adjudicator_model or args.model

    print("STAGE 0: denominators, derived from the key and asserted against rubric 0.2")
    key = load_key()
    den = denominators(key)
    print(
        f"  N_total={den['N_total']} N_scored={den['N_scored']} "
        f"retrievable={den['retrievable_rows']} rows / "
        f"{den['retrievable_documents']} docs / {den['retrievable_issuers']} issuers "
        f"gated={den['gated']} none={den['none']} "
        f"excluded invalid={den['excluded_invalid']} "
        f"unverified={den['excluded_unverified']}  OK")

    print("STAGE 1: emit the leak-free question set")
    q = emit_queries.emit(args.run_id, args.rows, args.limit)
    print(f"  {q}")

    print("STAGE 2: isolated retrieval (leak assertion runs BEFORE any model call)")
    retrieve.run(args.run_id, args.model, args.timeout)

    print("STAGE 3: leak check over every retrieval prompt")
    inv = key_url_inventory(key)
    prompts = (RUNS_DIR / args.run_id / "retrieval_prompts.jsonl").read_text()
    hits = scan_text(prompts, inv)
    if hits:
        print(f"  LEAK: {hits}", file=sys.stderr)
        return 1
    print(
        f"  zero matches across {len(inv['urls'])} key URLs, "
        f"{len(inv['hosts'])} hosts, {len(inv['doc_ids'])} document ids"
    )

    print("STAGE 4: grading, Stage A deterministic then Stage B where needed")
    grade.run(args.run_id, adj)

    print("STAGE 5: report")
    text, fails = report.render(args.run_id)
    banner = ""
    if args.partial_note:
        banner = (
            "!! PARTIAL RUN, NOT REPORTABLE: "
            + args.partial_note
            + "\n!! The block below prints the full frozen denominators from the "
            "answer key.\n\n"
        )
    out = RUNS_DIR / args.run_id / "report.txt"
    out.write_text(banner + text)
    print()
    print(banner + text)
    if fails:
        print("REPORT SHAPE GATE: FAILED", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 3
    print("REPORT SHAPE GATE: PASSED")
    print(f"artifacts: {RUNS_DIR / args.run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
