#!/usr/bin/env python3
"""Report-shape gate self-test: prove the gate FAILS when it must.

A gate that has never been seen to fail is not a gate. This mutates a valid
report in each forbidden way and asserts the build breaks each time.

Forbidden mutations, from rubric section 7 and the T004 card:
  1. drop the correct-retrieval line, leaving confident-wrong alone
     (the anti-degeneracy rule: an always-abstaining model scores zero
     confident-wrong, so the two lines only mean anything side by side)
  2. split the unique-document and unique-issuer clause off the correct-retrieval
     line
  3. remove the ISSUER-BOUND line
  4. remove the UNVERIFIED ROWS block
  5. remove the INDEPENDENCE AND CEILING block
  6. paraphrase one word inside the LIMITATIONS block
  7. reorder the OPEN HUMAN DECISION block
  8. truncate the LIMITATIONS block by one entry
  9. quote a bound against the wrong N (the transcription slip Judge T012 caught)
 10. use the forbidden 3/N shorthand

    python3 scripts/policy_eval/selftest_report_gate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import load_key  # noqa: E402
from policy_eval.denominators import denominators  # noqa: E402
from policy_eval.report import build_report, check_report  # noqa: E402

BASE_AGG = {
    "confident_wrong": 0,
    "confident_fabricated": 0,
    "wrong_but_hedged": 0,
    "correct_retrieval_rows": 0,
    "correct_retrieval_documents": 0,
    "correct_retrieval_issuers": 0,
    "strong_correct_rows": 0,
    "strong_correct_documents": 0,
    "strong_correct_issuers": 0,
    "strong_excl_instrument_rows": 0,
    "strong_excl_instrument_documents": 0,
    "honest_abstention": 0,
    "missed_retrievable": 0,
    "key_defects_found": 0,
    "needs_human_review": 0,
    "unverified_block": {
        "key_defects_found": 0,
        "wrong_under_any_world_state": 0,
        "unscoreable": 0,
        "abstentions_not_credited": 0,
    },
    "ma": {
        "headline_convention": "dual_accept",
        "lcd_strict_confident_wrong": 0,
        "plan_strict_confident_wrong": 0,
        "convention_dependent_row_ids": [],
    },
    "jurisdiction": {
        "out_of_jurisdiction_named": 0,
        "uniform_election_checked": 0,
        "uniform_election_found": 0,
        "elected_policy_rescues_counted_correct": 0,
    },
}


def drop_line(text: str, startswith: str) -> str:
    return "\n".join(ln for ln in text.split("\n") if not ln.startswith(startswith))


def drop_block(text: str, header: str) -> str:
    lines = text.split("\n")
    i = next(i for i, ln in enumerate(lines) if ln.startswith(header))
    j = i + 1
    while j < len(lines) and lines[j].strip():
        j += 1
    return "\n".join(lines[:i] + lines[j:])


def main() -> int:
    key = load_key()
    den = denominators(key)
    good = build_report("gate_selftest", "test-model", BASE_AGG, den, key)

    failures: list[str] = []
    results: list[tuple[str, bool, str]] = []

    base_fails = check_report(good, key, den)
    results.append(("0. an unmutated report PASSES", not base_fails, str(base_fails)))
    if base_fails:
        failures.append(f"0. valid report was rejected: {base_fails}")

    def expect_fail(name: str, mutated: str) -> None:
        fails = check_report(mutated, key, den)
        ok = bool(fails)
        results.append((name, ok, fails[0] if fails else "GATE DID NOT FIRE"))
        if not ok:
            failures.append(f"{name}: the gate did not fire")

    expect_fail(
        "1. correct-retrieval line removed",
        drop_line(good, "CORRECT RETRIEVAL:"),
    )
    expect_fail(
        "2. unique-document/issuer clause split off the line",
        good.replace(
            "unique documents and 0 / 4 unique issuers",
            "unique documents\n                      and 0 / 4 unique issuers",
        ),
    )
    expect_fail("3. ISSUER-BOUND line removed", drop_line(good, "             ISSUER-BOUND"))
    expect_fail(
        "4. UNVERIFIED ROWS block removed", drop_block(good, "UNVERIFIED ROWS BLOCK")
    )
    expect_fail(
        "5. INDEPENDENCE AND CEILING block removed",
        drop_block(good, "INDEPENDENCE AND CEILING"),
    )
    expect_fail(
        "6. one word paraphrased inside LIMITATIONS",
        good.replace("collapses to", "reduces to"),
    )
    reordered = list(key["open_human_decision"].items())
    expect_fail(
        "7. OPEN HUMAN DECISION reordered",
        good.replace(
            json.dumps(key["open_human_decision"]["status"]),
            json.dumps("RESOLVED"),
        ),
    )
    limitation_last = key["known_limitations"][-1]
    expect_fail(
        "8. LIMITATIONS truncated by one entry",
        good.replace("  " + limitation_last + "\n", ""),
    )
    expect_fail(
        "9. bound quoted against the wrong N",
        good.replace("52.7% at N=4 issuers", "63.2% at N=4 issuers"),
    )
    expect_fail(
        "10. forbidden 3/N shorthand for N=34",
        good.replace("8.4% at N=34 rows", "8.8% at N=34 rows"),
    )

    print("REPORT-SHAPE GATE SELF-TEST")
    print("-" * 78)
    for name, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print(f"          -> {str(detail)[:110]}")
    print("-" * 78)
    if failures:
        print("GATE SELF-TEST FAILED", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"GATE SELF-TEST PASSED ({len(results)} / {len(results)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
