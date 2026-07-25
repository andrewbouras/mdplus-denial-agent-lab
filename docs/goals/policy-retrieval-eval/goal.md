# OrthoAppeals policy-retrieval eval + patient-website wireup

`state.yaml` is board truth. This file is the editable charter.

## What was originally asked

Parse the 2026-07-25 call between Andrew Bouras and Akin Adio into next steps, then compile those steps into an executable board.

## What we are trying to accomplish

Turn the agreed plan into a trustworthy, calibration-graded evaluation of how well Claude finds the controlling insurance policy for a denied knee replacement, and connect that capability to the patient website. Reach a demoable state before MD Catalyst on **2026-08-17**.

## Input shape

`existing_plan`. The team already agreed the approach. This board preserves those decisions and validates their sequencing; it does not re-litigate them.

## The goal oracle

**Calibration, not raw accuracy.**

The model must correctly say either "I found the controlling document" or "I cannot confidently identify it." A confidently wrong answer is the failure that matters, because it causes a patient to file an appeal quoting criteria that do not apply to their plan.

So the headline metric of every run is the **count of confident-but-wrong answers**, reported above accuracy.

Final proof requires all three:
1. A corrected answer key where every surviving row carries a URL that was actually fetched, returns HTTP 200 without a login, and contains CPT 27447.
2. A cold eval run, meaning the retrieval model has no access to the key, emitting a scored report whose confident-wrong rows are zero or explicitly enumerated.
3. A walkthrough of the patient website producing a retrieval result for at least one case, end to end.

## Non-negotiable constraints

- **No fine-tuning and no training from scratch.** Improvement is in-context only: harness, CLAUDE.md, skills, routing directory. Training an open-source model is at most a side proof that the dataset has value, and is not the product.
- **Do not seed work that depends on phoning payers for login-gated policies.** That path was tried and failed. Payers demanded an NPI, treated the caller as a provider opening a practice, and redirected to marketing.
- **Benchmark Claude alone first.** Multi-model comparison is deferred until ground truth exists.
- **The scoring rubric is fixed in writing before any run.** If the definition is chosen after seeing results, it will be chosen to flatter the score.
- **Appeal generation is out of scope for this tranche.** Producing the patient-facing appeal across the permutation of denial reasons is acknowledged as the biggest eventual value, and is explicitly deferred.
- **Never hand the user a localhost URL.** Expose anything viewable over the tailnet.

## The likely misfire to avoid

Reporting a flattering accuracy number computed against a benchmark whose labels are wrong, self-inconsistent, or partly derived from the AI's own earlier output. A close second: polishing the eval and never wiring the website.

## Known-broken starting state

The benchmark spec `data/policy_platform/seed_review_39_spec.json` holds 39 rows for CPT 27447, counted as 13 public, 20 login-gated, 6 with no public policy.

Of the 13 public rows, 8 are Medicare Advantage and the key contradicts itself. Six rows point at one CMS document, LCD L36007, while two point at the plan's own document. One LCD cannot govern Michigan, North Carolina, the Maryland/New Jersey/Pennsylvania region, and Washington at the same time, because each LCD is bound to a single MAC jurisdiction.

Verified firsthand so far:

- **bm_0063 Premera is an invalid row.** Premera exited the Medicare Advantage market on 2025-01-01. Its public policy 7.01.550 states verbatim that it does not apply to Medicare Advantage, and cites L36575 (Noridian JF, covering WA and AK), not L36007.
- **bm_0065 UPMC is mislabeled.** UPMC publishes its own policy MP.PA.133 that explicitly applies to CMS-MA HMO, PPO, and DSNP and lists CPT 27447. It cites L36007, which is correct for Pennsylvania. Its policy list is not search-indexed and is served from an open JSON endpoint.

Still unverified: **bm_0056** BCBS Michigan, **bm_0057** BCBS North Carolina, **bm_0059** CareFirst, **bm_0061** Horizon BCBS NJ.

## Open human decision, owned by Andrew

When a Medicare Advantage plan genuinely defers to Medicare, what does a real appeal actually cite: the Medicare regional rule, or the plan's own page stating that it follows Medicare?

This sets the scoring convention and must be settled before the run. The board is designed so that research is not wasted while it is unsettled: rows record both candidate answers, so the ruling can be applied afterward without redoing work.

## Live risk

Cutting the 20 login-gated rows leaves 13, and several of those are turning out invalid or mislabeled. The scored set may shrink to single digits and be too small to support strong claims. The mitigation on the table is to obtain real denial cases from Phil, a colleague of Dr. Kassam, including recent denials with state, procedure, and plan, ideally with the actual document and his working trace, plus his review of the tool.

## Team and capacity

- **Andrew Bouras**: product and domain lead, does the building.
- **Akin Adio**: returns to clinical rotations 2026-07-27, capacity drops sharply, works well when given an exact next step.
- **Anish Easwaran**, **Jocelyn Chen**: on the team; Jocelyn owns the pitch deck.

Agreed working protocol: Andrew works one step at a time and pushes to GitHub after each; Akin's agent checks GitHub before starting anything, to avoid duplicate work.

## What counts as enough for this tranche

The three proofs listed under the oracle. Not a plan, not a passing scout report, and not a high accuracy number resting on unverified labels.
