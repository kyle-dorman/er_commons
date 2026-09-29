# Project TODO

## Sprint status

Tasks 02–06 and [Task 07A.1](../tasks/sprint2/07a1_repair_response_list_links.md)
are complete. The [accepted replacement inventory](specs/task07a1_final_result.json)
is the current input; historical releases and inherited limitations are preserved.
See the [index](index.md) for entry links.

## Next: finalize the combined 07E reference-answer prototype

[07E](../tasks/sprint2/07e_review_answer_logic.md) now combines reasoning and
reference-answer review in one human labeling pass; separate 07F is superseded.
No independently approved outline, mapping artifact or final prose-polishing
review is required. Finalize one case's question/input binding and proposed form
before execution; trial one task before expanding. No new labeling project or
judge run has started.

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
