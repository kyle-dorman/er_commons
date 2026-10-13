# Task 09E.1 provider research

Verified October 11, 2026 against the primary pages below. Documentation establishes
public capability, not this account's access. No authenticated requests or paid
calls were made. Exact requested identities are retained; none is substituted.

## Provider mapping and limits

| Condition | Endpoint and model | Credentials | Documented limits / qualification |
| --- | --- | --- | --- |
| OpenAI generation | `https://api.openai.com/v1/responses`, `gpt-6-luna` | `OPENAI_API_KEY` | 1,050,000 context, 128,000 maximum output; exact authoritative Responses counter exists, needs credentials and render binding |
| Anthropic generation | `https://api.anthropic.com/v1/messages`, `claude-haiku-5-5` | `ANTHROPIC_API_KEY` | 1M context, 128K output; counting endpoint is explicitly an estimate, exact qualification remains blocked |
| Fireworks GLM | `https://api.fireworks.ai/inference/v1/chat/completions`, `accounts/fireworks/models/glm-5p3-flash` | `FIREWORKS_API_KEY` | 1040k served context; no qualified exact request counter established |
| Fireworks DeepSeek | Same chat endpoint, `accounts/fireworks/models/deepseek-v4p1-flash` | `FIREWORKS_API_KEY` | 1040k served context; no qualified exact request counter established |
| OpenAI Decisions | `https://api.openai.com/v1/decisions`, `gpt-6-luna` | `OPENAI_API_KEY` | Responses counting does not establish decision-request counting; exact question overhead and endpoint limits need qualification |
| TypeSafe | `https://api.typesafe.ai/v1/systemone`, `jev-1.13.0` | `TYPESAFE_API_KEY` | 64K state plus all questions, AND 32K state plus longest question; exact renderer/counter not established |
| Clef local | `http://localhost:11434/v1/systemone`, `clef-flash` with digest pinned before execution | None | Matching GGUF/scoring runner; model page requires Ollama 0.35.1; text-only JSON body ≤64 KiB; context/counter need actual runtime qualification |

Sources: [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Haiku](https://platform.claude.com/docs/en/models/haiku-5-5/overview),
[GLM](https://fireworks.ai/models/fireworks/glm-5p3-flash),
[DeepSeek](https://fireworks.ai/models/deepseek-ai/deepseek-v4p1-flash),
[Jev](https://docs.typesafe.ai/models),
[Clef](https://ollama.com/library/clef-flash),
[Ollama API](https://docs.ollama.com/api/systemone).

The Clef listing advertises 256K while its prose says 64K; neither resolves the
loaded runtime context. Ollama states that oversized input is never truncated.
Its endpoint does not accept generation controls. Do not send `max_tokens`,
`temperature`, or a Qwen chat template as an attempted decision configuration.
A body-size check is additional to token preflight, not a replacement.

## Installed integration and request contracts

Local inspection found Inspect 0.3.278, httpx 0.28.1 and tiktoken 0.14.0.
OpenAI, Anthropic, Ollama Python, and TypeSafe SDK distributions were not installed
at research time. Inspect includes OpenAI Responses, Anthropic and Fireworks
provider source. Prefer those maintained providers where their exact rendered
request can be audited; use a narrow native decision ModelAPI adapter for the
other endpoint shapes. Keep Inspect scheduling and receipts.
[Inspect provider guidance](https://inspect.aisi.org.uk/providers.html).

Generation outputs still require project validation:

- OpenAI: Responses `text.format` JSON schema; `reasoning.effort` supports none,
  low, medium, high, xhigh, max. Pin the selected value and reserve all output,
  including invisible reasoning tokens. The wire schema removes defaults, turns
  constants into singleton enums, and requires all diagnostic fields with empty
  strings/lists permitted; this satisfies strict decoding without making
  quotations semantically mandatory. Truncation is explicitly disabled.
- Haiku: `output_config.format` JSON schema. Adaptive thinking is default;
  explicitly freeze effort and omit temperature/top_p/top_k. SDK schema
  simplification is a transformation to record and locally revalidate. Structured
  format injects extra input instructions and changing it invalidates caching.
  [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).
- Fireworks: `response_format.type=json_schema`; include the schema in prompt
  text too because constrained decoding alone does not show it to the model.
  Documentation says this mode disables reasoning output. Record this as an
  endpoint-specific difference; don't silently remove structured mode to recover
  reasoning. [Structured responses](https://docs.fireworks.ai/structured-responses/structured-response-formatting).

OpenAI Decisions uses `input` plus an ordered `questions` array. Binary questions
are `type=predicate`, with `name` and `instructions`; answers carry matching name,
`type=predicate`, and `probability`, or `type=refusal`. TypeSafe/Clef use `state`
plus a question-ID mapping, `type=noul`, instructions, and optional true/false
criteria; answers are a matching mapping with `type=noul` and numeric `noul`.
Neither needs generated explanations. Reject duplicate/missing names, nonfinite
or out-of-range probabilities, wrong types and refusals. Project recommendation:
freeze p>0.5 as true, p<0.5 as false, exact tie as unscored; never tune on Dev3.
[Decisions](https://developers.openai.com/api/docs/guides/decisions),
[TypeSafe API](https://docs.typesafe.ai/api).

## Exact counting blockers

OpenAI documents `POST /v1/responses/input_tokens` as exact, including role and
boundary overhead. Bind its response to the complete rendered generation input,
schema, reasoning configuration, model and counter request. Compare native usage
when later authorized. This does not authorize counting Decisions with a chat or
Responses tokenizer. [Counting](https://developers.openai.com/api/docs/guides/token-counting).

Anthropic `POST /v1/messages/count_tokens` is free, but explicitly documented as
an estimate that can differ from generation usage; system-added tokens further
complicate billing parity. It can support diagnostics, not a falsely labeled
exact counter. [Counting](https://platform.claude.com/docs/en/build-with-claude/token-counting).

The reviewed [Fireworks index](https://docs.fireworks.ai/llms.txt),
[TypeSafe index](https://docs.typesafe.ai/llms.txt), Decisions guide and Ollama
System One API did not establish an authoritative exact preflight endpoint for
these request shapes. This is a researched qualification gap, not a claim that
none could exist. Qualified model assets must reproduce the actual renderer and
all overhead; text tokenization alone is insufficient. Preserve blocked status
until evidence resolves this. No weaker fallback is proposed.

## Dated pricing and cache policy

USD per million tokens, standard global processing; source model pages above.

| Condition | Ordinary input | Cache read | Cache write | Output |
| --- | ---: | ---: | ---: | ---: |
| Luna Responses | 0.10 | 0.01 | 0.125 | 0.50 |
| Haiku ≤100K input | 0.10 | 0.01 | 0.125 (5m), 0.20 (1h) | 0.50 |
| Haiku >100K input | 0.50 | 0.05 | 0.625 (5m), 1.00 (1h) | 2.50 |
| Fireworks GLM | 0.15 | 0.03 | Ordinary rate; no separate surcharge established | 0.50 |
| Fireworks DeepSeek | 0.30 | 0.006 | Ordinary rate; no separate surcharge established | 1.20 |
| Luna Decisions | 0.10 | No cache charge | No cache charge | 0 |
| Jev | 0.042 | No discount established | No separate rate established | 0 |
| Clef local | No API fee | Not established | Not established | No API fee |

Luna Responses above 272K input doubles input/cache rates and multiplies output
by 1.5; regional processing adds 10%. Decisions documents regional and long-input
multipliers too. Do not apply the ordinary rate blindly. Jev pricing is input-only.

Luna Responses uses the GPT-5.6+ policy: minimum 1,024 visible input tokens,
`prompt_cache_options.ttl="30m"`, implicit or explicit breakpoints, four writes
maximum. Explicit mode without breakpoints avoids cache writes. Usage fields are
`input_tokens_details.cached_tokens` and `cache_write_tokens`; ordinary input is
total minus both. Write pricing replaces ordinary input pricing rather than adding
to it. Schema and reasoning changes can change the prefix. Do not reuse older
`prompt_cache_retention` policies. Decisions caching savings and receipt fields
are not established by this generation guide.
[OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching).

Haiku's minimum is 512 tokens. Explicit ephemeral breakpoints support 5m or 1h;
cache hits refresh lifetime. Total input equals `input_tokens` plus
`cache_read_input_tokens` plus `cache_creation_input_tokens`. Retain creation's
5m/1h breakdown. [Anthropic caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

Fireworks caching is automatic and replica-local. Stable session affinity improves
routing; a cache-isolation key supports controlled probes. Lifetime varies from
minutes to hours; no guaranteed TTL or minimum threshold was established. Dedicated
receipt headers include `fireworks-cached-prompt-tokens`; serverless evidence must
be verified from its actual receipt, never inferred from latency. Use model rates,
not the guide's generic 50% discount.
[Fireworks caching](https://docs.fireworks.ai/guides/prompt-caching).

## Measurement recommendations

Audit common prefixes from actual rendered Dev3 requests, separately by model,
stage, schema and allowed evidence. Report byte lengths when token qualification
is missing; do not call them exact token lengths. Put stable instructions and
shared evidence before varying claims without adding unrelated evidence. Keep
provider cache reuse distinct from identity-checked saved-result reuse.

For input I, reusable R, output O, ordinary rate P, write W, read C and output Q:
no-cache cost is `(I*P+O*Q)/1e6`; a cold write is
`((I-R)*P+R*W+O*Q)/1e6`; warm reuse substitutes C for W. Use zero assumed savings
for unknown cache behavior. Reserve the largest applicable rate and full output
cap for every allowed attempt before dispatch. Separate later cache probes from
69-answer denominators. Missing usage or uncertain transport leaves the reserved
cost unreleased until reconciled. These formulas are estimates, not billed totals.

The [Responses count API reference](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count)
explicitly accepts text-format/schema and reasoning settings. The counting request
retains these, model/input and disabled truncation; it removes storage, output cap
and cache-control settings that do not change input token content.
