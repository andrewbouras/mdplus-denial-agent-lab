"""Log every agent run to the shared Google Sheet for human review.

gspread lives in a separate virtual environment from the harness interpreter,
so this module shells out to that interpreter instead of importing gspread.

Logging is best-effort by design. A sheet outage, a revoked key, or a missing
virtual environment must never fail or delay a patient-facing run, so every
failure is swallowed and recorded locally in the arm directory instead.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Any

from .integrity import utc_now, write_json_atomic

WORKSPACE = Path(__file__).resolve().parents[1]
SHEET_SCRIPT = WORKSPACE / "scripts" / "sheet_log.py"
SHEET_PYTHON = Path(
    os.environ.get("MDPLUS_SHEETS_PYTHON", Path.home() / ".venvs/gsheets/bin/python")
).expanduser()
ENABLED = os.environ.get("MDPLUS_RUN_LOG_ENABLED", "1") not in {"0", "false", "no"}


def _first(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return ""


def build_record(
    episode_id: str,
    arm: str,
    episode_root: Path,
    arm_dir: Path,
    outcome: dict[str, Any],
) -> dict[str, Any]:
    """Flatten one finished run into a single reviewable row."""
    result: dict[str, Any] = {}
    result_path = arm_dir / "result.json"
    if result_path.exists():
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result = {}
    meta: dict[str, Any] = {}
    meta_path = arm_dir / "agent_run_meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {}

    case = result.get("case_identification") or {}
    retrieval = result.get("retrieval") or {}
    selected = retrieval.get("selected_source") or {}
    analysis = result.get("policy_analysis") or {}
    interaction = result.get("patient_interaction") or {}
    next_steps = result.get("next_steps") or {}
    confidence = result.get("confidence") or {}
    validation = outcome.get("validation") or {}

    return {
        "logged_at_utc": utc_now(),
        "episode_id": episode_id,
        "arm": arm,
        "revision": outcome.get("revision", 0),
        "engine": _first(outcome.get("engine"), meta.get("engine")),
        "model": meta.get("model", ""),
        "run_status": outcome.get("status", ""),
        "result_status": result.get("status", ""),
        "payer": case.get("payer", ""),
        "plan_name": case.get("plan_name", ""),
        "state": case.get("state", ""),
        "product_type": case.get("product_type", ""),
        "procedure": case.get("procedure", ""),
        "cpt": case.get("cpt", ""),
        "denial_category": analysis.get("denial_category", ""),
        "apparent_reason": analysis.get("apparent_reason", ""),
        "selected_source_title": selected.get("title", ""),
        "selected_source_url": _first(selected.get("url"), selected.get("path")),
        "evidence_role": selected.get("evidence_role", ""),
        "effective_date": selected.get("effective_date", ""),
        "confidence_overall": confidence.get("overall", ""),
        "primary_action": next_steps.get("primary_action", ""),
        "candidate_count": len(retrieval.get("candidates") or []),
        "citation_count": len(retrieval.get("citations") or []),
        "question_count": len(interaction.get("questions") or []),
        "blocker_codes": ", ".join(
            str(b.get("code", "")) for b in (result.get("blockers") or [])
        ),
        "tool_events": meta.get("tool_events", 0),
        "elapsed_s": _first(outcome.get("elapsed_s"), meta.get("elapsed_s")),
        "cost_usd": meta.get("total_cost_usd", ""),
        "validation_valid": validation.get("valid", ""),
        "validation_errors": "; ".join(validation.get("errors") or [])
        or outcome.get("error", ""),
        "episode_path": str(episode_root),
        "reviewer_verdict": "",
        "reviewer_notes": "",
    }


def log_run_sync(record: dict[str, Any], arm_dir: Path) -> dict[str, Any]:
    receipt: dict[str, Any] = {"attempted_at": utc_now(), "ok": False}
    try:
        if not ENABLED:
            receipt["error"] = "run logging disabled by MDPLUS_RUN_LOG_ENABLED"
        elif not SHEET_PYTHON.exists():
            receipt["error"] = f"sheets interpreter not found: {SHEET_PYTHON}"
        else:
            proc = subprocess.run(
                [str(SHEET_PYTHON), str(SHEET_SCRIPT)],
                input=json.dumps(record, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=120,
            )
            if proc.returncode == 0:
                receipt["ok"] = True
                receipt["stdout"] = proc.stdout.strip()[:2000]
            else:
                receipt["error"] = (proc.stderr or proc.stdout).strip()[:2000]
    except Exception as exc:  # never let logging break a run
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    receipt["record"] = record
    try:
        write_json_atomic(arm_dir / "run_log_receipt.json", receipt)
    except Exception:
        pass
    return receipt


def log_run_async(record: dict[str, Any], arm_dir: Path) -> None:
    threading.Thread(
        target=log_run_sync, args=(record, arm_dir), daemon=True
    ).start()
