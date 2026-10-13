# Task 09E.1 local Clef qualification

Status: **blocked before inference**, inspected October 11, 2026. No model
download, runtime upgrade, tiny inference fixture or Dev3 inference was run.

## Local observations

The installed executable is `/opt/homebrew/bin/ollama`, client version `0.40.2`.
Neither `ollama list` nor the loopback `/api/version` request could reach a
server on port 11434. Local model manifests contain Qwen, Gemma, Nemotron and
Ornith assets but no `clef-flash` asset. Consequently no Clef digest,
quantization, actual download size or loaded context has been measured.

The [Ollama model page](https://ollama.com/library/clef-flash) advertises Apache
2.0, a roughly 11–12 GB model and minimum Ollama 0.35.1. Its table advertises
256K while its prose advertises 64K. Neither is qualification of this machine's
loaded decision context. We did not download weights merely to bypass a missing
counter or the independently established request-size blocker.

## Exact endpoint and blockers

The [System One reference](https://docs.ollama.com/api/systemone) defines local
GGUF scoring through `/v1/systemone`, typed questions and post-call token usage.
It documents no truncation, a 64 KiB text-request ceiling and unsupported
generation controls. Safetensors/MLX assets do not qualify this endpoint.

The [0.40.2 handler](https://github.com/ollama/ollama/blob/v0.40.2/server/routes.go)
enforces the text-and-schema byte ceiling before scheduling, then compiles and
scores against the loaded runner context. Its route table exposes no public
decision count-only endpoint. The [Clef compiler](https://github.com/ollama/ollama/blob/v0.40.2/decision/clef.go)
constructs separate state, question and option segments with explicit special
tokens. An exact local counter would need matching GGUF tokenization and the
runtime's segment handling; concatenated chat counting is not an accepted
replacement. No such counter has been qualified here.

The unchanged Dev3 point projections alone contain **20 of 166 point requests
over 65,536 bytes**, even with compact UTF-8 JSON, before adding model/question
fields. The largest is **89,947 bytes**. This proves that the direct lossless
state mapping cannot cover the whole panel under the current endpoint ceiling.
Do not trim source evidence, split original points, or weaken preflight to make
them fit. The final renderer audit may additionally reject other requests.

These are independent blockers: absent exact decision preflight; and an endpoint
byte limit incompatible with some unchanged stage inputs. The stopped daemon and
missing model are setup observations, not the sole reason for stopping. No
claim of runtime no-truncation parity or model quality follows from documentation.

## Frozen input checks

Verified SHA-256 and byte sizes against `task09e_final_result.json`:

| Binding | SHA-256 |
| --- | --- |
| Combined 09A.3 panel manifest | `409c1f6d3bacd338da321727efaa623fefde56bd4bf76167b96264240a6d17ab` |
| Qwen 9B comparison checkpoint | `5787da03e270c01b2294bba95e355afc7c3d410f82564aa3ccda37524cd4b9d8` |
| Qwen 9B completion | `d2c151f23fb46e53c9178de437f594c0445c202466e3ad75cb51394313596e03` |
| Frozen packet container | `78b9f693d2e031375b8ea2b44b92f1a409c792f80bc0c3df7da71b6cbebcdce2` |

Also verified the manifest's source-result, namespace-completion, answers and
record-origin bindings. Dev3 selects exactly **69 IDs**: C041 22, C037 27,
C014 20. Its 166 original non-conclusion points imply an upper bound of **304
stage calls** without retries: 69 gates, 166 point checks and 69 conclusions.
Clean abstentions and stage errors can reduce actual dispatches. No expectations
were used in these counts. No reserved answer or test question/reference payload
was read. Existing artifacts were not changed.

## Requirements for a future local attempt

First resolve the exact counter and endpoint-size incompatibility within an
accepted contract; changing data visibility is not authorized by this task.
Then pin the one Clef model's digest, GGUF quantization, tokenizer, license and
download bytes; start the existing runtime with explicit context settings; prove
invented-fixture count parity against `usage.input_tokens`, special-token and
segment handling, and over-limit rejection without truncation. Only then may a
finite, serial, single Dev3 trial run through Inspect, with partial progress
retained and errors excluded from numeric scores.

The [native response type](https://github.com/ollama/ollama/blob/v0.40.2/decision/types.go)
also defines optional `prompt_eval_cached_count`. Preserve it if present, but do
not infer a cache hit from latency or from this field's existence. No local cache
measurement was made.
