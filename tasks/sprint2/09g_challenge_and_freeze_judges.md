# Task 09G — Challenge and freeze both judges

Status: **provisional; not started**. Refresh from accepted 09A–09F.1 outcomes
before execution. This contract does not itself start evaluation or model calls.
Parent: [Task 09](09_build_evaluation_and_qualify_judges.md).

## Abstract

Exercise the separate judges on synthetic development answers, diagnose observed
failures and freeze a reproducible initial configuration within the October 12–14
working window. Agreement with Astra's proposed expectations is a development
check, not human calibration or proof that either judge is reliable.

## Goal

Produce a compact, inspectable account of where each judge succeeds or fails,
with bounded revisions and an honest handoff to retrieval/target development.
Do not turn known weaknesses into an open-ended qualification project.

## Inputs

- Accepted 09A variants, coverage/skip records, evidence-based proposed G/A
  expectations and uncertainty dispositions, all from the 19 development cases.
- Accepted 09B runtime/runner qualification, 09C packets and 09D automatic metrics.
- [09F.1 grounding revisit](09f1_revisit_grounding_judge.md) policy, component datasets and evaluation outcome.
- Include 09F.1's independently established no-answer classifier and point-only
  grounding selections in the frozen bundle. Combined routing/reporting and strict
  joint success belong to [Task 12](12_integrate_evaluation_and_reporting.md), not
  a prerequisite combined-reporting implementation in judge development. Refresh
  historical call-count and 0/1/2 assumptions below to the accepted component contracts.
- [09E grounding](09e_implement_grounding_judge.md) and
  [09F adequacy](09f_implement_adequacy_judge.md) implementations and smoke results.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
  and [artifact rules](../../docs/data_artifacts.md).

## Outputs

- Versioned run configurations, saved per-dimension judgments and comparison
  tables, disagreement dispositions, coverage gaps and call/runtime accounting.
- A frozen initial judge bundle binding model/runtime, prompts, schemas, packet
  construction, scorer versions, decoding limits and retry/failure policy.
- A concise limitations report and Task 10/12 handoff with replay instructions;
  all bulk predictions/reports stay beneath the configured external root.

## Research / learning checkpoint

Use [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
for grader inspection and bounded development checks, and
[Inspect model grading](https://inspect.aisi.org.uk/model-graded.html) for grading
robustness if that runner was selected. Preserve the distinction between agreement
with proposed synthetic expectations and separately authorized human calibration.
Explain why many correlated mutations are not many independent benchmark cases.

## Plan / spec requirement

Record a short run/report specification and call budget before executing.

1. Confirm a deterministic tuning/final-check allocation of synthetic variants
   from development cases was recorded before prompt tuning in 09E/09F. Preserve
   meaningful failure types in both where feasible. The final-check subset is
   reserved development material, never the benchmark's 30 test cases, and may
   share base questions with tuning variants. Report this dependence plainly.
2. Count eligible variants and packet sizes; estimate approximately `2 × N`
   initial calls (one per dimension) plus explicitly budgeted revisions,
   repeats and retries. Use 09B measured latency to project elapsed time before
   launching. Narrow repeated reruns rather than silently dropping failure types.
3. Run the tuning subset with proposed expectations hidden from each judge.
   Save grounding before reference-bearing adequacy; retain every result/error
   and ensure resumption never reuses a different prompt or packet identity.
4. Report each dimension separately: exact agreement with proposed expectations,
   `0/1/2` confusion counts, per-expected-class agreement, distributions and
   failure-type breakdowns. Highlight expected `0/1` receiving `2` and expected
   `2` receiving penalties. Show denominators, uncertain/excluded expectations,
   abstentions/N/A and execution errors separately; no blended accuracy headline.
5. Diagnose disagreements as judge interpretation, ambiguous/wrong synthetic
   expectation, mutation defect, evidence-packet failure or reference limitation.
   Correct genuine artifact defects with new versions and reasons; do not relabel
   expectations solely to agree with the judge. No full human labeling pass.
6. Permit at most two prompt-revision rounds across the qualification pass.
   Retain before/after outputs and rationale. Stop at the timebox with weaknesses
   recorded; structural failures that prevent valid scoring remain explicit
   blockers rather than being called successful qualification.
7. Repeat a small predeclared stratified tuning sample once under identical
   settings with response-cache reuse disabled to assess score stability. Report
   disagreement counts and runtime; do not silently majority-vote scores.
8. Freeze the candidate, then run reserved final-check variants once. Report
   results without further tuning on that subset; an essential subsequent repair
   must disclose that its results are no longer an untouched final check.

## Validation

- Verify zero test case IDs in synthesis/judge inputs and no expectation fields
  in requests; ensure each judgment binds its exact dimension and packet.
- Recompute comparison tables from saved records; test score/N/A/error
  denominators, missing results, revised expectations and duplicate variant IDs.
- Check manifest/file closure, restart behavior and readable replay instructions.
  Run relevant tests and `make fix`, `make check`, and `git diff --check` for code
  changes; docs-only closeout uses diff/link inspection and `git diff --check`.

## Review pass

Use scoped independent review of comparison denominators, leakage and failure
dispositions, plus a practical check that limitations match the observed results.

## Acceptance criteria

- Both configurations and complete qualifying records are pinned and replayable;
  reserved-check use, revisions, errors and remaining weaknesses are disclosed.
- Results are labeled **uncalibrated automated judgments**. There is no invented
  accuracy threshold, reinstated 80-percent gate or claim of human agreement.
- The outcome states whether each judge is operational with known limitations
  or blocked, and names Task 12's small real-output integration check.

## Non-goals

Test tuning, new human labels, perfect agreement, many-model comparisons, agentic
retrieval, target execution, reference repair or expansion into another sprint.

## Outcome

Pending execution. Record frozen identities, findings, budgets and next task.
