# T021 gated re-probe: evidence log

Status: PROBE IN PROGRESS. This file is written incrementally, one payer block at a
time, as each payer probe finishes. Do not read a missing payer block as a finding.

Worker: T021. Board: docs/goals/policy-retrieval-eval/state.yaml.
A Worker may NOT change any row_class. Every class below is a PROPOSED class for a
Judge to apply or reject.

Started 2026-07-26.

---

## Method and standing caveats (applies to every payer block below)

- Every fetch used `scripts/policy_eval/webtools.py` `fetch()` (full browser headers,
  persistent session) or `webtools._session().get()` for raw HTML when href extraction
  was needed. Both send the identical request shape. All scripts ran from the repository
  root, never from /tmp.
- Every text test used `normalize_for_match` / `normalized_contains` from
  `scripts/policy_eval/common.py`. No raw substring test produced any conclusion here.
- `blocked` (detect_bot_block) is OUR artefact and never produces a class.
  `login_wall` (detect_login_wall) is a payer property.
- BENCHMARK LIMITATION, RECORDED AS ORDERED, INDEPENDENT OF WHAT THE PROBE FOUND.
  All 14 gated rows carry `fetched: null`. Seven of them carry no URL anywhere in the row
  (bm_0071, bm_0076, bm_0082, bm_0085, bm_0087, bm_0088, bm_0092), so their `gated` label
  was never auditable by anyone downstream. Discovery here was payer level, starting from
  each payer's own public policy index, because there was no recorded target to fetch.
- DIRECTION OF FINDING is stated for every row. `gated` earns the model full credit for
  abstaining, so any finding that KEEPS a row gated FLATTERS US and is marked FLATTERING.

---

## Payer 1 of 6: Horizon BCBS NJ (bm_0071 Commercial, bm_0082 ACA Marketplace, bm_0092 Medicaid)

### URLs tried, including dead ends

| # | URL | HTTP | bytes | stripped chars | blocked (detect_bot_block) | login_wall (detect_login_wall) | 27447 present |
|---|---|---|---|---|---|---|---|
| H1 | https://services3.horizon-bcbsnj.com/hcm/medpol2.nsf/homePage?OpenPage= | 200 | 7125 | 5503 | False | False | False |
| H2 | https://www.horizonblue.com/providers/products-programs/utilization-management-programs/surgical-and-implantable-device-management-program/medical-policy-criteria-and-guidelines | 200 | 495051 | 73752 | False | False | False |
| H3 | https://www.horizonblue.com/providers/policies-procedures/policies/medical-polices/medical-policy-manual | 200 | 518825 | 75775 | False | False | False |
| H4 | https://www.horizonblue.com/providers/products-programs/utilization-management-programs/surgical-and-implantable-device-management-program/orthopedic-services/orthopedic-services-procedure-codes | 200 | 493378 | 72235 | False | False | **True** |
| H5 | https://www.myturningpoint-healthcare.com/policySearch?org=8C85EE13-1CB6-444D-A9B7-7723610DC846 | 200 | 118481 | 563 | False | False | False |
| H6 | https://www.horizonblue.com/providers/products-programs/utilization-management-programs/carelon-medical-benefits-management/musculoskeletal-program | 200 | 494237 | 73790 | False | False | False |
| H7 | https://services3.horizon-bcbsnj.com/hcm/MedPol2.nsf/MedicalPolicies?OpenView | 200 | 567 | 15 | **True** (`thin_200_response:15_text_chars_of_567_bytes`) | False | False |
| H8 | https://services3.horizon-bcbsnj.com/hcm/MedPol2.nsf/Medical%20Policies%20By%20Section?OpenView | 200 | 620 | 27 | **True** (`thin_200_response:27_text_chars_of_620_bytes`) | False | False |
| H9 | https://services3.horizon-bcbsnj.com/hcm/MedPol2.nsf/Medical%20Policies%20By%20Section?ReadViewEntries&Count=2000 | 200 | 170599 | n/a (XML) | False | False | n/a |
| H10 | https://services3.horizon-bcbsnj.com/hcm/MedPol2.nsf/MedicalPolicies?ReadViewEntries&Count=2000 | 200 | 137574 | n/a (XML) | False | False | n/a |
| H11 | https://services3.horizon-bcbsnj.com/hcm/MedPol2.nsf/MedicalPolicies?SearchView&Query=27447&Count=200 | 200 | 3340 | 90 | False | False | 0 results |
| H12 | https://services3.horizon-bcbsnj.com/hcm/MedPol2.nsf/MedicalPolicies?SearchView&Query=%22total+knee%22&Count=200 | 200 | 11006 | 405 | False | False | 24 results |
| H13-H36 | 24 individual policy documents at https://services3.horizon-bcbsnj.com/hcm/MedPol2.nsf/MedicalPolicies/<UniID> for the 24 UniIDs returned by H12 | 200 on all 24 | 22,139 to 373,402 | 16,873 to 140,371 | False on all 24 | False on all 24 | **False on all 24** |

H7 and H8 are `detect_bot_block` True. Under the standing rule that is OUR artefact and
produces NO class. They are Domino frameset stubs, and H9/H10 reach the same two views'
full contents by plain HTTP, so nothing is lost.

### The recorded gating justification is DISPROVED

The row note said: "Horizon's medical policy search sits behind a click-through terms
agreement form and Imperva bot protection; a programmatic POST was blocked."

Both halves fail on this probe. The terms page H1 returns HTTP 200, 7,125 bytes, no wall
and no bot block, and it is not a barrier at all: the underlying policy documents are
directly fetchable without ever submitting it (H13 to H36, 24 of 24 at HTTP 200). The
whole 724-entry policy index is dumpable in ONE plain HTTP GET at H10, and the categorised
index at H9. No Imperva stub, no HTTP 403, no login redirect was observed on any of the
36 URLs. The disproof is the UNFLATTERING direction, which is why it is stated first.

### What is actually public, and what is actually walled

PUBLIC. The Horizon Uniform Medical Policy Manual is fully public and fully walkable by
plain HTTP. It carries no total knee arthroplasty criteria policy. That is a BOUNDED
absence, not a substring guess: the full index was enumerated (724 policies at H10, 734
view entries at H9, title regex for knee/arthroplast/joint returned 16 unrelated titles
such as Knee Braces and Total Ankle Replacement), and every one of the 24 documents the
payer's own full-text search returns for "total knee" was fetched and tested with
`normalized_contains`, giving 27447 absent 24 of 24.

CAUTION ON ONE SUB-RESULT. H11, the payer's own full-text search for the literal 27447,
returned zero results. I do NOT rely on that. A search index that does not tokenise bare
numerals would return exactly the same zero. This is the same shape as the earlier HbA1c
false absence. The load-bearing evidence is the 24 firsthand document fetches, not H11.

WALLED. Horizon states in its own words on H2 that the criteria are vendor held, and it
publishes three and only three access routes, all of which require identity or credentials.
Verbatim from H2:

> "TurningPoint manages and maintains the medical policy criteria and guidelines used to
> conduct PA/MND reviews as part of this program."

> "Using Availity Essentials(TM) You may review the medical policy criteria and guidelines
> online. To access this information, sign in to Availity Essentials(TM), under Payer
> Spaces, select the Horizon BCBSNJ tile ..."

> "Using TurningPoint's Web Portal If you do not have access to Availity Essentials(TM),
> you may access the medical policy criteria and guidelines used to conduct PA/MND reviews
> as part of this program through TurningPoint's web portal. To register for access to
> TurningPoint's web portal, call TurningPoint at 1-833-436-4083, Monday through Friday
> between 8 a.m. and 5 p.m., ET to register to obtain access credentials."

> "Using TurningPoint's Medical Policies and Clinical Guidelines tool ... Click TurningPoint
> Medical Policies and Clinical Guidelines. Enter the Horizon member ID number. Click
> Search. Click and review the policy in question."

The third route is the criteria INDEX itself. Its URL is printed verbatim on H2 and was
fetched as H5 at HTTP 200. Its entire body is an identity gate. Verbatim, the complete
563 stripped characters of H5:

> "TurningPoint Provider Portal Medical Policies and Clinical Guidelines Welcome To view
> the TurningPoint Healthcare Solutions Medical Policies, please use the Policy Access Form
> below. Policy Access Form First Name First Name First Name Last Name Last Name Last Name
> Email Address Email Address Email Address I agree to the Terms of Use & Privacy Policy Get
> Access If you have any additional questions or need assistance, please contact: Email -
> providersupport@turningpoint-healthcare.com Phone - 1-866-422-0800 (c) 2015- 2026
> TurningPoint Healthcare Solutions, LLC."

Raw-HTML form controls extracted from H5: `input name="firstName"`, `input name="lastName"`,
`input name="emailAddress"`, `input type="checkbox" name="touAndPp"`, and one submit button
labelled Get Access. There is no password field.

DISCREPANCY RECORDED HONESTLY. H2 says the tool asks for a Horizon member ID number. The
live tool at H5 asks for name, surname and email instead. Both are quoted above. I did not
submit either form. Submitting an identity form to obtain a payer document is outside the
no-credential probe standard and outside this task.

UNREACHED BY METHOD, stated with the method verbatim, never as "unreachable": the
TurningPoint criteria documents are UNREACHED BY METHOD "plain HTTP GET of the criteria
index URL printed on the payer page, followed by regex extraction of every href, src and
quoted /api|/policy|/policies path from the raw HTML of that response, then plain HTTP GET
of each extracted link". That extraction was run. The complete set of links in H5's raw
HTML is four items: `/_next/static/chunks/00dys7uf6evgs.css`,
`/_next/static/chunks/0tp09v-u1.-p2.js`, `/icon.svg?icon.0r4z1yr_3pvc8.svg`, and
`https://myturningpoint-healthcare.com`. Zero policy links, zero API paths. I am NOT
recording "renders client-side" or "requires JavaScript"; I am recording that the printed
index exposes no document link to plain HTTP and gates its body on an identity form.

### Rubric 2.3 verdicts, per condition, per row

Candidate part one for all three rows is H4, Orthopedic Services Procedure Codes.
Verbatim scope statement from H4:

> "TurningPoint Healthcare Solutions, LLC (TurningPoint) performs Prior Authorization or
> Medical Necessity Determination reviews of the orthopedic services represented by the
> CPT(R) and HCPCS codes listed below as part of our Surgical and Implantable Device
> Management Program. Please note that the orthopedic procedure codes listed below apply
> to the Surgical and Implantable Device Management Programs offered for both Horizon
> BCBSNJ and Horizon NJ Health patients. This content was last revised on May 18, 2026 and
> may be subject to change."

The code list on H4 includes 27447 (`normalized_contains` True; the printed run is
"27442 27443 27446 27447 27486 27487 27488").

**bm_0071, Horizon BCBS NJ, Commercial, New Jersey**
- V1a payer entity named in the page's own text: **PASS**. H4 names "Horizon Blue Cross Blue Shield of New Jersey" verbatim.
- V1b row `plan_type` named explicitly in the payer's own words on the page: **FAIL**. H4 says "Horizon BCBSNJ and Horizon NJ Health patients". Those are entity names, not a line of business. The word "Commercial" as a scope statement appears on H2, not on H4, and H2 fails V1d. No single page satisfies both.
- V1c state attested: **PASS via the licensee route**. Horizon BCBSNJ is the single-state New Jersey Blue licensee and the row already carries `state_basis payer_licensee_territory`. Recorded as the licensee route, not as a positive in-text attestation.
- V1d 27447 present under `normalized_contains`: **PASS** on H4.
- V1e verb of use plus named external reviewer: **PASS**. "performs Prior Authorization or Medical Necessity Determination reviews", entity "TurningPoint Healthcare Solutions, LLC".
- V1 overall: **FAIL**, on V1b alone.
- V2 criteria document fetched: **FAIL**. Not obtained. The index is identity gated (H5).
- V3 plain-HTTP reachability of part two: **FAIL**. See UNREACHED BY METHOD above.
- V4 no contrary marking on part two: **NOT ASSESSABLE**. Part two was never obtained.
- V5 displacement: **NOT ASSESSABLE**. Part two was never obtained.
- Guard M: not applicable, this row is Commercial.
- Guard S: not assessable, part two was never obtained.
- POSITIVE WALL EVIDENCE on the criteria document or its index: **YES**. Two independent forms. (1) Verbatim portal-credential language, quoted in full above: "call TurningPoint at 1-833-436-4083 ... to register to obtain access credentials", and it is explicitly about "the medical policy criteria and guidelines used to conduct PA/MND reviews as part of this program", not about a merely nearby provider portal. (2) An identity form occupying the entire body of the criteria index H5. The Availity route is a third, and Availity sign-in is a credential wall, but I rest the finding on (1) and (2) because those name the criteria directly.
- **PROPOSED CLASS: `gated`.** Not retrievable, because the criteria document was never obtained. Not unverified, because positive wall evidence exists and is on the criteria index itself.
- **DIRECTION: FLATTERING.** This keeps bm_0071 in the pool where abstention earns full credit. Stated plainly as required. The offsetting unflattering finding, recorded above, is that the stated reason for the old label (Imperva bot block on a POST) is disproved, and the replacement reason is a different mechanism entirely.

**bm_0082, Horizon BCBS NJ, ACA Marketplace, New Jersey**
- V1a: **PASS** (same page H4). V1c: **PASS via licensee route**. V1d: **PASS**. V1e: **PASS**.
- V1b: **FAIL**, and worse than for bm_0071. No fetched Horizon page names an ACA Marketplace or Individual Marketplace line of business in a medical-policy scope statement. H2's scope list is "Horizon BCBSNJ commercial plans, self-insured Administrative Services Only (ASO) employer group plans, Braven Health plans and Horizon NJ Health plans". Marketplace is absent from it.
- V1 overall: **FAIL**. V2: **FAIL**. V3: **FAIL**. V4, V5: **NOT ASSESSABLE**.
- POSITIVE WALL EVIDENCE for THIS row: **NO**. The wall at H5 is real, but the standard requires the wall to be on the criteria document controlling THIS row, and no fetched page states which criteria set governs a New Jersey Marketplace member. The nearest thing is H1, where the manual's own terms say it covers "Horizon Blue Cross Blue Shield of New Jersey, Horizon Healthcare of New Jersey, Inc., Horizon Insurance Company, and Healthier New Jersey Insurance Company (collectively 'Horizon BCBSNJ')". Healthier New Jersey Insurance Company is plausibly the individual-market entity, but that is INFERENCE from a company name, exactly what V1b forbids, and I decline to build a class on it.
- **PROPOSED CLASS: `unverified`.** Absence of a finding is not a login wall. This mirrors the bm_0083 precedent, where Independence published no ACA set and the row went unverified rather than gated.
- **DIRECTION: UNFLATTERING.** This removes a row from the honest-abstention pool where the model would have earned full credit for abstaining, and moves it into the excluded class that enters no headline denominator.

**bm_0092, Horizon BCBS NJ, Medicaid, New Jersey**
- V1a: **PASS**. V1c: **PASS via licensee route**. V1d: **PASS** on H4. V1e: **PASS**.
- V1b: **PASS**, and this is the one row where it passes. H4 states verbatim that the code list applies to the programs "offered for both Horizon BCBSNJ and Horizon NJ Health patients", and H2 lists "Horizon NJ Health plans" in the criteria scope. Horizon NJ Health is Horizon's New Jersey Medicaid plan and is named by the payer in the payer's own words.
- V1 overall: **PASS**, all five sub-conditions.
- V2: **FAIL**. Criteria document never obtained. V3: **FAIL**. V4, V5: **NOT ASSESSABLE**.
- **Guard M: BINDING AND STATED EXPLICITLY AS ORDERED.** A vendor guideline NEVER establishes a Medicaid row. Even if the TurningPoint criteria document had been obtained and had passed V2 to V5, I would NOT propose a `deferral_vendor_two_part` promotion for bm_0092, and I do not propose one. Guard M excludes it. This is stated rather than left implicit because V1 passes for this row and would otherwise look like the start of a promotion.
- POSITIVE WALL EVIDENCE on the criteria index controlling this row: **YES**. H2 names "Horizon NJ Health plans" inside the same scope sentence that governs the three credential-gated access routes, so the wall quoted above attaches to this row directly.
- **PROPOSED CLASS: `gated`.**
- **DIRECTION: FLATTERING.** Keeps a full-credit abstention row.

### Net effect for Horizon, stated so the direction is visible

Two of three rows stay `gated`, which flatters us, and one moves to `unverified`, which does
not. No row is promoted to `retrievable`. The old justification for all three was false and
has been replaced with a different, positively evidenced one for two of them.
