# T018: harness hardening, attestation revalidation, and a halted gated re-probe

Author: Worker T018, 2026-07-26. Firsthand HTTP fetches only, browser-shaped
requests, no login, no credential, no payer telephone call.

**STATUS: HALTED ON A STOP CONDITION. A Judge must rule before this work
continues.** The gated re-probe reached the first of seven payers and found a
publicly reachable policy page that lists CPT 27447, on a payer whose rows are
classed `gated`. The task card names that outcome as a stop condition, so the
probe stopped there. Nothing in `answer_key_v1.json` was changed. No row_class
was changed. No quote was edited.

---

## 1. The finding that stopped the probe

Independence Blue Cross serves a Commercial medical policy bulletin, and a
Medicare Advantage medical policy bulletin, that list CPT 27447 under the
heading `Knee Replacement`. Both are answered at HTTP 200 to an ordinary
browser-shaped request. Neither asks for a credential. Neither redirects to a
sign-in path. Neither carries a sign-in form, the word `login`, the word
`password`, the word `register`, or the word `portal` anywhere in its text.

Commercial, verbatim URL:

    https://medpolicy.ibx.com/ibc/Commercial/Pages/Policy/17d2df53-e600-440f-8ddd-0ad805614b91.aspx

Medicare Advantage, verbatim URL:

    https://medpolicy.ibx.com/ibc/ma/Pages/Policy/ea4c1763-0b64-4d01-b0ca-65c58f0f6ecc.aspx

Evidence, three fetches each through the shipped `policy_eval.webtools.fetch`:

| URL | Fetch | HTTP | Bytes | Tag-stripped chars | CPT 27447 | login_wall | blocked | Redirects |
|---|---|---|---|---|---|---|---|---|
| Commercial 17d2df53 | 1 | 200 | 112,321 | 3,400 | yes | False | False | none |
| Commercial 17d2df53 | 2 | 200 | 112,320 | 3,400 | yes | False | False | none |
| Commercial 17d2df53 | 3 | 200 | 112,321 | 3,400 | yes | False | False | none |
| Medicare Advantage ea4c1763 | 1 | 200 | 111,962 | 3,349 | yes | False | False | none |
| Medicare Advantage ea4c1763 | 2 | 200 | 111,963 | 3,349 | yes | False | False | none |
| Medicare Advantage ea4c1763 | 3 | 200 | 111,962 | 3,349 | yes | False | False | none |

The raw sha256 differs on every fetch on both pages, the same non-semantic
instability already recorded on other payer pages. The tag-stripped text is
byte-identical in length across fetches and the code list is unchanged.

Verbatim identity of the Commercial page:

    Title: Musculoskeletal Services (Independence)
    Musculoskeletal Services: Joint Surgery Procedure Codes That Require
    Preservice Utilization Management and Level of Care Review Through Carelon
    Medical Benefits Management Review
    Effective Date: 6/14/2026   Version Issued Date: 6/15/2026
    Medical Policy Bulletin   Commercial

Verbatim text carrying the code, identical on both pages:

    Codes followed by an asterisk (*) denotes services that require additional
    Level of Care Review by Carelon Medical Benefits Management(R)
    ...
    Knee Replacement 27446 * 27447 * 27486 27487 27488 27437 * 27438 * 27440 *
    27441 * 27442 * 27443 * J7330 S2112

The Medicare Advantage page is the same bulletin under the title
`Musculoskeletal Services`, marked `Medical Policy Bulletin   Medicare Advantage`,
with the same effective date and the same code list.

### Which rows this touches

| Row | Payer | Plan type | Current class | Evidence found |
|---|---|---|---|---|
| bm_0072 | Independence Blue Cross | Commercial | gated | Commercial bulletin above, public, CPT 27447 present |
| bm_0062 | Independence Blue Cross | Medicare Advantage | gated | Medicare Advantage bulletin above, public, CPT 27447 present |
| bm_0083 | Independence Blue Cross | ACA Marketplace | gated | NONE either way, see below |

For bm_0083 there is no evidence in either direction. The portal publishes three
policy sets, Commercial, Medicare Advantage and MA PPO Host. It publishes no ACA
Marketplace set, and nothing on the site says whether the Commercial set governs
Marketplace members. That is an absence, and it is recorded as an absence.

The existing note on bm_0062 reads "no public Medicare Advantage knee policy was
reachable" and on bm_0072 "No portal URL in spec; nothing public found". Both
statements are contradicted by the fetches above.

### What is NOT claimed

This note does not claim these bulletins are the controlling prior-authorisation
document for a total knee replacement. They are procedure-code attachments to the
`Musculoskeletal Services` policy, and they state that the code requires
preservice utilization management and level of care review through a delegated
vendor, Carelon Medical Benefits Management. Whether that satisfies the rubric
for a retrievable controlling document is a ruling, not a Worker's call. This
note claims only what was observed: a public page, HTTP 200, no credential
demanded, CPT 27447 present, reproduced three times.

### PM verification, added after the Worker returned

The PM re-fetched both bulletins independently, browser-shaped, and reproduces the
Worker's result exactly. Commercial: HTTP 200, 112,321 bytes, 3,400 characters of
tag-stripped text, CPT 27447 present. Medicare Advantage: HTTP 200, 111,963 bytes,
3,349 characters, CPT 27447 present. Neither page contains sign in, log in, login,
password, register, portal or credential. The finding stands.

Two corrections of emphasis, recorded rather than quietly fixed.

First, the Worker's returned summary said Independence "serves two knee-replacement
policy bulletins". That is stronger than what it wrote in this note, and the note is
the correct version. The pages are Attachment B to policy MA00.047t, titled
"Procedure Codes for Joints", under "Musculoskeletal Services". They are code lists.
They carry no medical-necessity criteria for a knee replacement: no BMI threshold,
no conservative-therapy duration, no imaging requirement. The visible text is a table
of CPT codes grouped by body part.

Second, and this is new information the Worker did not have, the deferral target is
publicly reachable. The bulletins state that codes marked with an asterisk require
"Level of Care Review by Carelon Medical Benefits Management", and 27447 carries the
asterisk. The PM followed the link printed on the page,
`https://aimspecialtyhealth.com/resources/clinical-guidelines/musculoskeletal/`,
which returns HTTP 200 and redirects to
`https://guidelines.carelonmedicalbenefitsmanagement.com/`. That host is public and
serves at HTTP 200 with no credential. The specific musculoskeletal knee guideline
document was not isolated. **CORRECTED by Judge T019.** The PM originally continued
"because the index renders client-side and the PM did not execute JavaScript". The
first half of that sentence is a fact about what the PM did. The second half is a
mechanism the PM never tested, and it is FALSE. Judge T019 reached the criteria
document in three plain HTTP hops with no JavaScript, by extracting href values from
the raw HTML, and the PM has since reproduced all three hops through the hardened
harness fetcher: `/current-musculoskeletal-guidelines/` at 200 and 250,379 bytes,
then `/joint-surgery-2025-11-15/` at 200 and 527,828 bytes, then
`/wp-content/uploads/2025/11/PDF-Joint-Surgery-2025-11-15.pdf` at 200 and 974,145
bytes, sha256 beginning b33ae12d3a59b1b4, containing CPT 27447 and quantified
criteria. The honest record is UNREACHED BY METHOD, not unreachable: the PM tried a
crude tag-strip of the index page and stopped there.

The direction of that error matters and is recorded rather than quietly fixed.
Leaving part two unisolated is what turned a completable evidence chain into an
apparently novel and unresolvable pattern, and that framing kept all three
Independence rows in the gated class where abstention earns full credit. This is the
second time on this board that the PM has attached an untested mechanism to an
absence, after Judge T017 caught the first. Twice is a pattern, so a standing control
now sits in the board rules rather than in a note that can be forgotten.

So the shape of this row is a third attestation pattern, and it is not the one the
key has language for. The key currently knows `deferral_two_part`, meaning the payer
states in writing that this plan follows CMS national and local coverage
determinations, and the CMS document supplies the criteria and the CPT code. What
Independence does here is defer to a COMMERCIAL VENDOR guideline instead, and it
does so on both the Commercial and the Medicare Advantage line of business.

Three consequences a Judge must weigh, none of which a Worker may decide.

1. Is a public payer page that names the code, states that prior authorisation is
   required, and names the governing guideline owner, enough to make the row
   retrievable? It is the same logical shape as `deferral_two_part`. The difference
   is that part two is a vendor document, not a CMS document.
2. On the Medicare Advantage row specifically, bm_0062, deferring knee arthroplasty
   review to a vendor guideline is in tension with the Medicare rule that an MA
   organisation follows CMS coverage determinations first. That tension is itself a
   finding worth carrying into the product, not just the benchmark.
3. Carelon and its predecessor AIM Specialty Health are used by many Blue Cross
   licensees for musculoskeletal review. If this pattern is accepted, it plausibly
   reaches beyond Independence into the six payers not yet probed. The re-probe must
   therefore not be resumed until the pattern is ruled on, or the remaining six
   payers will be judged against a standard that is still moving.

The PM changed nothing in `answer_key_v1.json` and changed no row class.

### How the page was reached, including the dead ends

Every URL tried, in order. Copy them verbatim; a truncated URL produces a 404
that means nothing.

| # | URL | HTTP | Bytes | Result |
|---|---|---|---|---|
| 1 | https://www.ibx.com/resources/for-providers/policies-and-guidelines/operations-management/medical-policy | 200 | 34,825 | Public provider page. Redirects to the `.html` form. No login wall. No CPT 27447. |
| 2 | https://www.ibx.com/resources/for-providers/policies-and-guidelines/operations-management/medical-policy.html | 200 | 34,824 | Carries a click-through disclaimer ending "Accept and go to Medical Policy Online | Decline". A terms gate, not a credential gate. |
| 3 | https://medpolicy.ibx.com/ | 200 | 77,791 | Redirects to `/ibc/pages/home.aspx`. 972 characters of text. Says "It looks like your browser does not have JavaScript enabled". Names the Commercial, Medicare Advantage and MA PPO Host policy sets. No credential demanded. |
| 4 | https://medpolicy.ibx.com/ibc/Commercial/Pages/default.aspx | 404 | 1,092 | Dead end, guessed path. |
| 5 | https://medpolicy.ibx.com/ibc/Commercial/Pages/Home.aspx | 404 | 1,089 | Dead end, guessed path. |
| 6 | https://medpolicy.ibx.com/ibc/Pages/Commercial.aspx | 404 | 1,080 | Dead end, guessed path. |
| 7 | https://medpolicy.ibx.com/ibc/Commercial/Pages/Policy-Bulletin-View.aspx | 200 | 272,053 | The Commercial policy index. Only 1,082 characters of visible text, but the list is embedded in the page as a JSON payload with 100 alphabetical entries. No knee arthroplasty title among them. |
| 8 | https://medpolicy.ibx.com/ibc/Commercial/Pages/Policy-Bulletin-View.aspx?Paged=TRUE&PageFirstRow=101..1501&View=97ae05d1-47e4-47d2-8622-ba2551a28ebb | 200 | ~272,000 | Sixteen paged requests. Every one returned the SAME first 100 entries. Paging is done by JavaScript, so a plain HTTP client cannot enumerate the full list this way. |
| 9 | https://medpolicy.ibx.com/ibc/Commercial/Pages/Policy/8976551b-e116-46a1-9813-0c82b43e743d.aspx | 404 | 1,132 | A deep link offered by a web search. Stale index entry, gone. |
| 10 | https://medpolicy.ibx.com/ibc/ma/pages/result.aspx | 200 | 98,783 | Medicare Advantage results shell. No knee content without JavaScript. |
| 11 | https://medpolicy.ibx.com/ibc/Commercial/Pages/Advance.aspx | 200 | 170,113 | Advanced search shell. No knee content without JavaScript. |
| 12 | https://medpolicy.ibx.com/_api/search/query?querytext='knee%20arthroplasty'&rowlimit=10 | 500 | 250 | Site-root search endpoint refuses the query. Dead end. |
| 13 | https://medpolicy.ibx.com/ibc/Commercial/_api/search/query?querytext='arthroplasty'&rowlimit=20 | 200 | 80,338 | The site's OWN public search endpoint answers without a credential. 28 matching policies. |
| 14 | https://medpolicy.ibx.com/ibc/ma/_api/search/query?querytext='arthroplasty'&rowlimit=20 | 200 | 67,904 | 17 matching policies. |
| 15 | https://medpolicy.ibx.com/ibc/MAPPO/_api/search/query?querytext='arthroplasty'&rowlimit=20 | 200 | 2,828 | 0 matching policies. |
| 16 | https://medpolicy.ibx.com/ibc/Commercial/_api/search/query?querytext='27447'&rowlimit=20 | 200 | - | 2 matches: `Procedure Codes for Joint Surgery` and `Services Requiring Precertification`. |
| 17 | https://medpolicy.ibx.com/ibc/ma/_api/search/query?querytext='27447'&rowlimit=20 | 200 | - | 2 matches: `Procedure Codes for Joints` and `Services Requiring Precertification`. |
| 18 | https://medpolicy.ibx.com/ibc/Commercial/Pages/Policy/42854bbe-41cd-43a0-a83a-53f34c973709.aspx | 200 | 179,873 | Parent Commercial policy `Musculoskeletal Services (Independence)`. 24,098 characters. Names knee and arthroplasty. Does NOT itself carry CPT 27447. |
| 19 | https://medpolicy.ibx.com/ibc/ma/Pages/Policy/7fc902ab-cc95-4dc6-86a4-5623e8567ee7.aspx | 200 | 179,497 | Parent Medicare Advantage policy. Same, no CPT 27447 on the page itself. |
| 20 | https://medpolicy.ibx.com/ibc/Commercial/Pages/Policy/17d2df53-e600-440f-8ddd-0ad805614b91.aspx | 200 | 112,321 | **CPT 27447 present. Public. The finding.** |
| 21 | https://medpolicy.ibx.com/ibc/ma/Pages/Policy/ea4c1763-0b64-4d01-b0ca-65c58f0f6ecc.aspx | 200 | 111,962 | **CPT 27447 present. Public. The finding.** |

One honest qualification about reachability. A person with a browser can reach
these pages by clicking through the portal, because the portal renders its index
in JavaScript. A plain HTTP client cannot walk that index, and this probe found
the two pages through the site's own public search endpoint, entries 13 to 17.
The documents themselves need no JavaScript, no credential and no cookie: the
direct URLs return the full policy text to a plain request, three times out of
three. So the retrieval model, which has search and fetch, could reach them.

## 2. Six payers were NOT probed

The card orders a probe of seven payers. One was probed. The other six were not
started, because the stop condition fired on the first one and the card says to
halt and escalate rather than continue.

Not probed, and their rows still rest on a carried-forward spec label with no
firsthand fetch evidence of any kind: Regence BCBS (bm_0064, bm_0074, bm_0085),
CareFirst BCBS (bm_0069, bm_0080), Highmark (bm_0070, bm_0081, bm_0091), Horizon
BCBS NJ (bm_0071, bm_0082, bm_0092), Wellmark BCBS (bm_0076, bm_0087), BCBS
Michigan (bm_0088). That is 14 of the 17 gated rows with no evidence either way.

The single result already in hand should raise the prior that the remaining six
need the same treatment, because the one payer that was checked did not hold up.

## 3. Harness hardening, which is complete and verified

These changes are independent of the probe and are finished.

### 3.1 A bot block can now be seen

`detect_bot_block(status, headers, body_text, byte_len)` is new in
`scripts/policy_eval/common.py`. It is deliberately SEPARATE from
`detect_login_wall` and their verdicts are never merged. A login wall is a true
property of the payer and belongs in the gated class. A bot block is an artefact
of our own request shape, it may sit in front of a fully public document, and it
must never produce a row class.

Proved against the live stub, same URL, same minute:

| Request shape | HTTP | Bytes | detect_login_wall | detect_bot_block |
|---|---|---|---|---|
| bare curl to the Horizon policy page | 200 | 1,038 | (False, None) | (True, 'imperva_incapsula_resource') |
| same stub as tag-stripped text | 200 | 1,038 | (False, None) | (True, 'request_unsuccessful_stub') |
| shipped fetcher, browser-shaped | 200 | 494,917 | (False, None) | (False, None) |

The stub's entire visible text was
`Request unsuccessful. Incapsula incident ID: 914000070907578519-974163363784425967`.
Note that `detect_login_wall` still returns `(False, None)` on it, which is the
correct answer: that stub is not a login wall.

### 3.2 Escaped markup no longer leaks into model-visible text

`strip_html` now unescapes entities BEFORE stripping tags, and repeats the pair
until the text stops changing, capped at four passes. The case proved live before
the fix: `strip_html('(&lt;abbr&gt;NCD&lt;/abbr&gt;)')` returned
`'(<abbr>NCD</abbr>)'` and now returns `'( NCD )'`.

`normalize_for_match()` and `normalized_contains()` are new. They unescape, strip
tags, normalise Unicode, fold case, fold every punctuation mark to a space and
collapse whitespace. Every identity and attestation check must go through them,
so that the check recorded in the key and the check run by the harness cannot
diverge.

All four existing self-tests still pass unchanged after the ordering fix:
`denominators.py`, `selftest_report_gate.py`, `selftest_discrimination.py` and
`selftest_tool_isolation.py`.

### 3.3 The fetcher now looks like a browser, and says when it was refused

`webtools.fetch` sends `Accept`, `Accept-Language`, `Accept-Encoding`,
`Upgrade-Insecure-Requests`, `Sec-Fetch-Dest`, `Sec-Fetch-Mode`,
`Sec-Fetch-Site`, `Sec-Fetch-User` and `Connection` over a persistent
`requests.Session`, and every returned record now carries `blocked` and
`blocked_reason`.

### 3.4 A near miss this task created and caught, worth recording

The first version of the header set advertised `Accept-Encoding: gzip, deflate, br`.
Brotli is NOT installed in this environment. One payer CDN honoured the offer,
and `requests` returned 13,025 bytes of still-compressed data at HTTP 200. Text
extraction turned it into mojibake. The recorded attestation quote was not found.
CPT 27447 was not found. Nothing reported an error anywhere.

| Request shape | HTTP | Bytes | Content-Encoding | Recorded quote found |
|---|---|---|---|---|
| no headers at all | 200 | 53,308 | none | yes |
| user agent only, the old harness shape | 200 | 53,308 | gzip | yes |
| full browser headers WITH br offered | 200 | 13,025 | br | NO |
| full browser headers WITHOUT br offered | 200 | 53,308 | gzip | yes |

That is the exact failure this task exists to remove, produced by the fix rather
than by a payer: a page the model was never shown, scored as a page the model
failed to read, pushing toward abstention, which is what the headline metric
rewards. The fetcher now advertises only the encodings this interpreter can
actually decode, and it marks a response that arrives in an undecodable encoding
as `blocked` rather than letting unreadable bytes be scored.

### 3.5 A trap for whoever repeats this work

A stray file at `/tmp/inspect.py` shadows the Python standard library `inspect`
module for any script run from `/tmp`. That breaks `dataclasses`, which breaks
`pypdf`. `pdf_text` in `common.py` catches every exception and returns an empty
string, so five PDF-backed rows silently produced zero characters of text and
every recorded quote on them looked absent. Run probe scripts from the repository
root, not from `/tmp`. Separately, `pdf_text` swallowing the reason for an empty
extraction is a real weakness that points in the flattering direction, and it is
left for a Judge to scope rather than changed here.

## 4. Attestation revalidation on all 11 retrievable rows

Every retrievable row's `attestation_quote` was rechecked on a live fetch under
the new normalised matcher. Nothing was edited.

Result: every recorded attestation is live and present today. 11 of 11 rows
carry their attestation. Four spans inside three rows do not match as one
contiguous run of text, and the reason is demonstrated below, not assumed.

| Row | Source fetched | HTTP | Verdict |
|---|---|---|---|
| bm_0056 | bcbsm.com plan page, and CMS L39911 | 200, 200 | PASS. Present. See the brotli note: with `br` offered this row's quote vanished, which is why the header set was corrected. |
| bm_0057 | bcbsnc.com plan page, and CMS L33456 | 200, 200 | PASS. The 325-character quote matches as two sentences, each contiguous. A raw substring test reports it absent; the normalised matcher finds it. |
| bm_0058 | blueshieldca.com utilization management page | 200 | PASS, contiguous. |
| bm_0059 | provider.carefirst.com policy page, and CMS L36007 | 200, 200 | PASS, two sentences each contiguous. |
| bm_0060 | securecms.highmark.com S-39-008 | 200 | PASS, all five spans contiguous. |
| bm_0061 | horizonblue.com plan page, and CMS L36007 | 200, 200 | PASS, contiguous. The 296-character quote is present. This is one more reproduction on top of the recorded 31 of 31. |
| bm_0065 | UPMC MP.PA.133 PDF | 200 | Present, but see the table note below. |
| bm_0073 | Premera 7.01.550 PDF, and the Premera WA policy index | 200, 200 | PASS. The quote spans two documents, separated in the key by `||`. Both parts contiguous on their own source. |
| bm_0075 | UPMC MP.PA.133 PDF | 200 | Present, but see the table note below. |
| bm_0084 | Premera 7.01.550 PDF, and the Premera WA policy index | 200, 200 | PASS, same as bm_0073. |
| bm_0094 | UPMC MP.PA.133 PDF | 200 | Present, but see the table note below. |

### The four non-contiguous spans, and why they are not a page change

All four are in the UPMC policy MP.PA.133, whose applicability statement is a
two-dimensional checkbox grid. Linear PDF text extraction reads that grid across
the columns, so a transcription of one column is never contiguous in the
extracted text. Every element of every failing span is present.

Span 1, in bm_0065, bm_0075 and bm_0094:
`This policy applies to the following lines of business: (Check those that apply.)`
The live extraction reads
`This policy applies to the 1 following lines of business: (Check those that apply.)`.
A footnote numeral sits inside the sentence. Both halves match on their own.

Span 2, in bm_0075:
`COMMERCIAL: HMO ( ) PPO ( ) Fully Insured ( ) Self Funded ( ) Marketplace HMO ( ) Marketplace PPO ( ) Marketplace EPO ( ) Indiv. Off Exchange ( ) All (X)`
Each of the ten elements, including the header `COMMERCIAL` and the checked
`All (X)`, is present. They are interleaved with the other three columns. The
live extraction reads
`COMMERCIAL CMS-MA DHS-MA ANCILLARY HMO ( ) PA (X) Health Choices/PH (X) Dental ( ) PPO ( ) Ohio ( ) ...`.

This is the PDF form of the trap already recorded on bm_0057: an exact substring
miss on a page that never changed. It is reported rather than fixed, because the
fix is a matcher design decision. A Judge should rule on whether the harness
attestation check treats an ellipsis-elided or table-transcribed quote as an
element-wise match, and if so, whether that rule is tight enough that it could
still detect a real change. It is recorded here so nobody later reports these
four spans as an integrity failure.

## 5. What a Judge must decide

1. bm_0072 and bm_0062. Independence Blue Cross publishes a policy page carrying
   CPT 27447 with no credential demanded. Does either row stay `gated`. If either
   moves, `gated`, the 23-row honest-abstention denominator, and every count that
   depends on them move with it, and the rubric's pinned table must be reissued.
2. bm_0083. There is no evidence in either direction for the ACA Marketplace row.
   Decide what an evidence-free row is allowed to be.
3. The remaining six payers. Fourteen gated rows still have no firsthand
   evidence. Decide whether the probe resumes now, and whether a run may start
   before it finishes.
4. The four UPMC spans. Decide the matcher rule for elided and tabular quotes.
5. `pdf_text` returning an empty string on any failure, with no error recorded.
6. The `verification_method` string on all 17 gated rows still reads "Firsthand
   HTTP fetch on 2026-07-26 with a browser user agent". It was NOT corrected in
   this task. Correcting it was ordered, but the honest replacement text names
   what the payer-level probe found, and the probe stopped after one payer of
   seven. Writing that sentence on 16 rows now would assert a conclusion this
   task did not reach. It is left untouched and flagged rather than half written.
7. The rubric v1.5 amendment for a blocked fetch, and the `known_limitations`
   rewrite, were both ordered and are both NOT done, for the same reason: they
   sit in the answer key and the rubric, and this task halted before touching
   either. The harness now records `blocked` on every fetch, so the amendment can
   be applied cleanly by the next task.
