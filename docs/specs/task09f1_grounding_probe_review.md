# Task 09F.1 — Historical catalog review for G

Status: planning input, not approved labels, a generated dataset or judge-prompt
content. The [proposed G rules](grounding_labeling_rules.md) and
[contract](task09f1_grounding_judge_contract.md) remain unchanged by this review.

## Sources and transfer boundary

Found the [original 31-category catalog](task09a_perturbations.json), its
[task explanation](../../tasks/sprint2/09a_create_synthetic_challenges.md#perturbation-catalog-and-expected-behavior),
the [fresh-generation instructions](task09a2_generation_prompt.md), and the
[A01–A10 adequacy additions](task09f_adequacy_perturbations.md).
The additions overlap historical families; they are not ten independent new failure
types. Historical G/A tendencies refer to obsolete whole-answer contracts. Review
actual point text, citations and source evidence before assigning new binary labels.

## Mapping to supporting-point G

| Historical IDs | Use under the proposed G boundary |
| --- | --- |
| P01, P05, P06 | Passing controls for paraphrase, compression and presentation changes that preserve the actual claims, qualifications and evidence links. Increased asserted certainty is a different edit. |
| P02 | Point-order/request-isolation control. Reordering other points should not alter an unchanged point's input or verdict. |
| P03, P04 | Combine/split points while preserving citation ownership and qualification attachment. Grouped assertions may need joint sources; supported fragments do not rescue an unsupported clause. |
| P07 | Removing unrelated optional context should not affect a target. Removing a material qualification is not this control. |
| P08 | Alternative actually cited, verified evidence may support a point even when it differs from reference citation IDs. |
| P09 | An alternative argument is not a G grading criterion; its newly asserted factual points still need their own cited support. |
| O01, O02, O03 | Supported but incomplete/irrelevant points are positive G controls. Missing explanation or question coverage belongs to S/C unless remaining assertions change. |
| O04, F03 | Conclusion-only edits have no G target effect when points/evidence are unchanged. Exclude redundant semantic G calls. |
| F01, F02, C04 | Unsupported added/replaced factual assertions within a point, including one unsupported clause among several supported ones. Original central/secondary significance does not change the point binary. |
| F04 | Wrong numbers, units, entities, direction or comparison. Include matching vocabulary with an altered relationship, not just obvious unrelated facts. |
| F05, F09 | Unsupported certainty, resolution or removal of source uncertainty. Pair with faithful tentative statements and tone-only P06 controls. |
| F06 | Wrong scenario, location, population, alternative or period. Accurate quotations can still be applied outside their supported scope. |
| F07 | Removing a condition/exception so that the point makes a broader unsupported assertion; pair with omissions of incidental detail that preserve the assertion. |
| F08 | Source says association, point asserts causation: G can fail. Sources support premises but their overall argument does not establish the conclusion: S owns that separate failure. |
| F10 | Contradictory assertions inside the target point are relevant. A disagreement elsewhere is not a global G penalty or permission to re-review another point. |
| C01, C02 | Real-but-irrelevant evidence or citations attached to the wrong point. Do not borrow the right evidence from another point. |
| C03 | Joint support versus removal of a necessary source. The remaining evidence, not citation count, determines support. |
| C05 | Automatic citation-precheck fixtures: missing/unresolved candidate IDs fail before G; valid-artifact read failures are evaluator errors. These are not semantic G model calls. |
| R01, R02 | No-answer classification/empty-field guard fixtures, not automatic G-positive or G-negative labels. Known eligible substantive points can be tested independently. |
| R03 | Instruction robustness: grade the actual assertion against permitted evidence; ignore grading instructions embedded in input. |
| A01, A02, A09, A10 | Conclusion list/reference-agreement failures belong to C. G evaluates actual support assertions, not reference coverage or permissible conclusion item count. |
| A03, A08 | Added explanatory/neutral text is not automatically a G pass or failure; any factual assertion added to the target still needs support. |
| A04–A07 | Restatement, neutral-only argument, missing supporting coverage and inadequate examples primarily test S. Their individual factual assertions can remain grounded. |

## Clarifications worth settling before locking G

1. **Local inference versus argument sufficiency.** A causal, comparative or numeric
   relationship asserted inside the target must be established by its sources;
   labeling it reasoning does not exempt it. Do not extend that check into deciding
   whether all candidate points establish the conclusion.
2. **Organization versus evidence ownership.** Source reuse across points is legal
   when each actually cites it. Splitting/combining can change the owned evidence
   and therefore the correct verdict; it is only an invariance control if support
   and links genuinely survive. Do not repair missing links from another point.
3. **Contradictions and uncertain labels.** Check whether apparently incompatible
   passages address the same scenario/time/condition. In genuinely unresolved source
   interpretations, hold the proposed calibration label for review; do not invent
   a false label or a precedence rule merely to fill the binary dataset.

These are mostly applications of existing draft rules, not grounds for adding a
long checklist or new output fields to the judge prompt.

Two useful contrasts deserve explicit probes: removing detail can leave a weaker,
still-supported claim, whereas removing a condition can make a claim unsupported;
and an irrelevant extra citation need not defeat sufficient owned evidence, whereas
removing a necessary joint-evidence member can. Extra citation relevance remains
distinct from point entailment, subject to actual scope/contradiction review.

## Additional probe candidates

Beyond the explicit historical category names, consider table headers/units and
footnotes that change a claim; subgroup versus total/denominator mistakes; estimates
versus measured results; exceptions/negation; unsupported document-wide absence;
and quotation or recommendation presented as an established fact. Treat these as
candidate applications, not newly approved independent families. Source scope and
applicability determine whether a useful contrasting pair exists.

Keep malformed schemas, lost source text and duplicate IDs as mechanical fixtures.
No cases or judges were run during this catalog review.
