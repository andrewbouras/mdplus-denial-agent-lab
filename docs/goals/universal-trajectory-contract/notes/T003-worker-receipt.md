# T003 Worker receipt — real browser trajectory → Plinth contract

## What was built
A repo-local runner that produces ONE genuine multi-step browser-retrieval
trajectory for the UHC Commercial / CPT-27447 row and emits it into the EXISTING
Plinth synthetic-emr trajectory contract, consumed unchanged by the Plinth
`read-trace.ts` reader + replay harness.

- `browser_capture/capture_uhc_policy.mjs` — drives a REAL Chromium (ms-playwright
  bundled chromium if present, else snap `/snap/bin/chromium` via
  `executablePath`) through 6 real steps (open index → search/scan → rank/select →
  open policy → fetch/inspect → return), screenshotting each real page paint and
  fetching the real policy PDF (real sha256).
- `browser_capture/plinth_trace_writer.mjs` — standalone re-implementation of the
  Plinth RunHeader/StepRecord/ArtifactRecord shapes + on-disk layout + canonical
  `runArtifactKey` storage_key. Imports NO Plinth file; writes byte-for-byte where
  `read-trace.ts` / `HetznerNativeDriver` read.
- `browser_capture/local_mirror/` — real-content fallback: real fetched policy
  index (255 real entries + live search box) + real `surgery-knee.pdf` (sha256
  `ce887339…`) and `joint-procedures.pdf` bytes; served over real HTTP and browsed
  by the real browser when live is flaky.
- `synthetic_harness/plinth_contract/oracle_to_rating.py` — maps the computed
  `kiss_oracle` verdict onto the Plinth rating (reward-derived pin). Reward is
  never hardcoded and lives on the unit's `oracle` block (re-derivable from real
  fetch facts); a human confirms/corrects the rating but cannot flip reward.
- `scripts/emit_plinth_trace.py` — orchestrates: shells the Node capture, computes
  the oracle via unmodified `kiss_oracle.compute_oracle`, maps to rating, writes
  `training-unit.json`.

## Produced run (verify step 2)
- run_id: `run_0f50cb26e94e` (regex `run_[a-f0-9]{12}` ✓)
- run_dir: `$HOME/clawd/state/projects/synthetic-emr-demo/runs/run_0f50cb26e94e/`
- surface: live uhcprovider.com (auto; falls back to local real-content mirror)
- steps: 6, screenshots: 6 (real PNG bytes, all > 1000)
- selected: `…/comm-medical-drug/surgery-knee.pdf`
- policy sha256: `ce887339facae80eb6967da6d7f222a6c0310447fbbf363ae2430e2e82be3048`
- oracle: correct=true, reachable=true, reward=1
- rating: outcome=success, verdict=good, failure_step_idx=null, failure_type=none

## Non-faked evidence
- Real browser: ms-playwright chromium-1223 / snap Chromium 150, real page paints.
- Real screenshots: `verify_artifact_sha.py` recomputes sha256 of each on-disk PNG
  and asserts equality + byte_size match → PASS (6/6).
- Real PDF: fetched over the network, real sha256 matching the KISS ground truth.
- Oracle discriminates (NOT stuck-true): a wrong pick (observed during ranker
  tuning) yielded reward=0 → failure/bad, retrieval, major, pinned to the
  rank/select step. The unmodified `kiss_oracle` + its tests still pass.
- Loads through the REAL Plinth `read-trace.ts`: header + 6 steps + all 6
  screenshots resolve via `resolveFile(storage_key)` to base64 data URIs.

## Verify results (all pass)
1. pytest (kiss_run + oracle_to_rating + conformance) — 18 passed
2. emit_plinth_trace — run produced
3. run_id regex + trace.jsonl exists — pass
4. steps > 1 + all screenshots > 1000 bytes — pass
5. Plinth replay harness (tsx --test) — 5/5 pass
6. verify_artifact_sha — 6/6 screenshots verified
