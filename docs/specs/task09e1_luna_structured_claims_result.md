# Task 09E.1 — Focused structured-explanation pilot outcome

The [100-call pilot](task09e1_luna_structured_claims_v1.md) is complete.
**Structured explanations did not establish a useful improvement.** Overall
agreement rose by one judgment, but a short pet-policy input regressed sharply.
The predeclared development criteria fail; set this candidate aside. No broader
run, default change or further prompt tuning followed.

## Results

Ten unchanged development inputs, five fresh repetitions per input per arm.
Both arms used Luna Responses at medium reasoning with the repaired cache layout.
The candidate added three headings in the existing explanation string; the
claim-level Boolean, schema, question and cited evidence remained unchanged.

| Metric | Direct baseline | Structured explanation |
| --- | ---: | ---: |
| Valid outputs | 50/50 | 50/50 |
| Agreement with proposed labels | 44/50 (88%) | 45/50 (90%) |
| Trouble-input agreement | 14/20 | 15/20 |
| Control agreement | 30/30 | 30/30 |
| False acceptances | 0 | 0 |
| False rejections | 6 | 5 |
| Inputs unanimous and correct | 7/10 | 8/10 |

| Trouble input | Baseline correct /5 | Structured correct /5 |
| --- | ---: | ---: |
| Short pet policy, S2 form | 2 | 3 |
| Short pet policy, S1 form | 5 | 2 |
| Expanded pet policy | 4 | 5 |
| Grading deadline qualification | 3 | 5 |

The pet-policy total declines from 11/15 to 10/15, while grading improves from
3/5 to 5/5. All five candidate label disagreements concern the short pet-policy
wording and the same narrower HOA/deed-versus-lease interpretation. Structured
explanation makes that interpretation visible but does not resolve it reliably.
The S1/S2 forms are related citation variants, not independent semantic cases.

The candidate misses the required gain of three trouble judgments (gain one)
and the requirement that no trouble input regress (S1 declines by three).
All-valid, perfect-control and unanimous-correct-count criteria pass. Those
partial successes do not override the conjunction. The contract permits no
expansion regardless of outcome.

## Interpretation and limits

All 50 candidate explanations contain the three requested headings and stay
within the requested 200 words (maximum 129 by whitespace count). Compliance
with the format is separate from faithful source interpretation. The explanation
is still generated text, not independent evidence that its conclusion is correct.

Independent source review inspected all 50 candidate explanations and all six
baseline label disagreements. Candidate explanations comprised 35 faithful concise
interpretations, ten accepted ambiguous policy readings and five narrower-attachment
disagreements. No concrete false acceptance or material invented qualifier was
identified. Some explanations compress source qualifications: four grading
summaries omit the City's timing exception, without changing their distinction
between the grading deadline and completed ecological recovery. Thus even a
useful concise explanation should not replace the original evidence. Citation
ownership was preserved; literal quotation diagnostics remain separate.

These are repeated judgments on an adaptively selected development failure
panel, not 100 independent claims, held-out accuracy or a significance test.
Pet-policy labels follow the user's accepted ordinary coordinated reading;
the alternative grammatical reading remains documented. No historical label
was changed. The candidate bundles structured output instructions with faithful
interpretation reminders, so differences cannot be attributed purely to format.

## Cost, validation and preservation

The baseline finished in 259 seconds and the structured arm in 313 seconds,
running concurrently; these are observed arm durations, not controlled latency
benchmarks. Estimated standard-rate cost is $0.013925195 versus $0.016972645,
**$0.030897840 total**. All 100 native payer fields report developer; actual
invoice and promotional-credit treatment remain unknown. Conservative reservations
total $0.377162500, below the $2 combined cap.

Native cache reads were 53,357/66,450 input tokens (80.3%) for baseline and
65,377/76,250 (85.7%) for structured. All 100 generations were fresh, with unique
native response identities, exact input-count parity and no replay, replacement,
retry or halt. Caching is input reuse, not reused judgments.

Focused regressions: 275 passed. Eleven offline launcher/analyzer guards passed.
`make fix` passed with 982 files unchanged. `make check` passed format/lint/types
and reported 4,259 passed, one skipped and only the three known historical Task
06G failures. Independent predispatch semantic/launcher reviews and postrun native
metrics/security audit passed. All 50,869 prior inventory checks matched.
Raw artifacts and decoded Inspect logs were scanned without exposing credentials.

The [result pointer](task09e1_luna_structured_claims_result.json) binds the frozen
inputs, native runs, analysis, reviews and completion inventory. All artifacts
are in the fresh `task_09/09e1_20261012_luna_structured_claims_v1/` namespace.
No package/default prompt change, conclusion calls, expanded dataset, commits or
pushes occurred.
