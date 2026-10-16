# Haiku small requirement-coverage experiment

**Outcome: do not expand or promote the coverage prompt.** Across three correlated
repetitions, baseline matched 24/54 proposed labels (44.44%, macro-F1 0.4220),
inventory-only 30/54 (55.56%, 0.5038), and coverage 28/54 (51.85%, 0.5010).
Coverage never beats inventory-only accuracy in a matching repetition and introduces
new passing-control failures. Retain the consolidated development default.

Three prompt arms each judged the same 18 selected answers across six questions three times. The fresh baseline and inventory arms are the comparison controls; prior Dev6 results are historical context only.

| Arm / pass | Correct / 18 | Macro-F1 | Numeric coverage | Passing controls | Clean abstentions |
| --- | --- | --- | --- | --- | --- |
| baseline_r1 | 7/18 (38.89%) | 0.3889 | 18/18 | 4/10 | 2/2 |
| inventory_r1 | 10/18 (55.56%) | 0.5056 | 18/18 | 6/10 | 2/2 |
| coverage_r1 | 9/18 (50.00%) | 0.4861 | 18/18 | 5/10 | 2/2 |
| baseline_r2 | 9/18 (50.00%) | 0.4850 | 18/18 | 5/10 | 2/2 |
| inventory_r2 | 9/18 (50.00%) | 0.4777 | 18/18 | 5/10 | 2/2 |
| coverage_r2 | 9/18 (50.00%) | 0.4850 | 18/18 | 5/10 | 2/2 |
| baseline_r3 | 8/18 (44.44%) | 0.3772 | 18/18 | 6/10 | 2/2 |
| inventory_r3 | 11/18 (61.11%) | 0.5101 | 18/18 | 8/10 | 2/2 |
| coverage_r3 | 10/18 (55.56%) | 0.5232 | 18/18 | 6/10 | 2/2 |

Errors below pool three repeated judgments of each selected answer; they are not independent examples.

| Question | Baseline errors / 9 | Inventory errors / 9 | Coverage errors / 9 |
| --- | --- | --- | --- |
| C041 | 6 | 5 | 3 |
| C037 | 4 | 2 | 5 |
| C014 | 3 | 4 | 4 |
| C001 | 7 | 5 | 5 |
| C019 | 5 | 5 | 5 |
| C056 | 5 | 3 | 4 |

## Paired changes and repeatability

- baseline_r1_to_inventory_r1: 8 numeric changes/18 valid pairs; 0 validity changes; 1 new passing-control failures and 3 recoveries.
- baseline_r1_to_coverage_r1: 4 numeric changes/18 valid pairs; 0 validity changes; 0 new passing-control failures and 1 recoveries.
- inventory_r1_to_coverage_r1: 6 numeric changes/18 valid pairs; 0 validity changes; 2 new passing-control failures and 1 recoveries.
- baseline_r2_to_inventory_r2: 9 numeric changes/18 valid pairs; 0 validity changes; 3 new passing-control failures and 3 recoveries.
- baseline_r2_to_coverage_r2: 6 numeric changes/18 valid pairs; 0 validity changes; 2 new passing-control failures and 2 recoveries.
- inventory_r2_to_coverage_r2: 5 numeric changes/18 valid pairs; 0 validity changes; 1 new passing-control failures and 1 recoveries.
- baseline_r3_to_inventory_r3: 4 numeric changes/18 valid pairs; 0 validity changes; 0 new passing-control failures and 2 recoveries.
- baseline_r3_to_coverage_r3: 4 numeric changes/18 valid pairs; 0 validity changes; 1 new passing-control failures and 1 recoveries.
- inventory_r3_to_coverage_r3: 4 numeric changes/18 valid pairs; 0 validity changes; 2 new passing-control failures and 0 recoveries.

All-three-pass score agreement is 14/18 answers for baseline and 11/18 for each
inventory condition.

Within-arm repeat comparisons are shown separately; each compares the same 18 answers.

- baseline_r1_to_baseline_r2: 2 numeric changes/18 valid pairs; 0 validity changes.
- baseline_r1_to_baseline_r3: 3 numeric changes/18 valid pairs; 0 validity changes.
- baseline_r2_to_baseline_r3: 3 numeric changes/18 valid pairs; 0 validity changes.
- inventory_r1_to_inventory_r2: 5 numeric changes/18 valid pairs; 0 validity changes.
- inventory_r1_to_inventory_r3: 5 numeric changes/18 valid pairs; 0 validity changes.
- inventory_r2_to_inventory_r3: 4 numeric changes/18 valid pairs; 0 validity changes.
- coverage_r1_to_coverage_r2: 6 numeric changes/18 valid pairs; 0 validity changes.
- coverage_r1_to_coverage_r3: 5 numeric changes/18 valid pairs; 0 validity changes.
- coverage_r2_to_coverage_r3: 3 numeric changes/18 valid pairs; 0 validity changes.

## Qualitative findings

Review covered all 18 answers, all 54 coverage judgments and the 108 matching
baseline/inventory judgments. Coverage recognizes C001 O04's supporting threshold
comparison in every pass, but still gives only 1 because the conclusion is implicit.
False omissions remain: C001 C01 in passes 2/3 and C001 F07 in passes 1/2 deny
numerical substance present in their supporting points. C056 O04 receives 0 in
all coverage passes despite a quoted statement of residual flooding risk.

The coverage map is not guaranteed to reflect the candidate faithfully. C001 F07
pass 2 attributes a source passage to the candidate, C037 C02 pass 3 uses a wrong
point ID, and C041 C01 pass 1 presents a purpose paraphrase as an exact quote.
Literal mismatches vary in severity; none was converted into a new score or parser
failure. These observations explain why visible structure alone is insufficient.
Exact candidate text, quotations, receipts and review limitations remain external.

## Output observations and accounting

Invalid outputs remain non-scores and count as errors. Inventory/coverage markers are checked heuristically, separately from strict validity; markers do not prove that requirements or evidence links are correct.

- inventory_r1: Requirements 18/18, Coverage 0/18, Verdict 18/18; strict valid 18/18.
- coverage_r1: Requirements 18/18, Coverage 16/18, Verdict 16/18; strict valid 18/18.
- inventory_r2: Requirements 18/18, Coverage 0/18, Verdict 18/18; strict valid 18/18.
- coverage_r2: Requirements 18/18, Coverage 15/18, Verdict 15/18; strict valid 18/18.
- inventory_r3: Requirements 18/18, Coverage 0/18, Verdict 18/18; strict valid 18/18.
- coverage_r3: Requirements 18/18, Coverage 16/18, Verdict 16/18; strict valid 18/18.

Postrun inspection clarifies the seven apparent Coverage/Verdict marker misses:
all seven actually contain both sections, but omit the literal pipe before
`Verdict:`. All 54 coverage outputs contain the requested sections. These seven
end normally (`end_turn`) at 540–2,234 output tokens; there is no truncation or
strict-validation failure. The counts above preserve the original literal-format
heuristic, not an assertion that the content is absent.

Candidate quote and point-ID checks are also heuristic: only adjacent ID/quote pairs receive direct-link checks. Other links remain unverified, not invalid; literal matches do not prove that no requirement was omitted.

- coverage_r1: 33/36 detected quotes appear somewhere in candidate points; 18/19 parseable direct links match a claimed point.
- coverage_r2: 31/34 detected quotes appear somewhere in candidate points; 22/24 parseable direct links match a claimed point.
- coverage_r3: 39/40 detected quotes appear somewhere in candidate points; 24/25 parseable direct links match a claimed point.

Native-token estimated cost: **USD 0.266243960**; actual billing unknown. Native cache reads: 2,503,131/3,576,699 input tokens (69.98%). 162 generations and 162 estimated-count requests; no retries.

Caps held: USD 12.00, 162 generations, 663,552 output tokens, 1,800 execution seconds, 324 total HTTP requests. Execution took 1,165.84 seconds (19.4 minutes).

Per-answer rationales, coverage text, failures, token usage and latency remain in the external report. This targeted small panel and three repeats do not establish general accuracy; synthetic labels are not independent human calibration. All arms share the same model settings, schema and whole-answer score rules. The coverage intervention adds rationale text; candidate visibility and output-length effects remain limitations.

**Stop for user review. No automatic promotion or additional inference.**

External report: `/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f_20261013_haiku_coverage_small_v1/report.json`

Independent review verified every native request/response binding, strict output,
count response, metric and cap. All 8,395 checked prior sealed files remain intact.
Validation: 386 focused tests; make fix; make check (4,512 passed, one skipped);
and git diff --check. No dataset expansion, score changes, commit or push.
