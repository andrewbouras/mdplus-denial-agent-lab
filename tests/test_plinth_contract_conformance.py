"""Conformance test: the emitted run-dir matches the Plinth trajectory contract.

Validates the produced trace.jsonl (RunHeader + StepRecord + ArtifactRecord) and
training-unit.json against the shapes/enums the Plinth reader + rating validator
require (mirrored from plinth-app capture-trace.ts + trajectory-capture.ts). If no
run has been produced yet, the test skips (verify step 1 runs pytest BEFORE the
capture in verify step 2); once a run exists it is fully asserted.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

PROJECT_SLUG = "synthetic-emr-demo"
# Our capture writes this workflow_id; the shared runs/ tree also holds foreign
# Plinth demo runs (EMR triage / computer-use), so we scope to OURS.
OUR_WORKFLOW_ID = "wf_policy_retrieval_uhc_27447"
RUN_ID_RE = re.compile(r"^run_[a-f0-9]{12}$")
STEP_ID_RE = re.compile(r"^step_[a-f0-9]{12}$")
ART_ID_RE = re.compile(r"^art_[a-f0-9]{12}$")

OUTCOMES = {"success", "partial", "failure", "unsafe", "indeterminate"}
VERDICTS = {"good", "bad"}
FAILURE_TYPES = {
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
}
SEVERITIES = {"critical", "major", "minor", "none"}
ARTIFACT_TYPES = {"screenshot", "dom", "elements"}

STEP_REQUIRED = {
    "kind", "step_id", "run_id", "tenant_id", "workflow_id", "task_id", "step_idx",
    "actor", "step_type", "phase", "subgoal", "ts_start", "ts_end",
    "observation", "decision", "action", "result", "labels", "privacy",
    "schema_version", "capture_version",
}
ARTIFACT_REQUIRED = {
    "kind", "artifact_id", "run_id", "tenant_id", "step_id", "step_idx",
    "storage_key", "artifact_type", "sha256", "byte_size", "created_at",
}
RUN_REQUIRED = {
    "kind", "run_id", "tenant_id", "project_slug", "workflow_id",
    "capture_version", "started_at",
}


def _runs_root() -> Path:
    home = os.environ.get("HOME", "/home/clawd")
    return Path(home) / "clawd" / "state" / "projects" / PROJECT_SLUG / "runs"


def _is_our_run(run_dir: Path) -> bool:
    """True only for runs our capture produced (by workflow_id in the header)."""
    try:
        first = (run_dir / "trace.jsonl").read_text().splitlines()[0]
        return json.loads(first).get("workflow_id") == OUR_WORKFLOW_ID
    except (OSError, ValueError, IndexError):
        return False


def _latest_run() -> Path | None:
    root = _runs_root()
    if not root.is_dir():
        return None
    runs = [
        d for d in root.iterdir()
        if d.is_dir() and RUN_ID_RE.match(d.name) and (d / "trace.jsonl").is_file()
        and _is_our_run(d)
    ]
    if not runs:
        return None
    return max(runs, key=lambda d: (d / "trace.jsonl").stat().st_mtime)


def _load_trace(run_dir: Path):
    header = None
    steps, artifacts = [], []
    for line in (run_dir / "trace.jsonl").read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec["kind"] == "run":
            header = rec
        elif rec["kind"] == "step":
            steps.append(rec)
        elif rec["kind"] == "artifact":
            artifacts.append(rec)
    return header, steps, artifacts


@pytest.fixture(scope="module")
def produced_run():
    rd = _latest_run()
    if rd is None:
        pytest.skip("no synthetic-emr-demo run produced yet (emit_plinth_trace not run)")
    return rd


def test_run_header_conforms(produced_run):
    header, _, _ = _load_trace(produced_run)
    assert header is not None, "trace.jsonl must start with a run header"
    assert RUN_REQUIRED.issubset(header.keys())
    assert header["kind"] == "run"
    assert RUN_ID_RE.match(header["run_id"])
    assert header["run_id"] == produced_run.name
    assert header["project_slug"] == PROJECT_SLUG


def test_steps_conform_and_multistep(produced_run):
    _, steps, _ = _load_trace(produced_run)
    assert len(steps) > 1, "trajectory must be genuinely multi-step"
    idxs = [s["step_idx"] for s in steps]
    assert idxs == sorted(idxs), "step_idx must be ordered"
    assert len(set(idxs)) == len(idxs), "step_idx must be unique"
    for s in steps:
        assert STEP_REQUIRED.issubset(s.keys()), f"step missing fields: {STEP_REQUIRED - s.keys()}"
        assert s["kind"] == "step"
        assert STEP_ID_RE.match(s["step_id"])
        assert s["run_id"] == produced_run.name
        assert s["actor"] == "agent"
        assert s["step_type"] == "browser_action"
        assert isinstance(s["step_idx"], int)
        assert s["schema_version"] == 2
        assert isinstance(s["subgoal"], str) and s["subgoal"]


def test_artifacts_conform_and_screenshots_exist(produced_run):
    header, steps, artifacts = _load_trace(produced_run)
    step_ids = {s["step_id"] for s in steps}
    screenshots = 0
    for a in artifacts:
        assert ARTIFACT_REQUIRED.issubset(a.keys())
        assert a["kind"] == "artifact"
        assert ART_ID_RE.match(a["artifact_id"])
        assert a["artifact_type"] in ARTIFACT_TYPES
        assert a["step_id"] in step_ids, "artifact must FK to a real step"
        assert isinstance(a["byte_size"], int) and a["byte_size"] > 0
        assert re.match(r"^[a-f0-9]{64}$", a["sha256"])
        # storage_key must be the canonical run-artifact shape the reader resolves:
        #   t/<tenant>/p/synthetic-emr-demo/runs/<runId>/<step_id>/<leaf>
        exp_prefix = f"t/{a['tenant_id']}/p/{PROJECT_SLUG}/runs/{header['run_id']}/{a['step_id']}/"
        assert a["storage_key"].startswith(exp_prefix), a["storage_key"]
        if a["artifact_type"] == "screenshot":
            screenshots += 1
            leaf = a["storage_key"].split("/")[-1]
            assert leaf == "screenshot.png"
            # the on-disk PNG the HetznerNativeDriver reads must exist + match size
            disk = produced_run / a["step_id"] / "screenshot.png"
            assert disk.is_file(), f"screenshot missing on disk: {disk}"
            assert disk.stat().st_size == a["byte_size"]
            assert disk.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", "real PNG bytes"
    assert screenshots > 1, "each real navigation step must carry a real screenshot"
    # every step should have a screenshot
    steps_with_shot = {a["step_id"] for a in artifacts if a["artifact_type"] == "screenshot"}
    assert steps_with_shot == step_ids


def test_training_unit_conforms(produced_run):
    tu_path = produced_run / "training-unit.json"
    assert tu_path.is_file(), "training-unit.json must be written next to trace.jsonl"
    tu = json.loads(tu_path.read_text())
    assert tu["training_unit_version"] == 1
    assert tu["run_id"] == produced_run.name
    assert tu["privacy"]["phi_status"] == "synthetic"

    tr = tu["trace_ref"]
    assert tr["project_slug"] == PROJECT_SLUG
    assert isinstance(tr["step_count"], int) and tr["step_count"] > 1

    r = tu["rating"]
    assert r["outcome"] in OUTCOMES
    assert r["verdict"] in VERDICTS
    f = r["failure"]
    assert isinstance(f["occurred"], bool)
    assert f["failure_type"] in FAILURE_TYPES
    assert f["severity"] in SEVERITIES
    assert isinstance(f["rationale"], str)
    # reward-derived failure-pin rule.
    _, steps, _ = _load_trace(produced_run)
    valid_idxs = {s["step_idx"] for s in steps}
    if f["occurred"]:
        assert isinstance(f["failure_step_idx"], int)
        assert f["failure_step_idx"] in valid_idxs, "pin must be an in-trace step"
        assert isinstance(f["failure_step_id"], str) and f["failure_step_id"]
    else:
        assert f["failure_step_idx"] is None
        assert f["failure_step_id"] is None
        assert f["failure_type"] == "none"
        assert f["severity"] == "none"

    # the computed oracle must be preserved on the unit and consistent with the
    # derived rating (human cannot flip reward: it lives here, re-derivable).
    o = tu["oracle"]
    assert o["reward"] in (-1, 0, 1)
    if o["reward"] == 1:
        assert r["verdict"] == "good" and f["occurred"] is False
    else:
        assert r["verdict"] == "bad" and f["occurred"] is True
