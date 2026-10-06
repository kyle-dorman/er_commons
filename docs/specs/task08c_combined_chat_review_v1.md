# Task 08C combined sequential review v1

Process revision: `task08c.combined_chat_review.v1`. Authorized 2026-10-01 for
exactly 57 selected comments, including the two historically approved health-risk
questions. This pass supersedes per-group presentation and the three-comment cap;
it preserves the historical `task08c.chat_review.v1` records and validators.

## Report-context amendment — 2026-10-02

Kyle explicitly permits verified report context to inform question wording. This
supersedes the comment-only restriction below prospectively. Original comments
and historical source-only versions stay unchanged. Record added context and its
source separately; do not imply it appeared in the original comment or infer
approval. The external `report_context_amendment_v1.json` preserves the request
and checked source. Before a context-informed proposal, pin its new prompt/context
provenance explicitly without rebinding earlier events. All queue, exact-version
approval and downstream reconciliation gates remain unchanged.

## Response display amendment — 2026-10-02

Kyle requested the response as part of question review. Starting with question 5,
show the verified direct response separately from original comment and proposal,
plus a concise alignment/gaps assessment. Identify relevant linked general
responses; preserve the complete linked response packet. Label abridged displays
as excerpts and provide a full-source link when needed. This extends the report
context authorization above; it does not introduce selection/ranking rationales
or approve any question or later-stage result. Existing versions stay unchanged.
The external `response_display_amendment_v1.json` preserves the request.

## Self-contained wording clarification — 2026-10-02

The answering model will not see the original comment. Questions must therefore
state necessary facts and qualifications directly; avoid phrases such as “the
commenter’s evidence” or unnamed comparisons. Verify report-derived context and
retain its source separately. If a claimed fact exists only in a comment, do not
misattribute it to the report. Preserve scope and uncertainty when simplifying.

## C017 adjacent-comment context amendment — 2026-10-02

Kyle explicitly authorized revising C017 using comments M-OSEC-272, M-OSEC-273,
and M-OSEC-274 together, and carrying all three responses into the next step.
Keep selected identity M-OSEC-273 and its original source hashes unchanged. Bind
the added comments and complete responses in a separate versioned context packet,
including explicit response links. Preserve earlier drafts and source packets.
The combined closeout and any later intake must carry this supplemental packet
alongside the approved question version; the original single-comment response
packet alone is insufficient for this case. This starts no later stage and adds
no selected candidate or automatic approval. Other cases retain their existing
source boundaries unless separately authorized.

## Intake and order

Bind `task08b_all_groups_export_result.json`, its checksummed summary and selected
CSV. Verify each `task08b.handoff.v3` and reproduce its saved closeout decisions
with `group_selection_closeout`. Reconcile all 42 groups, 606 candidates and 57
unique selected comments, including groups above three. Require the summary and
CSV to agree in saved order; never rerank or apply similarity-review filtering.
`group_wording_combined` projects only original comment text, comment-source
warnings, neutral IDs and hashes into `task08c.comment_only.v2`. Group membership,
source mappings and restricted selection provenance remain outside model input.
The queue uses positions 1–57 and neutral IDs C001–C057 in that exact order.

## Review and recording

Only the current question is displayed or drafted. Give an isolated Astra
(`gpt-6-astra`) worker only its verified comment, warnings and source-only prompt,
plus this question's feedback and versions when needed. Use the recommendation
framing in prompt v2 without dropping independent asks or difficult qualifications.
No response, selection reason, ranking explanation, answer, claim or evidence may
shape wording. A null proposal is pending discussion, never automatic exclusion.

For health-risk cases, display the exact historical approved question, identifying
its historical version separately from this pass's version. Historical approval
is not approval in this pass. Do not consult downstream payloads while drafting.

Save each exact displayed version, question hash, model or historical-origin
reference, source hashes, timestamp and chat reference. Save verbatim feedback;
only an explicit approval, exclusion or deferral against the active displayed
version permits moving on. An unresolved discussion remains active until the user
explicitly defers it. A revision requires a new display and fresh approval.
Unsupported clarification cannot be made source-faithful by approval.

`group_wording_combined_chat` replays immutable JSON snapshots with predecessor
hashes and unchanged event prefixes, rejecting queue jumps, stale approvals,
blank approved text, changed source bindings and unsupported wording. Only approved
current text can appear in its derived advancing records. A pending checkpoint is
not a completed handoff and authorizes no later stage.

## Historical compatibility and reconciliation

Keep health-risk 08C approvals and all 08D/08E/08F artifacts untouched. If either
question changes, save its new exact version and a reconciliation hold referencing
its historical question identity and the affected health-risk claim review,
evidence investigation, eligibility and answer work. Revisit dependent approvals
later under explicit authorization; never silently transfer or rewrite them.
Exclusion or deferral also leaves historical work intact and prevents advancement
in this pass. Even unchanged wording requires a fresh human decision here.

## Artifact and resume contract

External namespace: `pipelines/brisbane_baylands/task_08/08c_combined_20261001_v1/`.
Keep comment-only input separate from restricted provenance and historical bindings.
Snapshot the process, prompt and implementation, and retain qualification receipts.
Preserve numbered journals, per-display presentation text and derived progress
checkpoints; never overwrite a journal. The repository's compact result record
points to the latest verified checkpoint. Resume by verifying input completion,
its hashes and the journal chain, then present only the current position.
Do not mutate the historical group register to imply a new pass is completed.

## Qualification and learning

Before first display, test v3 intake, above-cap groups, exact membership/order,
source corruption, lazy proposals, queue gating, feedback/revision, explicit
approval/exclusion/deferral, stale/unsupported approval rejection and repeatable
replay. Review the projection and approval boundary independently. Use `make fix`
and `make check`; distinguish the known Task06G commit-pin failures from new ones.

The [W3C PROV overview](https://www.w3.org/TR/prov-overview/) was rechecked
2026-10-01: distinguish versioned entities, activities and responsible actors.
Plain JSON plus hashes fit this local review; a new provenance framework is
unnecessary. Separate this pass from historical approvals so revisiting wording
cannot silently change what earlier work depended on. Technical checks establish
binding and sequence, not semantic faithfulness or authenticity of transcription.

No Label Studio projects, new Codex chats, later stages, commits or pushes.

## Current qualified checkpoint and commands

The [compact result](task08c_combined_review_result.json) identifies the current
snapshot and input completion. `input_v3` is authoritative; v1/v2 remain preparation
history. At initialization all 42 groups replayed, 57 unique selections reconciled,
534 pinned references verified, and the first historical wording matched exactly.
The 29 focused tests and independent review passed. Full validation: 3,191 passed,
1 skipped, and the three previously recorded Task06G commit-pin failures; no new
failures. No historical approvals were transferred. Current review progress is owned by the
compact result and immutable checkpoints.

Use `make validate-combined-wording-chat` with `CHAT_JOURNAL`, `WORDING_PACKET`,
`CHAT_PROMPT`, and `CHAT_PREDECESSORS` (all earlier snapshots, oldest first).
`make export-combined-wording-chat` additionally requires a fresh `DECISIONS_OUTPUT`.
The CLI verifies canonical packet and journal bytes and replays the entire chain.
First verify the pinned input completion and every referenced file's SHA-256.
For any historical-origin display, independently check exact text and source
identity against the pinned historical approved-questions export; a reference
hash in an event alone does not establish this comparison. The first display's
binding receipt records that check. Future Astra runs must save their actual
isolated prompt/output provenance alongside the display proposal.
