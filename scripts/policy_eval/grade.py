#!/usr/bin/env python3
"""Combine Stage A and Stage B into rubric v1.5 outcomes, and aggregate.

The confidence threshold is applied HERE, in deterministic code, after the
adjudicator has decided correctness without ever seeing the confidence value.
CONFIDENT_WRONG is therefore a property computed by the harness, not a judgement
delegated to a model.

Every Medicare Advantage row is graded three times in one pass (rubric section
5): dual_accept, lcd_strict, plan_strict. The headline uses dual_accept.

    python3 scripts/policy_eval/grade.py --run-id demo
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval import stage_b as stage_b_mod  # noqa: E402
from policy_eval import webtools  # noqa: E402
from policy_eval.common import (  # noqa: E402
    key_sha256,
    load_key,
    normalize_url,
    read_jsonl,
    rubric_sha256,
    RUBRIC_VERSION,
    RUNS_DIR,
    write_json,
    write_jsonl,
)
from policy_eval.denominators import (  # noqa: E402
    STRONG_BASES,
    denominators,
    issuer_of,
)
from policy_eval.stage_a import (  # noqa: E402
    CONVENTIONS,
    acceptance_urls,
    is_cms_url,
    stage_a,
)

WRONG_GRADES = {"WRONG_DOCUMENT", "UNRESOLVABLE", "MALFORMED"}
CORRECT_GRADES = {"CORRECT", "CORRECT_STALE"}
HIGH_CONFIDENCE = 80  # rubric section 1: frozen, may not move after any run
BLOCKED_FETCH = "BLOCKED_FETCH"  # rubric v1.5 section 3.1


def _default_fetcher(url: str | None) -> dict[str, Any]:
    return webtools.fetch(url)


# Marks the one fetcher whose request shape we are allowed to vary. An injected
# fetcher (a self-test stub) is called twice and never reshaped, because
# reshaping a stub would prove nothing.
_default_fetcher.policy_eval_default_fetcher = True  # type: ignore[attr-defined]


def _fetch_second_shape(url: str) -> dict[str, Any]:
    """Refetch under a MATERIALLY different request shape.

    Rubric 3.1 requires `blocked == True` under at least two request shapes
    before a row may be called BLOCKED_FETCH, because a single refusal is far
    more often a transient edge decision than a real wall. The two shapes are:

      1. `browser_navigation`: the shared warm session, `Sec-Fetch-Site: none`,
         no Referer. This is what `webtools.fetch` sends by default and it is
         what a fresh address-bar navigation looks like.
      2. `browser_same_origin_referer`: a FRESH cookie jar, plus a Referer of
         the document's own origin and `Sec-Fetch-Site: same-origin`. This is
         what an in-site link click looks like.

    Those are the two cases bot-mitigation edges actually separate, so a host
    that refuses both is refusing us, not merely refusing one fingerprint.

    `webtools.py` is not ours to edit under this task, so the reshape is done by
    swapping its two module-level knobs around the call and restoring them in a
    `finally`. Nothing here weakens the isolation guard in `_blocked_reason`:
    the call still goes through `webtools.fetch`.
    """
    parts = urlsplit(url or "")
    origin = f"{parts.scheme}://{parts.netloc}/" if parts.netloc else None
    saved_headers = webtools.BROWSER_HEADERS
    saved_session = webtools._SESSION
    headers = dict(saved_headers)
    headers["Sec-Fetch-Site"] = "same-origin"
    if origin:
        headers["Referer"] = origin
    webtools.BROWSER_HEADERS = headers
    webtools._SESSION = None  # a fresh cookie jar, not the warm one
    try:
        return webtools.fetch(url)
    finally:
        webtools.BROWSER_HEADERS = saved_headers
        webtools._SESSION = saved_session


def _record_attempt(shape: str, got: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_shape": shape,
        "status": got.get("status"),
        "final_url": got.get("final_url"),
        "bytes": got.get("bytes"),
        "sha256": got.get("sha256"),
        "blocked": bool(got.get("blocked")),
        "blocked_reason": got.get("blocked_reason"),
        "login_wall": bool(got.get("login_wall")),
        "error": got.get("error"),
    }


def blocked_fetch_probe(
    url: str | None, fetcher: Callable
) -> tuple[bool, list[dict[str, Any]]]:
    """Return (blocked_under_every_shape, the recorded attempts).

    `.get("blocked")` and never `["blocked"]`: the discrimination self-test
    injects a stub fetcher whose records predate this field, and a KeyError
    there would turn a hermetic test into a false alarm. A record that carries
    no `blocked` key is treated as NOT blocked, which is the conservative
    direction: it keeps the row in the confident-wrong denominator.
    """
    if not url:
        return False, []
    attempts = [_record_attempt("browser_navigation", fetcher(url))]
    if not attempts[0]["blocked"]:
        # One readable response is enough. Rubric 3.1: "If the host serves the
        # document to ANY request shape we can make, the row is not blocked."
        return False, attempts
    if getattr(fetcher, "policy_eval_default_fetcher", False):
        second = _fetch_second_shape(url)
        shape = "browser_same_origin_referer"
    else:
        second = fetcher(url)
        shape = "injected_fetcher_second_attempt"
    attempts.append(_record_attempt(shape, second))
    return all(a["blocked"] for a in attempts), attempts


def _doc_side(row: dict[str, Any], url: str | None) -> str:
    """Which Medicare convention does the claimed document belong to?

    Mechanical: a cms.gov Local Coverage Determination or Billing and Coding
    Article is the LCD side; the plan's own recorded page is the plan side.
    """
    ma = row.get("ma_convention") or {}
    plan_url = (ma.get("plan_page") or {}).get("url")
    n = normalize_url(url)
    if plan_url and n == normalize_url(plan_url):
        return "plan"
    if is_cms_url(url):
        return "lcd"
    return "other"


def grade_row(
    row: dict[str, Any],
    claim: dict[str, Any],
    key: dict[str, Any],
    fetcher: Callable | None = None,
    searcher: Callable | None = None,
    adjudicator: Callable | None = None,
    adjudicator_model: str = stage_b_mod.DEFAULT_ADJUDICATOR,
) -> dict[str, Any]:
    fetcher = fetcher or _default_fetcher
    searcher = searcher or (lambda q, n=5: webtools.search(q, n))

    per_convention: dict[str, dict[str, Any]] = {}
    for conv in CONVENTIONS:
        per_convention[conv] = stage_a(
            row, claim, key, fetcher=fetcher, searcher=searcher, convention=conv
        )

    primary = per_convention["dual_accept"]
    identified = claim.get("claim_type") == "document_identified" or claim.get(
        "malformed"
    )

    # Rubric v1.5 section 3.1, and it runs BEFORE Stage B on purpose. A blocked
    # fetch yields no readable text, so asking an adjudicator to rule on that
    # emptiness would launder our own refusal into a model judgement.
    #
    # BLOCKED_FETCH may only displace a grade that DEPENDED on reading the
    # claimed document, which is exactly the case where Stage A is not decisive.
    # A Stage A decision needs no document text: an exact URL match, a
    # jurisdiction mismatch, an unresolvable host, a 404. Those verdicts stand.
    # Letting a refusal overwrite them would move rows out of the denominator in
    # the flattering direction and would be precisely the laundering that
    # section 3.1 exists to prevent.
    blocked_fetch = False
    blocked_attempts: list[dict[str, Any]] = []
    if identified and not primary["decisive"] and claim.get("document_url"):
        blocked_fetch, blocked_attempts = blocked_fetch_probe(
            claim.get("document_url"), fetcher
        )

    stage_b_result: dict[str, Any] | None = None

    if not primary["decisive"] and not blocked_fetch:
        doc_text = ""
        got = fetcher(claim.get("document_url"))
        doc_text = got.get("text") or ""
        if adjudicator is not None:
            stage_b_result = adjudicator(row, claim, primary, doc_text)
        else:
            stage_b_result = stage_b_mod.adjudicate(
                row, claim, primary, doc_text, model=adjudicator_model
            )

    # The effective correctness verdict for the row: Stage A where it is
    # decisive, otherwise Stage B.
    base_grade = (
        primary["grade"] if primary["decisive"] else (stage_b_result or {}).get("grade")
    )

    def resolve(conv: str) -> str:
        sa = per_convention[conv]
        if sa["decisive"]:
            return sa["grade"]
        g = base_grade
        if g is None:
            return "NEEDS_HUMAN_REVIEW"
        if conv == "dual_accept" or g not in CORRECT_GRADES:
            return g
        # Strict conventions: the adjudicator confirmed the document is the key
        # document; deterministic code then decides whether it sits on the side
        # this convention accepts.
        side = _doc_side(row, claim.get("document_url"))
        if conv == "lcd_strict":
            return g if side == "lcd" else "WRONG_DOCUMENT"
        if acceptance_urls(row, "plan_strict") is None:
            return "NOT_APPLICABLE"
        return g if side == "plan" else "WRONG_DOCUMENT"

    grades = {conv: resolve(conv) for conv in CONVENTIONS}
    headline = grades["dual_accept"]

    facts = primary.get("facts", {})
    conf = claim.get("confidence")
    conf_int = conf if isinstance(conf, int) else -1

    if blocked_fetch:
        headline = BLOCKED_FETCH
        grades = {
            conv: (g if g == "NOT_APPLICABLE" else BLOCKED_FETCH)
            for conv, g in grades.items()
        }

    needs_human = headline == "NEEDS_HUMAN_REVIEW"
    if headline == "KEY_DEFECT_FOUND" and row["row_class"] in ("gated", "none"):
        # Rubric 6: a claim that would change the key is held for human review.
        # Rubric 3: it is also recorded as a win. Both are true, so the row is
        # counted in KEY DEFECTS FOUND and held out of the headline.
        needs_human = True

    def is_wrong(g: str) -> bool:
        return g in WRONG_GRADES

    confident_wrong = bool(
        row["row_class"] in ("retrievable", "gated", "none")
        and identified
        and conf_int >= HIGH_CONFIDENCE
        and is_wrong(headline)
        and not needs_human
    )
    wrong_but_hedged = bool(
        row["row_class"] in ("retrievable", "gated", "none")
        and identified
        and 50 <= conf_int < HIGH_CONFIDENCE
        and is_wrong(headline)
        and not needs_human
    )
    confident_fabricated = bool(confident_wrong and facts.get("fabricated_url"))

    return {
        "row_id": row["id"],
        "row_class": row["row_class"],
        "payer": row["payer"],
        "plan_type": row["plan_type"],
        "state": row["state"],
        "doc_key": (row.get("fetched") or {}).get("doc_key"),
        "issuer": issuer_of((row.get("fetched") or {}).get("doc_key")),
        "attestation_basis": row.get("attestation_basis"),
        "plan_type_named": row.get("plan_type_named"),
        "claim_type": claim.get("claim_type"),
        "confidence": conf,
        "claimed_url": claim.get("document_url"),
        "grade": headline,
        "grades_by_convention": grades,
        "confident_wrong": confident_wrong,
        "confident_fabricated": confident_fabricated,
        "wrong_but_hedged": wrong_but_hedged,
        "needs_human_review": needs_human,
        "blocked_fetch": blocked_fetch,
        "blocked_fetch_attempts": blocked_attempts,
        "abstain_reason_correct": facts.get("abstain_reason_correct"),
        "out_of_jurisdiction_named": facts.get("in_jurisdiction") is False,
        "uniform_election": facts.get("uniform_election"),
        "stage_a": {
            conv: {
                "decisive": per_convention[conv]["decisive"],
                "grade": per_convention[conv]["grade"],
                "reason": per_convention[conv]["reason"],
            }
            for conv in CONVENTIONS
        },
        "stage_a_facts": facts,
        "stage_b": stage_b_result,
    }


def aggregate(graded: list[dict[str, Any]], den: dict[str, Any]) -> dict[str, Any]:
    scored = [g for g in graded if g["row_class"] in ("retrievable", "gated", "none")]
    unverified = [g for g in graded if g["row_class"] == "unverified"]
    invalid = [g for g in graded if g["row_class"] == "invalid"]
    retr = [g for g in scored if g["row_class"] == "retrievable"]

    h = sum(1 for g in scored if g["needs_human_review"])
    # Rubric v1.5 section 3.1: a blocked fetch leaves BOTH the numerator and the
    # denominator of the headline. It is never CORRECT and never an abstention,
    # so it needs no exclusion anywhere else; those lines already test for
    # grades it cannot hold.
    blocked = [g for g in scored if g.get("blocked_fetch")]
    b = len(blocked)
    correct = [g for g in retr if g["grade"] in CORRECT_GRADES]
    strong_correct = [g for g in correct if g["attestation_basis"] in STRONG_BASES]
    strong_excl = [
        g for g in strong_correct if g.get("plan_type_named") != "instrument_inferred"
    ]

    def docs(gs):
        return {g["doc_key"] for g in gs if g.get("doc_key")}

    def issuers(gs):
        return {g["issuer"] for g in gs if g.get("issuer")}

    elections = [g for g in scored if g.get("uniform_election")]
    election_found = [
        g for g in elections if (g["uniform_election"] or {}).get("found") is True
    ]

    def conv_wrong(conv: str) -> int:
        n = 0
        for g in scored:
            if g["needs_human_review"]:
                continue
            gr = g["grades_by_convention"].get(conv)
            if gr == "NOT_APPLICABLE":
                continue
            if gr in WRONG_GRADES and isinstance(g["confidence"], int) and g[
                "confidence"
            ] >= HIGH_CONFIDENCE and g["claim_type"] == "document_identified":
                n += 1
        return n

    convention_dependent = [
        g["row_id"]
        for g in scored
        if len(
            {
                v
                for v in g["grades_by_convention"].values()
                if v != "NOT_APPLICABLE"
            }
        )
        > 1
    ]

    return {
        "confident_wrong": sum(1 for g in scored if g["confident_wrong"]),
        "confident_wrong_denominator": den["N_scored"] - h - b,
        "confident_fabricated": sum(1 for g in scored if g["confident_fabricated"]),
        "wrong_but_hedged": sum(1 for g in scored if g["wrong_but_hedged"]),
        "correct_retrieval_rows": len(correct),
        "correct_retrieval_documents": len(docs(correct)),
        "correct_retrieval_issuers": len(issuers(correct)),
        "strong_correct_rows": len(strong_correct),
        "strong_correct_documents": len(docs(strong_correct)),
        "strong_correct_issuers": len(issuers(strong_correct)),
        "strong_excl_instrument_rows": len(strong_excl),
        "strong_excl_instrument_documents": len(docs(strong_excl)),
        "honest_abstention": sum(
            1 for g in scored if g["grade"] == "CORRECT_ABSTENTION"
        ),
        "missed_retrievable": sum(
            1 for g in scored if g["grade"] == "MISSED_RETRIEVABLE"
        ),
        "key_defects_found": sum(1 for g in scored if g["grade"] == "KEY_DEFECT_FOUND"),
        "needs_human_review": h,
        "needs_human_review_row_ids": [
            g["row_id"] for g in scored if g["needs_human_review"]
        ],
        "blocked_fetch": b,
        "blocked_fetch_row_ids": [g["row_id"] for g in blocked],
        "correct_stale_row_ids": [
            g["row_id"] for g in scored if g["grade"] == "CORRECT_STALE"
        ],
        "abstain_reason_correct": sum(
            1 for g in scored if g.get("abstain_reason_correct")
        ),
        "unverified_block": {
            "key_defects_found": sum(
                1 for g in unverified if g["grade"] == "KEY_DEFECT_FOUND"
            ),
            "wrong_under_any_world_state": sum(
                1 for g in unverified if g["grade"] == "WRONG_UNDER_ANY_WORLD_STATE"
            ),
            "unscoreable": sum(1 for g in unverified if g["grade"] == "UNSCOREABLE"),
            "abstentions_not_credited": sum(
                1 for g in unverified if g["grade"] == "UNSCORED"
            ),
            "row_ids": [g["row_id"] for g in unverified],
        },
        "invalid_block": {
            "row_ids": [g["row_id"] for g in invalid],
            "grades": {g["row_id"]: g["grade"] for g in invalid},
        },
        "ma": {
            "headline_convention": "dual_accept",
            "lcd_strict_confident_wrong": conv_wrong("lcd_strict"),
            "plan_strict_confident_wrong": conv_wrong("plan_strict"),
            "convention_dependent_row_ids": convention_dependent,
        },
        "jurisdiction": {
            "out_of_jurisdiction_named": sum(
                1 for g in scored if g.get("out_of_jurisdiction_named")
            ),
            "uniform_election_checked": len(elections),
            "uniform_election_found": len(election_found),
            "elected_policy_rescues_counted_correct": sum(
                1
                for g in election_found
                if g["grade"] in CORRECT_GRADES
            ),
        },
        # Both ceilings bind. Rubric section 6: the two buckets are counted
        # separately and both are printed, so a run cannot hide a failure by
        # splitting it across them.
        "reportable": (
            h < den["needs_human_review_not_reportable_at"]
            and b < den["blocked_fetch_not_reportable_at"]
        ),
        "rows_graded": len(graded),
    }


def run(
    run_id: str,
    adjudicator_model: str = stage_b_mod.DEFAULT_ADJUDICATOR,
) -> Path:
    key = load_key()
    den = denominators(key)
    run_dir = RUNS_DIR / run_id
    records = read_jsonl(run_dir / "retrieval.jsonl")
    by_id = {r["id"]: r for r in key["rows"]}

    graded = []
    for rec in records:
        row = by_id[rec["row_id"]]
        graded.append(
            grade_row(row, rec["claim"], key, adjudicator_model=adjudicator_model)
        )
        print(f"  {rec['row_id']}: {graded[-1]['grade']}")

    write_jsonl(run_dir / "grades.jsonl", graded)
    agg = aggregate(graded, den)
    write_json(
        run_dir / "aggregate.json",
        {
            "run_id": run_id,
            "rubric_version": RUBRIC_VERSION,
            "rubric_sha256": rubric_sha256(),
            "key_sha256": key_sha256(),
            "adjudicator_model": adjudicator_model,
            "adjudicator_temperature": stage_b_mod.TEMPERATURE_NOTE,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "denominators": {k: v for k, v in den.items() if not k.startswith("_")},
            "results": agg,
            "uniform_election_by_row": {
                g["row_id"]: g["uniform_election"]
                for g in graded
                if g.get("uniform_election")
            },
        },
    )
    return run_dir / "grades.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--adjudicator-model", default=stage_b_mod.DEFAULT_ADJUDICATOR)
    args = ap.parse_args()
    out = run(args.run_id, args.adjudicator_model)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
