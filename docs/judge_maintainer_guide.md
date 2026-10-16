# Production judge guide

The maintained judges are four independent native Inspect calls. The selected
models and exact semantic identities live in
[`configs/judges_selected_v1.json`](../configs/judges_selected_v1.json); native
provider profiles live in [`configs/judge_models_v1.json`](../configs/judge_models_v1.json).

| Component | Selected model / prompt | Model-visible input | Core / Inspect adapter |
| --- | --- | --- | --- |
| A: no-answer | Luna / v2 | Original candidate conclusion only | `no_answer` / `no_answer_inspect` |
| G: grounding | Luna / v3 | Question, one point or factual qualification, its complete owned evidence | `point_grounding` / `point_grounding_inspect` |
| S: support | Haiku / v6 | Original candidate reasoning and qualifications under the selected S contract | `adequacy_binary` / `adequacy_inspect` |
| C: conclusion | Luna / v8 | Question, candidate conclusion, reference conclusion | `adequacy_binary` / `adequacy_inspect` |

`judge_inspect` owns provider configuration, schema adaptation, model construction,
cost registration, sample identity checks and selection verification. The component
cores own input validation, exact prompts and strict parsing; component adapters
own scoring. Dataset loaders verify frozen development artifacts and keep labels
and provenance outside model messages. Task 12 owns whole-answer routing and joins.

## Execution

Inspect owns generation, retries, concurrency, epochs, logs and resumption. There
is no project HTTP executor, replacement-judgment loop or custom budget scheduler.
All four components support explicit `openai_generation`, `anthropic_generation`,
`fireworks_glm`, `ollama_small` and `ollama_9b` profiles. Omitting the condition uses
the verified selected model. The local models remain diagnostic alternatives.

Run from the repository with `.env` configured. Each command uses the full frozen
**development** dataset and defaults to one repetition. Set an external log location
and bounded sample options appropriate to the authorized run, for example:

```bash
make evaluate-no-answer JUDGE_LOG_DIR=/external/fresh-a-run JUDGE_OPTIONS='--limit 3'
make evaluate-point-grounding JUDGE_LOG_DIR=/external/fresh-g-run JUDGE_OPTIONS='--limit 3'
make evaluate-adequacy JUDGE_COMPONENT=C JUDGE_LOG_DIR=/external/fresh-c-run JUDGE_OPTIONS='--limit 3'
make evaluate-adequacy JUDGE_COMPONENT=S JUDGE_LOG_DIR=/external/fresh-s-run JUDGE_OPTIONS='--limit 3'
```

Use `JUDGE_CONDITION=fireworks_glm` or `JUDGE_CONDITION=ollama_small` to choose an
alternative explicitly, and `JUDGE_EPOCHS=3` for three repetitions. `JUDGE_OPTIONS`
passes through native Inspect options. These commands perform inference; cleanup
validation uses mocks and does not run them against live providers.

For saved or newly prepared inputs, use the adapters' `build_task` functions with
validated sample packets and separately bound labels. Calibration factories remain
available but use the selected prompts. Historical prompt experiments are archived.
Native logs preserve raw responses, errors, model usage and task identities.

Cloud defaults: 4,096 output tokens, medium reasoning, four static connections,
120-second request timeout, 45-second attempt timeout, two Inspect transport retries,
and 150-second sample limit. OpenAI/Anthropic SDK retries are disabled; Fireworks
retains its native SDK behavior. Native result caching is off; provider prompt
caching remains distinct. Inspect cost limits are soft per-sample limits, not a
project-wide hard spending cap. Token prices are dated estimates from the retained
comparison profiles, not live billing guarantees.

## Failure and visibility contracts

- G rejects missing or unresolved citations before inference. A failure to load
  known evidence is an evaluator error. Supporting points and factual qualifications
  use the same isolated check; no conclusion or neighboring prose enters G.
- A's `empty_other_prose_guard` is separate and required before accepting an
  abstention route. A classification alone never exempts a whole answer.
- Invalid, truncated or malformed output is a failure with no semantic decision;
  it never becomes false or clean abstention and never triggers a semantic reroll.
- C quotation fidelity remains diagnostic. It does not alter the selected binary
  decision. S receives original premises, without G predictions or filtering.
- Expected labels, IDs, mechanisms and provenance are evaluator metadata only.
  The strict combined A/G/S/C reporting policy is Task 12 work.

## Ollama and exact context checks

The native Ollama profiles use the existing `er09b-qwen-small-48k:v2` and
`er09b-qwen-f16-48k:v1` tags through Inspect. A tag is not a verified model digest;
verify the intended local service/model before a live diagnostic. Local concurrency defaults to one connection. Local cost is
unknown, not zero. These alternatives are not selected or benchmark-qualified.

`ollama_request` and `ollama_token_counter` retain the historical exact-rendering
preflight utilities used by deterministic packet preparation. Their render-only
request cannot generate text. They are not an exact counter for the new Inspect
OpenAI-compatible request. A future live qualification must bind that actual request
and context behavior; the old context receipt cannot qualify the new adapter.

## Evidence and historical replay

Model selections and completed reports remain immutable development evidence:
[C/S](specs/task09f_final_result.json), [A](specs/task09f1_a_full_development_v2_result.json),
[G](specs/task09f1_g_full_development_v3_result.json). The older per-component selected
configs and model profiles are historical bindings; production reads only the two
shared config files above. No labels or historical scores were changed by cleanup.

The recoverable pre-cleanup source snapshot lives under `ER_COMMONS_DATA_ROOT` at
`pipelines/brisbane_baylands/task_09/09f2_cleanup_20261016/`:
`pre_cleanup_source.tar.gz` plus `manifest.json` bind every archived file and archive
bytes. It includes the old uncommitted runtimes, tests, configs and both G analyzers.
Restore it into a separate directory, verify its hashes, and use its pinned `uv.lock`
for **offline** historical replay. G's archived analyzer intentionally verifies
historical runtime hashes; running it against the cleaned source is not supported.
Never extract over this checkout or modify sealed run directories. Snapshot recovery
does not authorize rerunning historical inference.

## Validation and ownership

Run `make fix`, `make check`, and `git diff --check`. Tests cover selected semantic
identities, strict failure behavior, label isolation, native provider serialization,
and sealed data loading. [09F.2](../tasks/sprint2/09f2_cleanup_production_judges.md)
records cleanup scope and verification. The [09G freeze](specs/task09g_judge_freeze_v1.json) binds the committed production
configuration and existing evidence without new inference. Task 12 owns
integration; held-out qualification remains separate.
