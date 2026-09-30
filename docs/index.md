# Docs Index

Start with `AGENTS.md`, then use this page to choose the smallest useful set of
project docs.

## Current status

Sprint 2 is active. Tasks 02–06 are complete, including the repaired
[Task 06H handoff](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
and the preserved [Task 05H response inventory](specs/task05h_final_result.json).
The [05H summary](specs/task05h_final_summary.md) owns review coverage and
inherited limits. The [Task 07 umbrella](../tasks/sprint2/07_pilot_reference_case_authoring.md)
is closed, with six approved reference answers and a recorded Task 08 handoff. The
[07A sample](../tasks/sprint2/07a_screen_pilot_candidates.md#sampling-outcome)
contains 50 selected comments with completed, verified human labels.
[Task 07A.1](../tasks/sprint2/07a1_repair_response_list_links.md) repaired explicit
response-list links, published the [replacement inventory](specs/task07a1_final_result.json),
and verified all 50 decisions in a separate review project. Task 07A is complete
with [eight selected Great cases](../tasks/sprint2/07a_screen_pilot_candidates.md#eight-case-selection-and-07b-handoff).
Task 07B is complete: seven approved cases and one unclear case (I-CJ-4), with
all eight outcomes exported and validated. Task 07C is complete: seven approved
cases and 31 reviewed response argument blocks, with a validated export.
Task 07C.1 is complete: its validated replacement retains 57 claims across six
approved cases and one unclear stop (I-EA-2). The 31 direct/supporting claims from
approved cases are candidates for Task 07D. Prior reviews remain preserved.
Task 07D is complete, including the required
[code-quality gate](specs/task07d_code_quality_result.json). Its maintained exporter
reproduces the [sealed six-case output](specs/task07d_final_result.json) byte-for-byte:
31 claims and 84 citations, with accepted MVP limitations preserved. The
[maintainer guide](task07d_maintainer_guide.md) owns replay and code boundaries.
07E is closed: six answers approved through combined answer/reasoning review
in chat, with the [sealed handoff](specs/task07e_final_result.json) preserving
all claims, citation pools and review histories. Separate 07F is superseded.
The [benchmark evaluation plan](sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
uses automatic retrieval/final-citation metrics plus grounded correctness and
answer adequacy. 07G is closed by user decision without a full retrospective or
another pilot round. The [Task 08 contracts](../tasks/sprint2/08_curate_grouped_benchmark.md) are
drafted; only 08A is the active next contract and execution has not started.
See the [TODO](todo.md) for the current queue.
The consolidated [comment and response human review process](response_comment_human_review_process.md)
owns reusable workflow guidance for Task 08 preparation; Task 07 outcomes retain
historical evidence and case-specific decisions.

## Read for the next phase

1. [Task 08 umbrella](../tasks/sprint2/08_curate_grouped_benchmark.md) and
   [08A ranking contract](../tasks/sprint2/08a_rank_group_candidates.md) for the
   rolling single-group workflow, isolated review chats, and shared templates.
   [Decision 005](decisions/005_task08_grouped_question_selection.md) for the
   accepted Task 08 question-selection plan: exclusive groups and up to three
   human-selected questions per group. [07G](../tasks/sprint2/07g_assess_pilot_and_local_replay.md)
   records the decision to proceed; the [07E outcome](../tasks/sprint2/07e_review_answer_logic.md#final-outcome-and-six-case-handoff)
   preserves the sealed pilot. Apply the
   [current benchmark evaluation contract](sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary).
2. [Task 07D](../tasks/sprint2/07d_discover_and_review_evidence.md) for the completed
   evidence handoff and preserved discovery procedure, the [search protocol](specs/task07d_search_protocol_v1.md)
   and [per-claim agent prompt](prompts/task07d_claim_citation_search_v1.md) for
   repeatable evidence discovery, and [Task 07C.1](../tasks/sprint2/07c1_review_claims_and_relevance.md#final-reviewed-export-and-replacement-handoff)
   for the accepted combined-review replacement, [07C](../tasks/sprint2/07c_review_response_assertions.md#final-reviewed-export-and-learning)
   for the completed seven-case export and review lessons, and
   [07B](../tasks/sprint2/07b_review_comment_questions.md#final-reviewed-export)
   for the completed review handoff, [07A](../tasks/sprint2/07a_screen_pilot_candidates.md)
   for the selected-case handoff, and [07A.1](../tasks/sprint2/07a1_repair_response_list_links.md)
   for the accepted replacement and verified migration.
3. [Task 07 umbrella](../tasks/sprint2/07_pilot_reference_case_authoring.md)
   for the closed pilot's outcomes and [Sprint 2 plan](sprints/sprint2_brisbane_draft_eir_defense.md)
   for later eligibility/evaluation boundaries.
   Use the [human review process](response_comment_human_review_process.md) for
   consolidated Task 07 learning and the prospective Task 08 question/claim/
   evidence/answer review sequence.
4. [Replacement result](specs/task07a1_final_result.json) for the current Task 07/08
   input; the [05H outcome](../tasks/sprint2/05h_review_and_freeze_response_inventory.md)
   preserves the predecessor and inherited limitations.
5. Read [task shape](../tasks/README.md) and the [documentation guide](documentation.md)
   when activating or revising a Task 08 stage contract. The [07A plan](../tasks/sprint2/07a_screen_pilot_candidates.md)
   preserves the completed pilot's selection contract.

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
- [LLM judge learning notes](llm_judge_learning_notes.md): questions and
  proposed development checks for future Tasks 09/12; the sprint plan owns
  the evaluation contract.
- [`tasks/`](../tasks/): detailed task contracts, validation, and outcomes.

## Reading rule

Use the next task's inputs and the document roles above. Read a completed task
only when its outcome or preserved evidence is an explicit input.
