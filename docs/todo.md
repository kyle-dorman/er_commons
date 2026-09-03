# Project TODO

## Sprint status

Sprint 2, Brisbane Draft-EIR defense vertical slice, is active. Task 02 and all
Task 03 work are complete. Task 04 and Task 03I are complete as the first-pass
review and its bounded extraction disposition. Task 03J is complete as the
fresh machine-only 35-source candidate and collection handoff.

The Task 03J machine handoff still records `task04_status: not_evaluated`
because immutable machine records are not rewritten by human review. Task 04A's
separate Gate D freeze is now the accepted human-usability decision.

## Current action: review Task 04C before activation

[Task 04A](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md) is
complete. Its Gate D package is under
`reviewv1-task03j-final-c17/gate_d/`. The release freezes all 35 sources as
eligible with the human TOC layer, 757 decisions (60 TOC and 697 Not TOC), the
Task 03I finding as fixed, and all 725 unreviewed ambiguous links as unresolved.
It records zero material blockers, closes Task 04B as a no-op, and references
sealed Task 03J identities without rehashing large files.

Provisional [Task
04C](../tasks/sprint2/04c_materialize_human_review_navigation_overlay.md) is now
the next task to review. It is not active. Its job is to materialize one derived
machine-plus-human navigation view and conservatively reconsider links for newly
confirmed TOCs without mutating Task 03J or Task 04A.

## Conditional follow-up

[Task 04B](../tasks/sprint2/04b_remediate_toc_navigation_and_reprocess.md) is a
no-op by user decision because Task 03J will not be regenerated.

## Later sequence

After the extraction release is frozen, the remaining planned work is:

1. [Task 04C](../tasks/sprint2/04c_materialize_human_review_navigation_overlay.md):
   materialize the human-reviewed navigation and linking overlay.
2. [Task 05](../tasks/sprint2/05_build_curator_only_response_inventory.md): build
   the separate Final EIR Volume 4 comment and response inventory.
3. Task 06: pilot reference-case authoring and evidence review.
4. Task 07: curate, cluster, split, and freeze benchmark cases.
5. Task 08: build and freeze human evaluation.
6. Task 09: build and freeze BM25 retrieval.
7. Task 10: build and freeze target generation.
8. Task 11: calibrate the automated judge.
9. Task 12: run the locked test and close Sprint 2.

These tasks remain planned. Their detailed boundaries are in the [Sprint 2
plan](sprints/sprint2_brisbane_draft_eir_defense.md); no later task is active.

## Historical routing

The completed Task 03 contracts and outcomes remain in `tasks/sprint2/` as
evidence and learning material. The first-pass Task 04 review and Task 03I
repair explain why Task 04A is a new review run rather than a continuation.
Superseded Task 03H and earlier pilot artifact trees are not valid inputs to
Task 04A or Task 04B. The [documentation guide](documentation.md) defines which
details belong in task records instead of this queue.
