# Task15Y six-question pilot v1

The user approved the semantic contract, prompt/schema, families and execution
settings in chat on2026-10-23, then explicitly activated implementation, synthetic
authoring, independent review and Round1. Round2 remains gated on review.

## Semantic contract

One fixed required reference point is judged against the entire candidate
supporting-point list. Equivalent and distributed meaning counts; incomplete or
incompatible meaning and unresolved mixed conflicts are false. Material conditions,
exceptions and scope remain necessary. Different scenarios and explicitly rejected
claims are not automatically contradictions. Coverage is distinct from grounding,
conclusion adequacy and inference support; it never adds an overall pass requirement.

Only question, one canonical required point and candidate supporting IDs/text enter
the user payload. The frozen Baylands overview accompanies the general prompt.
Conclusions, source evidence, citation metadata, separate qualifications/context,
other reference points, expectations and judge verdicts are excluded.

Output is exactly `covered`, `supporting_point_ids`, `reason`. True requires a
sufficient nonempty supplied-ID witness set; false requires an empty list. Unknown
or duplicate IDs, malformed output and unavailable calls are operational non-decisions.
Witness sets need not be uniquely minimal. Reasons are brief explanations, not a
separately scored semantic target. False is reported as **support not covered**.

## Families and expectations

| Family | Expected | Semantic intervention |
| --- | --- | --- |
| complete | true | Complete coherent required meaning |
| paraphrase | true | Equivalent meaning in different words |
| distributed | true | Multiple aligned points jointly cover all material meaning |
| compatible_extra | true | Complete coverage plus compatible or unrelated content |
| redundant | true | Compatible repetition of complete coverage |
| distinguished_scenarios | true | Complete coverage plus clearly distinct scenario/time |
| explicit_correction | true | Incompatible claim explicitly rejected/corrected |
| omission | false | All required meaning removed; other support remains |
| empty | false | No candidate support |
| topic_only | false | Relevant vocabulary without required relationship |
| partial | false | One material clause/detail removed |
| distributed_gap | false | Indispensable contribution removed from distributed positive |
| incompatible | false | Materially incompatible assertion replaces coverage |
| mixed_conflict | false | Complete coverage plus unresolved target contradiction |
| invalid_combination | false | Fragments from incompatible contexts cannot establish target |

Every expectation needs semantic review; a mutation is not inherently negative.
Record inapplicable families rather than force artificial defects. Fixed questions
and references come from15AC; only candidate support changes. Retain source variant,
transformation, affected IDs, rationale and positive witnesses outside model inputs.
Surviving points preserve IDs. Review every positive and negative independently.
No separate paid synthetic-generation model calls are authorized.

## Execution and stopping

Use only C014/C017/C019/C037/C041/C056,10 required points. Target150 variants,
maximum180. Three judge repetitions; candidate variant identity is separate from
judge repetition. Luna `gpt-6-luna`, medium reasoning,4096 output tokens,16 concurrent
requests, default sampling, no response-result caching. Provider prompt caching is
allowed. Native timeout120, attempt timeout45, sample limit150 seconds; at most two
transport retries, no semantic rerolls. SDK retries stay disabled.

Round1 maximum540 judgment slots and $10 inclusive of retry/uncertain liabilities.
Two rounds together maximum1080 slots and $20; unused Round1 allowance does not
raise Round2's $10 cap. Round2 is not dispatched without review and agreement.
Verify official prices and actual native request settings before dispatch. Reserve
conservative costs before remote work, retaining unknown liabilities. A soft Inspect
cost limit alone does not enforce the task budget. Freeze the exact suite, prompt,
schema, code and manifest for the run; write outputs in a fresh external namespace.

First20 variants/60 slots cover every required point, both labels and distributed/
mixed-conflict controls. Pause for two or more operational failures or the same clear
rule failure on two distinct variants. Review the checkpoint before remaining slots.
Stop new dispatch immediately for isolation/identity defects, unsupported settings,
accounting failures, insufficient budget reservation, authentication or repeated
run-level failures. Already admitted calls drain and remain charged.

Review every error/invalid/repeat disagreement and correct controls from every family.
Report validity, sensitivity/specificity, confusion counts and three-valid-repeat
agreement overall and by question/point/family. Gates for proposing expansion are
98% valid,95% sensitivity,95% specificity,95% complete agreeing triples, and no
unresolved systematic distributed/material-omission/mixed-conflict error. These are
development review gates, not statistical reliability guarantees. Preserve frozen
labels and document disputes rather than relabeling after observing outputs.

## Research and learning

[Anthropic's evaluation guidance](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
supports focused criteria and calibration against reviewed expectations. Native
Inspect adapters already separate payloads from labels and preserve invalid outputs;
reuse them instead of introducing an evaluation framework. One reference point per
request localizes omissions and conflicts without conflating source grounding.

[Official Luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
was checked2026-10-23: medium reasoning is supported; standard short-context rates
are $0.10 input/$0.50 output/$0.01 cached-read/$0.125 cache-write per million tokens.
Pin effective service/cache settings and conservatively account for their rates.

This six-question suite is exposed development evidence. It cannot establish held-out
performance or authorize all19 expansion, all49 real diagnostics or production promotion.

## Authorized Round1 operational continuation

After the sealed checkpoint rejected in-memory caching, the user explicitly authorized
24h cache retention and continuation under the original $10 cap. The fresh linked
`round1_continue_v1` verifies the failed ancestor's complete seal, binds identical
synthetics/labels/references/prompt/schema, and allows only the runner implementation
to change. A create-only sibling successor claim prevents a second continuation.

The16 sent requests retain $0.076253 conservative liability. The remaining
$6.336904 reservation represents provably unsent attempts and is reassigned within
the same $6.413157 total reserve; it is neither new budget nor evidence of zero prior
billing. At most1334 further wire attempts remain from the original1350 ceiling.
The checkpoint uses at most one transport retry per new judgment to keep each
previously attempted slot within three total attempts; remainder retains two retries.
All three judge repetitions and16 concurrency remain unchanged. Review the corrected
checkpoint before remainder; stop beforeRound2. Preserve all original failures.

The retained provider response directly establishes its24h requirement. Current
[caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching)
uses newer retention terminology; the conservative $0.25/M input reservation covers
the documented extended-cache write rate. Report usage-based estimates separately
from provider billing and prior uncertain liabilities.
