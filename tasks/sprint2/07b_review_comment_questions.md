# Task 07B: Review Comment Questions

Status: **Complete: seven approved, I-CJ-4 unclear and skipped; all eight outcomes exported and validated.**

## Abstract and goal

For the eight Great cases selected by [07A](07a_screen_pilot_candidates.md#eight-case-selection-and-07b-handoff),
record a clear, faithful list of what each original comment asks or raises.
Use a separate Label Studio project. Preserve original comments, all screening
labels, both existing screening projects, and accepted upstream artifacts.
Reviewed questions are curator-only guidance for later authoring; they never
replace the original comment in target-model input.

## Inputs

- Planning checkpoint: `ce2db1d`.
- The completed 07A selection under `ER_COMMONS_DATA_ROOT`:
  `pipelines/brisbane_baylands/task_07_pilot/07a/authoring_selection_20260924_v1/`.
  `selected_cases.json` binds the eight cases and screening provenance;
  `selection_manifest.json` pins the repaired sample and human export.
- Selected comments: I-EA-2, O-Joint-19, I-CJ-4, I-CF-4, PC-LM-2,
  SA-Caltrans-33, M-OSEC-273, and O-GGBA-2. Retain the saved selection;
  do not resample or rerate it.
- Use the [07A.1 replacement](../../docs/specs/task07a1_final_result.json),
  exact original comment text, source unit/span IDs, pages, and any applicable
  comment extraction or truncation limits. Preserve upstream relationship
  bindings in provenance without presenting official-response content.

## Agreed execution boundaries

The user's opening instructions establish these boundaries:

1. Discuss and agree on the approach before implementing or authoring the batch.
2. Draft from the original comments alone. Exclude official individual/general
   responses, response-derived summaries, selection topic descriptions, and
   evidence conclusions from the drafting input and review display. Statements
   quoted by the commenter remain part of the original comment.
3. After agreement, develop and test the UI with exactly one selected case
   before asking Kyle to review it. Do not populate all eight until Kyle approves
   the UI. UI approval and approval of a case's content are separate decisions.
4. Keep this MVP small. No changes to screening decisions or projects.

## Agreed drafting and review policy

- Use one concise item per distinct material question, concern, or requested
  action, in comment order. Split only when the issues could be addressed
  separately; combine repetition and keep necessary qualifications together.
- Preserve the commenter's meaning, scope, uncertainty, and requested remedy.
  Use a direct question when natural; retain a concern or request as a statement
  when converting it to a question would invent an ask. Do not add an answer,
  technical rationale, new terminology, or an expected response structure.
- Distinguish the commenter's allegations from established facts. Retain key
  cited sections/tables when they identify the issue. Do not turn every
  background sentence into a separate question or force a fixed item count.
- Flag missing antecedents, incomplete text, or ambiguous intent instead of
  resolving them from official responses. Do not fetch surrounding substantive
  context automatically; record what is missing for a later explicit decision.
- Keep a read-only original and immutable proposal separate from the edited
  review. Preserve original source spans automatically. Defer mandatory
  concern-by-concern highlighting; the MVP binds the reviewed list to the exact
  whole-comment source spans. This is coarser traceability, not a claim that
  individual concern offsets have been verified.

Kyle reviews whether the list covers all material asks, adds nothing, preserves
qualifications and requested actions, and uses sensible splitting and clear
language. Edit the list directly; no required explanation for routine edits.
This stage checks faithful interpretation, not whether the commenter is right,
whether the official response answers them, or whether evidence supports it.

## Agreed minimal Label Studio form

Read-only display: comment ID and pages, exact original comment, applicable
comment-source warnings, and the initial Codex proposal. No response panel.

| Editable field | Meaning |
| --- | --- |
| `concerns` | One multiline field, one question/concern per numbered item, initially populated from the proposal. Required for approval. |
| `review_status` | Required choice with no default: `approved`, `unclear`, or `needs_context`. Approval means the final edited list is faithful and complete. |
| `review_note` | Optional short note, especially useful to explain ambiguity or missing context. |

`unclear` means the supplied comment's intent cannot be represented confidently;
`needs_context` means identifiable missing material is needed. Both hold the
whole case from advancement while retaining any partial list. No annotation
means pending; an imported proposal must never count as human approval.

Technical provenance is automatic, not extra curator fields: stable comment ID,
source spans/text identity, selected handoff identity, proposal/form versions,
Label Studio task and annotation IDs, and export/reviewer metadata. Retain the
original proposal independently of later edits. Use a versioned external 07B
namespace under `pipelines/brisbane_baylands/task_07_pilot/07b/`; no-clobber
reviewed exports. Only approved records may feed 07C.

## Accepted MVP decisions

Kyle accepted all four planning choices on 2026-09-24:

1. Use mixed questions/concerns with one item per material issue. Revisit only
   if the trial reveals a concrete problem.
2. Use the three-field form and whole-comment source-span binding; defer
   mandatory per-item highlighting.
3. Retain the [umbrella](07_pilot_reference_case_authoring.md#shared-batch-workflow)
   workflow: Kyle starts a separate Codex task with a comment-only drafting
   packet. This task prepares the packet and integrates its returned proposal;
   it does not create the drafting task automatically or draft from its broader
   planning context.
4. Use O-Joint-19 for the one-case trial. Develop and test its UI before Kyle's
   review; the remaining seven stay unpopulated until explicit UI approval.

## Research / learning checkpoint

Consulted maintainer documentation during planning:

- [TextArea](https://docs.humansignal.com/tags/textarea): native editable text
  supports the proposed list without building a custom repeated-item editor.
- [Choices](https://docs.humansignal.com/tags/choices): a single explicit status
  avoids separate approval/uncertainty toggles with contradictory combinations.
- [Pre-annotations](https://docs.humansignal.com/guide/predictions): preserve the
  distinction between suggestions and human annotations. Trial prediction
  import and editing on the installed Community edition before relying on it.

The documentation informs the design; it does not establish that the installed
version has passed the trial. The practical tradeoff is fast whole-comment
review with coarse source binding, rather than extra per-concern annotation.

## Plan, validation, and review pass

1. Record the agreed choices and prepare the isolated one-case drafting packet.
2. Prepare the one-case comment-only drafting input, immutable proposal, minimal
   form, and narrow import/export handling. Read architecture and current
   Label Studio operation notes before code or service changes.
3. Test the one-case UI before handoff: original text integrity; absence of
   response material; proposal/edit separation; multiline add/edit/delete;
   save/reload/export; all statuses; and rejecting empty approved lists.
   Verify mappings and that test annotations cannot become curator approvals.
4. Verify retry behavior does not duplicate tasks and both screening projects
   and their labels remain unchanged. Use focused tests and repository `make`
   validation; visually inspect the actual form. Keep service use lightweight.
5. Ask Kyle to review the tested one-case UI. Revise as needed. Prepare/import
   remaining cases only after explicit UI approval, then obtain content review.
6. Export all eight outcomes, preserving original proposals and final reviews.
   Check unique selected IDs, source identity, annotation provenance, and
   approved versus unresolved accounting. Record only useful findings about
   clarity, omitted concerns, or overinterpretation; no new scoring framework.

An independent planning review checks scope and simplicity. Implementation
review checks usability, preservation, and faithful export. Planning edits use
Markdown diff review and `git diff --check`.

## Acceptance and non-goals

Close when all eight selected comments have curator-approved lists or explicit
unresolved outcomes, a verified versioned export exists, and only approved
records can advance to 07C without changing source text. Unresolved cases do not
silently advance. UI testing alone cannot satisfy content approval.

No official-response interpretation, evidence search, reference-defense writing,
formal eligibility decision, screening changes, paid API integration, live model
backend, generalized annotation framework, or full-batch import before UI
approval.

## One-case trial outcome

Integrated the proposal from Kyle's separate comment-only drafting task. Its
three concerns and exact comment identity match the prepared packet. The
proposal remains unchanged; its model identifier is unknown (`null`).

[Project 3](http://127.0.0.1:8097/projects/3/data?tab=2&labeling=1),
`Task 07B · O-Joint-19 · Question review trial`, contains only task 101.
It presents the original comment with natural line wrapping, its source note,
an expandable unchanged proposal, and the three agreed controls. Source bytes
and span identifiers remain intact. The editor shows all three proposed items;
no review status is preselected. The existing isolated Community 1.23.0 server
was reused without restarting services or installing dependencies.

`pilot_questions` verifies the drafting packet and proposal and prepares one
comment-only task with a concerns prediction. Review normalization compares the
native exported data against the trusted prepared task, preserves edited text,
and requires a saved annotation, reviewer, explicit status, and a nonempty
numbered list for approval. The function does not import or assign human labels.
The [form operation notes](../../configs/label_studio/README.md#task-07b-one-case-question-review)
own preparation and safe reuse.

Validation completed:

- Native UI: prefilled list, no default approval, required status, multiline
  editing and item deletion, save/reload, unchanged proposal display, all three
  statuses, and optional empty note. Desktop and narrow layouts inspected.
- Native exports round-trip edited lists exactly. Unclear and needs-context
  records retain partial or empty lists and cannot advance. Known limitation:
  the native form allows an empty list marked Approved to be saved; the export
  validator rejects it. Conditional list requirements are enforced at export
  to retain the simple three-field form and allow empty unresolved records.
- Temporary QA annotation 104 was saved as explicitly named test evidence and
  removed only after confirming it matched that evidence. At the UI handoff,
  project 3 had one pending task, one original prediction, zero annotations,
  and zero drafts.
  QA exports are test evidence, never curator-approved handoffs.
- Repeating the preparation reconciles the existing project and task without
  importing duplicates. Label Studio trims outer XML whitespace; comparison
  accommodates that presentation-only normalization.
- Both screening project settings and full native exports match their pretrial
  snapshots exactly. Global database size and modification time are unchanged.
- `make fix` and `make check` with
  `PYTEST_ADDOPTS='tests/test_pilot_questions.py tests/test_pilot_screening.py -q'`
  pass: formatting, lint, typing, and 38 focused tests. Full historical pipeline
  tests were not rerun for this bounded adapter.
- Independent review identified missing displayed source notes and insufficient
  export identity checking; both were corrected with tampering tests.

External artifacts under `ER_COMMONS_DATA_ROOT`:
`pipelines/brisbane_baylands/task_07_pilot/07b/o_joint_19_trial_v1/`.
`drafting/` preserves the original comment-only packet and returned proposal;
`ui/` holds the prepared task, bounded execution driver, import/project/task
identities, protected snapshots, QA exports, cleanup receipt, final pending
export, screenshots, and trial manifest. No existing reviewed export is replaced.

## Accepted UI and first case

Kyle approved the interface and retained the original three-item O-Joint-19
proposal on 2026-09-24. Live annotation 105 on task 101 is `approved`; its list
matches the proposal exactly and its note is empty. The native export, separate
live task read, and second export agree. Original source/proposal bindings and
the unchanged form were verified. Both screening projects remain unchanged.

The immutable review export is under `ER_COMMONS_DATA_ROOT`:
`pipelines/brisbane_baylands/task_07_pilot/07b/reviews/o_joint_19_approved_20260924_v1/`.
It includes native export, normalized review, task/project snapshots, explicit
UI approval and feedback, and a checksummed manifest. Preserve annotation 105;
the earlier QA cleanup procedure must never target this human review.

Learning: Kyle found the review task hard but the interface fine. He considered
splitting the feasibility question from its supporting concern about neighboring
cities' capacity, then kept them together. Retain the simple interface and the
rule to keep an ask with its supporting reason unless they are independently
addressable. One accepted case does not establish low annotation effort.

## Remaining seven handoff

Prepared exactly the seven unreviewed selected comments under:
`pipelines/brisbane_baylands/task_07_pilot/07b/remaining_seven_20260924_v1/`.
`batch_prompt.md` directs the separate user-started drafting task; each
comment-named directory contains `comment_input.json`, `drafting_prompt.md`, and
`packet_manifest.json`. `batch_manifest.json` records exact membership and hashes.
Each packet preserves exact original comment text and source spans/pages, with
no official responses, screening summaries, or reviewed pilot example supplied.
Selection and source hashes and exact copied text were verified.

## Eight-case review handoff

All seven returned proposals were validated and imported into existing project 3,
now titled `Task 07B · Eight-comment question review`. The approved form is
unchanged. O-Joint-19 task 101 and approved annotation 105 exactly match the
protected review export. Projects 1 and 2 and their screening exports/settings
remain unchanged; global database size and modification time also match.

| Comment | Label Studio task | Proposal items | State at import |
| --- | --- | --- | --- |
| O-Joint-19 | 101 | 3 | Approved, unchanged |
| I-EA-2 | 102 | 2 | Pending |
| I-CJ-4 | 103 | 1 | Pending |
| I-CF-4 | 104 | 1 | Pending |
| PC-LM-2 | 105 | 1 | Pending |
| SA-Caltrans-33 | 106 | 1 | Pending |
| M-OSEC-273 | 107 | 1 | Pending |
| O-GGBA-2 | 108 | 1 | Pending |

M-OSEC-273's proposal note identifies an unsupplied antecedent for “However”
and no explicit requested action. A small display addition includes nonempty
draft notes in the read-only **Initial proposal · unchanged** panel. The note
is not part of the editable concern list and does not set `needs_context` or
any other human status. No preceding text or official response was retrieved.
Empty-note task payloads, including the approved first case, are unchanged.

Validation: exact seven-case membership, packet/prompt/source hashes, proposal
IDs and text bindings, and comment-only fidelity review passed. The import
verified eight unique cases, seven exact native predictions, seven pending
records with no annotations or drafts, and preservation of the first review.
An immediate repeat imported zero cases. Native browser inspection confirmed
M-OSEC-273's draft note renders and all three status choices remain unset.
`make fix` and focused `make check` passed formatting, lint, typing, and 40 tests.

The batch's external `import/` directory preserves the prepared seven-task
payload, bounded import/reconciliation driver, import receipt, task-ID map,
eight-case native export, verification, note screenshot, and manifest.
Proposals and earlier reviewed exports remain untouched. The historical
one-case trial driver is not the current batch import interface.

At this handoff, the seven pending cases awaited Kyle's review and a final
validated export, now recorded below. Hold unclear or needs-context cases from
07C. No additional automatic authoring or source-context retrieval is implied
by an unresolved status.

## Review queue prefill repair

Kyle reported empty reviewed-list editors after the batch import. The initial
checks verified stored predictions and a task preview but missed the normal
labeling queue's project-level model-version filter. Each case had a distinct
prediction version while project 3 selected only the first case's version.
Installed Community 1.23's `Task.get_predictions_for_prelabeling` and
`NextTaskSerializer` confirmed this behavior.

All eight predictions now share `task07b.questions.v1`, selected by project 3.
The adapter uses this shared display selector while retaining each original
proposal's individual version and hash. Source data, prediction text, approved
annotation 105, and screening projects remain unchanged. Label Studio updated
task modification metadata automatically. The sole existing postponed draft,
17 on I-EA-2, was exactly empty; it was backed up and filled with that case's
proposal only, retaining postponement and leaving review status unset.

All seven actual next-task queue responses return their exact proposal text.
Browser checks verified normal queue prefill and the restored postponed draft.
The regression test covers distinct proposal versions under one shared selector;
focused `make check` passed lint, formatting, typing, and 41 tests. Repair
snapshots, queue responses, preservation checks, and checksums are retained in
`07b/prefill_repair_20260924_v1/` under the Task 07 artifact root. Earlier
trial/import evidence remains historical and must not be replayed over reviews.

## I-CJ-4 disposition

Kyle chose to skip I-CJ-4 and marked it `unclear`. Live task 103, annotation
107, confirms that saved status. Preserve its original comment, proposal,
reviewed list, and screening decision; exclude it from 07C authoring unless
Kyle explicitly reopens it. Count it as an explicit unresolved 07B outcome,
not an approved case or a deleted selection. Other cases remain subject to
their own saved review outcomes and the final export validation.

## Final reviewed export

All eight saved outcomes were exported to
`07b/reviews/eight_case_export_20260924T192020Z/` under the Task 07 artifact root.
Seven are approved: O-Joint-19, I-EA-2, I-CF-4, PC-LM-2, SA-Caltrans-33,
M-OSEC-273, and O-GGBA-2. I-CJ-4 remains `unclear` and must not advance.
There are no pending cases or drafts. Only the seven approved records may feed
07C; this handoff does not authorize starting that stage.

The directory contains the native export, live task snapshots, normalized
`reviews.json`, outcome summary, and checksummed manifest. Validation checked
all eight original packet bindings, saved annotation identities and statuses,
numbered approved lists, exact agreement with live results, and an identical
second native export. Both screening projects remain unchanged. Earlier
exports are preserved.
