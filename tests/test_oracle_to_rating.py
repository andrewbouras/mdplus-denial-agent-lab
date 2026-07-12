"""Tests for the oracle -> Plinth rating mapping.

Prove the mapping is DERIVED from the computed oracle (not hardcoded) and obeys
the board's reward-derived rule exactly:

    reward =  1 -> success/good, no failure, null pin
    reward =  0 -> failure/bad, retrieval, major, pinned to the rank/select step
    reward = -1 -> failure/bad, critical, pinned to the fetch/return step
                   (navigation when a navigation step failed, else retrieval)

Also proves every emitted enum value is legal per the Plinth contract, and that
the rating carries no `reward` field (so a human editing the rating cannot flip
the computed reward).
"""

from __future__ import annotations

import pytest

from synthetic_harness.kiss_oracle import compute_oracle
from synthetic_harness.plinth_contract.oracle_to_rating import (
    DERIVED_BY,
    FAILURE_TYPES,
    OUTCOMES,
    SEVERITIES,
    VERDICTS,
    build_training_unit,
    map_oracle_to_rating,
)

TRUE_URL = (
    "https://www.uhcprovider.com/content/dam/provider/docs/public/policies/"
    "comm-medical-drug/surgery-knee.pdf"
)
WRONG_URL = (
    "https://www.uhcprovider.com/content/dam/provider/docs/public/policies/"
    "medadv-mp/joint-procedures.pdf"
)

PINS = dict(
    decision_step_idx=2,
    decision_step_id="step_dec",
    fetch_step_idx=4,
    fetch_step_id="step_fetch",
)


def _assert_legal(rating: dict) -> None:
    assert rating["outcome"] in OUTCOMES
    assert rating["verdict"] in VERDICTS
    f = rating["failure"]
    assert f["failure_type"] in FAILURE_TYPES
    assert f["severity"] in SEVERITIES
    assert isinstance(f["occurred"], bool)
    assert isinstance(f["rationale"], str) and f["rationale"]
    # rating never carries reward -> human cannot flip it here.
    assert "reward" not in rating and "reward" not in f


def test_reward1_success_no_failure():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=200,
        fetch_content_type="application/pdf",
    )
    assert o["reward"] == 1
    r = map_oracle_to_rating(o, **PINS)
    _assert_legal(r)
    assert r["outcome"] == "success"
    assert r["verdict"] == "good"
    assert r["failure"]["occurred"] is False
    assert r["failure"]["failure_step_idx"] is None
    assert r["failure"]["failure_step_id"] is None
    assert r["failure"]["failure_type"] == "none"
    assert r["failure"]["severity"] == "none"


def test_reward0_reachable_but_wrong_pins_decision_step():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=WRONG_URL,
        fetch_status=200,
        fetch_content_type="application/pdf",
    )
    assert o["reward"] == 0
    r = map_oracle_to_rating(o, **PINS)
    _assert_legal(r)
    assert r["outcome"] == "failure"
    assert r["verdict"] == "bad"
    assert r["failure"]["occurred"] is True
    assert r["failure"]["failure_step_idx"] == PINS["decision_step_idx"]
    assert r["failure"]["failure_step_id"] == PINS["decision_step_id"]
    assert r["failure"]["failure_type"] == "retrieval"
    assert r["failure"]["severity"] == "major"


def test_reward_neg1_unreachable_pins_fetch_step_retrieval():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=404,
        fetch_content_type=None,
    )
    assert o["reward"] == -1
    r = map_oracle_to_rating(o, **PINS)
    _assert_legal(r)
    assert r["outcome"] == "failure"
    assert r["verdict"] == "bad"
    assert r["failure"]["occurred"] is True
    assert r["failure"]["failure_step_idx"] == PINS["fetch_step_idx"]
    assert r["failure"]["failure_step_id"] == PINS["fetch_step_id"]
    assert r["failure"]["failure_type"] == "retrieval"
    assert r["failure"]["severity"] == "critical"


def test_reward_neg1_navigation_failure_tags_navigation():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=None,
        fetch_content_type=None,
    )
    assert o["reward"] == -1
    r = map_oracle_to_rating(o, navigation_failed=True, **PINS)
    _assert_legal(r)
    assert r["failure"]["failure_type"] == "navigation"
    assert r["failure"]["severity"] == "critical"


def test_mapping_is_derived_not_hardcoded():
    # Same pins, different oracle -> different rating. Proves derivation.
    ok = map_oracle_to_rating(
        compute_oracle(
            ground_truth_url=TRUE_URL,
            selected_url=TRUE_URL,
            fetch_status=200,
            fetch_content_type="application/pdf",
        ),
        **PINS,
    )
    wrong = map_oracle_to_rating(
        compute_oracle(
            ground_truth_url=TRUE_URL,
            selected_url=WRONG_URL,
            fetch_status=200,
            fetch_content_type="application/pdf",
        ),
        **PINS,
    )
    assert ok["verdict"] == "good" and wrong["verdict"] == "bad"
    assert ok["failure"]["occurred"] is False and wrong["failure"]["occurred"] is True


def test_missing_reward_raises():
    with pytest.raises(ValueError):
        map_oracle_to_rating({"correct": True, "reachable": True}, **PINS)


def test_build_training_unit_shape():
    o = compute_oracle(
        ground_truth_url=TRUE_URL,
        selected_url=TRUE_URL,
        fetch_status=200,
        fetch_content_type="application/pdf",
    )
    r = map_oracle_to_rating(o, **PINS)
    unit = build_training_unit(
        run_id="run_abc123def456",
        trace_ref={
            "path": "/x/trace.jsonl",
            "project_slug": "synthetic-emr-demo",
            "tenant_id": "tnt_aaaaaaaaaaaa",
            "workflow_id": "wf_x",
            "capture_version": "v",
            "schema_version": 2,
            "step_count": 6,
        },
        scenario={
            "id": "s",
            "competency": "policy_retrieval",
            "patient_id": "27447",
            "phi_status": "synthetic",
        },
        rating=r,
        rated_at="2026-07-12T00:00:00+00:00",
    )
    assert unit["training_unit_version"] == 1
    assert unit["run_id"] == "run_abc123def456"
    assert unit["rated_by"] == DERIVED_BY
    assert unit["privacy"]["phi_status"] == "synthetic"
    assert unit["rating"] is r
