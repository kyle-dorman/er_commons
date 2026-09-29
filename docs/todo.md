# Project TODO

## Sprint status

Tasks 02–06 and [Task 07A.1](../tasks/sprint2/07a1_repair_response_list_links.md)
are complete. The [accepted replacement inventory](specs/task07a1_final_result.json)
is the current input; historical releases and inherited limitations are preserved.
See the [index](index.md) for entry links.

## Next: finalize Task 07G pilot assessment

[Combined 07E](../tasks/sprint2/07e_review_answer_logic.md#final-outcome-and-six-case-handoff)
is closed: six approved answers, preserved chat histories, 31 unchanged claims
and 84 reviewed citations. The [sealed result](specs/task07e_final_result.json)
retains inherited warnings and source limits. Separate 07F is superseded.

[07G](../tasks/sprint2/07g_assess_pilot_and_local_replay.md) remains provisional.
Revise its assessment and bounded local-proposal comparison contract using the
07E handoff and MVP lessons before execution. No local replay, target run, judge
run or benchmark eligibility decision has started. The [authoring prompt](prompts/task07e_reference_answer_authoring_v2.md)
records the current rebuttal and chat-review approach.

For the next authoring pass, each comment yields at most one faithful focused
question. Rewrite only when straightforward; otherwise skip rather than split or
salvage. Retrieval, target and judge use the same frozen question. Preserve the
sealed six-case MVP and all 31 claims; do not silently migrate its question scopes.

The [updated benchmark plan](sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
now specifies automatic retrieval recall and final-citation precision/recall/F1,
plus two judged dimensions: grounded correctness and answer adequacy. Optional
context citations are neutral; exact formulas and staged judge access live there.
The outline-dependent A+B oracle is deferred to avoid reference-answer leakage.

07D remains complete, including the
[maintainability gate](specs/task07d_code_quality_result.json),
[sealed export](specs/task07d_final_result.json), and accepted MVP warnings.
I-EA-2 and I-CJ-4 remain excluded. Use the [maintainer guide](task07d_maintainer_guide.md)
for replay and the [07C.1 takeaway](../tasks/sprint2/07c1_review_claims_and_relevance.md#takeaway-from-downstream-evidence-review-2026-09-28)
for clearer, more selective future claim authoring.
