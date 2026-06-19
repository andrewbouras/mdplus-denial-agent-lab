"""Arm-result validation, archival, event ingestion, and freezing."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .arms import result_contract
from .episode import Episode
from .integrity import read_jsonl, sha256_file, utc_now, write_json_atomic


def validate_arm_result(result: dict[str, Any], episode: Episode, arm: str) -> list[str]:
    errors: list[str] = []
    contract = result_contract()
    for field in contract["required_top_level_fields"]:
        if field not in result:
            errors.append(f"missing top-level field: {field}")
    if result.get("episode_id") != episode.episode_id:
        errors.append("episode_id mismatch")
    if result.get("arm") != arm:
        errors.append("arm mismatch")
    if result.get("status") not in contract["status_values"]:
        errors.append(f"invalid status: {result.get('status')!r}")

    retrieval = result.get("retrieval")
    if isinstance(retrieval, dict):
        if not isinstance(retrieval.get("candidates"), list):
            errors.append("retrieval.candidates must be a list")
        if not isinstance(retrieval.get("citations"), list):
            errors.append("retrieval.citations must be a list")
    elif "retrieval" in result:
        errors.append("retrieval must be an object")

    interaction = result.get("patient_interaction")
    if isinstance(interaction, dict):
        if not isinstance(interaction.get("questions"), list):
            errors.append("patient_interaction.questions must be a list")
        if not isinstance(interaction.get("provider_records_needed"), list):
            errors.append("patient_interaction.provider_records_needed must be a list")
    elif "patient_interaction" in result:
        errors.append("patient_interaction must be an object")

    if result.get("status") == "needs_patient_follow_up":
        questions = interaction.get("questions", []) if isinstance(interaction, dict) else []
        if not questions:
            errors.append("follow-up status requires at least one patient question")
    if result.get("status") == "actionable_result":
        selected = retrieval.get("selected_source") if isinstance(retrieval, dict) else None
        if not selected:
            errors.append("actionable result requires a selected source")
        elif selected.get("evidence_role") != "governing_policy":
            errors.append(
                "actionable result requires selected_source.evidence_role=governing_policy"
            )
        next_steps = result.get("next_steps")
        if not isinstance(next_steps, dict) or not next_steps.get("primary_action"):
            errors.append("actionable result requires next_steps.primary_action")
    if result.get("status") == "blocked" and not result.get("blockers"):
        errors.append("blocked result requires blocker details")
    return errors


def ingest_agent_events(episode: Episode, arm: str, path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    role = "library_agent" if arm == "library_only" else "web_agent"
    for row in read_jsonl(path):
        episode.log_event(
            role=role,
            arm=arm,
            event_type=str(row.get("event_type", "agent_observation")),
            status=str(row.get("status", "recorded")),
            summary=str(row.get("summary", "Agent event imported.")),
            artifacts=[str(item) for item in row.get("artifacts", [])],
            parent_event_id=row.get("parent_event_id"),
            details={
                key: value
                for key, value in row.items()
                if key not in {"event_type", "status", "summary", "artifacts", "parent_event_id"}
            },
        )
        count += 1
    return count


def ingest_arm_result(
    episode: Episode,
    arm: str,
    run_dir: Path | None = None,
) -> dict[str, Any]:
    arm_root = episode.root / "system" / arm
    arm_dir = run_dir.resolve() if run_dir else arm_root
    source_path = arm_dir / "result.json"
    if not source_path.exists():
        raise FileNotFoundError(f"arm has not produced result.json: {source_path}")
    result = json.loads(source_path.read_text(encoding="utf-8"))
    errors = validate_arm_result(result, episode, arm)

    attempts_dir = arm_dir / "attempts"
    attempts_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    attempt_number = len(list(attempts_dir.glob("result_*.json"))) + 1
    archived_path = attempts_dir / f"result_{attempt_number:03d}.json"
    shutil.copy2(source_path, archived_path)
    archived_path.chmod(0o600)
    imported_events = ingest_agent_events(episode, arm, arm_dir / "agent_events.jsonl")

    validation = {
        "schema_version": "1.0",
        "episode_id": episode.episode_id,
        "arm": arm,
        "attempt": attempt_number,
        "validated_at": utc_now(),
        "valid": not errors,
        "errors": errors,
        "result_sha256": sha256_file(archived_path),
        "imported_agent_events": imported_events,
    }
    validation_path = attempts_dir / f"validation_{attempt_number:03d}.json"
    write_json_atomic(validation_path, validation)
    episode.log_event(
        role="orchestrator",
        arm=arm,
        event_type="arm_result_validated",
        status="succeeded" if not errors else "failed",
        summary=(
            f"Validated {arm} result attempt {attempt_number}."
            if not errors
            else f"Rejected {arm} result attempt {attempt_number}: {'; '.join(errors)}"
        ),
        artifacts=[
            str(archived_path.relative_to(episode.root)),
            str(validation_path.relative_to(episode.root)),
        ],
        details={
            "attempt": attempt_number,
            "result_status": result.get("status"),
            "result_sha256": validation["result_sha256"],
            "error_count": len(errors),
        },
    )
    if errors:
        return validation

    validation["frozen"] = False
    if result["status"] in {"actionable_result", "blocked"}:
        frozen_path = arm_dir / "frozen_result.json"
        if frozen_path.exists():
            raise FileExistsError(f"{arm} result is already frozen")
        shutil.copy2(archived_path, frozen_path)
        frozen_path.chmod(0o400)
        freeze_manifest = {
            "schema_version": "1.0",
            "episode_id": episode.episode_id,
            "arm": arm,
            "frozen_at": utc_now(),
            "result_status": result["status"],
            "result_sha256": sha256_file(frozen_path),
            "source_attempt": attempt_number,
        }
        freeze_path = arm_dir / "freeze_manifest.json"
        write_json_atomic(freeze_path, freeze_manifest, mode=0o400)
        validation["frozen"] = True
        validation["freeze_manifest"] = str(freeze_path)
        episode.log_event(
            role="orchestrator",
            arm=arm,
            event_type="arm_result_frozen",
            status="succeeded",
            summary=f"Froze terminal {arm} result before evaluation.",
            artifacts=[
                str(frozen_path.relative_to(episode.root)),
                str(freeze_path.relative_to(episode.root)),
            ],
            details={"result_sha256": freeze_manifest["result_sha256"]},
        )
        active_result = arm_root / "active_result.json"
        active_manifest = arm_root / "active_manifest.json"
        if active_result.exists():
            active_result.chmod(0o600)
        shutil.copy2(frozen_path, active_result)
        active_result.chmod(0o400)
        active = {
            "schema_version": "1.0",
            "episode_id": episode.episode_id,
            "arm": arm,
            "activated_at": utc_now(),
            "result_sha256": sha256_file(active_result),
            "run_directory": str(arm_dir.relative_to(episode.root)),
            "source_attempt": attempt_number,
        }
        write_json_atomic(active_manifest, active)
        episode.log_event(
            role="orchestrator",
            arm=arm,
            event_type="arm_result_activated",
            status="succeeded",
            summary=f"Activated the newest validated {arm} result.",
            artifacts=[
                str(active_result.relative_to(episode.root)),
                str(active_manifest.relative_to(episode.root)),
            ],
            details={
                "result_sha256": active["result_sha256"],
                "run_directory": active["run_directory"],
            },
        )
    else:
        validation["questions"] = result["patient_interaction"]["questions"]
    return validation


def both_arms_frozen(episode: Episode) -> bool:
    for arm in ("library_only", "web_only"):
        freeze_path = episode.root / "system" / arm / "freeze_manifest.json"
        result_path = episode.root / "system" / arm / "frozen_result.json"
        if not freeze_path.exists() or not result_path.exists():
            return False
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        if freeze.get("result_sha256") != sha256_file(result_path):
            return False
    return True
