"""Aggregate retrieval and benchmark accuracy from immutable episode artifacts."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .integrity import read_jsonl


def build_metrics(episodes_root: Path) -> dict[str, Any]:
    decisions: dict[str, Counter[str]] = {
        "library_only": Counter(),
        "web_only": Counter(),
    }
    episodes = 0
    evaluated = 0
    score_totals: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for episode_dir in sorted(episodes_root.glob("ep_*")):
        if not (episode_dir / "manifest.json").exists():
            continue
        manifest = json.loads(
            (episode_dir / "manifest.json").read_text(encoding="utf-8")
        )
        if manifest.get("exclude_from_metrics"):
            continue
        episodes += 1
        feedback_path = episode_dir / "review" / "source_feedback.jsonl"
        if feedback_path.exists():
            for row in read_jsonl(feedback_path):
                arm = row.get("arm")
                decision = row.get("decision")
                if arm in decisions and decision:
                    decisions[arm][decision] += 1
        verdict_path = episode_dir / "evaluation" / "automated_verdict.json"
        if verdict_path.exists():
            evaluated += 1
            verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
            for arm, arm_verdict in verdict.get("arms", {}).items():
                for category in (
                    "retrieval",
                    "denial_reason",
                    "patient_interaction",
                    "next_steps",
                    "confidence_calibration",
                    "overall",
                ):
                    score = arm_verdict.get(category, {}).get("score")
                    if isinstance(score, int):
                        score_totals[arm][category].append(score)
    arm_metrics: dict[str, Any] = {}
    for arm, counts in decisions.items():
        judged = (
            counts["confirmed"]
            + counts["rejected"]
            + counts["replaced"]
        )
        arm_metrics[arm] = {
            "decisions": dict(counts),
            "judged_source_selections": judged,
            "confirmed_accuracy": (
                counts["confirmed"] / judged if judged else None
            ),
            "replacement_or_rejection_rate": (
                (counts["rejected"] + counts["replaced"]) / judged
                if judged
                else None
            ),
            "average_scores": {
                category: round(sum(values) / len(values), 2)
                for category, values in score_totals.get(arm, {}).items()
                if values
            },
        }
    return {
        "episodes": episodes,
        "evaluated_episodes": evaluated,
        "arms": arm_metrics,
        "method": {
            "source_accuracy_denominator": "confirmed + rejected + replaced; skips excluded",
            "automated_scores": "mean score on 0-4 scale for episodes with sealed truth",
        },
    }
