# Universal Trajectory Contract for Policy Retrieval

## Objective

Make the policy-retrieval trajectory environment emit **one real browser-retrieval
trajectory** for a single row (UHC Commercial, CPT 27447) into the **same universal
contract** the Plinth-app synthetic-emr trajectory system uses — `trace.jsonl`
(RunHeader + per-step StepRecord + ArtifactRecord), per-step `step_<id>/screenshot.png`
captured from genuine navigation, and `training-unit.json` — so the existing Plinth
replay + rate review UI/harness consumes our runs unchanged, while **preserving the
computed auto-oracle** and having it pre-fill the operator's rating.

One universal review surface for both what this env does and what the Plinth session does.

## Original Request

"we need ours to have per step screenshots and adhere moreso to what we have there but
for our use-case. is that feasible? i want one universal solution ... lets do your
recommendation" — the recommendation being **real browser retrieval** (the agent
genuinely navigates a payer portal/search to find the policy PDF), chosen over
schema-only alignment because only a genuine multi-step trajectory is worth replaying.

## Intake Summary

- Input shape: `existing_plan`
- Audience: Andrew (product/domain lead) + operators who review+rate captured runs on the universal Plinth surface
- Authority: `approved` (user picked the real-browser fork and said "lets do your recommendation")
- Proof type: `demo` + `review` (replay/harness render + schema/isolation audit)
- Completion proof: a real multi-step browser trajectory for one row stored in the Plinth
  run-dir contract, consumed by the Plinth replay UI/harness, computed oracle preserved and
  pre-filling the rating — verified by schema check + replay/harness render + oracle tests +
  non-faked evidence.
- Goal oracle: see below.
- Likely misfire: (1) faking the trajectory (single deep-link fetch dressed as multi-step,
  or synthesized screenshots); (2) schema drift so the Plinth replay UI can't consume our
  runs; (3) letting the human rating override/replace the computed oracle; (4) rebuilding a
  capture engine from scratch instead of reusing browser-trace/synthetic-emr-runner;
  (5) editing existing Plinth app files or the validated kiss_oracle logic destructively.
- Blind spots considered:
  - Deep-link reality: today's ground-truth target is a direct PDF URL; a genuine multi-step
    trajectory needs a real navigation surface (payer provider portal or search) to drill to
    that PDF, else screenshots are cosmetic.
  - Engine coupling: `synthetic-emr-runner.ts` targets the synthetic-EMR app + Plinth
    storage-key minting; reuse likely needs a thin repo-local wrapper to point at an arbitrary
    payer URL and write a repo-local run-dir.
  - Two run-dir conventions (KISS flat `runs/` vs Plinth `$HOME/clawd/state/.../run-dir`);
    the emitted contract must land where the replay UI/harness reads it.
  - Oracle-to-rating mapping must not let the human flip the computed reward.
  - PEP 668 / Playwright not in kiss-venv; capture likely stays in the Node engine, invoked
    from the Python runner via subprocess.
  - Live click-through may be env-blocked (single dev server per app dir; prod off-limits);
    a sanctioned harness render on the REAL screenshots is acceptable proof.
- Existing plan facts (preserve + validate): real-browser fork; emit per-step screenshots +
  trace.jsonl + training-unit.json in the Plinth contract; preserve computed kiss_oracle and
  have it pre-fill the rating; reuse the existing Playwright+CDP engine; KISS one row; do not
  edit existing Plinth app files or prod; the auto-oracle is load-bearing, not to be rewritten.

## Goal Oracle

`A REAL multi-step browser-retrieval run for the UHC/CPT-27447 row produces a run-dir with
trace.jsonl (RunHeader + per-step StepRecord + ArtifactRecord), per-step step_<id>/screenshot.png
from genuine navigation, and training-unit.json — all conforming to Plinth capture-trace.ts
types — such that the existing Plinth replay player/harness loads and plays the run, and our
computed oracle (kiss_oracle URL host+path compare) pre-fills training-unit rating.failure_step_idx
+ failure_type=retrieval which an operator can confirm/correct.`

The PM must keep comparing receipts to this oracle. A run that renders but is single-step, has
synthesized screenshots, drifts the schema, or lets the human override the computed reward does
NOT satisfy it.

## Goal Kind

`existing_plan`

## Current Tranche

One coherent vertical slice: a single real browser-retrieval trajectory for one row, emitted
into the Plinth contract, replayable, with the computed oracle preserved and pre-filling the
rating. Expanding to the remaining 38 rows, and any promotion of the Plinth review UI, are
explicitly separate FUTURE decisions and out of scope here.

## Non-Negotiable Constraints

- Never fake the trajectory: it must be a genuine multi-step browser navigation with real
  screenshot bytes and a real fetched policy (real sha256). No synthesized frames, no
  single-deep-link-dressed-as-multi-step.
- The computed oracle stays computed (kiss_oracle URL host+path compare, never hardcoded True)
  and genuinely discriminates (wrong URL -> correct=false/reward=0). The human rating pre-filled
  from it may be confirmed/corrected but must NEVER flip the computed reward.
- Reuse the existing Playwright+CDP browser-trace engine; do not rebuild capture from scratch.
- Do not edit any existing Plinth app file or touch prod `:3010`. Reference Plinth schemas/engine
  read-only; adapt via a repo-local wrapper if needed.
- Emitted schema must conform to Plinth `capture-trace.ts` types so the existing replay UI/harness
  consumes it unchanged.
- Preserve the existing validated `synthetic_harness/kiss_oracle.py` discrimination and tests.
- KISS: one row, one real trajectory this tranche.

## Stop Rule

Stop only when a final audit maps receipts + verification back to the oracle and records
`full_outcome_complete: true`. Do not stop after Scout/Judge planning. A live click-through may
be env-blocked (single dev server per app dir; prod off-limits); if so, a sanctioned harness
render that exercises the REAL replay timing/alignment on the REAL captured screenshots +
on-disk schema verification is acceptable proof for this tranche, with the residual live-click
gap recorded honestly.

## Slice Sizing

The real-browser run + contract emission + oracle pre-fill is one vertical slice — build it
whole, review it whole. Tiny tasks only if a specific risk (e.g. engine-adaptation unknown or
schema-conformance edge) needs isolating.

## Canonical Board

Machine truth: `docs/goals/universal-trajectory-contract/state.yaml`.
If this charter and `state.yaml` disagree, `state.yaml` wins.

## Run Command

```text
/goal Follow docs/goals/universal-trajectory-contract/goal.md.
```
