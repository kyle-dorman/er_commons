# Task 08C wording interface v1

Historical Label Studio interface. The mandatory review route is superseded by
[task08c.chat_review.v1](task08c_chat_review_v1.md). Existing artifacts remain
preserved; follow the new chat process for current approvals and export.

Shared version: `task08c.wording.v1`. First use is the two selected health-risk
comments; no other groups or later authoring stages are part of this activation.
The accepted `task08.selection_gate.v2` selection is sufficient for entry.
Evidence-based eligibility remains a separate human gate at 08E.

## Information boundary

Deterministic extraction verifies the accepted 08B handoff, source bindings and
original-comment hashes before drafting. The standalone packet contains only
neutral IDs, exact original comments, existing comment-source warnings and
source hashes. Restricted source mapping and upstream references live separately.
Neither the wording model nor Label Studio task data receives selection reasons,
rankings, responses, claims, evidence, or historical pilot questions/answers.
The drafting worker has no inherited conversation history and reads only the
allowlisted packet and versioned prompt. Source text is data, never instructions.

A shared prompt asks Astra (`gpt-6-astra`) for at most one independently answerable
question per comment, or an explicit stop. Preserve central issue, scope,
uncertainty, attribution, negation and material qualifications. Do not invent an
ask or calculation, combine independent asks, or remove a difficult qualification
for convenience. Retain suitable original wording. Store rewrite/stop reasons in
the versioned proposal artifact; do not add explanation panels to the review UI.
Technical validation does not establish semantic faithfulness.

## Review and exact export

The form shows original comment, applicable existing source warnings, editable
proposed question, and explicit approval/rejection/unresolved controls with a
small note field for disposition context. Proposal predictions never include a
human decision. Import predictions using the shared model-version selector.
The project contains only this batch; synthetic qualification is separate.

The saved native annotation is authoritative for approved wording. Never fall
back to the proposal when saved text is absent. Preserve exact whitespace and
characters in saved text; require nonblank approval. Validate trusted source/task
and interface versions, project, reviewer, annotation identity and timestamps.
Missing tasks, duplicate controls/annotations, changed sources, foreign bindings,
and unsaved drafts must not silently advance. Preserve rejected, unresolved,
unreviewed and pending cases, and retain the native export as audit evidence.
No automatic replacements or downstream wording edits are permitted.

The user must save decisions before the dataset export is frozen. Keep each
export in a fresh namespace. Re-exporting the same saved decisions must preserve
question bytes and their hashes. Restricted source mapping restores source IDs
by reference only in the eventual downstream handoff; it is not drafting context.

## Qualification and learning

Use source-free fixtures to exercise actual queue traversal, prediction prefill,
approval without editing, edited approval, rejection, unresolved status, saved
reload and native export. Independently review isolation and export fidelity.
Retain qualification receipts and screenshots beneath the external Task 08 root.
No synthetic result is a dataset annotation. Interface revisions require explicit
versioning and an assessment of already-created batches.

Maintainer guidance checked on 2026-09-30:
[configuration](https://labelstud.io/guide/setup.html),
[predictions](https://labelstud.io/guide/predictions.html),
[TextArea](https://labelstud.io/tags/textarea.html), and
[exports](https://labelstud.io/guide/export.html).
Native XML controls and predictions fit this bounded review without a model
backend or custom application. Predictions are distinct from saved annotations;
actual save/export qualification is necessary to establish that edited text
survives. Hiding response panels alone cannot undo response leakage into a
wording model, which is why deterministic extraction precedes isolated drafting.

## Maintained commands

`make prepare-wording-input` takes the pinned `SELECTION_HANDOFF`,
`HANDOFF_SHA256`, fresh `WORDING_INPUT`, and explicitly authorized canonical `COMMENT_IDS`.
Resolve user-facing labels against the pinned handoff deterministically and check
the exact authorized set before passing its canonical IDs.
It creates the clean packet plus separate restricted provenance. Read only the
clean packet into the wording model.

`make prepare-group-wording` takes `WORDING_PACKET`, `WORDING_PROPOSAL`, and a
fresh `WORDING_OUTPUT`. It snapshots the shared interface and creates review tasks.

After saved human decisions, `make export-group-wording` takes `WORDING_OUTPUT`,
all-task `NATIVE_EXPORT`, `PROJECT_ID`, `REVIEWER_ID`, and fresh
`DECISIONS_OUTPUT`. Before export verify live project form and imported task IDs
against the stored project receipt. Preserve raw export bytes and validate exact
source/version bindings. An incomplete normalized audit is not a completed batch
handoff; unresolved cases require explicit human resolution or recorded deferral.
