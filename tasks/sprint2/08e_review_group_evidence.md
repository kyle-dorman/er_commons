# Task 08E — Research evidence and review each question in chat

Status: **Plan updated 2026-10-06; combined-pass execution not started.**
This update authorizes documentation only. Research and implementation await an
explicit start request. Parent: [Task 08](08_curate_grouped_benchmark.md).

## Goal

Prepare evidence for every released question in one batch, then review one
question at a time in chat, with targeted additional research as needed.
Investigate the question itself as well as the approved response claims: the
response and claim list may omit important facts, context or reasoning.
Produce a reviewed evidence handoff, not a draft answer.

## Inputs and boundaries

- Verify the [combined 08D result](../../docs/specs/task08d_combined_review_result.json)
  and its complete sealed handoff, including required context and supplemental
  inventory. Preserve frozen questions, claim versions, support chains, source
  bindings, citation leads, exclusions, unresolved gaps and reconciliation holds.
- The initial research queue contains the 50 investigate cases in saved order.
  C014, C020 and C024 remain held; the four 08C deferrals stay outside the queue.
  Reopening a held case requires an explicit decision.
- Use eligible Draft EIR material and appendices under the
  [sprint evidence boundaries](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md).
  Responses supply claims and leads, not evidence. Preserve the 08D Modified
  Alternative 1/Chapter 16 exclusions, explicit exceptions and required rechecks.
- Keep each question's research and review self-contained. Do not deduplicate
  sources within or across questions or build a pooled source-review queue.
  The same source may appear wherever relevant; decisions stay question-specific.
- Preserve historical work separately; do not import its approvals. Prior
  workflows and outcomes are in the [historical record](08e_historical_workflows.md).
  This task supersedes the shared-source/Label Studio plan for the combined pass.

## Phase A — batch research before human review

1. **Plan each question's search.** Cover all five tracks: direct citations for
   approved claims; known question gaps; relevant definitions/acronyms/methods;
   broader context omitted from the response or claims; and counterevidence.
   Use the original comment, full question and required 08D notes to identify
   assumptions, alternative explanations and potentially missing information.
2. **Search beyond the supplied references and claim wording.** Resolve citation
   leads, search the eligible corpus independently, and inspect surrounding
   sections, technical appendices, assumptions and relevant cross-references.
   Seek both confirming and conflicting material. Finding apparent support is
   not a stopping rule; every track must receive a recorded search or a reason
   it does not apply.
3. **Keep research bounded and restartable.** Save each case's search plan and
   effort budget before execution, with follow-up allowance for each track.
   Set these by question complexity rather than inheriting the old claim-only
   query caps. Record actual queries, inspected hits, dispositions, failures,
   budget stops and remaining leads. Expand a budget through a saved, justified
   revision; never imply an exhaustive search or hide an unsearched track.
4. **Prepare source-grounded findings.** Use Astra for advisory research/proposals
   with exact inputs and model provenance saved. Retain exact passages or complete
   table families, document/edition, printed and PDF pages, canonical anchors,
   captions, notes and material limitations. Verify table content against renders;
   distinguish agent checks from any still-required human usability check.
5. **Assemble one review packet per question.** Group evidence logically with the
   claims or question parts it bears on. Propose Support, Partial, Context,
   Not support or Contradicts with a concise reason. Save gap findings,
   definitions and broader context independently when no approved claim fits;
   never force them into a claim link or silently rewrite the claim list.
6. **Validate and publish the batch.** Check coverage, exact source bindings,
   exclusions and material counterevidence independently. Save a checksummed
   “prepared, awaiting human review” handoff with packets, search receipts,
   unresolved issues and resume position. All human decisions start blank.
   Finish the batch before starting routine question-by-question review; identify
   any blocked case explicitly rather than silently omitting it.

## Phase B — one question at a time in chat

Present the full exact approved question and a readable evidence overview:

- **Evidence for the claims:** exact claim wording grouped with its citations,
  key source excerpts, proposed relationships and limitations.
- **Evidence beyond the claims:** findings for gaps, definitions, methods and
  missing context, with citations and a clear explanation of their relevance.
- **Problems still open:** counterevidence, inconsistencies, unanswered question
  parts and claims for which the bounded search found no suitable citation.

Use clear document titles and page references. Keep full passages/table families
available in the saved packet and show them when needed for interpretation or
on request. Separate verbatim text from summaries. “No citation found” describes
search results, not proof that evidence does not exist.

Discuss feedback and run targeted additional searches when requested or needed
by the discussion. Save the purpose and scope before searching, then show what
changed and what remains unresolved. Do not rerun the whole batch. Wait for
explicit acceptance, rejection or deferral of displayed findings/relationships;
acceptance never covers hidden material. Reopen affected decisions after edits.

After each interaction, save exact displayed versions, verbatim feedback,
decisions, source/claim bindings and queue position. At the end of the question,
show remaining gaps and obtain an explicit case disposition: advance to 08F,
hold or stop, with evidence-based human eligibility and its reasons. Bind it to
the current reviewed evidence. No second claim-by-claim aggregate-support pass;
answer composition and adequacy remain for separately authorized 08F.

## Implementation, validation and completion

Before live research, inspect maintained Task07D/08E search, canonical-source and
rendering helpers and the 08D chat journal/export pattern. Reuse those boundaries;
version the broader research prompt, per-question packet and chat decision/export
contract. Older search prompts and Label Studio exporters are historical
precedent, not the current execution contract. Keep artifacts under
`ER_COMMONS_DATA_ROOT` per the [artifact contract](../../docs/data_artifacts.md).

Qualify save/reload/resume and export with separate synthetic cases: gap-only
findings, definitions, conflicting evidence, missing citations, table families,
scoped batch approvals, follow-up research, edits and stale decisions. Independently
review search coverage and export fidelity. Reject missing bindings, lost context,
unsupported summaries and model proposals mistaken for human decisions.
Run focused tests and `make fix` / `make check` for implementation; document
historical failures separately. For documentation only, check links and
`git diff --check`.

Completion requires every input case to have an explicit disposition, all accepted
findings/relationships bound to reviewed versions, and a validated handoff retaining
all searches, prior versions, rejected findings, unresolved issues and eligibility
decisions. No automatic advancement, question/claim rewriting, source correction,
new calculations, external-evidence expansion, answer drafting, new projects/chats,
commit or push is authorized by this plan.
