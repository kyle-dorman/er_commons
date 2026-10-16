# Task 09F — Aligned scoring and three-model Dev6 comparison

The aligned prompt distinguishes a correct central conclusion with an essential omission or
materially defective explanation (1) from a wrong or misframed central answer (0).
Incidental defects do not automatically reduce an otherwise complete answer (2).
It uses the matching partial-credit validator and retains strict output validation.

All models received the same frozen 136 answers across six development question families,
twice each: 816 evaluation calls plus nine separate cache probes. Expectations remained
evaluator-only. No retries, label changes, dataset expansion or optional essentiality experiment.
This is development evidence; **no prompt or model is automatically promoted**.

## Accuracy and coverage

| Model/pass | Correct | Accuracy | Macro-F1 | Coverage | Controls correct | Abstentions correct |
| --- | --- | --- | --- | --- | --- | --- |
| GLM 1 | 110/136 | 80.88% | 0.7622 | 136/136 (100.00%) | 59/62 | 12/12 |
| GLM 2 | 112/136 | 82.35% | 0.7854 | 136/136 (100.00%) | 59/62 | 12/12 |
| Luna 1 | 116/136 | 85.29% | 0.8161 | 136/136 (100.00%) | 59/62 | 12/12 |
| Luna 2 | 115/136 | 84.56% | 0.8055 | 136/136 (100.00%) | 59/62 | 12/12 |
| Haiku 1 | 110/136 | 80.88% | 0.7688 | 136/136 (100.00%) | 58/62 | 12/12 |
| Haiku 2 | 106/136 | 77.94% | 0.7410 | 135/136 (99.26%) | 56/62 | 12/12 |

Luna had the highest accuracy in both passes, while GLM had the fewest repeat flips.
The aligned GLM prompt did not improve on the historical format-v2 results overall.
Haiku’s sole invalid output was C014 F05 in pass 2: an empty issue explanation failed
the nonblank-string contract despite native structured output. No repair or retry was applied.

Invalid outputs remain non-scores and count against the full accuracy/F1 denominator.
Synthetic-label agreement is not human calibration; variants within a question are correlated.

## Per-question failures

Counts include numeric disagreements and invalid outputs. Each model column is pass 1 / pass 2.

| Question | GLM | Luna | Haiku |
| --- | --- | --- | --- |
| C001 | 5 / 4 | 3 / 2 | 6 / 6 |
| C014 | 6 / 5 | 1 / 2 | 3 / 4 |
| C019 | 4 / 4 | 4 / 5 | 7 / 8 |
| C037 | 5 / 5 | 6 / 4 | 4 / 4 |
| C041 | 1 / 3 | 3 / 3 | 4 / 5 |
| C056 | 5 / 3 | 3 / 5 | 2 / 3 |

Detailed entries below use `category expected→predicted`; `invalid` means no numeric score.
Full sample identities, rationales and native receipt pointers are in the external report.

**GLM**

- C001 — pass 1: C04 0→1, F06 0→1, F07 1→2, F08 0→1, F10 0→1; pass 2: C04 0→2, F06 0→1, F08 0→1, F10 0→1.
- C014 — pass 1: C04 1→2, F05 1→2, F07 1→2, F09 1→2, F10 0→1, O01 1→2; pass 2: C04 1→2, F05 1→2, F07 1→2, F10 0→1, O01 1→2.
- C019 — pass 1: F05 0→2, F07 0→1, F08 0→1, F10 0→1; pass 2: F05 0→2, F07 0→1, F08 0→1, F10 0→1.
- C037 — pass 1: C05 2→1, F02 0→1, F05 1→2, F08 0→1, F10 0→1; pass 2: C05 2→1, F02 0→1, F05 1→2, F08 0→1, F10 0→1.
- C041 — pass 1: F07 1→2; pass 2: C04 1→2, F07 1→2, F10 1→2.
- C056 — pass 1: F01 2→1, F09 1→2, F10 0→1, O01 1→2, O04 2→0; pass 2: F01 2→1, F10 0→1, O04 2→0.

**Luna**

- C001 — pass 1: C04 0→1, F06 0→1, F10 0→1; pass 2: C04 0→1, F06 0→1.
- C014 — pass 1: F10 0→1; pass 2: C04 1→2, F10 0→1.
- C019 — pass 1: F05 0→1, F07 0→1, F08 0→1, O04 1→0; pass 2: F04 0→1, F05 0→1, F08 0→1, F10 0→1, O04 1→0.
- C037 — pass 1: F02 0→1, F04 1→2, F06 1→2, F07 1→2, F08 0→1, P09 2→1; pass 2: F02 0→1, F06 1→2, F07 1→2, F08 0→1.
- C041 — pass 1: C01 2→1, C04 1→2, C05 2→1; pass 2: C02 2→1, C04 1→2, R03 2→1.
- C056 — pass 1: F09 1→2, F10 0→1, O01 1→2; pass 2: F04 1→2, F09 1→2, F10 0→1, O01 1→2, P09 2→1.

**Haiku**

- C001 — pass 1: C04 0→1, F06 0→1, F07 1→2, F08 0→1, F10 0→1, O04 2→1; pass 2: C04 0→1, F06 0→1, F07 1→2, F08 0→1, F10 0→1, O04 2→1.
- C014 — pass 1: F04 1→2, F10 0→1, O01 1→2; pass 2: C04 1→2, F05 1→invalid, F10 0→1, O01 1→2.
- C019 — pass 1: F01 2→1, F04 0→1, F05 0→1, F06 0→1, F08 0→1, F10 0→1, R03 2→1; pass 2: F01 2→1, F04 0→1, F05 0→1, F06 0→1, F07 0→1, F08 0→1, F09 2→1, F10 0→1.
- C037 — pass 1: F02 0→1, F05 1→2, F08 0→1, F10 0→1; pass 2: C01 2→1, F02 0→1, F08 0→1, F10 0→1.
- C041 — pass 1: C04 1→2, F06 1→2, F07 1→2, F10 1→2; pass 2: C01 2→1, C04 1→2, F06 1→2, F07 1→2, F10 1→2.
- C056 — pass 1: F10 0→1, O04 2→1; pass 2: F10 0→1, O01 1→2, O04 2→0.

## Repeatability and model disagreement

| Model | Numeric flips / valid in both | Numeric agreement | Validity transitions |
| --- | --- | --- | --- |
| GLM | 7/136 | 94.85% | 0 |
| Luna | 13/136 | 90.44% | 0 |
| Haiku | 10/135 | 92.59% | 1 |

| Model pair | Pass 1 numeric / jointly valid | Pass 2 numeric / jointly valid | Validity transitions (1 / 2) |
| --- | --- | --- | --- |
| GLM / Luna | 23/136 | 25/136 | 0 / 0 |
| GLM / Haiku | 20/136 | 16/135 | 0 / 1 |
| Luna / Haiku | 26/136 | 24/135 | 0 / 1 |

Only two repeats were measured. Cache reuse does not establish determinism.

The preserved format-v2 GLM outputs, revalidated under the same partial-credit rule,
scored **116/136 and 112/136** (85.29% / 82.35%; macro-F1 0.8225 / 0.7811), with full coverage.
Those fixed outputs had six numeric flips across 136 jointly valid answers.
Aligned GLM adds a C037 C05 passing-control failure in both passes (59/62 versus
60/62 previously), with no recovered controls in those matched comparisons.
The report pairs each historical pass with its aligned GLM pass, including control regressions
and recoveries. Historical comparisons are not randomized concurrent controls.

## Sampling, caching and cost

| Model | Explicit supported generation settings |
| --- | --- |
| GLM | Medium; temperature 0, top_p 1, seed 0; prompt-schema output |
| Luna | Medium; temperature/top_p unsupported at this effort, seed unsupported; native structured output |
| Haiku | Adaptive medium; sampling fields deliberately omitted per provider contract; native structured output |

Requested settings and any returned Fireworks sampling header are preserved in the report.
A requested seed may not be echoed. Medium does not imply equal compute across providers.

| Model, including 3 probes | Estimated USD | Native cache read fraction | Call latency median / max | Call time sum |
| --- | --- | --- | --- | --- |
| GLM | $0.256149 | 74.22% | 3.2s / 12.5s | 984.3s |
| Luna | $0.126217 | 91.91% | 5.7s / 21.5s | 1813.3s |
| Haiku | $0.205947 | 91.95% | 4.5s / 15.4s | 1262.2s |
| All 825 calls | $0.588313 | 87.14% | 4.5s / 21.5s | 4059.7s |

The three GLM probes reported zero cache reads despite verified matching prefixes and
the documented routing key. That negative result was investigated and preserved; the
full GLM passes subsequently reported 78.18% and 70.70% cache reads. Luna and Haiku
showed reuse during their probes. Offline receipt replay dispatched no new requests.

Cache checks used actual distinct-candidate adequacy requests for all three providers. Generation receipts: 825; successful token-count responses: 550. Measured phase wall time: 4093.6s.

Fixed aggregate caps: $26.75, 825 generation requests, 550 count requests, 3,379,200 output tokens and 11,520 seconds. No cap was reset.

Costs are native-token estimates using dated rates, not billed invoices. Unknown native counters
remain unknown; the report retains known subtotals. Cache probes are included in cost and excluded from accuracy.

## Review and boundaries

The first round contains nine shared disagreements. Several models detect a false
assertion but preserve partial credit because the conclusion field is correct. Luna
sometimes demands pet-policy details in an enforcement answer, yet accepts their
absence in a neighboring candidate. C056 O04 receives GLM 0 / Luna 2 / Haiku 1
in pass 1. These are concrete essentiality and whole-answer interpretation differences,
not evidence that a new inventory procedure is already effective.

Semantic reviews inspect central contradictions, supporting defects and incidental details;
they do not relabel the dataset. See the bound review artifacts in the result pointer, especially
`first_round_semantic_review.json`, `glm_semantic_review.json` and `crossmodel_interim_review.json`.

Validation: 393 focused tests; `make fix`; `make check` (4,503 passed, 1 skipped); `git diff --check`. Independent preflight and report-code reviews are bound in the result pointer.

Stop for user review before promotion, further tuning, additional data or requirement-inventory experiments.
Prior artifacts and reserved/test boundaries remain preserved. No commit or push.

[Result pointer](task09f_aligned_models_dev6_result.json) binds the complete external comparison and reviews.
