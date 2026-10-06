# Task 08B selection interface v1

Historical: superseded by the [shared v2 contract](task08b_selection_v2.md).

Version: `task08b.selection.v1`. One shared native Label Studio form, ordered
input schema, preparation adapter, and saved-export validator. No earlier 08B
batch requires migration. A later interface change requires a named revision and
an explicit decision about affected batches.

## Inputs and display

`group_selection.prepare` verifies the supplied 08A completion record's five
bound artifacts and calls the unchanged `group_ranking.validate` for complete
seal, source replay, response closure, and advisory proposal checks. It renders
every candidate in the saved order. Native project sampling and Data Manager
ordering must preserve this order and be tested through the actual queue.

The form shows the unchanged original comment, every linked response, applicable
source-page supplements, reference outcomes, all advisory reasons/concerns, and
inherited limitations. Text is HTML escaped, never summarized or truncated;
scrollable source panes preserve full long responses. No predictions, rewritten
questions, selection defaults, or eligibility defaults are imported.

Prepared data keeps `original_comment` and `comment_source_warnings` separate
from `response_context`, `advisory`, and `source_warnings`. The latter includes
response-derived screening context. Future 08C must explicitly construct a fresh
comment-only packet; it must never pass whole task data or this review export to
its wording model. This interface does not create that packet.

## Human decisions

Each submitted candidate has separate required selection, selection reason,
provisional eligibility, eligibility reason, and continue/stop controls. Reasons
are fixed codes; `Other` requires written notes. Notes otherwise remain optional.
`Selected`, `Reviewed skip`, `Excluded`, and `Unresolved` are distinct. Eligibility
is `Provisionally eligible`, `Ineligible`, `Unresolved`, or `Not assessed` (allowed
only for candidates not selected). A selected but ineligible candidate remains
selected in the audit but cannot advance. Only selected and provisionally
eligible cases advance; the ceiling applies to all selections, not advancing IDs.

Stopping reasons distinguish enough candidates, no more suitable candidates,
unresolved decisions remaining, and another explained reason. Submit the stopping
candidate, then exit the queue. Label Studio's native next-task navigation does
not implement this custom stopping policy. The exporter rejects saved reviews
after a declared stop or after the third selection. Reaching the last candidate
can record exhaustion without forcing three selections. Downstream attrition
never causes backfilling.

Unseen tasks remain unreviewed. Native Skip/Postpone/cancellation is pending,
not a saved reviewed skip or exclusion. Drafts remain pending, including unsaved
edits to an earlier submitted decision; native saved content is preserved in the
audit. Unresolved decisions keep the group pending even when a stopping point is
recorded. Closing with an explicit deferral requires a separately recorded human
decision, not conversion of unresolved decisions to exclusions.

## Export and provenance

Use native JSON with **all tasks**, including untouched tasks. The exporter
requires exact candidate closure and trusted task-data equality, explicit project,
annotation/draft collections, saved reviewer identity and timezone-bound times.
It rejects multiple annotations requiring reconciliation, duplicate IDs, unknown
controls, missing reasons, contradictory eligibility reasons, and more than three
selections. It retains native tasks losslessly alongside normalized decisions,
reviewed positions, stopping point, untouched IDs, selected IDs, advancing IDs and
derived counts. It does not estimate active review time.

`load_prepared` revalidates shared snapshots and rebuilds tasks from the verified
08A inputs before export. Preserve each native export and normalized output in a
fresh no-clobber location; bind the native byte hash, preparation manifest and
project receipt in the batch result. No silent reconciliation or resubmission.

## Commands and qualification

`make prepare-group-selection` requires `RANKING_OUTPUT`, `RANKING_RESULT`, and
fresh `SELECTION_OUTPUT`. It prepares a queue and versioned interface snapshots;
local API/project creation remains in the external execution record.

After Kyle's decisions, `make export-group-selection` requires the trusted
`SELECTION_OUTPUT`, saved `NATIVE_EXPORT`, `PROJECT_ID`, and fresh
`DECISIONS_OUTPUT`. Validate the saved result, reconcile the batch register, and
create the exact coordination handoff before reporting group completion.

Source-free tests exercise long complete response text, literal HTML characters,
supplements, source/order tampering, untouched/draft/cancelled states, decisions,
reason requirements, selection ceilings, and stopping rules. Separate synthetic
projects must exercise actual queue order, source display, native save/reload and
all-task export before dataset use. Automated fixture annotations must never be
mixed with human dataset annotations.

## Learning and maintained guidance

Reusable native controls fit this small decision task. A narrow pure exporter
adds cross-task selection/stopping checks that the form cannot enforce. Saved
annotations are separate from displayed model advice; a missing or unsaved
annotation is not a negative label. Inspect the actual queue, because previews
and import order alone do not establish the review experience.

Maintained guidance checked 2026-09-30:
[configuration](https://labelstud.io/guide/setup.html),
[labeling](https://labelstud.io/guide/labeling.html), and
[native JSON export](https://labelstud.io/guide/export.html).
