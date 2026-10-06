# Task 08F chat review v1

Process: `task08f.chat_review.v1`. Owner:
[08F](../../tasks/sprint2/08f_review_group_answers.md). Prompt:
[task08f.reference_answer.v2](../prompts/task08f_reference_answer_v2.md).
The 2026-10-01 first use covers only health-risk C001 (M-OSEC-241) and C002
(O-Joint-44), in the existing chat, as an explicit all-batch sequencing exception.
This is a recording/presentation contract; no new executable validator is claimed.

## Entry gate

Export actual project 105 saved records and validate exact task/form/reviewer,
source, claim and question bindings. Preserve native annotations, normalized
relationships, notes, unresolved links and all provenance in a fresh export.
Inspect saved eligibility records against that export identity. Before drafting
any case, require its explicit human `eligible` decision with reason and exact
input binding; otherwise present the remaining eligibility decision concisely.
A stale or absent binding is pending, not a negative decision. There is one
human eligibility gate per case, with no revived preliminary eligibility pass.
Do not infer eligibility from submission, relationship labels, prior selection,
model advice or authorization to prepare 08F.

Record eligibility directly against the citation-first export; do not route it
through a legacy aggregate-claim adapter or fabricate aggregate outcomes. The
concise decision packet preserves material later-edition/external-source limits
and actual table-usability verification status. Citation relationship labels do
not imply human verification of required table-family renders. Expose any missing
verification for the human eligibility decision without creating a second evidence
labeling pass.

Preserve the 20 approved claims, 11 not-relevant claims, eight unresolved question
parts and exact approved support-chain targets, including C001 A006 → A005 → A004.
Unresolved scope can remain unresolved while accepted investigation results inform
a qualified answer. Keep every saved evidence relationship distinct: support,
partial support, context, no support, contradiction and unreviewed links. Neither
chain membership nor a support label for one claim transfers support to another.
The planned shared-source v2 interface creates no migration/relabeling prerequisite.

## Source-only answer boundary

Prompt v2 excludes official-response information as answer evidence. Approved
claims/relationships remain unchanged as investigation context; they do not license
answer assertions absent from actual reviewed source text. Attribution does not
cure this defect. Check answer facts and reasoning against reviewed sources before
display, without a new human labeling or aggregate-support step. Prior proposals
remain preserved; rejected response-derived wording receives a fresh version.

## Presentation and interaction

Activate only C001 first; proceed to C002 after explicit approval, stop, hold or
deferral of C001. Use Astra (`gpt-6-astra`) for all drafts and revisions.

Present a clear case/version label followed by:

1. The exact frozen question.
2. A concise proposed answer, with source references where needed.
3. The citations needed to assess it: source title/edition, section or table,
   printed pages and PDF pages when different, a usable link where available,
   and a short account of material support or limitation.

Do not reproduce the full claim inventory, chain diagrams, technical identifiers,
process history or provenance hashes in the main review text. Preserve these in
the bound records. Include substantive limitations in the answer when needed to
avoid overstatement. Optional short review notes may clarify an ambiguity that
requires discussion; do not create another evidence checklist or labeling pass.

Review answer and reasoning together in normal chat. Evidence may undermine a
claim or leave it unestablished. Explain partial support through careful wording
without changing saved relationships. No final aggregate-support label is required.
A requested question/claim/source change must return to its owning stage through
an explicitly authorized revision; do not silently change the bound inputs.

## Durable records

Save under `task_08/health_risk/08f/chat_review_v1/` beneath the configured data
root, in new no-clobber version directories. Preserve source artifacts in place.
Use plain JSON and exact UTF-8 Markdown snapshots; reuse maintained hashing and
record helpers when suitable. No new workflow engine or dependency is necessary.

| Record | Required content |
| --- | --- |
| Input binding | Group/case/comment IDs; exact question version/text hash; 08D handoff; 08E export and completion identities; eligibility decision identity; source/citation closure; complete retained claims, gaps, relationships, notes and warnings, directly or by checksummed reference. |
| Eligibility | Case, disposition, reason, human reviewer, actual statement or saved annotation reference, timestamp, exact evidence-export identity and input binding. Preserve prior decisions separately. |
| Proposal | Stable version such as `C001-answer-v1`; predecessor when present; actual Astra model/invocation; prompt and rendered-input paths/hashes; raw output; exact answer and citation IDs; referenced approved claim versions; exact displayed Markdown path/hash. |
| Event journal | Ordered display, feedback and decision events; case/version; actor; timestamp; actual chat reference; verbatim relevant user statement; target displayed-text hash. Continuation snapshots preserve prior events and record predecessor hash. |
| Decision | Explicit human approve, stop, hold or unresolved disposition, with reason where needed; exact displayed version/hash for answer approval; evidence/eligibility binding; event reference. Missing decision stays pending. |
| Checkpoint/handoff | Current state for both cases; all version/event references; final answer/citation/claim lists for approved cases; unresolved links/gaps and warnings; validation; counts; pending action; completion status. |

Do not invent timestamps or platform message IDs when unavailable. Preserve the
available transcript reference and state any capture limitation. The displayed
snapshot includes frozen question, proposed answer and rendered citations; record
answer-only bytes/hash separately. Record a display event only after actual display.
Raw model output is not proof of what the user saw.

Feedback reopens the current answer for revision without erasing earlier approval
history. Any change to answer or displayed citation content creates a new version
requiring fresh approval. If an approval target is ambiguous, clarify it instead
of assigning it automatically. Process feedback and silence never create approval.
No machine validation can establish human intent from sentiment.

## Validation and publication

Before each display verify frozen-question identity, supplied citation membership,
source locations and unchanged approved claims. Before accepting an answer verify
its exact displayed bytes, approval statement/target, current export-bound
eligibility and complete version history. Preserve prior history when an input
revision invalidates downstream approval. No final answer may silently differ
from its approved display.

Check all selected cases are accounted for and every record resolves; distinguish
pending checkpoints from completed handoffs. Preserve previous batch-register
bytes before updating only this group's stage status. Keep the three historical
Task06G commit-pin failures in the validation record; distinguish carried-forward
checks from current checks. No 08G/08H follows from this bounded pass.

The [JSON Schema object reference](https://json-schema.org/understanding-json-schema/reference/object)
was checked on 2026-10-01. Explicit required fields and closed records help detect
missing or accidental data; cross-record hashes and state checks still require
application validation. A concise review display is compatible with complete
provenance because immutable records retain the evidence behind each version.
