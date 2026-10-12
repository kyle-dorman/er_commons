# Task 09E — Point prompt scope revision

Status: experiment complete, October 11, 2026; user review pending.

## Hypothesis

The v1 point judge rejected evidence-supported points for not fully answering the
question and demanded assertions the point never made. V2 leads with target-only
support, limits question use to disambiguation, and gives invented examples of
omitted detail, equivalent wording and an unsupported added detail. It distinguishes
semantic support from mandatory literal copying in output spans, then asks for a
brief rejection check. The response schema and point/evidence inputs are unchanged.

The [DeepSearchQA starter notebook](https://www.kaggle.com/code/andrewmingwang/deepsearchqa-starter-code)
illustrates a narrow decision process, semantic matching and deterministic
aggregation. Its reference-based completeness rubric is not adopted. Its Gemini
judge provides no evidence that these changes will fix our small model.

## Controlled comparison

Use precisely the prior 36 non-conclusion point inputs from the unchanged twelve
Dev3 answers (C041/C037/C014). Compare with `09e_20261011_staged_v1` point records.
Retain Qwen3.5 0.8B F16, 49,152 context, 3,000 output allowance, schemas and exact
local request preflight. The prompt/version is the only changed model input.

Inspect owns execution, sample records, logs and aggregation. A minimal points-only
mode skips all abstention/conclusion calls, including two zero-point answers.
It reports point verdicts only when validated; malformed outputs are failures,
not unsupported findings. Raw parseable flags may be reported separately for
diagnosis. No final answer score or synthetic accuracy is produced.

Fresh namespace: `task_09/09e_20261011_point_scope_v2/`. Preserve prior evidence and
freeze source/prompt/settings before inference. No downloads, regenerated answers,
new labels, reserved/test reads, Dev6, 9B, full19, later-task work, commits or pushes.
One bounded operational retry is permitted; no semantic retries. Unavailable exact
counting blocks dispatch. Stop after this prompt cycle for review.

Compare validation failures, supported/unsupported verdicts, completeness objections
in matched controls, and whether genuine unsupported assertions remain rejected.
Source review is diagnostic, not a new ground-truth dataset. Independent review,
focused tests, make fix/check and git diff --check precede completion.

## Result

Rejections did not decrease. V1 produced 35 parseable false flags and one truncated
output; v2 produced 36 false flags. Among validated outputs, v1 had zero supported
and fifteen unsupported; v2 had zero supported and seventeen unsupported. Validation
failures changed from twenty schema errors plus one output limit to nineteen schema
errors and no output limits. These are validity improvements, not semantic accuracy.

All 36 point payloads, schemas and settings matched v1; only the prompt/version
changed. All 36 exact preflight/native input counts matched. Inspect retained twelve
answer records (two with no non-conclusion points), with ten attempted answers and
36 native calls, no retries and no abstention/conclusion calls. Usage was 193,782
input and 13,673 output tokens over 218.03 seconds of sample execution.

Independent source review found local changes in objections, not reliable correction.
C041 P2 no longer cites completeness, but rejects a supported authority paraphrase.
C041 P5 still demands unasserted enforcement details. C037 P3 drops a completeness
objection but misreads conditional support; C037 P6 now explicitly admits evidence
support and rejects the point for not answering the broader question. C037 P4/P5
substitute the question's avoidance premise for the actual target assertion.
The unchanged source-linked defects remain available in the preserved result audit.

Keep this as a negative prompt experiment. Do not infer accuracy from all-false
predictions or from structurally valid responses. Stop for review before choosing
another prompt, changing inputs/schema, or transitioning to a larger model.
