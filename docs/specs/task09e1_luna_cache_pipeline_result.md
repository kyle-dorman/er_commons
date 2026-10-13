# Task 09E.1 — Luna cache and complete-pipeline results

The user selected Luna only for subsequent inference and authorized the
[bounded cache and pipeline experiment](task09e1_luna_cache_pipeline_v1.md).
All historical experiments remain preserved. This follow-up uses the same eleven
original unresolved answers; there is no Dev6, full-19, reserved or test expansion.

## Cache repair

The opt-in Luna renderer splits the original user JSON into two text blocks after
the complete evidence and question fields, and marks that boundary for caching.
Their concatenated text is byte-identical to the previous payload; citation scope,
output schema and local validation remain unchanged. Implicit end-of-message
caching remains enabled, preserving exact-duplicate reuse. Default request layouts
and other provider paths remain unchanged.

Two original claim pairs with the same evidence, question and output schema each
ran A, B, A under old and repaired layouts. All twelve generations passed exact
count/native parity, model identity, semantic structure and no-reuse checks.
All four initial A requests were observed cold. On the changed B request:

| Pair | Old layout cache reads | Repaired layout cache reads |
| --- | ---: | ---: |
| P5 modality contrast | 0 | 1,303 |
| P4 bounded-absence paraphrase | 0 | 1,303 |

Exact-duplicate A requests still reused 1,334 or 1,346 input tokens under both
layouts. Total probe usage was 16,148 input / 3,752 output tokens, with a $0.002978
standard list-rate estimate. All twelve native receipts report developer as payer.
The independent cache audit passed, qualifying this layout for the full experiment.

These probes demonstrate improved changed-claim reuse for these inputs, not a
universal hit rate. Luna's minimum prefix length and changing schemas (including
point IDs), prompts and source identities can still prevent reuse. Cache keys
alone are not proof of cold isolation; the cold evidence is native receipt usage.
Caching reuses input computation, not previously generated judgments.

## Complete-pipeline experiment

Four prompt arms each run three fresh passes through all eleven answers. Every
pass includes the original gate, all 41 points and a new conclusion using only
that pass's actual binary predictions. No original saved prediction is forwarded.
Medium reasoning and the repaired cache layout are common to all arms.

| Arm | Claim instructions | Conclusion instructions |
| --- | --- | --- |
| A | Original | Original |
| B | Original + combined clarification | Original |
| C | Original + combined clarification | Original + combined clarification |
| D | Original + combined clarification | Combined + conclusion-specific refinement |

The combined addition addresses scope, bounded absence and grammatical attachment.
The conclusion refinement emphasizes independent review of fallible predictions,
each claim's own citations, and explaining a reversal without being instructed to
agree. Full texts are frozen in external `prompts.json`; base prompts are unchanged.

All 756 pipeline stages validated; there were no false abstentions, protocol
failures or replacement calls. Counts below are **33 evaluations per arm**
(eleven answers × three repetitions), not 33 distinct answers.

| Arm | Numeric scores by pass | Total numeric | Unresolved | Clear point / review agreement |
| --- | --- | ---: | ---: | --- |
| A: original | 7, 6, 5 | 18/33 | 15/33 | 13/15; 13/15 |
| B: claims only | 7, 5, 6 | 18/33 | 15/33 | 12/15; 13/15 |
| C: both stages | 6, 8, 8 | 22/33 | 11/33 | 15/15; 15/15 |
| D: stronger conclusion | 10, 8, 8 | 26/33 | 7/33 | 15/15; 15/15 |

The clear diagnostic denominator contains five original claim observations per
pass (four distinct reviewed claim groups, one appearing twice). These are frozen
source interpretations, not adjudicated gold labels. Ambiguous HOA/lease scope is
excluded from that agreement measure. Numeric scores matching synthetic proposals
were 14, 13, 14 and 14 respectively; extra numeric coverage does not establish
better accuracy. Point-review reversals were 17, 16, 11 and 7.

B fails the frozen improvement rule: no coverage gain and a clearer grading claim
regressed. C and D pass the quantitative screen; D ranks first on those metrics.
However, source review found D once rejected the non-substantive sentence “The
relevant provisions are set out below” solely because it had no citations. That
produced a numeric zero and illustrates why coverage cannot be the acceptance
gate. D is **not promoted**. C remains a development candidate, not a qualified
judge or default. The unchanged prompts remain the package defaults.

On the truly identical C04/F05/F07 conclusion text, supported judgments were
6/9, 5/9, 2/9 and 0/9 for A–D. D consistently uses a narrower grammatical reading;
that consistency does not settle the underlying ambiguity. The surrounding answer
and predictions differ, so these are not identical complete requests. The final
source review corrects an interim report that mistakenly grouped differently
worded P01/P03 conclusions with these. D also once overread P03's broad summary
as requiring every control, a separate scope concern requiring adjudication.

C and D had identical review-stage point decisions across all three repetitions for
41/41 point slots, compared with 37/41 for A and 36/41 for B. Initial point decisions
were unanimous for only 31, 36, 35 and 36 slots respectively. Complete final
outcomes (status and score) were repeat-consistent for 1, 6, 5 and 4 of eleven
answers; only 0, 3, 4 and 4 had the same numeric score on all three repetitions.
Stable point reviews therefore do not imply a stable complete evaluator.

### What changed at the conclusion step?

The earlier prompt addition was tested in both claims and a fixed-context
conclusion experiment; that earlier experiment retained the old point decisions.
Here every conclusion receives newly generated decisions. This distinction matters
because a reviewer may consistently correct an inconsistent first-stage judgment,
leaving an unresolved disagreement under the fail-closed aggregation contract.

Matching sample and repetition, and restricting to identical complete fresh point
verdict vectors, gives the following conditional comparison:

| Pair | Matching inputs out of 33 | Numeric, left | Numeric, right |
| --- | ---: | ---: | ---: |
| B versus C | 19 | 13 | 13 |
| B versus D | 19 | 15 | 15 |
| C versus D | 23 | 19 | 19 |

There is **no net numeric-coverage gain on these matched inputs**. The full-arm
coverage difference is concentrated where initial judgments differ, even though
B/C/D use the same point prompt. This is stochastic variation and a small selected
sample; it does not show that a later prompt caused earlier judgments to change.
Nor does the conditional comparison prove the conclusion prompts are equivalent.
Do not attribute D's complete coverage gain solely to its conclusion addition.

Source-review interpretations and synthetic proposals remain separate diagnostics,
not gold truth. The suite was selected because the original model disagreed with itself;
three repetitions cannot establish determinism or held-out accuracy. Independent
fresh point generations also introduce variation between arms, so the report
separately compares conclusion calls whose fresh input verdicts happen to match.

## Cost and caching in the full pipeline

Across the four full arms, 905,749 of 1,195,752 input tokens were cache reads
(**75.75%**), with 205,145 cache-write tokens and 84,858 ordinary input tokens.
This is an observed rate under the repaired layout, not a paired estimate of the
repair's full-pipeline savings. Prompts/schemas and prefix lengths still matter.

All 768 generations, including twelve qualification probes, have complete native
receipts. The standard list-rate estimate is **$0.223372 total** (about 22 cents):
A $0.049161, B $0.055852, C $0.057560, D $0.057821, probes $0.002978.
All report developer as payer; actual invoice totals or promotional coverage are
not inferred. Reservation bounds were $4.25 overall and $1 per pipeline arm;
each arm reserved less than $0.725 and finished within twenty minutes. No retries,
other models, dataset expansion or extra inference followed the experiment.

## Validation and evidence

Focused tests: 210 passed. `make fix` passed. `make check` passed format/lint/types
and reported 4,259 passed, one skipped and only the same three historical Task 06G
failures. Independent provider/Inspect, launcher, cache and analysis reviews were
performed; default behavior and full request/receipt binding have regression tests.
No commits or pushes.

All 45,712 checks of prior artifacts passed. Credential scanning includes decoded
Inspect logs; input and implementation bindings were independently verified.
The [result pointer](task09e1_luna_cache_pipeline_result.json) binds the completed
namespace and final reviews. The final source review supersedes its preserved
interim report; neither numeric coverage nor proposed-label agreement is a gold
accuracy estimate.

External namespace:
`task_09/09e1_20261012_luna_cache_pipeline_v1/`. Frozen inputs, launch/analysis
scripts, native receipts, Inspect logs, both positive and negative results,
pricing/payer diagnostics and independent reviews are retained there. Credentials
are loaded only inside code from the untracked repository `.env`.
