#!/usr/bin/env python3
"""Stage B: the model adjudicator, invoked ONLY where Stage A is not decisive.

Rubric section 6: "It receives the fetched document text, the key entry, and the
model's claim. It NEVER receives the retrieval model's reasoning."

Enforced structurally. The adjudicator input is built from a WHITELIST of claim
fields. `rationale` and `alternatives_considered` are the retrieval model's
reasoning and are dropped. `confidence` is dropped too, so that the correctness
judgement cannot be anchored on how sure the retrieval model sounded; the
confidence threshold is applied afterwards, by deterministic code, in grade.py.
A post-build assertion re-checks that none of the dropped text appears in the
prompt actually sent.

TEMPERATURE. Rubric section 6 asks for temperature 0. The Claude CLI print mode
used here exposes no temperature flag, so temperature is the service default.
This is recorded verbatim in every run artifact as
`adjudicator_temperature: "not settable via Claude CLI print mode"` rather than
being claimed falsely. The determinism the rubric is buying is supplied instead
by a fixed prompt, a fixed field whitelist and a closed grade vocabulary that is
re-validated in code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import sha256_text  # noqa: E402

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "/home/clawd/.local/bin/claude")
DEFAULT_ADJUDICATOR = "claude-opus-4-7"
TEMPERATURE_NOTE = (
    "not settable via Claude CLI print mode; fixed prompt, fixed field "
    "whitelist and closed grade vocabulary used instead"
)

FORBIDDEN_CLAIM_FIELDS = ("rationale", "alternatives_considered", "confidence")
CLAIM_WHITELIST = (
    "claim_type",
    "document_url",
    "document_id",
    "document_title",
    "issuer",
    "applies_to_attestation",
    "cpt_evidence",
)

ALLOWED_GRADES = {
    "retrievable": ["CORRECT", "CORRECT_STALE", "WRONG_DOCUMENT", "NEEDS_HUMAN_REVIEW"],
    "gated": ["KEY_DEFECT_FOUND", "WRONG_DOCUMENT", "NEEDS_HUMAN_REVIEW"],
    "none": ["KEY_DEFECT_FOUND", "WRONG_DOCUMENT", "NEEDS_HUMAN_REVIEW"],
    "unverified": ["KEY_DEFECT_FOUND", "UNSCOREABLE"],
}

SYSTEM_PROMPT = """You are a strict adjudicator for a health-policy retrieval \
benchmark. You decide document identity, jurisdiction and line-of-business \
applicability, and staleness. You are given the answer key entry, the fetched \
document text, and a claim. You are NOT given the claimant's reasoning and you \
must not speculate about it. Decide only from the evidence in front of you. \
Answer with one strict JSON object and nothing else."""

PROMPT_TEMPLATE = """Adjudicate one benchmark row.

ROW FACTS (from the answer key)
  row_id:     {row_id}
  row_class:  {row_class}
  insurer:    {payer}
  plan type:  {plan_type}
  state:      {state}
  procedure:  CPT {cpt}

ANSWER KEY ENTRY
{key_entry}

THE CLAIM UNDER ADJUDICATION (claimant reasoning withheld by design)
{claim}

DETERMINISTIC FACTS ALREADY ESTABLISHED BY STAGE A (treat as given, do not
re-derive, do not contradict)
{stage_a_facts}

FETCHED TEXT OF THE CLAIMED DOCUMENT (truncated)
<<<
{document_text}
>>>

QUESTION
{question}

RULES
- CPT 27447 never appears on a CMS Local Coverage Determination page. CMS places
  procedure codes in a separate companion Billing and Coding Article. Never
  grade a Medicare answer wrong for the absence of 27447 on an LCD page.
- A different URL serving the SAME document is CORRECT: mirrors, content
  delivery network copies and a plan's own copy of a vendor PDF all count, when
  the policy identifier or the document content matches.
- A document with the same policy identifier and an older effective date is
  CORRECT_STALE, unless the coverage criteria materially changed between
  versions, in which case answer NEEDS_HUMAN_REVIEW.
- WRONG_DOCUMENT means it resolves but is a different document: wrong line of
  business, wrong Medicare contractor jurisdiction, wrong procedure, or a
  different payer.
- If you are not at least 80 percent sure, answer NEEDS_HUMAN_REVIEW.

Allowed grades for this row, and no others: {allowed}

Reply with exactly one JSON object, no prose, no code fence:
{{"grade": "<one of the allowed grades>", "confidence": <integer 0 to 100>,
 "reason": "<one or two sentences>", "quote": "<verbatim quote from the fetched \
text that supports your grade, or null>"}}"""

QUESTIONS = {
    "retrievable": (
        "Is the claimed document the same controlling document as the answer "
        "key entry, or a legitimate mirror, copy or older version of it?"
    ),
    "gated": (
        "The key records this row as having no publicly retrievable policy. Does "
        "the fetched document actually govern this insurer, this plan type and "
        "this state, and address this procedure code? If it genuinely does, the "
        "key is wrong and the grade is KEY_DEFECT_FOUND."
    ),
    "none": (
        "The key records that this plan publishes no such policy. Does the "
        "fetched document actually govern this insurer, this plan type and this "
        "state, and address this procedure code? If it genuinely does, the key "
        "is wrong and the grade is KEY_DEFECT_FOUND."
    ),
    "unverified": (
        "We could not settle whether a public document exists for this row, so "
        "WRONG is unavailable to you on scope grounds. Answer KEY_DEFECT_FOUND "
        "only if the fetched document itself states, in text you can quote, that "
        "it governs this insurer, this plan type and this state. Otherwise "
        "answer UNSCOREABLE."
    ),
    "election": (
        "The claimed Local Coverage Determination is from a Medicare contractor "
        "jurisdiction that does not cover this row's state. Candidate election "
        "language was found. Under 42 CFR 422.101(b)(3) a plan spanning several "
        "contractor jurisdictions may elect one local policy for all enrollees. "
        "Answer CORRECT only if the evidence shows this plan elected THIS "
        "Local Coverage Determination. If it elected a different one, or no "
        "election is shown, answer WRONG_DOCUMENT."
    ),
}


def build_prompt(
    row: dict[str, Any],
    claim: dict[str, Any],
    stage_a_result: dict[str, Any],
    document_text: str,
    question_kind: str,
) -> str:
    safe_claim = {k: claim.get(k) for k in CLAIM_WHITELIST}
    key_entry = {
        k: row.get(k)
        for k in (
            "id",
            "row_class",
            "fetched",
            "attestation_quote",
            "attestation_basis",
            "plan_type_named",
            "ma_deferral_status",
            "ma_convention",
            "notes",
        )
    }
    if isinstance(key_entry.get("fetched"), dict):
        key_entry["fetched"] = {
            k: v for k, v in key_entry["fetched"].items() if k != "text"
        }
    row_class = row["row_class"]
    allowed = ALLOWED_GRADES.get(row_class, ALLOWED_GRADES["retrievable"])
    prompt = PROMPT_TEMPLATE.format(
        row_id=row["id"],
        row_class=row_class,
        payer=row["payer"],
        plan_type=row["plan_type"],
        state=row["state"],
        cpt=row["cpt"],
        key_entry=json.dumps(key_entry, indent=2, ensure_ascii=False)[:6000],
        claim=json.dumps(safe_claim, indent=2, ensure_ascii=False)[:3000],
        stage_a_facts=json.dumps(
            stage_a_result.get("facts", {}), indent=2, ensure_ascii=False
        )[:3000],
        document_text=(document_text or "")[:12000],
        question=QUESTIONS[question_kind],
        allowed=", ".join(allowed),
    )

    # Structural assertion: the retrieval model's reasoning must not be present.
    for f in FORBIDDEN_CLAIM_FIELDS:
        val = claim.get(f)
        if isinstance(val, str) and len(val.strip()) >= 12 and val.strip() in prompt:
            raise AssertionError(
                f"adjudicator prompt for {row['id']} contains the retrieval "
                f"model's {f}; that is prohibited by rubric section 6"
            )
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str) and len(item.strip()) >= 12 and item.strip() in prompt:
                    raise AssertionError(
                        f"adjudicator prompt for {row['id']} contains the "
                        f"retrieval model's {f}; prohibited by rubric section 6"
                    )
    return prompt


def invoke(prompt: str, model: str, timeout: int = 300) -> dict[str, Any]:
    argv = [
        CLAUDE_BIN,
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--tools",
        "",
        "--permission-mode",
        "default",
        "--disable-slash-commands",
        "--system-prompt",
        SYSTEM_PROMPT,
    ]
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, cwd="/tmp"
        )
        envelope = json.loads(proc.stdout)
        return {"ok": not envelope.get("is_error"), "text": envelope.get("result", "")}
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"ok": False, "text": "", "error": str(exc)}


def adjudicate(
    row: dict[str, Any],
    claim: dict[str, Any],
    stage_a_result: dict[str, Any],
    document_text: str,
    model: str = DEFAULT_ADJUDICATOR,
    invoker=None,
) -> dict[str, Any]:
    """Return {grade, confidence, reason, quote, ...} with the vocabulary closed."""
    row_class = row["row_class"]
    facts = stage_a_result.get("facts", {})
    question_kind = row_class
    if facts.get("in_jurisdiction") is False:
        question_kind = "election"
    prompt = build_prompt(row, claim, stage_a_result, document_text, question_kind)
    allowed = ALLOWED_GRADES.get(row_class, ALLOWED_GRADES["retrievable"])

    res = (invoker or invoke)(prompt, model)
    parsed: dict[str, Any] | None = None
    if res.get("ok"):
        from policy_eval.retrieve import extract_json

        parsed = extract_json(res.get("text", ""))

    fallback_reason = None
    if not parsed or parsed.get("grade") not in allowed:
        fallback_reason = (
            "adjudicator returned no usable grade"
            if not parsed
            else f"adjudicator returned out-of-vocabulary grade {parsed.get('grade')!r}"
        )
        # Rubric 4.1 hard prohibition: an unverified row falls back to our own
        # gap, never to WRONG.
        grade = "UNSCOREABLE" if row_class == "unverified" else "NEEDS_HUMAN_REVIEW"
        return {
            "grade": grade,
            "confidence": 0,
            "reason": fallback_reason,
            "quote": None,
            "adjudicator_model": model,
            "adjudicator_temperature": TEMPERATURE_NOTE,
            "prompt_sha256": sha256_text(prompt),
            "question_kind": question_kind,
            "raw": (res.get("text") or "")[:1500],
        }

    conf = parsed.get("confidence")
    try:
        conf = int(conf)
    except (TypeError, ValueError):
        conf = 0
    grade = parsed["grade"]
    if conf < 80 and grade != "NEEDS_HUMAN_REVIEW":
        # Rubric 6: adjudicator confidence below 80 becomes NEEDS_HUMAN_REVIEW,
        # except on unverified rows where WRONG is unavailable anyway.
        if row_class == "unverified":
            grade = "UNSCOREABLE"
            fallback_reason = "adjudicator confidence below 80 on an unverified row"
        else:
            grade = "NEEDS_HUMAN_REVIEW"
            fallback_reason = "adjudicator confidence below 80"
    return {
        "grade": grade,
        "confidence": conf,
        "reason": parsed.get("reason"),
        "quote": parsed.get("quote"),
        "downgrade_reason": fallback_reason,
        "adjudicator_model": model,
        "adjudicator_temperature": TEMPERATURE_NOTE,
        "prompt_sha256": sha256_text(prompt),
        "question_kind": question_kind,
        "claim_fields_shown": list(CLAIM_WHITELIST),
        "claim_fields_withheld": list(FORBIDDEN_CLAIM_FIELDS),
    }
