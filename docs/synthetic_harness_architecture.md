# Synthetic Harness Architecture (Internal)

Developer reference for the Denial Simulation Lab (`synthetic_harness/`). For
operator instructions see `SYNTHETIC_LAB.md`; for the blind-evaluation contract
see `docs/synthetic_patient_simulation_protocol.md`.

## Purpose

An internal, product-like environment that exercises the real
orthopedic-denial workflow against synthetic patients. A synthetic patient's
denial information is submitted, two isolated retrieval arms (internal library
vs. live web) independently find and parse the governing policy, and the run is
scored against a sealed answer key. It does not replace the patient-facing
product and stores no PHI.

## Component map

Each module under `synthetic_harness/` owns one concern:

| Module | Responsibility |
| --- | --- |
| `integrity.py` | Canonical JSON, SHA-256 helpers, atomic writes, the append-only `HashChainLog` (each row commits to the previous row's hash). |
| `episode.py` | `Episode` lifecycle: creates isolated role workspaces (`patient_workspace/`, `system/`, `sealed/`, `evaluation/`, `review/`), the manifest, message envelopes, event logs, and `verify()`. |
| `authoring.py` | Policy-anchored case authoring: validates the patient packet has no answer-key fields, snapshots the canonical policy anchor against the registry checksum, and seals/encrypts ground truth. |
| `patient_actor.py` | Builds the Claude patient-actor role prompt, the intake envelope, parses the pasted `PATIENT_ACTOR_RESPONSE` block, and records follow-ups. |
| `arms.py` | Defines the arm result contract/schema, builds per-arm agent prompts and work orders, and enforces the library-only vs. web-only read boundaries. Holds `SOURCE_LIBRARY_ROOT`. |
| `sandboxing.py` | Writes the macOS `sandbox-exec` read barrier (`.sb`) for the web arm so it cannot read the local library, sealed truth, keys, or the sibling arm. |
| `results.py` | Validates arm results against the schema, ingests agent events, archives revisions, and freezes results (`frozen_result.json`, `active_result.json`). `both_arms_frozen()`. |
| `source_review.py` | The human source-selection gate: records Confirm/Reject/Upload/Skip, captures uploaded/confirmed sources, computes source fingerprints, and resolves the document to render. |
| `evaluation.py` | Post-freeze blinded evaluation: eligibility checks, evaluator work order + schema, verdict validation. |
| `adjudication.py` | Appends human adjudication on top of an automated verdict without overwriting it. |
| `metrics.py` | Aggregates retrieval labels and benchmark scores across all episodes for the accuracy overview. |
| `cli.py` | Command-line entry points (init, message, author-case, prepare-patient, prepare-arms, etc.). |
| `server.py` | Local HTTP UI + JSON API on `127.0.0.1`; orchestrates Codex subprocess launches for each arm/correction/follow-up/evaluation. |

## Episode lifecycle

1. **Author** (sealed cases) — `author-case` validates the packet, snapshots the
   policy anchor, encrypts ground truth into `sealed/`, and stores the passphrase
   in the controller key directory *outside* the episode. Direct UI submissions
   skip this and stay human-label-only (no answer key).
2. **Intake** — patient submission is recorded as a hash-chained message; the
   submission snapshot is persisted so reopening an episode restores the form.
3. **Prepare arms** — `prepare_both_arms` writes per-arm work orders, prompts,
   the result contract/schema, and (for web) the read barrier.
4. **Run** — `server.py` launches an isolated Codex process per arm. Library arm
   may read the registry + scraped library but not pre-extracted criteria; web
   arm may browse official sources but cannot touch any local policy artifact or
   the sibling arm.
5. **Freeze** — each arm's result is validated and frozen; original outputs are
   immutable.
6. **Source review** — the UI renders the selected document and requires
   Confirm / Reject / Upload replacement / Continue-without-label. Reject or
   Upload spawns a versioned correction run under the arm's `revisions/`; only
   the newest validated revision becomes `active_result.json`. Next-step output
   is hidden until the source is confirmed or review is explicitly skipped.
7. **Evaluate** (sealed cases only) — once requested arms are terminal and
   reviewed, the blinded evaluator unseals truth and scores retrieval, denial
   inference, patient interaction, next steps, and confidence.
8. **Adjudicate** — human corrections are appended; the automated verdict is
   preserved.

## On-disk episode layout

```
outputs/synthetic_patient_simulations/episodes/<episode_id>/
  manifest.json
  patient_workspace/
    inbox/   NNNN_<msg_id>.json     # orchestrator -> patient
    outbox/  NNNN_<msg_id>.json     # patient -> orchestrator
    logs/    messages.jsonl         # hash-chained message log
  system/
    shared/
    library_only/   work_order.json, AGENT_PROMPT.txt, result.json,
                    frozen_result.json, active_result.json, agent_events.jsonl,
                    runtime_status.json, attempts/, revisions/, captured sources
    web_only/       (same, plus web_read_barrier.sb)
    logs/           <arm>.events.jsonl   # hash-chained per-arm event logs
  sealed/    relay_integrity.json, sealed ground truth (encrypted)
  review/    source_feedback.jsonl
  evaluation/  automated verdict, adjudication
```

Directories are created `0700`; files are written atomically `0600`.

## Integrity model

- **Hash chains** — message and event logs use `HashChainLog`; every row carries
  `sequence`, `previous_hash`, and a `record_hash` over the canonical body.
  `Episode.verify()` re-walks every chain plus message envelope hashes.
- **Sealing** — ground truth is encrypted before any active role runs; the key
  lives outside the episode. Neither the patient actor nor the retrieval arms can
  read it.
- **Web sandbox** — the web arm runs under a macOS `sandbox-exec` read barrier as
  its *sole* sandbox (Codex's managed child sandbox is disabled to avoid nested
  profiles, which macOS rejects). Retrieval is restricted to direct shell/HTTP.
- **Immutability** — frozen results and accuracy labels are never overwritten;
  corrections and adjudications are append-only revisions.

## HTTP API (server.py)

Served on `127.0.0.1` (run script default `8766`; `server.py` default `8765`).

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/episodes` | Create a direct episode and launch the selected arms. |
| POST | `/api/episodes/<id>/follow-up` | Record a patient follow-up answer and rerun. |
| POST | `/api/episodes/<id>/source-feedback` | Confirm / reject / upload / skip the selected source. |
| POST | `/api/episodes/<id>/retry-arm` | Relaunch an arm. |
| POST | `/api/episodes/<id>/evaluate` | Run blinded evaluation (sealed cases). |
| POST | `/api/episodes/<id>/adjudicate` | Append human adjudication. |
| GET | `/api/episodes/<id>` | Episode snapshot for the UI. |
| GET | `/api/episodes/<id>/source-document/...` | Render a captured policy document. |
| GET | `/api/health` | Health + server build id. |
| GET | `/api/metrics` | Aggregate accuracy overview. |

The frontend lives in `ui/` (Vite/React). Build with
`cd ui && npm install && npm run build`; `server.py` serves `ui/dist` and refuses
to start if the build is missing.

## Internal source library

The library-only arm reads from `data/policy_library/` by default. Override it
with `MDPLUS_POLICY_LIBRARY_ROOT`. Registry and platform metadata default to
`data/policy_platform/` and can be overridden with
`MDPLUS_POLICY_PLATFORM_ROOT`. Real policy documents are intentionally not
included in this repository.

## Running tests

```bash
python3 -m pytest tests/test_synthetic_harness.py   # 21 tests
```

Tests cover hash-chain integrity, episode/message handling, the arm boundaries,
source-review versioning, single-label enforcement, and metrics.
