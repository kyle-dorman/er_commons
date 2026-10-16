# Task 09F — Dev6 sampling and formatting comparison

Completed the user-authorized two-step comparison on the same 136 frozen Dev6
answers, with two fresh passes per condition. Stop for user review; no semantic
rubric changes, parser recovery, further expansion or automatic promotion occurred.
The original Dev3/Dev6 and grounding artifacts remain unchanged.

Both conditions explicitly sent temperature **0**, top_p **1**, seed **0**, medium
reasoning and a 4,096-token output limit. All 544 native response headers confirmed
temperature 0/top_p 1, with identical reported sampling profiles; the provider did not
echo seed. The original prompt remained byte-identical in the sampling condition.
Format v2 only appends serialization instructions and a populated invented example;
evidence, schema, parser, rubric and restricted expectations are unchanged.

| Condition | Correct / 136 | Accuracy | Macro-F1 | Valid / 136 | Invalid |
| --- | --- | --- | --- | --- | --- |
| Explicit sampling, pass 1 | 109 | 80.15% | 0.7696 | 132 | 4 |
| Explicit sampling, pass 2 | 108 | 79.41% | 0.7522 | 132 | 4 |
| Format v2, pass 1 | 115 | 84.56% | 0.8186 | 134 | 2 |
| Format v2, pass 2 | 110 | 80.88% | 0.7628 | 134 | 2 |

Historical unspecified-settings Dev6: 109/136 correct (80.15%), macro-F1 0.7692,
131/136 valid. Its provider defaults cannot be reconstructed from saved receipts;
it is not a controlled repeated comparison of sampling settings. New original-prompt
coverage is 97.06%; format-v2 coverage is 98.53%. All twelve clean abstentions agree
in every pass. Passing controls: 59/62, 60/62, 60/62, 60/62 in table order.

## Invalid outputs and repeatability

Each explicit-sampling original-prompt pass has two JSON/schema failures and two
score-1 invariant failures. Pass 1 duplicates JSON keys; pass 2 omits required
`candidate_point_ids` in issue objects. Both format passes have **zero JSON/schema
failures**; each still has two outputs assigning 1 with an empty `missing_essentials`
list. The score-1 rule was deliberately preserved for this isolated experiment.

Format pass 1 fails C041 C04 and C014 F10; pass 2 fails C041 C04 and C041 F02.
These remain non-scores and errors on the full denominator. No retry or parser
normalization recovers them. Of the five historical invalids, C014 O02, C001 O01,
C001 R02 and C019 C05 are valid and correct in all four new passes, including
original-prompt sampling. C014 F10 is invalid in format pass 1 and receives 1 rather
than expected 0 in pass 2: fixing serialization does not fix the semantic judgment.

| Repeated condition | Numeric changes / valid in both | Numeric agreement | Validity transitions | All outcome changes / 136 |
| --- | --- | --- | --- | --- |
| Original prompt | 14/128 | 89.06% | 8 | 22 |
| Format v2 | 6/133 | 95.49% | 2 | 8 |

Explicit controls do not make generation deterministic. The two format repetitions
show fewer observed flips, but this is a small fixed development comparison, not a
calibrated stability guarantee. Variants within each question are correlated.
Format v2 improves full-denominator macro-F1 over the matching sampling pass in
both repetitions, but the size varies substantially. It also newly fails C056 F01
relative to sampling pass 2, while recovering C037 C02; the no-new-control-failures
criterion is therefore not uniformly met. C056 F01 had already failed in historical
Dev6 and sampling pass 1, so this is a paired regression, not a newly discovered case.
No automatic promotion; retain both conditions and review the unresolved score rule.

## Per-question failures

Each cell is total incorrect outcomes / invalid outputs. Invalids are included
inside total failures, not added to them. Full score/rationale/receipt records are
in the external comparison report bound by the JSON pointer.

| Question | Sampling 1 | Sampling 2 | Format 1 | Format 2 |
| --- | --- | --- | --- | --- |
| C041 | 3 / 1 | 5 / 1 | 2 / 1 | 3 / 2 |
| C037 | 4 / 0 | 4 / 1 | 4 / 0 | 5 / 0 |
| C014 | 5 / 1 | 5 / 0 | 4 / 1 | 5 / 0 |
| C001 | 4 / 0 | 5 / 1 | 3 / 0 | 4 / 0 |
| C019 | 6 / 1 | 5 / 1 | 4 / 0 | 5 / 0 |
| C056 | 5 / 1 | 4 / 0 | 4 / 0 | 4 / 0 |

The format repeats still disagree on partial-credit boundaries. C056 remains a
control weakness: F01 receives 1 in both format passes; O04 receives 1 then 0,
instead of the proposed 2. These are disagreements with synthetic development expectations,
not new human findings or authorization to relabel answers.

## Cost, caching and validation

| Pass | Cached input | Estimated USD |
| --- | --- | --- |
| Explicit sampling, pass 1 | 53.41% | 0.17026733 |
| Explicit sampling, pass 2 | 66.78% | 0.14365913 |
| Format v2, pass 1 | 65.73% | 0.14929899 |
| Format v2, pass 2 | 70.31% | 0.14135223 |

Total estimated cost **USD 0.60457768**, with **64.12%**
of input tokens served from native cache. There were 544 fresh calls, no retries,
no saved-receipt substitutions and no extra cache probe. Native totals:
6,738,404 input / 4,320,516 cached input / 224,558 output tokens.
Actual billing and cache-write counts remain unknown. The four passes respected
USD 8 / 544 requests / 2,228,224 output tokens / 4,800 execution seconds aggregate caps and
each pass's USD 2 / 136 requests / 557,056 output tokens / 1,200 seconds caps.

Validation: 440 focused tests, `make fix`, `make check` (4,451 passed, one skipped),
and `git diff --check`. Independent preflight and postrun reviews verified all
requests, strict classifications, metrics, native sampling headers, usage and caps.
The prior grounding audit found all 284 GLM requests in the selected experiment
omitted sampling controls; historical effective defaults are unknown. No grounding
rerun was performed. No reserved/test access, commit or push.

[Machine-readable pointer](task09f_sampling_format_dev6_result.json) binds the
external report, plan, audit, validation and review evidence. The
[task outcome](../../tasks/sprint2/09f_implement_adequacy_judge.md) owns the review gate.
