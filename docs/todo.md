# Project TODO

## Sprint status

Sprint 2, Brisbane Draft-EIR defense vertical slice, is active. Task 02 and all
Task 03 work are complete. Task 04 and Task 03I are complete as the first-pass
review and its bounded extraction disposition. Task 03J is complete as the
fresh machine-only 35-source candidate and collection handoff.

The current handoff records `task04_status: not_evaluated`. This is the machine
handoff field; final human usability and release status still belong to Task
04A. The exact Task 03J identities and checksums are in its [task
outcome](../tasks/sprint2/03j_run_final_canonical_extraction.md).

## Next action: Task 04A

[Task 04A](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md) is
provisional, inactive, and unblocked. Before activation:

- revise Gate A from the validated Task 03J handoff;
- bind a new review identity to the exact Task 03J inputs and reject stale Task
  03H anchors and artifacts;
- freeze deterministic selection, recheck, TOC-census, and review policies;
- extend and qualify the existing review generator with its explicit
  `task03j_final` mode; and
- present the review workload and approval boundary before source-PDF reads or
  review renders.

During the active pass, Task 04A will recheck applicable Task 03I findings,
review fresh risk samples, review every machine-detectable TOC or document-index
candidate, record source usability, and either publish the release-freeze
record or stop with an approved remediation handoff.

## Conditional follow-up

[Task 04B](../tasks/sprint2/04b_remediate_toc_navigation_and_reprocess.md) is
inactive. Activate it only from a completed Task 04A stop record containing an
approved TOC/navigation finding and checksummed `task04b_handoff.json`. If Task
04A freezes the release without such a finding, close Task 04B as a no-op.

## Later sequence

After the extraction release is frozen, the remaining planned work is:

1. [Task 05](../tasks/sprint2/05_build_curator_only_response_inventory.md): build
   the separate Final EIR Volume 4 comment and response inventory.
2. Task 06: pilot reference-case authoring and evidence review.
3. Task 07: curate, cluster, split, and freeze benchmark cases.
4. Task 08: build and freeze human evaluation.
5. Task 09: build and freeze BM25 retrieval.
6. Task 10: build and freeze target generation.
7. Task 11: calibrate the automated judge.
8. Task 12: run the locked test and close Sprint 2.

These tasks remain planned. Their detailed boundaries are in the [Sprint 2
plan](sprints/sprint2_brisbane_draft_eir_defense.md); no later task is active.

## Historical routing

The completed Task 03 contracts and outcomes remain in `tasks/sprint2/` as
evidence and learning material. The first-pass Task 04 review and Task 03I
repair explain why Task 04A is a new review run rather than a continuation.
Superseded Task 03H and earlier pilot artifact trees are not valid inputs to
Task 04A or Task 04B. The [documentation guide](documentation.md) defines which
details belong in task records instead of this queue.
