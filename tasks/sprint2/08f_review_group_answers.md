# Task 08F — Approve structured, cited reference answers

Status: **Complete — 49 approved answers, zero pending decisions.** The
[consolidated reviewed result](../../docs/specs/task08f_combined_review_result.json)
is the current authority after Phase B and both bounded evidence reviews.
Earlier preparation and review seals remain historical inputs. This closeout
starts no 08G/08H, benchmark or judge runs and includes no commits or pushes.
The earlier two-case [health-risk outcome](08f_historical_health_risk.md) remains
preserved separately.

## Goal and scope

Finalize one structured, cited reference answer for each of the **49 eligible
cases** in the completed 53-case 08E pass, or retain an explicit human stop, hold
or deferral. Reuse the approved 08E questions, answer framings and citation roles;
do not restart their evidence review. Follow saved batch order, beginning at C001.
C015, C033, C039 and C047 are skipped. C013, C023, C038 and C057 remain deferred
outside the batch. Do not backfill or reopen them automatically.

[Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
and the [evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
require four separate results: automatic retrieval recall; automatic final-citation
precision/recall/F1; LLM grounded correctness; and LLM answer adequacy. 08F authors
the reference package for those checks, not model predictions or judge scores.

## Inputs and authoritative versions

- The [consolidated 08E result](../../docs/specs/task08e_combined_review_result.json),
  its handoff, completion inventory, validation, dependency bindings and independent
  audit. Verify checksums and exact file closure before using the handoff.
- The per-case current authority: original checkpoint for 44 cases, and approved
  scope overlay for the nine later revisions. Resolve exact final question,
  approval scope, eligibility, displayed framing, amendments and citation roles.
  Only 49 of the 53 cases are eligible for authoring.
- Complete reviewed source text, passages/tables, evidence occurrences, prior
  displays, source-edition limits, required rechecks, exclusions and historical
  reconciliation holds. Keep historical claim decisions unchanged, including
  C014/C020/C024's separate research-supplement findings.
- [Chat/recording contract v2](../../docs/specs/task08f_chat_review_v2.md),
  [authoring prompt v3](../../docs/prompts/task08f_reference_answer_v3.md), and
  [artifact contract](../../docs/data_artifacts.md).

C005 and C048 require their exact display-plus-amendment composites. Later human
role decisions override earlier proposals. Pending research in a scope-overlay
checkpoint is not newly approved evidence and is not automatically a reason to
repeat the completed scope review. Conversely, a hash-valid source outside the
approved scope is not silently available as approved answer support.

The live project-105 export and old two-case versions belong only to the historical
health-risk lineage. Do not import its approvals or use it as current intake.
There is no second eligibility vote when the existing decision binds the unchanged
current input; missing or stale bindings must be resolved explicitly.

## One structured answer to review

Show the exact question, then one readable list containing:

1. **Conclusion:** the direct answer, with citations establishing it.
2. **Essential supporting points:** the facts and visible reasoning necessary to
   explain that answer, each with citations. State how premises justify the
   conclusion; a list of individually true facts is not enough.
3. **Material qualifications:** cited conditions or limits attached to the
   conclusion or supporting point they constrain.
4. **Optional context:** separately labeled cited background, if useful.

Use a few coherent sentences, not a fixed number of bullets or atomized fact
inventory. Attach multiple citations when a point requires combined support.
Clearly distinguish direct support, necessary supporting evidence and required
qualifications from optional context. Do not pad the citation list for diversity.
Keep complete passages and tables available for inspection.

This single structured answer is both the reference answer and its adequacy guide.
There is no parallel flowing-text answer, duplicate claim list, separately approved
outline or additional point-labeling pass. Point identifiers and citation links
are recordkeeping, not extra human judgments. Display source title/edition,
section/table and pages with relevant excerpts where useful; keep raw IDs and
provenance hashes out of the readable answer.

### Citation count and target granularity

Do not impose a one-citation-per-point limit. Use one citation when sufficient;
allow multiple when they jointly establish the point or its necessary qualification.
Avoid redundant citations and do not split a coherent argument just to meet a cap.

Link to the smallest stable, meaningful canonical section, subsection or complete
table, identified by document/edition, stable unit ID and page/anchor locations.
Do not use an entire chapter when an appropriate subsection exists. Preserve table
continuations, captions, notes and necessary surrounding context. Existing sealed
units remain unchanged; do not invent new citation identities during authoring.

Keep the relevant supporting excerpt or table cells alongside that broader target
as a locator and explanation, not a replacement citation identity. Automatic
citation matching operates on canonical section/table units, not exact sentence
matches. Grounding checks the actual content and qualifications; a matching unit
ID alone does not establish support. These bindings must permit deterministic
link rendering and source verification.

## What the evaluation needs from 08F

Grounding judges the model's actual answer against its actual citations in the
question's scope, without seeing our reference. Adequacy adds this structured
reference and checks correct, sufficient substance rather than matching wording,
point count or citation IDs. A valid alternative argument can receive full credit.

Both are **whole-answer 0/1/2 scores**, not all-or-nothing checks or a fraction of
bullets. Automated point-level explanations provide interpretability, not a fifth
score. During authoring, make the essential reasoning and scope clear enough to
distinguish a central failure from a secondary defect without adding numeric
point weights or labeling hypothetical model mistakes:

- Grounding **2**: substantive assertions, conclusion and necessary qualifications
  are supported. **1**: a material supporting assertion is unsupported/overstated,
  but the remaining cited evidence independently justifies the conclusion.
  **0**: the central conclusion or a premise necessary to establish it is
  unsupported or contradicted by the cited evidence.
- Adequacy **2**: substantively correct and sufficiently complete; optional
  context may be absent. **1**: the conclusion is correct but an essential
  explanation, condition or question component is missing. **0**: the central
  question is unanswered, materially misframed or answered incorrectly.

One error may affect both dimensions. A missing condition can turn a supported
claim into an overstatement and make the answer incomplete. A merely omitted
additional point does not make other supported statements ungrounded. A correct
conclusion with missing essential explanation generally earns adequacy 1.

A wrong citation for the central premise with no other cited support can earn
grounding 0 even if the conclusion happens to be true. A secondary wrong citation
with independently sufficient remaining support generally earns 1. The judge must
not repair the answer by substituting the source it should have cited. A different
valid supporting citation from our reference can earn grounding 2 even when it
loses automatic reference-match credit. Importance, not bullet count, controls.

## Execution — batch preparation, then human chat review

The user specified this two-phase workflow on 2026-10-08. Prepare the complete
eligible batch first; do not alternate initial model drafting and human approval
case by case. This contract update does not launch either phase or create a chat.
The second phase is a human chat pass, not necessarily a newly created chat.

### Phase A — batch model preparation

1. Verify the current 08E handoff and create a fresh no-clobber preparation
   namespace outside all existing seals. Bind all 49 eligible cases to their
   exact current question, approved framing, evidence scope and eligibility.
2. Qualify required save/reload/export glue with synthetic inputs before live use.
   Check interruption recovery, failed attempts, per-case isolation and blank
   human decisions. No implemented v2 validator is claimed by this documentation.
3. Run Astra (`gpt-6-astra`) across the eligible batch using prompt v3, with an
   isolated input and output per case. Bounded concurrent invocations are allowed;
   never pool source decisions or mix case evidence. Each invocation produces one
   structured proposed answer. Save actual model/invocation, prompt, exact inputs,
   raw output, citation bindings and readable proposed review display.
4. Reuse approved 08E framings and mark substantive changes. Check every conclusion,
   premise, qualification and citation against the reviewed source text. Record
   mechanical validation separately from advisory source-grounding checks; neither
   establishes human approval. Official responses and claims are not evidence.
5. Save per-case status and retry history so the job can resume without overwriting
   completed versions or hiding failures. Any model repair is a new bound version.
   Account for every eligible case with a validated proposal or an explicit blocked
   record and reason. Missing support is not permission to invent an answer, change
   the question or automatically stop the case on the user's behalf.
6. Publish a checksummed **prepared, awaiting human review** handoff only after
   the whole batch is accounted for. Include ordered case records, proposal/display
   versions, complete source references, validation, unresolved issues, invocation
   receipts and resume instructions. Explicitly report any blocked cases; they are
   not completed answers. Carry 08E eligibility as input provenance while leaving
   all new 08F answer approvals and final dispositions blank. Preparation alone
   does not complete 08F.

### Phase B — question-by-question human review in chat

1. Verify the saved Phase A handoff and begin at C001 in saved order. Use the
   prepared proposals; do not rerun initial authoring for every case. Keep the
   human journal and later revisions outside the sealed preparation directory.
2. Show the exact current question, structured answer and citations, optional
   context and material remaining gaps as a readable list. A prepared display is
   only a proposal; record an actual display event when it is shown to the user.
3. Discuss one question at a time. Use Astra for targeted answer revisions needed
   by feedback, saving exact predecessor/input/output bindings. Do not rerun the
   full batch or restart completed evidence review. Material evidence or question
   changes require an explicitly authorized bounded reopening.
4. Obtain explicit approval of the exact structured answer and rendered citations,
   or an explicit stop, hold or deferral. Reformatting, successful validation and
   prior 08E approval do not silently approve the new final answer. Save verbatim
   feedback, exact displays, decisions and resume position after each interaction.
   Keep valid inherited eligibility; ask again only if its binding becomes stale.
5. Validate current approvals, citation links, input bindings and full case
   accounting. Publish the final reviewed handoff with dispositions and resume
   state. Pending human decisions stay pending. No 08G/08H, judge runs or benchmark
   execution follows automatically.

## Outputs and validation

Retain exact question, input/eligibility identities, structured answer and rendered
display, point-to-citation links, source occurrences and full-source references,
required/context roles, predecessor versions, actual model provenance, verbatim
feedback and explicit display-bound approvals. Derive the case citation pool from
links while retaining occurrence identities; evaluation canonical-unit aggregation
does not erase review provenance. No hidden or unreviewed source is promoted.

Verify source membership/resolution, qualification attachments, point identity,
nonempty substantive content, citations on all substantive points, exact display
hashes and approval targets, saved order and complete case accounting. Mechanical
checks cannot establish semantic support or human approval. A central inference
still needs evidence-based review even if every link resolves.

Retain source limitations and unresolved issues honestly. Explicitly stopped or
deferred cases are not automatically replaced. An unresolved live decision keeps
the pass pending until the user disposes of it. Preserve all original artifacts.

For documentation changes check local links and `git diff --check`. For later
helper implementation use focused qualification and repository `make fix` /
`make check`; separate existing failures from new results. Do not claim historic
checks were rerun. No full test suite is needed for this documentation-only update.

## Completion and labeling budget

08F is the last planned substantive case-labeling pass. Approve essential points,
material qualifications and citations as part of the answer itself. Later work
serializes these records and produces automated diagnostics without a new gold
labeling task. Separate cluster/split decisions remain planned.

Judge calibration or manual prediction labeling requires separate authorization.
Without actual human calibration, report uncalibrated automated judgments; reference
answer approval does not validate the judge. This contract does not run either
judge or replace the later evaluation implementation/freeze task.

## Learning note

Separating the answer's evidence support from its completeness prevents citation
matches from masquerading as correctness. One structured cited artifact makes
both checks inspectable without maintaining parallel annotations. Decision 006
records the research precedents and limits. Historical work is available in the
[health-risk record](08f_historical_health_risk.md); its approvals remain unchanged.

## Phase A execution plan — 2026-10-08

Verify the consolidated 08E seal and dependency closure, resolve each current
approval scope, then qualify isolated intake, answer validation and restartable
recording against synthetic failures before live use. Run independent ephemeral
Astra invocations in saved order with bounded concurrency. Save all attempts and
exact source-only inputs. Publish completion last only after every eligible case
has a validated proposal or an explicit blocked record; all 08F decisions stay null.

The maintained runner follows [OpenAI noninteractive-mode guidance](https://learn.chatgpt.com/docs/non-interactive-mode):
structured output and event logs provide inspectable execution receipts, while
ephemeral calls avoid persistent chats. JSON validity cannot establish source
support; separate advisory checks and later explicit human review retain that
boundary. This research concerns execution tooling only and adds no case evidence.

## Phase A outcome — 2026-10-08

All **49 eligible cases** now have validated structured proposals in saved order.
There are **zero blocked cases**. The [preparation result](../../docs/specs/task08f_combined_preparation_result.json)
binds the sealed handoff, readable review, exact completion inventory, validation
and independent audit. Phase B has not started; all new answer approvals and final
dispositions remain null. Existing 08E eligibility remains provenance.

The fresh external namespace is `task_08/08f_preparation_20261008_v1/`. Intake
verification covered the exact 57-file 08E inventory, 84 dependencies, 995 canonical
source occurrences and 18 source PDF/manifest hashes. Only 237 approved citation
occurrences entered the 49 isolated inputs. All nine overlays and the C005/C048
amendments remain bound. C002's undisplayed S011 was excluded from model evidence
with a recorded scope audit; its historical source remains preserved. Complete
table cell grids, captions and notes survive input projection.

Astra was invoked 54 times with `gpt-6-astra`, high reasoning effort, no tools and
ephemeral sessions: 49 initial calls plus five targeted repairs. C008, C009, C020,
C027 and C055 initially had invalid qualification targets; second attempts passed.
Every failed output and diagnostic remains preserved beside its bound replacement.
The CLI records the configured model but does not separately expose a backend
model identifier; no stronger backend-identity verification is claimed.

The narrow maintained helpers are `group_answer_intake`, `group_answer_records`
and `group_answer_batch`. Their qualified behavior includes exact scope isolation,
source-unit validation, multi-citation points, exact substring locators, full table
grids, null decisions, no-clobber attempt history, interruption recovery and
completion-last publication. `make run-answer-preparation`,
`make seal-answer-preparation` and `make verify-answer-preparation` accept
`ANSWER_BATCH`; completed preparation is immutable.

Validation: `make fix` passed. The integration `make check` passed formatting,
lint and types and reported 3,343 tests passed, one skipped and the same three
historical Task06G repository-base-commit pin failures recorded upstream. After
the bounded recording/rendering review fixes, all **51 focused tests** passed,
with lint, formatting and type checks passing. Live batch validation rechecked
every proposal, exact question, citation role, excerpt, qualification attachment,
rendered display, raw output and full attempt history. Upstream checksums were
reverified after execution. Mechanical success and advisory source-grounding notes
are not semantic approval or calibrated judge results.

For later human review, use the exact handoff in the result pointer and start at
C001. `REVIEW_INSTRUCTIONS.md` and `review.md` are inside the seal. Record actual
displays, feedback and any revisions in a separate namespace; reuse these saved
proposals. No Phase B decisions, 08G/08H work, benchmark/judge runs, new chats or
projects, commits or pushes were performed.

## C022 bounded Appendix P reopening — 2026-10-09

The user authorized resolving the saved Water Supply Assessment citation blocker
and preparing any resulting C022 revision. Preserve the sealed 49-case batch and
all 08E decisions. Inspect the original PDF, qualify a source-specific citation
boundary adapter, then use Astra for one targeted proposal with exact predecessor
and feedback bindings. New evidence roles and the revised answer remain proposals;
this authorization does not approve either or start the ordered Phase B pass.

The canonical Section 8 already contains its full text. Its internal statutory
callout labels trigger the generic next-heading validator. A narrowly audited
adapter preserves the existing section identity and all 25 member blocks, verifies
the following Section 9 boundary and binds rendered PDF evidence. It pins the
accepted canonical/PDF hashes and rejects omissions, rewritten content, wrong
boundaries and stale bindings. Generated records live outside all prior seals.


The [supplement pointer](../../docs/specs/task08f_c022_wsa_reopening_result.json)
binds the completed C022 revision and exact inventory. Astra made two attempts;
the first failed a qualification-attachment check and remains preserved. The
second changes that attachment only and passes validation. The answer now cites
Appendix P directly for its stated service commitment, possible reassessment and
conditional five-year construction/progress provision. It retains the nonbinding
letter and approved-assessment distinctions. Three distinct citation sections and
ten point-to-citation uses appear in the revised proposal.

All 106 focused tests and repository formatting, lint and type checks passed.
Independent source/code/answer review found no material issues. Both original
08E and 08F seals reverified unchanged. New evidence approval, answer approval,
disposition and expanded-scope eligibility remain null; prior eligibility remains
provenance. Ordered review still resumes at C001, consulting this supplement at
C022. Nearby Section 9 and context-search findings remain unpromoted; no chronology
or current contractual status is inferred. No judge runs, commits or pushes.

The learning is that block styling and semantic section ownership can differ:
statutory callout labels should not truncate their containing section. The
source-specific adapter preserves the benchmark's stable section identity and
complete text without weakening the generic validator or editing canonical data.

## Consolidated Phase B closeout

All 49 eligible cases received explicit human approval in saved order. The
approved C022 Appendix P replacement is included. The original completed Phase B
export remains sealed as `08f_reviewed_20261009_v2`; the current consolidated
export is `08f_reviewed_20261009_v3`, bound by the
[reviewed result](../../docs/specs/task08f_combined_review_result.json).

The ten-case additional evidence review produced seven approved replacements:
C002 v6, C016 v4, C028 v4, C032 v4, C036 v4, C043 v3 and C056 v3. C024, C004 and
C018 retained their answers. The six G.3/Appendix O reviews all ended with explicit
no-change decisions. Those scope-specific decisions do not reverse separately
approved additions, including C002's Frontage Road and G.2 context. The suggested
shoreline wind-recreation question remains discussion only and was not added.

Consolidation copies 42 unchanged case records byte-for-byte and binds the seven
replacement answers to their exact saved Astra proposals, effective inputs,
actual amendment displays and verbatim human approvals. C032 uses its corrected
page-label input; the original model input and correction receipt remain saved.
Current human decisions are separate from historical preparation placeholders.
No answer text, question or citation role is changed during consolidation.

The final export retains the original four 08E skips and four earlier deferrals
outside the 49-case batch. It preserves all original versions, failed attempts,
source-edition restrictions and unresolved source relationships. In particular,
G.3 scenario/receptor correspondence and C018 traffic-input correspondence were
not established by similar numbers or dates. Human no-change decisions do not
convert those research limits into new evidence.

Validation covers the predecessor's exact completion inventory, all 49 structured
answers using the maintained validator, current question/input/citation bindings,
explicit approvals and saved order. A separate independent provenance audit is
bound in the final handoff. The seal is published last over the exact managed-file
inventory; supplement journals and all historical attempts remain referenced in
place with checksums. The generated combined readable answer file is a reference
rendering, not a newly claimed human display. Unavailable chat IDs and timestamps
remain null. Mechanical validation and reference approval do not establish judge
calibration or eliminate source limitations.

The learning is to consolidate **approval-bound versions**, not simply the newest
file. This preserves rejected or superseded attempts without promoting them and
allows a later consumer to verify the exact current answer alongside its history.
No additional substantive human labeling is pending. Later stages require their
own authorization.
