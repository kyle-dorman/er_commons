# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then use this page to decide what to read.

## Current status

Sprint 2 is the active sprint. Task 02 and all Task 03 work, including Tasks
03A through 03J and their subtasks, are complete.

Task 03J produced the immutable machine extraction basis: all 35 sources and
48,341 pages were published with zero source failures. Task 04D reused that
sealed extraction and replaced only linking-dependent document and collection
records. Its independently validated Gate D handoff is now the designated
downstream machine candidate.

The extraction lineage remains under
`pipelines/brisbane_baylands/task_03h_clean_full_v4/`. The `task_03h` name is a
retained generator and lineage name for the Task 03J v4 run; this directory is
Task 03J output and must not be treated as Task 03H input. Current
linking-dependent consumers use
`pipelines/brisbane_baylands/task_04d_relinked_v1/` and handoff
`handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`.
The exact replacement identity, checksums, and completion path are recorded in
the [Task 04D outcome](../tasks/sprint2/04d_relink_frozen_extraction.md).

[Task 04A](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md) is
complete. Its Gate D package under `reviewv1-task03j-final-c17/gate_d/` freezes
the Task 03J candidate with a separate human-usability layer: all 35 sources are
eligible, the 757 accepted decisions contain 60 TOC and 697 Not TOC outcomes,
the Task 03I finding is fixed, and all 725 unreviewed ambiguous links remain
explicitly unresolved. The release has zero material blockers. Existing large
Task 03J files were not rehashed.

Task 04B is closed as a no-op because there was no extraction regeneration.
[Task 04C](../tasks/sprint2/04c_materialize_human_review_navigation_overlay.md)
completed its source-free Gates A through C. The accepted semantic
view materializes 5,800 sparse block/table overrides for the 406 disagreements,
preserves original machine placement and section context, and covers all 757
decisions. Replacement Gate C uses sealed Docling text instead of malformed
table rows for all 15 confirmed TOCs, exposes 560 ordered entries to document
exploration and linking, adds 28 evidence-backed links without adding
aliases, and carries all 725 inherited ambiguities forward unresolved. Its Gate
D publication is superseded by completed [Task
04D](../tasks/sprint2/04d_relink_frozen_extraction.md), whose designated
replacement reuses Task 03J's extraction while replacing its linking-dependent
records through one shared exact target-resolution engine.

Task 04's first-pass review and Task 03I's bounded extraction repair remain
historical inputs to Task 04A. They do not transfer review IDs, anchors,
checksums, or human approvals. Superseded Task 03H and pilot artifact trees are
historical evidence only; removed or quarantined artifacts are not eligible
inputs to the current review.

## Next action

Task 04D is complete. For the accepted machine corpus boundary, read these
files in order:

1. [Task 04D contract](../tasks/sprint2/04d_relink_frozen_extraction.md)
2. [Task 04C outcome](../tasks/sprint2/04c_materialize_human_review_navigation_overlay.md)
3. [Task 03J outcome](../tasks/sprint2/03j_run_final_canonical_extraction.md)
4. [Architecture contract](architecture.md) and [data/artifact contract](data_artifacts.md)

The accepted R1-through-R6a policy links 410 of 560 reviewed TOC entries, up
from the 28 published by Task 04C. The remaining 150 entries, including all 89
figure entries, are explicitly deferred with R7/R7a. Gate D replayed and
independently verified all 35 documents under production identity
`exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3`,
with zero unavailable sources, blocking reasons, invalidations, or undeclared
differences. Task 03J remains the immutable extraction source, and Task 04A and
Task 04C remain immutable review evidence. The next planned work is [Task
05](../tasks/sprint2/05_build_curator_only_response_inventory.md); it has not
been started by this designation.

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
