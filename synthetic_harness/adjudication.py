"""Human adjudication of automated benchmark verdicts."""

from __future__ import annotations

import json
from typing import Any

from .episode import Episode
from .integrity import HashChainLog, sha256_file

VALID_DECISIONS = {"confirmed", "corrected", "expert_review_required"}


def record_adjudication(
    *,
    episode: Episode,
    decision: str,
    notes: str,
    corrections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if decision not in VALID_DECISIONS:
        raise ValueError("invalid adjudication decision")
    verdict_path = episode.root / "evaluation" / "automated_verdict.json"
    if not verdict_path.exists():
        raise ValueError("automated verdict does not exist")
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    record = HashChainLog(
        episode.root / "evaluation" / "human_adjudication.jsonl"
    ).append(
        {
            "episode_id": episode.episode_id,
            "case_id": episode.case_id,
            "decision": decision,
            "notes": notes.strip(),
            "corrections": corrections or {},
            "automated_verdict_sha256": sha256_file(verdict_path),
            "automated_human_review_priority": verdict.get(
                "human_review_priority"
            ),
        }
    )
    episode.log_event(
        role="human_reviewer",
        arm="evaluation",
        event_type="automated_verdict_adjudicated",
        status="succeeded",
        summary={
            "confirmed": "Human reviewer confirmed the automated benchmark verdict.",
            "corrected": "Human reviewer corrected the automated benchmark verdict.",
            "expert_review_required": "Human reviewer escalated the benchmark verdict for expert review.",
        }[decision],
        details={
            "decision": decision,
            "adjudication_record_hash": record["record_hash"],
        },
    )
    return record


def latest_adjudication(episode: Episode) -> dict[str, Any] | None:
    path = episode.root / "evaluation" / "human_adjudication.jsonl"
    if not path.exists():
        return None
    from .integrity import read_jsonl

    rows = read_jsonl(path)
    return rows[-1] if rows else None
