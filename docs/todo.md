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
Task 10 input preparation is also complete. Task 11A–11C are complete; next refresh 11D. Task 11C supplies evaluation for prompt cycles;
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
canonical units. No inference or scoring ran. Task 11A panels are fixed and 11B/11C are complete; next refresh 11D. All Task 11
generation/evaluation uses development only.

## Task 11 — 11C complete; 11D next

[Luna generation umbrella](../tasks/sprint2/11_build_and_freeze_target_generation.md):
select three questions, expand to a fixed nested six for prompt iteration, then
check a frozen candidate on all 19 development questions. Automatic checks and
frozen judges are integrated before cycling prompts. [11A panels and criteria](specs/task11a_panel_protocol.md)
are complete. [11B](../tasks/sprint2/11b_build_luna_generation.md) completed its
bounded three-case smoke with valid candidates and preserved receipts; see the
[result and limitations](specs/task11b_final_result.json). [11C](../tasks/sprint2/11c_integrate_development_evaluation.md) completed saved-candidate
evaluation and no-call replay. Its [result](specs/task11c_final_result.json) retains
C017's C failure and C019's S failure. [11C.1 cleanup](../tasks/sprint2/11c1_cleanup_development_evaluation.md) is complete,
with exact offline replay preserved. Next: refresh 11D from these outcomes.
No prompt cycles or 11D work have begun.

| Subtask | Status |
| --- | --- |
| [11A — Panels and criteria](../tasks/sprint2/11a_select_development_panels.md) | Complete; [fixed panel manifest](specs/task11a_development_panels_v1.json) |
| [11B — Luna runner](../tasks/sprint2/11b_build_luna_generation.md) | Complete with documented limitations; [result](specs/task11b_final_result.json) |
| [11C — Evaluation integration](../tasks/sprint2/11c_integrate_development_evaluation.md) | Complete with documented limitations; [result](specs/task11c_final_result.json) |
| [11D — Prompt cycles](../tasks/sprint2/11d_iterate_development_prompt.md) | Provisional |
| [11E — Freeze and all-19 check](../tasks/sprint2/11e_freeze_development_baseline.md) | Provisional |

Refresh each provisional contract from its accepted predecessor before execution.

## Remaining queue

| Task | Scope and finish line |
| --- | --- |
| **11 — Target generation** | Luna evidence-only generation with 3→6 prompt cycles, integrated evaluation and a frozen all-19 development check. See 11A–11E above. |
| **[12 — Reporting and locked-test readiness](../tasks/sprint2/12_integrate_evaluation_and_reporting.md)** | Reuse 11C/11E; finalize aggregate reporting, denominators, strict joint results and locked-test readiness. |
| **13 — Locked test and results** | Run the frozen evidence-only baseline on the locked test set; report citation and semantic results, retrieval as not applicable, limitations and the next-project decision. |

Agentic search is a later, separately scoped condition. No new full labeling pass
is required, and no held-out test results may be used to tune the pipeline.
