# Grounding judge experiment record — Tasks 09E and 09E.1

Consolidated October 13, 2026, from the preserved task outcomes and experiment
reports. This is the entry point for what we tried, including unsuccessful
approaches. It summarizes completed grounding work; ongoing 09F adequacy work
has its own task and result records. No new experiments or metric recomputation
were performed for this consolidation.

## Accepted configuration and interpretation

Use GLM Flash at medium reasoning, simple claims instructions and original
conclusion semantics with the explicit empty-review-list clarification. Luna and
Haiku remain alternatives. Small Qwen remains useful for plumbing tests; Clef
execution is retired and DeepSeek is set aside. The
[maintainer guide](grounding_judge_guide.md) owns current interfaces and settings.

The final patched full-development comparison is below. These are the defined
failure-inclusive class-macro F1 metrics, not metrics conditional on valid output.

| Configuration | Original claims | Claim reviews | Conclusions | Final numeric score | Numeric coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna retained | 93.46% | 96.96% | 92.93% | 88.51% | 350/392 |
| Haiku updated | 93.23% | 94.84% | 96.05% | 89.05% | 354/392 |
| GLM updated | 97.50% | 94.64% | 97.57% | 93.46% | 365/392 |

[Source and remaining errors](specs/task09e1_glm14_conditions_dev6_result.md).
Population: 1,056 original claims/reviews, 392 substantive conclusions/numeric
targets, and 38 clean grounding N/A answers across 19 development questions.
Haiku and GLM include targeted repairs with mixed prompt provenance; these are
not fresh uniform-prompt reruns. Luna was retained, not rerun alongside the final
repairs. Agreement with synthetic development proposals is not independent human
validation or held-out judge qualification. 09G owns the final challenge/freeze.

## How to use this record

- Each link leads to the detailed outcome, which preserves the matching contract,
  identities, raw-artifact pointers, exact settings, costs and reviews. Historical
  commands and stop boundaries describe that experiment, not current instructions.
- Populations changed over time. Early Dev3 had 12 answers; later combined Dev3
  had 69 and Dev6 had 136. Repeated trials and citation aliases do not create new
  independent semantic questions. Do not compare percentages across rows as if
  they came from one controlled experiment.
- Separate five outcomes: valid output, numeric coverage, agreement with labels,
  repeatability on identical requests, and source-supported interpretation.
  Cache hits reuse input computation and do not make generations deterministic.
- Older reports retain their historical metric conventions. Do not silently
  substitute their valid-only figures for the final failure-inclusive metrics.
  Invalid/missing outputs remain failures in comparisons, never fabricated
  semantic zeroes. Clean grounding abstention remains separate N/A.

## Local judge and output-contract experiments

The [09E task](../tasks/sprint2/09e_implement_grounding_judge.md) contains the
source-linked outcomes for the early controlled changes below.

| Technique and scope | Observed result | Decision / reusable lesson |
| --- | --- | --- |
| Single-call prompt revision: enumerate points, concise exact spans, findings before final score; same 12 small-Qwen answers | Complete point coverage rose 2/12 to 8/12, but both versions produced zero valid judgments. | Clearer instructions helped structure, not sufficient source reading or semantic validity. [Outcome](../tasks/sprint2/09e_implement_grounding_judge.md#historical-outcome--initial-small-model-limitation) |
| Double output allowance, 1,500 to 3,000; same prompt and inputs | Length failures fell 3 to 2; zero valid judgments remained. Some outputs continued repeating invented point IDs. | More output space can prolong a loop rather than solve it. [Outcome](../tasks/sprint2/09e_implement_grounding_judge.md#historical-outcome--3000-token-length-only-experiment) |
| Exact per-point tuple in constrained schema | Complete coverage reached 12/12 and length failures reached zero; still zero valid judgments. | Structural constraints solved missing/duplicate entries, not entailment, quotes or materiality. [Outcome](../tasks/sprint2/09e_implement_grounding_judge.md#historical-outcome--structural-point-coverage) |
| Conditional materiality schema matching validator eligibility | Materiality failures disappeared; only 1/12 judgments validated. | Enforce mechanical eligibility in schema, but schema acceptance is not correct classification. [Outcome](../tasks/sprint2/09e_implement_grounding_judge.md#historical-outcome--materiality-eligibility) |
| Split into individual point checks and conclusion review | Small-Qwen panel still yielded only one numeric result; stage diagnosis became possible with more calls. | Retain stage separation for evidence ownership and inspectability; do not claim decomposition alone fixed quality. [Outcome](../tasks/sprint2/09e_implement_grounding_judge.md#current-outcome--per-point-checks-and-conclusion-review) |
| Answer-only abstention classifier | Initial 12-answer check matched all proposals, but contained just one clean abstention. Broader 136-answer run recognized only 6/12 clean abstentions and falsely exempted 15 substantive answers. | A narrow successful fixture did not generalize. Test varied abstentions and substantive controls. [Initial](../tasks/sprint2/09e_implement_grounding_judge.md#answer-only-abstention-follow-up--october-11-2026), [broader outcome](specs/task09e_09a3_small_v1.md) |
| Point-scope prompt: support what is asserted, not question completeness | Same 36 points: validated outputs rose 15 to 17, but all valid decisions were unsupported. | Some old objections disappeared and new incorrect reasons replaced them; no semantic improvement. [Outcome](../tasks/sprint2/09e_implement_grounding_judge.md#point-prompt-scope-revision--october-11-2026) |
| Small Qwen on all 136 eligible combined Dev6 answers | All 142 valid point predictions were unsupported, including 99 proposed-supported points; all 30 numeric scores were zero, with 75 output failures. | Broader coverage exposed classification collapse; matching some negative labels did not establish discrimination. [Outcome](specs/task09e_09a3_small_v1.md) |
| Qwen 9B replacing small Qwen on identical 69-answer Dev3 | Accepted more supported claims and recognized all six clean abstentions, but only 12/69 numeric scores; 50 output-validation failures. | Model capacity helped, but local judge quality and literal excerpt failures remained limiting. [Outcome](specs/task09e_09a3_qwen9b_v1.md) |
| Clef uncounted exploratory trial after exact qualification limits | 69-answer population: 22 numeric, seven N/A including one false exemption, 23 disagreements, 16 body-overflow answers and one ambiguous abstention. Oversized stages were skipped rather than truncated. | Request-body size and token context limits differ; this was not exact-counter qualification. Size-selected survivors cannot establish full-panel performance. Clef later retired by user preference. [Qualification](specs/task09e1_clef_qualification.md), [result](specs/task09e1_clef_exploratory_result.json) |
| Separate semantic validity from exact quotation diagnostics for cloud trials | Preserved strict source-ID validation while tracking quotation mismatches separately. | Quote-copy errors and unsupported claims are different failure classes. Cloud versus old Qwen results are not a model-only comparison. [Contract](specs/task09e1_comparison_v1.md), [initial Luna result](specs/task09e1_luna_generation_result.json) |

## Sampling, claims prompts and complete-pipeline tests

| Technique and scope | Observed result | Decision / reusable lesson |
| --- | --- | --- |
| Low versus medium reasoning; separately no-reasoning temperature 1 versus 0; eight inconsistent requests, three repeats each | Medium matched 10/12 clearer source-review observations versus low's 7/12. Temperature 0 made 6/8 claims unanimous but matched only 3/12 clearer observations; temperature 1 hit an output cap. | Selected medium for diagnostic follow-ups. Stability can preserve the wrong answer; temperature and reasoning comparisons were distinct. [Outcome](specs/task09e1_settings_prompts_models_result.md#settings-on-inconsistent-claims) |
| Five additions: scope/qualifications; bounded absence; grammatical attachment; combination of those three; balanced assertion checklist | Clear-review agreement: 11/12, 10/12, 10/12, 12/12, 12/12 versus medium baseline 10/12. Combined prompt was the leading diagnostic candidate; individual additions regressed items or stability. | Keep the full five-arm result, not just the apparent winner. Selected interpretations were not adjudicated gold labels. [Outcome](specs/task09e1_settings_prompts_models_result.md#five-prompt-ideas) |
| Combined clarification at conclusion review with original claim verdicts frozen; eleven unresolved answers | Both original and combined prompts left ten answers unresolved and produced one numeric score. | Improving review wording does not necessarily reconcile first-stage decisions. No pipeline gain established. [Outcome](specs/task09e1_settings_prompts_models_result.md#five-prompt-ideas) |
| Four complete-pipeline arms: original, claims-only addition, addition in both stages, stronger conclusion refinement; eleven answers × three repeats | Numeric coverage 18/33, 18/33, 22/33, 26/33; proposal-matching numeric counts 14, 13, 14, 14. Stronger conclusion also rejected a procedural introduction for lacking citations. | Claims-only failed; both-stage arm remained a candidate; stronger conclusion not promoted. No net coverage gain on matched fresh claim-verdict inputs, so whole-arm gains cannot be attributed solely to conclusion wording. [Outcome](specs/task09e1_luna_cache_pipeline_result.md) |
| Broad contextual-summary addition; ten exact claim inputs, nine repeats per arm | Overall agreement 81/90 to 83/90, but controls regressed and unanimous-correct inputs fell 6/10 to 5/10. | Failed frozen expansion criteria. Ordinary summary acceptance must not permit universal-scope overstatement. [Outcome](specs/task09e1_luna_context_claims_result.md) |
| Replacement scope-preserving instruction, rather than accumulating another addition; same pilot design | Overall agreement fell 83/90 to 79/90; controls and grading-condition interpretation regressed. | Rejected. Explicit relationship wording did not reliably fix the relationship error. [Outcome](specs/task09e1_luna_scope_claims_result.md) |
| Structured claims explanation inside existing response schema; ten inputs × five repeats per arm | Agreement 44/50 to 45/50, with a sharp regression on one short pet-policy input. | Failed the predefined gain/nonregression criteria. Inspectability alone is not enough. [Outcome](specs/task09e1_luna_structured_claims_result.md) |
| User-authorized Dev6 expansion of direct versus structured claims | Agreement 313/323 to 315/323; 157 added claims tied and exact-payload weighting did not favor structure. | Kept the simple claims version. Expansion did not retroactively pass the failed pilot. [Outcome](specs/task09e1_luna_structured_dev6_result.md) |

## Conclusion experiments with frozen original claims

These tests separated conclusion-stage changes from rerunning the original claims.
Claim review already existed; adding another explanation structure was not the
first decomposition of the judgment.

| Technique and scope | Observed result | Decision / reusable lesson |
| --- | --- | --- |
| Prior claim verdicts visible versus hidden versus no claim reviews; seventeen answers × three repeats | Review agreement visible 174/177 versus hidden 168/177; numeric coverage 36/51, 29/51, 51/51 respectively. All arms tied at 24/33 conclusion agreement on the original eleven trouble answers. | Hiding verdicts damaged controls. Removing review changed the scoring mechanism and preserved original claim errors; full coverage was not evidence that review was unnecessary. [Outcome](specs/task09e1_luna_conclusion_blind_result.md) |
| Structured conclusion explanation: Interpretation, Evidence, Inference, Verdict basis, plus fidelity guidance; seventeen answers × three repeats per arm | Repeatability improved, but conclusion agreement fell 36/51 to 32/51, with evidence-ownership errors. | Rejected. Structure and guidance changed together; this did not isolate formatting or establish effects on internal reasoning. More explicit explanations can accompany consistent errors. [Outcome](specs/task09e1_luna_structured_conclusion_result.md) |
| Clarify whole-answer conclusion evidence versus each claim's own citations; Dev6 | Overall conclusion agreement tied at 117/124; outside pet-policy rose 100/104 to 103/104; reviews rose 317/323 to 320/323. | Overall-gain criterion unmet; retained only as an experimental candidate. [Outcome](specs/task09e1_luna_conclusion_evidence_dev6_result.md) |
| Same conclusion clarification on full development, identical frozen claims | Conclusion macro-F1 92.93% to 92.97%; accuracy tied, equal-question F1 and review F1 fell, correct numeric scores tied. | Kept the original. Small pooled gains concealed regressions and did not justify complexity. [Outcome](specs/task09e1_luna_conclusion_full_dev_result.md) |
| Semantic appendix about unsupported assertions, conditions and scope; fresh paired Dev6 runs on Luna, Haiku and GLM | No model met overall/outside-pet-policy gain criteria; all lost claim-review agreement. GLM's tiny numeric-F1 gain did not increase correct scores and coverage fell. | Rejected across all three. Keep useful formatting clarification separate from this failed semantic addition. [Outcome](specs/task09e1_glm14_conditions_dev6_result.md#separate-fresh-dev6-prompt-comparison) |

## Provider, cache and formatting experiments

| Technique and scope | Observed result | Decision / reusable lesson |
| --- | --- | --- |
| Initial Luna generation on 69-answer Dev3 | 52 numeric scores, six clean N/A, eleven unresolved claim/review disagreements and zero invalid outputs. Of the seventeen nonnumeric answers, six were expected abstentions. | Generation stability, cross-stage agreement and agreement with labels require separate analysis; not every nonnumeric result is a failure. [Result](specs/task09e1_luna_generation_result.json) |
| GPT-5.4-mini and GPT-5.4, original prompts and low reasoning on Dev3 | GPT-5.4 showed strongest proposed-label agreement of those runs; mini's coverage gain did not offset weaker agreement. Neither eliminated inconsistencies or invalid locators. | Cost informed returning to Luna for subsequent experiments. No model was qualified by this development comparison. [Results, cost and timing](specs/task09e1_settings_prompts_models_result.md) |
| Luna shared-evidence cache boundary, old versus repaired layout | Changed-claim requests went from zero cached tokens to 1,303 in both probe pairs; exact duplicates already reused cache. Pipeline observed 75.75% cached input. | Retained repair. Byte-equivalent content can have materially different prefix reuse; probe changed targets, not just exact repeats. Full-run rate was not a controlled savings estimate. [Outcome](specs/task09e1_luna_cache_pipeline_result.md#cache-repair) |
| Same-prompt medium-effort GLM and Haiku full development | Haiku completed with unavailable downstream results; GLM completed claims but conclusions stopped on HTTP 412. | Preserve failures and partial denominators; provider reasoning settings are not guaranteed equivalent compute. Later continuations and repairs remain distinct. [Initial comparison](specs/task09e1_glm_haiku_full_dev_result.md) |
| Haiku resolved-evidence locator clarification on five invalid claims, then their five conclusions | All five claims validated as unsupported with empty locators; all five newly enabled conclusions matched expected labels and numeric scores. | Accepted targeted repair. IDs existing in a citation list do not mean source text is resolved. Results are mixed-prompt selected-failure patches. [Claims](specs/task09e1_haiku_locator_retry_result.md), [conclusions](specs/task09e1_haiku_conclusion_patch_result.md) |
| Fireworks layout/affinity repair: stable evidence before varying schema; GLM and DeepSeek | Changed-target probes improved from zero cache reads to roughly 96–98%; actual resumed GLM conclusions had only 22.72% cached input. | Retained repair, not a hit-rate guarantee. Short requests, cold groups and provider misses persisted; layout and affinity changed together. [Outcome](specs/task09e1_fireworks_cache_resume_result.md#cache-repair-and-actual-savings) |
| Narrow GLM JSON-wrapper recovery in saved outputs | Recovered allowed wrappers offline while retaining genuine model-output errors. | Parser repair is not a fresh generation or relaxed semantic validation. [Contract](specs/task09e1_glm_json_continuation_v1.md), [outcome](specs/task09e1_glm_haiku_full_dev_result.md) |
| Explicit empty claim-review list for GLM | First nine targeted retries all validated and matched labels; later fourteen repaired thirteen, with one still invalid. | Accepted narrow clarification. Models may invent review entries unless empty-list and exact-coverage rules are explicit. [Nine](specs/task09e1_fireworks_repair_8192_result.md), [fourteen](specs/task09e1_glm14_conditions_dev6_result.md) |
| DeepSeek output allowance 4,096 then 8,192 | First run exhausted allowance in reasoning with no final answer. Doubled allowance still ended with uncertain transport timeouts; final population: 822 valid claims, nine failures, 225 undispatched, no conclusions. | Set aside by user. Partial operational results cannot rank a complete pipeline; do not equate this with a demonstrated semantic failure. [Initial stop](specs/task09e1_fireworks_cache_resume_result.md), [continuation](specs/task09e1_fireworks_repair_8192_result.md) |

The original seven-condition plan also included Decisions/Jev paths. Implemented
adapters, offline audits or research do not establish completed paid comparisons.
See the [condition contract](specs/task09e1_comparison_v1.md) and
[provider research](specs/task09e1_provider_research.md); do not invent results for
unrun conditions. Clef retirement and the later cleanup preserved historical
artifacts rather than deleting evidence of unsuccessful approaches.

## Lessons to carry into the next experiment

1. Start simple and isolate changes. Explicit output rules and cache layout fixes
   produced useful engineering gains; broader semantic reminders often traded
   one interpretation error for another. More explanation was not reliably better.
2. Freeze original claims when testing conclusions. Otherwise upstream stochastic
   variation confounds claims about the conclusion prompt's effect.
3. Inspect failures by question and error type. Pet-policy wording concentrated
   ambiguity; passing controls exposed regressions that aggregate gains hid.
   Distinguish legitimate alternative readings from clear scope or modality errors.
4. Distinguish missing scores from incorrect semantic judgments. The disagreement
   gate sometimes withheld a score when review corrected the original claim.
   Removing the gate increased coverage without proving better underlying review.
5. Keep evidence ownership explicit. A claim uses its permitted citations; the
   conclusion can use the permitted whole-answer evidence. Quotation fidelity,
   identifier validity and entailment are separate properties.
6. Report accuracy, macro-F1, coverage, repeatability and cost together. Preserve
   selected-failure patches as patches, with mixed provenance disclosed. Native
   token-based cost estimates are not invoices or guarantees of free-tier coverage.
7. Recheck caching on the next task's actual request layout. Stable shared evidence
   helped, but probe success did not transfer directly to short heterogeneous runs.

The [research notes](llm_judge_learning_notes.md) connect these observations to
the papers and their transfer limits. The [09F contract](../tasks/sprint2/09f_implement_adequacy_judge.md)
owns how they apply to adequacy, including optional experiments; this record does
not authorize those experiments or change the adequacy rubric.

## Maintaining the record

For a new completed grounding experiment, add one bounded entry with the exact
change and comparator, model/settings, population and repeats, quantitative
result, regressions, decision and limitation. Link a detailed outcome containing
the frozen contract and artifact identities. Record failed gates and abandoned
approaches as first-class outcomes. Keep selected configuration separate from
historical winners; never overwrite prior reports to make the progression cleaner.
