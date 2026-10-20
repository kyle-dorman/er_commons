# Task 12 — Build results tables, charts and locked-test reporting

Status: planning refreshed 2026-10-20; next, not active. Bind accepted 09G,
Task 10 and Task 11 outcomes before implementation. This contract assigns deferred reporting work;
it does not authorize judge calls, target generation or locked-test access.

## Abstract

Reuse the generation/evaluation integration established in [Task 11C](11c_integrate_development_evaluation.md) and the
frozen Luna and Haiku configurations and development evidence from [Task 11E](11e_freeze_development_baseline.md). Audit routing,
exact artifact identities, independent judge inputs and component results.
Build replayable tables and charts for both models, each component, joint success,
repeatability, automatic citation metrics and existing judge calibration evidence.
Freeze the reporting contract and readiness decision before Task 13 uses it.

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
  [frozen Luna and Haiku configurations](../../docs/specs/task11e_frozen_generation_v1.json),
  [11E results](../../docs/specs/task11e_result.json), [11F maintenance](11f_cleanup_target_generation.md),
  actual delivery receipts, saved answers and evaluation
  reports, with source, corpus, question/split, configuration and candidate-content
  identities. Task 11 uses a nested three-then-six-question development cycle,
  followed by all 19 development questions; preserve those exposure groups.
- Historical judge-quality sources: [A](../../docs/specs/task09f1_a_full_development_v2_result.json),
  [G](../../docs/specs/task09f1_g_full_development_v3_result.json),
  [S/C](../../docs/specs/task09f_inspect_full_dev3_result.json),
  [selection/label limitations](../../docs/specs/task09f_final_result.json).
  Reuse their exact evaluated populations and any calibration-overlap partitions.
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

## Required tables and charts

Build these from saved development outputs first, with the same frozen reporting
code ready for Task 13. Export underlying machine-readable tables and static,
shareable charts; retain exact case/model/run/repeat identities. Generated reports
live under the external artifact root. Do not build a dashboard framework.

| Report | Required views |
| --- | --- |
| Model results | Luna and Haiku separately: A routing/answerability outcomes, G point-level and all-required-points pass rates, S and C pass rates, automatic checks and strict joint success. Show counts, denominators, eligibility and missing/error states. |
| Repeatability | Exactly three planned answers per question/model: each repeat, pooled observed pass fraction, 0/1/2/3 passes, at least once and every time, for each applicable component and the joint criterion. |
| Question overview | Question-by-model heatmap/table of component and joint results across repeats. Separate original six, additional thirteen and later locked test; never pool development with test. |
| Automatic evidence/citation metrics | Returned-citation precision, recall and F1, macro and micro, plus invalid IDs and availability. Display verified delivery coverage as an input audit; search/read-retrieval metrics are N/A for evidence-only. |
| Complexity associations | Luna (the primary, most-used development model): accuracy/pass rates versus distinct citations, sections and documents cited. Include counts and spread, plus input-evidence counts as separate covariates where available. |
| Judge accuracy | Existing frozen A/G/S/C predictions against their recorded reference labels: accuracy, precision, recall, F1 and confusion counts where valid and reconstructable. Label the positive class, evaluation unit, dataset/panel, exposure, label provenance, selected judge version and support size. |

### Definitions to freeze before locked results

- Use **model pass rate** for frozen-judge outcomes on target answers. Use **judge
  accuracy/F1** only for agreement against independently specified labels. Prior
  model-proposed labels must be identified as such; they are not human gold.
  A is a three-class routing classifier: show per-class precision/recall/F1 and
  macro-F1, with class definitions. G/S/C binary metrics must name the positive
  class. Show valid-only agreement with coverage and failure-inclusive accuracy
  separately; invalid predictions are not ordinary negative labels.
  Calibration is historical development evidence, not fresh held-out validation.
  Reuse existing summaries/aligned records; unavailable metrics stay unavailable.
  No new human labeling or judge calibration study belongs to Task 12.
- Joint success requires the applicable automatic checks, correct A routing,
  every required G point, S and C to pass on the **same answer**. Freeze clean
  abstention and invalid/missing handling explicitly; never interpret a raw A
  yes/no as correctness without its routing meaning. Never stitch passing
  components from different repeats or models into a joint pass.
- For a complete triple, at-least-once means >=1/3 passes and every-time means
  3/3. Publish unique-question denominators and triple completeness. Missing/error
  slots must not disappear: show full-planned coverage and explicitly unresolved
  repeat outcomes separately from measured semantic failures. These observed
  three-run summaries are not independent-sample estimates or deployment selectors.
- Freeze output-count definitions using distinct resolved canonical citation units,
  distinct stable source/section identities and distinct source documents; report
  invalid/unresolved IDs separately. Do not count repeated mentions or equate
  display headings with section identity. If stable section mapping is absent,
  record unavailable rather than invent an identity. Count the complete returned
  answer, and declare any field-specific auxiliary view separately.
- Output citation counts are model behavior, not intrinsic question difficulty.
  Label the plots descriptive associations, not causal explanations. Show bin N,
  preserve question/repeat grouping, avoid sparse fitted trends, and freeze bins
  from development before viewing locked results. Keep supplied-evidence counts
  distinct from output-cited counts. Do not switch the primary model after test.
- Reuse [09D metric semantics](../../docs/specs/task09d_automatic_metrics_v1.md):
  canonical matching, neutral context, eligibility, macro/micro definitions and
  explicit missing versus empty receipts. Automatic citation matching measures
  reference coverage, not semantic grounding. Do not invent retrieval precision/F1
  if only retrieval recall is defined by the accepted metric contract.
- The evidence-only condition supplies evidence; it does not measure successful
  search or literal model attention. Verified delivery coverage is an input audit.
  Keep retrieval/read-evidence recall and ranked diagnostics available in the
  report schema for a later search condition, with N/A now. Do not import the
  historical five-unit retrieval budget into evidence-only generation.

Task 14 owns selective failure/evaluator-disagreement discussion after Task 13.
Task 15 owns dataset construction/coverage narrative and the short writeup. This
task supplies reusable figures/tables and reuses existing reviews as provenance;
it does not launch a comprehensive failure annotation project.

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
   missing aligned data explicitly. This task is offline: reuse existing calls;
   new calls require a separately authorized scope. Recompute all 114 saved 11E
   answer observations; keep additional manual audit small and gap-driven.
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
The required tables/charts reproduce their machine-readable values, and judge
calibration quality is clearly separated from target-model pass rates.
Task 13 can use the same contract without choosing new denominator/aggregation rules
after seeing locked results. Remaining judge limitations are disclosed.

## Non-goals

Prompt cycles or new model search; another full labeling pass; target optimization;
new model/counting calls; comprehensive human failure review; methods/results prose;
test tuning; changing accepted evidence/reference policy incidentally; overwriting
historical artifacts; locked-test execution; commit or push.

## Outcome

Planning updated for the user-approved Task 12–15 split: tables/charts here,
locked execution in 13, selective review in 14, concise writeup in 15.
No implementation, generation, evaluation or locked-test access has run under this
contract. Refresh from accepted Task 11C/11E outcomes before activation. Task 13
owns locked execution using the frozen reporting contract; Task 14 owns selective
review and Task 15 the short methods/results writeup.
