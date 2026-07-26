# PM findings: Blue Shield of California scope, and the CareFirst state pin

Author: PM thread, 2026-07-26. Firsthand fetches only, browser user agent, no login,
no credential, no payer telephone call.

Purpose: resolve two of the three human-dependency blockers T003 left open, without
consuming Andrew's time. Andrew delegated both decisions explicitly.

Status: APPLIED. Judge T013 ruled on these findings on 2026-07-26 and approved the
bm_0058 promotion, with two corrections to this note that are now made in place below,
marked "CORRECTED by T013". Worker T015 applied the result to `answer_key_v1.json` the
same day. The full record is in `notes/key-corrections.md`, entry dated 2026-07-26.

---

## 1. Blue Shield of California: bm_0058 RESOLVES, bm_0068 and bm_0079 DO NOT

### What T003 found, and why it was right to stop

T003 classed three Blue Shield of California rows as `unverified` because the knee policy
BSC7.10 never states which line of business it governs. I re-checked that claim from
scratch rather than trusting it. T003 was correct, and the problem is worse than one
document: Blue Shield does not publish line-of-business scope anywhere I could reach.

### BSC7.10 itself

- URL: `https://www.blueshieldca.com/content/dam/bsca/en/provider/docs/medical-policies/Knee-Arthroplasty-Adults.pdf`
- HTTP 200, no login, 24 pages, sha256 `761ec47ecf92563ed48d175638355c7dbe2db7ec6fd79f87343d6e2a14c42b0a`
- Contains CPT 27447 exactly once, in the Coding table.
- Term frequency across the full extracted text: `line of business` 0, `Marketplace` 0,
  `Medi-Cal` 0, `IFP` 0, `Individual and Family` 0, `does not apply` 0. The single hits on
  `Commercial` and `Advantage` are incidental prose, not scope: "commercially available
  patient-specific templates" and "little clear advantage to one approach over another".
- The nearest thing to a scope statement is a punt, quoted verbatim from the Benefit
  Application section: "Benefit determinations should be based in all cases on the
  applicable member health services contract language. To the extent there are conflicts
  between this Medical Policy and the member health services contract language, the
  contract language will control."

That sentence defers to a document we cannot see (the member's own contract). It does not
tell us which plan types the policy covers.

### Corroborating checks, both negative

- Medical policy index page `.../authorizations/policy-medical`: no scope statement, no
  Medicare Advantage carve-out, no separate MA policy page linked.
- Medical policy list page `.../authorizations/policy-medical/list`: policies are listed
  alphabetically with NO line-of-business column, filter, tab, or header. The only scope
  language is, verbatim: "The application of each Blue Shield of California medical policy
  is subject to regulatory requirements and/or plan specific benefits and limitations
  (Evidence of Coverage - EOC)." Again a pointer to an unseen document.
- Prior Authorization List PDF `.../docs/BSC-Prior-Auth-List.pdf`: HTTP 200, 8 pages,
  contains 27447 once, and contains ZERO occurrences of `Medicare Advantage`,
  `Commercial`, `Medi-Cal`, `IFP`, `line of business`, or `applies to`.

### The one row that DOES resolve: bm_0058, Medicare Advantage

Found on the Blue Shield utilization management page, which T003 did not reach.

- URL: `https://www.blueshieldca.com/en/provider/guidelines-resources/guidelines-procedures/utilization-management`
- HTTP 200, no login.
- **Hash, CORRECTED by T013: there is no usable hash for this page.** This note first
  recorded sha256 `d329984708e4c08ee6fca9216df93f60d5c2116dbc3ce1a1b331729bae409df3`.
  That digest does not reproduce. Judge T013 refetched and got
  `e5982dc0c713588bcedfdb345903f14f58494acf56990ff6761ae2f3462ea692`, and Worker T015
  refetched again and got `8ee08c1ee72002a63f8dc4ecfa6b52491bf6de6d381051a2832aafb3e879ec8d`.
  All three fetches returned HTTP 200, needed no login, and carried the identical
  paragraph below. The page rebuilds its markup on every request, so a raw-HTML sha256
  cannot serve as an identity check here. The key records `content_hash_stable: false`
  and pins identity to the verbatim string instead.
- **Quote, CORRECTED by T013: the span below starts one sentence earlier than this note
  first recorded.** The original start point, "The resources are not listed in use
  order...", drops the only clause that names Blue Shield as the user of the criteria,
  and on that shorter span the promotion is not supported. Verbatim, in full:
  "Blue Shield and Blue Shield Life use the utilization management criteria found in the
  following resources to determine medical appropriateness and coverage. The resources
  are not listed in use order for utilization management and medically necessary
  decisions. The specific hierarchy for each line of business is determined by regulatory
  government bodies. For example, Medicare requires use of the Medicare Managed Care
  Manual and NCD/LCD’s first." The apostrophe in `NCD/LCD’s` is U+2019, not ASCII.

On the extended span that is a payer-attested Medicare deferral, which is exactly the
`deferral_two_part` basis T003 defined and used on four other rows. One further
correction from T013: the page never writes the words "Medicare Advantage". The plan type
is identified by instrument, that is by the Medicare Managed Care Manual, CMS Pub. 100-16,
which instructs Medicare Advantage organizations only, and by two D-SNP-only entries in
the resource list. The key therefore marks this row `plan_type_named:
instrument_inferred`, while the other ten retrievable rows are `explicit`.

Independent corroboration from inside BSC7.10 itself, under its own section heading
"Medicare National Coverage", quoted verbatim: "Medicare does not have a National Coverage
Determination, but does have a Local Coverage Determination (LCD) for Total Knee
Arthroplasty (L36575) effective December 1, 2019."

So bm_0058 is attested by three independent artifacts that agree:

| Part | Source | What it attests |
|---|---|---|
| payer + plan type | BSC utilization management page | Blue Shield and Blue Shield Life use these criteria, and Medicare requires the Medicare Managed Care Manual and NCD/LCD first. Plan type is inferred from the instrument, not written on the page |
| governing document | BSC7.10 "Medicare National Coverage" section | No NCD exists; L36575 governs total knee arthroplasty |
| state + jurisdiction | CMS L36575 Contractor Information table | Noridian J-E, "California - Entire State" |

**Change APPLIED: bm_0058 moves from `unverified` to `retrievable`, basis
`deferral_two_part`.** Approved by Judge T013 on the extended quote above, and only on
that quote. Written into the key by Worker T015. The counted document is **A57685**, the
CMS Billing and Coding Article companion to L36575, which carries CPT 27447. CPT 27447
does not appear on the Blue Shield page itself, and the key records that truthfully.

### The two rows that stay unverified: bm_0068 and bm_0079

Commercial and ACA Marketplace. No Blue Shield document I could reach states that BSC7.10
applies to either line of business. Marking them retrievable would mean asserting scope the
payer never asserted, which is precisely the shortcut this benchmark exists to detect. They
stay `unverified`.

### Why this is a product finding, not just a data gap

A patient on a Blue Shield commercial plan cannot determine from public sources whether the
published knee policy governs their plan. Neither can we, and we tried. Any system that
answers that question confidently is inventing the answer. This is a strong argument for
the confident-wrong headline metric and worth carrying into the MD Catalyst pitch.

### If Andrew wants to close bm_0068 and bm_0079 later

The missing artifact is a Blue Shield Evidence of Coverage, or any provider manual page
listing which policies bind which product lines. Both are plausibly behind the provider
portal, which makes these candidates for reclassification to `gated` rather than
`unverified`. I did not reclassify them, because "probably behind a login" is a guess and
`gated` is supposed to mean established.

T013 ruled on this and adopted the reasoning above without change: bm_0068 and bm_0079
KEEP `unverified`, and must not be reclassified as `gated`. Four independent negative
checks establish the absence of a public scope statement, not the presence of a gated
one.

---

## 2. CareFirst state pin: KEEP MARYLAND

Andrew delegated this choice. T003 pinned Maryland. I checked whether that is defensible
and concluded it is the best available option, so no change is needed.

CareFirst operates through three underwriting entities across a three-part service area:
Maryland, the District of Columbia, and Northern Virginia.

The pin matters only because it selects the governing Medicare document:

| Service area | MAC and jurisdiction | Governing LCD |
|---|---|---|
| Maryland | Novitas J-L | L36007 |
| District of Columbia | Novitas J-L | L36007 |
| Northern Virginia | Palmetto GBA J-M | L33456 |

Maryland is the right pin for three reasons:

1. **It is correct for two of the three service areas.** Maryland and DC share Novitas J-L,
   so pinning Maryland yields the same governing document as pinning DC. Only Northern
   Virginia diverges.
2. **The divergent area is the smallest.** CareFirst serves Northern Virginia only, not the
   whole state. Pinning Virginia would make the row correct for the smallest slice of
   membership and wrong for the largest.
3. **Maryland is the largest membership base and the corporate home of CareFirst of
   Maryland, Inc.**

Recorded consequence, so this is not silently forgotten: if a real appeal ever concerns a
CareFirst member in Northern Virginia, the governing document is L33456 (Palmetto J-M), not
L36007. That is a per-patient routing rule for the product, not a defect in the benchmark
row. The eval asks a state-pinned question and the state is pinned to Maryland.

---

## 3. Net effect on the class counts, as applied

T013 approved and T015 applied. These are the counts now in
`data/policy_platform/answer_key_v1.json`.

| Class | T003 | Now, after bm_0058 |
|---|---|---|
| retrievable | 10 | 11 |
| gated | 17 | 17 |
| none | 6 | 6 |
| unverified | 5 | 4 |
| invalid | 1 | 1 |
| **total** | **39** | **39** |

Derived figures, also recorded in the key:

| Figure | T003 | Now |
|---|---|---|
| scored rows | 33 | 34 |
| scored payers | 11 | 11 |
| Medicare Advantage scored rows | 8 | 9 |
| unique documents on the retrievable side | 6 | 7 |
| unique issuers on the retrievable side | 4 | 4 |
| strong attestation rows | 8 | 9 |
| strong subset documents | 5 | 6 |
| strong subset issuers | 3 | 3 |
| weak attestation rows | 2 | 2 |
| excluded, unverified | 5 | 4 |
| excluded, invalid | 1 | 1 |

Arithmetic: 11 plus 17 plus 6 equals 34 scored; 34 plus 4 unverified plus 1 invalid
equals 39.

The independence caveat does not improve much. The retrievable rows now rest on 7 unique
documents rather than 6, since bm_0058 introduces A57685, the companion article to
L36575, with the Blue Shield utilization management page as its deferral attestation.
Report both numbers together, per rubric section 0.1. Two limits on the improvement, from
T013 and repeated here so the report cannot overstate it. The issuer count does not move
at all, staying at 4 overall and 3 in the strong subset, and that is the binding
constraint on the retrieval side. Excluding the one instrument-inferred row, the strong
subset is 8 rows, 5 documents and 3 issuers, which is what T003 already had.
