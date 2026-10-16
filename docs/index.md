# Docs Index

Start with `AGENTS.md`, then use this page to choose the smallest useful set of
project docs.

## Current status

**09F and 09F.1 are complete, including production cleanup.** Kyle selected
Luna for A v2, G v3 and C v8, and Haiku for S v6.
[09F.2](../tasks/sprint2/09f2_cleanup_production_judges.md) consolidated native
Inspect execution and retired exploratory runtimes while retaining Fireworks/GLM
and Ollama diagnostics. [09G](../tasks/sprint2/09g_challenge_and_freeze_judges.md)
is next. The [production guide](judge_maintainer_guide.md) owns current use.

Current evidence and selections: [C/S](specs/task09f_final_result.json),
[A](specs/task09f1_a_inspect_handoff.md), [G](specs/task09f1_point_grounding_handoff.md).
Full-development labels remain reviewed proposals; no held-out qualification is
claimed. [Task 12](../tasks/sprint2/12_integrate_evaluation_and_reporting.md) owns
whole-answer routing and combined reporting. Historical runs remain immutable.

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
[09E](../tasks/sprint2/09e_implement_grounding_judge.md) and
[09E.1](../tasks/sprint2/09e1_compare_cloud_and_decision_judges.md) are complete, preserving the
local/cloud judge development results. The user selects GLM Flash with the simple
claims prompt, original conclusion semantics and empty-review clarification.
The [latest comparison](specs/task09e1_glm14_conditions_dev6_result.md) records
results and limitations; this development selection is not judge qualification.
Luna and Haiku remain cloud alternatives; Ollama/Qwen remains for local code-path
checks. Clef execution is retired, with its historical evidence preserved.

**[09E.2 — Judge code cleanup](../tasks/sprint2/09e2_cleanup_grounding_judges.md) is complete.**
This covers both inherited 09E and current 09E.1 code. See the
[judge maintainer guide](grounding_judge_guide.md) for maintained interfaces.
No model inference, label changes or reserved/test access belongs to this cleanup.
The [09F adequacy judge](../tasks/sprint2/09f_implement_adequacy_judge.md) is complete, including 09F.2 cleanup.
Its [final handoff](specs/task09f_final_result.json) selects Luna C v8 / Haiku S v6;
the task preserves earlier experiments and superseded whole-answer work.

The latest development synthetic dataset is the [09A.3 additive publication](specs/task09a3_final_result.json):
442 answers / 430 eligible, including two clean abstentions per question. It
preserves all 09A.2 records and exclusions; [the outcome](../tasks/sprint2/09a3_add_clean_abstentions.md)
explains publication and provenance boundaries. No judge ran for this supplement.

The [published support synthesis](specs/task09f_support_synthesis_result.json)
contains 490 independently reviewed proposed labels, with 471 eligible for paired
reference-visibility comparisons. The [calibration panels](specs/task09f_binary_calibration_review.md)
now select from both published component datasets. The combined prompt comparison is complete; the selected pair is recorded in the final handoff above.

## Read for Task 09

The [production judge guide](judge_maintainer_guide.md) owns current A/G/S/C
interfaces, shared provider configuration and offline historical replay.

1. [Task 09 umbrella](../tasks/sprint2/09_build_evaluation_and_qualify_judges.md),
   then [09A synthetic challenges](../tasks/sprint2/09a_create_synthetic_challenges.md).
   The umbrella links all seven contracts; do not read every historical task.
2. [08H release pointer](specs/task08h_final_result.json) and
   [08H outcome](../tasks/sprint2/08h_serialize_and_freeze_benchmark.md) for exact
   source/case/split identities and target/reference separation.
3. [Decision 006](decisions/006_structured_answers_four_part_evaluation.md) and the
   [sprint evaluation boundary](sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
   for the authoritative four results and judge visibility. The
   [remaining sequence](sprints/sprint2_brisbane_draft_eir_defense.md#remaining-task-sequence)
   keeps core judge work in 09 and later integration in 12.
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
  Task 09 judge development and Task 12 integration; the sprint plan owns
  the evaluation contract.
- [Grounding experiment record](grounding_experiment_record.md): consolidated
  09E/09E.1 techniques, successful and negative results, decisions and evidence.
- [`tasks/`](../tasks/): detailed task contracts, validation, and outcomes.

## Reading rule

Use the next task's inputs and the document roles above. Read a completed task
only when its outcome or preserved evidence is an explicit input.
