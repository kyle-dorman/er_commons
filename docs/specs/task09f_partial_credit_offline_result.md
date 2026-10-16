# Task 09F — Offline partial-credit revalidation

Applied the opt-in `task09f.score_rules.partial_credit.v2` validator to all 544
saved GLM outputs from the four Dev6 sampling/format passes. No model calls,
new tokens, cache operations or spending. All predecessor sealed files were
verified unchanged before and after analysis. Original reports remain preserved.

The narrow change allows a model-proposed score 1 with a missing-essential
**or** issue diagnostic. Both empty still fails. Strict JSON, schema, IDs,
source resolution, abstention and score-2 rules remain unchanged. No proposed
numeric score is rewritten, and no score 2 is lowered merely for having issues.
The original default/live validator and prompts remain unchanged; this is an
explicit offline opt-in, not a test of GLM receiving a revised scoring prompt.

## Before and after

Each row uses the same 136 frozen answers and exact saved outputs. Arrows describe
validation-policy effects on full-denominator metrics, not new model performance.

| Saved pass | Correct | Accuracy | Macro-F1 | Valid | Invalid |
| --- | --- | --- | --- | --- | --- |
| sampling_r1 | 109 → 110 | 80.15% → 80.88% | 0.7696 → 0.7745 | 132 → 134 | 4 → 2 |
| sampling_r2 | 108 → 109 | 79.41% → 80.15% | 0.7522 → 0.7579 | 132 → 134 | 4 → 2 |
| format_r1 | 115 → 116 | 84.56% → 85.29% | 0.8186 → 0.8225 | 134 → 136 | 2 → 0 |
| format_r2 | 110 → 112 | 80.88% → 82.35% | 0.7628 → 0.7811 | 134 → 136 | 2 → 0 |

The change recovers eight previously invalid outputs across six unique answers:
five recovered scores match development expectations; three do not. The original
prompt retains two JSON/schema failures per pass. Both format-v2 passes reach
100% coverage, but still have 20 and 24 score disagreements respectively.

## Recovered cases

| Case | Affected saved passes | Saved score / expectation | Interpretation |
| --- | --- | --- | --- |
| C041 F10 | sampling 1 | 1 / 1 | Correct enforcement account plus contradictory construction-pets rule; a plausible supporting defect. |
| C041 F02 | sampling 2, format 2 | 1 / 1 | Misidentifies the monitoring/fine authority, directly relevant to the enforcement question. |
| C041 C04 | format 1, format 2 | 1 / 1 | Unsupported fixed $500 fine; whether this is essential adequacy substance or incidental grounding remains ambiguous. |
| C019 F04 | sampling 1 | 1 / 0 | Invents the magnitude of the central modeled groundwater change; accepting 1 does not resolve the disagreement. |
| C019 F10 | sampling 2 | 1 / 0 | Contradicts the central groundwater direction. |
| C014 F10 | format 1 | 1 / 0 | Contradicts a central future-land-use inclusion component. |

Nonempty issues are mechanically verifiable; their essentiality is not. This
revalidation does not certify the recovered judgments or convert reviewer
interpretations into new human labels. It shows why rejecting every non-omission
score 1 was too restrictive, while preserving the unresolved 0-versus-1 and
incidental-versus-essential boundaries. All passing-control and abstention results
remain unchanged, including the C056 control disagreements.

## Per-question metric changes

Only C041 gains correct outcomes: sampling pass 1 adds one; sampling pass 2 adds
one; format pass 1 adds one; format pass 2 adds two. C019 gains numeric coverage
in both sampling passes without gaining correct answers. C014 gains numeric
coverage in format pass 1 without gaining a correct answer. All other per-question
results remain unchanged; the external report retains full per-question tables.

After revalidation, the fixed format outputs disagree numerically on 6/136
answers (95.59% agreement), with zero validity transitions. They previously
disagreed on 6/133 jointly valid answers. The small percentage change comes only
from recovered denominators, not improved model repeatability. Original-prompt
outputs now disagree on 15/132 jointly valid answers, with four validity
transitions. No new model stability experiment occurred.

## Validation and review

Focused tests cover old-default preservation, the opt-in policy, missing diagnostics,
invalid IDs/types/JSON, and retaining score 2 with incidental issues. Validation passed: 457 focused tests, `make fix`, `make check` (4,468 passed,
one skipped), and `git diff --check`. Independent code/result review verified all
544 outputs and all 3,033 predecessor sealed files. Neither the live prompt nor live validation policy is promoted by this
analysis. Stop for user review before a revised scoring-prompt run or the separate
essentiality experiment. No reserved/test access, commit or push.

[Result pointer](task09f_partial_credit_offline_result.json) binds the preserved
source seal, full offline report and independent review.
