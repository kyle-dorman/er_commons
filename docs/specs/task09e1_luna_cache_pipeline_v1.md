# Task 09E.1 — Luna cache repair and complete inconsistent-case experiment

The October 12 user request selects **Luna only for subsequent inference**,
authorizes the previously deferred cache repair, and requests a full pipeline
experiment on the inconsistent cases, including conclusion-prompt improvements.
Historical model runs and provider integrations remain preserved. No commits,
pushes, truncation, dataset expansion, Decisions or other-provider calls.

## Frozen scope and design

Use the eleven original Luna unresolved answers, identified by the prior sealed
`review_claims.json`, from the same frozen Dev3 panel. Each complete pass runs the
original gate, all 41 original point inputs, and a fresh conclusion with that
pass's actual binary predictions: at most 63 stages. No old predictions or saved
responses count as fresh observations. Preserve all evidence and source identity,
output contracts, fail-closed aggregation, and quotation/semantic separation.

First implement an opt-in evidence-prefix breakpoint for Luna Responses. The
point/conclusion user message becomes two text blocks, split after the ordered
evidence and question fields. Concatenated text must exactly match the previous
serialized payload. Mark the stable block with an explicit cache breakpoint;
retain implicit caching at the end for exact duplicates. Abstention rendering,
all default requests and output schemas remain unchanged. Optional cache keys
separate experimental cache accounting. The exact counter retains nested markers
and all actual input/schema/reasoning content while omitting top-level cache-only
controls. Count/native parity and model identity remain mandatory.

Cache qualification: two pairs of original point inputs from these eleven answers
with identical evidence/question/schema but different target suffixes. For each
pair, dispatch A, B, A under legacy and repaired layouts, with fresh layout/group
cache keys, identical medium reasoning and the prior combined point prompt.
Twelve calls maximum, $0.25 total reservation cap, 4,096 output tokens/call and
900 seconds for the phase. Report cold/warm status from native receipts; never
assume a fresh key guarantees a cold request. Require count parity, valid outputs,
exact payload reconstruction, and improved changed-suffix cache reads in both
pairs before using the repaired layout in the full experiment. If qualification
fails, preserve failures, diagnose offline, and do not silently relax gates.

Full pipeline: four frozen arms, each three independent repetitions in fresh
namespaces, medium reasoning, original gate, identical chosen cache layout:

| Arm | Point prompt | Conclusion prompt |
| --- | --- | --- |
| A | Original | Original |
| B | Original + prior combined addition | Original |
| C | Original + prior combined addition | Original + prior combined addition |
| D | Original + prior combined addition | Original + combined + conclusion-specific addition |

The conclusion-specific addition clarifies independent review of fallible earlier
predictions, attribution to each claim's own citations, scope preservation, and
explaining reversals without being instructed to agree. Freeze complete prompt
texts before dispatch. The prior combined addition already has point and
fixed-context conclusion evidence; this experiment newly tests fresh predictions
through the complete pipeline. Prompt changes cannot affect inference visibility
or load proposed labels into requests.

Each arm: at most 189 generations, 774,144 cumulative output-token reservations,
$1 reservation cap, and 3,600 seconds shared across all three repetitions.
Arms may run concurrently with independent caps; no cap is reset per repetition.
Total maximum: 768 generations and $4.25 reserved, including cache qualification.
Count/identity/truncation/budget failures halt the affected run; invalid outputs
remain unscored with no replacement or automatic retry. Structural failures in
cache qualification block pipeline dispatch. Preserve all negative results.

## Evaluation and decision rules

Report all eleven-answer denominators on every repetition, numeric coverage,
point/review disagreements, repeat stability, gate errors, native cache buckets,
latency, paid-payer metadata and rate-based costs. Reuse the prior frozen
source-review interpretations for clearer original claims; keep enforcement
ambiguity unadjudicated. Score agreement with synthetic proposals is a separate
postrun diagnostic. Inspect source explanations and citation ownership, including
regressions, before recommending any candidate.

An improvement needs higher numeric coverage without reduced agreement on any
clear diagnostic claim, new false abstentions or invalid outputs. Rank eligible
arms by clear-review agreement, numeric coverage, then repeat consistency; report
ties and do not infer qualification from three repetitions. No automatic default
prompt promotion. This suite was selected for prior failures and is not an
independent validation set. Stable but unsupported conclusions are not success.

## Evidence and validation

Fresh external namespace:
`task_09/09e1_20261012_luna_cache_pipeline_v1/`. Bind the selected packet identities,
prior result/completion pointers, prompts, cache probes, configurations and code
before calls. Load `.env` credentials only inside code; never print values.
Preserve native receipts and Inspect logs, independent code/design/results review,
postrun analysis and a completion inventory. Verify older sealed namespaces and
scan decoded logs for credentials. Run focused regression tests, `make fix`,
`make check`, and `git diff --check`; baseline has three historical Task 06G failures.

Official sources checked October 12:
[cache boundaries and schema sensitivity](https://developers.openai.com/api/docs/guides/prompt-caching),
[exact counter input-block markers](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count),
[reasoning prompting guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices).
Luna requires at least 1,024 visible prefix tokens for caching. Different schemas
can still break reuse, even with identical evidence. This repair deliberately
keeps schemas and semantic validation unchanged; measured savings may be partial.
