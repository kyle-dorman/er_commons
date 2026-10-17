# Task 11D — Iterate the prompt on three then six questions

Status: Provisional; refresh from accepted 11A–11C before execution.

## Abstract

Improve the Luna prompt through bounded comparisons on the fixed nested panels.

## Goal

Select a candidate prompt using three questions first, then six, with traceable reasons for every change.

## Inputs

Accepted panel/criteria and budgets from 11A, runner from 11B and integrated reports from 11C.

## Outputs

Versioned prompts and configurations, saved candidate/evaluation artifacts, compact comparison and decision record, selected candidate and remaining issues.

## Plan / spec requirement

Use this contract as the brief plan; record concrete interfaces and limits before implementation.

1. Freeze the initial prompt and declare concrete revision, call/cost, repeat and stopping limits before dispatch. Hold model, evidence and judges fixed so prompt effects remain interpretable.
2. Run the first three cases; inspect answers, source fidelity, automatic checks and judge explanations together. Record a specific hypothesis for each revision and preserve rejected versions.
3. Compare revisions on identical cases/settings; label retries and repeats. Do not cherry-pick favorable stochastic answers or suppress invalid outputs.
4. Once a candidate meets the recorded criteria or the first-cycle budget ends, expand to the fixed six (the original three plus three). Apply the same bounded comparison process and record regressions as well as gains.
5. Select a candidate with a rationale and disclosed failures, or explicitly report no acceptable candidate within budget. Manual review may disagree with a judge; preserve both without modifying frozen judge policy.
6. Keep reference answers and evaluator feedback out of individual generation requests. This is global prompt development, not a per-answer judge-feedback repair loop. Do not copy case-specific answers into the prompt.

## Research / learning checkpoint

Revisit the umbrella scoring/log references for paired saved-output comparisons. Explain adaptive selection bias and distinguish a prompt hypothesis from evidence of broad performance.

## Validation

Check complete declared panel coverage per revision, unchanged packet/judge identities, retained failures and budget accounting. Inspect prompt diffs and replay reports. Apply make checks if code changes; otherwise git diff --check.

## Acceptance criteria

A selected candidate, exact configuration and honest comparison record are ready for 11E, or the bounded failure is recorded without claiming completion of a baseline freeze.

## Review pass

Bounded review of comparison fairness, evidence fidelity, selection rationale and tuning exposure.

## Non-goals

No remaining-13 evaluation during cycling, test access, model sweep, evidence edits or judge optimization.

## Shared boundaries

Follow the [Task 11 umbrella](11_build_and_freeze_target_generation.md). Use only
the 19 development cases; no locked-test or reserved judge-challenge access.
Preserve Task 10 packets and frozen A/G/S/C judge policies. Keep references and
judge feedback outside target requests. Generated runs and reports belong under
`ER_COMMONS_DATA_ROOT`, with exact input/configuration hashes and fresh namespaces.
