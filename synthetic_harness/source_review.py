"""Human source-selection review and replacement-source capture."""

from __future__ import annotations

import base64
import binascii
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .episode import Episode
from .integrity import (
    HashChainLog,
    canonical_json,
    sha256_file,
    sha256_text,
    utc_now,
    write_json_atomic,
)
from .arms import PLATFORM_ROOT, SOURCE_LIBRARY_ROOT

VALID_DECISIONS = {"confirmed", "rejected", "replaced", "skipped"}
ALLOWED_UPLOAD_TYPES = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "text/plain": ".txt",
}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
REGISTRY_CSV = PLATFORM_ROOT / "source_registry.csv"
REGISTRY_JSON = PLATFORM_ROOT / "source_registry.json"


def safe_filename(value: str) -> str:
    name = Path(value).name
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", name).strip("-.")
    return cleaned or "uploaded-policy"


def review_log_path(episode: Episode) -> Path:
    return episode.root / "review" / "source_feedback.jsonl"


def latest_source_reviews(
    episode: Episode,
    active_result_hashes: dict[str, str] | None = None,
    active_source_fingerprints: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    path = review_log_path(episode)
    if not path.exists():
        return {}
    latest: dict[str, dict[str, Any]] = {}
    from .integrity import read_jsonl

    for row in read_jsonl(path):
        latest[row["arm"]] = row
    if active_result_hashes is None and active_source_fingerprints is None:
        return latest
    return {
        arm: review
        for arm, review in latest.items()
        if (
            review.get("selected_result_sha256")
            == (active_result_hashes or {}).get(arm)
            or source_fingerprint(review.get("selected_source"))
            == (active_source_fingerprints or {}).get(arm)
        )
    }


def source_fingerprint(source: dict[str, Any] | None) -> str:
    if not source:
        return ""
    identity = {
        key: source.get(key)
        for key in (
            "title",
            "url",
            "path",
            "local_snapshot_path",
            "effective_date",
            "sha256",
        )
    }
    return sha256_text(canonical_json(identity))


def save_uploaded_source(
    episode: Episode,
    arm: str,
    upload: dict[str, Any],
) -> dict[str, Any]:
    media_type = upload.get("media_type", "")
    if media_type not in ALLOWED_UPLOAD_TYPES:
        raise ValueError("replacement source must be PDF, HTML, or plain text")
    try:
        content = base64.b64decode(upload.get("base64", ""), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("replacement source is not valid base64") from exc
    if not content:
        raise ValueError("replacement source is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("replacement source exceeds 25 MB")
    if media_type == "application/pdf" and not content.startswith(b"%PDF-"):
        raise ValueError("uploaded PDF does not have a valid PDF signature")
    if media_type == "text/html":
        lowered = content[:4096].lower()
        if b"<html" not in lowered and b"<!doctype html" not in lowered:
            raise ValueError("uploaded HTML does not appear to contain an HTML document")
    if media_type.startswith("text/"):
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("uploaded text source must be UTF-8") from exc

    upload_dir = episode.root / "review" / "uploaded_sources"
    upload_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    base = safe_filename(upload.get("name", "uploaded-policy"))
    expected_suffix = ALLOWED_UPLOAD_TYPES[media_type]
    if Path(base).suffix.lower() != expected_suffix:
        base = Path(base).stem + expected_suffix
    path = upload_dir / f"{arm}__{base}"
    if path.exists():
        raise FileExistsError("a replacement source with this name already exists")
    path.write_bytes(content)
    path.chmod(0o600)
    return {
        "name": base,
        "media_type": media_type,
        "bytes": len(content),
        "sha256": sha256_file(path),
        "path": str(path.relative_to(episode.root)),
    }


def _promoted_source_type(media_type: str) -> str:
    return {
        "application/pdf": "clinical_policy_pdf",
        "text/html": "clinical_policy_html",
        "text/plain": "clinical_policy_text",
    }.get(media_type, "clinical_policy_document")


def promote_confirmed_web_source(
    episode: Episode,
    result: dict[str, Any],
) -> dict[str, Any]:
    source = result.get("retrieval", {}).get("selected_source") or {}
    if source.get("evidence_role") not in {None, "governing_policy"}:
        raise ValueError("only a governing policy can be promoted into the library")
    snapshot_value = source.get("local_snapshot_path") or source.get("path")
    if not snapshot_value:
        raise ValueError("confirmed web source has no local snapshot to preserve")
    snapshot = Path(snapshot_value)
    if not snapshot.is_absolute():
        snapshot = episode.root / "system" / "web_only" / snapshot
    snapshot = snapshot.resolve()
    web_root = (episode.root / "system" / "web_only").resolve()
    if not snapshot.is_file() or web_root not in snapshot.parents:
        raise ValueError("confirmed web snapshot is outside the web-arm workspace")

    source_sha = sha256_file(snapshot)
    existing = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    for row in existing:
        if row.get("sha256") == source_sha:
            return {
                "status": "already_present",
                "source_id": row.get("source_id"),
                "relative_path": row.get("relative_path"),
                "sha256": source_sha,
            }

    case = result.get("case_identification", {})
    payer = safe_filename(case.get("payer") or "Unknown-Payer")
    title = safe_filename(source.get("title") or snapshot.stem)
    suffix = snapshot.suffix.lower() or ".html"
    destination_dir = SOURCE_LIBRARY_ROOT / payer / "Human-Confirmed-Web"
    destination_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = destination_dir / f"{title}__confirmed-{episode.episode_id}{suffix}"
    shutil.copy2(snapshot, destination)
    destination.chmod(0o600)
    relative_path = str(destination.relative_to(SOURCE_LIBRARY_ROOT))
    media_type = {
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".htm": "text/html",
        ".txt": "text/plain",
    }.get(suffix, "application/octet-stream")
    source_id = f"SRC-human-confirmed-{episode.episode_id}-{source_sha[:12]}"
    verified_date = utc_now()[:10]
    notes = (
        f"Human-confirmed governing policy from synthetic episode "
        f"{episode.episode_id}; original web retrieval preserved by checksum."
    )
    row = {
        "source_id": source_id,
        "payer": case.get("payer") or "Unknown",
        "state": case.get("state") or "Unknown",
        "source_type": _promoted_source_type(media_type),
        "official_url": source.get("url") or "",
        "final_url": source.get("url") or "",
        "local_file_path": str(destination.resolve()),
        "relative_path": relative_path,
        "shared_drive_url": "",
        "date_verified": verified_date,
        "effective_date": source.get("effective_date") or "",
        "status": "human_confirmed",
        "http_status": "200",
        "content_type": media_type,
        "bytes": str(destination.stat().st_size),
        "sha256": source_sha,
        "official_source": str(bool(source.get("official"))).lower(),
        "notes": notes,
        "product_scope": case.get("product_type") or "commercial_unspecified",
        "include_in_core_denominator": "true",
        "product_scope_notes": (
            f"Plan={case.get('plan_name') or 'unknown'}; procedure="
            f"{case.get('procedure') or 'unknown'}; episode={episode.episode_id}"
        ),
    }
    existing.append(row)
    write_json_atomic(REGISTRY_JSON, existing)
    with REGISTRY_CSV.open("r", encoding="utf-8", newline="") as handle:
        fields = csv.DictReader(handle).fieldnames or list(row)
    with REGISTRY_CSV.open("a", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=fields).writerow(
            {field: row.get(field, "") for field in fields}
        )
    return {
        "status": "promoted",
        "source_id": source_id,
        "relative_path": relative_path,
        "sha256": source_sha,
    }


def record_source_review(
    *,
    episode: Episode,
    arm: str,
    decision: str,
    notes: str = "",
    upload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if arm not in {"library_only", "web_only"}:
        raise ValueError("invalid retrieval arm")
    if decision not in VALID_DECISIONS:
        raise ValueError(f"invalid source-review decision: {decision}")
    result_path = episode.root / "system" / arm / "active_result.json"
    if not result_path.exists():
        result_path = episode.root / "system" / arm / "frozen_result.json"
    if not result_path.exists():
        result_path = episode.root / "system" / arm / "result.json"
    if not result_path.exists():
        raise ValueError("the arm has not selected a source for review")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    selected_source = result.get("retrieval", {}).get("selected_source")
    if decision in {"confirmed", "rejected", "skipped"} and not selected_source:
        raise ValueError("there is no selected source to review")
    if decision == "replaced" and not upload:
        raise ValueError("replacement decision requires an uploaded source")
    result_sha256 = sha256_file(result_path)
    existing_path = review_log_path(episode)
    if existing_path.exists():
        from .integrity import read_jsonl

        for existing in read_jsonl(existing_path):
            if (
                existing.get("arm") == arm
                and existing.get("selected_result_sha256") == result_sha256
            ):
                raise ValueError(
                    "this exact arm result already has a human source-review label"
                )

    uploaded = save_uploaded_source(episode, arm, upload) if upload else None
    promotion = (
        promote_confirmed_web_source(episode, result)
        if arm == "web_only" and decision == "confirmed"
        else None
    )
    feedback = HashChainLog(review_log_path(episode)).append(
        {
            "episode_id": episode.episode_id,
            "case_id": episode.case_id,
            "arm": arm,
            "decision": decision,
            "notes": notes.strip(),
            "selected_source": selected_source,
            "selected_source_fingerprint": source_fingerprint(selected_source),
            "selected_result_sha256": result_sha256,
            "replacement_source": uploaded,
            "library_promotion": promotion,
        }
    )
    episode.log_event(
        role="human_reviewer",
        arm=arm,
        event_type="selected_source_reviewed",
        status="succeeded",
        summary={
            "confirmed": f"Human reviewer confirmed the {arm} selected policy.",
            "rejected": f"Human reviewer rejected the {arm} selected policy.",
            "replaced": f"Human reviewer supplied a replacement policy for {arm}.",
            "skipped": f"Human reviewer continued without judging the {arm} policy.",
        }[decision],
        artifacts=[
            item
            for item in [
                uploaded["path"] if uploaded else None,
                promotion.get("relative_path") if promotion else None,
            ]
            if item
        ],
        details={
            "decision": decision,
            "feedback_record_hash": feedback["record_hash"],
            "replacement_sha256": uploaded["sha256"] if uploaded else None,
            "library_promotion": promotion,
        },
    )
    return feedback


def source_document_for_review(episode: Episode, arm: str) -> tuple[Path | None, str | None]:
    active_path = episode.root / "system" / arm / "active_result.json"
    if not active_path.exists():
        active_path = episode.root / "system" / arm / "frozen_result.json"
    active_hashes = {arm: sha256_file(active_path)} if active_path.exists() else {}
    active_result = (
        json.loads(active_path.read_text(encoding="utf-8"))
        if active_path.exists()
        else {}
    )
    fingerprints = {
        arm: source_fingerprint(
            active_result.get("retrieval", {}).get("selected_source")
        )
    }
    reviews = latest_source_reviews(episode, active_hashes, fingerprints)
    review = reviews.get(arm)
    if review and review.get("replacement_source"):
        source = review["replacement_source"]
        return episode.root / source["path"], source["media_type"]

    result_path = episode.root / "system" / arm / "active_result.json"
    if not result_path.exists():
        result_path = episode.root / "system" / arm / "frozen_result.json"
    if not result_path.exists():
        result_path = episode.root / "system" / arm / "result.json"
    if not result_path.exists():
        return None, None
    result = json.loads(result_path.read_text(encoding="utf-8"))
    source = result.get("retrieval", {}).get("selected_source") or {}
    for key in ("local_snapshot_path", "path", "local_file_path"):
        value = source.get(key)
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = episode.root / "system" / arm / path
        path = path.resolve()
        allowed = [
            (episode.root / "system" / arm).resolve(),
            (episode.root / "review" / "uploaded_sources").resolve(),
            SOURCE_LIBRARY_ROOT.resolve(),
        ]
        if path.is_file() and any(path == root or root in path.parents for root in allowed):
            suffix = path.suffix.lower()
            media = {
                ".pdf": "application/pdf",
                ".html": "text/html",
                ".htm": "text/html",
                ".txt": "text/plain",
            }.get(suffix, "application/octet-stream")
            return path, media
    return None, None


def source_url_for_review(episode: Episode, arm: str) -> str | None:
    result_path = episode.root / "system" / arm / "active_result.json"
    if not result_path.exists():
        result_path = episode.root / "system" / arm / "frozen_result.json"
    if not result_path.exists():
        result_path = episode.root / "system" / arm / "result.json"
    if not result_path.exists():
        return None
    result = json.loads(result_path.read_text(encoding="utf-8"))
    value = (result.get("retrieval", {}).get("selected_source") or {}).get("url")
    if isinstance(value, str) and value.startswith(("https://", "http://")):
        return value
    return None
