"""Policy-anchored case validation and ground-truth sealing."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .episode import Episode
from .integrity import canonical_json, sha256_file, sha256_text, utc_now, write_json_atomic

DEFAULT_PLATFORM_ROOT = Path(
    os.environ.get(
        "MDPLUS_POLICY_PLATFORM_ROOT",
        Path(__file__).resolve().parents[1] / "data/policy_platform",
    )
)

FORBIDDEN_PATIENT_KEYS = {
    "answer_key",
    "canonical_criteria",
    "criteria_id",
    "expected_action",
    "expected_denial_reason",
    "expected_follow_up",
    "ground_truth",
    "judge_rubric",
    "likely_denial_reasons",
    "official_url",
    "policy_excerpt",
    "source_id",
    "source_text_path",
}

REQUIRED_TRUTH_KEYS = {
    "anchor",
    "denial",
    "hidden_patient_facts",
    "expected_interaction",
    "expected_next_steps",
}

REQUIRED_PATIENT_KEYS = {
    "persona",
    "insurance_card",
    "denial_materials",
    "patient_knowledge",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class PolicyIndex:
    def __init__(self, platform_root: Path = DEFAULT_PLATFORM_ROOT):
        self.platform_root = platform_root.resolve()
        self.sources = load_json(self.platform_root / "source_registry.json")
        self.criteria = load_json(self.platform_root / "criteria_extractions.json")
        self.sources_by_id = {row["source_id"]: row for row in self.sources}
        self.criteria_by_id = {row["criteria_id"]: row for row in self.criteria}

    def candidates(self, high_confidence_only: bool = True) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for criterion in self.criteria:
            confidence = str(criterion.get("extraction_confidence", "")).lower()
            if high_confidence_only and confidence != "high":
                continue
            source = self.sources_by_id.get(criterion.get("source_id"))
            if not source:
                continue
            local_path = Path(source.get("local_file_path", ""))
            rows.append(
                {
                    "criteria_id": criterion["criteria_id"],
                    "payer": criterion.get("payer"),
                    "state": criterion.get("state"),
                    "procedure": criterion.get("procedure"),
                    "subprocedure": criterion.get("subprocedure"),
                    "source_id": source["source_id"],
                    "source_type": source.get("source_type"),
                    "local_source_exists": local_path.is_file(),
                    "extraction_confidence": confidence,
                    "review_status": criterion.get("review_status"),
                }
            )
        return rows

    def anchor(self, criteria_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            criterion = self.criteria_by_id[criteria_id]
        except KeyError as exc:
            raise ValueError(f"unknown criteria_id: {criteria_id}") from exc
        try:
            source = self.sources_by_id[criterion["source_id"]]
        except KeyError as exc:
            raise ValueError(f"criteria {criteria_id} has no indexed source") from exc
        return criterion, source


def find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.lower() in FORBIDDEN_PATIENT_KEYS:
                findings.append(child_path)
            findings.extend(find_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_forbidden_keys(child, f"{path}[{index}]"))
    return findings


def require_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")


def build_anchor_snapshot(
    index: PolicyIndex,
    criteria_id: str,
) -> dict[str, Any]:
    criterion, source = index.anchor(criteria_id)
    source_path = Path(source.get("local_file_path", ""))
    if not source_path.is_file():
        raise ValueError(f"anchoring source is not available locally: {source_path}")
    actual_hash = sha256_file(source_path)
    registry_hash = source.get("sha256", "")
    if registry_hash and registry_hash != actual_hash:
        raise ValueError(
            f"source hash differs from registry for {source['source_id']}: "
            f"registry={registry_hash}, actual={actual_hash}"
        )
    return {
        "criteria_id": criterion["criteria_id"],
        "source_id": source["source_id"],
        "payer": criterion.get("payer"),
        "state": criterion.get("state"),
        "procedure": criterion.get("procedure"),
        "subprocedure": criterion.get("subprocedure"),
        "source_type": source.get("source_type"),
        "source_title": criterion.get("source_title"),
        "official_url": source.get("official_url"),
        "effective_date": source.get("effective_date"),
        "date_verified": source.get("date_verified"),
        "local_file_path": str(source_path.resolve()),
        "source_sha256": actual_hash,
        "source_page_or_line_reference": criterion.get("source_page_or_line_reference"),
        "canonical_extraction": {
            key: criterion.get(key)
            for key in [
                "coverage_rule_summary",
                "conservative_required",
                "conservative_duration",
                "pt_required",
                "imaging_required",
                "documentation_required",
                "peer_to_peer_applicable",
                "vendor_route",
                "likely_denial_reasons",
                "patient_next_step",
            ]
        },
        "extraction_confidence": criterion.get("extraction_confidence"),
        "review_status": criterion.get("review_status"),
    }


def seal_ground_truth(
    *,
    episode: Episode,
    truth: dict[str, Any],
    controller_keys_root: Path,
) -> dict[str, Any]:
    controller_keys_root = controller_keys_root.resolve()
    controller_keys_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    controller_keys_root.chmod(0o700)
    key_path = controller_keys_root / f"{episode.episode_id}.passphrase"
    if key_path.exists():
        raise FileExistsError(f"key already exists: {key_path}")
    passphrase = secrets.token_urlsafe(48)
    key_path.write_text(passphrase + "\n", encoding="utf-8")
    key_path.chmod(0o600)

    plaintext = canonical_json(truth).encode("utf-8")
    ciphertext_path = episode.root / "sealed" / "ground_truth.enc"
    with tempfile.NamedTemporaryFile("wb", delete=False) as temporary:
        temporary.write(plaintext)
        temporary_path = Path(temporary.name)
    try:
        subprocess.run(
            [
                "openssl",
                "enc",
                "-aes-256-cbc",
                "-salt",
                "-pbkdf2",
                "-iter",
                "250000",
                "-in",
                str(temporary_path),
                "-out",
                str(ciphertext_path),
                "-pass",
                f"file:{key_path}",
            ],
            check=True,
            capture_output=True,
        )
    finally:
        temporary_path.unlink(missing_ok=True)

    ciphertext_path.chmod(0o600)
    seal = {
        "schema_version": "1.0",
        "episode_id": episode.episode_id,
        "case_id": episode.case_id,
        "sealed_at": utc_now(),
        "cipher": "aes-256-cbc",
        "kdf": "pbkdf2",
        "iterations": 250000,
        "plaintext_sha256": sha256_text(canonical_json(truth)),
        "ciphertext_sha256": sha256_file(ciphertext_path),
        "key_location": "controller-owned; intentionally omitted from episode",
    }
    write_json_atomic(episode.root / "sealed" / "seal_manifest.json", seal)
    return {**seal, "controller_key_path": str(key_path)}


def author_case(
    *,
    episode: Episode,
    criteria_id: str,
    truth_input: dict[str, Any],
    patient_packet: dict[str, Any],
    platform_root: Path,
    controller_keys_root: Path,
) -> dict[str, Any]:
    require_keys(truth_input, REQUIRED_TRUTH_KEYS - {"anchor"}, "ground truth")
    require_keys(patient_packet, REQUIRED_PATIENT_KEYS, "patient packet")
    forbidden = find_forbidden_keys(patient_packet)
    if forbidden:
        raise ValueError(
            "patient packet contains answer-key fields: " + ", ".join(forbidden)
        )

    index = PolicyIndex(platform_root)
    anchor = build_anchor_snapshot(index, criteria_id)
    supplied_anchor = truth_input.get("anchor")
    if supplied_anchor:
        raise ValueError("truth input must not supply anchor; it is derived from the policy index")

    truth = {
        "schema_version": "1.0",
        "episode_id": episode.episode_id,
        "case_id": episode.case_id,
        "authored_at": utc_now(),
        "anchor": anchor,
        **truth_input,
    }
    visible_packet = {
        "schema_version": "1.0",
        "episode_id": episode.episode_id,
        "case_id": episode.case_id,
        "issued_at": utc_now(),
        **patient_packet,
    }
    patient_path = episode.root / "patient_workspace" / "patient_packet.json"
    write_json_atomic(patient_path, visible_packet)
    seal = seal_ground_truth(
        episode=episode,
        truth=truth,
        controller_keys_root=controller_keys_root,
    )

    episode._update_manifest(
        status="case_authored",
        criteria_anchor_hash=anchor["source_sha256"],
        patient_packet_sha256=sha256_file(patient_path),
        sealed_truth_sha256=seal["ciphertext_sha256"],
    )
    episode.log_event(
        role="case_author",
        arm="shared",
        event_type="case_authored_and_sealed",
        status="succeeded",
        summary="Anchored the case to a verified local policy, wrote the patient-visible packet, and encrypted ground truth.",
        artifacts=[
            "patient_workspace/patient_packet.json",
            "sealed/ground_truth.enc",
            "sealed/seal_manifest.json",
        ],
        details={
            "criteria_id_hash": sha256_text(criteria_id),
            "anchor_source_sha256": anchor["source_sha256"],
            "patient_packet_sha256": sha256_file(patient_path),
            "sealed_truth_sha256": seal["ciphertext_sha256"],
        },
    )
    return {
        "episode_id": episode.episode_id,
        "case_id": episode.case_id,
        "patient_packet_path": str(patient_path),
        "seal_manifest_path": str(episode.root / "sealed" / "seal_manifest.json"),
        "controller_key_path": seal["controller_key_path"],
        "anchor_summary": {
            "payer": anchor["payer"],
            "state": anchor["state"],
            "procedure": anchor["procedure"],
            "source_sha256": anchor["source_sha256"],
        },
    }


def unseal_ground_truth(episode: Episode, key_path: Path) -> dict[str, Any]:
    ciphertext_path = episode.root / "sealed" / "ground_truth.enc"
    result = subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-256-cbc",
            "-pbkdf2",
            "-iter",
            "250000",
            "-in",
            str(ciphertext_path),
            "-pass",
            f"file:{key_path.resolve()}",
        ],
        check=True,
        capture_output=True,
    )
    truth = json.loads(result.stdout.decode("utf-8"))
    seal = load_json(episode.root / "sealed" / "seal_manifest.json")
    if sha256_text(canonical_json(truth)) != seal["plaintext_sha256"]:
        raise ValueError("unsealed truth does not match the original plaintext commitment")
    return truth
