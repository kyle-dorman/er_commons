# Task 11 — Build and freeze Luna target generation

Status: Complete with limitations. The user-accepted focused conclusion prompt
and shared overview were frozen in [11E](11e_freeze_development_baseline.md) and
checked on all 19 development questions for Luna and Haiku, three repeats each.
The sealed handoff is ready for Task 12 reporting/readiness review; locked-test
readiness is not established. Historical prompt comparisons retain their outcomes.

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
| [11B — Build the Luna generation runner](11b_build_luna_generation.md) | Complete with documented limitations; [result](../../docs/specs/task11b_final_result.json) |
| [11C — Integrate development evaluation](11c_integrate_development_evaluation.md) | Complete with documented limitations; [result](../../docs/specs/task11c_final_result.json) |
| [11D — Iterate the prompt on three then six questions](11d_iterate_development_prompt.md) | Complete; no selection after full fixed-six comparisons |
| [11D.1 — Public rubric and examples](11d1_public_rubric_prompt_comparisons.md) | Complete; examples improved observed scores, but no repeat-qualified candidate |
| [11D.2 — Evaluation contract corrections](11d2_resolve_evaluation_contract.md) | Complete; retain V6b; 11D.3 tested the C014 alternative and retained original wording |
| [11D.3 — Light question comparison](11d3_test_light_question_wording.md) | Complete; no demonstrated wording improvement |
| [11D.4 — Alternative-model coverage](11d4_compare_alternative_models.md) | Complete; no additional coverage beyond Luna’s five of six |
| [11D.5 — Haiku output allowance](11d5_raise_haiku_output_cap.md) | Complete; truncation resolved, no added question coverage |
| [11D.6 — Context and qualifications](11d6_simplify_context_and_qualifications.md) | Complete offline; shared context and edition-neutral derivatives prepared, not evaluated |
| [11D.8 — V10 model comparison](11d8_compare_v10_luna_haiku.md) | Complete; Luna 5/12 and Haiku 3/12 all-checks passes; no selection |
| [11E — Freeze and check the development baseline](11e_freeze_development_baseline.md) | Complete with limitations; 114/114 evaluated |

Outputs progress from panel selection to a runner, integrated per-case evaluation,
versioned prompt comparisons and a frozen 19-case development handoff. Exact IDs,
Luna model/provider/settings and final call budgets are decided in the owning
subtask before runs. 11A fixes IDs and criteria and proposes budgets; 11B completed
one bounded three-case smoke. 11C evaluated those saved candidates with frozen judges
and verified no-call replay. 11D compared two revisions on three, then completed V3/V4 fixed-six comparisons
after an authorized input-cap increase. No candidate was selected. See its outcome
before any follow-up. [11D.1](11d1_public_rubric_prompt_comparisons.md) adds a public answer specification and three paired comparisons; its [result](../../docs/specs/task11d1_final_result.json) retains no selection and evaluation-interface limitations.
The three-day working timebox remains a planning target, not an implicit call budget.

## Plan / spec requirement

Use the contracts in order, including the bounded 11D.1 follow-up before any 11E activation. 11C owns the initial whole-answer routing, exact
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

## Current working prompt

The user accepted the [11D.12 focused conclusion check](11d12_conclusion_focus.md)
and [11D.14 document overview](11d14_document_overview.md). The [selection](../../docs/specs/task11_working_prompt.json)
binds the exact base and shared target/judge context, preserving frozen judge cores.
Qualification/citation rewrites remain excluded. The combined configuration was
validated on the fixed six in [11D.15](11d15_fixed_six_consolidation.md), three repeats per model/question: Luna15/18 and Haiku6/18 all-checks passes. Retain the accepted stack with documented limitations. [11E](11e_freeze_development_baseline.md) completed all19 for both models, three repeats each: Luna29/57 andHaiku6/57 all-checks passes. Task12 can consume the development handoff with limitations.
No further run is active; locked-test readiness is not established.

## Closeout review

Task 11 is complete with limitations. A bounded independent contract review found
no missing acceptance deliverable. Closeout verified all 19,673 sealed 11E files
and all 26 result-pointer bindings by size and SHA-256. All 114 planned answers,
repeats, failures, manual reviews and accounting are retained; no new calls were
made for this review.

The accepted condition includes invented nonbenchmark examples, the focused
conclusion check and shared document overview. It is not the sprint's originally
proposed zero-shot condition. The recorded output-token allowance replaces the
provisional word-limit experiment for this accepted development handoff; no
200/400-word comparison is claimed. Native unseeded repeats and their limitations
remain explicit. Historical configurations and results remain unchanged.

Task 12 remains provisional and owns final aggregation, routing/denominator
policy and locked-test readiness. Model failures, disputed reference/judge
readings, mixed-edition overview framing and uncertain counting charges are
limitations to carry forward, not grounds for another prompt cycle at closeout.
