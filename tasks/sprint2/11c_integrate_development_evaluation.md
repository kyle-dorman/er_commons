# Task 11C — Integrate development evaluation

Status: Provisional; refresh from accepted 11A and 11B before execution.

## Abstract

Connect automatic checks and frozen judges before any prompt-comparison cycle.

## Goal

Produce trustworthy per-question diagnostics from saved Luna answers using existing evaluation components.

## Inputs

Accepted 11B candidates/receipts, 11A panel, [09G freeze](../../docs/specs/task09g_judge_freeze_v1.json), judge guide, Task 10 mappings and [Task 12 reporting contract](12_integrate_evaluation_and_reporting.md).

## Outputs

A reusable evaluation command, exact candidate/point joins, routing specification, offline fixtures and compact per-question reports retaining automatic checks, A/G/S/C decisions, explanations and errors.

## Plan / spec requirement

Use this contract as the brief plan; record concrete interfaces and limits before implementation.

1. Specify generation/evaluation separation and joins keyed by complete candidate hash plus run/repeat and point identities; reject duplicates, orphan judgments, cross-answer joins and missing required coverage.
2. Integrate automatic schema/citation checks and final-citation precision/recall/F1 using canonical mappings and actual delivered evidence. Retrieval recall is not applicable, not perfect recall.
3. Apply frozen A no-answer routing to the conclusion, then check other answer prose before accepting clean abstention. Clean abstentions skip G/S/C; mixed, invalid and ambiguous outcomes remain explicit. Do not trust a target status flag or permit empty support to pass vacuously.
4. Before G, fail required uncited points and unresolved citations automatically, separately from artifact errors. Preserve G's point-owned evidence, S's original reasoning/qualifications and C's frozen question/candidate/reference projection. Do not add conclusion-grounding calls or feed judge verdicts across components.
5. Keep frozen Luna A/G/C and Haiku S configurations. Using Luna as the target does not replace S or retune judges. Preserve known calibration limits and possible correlated target/judge errors.
6. Define per-case availability/failure statuses before comparing prompts. Show automatic checks, per-point G, S/C, abstention and explanations; retain failures when another component is missing. Do not optimize an undeclared aggregate score.
7. Validate fixtures, then evaluate the bounded saved three-question smoke outputs with declared judge call/retry limits. Save all receipts for replay. Task 12 audits and finalizes aggregate denominators and strict joint reporting using this integration.

## Research / learning checkpoint

Use Inspect scoring and log guidance in the umbrella to score saved outputs without regenerating answers. Explain why judge agreement is diagnostic rather than proof and why independent inputs do not guarantee independent errors.

## Validation

Exercise clean/mixed abstention, empty/malformed answers, missing/unresolved citations, missing/duplicate/cross-answer judgments, partial evaluation and candidate repeats. Verify component projections and source-to-report hashes. Run make fix, make check and git diff --check.

## Acceptance criteria

Every attempted smoke candidate has a report or explicit failure; evaluation can be replayed without target generation. The three-question prompt loop can inspect automatic checks and frozen judge results together.

## Review pass

Independent review of routing, join identity, point coverage, leakage and error/status handling.

## Non-goals

No target prompt cycles yet, judge retuning, new labeling pass, test evaluation or final benchmark performance claims.

## Shared boundaries

Follow the [Task 11 umbrella](11_build_and_freeze_target_generation.md). Use only
the 19 development cases; no locked-test or reserved judge-challenge access.
Preserve Task 10 packets and frozen A/G/S/C judge policies. Keep references and
judge feedback outside target requests. Generated runs and reports belong under
`ER_COMMONS_DATA_ROOT`, with exact input/configuration hashes and fresh namespaces.
