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

## Active entry: Task 09A — synthetic development answers

Start with the [Task 09 umbrella](../tasks/sprint2/09_build_evaluation_and_qualify_judges.md)
and [09A contract](../tasks/sprint2/09a_create_synthetic_challenges.md).
Task plans are written; implementation and model execution have not started.
The current request is planning-only. Once 09A execution is authorized, prepare
and qualify intake/schema/prompt, then run restartable Astra generation across
all 19 development cases. No further Task 08 labeling or split work is needed.

Use only development cases for synthesis, prototypes, prompt changes and judge
qualification. Preserve the 30-case test set and Task 08 seals. Synthetic proposed
scores are not human labels. [Decision 006](decisions/006_structured_answers_four_part_evaluation.md)
continues to govern metrics, rubrics and separate judge information boundaries.

## Task 09 subqueue

| Task | Status | Deliverable |
| --- | --- | --- |
| [09A — Synthetic challenges](../tasks/sprint2/09a_create_synthetic_challenges.md) | Active entry; not executed | Broad applicable perturbations, exact edits, proposed G/A expectations, evidence and coverage |
| [09B — Harness/local inference](../tasks/sprint2/09b_choose_harness_and_qualify_local_judge.md) | Provisional | Runner decision, local candidate qualification and measured runtime |
| [09C — Evidence packets](../tasks/sprint2/09c_build_judge_evidence_packets.md) | Provisional | Separate validated grounding/adequacy inputs |
| [09D — Automatic metrics](../tasks/sprint2/09d_implement_automatic_metrics.md) | Provisional | Retrieval and citation scoring with explicit denominators |
| [09E — Grounding judge](../tasks/sprint2/09e_implement_grounding_judge.md) | Provisional | Independent reference-blind judge |
| [09F — Adequacy judge](../tasks/sprint2/09f_implement_adequacy_judge.md) | Provisional | Independent reference-aware judge |
| [09G — Challenge/freeze](../tasks/sprint2/09g_challenge_and_freeze_judges.md) | Provisional | Bounded revisions, comparison report and frozen configurations |

Refresh each provisional contract from preceding accepted outcomes before
activation. The intended synthesis kickoff is October 9; evaluation/judge work
is targeted for October 12–14. These are planning targets, not completed runs.

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
