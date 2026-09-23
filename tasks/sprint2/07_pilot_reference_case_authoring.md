# Task 07: Pilot Reference-Case Authoring

Status: **Draft for user review. No Task 07 execution is authorized by this draft.**

## Abstract

Learn how to turn a small set of official comment-response pairs into reviewed,
source-grounded reference defenses. Start by reviewing at least 50 pairs for
pilot fit, then advance only a small, varied selection through five separate
Label Studio review projects. Codex proposes each batch in a separate task;
the curator edits and approves each stage before its output becomes input to
the next. Revisit each project's form, prompt, and criteria in named revisions
as the pilot reveals problems.

This is exploratory authoring, not Task 08's complete eligibility review,
accepted-case selection, or split freeze. The later benchmark target never
receives the official response or curator-only authoring records.

## Goal

Produce a reviewed pilot set that makes the question, official-response
assertions, supporting evidence, answer logic, and reference defense explicit.
Measure how often each step succeeds, how much curator correction it needs,
and what must change before broader annotation.

## Inputs

- Pin one [Task 05H accepted inventory](../../docs/specs/task05h_final_result.json)
  and its component handoff; use comment, response, general-response,
  relationship, and explicit-reference records without modifying them.
- Pin the matching Task 03J extraction, Task 06H repaired handoff, and accepted
  usability review. Carry their sampled-review, Final F1, nonlink, and text-only
  figure limitations into screening and evidence review.
- Follow the [Sprint 2 scope](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md)
  and the [artifact contract](../../docs/data_artifacts.md).

## Proposed subtask order

| Subtask | Label Studio review stage | Outcome |
| --- | --- | --- |
| [07A](07a_screen_pilot_candidates.md) | Pilot-fit screening | Human-reviewed ratings and reasons for at least 50 distinct pairs; prioritized small pilot |
| [07B](07b_review_comment_questions.md) | Comment question | Approved account of what each selected comment asks |
| [07C](07c_review_response_assertions.md) | Response assertions | Reviewed facts, qualifications, conclusions, and source spans |
| [07D](07d_discover_and_review_evidence.md) | Evidence per assertion | Exact Draft EIR anchors, support judgments, and explicit gaps |
| [07E](07e_review_answer_logic.md) | Answer logic | Reviewed explanation connecting question, assertions, and evidence |
| [07F](07f_review_reference_defenses.md) | Reference defense | Reviewed full answers with mechanically resolvable citations |
| [07G](07g_assess_pilot_and_local_replay.md) | Assessment and local replay | Stage attrition, correction effort, unresolved cases, and local-model comparison |

07A is the first prospective implementation task after this draft is
reviewed. Later subtask contracts are **provisional**: revise the next one
from the accepted prior outcome before starting it. The curator may repeat a
stage with a new named form or prompt revision; a rejected or unresolved case
does not silently advance.

## Shared batch workflow

Each review subtask owns one focused Label Studio project and enough narrow
code to prepare inputs, validate Codex proposals, import suggestions, export
human annotations, and produce the next stage's approved records. Prepare a
bounded batch and a self-contained prompt for a **separate Codex task** using
the user's existing app allowance. The user starts that task; Task 07 does not
automate paid API calls or require a live model backend inside Label Studio.
Keep the model proposal distinct from the curator-edited record.

Use stable case, response, assertion, and evidence IDs; version the input
batch, form, prompt, selected Codex model, proposal, review, and export. Codex
may suggest search terms or evidence IDs only within an explicitly provided
candidate set. Code checks IDs and source anchors; a model statement alone is
never evidence. Keep generated records and Label Studio exports under
`ER_COMMONS_DATA_ROOT`, with only small configs, schemas, fixtures, and task
contracts in Git. A restart must not overwrite prior reviewed exports.

## Research / learning checkpoint

Before 07A implementation, test the installed Label Studio edition/version
against [pre-annotation import](https://docs.humansignal.com/guide/predictions),
[annotation export](https://docs.humansignal.com/guide/export), and the
[API](https://docs.humansignal.com/guide/api). Explain which fields the chosen
form can edit cleanly and where a simple text field or external record is
needed. Document why manual Codex batch handoffs and separate review projects
fit this pilot better than a live model integration. Record any operational
limits discovered with real example tasks.

## Plan / spec requirement

07A freezes the shared pilot batch envelope, provenance fields, review-state
meaning, and a minimal import/export convention before its first real batch.
Each later subtask freezes only its own stage schema and review criteria after
a tiny interface trial; it must not design all later forms in advance. Preserve
one explicit mapping from Label Studio task IDs back to stable source IDs.

## Validation and review pass

- Round-trip a small fixture through proposal validation, Label Studio import,
  human edit/export, and next-stage conversion before each project handles a
  real batch.
- Verify counts and ID closure at every stage: approved outputs bind exact
  reviewed inputs; missing, duplicate, or unreviewed records cannot advance.
- Review the resulting forms and records for curator usability, evidence
  traceability, maintainable code, and honest claim boundaries.
- Inspect Markdown diffs and run `git diff --check` for planning-only changes;
  implementation follows the repository's `make` validation entrypoints.

## Acceptance criteria

All seven subtasks close with human-reviewed outcomes or explicit stops. At
least 50 screening pairs have curator decisions; only a bounded selected
subset is authored. Every finalized pilot defense traces each substantive
statement to reviewed direct-support Draft EIR anchors, or the case retains an
insufficient-evidence status. The Task 07 outcome reports attrition, review
effort, failure patterns, and the Task 08 handoff without claiming formal
benchmark eligibility.

## Non-goals

Reviewing the complete response inventory; automatically declaring Task 08
eligibility; changing accepted Task 03/04/05/06 evidence; training or deploying
a model; an LLM judge; paid API integration; a workflow engine; or running the
target benchmark model.
