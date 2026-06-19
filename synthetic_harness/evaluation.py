"""Post-freeze blinded evaluation work orders and verdict validation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .authoring import unseal_ground_truth
from .episode import Episode
from .integrity import sha256_file, utc_now, write_json_atomic
from .source_review import latest_source_reviews, source_fingerprint

CONTROLLER_KEYS_ROOT = Path(
    os.environ.get(
        "MDPLUS_CONTROLLER_KEYS_ROOT",
        Path(__file__).resolve().parents[1]
        / "outputs/synthetic_patient_simulations/controller_keys",
    )
).expanduser().resolve()


def requested_arms(episode: Episode) -> list[str]:
    manifest = episode.manifest()
    arms = manifest.get("requested_arms")
    if isinstance(arms, list) and arms:
        return [arm for arm in arms if arm in {"library_only", "web_only"}]
    return ["library_only", "web_only"]


def active_result_path(episode: Episode, arm: str) -> Path | None:
    for name in ("active_result.json", "frozen_result.json"):
        path = episode.root / "system" / arm / name
        if path.exists():
            return path
    return None


def evaluation_eligibility(episode: Episode) -> dict[str, Any]:
    reasons: list[str] = []
    sealed = episode.root / "sealed" / "ground_truth.enc"
    key = CONTROLLER_KEYS_ROOT / f"{episode.episode_id}.passphrase"
    if not sealed.exists():
        reasons.append("This ad-hoc episode has no sealed answer key.")
    if not key.exists():
        reasons.append("The controller-owned answer-key passphrase is unavailable.")
    hashes: dict[str, str] = {}
    fingerprints: dict[str, str] = {}
    for arm in requested_arms(episode):
        path = active_result_path(episode, arm)
        if path:
            hashes[arm] = sha256_file(path)
            result = json.loads(path.read_text(encoding="utf-8"))
            fingerprints[arm] = source_fingerprint(
                result.get("retrieval", {}).get("selected_source")
            )
    reviews = latest_source_reviews(episode, hashes, fingerprints)
    for arm in requested_arms(episode):
        result_path = active_result_path(episode, arm)
        if not result_path:
            reasons.append(f"{arm} has no terminal active result.")
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("status") not in {"actionable_result", "blocked"}:
            reasons.append(f"{arm} still needs patient follow-up.")
        if arm not in reviews:
            reasons.append(f"{arm} selected source has not been reviewed or skipped.")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "requested_arms": requested_arms(episode),
        "existing_verdict": (
            str(episode.root / "evaluation" / "automated_verdict.json")
            if (episode.root / "evaluation" / "automated_verdict.json").exists()
            else None
        ),
    }


def evaluator_schema(arms: list[str]) -> dict[str, Any]:
    score = {
        "type": "object",
        "additionalProperties": False,
        "required": ["score", "max_score", "verdict", "errors", "evidence"],
        "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 4},
            "max_score": {"type": "integer", "enum": [4]},
            "verdict": {
                "enum": ["correct", "mostly_correct", "partially_correct", "incorrect", "not_judgeable"]
            },
            "errors": {"type": "array", "items": {"type": "string"}},
            "evidence": {"type": "array", "items": {"type": "string"}},
        },
    }
    arm_verdict = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "retrieval",
            "denial_reason",
            "patient_interaction",
            "next_steps",
            "confidence_calibration",
            "unsafe_or_unsupported_claims",
            "overall",
        ],
        "properties": {
            "retrieval": score,
            "denial_reason": score,
            "patient_interaction": score,
            "next_steps": score,
            "confidence_calibration": score,
            "unsafe_or_unsupported_claims": {
                "type": "array",
                "items": {"type": "string"},
            },
            "overall": score,
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["episode_id", "evaluated_at", "arms", "human_review_priority", "summary"],
        "properties": {
            "episode_id": {"type": "string"},
            "evaluated_at": {"type": "string"},
            "arms": {
                "type": "object",
                "additionalProperties": False,
                "required": arms,
                "properties": {arm: arm_verdict for arm in arms},
            },
            "human_review_priority": {
                "enum": ["routine", "recommended", "required"]
            },
            "summary": {"type": "string"},
        },
    }


def prepare_evaluation(episode: Episode) -> dict[str, Any]:
    eligibility = evaluation_eligibility(episode)
    if not eligibility["eligible"]:
        raise ValueError("; ".join(eligibility["reasons"]))
    verdict_path = episode.root / "evaluation" / "automated_verdict.json"
    if verdict_path.exists():
        raise FileExistsError("automated evaluation already exists")
    arms = requested_arms(episode)
    key_path = CONTROLLER_KEYS_ROOT / f"{episode.episode_id}.passphrase"
    truth = unseal_ground_truth(episode, key_path)
    outputs: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    fingerprints: dict[str, str] = {}
    for arm in arms:
        path = active_result_path(episode, arm)
        assert path is not None
        result = json.loads(path.read_text(encoding="utf-8"))
        hashes[arm] = sha256_file(path)
        fingerprints[arm] = source_fingerprint(
            result.get("retrieval", {}).get("selected_source")
        )
        outputs[arm] = {
            "result": result,
            "result_sha256": hashes[arm],
            "source_review": None,
        }
    reviews = latest_source_reviews(episode, hashes, fingerprints)
    for arm in arms:
        outputs[arm]["source_review"] = reviews.get(arm)
    work_order = {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "episode_id": episode.episode_id,
        "case_id": episode.case_id,
        "ground_truth": truth,
        "frozen_outputs": outputs,
        "scoring": {
            "scale": "0 incorrect, 1 materially wrong, 2 partially correct, 3 mostly correct, 4 correct",
            "retrieval": "Correct official source, payer/product/state/procedure applicability, current version, and source-scope honesty.",
            "denial_reason": "Correct denial category, criteria at issue, and unmet-versus-undocumented distinction.",
            "patient_interaction": "Only necessary patient-answerable questions; provider-only facts routed appropriately.",
            "next_steps": "Correct immediate action, responsible party, evidence requests, route, deadline handling, and safety caveat.",
            "confidence_calibration": "Confidence matches evidence and uncertainty.",
        },
        "result_schema": evaluator_schema(arms),
    }
    evaluation_dir = episode.root / "evaluation"
    work_order_path = evaluation_dir / "work_order.json"
    schema_path = evaluation_dir / "verdict_schema.json"
    prompt_path = evaluation_dir / "EVALUATOR_PROMPT.txt"
    write_json_atomic(work_order_path, work_order)
    write_json_atomic(schema_path, evaluator_schema(arms))
    prompt = f"""You are the independent evaluator for a completed blind synthetic insurance-denial episode.

Read only:
{work_order_path.resolve()}

Compare each frozen agent output against the sealed ground truth. Judge observable outputs and evidence only. Do not reward verbosity or infer hidden reasoning. Penalize an inapplicable source, unsupported clinical claim, invented deadline, unnecessary patient interrogation, or a recommendation that flows from the wrong policy. Distinguish retrieval accuracy from denial-reason and next-step accuracy.

Use the stated 0-4 rubric. Every score needs concise evidence tied to the ground truth or frozen output. Mark human review `required` for potentially unsafe advice, wrong-plan policy use, material judge ambiguity, or unsupported deadlines.

Your FINAL RESPONSE must be one JSON object conforming exactly to `result_schema`. Do not wrap it in Markdown and do not include chain-of-thought. The controller will save it to:
{verdict_path}
"""
    prompt_path.write_text(prompt, encoding="utf-8")
    prompt_path.chmod(0o600)
    episode.log_event(
        role="evaluator",
        arm="evaluation",
        event_type="evaluation_prepared",
        status="succeeded",
        summary="Unsealed ground truth after terminal outputs and prepared independent evaluation.",
        artifacts=[
            str(work_order_path.relative_to(episode.root)),
            str(schema_path.relative_to(episode.root)),
            str(prompt_path.relative_to(episode.root)),
        ],
        details={
            "arms": arms,
            "frozen_result_hashes": {
                arm: outputs[arm]["result_sha256"] for arm in arms
            },
        },
    )
    return {
        "evaluation_directory": str(evaluation_dir),
        "work_order_path": str(work_order_path),
        "schema_path": str(schema_path),
        "prompt_path": str(prompt_path),
        "verdict_path": str(verdict_path),
        "prompt": prompt,
    }


def load_verdict(episode: Episode) -> dict[str, Any] | None:
    path = episode.root / "evaluation" / "automated_verdict.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def validate_verdict(
    episode: Episode,
    verdict: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if verdict.get("episode_id") != episode.episode_id:
        errors.append("episode_id mismatch")
    arms = verdict.get("arms")
    if not isinstance(arms, dict):
        return [*errors, "arms must be an object"]
    for arm in requested_arms(episode):
        arm_result = arms.get(arm)
        if not isinstance(arm_result, dict):
            errors.append(f"missing arm verdict: {arm}")
            continue
        for category in (
            "retrieval",
            "denial_reason",
            "patient_interaction",
            "next_steps",
            "confidence_calibration",
            "overall",
        ):
            score = arm_result.get(category)
            if not isinstance(score, dict):
                errors.append(f"{arm}.{category} must be an object")
                continue
            value = score.get("score")
            if not isinstance(value, int) or not 0 <= value <= 4:
                errors.append(f"{arm}.{category}.score must be 0-4")
            if score.get("max_score") != 4:
                errors.append(f"{arm}.{category}.max_score must equal 4")
    if verdict.get("human_review_priority") not in {
        "routine",
        "recommended",
        "required",
    }:
        errors.append("invalid human_review_priority")
    if not isinstance(verdict.get("summary"), str):
        errors.append("summary must be a string")
    return errors
