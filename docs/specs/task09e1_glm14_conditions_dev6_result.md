# Fourteen GLM repairs and three-model Dev6 conclusion prompt test

Thirteen of fourteen older GLM empty-list failures now validate and match the
proposed conclusion and numeric-score labels. One still fails the claim-review
coverage rule. Separately, the new semantic conclusion appendix fails the
predefined improvement criteria for Luna, Haiku and GLM on Dev6. Keep the original
semantic prompt; retain the useful empty-list clarification. No expansion or
default promotion follows. DeepSeek was not used.

## Fourteen targeted GLM repairs

The repair uses exactly the formatting instruction that succeeded in the prior
nine-item retry, with unchanged input payloads, schemas and settings. The remaining failure is
`task09a2-C007-O03-17-fbd8aaa318dc`: the supplied claim list is empty, but the
response still violates the required review coverage. It remains a failure;
there was no second retry.

Current full-development results below include the thirteen successful replacements
and preserve all other prior outcomes. Luna and updated Haiku were not rerun on
the full panel. These are coverage-aware class-macro F1 scores, with missing or
invalid outputs retained as false negatives for their true class. They are not
conditional F1 calculated only on successful outputs.

| Current configuration | Original claims F1 | Claim-review F1 | Conclusion F1 | Numeric-score F1 | Numeric outputs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna retained | 93.46% | 96.96% | 92.93% | 88.51% | 350/392 |
| Haiku updated | 93.23% | 94.84% | 96.05% | 89.05% | 354/392 |
| GLM updated after fourteen retries | 97.50% | 94.64% | **97.57%** | **93.46%** | 365/392 |

GLM has 377 correct substantive conclusions out of 392 (96.17% accuracy) and
354 correct numeric scores out of 392 (90.31%). Every failure counts as wrong
in these denominators. The remaining conclusion outcomes are three semantic
disagreements and twelve missing outputs: seven invalid conclusions and five
dependent skips from invalid claims. Numeric results comprise 354 correct,
eleven incorrect and twenty-seven missing scores, including fifteen unresolved
claim/review disagreements. All 38 clean N/A answers remain correct.

Original claims and claim-review scores are unchanged: all fourteen repair inputs
contain no individual claims. These patched full-panel results remain a selective
repair with mixed prompt provenance, not a fresh full-panel experiment.

## Separate fresh Dev6 prompt comparison

Each model ran a fresh baseline and a fresh candidate on identical own-model
frozen claim vectors. The baseline is the selected original conclusion prompt;
both GLM arms also contain the empty-list clarification. The candidate appends:

> A correct main answer does not compensate for an unsupported substantive assertion in the conclusion. Apply the same standard to conditions and scope in claims and conclusions. Accept ordinary paraphrases, but preserve qualifications that change the meaning.

There are 136 eligible answers per arm, 124 substantive conclusions/numeric
targets, 323 original claims/reviews and twelve clean abstentions. Luna and Haiku
dispatch all 136; GLM dispatches 135 because one original claim is invalid.
Its skipped answer remains in every applicable denominator. The six questions
are C041, C037, C014, C001, C019 and C056. The motivating C029 habitat-management
case is outside Dev6 and was not directly retested.

Every arrow below is **fresh baseline → candidate**, not a comparison with
historical outcomes from a different run.

| Model | Correct conclusions / 124 | Conclusion macro-F1 | Correct claim reviews / 323 | Correct numeric scores / 124 | Numeric macro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna | 115 → 114 | 91.12% → 90.21% | 318 → 316 | 106 → 103 | 88.87% → 86.65% |
| Haiku | 122 → 121 | 97.89% → 97.62% | 316 → 309 | 103 → 100 | 89.42% → 87.73% |
| GLM | 120 → 120 | 98.90% → 98.36% | 304 → 301 | 107 → 107 | 92.18% → 92.44% |

All metrics keep full denominators and count failures as wrong. Numeric coverage
is Luna 114→113, Haiku 107→105 and GLM 109→108 out of 124. The small GLM numeric
F1 increase does not represent more correct answers; it reflects changed class
error/coverage distribution. Its conclusion F1 changes despite the same correct
count because missing outcomes occur on different classes. Conditional metrics,
confusion counts and per-case/equal-case summaries remain in the bound analysis.

All arms get twelve of twelve clean N/A answers correct. There are no valid
false-positive conclusion judgments in these Dev6 arms. Outside C041, correct
conclusions are Luna 101→99, Haiku 102→102 and GLM 100→100 out of 104. Thus no
model has the required overall and outside-C041 gain, and all three lose
claim-review agreement. None passes the quantitative gate.

Response validity is Luna 136/136 in both arms; Haiku 136→135; GLM 132/135 in
both arms, plus the unchanged dependent skip. Invalid outputs were never retried
or relabeled as negative judgments.

## What changed, and what the sources show

- **Luna:** four conclusion fixes and five regressions. Seven of its nine
  flips occur on animal-control variants with the familiar interpretation
  ambiguity. The other two regressions are evidence-use errors outside C041:
  the candidate ignores an allowed full-answer citation explicitly listing
  future projects, and rejects a groundwater conclusion because its local
  citation is unresolved even while acknowledging that another allowed source
  supports it. Conclusion assessment permits evidence cited elsewhere in the
  answer, so these are not justified tightening of the support standard.
- **Haiku:** one semantic conclusion fix, one semantic regression and one lost
  output to validation. The fix correctly stops an unrelated false claim from
  invalidating an independently supported conclusion. The regression rejects
  a nonassertive “details follow” lead-in without identifying a false fact.
  Two reviewed claim regressions borrow uncited evidence; another rejects an
  inference that the same response accepts in the conclusion. The invalid
  response omits a required review of an optional-context claim. The net result
  provides no reason to retain the semantic appendix.
- **GLM:** no conclusion verdict changes among the 117 substantive answers
  valid in both arms. Three outputs gain validity and three different outputs
  lose it. Its unchanged correct-conclusion count therefore hides no measured
  semantic improvement. There are five valid claim-review reversals: two fixes
  and three regressions, plus the consequences of changed output coverage.

An illustrative claim-review regression shared by Luna and GLM uses evidence
from a different citation to support a drainage claim. That is allowed for the
conclusion but not for the individual claim, which must use its own citations.
One GLM baseline Boolean matched the label despite an explanation making the
same improper cross-citation argument, so its baseline rationale is not credited
as sound merely because the final Boolean happened to match.

The new appendix did not change those evidence-ownership rules, yet the observed
outputs still misapplied them. This is a reason to keep source review alongside
label metrics and avoid assuming that a broader “same standard” reminder will
improve the whole stack. A single pass cannot separate every prompt effect from
sampling variation, but this experiment supplies no evidence for expanding the
candidate. The clearer practical gain came from the narrow output-format repair.

## Cost, caching and verification

All 828 authorized requests finished with known usage: 820 valid outputs and
eight validation errors. There were no transport-uncertain requests, replayed
judgments, hidden retries or further model calls. Estimated cost at the frozen
dated native rates is **$0.962124780**, including **$0.00695270** for the fourteen
repairs. Conservative reservations totaled $8.128671950; reservations are not
spending, and token estimates are not provider invoices.

| Model, Dev6 only | Baseline cost | Candidate cost | Baseline cached input | Candidate cached input |
| --- | ---: | ---: | ---: | ---: |
| Luna | $0.12267 | $0.12193 | 39.13% | 39.22% |
| Haiku | $0.18583 | $0.19285 | 47.28% | 47.45% |
| GLM | $0.16878 | $0.16311 | 34.80% | 38.84% |

The fourteen repairs had no cache reads. Across all requests, native usage is
7,723,516 input tokens, 652,872 output tokens and 3,259,342 cached-input tokens
(42.20% of input). Provider reasoning controls retain their established medium
settings; equal effort labels do not imply identical compute.

Thirty-five focused maintained adapter tests and twenty-seven external
run-control/metric tests passed. No maintained package code changed. The previous
full `make fix`/`make check` result remains 4,324 passed, one skipped and the same
three historical Task 06G failures. Independent arithmetic review checked 944
confusion/F1 calculations; seven native audits verified requests, model/schema
identity, exact Luna counts, Haiku estimated counts, GLM conservative allowances,
cache usage, costs and ledgers. Fresh preservation checks verified 31,916 prior
artifact files plus 41 consumed bindings without drift. Final report review,
credential scan, diff check and completion seal are recorded in the result pointer.

These remain development results against synthetic proposed labels, with
correlated variants and provider-specific fixed vectors. Claims were not rerun.
No labels, defaults, reserved/test data, later tasks, commits or pushes changed.
The experiment stops at Dev6 for the user's decision, as requested.

See the [frozen contract](task09e1_glm14_conditions_dev6_v1.md) and
[result pointer](task09e1_glm14_conditions_dev6_result.json) for exact paired IDs,
all per-case metrics, source reviews, native receipts and verification artifacts.
