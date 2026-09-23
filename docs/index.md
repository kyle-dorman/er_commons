# Docs Index

Start with `AGENTS.md`, then use this page to choose the smallest useful set of
project docs.

## Current status

Sprint 2 is active. Tasks 02–06 are complete, including the repaired
[Task 06H handoff](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
and the sole immutable [Task 05H response inventory](specs/task05h_final_result.json).
The [05H summary](specs/task05h_final_summary.md) owns review coverage and
inherited limits. No later task is active; [Task 07 planning](sprints/sprint2_brisbane_draft_eir_defense.md#model-assisted-reference-case-authoring)
is next. Write its bounded contract before implementation.

## Read for the next phase

1. [Sprint 2 plan](sprints/sprint2_brisbane_draft_eir_defense.md) for Task 07
   scope and later eligibility/evaluation boundaries.
2. [Task 05H outcome](../tasks/sprint2/05h_review_and_freeze_response_inventory.md)
   for the accepted Task 07/08 input; follow its predecessor links only as needed.
3. [Documentation guide](documentation.md) and [task shape](../tasks/README.md)
   before writing the next contract. Read architecture or artifact guidance when
   the contract touches those boundaries.

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
