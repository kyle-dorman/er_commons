# Task 11D.8 — V10 paired Luna and Haiku comparison

Status: Complete (2026-10-19); bounded comparison, no baseline promotion.

## Goal and authorization

The user requests V10 on the same six questions, two repeats each for Luna and
Haiku, with results by question, judge and model. This authorizes 24 fresh target
answers and their frozen component evaluations, not wider question exploration.
Use C041, C017, C019, C014, C037 and C056 in the fixed panel order.

## Accepted inputs and hypotheses

Use V10 from 11D.7 (citation clause check and support-to-conclusion completeness
check), the 11D.6 shared project summary, neutral locator projection and final
publication v5 fixed-six reference export. Preserve V6b examples and explicit
field schema. Both models receive identical substantive evidence and prompt.
Use Luna gpt-6-luna and Haiku claude-haiku-5-5 with their previously accepted
reasoning settings and native structured output. A/G/C remain frozen Luna and
S remains frozen Haiku; their core prompts and settings are unchanged. Prefix
the shared project context as prepared in 11D.6 and use neutral locators.

Hypotheses: the citation check reduces partially supported compound points;
the conclusion check reduces material answer facts left only in support;
shared general project context and neutral metadata reduce irrelevant provenance
caveats. This bundled condition cannot isolate each change's causal effect.
Historical scores remain descriptive comparators under their original contexts.

## Dispatch limits and stop policy

One prompt revision, two models, six fixed cases, exactly two planned repeats per
model: 24 generation slots. Maximum 100,000 input tokens and 12,288 output tokens
per generation; output allowance includes provider reasoning where applicable.
Judge input cap is 100,000 tokens; judge output cap remains 4,096. Maximum 16 judge items per answer, 384 judge
calls overall and 408 total count calls. Zero retries, replacement answers,
repair generations, best-of selection or extra repeats. Invalid outputs stay in
all planned-answer denominators; record unscored judges explicitly.

Reserve at most $30 for this experiment using a conservative token liability
calculation before dispatch; preserve usage estimates, missing fields and unknown
count billing. This is a new experiment reservation, not a claim of prior actual
spending. No paid calls before offline tests and independent preflight review.
Record executable exact caps, settings, conservative prices and reservation in
preflight. Stop at two hours from dispatch; per-generation timeout 900 seconds,
per-answer evaluation deadline at most 1,800 seconds. Stop globally for integrity failure, uncertain accounting, budget exhaustion or
provider/judge execution failure. This conservative preflight tightening avoids
continuing on an unverified transport condition. Invalid target content alone is
retained and does not stop later slots. Keep all planned slots and reasons.

## Implementation and validation

Use a new opt-in adapter/runner so sealed source, runs and Task 10 remain intact.
Bind actual native delivery, summary, V10, references, source content, candidate,
run/repeat/point identity and each projected judge context. Keep reference answers
and evaluator feedback out of target requests. Preserve raw requests/responses,
count/generation/judge receipts, partial errors and all judgments. Replay reports
without calls and verify full fixed-panel slot coverage. Independently review the
preflight boundary, then run make fix, make check and git diff --check for code
changes. Use bounded final review for accounting, denominators and report replay.

## Reporting and finish line

Report automatic validity, each A/G/S/C judged pass rate, strict all-judge pass
rate and complete-coverage counts by model and by question/model across both
repeats. For G give both point-level and all-points-per-answer denominators; judge
rates on evaluated items must not hide invalid or missing planned answers. A reports the substantive-answer routing result, not evidence adequacy or an
independently labeled routing-accuracy metric. These are model-judged pass
rates on six exposed cases, not independent ground-truth accuracy or statistical
proof of generalization. Preserve each repeat and failure reasons. Report costs
as estimated unless provider accounting explicitly supplies a charge.

No remaining-13, locked-test or reserved evaluation or content inspection. No
judge retuning, new stronger model or 11E. This comparison does not by itself
qualify a baseline. Update task outcome, result pointer and routing when complete.

## Validation and implementation outcome

The new `context_comparison` adapter reuses the frozen native count/receipt
boundary and checks the actual provider serialization, including each native
output schema. It validates delivered prompt and payload bytes before counting,
uses explicit no-retry settings and bounded deadlines, and preserves error causes.
The external runner binds projected source records and references, immutable task
snapshot, code/configuration and all 24 planned identities before dispatch.

Independent preflight review verified 23 unchanged passages, reference isolation,
source-seal chains and fixed judge cores. Repairs addressed shared-summary newline
parity, native schema serialization, source provenance, time limits and the
immutable contract snapshot needed for future replay. The first mock transport
used the wrong HTTP library family; the repaired tests exercise the actual SDK
serializer with mock HTTP and no live calls. Failed validation logs and draft
preflights remain preserved.

Validation passed: 13 transport tests, three external scheduling/replay tests and
10 reporting tests; make fix, make check (4,166 passed, one skipped) and
`git diff --check`. Reporting distinguishes A's substantive routing result from
accuracy, G point-level support from per-answer all-point support, and evaluated
items from all planned answers. This avoids hiding unavailable outputs or
weighting a long answer as though it were several independent questions.

## Measured outcome

All 24 planned answers were valid and fully evaluated: 24 generation calls,
207 judge calls and 231 count calls, with zero retries/replacements. No output
truncation, missing slot or incomplete evaluation occurred. Both models retained
the same six questions, shared context and V10 prompt across both repeats.

| Model | Valid | A substantive | G all points | S sufficient | C adequate | All checks |
| --- | --- | --- | --- | --- | --- | --- |
| Luna | 12/12 | 12/12 | 11/12 | 8/12 | 8/12 | 5/12 (41.7%) |
| Haiku | 12/12 | 12/12 | 5/12 | 11/12 | 8/12 | 3/12 (25.0%) |

G point-level support was 39/40 (97.5%) for Luna and 86/95 (90.5%) for Haiku.
The all-checks column is the recorded diagnostic conjunction, not a new official
Task 12 metric. A denotes substantive-answer routing, not independently labeled
classification accuracy. Every rate retains its planned-answer denominator.

| Question | Luna all checks | Haiku all checks |
| --- | --- | --- |
| C041 — Animal controls | 0/2 | 1/2 |
| C017 — Electricity/GHG | 0/2 | 0/2 |
| C019 — Groundwater | 1/2 | 1/2 |
| C014 — Cumulative transportation | 0/2 | 0/2 |
| C037 — Wetland function | 2/2 | 0/2 |
| C056 — Flooding | 2/2 | 1/2 |

The combined model coverage reaches four of six questions with at least one
all-checks pass. Neither model passes electricity/GHG or transportation in either
repeat. No condition is promoted; 11E remains unstarted.

### Learnings and limitations

- The conclusion check did not reliably move essential facts into the conclusion.
  Both models failed C on C017 and C014 twice. C017 omissions concern distributed
  solar storage and/or exclusion of the regional battery benefits; C014 failures
  concern the broader regional-growth context. These are the frozen C judgments,
  not independent new human adequacy labels.
- Luna grounded nearly all judged points but still omitted necessary support for
  parts of its conclusions. On animal controls, important facts sometimes landed
  only in optional context or were incompletely restated in supporting points.
  Haiku supplied fuller support but failed grounding more often; five of its nine
  failed G points were qualifications. Citation-scope, absence-claim and table
  interpretation failures persist despite the new instructions.
- Both models produced valid complete outputs within the allowance. This run does
  not isolate V10's two additions: the shared summary, neutral locators/references
  and qualification wording are also new relative to historical V6b comparisons.
  Do not interpret the lower historical-to-current scores as a causal estimate of
  either new sentence. Two repeats on six exposed questions establish no general
  model ranking. No judges or references were retuned from these results.

Library-reported generation-plus-judge cost estimates sum to $0.178724 across
231 usage receipts, with no missing cost receipt. Counting billing remains unknown
and excluded from this estimate. The current $30 reservation and cumulative
$95.740432 reservation are liability records, not spending. Raw usage retains
unreported subtotals separately rather than replacing them with zero.

### Replay and publication

The first replay assertion compared Python tuples against JSON arrays directly.
All 24 plans/reports match exactly after lossless JSON normalization. A separate
corrective replay checker preserves the original runner, failed check and live
artifacts, and passes five regression tests with provider calls disabled. No
answers, judgments or scores changed. The complete reports include per-question,
per-model, per-judge and per-point denominators, each repeat, and failure claims
with judge explanations. Exact artifacts and final independent audit are bound by
the [result pointer](../../docs/specs/task11d8_result.json).
