# Task 08F — Review one group's reference answers in chat

Status: **Health-risk batch complete: C001 answer v1 and C002 answer v4 approved.** The 2026-10-01 user instruction is an exception to
all-batch sequencing for this already-reviewed group. Continue in this chat;
no additional chat, project or relabeling is authorized.

## Abstract

Draft and review concise evidence-grounded answers to the exact frozen questions.
Combine answer and reasoning review in ordinary chat, retaining proposal versions,
feedback and explicit approval of the exact displayed answer. Evidence may support,
limit, contradict or fail to establish a response claim; a rebuttal is not required.

## Goal

Approve one faithful reference answer per eligible case, or preserve its human
stop, hold or unresolved disposition. Retain unresolved question scope without
requiring it to be relabeled resolved before using accepted investigation results.

## Inputs

- [Task 08 umbrella](08_curate_grouped_benchmark.md),
  [08D contract](08d_review_group_claims.md),
  [08E contract](08e_review_group_evidence.md) and
  [citation-first interface](../../docs/specs/task08e_citation_first_v1.md).
- The current saved records in Label Studio project 105, exported and validated
  against the trusted `health_risk/08e/citation_first_v1/` inputs under Task 08's
  external artifact root. The preparation result predates completed labeling;
  pending counts in that historical snapshot are not current decisions.
- Frozen M-OSEC-241 C001-v2 and O-Joint-44 C002-v2 questions, all 20 approved
  claims, 11 not-relevant claims, eight unresolved question parts and approved
  version-bound support chains, including C001 A006 → A005 → A004.
- Exact saved citation–claim relationships, notes, unresolved links, source
  warnings, full canonical evidence and provenance; the single evidence-based
  human eligibility decision for each case bound to that exact export.
- [Chat specification](../../docs/specs/task08f_chat_review_v1.md),
  [authoring prompt](../../docs/prompts/task08f_reference_answer_v2.md),
  [human review process](../../docs/response_comment_human_review_process.md),
  [sprint boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md), and
  [artifact contract](../../docs/data_artifacts.md).

The current specification and prompt supersede the older two-pass eligibility
wording and full claim-list presentation in provisional 08F. They supersede
rebuttal-first presentation guidance for this task without rewriting historical
07E or sealed upstream records. Planned shared-source v2 is future pooled review;
it does not require rebuilding project 105 or relabeling completed work.

## Outputs

- A validated current evidence export and checked eligibility bindings, with a
  concise human eligibility request if any required decision is absent or stale.
- Versioned proposals, revisions, verbatim relevant feedback, explicit approval
  or disposition records, and separate answer/citation/claim identities.
- A validated group checkpoint or final authoring handoff, batch-register update
  with predecessor preserved, and validation record retaining inherited limits.

## Research / learning checkpoint

The [07E prompt](../../docs/prompts/task07e_reference_answer_authoring_v2.md)
and [08C chat specification](../../docs/specs/task08c_chat_review_v1.md) supply
version-binding precedent, not case answers. Official
[JSON Schema object guidance](https://json-schema.org/understanding-json-schema/reference/object)
was checked on 2026-10-01: required fields and closed objects make missing or
unexpected decision fields detectable. Structural validation does not establish
human intent, evidence adequacy or eligibility. Exact displayed bytes and the
actual approval statement must therefore remain linked in the review record.
Keep process and source-audit history outside the answer unless a substantive
source limitation changes the conclusion.

## Plan / spec requirement

Use `task08f.chat_review.v1` and current prompt `task08f.reference_answer.v2`.

1. Export live project 105 into a fresh no-clobber namespace; preserve native
   annotations, task/form/reviewer bindings, all saved relationships and notes.
   Validate source, claim and question identities and reconcile unresolved links.
   Do not invent aggregate support judgments to fit an older export schema.
2. Inspect saved human eligibility records for exact export binding. If missing,
   stale or incomplete, present the remaining decision concisely with material
   source limitations and wait before drafting that case. One human eligibility
   decision per case is sufficient; 08B selection is not a second eligibility pass.
3. Start C001, then C002 after an explicit disposition or deferral of C001. Use
   Astra (`gpt-6-astra`) for every draft and revision and save actual invocation,
   prompt, input and output identities. Present frozen question, concise proposed
   answer, then the citations needed to assess it. No renewed claim inventory review.
4. Review answer and reasoning together. Discuss ambiguity about partial support
   while drafting and revising. Preserve contradiction, uncertainty and limits;
   neither blank links nor approved chains imply full support. Do not force a
   defense, change frozen questions or revise approved claims silently.
5. Save exact displayed versions and feedback. Human approval binds to the shown
   answer and its rendered citations; any later edit requires a new display and
   approval. Silence, process discussion and a revision request are not approval.
6. Validate current approvals and dispositions, save a checkpoint or final group
   handoff, and update the register. A pending eligibility or answer decision must
   remain visibly pending. Do not start 08G/08H or automatically replace stopped cases.

## Source boundary — mandatory for every answer and revision

Official responses and approved response claims identify what to investigate; they
cannot supply answer facts, reasoning or conclusions. Every substantive answer
statement must be independently grounded in actual reviewed DEIR evidence. Approval
of a claim or relationship is not a substitute for source content. Attribution to
“the response” is not an exception. Never fill a gap using response-only assertions,
including assertions about mitigation necessity or tree-barrier effectiveness.
Check source grounding during drafting without adding a human evidence pass.

## Review pass

Check faithful question scope, meaningful source qualifications, exact approval
bindings and preservation of all input records. This is a bounded integrity and
answer review, not another claim-by-claim evidence review or final aggregate-support
labeling step. Human review retains semantic and eligibility authority.

## Validation

- Reconcile the live export with exact saved annotations and all supplied input
  identities. Preserve 20 approved and 11 not-relevant claims, all eight unresolved
  question parts, original notes and links, and every approved target version.
- Confirm each drafted case has a current export-bound human eligibility decision.
  Do not require resolution of accepted unresolved scope or two eligibility passes.
- Check nonempty answers, citation membership, exact displayed-text hashes,
  predecessor versions, verbatim feedback and human approval targets. Reject stale
  approvals, altered source bindings and silent answer edits.
- Inspect Markdown/diffs and run `git diff --check` for docs. If helpers change,
  use appropriate focused checks and `make fix` / `make check`; never claim a
  carried-forward test result was rerun. Preserve the three historical Task06G
  commit-pin failures separately from any new failures:
  `test_collection_generator_preserves_historical_v38_owner_packet`,
  `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`, and
  `test_task06g_templates_are_executable_and_source_free`.

## Acceptance criteria

Only currently eligible cases with explicit approval of exact displayed answers
enter the accepted pool. Each selected case retains an approved answer, human
stop, hold or unresolved disposition; unresolved cases keep the batch open unless
Kyle explicitly defers them. An approved qualified answer need not resolve every
upstream question-gap label. All versions, support chains, evidence judgments,
warnings and provenance remain recoverable without reconstructing chat context.

## Non-goals

Other groups, new chats, project rebuilding, relabeling, backfill, new claim-wide
or aggregate-support review, automatic eligibility, hidden chain-of-thought
collection, new evidence discovery, question/claim changes, sealed upstream edits,
benchmark execution, clustering, split assignment, or starting 08G/08H.

## Outcome — health-risk complete

Kyle approved C001 answer v1 unchanged and C002 answer v4 after source-only
revision. The [completion record](../../docs/specs/task08f_health_risk_result.json)
binds `chat_review_v1/exports/approved_v1/`: two exact approved answers, their
rendered citations, eligibility decisions, full proposal/feedback history and
validated input references. Nine case-specific final citations are retained.
No 08G/08H or other-group execution follows from this bounded completion.

Both eligibility decisions bind the actual project 105 export: 43 saved tasks,
106 explicit relationships and seven unanswered proposed links. All 20 approved
claims, 11 not-relevant claims, eight unresolved question parts and approved
version-bound support chains remain intact. Answer approval does not resolve
those upstream gaps or create an aggregate-support label. C001's exploratory
appendix calculations remain outside its approved answer/citation pool.

The C002 revision exposed an important boundary: official-response claims can
guide investigation but cannot supply answer content, even with attribution.
Prompt v2 makes that rule explicit. Astra's final C002 draft used a source-only
view excluding response text and claim wording. A focused C001 check found no
response-only content; its approved version remains unchanged. Earlier C002
proposals remain unapproved and preserved.

Validation checks exact answer/display/approval identities, eligibility and
citation membership, retained scope and history. Documentation links and
`git diff --check` pass. No package code changed and the full suite was not
rerun. The three historical Task06G commit-pin failures remain recorded in the
completion validation, separate from current checks.
