# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then use this page to decide what to read.

## Current status

Sprint 2 is active. Tasks 02 through 05F are complete and accepted; Task 05F
closed as a partial outcome with 295 links and 216 explicit nonlinks across
511 mentions. Task 03J remains the immutable extraction basis, Task 04A supplies
accepted usability decisions, and Task 04D is the designated linking-dependent
handoff. Completed task records own exact identities and validation evidence.

## Next action

[Task 06](../tasks/sprint2/06_repair_reference_sources_and_target_index.md) now has
eight detailed contracts covering upstream repairs and bounded pipeline cleanup.
[Task 06A](../tasks/sprint2/06a_freeze_recovery_and_cleanup_plan.md) is the current
planning entry; source-free qualification is the next execution step, not a
completed result. Tasks 06B–06H remain provisional. No code changes, source
acquisition, conversion, or replay are authorized merely by this plan.

Read in this order:

1. [Task 06 umbrella](../tasks/sprint2/06_repair_reference_sources_and_target_index.md)
   for accepted directions, inputs, sequence, and shared boundaries.
2. [Task 06A](../tasks/sprint2/06a_freeze_recovery_and_cleanup_plan.md), or the
   active subtask designated by `docs/todo.md`, for the bounded contract.
3. [Task 05F accepted partial outcome](../tasks/sprint2/05f_resolve_official_draft_eir_references.md)
   for exact upstream bindings and the failure census.
4. [Architecture](architecture.md), [data/artifacts](data_artifacts.md), and the
   specific predecessor outcomes named by that subtask.

Task 06B combines safe sealed reuse and maintained-code cleanup in two gates.
Later tasks qualify the selected Final F1 substitute, repair repeated and missing
chapter targets, publish caption-backed figures, replay affected descendants,
and reuse or renew human review. Preserving existing chunked conversion and
accepted review is an explicit acceptance requirement.

After the replacement handoff is accepted, [Task 05G](../tasks/sprint2/05g_replay_and_extend_official_reference_links.md)
owns consumer-binding updates and reference replay; [Task 05H](../tasks/sprint2/05h_review_and_freeze_response_inventory.md)
owns final curator review and immutable response-inventory publication. The
[Task 05 umbrella](../tasks/sprint2/05_build_curator_only_response_inventory.md)
retains that separate curator-only inventory boundary.

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
