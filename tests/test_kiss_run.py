"""Offline tests proving the KISS oracle actually discriminates.

These feed the oracle *synthetic* fetch results (no network) to prove the
verdict is derived, not stuck-true:
  - a WRONG selection -> correct=False and reward <= 0
  - the RIGHT selection -> correct=True and reward == 1
  - an UNREACHABLE selection -> reachable=False and reward == -1
Plus a meta/jsonl round-trip parse of the produced run artifacts when present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from synthetic_harness.kiss_oracle import compute_oracle, urls_match

REPO_ROOT = Path(__file__).resolve().parent.parent

TRUE_URL = (
    "https://www.uhcprovider.com/content/dam/provider/docs/public/policies/"
    "comm-medical-drug/surgery-knee.pdf"
)
WRONG_URL = (
    "https://www.uhcprovider.com/content/dam/provider/docs/public/policies/"
    "medadv-mp/joint-procedures.pdf"
)


def test_wrong_selection_is_incorrect():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=WRONG_URL,
        fetch_status=200,
        fetch_content_type="application/pdf",
    )
    assert o["correct"] is False
    assert o["reward"] <= 0
    # reachable-but-wrong -> reward exactly 0
    assert o["reachable"] is True
    assert o["reward"] == 0


def test_right_selection_is_correct():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=200,
        fetch_content_type="application/pdf",
    )
    assert o["correct"] is True
    assert o["reachable"] is True
    assert o["reward"] == 1


def test_unreachable_selection_penalized():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=404,
        fetch_content_type=None,
    )
    assert o["reachable"] is False
    assert o["reward"] == -1


def test_non_policy_content_type_not_reachable():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=200,
        fetch_content_type="text/html",
    )
    assert o["reachable"] is False
    assert o["reward"] == -1


def test_sha256_strengthening_can_flip_a_path_match_to_wrong():
    # Same URL/path but the fetched body hash disagrees with ground truth ->
    # oracle must NOT declare correct.
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=200,
        fetch_content_type="application/pdf",
        fetch_sha256="a" * 64,
        ground_truth_sha256="b" * 64,
    )
    assert o["correct"] is False
    assert o["reward"] == 0


def test_url_normalization():
    assert urls_match(TRUE_URL, TRUE_URL + "")
    assert urls_match(TRUE_URL, TRUE_URL.replace("www.", ""))
    assert urls_match(TRUE_URL, TRUE_URL.rstrip("f") + "f")  # identity
    assert not urls_match(TRUE_URL, WRONG_URL)
    assert not urls_match(TRUE_URL, None)


def test_produced_run_roundtrips_if_present():
    stem = REPO_ROOT / "runs" / "run_0001"
    jsonl_path = stem.with_suffix(".jsonl")
    meta_path = Path(str(stem) + ".meta.json")
    if not (jsonl_path.exists() and meta_path.exists()):
        pytest.skip("run_0001 artifacts not produced yet")
    steps = [json.loads(x) for x in jsonl_path.read_text().splitlines() if x.strip()]
    assert steps and all("i" in s and "action" in s for s in steps)
    meta = json.loads(meta_path.read_text())
    o = meta["oracle"]
    assert isinstance(o["correct"], bool)
    assert isinstance(o["reachable"], bool)
    assert isinstance(o["reward"], (int, float))
    assert meta["target"]
