# OrthoAppeals patient-UI — implement Dr. Kassam review-call feedback

## Objective

Turn the documented decisions from the ~2026-07-12 patient-UI review call (Dr. Kassam,
Anish, Jocelyn) into actual implemented changes in the EXISTING mockups
(`mockups/` in the clone at `/home/clawd/mdplus-denial-agent-lab`), then dogfood the
result over a shareable HTTPS link Andrew can open and hand to an uncoached stress-test
cohort. This tranche stops short of wiring the "Build my appeal packet" backend CTA,
which is intentionally TBD.

## Original Request

"have you done /goal-prep to accomplish all of this actionable items or just documented
that they need to be done? can we do recon, dev, and dogfood if we haven't done so
already"

(The "actionable items" are the review-call decisions captured in
`memory/project_ui_review_call.md`.)

## Intake Summary

- Input shape: `existing_plan` (7 concrete items with clinical rationale, already documented)
- Audience: patients appealing a denied knee replacement — including low-tech-comfort older adults; the stress-test cohort is uncoached parents/grandparents. Secondary: Dr. Kassam, Anish, Jocelyn, Andrew.
- Authority: `approved` (Andrew asked to run recon/dev/dogfood on these items)
- Proof type: `demo`
- Completion proof: Andrew opens a shared link and sees all 7 items reflected; mobile/desktop split honored; final CTA left TBD.
- Goal oracle: Andrew (+ uncoached testers) open the updated mockups over a shared link and confirm the feedback is visibly reflected.
- Likely misfire: building a new UI instead of editing the existing mockups; re-synthesizing coded flows; over-polishing one screen; making the denial-letter upload merely present rather than prominent/near-mandatory; re-adding the date/session-count questions the call dropped; wiring the real backend.
- Blind spots considered: desktop v1-vs-v3 choice; location of Akin's ~20-procedure list; real phone camera capture; real voice-to-text with fallback; state→insurer gating data source; editable prepopulated "yes" answers.
- Existing plan facts: see `state.yaml -> goal.intake.existing_plan_facts` (the 7 items + clinical model + mobile/desktop split + source-of-truth = the clone mockups).

## Goal Oracle

The oracle for this goal is:

`Andrew (and uncoached parents/grandparents) open the updated mockups over a shared HTTPS link and confirm the review-call feedback is visibly reflected — prominent/near-mandatory denial-letter upload with phone capture, recency-based conservative-care questions (2-of-4, prepopulated yes), category→subtype procedure picker, body-part-conditional imaging, a State question that gates the insurer list, and an optional voice-friendly "tell us your story" field — with mobile=A / desktop=1-or-3 honored.`

The PM must keep comparing task receipts to this oracle. Documentation, a created board,
or a single polished screen is not enough. The goal finishes only when a final Judge/PM
audit maps receipts and a WebFetch-verified shared link back to this oracle and records
`full_outcome_complete: true`.

## Goal Kind

`existing_plan`

## Current Tranche

Implement the 7 items into the existing static mockups, verifying each in a browser, then
serve the result over `/url` and hand Andrew the link. Continuous execution: Scout maps
the mockups + resolves the two open questions, Judge validates/sequences into vertical
slices, Workers implement (denial-letter upload first, as top priority), then dogfood, then
final audit. Do NOT build the "Build my appeal packet" backend CTA.

## Non-Negotiable Constraints

- Edit the EXISTING mockups in the clone (`/home/clawd/mdplus-denial-agent-lab/mockups`); it is source of truth. The card-folder copy re-syncs and would revert edits.
- Do not re-synthesize a coded/fake flow; refine the real mockups.
- Denial-letter upload must be prominent and near-mandatory, with phone-photo/camera capture — not merely present.
- Ask conservative-care by recency; do NOT re-introduce dates / session counts / months-of-PT up front.
- Never hand Andrew a `localhost` URL — expose over the tailnet via `/url` and verify with WebFetch before sharing.
- Use `.docx` rules etc. do not apply here (web mockups). Use the frontend-design skill for design work.
- Leave the "Build my appeal packet" final CTA as a visible placeholder only.

## Stop Rule

Stop only when a final audit proves all 7 items are implemented and reachable via the
shared link. Do not stop after Scout/Judge planning. Do not stop after one item. If the
desktop v1-vs-v3 choice or Akin's procedure list is unresolved, proceed with a labeled
default and flag it for Andrew rather than stalling; those are per-task flags, not
whole-goal blockers.

## Slice Sizing

Each of the 7 items is a genuine vertical slice (a working screen/behavior). Workers finish
a whole item; Judge reviews the whole item. Do not split an item into wrapper/contract
micro-tasks. Same-shape data edits (adding procedures, states, insurers) belong in one
Worker package.

## Canonical Board

Machine truth lives at:

`/home/clawd/mdplus-denial-agent-lab/docs/goals/patient-ui-review-feedback/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins.

## Run Command

```text
/goal Follow docs/goals/patient-ui-review-feedback/goal.md.
```
