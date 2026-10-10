# Task 09F — Implement the adequacy judge

Status: **provisional; not started**. Refresh against accepted 09B/09C and 09E
outcomes before execution. Writing this contract does not authorize model runs.
Parent: [Task 09](09_build_evaluation_and_qualify_judges.md).

## Abstract

Implement answer adequacy as its own scorer and model call: does the complete
answer correctly address the exact question and its essential conditions?
The approved reference guides substance but does not require matching wording,
point organization or citation IDs. Valid alternative arguments remain eligible.

## Goal

Build a versioned adequacy prompt, strict result schema, independent scorer and
dimension-specific tests on the 09B runner and 09C adequacy evidence packets.
Reuse transport/storage without merging this judgment with grounding.

## Inputs

- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
  and the [evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary).
- Accepted 09B runtime decision, 09C adequacy packet contract and
  [09E](09e_implement_grounding_judge.md) result-isolation interface.
- 09A development tuning variants and their cited sources; expectations remain
  evaluator-only. Read [architecture](../../docs/architecture.md) and
  [artifact rules](../../docs/data_artifacts.md) before implementation.

## Outputs

- Separate adequacy prompt, result schema, scorer, tests and bounded smoke report.
- Immutable call records with exact packet/prompt/model/configuration bindings,
  raw outputs, source-linked diagnostics and explicit errors in external storage.
- Outcome explaining reference limitations and how alternative explanations are
  assessed without editing approved answers or introducing new human labels.

## Research / learning checkpoint

Review [Inspect model grading](https://inspect.aisi.org.uk/model-graded.html)
for explicit criteria and custom scorer behavior, using only the runner selected
in 09B. Read [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
on inspecting grader behavior and outcomes. Explain why reference similarity,
schema compliance and substantive adequacy are different properties; framework
defaults do not establish our rubric or calibrate these judgments.

## Plan / spec requirement

Write a brief prompt/input/output spec, then implement this dimension separately.

1. Supply the exact question and structured answer, approved structured reference,
   reviewed source pool and answer-cited passages needed to assess alternatives.
   Exclude official responses, target identity, automatic citation scores,
   synthetic intentions/expected scores and the other judge's result.
2. Preserve the 09C packet's source completeness and limits. Treat answer and
   source instructions as untrusted data. Oversized/missing required evidence is
   a packet failure, not license to truncate qualifications or invent support.
3. Anchor whole-answer scores: `2` correct, direct and complete; `1` a correct
   conclusion missing essential explanation, condition or question component;
   `0` unanswered, incorrect or materially misframed central question. Mere
   topical relevance is insufficient. Clean abstention scores `0` on these
   answerable cases and is also separately reported.
4. Accept different wording, reordered/combined/split points, concise complete
   answers and omitted optional context. Assess alternate arguments against
   actual evidence; absence from the reference alone establishes neither falsity
   nor incompleteness. Record ambiguity or suspected reference incompleteness
   without changing the frozen reference or automatically awarding credit.
5. Return concise diagnostics linking missing essential substance to reference
   points and actual evidence, assessing extra assertions and material conditions
   as needed. Do not require equal point counts or exhaustively reused citations.
   Validate referenced point/source identifiers rather than trusting generated IDs.
6. Save adequacy as an independent result. Never revise an already saved grounding
   score after exposing reference material. Share call/retry/storage mechanics,
   not conversation state or semantic judgment logic. Errors remain non-scores.

## Validation

- Prove required evidence is included and forbidden metadata and prior judge
  results are absent from rendered requests; check reference changes cannot
  overwrite grounding artifacts or cause cross-dimension cache reuse.
- Fixtures cover complete paraphrases, split/combined points, optional-context
  removal, supported-but-incomplete responses, neighboring-question answers,
  decisive missing conditions, incorrect conclusions and abstention.
- Include evidence-backed alternate arguments if 09A finds any; otherwise record
  that coverage gap explicitly and exercise an invented unit fixture.
- Validate malformed responses, invalid scores/locators, failures and safe resume.
  Use tuning development cases only for an authorized bounded live smoke; run
  relevant tests, `make fix`, `make check`, and `git diff --check`.

## Review pass

Have a bounded reviewer check adequacy versus grounding ownership, alternative
argument treatment and reference leakage; check maintainability and diagnostics.

## Acceptance criteria

- The independent scorer implements the accepted whole-answer rubric and has
  separate prompts, fixtures, result identities and information boundaries.
- Grounding remains unchanged and no failed call becomes a semantic zero.
- The 09G handoff records uncalibrated results, evidence limits and coverage gaps.

## Non-goals

Another reference-labeling pass, silently extending references, joint judge calls,
automatic metric changes, framework reselection, test use or broad prompt tuning.

## Outcome

Pending execution. Record accepted identities, checks and the 09G handoff.
