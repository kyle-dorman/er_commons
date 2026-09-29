# Task 07G: Assess Pilot and Improve Dataset Authoring

Status: **Closed by Kyle's decision on 2026-09-29: proceed to Task 08.**

## Outcome and next step

Kyle chose to proceed without another pilot round or the full retrospective
specified below. Reusable lessons remain in the
[human review process](../../docs/response_comment_human_review_process.md).
[Decision 005](../../docs/decisions/005_task08_grouped_question_selection.md)
records the accepted Task 08 plan: use the prepared exclusive groups and review
until up to three reasonable questions are selected per group. Human selection
has not started. No full effort/attrition assessment or model comparison is
claimed as completed; sealed pilot records remain unchanged.

The sections below preserve the former assessment contract for context and are
superseded by this closure decision.

## Abstract and goal

Summarize what screening, question review, claims/relevance, evidence discovery
and combined reference-answer review taught us. Identify practical improvements
for broader dataset authoring in Task 08. Use Astra (`gpt-6-astra`) for all
model-assisted dataset-label authoring, with human review and explicit acceptance.
This is an authoring-workflow assessment, not a model comparison, benchmark target
run or automated judge evaluation. Follow the [Task 07 umbrella](07_pilot_reference_case_authoring.md).

The filename retains its earlier replay wording to preserve existing links; no
local-model replay remains in this task's scope.

## Inputs and outputs

- Inputs: sealed stage handoffs, proposals and revisions, human feedback and
  decisions, unresolved cases, and the six approved 07E reference answers pinned
  by [the final result](../../docs/specs/task07e_final_result.json).
- Output: an evidence-backed pilot assessment covering stage attrition, correction
  effort, evidence-search contribution, unresolved gaps, and recommendations for
  Task 08's questions, prompts, review presentation and acceptance criteria.
- Maintain the consolidated [comment and response human review process](../../docs/response_comment_human_review_process.md)
  as the reusable guidance that carries Task 07 learning into Task 08 planning;
  numbered task outcomes remain the record for historical evidence and decisions.
- Use the [current authoring prompt](../../docs/prompts/task07e_reference_answer_authoring_v2.md)
  and preserve the question → claims → citation summaries → proposed rebuttal
  chat workflow. Kyle gives feedback; Astra revises; human approval determines
  acceptance. Human-only stages remain human-only.
- Record actual model identity, prompt version and input/output provenance for
  future model-assisted authoring. Do not retroactively relabel historical runs.

## Research / learning checkpoint and plan

Start from the recorded pilot evidence. Distinguish observations from estimates:
revision counts and saved feedback are measurable; elapsed chat timestamps do not
establish active review time. Separate evidence-discovery failures from drafting
errors and scope problems. Consult primary guidance when a proposed workflow or
data-contract change needs external justification; record why it fits this MVP.

Present the assessment and a bounded Task 08 recommendation before changing the
broader authoring workflow. No new model experiment is required to close 07G.

## Validation, review, and acceptance

Verify stage counts and denominators against authoritative handoffs, preserve
input identities, and link conclusions to saved evidence. Separate full answer
drafts from partial-paragraph revisions. Carry forward accepted MVP warnings,
source substitutions and unresolved support gaps without silently repairing them.

Accept when Kyle has reviewed the findings and the recommendations explain what
to keep, change or stop for Task 08. Preserve the six approved answers, all prior
reviews and frozen question scopes. Authoring approval does not establish Task 08
eligibility or authorize benchmark execution.

## Non-goals

No local/no-extra-cost authoring-model comparison, model installation, automatic
label acceptance, target-model evaluation or LLM judge run. Astra is the selected
dataset-authoring model; this decision does not change the separately scoped
benchmark target and judge roles.
