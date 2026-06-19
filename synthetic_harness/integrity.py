"""Canonical serialization, hashing, and append-only JSONL primitives."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

GENESIS_HASH = "0" * 64


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(row)
    return rows


class HashChainLog:
    """Append-only JSONL where every row commits to the previous row."""

    def __init__(self, path: Path):
        self.path = path

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = read_jsonl(self.path)
        previous_hash = rows[-1]["record_hash"] if rows else GENESIS_HASH
        sequence = len(rows) + 1
        body = {
            "sequence": sequence,
            "timestamp": utc_now(),
            "previous_hash": previous_hash,
            **payload,
        }
        if "record_hash" in payload:
            raise ValueError("record_hash is reserved")
        record_hash = sha256_text(canonical_json(body))
        record = {**body, "record_hash": record_hash}
        line = canonical_json(record) + "\n"

        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(descriptor, line.encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return record

    def verify(self) -> dict[str, Any]:
        rows = read_jsonl(self.path)
        previous_hash = GENESIS_HASH
        errors: list[str] = []
        for index, record in enumerate(rows, start=1):
            if record.get("sequence") != index:
                errors.append(f"row {index}: sequence is {record.get('sequence')!r}")
            if record.get("previous_hash") != previous_hash:
                errors.append(f"row {index}: previous_hash mismatch")
            supplied_hash = record.get("record_hash")
            body = {key: value for key, value in record.items() if key != "record_hash"}
            calculated_hash = sha256_text(canonical_json(body))
            if supplied_hash != calculated_hash:
                errors.append(f"row {index}: record_hash mismatch")
            previous_hash = supplied_hash or ""
        return {
            "path": str(self.path),
            "valid": not errors,
            "records": len(rows),
            "head_hash": previous_hash,
            "errors": errors,
        }


def write_json_atomic(path: Path, value: Any, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        os.write(descriptor, data.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    os.chmod(path, mode)


def hash_manifest(paths: Iterable[Path], relative_to: Path) -> dict[str, str]:
    return {
        str(path.relative_to(relative_to)): sha256_file(path)
        for path in sorted(paths)
        if path.is_file()
    }
