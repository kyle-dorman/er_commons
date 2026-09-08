# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then use this page to decide what to read.

## Current status

Sprint 2 is active. Tasks 02 through 04D are complete. Task 03J remains the
immutable extraction basis; Task 04A supplies the accepted usability registry;
and Task 04D is the designated replacement for linking-dependent consumers.
Task 04B is closed as a no-op and Task 04C remains superseded review evidence.
The detailed identities, outcome evidence, and historical transitions belong in
the completed task records.

## Next action

Task 05 is planned and not activated. Before activating it, read these files in
order:

1. [Task 05 contract](../tasks/sprint2/05_build_curator_only_response_inventory.md)
2. [Task 04D outcome](../tasks/sprint2/04d_relink_frozen_extraction.md)
3. [Task 04A outcome](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md)
4. [Task 03J outcome](../tasks/sprint2/03j_run_final_canonical_extraction.md)
5. [Architecture contract](architecture.md) and [data/artifact contract](data_artifacts.md)

Task 05 must bind the immutable Task 03J extraction, Task 04A usability
registry, and the Task 04D linking-dependent handoff. Its Final EIR Volume 4
inventory remains a separate curator-only artifact, not part of the model
corpus.

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
- [`docs/task04_maintainer_runbook.md`](task04_maintainer_runbook.md): first-pass
  review maintenance and the Task 04A transition boundary.
- [`docs/documentation.md`](documentation.md): documentation ownership and
  editing rules.
- [`docs/todo.md`](todo.md): current queue and next action.
- [`docs/backlog.md`](backlog.md): unselected future ideas only.
- [`tasks/`](../tasks/): detailed task contracts, validation, and outcomes.

## Reading rule

Do not read every historical task record for narrow work. Use the active task's
input list and the document roles above. Read a historical task only when its
outcome or preserved evidence is an explicit input to the current task.
