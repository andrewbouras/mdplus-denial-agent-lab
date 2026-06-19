"""Claude patient-actor prompt and copy/paste relay protocol."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .episode import Episode
from .integrity import sha256_file, write_json_atomic

RESPONSE_HEADER = "PATIENT_ACTOR_RESPONSE"
RESPONSE_FOOTER = "END_PATIENT_ACTOR_RESPONSE"


def role_prompt(episode: Episode) -> str:
    workspace = episode.root / "patient_workspace"
    return f"""You are the Synthetic Patient Actor for one internal orthopedic insurance-denial simulation.

You do not know the surrounding project. That is intentional. Your only role is to embody the patient described in your assigned packet while another system attempts to help you.

AUTHORIZED WORKSPACE
You may access only this directory:
{workspace}

Do not inspect its parent directory, sibling directories, repository files, insurance-policy libraries, web sources, or prior simulation episodes.

IDENTITY
- Episode ID: {episode.episode_id}
- Case ID: {episode.case_id}
- Role: patient_actor

BEHAVIOR RULES
1. Read only `patient_packet.json` and messages placed in `inbox/`.
2. Use only facts in the patient packet or facts communicated to you during this episode.
3. Never browse the web, research the payer, retrieve a policy, or try to solve or score the case.
4. Do not infer hidden medical facts. Do not turn uncertainty into a confident answer.
5. Behave like a cooperative ordinary patient, not a policy expert:
   - remember major events more readily than exact dates or clinical wording;
   - answer only what was asked;
   - say when you are unsure or do not possess a record;
   - distinguish personal recollection from what a clinician's chart may contain.
6. Do not invent treatment duration, imaging findings, diagnoses, deadlines, conversations, records, or insurer statements.
7. If asked for something only a clinician, insurer, or medical record could establish, say so naturally.
8. Never reveal or seek ground truth, expected answers, evaluator material, source IDs, canonical policy language, or scoring criteria.
9. Keep the episode and case IDs exactly as supplied.
10. Remain in role until an inbox message says `END PATIENT EPISODE`.

RESPONSE FORMAT
For every inbox message, return exactly one block:

{RESPONSE_HEADER}
episode_id: {episode.episode_id}
case_id: {episode.case_id}
in_reply_to: <copy the inbox message_id exactly>
body:
<your patient response; no analysis, policy research, or out-of-character commentary>
{RESPONSE_FOOTER}

Do not add text before or after the block.

INITIALIZATION
Read the patient packet now, but do not disclose its contents until asked by an inbox message.
Then respond with exactly:

PATIENT_ACTOR_READY
episode_id: {episode.episode_id}
case_id: {episode.case_id}
"""


def initial_intake_body() -> str:
    return """BEGIN PATIENT EPISODE

Please submit the information you would realistically provide when starting help with an orthopedic insurance denial.

Include:
1. The denial letter or the exact text visible in it.
2. The insurance-card details you can see: payer name, plan name, state, and any visible product clue such as PPO.
3. The procedure or test you believe was requested.
4. The treating surgeon or practice, if you know it.
5. Any appeal deadline explicitly printed in the denial letter.

Do not research anything. If a requested detail is unavailable in your packet, say that you do not know or do not have it."""


def prepare_patient_actor(episode: Episode) -> dict[str, Any]:
    packet_path = episode.root / "patient_workspace" / "patient_packet.json"
    if not packet_path.exists():
        raise FileNotFoundError("patient packet must be authored before preparing the actor")
    prompt_path = episode.root / "patient_workspace" / "CLAUDE_ROLE_PROMPT.txt"
    prompt_path.write_text(role_prompt(episode), encoding="utf-8")
    prompt_path.chmod(0o600)
    start = episode.create_message(
        sender="orchestrator",
        recipient="patient_actor",
        body=initial_intake_body(),
        message_type="episode_start",
    )
    start_path = next(
        path
        for path in (episode.root / "patient_workspace" / "inbox").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8"))["message_id"] == start["message_id"]
    )
    episode._update_manifest(
        status="patient_actor_prepared",
        active_patient_request_id=start["message_id"],
        patient_role_prompt_sha256=sha256_file(prompt_path),
    )
    episode.log_event(
        role="orchestrator",
        arm="shared",
        event_type="patient_actor_prepared",
        status="succeeded",
        summary="Created the episode-specific Claude role prompt and initial patient intake request.",
        artifacts=[
            "patient_workspace/CLAUDE_ROLE_PROMPT.txt",
            str(start_path.relative_to(episode.root)),
        ],
        details={"active_patient_request_id": start["message_id"]},
    )
    return {
        "episode_id": episode.episode_id,
        "case_id": episode.case_id,
        "patient_workspace": str(episode.root / "patient_workspace"),
        "role_prompt_path": str(prompt_path),
        "initial_message_path": str(start_path),
        "initial_message_id": start["message_id"],
        "copy_paste_prompt": prompt_path.read_text(encoding="utf-8"),
    }


def parse_patient_response(text: str) -> dict[str, str]:
    stripped = text.strip()
    pattern = re.compile(
        rf"^{RESPONSE_HEADER}\n"
        r"episode_id:\s*(?P<episode_id>[^\n]+)\n"
        r"case_id:\s*(?P<case_id>[^\n]+)\n"
        r"in_reply_to:\s*(?P<in_reply_to>[^\n]+)\n"
        r"body:\n(?P<body>.*?)\n"
        rf"{RESPONSE_FOOTER}$",
        re.DOTALL,
    )
    match = pattern.match(stripped)
    if not match:
        raise ValueError("response does not match the required patient-actor envelope")
    return {key: value.strip() for key, value in match.groupdict().items()}


def record_patient_response(episode: Episode, response_text: str) -> dict[str, Any]:
    parsed = parse_patient_response(response_text)
    manifest = episode.manifest()
    if parsed["episode_id"] != episode.episode_id:
        raise ValueError("patient response episode_id mismatch")
    if parsed["case_id"] != episode.case_id:
        raise ValueError("patient response case_id mismatch")
    expected_reply = manifest.get("active_patient_request_id")
    if parsed["in_reply_to"] != expected_reply:
        raise ValueError(
            f"patient response replies to {parsed['in_reply_to']}, expected {expected_reply}"
        )

    envelope = episode.create_message(
        sender="patient_actor",
        recipient="orchestrator",
        body=parsed["body"],
        message_type="patient_response",
        in_reply_to=parsed["in_reply_to"],
    )
    raw_path = (
        episode.root
        / "patient_workspace"
        / "outbox"
        / f"raw_relay_{envelope['sequence']:04d}_{envelope['message_id']}.txt"
    )
    raw_path.write_text(response_text.strip() + "\n", encoding="utf-8")
    raw_path.chmod(0o600)
    episode._update_manifest(
        active_patient_request_id=None,
        last_patient_response_id=envelope["message_id"],
    )
    episode.log_event(
        role="orchestrator",
        arm="shared",
        event_type="patient_response_ingested",
        status="succeeded",
        summary="Validated and recorded a user-relayed Claude patient response.",
        artifacts=[str(raw_path.relative_to(episode.root))],
        details={
            "message_id": envelope["message_id"],
            "in_reply_to": envelope["in_reply_to"],
        },
    )
    return envelope


def create_follow_up(episode: Episode, body: str) -> dict[str, Any]:
    manifest = episode.manifest()
    if manifest.get("active_patient_request_id"):
        raise ValueError("an unanswered patient request is already active")
    last_response = manifest.get("last_patient_response_id")
    if not last_response:
        raise ValueError("initial patient response has not been recorded")
    envelope = episode.create_message(
        sender="orchestrator",
        recipient="patient_actor",
        body=body,
        message_type="follow_up_question",
        in_reply_to=last_response,
    )
    episode._update_manifest(active_patient_request_id=envelope["message_id"])
    return envelope


def relay_block(envelope: dict[str, Any]) -> str:
    return f"""TO CLAUDE
episode_id: {envelope['episode_id']}
case_id: {envelope['case_id']}
message_id: {envelope['message_id']}
sequence: {envelope['sequence']}
body:
{envelope['body']}
END TO CLAUDE"""
