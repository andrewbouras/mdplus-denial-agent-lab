"""Map the computed KISS oracle onto the Plinth training-unit rating.

The Plinth ``training_unit`` contract (see plinth-app
``components/synthetic-emr/trajectory-capture/trajectory-capture.ts``) carries a
``rating`` block the review UI pre-fills and an operator later confirms/corrects:

    rating = {
      outcome: success|partial|failure|unsafe|indeterminate,
      verdict: good|bad,
      failure: {
        occurred: bool,
        failure_step_idx: int|null,
        failure_step_id: str|null,
        failure_type: retrieval|reasoning|planning|navigation|data_entry|
                      verification|premature_completion|failure_to_escalate|
                      unsafe_action|none,
        severity: critical|major|minor|none,
        rationale: str,
      },
    }

Our contribution is ONLY the translation: we take the verdict the oracle already
computed (``{correct, reachable, reward}`` from
``synthetic_harness.kiss_oracle.compute_oracle`` — never hardcoded) and derive
the rating fields from it, per the board's fixed rule:

    reward =  1  (reachable + correct)       -> success / good, no failure
    reward =  0  (reachable but WRONG pick)  -> failure / bad, retrieval, major,
                                                failure pinned to the rank/select
                                                DECISION step (the oracle grades
                                                that choice)
    reward = -1  (unreachable / not a PDF)   -> failure / bad, critical, pinned
                                                to the fetch/return step;
                                                failure_type = navigation when a
                                                navigation step failed, else
                                                retrieval

STRUCTURAL GUARANTEE: reward is DERIVED here from the oracle, and the human can
only confirm/correct the *rating* fields downstream — they cannot flip ``reward``
(reward is not a field of the rating and is re-computable from the trace's real
fetch facts). This module never invents a verdict; it only translates one.
"""

from __future__ import annotations

from typing import Any

# Marker so the review UI shows this rating was machine-pre-filled from the
# computed oracle (an operator confirms/corrects; they never author `reward`).
DERIVED_BY = "kiss_oracle_auto"

# Enum allow-lists mirrored verbatim from trajectory-capture.ts. Kept here as a
# read-only copy purely so our unit tests can assert we only emit legal values;
# the Plinth validator (validateClientRating) remains the real gate.
OUTCOMES = ("success", "partial", "failure", "unsafe", "indeterminate")
VERDICTS = ("good", "bad")
FAILURE_TYPES = (
    "retrieval",
    "reasoning",
    "planning",
    "navigation",
    "data_entry",
    "verification",
    "premature_completion",
    "failure_to_escalate",
    "unsafe_action",
    "none",
)
SEVERITIES = ("critical", "major", "minor", "none")


def map_oracle_to_rating(
    oracle: dict[str, Any],
    *,
    decision_step_idx: int,
    decision_step_id: str,
    fetch_step_idx: int,
    fetch_step_id: str,
    navigation_failed: bool = False,
) -> dict[str, Any]:
    """Translate a computed oracle verdict into a Plinth rating block.

    Args:
        oracle: the dict returned by ``compute_oracle`` (must carry ``reward``,
            ``correct``, ``reachable``). Nothing is recomputed here.
        decision_step_idx / decision_step_id: the rank/select step the oracle
            grades — the failure pin for a reachable-but-wrong pick (reward=0).
        fetch_step_idx / fetch_step_id: the fetch/return step — the failure pin
            for an unreachable / not-a-PDF outcome (reward=-1).
        navigation_failed: if the unreachable outcome was caused by a failed
            navigation step (vs a retrieval miss), tag the failure ``navigation``.

    Returns:
        A rating dict conforming to the Plinth Rating shape.
    """
    if "reward" not in oracle:
        raise ValueError("oracle dict missing 'reward'; pass compute_oracle output")
    reward = oracle["reward"]

    if reward == 1:
        return {
            "outcome": "success",
            "verdict": "good",
            "failure": {
                "occurred": False,
                "failure_step_idx": None,
                "failure_step_id": None,
                "failure_type": "none",
                "severity": "none",
                "rationale": (
                    "Auto-oracle: agent selected the governing policy and the "
                    "fetched document is a reachable PDF (host+path match to "
                    "ground truth). reward=1."
                ),
            },
        }

    if reward == 0:
        # Reachable, but the WRONG policy was picked. The error is in the
        # rank/select decision the oracle grades -> retrieval failure there.
        return {
            "outcome": "failure",
            "verdict": "bad",
            "failure": {
                "occurred": True,
                "failure_step_idx": decision_step_idx,
                "failure_step_id": decision_step_id,
                "failure_type": "retrieval",
                "severity": "major",
                "rationale": (
                    "Auto-oracle: the fetched document is reachable but does NOT "
                    "match the governing policy (host+path mismatch to ground "
                    "truth). The wrong policy was chosen at the rank/select step. "
                    "reward=0."
                ),
            },
        }

    if reward == -1:
        # Unreachable / not a policy PDF. Pin to the fetch/return step.
        failure_type = "navigation" if navigation_failed else "retrieval"
        return {
            "outcome": "failure",
            "verdict": "bad",
            "failure": {
                "occurred": True,
                "failure_step_idx": fetch_step_idx,
                "failure_step_id": fetch_step_id,
                "failure_type": failure_type,
                "severity": "critical",
                "rationale": (
                    "Auto-oracle: the selected document was not retrievable as a "
                    "policy PDF (non-200 or non-PDF content-type). reward=-1."
                ),
            },
        }

    raise ValueError(f"unexpected oracle reward {reward!r}; expected -1|0|1")


def build_training_unit(
    *,
    run_id: str,
    trace_ref: dict[str, Any],
    scenario: dict[str, Any],
    rating: dict[str, Any],
    rated_at: str,
    rated_by: str = DERIVED_BY,
) -> dict[str, Any]:
    """Assemble a full Plinth ``training_unit`` (version 1) around a rating.

    Mirrors the TrainingUnit shape in trajectory-capture.ts. ``rated_by`` defaults
    to the auto-oracle marker so the review UI shows the rating was pre-filled by
    the computed oracle (an operator later confirms/corrects it).
    """
    return {
        "training_unit_version": 1,
        "run_id": run_id,
        "trace_ref": trace_ref,
        "scenario": scenario,
        "rating": rating,
        "rated_by": rated_by,
        "rated_at": rated_at,
        "privacy": {"phi_status": "synthetic"},
    }
