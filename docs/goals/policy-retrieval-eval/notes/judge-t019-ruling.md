# Judge T019 ruling, in full and verbatim

Ruled 2026-07-26. Read-only; the Judge changed no file. This note is the
authoritative text of the ruling. A Worker applying it must follow the wording
here exactly and must not paraphrase.

PM verification of the load-bearing evidence is at the END of this file.


## decision

rejected

## full_outcome_complete

```json
false
```

## rationale

The gated label on all three Independence rows is affirmatively contradicted by pages I fetched myself with no credential. A vendor deferral CAN support retrievable, under a five-condition test whose fifth condition is a displacement check against the frozen 5.1 authority ladder. bm_0072 promotes; bm_0062 is displaced by CMS and goes unverified; bm_0083 has no evidence either way and goes unverified. Net effect shrinks the free-abstention pool from 23 to 20 and worsens the safety bound, which is the harder direction, while improving the issuer bound, which is disclosed. Probe resumes under the written standard.

## ruling_1_the_standard

```json
{
  "answer": "YES, a vendor deferral can support a retrievable class, and refusing it outright would be familiarity rather than principle. What makes CMS different from Carelon is NOT retrievability and NOT document quality. It is AUTHORITY, and authority is already handled by the frozen rubric section 5.1 ladder, not by the attestation vocabulary. A CMS LCD binds a Medicare Advantage organisation by regulation. A vendor guideline binds only by the payer's own written delegation, and yields where a higher rung has spoken. So the CMS-versus-vendor distinction belongs in a displacement check applied per row, not in a blanket refusal. A blanket refusal would also be the FLATTERING refusal, because it keeps rows in the gated class where abstention earns full credit.",
  "new_rubric_section": "2.3 VENDOR-DEFERRAL ADMISSIBILITY, new attestation_basis deferral_vendor_two_part. All five conditions must hold. Every one is mechanically checkable by a Worker.",
  "V1_part_one_payer_binding": "A page on the PAYER'S OWN registrable domain, fetched firsthand this session, HTTP 200, detect_login_wall False and detect_bot_block False, which satisfies all five of: V1a names the payer entity in its own text; V1b names the row's plan_type explicitly in the payer's own words on the page (not inferred, not from the URL path); V1c attests the row's state positively in the page text, or the payer is a single-state Blue licensee already pinned by state_basis payer_licensee_territory, and which of the two is recorded; V1d contains CPT 27447 under normalized_contains, never a raw substring test; V1e states, with a verb of use, that this code requires prior authorisation or utilisation management, and NAMES the external entity performing the review. NOTE: V1 is STRICTLY STRONGER than the existing section 2.2 part one, which requires neither the CPT code nor the plan type on the page.",
  "V2_part_two_criteria_document": "A document published by the entity named in V1e, fetched firsthand this session, HTTP 200, detect_login_wall False and detect_bot_block False, containing CPT 27447 under normalized_contains AND containing medical-necessity criteria for the row's procedure. Criteria means at least one QUANTIFIED or explicitly conditional coverage requirement, for example a BMI figure, a duration of conservative therapy, an imaging requirement or a laboratory threshold. A bare code list fails V2 and can never be part two. Record sha256 and whether it reproduces across three fetches.",
  "V3_plain_http_reachability": "Part two must be reachable from a URL PRINTED ON the part-one page using plain HTTP requests only: no JavaScript execution, no credential, no cookie beyond an ordinary session, no site search endpoint required. Every hop recorded verbatim with status and byte count. If part two can only be reached by executing JavaScript or by a credential, V3 fails and the row is unverified, not retrievable.",
  "V4_no_contrary_marking": "Part two carries no statement excluding the row's plan_type, payer or state. Any contrary marking fails V4 and the row is unverified, never retrievable. Silence is not contrary evidence, per the existing 2.1 Guard 2 reasoning.",
  "V5_displacement_check_this_is_the_one_that_does_the_work": "Part two must not itself defer to a higher authority that governs this row. Apply the frozen section 5.1 ladder. Mechanical rule: if part two contains a sentence yielding to CMS criteria for Medicare Advantage, AND section 5.1 resolves an in-jurisdiction LCD covering the row's state whose companion Billing and Coding Article lists CPT 27447, then part two is DISPLACED for that row and V5 FAILS. A displaced row is unverified unless a separate, admissible section 2.2 part one exists on the payer's own domain naming CMS NCDs or LCDs.",
  "guard_M_medicaid": "A vendor guideline NEVER establishes a Medicaid row. Medicaid criteria are state-mandated, and the Carelon guideline's own text says applicable federal and state coverage mandates take precedence. Any Medicaid row reached this way is unverified, never retrievable. This mirrors the existing 2.1 Guard 1 and binds bm_0088, bm_0091 and bm_0092 in the resumed probe.",
  "guard_S_substitution": "Where part two states that the health plan may substitute its own policy, that sentence is recorded VERBATIM in the row and in known_limitations. It does not defeat V1 to V5, because silence in part one is not contrary evidence, but it must travel with the number under section 9.",
  "counted_document": "Part two, the criteria document, is the counted document and goes in fetched. Part one goes in a new object vendor_convention.payer_page, mirroring ma_convention.plan_page. Rationale: exact parity with deferral_two_part, whose counted document is the CMS article and not the payer page. This is the HARDER choice, because it forces the model to name the criteria document to earn correct-retrieval credit, rather than crediting it for finding the payer's code list.",
  "strong_subset": "deferral_vendor_two_part COUNTS as strong. Add it to STRONG_BASES in scripts/policy_eval/denominators.py alongside single_document_full_scope and deferral_two_part, because V1 is strictly stronger than 2.2 part one on three axes: the code is on the page, the plan type is on the page, and the payer is on the page."
}
```

## ruling_2_the_rows

```json
{
  "bm_0072": {
    "order": "gated -> retrievable",
    "basis": "deferral_vendor_two_part",
    "plan_type_named": "explicit",
    "why": "Passes V1 to V5 and both guards, on evidence I personally reproduced. V1a payer named on page; V1b the page prints 'Medical Policy Bulletin Commercial'; V1c the page prints 'serving the health insurance needs of Philadelphia and southeastern Pennsylvania' and the row is pinned to Pennsylvania; V1d 'Knee Replacement 27446 * 27447 *'; V1e 'Joint Surgery Procedure Codes That Require Preservice Utilization Management and Level of Care Review Through Carelon Medical Benefits Management'. V2 the Carelon Joint Surgery guideline 2025-11-15 contains 27447 once with the full total-knee descriptor and contains quantified criteria: BMI at 62 occurrences with an explicit BMI 40 threshold, conservative at 128, physical therapy at 52, HbA1c 8% or less, tobacco abstinence at least 6 weeks. V3 reached in four plain requests with no JavaScript. V4 no contrary marking for Commercial. V5 the guideline's only yielding clause is Medicare Advantage specific and does not touch a Commercial row. Not Medicaid, so Guard M does not bite. CONSISTENCY CHECK: refusing bm_0072 while keeping bm_0061 retrievable would be incoherent, since bm_0061's part-one Horizon page carries NO CPT code at all (contains_cpt_27447 false) and the IBX bulletin does carry it. The incoherence would run in the flattering direction.",
    "counted_document": "https://guidelines.carelonmedicalbenefitsmanagement.com/wp-content/uploads/2025/11/PDF-Joint-Surgery-2025-11-15.pdf",
    "doc_key": "CARELON_Joint-Surgery-2025-11-15",
    "sha256": "b33ae12d3a59b1b43ed4864b4a61a4e0a0f3fbcd6d8709344700c6e94165147a",
    "content_hash_stable": true,
    "content_hash_note_to_record": "Reproduced 3 of 3 by Judge T019 on 2026-07-26, byte-identical at 974,145 bytes, same sha256 every time, application/pdf. This is the ONLY counted document in this key whose raw digest reproduces, so it is the one row where sha256 is a genuine identity check.",
    "identity_string_instruction": "The Worker must record identity_string as a verbatim span it fetches and confirms itself through normalized_contains. The Judge did not pin one, because pinning a string the Judge did not verify character by character is exactly the error this board punishes. Until then, identity rests on the reproducing sha256.",
    "alternate_current_edition": "https://guidelines.carelonmedicalbenefitsmanagement.com/wp-content/uploads/2024/12/PDF-Joint-Surgery-2024-11-17-UC0125.pdf returns 200, 949,858 bytes, sha256 begins f53d2d6ff7668d1a, contains 27447. Carelon lists BOTH editions as current and the Independence bulletin does not say which it adopted. Naming the 2024 edition grades CORRECT_STALE under section 2 Tier 3, NOT wrong. Record both URLs in the row."
  },
  "bm_0062": {
    "order": "gated -> unverified",
    "why": "It is NOT gated: I fetched the public Medicare Advantage bulletin twice at HTTP 200, 111,962 to 111,963 bytes, 3,349 characters of text, CPT 27447 present, zero occurrences of sign in, log in, login, password, register, portal or credential. The key note 'no public Medicare Advantage knee policy was reachable' is false. It is NOT retrievable either, because V5 FAILS. The Carelon guideline states verbatim: 'Applicable federal and state coverage mandates take precedence over these clinical guidelines, and in the case of reviews for Medicare Advantage Plans, the Guidelines are only applied where there are not fully established CMS criteria.' Under section 5.1 there is no NCD for total knee arthroplasty, rung 2 fires, Pennsylvania is Novitas J-L, L36007's companion article A56796 lists 27447, so CMS criteria ARE fully established and the vendor document is displaced for this row. The obvious fallback, promoting on the ordinary deferral_two_part route, FAILS section 2.2 P3: the Independence Medicare Advantage bulletin never names a CMS NCD or LCD. It names Carelon. The transitive step from Carelon to CMS is asserted by the VENDOR about itself, not by the payer, and it is conditional on its face, because the same document says a health plan may substitute its own policy. That is a genuine evidentiary gap, and the honest class for a genuine evidentiary gap is unverified.",
    "narrow_reopening_condition": "If a later Worker fetches a PUBLIC Independence Medicare Advantage page that satisfies section 2.2 P1 to P4 by naming CMS NCDs or LCDs with a verb of use, bm_0062 promotes to retrievable under the EXISTING deferral_two_part basis with fetched = A56796 and ma_convention.plan_page = that page, and no new vocabulary. The unfetched lead is the Medicare Advantage 'Services Requiring Precertification' policy, the second 27447 match at entry 17 of the T018 URL log. A Judge gates that promotion, per section 4.1."
  },
  "bm_0083": {
    "order": "gated -> unverified",
    "why": "There is no evidence in either direction, and the gated class requires POSITIVE wall evidence which does not exist. The Independence portal is demonstrably open at HTTP 200 with no credential and publishes exactly three policy sets, Commercial, Medicare Advantage and MA PPO Host. It publishes no ACA Marketplace set, and no fetched page states whether the Commercial set governs Marketplace members. Retrievable via section 2.1 scope_by_exclusion FAILS at E1 and E2: the Commercial bulletin states no line-of-business exclusion at all, it affirmatively says Commercial, so there is no closed exclusion set and no residual. The class 'none' would be WRONG and would be the flattering error, because none earns CORRECT_ABSTENTION at full credit and we have no evidence that Independence publishes nothing for Marketplace. unverified is the only class the evidence supports.",
    "note": "Do not mark it invalid. Independence plausibly sells Marketplace products in Pennsylvania; I did not fetch evidence either way and will not assert it."
  }
}
```

## ruling_3_bm_0062_medicare_advantage_tension

```json
{
  "verdict": "BOTH, but not in the way the task framed it. It is NOT a legal defect and it IS a row defect and a product finding.",
  "not_a_legal_defect": "The apparent conflict dissolves on the vendor's own text. Carelon states that for Medicare Advantage reviews its guidelines apply ONLY where CMS criteria are not fully established. That is precisely 42 CFR 422.101(b)(6), rung 4 of the frozen 5.1 ladder: internal criteria are a gap-filler and never override rungs 1 to 3. Independence delegating the mechanics of review to a vendor whose criteria self-limit to the CMS gap is lawful. I do not attach a mechanism I cannot demonstrate; I quote the vendor's own sentence.",
  "is_a_row_defect": "Yes. It removes bm_0062 from the retrievable route, because part two is displaced and no admissible part one exists. Hence unverified.",
  "is_a_product_finding_and_this_is_the_pitch_line": "Yes, and it is the strongest patient-facing finding on this board. The ONLY document Independence publishes for a Medicare Advantage knee case points the reader at a vendor guideline that does not govern the case, and nothing on that page tells the reader that Medicare's own regional rule controls instead. A patient, or an unaided model, that follows the payer's own page will cite the wrong criteria in an appeal. That is exactly the confident-but-wrong failure the whole benchmark exists to measure, observed in the wild, in the payer's own publishing, before any model was run. Carry it into the pitch as a worked example, with the two verbatim quotes and the 5.1 ladder, and NOT as a claim that Independence is breaking the law."
}
```

## ruling_4_resume_the_probe

```json
{
  "verdict": "GO. Resume as a single Worker package covering all six payers and all fourteen rows, but ONLY after the standard above is written into the rubric as v1.5. Do not let six payers be judged against a moving standard.",
  "written_standard_for_the_probe": [
    "Apply section 2.3 V1 to V5 plus Guard M and Guard S, verbatim, per row. Record the verdict on each condition separately, never as a single yes or no.",
    "The probe RECORDS evidence and a PROPOSED class. It changes no row_class. A Judge applies. A Worker may not reclassify.",
    "gated survives ONLY on positive wall evidence, and the wall must be on the CRITERIA document or its index, not merely on a provider portal that happens to sit nearby. Positive wall evidence means one of: a redirect to a path matching /login|/signin|/idp|/auth, a sign-in form in the body, an HTTP 401 or 403, or verbatim portal-credential language quoted in full.",
    "A row with no positive wall evidence and no admissible chain is unverified, NOT gated. Absence of a finding is not a login wall.",
    "detect_bot_block True NEVER produces a class. A bot block is our artefact. Retry under at least two request shapes before recording anything.",
    "Never conclude absence from a raw substring test. Use normalize_for_match and normalized_contains everywhere. Precedent: a 325-character quote on bm_0057 was reported missing from a page where it was present and unchanged.",
    "Never conclude that a client-side index is unwalkable without first extracting href values from the raw HTML and following them by plain HTTP. Judge T019 walked the Carelon index to the criteria PDF in three plain hops after the PM recorded that it needed JavaScript.",
    "Copy URLs verbatim, including odd-looking tails. The Independence page prints a link whose href literally ends /musculoskeletal/html; that exact form returns 200 and is not a truncation artefact.",
    "Record every URL tried including dead ends, with HTTP status, byte count, tag-stripped character count, blocked verdict and login_wall verdict.",
    "Run probe scripts from the repository root, never from /tmp, because a stray /tmp/inspect.py shadows the standard library and silently empties every PDF extraction."
  ],
  "expect_recurrence": "Carelon, formerly AIM Specialty Health, and comparable vendors such as eviCore and TurningPoint are used by many Blue licensees for musculoskeletal review. bm_0061's own note already names TurningPoint for Horizon. Treat a vendor name found on a public payer page as a LEAD, not a conclusion; the row still has to pass V1 to V5.",
  "priority_row": "bm_0071 first. Its recorded gating evidence is an Imperva bot block on a programmatic POST, which Judge T017 already ruled is our own request shape and not a payer property. Its gated label currently rests on a justification the board has already disproved.",
  "may_a_run_start_before_the_probe_finishes": "NO. T005 stays blocked. Fourteen of the twenty honest-abstention rows would otherwise be graded at full credit on labels never verified, and one payer of one probed has already had all three of its rows overturned."
}
```

## ruling_5_deferred_wording

```json
{
  "CRITICAL_off_by_one_correction_read_this_first": "The board, the T017 receipt and the T018 card all say to replace known_limitations ITEM 8. That is WRONG and a Worker must not obey it literally. In the key as committed at 51efc6c the list has nine items. Item 8 is the content-hash-instability caveat, which is TRUE, load-bearing and must NOT be touched. The disproved item is ITEM 9, the one beginning 'OPEN AND UNRESOLVED. On bm_0061 the Horizon attestation page'. Match it by that opening text, NEVER by index. Obeying the index would delete a correct caveat and leave the false one standing.",
  "a_verification_method_on_the_gated_rows": {
    "apply_to_the_14_rows_that_remain_gated": "bm_0064, bm_0069, bm_0070, bm_0071, bm_0074, bm_0076, bm_0080, bm_0081, bm_0082, bm_0085, bm_0087, bm_0088, bm_0091, bm_0092",
    "exact_text": "NO FIRSTHAND PER-ROW FETCH. This row's gated label is carried forward from the seed_review_39 spec and from the reviewer's note. No URL, no HTTP status and no login flag were ever recorded for it, and fetched is null. The string that previously stood here, claiming a firsthand HTTP fetch on 2026-07-26 with a browser user agent, was FALSE and is removed under the ruling of Judge T019. The payer-level re-probe ordered by Judge T017 reached Independence Blue Cross only, and this payer was not probed. Positive evidence of a login wall, meaning a redirect to a login path, a sign-in form, an HTTP 401 or 403, or verbatim portal-credential language, has NOT been recorded for this row. See docs/goals/policy-retrieval-eval/notes/gated-reprobe-t018.md.",
    "bm_0074_addendum_append_verbatim": " This row is the single gated row carrying a spec_original_target_url. That URL was not fetched in T018 and no HTTP status was recorded for it.",
    "note": "This string does NOT depend on the probe outcome, which is what T018 believed and why it deferred. It states only what was and was not done. It stays honest after the probe, which then appends to it."
  },
  "a2_verification_method_bm_0072": "Firsthand HTTP fetch on 2026-07-26 with browser-shaped headers, no login, no credential, no payer telephone call. Reproduced 3 of 3 by Worker T018, re-reproduced independently by the PM, and re-reproduced by Judge T019 at 2 of 2 on the payer page and 3 of 3 byte-identical on the criteria document. Part one is the Independence Blue Cross Commercial Medical Policy Bulletin, Attachment B to policy 00.01.66t, Procedure Codes for Joint Surgery, which carries CPT 27447 and names Carelon Medical Benefits Management as the reviewer. Part two is the Carelon Clinical Appropriateness Guidelines, Joint Surgery, edition 2025-11-15, reached from the link printed on part one in four plain HTTP hops with no JavaScript, no credential and no cookie beyond an ordinary session. Admitted under rubric section 2.3, deferral_vendor_two_part, by Judge T019. The row's earlier gated label and its note 'No portal URL in spec; nothing public found' were both false and are corrected here.",
  "a3_verification_method_bm_0062": "Firsthand HTTP fetch on 2026-07-26 with browser-shaped headers, no login, no credential, no payer telephone call. Reproduced 3 of 3 by Worker T018, re-reproduced by the PM and by Judge T019 at 2 of 2. The Independence Blue Cross Medicare Advantage Medical Policy Bulletin, Attachment B to policy MA00.047t, is public at HTTP 200 with no credential and carries CPT 27447, so the earlier note 'no public Medicare Advantage knee policy was reachable' was FALSE. The bulletin defers review to Carelon Medical Benefits Management. Judge T019 fetched the Carelon Joint Surgery guideline, edition 2025-11-15, at HTTP 200 with no credential, 3 of 3 byte-identical, and it states verbatim: 'Applicable federal and state coverage mandates take precedence over these clinical guidelines, and in the case of reviews for Medicare Advantage Plans, the Guidelines are only applied where there are not fully established CMS criteria.' Under rubric section 5.1 rung 2 the in-jurisdiction document for Pennsylvania is L36007 with companion Billing and Coding Article A56796, which is fully established, so the Carelon guideline is DISPLACED for this row and fails the section 2.3 V5 check. No Independence Medicare Advantage page satisfying rubric section 2.2 P1 to P4 has been fetched, so part one of a deferral_two_part basis is not in evidence. The label is unverified: not gated, and not retrievable.",
  "a4_verification_method_bm_0083": "Firsthand HTTP fetch on 2026-07-26 with browser-shaped headers, no login, no credential, no payer telephone call. The Independence Blue Cross medical policy portal is public at HTTP 200 with no credential and publishes three policy sets, Commercial, Medicare Advantage and MA PPO Host. It publishes no ACA Marketplace set, and no fetched page states whether the Commercial set governs Marketplace members. No positive login-wall evidence exists for this row, so the gated label is unsupported. The Commercial bulletin does not qualify under rubric section 2.1, because it states no line-of-business exclusion at all and therefore fails both E1 and E2. This is an absence of evidence in both directions and the label is unverified.",
  "a5_notes_field_rewrites": {
    "bm_0062": "Independence Blue Cross publishes a PUBLIC Medicare Advantage medical policy bulletin, Attachment B to MA00.047t, that lists CPT 27447 and requires Level of Care Review by Carelon Medical Benefits Management. The prior note claiming no public Medicare Advantage knee policy was reachable is withdrawn as false. The Carelon guideline is displaced for Medicare Advantage by its own terms where CMS criteria are fully established, which they are for CPT 27447 in Pennsylvania under L36007 and A56796. Unverified pending a public Independence Medicare Advantage page that names CMS NCDs or LCDs under rubric 2.2.",
    "bm_0072": "Admitted retrievable by Judge T019 under rubric section 2.3. The prior note 'No portal URL in spec; nothing public found' is withdrawn as false.",
    "bm_0083": "Independence publishes Commercial, Medicare Advantage and MA PPO Host policy sets and no ACA Marketplace set, and nothing fetched states whether the Commercial set governs Marketplace members. No login-wall evidence exists. Recorded as an absence in both directions."
  },
  "b_replace_known_limitations_ITEM_9_not_item_8": "RAISED, INVESTIGATED, RESOLVED, AND THE ORIGINAL ASSERTION WAS FALSE. Worker T016 reported on 2026-07-26 that the Horizon attestation page on bm_0061 served the recorded 296-character quote on two fetches and then failed to serve it on nineteen further fetches over the following twenty minutes, and it wrote here that no substring of the quote was presently retrievable on demand. The alarm was correctly raised, correctly escalated, and T016 correctly refused to change the row class. The assertion itself is FALSE. The PM reproduced the page 6 of 6 and Judge T017 reproduced it 25 more times, 3 by browser-shaped curl, 14 by no-cache curl spaced over 90 minutes and 8 through the shipped fetcher, for 31 of 31 fetches at HTTP 200, all 494,917 decompressed bytes, all carrying content digest 39f425cf34e622ea7f0335a87dd4736c94107655ff7e808b5ab302fd1c749322, with the 296-character quote present verbatim in tag-stripped text every time. Worker T018 fetched it once more under the normalised matcher and found it present. The cause of the nineteen absences in that single seventeen-minute window is NOT established and is NOT claimed. The PM originally attributed them to an Imperva HTTP-200 bot stub; Judge T017 disproved that, because the stub is 927 to 931 bytes and T016's absences were full pages of 492,010 to 492,144 bytes, and the PM withdrew the claim in place. bm_0061 keeps row_class retrievable and attestation_basis deferral_two_part. It carries a standing control instead: any run whose normalised matcher fails to find that quote must halt and escalate, and must never regrade or reclass the row on its own. content_hash_stable stays false, which was always correct.",
  "b2_ALSO_UNORDERED_UNTIL_NOW_bm_0061_content_hash_note": {
    "why": "The same disproved sentence also sits inside the row, in bm_0061.ma_convention.plan_page.content_hash_note, and still says a Judge is needed on a page a Judge already ruled on. Nobody ordered this fixed. Under section 9 the key is copied byte for byte into every report, so a false sentence in the key becomes a false sentence in the pitch.",
    "replace_the_header": "Replace the leading 'NOT AN IDENTITY CHECK, AND THIS PAGE NEEDS A JUDGE.' with 'NOT AN IDENTITY CHECK. RULED ON BY JUDGE T017.'",
    "replace_the_trailing_three_sentences": "Replace 'No identity_string is recorded here, because no substring of the quote is presently retrievable on demand. This does not change row_class, which a Worker may not do. It is escalated for a Judge, because part one of this row's deferral_two_part basis rests on that quote.' with: 'Judge T017 ruled on this page. The quote reproduced 31 of 31 across two agents and two independent HTTP stacks, and Worker T018 reproduced it once more under the normalised matcher. The earlier statement here, that no substring of the quote was presently retrievable on demand, is FALSE and is withdrawn. The identity check for this page is the verbatim 296-character quote recorded in the quote field, tested through normalize_for_match and never through a raw substring test. The cause of the nineteen absences T016 observed is not established and is not claimed. Standing control: any run whose normalised matcher fails to find this quote must halt and escalate, and must never regrade or reclass the row on its own.' Leave every other sentence in that note unchanged, including the observed digests and the byte counts.",
    "keep": "Do NOT delete the record that the alarm was raised, in either location. It is the board's evidence that the escalation happened and was checked."
  },
  "c_new_known_limitations_item_10_url_absence": "THE GATED CLASS RESTS LARGELY ON A CARRIED-FORWARD LABEL, NOT ON EVIDENCE. Of the fourteen rows still classed gated, thirteen carry no recorded URL of any kind, no HTTP status and no login flag, and fetched is null on all fourteen. Their label comes from the seed_review_39 spec and a reviewer's note, not from a firsthand fetch. Until 2026-07-26 every one of them nonetheless carried the string 'Firsthand HTTP fetch on 2026-07-26 with a browser user agent' in provenance.verification_method; that string was false and has been removed. Positive wall evidence, meaning a redirect to a login path, a sign-in form, an HTTP 401 or 403, or verbatim portal-credential language, is recorded for NONE of the fourteen. One of them, bm_0071, previously cited an Imperva bot block on a programmatic POST as its gating evidence, which is an artefact of our own request shape and not a payer property. Gated rows are graded CORRECT_ABSTENTION at full credit and supply 14 of the 20 honest-abstention rows, so an always-abstain policy still collects most of that credit on labels never verified. Before the Judge T019 ruling the position was worse and is recorded so the finding is not erased: sixteen of seventeen gated rows had no URL, and gated rows supplied 17 of the 23 honest-abstention rows. The payer-level re-probe reached one payer of seven and overturned that payer's label on all three of its rows, which should RAISE rather than lower the prior on the remaining six. Six payers covering fourteen rows remain unprobed: Regence BCBS, CareFirst BCBS, Highmark, Horizon BCBS NJ, Wellmark BCBS and BCBS Michigan. This item stands whatever that probe returns.",
  "c2_new_known_limitations_item_11_bot_block": "THE HARNESS COULD NOT SEE AN HTTP-200 BOT BLOCK, AND NOW CAN. Until 2026-07-26 detect_login_wall returned (False, None) on a 931-byte Imperva 'Request unsuccessful' stub served at HTTP 200, so the harness could not tell a refused fetch from a successful one. A refused fetch yields no readable text, which pushes the model toward abstention, which is the behaviour the headline metric rewards. Worker T018 added detect_bot_block, kept strictly separate from detect_login_wall because a login wall is a true payer property and a bot block is an artefact of ours that must never produce a row class; gave the fetcher full browser headers over a persistent session; and recorded blocked and blocked_reason on every fetch. While doing so it created and caught a second instance of the same family: advertising brotli in Accept-Encoding, which this interpreter cannot decode, made one payer CDN return 13,025 bytes of still-compressed data at HTTP 200 that decoded to unreadable text, with no error reported anywhere. Rubric v1.5 makes a blocked fetch a distinct outcome, BLOCKED_FETCH, excluded from the confident-wrong numerator and denominator and printed on its own headline line. One weakness in the same family is recorded and NOT yet fixed: pdf_text returns an empty string on any exception with no reason recorded, so a broken PDF extraction is indistinguishable from a document containing no text, and that points in the flattering direction.",
  "c3_new_known_limitations_item_12_vendor_deferral": "ONE RETRIEVABLE ROW RESTS ON A COMMERCIAL VENDOR GUIDELINE, NOT ON A PAYER OR CMS DOCUMENT. bm_0072 is admitted under rubric section 2.3, deferral_vendor_two_part. Part one is a public Independence Blue Cross Commercial bulletin that carries CPT 27447 and names Carelon Medical Benefits Management as the reviewer. Part two is the Carelon Clinical Appropriateness Guidelines, Joint Surgery, edition 2025-11-15, which is the counted document and the only Carelon document in the benchmark. Three limits travel with it. First, the Carelon guideline states verbatim: 'If requested by a health plan, Carelon will review requests based on health plan medical policy/guidelines in lieu of the Carelon Guidelines.' The Independence bulletin is silent on whether it substitutes its own policy. Silence is not contrary evidence under rubric 2.1 Guard 2, but the substitution clause is real and is recorded rather than smoothed away. Second, Carelon lists TWO Joint Surgery editions as current, 2024-11-17 updated 2025-01-01 and 2025-11-15, and the Independence bulletin does not say which edition it has adopted, so naming the 2024 edition grades CORRECT_STALE under section 2 Tier 3 rather than wrong. Third, this promotion moves the unique-issuer count from 4 to 5, and section 0.1 names the issuer count as the BINDING constraint on the retrieval side. That is a larger flattering move than the v1.3 promotion of bm_0058, which moved no issuer at all, and it must be disclosed on the same line as any retrieval number.",
  "c4_new_known_limitations_item_13_the_MA_product_finding": "A MEDICARE ADVANTAGE PLAN ROUTES KNEE REVIEW TO A COMMERCIAL VENDOR, AND THE VENDOR YIELDS BACK TO MEDICARE. On its public Medicare Advantage bulletin, Attachment B to policy MA00.047t, Independence Blue Cross marks CPT 27447 as requiring Level of Care Review by Carelon Medical Benefits Management, exactly as it does on the Commercial line. The Carelon guideline itself resolves the apparent conflict with Medicare law, stating verbatim: 'Applicable federal and state coverage mandates take precedence over these clinical guidelines, and in the case of reviews for Medicare Advantage Plans, the Guidelines are only applied where there are not fully established CMS criteria.' Under rubric section 5.1 there is no National Coverage Determination for total knee arthroplasty, so rung 2 fires and Pennsylvania's in-jurisdiction document, L36007 with companion Billing and Coding Article A56796, is fully established and controls. So there is no legal defect and none is alleged. There is a patient-facing defect, and it is a product finding rather than a benchmark defect: the only document Independence publishes for a Medicare Advantage knee case points the reader at a vendor guideline that does not govern the case, and nothing on that page tells the reader that Medicare's own regional rule controls instead. A patient, or an unaided model, that follows the payer's own page will cite the wrong criteria. bm_0062 is therefore unverified rather than retrievable, because no public Independence Medicare Advantage page has been found that satisfies rubric section 2.2 P1 to P4 by naming CMS NCDs or LCDs.",
  "d_rubric_v1_5": {
    "header_change": "Set the title to 'RUBRIC v1.5' and the machine-read line to 'rubric_version: 1.5'. scripts/policy_eval/common.py RUBRIC_VERSION must be updated in the same commit, because denominators.py aborts when the file and the constant disagree.",
    "amendment_log_row_verbatim": "| 1.5 | 2026-07-26 | Judge T019 rulings. Added section 2.3, the five-condition vendor-deferral test: V1 payer binding with the CPT code and the plan type on the payer's own page, V2 a public criteria document from the named vendor containing CPT 27447 and quantified criteria, V3 plain-HTTP reachability from the printed link with no JavaScript, V4 no contrary marking, V5 a displacement check against the section 5.1 authority ladder. Added Guard M excluding Medicaid rows and Guard S requiring the vendor's substitution clause to be recorded verbatim. Added the attestation basis `deferral_vendor_two_part` and counted it in the strong subset. Made a blocked fetch a distinct outcome, `BLOCKED_FETCH`, excluded from the confident-wrong numerator and denominator, never counted correct, printed on its own headline line by row_id, requiring a documented retry under at least two request shapes, and not reportable at b >= 7. Reissued the section 0.2 table for three row moves: bm_0072 gated to retrievable, bm_0062 and bm_0083 gated to unverified. | **none. No eval run had executed. T005 had not started.** |",
    "blocked_fetch_definition_verbatim": "A row grades `BLOCKED_FETCH` when the model names a document AND the adjudicator's Stage A fetch of that document returns `blocked == True` from `detect_bot_block` under at least TWO different request shapes, both recorded. It is NOT the same as Tier 5 UNRESOLVABLE: UNRESOLVABLE is a property of the document or the claim, BLOCKED_FETCH is an artefact of our own request. A BLOCKED_FETCH row is excluded from BOTH the numerator and the denominator of CONFIDENT-BUT-WRONG, is never counted CORRECT, is never counted as honest abstention, and is printed on its own headline line listed by row_id. If the host serves the document to ANY request shape we can make, the row is not blocked and must be graded normally. Anti-burial control, mirroring the section 6 human-review trigger: if BLOCKED_FETCH exceeds 20% of N_scored, that is b >= 7 at N_scored 32, the run is NOT reportable. This exists so a failure cannot be laundered into an infrastructure excuse.",
    "section_0_2_new_pinned_table": {
      "N_total": 39,
      "excluded_invalid": "1 (bm_0063)",
      "excluded_unverified": "6 (bm_0062, bm_0068, bm_0079, bm_0083, bm_0086, bm_0089)",
      "N_scored": "32 (12 + 14 + 6, also 39 minus 6 minus 1)",
      "scored_payers": 11,
      "retrievable_rows": 12,
      "retrievable_documents": 8,
      "retrievable_issuers": "5 (CMS, Highmark, UPMC, Premera, Carelon)",
      "strong_rows_documents_issuers": "10 / 7 / 4",
      "strong_excl_instrument": "9 / 6 / 4",
      "gated": 14,
      "none": 6,
      "ma_scored_rows": "8 (10 MA rows minus bm_0063 invalid minus bm_0062 unverified)",
      "needs_human_review_not_reportable_at": "h >= 7 (ceil of 20% of N_scored 32, which is 6.4)",
      "blocked_fetch_not_reportable_at": "b >= 7 (same ceiling rule)"
    },
    "section_0_2_denominator_map_replacement": "CONFIDENT-BUT-WRONG over N_scored - h - b. CORRECT RETRIEVAL over 12 rows and 8 documents. HONEST ABSTENTION over 20 (14 gated plus 6 none), unverified rows excluded. MISSED RETRIEVABLE over 12. NEEDS HUMAN REVIEW over 32. BLOCKED FETCH over 32. grade_plan_strict additionally excludes bm_0064 ONLY, because bm_0062 has left the scored set and its exclusion is now redundant.",
    "section_7_template_changes": "CORRECT RETRIEVAL line becomes '<c> / 12 rows, resting on <cd> / 8 unique documents and <ci> / 5 unique issuers', with 'strong-attestation subset: <cs> / 10 rows, <cds> / 7 documents, <cis> / 4 issuers' and 'strong subset excluding instrument-inferred: <cse> / 9 rows, <cdse> / 6 documents'. HONEST ABSTENTION becomes '<a> / 20   (14 gated + 6 none; unverified excluded)'. MISSED RETRIEVABLE becomes '<m> / 12'. NEEDS HUMAN REVIEW becomes '<h> / 32'. Add a new mandatory line directly under NEEDS HUMAN REVIEW: 'BLOCKED FETCH:        <b> / 32              (our artefact, excluded from every line above: <row_ids>)'. Denominators line becomes 'N_total=39  N_scored=32  retrievable=12 rows / 8 docs / 5 issuers' and 'gated=14  none=6'. Excluded unverified list becomes six row_ids. UNVERIFIED ROWS BLOCK header becomes '(6 rows, 15.4% of 39, excluded from every line above)' and every '/ 4' inside it becomes '/ 6'. INDEPENDENCE AND CEILING becomes: retrieval upper bound <= 31.2% at N=8 unique documents, 34.8% at N=7 strong-only, 39.3% at N=6 excluding instrument-inferred, ISSUER-BOUND binding <= 45.1% at N=5 issuers and 52.7% at N=4 issuers in the strong subset; safety <= 8.9% at N=32 rows and 23.8% at N=11 unique payers. All bounds are the exact binomial 1 - 0.05^(1/N), never 3/N.",
    "mandatory_disclosure_paragraph_verbatim": "**Disclosure required with any v1.5 or later number.** The v1.5 promotion of bm_0072 moves the unique-issuer count from 4 to 5 and the unique-document count from 7 to 8, improving the reportable retrieval ceiling from 52.7% to 45.1% on the binding issuer bound and from 34.8% to 31.2% on the document bound. Section 0.1 names the issuer count as the binding constraint, and this is the FIRST change on this board to move it; the v1.3 promotion of bm_0058 moved no issuer at all. Three facts bound the flattery and must travel with it on the same line. The safety bound WORSENS, from 8.4% at N_scored 34 to 8.9% at 32. The honest-abstention pool SHRINKS from 23 rows to 20, so an always-abstain policy now collects less free credit. The unverified coverage gap GROWS from 4 of 39, 10.3%, to 6 of 39, 15.4%, and is printed as a limitation of the benchmark. The Judge that ruled was not the party that found the evidence; it reproduced the payer page 2 of 2 and the vendor criteria document 3 of 3 byte-identical before ruling, and it walked the vendor index by plain HTTP after the PM had recorded that the index could not be walked without JavaScript."
  }
}
```

## denominator_impact

```json
{
  "row_moves": "bm_0072 gated -> retrievable. bm_0062 gated -> unverified. bm_0083 gated -> unverified.",
  "before": "N_total 39, N_scored 34, retrievable 11 rows / 7 documents / 4 issuers, strong 9/6/3, strong excl instrument 8/5/3, gated 17, none 6, unverified 4, invalid 1, scored_payers 11, ma_scored_rows 9, honest-abstention denominator 23.",
  "after": "N_total 39, N_scored 32, retrievable 12 rows / 8 documents / 5 issuers, strong 10/7/4, strong excl instrument 9/6/4, gated 14, none 6, unverified 6, invalid 1, scored_payers 11 (unchanged, Independence still has bm_0072 scored), ma_scored_rows 8, honest-abstention denominator 20.",
  "arithmetic_check": "12 + 14 + 6 = 32 scored. 32 + 6 + 1 = 39 total. Verified by recomputing from the rows.",
  "new_exact_binomial_bounds": "All 1 - 0.05^(1/N), never 3/N. Safety: 8.9% at N_scored 32, was 8.4% at 34, so the safety bound WORSENS. Retrieval documents: 31.2% at N=8, was 34.8% at N=7. Retrieval issuers, the binding one: 45.1% at N=5, was 52.7% at N=4. Strong documents: 34.8% at N=7, was 39.3% at N=6. Strong issuers: 52.7% at N=4, was 63.2% at N=3. Strong excluding instrument-inferred documents: 39.3% at N=6, was 45.1% at N=5. Payers unchanged at 23.8% for N=11.",
  "thresholds": "needs_human_review_not_reportable_at stays h >= 7, because ceil(0.20 x 32) = 7 exactly as ceil(0.20 x 34) = 7. Restate its basis as 20% of 32, do not leave the text saying 'pinned to 34'. New blocked_fetch_not_reportable_at b >= 7 on the same rule.",
  "grade_plan_strict": "Its exclusion list drops bm_0062 and keeps bm_0064 only.",
  "the_case_where_nothing_moves": "If the PM or a Worker declines to apply this ruling and nothing moves, that is NOT the neutral option and must not be described as caution. It means the key keeps three rows labelled as sitting behind a login on a payer whose pages I opened eight times with no credential; it keeps 17 rows asserting a firsthand HTTP fetch that never happened; it keeps an honest-abstention denominator of 23 in which 17 rows earn full credit on unverified labels; and it keeps two disproved sentences that section 9 will copy byte for byte into the MD Catalyst report. Doing nothing is the flattering choice here, not the safe one."
}
```

## incentive_direction_statement

```json
{
  "stated_before_the_justification": "My ruling points NET HARDER, by three effects to one, and the one flattering effect is the largest single move on the binding constraint in this board's history, so I disclose it rather than net it out.",
  "harder_effects": [
    "The honest-abstention pool falls from 23 rows to 20, a 13% cut in the credit an always-abstain policy collects for free. Gated rows fall from 17 to 14.",
    "N_scored falls from 34 to 32, so the headline safety bound worsens from 8.4% to 8.9%. The number we quote at the pitch gets WEAKER.",
    "The unverified coverage gap, printed as a limitation of the benchmark and not of the model, grows from 10.3% to 15.4% of rows.",
    "MISSED_RETRIEVABLE exposure grows from 11 rows to 12, and bm_0072 becomes a row where the model can be caught confidently wrong instead of a row where saying nothing scores full marks."
  ],
  "flattering_effect_disclosed_not_minimised": "Promoting bm_0072 adds a new unique document AND a new unique issuer, Carelon. Section 0.1 states that the issuer count is the binding constraint on the retrieval side. This moves it from 4 to 5, improving the reportable ceiling from 52.7% to 45.1%. Judge T013 flagged the analogous flattery when promoting bm_0058 and noted that the issuer count did not move; here it does. That makes this the most flattering single change yet made on the retrieval side, and it is why I ordered a mandatory v1.5 disclosure paragraph mirroring the v1.3 one.",
  "why_i_ruled_anyway": "Because the alternative is asserting a login wall on pages I personally fetched through, eight times across three agents, with no credential, no cookie and no redirect to a sign-in path. A false label on a free-credit row is the exact failure this board exists to police, and it is worse than a disclosed improvement to a bound.",
  "correcting_the_task_framing": "The task suggested promotion is plausibly the harder direction. That is true for the abstention pool and the scored denominator, and FALSE for the retrieval ceiling. Both are real. I did not treat promotion as automatically self-serving, and I did not treat it as automatically virtuous either. I ruled each of the three rows on its own evidence and they moved in two different directions, which is itself evidence that the standard, not the denominator, drove the outcome."
}
```

## pm_audit

```json
{
  "verdict": "SAME FAILURE MODE AS T017 CAUGHT, TWICE MORE, AND BOTH TIMES IN THE DENOMINATOR-PRESERVING DIRECTION. This is now a pattern rather than an incident, and it needs a standing control.",
  "finding_1_refuted_the_stated_reason": "The PM wrote in notes/gated-reprobe-t018.md, verification section: 'The specific musculoskeletal knee guideline document was not isolated, because the index renders client-side and the PM did not execute JavaScript.' I refuted that. Using plain requests.get with browser headers and no JavaScript at all, I extracted href values from the raw HTML and reached the criteria document in three hops from the guidelines home page: /current-musculoskeletal-guidelines/ at 200 and 250,379 bytes, then /joint-surgery-2025-11-15/ at 200 and 527,828 bytes, then the PDF at 200 and 974,145 bytes. The PDF contains CPT 27447 and the quantified criteria. So part two was isolable by the same method the PM was already using, and it did not require JavaScript.",
  "finding_1_direction": "Leaving part two unisolated is what turned a completable evidence chain into an apparently novel and unresolvable third pattern. That framing kept all three Independence rows in gated, where abstention earns full credit and the honest-abstention denominator stays at 23. The failure runs in the denominator-preserving direction, exactly as T017 found.",
  "finding_1_calibration_and_fairness": "I do not claim the PM knew. The PM's VERDICT was correct and evidence-led: the Carelon site is public, HTTP 200, no credential, and I reproduce that. The PM also flagged its own uncertainty and referred the question up rather than resolving it. What is wrong is the stated REASON, which is a mechanism the PM attached to an absence it had not demonstrated. That is the precise error T017 named, repeated on a new absence.",
  "finding_2_taxonomy_framing_postponed_a_promotion": "The PM framed the finding as 'a THIRD attestation pattern the key has no language for'. On its face the Independence Commercial bulletin already satisfies, word for word, the key's EXISTING retrievable row_class definition and its section 3 promotion test: public, HTTP 200, no login, contains CPT 27447, and self-attesting to payer, plan type and state, all of which are printed on the page. Framing an existing-vocabulary case as a vocabulary gap postpones the promotion. Direction: postponement keeps the row gated. Softer than finding 1, and worth recording. It does not change my ruling, because I require part two anyway, which is a HIGHER bar than the row_class definition alone.",
  "credit_where_due_and_this_matters": "The PM's corrections of the Worker were exemplary and ran AGAINST its own interest. It downgraded the Worker's summary phrase 'two knee-replacement policy bulletins' to the accurate 'code lists with no medical-necessity criteria: no BMI threshold, no conservative-therapy duration, no imaging requirement.' That correction made the promotion HARDER to justify, and the PM made it anyway and recorded it in place rather than rewriting history. It also accepted the T017 correction in place. The PM is not concealing; it is stopping one step early and supplying a tidy reason for stopping.",
  "standing_control_i_order": "Add to the board rules: a PM or Worker that records a reason why a document could not be reached must state the METHOD it tried, verbatim, and must try plain-HTTP link extraction before recording 'renders client-side', 'requires JavaScript', 'not indexed' or any equivalent. An unreached document is recorded as UNREACHED BY METHOD X, never as unreachable. Rationale, stated plainly: three separate incidents on this board now consist of an unproven mechanism attached to an absence, and every one of them pointed toward keeping a denominator larger or a row unpromoted."
}
```

## worker_package

```json
{
  "objective": "Apply the Judge T019 ruling in full to the answer key, the rubric and the harness, in one commit. Move bm_0072 gated to retrievable under the new deferral_vendor_two_part basis; move bm_0062 and bm_0083 gated to unverified. Write rubric v1.5 with new section 2.3, Guards M and S, the BLOCKED_FETCH outcome, the reissued section 0.2 table and the mandatory disclosure paragraph. Replace the false verification_method string on the 14 remaining gated rows and write the three per-row strings. Replace known_limitations item 9, NOT item 8, and correct the same disproved sentences inside bm_0061.ma_convention.plan_page.content_hash_note. Add known_limitations items 10, 11, 12 and 13. Update STRONG_BASES, RUBRIC_VERSION, the report template and the grader for BLOCKED_FETCH. Every wording string is supplied verbatim in the T019 receipt: copy it, do not paraphrase it.",
  "allowed_files": [
    "data/policy_platform/answer_key_v1.json",
    "docs/goals/policy-retrieval-eval/notes/scoring-rubric-v1.md",
    "docs/goals/policy-retrieval-eval/notes/key-corrections.md",
    "docs/goals/policy-retrieval-eval/notes/gated-reprobe-t018.md",
    "scripts/policy_eval/common.py",
    "scripts/policy_eval/denominators.py",
    "scripts/policy_eval/grade.py",
    "scripts/policy_eval/report.py",
    "scripts/policy_eval/selftest_report_gate.py",
    "scripts/policy_eval/selftest_discrimination.py",
    "tests/test_policy_eval_fetch_guards.py"
  ],
  "verify": [
    "python3 -c \"import json;json.load(open('data/policy_platform/answer_key_v1.json'))\"",
    "python3 scripts/policy_eval/denominators.py",
    "python3 scripts/policy_eval/selftest_report_gate.py",
    "python3 scripts/policy_eval/selftest_discrimination.py",
    "python3 scripts/policy_eval/selftest_tool_isolation.py",
    "python3 scripts/policy_eval/verify_no_leak.py",
    "python3 tests/test_policy_eval_fetch_guards.py",
    "python3 -c \"import json;k=json.load(open('data/policy_platform/answer_key_v1.json'));c={};[c.__setitem__(r['row_class'],c.get(r['row_class'],0)+1) for r in k['rows']];print(c);assert c=={'retrievable':12,'gated':14,'none':6,'unverified':6,'invalid':1},c\"",
    "python3 -c \"import json;k=json.load(open('data/policy_platform/answer_key_v1.json'));bad=[r['id'] for r in k['rows'] if r['row_class']=='gated' and 'Firsthand HTTP fetch' in r['provenance']['verification_method']];print(bad);assert bad==[],bad\"",
    "python3 -c \"import json;k=json.load(open('data/policy_platform/answer_key_v1.json'));s=json.dumps(k);assert 'no substring of the quote is presently retrievable on demand. This does not change row_class' not in s;assert 'NEEDS A JUDGE' not in s;assert 'Five of the eleven retrievable rows' in s, 'item 8 was destroyed; it must survive';print('caveat checks pass')\"",
    "python3 -c \"import sys;sys.path.insert(0,'scripts');from policy_eval.denominators import STRONG_BASES;print(STRONG_BASES);assert 'deferral_vendor_two_part' in STRONG_BASES\"",
    "python3 -c \"import re;t=open('docs/goals/policy-retrieval-eval/notes/scoring-rubric-v1.md').read();assert re.search(r'^`rubric_version: 1.5`',t,re.M);assert '2.3' in t and 'BLOCKED_FETCH' in t;assert '\\u2014' not in t\"",
    "python3 -c \"import json;s=open('data/policy_platform/answer_key_v1.json',encoding='utf-8').read();assert '\\u2014' not in s.replace('independent licensees','independent licensees'),'em dash present'\" ",
    "git diff --name-only"
  ],
  "stop_if": [
    "denominators.py reports any derived value not equal to its pinned value. Do not adjust the derived side to match; the pinned table in rubric 0.2 is the thing to fix.",
    "Any row_class other than bm_0062, bm_0072 and bm_0083 would change. Halt and escalate to a Judge.",
    "The known_limitations item beginning 'Five of the eleven retrievable rows' is missing after the edit. That is item 8, it is TRUE, and destroying it means the index-based instruction was followed instead of the text-based one.",
    "The record that the T016 alarm was raised is absent from either known_limitations or bm_0061's content_hash_note after the edit.",
    "A live fetch of https://guidelines.carelonmedicalbenefitsmanagement.com/wp-content/uploads/2025/11/PDF-Joint-Surgery-2025-11-15.pdf returns anything other than HTTP 200 with sha256 b33ae12d3a59b1b43ed4864b4a61a4e0a0f3fbcd6d8709344700c6e94165147a, or the document no longer contains CPT 27447 under normalized_contains. Halt and escalate; do not silently update the digest.",
    "A live fetch of either Independence bulletin returns a login wall, a 401, a 403, a redirect to a sign-in path, or detect_bot_block True. Halt and escalate; the promotion rests on those pages being public.",
    "Any of the 11 existing retrievable rows fails its attestation_quote under the normalised matcher. Halt; do not edit the quote.",
    "Any selftest that passed at 51efc6c fails after the edit.",
    "You are tempted to reclassify any of the 14 remaining gated rows. You may not. That is the next package and it needs evidence first.",
    "git diff --name-only lists a file outside allowed_files.",
    "Any file you touch contains an em dash or an en dash used as a sentence dash."
  ]
}
```

## evidence

```json
[
  "Judge reproduced the Independence Commercial bulletin 2 of 2 through the shipped policy_eval.webtools.fetch: HTTP 200, 112,321 to 112,322 bytes, 3,400 characters of tag-stripped text, CPT 27447 present, blocked False, zero occurrences of sign in, log in, login, password, register, portal, credential. URL verbatim https://medpolicy.ibx.com/ibc/Commercial/Pages/Policy/17d2df53-e600-440f-8ddd-0ad805614b91.aspx",
  "Judge reproduced the Independence Medicare Advantage bulletin 2 of 2: HTTP 200, 111,961 to 111,962 bytes, 3,349 characters, CPT 27447 present, blocked False, same zero credential-word count. URL verbatim https://medpolicy.ibx.com/ibc/ma/Pages/Policy/ea4c1763-0b64-4d01-b0ca-65c58f0f6ecc.aspx",
  "Verbatim from both pages: 'Knee Replacement 27446 * 27447 * 27486 27487 27488 27437 * 27438 * 27440 * 27441 * 27442 * 27443 * J7330 S2112' and 'Codes followed by an asterisk (*) denotes services that require additional Level of Care Review by Carelon Medical Benefits Management(R)'. Plan type printed on page as 'Medical Policy Bulletin Commercial' and 'Medical Policy Bulletin Medicare Advantage'. State printed as 'serving the health insurance needs of Philadelphia and southeastern Pennsylvania'.",
  "The href printed on the Independence page is literally https://aimspecialtyhealth.com/resources/clinical-guidelines/musculoskeletal/html, with a trailing /html that is NOT an extraction artefact. Fetched verbatim: HTTP 200, redirects to https://guidelines.carelonmedicalbenefitsmanagement.com/, 389,510 bytes. The form without /html also returns 200 and 389,506 bytes. Neither is a phantom 404.",
  "PM CLAIM REFUTED. Judge walked the Carelon index with plain requests.get and href extraction, no JavaScript: /current-musculoskeletal-guidelines/ HTTP 200 250,379 bytes, then /joint-surgery-2025-11-15/ HTTP 200 527,828 bytes, then the PDF. Three hops, no credential, no cookie beyond the session.",
  "Carelon Joint Surgery 2025-11-15 PDF: 3 of 3 fetches HTTP 200, byte-identical at 974,145 bytes, sha256 b33ae12d3a59b1b43ed4864b4a61a4e0a0f3fbcd6d8709344700c6e94165147a every time, content-type application/pdf, 241,279 characters extracted, CPT 27447 present once with the full descriptor 'Arthroplasty, knee, condyle and plateau; medial AND lateral compartments with or without patella resurfacing (total knee arthroplasty)'.",
  "Quantified criteria present in that PDF, which is what makes it part two rather than another code list: body mass index 4 occurrences, BMI 62, conservative 128, physical therapy 52, and verbatim 'It is strongly recommended that a patient with a BMI equal to or greater than 40 attempt weight reduction prior to surgery', 'maintain a hemoglobin A1C of 8% or less prior to any joint replacement surgery', 'abstinence from tobacco and nicotine products for at least 6 weeks prior to surgery'.",
  "THE V5 SENTENCE, verbatim from the Carelon PDF: 'Applicable federal and state coverage mandates take precedence over these clinical guidelines, and in the case of reviews for Medicare Advantage Plans, the Guidelines are only applied where there are not fully established CMS criteria.'",
  "THE GUARD S SENTENCE, verbatim from the same paragraph: 'If requested by a health plan, Carelon will review requests based on health plan medical policy/guidelines in lieu of the Carelon Guidelines.'",
  "Second current edition confirmed public: https://guidelines.carelonmedicalbenefitsmanagement.com/wp-content/uploads/2024/12/PDF-Joint-Surgery-2024-11-17-UC0125.pdf HTTP 200, 949,858 bytes, sha256 begins f53d2d6ff7668d1a, contains CPT 27447. Carelon lists both as current; Independence does not say which it adopted.",
  "Denominators recomputed from the rows under the ruling: retrievable 12, gated 14, none 6, unverified 6, invalid 1, N_scored 32, scored_payers 11, ma_scored_rows 8, honest-abstention 20. Exact binomial bounds 1 - 0.05^(1/N): 8.9% at 32, 31.2% at 8, 45.1% at 5, 34.8% at 7, 52.7% at 4, 39.3% at 6, 23.8% at 11. ceil(0.20 x 32) = 7.",
  "OFF-BY-ONE CONFIRMED against the committed key at 51efc6c: known_limitations has 9 items. Index 7 (item 8) begins 'Five of the eleven retrievable rows' and is TRUE. Index 8 (item 9) begins 'OPEN AND UNRESOLVED. On bm_0061 the Horizon attestation page' and is the disproved one. The board's repeated instruction to replace 'item 8' would destroy the true caveat.",
  "SECOND UNCORRECTED COPY FOUND: the string 'no substring of the quote is presently retrievable on demand' also lives inside bm_0061.ma_convention.plan_page.content_hash_note, whose header still reads 'NOT AN IDENTITY CHECK, AND THIS PAGE NEEDS A JUDGE' although Judge T017 already ruled. Section 9 copies the key byte for byte into the report, so this would print at the pitch.",
  "All 17 gated rows confirmed: fetched is null on every one, and only bm_0074 carries a spec_original_target_url. After the three Independence moves, 13 of the remaining 14 gated rows have no URL.",
  "Judge changed no file. git status at exit shows only the three pre-existing untracked runs/ directories, identical to entry, at commit 51efc6c."
]
```

## blocked_tasks

```json
[
  "T005 stays blocked. It may not start until this package lands AND the six-payer probe completes AND a Judge reviews the probe result. Fourteen of the twenty honest-abstention rows still rest on unverified labels."
]
```

## missing_evidence

```json
[
  "No public Independence Blue Cross Medicare Advantage page has been fetched that names CMS NCDs or LCDs with a verb of use. Until one is, bm_0062 cannot be retrievable. The unfetched lead is the Medicare Advantage 'Services Requiring Precertification' policy, the second 27447 match recorded at entry 17 of the T018 URL log.",
  "No evidence in either direction on whether Independence's Commercial policy set governs its ACA Marketplace members, which is the whole of bm_0083.",
  "Fourteen gated rows across six payers have no firsthand evidence of any kind: Regence BCBS, CareFirst BCBS, Highmark, Horizon BCBS NJ, Wellmark BCBS, BCBS Michigan.",
  "The four non-contiguous UPMC MP.PA.133 attestation spans reported by T018 are NOT ruled on here, because they were not in the T019 inputs and they do not gate this package. They need a Judge ruling on whether the matcher treats a table-transcribed or ellipsis-elided quote as an element-wise match, and whether such a rule could still detect a real page change. Queue it before T005.",
  "pdf_text swallowing every exception and returning an empty string is unfixed. It makes a broken extraction indistinguishable from a document with no text, and it points in the flattering direction. Scope it into the probe package or the one after."
]
```

## required_board_updates

```json
[
  "Set T019 status done and attach this receipt.",
  "Open T020 as the write Worker package specified in worker_package above. Single write worker, max_write_workers 1 respected.",
  "Open T021 as the six-payer probe, GO under the written standard in ruling_4. It must not start before T020 lands, so the six payers are judged against a settled rubric v1.5. Its allowed_files are notes/gated-reprobe-t021.md only, plus the answer key for verification_method appends, and it changes NO row_class.",
  "Open T022 as a Judge review of the T021 probe result before T005 is unblocked.",
  "Add the standing control from pm_audit to the board rules: an unreached document is recorded as UNREACHED BY METHOD X with the method stated verbatim, never as unreachable, and plain-HTTP link extraction must be tried before recording 'renders client-side' or any equivalent.",
  "Correct the board text everywhere it says 'replace known_limitations item 8'. It is item 9, matched by its opening text 'OPEN AND UNRESOLVED. On bm_0061 the Horizon attestation page'. This appears in the T017 receipt ruling_caveat_text and in the T018 card constraints.",
  "Record in checks.rubric that the version is v1.5 with amendment_v1_5 text, and update checks.rubric.pending.",
  "Queue the UPMC matcher ruling and the pdf_text silent-failure fix before T005."
]
```

---

## PM verification of the Judge, run after the ruling

The PM verifies a Judge for the same reason a Judge verifies the PM. Every
load-bearing claim below was re-fetched independently, through the hardened
harness fetcher, on 2026-07-26.

### The Carelon chain, walked by plain HTTP with no JavaScript

| Hop | HTTP | Bytes | Blocked | Login wall | CPT 27447 | sha256 first 16 |
|---|---|---|---|---|---|---|
| `/current-musculoskeletal-guidelines/` | 200 | 250,379 | no | no | no | 732effb12196a7f5 |
| `/joint-surgery-2025-11-15/` | 200 | 527,828 | no | no | yes | c564faa4fd0485bd |
| `/wp-content/uploads/2025/11/PDF-Joint-Surgery-2025-11-15.pdf` | 200 | 974,145 | no | no | yes | b33ae12d3a59b1b4 |

Every byte count and the PDF digest match the Judge exactly. So the chain is real
and it needs no JavaScript.

### The criteria in the counted document

Extracted text is 241,279 characters. Term counts match the Judge: BMI 62,
conservative 128, physical therapy 52, tobacco 14. CPT 27447 appears once, with
the full descriptor "Arthroplasty, knee, condyle and plateau; medial AND lateral
compartments with or without patella resurfacing (total knee arthroplasty)".

Three quantified requirements, verbatim:

- "Body mass index (BMI) - It is strongly recommended that a patient with a BMI
  equal to or greater than 40 attempt weight reduction prior to surgery."
- "Diabetes - It is strongly recommended that a patient with a history of diabetes
  maintain a hemoglobin A1C of 8% or less prior to any joint replacement surgery."
- "Tobacco cessation - Adherence to a tobacco cessation program resulting in
  abstinence from tobacco and nicotine products for at least 6 weeks prior to
  surgery is strongly recommended."

So condition V2 is satisfied on evidence, not on assertion. This document carries
real criteria; the Independence bulletin does not.

Correction of the PM's own first check, recorded because this board records them.
The PM initially searched for the literal string `HbA1c` and found zero hits, which
would have made the Judge look like it overclaimed. The document writes it as
`hemoglobin A1C`, with a space and different capitalisation. The PM's raw search
was wrong and the Judge was right. This is the fourth time on this board that a raw
string test has produced a false absence, after bm_0057, bm_0061 and the brotli
regression. It is the strongest possible argument for the Judge's rule that
`normalized_contains` is used everywhere.

### The displacement clause for bm_0062

Verbatim from the same PDF, confirming the Judge's quote character for character:

"Applicable federal and state coverage mandates take precedence over these clinical
guidelines, and in the case of reviews for Medicare Advantage Plans, the Guidelines
are only applied where there are not fully established CMS criteria."

### The PM accepts both findings against itself

Finding 1 is correct and the PM withdraws the sentence it wrote. The PM recorded
that the Carelon knee guideline "was not isolated, because the index renders
client-side and the PM did not execute JavaScript." The first half is a fact about
what the PM did. The second half is a mechanism the PM did not test, and it is
false: three plain HTTP hops reach the document. The PM did exactly what Judge T017
caught it doing before, which is to attach a tidy cause to an absence. Twice is a
pattern, so the standing control the Judge ordered is accepted and goes into the
board rules rather than into a note that can be forgotten.

Finding 2 is accepted with one qualification the PM records rather than argues. The
PM framed the case as a third pattern with no vocabulary, and the Judge is right
that this postponed a promotion. The qualification is that the Judge's own ruling
requires a part two that the existing vocabulary does not describe, so new
vocabulary was in fact needed. The error was not inventing `deferral_vendor_two_part`.
The error was stopping before walking the chain that would have shown what part two
had to be.

Nothing in `answer_key_v1.json` changed. No row class changed.
