# Task 07C: Review Official-Response Claims

Status: **Complete: seven approved cases, 31 reviewed argument blocks, validated immutable export.**

## Abstract and goal

Turn official responses for the seven approved 07B cases into a concise,
reviewed list of what the responses claim. Preserve material qualifications,
source attribution, and links to reviewed concerns. These are **response
claims, not verified facts**. Evidence verification belongs to 07D.
Follow the [Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs

- Planning checkpoint: `020a02f`.
- [Completed 07B handoff](07b_review_comment_questions.md#final-reviewed-export):
  `pipelines/brisbane_baylands/task_07_pilot/07b/reviews/eight_case_export_20260924T192020Z/`
  under `ER_COMMONS_DATA_ROOT`. Its four manifest-listed file hashes were
  verified during this planning pass.
- Approved cases: O-Joint-19, I-EA-2, I-CF-4, PC-LM-2, SA-Caltrans-33,
  M-OSEC-273, and O-GGBA-2. **I-CJ-4 is unclear and excluded.**
- Use final reviewed concerns, not the original 07B proposals. Pin their export
  and annotation identities. Assign case-local concern references without
  altering the reviewed wording or upstream records.
- Exact individual and incorporated general responses from the
  [07A.1 replacement inventory](../../docs/specs/task07a1_final_result.json),
  with separate source IDs, spans, pages, incorporation links, and inherited
  relationship/extraction warnings. Resolve these before preparing the packet;
  do not infer incorporation from topic similarity.

## Established execution boundaries

These boundaries come from Kyle's opening instructions. Kyle accepted the
claim granularity, compact editable references, and O-Joint-19 trial on
2026-09-24, adding the recursive response-inclusion requirement below.

1. Agree on the approach before implementation or claim drafting.
2. Preserve all existing comments, proposals, labels, exports, and projects.
   Use a separate 07C Label Studio project and a fresh external 07C namespace.
3. Prepare a self-contained drafting packet for a separate Codex task that
   Kyle starts. Do not start that task automatically.
4. After agreement, develop and test the UI on exactly one case before asking
   Kyle to review it. Do not populate the remaining cases before explicit UI
   approval. UI approval and claim-content approval are separate decisions.
5. Verify prefilled editable fields through the actual labeling queue, not
   just a task preview. Preserve existing drafts and annotations.

## Complete linked-response context

Start with the case's individual response and follow all explicit links to other
responses, including general responses, recursively until no new response is
reachable. Do not stop at one hop or prune traversal based on estimated topic
relevance. Include each reachable response's full exact text in both the model's
drafting packet and the Label Studio task, with distinct source identity, pages,
passage references, and warnings. Collapsible source panels may reduce visual
burden but must not omit text or substitute summaries.

Deduplicate responses by stable source identity while preserving every link and
its source passage. Track visited responses so cycles terminate without losing
relationships. Record missing, ambiguous, or unresolved targets explicitly; do
not claim complete closure or advance an incomplete packet as ready for drafting.
An apparent response referral missing from the recorded links must be flagged
for resolution rather than silently ignored or guessed. No arbitrary depth limit
or silent text truncation is acceptable. If the full context does not fit, report
that limitation and settle a delivery plan before drafting.

Full context inclusion and claim selection are separate: the model receives all
reachable response text, but drafts only claims relevant to the original comment
and reviewed concerns, including conditions or reasoning needed to interpret
those claims. Preserve relevant claims without a clear concern match as
`unassigned`; do not extract unrelated topics just because they occur in a linked
response. Record brief source-level coverage notes without requiring the curator
to classify every unused sentence.

This traversal follows response-to-response referrals. Citations to Draft EIR
sections, studies, or other supporting evidence remain cited references for 07D;
following the response chain is not evidence verification.

## Agreed drafting policy

- Use one block per distinct substantive response argument or conclusion. Group
  supporting quantities, background facts, and intermediate reasoning with that
  argument. Split when arguments materially differ, need distinct qualifications,
  or become confusing together; separate verifiability alone does not require
  separate blocks. Keep conditions, exceptions, scope limits, and uncertainty.
  Impose no target count and avoid unreadably long compound blocks. This is
  Kyle's accepted revision after the initial 19-claim trial.
- Preserve negation, quantities, time/geographic limits, modality (for example,
  may versus will), and who is speaking. Keep attributed reports or opinions
  attributed. Do not strengthen predictions into outcomes or findings into
  independently established facts.
- Include material conclusions and commitments as well as descriptive claims.
  A referral alone stays a referral; do not invent the substance of its target.
  Preserve response citations as things the response cites, not verified support.
- Give each claim a short reference to its exact response passage. Keep individual
  and general-response sources distinct. Prefer separate claims where combining
  sources would conceal who said what. Preserve relevant general-response claims
  that do not fit a concern; do not atomize unrelated general-response topics.
  Record the supplied source coverage and any deliberately out-of-scope topics.
- Link a claim to zero, one, or several reviewed concern IDs. Use `unassigned`
  for no clear link. A link means relevance, not that the concern was answered
  adequately. Defer fully/partially/not-addressed scores and support judgments.
- Flag missing context or ambiguous source meaning; do not browse for evidence,
  repair the source, or resolve ambiguity using outside knowledge.

## Agreed minimal review form

Use one Label Studio task per case. Show read-only reviewed concerns, exact
full text of every response in the recursive closure, with short passage
references and pages,
source warnings, and the immutable initial proposal. Keep the original comment
available as context without replacing its reviewed concerns.

| Editable field | Meaning |
| --- | --- |
| `claims` | Prefilled multiline list. Each short claim block contains claim text (including qualifications and attribution), source passage reference(s), and concern reference(s) or `unassigned`. Allow add, edit, split, merge, and delete. |
| `review_status` | Required explicit choice, no default: `approved`, `unclear`, or `needs_context`. |
| `review_note` | Optional case note for missing context, ambiguity, or a material omission. No required rationale for routine edits. |

Approval means the decomposition is faithful and covers material in-scope
response statements; it does not establish truth, evidentiary support, or answer
adequacy. An unresolved case retains partial work but does not advance. No saved
human annotation means pending. A proposal never counts as approval.

Avoid separate mandatory claim-type, confidence, qualification, attribution,
or evidence controls in the MVP. Qualifications and semantic attribution belong
in readable claim text; source attribution comes from explicit passage bindings.
Tradeoff: a small text convention reduces clicks but requires validation of the
edited source/concern references. Test that burden in the one-case trial.

Technical records retain exact source text/identity and passage offsets or span
bindings, concern/export identities, immutable proposals, final edited lists,
claim IDs, reviewer/annotation IDs, versions, and hashes. Short display references
must resolve deterministically. Preserve exact passages for each final claim;
never silently reuse an obsolete source link after an edit. Define claim-ID and
split/merge rules before implementation so downstream records are stable without
requiring the curator to type long IDs.

## Drafting packet deliverable

Prepare the trial packet before any batch packet. It must be usable without
this conversation and contain:

- A prompt explaining scope, splitting/qualification rules, source boundaries,
  concern linking, output format, review criteria, and stop conditions.
- Exact reviewed concerns, original comment context, and the full recursively
  linked response set, with separately identified passages, pages, and warnings.
- A manifest pinning the 07B export, upstream identities, membership, source
  text hashes, prompt/schema version, all traversed response links, and closure
  accounting (including cycles, deduplication, and unresolved targets).
- A small output example and explicit output location for proposed claims,
  source references, concern links, and unresolved/coverage notes. Identify
  examples as illustrative; they must not become case content.

The separate drafting task uses only supplied material and returns proposals;
this task validates and integrates them. Preserve the returned proposal before
curator edits. Record the model when known; do not guess it.

## Research / learning checkpoint

Consulted maintainer documentation during planning:

- [TextArea](https://docs.humansignal.com/tags/textarea): native editable text
  can support the compact claim list without a custom repeated-item editor.
- [Choices](https://docs.humansignal.com/tags/choices): one explicit status.
- [Pre-annotations](https://docs.humansignal.com/guide/predictions): distinguish
  imported suggestions from human annotations; verify installed behavior.

The [backlog claim map](../../docs/backlog.md) informs attribution, conditions,
source traceability, and unassigned claims. Its evidence and answer-coverage
judgments are deferred to later stages. The MVP favors faithful decomposition
and fewer curator actions over a detailed taxonomy.

The [07B operation notes](../../configs/label_studio/README.md#task-07b-one-case-question-review)
record prediction filtering in the normal queue. Use a shared display prediction
version and retain per-proposal versions separately; prove prefill in the real
queue on the installed version rather than relying on documentation or previews.

## Plan, validation, and review pass

1. Use the agreed granularity, concern-link semantics, three-field form, and
   O-Joint-19 trial. Resolve its complete linked-response closure and assess
   total context size before preparing the packet. Check that packet and task
   contain the same full source set and exact text, including multi-hop links.
   Validate cycle handling, duplicate targets, and missing/ambiguous referrals.
2. Finalize the packet/schema and prepare only the chosen case for Kyle's
   separate drafting task. Read architecture and operation notes before code
   or service changes. Validate returned proposals against exact packet inputs.
3. Build the separate project. Test prefill through the actual queue; edit,
   add/delete, split/merge, save/reload, and export. Check unchanged source and
   proposal displays, no default approval, all statuses, valid source/concern
   references, and complete final claim bindings. Test bad/missing references
   and empty approval rejection. Keep QA records distinct from human approvals.
4. Verify existing projects and artifacts remain unchanged and preparation
   retries do not duplicate tasks. Run appropriate repository checks. Review
   usability, preservation, provenance, and maintainability independently.
5. Ask Kyle to review the tested one-case UI. Only after explicit UI approval
   prepare/import the other six cases and obtain case-content reviews.
6. Export all seven outcomes to a new no-clobber directory. Validate exact
   membership, approved/unresolved accounting, source and concern identity,
   claim-ID uniqueness, and native-to-normalized edit fidelity. Only approved
   records feed 07D; unresolved records retain their reason and partial work.

Planning validation: independent bounded review, Markdown diff inspection,
`git diff --check`. No application implementation, project creation, claim
proposal, or batch population has been performed in this planning pass.

## Acceptance and non-goals

Close when the seven eligible cases have reviewed claim maps or explicit stops,
with preserved proposals and a validated immutable export. Human review decides
faithfulness and material completeness; code checks bindings and record integrity.
Record practical review burden and useful lessons without a new scoring system.

No evidence search or verification, defense writing, answer-adequacy grading,
benchmark eligibility decisions, upstream mutation, paid model integration,
automatic drafting-task creation, or remaining-case population before UI approval.

## O-Joint-19 drafting packet handoff

Prepared the self-contained trial packet under `ER_COMMONS_DATA_ROOT`:
`pipelines/brisbane_baylands/task_07_pilot/07c/o_joint_19_trial_v1/drafting/`.
Kyle starts a separate Codex task with `drafting_prompt.md`. It returns a new
sibling `returned_proposal_v1/proposal.json`; no claims have been drafted here.
The packet manifest SHA-256 is
`e349d7725971b2593c60268d8d110ce08b53777b5f78fca47f2212e2a2de3ead`.

The complete response-only closure is Response O-Joint-19 (physical pages
617–618, 1,396 characters) and General Response 3 (pages 44–49, 16,271
characters). General Response 3 contains no further substantive response
referral. All eight intra-volume mentions were audited: one actual referral,
a self-description, four repeated General Response 3 headers, a General
Response 4 header, and a false match across subsection/topic headings.
The addressed-comment list does not incorporate those comments' responses.
The mixed upstream graph's cycle warning is preserved; this directed
response-only closure has no cycle or unresolved referral.

Both full response texts and all eight page-fragment passages are supplied.
Footnote 75's body, outside the accepted response span on page 618, is retained
as a separately attributed exact page excerpt without modifying the source unit.
It supplies the cited census attribution, not independently verified evidence.
Tables, headers, extraction characters, and source limitations remain explicit.

The packet contains exact final Q1–Q3 concerns and the unchanged 07B review,
source metadata/terms, inherited limitations, input bindings, closure accounting,
drafting instructions, output schema, preparation record, read-only validator,
and validation receipt. Proposal-local C001-style IDs are bound to a versioned proposal. Final reviewed
IDs bind current claim content, case/input identity, and export lineage. The MVP
preserves the whole proposal and edited list; a retained C-label records only a
label association, not verified ancestry. Exact per-claim split/merge parentage
is not collected. Quotes select exact passages without requiring curator offsets.

Validation passed: 17 upstream input hashes, exact source fragments and offsets,
original comment and final concern identity, supplementary footnote, independent
fixed-point closure, all mention dispositions, schema validity, per-source
coverage-note uniqueness, and all 13 manifest-listed packet files. Independent
review checked source completeness and prompt scope. The packet requests all
source text be read before relevant claims are selected. No source verification,
UI implementation, project creation, or remaining-case preparation occurred.
Actual queue-prefill testing and multi-hop/cycle fixture tests remain UI-stage
requirements; this particular case cannot exercise a deeper response chain.

Next: integrate and validate the separately drafted proposal, then develop and
test the one-case UI before Kyle's review. Preserve this sealed packet and all
existing artifacts. Only explicit UI approval permits the other six cases.

## One-case UI handoff

Integrated the separate drafting task's unchanged 19-claim proposal from
`returned_proposal_v1/proposal.json`. All 31 quotations occur uniquely in their
cited passages; packet hashes, source IDs, concern links, and schema validate.
The two source ambiguities (undefined city “size” and RHNA chronology) remain
visible and preserved. They do not automatically prevent approval of a faithful
extraction; the curator decides whether the meaning is adequately represented.
No factual verification was performed.

[Project 4](http://127.0.0.1:8097/projects/4/data?tab=3&labeling=1),
`Task 07C · O-Joint-19 · Claim review`, contains only task 109. Full response text,
all eight response passages and the supplementary footnote are retained beside
Q1–Q3 and the editable claims. Source line breaks, including table/list breaks,
remain visible. Initial proposal quotations and coverage notes are available in
separate expandable panels. There is no default review status.

`pilot_claims` verifies the sealed packet/proposal and prepares one prediction
using shared version `task07c.claims.v1`, selected in project settings. Its export
normalizer checks saved annotation identity and trusted task data, then resolves
edited source references to current full passages. It never silently treats an
original proposal quote as supporting a changed claim. Exact per-claim split/merge
ancestry is deferred; complete proposal and final-edit provenance are retained.
The [form notes](../../configs/label_studio/README.md#task-07c-one-case-claim-review)
own current preparation and operating instructions.

Validation completed:

- Actual normal labeling queue returned the correct prediction; browser editor
  exactly matched all 19 claims. All nine rendered source passage texts matched
  the packet (browser newline normalization only); all 31 original quotes matched.
- Native add/edit/delete, split/merge, all statuses, required-status warning,
  optional empty note, save/reopen/reload, and native export were exercised.
  Empty or invalid-reference Approved records are rejected by the export
  normalizer. Native Label Studio can save them; this limitation matches 07B.
- QA annotation 113 was exported under explicitly named QA records and removed
  only after an exact comparison with its latest saved evidence. It never became
  a curator handoff. Final state: one task, one prediction, zero annotations,
  zero drafts, original prefill, and no selected status.
- Preparation retry reconciled the existing project/task without duplicates.
  Protected settings and complete exports for projects 1, 2, and 3 matched their
  pretrial snapshots; the global Label Studio database metadata was unchanged.
- Independent review checked proposal faithfulness, code/provenance, and form.
  Its source-line-break finding was corrected; the MVP's lack of per-claim
  split/merge parentage is now explicit. Desktop and narrow layouts inspected.
- `make fix` and `make check` with
  `PYTEST_ADDOPTS='tests/test_pilot_claims.py tests/test_pilot_questions.py tests/test_pilot_context_repair.py -q'`
  passed formatting, lint, typing, and all 64 focused tests. Existing closure
  fixtures plus added general-response multi-hop/cycle and missing-target tests
  cover directed traversal behavior. No broad historical pipeline rerun.

External UI evidence, preservation snapshots, execution driver, QA exports,
screenshots, queue responses, and manifest live in the trial's separate `ui/`
directory. Preserve the sealed drafting packet and returned proposal unchanged.
The temporary QA cleanup is complete; never rerun it against a human annotation.

Next: Kyle reviews the tested one-case UI and its content. UI approval must be
explicit before the other six cases are prepared/imported. A saved case approval
alone does not imply UI approval or authorize the remaining batch.

## Current UI revision: nine argument blocks

At Kyle's request, integrated the separately authored
`returned_proposal_v2/proposal.json` and preserved `revision_notes.md` with its
19-to-9 mapping. Independent verification confirmed every original quotation
and passage binding in its mapped block, unioned concern links, and unchanged
ambiguity/coverage notes and packet bindings. V1 and the sealed packet remain
unchanged. The original 19-claim trial above is historical validation evidence.

Updated only pending task 109 in project 4 after checking zero annotations and
zero drafts. Its old prediction is retained unchanged. A new prediction selected
through shared version `task07c.claims.v2` supplies the nine blocks; task data now
preserves the immutable V2 proposal. Prior task data/settings/native export and
new state are retained separately in `ui_v2/`, alongside the update receipt,
queue evidence, screenshot, and manifest. Projects 1–3 remain unchanged.

The actual normal labeling queue returned one selected prediction and the editor
matched all nine blocks exactly, with no status selected. UI approval is still
pending; the other six cases remain untouched. Use V2 for future normalization;
the old `ui/trial_driver.py` and QA cleanup are historical and must not be rerun.

## Approved O-Joint-19 content

Kyle saved annotation 114 on task 109: all nine V2 argument blocks approved,
unchanged, with no review note or drafts. Both source ambiguity notes remain
preserved in the proposal. Native export, live task results, and a repeated
native export agree. The immutable export is under `ER_COMMONS_DATA_ROOT`:
`pipelines/brisbane_baylands/task_07_pilot/07c/reviews/o_joint_19_approved_20260924T212352Z/`.
It includes normalized review, native export, task/project snapshots, summary,
and a checksummed manifest. Projects 1–3 remain unchanged.

The export check exposed paragraph breaks inside V2 argument blocks. The parser
now uses explicit C-ID headers as block boundaries, preserving internal blank
lines exactly. Regression tests cover multi-paragraph approved arguments and
malformed following headers; `make fix` and `make check` with
`PYTEST_ADDOPTS='tests/test_pilot_claims.py -q'` passed all checks and 26 tests.
No annotation, wording, or live task data was changed by this fix.

Content approval is confirmed. Kyle explicitly approved the UI on 2026-09-24
and requested a new task to draft the remaining six cases. The UI gate is met;
no further UI approval is required for this batch. 07D still follows completed
07C review; this approval is not evidence verification.

## Accepted two-pass batch drafting handoff

Prepare and draft I-EA-2, I-CF-4, PC-LM-2, SA-Caltrans-33, M-OSEC-273,
and O-GGBA-2 in one new task. O-Joint-19 is the accepted example, not a new
assignment; I-CJ-4 remains excluded. Kyle explicitly requested creation of this
new task, superseding the earlier prohibition on automatic task creation for
this dispatch only.

For each case, prepare and validate its complete recursive response packet
before drafting. The same drafting task then performs both passes:

1. Extract all material, relevant assertions with exact quotations, source
   attribution, qualifications, and reviewed concern links. Preserve this
   detailed proposal as an immutable first pass.
2. Group the assertions into readable substantive arguments or conclusions.
   Supporting quantities, background, and reasoning belong with the argument.
   Split materially different conclusions or qualifications. Set no target
   number of blocks and avoid long compound blocks that hide distinct claims.
3. Map every first-pass assertion to a final block or an explicit reason for
   omission. Check source quotations, concern links, material qualifications,
   coverage, and ambiguity preservation. This checks faithful extraction, not
   truth. Preserve both proposals, the mapping, and validation evidence.

The grouped proposal is the future Label Studio prefill; the detailed pass and
mapping remain audit material. Do not add review controls or require Kyle to
repeat the manual regrouping instructions. Carry unresolved source meanings
forward without outside evidence searches. Full linked-response text stays in
both the packet and eventual task even when only some parts yield claims.

The new task prepares packets and returns validated drafts for integration here;
it must not alter Label Studio, human labels, existing artifacts, or upstream
sources. Record explicit case stops for genuinely missing or ambiguous response
targets; continue independent cases. Do not treat proposals as human approval.

## Remaining six integrated for review

Accepted the separate task's sealed `remaining_six_20260924_fd06/` batch under
`pipelines/brisbane_baylands/task_07_pilot/07c/`: 49 detailed assertions mapped
to 23 grouped arguments, with no case stops. All 143 manifest-listed files and
selected final versions verified, including I-CF-4 V3. Independent review
checked complete mappings, preserved quotations/concern links, ambiguity notes,
and closure receipts. Nine full responses and 28 passages are included;
I-CF-4 follows General Response 8 onward to General Response 7.

Appended tasks 110–115 to existing 07C project 4 with the approved form and
shared prediction version `task07c.claims.v2`:

| Case | Task | Arguments |
| --- | --- | --- |
| I-EA-2 | 110 | 3 |
| I-CF-4 | 111 | 10 |
| PC-LM-2 | 112 | 3 |
| SA-Caltrans-33 | 113 | 3 |
| M-OSEC-273 | 114 | 2 |
| O-GGBA-2 | 115 | 2 |

The actual normal labeling queue and browser editor matched every selected
proposal exactly. All 28 rendered source passages matched packet text (browser
newline normalization only), with no default review status. Navigation used
Postpone without submitting. Its five temporary drafts contained only exact
unchanged prefills; they were preserved as QA evidence and removed after fresh
identity/content checks. At integration handoff, all six had zero annotations
and drafts; their subsequent approvals are recorded below.
O-Joint-19 task 109 and human annotation 114 are unchanged; projects 1–3 settings
and exports are unchanged (computed relative-age display strings excluded from
comparison). The project retains its original trial title.

Preparation, bounded import driver, before/after snapshots, task map, queue
responses/checks, screenshot, preservation check and manifest are preserved in
sibling `remaining_six_ui_20260924_v1/`. The driver is historical execution
evidence; do not rerun it after human review begins. No package or UI changes
were required. The adapter validated each packet/proposal; documentation passed
`git diff --check`.

The integration handoff requested six case reviews and a fresh seven-case
export, now completed below. These are response claims;
source ambiguities remain explicit and evidence verification belongs to 07D.

## Final reviewed export and learning

All seven cases are approved in project 4, tasks 109–115, annotations 114–120.
There are no pending cases, unresolved statuses, or drafts. The final total is
31 argument blocks: O-Joint-19 9, I-EA-2 3, I-CF-4 10, PC-LM-2 2,
SA-Caltrans-33 3, M-OSEC-273 2, and O-GGBA-2 2. PC-LM-2 differs from its
three-block proposal; the other six lists are unchanged. Preserve the human
edit without inferring a rationale that was not recorded.

The immutable handoff under `ER_COMMONS_DATA_ROOT` is
`pipelines/brisbane_baylands/task_07_pilot/07c/reviews/seven_case_export_20260924T225154Z/`.
It contains native export, normalized reviews, live task and project snapshots,
input index, summary, and checksummed manifest with parser identity. Validation
rebuilt each expected task from sealed packets and selected proposal versions,
checked exact seven-case membership, source/concern identity, valid claims and
unique final IDs, saved human statuses, zero drafts, and native/live normalized
agreement (resolving the API's reviewer object to its exported reviewer ID).
A repeated native export agreed exactly. Earlier exports and all proposals remain
preserved. No evidence verification was performed.

Kyle reported that review was difficult and that official responses sometimes
over-answer: some statements seem unwarranted by the original comment. This is
a case-level learning observation, not a retroactive label on individual claims.
Faithful extraction, relevance to a concern, evidentiary support, and adequacy of
an answer are distinct judgments. Existing concern links mean relevance only;
approval establishes neither necessity nor support. Preserve the approved maps.
During 07D planning, decide how to prioritize claims that actually answer the
concern and handle incidental or only partly relevant arguments without making
Kyle review a new taxonomy for every sentence. Do not silently drop claims or
interpret an overbroad response as unsupported merely because it is overbroad.

Next: revise the provisional 07D contract with Kyle using this handoff and the
review-burden lesson before evidence discovery or another UI implementation.
