# Combined claim and relevance review v1

Task 07C.1 uses a separate adapter and project. Original 07C remains immutable.
This contract describes response assertions, not truth, evidence support,
or answer adequacy. Kyle approved the combined UI and the O-Joint-19 review;
remaining case content still requires separate human acceptance.

## Inputs and proposal

`er_commons.task07c1.proposal.v1` binds a fresh proposal ID, the verified 07C
packet manifest and claim-input byte hashes, and the exact predecessor review
file/hash. The source packet remains sealed in place. The new task carries its
complete source, closure, concerns, citations, warnings and inherited limits.
The old instruction to extract only relevant claims is explicitly superseded;
it remains historical packet provenance, not the new extraction policy.

Each proposal claim has a durable `claim_id`, a human-readable `local_id`, text,
exact `source_refs` (passage ID and unique verbatim quote), relationship,
`concern_ids`, `supporting_claim_ids`, a model rationale, and prior-edit note.
Prior edits are never silently presented as approved restorations. New suggestions
are unreviewed even when their wording matches an earlier approval.

Coverage is a passage-by-passage argument inventory. Every source passage,
including supplemental footnotes, has entries mapping every substantive argument
to claims. Repeated arguments map to an existing claim; headings, page furniture,
and citation-only material have an explicit exclusion reason. There is no claim
count cap. Coverage accounting is a reviewed drafting judgment: passage membership
validation alone does not prove semantic completeness.

## Relationships and uncertainty

- `direct`: one or more reviewed concern IDs; no claim targets.
- `supporting`: one or more claim IDs; no concern targets. Every target path must
  terminate in a direct claim. Unknown targets, self-links and cycles fail validation.
- `not_relevant`: no targets; preserved in the full export, outside evidence work.
- `unclear`: no forced targets. The proposal supplies an explanation. The reviewer
  can correct any label without a mandatory written rationale.

Faithfully represented uncertainty can coexist with an approved case. Only direct
and valid supporting claims from approved cases are candidate evidence-work items;
unclear claims remain an explicit held list and prevent whole-case readiness.
No 07D execution is authorized by this prototype.

## Native form and stable identity

Fixed slots use independent native TextArea and Choices controls. Each slot has
editable wording, passage IDs, a relationship radio group, target IDs, and an
optional removal checkbox. The model rationale and original quote are read-only.
A selected removal deletes a proposed or newly written claim, distinct from
`not_relevant`. A removed claim remains in the export with its original proposal
and saved fields. A removal click on a spare slot with no proposal and no current
claim text is instead recorded under `unused_slot_removals`, preserving its slot
identity and saved fields without counting a substantive deletion. This records
the exported state, not an inferred history of earlier typing.
Approved reviews reject any surviving link to a removed or empty claim.

Task data carries a slot-to-identity map. IDs are allocated independently of slot
positions; each proposal or potential added claim has a durable ID and unique
short alias. Editing does not change identity; a revision hash records changed
content. Spare slots have no text, label, targets, or prediction. Unused slots do
not become claims and need no label or removal click. Adding uses a spare slot; splitting keeps the original identity
for one part and uses a new identity for the other. No inferred split/merge ancestry.

Choose capacity after complete extraction, with at least four spare slots.
Overflow never truncates: save partial work as Needs context, export native tasks,
annotations and drafts to a checksummed snapshot, then prepare a fresh larger form
and separate project retaining all existing identities and human fields. Verify
field-by-field migration before resuming; preserve the prior project and keep
migrated human records separate from model suggestions. Do not clear drafts or
mutate a saved form to create space. The prototype tests both the preservation transform and a native migration in
a separate QA project. Operational migration still requires its own reconciled
execution record: explicitly rebind/import the preserved annotation as a human
record, retain its original identity separately, and verify reload before resuming.
The `migration` field alone does not seed an editable native annotation.

## Review and provenance

`er_commons.task07c1.review.v1` compares exported task data to a trusted rebuild.
It retains immutable source/proposal bindings, slot identities, all raw annotation
results, reviewer and annotation/task identities, timestamps, export identity,
content revisions, retained claims, removals, unused-slot removal actions, added
claims, unresolved accounting,
and per-slot/graph validation errors. The full native annotation is retained and
hashed. Unknown or duplicate fields and foreign object/control bindings are errors.

Explicit `approved`, `unclear`, or `needs_context` is required; no prediction
contains case status. Approved records must contain at least one valid retained
claim and pass all references/graph checks. Unresolved records preserve valid
partial claims and invalid raw fields with errors, but cannot advance. Original
proposal quotes are provenance and never automatically attributed to edited text;
final claims bind the current full passages.

## Learning and validation

Installed Label Studio Community 1.23.0 is the target. Named fixed controls avoid
assuming dynamic paired rows. TextArea's `editable` plus `transcription` settings
keep a single text value editable; Choices gives each slot its own relationship.
This trades a longer form and typed short targets for a simple native implementation.
See [TextArea](https://labelstud.io/tags/textarea),
[Choices](https://labelstud.io/tags/choices), and
[configuration constraints](https://labelstud.io/guide/setup).

Validate the actual labeling queue, source text equality, independent labels,
blank slots, add/edit/remove, chains and invalid links, partial saves, reload,
native export and overflow preservation. QA uses a separate project and never
creates human approvals in the trial. Model-version selection must match the
prediction. Prior projects and sealed inputs are compared before and after.

Installed-browser finding: Community 1.23.0 gives radio inputs the Choice value
as their HTML name. Repeating values across slots caused checked-state collisions.
The generated form uses unique internal values, friendly `html` display labels,
and semantic export aliases. Actual-queue tests cover simultaneous selections
and reload; see [Choice parameters](https://labelstud.io/tags/choice).
