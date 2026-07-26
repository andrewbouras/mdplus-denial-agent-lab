#!/usr/bin/env python3
"""Emit the rubric section 7 headline block verbatim, then gate the build on it.

Report shape is a GATE, not a formatting preference. `check_report` fails the
build when:
  - the confident-wrong line and the correct-retrieval line are not printed
    together (an always-abstaining model scores zero confident-wrong, so the two
    lines only mean anything side by side);
  - the correct-retrieval line lacks its unique-document and unique-issuer
    clause on the same physical line;
  - the ISSUER-BOUND line is missing;
  - the UNVERIFIED ROWS block or the INDEPENDENCE AND CEILING block is absent;
  - the LIMITATIONS or OPEN HUMAN DECISION block does not hash-match the key's
    `known_limitations` and `open_human_decision`, copied byte for byte.

Every denominator printed here comes from `denominators()`. Nothing is
hardcoded. Every bound is the exact binomial 1 - 0.05^(1/N); the 3/N shorthand
appears nowhere in this harness.

    python3 scripts/policy_eval/report.py --run-id demo
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import (  # noqa: E402
    RUNS_DIR,
    format_bound,
    key_sha256,
    load_key,
    read_jsonl,
    rubric_sha256,
    sha256_text,
)
from policy_eval.denominators import denominators  # noqa: E402
from policy_eval.grade import aggregate  # noqa: E402


class ReportShapeFailure(RuntimeError):
    pass


# --------------------------------------------------------------------------
# verbatim caveat blocks (rubric section 9)
# --------------------------------------------------------------------------


def canonical_limitations(key: dict[str, Any]) -> str:
    items = key["known_limitations"]
    for it in items:
        if "\n" in it:
            raise ReportShapeFailure(
                "a known_limitations entry contains a newline; the verbatim "
                "block cannot round-trip. Fix the key."
            )
    return "\n".join(items)


def canonical_open_decision(key: dict[str, Any]) -> str:
    return json.dumps(key["open_human_decision"], indent=2, sort_keys=True,
                      ensure_ascii=False)


def indent_block(text: str, spaces: int = 2) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else pad.rstrip() for line in text.split("\n"))


def dedent_block(text: str, spaces: int = 2) -> str:
    out = []
    for line in text.split("\n"):
        out.append(line[spaces:] if line.startswith(" " * spaces) else line.strip())
    return "\n".join(out)


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------


def build_report(
    run_id: str,
    model: str,
    agg: dict[str, Any],
    den: dict[str, Any],
    key: dict[str, Any],
    generated_at: str | None = None,
) -> str:
    d = den
    r = agg
    ksha = key_sha256()
    n_scored = d["N_scored"]
    h = r["needs_human_review"]
    invalid_ids = d["_detail"]["excluded_invalid_ids"]
    def _one_line_reason(row: dict[str, Any]) -> str:
        text = (row.get("provenance") or {}).get("change_reason") or row.get(
            "notes"
        ) or "no reason recorded"
        parts = [p.strip() for p in text.split(".") if p.strip()]
        return ". ".join(parts[:2]) + "."

    invalid_reason = next(
        (_one_line_reason(row) for row in key["rows"] if row["id"] in invalid_ids),
        "no reason recorded",
    )
    unverified_ids = ", ".join(d["_detail"]["excluded_unverified_ids"])
    unverified_pct = (
        100.0 * d["excluded_unverified"] / d["N_total"] if d["N_total"] else 0.0
    )
    ub = r["unverified_block"]
    ma = r["ma"]
    ju = r["jurisdiction"]
    conv_dep = ", ".join(ma["convention_dependent_row_ids"]) or "none"

    lines = []
    lines.append(f"POLICY RETRIEVAL COLD RUN {run_id}")
    lines.append(
        f"model={model}  rubric=v1.3  rubric_sha256={rubric_sha256()}"
    )
    lines.append(
        f"key_sha256={ksha}  "
        f"date={generated_at or dt.datetime.now(dt.timezone.utc).isoformat()}"
    )
    lines.append("")
    lines.append(
        f"CONFIDENT-BUT-WRONG:  {r['confident_wrong']} / {n_scored - h}   "
        f"(fabricated URLs: {r['confident_fabricated']})"
    )
    lines.append(
        f"CORRECT RETRIEVAL:    {r['correct_retrieval_rows']} / "
        f"{d['retrievable_rows']} rows, resting on "
        f"{r['correct_retrieval_documents']} / {d['retrievable_documents']} "
        f"unique documents and {r['correct_retrieval_issuers']} / "
        f"{d['retrievable_issuers']} unique issuers"
    )
    lines.append(
        f"                      strong-attestation subset: "
        f"{r['strong_correct_rows']} / {d['strong_rows']} rows, "
        f"{r['strong_correct_documents']} / {d['strong_documents']} documents, "
        f"{r['strong_correct_issuers']} / {d['strong_issuers']} issuers"
    )
    lines.append(
        f"                      strong subset excluding instrument-inferred: "
        f"{r['strong_excl_instrument_rows']} / "
        f"{d['strong_rows_excl_instrument']} rows, "
        f"{r['strong_excl_instrument_documents']} / "
        f"{d['strong_documents_excl_instrument']} documents"
    )
    abst_den = d["gated"] + d["none"]
    lines.append(
        f"HONEST ABSTENTION:    {r['honest_abstention']} / {abst_den}"
        f"              ({d['gated']} gated + {d['none']} none; "
        "unverified excluded)"
    )
    lines.append(
        f"MISSED RETRIEVABLE:   {r['missed_retrievable']} / {d['retrievable_rows']}"
    )
    lines.append(f"KEY DEFECTS FOUND:    {r['key_defects_found']}")
    lines.append(
        f"NEEDS HUMAN REVIEW:   {h} / {n_scored}"
        "              (excluded from the lines above)"
    )
    lines.append("")
    lines.append(
        f"Denominators: N_total={d['N_total']}  N_scored={n_scored}  "
        f"retrievable={d['retrievable_rows']} rows / "
        f"{d['retrievable_documents']} docs / {d['retrievable_issuers']} issuers"
    )
    lines.append(f"              gated={d['gated']}  none={d['none']}")
    lines.append(
        f"Excluded invalid ({d['excluded_invalid']}):     "
        f"{', '.join(invalid_ids)}: {invalid_reason}"
    )
    lines.append(
        f"Excluded unverified ({d['excluded_unverified']}):  {unverified_ids}"
    )
    lines.append("")
    lines.append(
        f"UNVERIFIED ROWS BLOCK ({d['excluded_unverified']} rows, "
        f"{unverified_pct:.1f}% of {d['N_total']}, excluded from every line above)"
    )
    nu = d["excluded_unverified"]
    lines.append(
        f"  key defects found:            {ub['key_defects_found']} / {nu}"
    )
    lines.append(
        f"  wrong under any world state:  {ub['wrong_under_any_world_state']} / {nu}"
        "   (404, login wall, timeout, fabricated host, no 27447)"
    )
    lines.append(
        f"  unscoreable claims:           {ub['unscoreable']} / {nu}"
        "   (resolved, but could not attest scope; our gap)"
    )
    lines.append(
        f"  abstentions, not credited:    {ub['abstentions_not_credited']} / {nu}"
    )
    lines.append("  This is a limitation of the benchmark, not of the model.")
    lines.append("")
    lines.append("INDEPENDENCE AND CEILING")
    lines.append(
        f"  retrieval: 95% upper bound on error <= "
        f"{format_bound(d['retrievable_documents'])} at "
        f"N={d['retrievable_documents']} unique documents"
    )
    lines.append(
        f"             ({format_bound(d['strong_documents'])} at "
        f"N={d['strong_documents']} strong-only; "
        f"{format_bound(d['strong_documents_excl_instrument'])} at "
        f"N={d['strong_documents_excl_instrument']} excluding instrument-inferred)"
    )
    lines.append(
        f"             ISSUER-BOUND, binding: <= "
        f"{format_bound(d['retrievable_issuers'])} at "
        f"N={d['retrievable_issuers']} issuers "
        f"({format_bound(d['strong_issuers'])} at N={d['strong_issuers']} "
        "issuers in the strong subset)"
    )
    lines.append(
        f"  safety:    95% upper bound on confident-wrong <= "
        f"{format_bound(n_scored)} at N={n_scored} rows,"
    )
    lines.append(
        f"             {format_bound(d['scored_payers'])} at "
        f"N={d['scored_payers']} unique payers"
    )
    lines.append("")
    lines.append(
        f"MA convention: headline={ma['headline_convention']}; lcd_strict "
        f"confident-wrong={ma['lcd_strict_confident_wrong']};"
    )
    lines.append(
        f"               plan_strict confident-wrong="
        f"{ma['plan_strict_confident_wrong']}; convention_dependent={conv_dep}"
    )
    lines.append(
        f"Jurisdiction: out_of_jurisdiction_named={ju['out_of_jurisdiction_named']}; "
        f"uniform_election_rate={ju['uniform_election_found']}/"
        f"{ju['uniform_election_checked']}"
    )
    lines.append(
        "              (elected-policy rescues counted CORRECT: "
        f"{ju['elected_policy_rescues_counted_correct']})"
    )
    lines.append(f"Wrong but hedged (confidence 50-79): {r['wrong_but_hedged']}")
    lines.append("")
    lines.append(f"LIMITATIONS (verbatim from answer key {ksha})")
    lines.append(indent_block(canonical_limitations(key)))
    lines.append("")
    lines.append(f"OPEN HUMAN DECISION (verbatim from answer key {ksha})")
    lines.append(indent_block(canonical_open_decision(key)))
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# build gate
# --------------------------------------------------------------------------


def check_report(text: str, key: dict[str, Any], den: dict[str, Any]) -> list[str]:
    """Return the list of gate failures. Empty list means the build passes."""
    fails: list[str] = []
    lines = text.split("\n")

    cw = [ln for ln in lines if ln.startswith("CONFIDENT-BUT-WRONG:")]
    cr = [ln for ln in lines if ln.startswith("CORRECT RETRIEVAL:")]
    if not cw:
        fails.append("missing the CONFIDENT-BUT-WRONG line")
    if not cr:
        fails.append("missing the CORRECT RETRIEVAL line")
    if bool(cw) != bool(cr):
        fails.append(
            "anti-degeneracy rule: the confident-wrong line and the "
            "correct-retrieval line must be printed together"
        )
    if cw and cr:
        i_cw, i_cr = lines.index(cw[0]), lines.index(cr[0])
        if abs(i_cr - i_cw) != 1:
            fails.append(
                "the confident-wrong line and the correct-retrieval line must be "
                "adjacent so neither can be quoted without the other"
            )
    if cr:
        line = cr[0]
        if "unique documents" not in line or "unique issuers" not in line:
            fails.append(
                "the CORRECT RETRIEVAL line must carry its unique-document AND "
                "unique-issuer clause on the same physical line"
            )
    if not any("ISSUER-BOUND" in ln for ln in lines):
        fails.append("missing the mandatory ISSUER-BOUND line")
    if not any(ln.startswith("UNVERIFIED ROWS BLOCK") for ln in lines):
        fails.append("missing the UNVERIFIED ROWS block")
    if not any(ln.startswith("INDEPENDENCE AND CEILING") for ln in lines):
        fails.append("missing the INDEPENDENCE AND CEILING block")

    # verbatim caveat blocks, hash-matched
    for header, canon in (
        ("LIMITATIONS (verbatim from answer key ", canonical_limitations(key)),
        ("OPEN HUMAN DECISION (verbatim from answer key ", canonical_open_decision(key)),
    ):
        idx = next((i for i, ln in enumerate(lines) if ln.startswith(header)), None)
        if idx is None:
            fails.append(f"missing the {header.split(' (')[0]} block")
            continue
        n_block = len(canon.split("\n"))
        body = "\n".join(lines[idx + 1 : idx + 1 + n_block])
        got = dedent_block(body)
        if sha256_text(got) != sha256_text(canon):
            fails.append(
                f"{header.split(' (')[0]} block does not hash-match the answer "
                f"key. expected sha256={sha256_text(canon)} "
                f"got sha256={sha256_text(got)}"
            )

    # Every printed bound must equal the exact binomial 1 - 0.05^(1/N) for the
    # N it is attached to. This catches both the forbidden 3/N shorthand and the
    # off-by-one-row transcription slip that Judge T012 already caught once,
    # where a bound was quoted against the wrong N.
    for value, n_str in re.findall(r"([0-9]+\.[0-9])% at N=([0-9]+)", text):
        n = int(n_str)
        exact = format_bound(n)
        if f"{value}%" != exact:
            fails.append(
                f"printed bound {value}% is attached to N={n}, but the exact "
                f"binomial 1 - 0.05^(1/{n}) is {exact}"
            )

    # forbidden statistical shorthand
    for n in (
        den["retrievable_documents"],
        den["strong_documents"],
        den["retrievable_issuers"],
        den["N_scored"],
        den["scored_payers"],
    ):
        shorthand = f"{300.0 / n:.1f}%"
        exact = format_bound(n)
        if shorthand != exact and shorthand in text:
            fails.append(
                f"the report contains {shorthand}, which is the forbidden 3/N "
                f"shorthand for N={n}. The exact binomial value is {exact}."
            )

    if "—" in text:
        fails.append("the report contains an em dash, which house style forbids")
    return fails


def render(run_id: str) -> tuple[str, list[str]]:
    key = load_key()
    den = denominators(key)
    run_dir = RUNS_DIR / run_id
    graded = read_jsonl(run_dir / "grades.jsonl")
    agg = aggregate(graded, den)
    meta_path = run_dir / "retrieval_meta.json"
    model = "unknown"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        model = (
            f"{meta.get('retrieval_model')} via Claude CLI "
            f"{meta.get('claude_cli_version')}"
        )
    text = build_report(run_id, model, agg, den, key)
    return text, check_report(text, key, den)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--partial-note", default=None)
    args = ap.parse_args()
    text, fails = render(args.run_id)
    out = RUNS_DIR / args.run_id / "report.txt"
    banner = ""
    if args.partial_note:
        banner = (
            "!! PARTIAL RUN, NOT REPORTABLE: "
            + args.partial_note
            + "\n!! The block below prints the full frozen denominators from the "
            "answer key.\n\n"
        )
    out.write_text(banner + text)
    print(banner + text)
    if fails:
        print("REPORT SHAPE GATE: FAILED", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 3
    print("REPORT SHAPE GATE: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
