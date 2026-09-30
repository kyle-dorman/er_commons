# Task 08F — Review one group's reference answers in chat

Status: **Provisional contract; execution has not started.** Revise from the first
accepted 08E batch before activation. Repeat for each group in its own stage chat.

## Abstract

Draft and review evidence-grounded rebuttals for one group's surviving cases.
Combine answer and reasoning review in ordinary chat, preserving exact proposal
versions and explicit human approval as structured handoffs.

## Goal

Approve one faithful reference answer per surviving case, or record why the case
stops. An answer must address its frozen question using the reviewed Draft EIR
evidence; it must not force a defense that the sources cannot support.

## Inputs

- [Task 08 umbrella](08_curate_grouped_benchmark.md) and the named group's
  accepted [08E evidence handoff](08e_review_group_evidence.md).
- [Human review process](../../docs/response_comment_human_review_process.md),
  [current answer prompt](../../docs/prompts/task07e_reference_answer_authoring_v2.md),
  [sprint evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md),
  and [artifact contract](../../docs/data_artifacts.md).
- Frozen questions, approved claim/relationship lists, full reviewed evidence,
  support/context citation pools, warnings, and both human eligibility decisions.

## Outputs

- A shared versioned chat presentation and decision-recording specification.
- Per-case proposals, revisions, relevant feedback, explicit approval or stop
  records, and exact final answer/citation/claim lists.
- A validated, versioned group authoring handoff retaining all decision history,
  approved input identities, citation pools, and inherited limitations.

## Research / learning checkpoint

Review the 07E prompt and closed outcome for exact-version approval and citation
handling. Before implementation, inspect the official
[JSON Schema validation guidance](https://json-schema.org/understanding-json-schema/reference)
for maintained decision-record validation. Preserve a short explanation of why
chat approval needs a durable binding to the displayed text and why source-audit
notes should stay separate from the answer unless they change its conclusion.

## Plan / spec requirement

Write a brief first-use spec for the common presentation, versioning, approval
capture, citation rendering, and export format. Reuse it for later group batches.

1. Open an isolated 08F chat with only this group's accepted authoring packet and
   stage instructions. Do not load unrelated labels or sealed pilot answers as
   examples/defaults; reentering pilot cases receive fresh proposals and review.
2. Use Astra (`gpt-6-astra`) for every draft and revision; record actual model,
   prompt, input, and output identities. Present each case in this order: frozen
   question; approved claims and relationships; citation summaries with roles
   and locations; one proposed rebuttal.
3. Lead with the supported conclusion and explain its bearing on the precise
   contention. Retain conditions and uncertainty. Keep examples' subjects,
   units, dates, and calculations distinct. Explain omitted sources to the
   reviewer rather than padding the reference answer with them.
4. Receive human feedback and revise one case at a time. Review answer and
   reasoning together. Preserve proposal versions and feedback; an approval
   binds to the exact displayed version, never to a later silent edit. Silence,
   process discussion, or a revision request is not approval.
5. Keep separate citation and claim lists plus the final answer. Use only supplied
   citation IDs and deterministic source-label rendering; do not require new
   statement-to-evidence mappings. Context citations remain optional and cannot
   replace support. If needed evidence or claim changes, return to the owning
   stage and reapprove affected material before continuing.
6. Save accepted answers and stops, validate the batch, and update its completion
   record. Preserve ordinary attrition without automatically backfilling groups.

This stage uses chat, not a new Label Studio answer form. A batch chat generates
case data using the shared schema; it does not create its own serialization or
approval conventions. Deliberate shared revisions record their effect on earlier
batches. No cross-case clustering occurs here; 08G starts after all group
authoring batches are complete, including explicitly closed empty batches.

## Review pass

Check faithful question scope, evidentiary support and qualifications, exact
approval binding, and maintainability of any small export helper. Human review
owns semantic acceptance; model review cannot mark an answer approved.

## Validation

- Validate nonempty final answers, source/case/question versions, supplied citation
  membership, and exact displayed-text approval bindings.
- Confirm both eligibility passes and all prerequisite reviews for advancing cases.
- Verify revisions preserve earlier history and invalidated approvals cannot be
  exported as current; validate explicit stops and unresolved dispositions.
- Compare saved records with the actual approved chat version. Run focused checks
  and `make fix` / `make check` for helper changes; `git diff --check` for docs.

## Acceptance criteria

- Every case has a reviewed final answer, a human stop, or an explicit unresolved
  status; only approved, fully eligible cases enter the accepted pool. Unresolved
  cases keep the group open unless Kyle explicitly defers them outside this
  pass and closes the batch under the umbrella's deferral rule. An unresolved
  record alone is not a completed group handoff to 08G.
- All substantive reasoning is grounded in reviewed evidence, with no invented
  source citations or unapproved question changes.
- The handoff preserves versions, provenance, warnings, and decisions without
  requiring downstream chats to reconstruct this conversation.

## Non-goals

Label Studio answer-form development, hidden chain-of-thought collection,
benchmark judging, split assignment, clustering within this group, automatic
approval, or modification of sealed Task 07 artifacts.

## Outcome

Not started. Record the shared setup and per-group completion evidence, accepted
and stopped counts, learning, and readiness for the eventual whole-pool 08G gate.
