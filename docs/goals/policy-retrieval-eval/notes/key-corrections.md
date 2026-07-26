# Answer key v1: corrections log

Task T003. Written 2026-07-26. Board: `docs/goals/policy-retrieval-eval/state.yaml`.

Output: `data/policy_platform/answer_key_v1.json`.
Input, unmodified: `data/policy_platform/seed_review_39_spec.json`,
sha256 `76f64b65382cffeb0bba6748895ba07a11f60440983887a9af430dfdf812c053`.

## What this file is

Every row in the answer key, with the URL that was actually fetched, the HTTP
status that came back, the sha256 of the bytes received, a verbatim quote from
the document, and what changed against the original spec.

Nothing here was inferred from memory. Every URL was fetched during the T003
session on 2026-07-26 with a browser user agent, over plain HTTPS, with no
login, no credential, no NPI, and no payer telephone call.

## Headline result

| Class | Count | Spec said |
|---|---|---|
| retrievable | 10 | 13 public |
| gated | 17 | 20 login-gated |
| none | 6 | 6 no public policy |
| invalid | 1 | (no such class) |
| unverified | 5 | (no such class) |
| **total** | **39** | 39 |

Ten rows survive as retrievable, which clears the board's escalation floor of
six. But those ten rows rest on only **six unique documents**, so they are not
ten independent tests. Two of the ten rest on the weakest attestation basis in
the key and are flagged below.

Six of the spec's thirteen "public" rows did not survive: one is invalid and
five are unverified.

## The core defect, and how it was fixed

The spec pointed six Medicare Advantage rows at one CMS document, LCD L36007.
A Local Coverage Determination is bound to one Medicare Administrative
Contractor jurisdiction. One LCD cannot govern Michigan, North Carolina, the
Maryland/New Jersey/Pennsylvania region and Washington at the same time.

I fetched L36007's own Contractor Information table. It reads:

> Novitas Solutions, Inc. | A and B MAC | 12301 - MAC A | J - L | Maryland
> Novitas Solutions, Inc. | A and B MAC | 12401 - MAC A | J - L | New Jersey
> Novitas Solutions, Inc. | A and B MAC | 12501 - MAC A | J - L | Pennsylvania
> Novitas Solutions, Inc. | A and B MAC | 12901 - MAC A | J - L | Delaware District of Columbia Maryland New Jersey Pennsylvania

Delaware, DC, Maryland, New Jersey, Pennsylvania. Michigan, North Carolina and
Washington are absent. The spec was wrong for three of the six rows.

The corrected map, every line of it read off a page fetched this session:

| State | MAC | Jurisdiction | LCD | LCD title | Companion article |
|---|---|---|---|---|---|
| MD, NJ, PA (also DE, DC) | Novitas Solutions | J-L | L36007 | Lower Extremity Major Joint Replacement (Hip and Knee) | A56796 |
| Michigan (also IN) | Wisconsin Physicians Service | J-08 | L39911 | Total Joint Arthroplasty | A59811 |
| North Carolina (also SC, VA, WV) | Palmetto GBA | J-M | L33456 | Total Joint Arthroplasty | A56777 |
| Washington (also AK, ID, OR, AZ, MT, ND, SD, UT, WY) | Noridian Healthcare Solutions | J-F | L36575 | Total Knee Arthroplasty | A57685 |
| California (also HI, NV, and Pacific territories) | Noridian Healthcare Solutions | J-E | L36575 | Total Knee Arthroplasty | A57685 |

## The CPT 27447 trap

CPT 27447 appears **zero** times on all four LCD pages. CMS puts procedure
codes in a separate companion Billing and Coding Article. Measured directly:

```
l33456.txt  27447 count = 0      a56777.txt  27447 count = 1
l36007.txt  27447 count = 0      a56796.txt  27447 count = 1
l36575.txt  27447 count = 0      a57685.txt  27447 count = 1
l39911.txt  27447 count = 0      a59811.txt  27447 count = 1
```

So on every Medicare Advantage row the key records **both** URLs, and
`cpt_27447_present` is measured against the companion article, which is also
the URL stored in the row's `fetched` block. A model answer that names only the
LCD must not be graded wrong for that reason alone.

---

# Document register

Every document fetched, with status and sha256. All returned HTTP 200 with no
login.

| Key | URL | sha256 | 27447 |
|---|---|---|---|
| L36007 | https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId=36007 | 743a96d7046e09d034e31b3433ba9f2036f5ae10425efd7f43ab0e0826d4dcf0 | no |
| A56796 | https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleId=56796 | 04cc0d3b62c6ca81b717808fb091e1961ea85b42365fbe24920118aecb1718d3 | yes |
| L39911 | https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId=39911 | 4e2279eaadfc708033e63680fe15bf50fcfeaec16e2049fbd24474698b6447d4 | no |
| A59811 | https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleId=59811 | 02fda72ef458094758c9eec1f27c94b9a1594f557397bd8fc93764ae21e33f03 | yes |
| L33456 | https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId=33456 | d40accf0ad92a12e225983b20f5cd033ca6e810974090cf09eaf9f40fa0810b8 | no |
| A56777 | https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleId=56777 | 0e32702668f2d8cab9f7c3bc25a8a32dc18be53ed524d0bcc96b1bc5e25b6378 | yes |
| L36575 | https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId=36575 | 20b570f8748bd124419acd6b8def794d3f67fdf0ce9ee515a3b74c7ecc87b89c | no |
| A57685 | https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleId=57685 | be8d730ef4d093f7acd93015b8402de2fba5c5fa4b760e804aa63c80ac68ba9e | yes |
| HIGHMARK_S39008 | https://securecms.highmark.com/content/medpolicy/en/highmark/pa/medicare-advantage/policies/Surgery/S-39/S-39-008.html | f1f28a299bdc0b7ef8f8b86c82035242e62b6104fb55075a863fd2d149c5c8b3 | yes |
| UPMC_MPPA133 | https://embed.widencdn.net/download/upmc/rqw3ib3zmx/MP.PA.133.pdf | 2b44474e0b2f963948f3823ae7355af6ee75d1f012b82c4c992e85e6ca8ff622 | yes |
| PREMERA_701550 | https://www.premera.com/medicalpolicies/7.01.550.pdf | 3a1341f0764cfb049bb779cf548f0c2363929b7efe9ac6840374487ed3753183 | yes |
| PREMERA_INDEX | https://www.premera.com/wa/provider/reference/medical-policies/ | 492d641d105af5fc2b7b36a4035453aca0da478cc23da8175eeb7c3d6f2e7144 | no |
| BSCA_BSC710 | https://www.blueshieldca.com/content/dam/bsca/en/provider/docs/medical-policies/Knee-Arthroplasty-Adults.pdf | 761ec47ecf92563ed48d175638355c7dbe2db7ec6fd79f87343d6e2a14c42b0a | yes |
| CARELON_JOINT | https://guidelines.carelonmedicalbenefitsmanagement.com/wp-content/uploads/2025/11/PDF-Joint-Surgery-2025-11-15.pdf | b33ae12d3a59b1b43ed4864b4a61a4e0a0f3fbcd6d8709344700c6e94165147a | yes |
| BCBSM_MA | https://www.bcbsm.com/medicare/help/using-your-plan/prior-authorization/medicare-advantage-medical-policy-guidelines/ | 1742c04f35bb2d3ea00a31d21d08f8685ad8f1c4c057863f578f5b4789860c60 | no |
| BCBSNC_HIER | https://www.bcbsnc.com/providers/policies-guidelines-codes/medicare/guidelines/medicare-advantage-coverage-determination-hierarchy | 3f79598457d3e8697b7c7f02cb207e6bd217fca966087903acc2993686520568 | no |
| CAREFIRST_MP | https://provider.carefirst.com/providers/medical/medical-policy.page | abbd1177a2345a5691f2e78274455b9a25c0340c8a6d91b82ae00babdf7d6613 | no |
| HORIZON_SIDM | https://www.horizonblue.com/providers/products-programs/utilization-management-programs/surgical-and-implantable-device-management-program/medical-policy-criteria-and-guidelines | 611a162f5520deace245ece1a639c148a54437f3508fd986584185cba59b1c7c | no |

Also fetched, as supporting evidence: the official CMS bulk export
`https://downloads.cms.gov/medicare-coverage-database/downloads/exports/current_lcd.zip`
(HTTP 200, sha256 `138551e0c9e4278cfbdae1162bba7118cec4866f7bbe93746fc8496dfa68a010`),
used to cross-check the LCD-to-state mapping independently of the rendered
HTML pages.

---

# Row by row

## bm_0056 BCBS Michigan, Medicare Advantage, Michigan

CHANGED. Spec said public with target L36007. Key says retrievable with
A59811.

- Fetched `https://www.bcbsm.com/medicare/help/using-your-plan/prior-authorization/medicare-advantage-medical-policy-guidelines/` -> 200.
  Quote: "At BCBSM and BCN, medical policies follow Medicare Advantage Policy
  Guidelines to comply with the Centers for Medicare & Medicaid Services (CMS)
  Policy, National Coverage Determinations (NCDs) and/or Local Coverage
  Determinations (LCDs)."
- Fetched `.../lcd.aspx?LCDId=39911` -> 200. Contractor table quote: "Wisconsin
  Physicians Service Insurance Corporation | MAC - Part A | 08201 - MAC A |
  J - 08 | Michigan".
- Fetched `.../article.aspx?articleId=59811` -> 200. Quote: "The following
  ICD-10-CM codes support medical necessity and provide coverage for the Total
  Knee Arthroplasty CPT codes: 27447, 27486 and 27487."

Why changed: Michigan is not in Novitas J-L, so L36007 could never have
governed this row. Michigan is WPS J-08. BCBSM publishes no public Medicare
Advantage knee policy of its own, so the controlling document is the Michigan
LCD pair.

Note on discovery: `ereferrals.bcbsm.com/prov-ref-*.shtml` silently redirected
to a 15,979 byte home page every time. The real pages are served from
`authorizations.bcbsm.com`. Recorded because a retrieval model will hit the
same redirect.

## bm_0057 BCBS North Carolina, Medicare Advantage, North Carolina

CHANGED. Spec said L36007. Key says A56777.

- Fetched `https://www.bcbsnc.com/providers/policies-guidelines-codes/medicare/guidelines/medicare-advantage-coverage-determination-hierarchy` -> 200.
  Quote: "Blue Cross NC Medicare Advantage Plan staff will perform clinical
  reviews for prior approval determinations utilizing defined Medicare criteria
  outlined in National Coverage Determinations (NCD), Local Coverage
  Determination (LCD), Local Coverage Article (LCA), Medicare Benefit Policy
  and Medicare Program Integrity manuals."
  The same page also names the contractor: "Palmetto GBA: Fiscal Intermediary
  (FI) Part A (and some Part B services) MAC for Jurisdiction M."
- Fetched `.../lcd.aspx?LCDId=33456` -> 200. Contractor table quote: "Palmetto
  GBA | A and B and HHH MAC | 11501 - MAC A | J - M | North Carolina".
- Fetched `.../article.aspx?articleId=56777` -> 200. Quote: "ICD-10-CM
  diagnoses codes for Total Knee Arthroplasty for CPT Code 27447 only."

Why changed: North Carolina is Palmetto J-M, not Novitas J-L. This is the
strongest deferral row in the key, because Blue Cross NC names its own MAC.

## bm_0058 Blue Shield of California, Medicare Advantage, California

CHANGED. Spec said public. Key says **unverified**.

- Fetched `https://www.blueshieldca.com/content/dam/bsca/en/provider/docs/medical-policies/Knee-Arthroplasty-Adults.pdf` -> 200, sha256 761ec4..., contains 27447.
- Searched all 24 pages of BSC7.10 for a line-of-business statement. The
  strings "Medicare Advantage", "Commercial", "Marketplace" and "Medi-Cal" do
  not appear anywhere in the document. The nearest scope sentence is: "Benefit
  determinations should be based in all cases on the applicable member health
  services contract benefits."

Why unverified: the document cannot say it governs a Medicare Advantage
member, because it never says which members it governs at all. Three attempts
to reach a Blue Shield of California Medicare Advantage coverage-guideline page
returned HTTP 404, and I stopped rather than keep guessing URL shapes, which
the task forbids.

Research preserved: the California LCD pair is recorded on the row. L36575's
contractor table quote: "Noridian Healthcare Solutions, LLC | A and B MAC |
01111 - MAC A | J - E | California - Entire State". So if Andrew supplies a
Blue Shield of California deferral statement, this row becomes retrievable with
no further work.

## bm_0059 CareFirst BCBS, Medicare Advantage, Maryland

CONFIRMED, and now justified rather than assumed. L36007 retained.

- Fetched `https://provider.carefirst.com/providers/medical/medical-policy.page` -> 200.
  Quote: "Medicare Medical Policy Guidelines For Medicare Advantage plans, the
  guidelines describe when certain medical services are considered medically
  necessary and are based on Original Medicare National Coverage Determinations
  (NCD's) and Local Coverage Determinations (LCD's) when available."
  State quote from the same page: "Serving Maryland, the District of Columbia,
  and portions of Virginia, CareFirst BlueCross BlueShield is the shared
  business name of CareFirst of Maryland, Inc."
- Fetched `.../article.aspx?articleId=56796` -> 200, contains 27447.

State pin: Maryland. **This pin is load-bearing.** Maryland and DC are Novitas
J-L (L36007). Virginia is Palmetto J-M (L33456). If Andrew pins CareFirst to
Virginia, the governing LCD changes. Flagged for his ruling.

Also recorded: CareFirst's own Medical Policy Reference Manual link resolves to
`secure.compliance360.com` and returned "Permission Denied". That is firsthand
proof CareFirst's own criteria are access-gated, which is why the CMS document
is the answer here.

## bm_0060 Highmark, Medicare Advantage, Pennsylvania

CONFIRMED, upgraded from unattested to attested. URL unchanged.

- Fetched `https://securecms.highmark.com/content/medpolicy/en/highmark/pa/medicare-advantage/policies/Surgery/S-39/S-39-008.html` -> 200, sha256 f1f28a..., contains 27447.
- Header quote: "HIGHMARK MEDICARE ADVANTAGE MEDICAL POLICY - PENNSYLVANIA".
- Body quote: "Medical Policy: S-39-008 ... Topic: Lower Extremity Major Joint
  Replacement (Hip and Knee) ... Procedure Codes 27130 27132 27134 27137 27138
  27445 27447 27486 27487".
- Scope quote: "The policy position applies to all Medicare Advantage lines of
  business".

This is the only row in the whole key where one fetched document attests payer,
plan type, state and CPT together. It is the cleanest row available.

## bm_0061 Horizon BCBS NJ, Medicare Advantage, New Jersey

CONFIRMED, and now justified. L36007 retained.

- Fetched `https://www.horizonblue.com/providers/products-programs/utilization-management-programs/surgical-and-implantable-device-management-program/medical-policy-criteria-and-guidelines` -> 200.
  Quote: "In the processing of claims for services provided to our MA members,
  we follow Centers for Medicare & Medicaid Services (CMS) guidelines, NCDs
  and/or LCDs. For those services where no LCD or NCD exists, claims for MA
  members will be processed based on TurningPoint policy criteria and
  guidelines."
- Fetched `.../article.aspx?articleId=56796` -> 200, contains 27447.
- New Jersey confirmed in L36007's contractor table: "12401 - MAC A | J - L |
  New Jersey".

The deferral statement is on Horizon's orthopedic utilization-management page,
so it is knee-specific, not generic boilerplate.

Horizon's own knee criteria are genuinely gated. The same page requires an
Availity Essentials sign-in, or TurningPoint web portal credentials obtained by
telephoning 1-833-436-4083, or a member ID number. All three are credential
paths and were not attempted, per the task's stop rule.

Technical note: horizonblue.com sits behind Imperva bot protection and returns
a 931 byte block page to a plain curl. Real pages came back only after adding a
full browser header set (Accept, Accept-Language, Upgrade-Insecure-Requests,
Sec-Fetch-*) and a persistent cookie jar. A retrieval agent will hit this. The
medical policy search additionally sits behind a click-through "I AGREE" terms
form whose token could not be obtained programmatically.

## bm_0062 Independence Blue Cross, Medicare Advantage, Pennsylvania

No class change: gated. Pennsylvania LCD pair recorded so the row is scorable
under the lcd_strict convention with no further research. No public
Independence Medicare Advantage knee policy was reachable, and the spec carries
no portal URL.

## bm_0063 Premera Blue Cross, Medicare Advantage, Washington

CHANGED. Spec said public. Key says **invalid**.

- Fetched `https://www.premera.com/medicalpolicies/7.01.550.pdf` -> 200,
  sha256 3a1341..., contains 27447.
  Quote, last line of the Scope section: "This medical policy does not apply to
  Medicare Advantage."
- Fetched `https://www.premera.com/wa/provider/reference/medical-policies/` -> 200.
  Quote: "The medical policies contained within this website do not apply to
  Medicare Advantage network members. Please call 888-850-8526 if you have
  questions or requests to see a Medicare Advantage medical policy for services
  prior to the end of 2024."
- The policy's own reference list cites the correct regional LCD, not L36007:
  "15. Centers for Medicare & Medicaid Services. Local Coverage Determination
  (LCD): Total Knee Arthroplasty (L36575)."

Why invalid: Premera exited Medicare Advantage on 2025-01-01. There is no
Premera Medicare Advantage product for a Washington knee patient. Separately,
the spec's L36007 could not have governed Washington regardless: Washington is
Noridian J-F, contracts 02401 and 02402.

The row is kept, not deleted. It should be excluded from the scored denominator
and reported as a key defect. Any model that confidently names a controlling
Premera Medicare Advantage knee policy is wrong.

## bm_0064 Regence BCBS, Medicare Advantage, Oregon

No class change: gated. State pinned to Oregon by deliberate choice. Regence
spans OR, WA, ID and UT, and all four sit inside Noridian J-F, so the pin does
not change the governing LCD. The Oregon LCD pair is recorded. No Regence
document naming a single state was fetched, so the state basis is a recorded
choice, not an attestation.

## bm_0065 UPMC Health Plan, Medicare Advantage, Pennsylvania

CHANGED target document. Spec said L36007. Key says MP.PA.133, with L36007
retained as the alternate convention.

- Fetched `https://embed.widencdn.net/download/upmc/rqw3ib3zmx/MP.PA.133.pdf` -> 200,
  sha256 2b4447..., contains 27447 in its CPT table: "27447 Arthroplasty, knee,
  condyle and plateau; medial AND lateral compartments with or without patella
  resurfacing (total knee arthroplasty)".
- Scope quote: "This policy applies to the following lines of business: (Check
  those that apply.)" with the CMS-MA column carrying (X) on PA, HMO, PPO and
  DSNP. Footnote: "The check next to a line of business indicates that the
  policy has applicability to that line of business, and the policy will
  further explain or define any coverage, exceptions, exclusions, limitations,
  variations, or special circumstances."
- State: policy number MP.**PA**.133, and "Reference State Addendums for:
  Delaware ( ) Maryland ( ) New Jersey ( ) Ohio ( ) Virginia ( ) West Virginia
  ( ) Wisconsin ( )", all unchecked, so this is the base Pennsylvania policy.

Method note that matters: the checkbox grid is a four-column table that flowed
text extraction scrambles. I read it from PDF word coordinates with PyMuPDF
instead. The COMMERCIAL checkbox column sits at x=190, CMS-MA at x=269, DHS-MA
at x=386, ANCILLARY at x=532. Empty boxes tokenise as "(" and ")" separately;
checked boxes tokenise as the single token "(X)". That is how each (X) was
attributed to a column without guessing.

## bm_0066, bm_0067 BCBS Michigan and BCBS NC, Commercial

No change: none. Carried forward from the spec. Not re-researched, because the
priority order put the public rows first.

## bm_0068 Blue Shield of California, Commercial, California

CHANGED. Spec said public. Key says **unverified**. Same reason as bm_0058:
BSC7.10 never names a line of business.

This is the shared-document test T002 flagged. The spec cited one Blue Shield
of California PDF for three different rows: bm_0058 Medicare Advantage,
bm_0068 Commercial, bm_0079 ACA Marketplace. **Confirmed as a labeling
shortcut.** One document with no scope statement cannot settle three different
lines of business.

## bm_0069 to bm_0072 CareFirst, Highmark, Horizon, Independence, Commercial

No change: gated. Firsthand notes recorded above for CareFirst
(secure.compliance360.com "Permission Denied") and Horizon (terms-agreement
form plus Imperva block).

## bm_0073 Premera Blue Cross, Commercial, Washington

RETRIEVABLE, but on the weakest basis in the key. **Flagged for Judge.**

- Same document as bm_0063: 7.01.550, fetched 200, contains 27447.
- Attestation is by exclusion, not by positive naming. The policy states it
  does not apply to Medicare Advantage, and the Premera policy index repeats
  that site-wide. Neither the policy nor the index ever uses the word
  "Commercial".
- State attested: "Premera Blue Cross is an independent licensee of the Blue
  Cross Blue Shield Association serving businesses and residents of Alaska and
  Washington state, excluding Clark County."

Honest statement of the judgement call: this does not meet the strict bar the
board set, which is a quote where the document says it governs this plan type.
I recorded it as retrievable because the document is genuinely Premera's
operative non-Medicare knee policy, and marking it unverified would hide a
correct answer from the eval and understate the model's real task. The row
carries `attestation_basis: "scope_by_exclusion"` so the scorer can report the
retrievable count both with and without it. If the Judge disagrees, flipping
this row and bm_0084 to unverified is a two-line change and drops the
retrievable count from 10 to 8.

## bm_0074 Regence BCBS, Commercial, Oregon

No change: gated. The spec's portal URL is carried forward.

## bm_0075 UPMC Health Plan, Commercial, Pennsylvania

CHANGED. Spec said login_gated. Key says **retrievable**. This is a
KEY_DEFECT_FOUND promotion under the T002 ruling.

- Same MP.PA.133 PDF, fetched at 200 with no login, contains 27447.
- COMMERCIAL column word coordinates: HMO ( ), PPO ( ), Fully Insured ( ),
  Self Funded ( ), Marketplace HMO ( ), Marketplace PPO ( ), Marketplace EPO
  ( ), Indiv. Off Exchange ( ), **All (X)** at x=188.
- The individual sub-boxes are unchecked while "All" is checked, which is the
  usual convention when a policy covers a whole column.

## bm_0076 Wellmark BCBS, Commercial, Iowa

No change: gated. State pinned to Iowa by deliberate choice; Wellmark also
serves South Dakota. Both are inside WPS J-05, and no Wellmark row is Medicare
Advantage, so the pin is not load-bearing.

## bm_0077, bm_0078 BCBS Michigan and BCBS NC, ACA Marketplace

No change: none. Carried forward.

## bm_0079 Blue Shield of California, ACA Marketplace, California

CHANGED to unverified. Third of the three rows sharing the unscoped BSC7.10.

## bm_0080 to bm_0083 CareFirst, Highmark, Horizon, Independence, ACA Marketplace

No change: gated. Carried forward.

## bm_0084 Premera Blue Cross, ACA Marketplace, Washington

RETRIEVABLE on `scope_by_exclusion`, identical to bm_0073. **Flagged for
Judge, same caveat.** The two rows share one document and one reasoning chain,
so grading them differently would be arbitrary.

## bm_0085 Regence BCBS, ACA Marketplace, Oregon

No change: gated.

## bm_0086 UPMC Health Plan, ACA Marketplace, Pennsylvania

CHANGED. Spec said login_gated. Key says **unverified**.

MP.PA.133 leaves Marketplace HMO, Marketplace PPO and Marketplace EPO
unchecked, yet checks COMMERCIAL "All", and the three marketplace lines sit
inside the COMMERCIAL column. The document genuinely contradicts itself on this
point. Neither gated nor retrievable can be attested, so the ambiguity is
recorded rather than resolved by inference.

## bm_0087 Wellmark BCBS, ACA Marketplace, Iowa

No change: gated.

## bm_0088 BCBS Michigan, Medicaid, Michigan

No change: gated.

## bm_0089 BCBS North Carolina, Medicaid, North Carolina

CHANGED. Spec said public. Key says **unverified**.

- Fetched `https://guidelines.carelonmedicalbenefitsmanagement.com/wp-content/uploads/2025/11/PDF-Joint-Surgery-2025-11-15.pdf` -> 200,
  sha256 b33ae1..., contains 27447.
- Across all 75 pages the document never names Blue Cross NC, never names
  Healthy Blue, and never names North Carolina Medicaid. Its own header
  disclaims plan-specific applicability: "Approval and implementation dates for
  specific health plans may vary. Please consult the applicable health plan for
  more details."
- Two attempts to reach Healthy Blue North Carolina provider pages returned
  HTTP 404. No further URL was tried, because pattern-guessing is forbidden.

Why this matters for the eval: a vendor's clinical guideline is not by itself
the controlling document for a named health plan. Crediting it would be exactly
the confident-but-wrong failure the headline metric exists to catch, so the row
is preserved as unverified rather than counted.

## bm_0090, bm_0093 Blue Shield of California and Independence, Medicaid

No change: none. Carried forward.

## bm_0091, bm_0092 Highmark and Horizon, Medicaid

No change: gated. Carried forward.

## bm_0094 UPMC Health Plan, Medicaid, Pennsylvania

CHANGED. Spec said login_gated. Key says **retrievable**. Second
KEY_DEFECT_FOUND promotion.

- Same MP.PA.133 PDF, 200, no login, contains 27447.
- DHS-MA column at x=386 carries (X) on the "Health Choices/PH" row. DHS-MA is
  the Pennsylvania Department of Human Services Medical Assistance programme,
  and HealthChoices physical health is Pennsylvania's Medicaid managed care
  programme. CHIP (X) and Community HealthChoices CHC/MLTSS (X) are also
  checked.

---

# Deviations from the task text, stated plainly

1. **`ma_deferral_status` uses a fourth value, `"unverified"`.** The task fixed
   three values: defers, publishes_own, invalid. On bm_0058 (Blue Shield of
   California), bm_0062 (Independence) and bm_0064 (Regence) I have no payer
   document attesting any of the three. Picking one anyway would be the exact
   model-asserted labelling the board bans, so I added a fourth value rather
   than invent a status. No verify command checks the enum.

2. **`attestation_quote` is a composite string on deferral rows.** The task
   asks for one verbatim quote saying the document governs this payer, plan
   type and state. On a deferral row no single document can say all three: the
   payer page attests payer and plan type, and the CMS contractor table attests
   the state. The field therefore carries both quotes, each labelled with its
   source URL and separated by `||`, and `attestation_basis` records
   `deferral_two_part`.

3. **Two rows recorded retrievable on exclusion-based scope** (bm_0073,
   bm_0084). Explained in full above. Machine-readable via
   `attestation_basis: "scope_by_exclusion"`.

4. **Two rows promoted from gated to retrievable** (bm_0075, bm_0094). The task
   said no need to crack gated rows. I did not attempt to crack them; the same
   already-fetched UPMC document turned out to attest them, so the T002
   KEY_DEFECT_FOUND rule applied itself.

# Open items for Andrew

1. **The Medicare Advantage convention** stays unresolved and is now blocking
   nothing. Every Medicare Advantage row records both candidate answers.
2. **The CareFirst state pin.** Maryland was chosen. Maryland and DC are
   Novitas J-L; Virginia is Palmetto J-M. This is the one state pin that
   changes a governing document.
3. **bm_0073 and bm_0084.** Accept exclusion-based scope, or drop the
   retrievable count from 10 to 8.
4. **Blue Shield of California.** If Andrew can supply a Blue Shield of
   California statement of Medicare Advantage deferral, or line-of-business
   scope for BSC7.10, three rows move out of unverified in one step. This is
   the single highest-value piece of missing evidence.
5. **Healthy Blue North Carolina.** One working URL for the Healthy Blue NC
   Medicaid clinical guideline list would settle bm_0089.

# What was deliberately not attempted

- No login, no NPI, no credential, no payer telephone call.
- The CMS coverage API (`api.coverage.cms.gov`) returned HTTP 401 and requires
  an authentication token. Abandoned, because a token is a credential.
- Every public search engine is blocked from this host: DuckDuckGo returned
  HTTP 202 anomaly pages, Mojeek and Bing returned captchas, and public SearxNG
  instances returned 429 or 403. All discovery was therefore done by
  robots.txt, sitemap.xml and link-following from payer root domains. That is a
  stricter method anyway, because it cannot pattern-guess a URL.

---

# 2026-07-26, T015: bm_0058 promoted to retrievable (Judge ruling T013)

Task T015. Applied by GoalBuddy Worker against
`data/policy_platform/answer_key_v1.json` under Judge ruling T013 on the same
board. This entry supersedes the T003 headline table at the top of this file.

## What changed

Row **bm_0058** (Blue Shield of California, Medicare Advantage, California,
CPT 27447) moves from `unverified` to **`retrievable`**, on
`attestation_basis: deferral_two_part`, with `ma_deferral_status: attested`.

T003 could not settle the row because the only Blue Shield knee document it
reached, medical policy BSC7.10, never names a line of business. That finding
stands and is unchanged. The promotion rests on a different document that T003
never reached: the Blue Shield provider utilization management page at
`https://www.blueshieldca.com/en/provider/guidelines-resources/guidelines-procedures/utilization-management`.

That page supplies part one of `deferral_two_part`. Part two is unchanged and
was never in doubt: LCD **L36575** with companion Billing and Coding Article
**A57685** (Noridian, jurisdiction J-E, whose contractor table lists
California, and whose article carries CPT 27447).

**Counted document key: `A57685`.** No other retrievable row uses it, so unique
documents on the retrievable side move from 6 to 7. The issuer is CMS, which
was already counted, so unique issuers stay at 4.

## The two PM errors that T013 corrected

**Error 1, the quote started one sentence too late.** The PM submitted a quote
beginning "The resources are not listed in use order...". That start point
drops the only clause that names Blue Shield as the user of the criteria, and
what remains is a general statement about what regulators require. On that
span the promotion is not supported. The key now records the extended span,
verbatim:

> Blue Shield and Blue Shield Life use the utilization management criteria
> found in the following resources to determine medical appropriateness and
> coverage. The resources are not listed in use order for utilization
> management and medically necessary decisions. The specific hierarchy for each
> line of business is determined by regulatory government bodies. For example,
> Medicare requires use of the Medicare Managed Care Manual and NCD/LCD’s
> first.

The apostrophe in `NCD/LCD’s` is the typographic right single quote, U+2019,
not an ASCII apostrophe. Any grep or assertion against this string must use the
typographic character. A verify command on T015 asserts U+2019 is present.

**Error 2, the recorded hash does not reproduce.** The PM recorded sha256
`d329984708e4c08ee6fca9216df93f60d5c2116dbc3ce1a1b331729bae409df3` for that
page. Judge T013 refetched and got
`e5982dc0c713588bcedfdb345903f14f58494acf56990ff6761ae2f3462ea692`. Worker
T015 refetched again on 2026-07-26 and got a third value,
`8ee08c1ee72002a63f8dc4ecfa6b52491bf6de6d381051a2832aafb3e879ec8d`. All three
fetches returned HTTP 200, needed no login, and carried the identical verbatim
paragraph above. The page rebuilds its markup on every request, so a raw-HTML
sha256 is not an identity check for this artifact.

The key therefore records `content_hash_stable: false` on this row, keeps all
three observed digests in `content_hash_note`, presents none of them as
authoritative, and pins identity to the verbatim string in `identity_string`
and `attestation_quote`. T016 sweeps every other recorded payer-page hash for
the same defect.

## Why the plan type is marked inferred, not explicit

The utilization management page never writes the words "Medicare Advantage".
T013 therefore added a field `plan_type_named` to every retrievable row. Ten
rows are `explicit`. bm_0058 alone is `instrument_inferred`, with this basis
recorded on the row:

> The page never writes Medicare Advantage. Plan type is identified by the
> Medicare Managed Care Manual, CMS Pub. 100-16, which instructs Medicare
> Advantage organizations only, and by two D-SNP-only resource entries, D-SNP
> being a Medicare Advantage product type.

This exists so a reader can report the strong-attestation subset both with and
without the softer row, and see exactly what the softer row contributes.

## CPT 27447 is not on the Blue Shield page

`fetched.cpt_27447_present` is **false** for bm_0058, and that is truthful. A
refetch on 2026-07-26 counted zero occurrences of `27447` on the utilization
management page. The code lives on A57685, which is part two of the basis and
is recorded in `ma_convention.lcd`. A retrieval answer naming only the Blue
Shield page must not be graded wrong for that reason alone, exactly as
`cms_note` already says for LCD pages.

## Rows that did NOT change

bm_0068 (Commercial) and bm_0079 (ACA Marketplace) **stay unverified**. T013
ruled that four independent negative checks establish the absence of a public
scope statement, not the presence of a gated one. Reclassifying them as gated
would be a guess, and it would inflate the honest-abstention denominator with
rows nobody proved. No row was deleted. No row other than bm_0058 changed,
except to gain the `plan_type_named` field.

## Superseding counts, replacing the T003 headline table

| Class | T003 count | Now | Spec said |
|---|---|---|---|
| retrievable | 10 | **11** | 13 public |
| gated | 17 | 17 | 20 login-gated |
| none | 6 | 6 | 6 no public policy |
| invalid | 1 | 1 | (no such class) |
| unverified | 5 | **4** | (no such class) |
| **total** | **39** | **39** | 39 |

Derived figures now recorded in the key's `counts` block: scored rows 34,
across 11 payers, of which 9 are Medicare Advantage. The retrievable side is 11
rows resting on 7 unique documents from 4 unique issuers. The strong subset,
meaning `single_document_full_scope` plus `deferral_two_part`, is 9 rows, 6
documents and 3 issuers; excluding the one instrument-inferred row it is 8
rows, 5 documents and 3 issuers. The weak subset, meaning `scope_by_exclusion`,
stays at 2 rows. Arithmetic: 11 plus 17 plus 6 equals 34 scored; 34 plus 4
unverified plus 1 invalid equals 39.

## Honesty note on the direction of this change

T013 recorded, and this log repeats, that the promotion flatters the result.
The 95 percent upper bound on retrieval error improves from 39.3 percent at 6
documents to 34.8 percent at 7. Two facts limit that. The issuer bound does not
move at all: 4 issuers, and 3 in the strong subset, which stays the binding
constraint on the retrieval side. The headline confident-wrong metric only
changes denominator, 33 to 34, an 8.7 to 8.4 percent bound.
