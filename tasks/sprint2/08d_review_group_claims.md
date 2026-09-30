# Task 08D — Review one group's response claims and relationships

Status: **Provisional; execution not started.** Refine and activate from an
accepted 08C handoff before use. Parent: [Task 08](08_curate_grouped_benchmark.md).

## Abstract

Extract substantive assertions from complete linked official responses and
review their relevance to frozen questions. Run one group's cases in a separate
chat/project. Human approval establishes what the response asserts and how it
relates to the question; it does not establish truth or evidentiary support.

## Goal

Produce clear, independently assessable direct and supporting claims for later
evidence discovery, retaining the rest of the reviewed inventory for audit.

## Inputs

- Accepted [08C](08c_review_group_questions.md) frozen questions and original
  source bindings, and the corresponding 08B first-pass decisions.
- Complete resolved response closure from the accepted inventory, exact response
  passages, supplied citations, source warnings, and inherited limits.
- [Human review process](../../docs/response_comment_human_review_process.md),
  [07C.1 learning](07c1_review_claims_and_relevance.md#takeaway-from-downstream-evidence-review-2026-09-28),
  and umbrella batch/provenance requirements.
- [Artifact rules](../../docs/data_artifacts.md) and, before implementation,
  [architecture](../../docs/architecture.md).

## Outputs

- A versioned inventory of substantive response claims with exact source spans,
  citation pointers, drafting provenance and proposed relevance relationships.
- One group-specific Label Studio project using the shared claim/relationship
  review template, plus validated saved human decisions and revisions.
- Approved direct/supporting claims for evidence review, and explicit retained
  not-relevant, unclear, rejected or stopped records. Handoff destinations follow
  the umbrella task map.

## Research / learning checkpoint

Inspect the pilot's claim/relevance lessons and maintained Label Studio
[configuration](https://labelstud.io/guide/setup),
[preannotations](https://labelstud.io/guide/predictions), and
[export](https://labelstud.io/guide/export) guidance. Explain the distinction
between an assertion, a relevance relationship, and evidence support. Record
why separate source spans cannot substitute for readable claim wording.

## Plan / spec requirement

Before first use, define a shared versioned claim prompt, review template,
input/output schema, relationship rules, exporter and validators. Prefer
adapting existing maintained helpers over another extraction framework. Test
real queue-to-export behavior with separate test records, including edits,
relationship changes, unresolved claims and whole-case stops. Later batch chats
generate data using these components; shared template revisions require explicit
versioning and a prior-batch impact decision.

1. Validate frozen question identity and complete response closure. Have Astra
   (`gpt-6-astra`) inventory substantive claims before relevance filtering;
   present direct claims first without silently discarding unrelated content.
2. Write concrete assertions with source-supported subject, conditions,
   quantities, time/place/comparison, attribution, uncertainty and negation.
   Split independently assessable conclusions when their review decisions differ;
   retain necessary reasons/qualifications together. Avoid incidental-fact bloat.
3. Propose `direct`, `supporting`, `not-relevant`, or `unclear` relationships.
   Direct claims identify the question or part addressed. Supporting claims link
   to a specific direct claim and explain their material contribution; topic
   overlap alone does not suffice. Attach exact response passages and supplied
   citations beneath the claim as provenance.
4. Kyle reviews wording and relationships together, approving exact versions,
   editing, rejecting, or stopping the case. After edits, recheck affected links
   and target claims; do not preserve stale relationships by ID alone.
5. Export and validate. Only explicitly approved direct/supporting claims advance;
   not-relevant and unresolved claims remain in history. An unresolved issue
   essential to answering the question blocks the case rather than silently
   shrinking its scope. If no usable direct claim remains, obtain a human stop
   or unresolved disposition, never manufacture an answer.

Reenter pilot sources through new Task 08 claim review. Historical claim IDs may
be cross-referenced for provenance outside proposal inputs, but sealed labels
and answers are not automatically imported as current claims or approvals.

## Validation

Check inventory/source closure, stable IDs, frozen question hash, nonempty exact
approved claim text, source-span resolution, human decision bindings and valid
relationship targets. Verify no stale links after edits, no unresolved or
not-relevant claim in the evidence handoff, and no dangling support claims.
Reconcile exported counts and case dispositions. Use applicable `make` checks
for implementation and `git diff --check` for documentation.

## Acceptance criteria

- Approved claims are clear assertions with faithful source provenance.
- Every advancing supporting claim has an approved direct target and explicit
  human-reviewed reasoning relationship.
- All substantive inventoried claims retain a disposition; case-level stops and
  unresolved dependencies are explicit and prevent inappropriate advancement.
- A separate evidence chat can resume from the validated handoff alone, with
  no inherited chat context or model-approved evidence judgments.

## Review pass

Use bounded independent checks of response coverage, relationship consistency,
and exported version identity. Kyle retains semantic decision authority.

## Non-goals

Rewriting frozen questions, determining evidence support or final eligibility,
answer drafting, clustering within or across groups, or assigning benchmark splits.
