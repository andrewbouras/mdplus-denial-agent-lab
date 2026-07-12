# browser_capture — real UHC policy-retrieval → Plinth trajectory contract

Repo-local Playwright capture that produces ONE **genuine** multi-step
browser-retrieval trajectory for the UHC Commercial / CPT-27447 row and emits it
into the **existing Plinth synthetic-emr trajectory contract**, so the EXISTING
Plinth replay+rate reader/harness consumes it unchanged.

Nothing is faked: a real Chromium navigates a real UHC policy surface, every step
is screenshotted with real PNG bytes, and the selected policy PDF is fetched for
real (real sha256).

## What it does

`capture_uhc_policy.mjs` drives a real browser through six real steps, each of
which appends a Plinth `StepRecord` + a real screenshot `ArtifactRecord`:

| step | name           | real browser action                                   |
|------|----------------|-------------------------------------------------------|
| 0    | open_index     | open the Commercial medical-drug policy index/search  |
| 1    | search_scan    | type the knee/arthroplasty query, scan the list       |
| 2    | rank_select    | rank visible candidates + select one (oracle grades)  |
| 3    | open_policy    | navigate the browser to the selected policy link      |
| 4    | fetch_inspect  | fetch the selected PDF over the network + inspect      |
| 5    | return_policy  | return the selected policy URL as the final answer     |

`plinth_trace_writer.mjs` is a **standalone** re-implementation of the Plinth
record shapes + on-disk layout (RunHeader / StepRecord / ArtifactRecord, the
`t/<tenant>/p/synthetic-emr-demo/runs/<runId>/<step_id>/<leaf>` storage key, and
the `$HOME/clawd/state/projects/synthetic-emr-demo/runs/<runId>/` run-dir). It
imports **no** Plinth file — it just writes byte-for-byte where the Plinth reader
(`read-trace.ts`) and replay harness look, so the run loads unchanged.

## Navigation surface

- **live** (default via `auto`): `uhcprovider.com` Commercial medical-drug policy
  index → drill to `surgery-knee.pdf`.
- **mirror** fallback (when live is flaky/blocked/JS-gated): a locally-served
  **real-content** mirror under `local_mirror/` — the real fetched policy index
  (255+ real entries, live search box) plus the **real** `surgery-knee.pdf` and
  `joint-procedures.pdf` bytes — navigated over real HTTP by the real browser.
  Still a genuine multi-step browse; the selected link maps back to its canonical
  live UHC URL, which is the identity the oracle grades.

`--surface auto|live|mirror` selects; `auto` tries live first, falls back to
mirror, recording `live_error` honestly.

## Browser

Uses the ms-playwright bundled Chromium if downloaded, else drives **snap
Chromium** (`/snap/bin/chromium`) via Playwright `executablePath`
(override with `PW_CHROMIUM_EXE`). `@playwright/test` is resolved from the Plinth
app's `node_modules` (the Python orchestrator sets `NODE_PATH`), so nothing is
installed into this repo and no Plinth file is touched.

## Run it

Driven by the Python orchestrator (computes the oracle, writes
`training-unit.json`):

```
python scripts/emit_plinth_trace.py --row data/policy_platform/kiss_row_uhc_27447.json
```

Direct Node run (capture only, prints a `__CAPTURE_SUMMARY__` JSON line):

```
NODE_PATH=/home/clawd/plinth-v1/tools/plinth-app/node_modules \
  node browser_capture/capture_uhc_policy.mjs --row ../data/policy_platform/kiss_row_uhc_27447.json
```

## Oracle → rating

The computed `kiss_oracle` verdict (`synthetic_harness/kiss_oracle.py`, never
hardcoded) is mapped onto the Plinth rating by
`synthetic_harness/plinth_contract/oracle_to_rating.py`:

- `reward=1` → success/good, no failure.
- `reward=0` (reachable but wrong pick) → failure/bad, `retrieval`, `major`,
  failure pinned to the **rank/select** step.
- `reward=-1` (unreachable/not-PDF) → failure/bad, `critical`, pinned to the
  **fetch/return** step (`navigation` if a nav step failed, else `retrieval`).

`reward` is derived from the trace's real fetch facts and lives on the unit's
`oracle` block — an operator may confirm/correct the *rating* but cannot flip the
computed reward.
