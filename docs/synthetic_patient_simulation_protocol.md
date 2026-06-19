# Blind Synthetic Patient Simulation Protocol

This internal harness tests the real denial-navigation workflow without changing the patient-facing product.

## Roles

- **Case author:** creates a policy-anchored case and sealed answer key.
- **Patient actor:** Claude Code receives only facts a realistic patient could know.
- **Orchestrator:** Codex records relayed messages and coordinates isolated retrieval arms.
- **Library agent:** searches only the existing source library.
- **Web agent:** performs fresh official-source web retrieval without reading the library arm.
- **Evaluator:** compares frozen outputs with unsealed ground truth.
- **Human reviewer:** adjudicates source scope, safety-sensitive advice, and judge disagreements.

## Evidence Rules

- Logs contain observable actions, searches, source decisions, messages, outputs, timestamps, and concise decision summaries.
- Logs must not contain private chain-of-thought.
- Message envelopes and event logs are hash-chained.
- Original outputs are never overwritten by evaluation or human corrections.
- Ground truth remains sealed until both retrieval arms are finalized.

## Directory Boundary

Claude Code receives only the absolute `patient_workspace` path for the active episode. It must not inspect parent or sibling directories. The patient workspace contains its prompt, patient-visible packet, inbox, outbox, and transcript log. Sealed truth and system-arm artifacts are outside that workspace.

The user relays copy/paste messages between Claude and Codex during the calibration pilot. Every relay must retain the episode ID, message ID, sequence, and exact body.

## Current CLI

```bash
python3 -m synthetic_harness.cli init
python3 -m synthetic_harness.cli message --episode <path> --sender orchestrator --recipient patient_actor --body "..."
python3 -m synthetic_harness.cli log-event --episode <path> --role orchestrator --arm shared --event-type example --status succeeded --summary "..."
python3 -m synthetic_harness.cli verify --episode <path>
```

## Case Authoring

List high-confidence policy anchors:

```bash
python3 -m synthetic_harness.cli list-candidates
```

Create an episode, prepare truth and patient-packet JSON from the templates under
`synthetic_harness/templates`, and seal the case:

```bash
python3 -m synthetic_harness.cli author-case \
  --episode <episode-path> \
  --criteria-id <criteria-id> \
  --truth <truth-input.json> \
  --patient-packet <patient-packet.json>
```

The command derives the canonical policy anchor itself, verifies the source file
against its registry checksum, rejects answer-key fields in the patient packet,
encrypts ground truth, and stores the passphrase in the controller-owned key
directory outside the episode.

Prepare Claude after case authoring:

```bash
python3 -m synthetic_harness.cli prepare-patient --episode <episode-path>
```

This produces an episode-specific role prompt and the initial intake envelope.
Claude must reply using the exact `PATIENT_ACTOR_RESPONSE` block defined in that
prompt. Save the pasted response to a text file, then ingest it with:

```bash
python3 -m synthetic_harness.cli record-patient-response \
  --episode <episode-path> \
  --response-file <relayed-response.txt>
```

Later follow-up questions are logged and rendered for copy/paste using:

```bash
python3 -m synthetic_harness.cli follow-up \
  --episode <episode-path> \
  --body "Your patient-answerable question"
```

After the initial patient submission is recorded, prepare both independent
retrieval work orders:

```bash
python3 -m synthetic_harness.cli prepare-arms \
  --episode <episode-path> \
  --arm both
```

The library arm may inspect the source registry and scraped policy library but
not pre-extracted criteria. The web arm may browse current official sources but
may not inspect any local policy artifact, registry, criteria extraction, or the
other arm. Both receive only the patient-visible message transcript, never the
actor's full packet.

The web worker uses the controller's dedicated macOS `sandbox-exec` read
barrier as its sole OS sandbox. Codex's managed child sandbox is disabled for
that process because macOS rejects nested sandbox profiles. Retrieval stays on
direct shell and HTTP tools inside the inherited boundary; MCP, browser-control,
and node-repl child runtimes are excluded from the web-arm execution path.

## Internal Test Cockpit

The local UI accepts a synthetic patient's denial letter, visible card details,
procedure, and patient-level recollection. Starting an episode creates the same
hash-chained record and launches fresh isolated Codex processes for the selected
retrieval tracks.

Build and run:

```bash
cd ui
npm install
npm run build
cd ..
python3 -m synthetic_harness.server
```

Open `http://127.0.0.1:8765`.

This is intentionally an internal product-like test surface. It exercises
intake, retrieval, policy parsing, evidence display, follow-up, and action
generation, but it is not a production patient application and does not yet
provide accounts, PHI operations, authentication, or clinical deployment
controls.

The first human-review gate occurs at source selection. When an arm chooses a
policy, the UI renders the captured document when possible and requires one of
four explicit decisions:

- Confirm the selected policy.
- Reject it as inapplicable or incorrect.
- Upload a replacement PDF/HTML/text source.
- Continue without providing a correctness label.

The decision, selected-result checksum, notes, and any replacement-file checksum
are appended to the episode audit trail. Downstream next-step output remains
hidden until the source is confirmed or review is explicitly skipped. Rejected
or replaced sources require a new reasoning run rather than allowing stale
conclusions to flow forward.

Each correction is versioned under the arm's `revisions/` directory. The
original frozen result and its accuracy label remain preserved. A rejected
source is explicitly excluded from the correction search; an uploaded source is
the only policy candidate for that correction. Only the newest validated
revision becomes `active_result.json`.

If an arm needs patient clarification, the UI shows one targeted question at a
time. The pasted answer is added to the hash-chained patient transcript and
starts a versioned analysis against the same source. Source confirmation carries
forward only when the source fingerprint is unchanged.

For policy-anchored cases with sealed truth, autonomous evaluation becomes
available only after the requested arms are terminal and their sources have
been reviewed or explicitly skipped. The independent evaluator then scores
retrieval, denial inference, patient interaction, next steps, and confidence.
Human adjudication is appended afterward and never overwrites the automated
verdict.
