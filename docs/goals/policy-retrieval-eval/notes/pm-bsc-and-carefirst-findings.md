# PM findings: Blue Shield of California scope, and the CareFirst state pin

Author: PM thread, 2026-07-26. Firsthand fetches only, browser user agent, no login,
no credential, no payer telephone call.

Purpose: resolve two of the three human-dependency blockers T003 left open, without
consuming Andrew's time. Andrew delegated both decisions explicitly.

Status: findings recorded here only. NOT yet applied to `answer_key_v1.json`, because
the T012 Judge is reading that file and the board allows one writer at a time.

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
- HTTP 200, no login, sha256 `d329984708e4c08ee6fca9216df93f60d5c2116dbc3ce1a1b331729bae409df3`
- Verbatim: "The resources are not listed in use order for utilization management and
  medically necessary decisions. The specific hierarchy for each line of business is
  determined by regulatory government bodies. For example, Medicare requires use of the
  Medicare Managed Care Manual and NCD/LCD's first."

That is a payer-attested Medicare deferral for the Medicare Advantage line of business,
which is exactly the `deferral_two_part` basis T003 defined and used on four other rows.

Independent corroboration from inside BSC7.10 itself, under its own section heading
"Medicare National Coverage", quoted verbatim: "Medicare does not have a National Coverage
Determination, but does have a Local Coverage Determination (LCD) for Total Knee
Arthroplasty (L36575) effective December 1, 2019."

So bm_0058 is attested by three independent artifacts that agree:

| Part | Source | What it attests |
|---|---|---|
| payer + plan type | BSC utilization management page | Medicare Advantage defers to the Medicare Managed Care Manual and NCD/LCD first |
| governing document | BSC7.10 "Medicare National Coverage" section | No NCD exists; L36575 governs total knee arthroplasty |
| state + jurisdiction | CMS L36575 Contractor Information table | Noridian J-E, "California - Entire State" |

**Proposed change: bm_0058 moves from `unverified` to `retrievable`, basis
`deferral_two_part`.** Subject to the T012 Judge, since it changes a denominator.

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

## 3. Net effect on the class counts, if T012 approves

| Class | T003 | After bm_0058 |
|---|---|---|
| retrievable | 10 | 11 |
| gated | 17 | 17 |
| none | 6 | 6 |
| unverified | 5 | 4 |
| invalid | 1 | 1 |

The independence caveat does not improve much. The retrievable rows would rest on 7 unique
documents rather than 6, since bm_0058 introduces L36575 with the Blue Shield utilization
management page as its deferral attestation. Report both numbers together, per rubric
section 0.1.
