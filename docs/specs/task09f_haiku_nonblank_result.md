# Task 09F — Haiku nonblank-diagnostic experiment

Compared the unchanged aligned prompt with three formatting revisions on five frozen C014
answers, five repeats per arm. The target is F05; diagnostic controls are F04, F10, P01 and R01.
Schema, parser, rubric, model and adaptive medium settings stayed fixed. No retries or score overrides.

| Arm | Valid / 25 | Blank explanations | Target valid / 5 | Accuracy | Macro-F1 |
| --- | --- | --- | --- | --- | --- |
| a_nonblank | 25/25 | 0 | 5/5 | 64.00% | 0.6508 |
| b_consolidated | 25/25 | 0 | 5/5 | 80.00% | 0.8222 |
| baseline | 25/25 | 0 | 5/5 | 64.00% | 0.6508 |
| c_issue_example | 25/25 | 0 | 5/5 | 72.00% | 0.7319 |

**Primary outcome:** All arms, including baseline, were valid. The original failure did not reproduce; this cannot establish a repair advantage.

Baseline is unchanged; A adds a nonblank reminder; B consolidates overlapping output instructions;
C adds a populated issue example. Numeric disagreements remain separate from formatting validity.

## Per-answer outcomes

Histograms are `score: count`; invalid is a non-score. Each cell summarizes five fresh requests.

| Answer / expected | Baseline | A: nonblank | B: consolidated | C: issue example |
| --- | --- | --- | --- | --- |
| C014 F05 / 1 | 1: 5 | 1: 3, 2: 2 | 1: 5 | 1: 5 |
| C014 F04 / 1 | 1: 1, 2: 4 | 1: 3, 2: 2 | 1: 5 | 1: 3, 2: 2 |
| C014 F10 / 0 | 1: 5 | 1: 5 | 1: 5 | 1: 5 |
| C014 P01 / 2 | 2: 5 | 2: 5 | 2: 5 | 2: 5 |
| C014 R01 / 0 | 0: 5 | 0: 5 | 0: 5 | 0: 5 |

## Caching, cost and limits

| Arm | Estimated USD | Cache read fraction | Median call latency |
| --- | --- | --- | --- |
| a_nonblank | $0.032001 | 95.13% | 6.4s |
| b_consolidated | $0.031273 | 95.12% | 4.7s |
| baseline | $0.029467 | 95.13% | 4.4s |
| c_issue_example | $0.030102 | 95.14% | 6.0s |

Total: 100 generation requests, 100 saved count responses, $0.122843 estimated cost and 509.5s elapsed. Costs use native token usage and dated rates; billed invoices remain unknown.

Fixed caps: $10, 100 generation requests, 100 count requests, 409,600 output tokens and
1,200 seconds. Unknown counters remain unknown in the full report.

This targeted sample is not Dev6 qualification. Five repeated answers are not 25 independent cases.
No failure reproduction or no invalids across arms is insufficient proof that a revision fixes the original issue.
Strict errors, blank-field locations, full diagnostics and receipt paths remain in the external report.

The consolidated contract is the most promising candidate here: it is shorter, states
the nonblank requirement directly and returned identical scores across repeats of each
answer. Its 80% agreement is a secondary observation, not proof of general superiority.
The earlier successful formatting instructions remain retained; valid incorrect scores
do not automatically veto formatting changes. No new default is promoted from this
non-reproducing trial. Stop for review before broader testing or other experiments.

Validation passed: 393 focused tests, make fix, make check (4,503 passed, one skipped),
git diff --check and independent preflight/report/post-run review. All 4,760 files
sealed by the preceding comparison remain unchanged. No commit or push.

[Result pointer](task09f_haiku_nonblank_result.json) binds prompts, outcomes and accounting.
