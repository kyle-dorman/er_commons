# Task 09 — Build evaluation and qualify two judges

Status: **09A–09D complete with limitations;
09E Qwen 9B Dev3 comparison complete; 09E.1 cloud/decision comparison planned;
09F–09G provisional.**
Reconcile later contracts with preceding outcomes before activation. The October 9
execution authorization covered 09A, including its full Astra authoring batch.
The October 10 request authorized 09B after runner/model/runtime discussion:
Inspect AI, local Ollama and a bounded two-model qualification. The later October
10 request authorized 09C packet construction and offline validation only.
The subsequent 09D start request authorized automatic metrics and offline Inspect
qualification, without inference or later-task work.

## Abstract

Turn the approved four-part evaluation into a runnable, inspectable evaluator.
Create synthetic development answers first, choose the runner and qualify local
inference, then implement mechanical metrics and each semantic judge separately.
Synthetic challenges expose weaknesses; their proposed scores are not human gold.

## Goal

Freeze automatic scoring and two separately tested judges, with reproducible
inputs, diagnostics, challenge results and explicit limitations. Target completion
is October 14, 2026, following the intended October 9 synthesis kickoff and
October 12–14 evaluation window; dates are planning targets, not execution claims.

## Inputs

- [08H release](../../docs/specs/task08h_final_result.json) and
  [outcome](08h_serialize_and_freeze_benchmark.md): `task08_20261009_v1`, 49 cases,
  exactly 19 development and 30 test. Preserve the approved allocation and seals.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
  and [evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
  own formulas, 0/1/2 rubrics, source eligibility and judge visibility.
- [Architecture](../../docs/architecture.md), [artifact contract](../../docs/data_artifacts.md),
  and [task shape](../README.md) govern implementation and publication.

## Plan and subtask contracts

| Task | Deliverable | Dependencies |
| --- | --- | --- |
| [09A — Synthetic answers](09a_create_synthetic_challenges.md) | Framework-independent development variants, proposed expectations, coverage and provenance | Frozen 08H |
| [09B — Harness and local inference](09b_choose_harness_and_qualify_local_judge.md) | Bounded runner decision and measured local inference qualification | 09A representative packets |
| [09C — Evidence packets](09c_build_judge_evidence_packets.md) | Validated, separate grounding and adequacy inputs | 09A, 09B |
| [09D — Automatic metrics](09d_implement_automatic_metrics.md) | Exact retrieval and citation scores with edge-case checks | 09C canonical resolution |
| [09E — Grounding judge](09e_implement_grounding_judge.md) | Reference-blind grounding prompt, implementation and checks | 09B–09D |
| [09E.1 — Cloud/decision comparison](09e1_compare_cloud_and_decision_judges.md) | Seven model/API conditions, cache/cost checks, offline integration and bounded local Dev3 | 09E outcomes, 09A.3 frozen panel |
| [09F — Adequacy judge](09f_implement_adequacy_judge.md) | Separate reference-aware adequacy prompt, implementation and checks | 09B, 09C; review shared interfaces after 09E |
| [09G — Challenge and freeze](09g_challenge_and_freeze_judges.md) | Results, bounded revisions and configuration freeze | 09A–09F |

Use the listed order as the default queue. Independent implementation can be
scoped later; dependencies do not require unnecessary new serial approvals once
execution is authorized. 09A–09D are complete. 09E completed the authorized 9B Dev3 comparison. The follow-on 09E.1 contract is
ready for a new implementation chat; 09F–09G remain unstarted.

## Outputs and boundaries

Keep schemas, prompts, configurations, small fixtures and code in Git; keep source
packets, generated answers, calls and reports under `ER_COMMONS_DATA_ROOT` in a
versioned Task 09 namespace. Each subtask publishes a compact checked-in result
pointer to its external artifacts and records its exact upstream bindings.
Share transport, persistence and citation-resolution utilities where useful;
keep semantic prompts, evidence visibility and results separate. No judge sees
Astra's proposed expectations, automatic scores, target identity or official
response content. Grounding also must not see references or gold evidence roles.

09B selects Inspect AI with a narrow native Ollama adapter, without containers
or judge tools. The user authorized comparison of Gemma 4 12B and Qwen3.5 9B,
starting at released 16-bit precision where feasible. Model substitutions require
an explicit recorded decision. See 09B for exact format/backend identities and
measured limitations. No ensemble or broad model sweep.

## Research / learning checkpoint

Use primary [Inspect grading](https://inspect.aisi.org.uk/model-graded.html),
[providers](https://inspect.aisi.org.uk/providers.html),
[Harbor task guidance](https://docs.harborframework.com/tasks/overview), and
[Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
to distinguish model serving, orchestration and project-specific scoring.
[Anthropic's evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
and the [judge notes](../../docs/llm_judge_learning_notes.md) inform challenge design;
our accepted rubric remains authoritative. Explain selected tradeoffs in outcomes.

## Review pass

Use bounded independent reviews for dev/test and judge information boundaries,
metric/rubric fidelity, and maintainable restartable implementation. Reconcile
findings, not just test failures. Avoid adding a new full human labeling pass.

## Validation and acceptance criteria

- Verify frozen release identity and exact development membership; no test answers
  enter synthesis, tuning, smoke qualification or challenge evaluation.
- Test separate packets, exact formulas, partial credit, abstention and failed-call
  behavior. Never report infrastructure failures as semantic zero scores.
- Save actual inputs/outputs, versions, model identity, attempts and coverage;
  validate reuse and interruption recovery. Inspect human readability of code.
- Run focused meaningful tests plus `make fix` and `make check` for implementation;
  docs-only changes require link/diff inspection and `git diff --check`.
- Freeze separate metric/judge configurations with known limits and results;
  report **uncalibrated automated judgments** unless separate human calibration
  actually occurs. No invented accuracy threshold or claim of general reliability.

## Non-goals

Reopening Task 08, reclustering/resplitting, test execution, retriever or target
implementation, agentic search, human calibration, framework building, model
training, automatic expansion of gold evidence, commits or pushes in this planning
request. Task 12 later checks actual target-output integration; Task 13 runs test.

## Outcome

[09A outcome](09a_create_synthetic_challenges.md#outcome) and
[sealed result](../../docs/specs/task09a_final_result.json): all 19 development
cases, 546 variants, 19 controls; 541 comparison-eligible variants split into 423
development and 118 reserved final checks. Five review exclusions and 43
inapplicable combinations remain explicit. Synthetic proposals are uncalibrated.
[09B outcome](09b_choose_harness_and_qualify_local_judge.md#outcome) and
[result](../../docs/specs/task09b_final_result.json) select Inspect/native Ollama
with Qwen F16 at 48K as the operational default and Gemma BF16 as an alternative.
Both prototypes showed semantic failures; no accurate judge is established.
[09C outcome](09c_build_judge_evidence_packets.md#outcome) and
[result](../../docs/specs/task09c_final_result.json) provide strict separate packets,
explicit unresolved citations and a 48K preflight adapter, verified with fixtures
and 12 bounded offline development packets. No judge calls occurred; exact
runtime token counting remains the consuming judge's responsibility.
[09D outcome](09d_implement_automatic_metrics.md#outcome) and
[result](../../docs/specs/task09d_final_result.json) provide exact automatic metrics,
offline Inspect integration and a canonical retrieval-receipt contract.
Task 10/12 must qualify production mappings and delivery. The refreshed
[09E plan](09e_implement_grounding_judge.md) fixes nested dev3/dev6 tuning panels,
small Qwen before larger Qwen, bounded revisions and user reflection checkpoints.
The subsequent 09E start authorizes Stage 0 and bounded small-Qwen Stages 1–2,
subject to exact preflight and an early blocker stop. The later user approval
authorized the now-completed [fixed-pipeline 9B Dev3 comparison](../../docs/specs/task09e_09a3_qwen9b_v1.md)
only. Stop for review before 9B Dev6 or full-19. 09F–09G still require contract
refresh before execution.
