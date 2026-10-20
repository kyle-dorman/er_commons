# Task 11D.2 — Resolve specification, reference scope and metadata interfaces

Status: Offline corrections implemented (2026-10-17); exact C014 question approval pending.

## Abstract and goal

Retain V6b's explicit field contract and invented examples unchanged. Resolve the
11D.1 specification and metadata mismatches without rewriting historical scores.
Prepare the exact C014 question clarification for approval under the inherited
08E question-version policy; preserve its intentionally approved reference.

## Inputs and outputs

Inputs: 11D.1 outcome and sealed result; fixed six C041, C017, C019, C014, C037,
C056; public specification; frozen 09G guide/policies; Task 10 delivered packets;
C014's existing approval lineage. Outputs: retained-prompt hash, prospective
specification and adjudication note, explicit offline edition projection adapter
and tests, exact question proposal, validation and routing. Large audit artifacts
belong under the external Task 11 artifact root in a fresh 11D.2 directory.

## Plan / research and learning

1. Independently audit question/reference scope, metadata projection and manual
   materiality; integrate findings before implementation.
2. Pin V6b. Clarify what automated G/S/C and separate manual conclusion-source
   review establish. Require a concrete interpretation effect for an omission.
3. Prepare a new question that exposes both supplied editions and future-growth
   analysis without exposing answers. Do not change the reference or publication.
4. Add an opt-in offline projection that places audited bibliographic edition in
   the existing canonical locator, excluding curator approval. Bind mapping,
   exact input and payload to new identities. Legacy projection stays unchanged.
5. Validate offline, independently review, and present the exact question for the
   approval required by 08E before activating any changed-question condition.

Use the primary research recorded in 11D.1: explicit public requirements, human
calibration and separate correctness/citation measurement. Local authoritative
contracts determine versioning. A metadata correction changes the evaluation
condition even when model/prompt/schema remain identical; it cannot retroactively
repair a sealed score. Public task clarity is distinct from feeding reference
answers or evaluator feedback to generation.

## Limits and non-goals

Zero live generation, judge or token-count calls; zero new spending, retries or
repeats. This task resolves interfaces offline, not candidate performance. Keep
100K as the future authorized input ceiling, not a dispatch authorization here.
No new prompt version; no baseline promotion; no 11E, remaining 13 development,
locked-test or reserved content. Do not mutate Task 10, 09G policies/configs,
approved references or any sealed results. The new adapter is not wired into
legacy production dispatch; future runs require explicitly versioned plans.

## Validation and acceptance

Verify prompt hash, fixed-six-only inventory, bibliographic/curation separation,
exact source preservation, strict mapping/identity failure cases, frozen G input
validation and unchanged legacy path. Run make fix, make check and git diff --check
for code. Save independent bounded review. A pending exact-question approval is
reported as pending, not silently treated as a published benchmark revision.

## Review pass

Three bounded independent audits cover metadata/architecture, C014 provenance,
and specification/materiality. One final independent implementation/doc review
checks scope, leakage, identities and preservation.

## Outcome

V6b is retained byte-for-byte as the diagnostic comparator, not a promoted
baseline. Its field contract and examples remain intact. The separate
[answer review contract](../../docs/specs/task11d2_answer_review_contract.md)
clarifies automated scope, manual conclusion-source review and omission
materiality. C037's precise mitigation omission alone does not establish a
material defect; historical findings are preserved as sensitivity evidence.

The [C014 question proposal](../../docs/specs/task11d2_c014_question_proposal.md)
exposes the intentionally approved two-edition and future-growth scope. Reference
content needs no factual correction and remains unchanged. The exact proposed
question was displayed for approval; no reply has yet approved it. The inherited
08E exact-question/version rule keeps activation pending.

The [metadata correction](../../docs/specs/task11d2_metadata_projection.md)
separates bibliography from curator qualification and adds an offline adapter
using G's existing locator field. All 23 fixed-six passages are mapped; six
bibliographic-only generation records are staged. Both V6b repeats yield 47
fresh, schema-valid G projections, with exact source/candidate preservation and
new projection-bound sample identities. No live dispatch integration or score
improvement is claimed. Claims already made by a candidate about curator approval
remain claims; adding edition metadata does not establish them.

The new [result pointer](../../docs/specs/task11d2_result.json) binds artifacts,
validation and review under
`pipelines/brisbane_baylands/task_11/validation_11d2_20261017`.
There were zero generation, judge or count calls and zero new spending. Prior
accounting uncertainty and reservations are unchanged. The 100K ceiling remains
available for a later explicitly bounded comparison.

### Learnings and next action

Examples improved observed consistency (V6b 10/12 diagnostic passes versus V5b
5/12), while V7's extra procedure regressed to 6/12. These are tuning observations,
not estimates of benchmark accuracy. Further prompting cannot repair hidden
requirements or unequal metadata visibility. Fix those interfaces first, then
measure any gain under distinct conditions rather than rewriting old results.

Next: obtain the exact C014 wording decision. Before any new live comparison,
integrate the approved question and metadata condition into fresh generation and
evaluation manifests, preserve V6b, predeclare bounds/repeats, and validate native
request counting and replay. This task does not start 11E or open additional cases.

### Completed validation

`make fix` passed without formatting changes. `make check` passed with 4,103
passed tests and one skipped (32 new projection tests). `git diff --check`
passed. Independent review passed after adding a fail-closed check of each saved
plan against its sealed completion hash and byte size before derivation. All
221 protected bindings match. Offline development failures and their fixes are
retained in the external validation directory. No provider was constructed by
the projection audit and no live request was dispatched.

## Subsequent decision — 2026-10-18

The user rejected the detailed question proposal because it gives a future search
agent too many clues. Its sealed proposal/result remain historical records, not
current pending approvals. The user then authorized testing the lighter wording
that replaces only “the DEIR” with “the environmental review”; see
[11D.3](11d3_test_light_question_wording.md). Neither this decision nor the test
changes the approved reference or activates the staged metadata correction.
