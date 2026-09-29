# Task 07: Pilot Reference-Case Authoring

Status: **07A–07E complete, including the 07C.1 replacement and six approved
chat-reviewed reference answers. Next: finalize provisional 07G; 07F superseded.**

## Abstract

Learn how to turn a small set of official comment-response pairs into reviewed,
source-grounded reference defenses. Start with human-only review of at least
50 comment-rooted cases for pilot fit, then advance only a small, varied selection
through question, claims/relevance, evidence and combined reference-answer review. For those later stages,
Codex proposes each batch in a separate task; the curator edits and approves
each stage before its output becomes input to the next. Revisit each project's form, prompt, and criteria in named revisions
as the pilot reveals problems.

This is exploratory authoring, not Task 08's complete eligibility review,
accepted-case selection, or split freeze. The later benchmark target never
receives the official response or curator-only authoring records.

## Goal

Produce a reviewed pilot set that makes the question, official-response
assertions, supporting evidence, and reference answer with its reasoning explicit.
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

| Subtask | Review stage | Outcome |
| --- | --- | --- |
| [07A](07a_screen_pilot_candidates.md) | Pilot-fit screening | Human-only ratings and optional skip reasons for at least 50 distinct comments with complete response context; prioritized small pilot |
| [07B](07b_review_comment_questions.md) | Comment question | Approved account of what each selected comment asks |
| [07C](07c_review_response_assertions.md) | Response assertions | Reviewed facts, qualifications, conclusions, and source spans |
| [07D](07d_discover_and_review_evidence.md) | Evidence per assertion | Exact Draft EIR anchors, support judgments, and explicit gaps |
| [07E](07e_review_answer_logic.md) | Reference answer and reasoning | One reviewed concise answer with essential explanation, conditions, limits and source provenance |
| [07F](07f_review_reference_defenses.md) | Merged into 07E | No separate labeling pass or post-outline approval |
| [07G](07g_assess_pilot_and_local_replay.md) | Assessment and local replay | Stage attrition, correction effort, unresolved cases, and local-model comparison |

07E is complete. The 07G assessment/replay contract remains **provisional**:
revise it
from the accepted prior outcome before starting it. The curator may repeat a
stage with a new named form or prompt revision; a rejected or unresolved case
does not silently advance.

## Prospective case and review simplification (2026-09-29)

One comment yields at most one independently answerable question. Prefer strong
examples and skip ambiguous/multiple-question comments unless a faithful single
question is straightforward. Do not split them into additional cases or discard
hard qualifications to salvage an answer. Save the original comment and approved
question; retrieval, target and judge must use that same question. This applies
to the next pass, not a silent rewrite of the sealed six-case MVP.

07E and 07F are one human pass over the reference answer, including its explanation
and limits. No separate approved outline or required claim-to-citation output map.
The reference serves later answer-adequacy scoring; source text serves grounded-
correctness scoring. Automatic citation matching remains separate from both.

## Shared batch workflow

07A uses direct human review with a click-only form and lightweight sample and
export records; it has no Codex proposals or handoff prompt. Its sampling and
rebuttal-focused skip criteria are owned by the [07A plan](07a_screen_pilot_candidates.md).

Tasks 07B–07D use focused Label Studio projects and enough narrow code
to prepare inputs, validate Codex proposals, import suggestions, export human
annotations, and produce the next stage's approved records. Prepare a
bounded batch and a self-contained prompt for a **separate Codex task** using
the user's existing app allowance. The user starts that task; Task 07 does not
automate paid API calls or require a live model backend inside Label Studio.
Keep the model proposal distinct from the curator-edited record.

07E instead uses chat: Codex drafts, Kyle gives feedback, and Codex revises until
explicit approval or stop. Its sealed exports preserve exact answer versions and
chat decisions; direct human editing and Label Studio forms are not required.

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

All executed stages close with human-reviewed outcomes or explicit stops; 07F
is satisfied by the combined 07E outcome, not a second review. At
least 50 distinct comment-rooted screening cases have curator decisions; only a
bounded selected subset is authored. Reviewers verify that each substantive
statement in a finalized reference answer is justified by the reviewed supporting
Draft EIR sources, or the case retains an insufficient-evidence status. This
does not require an exported statement-to-citation map or a separate outline.
The Task 07 outcome reports attrition, review
effort, failure patterns, and the Task 08 handoff without claiming formal
benchmark eligibility.

## Non-goals

Reviewing the complete response inventory; automatically declaring Task 08
eligibility; changing accepted Task 03/04/05/06 evidence; training or deploying
a model; an LLM judge; paid API integration; a workflow engine; or running the
target benchmark model.
