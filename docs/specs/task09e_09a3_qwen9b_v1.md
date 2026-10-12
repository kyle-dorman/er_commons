# Task 09E — Qwen 9B on combined 09A.3 Dev3

Status: fixed-pipeline Dev3 comparison complete; user review required.

The user accepted the proposed next experiment: Qwen3.5 9B F16 on exactly the same
69 eligible Dev3 answers (C041/C037/C014) as the completed small-model run.
Reuse its frozen 09A.3 manifest, packets and separate proposed expectations. Keep
answer_abstention.v1, point_support.v2, conclusion_review.v1, response schemas,
49,152-token context, 3,000-token output allowance, deterministic request settings,
and staged routing unchanged. Only the model identity and its native renderer /
tokenizer binding change. Record inherited model parameters explicitly.

Use the locally pinned 09B compatibility-converted F16 model and current verified
Ollama build. Check exact model-specific preflight before every native dispatch;
unavailable local assets block inference without downloads or model substitution.
Inspect owns execution, samples, logs and aggregation through the existing
interfaces. Save a fresh external namespace `task_09/09e_20261011_09a3_qwen9b_v1/`.
Do not modify earlier namespaces. No new answer generation or labels are needed.

Compare stage coverage, supported/unsupported confusion, abstention false exemptions
and missed refusals, conclusion outcomes, output validity, numeric distributions,
latency and token use. Compare identical point inputs where both models reached
that stage; changed gate routing can change which points are attempted. Conclusion
inputs include each model's own predictions and therefore can differ by design.
Agreement remains diagnostic against proposed expectations, not calibrated accuracy.
Independent review checks runtime identity, input isolation, paired comparison and
representative source-linked disagreements. Do not relax validation for this run.

Stop after Dev3 for user review, or earlier for an operational/integrity blocker.
No prompt revision, 9B Dev6, full-19, reserved/test use, 09F–09G, Task 10, commits or
pushes are authorized by this experiment. Preserve the original 19/30 question
split, 423 development variants, 118 reserved checks and five exclusions, alongside
the separate combined-publication counts of 442 answers / 430 eligible / 12 exclusions.

## Outcome

The authorized Dev3 comparison is complete; stop for user review. Qwen 9B shows
substantial stage-level improvement, but is not a qualified judge. It recognizes
supported claims and varied abstentions more often. End-to-end score coverage
remains very low because many evidence excerpts fail literal-source validation.

| Diagnostic on the same frozen Dev3 answers | Qwen 0.8B | Qwen 9B |
| --- | ---: | ---: |
| Answers attempted | 69 | 69 |
| Clean abstentions recognized | 3/6 | 6/6 |
| Substantive answers falsely exempted | 7/63 | 1/63 |
| Ambiguous abstention decisions | 6 | 0 |
| Valid point predictions / eligible points | 72/166 | 93/166 |
| Point predictions matching proposals | 16/72 | 62/93 |
| Proposed-supported points accepted / rejected among valid predictions | 0 / 56 | 41 / 29 |
| Proposed-unsupported points accepted / rejected among valid predictions | 0 / 16 | 2 / 21 |
| Valid conclusion predictions / eligible conclusions | 12/63 | 12/63 |
| Conclusion predictions matching proposals | 1/12 | 7/12 |
| Numeric answer scores | 11 | 12 |
| Numeric scores matching proposals | 0/11 | 6/12 |
| Score distribution: 0 / 1 / 2 | 11 / 0 / 0 | 7 / 3 / 2 |
| Answer output failures | 41 | 50 |
| Unresolved point/conclusion disagreement | 1 | 0 |
| Native calls | 229 | 255 |
| Recorded evaluation seconds | 1,254.01 | 10,528.90 |

These conditional agreement fractions are diagnostics against proposed synthetic
expectations, not calibrated accuracy. Coverage and stage populations differ.
Both runs attempted 145 identical point inputs; 72 small-model outputs and 81
9B outputs validated on that shared set. The 9B run attempted another 20 points
because its gate routed more substantive answers to grounding. Among 45 points
with valid outputs in both runs, 18 changes moved toward proposals and two moved
away (25 unchanged); agreement on that selected subset rose from 9/45 to 27/45.
Conclusions use
each model's own preceding point predictions, so their complete inputs can differ.

For 9B, C041 produced 2 numeric scores from 22 answers, C037 produced 10 from 27,
and C014 produced none from 20. Its remaining outcomes were seven N/A (six genuine,
one false exemption) and 50 schema failures. Across all stages, 79 failures were
nonliteral source excerpts, one was a nonliteral unsupported-assertion span, and
one hit the 3,000-token output limit. A sample with both schema and length failures
is classified as schema failure; this explains the absence of a separate final
answer output-limit count. Invalid judgments remain excluded, not converted to
unsupported predictions. Output coverage is a serious remaining limitation.

## Source-linked review

Independent reviews are saved under the experiment's `dev3/` directory:

- `first_score_review.json`: C041-O03 now receives 2 instead of 0. The source
  (`deir_main/sec000992`) supports the stated spay/neuter requirement; the small
  model penalized unasserted missing enforcement detail.
- `c037_followup_review.json`: C037-F03 correctly separates supported points from
  an unsupported uninterrupted-function guarantee. C037-F05 nevertheless accepts
  a change from source “may/could” to target “will,” including during the conclusion-stage point recheck.
- `first_supported_review.json`: C041-F05 similarly accepts trapping “will be
  necessary” where the source says “may be necessary.” Its valid quotation does
  not make the support judgment correct.
- `early_source_review.json`: C041-C01 still imports residential HOA/lease
  enforcement into a separate construction-worker ban. Two other raw judgments
  improve but remain invalid because excerpts contain inserted ellipses.
- `c014_source_review.json`: C014-C01 recognizes some project/scenario support,
  but rewrites excerpts and misreads one table's year grouping. None of its three
  point outputs validates; raw reasoning is not counted as an accepted result.
- `final_abstention_review.json`: C014-R02 asserts that the documents omit both
  developments. Both models wrongly exempt these substantive document-content
  claims as clean abstention. All six actual clean abstentions are recognized by 9B.
- `mixed_support_review.json`: C037-C05 improves from 0 to the proposed 1. The
  cited point is defective while the conclusion has independent support. This
  follows the accepted staged rule: supported conclusion plus any unsupported
  point yields 1, including when that is the only listed point.

## Execution and implementation

The only runtime code change extends the exact-counter allowlist from one pinned
model identity to two exact alias/digest/blob tuples. Cross-model combinations
still fail closed. Eleven added tests cover the 9B identity and mismatch rejection;
all prompts, schemas, stage routing and inference settings remain frozen.

Used the already-local compatibility-converted Qwen3.5 9B F16 blob through an
isolated alias, with Ollama 0.40.2, 49,152 context, 3,000 output tokens,
temperature 0 and seed 42. Inherited parameters match the small model:
presence penalty 1.5, top-k 20 and top-p 0.95. Render-only qualification made
no invented generation. No download or additional model was used.

Inspect owns all 255 calls, sample records and aggregation. All 255 exact request
counts match native input receipts. Independent audits verify label-free model
inputs, unchanged 69 answers/proposals, unchanged prompts and non-model settings,
all 12 implementation bindings, and all 16,460 files in the preserved small-model
completion inventory. Runtime processes are stopped. No retries, context blocks
or transport failures occurred. Native use was 1,206,901 input and 83,553 output
tokens. The preserved lineage totals 856 generations (601 earlier + 255 here).

A timing audit of the first 36 stages found roughly 17.7 seconds per stage outside
native inference, mainly in model-identity checks. The counter hashes the full
18.4 GB model twice per request. Logical reads may be cached; these are not measured
physical disk reads. Identity verification is a separate future optimization
opportunity and was not changed during this comparison.

## Learning and review checkpoint

A stronger model improves semantic discrimination under identical point inputs,
but does not resolve exact quotation, modality, table-reading or abstention-scope
errors. Better gate routing also exposes more downstream failures; raw failure
counts alone do not measure whether the gate improved. Numeric-score agreement on
12 selected surviving answers cannot establish overall judge reliability.

The next review should decide how to address evidence-excerpt failures before
expanding the panel, while preserving strict provenance and separately testing
modality errors. No additional experiment is authorized by this outcome. The
[central pointer](task09e_final_result.json) binds this run and preserves earlier
results. Stop before 9B Dev6, full-19, revisions or later tasks.

## Validation

98 focused tests passed. `make fix` passed with 965 files unchanged. `make check`
passed formatting, lint and types, then reported 3,923 passed, one skipped and
only the three historical Task 06G failures. `git diff --check` passed. Independent
result and integrity reviews found no execution or accounting blocker; semantic
limitations remain as documented above. No commits or pushes were made.
