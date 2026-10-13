# Dev6 conclusion evidence-boundary result

The clarification improves agreement outside the pet-policy question, but does
not improve overall conclusion agreement. Keep it as an experimental candidate;
the predeclared overall-gain criterion is unmet, so no default is promoted.
The [contract](task09e1_luna_conclusion_evidence_dev6_v1.md) remains frozen.

Both fresh Luna arms completed 136 answers with the same 323 actual original
claim decisions. Only the conclusion stage ran, including its existing point
review; the original claims remain frozen. All 272 generations validated. One
pass per arm measures agreement, not repeatability or a causal prompt effect.
All results below retain the unchanged proposed labels. All 136 complete input
payloads are distinct; there are no exact duplicate-input groups to compare.

## Conclusion support agreement

Clean abstentions are excluded from this table and assessed separately.

| Question | Original | Clarified |
| --- | --- | --- |
| C001 | 20/21 | 21/21 |
| C014 | 17/18 | 18/18 |
| C019 | 19/20 | 20/20 |
| C037 | 25/25 | 25/25 |
| C056 | 19/20 | 19/20 |
| C041 (pet policy) | 17/20 | 14/20 |
| **All six** | **117/124 (94.4%)** | **117/124 (94.4%)** |
| **Five excluding C041** | **100/104 (96.2%)** | **103/104 (99.0%)** |

Equal-weight question means are 94.11% versus 94.17%; outside C041 they are
95.94% versus 99.00%. Both arms have zero false acceptances and seven false
rejections against the proposals. Three corrections outside C041 are offset by
three C041 regressions. This is a broader picture than the deliberately difficult
seventeen-answer pilot, whose results should not be read as full-panel accuracy.

The other 119 answers contain 107 substantive conclusions: agreement rises
103/107 to 105/107. The earlier seventeen fall 14/17 to 12/17. Original Dev3
substantive agreement is 59/63 to 57/63; the three added cases rise 58/61 to
60/61. These remain development data, not held-out validation.

## Claims review and final scoring

| Measure | Original | Clarified |
| --- | --- | --- |
| Frozen original claim agreement | 313/323 | 313/323 |
| Conclusion-stage claim-review agreement | 317/323 (98.1%) | 320/323 (99.1%) |
| Corrections / damaging reversals of frozen claims | 8 / 4 | 9 / 2 |
| Numeric scores returned, eligible denominator | 113/124 | 114/124 |
| Correct numeric scores, eligible denominator | 106/124 (85.5%) | 109/124 (87.9%) |
| Correct among returned numeric scores | 106/113 (93.8%) | 109/114 (95.6%) |
| Correct N/A outcomes | 12/12 | 12/12 |
| Unresolved claim-review disagreements | 11 | 10 |
| Correct final status/score, all answers | 118/136 | 121/136 |

No abstentions are included in the numeric denominator; no unresolved result is
credited as N/A. All twenty zero-point inputs were retained, including eight
substantive answers. The existing disagreement gate remains: even a useful
correction of an original claim can prevent a numeric score. Outside C041,
returned scores fall 101/104 to 99/104 while correct numeric scores rise 95/104
to 98/104. Agreement, score coverage and disagreement are distinct outcomes.

## Independent source review

The gains outside C041 have a concrete mechanism. C001's conclusion can use the
thresholds and tables cited elsewhere in its answer; C019's conclusion can use
the explicit trench-model evidence on a supporting point even though its own
citation is unresolved. C014 likewise benefits from answer-wide evidence, but
its reference to the Draft document versus supporting Final evidence remains an
attribution caveat. These are not three equally unqualified successes.

C001 also exposes a remaining rule failure: its corrected conclusion comes with
a newly incorrect claim review that explicitly borrows another point's source
to repair that claim's own wrong citation. Three other changed claim reviews
correctly reject unsupported scope or contrasts. A matching conclusion label
does not establish that the whole response follows the evidence boundaries.
Both arms also miss an unsupported development-plus-buildout extension when it
appears inside a compound claim, although they reject it when presented as a
separate claim. This is a remaining compound-claim coverage error, not a gain
from the clarification.

C041's three new conclusion rejections share a defensible stricter reading of an
ambiguous terminal modifier. Preserve the proposal disagreements without calling
them three fabricated facts or silently relabeling them. Stable correct controls
were inspected across all six questions. The broader gains support the intended
evidence distinction, but the overall result and remaining citation leakage do
not meet the predeclared promotion criteria.

## Execution and limitations

Standard-rate estimates are $0.122126360 original and $0.122471885 clarified,
$0.244598245 total. These are usage-based estimates, not an invoice or a claim
that daily promotional credits applied; native receipts identify developer payer.
Cache reads account for 39.1% and 40.7% of input tokens. Each arm finished in
about 3.6 minutes; median call latency was 5.49/5.83 seconds. Separate cold arm keys
and varied complete inputs limit comparison with earlier repeated-input runs.
Quotation diagnostics remain separate: missing quotation flags 59/68 and
nonliteral locator flags 9/8, respectively; these do not invalidate semantic
judgments or silently change scores.

Focused tests: 366 passed. `make fix` passed without source changes. `make check`
retains 4,271 passed, one skipped and the same three historical Task 06G failures.
Prior artifacts and input bindings were checked; details and native receipts live
in the external result namespace. No labels, package defaults, original claims,
reserved/test data or later tasks changed. No commits or pushes.

The [result pointer](task09e1_luna_conclusion_evidence_dev6_result.json) binds the
analysis, source reviews, native audit, validation and completion inventory.
