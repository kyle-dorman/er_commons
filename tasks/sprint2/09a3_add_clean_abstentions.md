# Task 09A.3 — Add varied clean abstentions

Status: complete October 11, 2026; inherited limitations retained.

## Abstract and goal

Top up each of the 19 development questions to two clean abstentions. Keep the
15 existing clean abstentions and every other 09A.2 record unchanged; generate
only the 23 missing examples. This is an additive supplement, not regeneration.

## Inputs and outputs

Use the sealed 09A.2 publication and its approved development question packets.
Do not read reserved/test payloads or the historical 09A synthetic payloads.
Record the supplement under a new external `task_09/09a3_*` namespace. Publish
separate additions and a convenient combined view containing the exact original
JSONL bytes followed by additions. Preserve original IDs, expectations, edits,
eligibility decisions, reference/source bindings and prior reservation metadata.
New records have independent supplement IDs, never fabricated predecessor slots.

## Plan and learning checkpoint

Reuse the existing Astra transport, strict 09A.2 variant schema, stage validator,
edit recorder and checksum helpers. A small artifact-specific recording script
is sufficient; do not introduce another package workflow or change the existing
sealed-batch writer. Its complete source and invocation receipts belong beside
the additions. Immutable publication with an append-only combined view makes
the user's additions available while retaining the reproducible prior version.

Generate the answer and expectation together. Give Astra only development
questions, existing clean abstention texts and required new slot identities.
Vary concise refusal, explicit uncertainty, request for sufficient evidence and
careful question-specific wording. No substantive assertions about documents,
conditions, impacts or what the source does/does not establish. A statement of
the responder's inability is distinct from claiming that the source lacks data.
Clean abstention means no supporting/qualification/context points or citations,
G=N/A, A=0, conclusion_supported=null and not_supported=false. Preserve the
separate insufficient_evidence_response flag according to the actual wording.

## Validation and review

Check exact slot coverage, two clean abstentions per case, distinct wording within
each pair, schema/score consistency and no added substantive points. Review every
new answer independently for clean-abstention semantics and meaningful variation.
Bind raw inputs, schema, code, model invocation/output and review by checksum.
Permit two infrastructure retries and one corrective generation if needed;
preserve failed attempts and reuse only identical completed input/output units.
Verify original JSONL byte prefixes, all original IDs/records unchanged, unchanged
old publication seal, new addition IDs disjoint from all prior partitions, and
combined counts/eligibility. No judge calls or test/reserved content access.

## Acceptance and non-goals

All 19 cases have two comparison-eligible clean abstentions: 38 total. Expected
combined size is 442 answers, 430 comparison-eligible, with the existing twelve
exclusions unchanged. No previous variant is regenerated or relabeled. No judge
pipeline, reference changes, split changes, commits or pushes.

## Outcome

Published [the additive result](../../docs/specs/task09a3_final_result.json) under
`task_09/09a3_20261011_abstentions_v1`. One Astra generation attempt produced
23 new records, all independently reviewed and accepted without corrections.
There are now **38 clean abstentions, exactly two for each of 19 questions**,
inside 442 total answers / 430 comparison-eligible answers. The original 419
records, twelve exclusions, approved inputs and prior split metadata are intact.

Wording spans seven styles: refusal, personal uncertainty, evidence request,
deferred judgment, question-specific inability, concise non-answer and conditional
willingness. All new records have G=N/A, A=0 and `not_supported=false`; two also
explicitly state an information shortfall. Expectations remain separate from answers
and remain model proposals, not human-validated truth. No new labeling issues remain.

Eight recording checks, schema/stage consistency, all 23 semantic reviews,
exact original JSONL byte prefixes, unchanged original sealed inventories,
zero-model-call restart and the final publication seal all passed. The first
verification harness invocation omitted a required inventory argument; correcting
that invocation completed verification without changing generation or artifacts.
No judge pipeline ran; no reserved/test payloads were read; no commits or pushes.

`published/answers.jsonl`, `expectations.jsonl` and `edits.jsonl` are combined
views; `additions_*` contains only new records. `record_origins.jsonl` resolves
original relative provenance against its original root. Inherited coverage and
423 development slots still describe the base batch; `supplement_slots.jsonl`
records the 23 additions. This avoids rewriting historical records or inventing
predecessor slots. The full recording/publishing scripts, prompts, model receipts,
review and validation are sealed beside the publication.

Next: select the combined publication for a separately authorized development
experiment, preserve `comparison_eligible` filtering and the record-origin mapping.
Existing judge-run state is unchanged.
