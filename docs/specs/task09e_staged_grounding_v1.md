# Task 09E — Point checks followed by conclusion review

Status: implemented and tested on Dev3, October 11, 2026; user review pending. This is a new
pipeline/prompt version, not a one-variable continuation of the single-call judge.
Use the same frozen Dev3 answers and existing small-Qwen runtime; stop for review.

## Purpose and inputs

Grounding asks whether the answer's substantive assertions are established by its
actual cited evidence. The question supplies context, not assertions to be graded.
Adequacy, reference answers, expected scores and automatic metrics remain excluded.
Do not rewrite, atomize, relabel or regenerate saved answers. A point may contain
several assertions, may combine sources and may reuse sources cited by other points.
No independent point-level truth labels exist; all stage decisions are predictions.

## Stage 1: one binary check per non-conclusion point

Run one call for each nonempty supporting point, qualification and optional-context
point. Pass the question, original point text/ID/citations and all full evidence
cited by that point. Explicitly linked qualifications or their target points remain labeled context;
only the selected point is scored and only its citations can supply locators.
Do not include other point predictions or hidden metadata.
The conclusion itself is checked in Stage 2, avoiding a redundant separate call.

A pass means every substantive assertion in the point is supported and appropriately
qualified. A fail must identify at least one specific unsupported/contradicted
assertion as an exact span of the point's text, with a concise explanation. Preserve
the entire point, including supported assertions; never strip failed content.
Return a binary supported flag, issue spans, source locators and explanation.
Multiple source locators are allowed, with literal source excerpts. Exact source
matching checks linkage, not entailment. Missing evidence cannot establish support.

## Stage 2: review the conclusion and earlier predictions

Pass the original full question/answer/cited-evidence payload and the validated
Stage 1 predictions. The predictions are explicitly fallible data, not instructions
or ground truth. Review every prediction against the source and return an ordered
binary review per point, plus a binary conclusion-supported decision and rationale.

The conclusion passes only if supported evidence establishes it without depending
on unsupported assertions. Do not assume that logical consistency with unsupported
points establishes evidence support. Preserve all original text and issue spans;
this stage must distinguish supported content within a partly unsupported point.
A clean abstention without substantive assertions is a separate N/A classification.
An abstention flag alone cannot exempt factual assertions or additional points.

## Deterministic final result

First require complete, valid stages. A malformed response, invalid source locator,
context overflow or runtime failure is an evaluation failure, never binary fail.
If any point call fails validation, retain all point records and skip the conclusion
call; do not feed absent/unvalidated predictions to it. No retry for semantic errors.

If any conclusion-stage point verdict disagrees with its Stage 1 verdict, preserve
both and return `unresolved_disagreement`, score null. Do not override, vote or
rerun for agreement. This first experiment detects binary verdict disagreement;
unchanged flags can still hide differing rationales and require source review.

With valid, agreeing stages:

| Conclusion supported | Every point supported | Final score |
| --- | --- | --- |
| No | Either | 0 |
| Yes | No | 1 |
| Yes | Yes | 2 |

Clean abstention is N/A. An answer with no non-conclusion points still gets the
conclusion check; an evidence-supported substantive conclusion may score 2.
There is no fraction-of-points rule, averaging, or automatic all-points-failed zero.
This avoids changing scores merely by regrouping claims, though model judgments
can still vary with presentation. Explicit central/secondary labels are unnecessary.

## Execution, provenance and validation

Inspect owns sample execution, saved results, stage receipts and aggregation.
Reuse native transport and exact request-token preflight for every individual call,
including the final conclusion request with its actual point predictions. Keep
49,152 context and a 3,000 output allowance, without truncation or summarization.
Unavailable exact counting blocks dispatch; no downloads or model substitution.
Use the existing 0.8B F16 identity and frozen 12-answer Dev3 panel. No Dev6, 9B,
full-19, reserved/test use, target generation, later tasks, commits or pushes.

Fresh experiment directories preserve previous evidence. Save each request, schema,
prompt/version, raw response, validated decision, native usage and exact preflight;
bind the frozen sample and settings on each answer record. This implementation
uses fresh runs, not automatic reuse of prior staged results. One transient retry
per stage is permitted, with every attempt recorded; Inspect automatic retries stay
disabled. Serial execution keeps the small-model run bounded and inspectable.

Offline tests must exercise narrow input projection, metadata/reference isolation,
compound claims, multiple/reused sources, exact issue/source spans, unknown or
missing IDs, agreement/disagreement, clean/substantive abstention, conclusion-only
answers, context/token mismatch and failure propagation. Actual offline Inspect
fixtures precede live fixtures and the bounded panel. Run focused tests, make fix,
make check and diff checks; distinguish the three historical Task 06G failures.
Independently review implementation and source-linked results before reporting.

Report attempted/skipped point and conclusion calls, validation/runtime failures,
unresolved disagreements, numeric/N/A results, token cost and source-linked examples.
Synthetic whole-answer agreement remains diagnostic; report eligible denominators
and do not treat the new decomposition as calibrated accuracy or independent labels.
Compare the prior pipeline's operational and semantic failures on the same answers,
while acknowledging that prompts, call structure and rubric representation changed.

## Why this shape

[Inspect custom scorers](https://inspect.aisi.org.uk/scorers.html) support dedicated
rubrics and metrics; a thin scorer can own bounded sequential calls without adding
a workflow engine. [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
provide parseable output constraints, while independent application validation
checks point/source identities and result consistency. Neither package certifies
semantic correctness. Narrow point calls reduce competing instructions and evidence,
but repeat shared evidence and can lose cross-point context. The final full-answer
review restores that context and exposes disagreements instead of hiding them.


## Maintained entrypoint

`make evaluate-staged-grounding-panel` accepts the same `GROUNDING_MANIFEST`,
`GROUNDING_PANEL`, `GROUNDING_SETTINGS`, `GROUNDING_COUNTER_CONFIG` and
`GROUNDING_OUTPUT` variables as the original command. It selects `--pipeline staged`;
the default `single` mode and its historical prompt/schema remain available.
The service must already be loaded and qualified. Neither command starts a service,
downloads assets or discovers benchmark partitions.


## First experiment checkpoint

The frozen 12-answer Dev3 run made 36 point calls and three conclusion calls.
Nine conclusion calls were skipped because a point response failed validation.
Fifteen point outputs passed validation, all with unsupported predictions; source
review found multiple false rejections. The only accepted final result scored a
clean abstention zero instead of N/A. Eleven answers remained evaluation failures.
No valid benchmark chain containing point predictions reached a final score, so
live cross-stage disagreement behavior remains unassessed; offline fixtures verify
its unresolved handling. One invented supported chain completed with score 2.
See the [task outcome](../../tasks/sprint2/09e_implement_grounding_judge.md) and
[result pointer](task09e_final_result.json) for counts, sources and validation.
The implementation is an experimental evaluator, not an accepted accurate judge.
