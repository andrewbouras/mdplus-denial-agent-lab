#!/usr/bin/env python3
"""Grader self-test, five-way discrimination. Rubric section 6.

Must pass before any real run:
  - an injected wrong URL at confidence 95 grades CONFIDENT_WRONG;
  - the exact key URL at confidence 95 grades CORRECT;
  - an abstention on a retrievable row grades MISSED_RETRIEVABLE;
  - a fabricated host grades CONFIDENT_FABRICATED;
  - a resolving-but-unattesting claim on an unverified row grades UNSCOREABLE
    and never WRONG.

Plus two extra cases this harness insists on:
  - case 6, the Medicare CPT trap: a claim naming the row's own in-jurisdiction
    LCD page grades CORRECT even though CPT 27447 appears nowhere on that page,
    because CMS puts procedure codes on the companion Billing and Coding
    Article. A naive "the document must contain 27447" check would reject every
    correct Medicare answer.
  - case 7, malformed output at high confidence counts with confident-wrong.

The test is hermetic. HTTP and search are stubbed, so it reproduces exactly and
costs nothing. The adjudicator is wired to a function that RAISES: every one of
these outcomes must be reachable by deterministic Stage A code alone. If the
grader ever tries to ask a model whether a fabricated host is fabricated, this
test fails loudly.

    python3 scripts/policy_eval/selftest_discrimination.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import load_key  # noqa: E402
from policy_eval.grade import grade_row  # noqa: E402

FABRICATED = "https://policy.knee-coverage-authority.example/tka/27447.pdf"


def stub_fetcher(pages: dict[str, dict[str, Any]]):
    def _fetch(url: str | None) -> dict[str, Any]:
        base = {
            "url": url,
            "final_url": url,
            "status": 200,
            "redirect_chain": [],
            "content_type": "text/html",
            "bytes": 1000,
            "sha256": "0" * 64,
            "text": "generic page with no election language",
            "text_truncated": False,
            "contains_cpt_27447": False,
            "login_wall": False,
            "login_wall_reason": None,
            "host": "stub",
            "host_resolves": True,
            "error": None,
        }
        base.update(pages.get(url or "", {}))
        return base

    return _fetch


def stub_searcher(results: list[str]):
    def _search(query: str, count: int = 5) -> dict[str, Any]:
        return {
            "backend": "stub",
            "query": query,
            "result_count": len(results),
            "results": [{"title": "stub", "url": u, "snippet": ""} for u in results],
            "error": None,
        }

    return _search


def no_adjudicator(*args, **kwargs):
    raise AssertionError(
        "Stage B was invoked for a case that deterministic code must decide. "
        "Rubric section 6: never delegate a mechanically checkable fact to a model."
    )


def claim(row_id: str, **kw) -> dict[str, Any]:
    base = {
        "row_id": row_id,
        "claim_type": "document_identified",
        "document_url": None,
        "document_id": None,
        "document_title": None,
        "issuer": None,
        "applies_to_attestation": None,
        "cpt_evidence": None,
        "confidence": 95,
        "abstain_reason": None,
        "ma_dual": {"lcd_answer": None, "plan_page_answer": None},
        "alternatives_considered": [],
        "rationale": "stub",
        "malformed": False,
        "malformed_reasons": [],
    }
    base.update(kw)
    return base


def main() -> int:
    key = load_key()
    rows = {r["id"]: r for r in key["rows"]}
    jmap = key["lcd_jurisdiction_map"]

    mi = rows["bm_0056"]  # retrievable, Medicare Advantage, Michigan, WPS J-08
    nc = rows["bm_0057"]  # retrievable, Medicare Advantage, North Carolina
    hm = rows["bm_0060"]  # retrievable, Highmark
    uv = rows["bm_0086"]  # unverified, UPMC ACA Marketplace

    out_of_jurisdiction = jmap["L36007"]["url"]  # Novitas J-L: no Michigan
    key_url_mi = mi["fetched"]["url"]  # A59811 companion article
    own_lcd_page = mi["ma_convention"]["lcd"]["url"]  # L39911 page, no 27447 on it

    failures: list[str] = []
    results: list[tuple[str, str, str, bool]] = []

    def check(name: str, expect: str, got: str, extra_ok: bool = True) -> None:
        ok = (got == expect) and extra_ok
        results.append((name, expect, got, ok))
        if not ok:
            failures.append(f"{name}: expected {expect}, got {got}")

    # 1. injected wrong URL at confidence 95 -> CONFIDENT_WRONG
    g1 = grade_row(
        mi,
        claim("bm_0056", document_url=out_of_jurisdiction, confidence=95),
        key,
        fetcher=stub_fetcher({}),
        searcher=stub_searcher(["https://example.org/no-election-here"]),
        adjudicator=no_adjudicator,
    )
    check(
        "1. injected wrong URL @95 (out-of-jurisdiction LCD)",
        "WRONG_DOCUMENT",
        g1["grade"],
        g1["confident_wrong"] is True,
    )
    if not g1["confident_wrong"]:
        failures.append("1. confident_wrong flag was not set")
    if (g1.get("uniform_election") or {}).get("found") is not False:
        failures.append(
            "1. the uniform-election escape must record {found: false} after a "
            "documented search, never absent"
        )

    # 2. exact key URL at confidence 95 -> CORRECT
    g2 = grade_row(
        mi,
        claim("bm_0056", document_url=key_url_mi, confidence=95),
        key,
        fetcher=stub_fetcher({}),
        searcher=stub_searcher([]),
        adjudicator=no_adjudicator,
    )
    check("2. exact key URL @95", "CORRECT", g2["grade"], not g2["confident_wrong"])

    # 3. abstention on a retrievable row -> MISSED_RETRIEVABLE
    g3 = grade_row(
        nc,
        claim(
            "bm_0057",
            claim_type="cannot_identify",
            document_url=None,
            confidence=10,
            abstain_reason="searched_and_failed",
        ),
        key,
        fetcher=stub_fetcher({}),
        searcher=stub_searcher([]),
        adjudicator=no_adjudicator,
    )
    check(
        "3. abstention on a retrievable row",
        "MISSED_RETRIEVABLE",
        g3["grade"],
        not g3["confident_wrong"] and not g3["confident_fabricated"],
    )

    # 4. fabricated host -> CONFIDENT_FABRICATED
    g4 = grade_row(
        hm,
        claim("bm_0060", document_url=FABRICATED, confidence=95),
        key,
        fetcher=stub_fetcher(
            {
                FABRICATED: {
                    "status": None,
                    "host_resolves": False,
                    "error": "DNS resolution failed",
                }
            }
        ),
        searcher=stub_searcher([]),
        adjudicator=no_adjudicator,
    )
    check(
        "4. fabricated host @95",
        "UNRESOLVABLE",
        g4["grade"],
        g4["confident_fabricated"] is True and g4["confident_wrong"] is True,
    )
    if not g4["confident_fabricated"]:
        failures.append("4. confident_fabricated flag was not set")

    # 5. resolving but unattesting claim on an unverified row -> UNSCOREABLE
    resolving = "https://www.upmchealthplan.com/docs/some-other-policy.pdf"
    g5 = grade_row(
        uv,
        claim(
            "bm_0086",
            document_url=resolving,
            confidence=95,
            applies_to_attestation=None,
        ),
        key,
        fetcher=stub_fetcher(
            {resolving: {"status": 200, "contains_cpt_27447": True,
                         "text": "total knee arthroplasty 27447 criteria"}}
        ),
        searcher=stub_searcher([]),
        adjudicator=no_adjudicator,
    )
    check(
        "5. unverified row, resolves but does not attest",
        "UNSCOREABLE",
        g5["grade"],
        not g5["confident_wrong"],
    )
    if "WRONG" in g5["grade"]:
        failures.append("5. an unverified row was graded WRONG. Hard prohibition.")
    if g5["confident_wrong"]:
        failures.append("5. an unverified row leaked into the headline")

    # 6. the Medicare CPT trap: correct LCD page, 27447 absent from the page
    g6 = grade_row(
        mi,
        claim("bm_0056", document_url=own_lcd_page, confidence=90),
        key,
        fetcher=stub_fetcher(
            {own_lcd_page: {"status": 200, "contains_cpt_27447": False,
                            "text": "Lower extremity major joint replacement LCD"}}
        ),
        searcher=stub_searcher([]),
        adjudicator=no_adjudicator,
    )
    check(
        "6. in-jurisdiction LCD page with no 27447 on it",
        "CORRECT",
        g6["grade"],
        not g6["confident_wrong"],
    )

    # 7. malformed output at high confidence counts with confident-wrong
    g7 = grade_row(
        hm,
        claim(
            "bm_0060",
            confidence=95,
            malformed=True,
            malformed_reasons=["claim_type invalid: None"],
        ),
        key,
        fetcher=stub_fetcher({}),
        searcher=stub_searcher([]),
        adjudicator=no_adjudicator,
    )
    check(
        "7. malformed claim @95",
        "MALFORMED",
        g7["grade"],
        g7["confident_wrong"] is True,
    )

    width = 52
    print("GRADER SELF-TEST, five-way discrimination (rubric section 6)")
    print("-" * 78)
    for name, expect, got, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}} -> {got}")
    print("-" * 78)
    print("  Stage B was never invoked: every outcome above is decided by")
    print("  deterministic code, as rubric section 6 requires.")
    if failures:
        print("SELF-TEST FAILED", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("SELF-TEST PASSED (7 / 7)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
