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

Task 05 is now a seven-part planned umbrella. Task 05A is the next subtask and
is not activated. Before activating it, read these files in order:

1. [Task 05 umbrella](../tasks/sprint2/05_build_curator_only_response_inventory.md)
2. [Task 05A contract](../tasks/sprint2/05a_qualify_and_profile_response_source.md)
3. [Architecture contract](architecture.md) and [data/artifact contract](data_artifacts.md)

Task 05A binds the immutable Task 03J extraction, Task 04A usability registry,
and Task 04D linking-dependent handoff through compact sealed metadata without
rehashing their large payloads. It then profiles only a bounded representative
selection from Final EIR Volume 4. Tasks 05B through 05G remain provisional and
must be revised in sequence from accepted preceding outcomes. The final
inventory remains a separate curator-only artifact, not part of the model
corpus. Read the full Task 03J, Task 04A, or Task 04D historical outcomes only
if compact metadata disagree or Task 05A encounters an unresolved boundary.

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
