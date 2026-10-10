# Task 08E evidence chat checkpoint contract v1

This contract qualifies preparation and evidence discussion for the combined
[08E pass](../../tasks/sprint2/08e_review_group_evidence.md). It does not start
human review, determine eligibility or authorize 08F. Historical Label Studio
projects and approvals remain separate.

## Authorized Phase B workflow amendment

For the completed 53-case pass, follow the task's
[argument-led review](../../tasks/sprint2/08e_review_group_evidence.md#phase-b--argument-led-review-one-question-at-a-time).
The user authorized question revisions and citable answer/argument development
within 08E. Present the full question, a direct source-grounded answer, required
citations, optional context and material gaps as a readable list. Claims guide
research; they are not a checklist of mandatory answer statements. Preserve all
original claim decisions and prepared inputs. This amendment changes the human
workflow, not the journal API's validation rules or the sealed preparation.

The user approved exact displayed question/answer/citation scopes and eligibility.
These approvals must survive into later 08F intake; 08F was not executed and
unseen or changed final answers are not preapproved. Do not repeat the completed
evidence review merely because its answer development occurred during 08E.

## Ownership and boundaries

`group_evidence_research` owns complete research-packet validation, canonical
source validation, query receipts and preparation sealing.
`group_evidence_chat` owns exact displays, scoped evidence decisions, feedback,
follow-up purposes, revision history, durable journal replay and checkpoint
export. It uses the maintained Task08D deterministic JSON encoding and SHA-256
helpers and its exclusive-lock, append-and-fsync journal pattern. Keeping the
journal outside the preparation seal allows later review without changing
prepared evidence. Hash chains detect accidental or unacknowledged mutation;
they do not authenticate a reviewer. Preserve the original chat reference.

The packet schema is `task08e.research_packet.v1`; the journal schema is
`task08e.chat_review.v1`. Intake retains the entire packet and binds its exact
JSON digest. The local chat guard checks blank proposal decisions, exact approved
claim membership and source occurrence bindings. It does not replace the research
sealer's canonical source, eligible-document, table/render or five-track checks.
A review chat must verify that seal before using this API.

## Display and decision semantics

Each display saves its actual rendered text, full frozen question/claim/context
record, exact selected finding versions and complete referenced source payloads.
Full table families, notes and render bindings remain in those payloads. Citations
bind both `occurrence_id` and `candidate_id`; repeated candidates are never pooled
or deduplicated. The display differentiates verbatim excerpts, approved claim
wording and advisory findings beyond claims. Search limits and gaps remain visible.
No suitable citation within a bounded search is not evidence of absence.

An explicit accept, reject or defer event must bind the current display digest
and enumerate its finding IDs. Each finding includes its displayed proposed
relationships and exact citation occurrences. A scoped batch approval covers
only the enumerated displayed findings; hidden findings cannot be accepted.
Every event retains actor, timezone-bearing time and original chat reference.
Feedback is saved verbatim. Model proposals never populate human decisions.

A standard API packet revision preserves the entire previous packet in the journal, binds its
predecessor digest and cannot change frozen questions, approved claims or
required context. It conservatively reopens **all** evidence decisions for that
question, because a source/context edit may affect another relationship. The
previous decisions remain available in history. A fresh display is required.
This restriction describes that API operation, not a prohibition on the later
user-authorized question revisions. Those use separately versioned review inputs
or explicit approval scopes, retaining the predecessor and renewed human approval;
do not mutate frozen preparation or claim history to make them fit the API.

A targeted follow-up starts with a saved search identifier, current packet digest,
purpose, scope and effort budget. The result must reference that prior plan and
retain query receipts and remaining limits. It does not silently revise the
packet or rerun a batch. A separate revision records new findings.

## Persistence and export

`new_journal(packet)` creates blank production state in preparation mode, which
rejects every human interaction event. Explicit `phase="review"` is reserved for
a separately authorized review chat; synthetic qualification uses that mode.
The phase and synthetic marker are included in the journal hash-chain root. `render_display` creates
a display payload; `add_event` validates an in-memory appended copy.
`append_event` writes one validated JSONL event under a file lock and fsyncs it.
`load_journal` reconstructs and validates the entire chain; a torn final line
fails closed and must be preserved before recovery. `replay` returns pending
finding IDs and the first pending ID as the question-local resume position.
The batch manifest owns saved case order and the question-level position.

`export_review(..., preparation=True)` is the Phase A export: it requires a
completely empty interaction journal and returns **prepared, awaiting human
review**, blank human decisions and null eligibility, disposition and next stage.
`preparation=False` creates an evidence-review checkpoint retaining the complete
journal, current packet, previous displays/revisions, rejected/deferred decisions,
follow-up receipts, unresolved findings and resume position. A separate case display binds the complete current packet and all decisions.
An explicit human case disposition may then record advance to 08F, hold or stop,
with eligibility and reasons. Advancement requires a current decision for every
finding, no deferred finding, all follow-up results saved and explicitly positive
human eligibility. Hold/stop may retain unresolved eligibility. New evidence
decisions, revisions and follow-up research invalidate any earlier case closeout.
Export records the requested disposition but never executes or starts 08F;
`next_stage` remains null. No production case disposition is created in Phase A.

### Consolidated approved-scope overlays

The [final review result](task08e_combined_review_result.json) combines the original
53 case checkpoints with nine later approved display scopes. These later approvals
were saved as feedback and scope records; they are not standard per-finding
`decision` or `case_decision` events. The consolidated handoff explicitly binds
the final question, exact proposal display, any amendment, verbatim approval,
eligibility, citation occurrences and prior checkpoint.

A scope overlay supersedes only the displayed material it identifies. It does
not clear pending finding IDs, accept undisplayed packet material, or claim a
standard API advancement was replayed. Earlier complete checkpoints retain the
full research and historical decisions. Preserve composite display-plus-amendment
versions and detailed required/context roles. The handoff's validation statement
distinguishes checked hashes and scope bindings from semantic journal replay.

## Qualification and separate review chat instructions

The synthetic tests in `tests/test_group_evidence_chat.py` exercise missing
citations and gaps, definitions, counterevidence, complete table payloads, scoped
approvals, hidden-material rejection, follow-up planning, exact reload/export,
mutation detection, torn journals and stale-decision invalidation. Synthetic
journals are explicitly marked and kept outside dataset artifacts.

After Phase A completes, open a separate review chat only when explicitly
requested. Give it the compact preparation result pointer and this contract.
Verify the complete sealed batch, select the first pending case in saved order,
and create a separate mutable journal. Present the exact question and readable
argument-led evidence overview as specified in the Phase B amendment above.
Retain full claims, beyond-claim findings, excerpts and research limits in the packet. Save every displayed version and verbatim response. Do not
interpret approval of one finding as approval of hidden material or eligibility.
Obtain separate authorization for human review before entering review mode.
At case closeout display remaining gaps and obtain explicit disposition and
evidence-based eligibility reasons before publishing any reviewed handoff. The
authorized answer framings belong to 08E review; final 08F execution is separate.

## Learning note

The repository's existing journal pattern is sufficient; no database or workflow
engine is needed. The Python standard library's
[`os.fsync`](https://docs.python.org/3/library/os.html#os.fsync) and
[`fcntl.flock`](https://docs.python.org/3/library/fcntl.html#fcntl.flock) provide the
same explicit durability and writer coordination boundary used by Task08D.
Whole-question invalidation is deliberately conservative and easier to audit than
an unproven dependency inference algorithm.
