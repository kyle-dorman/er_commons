# Task 11D.3 — Test a light C014 question revision

Status: Complete (2026-10-18); no demonstrated improvement; no publication change.

## Abstract and goal

Test whether replacing “the DEIR” with “the environmental review” improves C014
answer quality with V6b, without supplying retrieval clues. The user approved
trying the exact lighter question. The detailed 11D.2 question was rejected for
giving a future search agent too many clues; it is not approved or activated.

## Approved experimental question

> How does the environmental review account for the Quarry and Candlestick Point developments when evaluating the Baylands’ cumulative transportation impacts?

Original control:

> How does the DEIR account for the Quarry and Candlestick Point developments when evaluating the Baylands’ cumulative transportation impacts?

Authorization: after the exact lighter wording was displayed, the user said:
“Ok try that question and see if it’s better or not. I expect the same but let’s see”.
This authorizes a versioned experiment, not replacement of the benchmark publication.
The existing reference remains unchanged and evaluator-only.

## Inputs, outputs and hypothesis

Use sealed 11D.1 V6b C014 records, exact V6b prompt, Task 10 evidence/citation
mapping, frozen 09G judges, 11D.2 manual review definitions and prior results.
Output four freshly generated C014 candidates, complete A/G/S/C evaluation,
independent source review, raw receipts, exact identities, replay, accounting and
result pointer. The old V6b repeats remain historical context, not substituted
for contemporaneous controls.

Hypothesis: broader source scope may improve coverage of the supplied later
appendix without revealing its location or expected findings. Null expectation:
no consistent improvement; ambiguity and small-model errors may remain.

## Design and limits recorded before dispatch

A narrow C014-only question experiment: original r1, revised r1, revised r2,
original r2. Two observations per wording; no selection of favorable outputs.
The fixed three/six manifests stay unchanged. This is not a panel promotion test.
Keep V6b, all evidence bytes/metadata, model, reasoning, output schema, judges and
reference fixed. Do NOT activate the 11D.2 metadata correction in either arm;
otherwise a score difference would confound wording and metadata visibility.

Maximum four generation calls, 64 judge calls (16 per candidate), 68 counts;
zero retries, repairs or extra repeats. One question revision only. Exact input
cap 100,000; generation output cap 4,096 including reasoning; judge outputs use
frozen settings. Luna medium/default and frozen Luna A/G/C, Haiku S. Preserve
full point fan-out; stop rather than omit points if the limit is exceeded.
Reserve USD 0.028072 per possible call: USD 1.908896 new maximum liability, added
to prior USD 43.831536 = USD 45.740432 under the USD 100 ceiling. These are
conservative inherited reservations, not invoices or current price claims.
Counting allowance remains zero under the user's assumption; actual counting
billing remains uncertain. Preserve raw token usage and unknown outcomes.
One-day task timebox; maximum 15 minutes generation and 30 minutes evaluation per
candidate. Stop on integrity/context/provider/structural/accounting failure;
semantic failures do not suppress planned observations. No redispatch.

## Plan, learning and review

Create additive question-overlay records and matching citation payload hashes;
never mutate Task 10. Bind condition, question hash and repeat into fresh run
identities. Verify requests differ only in question wording between conditions;
keep reference and evaluator feedback outside generation. Independently review
preflight/dispatch once with one repair pass. After calls review all four answers
against supplied evidence, then compare frozen results and manual interpretation.

Use the experimental principles recorded in 11D.1: explicit requirements,
controlled comparisons and human source review. A natural search question need
not enumerate reference items. Do not optimize task wording until a model passes.
Two repeats of one exposed case cannot establish a reliable general improvement
or retrieval performance; no search agent is being tested here.

## Validation and acceptance

Offline overlay/schema/isolation checks before live calls; preserve sealed input
hashes, receipts and failures. Reuse maintained provider/harness routines; keep
new orchestration narrow and external. Run make fix, make check and git diff
--check for any code changes. Require provider-disabled report replay. Report
better, worse, mixed or no demonstrated improvement using both repeats, coverage
and concrete errors; no baseline promotion from this experiment.

## Non-goals

No remaining 13 development cases, locked test or reserved challenges; no 11E.
No judge retuning, reference change, metadata intervention, prompt revision,
publication replacement, broader panel rerun or search implementation.

## Outcome

The lighter question did not demonstrate improved performance. All four fresh
answers were valid and fully evaluated. Original wording passed C twice; revised
wording passed C zero times. Both passed S twice. All-G/S/C diagnostic passes were
one of two original and zero of two revised observations. These are one-case
tuning observations, not evidence of a general or statistically reliable decline.

| Wording | Repeat | Grounded points | S | C |
| --- | --- | --- | --- | --- |
| Original | 1 | 6/6 | Pass | Pass |
| Revised | 1 | 3/6 | Pass | Fail |
| Revised | 2 | 2/6 | Pass | Fail |
| Original | 2 | 2/4 | Pass | Pass |

Independent source review, locked before seeing these judgments, found mixed
behavior: revised repeat 1 had clearer Draft/Final attribution, but revised repeat
2 missed necessary own citations. Original repeat 2 also had citation and TRA-4
method defects. Both wordings included the later 2035 inputs in both repeats;
none clearly supplied the complete broader future-growth explanation. Manual
conclusion-source status counts were one pass, two material defects and one
unresolved edition attribution. Preserve these separately from frozen scores.

A bounded postjudge review confirmed a table-reading error in revised repeat 2
G/S2: both developments are in the Land Use column. Its C failure also conflates
explicit 2035 inclusion with absence of separately named 2040 inputs. The latter
does not logically contradict the reference's general future-input statement.
Other G failures reflect real missing citations or the intentionally unchanged
edition-metadata visibility mismatch. Original repeat 1 has a quotation-fidelity
flag. None of these diagnoses overwrites a score or triggers replacement calls.

### Validation, accounting and preservation

`make fix`, `make check` (4,103 passed, one skipped) and `git diff --check` passed.
Predispatch independent review passed after an accounting-stop guard was added.
The offline same-candidate fixture verified question-only A/G/S/C projection
changes; final native generation requests are identical within each wording and
differ only in question text across wordings. All 233 protected bindings match.

All four reports replay with providers disabled using canonical serialized JSON.
The initial raw Python equality check failed on tuple/list round-tripping; the
failure is preserved. A separate audit compares canonical serialization without
changing the frozen runner, sealed observations or model outputs.

Actual calls: four generations, 34 judgments and 38 counts; zero retries, unknown
usage records or discarded outputs. Known usage is 407,584 input tokens including
cache and 23,987 output tokens including reasoning. The inherited dated-rate
estimate is USD 0.05323371, excluding uncertain counting charges; it is not an
invoice. Retain the full USD 1.908896 reservation and USD 45.740432 combined
liability; no refunds are inferred from low observed usage.

The [result pointer](../../docs/specs/task11d3_result.json) binds complete outputs,
raw receipts, sample/point identities, source-first and postjudge reviews,
comparison, replay, failure record and question authorization under
`pipelines/brisbane_baylands/task_11/validation_11d3_20261018`.

### Decision and learning

Stop after the preregistered four answers. Do not adopt the lighter wording on
performance grounds, weaken the reference, or keep tuning the question until
Luna passes. The lighter phrasing remains a tested experimental alternative,
not a changed publication. Keep V6b and the original published question; no
baseline promotion or 11E activation. The staged metadata correction remains a
separate condition, not silently combined with this comparison. A future search
agent would need its own evaluation; this test provides no retrieval evidence.
