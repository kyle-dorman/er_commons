# Haiku question-requirement inventory experiment

**Outcome: retain the consolidated baseline.** The first-pass accuracy gain reversed
on the second pass; both arms total 214/272 correct (78.68%), while repeated-score
changes increase from 14/136 to 24/136 with the inventory. This is a negative
development result, not evidence for adopting the inventory prompt.

Completed the fixed Dev6 comparison: 136 answers, two passes per arm. The inventory remains in the same judgment call; the schema and scoring rules are unchanged.

| Arm / pass | Correct / 136 | Macro-F1 | Numeric coverage | Passing controls | Clean abstentions |
| --- | --- | --- | --- | --- | --- |
| baseline_r1 | 106/136 (77.94%) | 0.7620 | 136/136 | 48/62 | 12/12 |
| inventory_r1 | 110/136 (80.88%) | 0.7854 | 136/136 | 51/62 | 12/12 |
| baseline_r2 | 108/136 (79.41%) | 0.7625 | 136/136 | 54/62 | 12/12 |
| inventory_r2 | 104/136 (76.47%) | 0.7362 | 136/136 | 49/62 | 12/12 |

Invalid outputs remain non-scores and count as incorrect in full-denominator metrics.

| Question | Baseline 1 errors | Inventory 1 errors | Baseline 2 errors | Inventory 2 errors |
| --- | --- | --- | --- | --- |
| C041 | 3 | 4 | 4 | 5 |
| C037 | 7 | 4 | 4 | 6 |
| C014 | 2 | 3 | 3 | 5 |
| C001 | 7 | 7 | 7 | 8 |
| C019 | 6 | 4 | 6 | 4 |
| C056 | 5 | 4 | 4 | 4 |

## Paired changes and repeatability

- baseline_r1_to_inventory_r1: 24 numeric changes among 136 valid pairs; 0 validity changes. Passing controls: 4 new failures and 7 recoveries.
- baseline_r2_to_inventory_r2: 26 numeric changes among 136 valid pairs; 0 validity changes. Passing controls: 8 new failures and 3 recoveries.
- baseline_r1_to_baseline_r2: 14 numeric changes among 136 valid pairs; 0 validity changes. Passing controls: 1 new failures and 7 recoveries.
- inventory_r1_to_inventory_r2: 24 numeric changes among 136 valid pairs; 0 validity changes. Passing controls: 8 new failures and 6 recoveries.

## Inventory observability

The following is a literal-format heuristic, separate from strict output validity. It checks section markers, numbering, quoted question spans and an essentiality phrase; it does not certify that requirements are correct, complete, stable or independent of the candidate.

- inventory_r1: 133/136 pass all observable checks; 136 are strictly valid outputs.
- inventory_r2: 132/136 pass all observable checks; 136 are strictly valid outputs.

Per-answer rationales, extracted inventories, failures and paired control changes are preserved in the external report for qualitative review.

## Qualitative findings

The inventory can name a correct requirement without evaluating the complete answer.
For C001 O04, both inventory passes state that the candidate only contains a
placeholder and lacks a threshold comparison. In fact, supporting points P2/P3
explicitly provide cumulative thresholds, the positive 5.0-per-million increment,
86.3 below 100 per million, and buildout nonexceedances. Baseline gives 1; inventory
gives 0 in both passes. This is observed whole-answer assessment failure, not a
missing inventory item. It does not establish why the model ignored the content.

The bounded review also examines changing optional pet-policy and construction-duration
requirements, improvements and regressions. Exact selected cases, source-linked
observations and limits are preserved in the separate qualitative review artifact.
No model scores or development labels were changed.

## Accounting and limits

Estimated native-token cost: **USD 0.532872400**. Actual billing remains unknown. Generation calls: 544; estimated-count calls: 544. Native cache reads: 10,638,100/11,570,316 input tokens (91.94%).

Shared caps: USD 32.00, 544 generations, 2,228,224 output tokens and 4,800 execution seconds. The separate counter and total HTTP limits also held. Execution took 3,586.50 seconds
(59.8 minutes), without retries. Inventory output tokens increased 55.9% and its
estimated cost increased 30.6% relative to baseline across the paired repetitions.

Six correlated synthetic question families and two repeats provide development evidence, not human calibration or judge qualification. The rationale intervention changes output length as well as instructions. Textual inventory differences are not proof of semantic drift. The candidate remains visible in the same call.

**Stop for user review. No automatic promotion, additional tuning, expanded dataset, coverage-map experiment or separate candidate-blind call.**

External report: `/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f_20261013_haiku_requirements_v1/report.json`

Independent postrun review verified all 544 native request/response bindings,
strict results, counts, paired metrics, costs and caps. All 5,365 checked prior
sealed files remain unchanged. Offline validation passed 386 focused tests,
make fix, make check (4,512 passed, one skipped) and git diff --check.
