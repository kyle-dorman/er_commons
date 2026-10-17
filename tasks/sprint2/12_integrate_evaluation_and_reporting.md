# Task 12 — Finalize reporting and locked-test readiness

Status: provisional; not active. Refresh from accepted 09G, Task 10 and Task 11
outcomes before implementation. This contract assigns deferred reporting work;
it does not authorize judge calls, target generation or locked-test access.

## Abstract

Reuse the generation/evaluation integration established in [Task 11C](11c_integrate_development_evaluation.md) and the
frozen Luna candidate and development evidence from [Task 11E](11e_freeze_development_baseline.md). Audit routing,
exact artifact identities, independent judge inputs and component results.
Finalize combined reporting, including the accepted strict all-grounding-pass AND
S-pass AND C-pass result, and locked-test readiness before Task 13 uses it.

## Goal

Freeze a reproducible aggregate reporting contract using the established
per-question evaluation pipeline. Task 11 owns initial wiring and prompt cycles;
this task owns the follow-up audit, final denominator/aggregation rules and the
Task 13 reporting handoff. No new full labeling pass is required.

## Inputs

- [Frozen 09G judge bundle](../../docs/specs/task09g_judge_freeze_v1.json), including 09F adequacy and
  [09F.1 no-answer/grounding](09f1_revisit_grounding_judge.md) policies, prompts,
  model selections, schemas, records and limitations.
- Accepted [Task 10 evidence-only packets](10_prepare_evidence_only_inputs.md)
  and citation mappings, plus accepted Task 11C evaluation wiring and Task 11E
  frozen Luna configuration, actual delivery receipts, saved answers and evaluation
  reports, with source, corpus, question/split, configuration and candidate-content
  identities. Task 11 uses a nested three-then-six-question development cycle,
  followed by all 19 development questions; preserve those exposure groups.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [sprint evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary),
  existing automatic metrics and [artifact contract](../../docs/data_artifacts.md).

The documentation-only 09G freeze adds no reserved-set evaluation or end-to-end
validation. Task 11C owns initial whole-answer routing, exact identity joins,
automatic checks, frozen A/G/S/C dispatch, safe status handling and per-question
reports on real outputs. This task audits and reuses that implementation; it does
not repeat initial integration or reopen prompt development.

Under [Decision 007](../../docs/decisions/007_evidence_only_first_baseline.md),
the first condition supplies approved evidence. Retrieval recall is not applicable;
do not manufacture retrieval histories or score supplied evidence as discovery.
All checks here use only the 19 development cases; the 30 test cases remain locked.

## Outputs

- Final versioned aggregate reporting and denominator specification, with only
  the implementation additions needed beyond the accepted Task 11C pipeline.
- Separate automatic final-citation results (retrieval not applicable), point-grounding results, S/C
  decisions and adequacy aggregation, plus strict joint success and availability.
- Reused and extended offline truth-table/identity fixtures, bounded follow-up
  development audit evidence, replay instructions and frozen Task 13 reporting
  handoff. Report the six prompt-development cases separately from the remaining
  13; do not characterize the latter as a new independent benchmark split.

## Research / learning checkpoint

Use [Inspect's scoring guidance](https://inspect.aisi.org.uk/scorers.html)
and the existing project interfaces to separate saved answer generation from
evaluation/reporting. Verify the applicable maintained API before implementation.
Explain why independent judge inputs do not imply independent errors and why
separate-panel accuracies cannot be multiplied into measured joint success.

## Plan / spec requirement

1. Review the accepted Task 11C/11E implementation and evidence first. Bind exact
   saved answers, evidence receipts and frozen judge versions. Reuse the current
   answer adapter and legacy-field boundary without rewriting historical
   references/results or changing automatic citation semantics incidentally.
   Identify concrete reporting or audit gaps before adding implementation.
2. Audit the established no-answer route from Task 11C. Clean abstentions skip
   semantic calls; substantive responses continue; ambiguous/invalid/error outcomes remain
   explicit. Classify the conclusion only, then require empty support, qualifications
   and other answer prose before accepting abstention. Nonempty prose accompanying
   an abstaining conclusion is inconsistent/unresolved. Check abstention before
   requiring substantive support; do not trust status flags. Verify that a
   false exemption cannot disappear from routing validation or report coverage.
3. Verify that Task 11C automatically fails required points with missing citations
   or any unresolved candidate citation ID before G, without dispatching a model
   call. Retain
   those failures distinctly from evaluator artifact-read errors and semantic
   judgments. Preserve independent G/S/C inputs. Ground each required support/qualification
   item against its owned evidence; S gets all original support and qualifications,
   without evidence/filtering/verdicts; C keeps its frozen question/candidate/reference
   projection. Emit no conclusion-grounding or re-review call.
4. Audit that joins use only identical complete candidate answers and declared
   repeat identities.
   Require exact expected point coverage; reject duplicate/orphan/cross-answer
   observations. Preserve hashes and source/policy/prompt/schema/run versions.
5. Finalize reporting and denominator policy before examining locked results,
   building on Task 11C status handling and Task 11E development reports.
   Retain all component outcomes. Derive all-points-grounded and strict joint pass
   only from required valid observations; empty support must not pass vacuously.
   Distinguish semantic false, incomplete/invalid evaluation, ambiguous routing and
   abstention. Preserve known failures even when another component is unavailable.
   Show total eligibility, complete-evaluation coverage, missing outcomes and
   explicit abstention treatment. Keep historical grounding 0/1/2 scores distinct;
   do not silently reinterpret them as the new strict result.
6. Reuse Task 11C fixtures and add coverage only for demonstrated gaps. Verify:
   all pass; fabricated premises with S/C passing; grounded but insufficient reasoning; wrong/incomplete conclusion; a conclusion-only claim
   absent from support; mixed grounding results; factual qualifications; missing
   citations; optional-context boundaries; empty/malformed answers; clean/mixed
   abstention; invalid/missing/duplicate judgments; and multiple candidates sharing
   a question ID. Report per-point and per-answer units separately.
7. Replay a small, prebounded follow-up audit on saved real development target
   outputs. Reuse Task 11 receipts and judgments wherever identities match; identify
   missing aligned data explicitly. Declare budgets and repeats before any
   necessary new calls; an already validated initial integration need not be rerun.
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

The accepted Task 11 pipeline produces reproducible component and strict aggregate
reports from saved development records, with explicit routing, identity, exposure
group and availability accounting. A bounded follow-up audit verifies the final
reporting contract without duplicating initial integration.
Task 13 can use the same contract without choosing new denominator/aggregation rules
after seeing locked results. Remaining judge limitations are disclosed.

## Non-goals

Prompt cycles or new model search; another full labeling pass; target optimization;
test tuning; changing accepted evidence/reference policy incidentally; overwriting
historical artifacts; locked-test execution; commit or push.

## Outcome

Provisional reporting ownership updated for Task 11's Luna development sequence.
No implementation, generation, evaluation or locked-test access has run under this
contract. Refresh from accepted Task 11C/11E outcomes before activation. Task 13
owns locked execution and publication using the frozen reporting contract.
