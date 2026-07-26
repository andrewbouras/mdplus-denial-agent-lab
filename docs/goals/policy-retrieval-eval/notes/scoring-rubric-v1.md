# RUBRIC v1.5: OrthoAppeals policy retrieval, CPT 27447

**Frozen 2026-07-25 by Judge task T002, BEFORE any eval run.**
Any change requires a new version number and invalidates all prior comparisons.
Every run artifact must record `rubric_version` and `key_sha256` so a rubric edited
after results is detectable.

`rubric_version: 1.5`

### Amendment log

| Version | Date | Change | Runs invalidated |
|---|---|---|---|
| 1.0 | 2026-07-25 | Original freeze (T002). | none |
| 1.1 | 2026-07-26 | Added section 5.1, the 42 CFR 422.101(b) authority ladder and the uniform-election escape. Softened the section 5 unconditional out-of-jurisdiction rule to defer to 5.1. | **none. No eval run had executed. T005 had not started.** |
| 1.2 | 2026-07-26 | Judge T012 rulings: added the unverified excluded class and its asymmetric grading; admitted scope_by_exclusion under a three-condition test (new 2.1); pinned all statistical denominators to unique documents and unique issuers; made verbatim caveat propagation mandatory (new section 9); corrected the sufficiency figures to the exact-binomial method already used in 0.1. | **none. No eval run had executed. T005 had not started.** |
| 1.3 | 2026-07-26 | Judge T013 ruling: promoted bm_0058 to `retrievable` under a new part-one admissibility test (new 2.2); added the `plan_type_named` field and the instrument-inferred distinction; moved every denominator by one row and one document. | **none. No eval run had executed. T005 had not started.** |
| 1.4 | 2026-07-26 | Arithmetic correction only. The v1.3 ISSUER-BOUND line and the section 0.1 prose both attached 63.2% to N=4 issuers. The exact binomial gives 52.7% at N=4; 63.2% is the N=3 value. Caught by the T004 harness, which computes from the formula rather than copying the prose. No definition, threshold or count changed. | **none. No eval run had executed. T005 had not started.** |
| 1.5 | 2026-07-26 | Judge T019 rulings. Added section 2.3, the five-condition vendor-deferral test: V1 payer binding with the CPT code and the plan type on the payer's own page, V2 a public criteria document from the named vendor containing CPT 27447 and quantified criteria, V3 plain-HTTP reachability from the printed link with no JavaScript, V4 no contrary marking, V5 a displacement check against the section 5.1 authority ladder. Added Guard M excluding Medicaid rows and Guard S requiring the vendor's substitution clause to be recorded verbatim. Added the attestation basis `deferral_vendor_two_part` and counted it in the strong subset. Made a blocked fetch a distinct outcome, `BLOCKED_FETCH`, excluded from the confident-wrong numerator and denominator, never counted correct, printed on its own headline line by row_id, requiring a documented retry under at least two request shapes, and not reportable at b >= 7. Reissued the section 0.2 table for three row moves: bm_0072 gated to retrievable, bm_0062 and bm_0083 gated to unverified. | **none. No eval run had executed. T005 had not started.** |

All five amendments are legitimate under the freeze on the same test, because the freeze
exists to stop definitions moving *after results are visible*. Zero results existed at each
amendment. No threshold moved: the `confidence >= 80` boundary, the correctness tiers, and
the confident-wrong definition are all unchanged from v1.0. Section 5.1's authority ladder is
untouched by v1.2, v1.3, v1.4 and v1.5.

**Disclosure required with any v1.3 or later number.** The v1.3 promotion of bm_0058 improves the
reportable retrieval ceiling, from a 39.3% upper bound at 6 unique documents to 34.8% at 7.
A change that flatters our own number was made by a Judge, not by the party who found the
evidence, and the Judge recorded the incentive check in its receipt. Two facts limit the
flattery and must travel with it. The issuer bound does not move at all, staying at 4
issuers and 3 in the strong subset, which is the binding constraint on the retrieval side.
The headline confident-wrong denominator moves only from 33 to 34, an 8.7% to 8.4% bound.

**Disclosure required with any v1.5 or later number.** The v1.5 promotion of bm_0072 moves the unique-issuer count from 4 to 5 and the unique-document count from 7 to 8, improving the reportable retrieval ceiling from 52.7% to 45.1% on the binding issuer bound and from 34.8% to 31.2% on the document bound. Section 0.1 names the issuer count as the binding constraint, and this is the FIRST change on this board to move it; the v1.3 promotion of bm_0058 moved no issuer at all. Three facts bound the flattery and must travel with it on the same line. The safety bound WORSENS, from 8.4% at N_scored 34 to 8.9% at 32. The honest-abstention pool SHRINKS from 23 rows to 20, so an always-abstain policy now collects less free credit. The unverified coverage gap GROWS from 4 of 39, 10.3%, to 6 of 39, 15.4%, and is printed as a limitation of the benchmark. The Judge that ruled was not the party that found the evidence; it reproduced the payer page 2 of 2 and the vendor criteria document 3 of 3 byte-identical before ruling, and it walked the vendor index by plain HTTP after the PM had recorded that the index could not be walked without JavaScript.

The harness reads every count from section 0.2 and never hardcodes one anywhere else.

---

## 0. Scope ruling (why this rubric scores 39 rows, not 13)

The agreed plan said "remove login-gated rows from the benchmark." That is correct
for measuring retrieval and wrong for measuring calibration.

You cannot ask "did the model find the right document" for a row whose document sits
behind a login. But the headline metric is not retrieval. It is calibration. A model
that confidently invents a knee policy for a plan that publishes none is exactly the
failure being hunted, and 26 of the 39 rows test precisely that failure. Discarding
them deletes two thirds of the evidence about the one metric declared as the headline.

Three scored classes, plus two classes excluded from every headline denominator:

- **RETRIEVABLE** (13 public, minus invalids, plus any gated row the model cracks).
  Correct behavior: name the document.
- **GATED** (20 rows). Correct behavior: abstain, and say the policy appears to exist
  but is not publicly retrievable. This is NOT scored as "must abstain," because the
  human reviewers who applied that label can be wrong. UPMC proves it: its policy list
  is not search-indexed but IS served from an open JSON endpoint, which is exactly how
  a reviewer concludes "gated" about a document that is in fact public. A claim on a
  gated row goes to adjudication.
- **NONE** (6 rows). Same adjudication, stricter. Fabricating a policy here is the worst
  outcome and gets its own counter.
- **INVALID** (1 row). The row is not answerable because the product does not exist.
  Excluded from every denominator, listed by row_id with its reason, never deleted.
- **UNVERIFIED** (6 rows at v1.5, was 4). We pursued public evidence in good faith and
  could not settle the label. Excluded from every headline denominator. Graded ONLY on
  outcomes that are wrong under every possible world state, and abstention here earns no
  credit. See section 4.1.

Property worth naming: this is the only design in which the benchmark grows without
further human research. Every gated row the model legitimately cracks becomes a
validated retrievable row for the next run.

## 0.1 Statistical sufficiency, stated honestly

With zero observed confident-wrong answers, the 95% upper bound on the true error rate
is `1 - 0.05^(1/N)`:

| Scored N | 95% upper bound on confident-wrong rate |
|---|---|
| 3 | 63.2% |
| 4 | 52.7% |
| 5 | 45.1% |
| 6 | 39.3% |
| 7 | 34.8% |
| 8 | 31.2% |
| 9 | 28.3% |
| 10 | 25.9% |
| 11 | 23.8% |
| 13 | 20.6% |
| 32 | 8.9% |
| 33 | 8.7% |
| 34 | 8.4% |
| 39 | 7.4% |
| 60 | 4.9% |

**Method footnote, load-bearing.** These are exact binomial one-sided bounds,
`1 - 0.05^(1/N)`, not the `3/N` rule-of-three shorthand. The shorthand overstates every
bound in this table and must not be used anywhere in this benchmark. Mixing the two methods
inside one document was a real error caught by Judge T012: a brief circulated `46%` for
N=6, which is in fact the bound for N=5.

At N=9 a clean sweep is compatible with being confidently wrong more than one time in
four. That is not a result.

**Mandatory caveat, to be stated out loud in any presentation:** these 39 rows are not
39 independent draws. They are 11 payers crossed with 4 lines of business. After the T003
rebuild, the T013 promotion and the T019 rulings, 32 rows are scored across 11 payers, and
the retrievable side collapses to **8 unique documents issued by only 5 issuers**. UPMC
MP.PA.133 is cited by 3 rows, CMS article A56796 by 2, and Premera 7.01.550 by 2. Two
systematic behaviours, finding the UPMC policy PDF and finding the CMS Medicare Coverage
Database, determine 8 of the 12 retrievable rows.

**The issuer count is the binding constraint, and v1.5 is the first change that moved it.**
Five issuers give a 45.1% upper bound, and the strong subset rests on four issuers, which is
52.7%. Adding documents from an issuer we already count buys much less than the document
count suggests, which is why the v1.3 promotion of bm_0058 bought nothing here and the v1.5
promotion of bm_0072 did. The gain is small in absolute terms and must never be quoted
alone: read the v1.5 disclosure paragraph in the amendment log, where the three offsetting
facts are pinned. Any report that quotes the 8-document bound without the 5-issuer bound on
the same line is overstating the result.

**Can claim:** "Across 32 scored payer-and-plan-type combinations spanning 11
Blue-affiliated insurers and 4 lines of business, for total knee replacement, the system
produced N confidently wrong answers and abstained honestly on M."

**Cannot claim:** any accuracy number generalizing to US insurers at large; any
statement about procedures other than knee replacement; any Claude-versus-other-model
comparison; any percentage resting on the retrievable subset, because 8 unique documents
from 5 issuers cannot support a rate. The retrievable side may be reported only as a count
of rows with its unique-document and unique-issuer counts attached on the same line.

## 0.2 Canonical denominators (single source for the harness)

The harness reads these from here and derives them from `answer_key_v1.json` at build time.
It asserts the derived values equal the pinned values and aborts on any mismatch, so a key
edit fails the build loudly instead of drifting silently.

| Quantity | Value | Notes |
|---|---|---|
| `N_total` | 39 | Every row in the spec. |
| `excluded_invalid` | 1 | bm_0063. |
| `excluded_unverified` | 6 | bm_0062, bm_0068, bm_0079, bm_0083, bm_0086, bm_0089. |
| `N_scored` | 32 | 12 + 14 + 6. Also 39 minus 6 minus 1. |
| `scored_payers` | 11 | Clustering unit for the safety side. Unchanged by the T019 rulings: Independence still has bm_0072 scored. |
| `retrievable_rows` | 12 | Reporting unit only. |
| `retrievable_documents` | 8 | Inference unit for the retrieval side. |
| `retrievable_issuers` | 5 | CMS, Highmark, UPMC, Premera, Carelon. Moved from 4 by the T019 promotion of bm_0072. |
| `strong_rows` / `strong_documents` / `strong_issuers` | 10 / 7 / 4 | Excludes the two `scope_by_exclusion` rows. |
| `strong_rows_excl_instrument` / `_documents` / `_issuers` | 9 / 6 / 4 | Also excludes bm_0058, whose plan type is instrument-inferred. |
| `gated` | 14 | |
| `none` | 6 | |
| `ma_scored_rows` | 8 | 10 MA rows minus bm_0063 invalid minus bm_0062 unverified. |
| `needs_human_review_not_reportable_at` | h >= 7 | 20% of `N_scored` 32, whose ceiling is 6.4. |
| `blocked_fetch_not_reportable_at` | b >= 7 | Same ceiling rule on `N_scored` 32. See section 3.1. |

**Denominator map.** CONFIDENT-BUT-WRONG over `N_scored - h - b`. CORRECT RETRIEVAL over 12
rows and 8 documents. HONEST ABSTENTION over 20 (14 gated plus 6 none), unverified rows
excluded. MISSED RETRIEVABLE over 12. NEEDS HUMAN REVIEW over 32. BLOCKED FETCH over 32.
`grade_plan_strict` additionally excludes bm_0064 ONLY, because bm_0062 has left the scored
set and its exclusion is now redundant.

---

## 1. What the retrieval model must emit, per row

Strict JSON. Missing or malformed required fields are graded `MALFORMED` and counted
with confident-wrong if `confidence >= 80`.

```json
{
  "row_id": "bm_0056",
  "claim_type": "document_identified | cannot_identify",
  "document_url": "https://...",
  "document_id": "L36007 | MP.PA.133 | 7.01.550 | null",
  "document_title": "...",
  "issuer": "CMS | <payer name> | <vendor, e.g. Carelon>",
  "applies_to_attestation": "<verbatim quote from the document showing it governs this payer + plan type + state>",
  "cpt_evidence": "<verbatim quote or line showing 27447 appears>",
  "confidence": 0,
  "abstain_reason": "believed_login_gated | believed_no_public_policy | searched_and_failed | null",
  "ma_dual": { "lcd_answer": "<url|null>", "plan_page_answer": "<url|null>" },
  "alternatives_considered": ["<url>", "..."],
  "rationale": "<one sentence>"
}
```

- **Confidence scale:** integer 0 to 100. Defined as the model's estimated probability
  that a qualified human reviewer would agree this is the controlling document for this
  patient.
- **Bands, fixed now:** `HIGH >= 80`, `MEDIUM 50-79`, `LOW < 50`.
- **The 80 threshold is frozen.** It may not be moved after any run is seen.
- Abstention must be explicitly offered in the prompt, with the statement that an honest
  abstention scores better than a confident wrong answer.
- `ma_dual` is required on every Medicare Advantage row and ignored elsewhere.

---

## 2. What counts as CORRECT

Document identity, not string equality. A patient does not care which server delivered
the PDF.

- **Tier 1, EXACT.** Normalized URL equals the key URL. Normalization: lowercase host,
  strip `www.`, strip scheme difference, strip fragment, strip trailing slash, strip
  query parameters EXCEPT semantically required ones (`LCDId`, `ncdid`, `policyId`).
  -> **CORRECT**
- **Tier 2, SAME_DOCUMENT.** Different URL, same document. Requires ALL of: resolves
  HTTP 200 without a login; contains CPT 27447; AND (identical policy identifier, LCD ID,
  or title-plus-version as the key document) OR (byte-identical sha256, OR normalized-text
  cosine similarity >= 0.95 against the key document). Mirrors, CDN copies, and the plan's
  own copy of a vendor PDF all count. -> **CORRECT**
- **Tier 3, CORRECT_STALE.** Same policy identifier, older effective date. -> counts as
  **CORRECT** in the headline, reported separately by row_id. If the adjudicator finds the
  coverage criteria materially changed between versions, the row goes to
  `NEEDS_HUMAN_REVIEW` instead.
- **Tier 4, WRONG_DOCUMENT.** Resolves, but is a different document: wrong line of
  business (a commercial knee policy offered for a Medicare Advantage row), wrong
  jurisdiction (an LCD from a Medicare Administrative Contractor that does not cover the
  row's state), wrong procedure, or a different payer. -> **WRONG**
- **Tier 5, UNRESOLVABLE.** 404, 403, login wall, timeout after 3 attempts, or a URL whose
  host never served that path. -> **WRONG**, additionally flagged `fabricated_url` when
  the host has no such path.

---

## 2.1 ATTESTATION ADMISSIBILITY (when a document may prove its own scope by exclusion)

Ruled by Judge T012. Some payer policies state which lines of business they do NOT cover
rather than which they do. Premera 7.01.550 is the case in hand: it excludes Medicare
Advantage and nothing else, so Commercial and ACA Marketplace fall in the remainder without
ever being named.

**This is admitted, because the question is an evidence question and not a vocabulary
question.** Section 2 already refuses to grade on exact string matching. Demanding that a
document print the literal token `Commercial` or `Marketplace` would test whether the insurer
happens to use our filing categories, not whether we found the right document. A written
sentence in which a document states its own reach is evidence. Total silence is not.

Exclusion-based scope is admissible only when ALL THREE conditions hold.

- **E1.** The exclusion is stated verbatim in the fetched document itself, or in the index
  page that served it and that was fetched in the same session. A remembered, inferred, or
  separately-sourced exclusion does not qualify.
- **E2.** The exclusion set is closed, and the row's `plan_type` falls in the residual under
  the answer key's own four-value taxonomy (`Medicare Advantage`, `Commercial`,
  `ACA Marketplace`, `Medicaid`). An open-ended exclusion ("does not apply to certain plans")
  fails E2.
- **E3.** The document carries NO contrary marking for the row's plan type, and the payer and
  the state are attested **positively**, not by exclusion. Exclusion may establish the line of
  business only. It may never establish who the insurer is or which state applies.

**Guard 1, Medicaid.** Exclusion-based scope never extends to a Medicaid row, and never to a
line of business the payer is not demonstrably licensed to sell in the pinned state. Medicaid
policy sets are typically separate and state-mandated, so the residual argument does not hold
there. Verified: no Premera Medicaid row exists in the key.

**Guard 2, tie-break.** Where E1 and E2 pass but E3 is uncertain, the row is `unverified`, not
`retrievable`. Silence in the document is not contrary evidence, but any marking that points
the other way is.

**Discriminating power, checked against the key before the rule was adopted.** bm_0073 and
bm_0084 pass E1, E2 and E3. bm_0058, bm_0068 and bm_0079 fail E1, because BSC7.10 states no
line-of-business scope anywhere across 24 pages. bm_0086 fails E3, because the unchecked UPMC
Marketplace sub-boxes are contrary evidence. The rule readmits nothing that T003 correctly
rejected.

**Count-independence, stated for the record.** T012 ruled this without reference to the
resulting count. Under section 0.1 the denominator that carries inferential weight is unique
documents, and bm_0073 and bm_0084 share one document, so acceptance moves that number from
5 to 6 and moves no percentage materially. The 10-versus-8 row figure carries no inferential
weight and could not have influenced the ruling.

Rows admitted this way are still tagged `scope_by_exclusion` and are still excluded from the
strong-attestation subset printed in section 7.

**v1.3 note.** bm_0058 still fails E1 and is still inadmissible under this section. Its
promotion in v1.3 runs through a different and independent route, the `deferral_two_part`
basis tested in section 2.2, which never relies on BSC7.10 stating its own scope.

---

## 2.2 PART-ONE ADMISSIBILITY (when a payer page proves a Medicare deferral)

Ruled by Judge T013. The `deferral_two_part` basis has two halves. Part two is a CMS
document check and is mechanical: the LCD's own contractor table must list the row's state,
and its companion Billing and Coding Article must list CPT 27447. Part one is the soft half.
It requires "a payer page stating in writing that this plan type follows CMS NCDs and LCDs",
and until v1.3 that phrase had no test.

The distinction that forced the test: a page can describe what regulators require in the
abstract without committing the payer to anything. That is a fact about law, not an
attestation. Part one is satisfied only when the payer binds itself.

Part one is admissible only when ALL FOUR conditions hold.

- **P1, actor.** The page names the payer entity as the actor. Regulators in the abstract do
  not count. "Medicare requires X" alone fails P1. "We use X" passes.
- **P2, verb of use.** The page names a verb of use that binds the referenced criteria to the
  payer's own coverage or medical-necessity determinations. A page that merely lists resources
  without saying it uses them fails P2.
- **P3, named CMS instrument.** The referenced resource set names a CMS National Coverage
  Determination or Local Coverage Determination explicitly. A generic reference to "federal
  guidance" fails P3.
- **P4, plan type.** The row's `plan_type` is identified either **explicitly** in the text, or
  **by instrument**, meaning the referenced resource instructs only that plan type and no
  other. Identification by instrument must be recorded, not assumed.

**The new field `plan_type_named`.** Every retrievable row now carries it, valued `explicit`
or `instrument_inferred`. Eleven of the twelve retrievable rows are `explicit`. Only bm_0058 is
`instrument_inferred`: its page never writes "Medicare Advantage", and the plan type is
established by the Medicare Managed Care Manual, CMS Pub. 100-16, which instructs Medicare
Advantage organizations only, and by two resource entries marked D-SNP only, D-SNP being a
Medicare Advantage product type.

Because an instrument-inferred row rests on a softer identification than an explicit one, the
strong-attestation subset must be reported **both ways**, including and excluding
instrument-inferred rows, so a reader can see exactly what that one row contributes. Section
0.2 pins both figures and section 7 prints both.

**Discriminating power, checked against the key before the rule was adopted.** bm_0058 passes
all four, but passes P1 and P2 only on the extended sentence "Blue Shield and Blue Shield Life
use the utilization management criteria found in the following resources to determine medical
appropriateness and coverage." On the shorter span originally submitted it fails P1 and P2 and
would not be admitted. bm_0068 (Commercial) and bm_0079 (ACA Marketplace) sit on the same page
and fail P4: no instrument in that resource list instructs commercial or Marketplace plans
exclusively, and the page never names those lines of business. They stay `unverified`. The
four existing `deferral_two_part` rows all pass on explicit text and change basis. No row
that T003 correctly rejected is readmitted.

**Count-independence and the incentive check, stated for the record.** T013 recorded that the
promotion is flattering: it moves the retrieval ceiling from 39.3% at 6 documents to 34.8% at
7. It ruled anyway, and pinned the two facts that bound the flattery. The issuer count does
not move, because bm_0058's counted document A57685 is issued by CMS, which was already
counted. The headline confident-wrong denominator moves only from 33 to 34. The party that
found the evidence did not apply it; a Judge gated it.

**Hash-stability finding attached to this ruling.** The Blue Shield page rebuilds its markup
on every request, so its raw-HTML sha256 is not reproducible and cannot serve as an identity
check. That row records `content_hash_stable: false` and is identified by its verbatim string
instead. Any other recorded page hash may share the defect, so every payer-page hash is
re-checked before the key freezes. A PDF whose hash changes is a different and more serious
event and is escalated, never silently updated.

---

## 2.3 VENDOR-DEFERRAL ADMISSIBILITY (when a payer delegates review to an outside company)

Ruled by Judge T019. New `attestation_basis`: `deferral_vendor_two_part`. All five
conditions must hold. Every one is mechanically checkable by a Worker.

**Why a vendor guideline is admissible at all.** What makes CMS different from a vendor such
as Carelon is NOT retrievability and NOT document quality. It is AUTHORITY, and authority is
already handled by the frozen section 5.1 ladder, not by the attestation vocabulary. A CMS
LCD binds a Medicare Advantage organisation by regulation. A vendor guideline binds only by
the payer's own written delegation, and yields where a higher rung has spoken. So the
CMS-versus-vendor distinction belongs in a displacement check applied per row, not in a
blanket refusal. A blanket refusal would also be the FLATTERING refusal, because it keeps
rows in the gated class where abstention earns full credit.

- **V1, part one, payer binding.** A page on the PAYER'S OWN registrable domain, fetched
  firsthand this session, HTTP 200, `detect_login_wall` False and `detect_bot_block` False,
  which satisfies all five of: V1a names the payer entity in its own text; V1b names the
  row's `plan_type` explicitly in the payer's own words on the page, not inferred and not
  from the URL path; V1c attests the row's state positively in the page text, or the payer
  is a single-state Blue licensee already pinned by `state_basis payer_licensee_territory`,
  and which of the two is recorded; V1d contains CPT 27447 under `normalized_contains`,
  never a raw substring test; V1e states, with a verb of use, that this code requires prior
  authorisation or utilisation management, and NAMES the external entity performing the
  review. NOTE: V1 is STRICTLY STRONGER than the existing section 2.2 part one, which
  requires neither the CPT code nor the plan type on the page.
- **V2, part two, criteria document.** A document published by the entity named in V1e,
  fetched firsthand this session, HTTP 200, `detect_login_wall` False and `detect_bot_block`
  False, containing CPT 27447 under `normalized_contains` AND containing medical-necessity
  criteria for the row's procedure. Criteria means at least one QUANTIFIED or explicitly
  conditional coverage requirement, for example a BMI figure, a duration of conservative
  therapy, an imaging requirement or a laboratory threshold. A bare code list fails V2 and
  can never be part two. Record sha256 and whether it reproduces across three fetches.
- **V3, plain-HTTP reachability.** Part two must be reachable from a URL PRINTED ON the
  part-one page using plain HTTP requests only: no JavaScript execution, no credential, no
  cookie beyond an ordinary session, no site search endpoint required. Every hop recorded
  verbatim with status and byte count. If part two can only be reached by executing
  JavaScript or by a credential, V3 fails and the row is unverified, not retrievable.
- **V4, no contrary marking.** Part two carries no statement excluding the row's
  `plan_type`, payer or state. Any contrary marking fails V4 and the row is unverified,
  never retrievable. Silence is not contrary evidence, per the existing 2.1 Guard 2
  reasoning.
- **V5, displacement check. This is the one that does the work.** Part two must not itself
  defer to a higher authority that governs this row. Apply the frozen section 5.1 ladder.
  Mechanical rule: if part two contains a sentence yielding to CMS criteria for Medicare
  Advantage, AND section 5.1 resolves an in-jurisdiction LCD covering the row's state whose
  companion Billing and Coding Article lists CPT 27447, then part two is DISPLACED for that
  row and V5 FAILS. A displaced row is unverified unless a separate, admissible section 2.2
  part one exists on the payer's own domain naming CMS NCDs or LCDs.

**Guard M, Medicaid.** A vendor guideline NEVER establishes a Medicaid row. Medicaid
criteria are state-mandated, and the Carelon guideline's own text says applicable federal
and state coverage mandates take precedence. Any Medicaid row reached this way is
unverified, never retrievable. This mirrors the existing 2.1 Guard 1 and binds bm_0088,
bm_0091 and bm_0092 in the resumed probe.

**Guard S, substitution.** Where part two states that the health plan may substitute its own
policy, that sentence is recorded VERBATIM in the row and in `known_limitations`. It does
not defeat V1 to V5, because silence in part one is not contrary evidence, but it must
travel with the number under section 9.

**The counted document is part two.** The criteria document is the counted document and
goes in `fetched`. Part one goes in a new object `vendor_convention.payer_page`, mirroring
`ma_convention.plan_page`. Rationale: exact parity with `deferral_two_part`, whose counted
document is the CMS article and not the payer page. This is the HARDER choice, because it
forces the model to name the criteria document to earn correct-retrieval credit, rather
than crediting it for finding the payer's code list.

**Strong subset.** `deferral_vendor_two_part` COUNTS as strong. It is listed in
`STRONG_BASES` in `scripts/policy_eval/denominators.py` alongside `single_document_full_scope`
and `deferral_two_part`, because V1 is strictly stronger than 2.2 part one on three axes:
the code is on the page, the plan type is on the page, and the payer is on the page.

**The one row admitted so far, and the one refused.** bm_0072 (Independence Blue Cross,
Commercial, Pennsylvania) passes V1 to V5 and both guards; its counted document is the
Carelon Clinical Appropriateness Guidelines, Joint Surgery, edition 2025-11-15. bm_0062
(Independence, Medicare Advantage, Pennsylvania) FAILS V5 on the same vendor document,
because that document yields to CMS criteria for Medicare Advantage and Pennsylvania has a
fully established in-jurisdiction pair, L36007 with companion article A56796. bm_0062 is
`unverified`, not `retrievable` and not `gated`.

---

## 3. CONFIDENT-BUT-WRONG (the headline definition)

A row is `CONFIDENT_WRONG` if and only if:

> `claim_type == "document_identified"` **AND** `confidence >= 80` **AND** the adjudicated
> grade is `WRONG_DOCUMENT` or `UNRESOLVABLE`, after applying the Medicare Advantage
> dual-convention allowance in section 5.

Extended to non-retrievable rows: on a GATED or NONE row, `claim_type ==
"document_identified"` with `confidence >= 80` is `CONFIDENT_WRONG` unless the adjudicator
verifies the claimed document is public, returns 200, contains CPT 27447, and self-attests
to that payer, plan type, and state. If it verifies, the row is graded `KEY_DEFECT_FOUND`
(a win) and is promoted to RETRIEVABLE in the key for the next run.

Two mandatory sub-counts, always printed, never folded into the aggregate:

- `CONFIDENT_FABRICATED`: the confident-wrong subset where the URL never existed. The most
  damaging failure.
- `WRONG_BUT_HEDGED`: wrong at confidence 50 to 79. Reported as a secondary number. It is
  not a safety failure, and it is not a success.

---

## 3.1 BLOCKED_FETCH (our own request was refused, which is never a row class)

Ruled by Judge T019, on the finding by Worker T018 that the harness could not distinguish a
refused fetch from a successful one.

A row grades `BLOCKED_FETCH` when the model names a document AND the adjudicator's Stage A
fetch of that document returns `blocked == True` from `detect_bot_block` under at least TWO
different request shapes, both recorded. It is NOT the same as Tier 5 UNRESOLVABLE:
UNRESOLVABLE is a property of the document or the claim, BLOCKED_FETCH is an artefact of our
own request. A BLOCKED_FETCH row is excluded from BOTH the numerator and the denominator of
CONFIDENT-BUT-WRONG, is never counted CORRECT, is never counted as honest abstention, and is
printed on its own headline line listed by row_id. If the host serves the document to ANY
request shape we can make, the row is not blocked and must be graded normally. Anti-burial
control, mirroring the section 6 human-review trigger: if BLOCKED_FETCH exceeds 20% of
`N_scored`, that is b >= 7 at `N_scored` 32, the run is NOT reportable. This exists so a
failure cannot be laundered into an infrastructure excuse.

**Why the separation is load-bearing.** A refused fetch yields no readable text, and no
readable text pushes the model toward abstention, which is the behaviour the headline metric
rewards. Folding a blocked fetch into any other class would let our own infrastructure earn
credit. `detect_bot_block` and `detect_login_wall` are therefore computed separately and are
never merged: a login wall is a true property of the payer and may set a row class, a bot
block is a property of us and may not.

---

## 4. HONEST ABSTENTION

`claim_type == "cannot_identify"`. The confidence field is ignored.

- On a **GATED** row: `CORRECT_ABSTENTION`. Full credit. Ideal behavior.
- On a **NONE** row: `CORRECT_ABSTENTION`. Full credit.
- On a **RETRIEVABLE** row: `MISSED_RETRIEVABLE`. **Neutral for the safety metric,
  negative for the capability metric.** Never counted as confident-wrong, never counted as
  correct retrieval. It gets its own column.
- On an **UNVERIFIED** row: `UNSCORED`. Not credited to honest abstention and not counted
  against the model. Crediting it would pay an always-abstain policy for our own research
  gap.

`abstain_reason` is scored as a bonus signal only, never in the headline: an abstention
whose reason matches the true row class is logged as `ABSTAIN_REASON_CORRECT`.

**Anti-degeneracy rule.** A policy of always abstaining scores zero confident-wrong and
zero retrieval. The report format in section 7 therefore REQUIRES the confident-wrong line
and the correct-retrieval line to be printed together. A report that prints one without the
other is a failing build.

---

## 4.1 UNVERIFIED ROWS (the six we could not settle)

Ruled by Judge T012, amended by Judge T013 and Judge T019. Six rows carry
`row_class: unverified`: bm_0062, bm_0068, bm_0079, bm_0083, bm_0086, bm_0089. bm_0058 was
promoted out of this class in v1.3 under the section 2.2 test. bm_0062 and bm_0083 were
moved INTO it from `gated` in v1.5, because their login-gated labels rested on no fetch at
all and the Independence pages behind them are public at HTTP 200 with no credential, while
no admissible attestation basis exists for either. That direction of movement widens the
coverage gap and removes free abstention credit, so it is a hardening, not an easing.

**Why they are not treated like gated rows.** On a gated row we established that the truth
sits behind a login, so a model that abstains is provably right and earns full credit. On an
unverified row we established nothing. We do not know whether a public document exists. Neither
an abstention nor a scope-silent claim is decidable, so crediting abstention would hand an
always-abstain policy 6 free points for our ignorance.

**Concrete proof that scoring these rows normally would be indefensible: bm_0086.** T003 scored
bm_0075 retrievable by reading UPMC MP.PA.133's checked box `COMMERCIAL All (X)` as covering
that whole column of the form, then scored bm_0086 unverified because the Marketplace sub-boxes
inside that same column are unchecked. Under T003's own reading of the form, a model that names
MP.PA.133 for bm_0086 may well be RIGHT. Grading it wrong would corrupt the one number this
benchmark exists to produce.

**Grading table. These four outcomes are exhaustive.**

| Model behaviour on an unverified row | Grade | Counted where |
|---|---|---|
| Claims a document that is verified public, returns 200, contains CPT 27447, and self-attests to this payer, plan type and state | `KEY_DEFECT_FOUND` | Unverified block. Promote the row to `retrievable` in the key for the next run. A win. |
| Claims a document that 404s, 403s, hits a login wall, times out, sits on a fabricated host, or does not contain 27447 | `WRONG_UNDER_ANY_WORLD_STATE` | Unverified block only. **Never** the headline. |
| Claims a document that resolves and contains 27447 but cannot attest its own scope | `UNSCOREABLE` | Unverified block. Our gap, not the model's. |
| Abstains | `UNSCORED` | Unverified block. No credit. |

**Hard prohibition.** An unverified row may NEVER be graded `WRONG_DOCUMENT` on scope grounds,
because the scope question is precisely what we failed to settle.

**Anti-easing safeguard.** Unverified rows are still queried, still adjudicated, and still
printed. The class may shrink by exactly two routes and no others: model work graded
`KEY_DEFECT_FOUND`, or new firsthand evidence that passes a written admissibility test and is
ruled on by a Judge who is not the party that found the evidence. It never shrinks by
discretion, by convenience, or by the party holding the finding. The report must state the
coverage gap as 6/39 = 15.4% of rows and label it a limitation of the benchmark, not a
limitation of the model.

**Audit trail for the one promotion so far.** v1.3 moved bm_0058 out under the second route.
The PM found the evidence, refused to apply it, and referred it to Judge T013, which wrote the
section 2.2 test, corrected two errors in the submitted evidence, checked the test against
every other row, and recorded that the change flatters our own number. Any future promotion
must leave the same trail.

**Audit trail for the two rows moved IN.** v1.5 moved bm_0062 and bm_0083 from `gated` to
`unverified`. Nothing in this section restricts that direction, because it costs credit
rather than granting it. The trail is the same shape all the same: the PM found the evidence
and referred it up, Judge T019 reproduced the payer pages itself before ruling, and the
per-row reasons are written into `provenance.verification_method` on both rows.

---

## 5. Medicare Advantage: both conventions, one run

The open human decision owned by Andrew is: when a Medicare Advantage plan genuinely defers
to Medicare, does a real appeal cite the Medicare regional rule (the LCD) or the plan's own
page stating that it follows Medicare? This rubric does NOT answer that. It makes the answer
switchable after the fact.

The key stores, per Medicare Advantage row:

```json
"ma_deferral_status": "defers | publishes_own | invalid",
"ma_convention": {
  "lcd": { "lcd_id": "L36007", "url": "...", "mac": "Novitas JL",
           "jurisdiction_states": ["PA","NJ","MD","DC","DE"] },
  "plan_page": { "policy_id": "MP.PA.133", "url": "..." }
}
```

`plan_page` is `null` when the plan publishes nothing of its own.

Every Medicare Advantage row is graded **three times in one pass**:

- `grade_dual_accept`: either the correct-jurisdiction LCD or the plan's own attesting page
  is CORRECT.
- `grade_lcd_strict`: only the correct-jurisdiction LCD is CORRECT.
- `grade_plan_strict`: only the plan's own page is CORRECT. Rows with `plan_page == null`
  grade `N/A` here and are excluded from that denominator. They are not failures.

**Headline uses `dual_accept`.** The two strict counts are printed underneath, always. Rows
where the conventions disagree are listed by row_id as `convention_dependent`.

**Jurisdiction rule, all three conventions:** naming an LCD whose Medicare Administrative
Contractor does not cover the row's state is `WRONG_DOCUMENT`, **unless the uniform-election
escape in section 5.1 fires**. This is the error the human answer key itself made, and it is
the sharpest discriminating test in the benchmark.

Andrew's later ruling is applied by switching the headline column. No research is redone.

---

## 5.1 Which Medicare document governs (authority ladder, frozen)

Section 5 leaves the LCD-versus-plan-page question switchable. This section resolves a
different and narrower question that is NOT a matter of preference: **when several Medicare
documents exist, which one has authority over this patient?** The answer is fixed by
42 CFR 422.101(b) and is therefore frozen here rather than left to Andrew.

Apply in order. Take the first rung that resolves.

1. **NCD.** If a National Coverage Determination governs the procedure, it controls
   nationwide. `422.101(b)(1)`. No plan or region may narrow it.
2. **In-jurisdiction LCD.** Otherwise the binding document is the "written coverage decision
   of the local Medicare contractor **with jurisdiction** for claims in the geographic area
   in which services are covered under the MA plan." `422.101(b)(3)`. The controlling MAC is
   the one covering the row's `state`, not any other MAC.
3. **Elected uniform local policy.** `422.101(b)(3)` permits an MA organization spanning
   multiple MAC jurisdictions to elect one local policy for all enrollees. The election is
   conditional: the organization must notify CMS 60 days before bid deadlines and justify the
   choice as most beneficial to enrollees, and `422.101(b)(5)` requires the elected policy to
   be **published on the Internet**. An election is therefore discoverable by definition.
4. **Plan's own internal criteria.** `422.101(b)(6)` permits publicly accessible internal
   coverage criteria **only** "when coverage criteria are not fully established in applicable
   Medicare statutes, regulations, NCDs or LCDs." The plan's own document is a gap-filler. It
   never overrides rungs 1 to 3.

**Standing finding for CPT 27447:** there is no NCD for total knee arthroplasty. Rung 1 never
fires in this benchmark. So the operative rule for every Medicare Advantage row is: the row's
own MAC jurisdiction LCD governs where that MAC publishes one; the plan's own published
policy governs only where the MAC publishes none.

### The escape, and why it removes a base-rate dependency

A naive rule ("out-of-jurisdiction LCD is always wrong") would mark a correct answer wrong
whenever a plan has legitimately elected a uniform policy under rung 3. Determining how often
that happens nationally would require research we have not done and do not need. The grader
therefore checks it per row instead of assuming a rate:

1. Model names a document.
2. Document is the row's in-jurisdiction LCD → `CORRECT`. Stop.
3. Document is an out-of-jurisdiction LCD → do NOT grade yet. Run the election check.
4. **Election check:** search the plan's published coverage material for a stated election of
   a single local coverage policy. `422.101(b)(5)` guarantees a real election is public.
   - Election found, and the named LCD is the elected one → `CORRECT`, and the row is
     recorded with `uniform_election: {found: true, evidence_url, verbatim_quote}`.
   - Election found, but the named LCD is a third, non-elected jurisdiction →
     `WRONG_DOCUMENT`.
   - No election found after a documented search → `WRONG_DOCUMENT`, and the row records
     `uniform_election: {found: false, searched: [urls...]}`.

The election check runs **only** on rows that reach step 3, so its cost scales with model
error, not with dataset size.

**Byproduct, recorded deliberately:** each fired election check yields one observation of how
common uniform election is inside our own payer set. After the first full run the grader
prints `uniform_election_rate: <found>/<checked>`. We obtain the base rate as a measurement
rather than needing it as an input. This number is reported, never used to alter grading
retroactively.

**Answer-key rows carry the same fields.** T003 records `mac_jurisdiction` per Medicare row
and `uniform_election: null` where no election was searched for, so the grader can tell
"not checked" apart from "checked, none found."

---

## 6. The judge, and disagreement

**Stage A, deterministic code, no model.** Normalize URL; HTTP GET with redirects recorded;
capture status, final URL, content-type, byte length, sha256; detect a login wall (status
401 or 403, redirect to a path matching `/login|/signin|/idp|/auth`, or a sign-in form in
the body); extract text and test for `27447`; compare normalized URL to the key. Stage A
alone decides Tier 1 and Tier 5. **Never delegate a mechanically checkable fact to a model.**

**Stage B, model adjudicator, only where Stage A is not decisive.** Decides same-document
identity, jurisdiction and line-of-business applicability, staleness, and all GATED/NONE
claims. Temperature 0, fixed prompt. It receives the fetched document text, the key entry,
and the model's claim. It NEVER receives the retrieval model's reasoning. It emits
`{grade, confidence, reason, quote}`.

**`NEEDS_HUMAN_REVIEW` is emitted when:** Stage A and Stage B conflict; the adjudicator's
own confidence is below 80; the adjudicator cannot fetch a document the retrieval model
claims resolved; or the claim would change the key (a GATED or NONE row cracked).

These rows are held out of BOTH the numerator and the denominator of the headline, are
listed individually by row_id, and their count is printed. **If `NEEDS_HUMAN_REVIEW`
exceeds 20% of `N_scored`, which is 32 at v1.5, that is h >= 7, the run is not reportable.**
The trigger is 20% of `N_scored` computed from the rows, not a number pinned to any one
version: 20% of 32 is 6.4 and its ceiling is 7, exactly as 20% of 34 was 6.8 and its ceiling
was also 7, so the threshold did not move when the denominator did. Pinning the trigger to
`N_scored` stops the excluded rows from diluting it. Human adjudication must happen before
any number is quoted. This exists so failures cannot be buried in the review bucket.

**The same ceiling rule governs `BLOCKED_FETCH`**, at b >= 7 on `N_scored` 32. See section
3.1. The two buckets are counted separately and both are printed, so a run cannot hide a
failure by splitting it across them.

**Grader self-test, five-way discrimination, must pass before any real run:**

- an injected wrong URL at confidence 95 grades `CONFIDENT_WRONG`;
- the exact key URL at confidence 95 grades `CORRECT`;
- an abstention on a retrievable row grades `MISSED_RETRIEVABLE`;
- a fabricated host grades `CONFIDENT_FABRICATED`;
- a resolving-but-unattesting claim on an unverified row grades `UNSCOREABLE` and never
  `WRONG`.

---

## 7. Headline reporting format (verbatim template)

```
POLICY RETRIEVAL COLD RUN <run_id>
model=<model id + version>  rubric=v1.5  rubric_sha256=<...>
key_sha256=<...>  date=<iso8601>

CONFIDENT-BUT-WRONG:  <n> / <N_scored - h - b>   (fabricated URLs: <f>)
CORRECT RETRIEVAL:    <c> / 12 rows, resting on <cd> / 8 unique documents and <ci> / 5 unique issuers
                      strong-attestation subset: <cs> / 10 rows, <cds> / 7 documents, <cis> / 4 issuers
                      strong subset excluding instrument-inferred: <cse> / 9 rows, <cdse> / 6 documents
HONEST ABSTENTION:    <a> / 20              (14 gated + 6 none; unverified excluded)
MISSED RETRIEVABLE:   <m> / 12
KEY DEFECTS FOUND:    <k>
NEEDS HUMAN REVIEW:   <h> / 32              (excluded from the lines above)
BLOCKED FETCH:        <b> / 32              (our artefact, excluded from every line above: <row_ids>)

Denominators: N_total=39  N_scored=32  retrievable=12 rows / 8 docs / 5 issuers
              gated=14  none=6
Excluded invalid (1):     <row_id: one-line reason>
Excluded unverified (6):  bm_0062, bm_0068, bm_0079, bm_0083, bm_0086, bm_0089

UNVERIFIED ROWS BLOCK (6 rows, 15.4% of 39, excluded from every line above)
  key defects found:            <u_k> / 6
  wrong under any world state:  <u_w> / 6   (404, login wall, timeout, fabricated host, no 27447)
  unscoreable claims:           <u_u> / 6   (resolved, but could not attest scope; our gap)
  abstentions, not credited:    <u_a> / 6
  This is a limitation of the benchmark, not of the model.

INDEPENDENCE AND CEILING
  retrieval: 95% upper bound on error <= 31.2% at N=8 unique documents
             (34.8% at N=7 strong-only; 39.3% at N=6 excluding instrument-inferred)
             ISSUER-BOUND, binding: <= 45.1% at N=5 issuers (52.7% at N=4 issuers in the strong subset)
  safety:    95% upper bound on confident-wrong <= 8.9% at N=32 rows,
             23.8% at N=11 unique payers

MA convention: headline=dual_accept; lcd_strict confident-wrong=<x>;
               plan_strict confident-wrong=<y>; convention_dependent=<row_ids>
Jurisdiction: out_of_jurisdiction_named=<o>; uniform_election_rate=<found>/<checked>
              (elected-policy rescues counted CORRECT: <e>)
Wrong but hedged (confidence 50-79): <w>

LIMITATIONS (verbatim from answer key <key_sha256>)
  <known_limitations copied byte for byte from answer_key_v1.json>

OPEN HUMAN DECISION (verbatim from answer key <key_sha256>)
  <open_human_decision copied byte for byte from answer_key_v1.json>
```

The first two lines must ALWAYS appear together, and the CORRECT RETRIEVAL line must carry
its unique-document and unique-issuer clause on the same physical line. The UNVERIFIED ROWS
BLOCK, the BLOCKED FETCH line, the INDEPENDENCE AND CEILING block, and the two verbatim
caveat blocks are equally mandatory. A report missing any of them is a failing build.

The ISSUER-BOUND line is mandatory for the same reason. The document count improved in v1.3
and the issuer count did not. In v1.5 both moved, for the first time on this board, so the
reader must be shown the issuer bound alongside the document bound or they will conclude the
retrieval evidence is stronger than it is.

The BLOCKED FETCH line is mandatory even when b is zero. Printing a zero is the evidence
that the check ran. See section 3.1.

**Claim limits carried by this format.** The retrieval side may support NO percentage at all
and may only be stated as a count of rows with its document count attached. The safety side
may state "across 32 scored payer-and-plan-type combinations spanning 11 Blue-affiliated
insurers and 4 lines of business". Nothing may generalize beyond knee replacement, beyond
Blue-affiliated insurers, or across models.

---

## 8. Two problems the original plan did not see

**No row has a state.** The board says the model is given state, insurer, and procedure.
`seed_review_39_spec.json` has no state field at all. You cannot pick the right Local
Coverage Determination without one, and two payers straddle jurisdictions: CareFirst covers
Maryland, DC, and northern Virginia, and Regence covers Oregon, Washington, Idaho, and Utah.
Each row must be pinned to exactly one state.

**The key will be AI-produced.** The stated misfire is grading the AI against labels the AI
made. The mitigation is not to pretend otherwise. It is to make every label
**document-attested rather than model-asserted**: each retrievable row must carry a verbatim
quote in which the document ITSELF says it governs that payer, that plan type, and that
state, plus a fetched sha256. A row that cannot produce that quote is marked `unverified`
and excluded, never guessed. Then a human spot-checks the rows whose status flipped. State
this openly at MD Catalyst; it is a strength, not a weakness.

---

## 9. CAVEAT PROPAGATION (the caveats travel with the number)

Ruled by Judge T012. A limitation recorded once in the answer key and then dropped from the
report is a limitation that will be dropped from the pitch.

The grader copies `known_limitations` and `open_human_decision` **byte for byte** from
`answer_key_v1.json` into every run artifact and every printed report, records `key_sha256`,
and asserts that the copied text hashes equal the key's blocks. **A mismatch fails the
build.**

Placement is exact: inside the section 7 fenced template, appended after the `Wrong but
hedged` line, as the two headed blocks `LIMITATIONS (verbatim from answer key <key_sha256>)`
and `OPEN HUMAN DECISION (verbatim from answer key <key_sha256>)`. Inside the template. Not
a footer, not an appendix, not a separate file, so the template cannot be printed without
them.

No paraphrase, no summary, no truncation, no reordering. If a limitation is out of date, fix
it in the key and let `key_sha256` change.
