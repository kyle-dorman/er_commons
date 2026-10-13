# Grounding judge maintainer guide

The maintained cloud profile is `configs/grounding_judges_v1.json`: GLM Flash is
the selected development judge, with Luna and Haiku alternatives. All three use
medium reasoning and their measured evidence-cache settings. The explicit GLM
conclusion override is `configs/grounding_glm_prompts_v1.json`; it adds only the
accepted empty-review clarification. The simple claims instructions are unchanged.
These are development choices, not calibrated judge qualification.

## Responsibilities

| Module | Owns |
| --- | --- |
| `grounding_records`, `grounding_metrics` | Pure sample contracts and diagnostic metrics |
| `grounding_stages`, `grounding_evidence` | Original point/evidence projection and shared source-text access |
| `grounding_comparison_prompts`, `grounding_comparison_semantics` | Frozen cloud instructions, semantic validation, quotation diagnostics and deterministic scoring |
| `grounding_provider_config`, `grounding_comparison_providers` | Validated provider settings, request rendering and native response/usage parsing |
| `grounding_comparison_safety` | Context qualification, decimal budgets and immutable attempt receipts |
| `grounding_comparison_inspect` | Inspect stage graph and bounded execution |
| `grounding_comparison_panel`, `grounding_comparison_analysis` | Label-blind development loading and separate post-run label analysis |
| `grounding_comparison_run`, `grounding_comparison_audit` | Maintained command and offline request audit |
| `grounding_native`, `grounding_stage_runtime`, legacy Inspect adapters | Retained Ollama diagnostics and small-Qwen integration tests |

Keep model inputs separate from restricted labels. Original claim checks see only
their own evidence and permitted context. Conclusions receive binary observations,
not earlier explanations. Invalid output is an error; it is never converted to a
negative judgment. Conflicting original/review decisions remain unresolved.

Cloud prompt constants are independent of historical local prompts. Before changing
an instruction, make an explicit new prompt file and compare fixed inputs. The
pre-cleanup prompt hashes and Phase 0 request/result fixtures protect byte parity.
Provider rendering may differ while source visibility and local validation remain
fixed. Unknown configuration settings fail rather than being silently ignored.

## Offline preparation

Use a fresh external output directory. The default manifest is the preserved
69-answer Dev3 panel; no credentials or model calls are used by preparation.

```sh
make prepare-grounding-comparison \
  GROUNDING_COMPARISON_CONDITION=fireworks_glm \
  GROUNDING_STAGE_PROMPTS=configs/grounding_glm_prompts_v1.json \
  GROUNDING_COMPARISON_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/MY_NEW_PREPARATION"
```

Shell variables in examples must already be set, including `ER_COMMONS_DATA_ROOT`.
The Makefile loads the local `.env`; the cloud command uses uv's dotenv loading so
credential values need not be printed, copied into commands or exported manually.
Configure `FIREWORKS_API_KEY`, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` for the selected
provider. Do not place credentials in JSON configurations or receipts.

For another frozen combined-development panel, supply all three:

- `GROUNDING_COMPARISON_MANIFEST=/absolute/path/to/manifest.json`
- `GROUNDING_COMPARISON_MANIFEST_SHA256=<reviewed manifest checksum>`
- `GROUNDING_COMPARISON_PANEL=dev3|dev6|dev6_additions|full_dev`

An explicit checksum identifies the reviewed publication; it does not grant
permission to expand an experiment. The loader checks the existing frozen schema,
development membership, source/answer/packet relationships and original bindings.
It does not open restricted expectations. Test/reserved datasets are unsupported.
This interface consumes the existing combined-dataset publication, not arbitrary
future benchmark schemas; introduce another explicit adapter when needed.

## Explicit cloud execution

The following is an example for a separately authorized smoke call, not a command
run during cleanup. Use distinct directories for preparation, smoke, cache probes
and evaluation. All four run caps are mandatory and conservative reservations may
stop a run before its nominal monetary cap is spent.

```sh
make compare-grounding-cloud \
  GROUNDING_COMPARISON_CONDITION=fireworks_glm \
  GROUNDING_COMPARISON_MODE=smoke \
  GROUNDING_COMPARISON_COUNTING_MODE=provider-allowance \
  GROUNDING_STAGE_PROMPTS=configs/grounding_glm_prompts_v1.json \
  GROUNDING_COMPARISON_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/MY_NEW_SMOKE" \
  GROUNDING_CURRENCY_CAP=0.10 \
  GROUNDING_REQUEST_CAP=1 \
  GROUNDING_OUTPUT_CAP=4096 \
  GROUNDING_WALL_SECONDS=120
```

`smoke` checks the answer-only gate, `cache` probes original claims with shared
evidence, and `run` executes the full staged panel. Cache probes are excluded from
evaluation denominators. Size caps for the actual panel from preparation; do not
reuse the one-call smoke caps for a complete run.

Counting defaults to `exact`. Luna uses its native count endpoint. GLM and Haiku
require the explicit `provider-allowance` mode tested during development: conservative
byte/estimated-token headroom, full reservations, and native usage checks. This
mode does not claim exact token qualification. Selecting it for an incompatible
condition fails before any model dispatch; there is no automatic downgrade.
Run different counting modes in separate namespaces.

Each dispatch writes an intent before transport and a completion seal only after
response persistence. Transport uncertainty, invalid usage/identity, cancellation,
receipt corruption or storage failure halt the shared budget. There are no automatic
cloud retries. Existing live namespaces cannot restart with fresh spending caps.
Completed receipts can be inspected/revalidated offline; incomplete intents require
explicit reconciliation. Never delete a failed attempt to make replay look new.

## Results and tests

Post-run `metrics_v2` separately reports original claims, claim reviews, conclusions
and numeric scores. Accuracy includes every eligible item. Missing/invalid outputs
count as errors and false negatives for their expected class in macro-F1. Binary
classes are fixed to false/true; numeric classes are 0/1/2. Valid-only diagnostics
are explicitly separate. Clean N/A proposals are excluded from numeric eligibility.
Synthetic labels remain proposals, not human calibration.

Native usage retains disjoint input/cache/output buckets and unknown cache counters.
Reservations are conservative cost bounds, not invoices. The maintained generic
analysis does not invent an exact cost when receipt pricing/cache information is
insufficient. Provider cache hits reuse computation; saved receipt reuse avoids a
new call. Neither implies deterministic judgments.

```sh
uv run pytest -q tests/test_grounding*.py tests/test_ollama_token_counter.py tests/test_judge_packet_requests.py
make fix
make check
git diff --check
```

Ollama commands such as `evaluate-grounding-dataset-panel` remain available for
small-Qwen code-path checks with explicit settings and exact pinned token-counter
configuration. Their historical strict quotation behavior is distinct from the
cloud semantic/quotation split. No local model is selected for benchmark judging.

Clef dispatch, its special uncounted exception and runtime probes have been removed.
The original seven-condition config and sealed experiment records remain historical
evidence; they are not a maintained execution profile. The six-condition v2 config
retains offline protocol coverage for deferred Decisions/Jev/DeepSeek adapters.
Use the three-model profile for normal judge work. No schema migration, new provider
qualification, model download or performance benchmark was part of this cleanup.
