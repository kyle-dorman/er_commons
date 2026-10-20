# Project TODO

## Sprint status

Tasks 02–08 are closed, including the approved benchmark release. The
[current inventory](specs/task07a1_final_result.json), repaired 06H handoff, and
[sealed pilot](specs/task07e_final_result.json) remain preserved. See the
[index](index.md) for upstream routes.

## Task 08 — complete

The [frozen release](specs/task08h_final_result.json) contains all **49 approved
cases: 19 development and 30 test**, with no pending Task 08 decisions. The
[08G outcome](specs/task08g_topic_review_result.json) preserves topic balancing
and accepted cross-split evidence overlap. [08H](../tasks/sprint2/08h_serialize_and_freeze_benchmark.md)
owns release validation, role separation, accounting and source limitations.
All prior artifacts remain preserved.

## Task 09A.2 — complete with limitations

[09A.3](../tasks/sprint2/09a3_add_clean_abstentions.md) is complete:
[the combined publication](specs/task09a3_final_result.json) adds 23 varied clean
abstentions, reaching two per development question (38 total). All 419 original
records remain unchanged; the combined set has 442 answers / 430 eligible.
Use this additive version for subsequent development experiments; the bounded 09E rerun is complete.

[09A.2](../tasks/sprint2/09a2_regenerate_point_expectations.md) published fresh
answers and jointly authored point/conclusion expectations for all 19 development
cases. The [new result](specs/task09a2_final_result.json) contains 419 variants,
407 eligible for comparison, twelve review exclusions and four inapplicable slots.
Review the proposed expectations and exclusions before downstream judge use.
Prior artifacts and reserved/test boundaries remain unchanged. No judge ran.

## Task 09B — complete with limitations

[09A](../tasks/sprint2/09a_create_synthetic_challenges.md) sealed 546 variants:
423 development, 118 reserved final checks and five exclusions, plus unchanged
controls. Preserve those partitions and the frozen 19-development/30-test split.

[09B outcome](../tasks/sprint2/09b_choose_harness_and_qualify_local_judge.md) and
[result](specs/task09b_final_result.json) select Inspect with native local Ollama.
Qwen 9B F16 at 48K is selected for the first accuracy evaluation; Qwen 0.8B
is for fast live integration checks only. Gemma and Nemotron remain tested
alternatives; Ornith is set aside. All tested models exhibited semantic failures
and are not accepted judges. See the outcome for measurements and limitations.

## Task 09C — complete with limitations

[09C outcome](../tasks/sprint2/09c_build_judge_evidence_packets.md) and
[result](specs/task09c_final_result.json) provide deterministic separate judge
packets, explicit unresolved citations, strict model-input boundaries and a
48K/output-reserve preflight. Twelve offline development packets passed exact
source-content checks; no inference ran. Final request counts remain
`context_unverified` until the consuming judge supplies an exact runtime counter.

## Task 09D — closed with limitations

[09D outcome](../tasks/sprint2/09d_implement_automatic_metrics.md) and
[result](specs/task09d_final_result.json) provide exact automatic metrics through
Inspect with canonical identity matching, explicit eligible counts and offline
integration tests. Task 10 now prepares evidence-only source mappings under Decision 007;
retrieval qualification is deferred. Fixture receipts are not baseline results. The bounded code-quality
pass strengthens validation and supports distinct saved variants of one case;
see the outcome for verification and accepted closeout.

## Task 09 — complete with limitations

The [09G freeze](specs/task09g_judge_freeze_v1.json) binds selected Luna A/G/C and
Haiku S to the committed native Inspect implementation and completed comparison
and cleanup evidence. Fireworks/GLM and Ollama remain alternatives. Earlier 09E
selections and runtimes are historical. No further judge-development run is queued.

## Task 09 subqueue

**09A–09G are complete within their documented scopes.** 09G is a documentation-only
freeze; the original additional challenge requirement was superseded, not executed.
Task 10 input preparation is also complete. Task 11A–11D are complete; 11D selected no candidate after full fixed-six comparisons. Task 11C supplies evaluation for prompt cycles;
Task 12 finalizes reporting before locked benchmark execution.

| Task | Status | Deliverable |
| --- | --- | --- |
| [09A — Synthetic challenges](../tasks/sprint2/09a_create_synthetic_challenges.md) | Complete with limitations | Broad applicable perturbations, exact edits, proposed G/A expectations, evidence and coverage |
| [09A.2 — Development regeneration](../tasks/sprint2/09a2_regenerate_point_expectations.md) | Complete with limitations | Fresh answers with point/conclusion support, not-supported flags and inherited development boundaries |
| [09A.3 — Abstention supplement](../tasks/sprint2/09a3_add_clean_abstentions.md) | Complete | Two varied clean abstentions per development question; original records unchanged |
| [09B — Harness/local inference](../tasks/sprint2/09b_choose_harness_and_qualify_local_judge.md) | Complete with limitations | Inspect/Ollama integration, candidate qualification and measured runtime |
| [09C — Evidence packets](../tasks/sprint2/09c_build_judge_evidence_packets.md) | Complete with limitations | Separate validated inputs and explicit context diagnostics |
| [09D — Automatic metrics](../tasks/sprint2/09d_implement_automatic_metrics.md) | Complete with limitations | Inspect metrics, canonical identities and Task 10 receipt interface |
| [09E — Grounding judge](../tasks/sprint2/09e_implement_grounding_judge.md) | Complete | Reference-blind grounding judge; accepted development results and limitations |
| [09E.1 — Cloud/decision comparison](../tasks/sprint2/09e1_compare_cloud_and_decision_judges.md) | Complete (historical) | Prior GLM selection and provider evidence; superseded by the 09G bundle |
| [09E.2 — Code cleanup](../tasks/sprint2/09e2_cleanup_grounding_judges.md) | Complete | Reusable cloud interfaces, retained local smoke paths, regression tests and independent review |
| [09F — Adequacy judge](../tasks/sprint2/09f_implement_adequacy_judge.md) | Complete with documented limitations | Luna C v8 / Haiku S v6; native cleanup complete |
| [09F.1 — No-answer and grounding judges](../tasks/sprint2/09f1_revisit_grounding_judge.md) | Complete with documented limitations | Luna A v2 / G v3; full comparisons, handoffs and native cleanup complete |
| [09G — Documentation freeze](../tasks/sprint2/09g_challenge_and_freeze_judges.md) | Complete with limitations | Committed source/configuration and existing evidence bound; no reruns |

Refresh downstream provisional contracts from the 09G freeze and accepted upstream
outcomes before activation. The former October 12–14 targets are historical.

## Task 10 — complete

[Evidence-only preparation](../tasks/sprint2/10_prepare_evidence_only_inputs.md)
publishes all 49 cases in separate 19-development/30-test files. The
[result pointer](specs/task10_final_result.json) owns exact identities and validation.
All 232 approved occurrences are retained in 208 passage views over 207 case-level
canonical units. No inference or scoring ran. Task 11A panels are fixed and 11B–11D are complete; any further prompt work needs a new bounded task. All Task 11
generation/evaluation uses development only.

## Task 11 — closed; Task 12 next

Task 11 is fully closed, including code cleanup and the
[internal intervention findings](../tasks/sprint2/11_prompt_iteration_findings.md).
No further Task 11 work or runs are pending.

[Luna generation umbrella](../tasks/sprint2/11_build_and_freeze_target_generation.md):
select three questions, expand to a fixed nested six for prompt iteration, then
check a frozen candidate on all 19 development questions. Automatic checks and
frozen judges are integrated before cycling prompts. [11A panels and criteria](specs/task11a_panel_protocol.md)
are complete. [11B](../tasks/sprint2/11b_build_luna_generation.md) completed its
bounded three-case smoke with valid candidates and preserved receipts; see the
[result and limitations](specs/task11b_final_result.json). [11C](../tasks/sprint2/11c_integrate_development_evaluation.md) completed saved-candidate
evaluation and no-call replay. Its [result](specs/task11c_final_result.json) retains
C017's C failure and C019's S failure. [11C.1 cleanup](../tasks/sprint2/11c1_cleanup_development_evaluation.md) is complete,
with exact offline replay preserved. [11D](../tasks/sprint2/11d_iterate_development_prompt.md) is complete after its authorized
100K continuation. Both six-case arms have complete evaluation, but V4's new
material defect blocks promotion and V3 retains failures. The
[result](specs/task11d_resume_100k_result.json) preserves the no-selection decision.
[11D.1 public-rubric comparisons](../tasks/sprint2/11d1_public_rubric_prompt_comparisons.md) are complete; examples improved observed scores, but no prompt met repeat promotion criteria. See the [result](specs/task11d1_final_result.json). [11D.2](../tasks/sprint2/11d2_resolve_evaluation_contract.md) retains V6b and has implemented the offline specification and metadata corrections. The detailed C014 proposal was rejected as too revealing for search. [11D.3](../tasks/sprint2/11d3_test_light_question_wording.md) completed the lighter-wording experiment without demonstrated improvement. Keep the original publication and V6b. [11D.4](../tasks/sprint2/11d4_compare_alternative_models.md) completed Haiku/GLM comparisons without expanding Luna’s five-of-six coverage; see the [result](specs/task11d4_result.json). [11D.5](../tasks/sprint2/11d5_raise_haiku_output_cap.md) completed the tripled-output comparison: truncation resolved, no added frozen-score coverage; see [results](specs/task11d5_result.json). Stronger models remain deferred. The completed 11E outcome owns the all-19 check.

| Subtask | Status |
| --- | --- |
| [11A — Panels and criteria](../tasks/sprint2/11a_select_development_panels.md) | Complete; [fixed panel manifest](specs/task11a_development_panels_v1.json) |
| [11B — Luna runner](../tasks/sprint2/11b_build_luna_generation.md) | Complete with documented limitations; [result](specs/task11b_final_result.json) |
| [11C — Evaluation integration](../tasks/sprint2/11c_integrate_development_evaluation.md) | Complete with documented limitations; [result](specs/task11c_final_result.json) |
| [11D — Prompt cycles](../tasks/sprint2/11d_iterate_development_prompt.md) | Complete; no selection after full fixed-six comparisons |
| [11D.1 — Public rubric and examples](../tasks/sprint2/11d1_public_rubric_prompt_comparisons.md) | Complete; no selection after three paired prompt comparisons |
| [11D.2 — Evaluation contract corrections](../tasks/sprint2/11d2_resolve_evaluation_contract.md) | Offline corrections ready; detailed question rejected |
| [11D.3 — Light question comparison](../tasks/sprint2/11d3_test_light_question_wording.md) | Complete; no demonstrated improvement; original publication retained |
| [11D.4 — Alternative-model coverage](../tasks/sprint2/11d4_compare_alternative_models.md) | Complete; no additional question coverage; no selection |
| [11D.5 — Haiku output allowance](../tasks/sprint2/11d5_raise_haiku_output_cap.md) | Complete; truncation resolved; no selection |
| [11D.6 — Context and qualifications](../tasks/sprint2/11d6_simplify_context_and_qualifications.md) | Complete offline; [result](specs/task11d6_result.json); no live evaluation |
| [11E — Freeze and all-19 check](../tasks/sprint2/11e_freeze_development_baseline.md) | Complete with limitations;114/114 evaluated |

Next: Task 12 builds tables/charts and freezes reporting using the sealed [11E handoff](../tasks/sprint2/11e_freeze_development_baseline.md). No further calls or locked-test run are active.

[Task 11F maintenance](../tasks/sprint2/11f_cleanup_target_generation.md) is complete: shared attempt handling, clearer projection stages and stronger failure receipts; offline checks passed. Task 12 planning is refreshed; implementation is not active.

## Remaining queue

| Task | Scope and finish line |
| --- | --- |
| **[12 — Tables, charts and reporting](../tasks/sprint2/12_integrate_evaluation_and_reporting.md)** | Next, not active. Both models, three-repeat component/joint/any/every results, automatic citation metrics, historical judge-label agreement and Luna complexity plots; freeze reporting. |
| **[13 — Locked evaluation](../tasks/sprint2/13_run_locked_test.md)** | Provisional. Both models × 30 questions × three repeats; sealed results using Task 12 reports. |
| **[14 — Selective failure review](../tasks/sprint2/14_selective_failure_review.md)** | Provisional, after 13. Small selection of failures, successes and evaluator disagreements; reuse prior reviews. |
| **[15 — Short methods/results writeup](../tasks/sprint2/15_write_methods_and_results.md)** | Provisional. Dataset construction/coverage, methods, results and selected limitations; short mini-paper-style report. |

Agentic search is a later, separately scoped condition. No new full labeling pass
is required, and no held-out test results may be used to tune the pipeline.

[11D.7](../tasks/sprint2/11d7_citation_clause_check.md) preserves the V9/V10 prompt preparation; its additions were evaluated in 11D.8 and isolated in 11D.9.

[11D.8 V10 Luna/Haiku comparison](../tasks/sprint2/11d8_compare_v10_luna_haiku.md) is complete: all 24 answers valid and fully evaluated; Luna 5/12 and Haiku 3/12 all-checks passes. [Results](specs/task11d8_result.json); no baseline selected.

Current: [Task 11E](../tasks/sprint2/11e_freeze_development_baseline.md) is complete with limitations: all 114 planned development answers evaluated. Luna passed all checks on 29/57; Haiku on 6/57. The additional 13 are weaker than the original six. [Results](specs/task11e_result.json) and the [frozen configuration](specs/task11e_frozen_generation_v1.json) form the Task 12 reporting/readiness handoff. No further run is active and locked-test readiness is not established.
