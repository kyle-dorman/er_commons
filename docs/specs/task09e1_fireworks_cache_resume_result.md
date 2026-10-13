# Fireworks cache repair and updated development results

GLM completed the 108 authorized remaining conclusions. Both models passed the
cache gate before evaluation. DeepSeek stopped after 49 claims because one
response exhausted its 4,096-token output allowance entirely on reasoning,
with no final answer. No retry or conclusion pass followed that bounded stop.

## Updated comparison

Only the updated, patched Haiku result is included below. Luna and Haiku were
not rerun. All models use the same development population: 1,056 claims,
392 substantive conclusions/numeric scores and 38 separate clean N/A answers.

| Model/configuration | Claims macro-F1 | Claim-review macro-F1 | Conclusion macro-F1 | Numeric macro-F1 | Numeric coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna historical | 93.46% | 96.96% | 92.93% | 88.51% | 350/392 (89.29%) |
| Haiku updated | 93.23% | 94.84% | 96.05% | 89.05% | 354/392 (90.31%) |
| GLM Flash completed | 97.50% | 94.64% | 94.46% | 90.60% | 343/392 (87.50%) |
| DeepSeek Flash stopped early | 9.02%* | 0%* | 0%* | 0%* | 0/392 |

These are coverage-aware class-macro F1 scores: every missing or invalid output
remains a false negative for its true class, without inventing a predicted class.
They are not conventional F1 computed only on successful outputs. Every failed
or missing slot also counts as wrong in full-denominator accuracy below.
Claim reviews are the conclusion judge's second assessment of individual claims.

| Model/configuration | Claims correct / 1,056 | Conclusions correct / 392 | Numeric correct / 392 | Correct N/A / 38 |
| --- | ---: | ---: | ---: | ---: |
| Luna historical | 1,012 | 370 | 328 | 38 |
| Haiku updated | 1,011 | 379 | 331 | 38 |
| GLM Flash completed | 1,037 | 355 | 332 | 38 |
| DeepSeek Flash stopped early | 47* | 0* | 0* | 0* |

*DeepSeek has only 47 valid claims (4.45% coverage), one invalid locator response,
one truncated response and 1,007 undispatched claims. Its 47 valid predictions all
match the proposed labels, but this small scheduling-dependent subset cannot
support a full-panel accuracy comparison. The zero downstream scores describe
missing coverage, not observed incorrect conclusion judgments.

GLM retains all five original invalid claims and all 20 original invalid
conclusions. The continuation adds 99 valid and nine invalid conclusions:
396/430 valid overall, including all 38 N/A answers. Of the 392 substantive
conclusions, 358 validate, with three false acceptances and no false rejections;
29 invalid outputs plus five invalid-claim skips account for the other 34.
Conditional conclusion F1 is 98.87%, but the full-denominator value is 94.46%.
Final numeric results have 332 correct, 11 incorrect and 49 missing scores:
15 unresolved claim/review disagreements plus the 34 missing conclusion outputs.
Conditional numeric F1 is 96.86%; full-denominator numeric accuracy is 84.69%.

All nine new invalid outputs involve answers with zero frozen individual claims:
the required claim-review array is empty, but GLM invents a `P1` review for the
conclusion itself. These are schema-compliance failures, not missing citations
or malformed JSON. They remain failures without retries. The sole new valid
conclusion disagreement has substantial support for its central relationship
but an unverified compliance premise; independent source review treats it as
ambiguous and leaves the proposed label unchanged.

GLM has the strongest original-claims F1 and slightly higher final numeric F1
in this comparison. Updated Haiku has higher conclusion F1 and numeric coverage.
GLM's output-validation failures are a material limitation, despite strong
agreement among valid conclusions. Full per-class confusion, conditional metrics,
equal-case metrics, per-case results and prior-Dev6/added-13/outside-C041 breakdowns
are retained in the external analysis and independent arithmetic audit.

## Cache repair and actual savings

The old message layout placed a varying JSON schema before shared evidence.
Point identifiers and review arrays could therefore break the reusable prefix.
The opt-in repair keeps the exact rubric in the system message, puts the unchanged
complete evidence-first payload before the exact schema instructions, and supplies
a stable native `prompt_cache_key` for the model/stage/rubric/evidence/question.
No evidence truncation, semantic prompt tuning or label exposure was introduced.
Default rendering remains unchanged.

Each model passed 12 separately isolated protocol requests before evaluation,
covering old/fixed layouts and both judging stages. All 24 outputs validated.

| Model/stage | Old identical repeat | Old changed target | Fixed identical repeat | Fixed changed target |
| --- | ---: | ---: | ---: | ---: |
| GLM claims | 99.77% | 0% | 96.50% | 96.50% |
| GLM conclusions | 99.82% | 0% | 96.79% | 96.32% |
| DeepSeek claims | 99.50% | 0% | 99.50% | 98.29% |
| DeepSeek conclusions | 99.50% | 0% | 99.50% | 97.23% |

Real-run cached-input shares were **22.72% for the 108 resumed GLM conclusions**
and **68.92% for DeepSeek's 49 attempted claims**. The earlier GLM conclusion
batch was 2.35%; this is a descriptive comparison across different subsets,
not a controlled estimate of the repair's effect. Historical plus new GLM
requests together show 6.91%, since earlier calls cannot gain caching retroactively.

The probes deliberately shared roughly 25,000-token evidence prefixes. Actual
GLM continuation requests were all below 8,192 input tokens. They covered 41
routing groups, including 24 singletons; every group's first observed request
reported zero cache reads.
The 67 subsequent requests reused 35.34% of input tokens in aggregate, with
39 still showing zero cache reads. Native affinity is a hint, not a cache guarantee.
The repair establishes reusable evidence prefixes; it does not eliminate cold,
short or provider-side cache misses. Layout and affinity changed together, so
this experiment does not separate their individual effects.

## Cost, limits and validation

Native-token estimates at the dated standard rates:

| New work | Estimated cost |
| --- | ---: |
| GLM cache qualification | $0.02920128 |
| DeepSeek cache qualification | $0.052982616 |
| GLM 108-conclusion continuation | $0.08280806 |
| DeepSeek 49-claim partial run | $0.08867118 |
| Total this follow-up | **$0.253663136** |

GLM's whole original-plus-resumed evaluation has $1.09108090 of measured native
usage, excluding probes and the unknown charge from the original HTTP 412.
Its $0.0055529 reservation for that failed attempt remains retained. These are
standard-rate estimates, not provider invoices; conservative reservations are
not spending. Historical Luna reused claims, and Haiku is a selected patch, so
incremental costs should not be presented as equal fresh-pipeline model costs.

Both providers requested native medium reasoning; Fireworks maps DeepSeek's
medium to native high (scale 75), so compute is not equal. DeepSeek's stop was
output exhaustion, not input length: 3,133 input tokens versus a 20,704 allowance.
The runtime conservatively capped context at 200,000 even though the model
condition declared 1,000,000. No request exceeded its allowance.

The maintained cache/prefix change passed 205 focused tests, including 17 new
guards. Probe/main guards passed; the reviewed analyzer passed 14 metric/guard
tests. `make fix` passed. `make check` produced 4,320 passed, one skipped and the
same three historical Task 06G failures. Independent cache, native-accounting,
metric and source reviews accompany the result pointer. Previous sealed
inventories remain unchanged. No commits, pushes, defaults, labels, reserved/test
data or later-task work changed.

These are development results against synthetic proposed labels, not independent
human calibration or judge qualification. GLM mixes preserved and repaired
transport layouts; updated Haiku includes the user-accepted locator prompt patch.
Provider-owned claim vectors differ. Single passes do not establish stability.
DeepSeek remains incomplete; any continuation must explicitly revise the bounded
output/stop policy while preserving this failed attempt and its costs.

See the [frozen contract](task09e1_fireworks_cache_resume_v1.md) and
[result pointer](task09e1_fireworks_cache_resume_result.json).
The cache design follows [Fireworks caching guidance](https://docs.fireworks.ai/guides/prompt-caching)
and the [native API contract](https://docs.fireworks.ai/api-reference/post-chatcompletions).
