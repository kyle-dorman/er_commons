# Task 08E — Research evidence and review each question in chat

Status: **Complete: Phase A preparation and separately authorized Phase B human
review, including nine approved answerability revisions.** The final reviewed
handoff records 49 eligible cases and four skips across all 53 cases. The user
separately authorized question revisions, citable argument framings and this
consolidation during review. No downstream 08F, new chats/projects or commit/push
was performed. Parent: [Task 08](08_curate_grouped_benchmark.md).

## Goal

Prepare evidence for every released question in one batch, then review one
question at a time in chat, with targeted additional research as needed.
Investigate the question itself as well as the approved response claims: the
response and claim list may omit important facts, context or reasoning.
Produce a reviewed handoff containing answerable questions, citable answer
framings, required and optional evidence, and explicit human dispositions.
The user expanded Phase B during review to include question revision and
answer/argument development; this work is substantive input to later 08F.

## Inputs and boundaries

- Verify the [combined 08D result](../../docs/specs/task08d_combined_review_result.json)
  and its complete sealed handoff, including required context and supplemental
  inventory. Preserve frozen questions, claim versions, support chains, source
  bindings, citation leads, exclusions, unresolved gaps and reconciliation holds.
- The initial research queue contains the 50 investigate cases in saved order.
  The user explicitly reopened C014, C020 and C024 for research on 2026-10-07,
  extending preparation to 53 cases. The four 08C deferrals stay outside the queue.
  Preserve the historical 08D holds and claim classifications unchanged.
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

## Phase B — argument-led review, one question at a time

This section records the workflow authorized during the 2026-10-07–08 review.
The original plan presented claims and citation groups before developing an
answer and prohibited question changes and answer drafting. The user changed
that approach during the first questions: review a whole question with a clear
citable argument, revise weak questions when explicitly approved, and distinguish
required evidence from optional context before presenting the citations. Later,
nine cases were revisited using the answerability standard developed in the pass.
These were user-directed amendments, not silent changes to the preparation plan.

### Presentation and evidence reasoning

Use a readable list, not a dense table, for each full-question review:

1. **Exact current question.** Show the approved wording, or clearly mark a new
   wording proposal pending approval. Aim for one focused, answerable question.
2. **Direct answer and argument.** Lead with the conclusion warranted by the
   documents, then explain the reasoning with citations for substantive facts.
   The assistant develops this framing; the user should not have to formulate it.
   Do not force a rebuttal or import reasoning from the official response.
3. **Required citations.** Give document/edition, printed or PDF pages, relevant
   excerpts and each citation's contribution to the argument. Distinguish direct
   evidence, necessary supporting reasoning or methods, and required qualifications.
4. **Optional context.** List useful background separately and explain its limited
   role. Context is not required evidence-citation credit. Its possible use in a
   more relaxed evaluation remains a later metric-design choice.
5. **Material gaps and disposition.** State unresolved issues that could change
   the answer, its scope or eligibility, then obtain explicit decisions.

Reassess citation roles before displaying the whole question. A supporting
citation must do necessary argumentative work; context must not conceal a
qualification needed to make the answer accurate. Do not add appendix citations
just for variety, inflate citation counts or require redundant passages. Preserve
all occurrence identities and full research even when the displayed argument
needs only a subset; never pool approvals across questions.

Approved response claims are research leads, not mandatory answer sentences or
independent evidence. Retain their exact wording and historical decisions in the
packet. An uncitable claim matters when the conclusion relies on it without
source support. A partially citable or tertiary claim does not automatically
invalidate the case. Call out central unsupported premises clearly and use the
reviewed source material to decide what can fairly be concluded.

Keep full passages and tables available for inspection. Separate exact excerpts
from paraphrases and inference. This text-evidence benchmark cannot depend on
untranscribed visual interpretation of a figure; use citable text when available.
Preserve source-edition warnings, exclusions, required rechecks and historical
holds in the artifacts without repeatedly overwhelming the presentation with
already-understood audit details.

### Question revision and targeted research

When a question is compound, vague, overly leading, trivial, or unsupported,
propose a focused revision and show how it changes the argument and citations.
Favor a question that requires meaningful reasoning rather than a list of
provisions; avoid gratuitous technical clues. Citation diversity is useful only
when the sources contribute. The user can retain a misleading premise when the
sources support a clear correction, or skip a weak question entirely.

Question changes require explicit approval and a new version bound to its
reviewed evidence. Preserve original questions, claims, preparation packets and
all intermediate versions. Initial-pass revisions and the later nine-case
answerability revisit are both part of 08E; do not count only the nine later
revisions as the full extent of wording changes.

Research material gaps when needed: save purpose, scope, queries, source bindings
and prior versions, then present what changed. Avoid exhaustive investigations of
report inconsistencies unless central to the answer; preserve other inconsistencies
as qualifications. Open-ended missing-information searches are not automatically
testable benchmark targets. Distinguish documented absence from an unsuccessful
search and a retrieval-runtime failure. Explain which gaps are local to a citation
group and which remain after the whole question's evidence is considered; do not
promise that another group resolves them without checking. Disclose environment
limitations when they impede research so the user can help resolve them.

### Approval, persistence and the 08F boundary

Wait for explicit approval of displayed question, answer framing and citation
scope. Save exact displays, verbatim feedback, source/claim bindings, decisions
and resume position after each interaction outside all immutable preparation
folders. Whole-question approval covers the displayed material only, not hidden
research. Preserve edits as new versions and obtain renewed approval for changed
material; do not infer eligibility or advancement from general agreement.

Before closing a question, show material remaining gaps and obtain explicit
case disposition and evidence-based eligibility. There is no second claim-by-claim
aggregate-support review. The completed handoff retains both ordinary journal
checkpoints and the nine later scoped approval overlays described below.

08E included substantial answer drafting and revision in service of evidence
review, and the user's approvals of those displayed framings are real approvals.
Do not describe that work as unperformed or require it to be repeated from scratch.
It did not execute the separate 08F reference-answer export. Later 08F should
start from these exact approved framings and scopes, updating its older contract
to the current batch before execution. Any changed final answer or citations
require review; no blanket approval of unseen 08F outputs is implied.

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
decisions. The Phase B authorization permits explicitly reviewed question revisions and
citable answer framings. It does not permit automatic advancement, silent
question/claim rewriting, source correction, new calculations, external-evidence
expansion, new projects/chats, commit or push. Final 08F execution remains separate.


## Historical Phase A authorization — three-case research supplement

On 2026-10-07 the user authorized researching C014, C020 and C024 and adding them
to the prepared 50. This reopens research only. Exact approved questions and all
08D claim decisions remain frozen; these cases have no released direct/supporting
claims, so new evidence is recorded as findings beyond claims.

- C014: investigate regional traffic changes and source evidence identifying
  which named developments were included in future regional analysis.
- C020: independently seek additional reporting triggered by detected landfill
  seepage, including requirements omitted by the response to the revised question.
- C024: test the non-contact/no-input hypothesis against eligible records. Distinguish
  documented non-contact, missing records and lack of identified input; a bounded
  unsuccessful search cannot prove no contact or input occurred.

Use the qualified five-track research, canonical source, rendering and chat
contracts. Before live research, qualify explicit reopening intake and gap-only
packets. Save authorization separately from historical human evidence decisions.
Preserve the immutable 50-case seal; publish a separately sealed three-case
supplement and a checksummed combined 53-case index referencing both. Revalidate
both inventories, saved order, source bindings, independent coverage and export
fidelity. No human review, eligibility, answer drafting, 08F, new chats/projects,
commit or push is authorized. The original preparation outcome below remains
historical evidence.

### Validated supplement and combined outcome

The [combined 53-case result](../../docs/specs/task08e_combined_preparation_53_result.json)
is the current preparation entry point. It references the unchanged original
50-case seal and the [three-case supplement](../../docs/specs/task08e_supplement_preparation_result.json).
All cases follow the original 08D saved order. Four 08C deferrals remain excluded.
The historical holds and every claim classification remain unchanged; reopening
was research-only authorization.

The supplement retains **32 findings beyond claims, 52 source occurrences and
65 query receipts** across C014, C020 and C024. It adds no approved response claims.
The combined batch contains **53 packets, 385 approved claims, 1,035 source
occurrences, 363 findings beyond claims and 1,148 query receipts**. The original
failed-query receipts remain preserved; counts do not imply every query succeeded.

C014 now includes regional traffic/VMT projections and named-project inclusion,
with explicit differences between the cumulative inventory and modeled scenarios,
High-Speed Rail exclusions, local capacity concerns and Final F1 edition limits.
C020 identifies immediate telephone and five-day written seepage reporting in
reproduced historical provisions, retaining adoption certifications, tentative
headers, conditional additional duties and unresolved current applicability.
C024 documents the bounded formal-notification account and absence of Ramaytush
from its named list, without inferring universal non-contact or no input. It retains
source count/date discrepancies and prospective tribal-participation provisions.

Each packet passed independent coverage review and full source/query validation.
An independent export audit verified complete source occurrences, exact excerpts,
table cells/notes and blank initial journals. Both component inventories and the
combined file closure passed checksum verification. Qualification and final audit
receipts live in `task_08/qualification/08e_supplement_20261007_v1/` outside the seals.
`make fix`, formatting, lint and types passed. The full suite passed 3,305 tests,
with one project-runtime FTS5 skip and the same three historical Task06G commit-pin
failures. Research used the previously qualified FTS runtime.

The combined handoff is `task_08/08e_combined_53_20261007_v1/`, with its own
`REVIEW_INSTRUCTIONS.md`. Verify it using `group_evidence_extension.verify_combined_result`.
The next separate review chat starts at C001 in saved order and stores journals
outside all preparation seals. All new human evidence decisions, eligibility and
case dispositions remain blank; Phase B and 08F have not started. No projects/chats,
commits or pushes were created.

The practical lesson is that question-first research can recover useful evidence
when no response claim advances, while preserving the difference between an
inventory and a modeled scenario, historical requirements and current applicability,
and a documented omission and a universal absence claim.

## Original 50-case Phase A preparation outcome

The new run is `task_08/08e_combined_20261006_v1/` under the artifact root.
The [research contract](../../docs/specs/task08e_batch_research_v1.md) and
[chat contract](../../docs/specs/task08e_chat_review_v1.md) replace historical
claim-only and native-project preparation for this pass. Intake verifies the
complete 08D review, preparation manifest and supplemental inventory.

Qualification is isolated in `task_08/qualification/08e_batch_chat_20261006_v1/`.
The project Python lacks SQLite FTS5; actual retrieval uses a separately qualified
system Python runtime recorded there. Failed query receipts remain preserved;
retry budgets receive explicit saved revisions. The three historical Task06G
commit-pin test failures remain unchanged. Human decisions remain blank.

### Implementation and qualification outcome

The maintained search, canonical-source validators, PDF rendering and chat
journal components now support versioned five-track question packets and
completion-last batch publication. Exact input snapshots preserve the entire
08D context, rather than reconstructing only approved claims. Each finding keeps
its own source occurrences, including repeated passages and complete tables.
Separate source occurrences are accepted only when their canonical bindings
remain exact; missing or conflicting table members still fail validation.

Qualification covers save/reload/resume, scoped display-bound decisions,
follow-up versions and stale decisions, missing citations, beyond-claim findings,
counterevidence, mixed sections, table families, original-PDF provenance and
query-intent closure. Every saved query intent must terminate in an exact receipt
or an explicitly disclosed abort. A retrieval failure is not a negative finding.
Synthetic decisions never enter the live batch.

The final implementation qualification is `qualification_v7.json` in the external
qualification directory. `make fix` passed; format, lint and type checks passed.
The full test run passed 3,296 tests, with one project-runtime FTS5 skip and the
same three historical Task06G commit-pin failures. Six actual FTS tests passed
without skips in the separately qualified search runtime. Independent review of
the final repeated-table repair passed 80 relevant tests.

The practical lessons are to separate lexical retrieval from evidence judgment,
source identity from display identity, and project requirements from observed
compliance. Full context often qualifies an apparently direct citation: an
alternative can use different assumptions, a final appendix can differ in
edition, and a mitigation deadline need not mean ecological recovery. The
[research contract](../../docs/specs/task08e_batch_research_v1.md#design-notes-and-research)
records the W3C provenance and SQLite guidance behind these choices; the
[chat contract](../../docs/specs/task08e_chat_review_v1.md#learning-note) explains
the maintained durable-journal boundary.

### Validated full-batch handoff

The [compact preparation result](../../docs/specs/task08e_combined_preparation_result.json)
binds the complete checksummed handoff and exact file inventory. All **50 cases
and 385 approved claims** are retained in saved case order, with **983 independent
source occurrences, 331 findings beyond the claims and 1,083 query receipts**.
Receipts include preserved failed attempts; they are not 1,083 successful searches.
All five research tracks were completed with explicit limits. Each case has an
independent review bound to its final packet, a readable `REVIEW.md`, complete
`SOURCES.html`, exact `review_display.json`, and blank initial review journal and
checkpoint. Full source validation and independent export-fidelity checks passed.

The external run contains `REVIEW_INSTRUCTIONS.md` and `PREPARATION_NOTES.md`.
Its `prepared_handoff.json` and `completion.json` are immutable; later human
review and follow-up versions must use a separate directory. The next authorized
review begins at **C001**, then follows the handoff order. No review chat was
created. Phase B and 08F have not started; all new human evidence decisions,
eligibility and case dispositions remain blank.

C014, C020 and C024 remain held; C013, C023, C038 and C057 remain deferred.
C042 A011 still requires human reconsideration; C044's retained claim grants no
general Chapter 16 permission; C054's contradictory numerical premises and
support-chain cautions remain unresolved. Frozen versions, source exclusions,
unanswered question parts and historical reconciliation holds were preserved.

Preparation does not resolve every evidence gap. Packets explicitly retain
failed canonical source assemblies, unverified edition equivalence, missing
operative provisions and conflicting source values or labels. They distinguish
model predictions and future obligations from observed outcomes. No source
correction, new evidence calculation, eligibility determination, answer drafting,
commit or push was performed.

Final verification receipts are stored outside the preparation seal in
`qualification/08e_batch_chat_20261006_v1/final_lead_verification.json` and
`qualification/08e_batch_chat_20261006_v1/final_export_independent_review.json`.

## Phase B human review closeout

The [consolidated review result](../../docs/specs/task08e_combined_review_result.json)
is the current handoff. All 53 cases have explicit dispositions: **49 approved
and eligible; C015, C033, C039 and C047 skipped**. C013, C023, C038 and C057 remain
outside this batch. The preparation outcomes above describe their historical
pre-review state, not the current review status.

Nine later revisions supersede the earlier displayed question and argument scope:
C005, C026, C001, C008, C034, C048, C009, C003 and C053. Each case binds the exact
approved display, final question, any wording amendment, citation roles, approval
scope and verbatim feedback. C005 and C048 retain composite display-plus-amendment
versions. C026 retains both occurrence identities for one displayed regional
context item. C034 preserves the permanent-barrier qualification; C053 explicitly
binds the displayed Appendix D context without promoting it to required evidence.

These nine approvals were saved as scoped feedback, not blanket decisions on all
packet findings. The consolidated schema therefore uses explicit scope overlays
rather than forging standard journal finding decisions or clearing pending research.
The other 44 cases retain their original final checkpoint authority. In every
case, final human decisions override earlier proposed roles; optional context is
not required citation credit. Exact prior displays, full passages and tables,
source editions, research receipts, exclusions, required rechecks and historical
reconciliation holds remain accessible through checksummed dependencies. Historical
claim decisions, including the three research-supplement cases, are unchanged.

Validation re-verifies the combined preparation and both sealed components, all
53 original checkpoint bindings and dispositions, 62 journal hash chains, all
nine canonical approval/proposal bindings, revised citation occurrence membership,
and the final export/dependency inventory. This closeout does not rerun research
or semantically replay all journal transitions. The complete prior checkpoints
remain the evidence for those original decisions. An independent read-only audit
checks the consolidated authority and scope handling before publication.

Resume position is complete with no pending case and `next_stage: null`.
`advance_to_08f` is the saved eligibility disposition only; it does not execute
08F. Approved argument framings and their review history are substantive 08E outputs,
ready for reuse in later answer authoring. Final 08F execution requires separate
authorization. No commit or push was made.
