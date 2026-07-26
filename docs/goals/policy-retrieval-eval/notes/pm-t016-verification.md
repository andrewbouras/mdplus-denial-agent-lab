# PM verification of Worker T016, and two defects the sweep exposed

Author: PM thread, 2026-07-26. Firsthand fetches only, browser user agent, no login,
no credential, no payer telephone call.

Purpose: T016 escalated a finding that would have removed a row from the retrievable
class. Before accepting it I reproduced the fetch myself. The escalation does not hold,
and the reason it does not hold is a defect in how we fetch, which matters far more than
the row did.

Status: OPEN. This note is PM evidence, not a ruling. Judge T017 must rule on all three
findings below. The PM has changed nothing in the answer key.

---

## Why the PM re-checked at all

T016 reported that the Horizon attestation page served the recorded quote on two fetches
and then stopped serving it on the next nineteen. It correctly refused to change the row
class, and correctly escalated. It also wrote a caveat into `known_limitations` beginning
"OPEN AND UNRESOLVED" and stating that "no substring of the quote is presently
retrievable on demand".

Two things made the PM check rather than accept. First, the finding, if true, removes
bm_0061 from the retrievable class and moves the headline denominators. Second, the
finding is an absence, and an absence is the one kind of evidence our own fetch method
can manufacture.

## Finding 1: the Horizon escalation does not hold. The quote is reliably retrievable

Six fetches, spaced, with a browser user agent, standard `Accept` and `Sec-Fetch-*`
headers and transparent compression:

| Fetch | HTTP | Content sha256 (first 16) | Recorded 296-character quote present |
|---|---|---|---|
| A | 200 | 39f425cf34e622ea | yes |
| 1 | 200 | 39f425cf34e622ea | yes |
| 2 | 200 | 39f425cf34e622ea | yes |
| 3 | 200 | 39f425cf34e622ea | yes |
| 4 | 200 | 39f425cf34e622ea | yes |
| 5 | 200 | 39f425cf34e622ea | yes |

The full digest is
`39f425cf34e622ea7f0335a87dd4736c94107655ff7e808b5ab302fd1c749322`. It reproduced on 6
of 6 fetches. The recorded quote matched verbatim, all 296 characters, in tag-stripped
text. So this page is not per-request unstable, and its part-one attestation is not
missing.

The PM did not retain T016's bytes either, so the PM cannot prove what T016 received.
The PM can prove what the page returns now, repeatedly, and can prove a mechanism that
produces exactly the absence T016 saw. That mechanism is finding 2.

## Finding 2, MATERIAL: this payer blocks non-browser fetches with HTTP 200

The Horizon host sits behind Imperva bot mitigation. A request that does not look like a
browser is not refused with an error status. It is answered with HTTP 200 and a 931-byte
stub. The entire visible text of that stub is:

    Request unsuccessful. Incapsula incident ID: 914000070904437332-329831614124261862

Same URL, same minute, three request shapes:

| Request shape | HTTP | Bytes | Real policy content |
|---|---|---|---|
| default curl user agent | 200 | 931 | no, Imperva stub |
| browser user agent, no compression negotiated | 200 | 925 | no, Imperva stub |
| browser user agent, full browser headers, compression | 200 | about 53,600 | yes |

This is the defect, stated plainly: our harness cannot currently tell a blocked fetch
from a successful one. `detect_login_wall` in `scripts/policy_eval/common.py` tests for
status 401 or 403, for a login path in the redirect chain, and for a sign-in form in the
body. An Imperva stub passes all three tests. Run against the stub above it returns
`(False, None)`.

Why this is worse than a data-quality problem. The benchmark's headline number is
confident-but-wrong. If the retrieval model fetches a payer page and receives an
81-character block notice at HTTP 200, it will find no policy and will either abstain or
guess. Both outcomes get attributed to the model. Neither is the model's doing. A
benchmark that silently scores our own network conditions as model behaviour is not
measuring what it claims to measure, and the direction of the error is not neutral: more
blocking produces more abstention, and abstention is the behaviour our headline metric
rewards. We would be flattering ourselves with our own rate limiter.

Second-order consequence that a Judge must scope. Rows classed `gated` were classed that
way from firsthand fetches. If any of those fetches were bot-blocked rather than genuinely
login-walled, the class is wrong. `gated` is 17 of 34 scored rows, so this is not a minor
edge.

Scope check across every recorded payer host, bare fetch against browser fetch, run by
the PM:

| Host | Bare fetch | Browser fetch | Blocked at 200 |
|---|---|---|---|
| www.horizonblue.com | 200, 931 bytes, Imperva stub | 200, about 53,600 bytes, real | YES |
| provider.carefirst.com | 200, 69,730 | 200, 70,704 | no |
| securecms.highmark.com | 200, 139,294 | 200, 139,294 | no |
| www.bcbsm.com | 200, 53,308 | 200, 13,026 | no |
| www.bcbsnc.com | 406 | 200, 13,972 | no, but see finding 3 |
| www.blueshieldca.com | 200, 179,001 | 200, 28,624 | no |
| www.premera.com (PDF) | 200, 912,610 | 200, 912,610 | no |

One host of seven, on the evidence so far. That is enough to prove the mechanism is real
and that the detector is blind to it. It is not enough to bound the exposure, because the
gated rows were never re-probed this way.

## Finding 3: verbatim identity strings are brittle, and T016 just made us depend on them

T016 replaced unreproducible hashes with `identity_string`, a verbatim substring the page
must contain. That mechanism is now the identity check on 5 of the 11 retrievable rows.
It is more brittle than it looks.

Worked example, bm_0057, BCBS North Carolina. The PM's first exact substring test for the
recorded 325-character quote returned NOT PRESENT, at HTTP 200 on the real page. The
quote is in fact present and unchanged. The test failed because the live page wraps three
abbreviations in markup, `National Coverage Determinations (<abbr>NCD</abbr>)` where the
recorded quote has `(NCD)`, and because the page delivers that region as escaped markup
inside a JSON payload rather than as plain HTML. After normalising case, punctuation and
whitespace, the recorded quote is present.

So a naive identity check would have reported an integrity failure on a page that never
changed. Had the PM trusted its own first result the way it nearly trusted T016's, this
note would be escalating a second phantom.

The fix is a normalising comparison, not a raw substring test: strip tags, unescape
entities, collapse whitespace, fold case and punctuation, then compare. Any identity
check the key relies on must be executed by shared code that does this, so that the check
recorded in the key and the check run by the harness cannot diverge.

## What the PM did not do

The PM changed nothing in `answer_key_v1.json`. bm_0061 keeps `retrievable` for now
because a PM must not quietly restore a class that a Worker escalated, least of all in
the direction that keeps the denominators larger. The `known_limitations` item that says
the quote is not retrievable is, on the evidence above, false, and rubric section 9 makes
the report print that block byte for byte. It must be corrected rather than deleted, and
a Judge should decide the wording.

## What a Judge must rule on

1. bm_0061. Does the row keep `retrievable` and `deferral_two_part`, given 6 of 6
   reproductions of the quote and a proven mechanism for the earlier absence.
2. The caveat text. The current item 8 asserts an absence the PM has disproved. Replace
   it with the bot-block finding, which is a real and larger limitation, without deleting
   the record that the alarm was raised.
3. Scope of the bot-block defect. Whether the 17 gated rows must be re-probed with
   browser-shaped requests before T005, and whether `detect_login_wall` must gain a
   bot-block detector and the fetcher must send browser headers, before any cold run.
4. Whether identity checks must be normalised, and whether the 5 rows T016 just moved
   onto `identity_string` need their strings re-validated under a normalising matcher.

## Technical detail

Reproduction, Imperva stub against real page, same URL:

    URL=https://www.horizonblue.com/providers/products-programs/utilization-management-programs/surgical-and-implantable-device-management-program/medical-policy-criteria-and-guidelines

    curl -sS -L "$URL"                      # 200, 931 bytes, Incapsula stub
    curl -sS -L --compressed \
      -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 \
          (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" \
      -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
      -H "Accept-Language: en-US,en;q=0.9" \
      -H "Sec-Fetch-Dest: document" -H "Sec-Fetch-Mode: navigate" \
      -H "Sec-Fetch-Site: none" "$URL"      # 200, about 53,600 bytes, real page

Detector blindness, verbatim:

    from policy_eval.common import detect_login_wall, extract_text
    txt = extract_text(open('stub.html','rb').read(), 'text/html')
    # txt == 'Request unsuccessful. Incapsula incident ID: 914000070904437332-329831614124261862'
    detect_login_wall(200, url, [], txt)     # -> (False, None)

Stable content digest for the Horizon plan page, 6 of 6 fetches on 2026-07-26:
`39f425cf34e622ea7f0335a87dd4736c94107655ff7e808b5ab302fd1c749322`. This is a PM
observation and is not written into the key.

Recorded plan-page digest in the key for bm_0061 is
`611a162f5520deace245ece1a639c148a54437f3508fd986584185cba59b1c7c`, which did not
reproduce for T016 and did not reproduce for the PM. `content_hash_stable: false` on that
row is therefore correct and should stand regardless of how findings 1 to 3 are ruled.
