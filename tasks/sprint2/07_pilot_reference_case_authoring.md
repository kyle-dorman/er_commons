# Task 07: Pilot Reference-Case Authoring

Status: **07A screening and export complete; example selection deferred pending linking repair. Later authoring subtasks remain provisional.**

## Abstract

Learn how to turn a small set of official comment-response pairs into reviewed,
source-grounded reference defenses. Start with human-only review of at least
50 comment-rooted cases for pilot fit, then advance only a small, varied selection
through five separate Label Studio authoring projects. For those later stages,
Codex proposes each batch in a separate task; the curator edits and approves
each stage before its output becomes input to the next. Revisit each project's form, prompt, and criteria in named revisions
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
| [07A](07a_screen_pilot_candidates.md) | Pilot-fit screening | Human-only ratings and optional skip reasons for at least 50 distinct comments with complete response context; prioritized small pilot |
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

07A uses direct human review with a click-only form and lightweight sample and
export records; it has no Codex proposals or handoff prompt. Its sampling and
rebuttal-focused skip criteria are owned by the [07A plan](07a_screen_pilot_candidates.md).

Later review subtasks own focused Label Studio projects and enough narrow code
to prepare inputs, validate Codex proposals, import suggestions, export human
annotations, and produce the next stage's approved records. Prepare a
bounded batch and a self-contained prompt for a **separate Codex task** using
the user's existing app allowance. The user starts that task; Task 07 does not
automate paid API calls or require a live model backend inside Label Studio.
Keep the model proposal distinct from the curator-edited record.

Use stable case, response, assertion, and evidence IDs; version the input
batch, form, review, and export; add prompt, selected Codex model, and proposal
versions only for stages using model suggestions. Codex may suggest search terms or evidence IDs only within an explicitly provided
candidate set. Code checks IDs and source anchors; a model statement alone is
never evidence. Keep generated records and Label Studio exports under
`ER_COMMONS_DATA_ROOT`, with only small configs, schemas, fixtures, and task
contracts in Git. A restart must not overwrite prior reviewed exports.

## Research / learning checkpoint

For 07A, test the installed Label Studio edition/version against its
[choice controls](https://docs.humansignal.com/tags/choices),
[task import](https://docs.humansignal.com/guide/tasks), and
[annotation export](https://docs.humansignal.com/guide/export). Confirm that
rating and optional skip reasons can be completed without typing.
Before the first model-assisted authoring stage, separately trial
[pre-annotation import](https://docs.humansignal.com/guide/predictions) and the
[API](https://docs.humansignal.com/guide/api). Explain why manual Codex batch
handoffs fit those later stages better than a live model integration.
Record only useful operational limits from the small interface trials.

## Plan / spec requirement

07A fixes a minimal sample record, source-ID mapping, review-state meaning, and
import/export convention before its first real batch. Later stages add their
Codex handoff fields when needed.
Each later subtask freezes only its own stage schema and review criteria after
a tiny interface trial; it must not design all later forms in advance. Preserve
one explicit mapping from Label Studio task IDs back to stable source IDs.

## Validation and review pass

- Round-trip a small fixture through Label Studio import, human edit/export,
  and next-stage conversion before each project handles a real batch. Add
  proposal validation only for stages using model suggestions.
- Verify counts and ID closure at every stage: approved outputs bind exact
  reviewed inputs; missing, duplicate, or unreviewed records cannot advance.
- Review the resulting forms and records for curator usability, evidence
  traceability, maintainable code, and honest claim boundaries.
- Inspect Markdown diffs and run `git diff --check` for planning-only changes;
  implementation follows the repository's `make` validation entrypoints.

## Acceptance criteria

All seven subtasks close with human-reviewed outcomes or explicit stops. At
least 50 distinct comment-rooted screening cases have curator decisions; only a
bounded selected subset is authored. Every finalized pilot defense traces each substantive
statement to reviewed direct-support Draft EIR anchors, or the case retains an
insufficient-evidence status. The Task 07 outcome reports attrition, review
effort, failure patterns, and the Task 08 handoff without claiming formal
benchmark eligibility.

## Non-goals

Reviewing the complete response inventory; automatically declaring Task 08
eligibility; changing accepted Task 03/04/05/06 evidence; training or deploying
a model; an LLM judge; paid API integration; a workflow engine; or running the
target benchmark model.
