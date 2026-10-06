# Task 08D claim and relationship review v1

Status: preserved v1 qualification; superseded for new review by
[v2](task08d_claim_review_v2.md). Project 47 and its unsaved draft remain preserved.
Owner: [08D contract](../../tasks/sprint2/08d_review_group_claims.md).

## Boundary

`task08d.claim_review.v1` separates exact source assertions, advisory relationships,
and explicit human decisions. Human approval concerns faithful response wording
and relevance to a frozen question, not truth or evidence support. The first batch
is health-risk M-OSEC-241 and O-Joint-44 only. Prospective 08C prompt changes do not
modify their frozen approved text or provenance.

The shared [prompt](../prompts/task08d_claim_review_v1.md) inventories substantive
assertions before assigning relationships. Inventory coverage names every response
passage, including a reason when no substantive assertion is extracted. The second
pass maps every assertion to a claim and every material question part to addressed,
unanswered or unclear status. This preserves unrelated assertions without turning
incidental details into individual evidence tasks.

## Interface and relationships

One native task contains a complete case and linked response closure. Claim cards
show direct claims first, then supporting and remaining assertions. Each card has
editable wording, exact source-passage references, relationship, targets, rationale
and a separate initially blank human decision: approve, reject or unresolved.
Question wording is read-only. Supplied citations and source warnings remain source
provenance. Spare cards allow source-bound additions; overflow requires a separate
preserved project revision.

A direct claim targets one or more displayed parts of the frozen question.
A supporting claim targets exactly one direct claim and explains its material
contribution. No support chains or topic-only support. Not-relevant and unclear
claims have no targets. Editing a relationship requires fixing its targets and
rationale; the exporter never silently clears or repairs links. Rejected claims
remain in the audit inventory.

Case controls explicitly record ready, unresolved or stopped, notes, question-gap
resolution and confirmation of the current links after edits. Confirming current
links applies to the entire saved annotation, including exact edited target text;
export binds each support relationship to that target's current revision hash.
A subsequent saved revision requires validation anew. This is an auditable human
attestation, not automated proof that the relationship is semantically sound.

For v1 all unresolved claim decisions or unclear approved relationships hold the
whole case. This conservative rule avoids silently declaring uncertain scope
nonessential. Unanswered/unclear question parts remain visible; readiness requires
an explicit saved resolution, with reasons. A stopped or pending case exports its
history but no advancing claims. No usable approved direct claim also blocks
advancement.

## Source and export contract

Input verification binds the accepted 08C handoff, explicit approval, question text
hash/version and original comment to accepted selection/source records. Complete
response closure is reconciled against the full accepted directed graph, including
cycles, response lists, general responses, supplements and reference outcomes.
Source passages preserve exact offsets/text in original units. Proposal inventories
and relationship files bind this source-only packet; no historical claims, labels
or answers enter proposal inputs.

Prepared task data, form, prompt, schemas, implementation and proposal inputs receive
checksums in a no-clobber external directory. Native exports are compared against
trusted prepared tasks, never against a second untrusted field in the export.
Project, reviewer, task, annotation, timestamps and exact fields must validate.
Multiple annotations require reconciliation; drafts, cancelled and untouched tasks
remain distinct from submitted approvals. Predictions never supply missing decisions.

Only explicitly approved exact direct/supporting claims from ready, unblocked cases
advance. Every other decision remains preserved, including rejected/unresolved and
not-relevant claims, source warnings, question gaps and whole-case stops. Saved
native JSON and normalized decisions remain versioned. Pending-review receipts are
not completed 08D or authorized 08E handoffs.

## Qualification and learning

Use separate source-free projects for actual queue/prefill/save/reload/export checks,
including edited words and targets, changed relationships, rejection, unresolved
claims/gaps, stopped cases and untouched tasks. Negative tests reject stale/foreign
bindings, missing approvals and invalid targets. Bounded independent reviews cover
response coverage, relationship consistency and export fidelity. No synthetic
annotation is imported into the health-risk project.

Native Label Studio predictions and saved annotations have distinct roles, as
specified in the [prediction guidance](https://labelstud.io/guide/predictions.html).
The [configuration guide](https://labelstud.io/guide/setup.html) and
[native export guide](https://labelstud.io/guide/export.html) support a shared native
form plus JSON review boundary. Existing fixed-slot controls and hashing/source
helpers fit this small batch; a new annotation framework is unnecessary. Readable
claim wording and exact spans solve different problems: wording enables a clear
review decision, while spans permit checking what the response actually said.

## Maintained commands

`make prepare-group-claims CLAIM_PACKET=... CLAIM_PROPOSAL=... CLAIM_PREPARED=...`
verifies source-only input and the adjacent two-pass inventory, then writes a fresh
trusted review directory. `make export-group-claims CLAIM_PREPARED=... NATIVE_EXPORT=...
PROJECT_IDENTITY=... CURRENT_PROJECT=... REVIEWER_ID=... CLAIM_EXPORT=...` validates a
saved all-task native export and current project settings against the imported
identity and qualified form. Output directories must be fresh. Capture native JSON
and project settings read-only after the reviewer confirms saved decisions; the
command never creates or repairs annotations. Flat advancing claims carry case,
question/version/hash and input/proposal bindings because local claim IDs repeat
across cases.
