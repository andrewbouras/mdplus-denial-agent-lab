# Denial Simulation Lab

The Denial Simulation Lab is an internal product-like environment for testing
orthopedic insurance-denial retrieval and reasoning with synthetic patients.
It does not replace or redefine the eventual patient-facing application.

## Start

```bash
./scripts/run_denial_simulation_lab.sh
```

Open:

`http://127.0.0.1:8766`

## Current workflow

1. Paste the synthetic denial letter and visible insurance-card details.
2. Run the internal-library arm, live-web arm, or both.
3. Review the selected policy and rendered document.
4. Confirm, reject, upload a replacement, or continue without a label.
5. If rejected or replaced, the system starts a versioned correction run.
6. Paste any targeted synthetic-patient follow-up answer.
7. Review the actionable next step.
8. For sealed policy-anchored fixtures, run autonomous evaluation and append a
   human adjudication.
9. Open **Accuracy overview** to see aggregate retrieval labels and benchmark
   scores.

Every patient message, source decision, agent event, result version, source
label, evaluation, and adjudication is recorded in a hash-chained episode
directory under:

`outputs/synthetic_patient_simulations/episodes/`

The live-web process is wrapped in a macOS read barrier that prevents access to
the internal policy library, extracted criteria, sealed truth, controller keys,
and the library-only arm. That outer profile is the web worker's sole sandbox;
the agent uses direct shell/HTTP retrieval so macOS is not asked to nest a
second sandbox inside it.

## Internal documentation

- `docs/synthetic_harness_architecture.md` — developer reference: component map,
  episode lifecycle, on-disk layout, integrity model, and HTTP API.
- `docs/synthetic_patient_simulation_protocol.md` — blind-evaluation roles,
  evidence rules, and the CLI authoring workflow.
