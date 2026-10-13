# Same-prompt GLM Flash and Haiku development result

Haiku completes the planned pass with seven unavailable conclusions. GLM completes all original claims with substantially higher proposal agreement, but its conclusion pass stops on Fireworks HTTP 412. The partial GLM conclusion results cannot establish full-panel superiority. Keep the existing selected configuration; this comparison promotes no package default.

Each provider used the selected simple claims prompt and original visible-review conclusion prompt, its own frozen claim decisions, native medium effort and a 4,096-token output cap. The panel contains 1,056 claims and 430 eligible answers across all 19 development cases: 392 substantive conclusions and 38 clean N/A answers. No reserved/test data, label edits or additional prompt arms. Luna is the preserved historical original arm, not a fresh rerun.

## Same metrics

Values below are pooled class-macro F1, with missing/invalid predictions counted as false negatives for their true class. This is the explicitly defined coverage-aware extension; conventional F1 on valid predictions is reported separately. Neither metric fabricates a negative judgment for a missing response.

| Model | Original claims F1 | Claim review F1 | Conclusion F1 | Numeric score F1 | Numeric coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna (historical) | 93.46% | 96.96% | 92.93% | 88.51% | 350/392 (89.29%) |
| glm | 97.50% | 81.76% | 81.85% | 78.26% | 259/392 (66.07%) |
| haiku | 92.55% | 93.91% | 95.23% | 88.20% | 349/392 (89.03%) |

| Model | Claim correctness / planned | Conclusion correctness / planned | Conclusion coverage | Conditional conclusion F1 | Conditional numeric F1 | Correct N/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna (historical) | 1012/1056 | 370/392 | 392/392 | 92.93% | 93.51% | 38/38 |
| glm | 1037/1056 | 267/392 | 269/392 | 99.05% | 97.67% | 28/38 |
| haiku | 1006/1056 | 374/392 | 385/392 | 96.14% | 93.36% | 38/38 |

Haiku improves conclusion F1 by 2.30 percentage points over Luna, but makes more false acceptances (7 versus 2) while reducing false rejections (4 versus 20). Seven Haiku conclusions are unscored. Its weaker original claims and claim reviews leave final numeric F1 essentially unchanged: 88.20% versus 88.51%, with 326 versus 328 correct numeric scores out of 392. Haiku has 36 unresolved claim/review disagreements plus seven unavailable conclusions.

GLM original claims are 1,037/1,056 correct, versus Luna 1,012/1,056 and Haiku 1,006/1,056. Both new providers have five invalid original claims. GLM conclusion F1 on its 269 valid substantive outputs is 99.05%, but those outputs cover only 68.62% of the intended population; the run order and output failures make this a selected subset. Its full-denominator conclusion F1 is 81.85%. Do not compare 99.05% directly with Luna’s full-panel result.

Full per-class precision/recall/F1, confusion matrices, balanced accuracy, per-case/equal-case results and prior-Dev6/added-13/outside-C041 groups are preserved in the checksummed analysis linked by the result pointer. Proposed synthetic expectations are unchanged; they are not independently calibrated human truth.

## Execution and output failures

Haiku: 1,056 original claims and 425 conclusion calls; 1,051 valid claims and 423 valid conclusions. Five unresolved-source locator violations skip five dependent conclusions. Two conclusion outputs omit a required optional-context claim review. All 38 clean N/A answers are correct.

GLM: 1,056 original claims; 318 conclusion dispatches reserved, including one HTTP 412 with no completed native usage receipt. There are 297 valid conclusion outputs, 20 completed but invalid conclusion outputs, 107 conclusions not dispatched after the stop, and five skipped for invalid claims. Twenty-eight N/A answers were judged correctly; ten were unavailable. The saved error records only HTTP status 412, so the underlying provider cause is not established. No retry or replacement was made.

The initial strict run rejected three surrounding Markdown JSON fences. A reviewed, separately frozen continuation removes exactly one complete outer fence for GLM, then applies unchanged strict JSON/schema validation. It reuses those paid receipts and all other prior calls. No JSON value repair, prompt change or paid duplicate judgment. Other malformed/schema/locator failures remain unscored. The original strict attempts and explicit continuation remain separately inspectable.

## Independent review

Independent arithmetic checks pass for both providers and historical Luna across
all four population groups. Source review covers 15 Haiku answers and 14 GLM
answers, including every false acceptance among valid conclusions. It identifies
useful answer-wide citation corrections, but also missed conditional language,
unsupported peripheral assertions and geography mistakes. Haiku sometimes accepts
a conclusion's main point while excusing an unsupported clause. GLM's C029 F07
review recognizes the missing contingency in a claim but misses the same flaw in
the conclusion. Pet-policy package scope and one queue-comparison inference remain
interpretation-sensitive. No proposed labels were changed.

A separate descriptive check on 264 substantive conclusions valid for all three
providers gives macro-F1 99.04% GLM, 96.18% Haiku and 92.35% Luna. This subset is
selected by completion/validation and uses different provider-owned claim vectors;
it cannot establish a full-panel ranking or isolate conclusion-model quality.

The native audit verifies every completed request, model identity, schema, usage,
allowance, reservation and receipt, with the one HTTP failure explicitly unknown.
All 33 final failed attempts/outputs receive a separate technical review. GLM's
most common conclusion schema issue is adding the conclusion itself (P1) to the
claim-review array, rather than reviewing only the provided claims. This does not
justify silently removing it. Earlier strict JSON-wrapper errors remain preserved.

## Cost, caching and runtime

Native-usage estimates at the dated provider prices (not invoices):

| Provider | Main run cost | Qualification cost | Input cache reads | Claims / conclusions cache reads | Median claims / conclusions latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Haiku 5.5 | $1.07024 | $0.01523 | 62.36% | 70.38% / 50.88% | 3.92s / 4.81s |
| GLM 5.3 Flash, partial | $1.00827 | $0.01122 | 5.88% | 7.96% / 2.35% | 3.71s / 6.84s |

The GLM estimate excludes unknown usage on its rejected HTTP 412 attempt;
its $0.0055529 reservation remains held. Main reservations were $9.94599 Haiku
and $7.77072 GLM, within their $25/$15 caps. No paid duplicate judgments.
Haiku's explicit evidence-prefix cache performs substantially better in this
run. GLM caching is weak despite an exact-repeat qualification cache hit;
this is measured native behavior, not evidence that identical request results
are reusable locally. No billing savings or provider routing behavior is assumed.
Luna's historical pass reused 323 claims, so its incremental cost would not be
a fair fresh-pipeline cost comparison. Latency is per completed request,
including local/counter handling; concurrency was at most four per provider.

## Limits and reproducibility

Medium is the same requested effort label, not equal reasoning compute across vendors. Haiku uses adaptive thinking and native structured output; GLM requires prompt-schema mode to preserve reasoning. Their concatenated semantic prompts and validation schema are unchanged. Haiku uses a qualified explicit evidence cache boundary; GLM uses native implicit caching.

This new exploratory mode uses conservative byte-based input allowances plus Anthropic’s native estimate where available. It does not claim exact preflight token counts. Native usage is checked against those allowances. The old exact-counter paths remain unchanged. One pass does not establish repeatability, calibration or production qualification.

The [frozen comparison contract](task09e1_glm_haiku_full_dev_v1.md) and [continuation contract](task09e1_glm_json_continuation_v1.md) bind provider settings, prompts, input identities, budgets and scripts. Credentials were loaded internally from the local untracked `.env`. Do not rerun a completed launcher: a future experiment needs a fresh namespace and explicit scope; Fireworks also needs its HTTP 412 cause resolved. Offline analysis, metric audit and native audit use no cloud calls.

Validation: focused provider/runtime tests, `make fix`, and `make check` completed. The full suite reports 4,303 passed, one skipped and the same three historical Task 06G failures; no new failures. No commits or pushes.
