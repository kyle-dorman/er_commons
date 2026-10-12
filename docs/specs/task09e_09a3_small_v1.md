# Task 09E — Combined 09A.3 development rerun

Status: completed small-model Dev6; user review checkpoint, October 11, 2026.

## Dataset and question membership

The user explicitly selected every comparison-eligible answer in the combined
[09A.3 publication](task09a3_final_result.json), replacing the prior four-answer
selection for this experiment. Preserve all historical 09E panels and results.
Use combined answers.jsonl and separate expectations.jsonl, filtering strictly on
comparison_eligible. The publication contains 442 answers / 430 eligible, 38 clean
abstentions, and 12 unchanged review exclusions. These are new development publication
counts; the original 423 development / 118 reserved / five-exclusion lineage remains sealed.
The approved 19 development / 30 test question split is unchanged.

Dev3 remains C041/C037/C014: 22/27/20 eligible answers, 69 total, 6 clean abstentions,
166 non-conclusion points. Dev6 adds C001/C019/C056: 23/22/22 eligible answers,
67 additional answers and 157 points. Dev6 therefore contains 136 answers, 12 clean
abstentions and 323 points. No controls outside combined answers.jsonl are added.
Freeze the entire six-question manifest before inference; retain exact Dev3 packets,
answers and results in the Dev6 union. Do not consume regenerated records elsewhere.

## Provenance and isolation

Verify result-pointer hashes and sealed publication inventories. Resolve each
record's provenance bindings using record_origins.jsonl and its correct original
artifact root. Inherited coverage/development_slots describe the original batch;
supplement_slots describes additions. Reuse verified development case inputs and
existing evidence-packet construction. Do not decode mixed-split question containers,
reserved answers or test questions/references. Keep expected labels, reasons,
reference answers and automatic metrics outside native judge requests.

## Execution and comparison

Keep Qwen3.5 0.8B F16, 49,152 context, 3,000 output allowance and current prompts fixed:
answer_abstention.v1, point_support.v2, conclusion_review.v1. Inspect owns execution,
logs, sample records and aggregation. Run the full staged pipeline with the initial
abstention gate. Clean abstention skips further judging; ambiguous/invalid gates
remain unresolved/failures. Invalid point predictions skip conclusion review.
Keep exact model-specific request counting and runtime parity checks; missing
local assets block dispatch without downloads. No target generation or prompt edits.

Run Dev3, reflect on stage metrics and source-linked disagreements, then run only
the three added questions. Dev6 aggregation combines the preserved Dev3 results
with the incremental run, without rerunning Dev3. Stop after small-model Dev6 or
an operational blocker. No larger model, full-19, later tasks, commits or pushes.

Stage-level agreement/confusion and coverage must have explicit eligible and
validated-prediction denominators. Invalid outputs are not unsupported labels.
Abstention, point support, conclusion support and final score are separate.
Report raw flags only as diagnostics. All agreement is with proposed expectations.
Because the answer population changed, differences from the old panel are
observational; they cannot establish a causal prompt or model improvement.

Fresh namespace: task_09/09e_20261011_09a3_small_v1/. Preserve source bindings,
packet manifest, prompts/settings, exact preflights, native outputs, Inspect logs,
Dev3 reflection, combined diagnostics, independent review and completion inventory.
Run focused tests, make fix, make check and git diff --check. Independent review
checks provenance, isolation, aggregation and representative disagreements.


## Outcome

All 136 selected answers ran with the frozen model, prompts and 3,000-token output
allowance. Dev3 completed first; its reflection preceded the 67-answer addition.
Inspect combined the exact preserved records without another model call.

| Diagnostic | Dev3 | Dev6, including Dev3 |
| --- | ---: | ---: |
| Answers | 69 | 136 |
| Valid numeric scores, all zero | 11 | 30 |
| Numeric proposal matches / comparable scores | 0/11 | 12/29 |
| Valid point predictions / eligible points | 72/166 | 142/323 |
| Predicted supported points | 0 | 0 |
| Proposed-supported points rejected | 56 | 99 |
| Recognized clean abstentions / actual proposed clean | 3/6 | 6/12 |
| Substantive answers incorrectly exempted | 7 | 15 |
| Output failures | 41 | 75 |
| Ambiguous abstention / point-conclusion disagreement | 6/1 | 9/1 |

Dev6's remaining outcomes are 21 N/A classifications (6 proposed clean, 15 false
exemptions), 73 schema failures, two output limits, nine ambiguous gates and one
unresolved disagreement. One clean abstention was incorrectly treated as substantive
and scored zero; five were ambiguous. Thus final N/A agreement among only completed
clean cases (6/7) must not replace clean-abstention recognition over all twelve (6/12).

Point diagnostics have 43/142 proposal agreements and 99/142 false rejections
against proposed labels. All 142 validated predictions are false; 133 other point
calls failed validation, and 48 points were skipped by the gate. Of 275 point calls,
274 raw boolean flags were false and one output was unparseable. Invalid outputs
remain failures. Conclusion diagnostics cover 30/124 eligible proposals, with
13/30 agreements; the clean-abstention conclusion has no comparable support label.
Final numeric agreement is 12/29 (41.4%), with 34.4% question-balanced agreement.
Thirty numeric scores include the one incorrect numeric score for clean abstention.

The added cases produce more correct zero scores, but this does not demonstrate
better discrimination: all numeric scores and all validated point-stage predictions remain
negative. Earlier point v2 also accepted zero points. The broader answer population
is different, so changed percentages cannot establish a causal improvement.
Generated expectations remain diagnostic proposals, not calibrated accuracy.

## Source-linked review

- C041: association monitoring is explicit in `deir_appendix_a/sec000433`, yet
  supported points are rejected. Literal excerpt failures remain separate.
- C037: `deir_main/tbl000142` supports the 16.92-to-21.20-acre statement; the point
  stage rejects it while admitting the numbers. Conclusion review reverses that
  point judgment, correctly producing an unresolved disagreement.
- C019: `deir_appendix_k3/sec000820` supports the conclusion about lower landfill
  groundwater despite sea-level rise. The conclusion stage instead repeats a
  defect in a different point. `deir_appendix_l/sec000024` also directly supports
  the barrier function that one point judgment rejects.
- C056: one rejection reverses a "does not identify" baseline qualification.
  Other missing/wrong-citation rejections are justified, although explanations can
  still confuse the target point or omit an unsupported assertion.
- C001: qualified factual answers are incorrectly exempted by the gate. Conversely,
  "I won’t offer a rationale for the cumulative health-risk finding" is classified
  substantive and scored against the question's proposition. A source review
  confirms an actual unsupported exclusion claim is correctly rejected using
  `deir_main/sec002530`; correct zero scores coexist with the broader failures.

The external reviews preserve exact sample IDs, cited evidence and model outputs.
No proposal was changed to match a prediction.

## Execution and review checkpoint

Inspect recorded 447 native calls: 136 abstention, 275 point and 36 conclusion.
Every request passed exact preflight/native token parity and comparison with its
label-free projection. There were no retries, runtime errors or context failures.
Usage was 1,407,570 input and 152,099 output tokens; summed sample execution was
2,429.98 seconds (40.5 minutes). Owned runtime processes stopped after execution.
All 8,409 preserved Dev3 file hashes and all twelve implementation bindings passed
final verification. Independent recomputation matches Inspect stage diagnostics.

The dataset adapter and stage diagnostics improve traceability and measurement;
they do not improve this model's semantic behavior. Keep the model unqualified and
stop for user review. A stronger-model comparison with this unchanged pipeline is
a possible next experiment, requiring explicit authorization. No 9B, full-19,
reserved/test evaluation, later-task work, downloads, commits or pushes occurred.


Validation: 115 focused tests passed. `make fix` passed with 965 files unchanged.
`make check` passed formatting, lint and types, then reported 3,912 passed, one
skipped and only the same three historical Task 06G failures. `git diff --check`
passed. Independent code and final-result review found no implementation blocker;
source reviews preserve the semantic limitations above.
