# Task 09F simple adequacy baseline v1

This specification owns the first independent adequacy prompt and result boundary.
The [09F contract](../../tasks/sprint2/09f_implement_adequacy_judge.md) owns execution
scope: a fixed three-question development checkpoint, then user review before
expansion, prompt changes or optional experiments.

This preserves the historical v1 contract. The current selected development
configuration uses consolidated v4 and partial-credit v2; see the
[maintainer guide](../adequacy_judge_guide.md#selected-development-configuration)
for those versioned changes and replay instructions.

## Input and rubric

`adequacy_judge.py` consumes integrity-checked 09C adequacy packets. Only question,
structured candidate answer, approved reference and complete permitted source units
cross the model boundary. Expectations, raw variant identities, provenance, official
responses and grounding results remain outside the call. Required missing reference
evidence is a packet failure. Unknown candidate citations remain explicitly unresolved.

The independent whole-answer score is 2 for correct, direct and complete essential
substance; 1 for a correct conclusion missing essential explanation, condition or
question component; and 0 for unanswered, incorrect or materially misframed central
questions. Clean abstentions are numeric zero. Equivalent paraphrases, different
point organization, omitted optional context and supported alternative arguments
remain eligible. The judge reports suspected reference gaps without editing the
reference or automatically granting credit.

## Prompt, output and validation

`task09f.adequacy.v1` starts with the simple rubric and concise diagnostics. Its
strict JSON result has required `score`, `clean_abstention`, `rationale`,
`missing_essentials`, `issues` and `reference_limitations` fields. Empty diagnostic
lists are valid; exhaustive reference-point reviews and equal point counts are not
required. The prompt includes positive and empty-abstention format examples.

A missing-essential entry has `reference_point_ids`, `citation_ids` and
`explanation`. An issue also has `candidate_point_ids`. Each ID list is unique and
must resolve within its own namespace; source IDs must identify supplied resolved
source text. Empty links require an explanation of the reference or evidence gap.
Diagnostic prose is not executable or a verified chain of reasoning. Local validation
checks structure, ID membership, nonblank explanations, duplicate JSON keys and
limited score invariants. Score 1 requires a missing essential, score 2 cannot have
one, and clean abstention requires score 0. Errors remain non-scores. These checks
cannot establish that an explanation or semantic judgment is correct.

## Stable prefix and identity

09C normally assigns citation IDs in candidate order. The adequacy adapter sorts
complete resolved source identities, remaps source links in both answers, and
preserves every source byte and attachment. It never changes the original packet.
Unresolved candidate markers follow resolved sources. Requests place evidence,
question and reference before the varying candidate. Unresolved marker differences
can still reduce a shared prefix; provider cache counters must establish actual
reuse. IDs in saved results refer to the prepared payload saved with the request.

The maintained Fireworks renderer supplies the selected GLM provider settings.
The cache routing key includes adequacy dimension, model, prompt, evidence,
question and reference. Complete request hashes also bind candidate, schema and
settings. Neither a shared computation prefix nor receipt reuse crosses the
independent grounding/adequacy result boundary. Actual caching, native usage and
cost must be measured before the authorized panel evaluation.

## Learning and limits

[Inspect model grading](https://inspect.aisi.org.uk/model-graded.html) supports
custom scorers, but framework defaults do not select or calibrate this project's
rubric. Reference similarity, JSON validity and substantive adequacy are separate
properties. [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
motivates inspecting grader outcomes and disagreements rather than trusting an
aggregate or plausible explanation. Synthetic expectations are development
proposals, not independent human calibration. Stable-prefix layout follows the
provider's [prompt caching guidance](https://docs.fireworks.ai/guides/prompt-caching):
static material precedes dynamic material, with no assumption that an identical
routing key guarantees a measured hit.

Invented offline fixtures establish contract behavior for complete paraphrases,
combined points, alternative arguments, essential omissions, incorrect conclusions,
neighboring-question answers and abstention. They do not measure model accuracy.
The live checkpoint must report fixed-class, failure-inclusive metrics, per-question
failures and any unavailable alternative-argument coverage.
