"""KISS v0 automatic oracle for policy-retrieval trajectories.

The oracle is *computed* by comparing the agent's returned/fetched policy URL
against the known-correct governing policy URL from the ground-truth snapshot.
Nothing here hardcodes ``correct = True`` — every verdict is derived from a
comparison of the agent's real fetch result to the ground truth.

Design mirrors the field vocabulary used elsewhere in the harness
(``synthetic_harness.source_review.source_fingerprint`` compares url/sha256
identities); here we normalize and compare host + path, and optionally
strengthen the match with the sha256 of the fetched body.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def normalize_url(url: str | None) -> tuple[str, str]:
    """Return (host, path) normalized for comparison.

    - host: lowercased, ``www.`` prefix stripped, scheme ignored.
    - path: trailing slash stripped (except root), case preserved
      (server paths are case-sensitive; only host casing is normalized).
    """
    if not url:
        return ("", "")
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path or ""
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return (host, path)


def urls_match(a: str | None, b: str | None) -> bool:
    """Host AND path must match after normalization."""
    na, nb = normalize_url(a), normalize_url(b)
    if not na[0] or not nb[0]:
        return False
    return na == nb


def compute_oracle(
    *,
    ground_truth_url: str,
    selected_url: str | None,
    fetch_status: int | None,
    fetch_content_type: str | None,
    fetch_sha256: str | None = None,
    ground_truth_sha256: str | None = None,
    policy_content_types: tuple[str, ...] = ("application/pdf",),
) -> dict[str, Any]:
    """Compute the automatic oracle verdict from a real fetch result.

    Args:
        ground_truth_url: known-correct governing policy URL (from snapshot).
        selected_url: URL the agent actually selected and fetched.
        fetch_status: HTTP status code observed during the real fetch.
        fetch_content_type: Content-Type header observed during the fetch.
        fetch_sha256: sha256 of the fetched body (optional strengthening).
        ground_truth_sha256: sha256 of the ground-truth doc if separately
            fetched (optional strengthening; when both present they must agree).
        policy_content_types: content-types that count as a policy document.

    Returns:
        {"correct": bool, "reachable": bool, "reward": int} plus derived
        detail fields for the trajectory record.
    """
    # correct: derived from URL comparison (never a literal True).
    correct = urls_match(selected_url, ground_truth_url)

    # Optional strengthening: if we have both hashes, they must agree for the
    # match to stand (guards against same-path-different-content edge cases).
    sha_checked = False
    if correct and fetch_sha256 and ground_truth_sha256:
        sha_checked = True
        correct = fetch_sha256 == ground_truth_sha256

    ct = (fetch_content_type or "").split(";")[0].strip().lower()
    is_policy_ct = any(ct == c for c in policy_content_types)
    reachable = bool(fetch_status == 200 and is_policy_ct)

    if not reachable:
        reward = -1
    elif correct:
        reward = 1
    else:
        reward = 0

    return {
        "correct": bool(correct),
        "reachable": bool(reachable),
        "reward": reward,
        "url_match": urls_match(selected_url, ground_truth_url),
        "sha256_checked": sha_checked,
        "observed_status": fetch_status,
        "observed_content_type": fetch_content_type,
    }
