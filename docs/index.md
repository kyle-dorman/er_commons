# Docs Index

Start with `AGENTS.md`, then use this page to choose the smallest useful set of
project docs.

## Current status

**Task 09 is complete with documented limitations.** The
[09G documentation freeze](../tasks/sprint2/09g_challenge_and_freeze_judges.md)
binds Luna A v2 / G v3 / C v8 and Haiku S v6, existing comparisons and the cleaned
native Inspect implementation. No additional model run or reserved-set check was
performed. The [freeze manifest](specs/task09g_judge_freeze_v1.json) owns exact
identities; the [production guide](judge_maintainer_guide.md) owns current use.

**Task 10 evidence-only inputs are prepared for all 49 cases.** The
[result pointer](specs/task10_final_result.json) binds the 19-development/30-test
publication, canonical citation maps and validation. **[Task 11A panel selection](../tasks/sprint2/11a_select_development_panels.md) is complete.**
**[11B](../tasks/sprint2/11b_build_luna_generation.md) is complete:** the bounded
three-case Luna smoke produced valid candidates and delivery receipts; the
[result pointer](specs/task11b_final_result.json) records validation and limitations.
**[11C](../tasks/sprint2/11c_integrate_development_evaluation.md) is complete:**
saved-candidate automatic checks and frozen A/G/S/C reports replay without calls;
see the [result](specs/task11c_final_result.json) for semantic failures and accounting limits.
The [11C.1 cleanup](../tasks/sprint2/11c1_cleanup_development_evaluation.md) documents
the maintained module boundaries and unchanged-output verification.
Next: refresh [11D](../tasks/sprint2/11d_iterate_development_prompt.md) before any
prompt iteration under the [Luna generation plan](../tasks/sprint2/11_build_and_freeze_target_generation.md):
three then six questions for prompt iteration, followed by all 19 development cases. Retrieval remains
deferred under [Decision 007](decisions/007_evidence_only_first_baseline.md).
[Task 12](../tasks/sprint2/12_integrate_evaluation_and_reporting.md) finalizes combined reporting and locked-test readiness using Task 11C whole-answer evaluation for prompt iteration. No model run or end-to-end qualification is
claimed by input preparation.

The current [question publication](specs/task09f_question_publication_v2_result.json)
contains 49 cases with the unchanged 19-development/30-test split. See
[adequacy rules](specs/adequacy_labeling_rules.md),
[no-answer rules](specs/no_answer_labeling_rules.md), and
[grounding rules](specs/grounding_labeling_rules.md) for the component semantics.

Sprint 2: Tasks 02–08 are complete. The [08H release](specs/task08h_final_result.json)
freezes **49 approved cases: 19 development / 30 test**. The
[08H outcome](../tasks/sprint2/08h_serialize_and_freeze_benchmark.md) owns source,
role-separation and validation limits; [08G](specs/task08g_topic_review_result.json)
owns accepted topic balancing and shared-evidence overlap. Historical artifacts
remain preserved.

[09A](../tasks/sprint2/09a_create_synthetic_challenges.md) is complete: all 19
development cases, 546 synthetic variants and a reserved final-check subset are
sealed in the [09A handoff](specs/task09a_final_result.json). [09B is complete](../tasks/sprint2/09b_choose_harness_and_qualify_local_judge.md)
with an Inspect/Ollama integration, a measured model comparison and explicit
semantic limitations. [Its result](specs/task09b_final_result.json) recommends
Qwen 9B F16 at 48K for judge development and Qwen 0.8B for fast integration
smoke checks. [09C is complete](../tasks/sprint2/09c_build_judge_evidence_packets.md)
with separate deterministic evidence packets and explicit context diagnostics;
[its result](specs/task09c_final_result.json) records offline validation and the
remaining exact-token-counter requirement. [09D is complete](../tasks/sprint2/09d_implement_automatic_metrics.md) with offline
Inspect metrics, canonical-ID matching and an explicit Task 10 receipt contract;
[its result](specs/task09d_final_result.json) records fixture validation and limits.
[09E/09E.1](../tasks/sprint2/09e1_compare_cloud_and_decision_judges.md) and
[09E.2](../tasks/sprint2/09e2_cleanup_grounding_judges.md) preserve historical
experiments. Their former GLM default and retired runners are superseded by
[09F](specs/task09f_final_result.json), [A](specs/task09f1_a_inspect_handoff.md),
[G](specs/task09f1_point_grounding_handoff.md) and
[09F.2 cleanup](../tasks/sprint2/09f2_cleanup_production_judges.md).

The latest development synthetic dataset is the [09A.3 additive publication](specs/task09a3_final_result.json):
442 answers / 430 eligible, including two clean abstentions per question. It
preserves all 09A.2 records and exclusions; [the outcome](../tasks/sprint2/09a3_add_clean_abstentions.md)
explains publication and provenance boundaries. No judge ran for this supplement.

The [published support synthesis](specs/task09f_support_synthesis_result.json)
contains 490 independently reviewed proposed labels, with 471 eligible for paired
reference-visibility comparisons. The [calibration panels](specs/task09f_binary_calibration_review.md)
now select from both published component datasets. The combined prompt comparison is complete; the selected pair is recorded in the final handoff above.

## Read for Task 11

Start with the [Task 11 umbrella](../tasks/sprint2/11_build_and_freeze_target_generation.md)
and completed [11A](../tasks/sprint2/11a_select_development_panels.md), including its
[fixed panels](specs/task11a_development_panels_v1.json) and
[criteria/budgets](specs/task11a_panel_protocol.md). Read the completed [11B outcome](../tasks/sprint2/11b_build_luna_generation.md) and
[result pointer](specs/task11b_final_result.json) next, then the completed
[11C outcome](../tasks/sprint2/11c_integrate_development_evaluation.md) and
[result](specs/task11c_final_result.json). Subtasks 11D–11E remain provisional;
refresh each from its predecessor before execution. 11D has not begun.

## Task 10 handoff

Start with [Task 10](../tasks/sprint2/10_prepare_evidence_only_inputs.md) and its
explicit inputs. It is one preparation task with no subtasks or model runs.

## Task 09 handoff references

The [production judge guide](judge_maintainer_guide.md) owns current A/G/S/C
interfaces, shared provider configuration and offline historical replay.

1. [Task 09 umbrella](../tasks/sprint2/09_build_evaluation_and_qualify_judges.md),
   then [09A synthetic challenges](../tasks/sprint2/09a_create_synthetic_challenges.md).
   The umbrella links completed component records; do not read every historical task.
2. [08H release pointer](specs/task08h_final_result.json) and
   [08H outcome](../tasks/sprint2/08h_serialize_and_freeze_benchmark.md) for exact
   source/case/split identities and target/reference separation.
3. [Decision 006](decisions/006_structured_answers_four_part_evaluation.md) and the
   [sprint evaluation boundary](sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
   for the authoritative four results and judge visibility. The
   [remaining sequence](sprints/sprint2_brisbane_draft_eir_defense.md#remaining-task-sequence)
   keeps core judge work in 09 and initial integration in 11C and final reporting in 12.
4. [Architecture](architecture.md) and [artifact contract](data_artifacts.md)
   before implementation; [task shape](../tasks/README.md) and
   [documentation guide](documentation.md) for contract changes.

## Historical entry points

- [Task 08 umbrella](../tasks/sprint2/08_curate_grouped_benchmark.md) and
  [08F result](specs/task08f_combined_review_result.json) for authoring approvals.
- [Task 07 umbrella](../tasks/sprint2/07_pilot_reference_case_authoring.md),
  [07E result](specs/task07e_final_result.json), and
  [07D maintainer guide](task07d_maintainer_guide.md) for pilot/replay evidence.
- [Current response inventory](specs/task07a1_final_result.json),
  [06H handoff](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md), and
  [05H summary](specs/task05h_final_summary.md) for upstream review limits.
- [Human review process](response_comment_human_review_process.md) for historical
  authoring workflow, not an additional Task 09 labeling requirement.

## Document roles

- [`docs/product.md`](product.md): project purpose, scope, claim boundaries,
  and success criteria.
- [`docs/architecture.md`](architecture.md): maintained package, CLI, pipeline,
  and configuration boundaries.
- [`docs/data_artifacts.md`](data_artifacts.md): external root, artifact layout,
  Git policy, and provenance requirements.
- [`docs/sprints/`](sprints/): accepted sprint scope and sequencing.
- [`docs/decisions/`](decisions/): durable accepted choices and non-promoted
  results.
- [`docs/pipeline_commands.md`](pipeline_commands.md): maintained workflow commands.
- [`docs/task04_maintainer_runbook.md`](task04_maintainer_runbook.md): first-pass
  review maintenance and the Task 04A transition boundary.
- [`docs/documentation.md`](documentation.md): documentation ownership and
  editing rules.
- [`docs/todo.md`](todo.md): current queue and next action.
- [`docs/backlog.md`](backlog.md): unselected future ideas only.
- [LLM judge learning notes](llm_judge_learning_notes.md): supporting checks for
  Task 09 judge development, Task 11C integration and Task 12 reporting; the sprint plan owns
  the evaluation contract.
- [Grounding experiment record](grounding_experiment_record.md): consolidated
  09E/09E.1 techniques, successful and negative results, decisions and evidence.
- [`tasks/`](../tasks/): detailed task contracts, validation, and outcomes.

## Reading rule

Use the next task's inputs and the document roles above. Read a completed task
only when its outcome or preserved evidence is an explicit input.
