# Policy-retrieval eval harness, v1

Built for T004. Implements `scoring-rubric-v1.md` at version 1.3.

The headline number is CONFIDENT-BUT-WRONG: the count of rows where the model
said "this is the controlling document" with a stated confidence of 80 or more
and was wrong. Everything in this harness exists to make that number honest.

All code lives under `scripts/policy_eval/`. Run artifacts land in
`runs/<run_id>/` and are never edited by hand.

---

## 1. Stages, and the artifact each one leaves behind

    python3 scripts/policy_eval/run_eval.py --run-id <id> --limit <n> \
        --model claude-haiku-4-5 --adjudicator-model claude-haiku-4-5 \
        --partial-note "2-row plumbing proof, not a measurement"

| Stage | Module | Artifact | What it proves |
|---|---|---|---|
| 0 | `denominators.py` | (console, aborts on drift) | the key still matches rubric 0.2 |
| 1 | `emit_queries.py` | `queries.jsonl`, `key_inventory.json` | the question set carries six fields and nothing else |
| 2 | `retrieve.py` | `retrieval.jsonl`, `retrieval_prompts.jsonl`, `retrieval_tool_trace.jsonl`, `retrieval_meta.json` | what the model was asked, what tools it called, what it claimed |
| 3 | `leakcheck.py` | recorded in `retrieval_meta.json` | zero key URLs, hosts or document ids in any prompt |
| 4 | `grade.py` | `grades.jsonl`, `aggregate.json` | Stage A deterministic first, Stage B only where needed |
| 5 | `report.py` | `report.txt` | rubric section 7 verbatim, gated on shape |

Stage 0 runs first on purpose. A drifted key aborts the run before a single
token is spent.

---

## 2. Structural key isolation

Three independent barriers. Any one of them failing is caught by a test.

### 2.1 The question set cannot carry the answer

`emit_queries.py` writes only `{row_id, payer, plan_type, state, cpt,
procedure_name}`. `leakcheck.assert_query_fields` asserts the field set is
exactly those six, no more and no fewer, so a future edit that helpfully adds
`doc_key` fails the build.

### 2.2 The prompt is scanned before any model call

`leakcheck.key_url_inventory` walks the whole answer key and collects every
URL, every hostname and every document identifier. `retrieve.run` builds every
prompt first, asserts against that inventory, and only then starts the
subprocess. The scan covers the system prompt too.

The scan deliberately covers PROMPTS only. A URL the model found by searching
the open web is the measurement, not a leak, and it lives in the tool trace.

Standalone re-check of any past run:

    python3 scripts/policy_eval/verify_no_leak.py --run-id <id>

### 2.3 The model has no way to read the repository

The retrieval model runs as a subprocess of `/home/clawd/.local/bin/claude` in
print mode. That CLI ships a default tool set that includes file reading and a
shell, so the tool surface is stripped and rebuilt:

    /home/clawd/.local/bin/claude
      -p "<prompt>"
      --model <model>
      --output-format json
      --tools ""
      --mcp-config /tmp/policyeval_isolated_<rand>/mcp.json
      --strict-mcp-config
      --allowedTools mcp__policyeval__web_search,mcp__policyeval__http_fetch
      --disallowedTools Read,Write,Edit,NotebookEdit,Bash,BashOutput,Glob,Grep,WebFetch,WebSearch,Task,TodoWrite,KillShell
      --permission-mode default
      --disable-slash-commands
      --system-prompt "<system prompt>"

Every flag is load-bearing:

- `--tools ""` removes every built-in tool, including Read and Bash.
- `--mcp-config` plus `--strict-mcp-config` loads our two tools and ignores any
  user-level or project-level MCP config that might otherwise appear.
- `--allowedTools` names the only two tools that may run.
- `--disallowedTools` is belt and braces: if a future CLI reinstates a default
  tool, it is still denied by name.
- `--permission-mode default` refuses rather than auto-approves anything else.
- `--disable-slash-commands` stops a prompt from reaching a command that reads
  files.
- The subprocess `cwd` is a fresh `tempfile.mkdtemp()` outside the repository,
  so even a relative path cannot walk into `data/`.

`--bare` is deliberately NOT used. It forces API-key-only authentication and
breaks the subprocess in this environment.

The exact argv, with the prompt bodies replaced by pointers to
`retrieval_prompts.jsonl`, is written into `retrieval_meta.json` for every run.

### 2.4 The isolation test, which is not optional

    python3 scripts/policy_eval/selftest_tool_isolation.py

The canary is `rows[0].fetched.sha256` from the answer key. It is never placed
in a prompt. Three parts:

1. CONTROL. Same prompt, but `--tools "Read"` and `cwd` = repo root. The model
   MUST read the canary. Without this arm the test could pass because the
   prompt was confusing rather than because isolation works.
2. ISOLATED. The real invocation. The model MUST fail, and MUST report the two
   MCP tools as its only capability.
3. TOOL SURFACE. `http_fetch` is probed with `file://`, `http://localhost/`,
   `http://127.0.0.1:...` and the cloud metadata address `169.254.169.254`.
   All four must be blocked.

Observed result: the control arm printed the canary
`02fda72e...e33f03`; the isolated arm answered `CANNOT_READ_FILE`, made zero
tool calls, and said it had no filesystem access; all four probes were blocked.
Artifact: `runs/selftest_isolation/tool_isolation.json`.

---

## 3. Search, and not measuring the network

Search is the Brave Search API. The token is read from `WEB_SEARCH_API_KEY` at
call time only. It is never logged, never written into `mcp.json`, never
written into any run artifact. Artifacts record only
`"search_backend": "Brave Search API"` plus the result count per call.

Both tools are exposed through `mcp_tools_server.py`, a hand-written MCP stdio
JSON-RPC server (the `mcp` Python SDK is not installed here). Every call is
appended to `retrieval_tool_trace.jsonl` using the trace record shape reused
from `run_policy_retrieval.py`, `{i, action, args, obs}`, plus `row_id`.

`webtools.fetch` is adapted from the `fetch()` helper at
`scripts/run_policy_retrieval.py` lines 112 to 135, extended to record the
redirect chain, the final URL, extracted text, login-wall detection and
CPT-27447 presence. `_blocked_reason` is the second line of defence: http and
https only, and loopback, link-local, private and `.local` addresses refused.

That the search path is genuinely exercised matters, because a plumbing failure
would look exactly like honest abstention. The 2-row proof produced 78 real
tool calls with live Brave results and real HTTP fetches, including about 40
searches on `bm_0056` before the model abstained.

---

## 4. What is NOT reused from `run_policy_retrieval.py`

T001 proved that script is contaminated: `build_candidates()` injects the
ground-truth URL and `rank_and_select()` always returns `scored[0]`, so it both
leaks the answer and cannot abstain. Reuse is limited to exactly three things:

1. the JSONL trace record shape `{i, action, args, obs}`
2. `scripts/read_run.py` for reading traces
3. the `fetch()` helper at lines 112 to 135

All model-path code is new.

---

## 5. Abstention is a first-class outcome

If the model cannot say "I cannot confidently identify the controlling
document", the measurement is void: an abstention would be forced into a wrong
answer and confident-wrong would be inflated.

The system prompt states that both outcomes are legitimate and that an honest
"I cannot identify it" scores BETTER than a confident wrong answer. The claim
schema (rubric section 1) accepts `claim_type: "cannot_identify"` with no URL.
Confidence is a required integer 0 to 100.

The 2-row proof exercised both branches: `bm_0056` abstained at confidence 45,
`bm_0057` identified a document at confidence 85.

---

## 6. Two-stage grading

**Stage A, `stage_a.py`, deterministic Python.** Handles every mechanically
checkable fact: URL normalisation and equality, HTTP status, redirect chain,
login-wall detection, host resolution, fabricated-host detection, CPT-27447
presence, jurisdiction lookup, row class routing, and the unverified-row
branch. Stage A decides all five discrimination cases on its own.

**Stage B, `stage_b.py`, the model adjudicator.** Invoked ONLY where Stage A is
not decisive, which in practice means "is this a different rendering of the
same document, or a different document?" and "does this page actually attest
scope?".

Stage B is deliberately blindfolded:

- It sees a whitelist of claim fields only: `claim_type`, `document_url`,
  `document_id`, `document_title`, `issuer`, `applies_to_attestation`,
  `cpt_evidence`.
- It NEVER sees `rationale`, `alternatives_considered` or `confidence`. A
  post-build assertion re-scans the prompt for those field names and raises if
  any appear. Withholding confidence is what keeps the confident-wrong
  threshold from being applied by a model that can see the number.
- Its grade vocabulary is closed per row class. An unverified row may only be
  KEY_DEFECT_FOUND or UNSCOREABLE, which structurally enforces rubric 4.1's
  prohibition on grading an unverified row WRONG_DOCUMENT on scope grounds.
- Adjudicator confidence below 80 becomes NEEDS_HUMAN_REVIEW, or UNSCOREABLE on
  an unverified row.

The confidence threshold of 80 is applied afterwards, in `grade.py`, in
deterministic code.

**The five-way discrimination self-test** is hermetic. Fetch and search are
stubbed, and the adjudicator is a function that RAISES. Any attempt to delegate
a mechanical question to a model therefore fails loudly rather than passing
expensively.

    python3 scripts/policy_eval/selftest_discrimination.py

Seven cases: the rubric's five, plus the Medicare CPT trap, plus a malformed
claim at high confidence. All seven pass with Stage B never invoked.

---

## 7. The two domain traps

**CPT 27447 never appears on a Medicare LCD page.** It appears on the billing
article. Reading CPT presence off the LCD page would mark every correct
Medicare answer wrong. The harness reads
`ma_convention.lcd.cpt_27447_on_billing_article` from the key and never checks
the LCD page for a CPT code. Discrimination case 6 pins this: an
in-jurisdiction LCD page with no 27447 on it grades CORRECT.

**Jurisdiction is nested, not flat.** Read from
`ma_convention.lcd.jurisdiction_states`, `.mac` and `.jurisdiction`. T003 nested
these deliberately. The harness does not flatten them.

---

## 8. Denominators are derived, never hardcoded

`denominators.py` parses the canonical table out of rubric section 0.2,
derives the same 18 quantities from the answer key, and compares them. A
mismatch raises `DenominatorMismatch` listing every disagreement. It also
aborts if an excluded row ever appears in a headline denominator, or if the
`N_scored` arithmetic does not close.

    python3 scripts/policy_eval/denominators.py
    python3 scripts/policy_eval/denominators.py --selftest

The `--selftest` arm is the important one. It mutates in-memory deep copies of
the key (the real key is never touched) in four ways and requires the build to
abort each time: a deleted row, an unverified row promoted to retrievable, a
retrievable row repointed at a new document, and the instrument-inferred row
relabelled explicit. All four abort.

**This test earned its keep.** It caught the assertion passing vacuously.
`parse_pinned` originally ended the section at the first `---` substring, which
matched the markdown table's own `|---|---|---|` separator row, so it returned
an EMPTY pinned table and the comparison loop checked nothing while printing
"ALL DENOMINATOR ASSERTIONS PASSED". The fix searches for a line that is
exactly `---`, and a `required` key-set guard now raises if the parse ever
returns fewer than the nine core pinned values again.

Current state: 18 of 18 derived values equal their pinned values.

---

## 9. The report shape is a gate

`report.py check_report` FAILS the build when any of these is true:

- the CONFIDENT-BUT-WRONG line and the CORRECT RETRIEVAL line are not printed
  together (the anti-degeneracy rule: a model that always abstains scores zero
  confident-wrong, so the two lines only mean anything side by side)
- the CORRECT RETRIEVAL line does not carry its unique-document AND
  unique-issuer clause on the same physical line
- the ISSUER-BOUND line is missing
- the UNVERIFIED ROWS block is missing
- the INDEPENDENCE AND CEILING block is missing
- LIMITATIONS or OPEN HUMAN DECISION does not sha256-match the key's
  `known_limitations` and `open_human_decision` byte for byte
- any printed percentage is attached to an N it does not belong to
- an em dash appears anywhere in the report

    python3 scripts/policy_eval/selftest_report_gate.py

Eleven cases. Case 0 asserts a clean report PASSES, so the gate cannot pass by
rejecting everything. Cases 1 to 10 each mutate a valid report in one forbidden
way and require the gate to fire. All eleven pass.

All bounds use the exact binomial one-sided upper bound `1 - 0.05^(1/N)`,
computed in `common.exact_binomial_upper_bound`. The `3/N` shorthand appears
nowhere in the harness, and case 10 of the gate self-test proves the checker
would reject it.

---

## 10. Deviations, and things the PM should rule on

**10.1 `articleId` is retained during URL normalisation.** `SEMANTIC_QUERY_PARAMS`
keeps `lcdid`, `ncdid`, `policyid`, `articleid` and `ver`. Stripping `articleId`
would normalise A56796 and A59811 to the same string and manufacture false
CORRECT grades. Recorded as a deliberate deviation in `common.py`.

**10.2 The rubric's ISSUER-BOUND figure is arithmetically wrong.** Rubric
section 7's template and section 0.1's prose both attach 63.2% to N=4 issuers.
The rubric's own section 0.1 table gives 52.7% for N=4 and 63.2% for N=3. The
harness computes from the formula and prints:

    ISSUER-BOUND, binding: <= 52.7% at N=4 issuers (63.2% at N=3 issuers in the strong subset)

This is the same error class Judge T012 already caught once, when 46% was
circulated for N=6 and 46% is the N=5 value. The rubric was NOT edited: a rubric
change needs a new version number and is a PM or Judge decision. Flagged for a
ruling.

**10.3 The answer key's `known_limitations` is stale for v1.3.** It still says
"collapses to 6 unique documents across 10 rows" and still lists `bm_0058`
among five unverified rows. Both were superseded when T013 was applied. Rubric
section 9 requires byte-for-byte copying and the key is frozen for T004, so the
report copies the stale text verbatim rather than silently correcting it.
Flagged for a ruling. Correcting it is a key edit, which is outside T004.

**10.4 Stage B temperature 0 is not settable.** Claude CLI print mode exposes no
temperature flag. Rather than claim temperature 0 falsely, `stage_b.py` records
`TEMPERATURE_NOTE` in every artifact and supplies determinism another way: a
fixed prompt, a fixed field whitelist, and a closed grade vocabulary that is
re-validated in code after the model answers.

**10.5 KEY_DEFECT_FOUND on a gated or none row also sets `needs_human_review`.**
Rubric section 3 calls a found key defect a win. Rubric section 6 says a claim
that would change the key needs human review. Both are recorded: the row counts
under KEY DEFECTS FOUND and is held out of the headline.

---

## 11. Cost discipline

The plumbing proof runs on 2 rows with `claude-haiku-4-5`, not on 39 with the
expensive model. The full cold run is T005 and is not launched from here.

The uniform-election escape (rubric 5.1) runs ONLY on rows that name an
out-of-jurisdiction LCD, so its cost scales with model error and not with
dataset size.

---

## 12. Command reference

    # denominators, and the proof that drift aborts
    python3 scripts/policy_eval/denominators.py
    python3 scripts/policy_eval/denominators.py --selftest

    # grading discrimination, hermetic and free
    python3 scripts/policy_eval/selftest_discrimination.py

    # report-shape gate, hermetic and free
    python3 scripts/policy_eval/selftest_report_gate.py

    # tool isolation, control arm plus isolated arm, costs a few model calls
    python3 scripts/policy_eval/selftest_tool_isolation.py

    # end to end on 2 rows
    python3 scripts/policy_eval/run_eval.py --run-id demo2 --limit 2 \
        --model claude-haiku-4-5 --adjudicator-model claude-haiku-4-5 \
        --partial-note "2-row plumbing proof, not a measurement"

    # re-check the prompt log of any past run
    python3 scripts/policy_eval/verify_no_leak.py --run-id demo2
