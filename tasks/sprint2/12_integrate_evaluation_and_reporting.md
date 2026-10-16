# Task 12 — Integrate evaluation and define combined reporting

Status: provisional; not active. Refresh from accepted 09G, Task 10 and Task 11
outcomes before implementation. This contract assigns deferred reporting work;
it does not authorize judge calls, target generation or locked-test access.

## Abstract

Apply the frozen evaluator and judges to saved real development target answers.
Verify routing, exact artifact identities, independent judge inputs and component
results. Define and validate combined reporting, including the accepted strict
all-grounding-pass AND S-pass AND C-pass result, before Task 13 uses it.

## Goal

Connect the established components and freeze a reproducible reporting contract.
This is a bounded integration task, not another prompt-development/model-selection
project. No new full labeling pass is required.

## Inputs

- [Frozen 09G judge bundle](../../docs/specs/task09g_judge_freeze_v1.json), including 09F adequacy and
  [09F.1 no-answer/grounding](09f1_revisit_grounding_judge.md) policies, prompts,
  model selections, schemas, records and limitations.
- Accepted Task 10 retrieval/evidence receipts and Task 11 saved target answers,
  with source, corpus, question/split, configuration and candidate-content identities.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [sprint evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary),
  existing automatic metrics and [artifact contract](../../docs/data_artifacts.md).

The documentation-only 09G freeze adds no reserved-set evaluation or end-to-end
validation. This task still owns the real-output integration gate below.

## Outputs

- Versioned routing/join/reporting specification and deterministic implementation.
- Separate automatic retrieval/citation results, point-grounding results, S/C
  decisions and adequacy aggregation, plus strict joint success and availability.
- Offline truth-table/identity fixtures, bounded real-development integration
  evidence, replay instructions and frozen Task 13 reporting handoff.

## Research / learning checkpoint

Use [Inspect's scoring guidance](https://inspect.aisi.org.uk/scorers.html)
and the existing project interfaces to separate saved answer generation from
evaluation/reporting. Verify the applicable maintained API before implementation.
Explain why independent judge inputs do not imply independent errors and why
separate-panel accuracies cannot be multiplied into measured joint success.

## Plan / spec requirement

1. Bind exact saved answers, evidence receipts and frozen judge versions. Define
   the current answer adapter and legacy-field boundary without rewriting historical
   references/results or changing automatic citation semantics incidentally.
2. Integrate the established no-answer route. Clean abstentions skip semantic
   calls; substantive responses continue; ambiguous/invalid/error outcomes remain
   explicit. Classify the conclusion only, then require empty support, qualifications
   and other answer prose before accepting abstention. Nonempty prose accompanying
   an abstaining conclusion is inconsistent/unresolved. Check abstention before
   requiring substantive support; do not trust status flags. Verify that a
   false exemption cannot disappear from routing validation or report coverage.
3. Before G, automatically fail required points with missing citations or any
   unresolved candidate citation ID, without dispatching a model call. Retain
   those failures distinctly from evaluator artifact-read errors and semantic
   judgments. Preserve independent G/S/C inputs. Ground each required support/qualification
   item against its owned evidence; S gets all original support and qualifications,
   without evidence/filtering/verdicts; C keeps its frozen question/candidate/reference
   projection. Emit no conclusion-grounding or re-review call.
4. Join only identical complete candidate answers and declared repeat identities.
   Require exact expected point coverage; reject duplicate/orphan/cross-answer
   observations. Preserve hashes and source/policy/prompt/schema/run versions.
5. Define reporting and denominator policy before examining locked results.
   Retain all component outcomes. Derive all-points-grounded and strict joint pass
   only from required valid observations; empty support must not pass vacuously.
   Distinguish semantic false, incomplete/invalid evaluation, ambiguous routing and
   abstention. Preserve known failures even when another component is unavailable.
   Show total eligibility, complete-evaluation coverage, missing outcomes and
   explicit abstention treatment. Keep historical grounding 0/1/2 scores distinct;
   do not silently reinterpret them as the new strict result.
6. Verify offline cases: all pass; fabricated premises with S/C passing; grounded
   but insufficient reasoning; wrong/incomplete conclusion; a conclusion-only claim
   absent from support; mixed grounding results; factual qualifications; missing
   citations; optional-context boundaries; empty/malformed answers; clean/mixed
   abstention; invalid/missing/duplicate judgments; and multiple candidates sharing
   a question ID. Report per-point and per-answer units separately.
7. Run a small, prebounded integration check on real development target outputs.
   Use suitable existing receipts where identities match; identify missing aligned
   data explicitly. Declare budgets and repeats before any necessary new calls.
   Document substantive fixes and repeat affected development checks. Judge policy
   or prompt changes require explicit scope and component revalidation, not hidden
   integration tuning. Freeze report/configuration identities for Task 13.

## Validation and review

- Independently review join identity, eligible-item coverage, routing semantics,
  status truth tables and denominators; keep test/reserved material inaccessible.
- Recompute results from saved records and verify raw errors/unknowns remain visible.
  A strict success fraction is an additional diagnostic, not a substitute for the
  four separate benchmark result dimensions or a claim of human calibration.
- Verify replay, input separation and complete source-to-report provenance.
- Implementation: focused offline tests, `make fix`, `make check`, `git diff --check`.
  Planning: Markdown/link inspection and whitespace checks.

## Acceptance criteria

The frozen evaluator produces reproducible component and strict reports on a bounded
real-development run with explicit routing, identity and availability accounting.
Task 13 can use the same contract without choosing new denominator/aggregation rules
after seeing locked results. Remaining judge limitations are disclosed.

## Non-goals

Prompt cycles or new model search; another full labeling pass; target optimization;
test tuning; changing accepted evidence/reference policy incidentally; overwriting
historical artifacts; locked-test execution; commit or push.

## Outcome

Provisional reporting ownership assigned from 09F.1. Implementation and real-output
integration await accepted upstream outcomes. Task 13 owns locked execution and
publication using the frozen reporting contract.
