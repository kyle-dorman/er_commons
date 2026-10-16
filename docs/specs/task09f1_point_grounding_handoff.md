# Task 09F.1 — Independent G implementation handoff

## Selected G configuration and handoff

Kyle selected **Luna (`gpt-6-luna`) with the v3 reason-first grounding prompt**
on 2026-10-16. The G portion of 09F.1 is complete and ready for 09G freeze;
Task 12 owns routing and combined reporting. The
[selected configuration](../../configs/point_grounding_selected_v1.json) binds
model, prompt, semantic schema, native response schema and provider profiles to the
[full-development comparison](task09f1_g_full_development_v3_result.json).

Luna produced **1,833/1,833 valid outputs**, with 1,822 correct judgments,
604/611 cases correct in all three repetitions, zero false accepts and 11 false
rejects against the frozen proposed labels. P90 sample latency was 2.866966 seconds;
estimated cost was USD0.44425775. Kyle prioritized output validity and lower cost:
GLM emitted three invalid outputs and Haiku cost over twice as much.

`point_grounding_inspect.point_grounding_full` already defaults to Luna, v3 and
three epochs. For individual production calls, pass `openai_generation` and
`core.REASON_FIRST_PROMPT_VERSION` explicitly to the native adapter. The selection
file is historical selection evidence. The [shared production selection](../../configs/judges_selected_v1.json)
is validated before task construction; the [production guide](../judge_maintainer_guide.md)
owns current runtime commands.
09F.2 makes calibration/core defaults selected v3 as well; historical v1
replay uses the archived source snapshot. Native v3
structured output orders `reason` before `supported`; strict parsing remains mandatory.

This is a development selection, not held-out qualification. The 611 eligible
points span 19 development questions and include the 36 calibration points; four
unresolved candidates are excluded. Full-pool labels remain reviewed agent proposals,
and five possible label/evidence issues remain flagged without relabeling. See the
[comparison outcome](task09f1_g_full_development.md) for limits and replay.
09G receives this selection and preserved evidence; Task 12 receives the independent
point/qualification interface, identities and failure statuses. The comparison's
historical `model_selected: null` records its pre-selection state.

## Historical implementation and calibration record

The material below records earlier stages; pending-selection statements and
calibration-only scope describe those stages and are superseded by the selection above.

The first authorized three-model calibration is complete; see the
[result pointer](task09f1_point_grounding_calibration_result.json). No model has been selected. This handoff owns the G implementation only. The accepted parent task,
A implementation, running C/S comparison, shared settings and original artifacts
remain separate. Task 12 owns answer routing and combined reporting.

## Entry points and boundaries

- `src/er_commons/point_grounding.py`: locked prompt, strict two-field output schema
  and parser, exact three-field input validation, and `prepare_point` citation checks.
- `src/er_commons/point_grounding_panel.py`: loads only the accepted 36 G payloads
  and separately bound labels. Immutable selection/completion digests anchor all
  selected payloads, labels, point/evidence hashes and the 19 development questions.
- `src/er_commons/point_grounding_inspect.py@point_grounding`: native Inspect task,
  one generation per point per epoch, provider configuration and component scoring.
- `configs/point_grounding_models_v1.json`: separate snapshot of the current C/S
  model profiles; it selects no C/S winner. The schema version remains the existing
  provider-loader version. Model IDs and dated pricing come from that snapshot.
- `tests/test_point_grounding*.py`: strict parsing, projection, all 57 published
  citation fixtures, frozen-panel integrity and mocked native provider execution.

Each model request contains only `question`, `point_text`, and complete owned
`evidence`. Source text, tables, headers, units, footnotes and identities retain
original structure. A factual qualification uses the same function as a supporting
point; no answer role, point ID, conclusion or attached prose enters the request.
Panel hashes attest to the reviewed evidence ownership; the loader does not rebuild
it using reference answers or search the corpus. Only selected copied payloads are
read, never the reserved/test sets or full candidate payload pool.

`prepare_point` accepts one already eligible point, its actual citation IDs, an
allowed-ID index and a complete source-record loader. It checks all IDs before any
source load. Missing or unresolved citations produce `precheck_failed`; a known
artifact that cannot load produces `execution_error`; malformed projections produce
`invalid_input`. These carry no packet or semantic decision. A successful preparation
has status `not_run`, a validated packet and no decision. Whole-answer abstention,
empty-support checks and eligibility routing remain Task 12 work.

The calibration factory only accepts the locked semantic panel. Its 36 points have
already passed citation review. Mechanical fixtures stay outside that denominator;
tests exercise their no-call boundary separately. Missing/altered panel artifacts
abort task construction as evaluator errors, not semantic failures.

## Execution and learning notes

The implementation follows the [current native C/S execution contract](task09f_inspect_native.md),
[Inspect scorer guidance](https://inspect.aisi.org.uk/scorers.html) and
[structured-output guidance](https://inspect.aisi.org.uk/structured.html). Inspect
owns provider SDKs, connection management, transport retries, logs and epochs.
Small project adapters supply data, schemas and scores; there is no custom HTTP
executor, receipt ledger, scheduler, claim extraction or re-review.

Luna and Haiku receive native structured-output schemas. GLM receives the unchanged
locked prompt's JSON guidance, which is not schema enforcement. All responses pass
the same strict local parser: actual boolean `supported`, nonblank string `reason`,
exact fields, no duplicate keys, wrappers or surrounding prose. Invalid or truncated
output is never converted to false or regenerated for a better judgment.

Native defaults: 4,096 output tokens, medium reasoning, 120-second request timeout,
45-second attempt timeout, 150-second sample limit, two Inspect transport retries,
and one static connection. OpenAI/Anthropic SDK retries are disabled; Fireworks
retains its native SDK retry defaults, as C/S does. Result caching is off. Prompt
caching uses G-specific stable keys/affinity and Haiku's five-minute system prefix.
The copied profile's legacy OpenAI 30-minute cache notes and exact-count blockers
are provenance, not native runtime controls; the actual native options above and
in `generation_config` apply. Costs use the dated profile rates and may differ from
billed charges. No exact request counter or hard aggregate spending cap is claimed.

Inspect scores preserve raw output, null invalid decisions, semantic false accepts
and false rejects separately. The four metric means apply to **scored observations**;
false-accept/reject means are not class-conditional rates. Provider failures remain
native Inspect sample errors and may have no score. Future reporting must join
those errors and missing observations back to the fixed 36 × repetitions inventory
for failure-inclusive coverage and accuracy. Report valid-only accuracy separately.
Retain per-epoch decisions to compute observed all-k-correct, all-k-valid and
same-label agreement; never exponentiate pooled accuracy. The panels are correlated
diagnostic cases, not prevalence estimates or judge qualification.

## Offline commands

```bash
uv run pytest tests/test_point_grounding.py tests/test_point_grounding_panel.py tests/test_point_grounding_inspect.py -q
uv run mypy src/er_commons/point_grounding.py src/er_commons/point_grounding_panel.py src/er_commons/point_grounding_inspect.py
make check
git diff --check
```

Formatting/lint fixes were scoped to G-owned files using the commands underlying
`make fix`, avoiding repository-wide writes during concurrent A/C/S work.

## Proposed first calibration — not executed or authorized here

Use the locked 36 cases and labels unchanged on GLM, Luna and Haiku, **three epochs
per model: 108 judgments each, 324 planned judgments total**. Run providers
sequentially with one sample and one connection at a time. Before authorization and
dispatch, account for both running C/S and A traffic; preferably wait until those
runs are idle. A connection limit is local to this evaluation, not a shared
provider-rate-limit reservation. Transport retries can increase billed attempts;
324 is the semantic generation count, not a hard network-attempt ceiling.

After explicit authorization, set `ER_COMMONS_DATA_ROOT` in the shell to the verified
root from `.env` (Inspect loading `.env` later does not set shell expansions). Use a
fresh G-only directory; these commands intentionally refuse an existing run root:

```bash
: "${ER_COMMONS_DATA_ROOT:?Export the verified artifact root first}"
G_RUN_ROOT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/09f1_g_calibration_native_v1"
mkdir "$G_RUN_ROOT" || exit 1
for condition in fireworks_glm openai_generation anthropic_generation; do
  uv run --env-file .env inspect eval src/er_commons/point_grounding_inspect.py@point_grounding \
    -T condition_id="$condition" -T panel=calibration \
    --epochs 3 --no-epochs-reducer --max-samples 1 --max-connections 1 \
    --retry-on-error 0 --no-fail-on-error --cost-limit 0.10 --log-model-api \
    --log-dir "$G_RUN_ROOT/$condition" || break
done
```

The $0.10 limit is Inspect's **per-sample soft limit**, not a hard total cap. Any
aggregate cost/wall-time ceiling required by the live authorization must be settled
before dispatch; this implementation does not recreate the old budget framework.
Inspect errors remain visible while other samples proceed. Preserve all `.eval`
logs and raw API events. Use native Inspect log/resumption tools only after reviewing
which samples failed; do not rerun malformed judgments or replace semantic errors.
Review the complete three-model result before changing prompts, labels or scope.

## Validation and independent review

- Focused final G suite: **66 passed**. Includes all 57 published mechanical
  fixtures, all 36 locked payloads through runtime validation, strict parsing and
  mocked native transports for all three providers. Original sparse evidence can
  omit tables/printed labels; validation preserves those omissions.
- Repository `make check`: **4,819 passed, 1 skipped**; formatting, lint and mypy
  passed. This run began before the final two sparse-source integration tests were
  added; the final focused suite and changed-core lint/type checks passed afterward.
- `git diff --check`: passed. No shared files were edited by this implementation.
- Bounded independent review found no actionable issues. Follow-up review of the
  sparse-source fix and its full-panel regression also found no actionable issues.
- No live model calls, prompt/label edits, held-out access, commits or pushes.


## First calibration authorized — 2026-10-16

Kyle authorized the proposed first run in this chat: 36 locked points, three
repetitions each on GLM/Luna/Haiku, 324 planned judgments, sequential providers,
concurrency one. The fresh external namespace is
`pipelines/brisbane_baylands/task_09/09f1_g_calibration_native_v1/`; its
`run_manifest.json` binds the implementation snapshot, exact settings, selected
inputs, separate labels and execution limits before generation. No prompt cycles,
label changes, scope expansion or automatic model selection are authorized.

Preflight found concurrent C/S Luna/Haiku traffic and A's GLM batch. G waits for
A's GLM batch before dispatch, then rechecks traffic between provider batches.
The implementation and original proposal above remain the preserved pre-run record;
results will be published separately after all observations and failures are reviewed.

## First calibration outcome

All 324 judgments completed on the locked 36-case panel. Every output was valid;
there were no execution errors, reported HTTP retries or response-cache reuse.

| Model | Correct | All three correct | False accept / reject | Estimated USD |
| --- | --- | --- | --- | --- |
| GLM | 107/108 | 35/36 | 1 / 0 | 0.045133 |
| Luna | 105/108 | 34/36 | 2 / 1 | 0.024382 |
| Haiku | 96/108 | 32/36 | 9 / 3 | 0.055635 |

GLM and Luna's errors concern the paired queue-length versus vehicle-count claims.
Haiku repeats four case errors across all three epochs: that unit substitution,
reversed thistle-removal timing, rejection of the correct timing restriction,
and acceptance of an unsupported clause in a compound recreation claim. Six Haiku
booleans contradict their own explanations. They remain semantic errors; no
explanation-based override, rerun, label change or prompt repair occurred.

All models were valid on all three epochs for all 36 cases. Same-label consistency
was 35/36 GLM, 34/36 Luna and 36/36 Haiku: consistency does not imply correctness.
The failure-inclusive and valid-only accuracies coincide here because no output
or execution failures occurred. Valid-only macro-F1 is 0.990702 / 0.972105 / 0.887500.
Native evaluation wall times were 158 / 238 / 201 seconds, respectively.

Total estimated cost is **$0.125149115**, reconciled with Inspect's native costs.
For this installed Inspect version, `input_tokens` excludes cache reads/writes;
price those three input buckets separately. Reasoning tokens are already part of
output tokens. Regression tests exercise the installed provider conversions.
These are dated-profile estimates, not invoices.

The result pointer binds the complete native logs, full metrics/error records,
source-backed error review and independent audit. No model selection, full-pool
expansion or prompt tuning follows automatically. GLM leads this panel, which is
small, purposive and correlated.

Offline reporting is reproducible with
`scripts/analyze_point_grounding_calibration.py --run-root <external run root>`
through `uv run python`. It refuses an existing `analysis` directory; preserve the
published report rather than rerunning in place. Analysis performs no generation.

Final validation: `make check` passed (4,835 tests passed, one skipped), including
14 analysis tests; standalone analysis mypy and `git diff --check` passed.
Independent code/statistics and final-log audits passed. All G prompt, labels,
provider configuration and execution modules stayed unchanged during calibration.
A and C/S work and artifacts were preserved; no commit or push occurred.

## Clarification v2 comparison

Kyle authorized the [v2 prompt](task09f1_grounding_judge_prompt_v2.md), including
addition/subtraction alongside units, timing and verdict/reason consistency.
The [v2 result](task09f1_point_grounding_calibration_v2_result.json) binds 324 fresh
judgments on the identical panel and labels. All generation settings stayed fixed;
providers ran sequentially at concurrency one with distinct v2 logs/cache identities.

| Model | Correct v1 → v2 | All three correct v1 → v2 | V2 false accept / reject |
| --- | --- | --- | --- |
| GLM | 107 → 105 / 108 | 35 → 35 / 36 | 3 / 0 |
| Luna | 105 → 107 / 108 | 34 → 35 / 36 | 1 / 0 |
| Haiku | 96 → 97 / 108 | 32 → 32 / 36 | 9 / 2 |

All v2 outputs were valid, with no execution errors, reported retries or saved-response
reuse. Estimated cost was $0.12522778. No new failing cases appeared; the repeat-level
changes remain visible in the paired comparison. Exact epoch pairing records GLM
zero gains/two regressions, Luna three gains/one regression, and Haiku one gain/zero
regressions. These are descriptive fresh-run comparisons, not independent trials.

GLM accepted the wrong queue unit more consistently. Luna repaired the supported
feet control but still accepted the wrong vehicles claim once. Haiku's same four
cases remain problematic; eight wrong booleans contradict their explanations,
compared with six in v1. Additional instructions did not provide a general fix.
V1 remains the default; neither v2 promotion nor model selection is automatic.
The combined treatment does not isolate any arithmetic-specific effect.

For a future explicitly authorized v2 evaluation, add
`-T prompt_version=task09f1.grounding.point.v2` to the native task command and use a
fresh G namespace. The frozen v1 prompt remains available by default or explicit
`-T prompt_version=task09f1.grounding.point.v1`.

Offline reporting accepts `--baseline-report <preserved v1 report.json>` alongside
`--run-root <v2 run root>`. It creates comparison JSON/Markdown and refuses overwrites.
The published baseline report was checked against its prior result-pointer hash;
`comparison_bindings.json` preserves that check. Native logs, input snapshots, exact
prompt text, all decisions and source-backed error review remain external.

Validation: 39 adapter tests, 21 reporting tests, and full `make check` passed
(4,862 tests passed, one skipped). The prompt/version adapter and comparison received
independent review. No shared A/C/S implementation, labels or held-out data changed.

## Bounded Haiku boolean diagnostic

The [two-case diagnostic](task09f1_haiku_boolean_probe.md) compared existing v2,
explicit boolean meaning, explanation-first output, and both changes across three
repetitions each. Correct judgments were 3/6, 3/6, 5/6 and 6/6 respectively; all 24
outputs were valid. Explanation-first arms had no observed boolean/reason
contradictions, although explanation-first alone still misread timing once.
The combined treatment is a candidate for later validation, not a promoted default
or general grounding result. The [result pointer](task09f1_haiku_boolean_probe_result.json)
binds the preserved inputs, logs and independent reviews.

## Full-panel v3 comparison

Kyle authorized the combined prompt on all 36 locked cases, three repetitions
across all three models. [V3](task09f1_grounding_judge_prompt_v3.md) exactly matches
the successful combined diagnostic wording and requests reason-first output;
native Luna/Haiku schemas also put reason first. GLM remains prompt-only.

The [result](task09f1_point_grounding_calibration_v3_result.json) records GLM
108/108, Luna 107/108 and Haiku 105/108 correct, with all 324 outputs valid.
Cases correct across all three repetitions are 36/36, 35/36 and 35/36 respectively.
Remaining errors are the 680-vehicles unit substitution (Luna once, Haiku three
times). Both thistle directions and recreation compound scope pass every time.
The v1 default remains unchanged; v3 is available by explicit prompt_version.
Comparison artifacts bind both earlier reports, preserve all raw outputs and
include independent source and execution reviews. No labels, A/C/S settings or
held-out data changed.

## Full-development comparison

The [full G comparison](task09f1_g_full_development.md) runs the fixed v3 prompt
on all 611 binary eligible development candidates, three repetitions per model.
Four unresolved labels remain excluded; the broader labels are independently
reviewed agent proposals. The separate `point_grounding_development.py` loader
and native `point_grounding_full` task preserve calibration defaults and verify
publication hashes, exact owned evidence, development scope and the 36-case overlap.

All 5,499 judgments completed: GLM 1,824/1,833 correct and 607/611 all-three,
Luna 1,822 and 604, Haiku 1,819 and 605. P90 sample latencies are 1.94s, 2.87s
and 2.67s at four connections; costs are $1.16136, $0.44426 and $1.04246.
GLM had three invalid outputs; all others were valid. The
[sealed result](task09f1_g_full_development_v3_result.json) includes full metrics,
overlap partitions, source-review caveats and reproducible independent accounting.
GLM leads agreement/consistency/latency on this run; Luna is cheapest. No automatic
selection or default change. Shared A/C/S work and held-out data remain untouched.
