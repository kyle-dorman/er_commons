# Task 11E — Freeze and check the development baseline

Status: Provisional; refresh from accepted 11D before execution.

## Abstract

Freeze the selected Luna candidate and run a broader development check before final reporting.

## Goal

Qualify the complete generation/evaluation path on all 19 development questions and hand off to Task 12.

## Inputs

Accepted 11D candidate, 11A panel/exposure record, 11B runner, 11C evaluator and Task 10 development publication.

## Outputs

Frozen prompt/model/settings/schema/evaluator identities; saved outputs and per-question reports for all 19; bounded repeatability results; exposure-aware summary and Task 12 handoff.

## Plan / spec requirement

Use this contract as the brief plan; record concrete interfaces and limits before implementation.

1. Pin the candidate and declare run/repeat budgets, stability subset and criteria before viewing broader results. Verify context/output fit per request; preserve explicit failures.
2. Run and evaluate all 19 development cases using the same frozen configuration. Record reuse only where exact receipts/configuration match; otherwise create fresh versioned runs.
3. Report the six prompt-development cases separately from the remaining 13, plus all-19 coverage. Neither group is the locked test set; preserve prior development exposure and overlap limitations.
4. Repeat the predeclared bounded subset to assess schema, citation and semantic stability without selecting the best answer. Distinguish target variation from judge variation using saved outputs and fixed evaluator identities.
5. Record deficiencies and decide readiness for Task 12. If broader results trigger a prompt change, version it, disclose newly exposed cases, return to the bounded development loop and rerun affected checks; do not describe the revised result as untouched validation.
6. Hand off exact request/candidate/judge receipts, failure accounting and selected configuration. Task 12 finalizes aggregate reporting and locked-test readiness; Task 13 alone executes the locked 30.

## Research / learning checkpoint

Use Inspect log guidance for reproducible run/repeat identities. Explain a frozen configuration versus a passing result, and why a development check cannot establish held-out performance.

## Validation

Verify 19 unique expected IDs, all attempted outcomes, exact identities, six/13 reporting separation, repeat accounting, replay and no locked-test reads. Run make fix, make check and git diff --check for implementation changes.

## Acceptance criteria

A sealed development handoff exists with explicit readiness or blockers and all failures preserved. No perfect-score threshold or independent-performance claim is invented after seeing results.

## Review pass

Independent bounded review of freeze identities, completeness, exposure claims, stability evidence and Task 12 readiness.

## Non-goals

No locked-test run, new judge policy, open-ended prompt tuning, retrieval or public benchmark conclusions.

## Shared boundaries

Follow the [Task 11 umbrella](11_build_and_freeze_target_generation.md). Use only
the 19 development cases; no locked-test or reserved judge-challenge access.
Preserve Task 10 packets and frozen A/G/S/C judge policies. Keep references and
judge feedback outside target requests. Generated runs and reports belong under
`ER_COMMONS_DATA_ROOT`, with exact input/configuration hashes and fresh namespaces.
