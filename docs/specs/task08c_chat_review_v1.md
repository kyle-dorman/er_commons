# Task 08C shared chat review v1

The new 57-comment pass uses the [combined revision](task08c_combined_chat_review_v1.md).
This v1 remains authoritative for historical health-risk approvals.

Process revision: `task08c.chat_review.v1`. This explicitly replaces the mandatory
Label Studio wording-review step for all new 08C review work. The comment-only
input contract and `task08.selection_gate.v2` entry gate remain unchanged.
One chat may review the whole selected batch, but only one comment is active
in each back-and-forth. Show its original text and current question, iterate,
and obtain an explicit disposition before moving down the queue. A case may be
left unresolved explicitly; it is never excluded automatically. Start here with
M-OSEC-241, then review O-Joint-44 in this same chat. Preserve prior combined
displays as history; do not present the remaining queue during active review. Existing proposals,
source hashes, Label Studio project 44 and its qualification artifacts remain
preserved; they are not current approval authorities. No retroactive approvals
or migrated decisions are inferred.

## Plan and boundary

1. Reference the verified comment-only packet and preserved initial Astra proposal.
   Snapshot the new prompt, process specification, schemas and validator. Keep
   restricted provenance outside the wording conversation and model inputs.
2. Present each selected comment separately, with original text, applicable existing
   comment-source warnings and a clearly identified proposed-question version.
   Preserve exact source bytes; disclose any display-only extraction normalization.
3. Save every displayed proposal and relevant verbatim human feedback. Discuss
   ambiguity, independent asks and material qualifications before disposition.
4. Record explicit approval, exclusion or unresolved decisions against the exact
   displayed version; validate export before freezing or issuing a final handoff.

Do not consult responses, selection rationales, rankings or ranking reasons,
claims, evidence, or historical answers/questions when drafting or revising.
Comment-only feedback and earlier versions within this review may inform revision.
If user clarification adds intent or facts unsupported by the original comment,
flag the difference and keep it out of approved wording. Human approval cannot
make unsupported content source-faithful. No forced simplification or backfill.

## Conversation and approval

Use stable per-comment display versions, such as `C001-v1`. A current null proposal
is an unresolved model outcome, not an exclusion or human disposition. Explain
briefly why no faithful single question was proposed and invite discussion.
One comment yields at most one independently answerable question. Preserve its
central issue, scope, uncertainty, attribution, negation and material qualifications.
Keep suitable original wording. Do not turn independent asks into a compound
question or delete difficult qualifications to obtain an answerable case.

A change to question text creates a new displayed version. Preserve its exact text,
text hash, source hashes, prompt/model provenance and the feedback that motivated
it. Feedback, suggested edits, silence, or approval of the process are not wording
approval. An explicit human approval must identify the exact displayed version;
if its target is ambiguous, clarify before recording it. Record the user's actual
statement and chat reference rather than fabricating an annotation or paraphrased
approval. Display any edited wording before requesting its exact approval.

New feedback reopens that case for discussion and invalidates advancement under
an earlier approval. A new display requires a new approval. Preserve the earlier
record as history. Approval requires nonempty text and no unresolved source-support
flag. Exclusion and unresolved decisions require the user's actual disposition;
an assistant's diagnostic outcome never creates either. The user may leave cases
unresolved. They cannot advance; finishing this pass with unresolved cases requires
an explicit recorded deferral and does not relabel them as excluded.

## Durable records and export

Use immutable journal snapshots containing ordered display, feedback and disposition
events, with predecessor hashes on continuation snapshots. Events bind neutral
source ID, original-comment and text hashes through the pinned packet, display
version, exact text, actor, timestamp and chat reference. Keep proposals distinct
from human statements and dispositions. The initial saved proposal remains an
unchanged, checksummed upstream artifact, including its rewrite/stop explanation.

`group_wording_chat` owns strict replay and export of these records. Export must
reject stale version approvals, altered hashes, missing sources, unsupported
content, malformed or ambiguous events, and empty approved text. Preserve exact
approved bytes and stable question IDs across repeated exports. Export all selected
comments with their states; only explicitly approved current text advances. Keep
native chat evidence and all versions. Technical validation verifies bindings and
state transitions, not whether a human statement was truthfully transcribed or
whether wording faithfully captures meaning; bounded review covers those checks.

The coordination handoff includes `task08c.chat_review.v1`, the source packet,
journal/export hashes, exact approved question versions, exclusions/unresolved
cases, and pending actions. A pending checkpoint is not a completed 08C handoff.
The batch register preserves its predecessor before each update. Do not start 08D.

## Qualification and learning

Source-free fixtures cover initial null proposal, feedback, revised display,
exact approval, stale/blank approval rejection, exclusion, unresolved decisions,
source/version corruption and deterministic export. Independently review the
approval boundary and documentation migration. Preserve existing 08C v1 artifacts
rather than rewriting their history; no earlier completed chat batches need replay.

The [W3C PROV overview](https://www.w3.org/TR/prov-overview/) motivates distinguishing
versioned entities, activities and responsible people. Here plain JSON and hashes
are sufficient; an RDF system or new dependency would add unnecessary machinery.
A chat event records what was displayed and what the human approved; a summary
that only says “approved” loses that critical relationship. Research checked on
2026-09-30. The three historical Task06G commit-pin failures remain carried forward.

### Prospective recommendation-framing prompt

The [v2 wording prompt](../prompts/task08c_chat_review_v2.md) incorporates the
[recommendation-framing learning](../response_comment_human_review_process.md#learning-recommendation-shaped-comments)
from health-risk review. It is a prospective prompt revision, not a change to the
v1 journal/export schema or the completed batch's pinned prompt. Snapshot and bind
its exact bytes for any future use. It has received documentation review only;
no new model qualification or batch replay is claimed.

## Maintained commands

`make validate-wording-chat` takes `CHAT_JOURNAL`, `WORDING_PACKET` and
`WORDING_PROPOSAL`. For a continuation snapshot also supply `CHAT_PREVIOUS`;
its unchanged prefix and predecessor digest must verify. The shared chat prompt
is pinned separately from the original proposal's prompt.

`make export-wording-chat` takes the same inputs plus a fresh
`DECISIONS_OUTPUT`. It preserves the full journal and exports approved exact
wording only. A pending audit with zero or partial approvals is not final batch
completion. Preserve the transcript statement and displayed-version evidence
alongside each journal snapshot; do not infer approval by parsing sentiment.
