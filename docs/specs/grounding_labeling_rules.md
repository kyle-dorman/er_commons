# Supporting-point grounding rules

Status: accepted and locked by Kyle on 2026-10-16; runtime not implemented.
Version: `task09f1.grounding.rules.v1`. Semantic changes require a new version.
The [contract](task09f1_grounding_judge_contract.md) owns fields and errors.

For each eligible supporting point, ask: **Do its own cited passages establish
every material assertion it actually makes?** Factual qualifications also need
grounding in exactly the same way: each is another point with its own citations.
The conclusion is not a separate G item.

1. **Own evidence only.** Use this point's actual cited source passages. Multiple
   passages may jointly support it. The question clarifies meaning/scope but supplies
   no evidence. Use no outside knowledge, reference answer or another point's sources.
2. **Require support for the whole assertion.** A compound point fails if a material
   assertion is unsupported or contradicted. Matching some facts or mentioning the
   same topic is insufficient.
3. **Match meaning.** Accept paraphrases and inferences established by the supplied
   evidence. Preserve entities, quantities, relationships, negation, scope, timing,
   conditions and uncertainty. Do not repair the candidate or invent premises.
4. **Evaluate the point, not question completeness.** Do not fail a supported point
   because it does not fully answer the question or reproduce incidental source
   detail. Absence from supplied excerpts
   does not prove document-wide absence. A possible/planned result does not establish
   a guaranteed/completed result.

Insufficient semantic support and explicit contradiction both produce `supported=false`; the
reason distinguishes them. A passage that does not support this point is not
therefore an invalid source. Every citation need not independently prove the point;
the owned evidence is assessed jointly. Citation matching metrics stay separate.

Code checks citations before any G call. A required point with no citations or
any unresolvable candidate citation fails the precheck automatically; it is not
sent to the model. Only points with nonempty, resolved owned evidence reach G.
Failure to load an otherwise valid source artifact is an evaluator error, not a
candidate citation failure. Preserve the distinction in saved statuses.

Check clean abstention first: a valid abstention has no points to ground. A
substantive answer with no support is not an abstention and fails the support
requirement. Neither case requires an empty-evidence G call.

Supporting points and factual qualifications use the same call and rule. Supply
only the current point's original text and its own cited evidence, plus the question.
Do not attach another point, qualification or conclusion as interpretive context.
Any conditions needed for a point to be supported must be expressed in that point.
Eligibility is defined before predictions; nonfactual exclusions retain reasons.
Optional-context metadata cannot shelter an essential factual premise.

Task 12 owns aggregation/reporting. These rules replace neither S/C policy nor
historical grounding contracts. No re-review, filtering or prediction forwarding.
