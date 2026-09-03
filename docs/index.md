# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then use this page to decide what to read.

## Current status

Sprint 2 is the active sprint. Task 02 and all Task 03 work, including Tasks
03A through 03J and their subtasks, are complete.

Task 03J produced the current machine-only corpus candidate: all 35 sources and
48,341 pages were published with zero source failures. Its collection handoff
passed the owning validator and records `task04_status: not_evaluated`; that
field describes the machine handoff, not the status of the completed first-pass
Task 04 review.

The current artifact lineage is stored under
`pipelines/brisbane_baylands/task_03h_clean_full_v4/`. The `task_03h` name is a
retained generator and lineage name for the Task 03J v4 run; this directory is
Task 03J output and must not be treated as Task 03H input. The exact identity,
handoff ID, checksums, and completion path are recorded in the [Task 03J
outcome](../tasks/sprint2/03j_run_final_canonical_extraction.md).

[Task 04A](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md) is
complete. Its Gate D package under `reviewv1-task03j-final-c17/gate_d/` freezes
the Task 03J candidate with a separate human-usability layer: all 35 sources are
eligible, the 757 accepted decisions contain 60 TOC and 697 Not TOC outcomes,
the Task 03I finding is fixed, and all 725 unreviewed ambiguous links remain
explicitly unresolved. The release has zero material blockers. Existing large
Task 03J files were not rehashed.

Task 04B is closed as a no-op because there will be no machine regeneration.
Provisional [Task
04C](../tasks/sprint2/04c_materialize_human_review_navigation_overlay.md) is the
next task to review and is not active. It owns the separate work of applying the
accepted human layer to semantic navigation, aliases, and links.

Task 04's first-pass review and Task 03I's bounded extraction repair remain
historical inputs to Task 04A. They do not transfer review IDs, anchors,
checksums, or human approvals. Superseded Task 03H and pilot artifact trees are
historical evidence only; removed or quarantined artifacts are not eligible
inputs to the current review.

## Next action

For the next task decision, read these files in order:

1. [Task 04C contract](../tasks/sprint2/04c_materialize_human_review_navigation_overlay.md)
2. [Task 04A outcome](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md)
3. [Architecture contract](architecture.md) and [data/artifact contract](data_artifacts.md)

The accepted Gate D completion and release records are under
`pipelines/brisbane_baylands/task_04_review/reviewv1-task03j-final-c17/gate_d/`.

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
