# Task 08B selection interface v2

Template/schema version: `task08b.selection.v2`.
Process revision: `task08.selection_gate.v2`.
This shared revision supersedes v1 for all new 08B batches. Kyle requested the
change before any submitted health-risk annotations; no migration is needed.
The original project, its unsaved draft, and v1 artifacts remain preserved.

The [qualified intake revision](task08b_intake_v2.md) adds v2 handoff support
and exact source-page display while retaining this form and process.

The 2026-10-01 all-group closeout uses `task08.selection_closeout.v1`: the user
explicitly accepts every saved Selected candidate, without the historical
three-candidate cap, and confirms all groups finished. Native Skip records remain
distinct nonselected dispositions. This export amendment changes no native form
or historical export; see the Task 08B closeout outcome.

## Input and display

Reuse the same sealed 08A input and proposal, verifying their existing identities
without reranking or regenerating proposals. Preserve the saved total order.
Show the unchanged original comment, complete linked responses and source
footnotes. Escape text for HTML; never truncate or rewrite it. Import no human
decisions or predictions.

Do not display source-warning/review-limitation sections, advisory ranking
reasons, or source-bound ranking records. Do not generate replacement narrative
for them. Existing `advisory`, `source_warnings`, `response_context` and original
source provenance remain in the underlying task records and bound upstream
artifacts. This includes O-Joint-44's recorded incidental-revision exception.
The exact displayed comment and response HTML derives only from source text.

Keep `original_comment` and `comment_source_warnings` separately addressable.
08C will construct its own strictly comment-only packet, excluding response text,
ranking reasons and selection rationale. No 08C packet is created here.

## Human controls and advancement

The shared form has required **selection** and **selection reason**, plus optional
notes. Selection values remain `Selected`, `Reviewed skip`, `Excluded`, and
`Unresolved`. Existing reason codes remain available, including `Source or
eligibility concern`; explain concerns in notes as needed. `Other` requires notes.

There is no provisional-eligibility decision or continue/stop control. Selection
is the single human label gate from 08B to 08C. It is not final case eligibility:
the evidence-based human eligibility review remains at 08E. Enforce at most three
selections; fewer, including zero, are allowed. No automatic backfilling.

Reconcile saved annotations against every candidate in the trusted inventory.
Unanswered candidates remain unreviewed even when other candidates were reviewed
out of order. Native Skip/Postpone/cancellation and drafts stay distinguishable
pending states; they never become reviewed exclusions. Unsaved edits do not
silently replace or authorize advancement of an older saved annotation.

## Chat completion and export

When Kyle requests export, confirm in chat that he is finished with this group's
review. An explicit statement that he has finished and wants export is itself
confirmation; otherwise ask. Neither three selections nor queue exhaustion is
completion confirmation. Save the actual statement and chat reference separately
from per-candidate annotations, bound to the current export and input identities.

The confirmation uses `task08b.finish.v2`, including `finished: true`,
`process_revision`, `template_version`, `project_id`, `input_sha256`,
`proposal_sha256`, `export_sha256`, `reviewer`, timezone-bound `confirmed_at`,
`chat_reference`, and `statement`. Synthetic qualification uses a clearly marked
synthetic confirmation and never impersonates a dataset reviewer.

Without a valid confirmation, normalized exports are awaiting confirmation and
have no advancing IDs. With confirmation and no pending drafts/cancellations,
explicitly selected records alone advance; skips, exclusions and unresolved
records remain preserved but do not advance. Unresolved selections can remain
unresolved when the human closes this review pass; closure does not relabel them.
Pending drafts/cancellations require reconciliation before a final handoff.

Export native JSON with all tasks. Reject missing/duplicate candidates, changed
source data, legacy v1 controls, unknown controls, missing reasons, duplicate or
ambiguous annotations, missing project/reviewer/time provenance, and more than
three selections. Reject false or stale completion confirmations. Keep the full
native audit and separate normalized decisions, reviewed positions, untouched IDs,
selection counts and advancing IDs. The last reviewed position is informational,
not a stopping gate. No eligibility or stopping field is inferred.

## Maintained commands and qualification

`make prepare-group-selection` takes `RANKING_OUTPUT`, `RANKING_RESULT` and a fresh
`SELECTION_OUTPUT`; it writes source-bound blank tasks and shared snapshots.

`make export-group-selection` takes `SELECTION_OUTPUT`, saved all-task
`NATIVE_EXPORT`, `PROJECT_ID`, and fresh `DECISIONS_OUTPUT`. Supply the saved
`FINISH_CONFIRMATION` for final export. Omission creates only a pending audit;
it cannot advance cases. Before export verify the project's form and task IDs
against its import receipt. Preserve each export in a new no-clobber location.

Tests and a separate synthetic project cover full long-source display, saved
order, blank controls, save/reload, partial inventory reconciliation, unreviewed
cases, selection-only advancement, chat confirmation and maximum-three rejection.
The v2 form and exporter must be qualified together. Later batches use this same
shared interface; any further revision requires explicit prior-batch assessment.

## Learning and provenance

The native form can collect these two decisions without a custom stopping UI.
Full-inventory reconciliation preserves unanswered cases, while chat completion
records the human boundary independently of task traversal. This reduces form
burden without conflating selection and later evidence-based eligibility.
Maintained [configuration guidance](https://labelstud.io/guide/setup.html) and
[JSON export guidance](https://labelstud.io/guide/export.html) were rechecked on
2026-09-30. Original v1 qualification and native records remain historical evidence.

The final coordination handoff must include both revisions, superseded/current
project references, the confirmed completion record, exact input/export hashes,
selected and unreviewed dispositions, and the retained later eligibility gate.
