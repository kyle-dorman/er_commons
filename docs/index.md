# Docs Index

Start with `AGENTS.md`, then use this page to choose the smallest useful set of
project docs.

## Current status

Sprint 2 is active. Tasks 02–06 are complete, including the repaired
[Task 06H handoff](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
and the preserved [Task 05H response inventory](specs/task05h_final_result.json).
The [05H summary](specs/task05h_final_summary.md) owns review coverage and
inherited limits. The [Task 07 umbrella](../tasks/sprint2/07_pilot_reference_case_authoring.md)
and later subtasks remain provisional. The
[07A sample](../tasks/sprint2/07a_screen_pilot_candidates.md#sampling-outcome)
contains 50 selected comments with completed, verified human labels.
[Task 07A.1](../tasks/sprint2/07a1_repair_response_list_links.md) repaired explicit
response-list links, published the [replacement inventory](specs/task07a1_final_result.json),
and verified all 50 decisions in a separate review project. Task 07A is complete
with [eight selected Great cases](../tasks/sprint2/07a_screen_pilot_candidates.md#eight-case-selection-and-07b-handoff).
Next, revise Task 07B for their comment-question review.

## Read for the next phase

1. [Task 07B](../tasks/sprint2/07b_review_comment_questions.md) for the next
   provisional contract, [07A](../tasks/sprint2/07a_screen_pilot_candidates.md)
   for the selected-case handoff, and [07A.1](../tasks/sprint2/07a1_repair_response_list_links.md)
   for the accepted replacement and verified migration.
2. [Task 07 umbrella](../tasks/sprint2/07_pilot_reference_case_authoring.md)
   for the proposed stage order and [Sprint 2 plan](sprints/sprint2_brisbane_draft_eir_defense.md)
   for later eligibility/evaluation boundaries.
3. [Replacement result](specs/task07a1_final_result.json) for the current Task 07/08
   input; the [05H outcome](../tasks/sprint2/05h_review_and_freeze_response_inventory.md)
   preserves the predecessor and inherited limitations.
4. [07A plan](../tasks/sprint2/07a_screen_pilot_candidates.md) for the current
   selection contract; read [task shape](../tasks/README.md) and the [documentation
   guide](documentation.md) before revising it.

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
- [`tasks/`](../tasks/): detailed task contracts, validation, and outcomes.

## Reading rule

Use the next task's inputs and the document roles above. Read a completed task
only when its outcome or preserved evidence is an explicit input.
