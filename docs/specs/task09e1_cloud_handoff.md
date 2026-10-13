# Task 09E.1 cloud handoff

No cloud authentication, counting, generation, Decisions request or cache probe ran
in the implementation session. Clef also made no inference calls or downloads.
The seven offline wire paths are implemented; only OpenAI Responses has an
identified exact counting endpoint that can qualify at runtime with credentials.
Other conditions remain blocked by the counter gaps in
[provider research](task09e1_provider_research.md). Keys do not remove those gaps.

## Setup and offline preparation

Use the existing `uv` environment from the repository root. No SDK installation,
new dependency, model download or runtime upgrade is required for preparation.
The local untracked `.env` must retain `ER_COMMONS_DATA_ROOT=/Volumes/x10pro/er_commons`.
Use a fresh output directory for each invocation. The CLI refuses an existing
live namespace so a restart cannot reset spending or wall-clock limits.

```sh
cd /Users/kyledorman/Documents/er_commons
export TASK09E1_ROOT=/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09e1_cloud_session_v1
make prepare-grounding-comparison GROUNDING_COMPARISON_OUTPUT="$TASK09E1_ROOT/readiness"
```

Preparation verifies the exact historical panel hash, original answer records,
origins and sources, without loading expectations. It writes rendered requests,
per-condition prefix/limit/cost audits and a sealed experiment manifest. Conclusion
requests in this audit use labeled synthetic all-false/all-true observations;
actual execution replaces them with the model's validated binary predictions.

## Credentials and access

These names are read only immediately before dispatch. Store keys in your shell
or secret manager, never in tracked JSON or command arguments. For example, in zsh:

```sh
read -rs 'OPENAI_API_KEY?OpenAI API key: '
export OPENAI_API_KEY
```

Use the same silent pattern for `ANTHROPIC_API_KEY`, `FIREWORKS_API_KEY` and
`TYPESAFE_API_KEY` when those conditions become qualified. Neither the runner nor
receipts persist authorization headers. Invalid credentials report the HTTP status
without response bodies or raw exception text. No alternate model is tried.

| Selection | Exact model | Current inference gate |
| --- | --- | --- |
| `openai_generation` | `gpt-6-luna`, Responses | Key/access, exact `/responses/input_tokens` response, limits and positive caps |
| `anthropic_generation` | `claude-haiku-5-5` | Published count endpoint is an estimate; exact qualification missing |
| `fireworks_glm` | `accounts/fireworks/models/glm-5p3-flash` | Exact full-request counter missing |
| `fireworks_deepseek` | `accounts/fireworks/models/deepseek-v4p1-flash` | Exact full-request counter missing |
| `openai_decisions` | `gpt-6-luna`, Decisions | Exact decision counter and endpoint context limit missing |
| `typesafe_jev` | `jev-1.13.0` | Exact counter for both total and state-plus-longest-question limits missing |
| `local_clef` | `clef-flash`, local System One | Exact counter, pinned assets and lossless request-size qualification missing |

The OpenAI counting call is authoritative preflight, not a paid model sample.
Its rendered model/input/schema/reasoning identity is saved and compared with
native usage. The first authorized smoke establishes account access and checks
parity; a mismatch halts subsequent calls. Missing exact counters cannot be
replaced by uploaded count receipts or chat token estimates.

## Deliberate cloud commands

The following commands **make paid calls when their gates pass**. Their numeric
caps are explicit examples, not a statement of expected spend. Increase a cap
only deliberately; partial results are retained when it is reached.

Start with one answer-only protocol smoke outside evaluation denominators:

```sh
make compare-grounding-cloud GROUNDING_COMPARISON_MODE=smoke \
  GROUNDING_COMPARISON_CONDITION=openai_generation \
  GROUNDING_COMPARISON_OUTPUT="$TASK09E1_ROOT/openai_smoke" \
  GROUNDING_CURRENCY_CAP=0.10 GROUNDING_REQUEST_CAP=1 \
  GROUNDING_OUTPUT_CAP=4096 GROUNDING_WALL_SECONDS=120
```

Then a separate three-call cache probe: original point, identical repeat, and a
second original point sharing its evidence prefix. No artificial padding or
unrelated evidence is added. A first call is not assumed cold.

```sh
make compare-grounding-cloud GROUNDING_COMPARISON_MODE=cache \
  GROUNDING_COMPARISON_CONDITION=openai_generation \
  GROUNDING_COMPARISON_OUTPUT="$TASK09E1_ROOT/openai_cache" \
  GROUNDING_CURRENCY_CAP=0.25 GROUNDING_REQUEST_CAP=3 \
  GROUNDING_OUTPUT_CAP=12288 GROUNDING_WALL_SECONDS=300
```

Finally, one complete 69-answer Dev3 attempt, at most 304 stage calls:

```sh
make compare-grounding-cloud GROUNDING_COMPARISON_MODE=run \
  GROUNDING_COMPARISON_CONDITION=openai_generation \
  GROUNDING_COMPARISON_OUTPUT="$TASK09E1_ROOT/openai_dev3" \
  GROUNDING_CURRENCY_CAP=2.00 GROUNDING_REQUEST_CAP=304 \
  GROUNDING_OUTPUT_CAP=1245184 GROUNDING_WALL_SECONDS=7200
```

For one other condition, replace the selection and use a different output root;
current counter blockers produce unscored records without inference. To select
all six cloud conditions deliberately, use `GROUNDING_COMPARISON_CONDITION=all-cloud`.
The same currency/request/output/wall budget is shared across all selections,
not multiplied silently. A full graph across six conditions has at most 1,824
stage calls and 4,980,736 generation output tokens; decision endpoints have zero
generation-output reserve. Their separate context constraints still apply.
There are no automatic retries. Counting calls are separate from the inference
request cap and stop when the inference cap is exhausted.

## Receipts, caching and recovery

Each run saves `manifest.json`, condition-specific `inspect/*.eval`, immutable
`requests/*/*/{intent,request,response,completion}.json`, per-sample result files,
and `summary.json`. Full runs add `analysis.json` only after Inspect returns;
that operation alone reads proposed expectations. Probes remain outside judge
coverage and comparison denominators. Native usage includes cache reads/writes
where exposed; `summary.json` preserves those measurements and a conservative
measured-token cost bound even when the semantic decision fails. Missing fields remain unknown, never inferred from latency.

Worst-case cost is reserved before dispatch, including cache-write premiums and
all output/reasoning allowance. Reservations remain spent for uncertain network
outcomes; no charge refund is assumed. Billed figures require the provider invoice.
OpenAI currently uses implicit cache controls; a shared prefix inside one user
message is not automatically an eligible write breakpoint. The offline audit
gives full-context spending ceilings, not expected Dev3 costs;
exact input totals and cache savings remain unavailable without qualified counts.

Identity-checked saved-receipt reuse is tested separately from provider caching.
The live CLI deliberately refuses resume into an existing run: inspect partial
results and uncertain intents before starting another explicitly budgeted namespace.
It does not silently replay interrupted calls or hide semantic failures with retries.
A cold/warm probe records its original response receipts even if a semantic
validation fails. No judge is qualified by these integrations or synthetic proposals.
