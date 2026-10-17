# Task 11 — Build and freeze Luna target generation

Status: 11A complete; 11B is next, pending contract refresh. Implementation has not started.
Refresh each provisional subtask from the accepted preceding outcome before execution.

## Abstract

Start with Luna answering from the Task 10 evidence-only packets. Select three
questions, expand to a nested six for prompt iteration, then check a frozen
candidate on all 19 development questions. Integrate automatic checks and frozen
judges before cycling prompts. This replaces the earlier Qwen3 4B starting choice.

## Goal

Produce a reproducible development baseline with cited supporting points,
applicable qualifications and a conclusion, plus evaluation evidence sufficient
to understand failures and choose a prompt. No retrieval or locked-test execution.

## Inputs

- [Task 10 handoff](../../docs/specs/task10_final_result.json) and [format](../../docs/specs/task10_evidence_only_v1.md).
- [09G judge freeze](../../docs/specs/task09g_judge_freeze_v1.json) and [maintainer guide](../../docs/judge_maintainer_guide.md).
- [Sprint plan](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md), [architecture](../../docs/architecture.md), [artifact contract](../../docs/data_artifacts.md).

## Outputs and sequence

| Subtask | Status |
| --- | --- |
| [11A — Select development panels and success criteria](11a_select_development_panels.md) | Complete; [panels and protocol](../../docs/specs/task11a_development_panels_v1.json) fixed |
| [11B — Build the Luna generation runner](11b_build_luna_generation.md) | Provisional |
| [11C — Integrate development evaluation](11c_integrate_development_evaluation.md) | Provisional |
| [11D — Iterate the prompt on three then six questions](11d_iterate_development_prompt.md) | Provisional |
| [11E — Freeze and check the development baseline](11e_freeze_development_baseline.md) | Provisional |

Outputs progress from panel selection to a runner, integrated per-case evaluation,
versioned prompt comparisons and a frozen 19-case development handoff. Exact IDs,
Luna model/provider/settings and final call budgets are decided in the owning
subtask before runs. 11A fixes IDs and criteria and proposes budgets; no calls ran.
The three-day working timebox remains a planning target, not an implicit call budget.

## Plan / spec requirement

Use the five contracts in order. 11C owns the initial whole-answer routing, exact
candidate joins and per-case diagnostics needed for iteration. [Task 12](12_integrate_evaluation_and_reporting.md)
reuses this path to finalize aggregate denominators, strict combined reporting and
locked-test readiness; it does not rebuild the integration or reopen judge tuning.
Use frozen Luna A/G/C and Haiku S judges; Luna target selection does not change them.
Keep source/reference and judge-feedback projections separate from target requests.

## Research / learning checkpoint

Reviewed 2026-10-17: [Inspect datasets](https://inspect.aisi.org.uk/datasets.html)
support explicit sample IDs and separate input/reference metadata;
[scorers](https://inspect.aisi.org.uk/scorers.html) separate answer generation from
scoring; [evaluation logs](https://inspect.aisi.org.uk/eval-logs.html) retain run and
sample records. Reuse the project's native Inspect integrations and saved-output
boundaries. Check concrete APIs at implementation time. Preserve brief learning
notes explaining tuning exposure, semantic versus structural validity, and exact
request provenance; do not add a workflow framework.

## Validation and acceptance criteria

Each subtask owns bounded validation. The final handoff covers all 19 attempted
cases and explicit failures, exact source/request/candidate/judge identities,
repeatability limits and separate six-versus-13 summaries. All six iteration cases
are tuning data; the other 13 are development checks, not independent held-out
performance estimates. The 30 test cases remain locked for Task 13. No silent
truncation, missing-result exclusion or judge-policy changes are permitted.

## Review pass

Use bounded independent reviews at panel selection, runner/evaluator boundaries,
prompt comparison and final handoff, as specified in the subtasks. Reconcile
findings before promoting artifacts. Planning changes require link/diff review
and git diff --check; implementation uses make fix and make check.

## Non-goals

BM25 or other retrieval, model sweeps, judge development, reference re-curation,
case-specific answer hints, automatic judge-feedback answer repair, locked-test
execution or a claim that judge success proves correctness.
