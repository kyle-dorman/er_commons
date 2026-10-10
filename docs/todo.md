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
integration tests. Task 10 must qualify actual retrieval mappings and delivery
receipts; fixture receipts are not baseline results. The bounded code-quality
pass strengthens validation and supports distinct saved variants of one case;
see the outcome for verification and accepted closeout.

**No task is active.** Refresh provisional 09E from the completed 09B–09D
interfaces before a separately authorized start. 09E–09G and Task 10 remain
unstarted. [Decision 006](decisions/006_structured_answers_four_part_evaluation.md)
continues to govern separate judge visibility and the four evaluation results.

## Task 09 subqueue

| Task | Status | Deliverable |
| --- | --- | --- |
| [09A — Synthetic challenges](../tasks/sprint2/09a_create_synthetic_challenges.md) | Complete with limitations | Broad applicable perturbations, exact edits, proposed G/A expectations, evidence and coverage |
| [09B — Harness/local inference](../tasks/sprint2/09b_choose_harness_and_qualify_local_judge.md) | Complete with limitations | Inspect/Ollama integration, candidate qualification and measured runtime |
| [09C — Evidence packets](../tasks/sprint2/09c_build_judge_evidence_packets.md) | Complete with limitations | Separate validated inputs and explicit context diagnostics |
| [09D — Automatic metrics](../tasks/sprint2/09d_implement_automatic_metrics.md) | Complete with limitations | Inspect metrics, canonical identities and Task 10 receipt interface |
| [09E — Grounding judge](../tasks/sprint2/09e_implement_grounding_judge.md) | Provisional | Independent reference-blind judge |
| [09F — Adequacy judge](../tasks/sprint2/09f_implement_adequacy_judge.md) | Provisional | Independent reference-aware judge |
| [09G — Challenge/freeze](../tasks/sprint2/09g_challenge_and_freeze_judges.md) | Provisional | Bounded revisions, comparison report and frozen configurations |

Refresh each provisional contract from preceding accepted outcomes before
activation. Synthesis is complete; evaluation/judge work
is targeted for October 12–14. These remain planning targets.

## Remaining queue

| Task | Scope and finish line |
| --- | --- |
| **09 — Evaluation and synthetic judge qualification** | Astra development challenges first; then automatic metrics, separate grounding/adequacy calls, bounded disagreement analysis and prompt revisions, frozen judge configuration and known limitations. Target completion October 14. |
| **10 — BM25 retrieval and evidence presentation** | Freeze question-only search and the top five full sections/tables, source labels and heading paths, length handling, and development recall. No model selection of results or generated section summaries. |
| **11 — Target generation** | One frozen zero-shot target baseline, structured citations/abstention, output-length and stability checks. Three-day working timebox. |
| **12 — Integration check** | Exercise the existing evaluator/judge on real development target outputs, verify the complete artifact/configuration chain, and confirm the final freeze. Keep this small; substantive fixes must be explicit and rechecked on development data. |
| **13 — Locked test and results** | Run the primary baseline followed by the evidence-only oracle; report four separate results, stage-level errors, limitations and the next-project decision. |

Agentic search is a later, separately scoped condition. No new full labeling pass
is required, and no held-out test results may be used to tune the pipeline.
