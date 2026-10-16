# Inspect-native adequacy execution

The maintained new execution path is `er_commons.adequacy_inspect`, using
Inspect 0.3.278's OpenAI, Anthropic and Fireworks providers. It keeps the existing
C v8 and S v6 policies, projections, strict parser and independent quotation
checks. It does not alter prior results or resume the interrupted comparison.

## Accepted selection

09F is complete. Default C uses Luna; default S uses Haiku, as locked in
[adequacy_selected_v1.json](../../configs/adequacy_selected_v1.json).
Omit `condition_id` to use this selection. The [final handoff](task09f_final_result.json)
records evidence and limitations. Explicit overrides do not alter the locked pair.

## Ownership

Inspect owns generation, SDK transport, connection management, backoff, retries,
concurrency, epochs, evaluation logs and task resumption. Project code supplies
sealed development samples, exact prompts, provider configuration and scoring.
There is no new transport loop, scheduler, retry library or budget framework.
Historical direct-HTTP modules remain for existing consumers and receipt replay;
they are not the recommended entry point for new adequacy evaluations.

## Controls

| Concern | Selected control |
| --- | --- |
| Models | Fixed existing Luna, Haiku and GLM IDs from `adequacy_binary_models_v2.json` |
| Output | 4,096 tokens; strict local validation; native schema for Luna/Haiku |
| GLM format | Existing prompt-only schema contract, preserving reasoning |
| Request recovery | Inspect `max_retries=2`, `timeout=120`, `attempt_timeout=45` |
| SDK recovery | Disabled for OpenAI/Anthropic; Fireworks native SDK retains two retries |
| Concurrency | Four static connections; explicit sample concurrency at invocation |
| Whole-sample retries | Disabled for ordinary execution; never reroll invalid judgments |
| Sample duration | 150 seconds |
| Repetition | Inspect epochs; response-result caching disabled |
| Prompt caching | Luna provider-default retention with stable key; Haiku system prefix 5 minutes; stable Fireworks affinity |
| Cost reporting | Existing dated provider/cache rates registered with Inspect |
| Cost limit | Inspect per-sample limit; not a hard aggregate invoice ceiling |
| Logging | Full model API logging, sample scores and raw output/quotation diagnostics |

Fireworks has two retry layers: up to three SDK attempts per Inspect attempt,
with up to three Inspect attempts. OpenAI/Anthropic have only Inspect's three
attempts. Timeouts may terminate sooner. Connection-establishment retries are
separate from generation requests. A failed request may incur an unknown charge.

## Explicitly changed guarantees

- No custom exact full-request counting gate before generation. Actual returned
  token/cache usage remains available. Inspect's optional `count_tokens` methods
  are not claimed to include every generation schema/config field identically.
- No durable custom intent/reservation transaction before each HTTP attempt and
  no cumulative worst-case dollar ledger. Inspect records request/retry events;
  missing-response billing remains unknown. Fireworks SDK-internal retries do not
  provide a separate project receipt for every underlying HTTP attempt.
- No promise of byte-identical provider requests or identical cache routing to
  the legacy executor. Native provider defaults and serialization are checked
  in offline fixtures and the integration smoke test; these are new execution
  conditions, not a silent continuation of historical five-pass results.
- Malformed/truncated outputs are recorded as invalid; truncation no longer
  triggers the legacy execution halt. There is no exact returned-model-name
  equality gate. Per-sample cost limits can overshoot by the in-flight generation.
- Inspect evaluation logs replace the custom receipt-directory layout for new
  runs. Existing logs and receipts remain untouched.

Inspect does not expose the historical OpenAI `prompt_cache_options` 30-minute
TTL. The new path uses a stable native `prompt_cache_key` and provider-default
retention, with actual cache reads checked in the live smoke. No custom adapter
patch is added solely to reproduce that option.

Native serialization uses OpenAI Responses `text.format` and Anthropic
`output_format` with Inspect’s structured-output beta header. Anthropic also
adds its native thinking block-binding setting. These preserve the strict schema
meaning but differ from the historical wire format. Explicit cache breakpoints
keep Haiku caching on the system prefix; disabling OpenAI reasoning summaries
avoids an unsolicited capability-probe generation.

## Standard entry point

From the repository, load credentials/root via the existing `.env`. Choose a
fresh external log directory. This example is a command template, not permission
to run a new evaluation:

```bash
uv run inspect eval src/er_commons/adequacy_inspect.py@adequacy \
  -T condition_id=openai_generation -T component=C -T panel=calibration \
  --epochs 5 --max-samples 4 --retry-on-error 0 \
  --cost-limit 0.10 --log-model-api \
  --log-dir "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/NEW_RUN"
```

Use `anthropic_generation` or `fireworks_glm` for the other provider profiles;
`component=S` uses unchanged reference-blind support. `panel=full_development`
explicitly selects the published development sets. Fireworks integration support
does not restore GLM to adequacy model selection. Use Inspect's normal log tools
and `eval-retry` after inspecting failed samples; do not silently rerun completed
judgments or mix transport versions in one stability result.

The shell does not inherit variables from Inspect's later `.env` loading. Set
`ER_COMMONS_DATA_ROOT` in the shell before using the example's expansion, or pass
the verified external directory explicitly; never print credential values.

## Options review

The complete [Inspect Options reference](https://inspect.aisi.org.uk/options.html)
was read: environment/run configuration, provider/generation parameters, task
and solver overrides, sample selection, parallelism, errors/limits, logs,
scoring, sandboxes, debugging and miscellaneous controls. Only controls useful to
one-generation C/S judging are selected above. There are no tools, sandboxes,
agent loops, fallback models or custom hooks in this first integration.

[Hooks](https://inspect.aisi.org.uk/extensions-hooks.html) can add per-attempt
policy later if a concrete need survives the native controls. Rebuilding the
old ledger in hooks would defeat this change's maintenance goal.
[Concurrency/retries](https://inspect.aisi.org.uk/models-concurrency.html) and
[API logging](https://inspect.aisi.org.uk/eval-logs.html) describe Inspect-owned
recovery and diagnostics. Installed provider code is authoritative when the
options table omits newer provider capabilities.

## Verified integration result

The [result pointer](task09f_inspect_native_result.json) records 12 successful
invented-input calls. All six repeated C/S requests reported provider cache reads
with fresh request IDs; response caching was disabled. Estimated total cost was
USD0.002562035. Native tests passed 21/21; full validation passed 4,694 tests with
one skip. These checks establish integration and cache behavior, not accuracy.
