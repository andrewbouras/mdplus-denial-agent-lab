"""Episode lifecycle, role isolation, and message-envelope handling."""

from __future__ import annotations

import re
import secrets
import uuid
from pathlib import Path
from typing import Any

from .integrity import HashChainLog, canonical_json, sha256_text, utc_now, write_json_atomic

EPISODE_PREFIX = "ep"
CASE_PREFIX = "case"
VALID_ROLES = {"case_author", "patient_actor", "orchestrator", "library_agent", "web_agent", "evaluator", "human_reviewer"}
VALID_ARMS = {"shared", "library_only", "web_only", "evaluation"}


def opaque_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def safe_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-")
    if not cleaned:
        raise ValueError("identifier cannot be empty")
    return cleaned


class Episode:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.manifest_path = self.root / "manifest.json"
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"not an episode: {self.root}")

    @classmethod
    def create(cls, episodes_root: Path, label: str | None = None) -> "Episode":
        episode_id = opaque_id(EPISODE_PREFIX)
        case_id = opaque_id(CASE_PREFIX)
        root = episodes_root.resolve() / episode_id
        root.mkdir(parents=True, exist_ok=False, mode=0o700)

        directories = [
            "patient_workspace/inbox",
            "patient_workspace/outbox",
            "patient_workspace/logs",
            "system/shared",
            "system/library_only",
            "system/web_only",
            "system/logs",
            "sealed",
            "evaluation",
            "review",
        ]
        for directory in directories:
            path = root / directory
            path.mkdir(parents=True, exist_ok=False, mode=0o700)
            path.chmod(0o700)

        relay_secret = secrets.token_hex(32)
        manifest = {
            "schema_version": "1.0",
            "episode_id": episode_id,
            "case_id": case_id,
            "label": label or "",
            "created_at": utc_now(),
            "status": "initialized",
            "active_message_sequence": 0,
            "roles": sorted(VALID_ROLES),
            "arms": sorted(VALID_ARMS),
            "patient_workspace": "patient_workspace",
            "sealed_workspace": "sealed",
        }
        write_json_atomic(root / "manifest.json", manifest)
        write_json_atomic(
            root / "sealed" / "relay_integrity.json",
            {"relay_secret": relay_secret, "created_at": utc_now()},
        )

        episode = cls(root)
        episode.log_event(
            role="orchestrator",
            arm="shared",
            event_type="episode_initialized",
            status="succeeded",
            summary="Created isolated role workspaces and append-only logs.",
            artifacts=["manifest.json"],
        )
        return episode

    def manifest(self) -> dict[str, Any]:
        import json

        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    @property
    def episode_id(self) -> str:
        return self.manifest()["episode_id"]

    @property
    def case_id(self) -> str:
        return self.manifest()["case_id"]

    def _update_manifest(self, **updates: Any) -> dict[str, Any]:
        manifest = self.manifest()
        manifest.update(updates)
        write_json_atomic(self.manifest_path, manifest)
        return manifest

    def _event_log_path(self, arm: str) -> Path:
        if arm not in VALID_ARMS:
            raise ValueError(f"invalid arm: {arm}")
        return self.root / "system" / "logs" / f"{arm}.events.jsonl"

    def log_event(
        self,
        *,
        role: str,
        arm: str,
        event_type: str,
        status: str,
        summary: str,
        artifacts: list[str] | None = None,
        parent_event_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if role not in VALID_ROLES:
            raise ValueError(f"invalid role: {role}")
        event_id = opaque_id("evt")
        return HashChainLog(self._event_log_path(arm)).append(
            {
                "event_id": event_id,
                "episode_id": self.episode_id,
                "case_id": self.case_id,
                "role": role,
                "arm": arm,
                "event_type": event_type,
                "status": status,
                "summary": summary,
                "artifacts": artifacts or [],
                "parent_event_id": parent_event_id,
                "details": details or {},
            }
        )

    def _message_log_path(self) -> Path:
        return self.root / "patient_workspace" / "logs" / "messages.jsonl"

    def create_message(
        self,
        *,
        sender: str,
        recipient: str,
        body: str,
        message_type: str = "conversation",
        in_reply_to: str | None = None,
    ) -> dict[str, Any]:
        if sender not in VALID_ROLES or recipient not in VALID_ROLES:
            raise ValueError("invalid sender or recipient")
        manifest = self.manifest()
        sequence = int(manifest["active_message_sequence"]) + 1
        message_id = opaque_id("msg")
        body_hash = sha256_text(body)
        envelope_without_hash = {
            "schema_version": "1.0",
            "episode_id": self.episode_id,
            "case_id": self.case_id,
            "message_id": message_id,
            "sequence": sequence,
            "sender": sender,
            "recipient": recipient,
            "message_type": message_type,
            "in_reply_to": in_reply_to,
            "created_at": utc_now(),
            "body": body,
            "body_sha256": body_hash,
        }
        envelope_hash = sha256_text(canonical_json(envelope_without_hash))
        envelope = {**envelope_without_hash, "envelope_sha256": envelope_hash}

        directory = "outbox" if sender == "patient_actor" else "inbox"
        relative_path = Path("patient_workspace") / directory / f"{sequence:04d}_{message_id}.json"
        write_json_atomic(self.root / relative_path, envelope)
        HashChainLog(self._message_log_path()).append(
            {
                "episode_id": self.episode_id,
                "case_id": self.case_id,
                "message_id": message_id,
                "message_sequence": sequence,
                "sender": sender,
                "recipient": recipient,
                "message_type": message_type,
                "in_reply_to": in_reply_to,
                "body_sha256": body_hash,
                "envelope_sha256": envelope_hash,
                "envelope_path": str(relative_path),
            }
        )
        self._update_manifest(active_message_sequence=sequence)
        self.log_event(
            role="orchestrator",
            arm="shared",
            event_type="message_recorded",
            status="succeeded",
            summary=f"Recorded message {sequence} from {sender} to {recipient}.",
            artifacts=[str(relative_path)],
            details={"message_id": message_id, "body_sha256": body_hash},
        )
        return envelope

    def verify(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        log_paths = [
            self._message_log_path(),
            *sorted((self.root / "system" / "logs").glob("*.jsonl")),
            *sorted((self.root / "review").glob("*.jsonl")),
            *sorted((self.root / "evaluation").glob("*.jsonl")),
        ]
        for path in log_paths:
            if path.exists():
                checks.append(HashChainLog(path).verify())

        message_errors: list[str] = []
        import json

        for path in sorted((self.root / "patient_workspace").glob("*/*.json")):
            envelope = json.loads(path.read_text(encoding="utf-8"))
            body = envelope.get("body", "")
            if envelope.get("body_sha256") != sha256_text(body):
                message_errors.append(f"{path}: body hash mismatch")
            supplied_hash = envelope.get("envelope_sha256")
            without_hash = {key: value for key, value in envelope.items() if key != "envelope_sha256"}
            if supplied_hash != sha256_text(canonical_json(without_hash)):
                message_errors.append(f"{path}: envelope hash mismatch")

        valid = all(check["valid"] for check in checks) and not message_errors
        return {
            "episode_id": self.episode_id,
            "valid": valid,
            "log_checks": checks,
            "message_errors": message_errors,
        }
