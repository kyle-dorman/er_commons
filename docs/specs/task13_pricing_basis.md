# Task 13 pricing and counting preflight

Verified 2026-10-20 against official documentation and read-only account model
metadata. No generation or token-count requests were made for this check.

## Frozen identities and current rates

The 11E targets are `gpt-6-luna` (medium reasoning) and `claude-haiku-5-5`
(adaptive thinking, medium effort). The 09G judges use Luna for A/G/C and Haiku
for S. Authenticated model-metadata GET requests returned HTTP 200 and those exact
IDs for both accounts. Metadata did not expose billing rates or count-call fees.

| USD per million tokens | Luna | Haiku, input ≤100,000 |
| --- | --- | --- |
| Ordinary input | 0.10 | 0.10 |
| Cached read | 0.01 | 0.01 |
| Default cache write | 0.125 (30 minutes) | 0.125 (5 minutes) |
| Output, including reasoning | 0.50 | 0.50 |

Sources: [Luna model](https://developers.openai.com/api/docs/models/gpt-6-luna),
[OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching),
[Haiku model](https://platform.claude.com/docs/en/models/haiku-5-5/overview),
[Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
Longer cache lifetimes and regional processing have premiums. Preserve and
validate the frozen request settings; do not introduce either option.
Haiku input over 100,000 tokens, including cached input, has higher rates.

## Counting fee gate

[Anthropic token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)
explicitly states that counting is free. Calls still consume the shared remote
concurrency and count-call allowance.

The [OpenAI counting guide](https://developers.openai.com/api/docs/guides/token-counting)
and [pricing page](https://developers.openai.com/api/docs/pricing) inspected on
this date do not establish a fee or free status for `/v1/responses/input_tokens`.
The model-metadata response does not resolve this. **The remote OpenAI counting
fee remains unverified.** A guessed per-call allowance does not establish a
maximum liability. The previous development accounting allowance is not evidence
of the endpoint's price.

**User exception, 2026-10-20:** the user explicitly accepts possible OpenAI
counting charges and says this uncertainty should not block the run. An
authoritative fee bound is therefore no longer a prerequisite for this endpoint.
Keep its actual fee unverified and disclose the accepted assumption in accounting;
do not label it provider-confirmed free. The $10 budget and all other limits remain
unchanged. Execution now records `user_accepted_unknown_openai_count_fee`, a zero
planning allowance and a null actual charge. The zero allowance is the accepted
planning assumption, not a price or a guarantee about unobserved fees. These count
requests remain included in request limits and the shared concurrency gate, and
are separately listed in accounting. The original blocked preflight stays sealed;
a fresh preflight and independent review bind this explicit exception.

## Admission and reconciliation basis

Provider counts can differ from actual billed usage. Reserving only the planned
100,000 input-token limit is insufficient if a provider returns unexpectedly
larger effective usage. Reserve the model's full documented input/context ceiling
at its highest applicable long-context/default-cache rate, plus the capped output.
The request still must pass the 100,000 input-token admission check; this larger
liability reserve protects against count/usage mismatch rather than expanding the
benchmark's input allowance.

| Provider | Worst input tokens | Reserved input USD/M | Reserved output USD/M | Target reserve | Judge reserve |
| --- | --- | --- | --- | --- | --- |
| OpenAI Luna | 1,050,000 | 0.25 | 0.75 | 0.271716 | 0.265572 |
| Anthropic Haiku | 1,000,000 | 0.625 | 2.50 | 0.655720 | 0.635240 |

Luna's model page documents a 1,050,000 context window and, above 272,000 input
tokens, 2× input/cache rates and 1.5× output rates. Haiku's pricing page documents
5× input/cache/output rates above 100,000 total input tokens; its model metadata
reports a 1,000,000 maximum input. These bounds assume the frozen standard/global
requests and default cache lifetime. Even ten simultaneous worst-case Haiku target
reservations fit below $10 before settled expenditure; later admission always
includes settled charges and unresolved reservations. This does not resolve the
unknown OpenAI counting fee.

Release unused liability only after trustworthy usage reconciliation. Preserve
the full reservation for uncertain transport outcomes, missing/malformed usage
or interrupted requests; never replay them automatically. OpenAI ordinary input
is total input minus read and write tokens. Anthropic's ordinary, cache-read and
cache-creation counts are separate. Do not double count cache writes or reasoning
tokens. Any usage violating admitted bounds stops further dispatch.

Provider counters are estimates where documented; strict input validation must
account for effective request overhead and reject unknown native fields.
The concurrency semaphore must be held only for an individual wire request:
an outer generation hook awaiting a counter must not hold it and deadlock all
ten permits. Persist admission before the request can reach the wire.
