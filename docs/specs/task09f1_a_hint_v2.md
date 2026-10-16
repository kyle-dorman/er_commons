# A v2 generic-advice hint — targeted calibration

Kyle authorized a small hint and a three-model retry on the prior failure plus
two similar positive controls. Here positive means **substantive**, guarding
against an overcorrection that labels actual answer assertions ambiguous.
No categories, output schema, guard rules, labels or original payloads change.

## Single prompt change

Version `task09f1.no_answer.conclusion.v2` inserts this paragraph after the
classification definitions in v1:

> Generic advice to pay attention to a topic or consult a source is ambiguous unless it also states a concrete answer position. A specific conclusion remains substantive even when phrased cautiously or as a recommendation.

The rest of v1 is unchanged. This clarifies the accepted generic-filler boundary;
it does not make recommendations categorically ambiguous or require an unhedged
answer. V1 remains the default and earlier native logs remain preserved. No
automatic promotion follows this targeted check.

## Fixed three-case selection

All three IDs, original conclusion payloads and expected labels come unchanged
from the locked A24 calibration selection.

| ID | Expected | Role |
| --- | --- | --- |
| A-C028-U01 | ambiguous | Prior Luna failure: generic request for careful attention to rail operations and nearby housing |
| A-C028-S04 | substantive | Same-question hedged positive: noise-conscious building/site design as a safeguard |
| A-C027-S03 | substantive | Nearby-question concrete positive: the connection includes visible roadway crossings |

The exact positive conclusions are:

- “The likely safeguard is noise-conscious building and site design, which appears intended to keep residents' exposure within the specified standards.”
- “The connection would include visible roadway crossings.”

These are a small regression check, not a comprehensive test of recommendation
wording. Their original v1 judgments were correct in all three repetitions for
all models. A-C028-U01 was ambiguous/substantive/substantive for Luna and
ambiguous in all repetitions for GLM/Haiku. Historical v1 calls are compared as
saved results; no fresh v1 calls are added.

## Authorized execution

Three cases × three epochs × GLM/Luna/Haiku = **27 new planned generations**, nine
per model. Inspect owns native generation, transport recovery and logs. Preserve
v1 provider settings and strict parsing; sequential models, one connection/sample,
response caching off, two Inspect transport retries, no whole-sample retry,
4,096 output tokens, 150-second sample limit and USD0.10 per-sample soft limit.
Transport recovery can increase billed requests; no aggregate invoice cap is claimed.

Before dispatch, inspect current C/S and G traffic; do not change those runs.
Use the separate `no_answer_hint` entry point and a fresh external A directory:
`pipelines/brisbane_baylands/task_09/09f1_a_hint_v2/` beneath the configured root.
Change only this one prompt factor. Preserve every outcome, including errors.
Stop after the planned three-model check; no expansion or additional tuning.

```bash
uv run --env-file .env inspect eval src/er_commons/no_answer_inspect.py@no_answer_hint \
  -T condition_id=fireworks_glm --epochs 3 --max-samples 1 --max-connections 1 \
  --retry-on-error 0 --cost-limit 0.10 --log-model-api --display plain \
  --log-dir /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_hint_v2/glm
```

Then use `openai_generation` with log subdirectory `luna`, followed by
`anthropic_generation` with `haiku`, reviewing each completed log first.

## Interpretation

Report the failure case and the two controls separately, including exact predictions
across all three epochs, validity, errors, cache usage and estimated cost. “Fixed in
this check” requires the failure case correct in all three repetitions for each
model while both positive controls remain correct. A clean targeted result does
not establish full-panel stability, generalization or final judge qualification.

## Outcome — 2026-10-16

All **27/27** new judgments are correct and valid. Each model returns `ambiguous`
on A-C028-U01 in all three epochs and `substantive` on both positive controls in
all three epochs. No output/execution failures, missing judgments or Inspect-reported
retries occurred. No labels or payloads changed.

| Model | Failure case correct: v1 → v2 | Positive controls correct: v1 → v2 | v2 total | Estimated USD |
| --- | --- | --- | --- | --- |
| GLM | 3/3 → 3/3 | 6/6 → 6/6 | 9/9 | 0.000914900 |
| Luna | 1/3 → 3/3 | 6/6 → 6/6 | 9/9 | 0.000732900 |
| Haiku | 3/3 → 3/3 | 6/6 → 6/6 | 9/9 | 0.000600445 |

Total estimated cost: **$0.002248245**. Cache-read observations were 0/9 GLM,
0/9 Luna and 8/9 Haiku. These are native log estimates under the existing dated
pricing configuration, not invoice reconciliations. V1 is the earlier saved
comparison; there was no fresh randomized paired v1 run.

Luna's first revised reason is: “This recommends attention to rail operations and
nearby housing but does not state a concrete answer position.” Its other two
reasons draw the same distinction. The observed failure is fixed in this narrow
check without regressions on the two controls. This does not test all remaining
A24 cases, clean abstentions, the source-consultation phrase or concrete recommendations.
V2 remains opt-in; full-panel stability and promotion remain separate decisions.

The [result pointer](task09f1_a_hint_v2_result.json) binds the exact selection,
prompt, native logs, summary and completion inventory. Offline replay:

```bash
uv run python /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_hint_v2/summarize.py
```

Validation: 65 focused A tests passed, including version/default preservation,
cache separation, metadata and exact selection. `make check` passed formatting,
lint, mypy and **4,839 tests with one skip** (112.01 seconds). Independent pre-call
review found no actionable issues in policy fidelity or implementation. Runtime
v1 remains unchanged by default; original v1 logs/artifacts are preserved.

Independent final log review also passed: all 27 exact case/epoch identities,
v2 messages/metadata, accepted labels, source hashes, outcomes, costs and cache
accounting reconcile. A fresh completion inventory seals the external artifacts.
Whitespace validation passed. No commit or push was made.
