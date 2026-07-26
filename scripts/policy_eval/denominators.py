#!/usr/bin/env python3
"""Canonical denominators: read them from rubric 0.2, derive them from the key,
assert they agree, abort loudly on any mismatch.

Rubric section 0.2, unchanged in wording since v1.3: "The harness reads these
from here and derives them from answer_key_v1.json at build time. It asserts
the derived values equal the pinned values and aborts on any mismatch, so a key
edit fails the build loudly instead of drifting silently."

Nothing anywhere else in this harness may hardcode a denominator. Every module
calls `denominators()`.

Run standalone:
    python3 scripts/policy_eval/denominators.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import (  # noqa: E402
    KEY_PATH,
    RUBRIC_PATH,
    RUBRIC_VERSION,
    load_key,
)

SCORED_CLASSES = ("retrievable", "gated", "none")
EXCLUDED_CLASSES = ("invalid", "unverified")
# Rubric v1.5 section 2.3 adds the third strong basis. A row on
# `deferral_vendor_two_part` has passed V1 to V5 plus Guard M and Guard S, so
# its counted document (part two, the vendor criteria document) carries the
# same evidentiary weight as a single full-scope document.
STRONG_BASES = (
    "single_document_full_scope",
    "deferral_two_part",
    "deferral_vendor_two_part",
)

# Names that carry a triple value "rows / documents / issuers" in the table.
TRIPLE_KEYS = {
    "strong_rows": ("strong_rows", "strong_documents", "strong_issuers"),
    "strong_rows_excl_instrument": (
        "strong_rows_excl_instrument",
        "strong_documents_excl_instrument",
        "strong_issuers_excl_instrument",
    ),
}


class DenominatorMismatch(RuntimeError):
    pass


def parse_pinned(rubric_path: Path | None = None) -> dict[str, int]:
    """Parse the section 0.2 table out of the rubric markdown."""
    text = Path(rubric_path or RUBRIC_PATH).read_text()

    m = re.search(r"^`rubric_version:\s*([0-9.]+)`", text, re.MULTILINE)
    if not m or m.group(1) != RUBRIC_VERSION:
        raise DenominatorMismatch(
            f"rubric version is {m.group(1) if m else 'absent'}, "
            f"harness implements {RUBRIC_VERSION}"
        )

    start = text.index("## 0.2 Canonical denominators")
    # The section ends at a horizontal rule, which is a line that is exactly
    # "---". Searching for the bare substring instead would stop at the table's
    # own `|---|---|---|` separator row and silently yield an EMPTY pinned
    # table, which would make this whole assertion pass vacuously.
    m_end = re.search(r"^---\s*$", text[start:], re.MULTILINE)
    block = text[start : start + m_end.start()] if m_end else text[start:]

    pinned: dict[str, int] = {}
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        name_cell, value_cell = cells[0], cells[1]
        names = [n.strip().strip("`") for n in name_cell.split("/") if n.strip()]
        if not names or names[0] in ("Quantity", "---"):
            continue
        if set(name_cell) <= set("-| "):
            continue
        values = [v.strip() for v in value_cell.split("/")]
        ints: list[int] = []
        for v in values:
            mm = re.search(r"-?\d+", v)
            if mm:
                ints.append(int(mm.group(0)))
        if not ints:
            continue
        canonical = names[0]
        if canonical in TRIPLE_KEYS and len(ints) == 3:
            for key_name, val in zip(TRIPLE_KEYS[canonical], ints):
                pinned[key_name] = val
        elif len(ints) == 1:
            pinned[canonical] = ints[0]
        elif len(names) == len(ints):
            for key_name, val in zip(names, ints):
                pinned[key_name] = val
        else:
            raise DenominatorMismatch(
                f"cannot parse rubric 0.2 row: {line!r}"
            )
    # Guard against a vacuous pass. If the parser silently returns nothing, the
    # comparison below would find no mismatches and report success while
    # checking nothing at all.
    required = {
        "N_total",
        "N_scored",
        "retrievable_rows",
        "retrievable_documents",
        "retrievable_issuers",
        "gated",
        "none",
        "excluded_invalid",
        "excluded_unverified",
    }
    missing = required - set(pinned)
    if missing:
        raise DenominatorMismatch(
            f"rubric section 0.2 did not yield the pinned values {sorted(missing)}. "
            "Refusing to run: an empty pinned table would make the denominator "
            "assertion pass without checking anything."
        )
    return pinned


def issuer_of(doc_key: str | None) -> str | None:
    """Derive the ISSUER of a counted document from its doc_key.

    Rubric 0.1/0.2 count unique issuers, and the key stores no flat issuer
    field. CMS article and LCD keys are `A#####` / `L#####`; payer document keys
    are `<ISSUER>_<policy id>`. Rubric 2.2 fixes the one case that matters:
    bm_0058's counted document A57685 "is issued by CMS, which was already
    counted", even though the row's fetched URL is a Blue Shield page.
    """
    if not doc_key:
        return None
    if re.fullmatch(r"[AL]\d+", doc_key):
        return "CMS"
    return doc_key.split("_", 1)[0]


def derive(key: dict[str, Any]) -> dict[str, Any]:
    rows = key["rows"]
    by_class: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_class.setdefault(r["row_class"], []).append(r)

    retrievable = by_class.get("retrievable", [])
    scored = [r for r in rows if r["row_class"] in SCORED_CLASSES]

    def doc_key_of(r: dict[str, Any]) -> str | None:
        return (r.get("fetched") or {}).get("doc_key")

    strong = [r for r in retrievable if r.get("attestation_basis") in STRONG_BASES]
    strong_excl = [r for r in strong if r.get("plan_type_named") != "instrument_inferred"]

    def docs(rs: list[dict[str, Any]]) -> set[str]:
        return {d for d in (doc_key_of(r) for r in rs) if d}

    def issuers(rs: list[dict[str, Any]]) -> set[str]:
        return {i for i in (issuer_of(doc_key_of(r)) for r in rs) if i}

    derived = {
        "N_total": len(rows),
        "excluded_invalid": len(by_class.get("invalid", [])),
        "excluded_unverified": len(by_class.get("unverified", [])),
        "N_scored": len(scored),
        "scored_payers": len({r["payer"] for r in scored}),
        "retrievable_rows": len(retrievable),
        "retrievable_documents": len(docs(retrievable)),
        "retrievable_issuers": len(issuers(retrievable)),
        "strong_rows": len(strong),
        "strong_documents": len(docs(strong)),
        "strong_issuers": len(issuers(strong)),
        "strong_rows_excl_instrument": len(strong_excl),
        "strong_documents_excl_instrument": len(docs(strong_excl)),
        "strong_issuers_excl_instrument": len(issuers(strong_excl)),
        "gated": len(by_class.get("gated", [])),
        "none": len(by_class.get("none", [])),
        "ma_scored_rows": len(
            [r for r in scored if r["plan_type"] == "Medicare Advantage"]
        ),
    }
    derived["needs_human_review_not_reportable_at"] = -(
        -derived["N_scored"] * 20 // 100
    )  # ceil(0.20 * N_scored)
    # Rubric v1.5: BLOCKED_FETCH is OUR artefact, not a property of the payer,
    # so it is excluded from both the numerator and the denominator of the
    # headline. It gets the same ceiling rule as needs_human_review: once a
    # fifth of the scored rows are pages we were refused, the headline is a
    # statement about our request shape and is not reportable.
    derived["blocked_fetch_not_reportable_at"] = -(
        -derived["N_scored"] * 20 // 100
    )  # ceil(0.20 * N_scored)

    derived["_detail"] = {
        "retrievable_row_ids": [r["id"] for r in retrievable],
        "retrievable_doc_keys": sorted(docs(retrievable)),
        "retrievable_issuers": sorted(issuers(retrievable)),
        "strong_row_ids": [r["id"] for r in strong],
        "strong_doc_keys": sorted(docs(strong)),
        "strong_issuers": sorted(issuers(strong)),
        "strong_excl_instrument_row_ids": [r["id"] for r in strong_excl],
        "strong_excl_instrument_doc_keys": sorted(docs(strong_excl)),
        "excluded_invalid_ids": [r["id"] for r in by_class.get("invalid", [])],
        "excluded_unverified_ids": [r["id"] for r in by_class.get("unverified", [])],
        "scored_row_ids": [r["id"] for r in scored],
        "honest_abstention_denominator": derived["gated"] + derived["none"],
    }
    return derived


def denominators(
    key: dict[str, Any] | None = None,
    rubric_path: Path | None = None,
    key_path: Path | None = None,
) -> dict[str, Any]:
    """Derive, compare against the rubric's pinned table, abort on mismatch."""
    key = key or load_key(key_path)
    pinned = parse_pinned(rubric_path)
    derived = derive(key)

    mismatches = []
    for name, pin in sorted(pinned.items()):
        if name not in derived:
            mismatches.append(f"  {name}: pinned={pin} derived=<NOT DERIVED>")
        elif derived[name] != pin:
            mismatches.append(f"  {name}: pinned={pin} derived={derived[name]}")
    missing_pins = sorted(set(derived) - set(pinned) - {"_detail"})
    if mismatches:
        raise DenominatorMismatch(
            "rubric 0.2 pinned denominators disagree with the answer key.\n"
            + "\n".join(mismatches)
            + "\nSTOP. Do not adjust either side to make them agree."
        )

    # Abort if an excluded row leaked into a headline denominator.
    excluded_ids = set(derived["_detail"]["excluded_invalid_ids"]) | set(
        derived["_detail"]["excluded_unverified_ids"]
    )
    leaked = excluded_ids & set(derived["_detail"]["scored_row_ids"])
    if leaked:
        raise DenominatorMismatch(
            f"excluded rows appear in a headline denominator: {sorted(leaked)}"
        )
    if derived["N_scored"] != derived["N_total"] - derived["excluded_invalid"] - derived[
        "excluded_unverified"
    ]:
        raise DenominatorMismatch("N_scored arithmetic does not close")

    derived["_pinned"] = pinned
    derived["_unpinned_derived"] = missing_pins
    return derived


def selftest_abort() -> list[str]:
    """Prove the assertion ABORTS on drift. An assertion never seen to fire is
    not an assertion. The real key is never modified: these mutations are made
    on in-memory copies."""
    import copy

    problems: list[str] = []
    base = load_key()

    def must_abort(name: str, mutate) -> None:
        k = copy.deepcopy(base)
        mutate(k)
        try:
            denominators(k)
        except DenominatorMismatch:
            print(f"  PASS  {name} aborts the build")
            return
        problems.append(f"{name} did NOT abort the build")
        print(f"  FAIL  {name} did NOT abort the build")

    must_abort("a deleted row", lambda k: k["rows"].pop())
    must_abort(
        "an unverified row silently promoted to retrievable",
        lambda k: next(
            r for r in k["rows"] if r["row_class"] == "unverified"
        ).__setitem__("row_class", "retrievable"),
    )
    must_abort(
        "a retrievable row repointed at a new document",
        lambda k: next(
            r for r in k["rows"] if r["row_class"] == "retrievable"
        )["fetched"].__setitem__("doc_key", "BRAND_NEW_DOC"),
    )
    must_abort(
        "an instrument-inferred row relabelled explicit",
        lambda k: next(
            r for r in k["rows"] if r.get("plan_type_named") == "instrument_inferred"
        ).__setitem__("plan_type_named", "explicit"),
    )
    return problems


def main() -> int:
    if "--selftest" in sys.argv:
        print("DENOMINATOR ASSERTION SELF-TEST (drift must abort the build)")
        print("-" * 62)
        problems = selftest_abort()
        print("-" * 62)
        if problems:
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 1
        print("DENOMINATOR ABORT SELF-TEST PASSED (4 / 4)")
        return 0
    key = load_key()
    try:
        d = denominators(key)
    except DenominatorMismatch as exc:
        print("DENOMINATOR ASSERTION FAILED", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2
    order = [
        "N_total",
        "N_scored",
        "retrievable_rows",
        "retrievable_documents",
        "retrievable_issuers",
        "gated",
        "none",
        "excluded_invalid",
        "excluded_unverified",
        "scored_payers",
        "strong_rows",
        "strong_documents",
        "strong_issuers",
        "strong_rows_excl_instrument",
        "strong_documents_excl_instrument",
        "strong_issuers_excl_instrument",
        "ma_scored_rows",
        "needs_human_review_not_reportable_at",
        "blocked_fetch_not_reportable_at",
    ]
    print(f"key      = {KEY_PATH}")
    print(f"rubric   = {RUBRIC_PATH} (v{RUBRIC_VERSION})")
    print("-" * 62)
    for name in order:
        print(f"  {name:<40} {d[name]:>4}   derived == pinned OK")
    print("-" * 62)
    print(
        "  excluded rows never enter a headline denominator: "
        f"invalid={d['_detail']['excluded_invalid_ids']} "
        f"unverified={d['_detail']['excluded_unverified_ids']}"
    )
    print(f"  retrievable documents: {d['_detail']['retrievable_doc_keys']}")
    print(f"  retrievable issuers:   {d['_detail']['retrievable_issuers']}")
    print("ALL DENOMINATOR ASSERTIONS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
