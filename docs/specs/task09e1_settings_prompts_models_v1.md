# Task 09E.1 — bounded settings, prompts and model comparison

The October 12 user request authorizes three sequential experiments: settings on
inconsistent claims, five prompt ideas on those claims, then GPT-5.4 and
GPT-5.4-mini on the full existing panel. “Full” means the frozen **69-answer Dev3
panel**, not Dev6, full-19, reserved or test data. No dataset/label edits, commits
or pushes. Preserve the original Luna and prior namespaces.

## Predeclared design

Use eight exact original point payloads covering all fourteen point reversals in
the eleven unresolved Luna answers. Keep original citation IDs and text, including
the two otherwise identical enforcement claims with different citation identities.
Run three fresh calls per input/condition; native prefix caching is allowed, but
saved-result replay does not count as a repetition. No automatic retries.

Settings: original low reasoning/default sampling, medium/default sampling,
no reasoning/temperature 1, no reasoning/temperature 0. The latter pair isolates
temperature; low versus medium isolates reasoning effort. Sampling overrides are
not supported in Luna's reasoning modes. No causal comparison of temperature
alone may be made between reasoning-enabled and reasoning-disabled arms.

Five prompt additions, frozen before dispatch, test scope preservation, bounded
absence, grammatical attachment, their combination, and a balanced assertion
checklist. Append each separately to the original prompt. Hold selected settings,
source evidence, target claims, output schema and diagnostic separation fixed.
Reject settings that regress on any clearer claim relative to the complete
low-reasoning baseline. Select remaining settings lexicographically by source-review agreement on four clearer
claims, number of unanimous claims, then shorter outputs; use original low mode
for a tie. For prompt comparison, reuse the selected arm's matching baseline
observations as a baseline only, never as new repetitions. Reject variants that
lose agreement on any clearer claim or fail to improve unanimity; rank remaining variants
by those same diagnostics. Report every arm, including unsuccessful variants.

The four clearer diagnostic claims are: the grading milestone contrast, two
bounded-absence claims (source-review support), and the universal-policy claim
(source-review rejection). Four enforcement-scope paraphrases remain ambiguous;
report direction and consistency without declaring either boolean ground truth.
These source-based diagnostic interpretations are frozen separately from model
inputs. The suite is selected for prior inconsistency and is development tuning,
not an independent accuracy test. Three repetitions cannot establish determinism.

If a prompt improves these diagnostics, inspect its explanations and test it on
the eleven original conclusion/review inputs with original binary assessments
held fixed, alongside the original prompt at the same settings. This is a bounded
fixed-context check, not an end-to-end rerun or automatic promotion.

Run one full Dev3 pass each for GPT-5.4 and GPT-5.4-mini through the existing
Inspect runner using **original prompts and low reasoning**. This isolates the
model comparison from prompt tuning. Each model first needs a protocol smoke
with exact count parity. Preserve all 69 denominators and fail-closed aggregation.
Use documented pinned snapshots if listed by the account; bind exact native
model identity. Do not silently substitute models on failure.

## Bounds and provenance

External namespace: `task_09/09e1_20261012_settings_prompts_models_v1/`.
Load credentials only in code from the untracked `.env`; do not display or save
key values. Every generation uses exact preflight, disabled truncation, durable
request/response receipts and conservative reservation. Each phase gets a fresh
namespace and cannot reset an existing run's caps.

Settings: 96 calls maximum; prompts: 120; finalist review: 22; reserve at most
$3 total for these Luna diagnostics, with 4,096 output tokens/call and 3,600
seconds per phase. Each full-model run: one smoke plus at most 304 panel calls,
4,096 output tokens/call, 7,200 seconds panel limit. Currency reservation caps:
GPT-5.4 $50; GPT-5.4-mini $16 (including separate small smoke allowances).
Combined maximum reservation $69. Actual costs are expected to be substantially
lower; free-token eligibility and payer metadata are not invoice guarantees.
Stop affected arms on structural/count/identity/provider failures; preserve partial
results. Freeze code/config identities before calls and validate after completion.

## Official sources and choices

- [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) and
  [parameter compatibility](https://developers.openai.com/api/docs/guides/latest-model):
  temperature overrides only with reasoning disabled; existing implicit 30m cache.
- [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4) and
  [mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini):
  standard input/cache-read/output rates $2.50/$0.25/$15 and $0.75/$0.075/$4.50
  per million tokens, respectively. Keep requests below the 272K input threshold.
- [Cache model differences](https://developers.openai.com/api/docs/guides/prompt-caching):
  older GPT-5.4 models use `prompt_cache_retention`, not Luna's
  `prompt_cache_options`; new cache tokens cost the ordinary input rate.

The separate shared-evidence cache optimization remains deferred. These changes
only expose explicit experiment settings and model-compatible cache controls.
