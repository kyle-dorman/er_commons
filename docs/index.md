# Docs Index

Start with `AGENTS.md`, then use this page to choose the smallest useful context.

## Current status

**Task 13 is closed with all 180 evaluations complete:** 90 per model across
30 test questions and three fresh answers each. The
[sealed result pointer](specs/task13_result.json) selects the final report and
gallery. Presented benchmark results cover **Luna and Haiku only**.
[Task 13B maintenance](../tasks/sprint2/13b_locked_code_quality.md) is closed.
No task or remote run is active; Tasks 14–15 remain provisional.

The benchmark contains **49 questions: 19 development and 30 test**. Development
and test publications remain separate, as do synthetic judge accuracy and
repeatability. See the [Task 13 outcome](../tasks/sprint2/13_run_locked_test.md)
for coverage, accounting and limitations.

## Next work

Tasks 14–15 require separate activation:

1. [Task 14 — Selective review](../tasks/sprint2/14_selective_failure_review.md):
   bounded diagnosis of the completed frozen test results.
2. [Task 15 — Methods/results](../tasks/sprint2/15_write_methods_and_results.md):
   short writeup of dataset construction, methods, results and limitations.

See [TODO](todo.md) for the actionable queue and
[Sprint 2](sprints/sprint2_brisbane_draft_eir_defense.md) for scope.

## Read for reporting and Task 13

| Need | Authoritative route |
| --- | --- |
| Locked test publication and limitations | [Task 13 outcome](../tasks/sprint2/13_run_locked_test.md), [sealed result pointer](specs/task13_result.json) |
| Reporting code, edits and reuse | [Maintainer guide](reporting_maintainer_guide.md), [Task 12A outcome](../tasks/sprint2/12a_reporting_code_quality.md) |
| Reporting definitions | [Base contract](specs/task12_reporting_v1.md), [pooled presentation](specs/task12_presentation_v2.md), [judge repeatability](specs/task12_judge_repeatability_v3.md), [response-unit/citation counts](specs/task12_response_units_v4.md) |
| Original reporting publication and readiness | [Task 12 outcome](../tasks/sprint2/12_integrate_evaluation_and_reporting.md), [sealed result pointer](specs/task12_result.json); later amendments above supersede historical display/count definitions |
| Accepted target configuration and development results | [11E frozen configuration](specs/task11e_frozen_generation_v1.json), [11E result](specs/task11e_result.json), [11F maintenance](../tasks/sprint2/11f_cleanup_target_generation.md) |
| Frozen judges and existing calibration | [09G freeze](specs/task09g_judge_freeze_v1.json), [judge maintainer guide](judge_maintainer_guide.md) |
| Published questions and prepared evidence | [Question publication](specs/task09f_question_publication_v2_result.json), [Task 10 result](specs/task10_final_result.json), [08H release](specs/task08h_final_result.json) |
| Evidence-only boundary | [Decision 007](decisions/007_evidence_only_first_baseline.md); retrieval remains N/A |

The final test gallery is under `ER_COMMONS_DATA_ROOT` at
`pipelines/brisbane_baylands/task_13/test_30_review/START_HERE.html`.
The separate development gallery is at
`pipelines/brisbane_baylands/task_12/development_19_review/START_HERE.html`.
It contains seven PNG/SVG figures and eleven CSV tables. Provenance and validation
are adjacent to the folder. Source publications and prior presentations are
preserved separately; generated artifacts are not tracked by Git.

## Project documentation

- [Product](product.md): purpose and claim boundaries.
- [Architecture](architecture.md): maintained package and workflow boundaries.
- [Data/artifacts](data_artifacts.md): external storage, provenance and seals.
- [Commands](pipeline_commands.md): maintained entrypoints.
- [Documentation guide](documentation.md): ownership and editing rules.
- [Task contracts](../tasks/README.md): scope, review and closeout requirements.
- [Backlog](backlog.md): unselected future ideas.

## Historical context — read only when needed

Detailed experiment histories belong to task outcomes, not the current queue.

- [Task 13A](../tasks/sprint2/13a_minimax_cloud_comparison.md) is an archived MiniMax
  side experiment. Its code and sealed artifacts are retained for provenance;
  it is excluded from presented benchmark results and further exploration.

- [Task 11 umbrella](../tasks/sprint2/11_build_and_freeze_target_generation.md)
  and [internal findings](../tasks/sprint2/11_prompt_iteration_findings.md) preserve
  prompt comparisons and accepted limitations; Task 11 is fully closed.
- [Task 09 umbrella](../tasks/sprint2/09_build_evaluation_and_qualify_judges.md),
  [09F outcome](specs/task09f_final_result.json) and
  [calibration records](specs/task09f_binary_calibration_review.md) preserve judge
  development. The 09G freeze owns the selected judges.
- [Task 08 umbrella](../tasks/sprint2/08_curate_grouped_benchmark.md),
  [08G topic review](specs/task08g_topic_review_result.json) and
  [08H outcome](../tasks/sprint2/08h_serialize_and_freeze_benchmark.md) own curation
  and release boundaries.
- [Task 07 maintainer guide](task07d_maintainer_guide.md),
  [Task 06H handoff](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
  and [Task 04 runbook](task04_maintainer_runbook.md) route earlier pipeline work.
