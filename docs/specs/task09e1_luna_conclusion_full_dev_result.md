# Full-development conclusion comparison result

The original and clarified conclusion prompts are effectively tied on the full
development set. The clarification offers no convincing overall improvement:
pooled conclusion macro-F1 rises only 0.04 percentage points, equal-weight question
macro-F1 falls, claim-review F1 falls and correct final numeric scores tie. Keep
the simpler original conclusion prompt; no package default or label is changed.

The [contract](task09e1_luna_conclusion_full_dev_v1.md) authorized all 430 eligible
answers across 19 development questions, excluding 12 records. Reused 323 sealed
Dev6 claim decisions and generated 733 missing claims once. Both fresh 430-answer
conclusion passes received exactly the same 1,056 frozen actual claim judgments.
All 1,593 new generations validated with no retries or replacement outputs.

## Label balance and metric choice

There are 392 substantive conclusions: 294 supported (75%) and 98 unsupported
(25%). The 38 clean abstentions are separate. Original claim labels are 862
supported and 194 unsupported (81.6%/18.4%). Always predicting supported would
give 75% conclusion accuracy but only 42.86% class-macro F1. Accuracy alone is
therefore insufficient; supported-class F1 alone also hides the negative class.

Primary macro-F1 weights supported and unsupported equally. Both conclusion
arms return a valid binary judgment on every substantive case, so ordinary and
coverage-aware F1 coincide here. For numeric scores they differ: unresolved
disagreements count as misses in the all-eligible metric, and the conditional
metric is accompanied by explicit score coverage. These are agreement metrics
against unchanged synthetic proposals, not human-validated truth.

## Full-set results

| Measure | Original | Clarified |
| --- | --- | --- |
| Conclusion class-macro F1 | 92.93% | 92.97% |
| Conclusion accuracy | 94.39% (370/392) | 94.39% (370/392) |
| Conclusion balanced accuracy | 95.58% | 95.92% |
| Equal-question mean conclusion macro-F1 | 92.97% | 92.67% |
| Claim-review class-macro F1 | 96.96% | 96.55% |
| Claim-review correct | 1037/1056 (98.20%) | 1034/1056 (97.92%) |
| Original-claim corrections / damaging reversals | 37 /12 | 35 /13 |
| Final numeric macro-F1, all eligible | 88.51% | 88.40% |
| Final numeric macro-F1, returned scores only | 93.51% | 93.27% |
| Numeric scores returned | 350/392 (89.29%) | 351/392 (89.54%) |
| Correct final numeric scores, all eligible | 328/392 (83.67%) | 328/392 (83.67%) |
| Correct N/A outcomes | 38/38 | 38/38 |
| Correct final status/score, all answers | 366/430 | 366/430 |
| Unresolved original-versus-review disagreement | 42 | 41 |

Frozen original claim agreement is 1,012/1,056 (95.83%), macro-F1 **93.46%**.
Review improves both arms relative to that same vector, but an original/review
disagreement still prevents a numeric score under the unchanged aggregation.

## Per-class conclusion performance

| Class | Count | Original precision / recall / F1 | Clarified precision / recall / F1 |
| --- | --- | --- | --- |
| supported | 294 | 99.28% / 93.20% / 96.14% | 99.64% / 92.86% / 96.13% |
| unsupported | 98 | 82.76% / 97.96% / 89.72% | 82.20% / 98.98% / 89.81% |

Original: 274 supported accepted, 20 supported rejected, 96 unsupported rejected
and 2 unsupported accepted. Clarified: 273, 21, 97 and 1 respectively. Most
conclusion errors are over-rejections, not acceptance of unsupported conclusions.
There are 26 changed conclusion decisions: 13 corrections and 13 regressions.

## Breadth checks

| Population | Substantive conclusions | Original macro-F1 | Clarified macro-F1 |
| --- | --- | --- | --- |
| Prior six questions | 124 | 91.12% | 92.04% |
| Thirteen added questions | 268 | 93.80% | 93.41% |
| Excluding C041 | 372 | 94.53% | 94.89% |

The added 13 questions show no gain. These are broader development checks, not
held-out tests. The current fresh Dev6 calls are a new comparison, not reuse of
the earlier reported Dev6 result. One pass does not establish repeatability.

| Question | Original correct/eligible | Clarified correct/eligible | Original / clarified macro-F1 |
| --- | --- | --- | --- |
| C001 | 20/21 | 21/21 | 94.43% / 100.00% |
| C006 | 19/19 | 19/19 | 100.00% / 100.00% |
| C007 | 26/28 | 27/28 | 91.25% / 95.45% |
| C008 | 17/17 | 16/17 | 100.00% / 81.72% |
| C014 | 18/18 | 18/18 | 100.00% / 100.00% |
| C017 | 22/22 | 22/22 | 100.00% / 100.00% |
| C019 | 19/20 | 20/20 | 94.30% / 100.00% |
| C027 | 16/17 | 14/17 | 88.28% / 73.02% |
| C028 | 13/15 | 14/15 | 86.61% / 93.33% |
| C029 | 21/23 | 19/23 | 88.73% / 80.83% |
| C036 | 16/16 | 16/16 | 100.00% / 100.00% |
| C037 | 24/25 | 25/25 | 93.22% / 100.00% |
| C041 | 14/20 | 13/20 | 67.03% / 62.67% |
| C042 | 23/24 | 24/24 | 93.16% / 100.00% |
| C045 | 19/22 | 19/22 | 83.62% / 84.83% |
| C050 | 21/22 | 21/22 | 94.54% / 94.54% |
| C051 | 23/23 | 23/23 | 100.00% / 100.00% |
| C054 | 19/20 | 20/20 | 91.34% / 100.00% |
| C056 | 20/20 | 19/20 | 100.00% / 94.30% |

## Independent source review

The source-review selection covers 91 answers across all nineteen questions:
all 74 answer slots with changed judgments or false acceptances, plus nineteen
stable correct controls (two overlap those slots). Reviews include changes from
the frozen original claims even when both conclusion arms agree with each other.
The three independently scoped reports retain per-answer sources and rationales.

The clarification does repair real evidence-ownership mistakes: for example,
C007, C028, C037, C042 and C054 contain conclusions supported by citations
elsewhere in their original answers. C045 also has a corrected rejection where
the original judge accepted a conclusion despite acknowledging its unsupported
second assertion. These support the intended rubric, but are offset elsewhere.

Remaining problems include:

- **Cross-citation leakage in claim reviews.** C054-C02 accepts a point using S2
  even though that point cites only S1. C029-C02 similarly uses S2 to repair an
  S1-only citation. Clarifying the rule does not reliably enforce it.
- **Overly strict synthesis or qualification readings.** C007 rejects local
  access language despite a source describing a more accessible environment;
  C027 and C029 have stricter readings of qualified summaries. Some disagreements
  are defensible interpretations, not definite factual hallucinations.
- **Compound assertions and wording sensitivity.** C036's indoor-exemption
  wording omits the source's alternative of limited requirements. C050's map
  descriptions produce different outcomes depending on adjective attachment.
  Source distinctions and unresolved ambiguity remain separate from label counts.

Source review does not relabel proposals or transform every label-matching
change into a verified improvement. It also does not establish identical-input
repeatability: complete inputs are distinct and each arm ran once.

## Execution and verification

Standard-rate estimates: new claims $0.226710895, original conclusion
$0.292737990, clarified $0.298601140; **$0.818050025 total**. Native payer fields
show OpenAI for 838 calls and developer for 755; these estimates are not an
invoice or a credit guarantee. Conclusion input cache-read ratios were 40.87%
and 43.69%, respectively (new claims: 57.70%).
All 430 complete conclusion inputs are distinct. Separate quotation diagnostics
do not modify semantic decisions or the final-score policy. Missing-quotation
flags were 205/229 and nonliteral locator counts 39/47, respectively. All 75
zero-point answers were retained: 38 clean abstentions and 37 substantive cases.

Focused tests: 357 passed; external/metrics guards: 27 passed. make fix passed.
make check: 4,274 passed, one skipped, the same three historical Task 06G failures.
No reserved/test inference, other models, later tasks, commits or pushes.

Implementation adds only an explicit full-development opt-in to the maintained
panel builder/loader; the default Dev6 artifact shape and inputs remain unchanged.
The F1 helper uses documented [scikit-learn definitions](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html)
with narrow standard-library counting because sklearn is not installed. Explicit
labels, zero-division handling, absent-class flags, confusion matrices and
independently checked fixtures prevent hidden denominator changes.

The [result pointer](task09e1_luna_conclusion_full_dev_result.json) binds the full
analysis, source reviews, native/metric audits, validation and completion inventory.
