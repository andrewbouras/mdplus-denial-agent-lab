# Policy-retrieval trajectory environment — KISS v0

## Objective

Prove the storable data unit before any dashboard: for ONE payer-policy-retrieval row,
have an agent actually attempt retrieval and write a **real, structured trajectory to disk**
(`runs/run_XXXX.jsonl` steps + `runs/run_XXXX.meta.json` with an automatic oracle verdict),
plus a thin CLI reader that displays the steps and lets a reviewer mark where it went wrong.

This is bare essentials. No fleet view, no scrubber UI, no scorecard, no database. Just:
run one row for real → get a real file → read it → label it.

## Original Request

"can we build the full rl environment to be ran for our use cases?" — then narrowed, in
conversation, to: the use case is **policy retrieval** (find the governing medical-necessity
policy for payer + plan + CPT 27447), and the ask is to **start KISS / bare essentials** because
the existing design mockup stores nothing and is over-engineered. Build the smallest REAL thing
(a stored trajectory) first, then go further.

## Intake Summary

- Input shape: `existing_plan` (a concrete KISS plan exists; substantial existing repo code to map/reuse)
- Audience: Andrew (domain/product lead) + his human reviewers; downstream buyer = frontier labs
- Authority: `requested`
- Proof type: `artifact` (a real trajectory file on disk)
- Completion proof: one real `runs/run_XXXX.jsonl` + `runs/run_XXXX.meta.json` produced by an
  actual retrieval run for one row, with an oracle verdict computed from ground truth, readable
  and labelable via a thin CLI. Not hardcoded, not faked.
- Goal oracle: for the chosen row, does the agent's returned policy match the **known-correct**
  governing policy (right plan variant, current version) in the ground-truth registry
  (`data/policy_platform/source_registry.json` and/or the consolidated Google Sheet)?
- Likely misfire: rebuilding the fancy fleet/cockpit UI or the "full RL environment" (reward
  shaping, branching, 5 synchronized streams) before ONE real stored trajectory exists — or
  faking the trajectory with scripted data again.
- Blind spots considered:
  - The HTML mockup stores nothing; every value is hardcoded. A real system needs a data source
    + storage that do not exist yet.
  - The repo already targets "policy retrieval agents" (see `pyproject.toml`) and ships
    `source_registry.json` / `criteria_extractions.json` — map and reuse, don't reinvent.
  - The oracle must be automatic (compare retrieved policy to ground truth), not human-declared,
    or the output is just annotated data, not an RL environment.
  - PHI: policy retrieval uses PUBLIC payer documents, so no patient data — keep it that way.
  - Full RL env is the endgame, not v0.
- Existing plan facts (preserve and validate):
  - Data unit = two flat files per run: `runs/run_XXXX.jsonl` (one JSON line per step) +
    `runs/run_XXXX.meta.json` (row inputs + oracle verdict + human label).
  - Minimal step line: `{"i":N,"action":"...","choice/args":...,"obs":"...","self_verdict":"..."}`.
  - Minimal meta: `{row, payer, plan, cpt, target, oracle:{correct,reachable,reward}, label:{fail_state,failure_type,expert_action}}`.
  - Build order: (1) schema + storage, (2) one real run writes them, (3) thin reader/labeler.
  - Durable home = THIS repo (not the card folder, which sync reverts; not /tmp, which is ephemeral).
  - Task is policy retrieval only (not filing appeals).

## Goal Oracle

The oracle for this goal is:

`For the chosen row, the retrieved policy identifier equals the known-correct governing policy
(correct plan variant + current version) per the ground-truth registry — computed automatically,
recorded in run_XXXX.meta.json.oracle, and NOT overridden by the human label.`

The PM must keep comparing task receipts to this oracle. A pretty reader, a passing import, or a
file that merely exists is not enough — the file must contain a real run whose oracle verdict was
computed against ground truth.

## Goal Kind

`existing_plan`

## Current Tranche

Produce ONE real stored trajectory for one row plus a thin CLI reader/labeler, reusing existing
repo machinery where it fits. Stop there for review before expanding to more rows, running the
oracle at batch scale, adding parallelism, or building any dashboard/fleet UI.

## Non-Negotiable Constraints

- KISS: bare essentials only. Two flat files per run; no database, no UI beyond a thin CLI reader.
- No PHI: public payer policy documents only.
- Automatic oracle from ground-truth registry/Sheet; the human label supplements, never replaces, reward.
- Reuse existing `synthetic_harness/` + `data/policy_platform/` where it fits; do not reinvent.
- The trajectory must come from a REAL run; never hardcode or fake data and call it "stored".
- Durable code lives in this repo; commit only feature files deliberately (never `git add -A`).

## Stop Rule

Stop when a final audit proves the tranche outcome: one real stored trajectory (jsonl + meta with
automatic oracle) for one row, readable and labelable via the thin CLI. Do not expand scope to
more rows, batch oracle, parallelism, or dashboards within this tranche.

## Canonical Board

Machine truth lives at `docs/goals/policy-retrieval-env/state.yaml`. If this charter and
`state.yaml` disagree, `state.yaml` wins.

## Run Command

```text
/goal Follow docs/goals/policy-retrieval-env/goal.md.
```
