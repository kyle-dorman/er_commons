# Task 09F.1 A — selected judge handoff

**A's portion of 09F.1 is complete.** Kyle selected **Luna with the existing v2
prompt** on 2026-10-16. The [selection configuration](../../configs/no_answer_selected_v1.json)
binds the model, exact prompt/schema identities and comparison evidence. This
selection is independent of C/S and G; it does not close the whole 09F.1 task.

## Current handoff to 09G and Task 12

[09F.2 cleanup](../../tasks/sprint2/09f2_cleanup_production_judges.md) consolidates
production configuration in [the shared selection](../../configs/judges_selected_v1.json).
The [production guide](../judge_maintainer_guide.md) owns current runtime commands;
the per-component selection above remains immutable comparison evidence.

- Model: `gpt-6-luna`, condition `openai_generation`, A-only provider profile
  `configs/no_answer_models_v1.json`, medium reasoning, native structured output.
- Prompt: `task09f1.no_answer.conclusion.v2`. Request input is exactly the original
  `candidate_conclusion`; strict output is `classification` and nonblank `reason`.
- Runtime: `er_commons.no_answer_inspect.build_task`, supplying the selected
  condition and prompt explicitly. `no_answer_full` already uses Luna/v2 by
  default on A310. The A24 factory and core now also default to selected v2.
  The shared selection is validated before task construction. The historical
  per-component selection remains a declarative evidence record.
- Evidence: [full comparison](task09f1_a_full_development_v2_result.json), 914/930
  label agreement, 302/310 correct in all three repeats, five unstable cases,
  all 930 outputs valid. No false abstentions; five missed abstentions. These
  involve quoted/hypothetical content expressly disclaimed by the conclusion.
- Limits: full-pool labels remain agent-reviewed proposals, including 33 flagged
  cases. This is development selection, not held-out qualification. No further
  tuning or label changes are required to close A's development scope.
- 09G owns the next challenge/freeze stage, preserving these versions and known
  weaknesses. Task 12 owns whole-answer routing and G/S/C integration. It must
  separately apply `empty_other_prose_guard` after a clean-abstention judgment;
  invalid output is never an abstention or another semantic category.
- Validation: 79 focused A tests and full project checks passed (4,875 passed,
  one skipped); bounded independent implementation and result reviews passed.
  All 20 mechanical guard fixtures are covered separately from semantic calls.

No live calls are pending. The [full-suite record](task09f1_a_full_development.md)
provides the exact offline replay command. Any future live evaluation needs a
fresh artifact directory and a shared-provider traffic check. Existing results,
labels, source defaults and other components remain preserved.

## Historical implementation and experiment record

The following sections describe earlier stages and their then-current status.
The selected configuration above supersedes their pending-selection language.

A is implemented independently of G and the running C/S comparison. This is an
implementation and first-calibration handoff, not final judge qualification or model selection.
The user's 2026-10-16 instruction activates this bounded work despite older shared
status text. Shared routers and the parent task are intentionally untouched.

## Interfaces and ownership

- `src/er_commons/no_answer.py`: exact conclusion input, strict two-field output,
  unchanged candidate system prompt, integrity-checked locked A24 loader, and
  separate deterministic empty-other-prose guard/fixture loader.
- `src/er_commons/no_answer_inspect.py`: A-only task, provider settings and scorer.
- `configs/no_answer_models_v1.json`: independent snapshot of the three current
  C/S provider profiles from `adequacy_binary_models_v2.json`; this does not inherit
  the pending C/S model selection. Its condition schema version is retained for
  the existing read-only configuration helper.
- `tests/test_no_answer.py` and `tests/test_no_answer_inspect.py`: offline contracts,
  guard fixtures, provider serialization and native evaluation/log checks.

The CLI factory loads only the locked 24 selections: 8 clean abstentions,
12 substantive and 4 ambiguous across 19 development questions. No full-pool,
reserved or test selector exists. Labels remain in Inspect targets; case IDs,
mechanisms, provenance and hashes remain metadata. The user message is exactly
one JSON object containing the original `candidate_conclusion` string.

The starting prompt is preserved verbatim from
[the candidate prompt](task09f1_no_answer_judge_prompts.md). Luna and Haiku use
native structured output. GLM retains the existing JSON serialization checklist
and reasoning settings without a response schema; prompt instructions do not
enforce schema validity. Every provider still passes the same strict local parser.
Blank reasons, duplicates, wrappers, extra fields and unknown categories fail.
Truncation fails even when the returned text happens to parse.

The guard is a separate deterministic function over the published fixture answer
schema. It never changes the conclusion classification, calls a model or controls
benchmark routing. Classifier logs record `guard_status=not_run`. Task 12 owns
whole-benchmark routing and support enforcement.

## Execution and diagnostics

Inspect owns generation, retries, connection management, concurrency, epochs,
logs and resumption. There is no custom HTTP executor, scheduler, receipt system
or budget framework. Stable schema/config/hash helpers are reused read-only.
The provider adapter mirrors the current C/S native configuration: 4 connections
maximum, 4,096 output tokens, medium reasoning, response caching off, two Inspect
retries, 120-second request timeout, 45-second attempt timeout and 150-second
sample limit. OpenAI/Anthropic SDK retries are off; Fireworks retains its native
two SDK retries. Request recovery can therefore issue up to three attempts for
Luna/Haiku and nine for GLM, subject to time limits. Transport recovery is distinct
from semantic regeneration; malformed judgments are scored once and never rerolled.

Native logs preserve exact messages, target, raw response, model/settings, sample
ID and epoch, usage, scorer metadata and errors. Task metadata includes policy,
contract, prompt and schema identities, provider-config hash and panel provenance.
The scorer saves `correct` and `valid` separately. Evaluated samples retain
expected/predicted categories plus `false_abstention`,
`substantive_false_abstention`, `missed_abstention` and `ambiguous_class_error`.
These flags may overlap. Invalid output is `invalid_output`/`output_failure`, with
no predicted classification. Transport failures remain native Inspect sample errors,
not semantic predictions; unexecuted samples remain missing. Do not count only
scored samples as total coverage.

For subsequent analysis, report the full 3x3 confusion matrix, output failures,
execution errors and missing samples separately; include all planned judgments
in failure-inclusive agreement/coverage. Valid-only agreement must name its
smaller denominator. Compute empirical all-three-correct, all-three-valid and
same-label agreement from individual sample epochs; never exponentiate aggregate
accuracy or treat these correlated diagnostic cases as independent questions.

## Proposed first live calibration (not run or authorized here)

First account for current C/S and G traffic and reserve provider capacity with
Kyle. These processes share account rate limits; A's connection setting is not
a global limiter. If capacity is unavailable, defer A; do not stop or modify the
other runs. Run the three profiles sequentially, one in-flight A sample at a time,
with three epochs each: **24 × 3 × 3 = 216 planned generations**, 72 per model.
No additional smoke calls, prompt edits, label changes or automatic replacements.
Actual HTTP attempts can exceed 216 due to transport retries; missing-response
billing remains unknown. The proposed USD0.10 limit is per sample and soft, not an
aggregate invoice cap. A future live authorization must accept these native limits.

Choose a fresh A-only directory for each new calibration. The commands below use
this machine's documented external root and preserve all existing artifacts:

```bash
uv run --env-file .env inspect eval src/er_commons/no_answer_inspect.py@no_answer \
  -T condition_id=fireworks_glm \
  --epochs 3 --max-samples 1 --max-connections 1 --retry-on-error 0 \
  --cost-limit 0.10 --log-model-api \
  --log-dir /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_calibration_v1/glm

uv run --env-file .env inspect eval src/er_commons/no_answer_inspect.py@no_answer \
  -T condition_id=openai_generation \
  --epochs 3 --max-samples 1 --max-connections 1 --retry-on-error 0 \
  --cost-limit 0.10 --log-model-api \
  --log-dir /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_calibration_v1/luna

uv run --env-file .env inspect eval src/er_commons/no_answer_inspect.py@no_answer \
  -T condition_id=anthropic_generation \
  --epochs 3 --max-samples 1 --max-connections 1 --retry-on-error 0 \
  --cost-limit 0.10 --log-model-api \
  --log-dir /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_calibration_v1/haiku
```

Review each log before starting the next command. Inspect `eval-retry` is the
resumption mechanism only after reviewing failed or unexecuted samples and obtaining
bounded continuation authorization. Preserve completed malformed judgments; never
use a retry to improve semantic accuracy. A scored malformed result is a completed
sample, not an execution error. Keep partial and resumed logs traceable rather than
silently combining them into a fresh three-pass claim.

## Design basis and validation

[Inspect scorers](https://inspect.aisi.org.uk/scorers.html),
[concurrency](https://inspect.aisi.org.uk/models-concurrency.html), and
[logs](https://inspect.aisi.org.uk/eval-logs.html) support the thin task/scorer
boundary. Installed native provider serialization and current C/S tests are the
local execution reference. The key tradeoff is native operational recovery and
logs in place of the old custom accounting guarantees. Valid JSON does not establish
semantic accuracy; a false abstention can otherwise hide substantive-answer errors.

A-specific offline validation: **61 tests passed** (33 core/fixture tests and
28 native Inspect tests), including all 20 published mechanical fixtures and
integrity/count/coverage checks on the unchanged 24-case panel. Provider tests
mock only HTTP transport, exercising native SDK request rendering and Inspect
logging without live calls. Scoped Ruff formatting/lint and mypy passed.
A bounded independent read-only review found **no actionable findings** in input
isolation, invalid-output handling, guard semantics, panel integrity, provider
compatibility or logs. Its independent run also passed all 61 tests.

The repository-wide `make check` passed: formatting, lint, mypy and **4,819 tests
passed, 1 skipped** (111.25 seconds). No failures. This is a snapshot of the
shared workspace, including concurrent G changes present at collection time.
To preserve concurrent edits,
formatting fixes were scoped to A files instead of running the repository-wide
mutating `make fix`. No shared change was required. No live models, prompt tuning,
label changes, held-out/reserved reads, commits or pushes occurred.

Reproduce the A-specific checks offline:

```bash
uv run pytest tests/test_no_answer.py tests/test_no_answer_inspect.py
uv run ruff check src/er_commons/no_answer.py src/er_commons/no_answer_inspect.py tests/test_no_answer.py tests/test_no_answer_inspect.py
uv run ruff format --check src/er_commons/no_answer.py src/er_commons/no_answer_inspect.py tests/test_no_answer.py tests/test_no_answer_inspect.py
uv run mypy src/er_commons/no_answer.py src/er_commons/no_answer_inspect.py
git diff --check
```

The offline implementation checks did not establish live endpoint compatibility
or semantic accuracy. The subsequent first calibration below supplies bounded
live evidence; it does not qualify A or guarantee cache hits on other workloads.

## First calibration authorization — 2026-10-16

Kyle explicitly authorized the proposed first calibration in this chat: all three
models, locked A24, three epochs, sequential providers, one sample/connection,
no whole-sample retries, and the proposed native per-sample limits. The fresh
external directory is `pipelines/brisbane_baylands/task_09/09f1_a_calibration_v1/`.
`started.json` records authorization, panel identity, source/configuration hashes,
settings and the shared-traffic check. C/S was still running Luna/Haiku without
reported retries; G was idle. GLM starts first; traffic is checked again before
the next provider. This authorization does not permit prompt tuning, relabeling,
full-pool expansion or model selection.


## First calibration outcome

Completed all **216 planned judgments**, preserving all outputs in native Inspect
logs. Providers ran sequentially at one sample/connection, with the original prompt
and locked labels unchanged. The [result pointer](task09f1_a_calibration_v1_result.json)
binds external logs, source hashes and the reproducible offline summary.

| Model | Correct / valid | Macro-F1 | All 3 correct | All 3 valid | Same label all 3 | Estimated USD |
| --- | --- | --- | --- | --- | --- | --- |
| GLM Flash | 72/72 correct; 72/72 valid | 1.0000 | 24/24 | 24/24 | 24/24 | 0.00445239 |
| Luna | 70/72 correct; 72/72 valid | 0.9607 | 23/24 | 24/24 | 23/24 | 0.00601830 |
| Haiku | 72/72 correct; 72/72 valid | 1.0000 | 24/24 | 24/24 | 24/24 | 0.004960735 |

Failure-inclusive and valid-only agreement coincide because every planned judgment
completed validly. No output failures, execution errors, missing judgments, false
abstentions or missed abstentions occurred. Inspect reported zero retries. No
malformed or disagreeing judgment was rerun. Total estimated cost is **$0.015431425**
using the configured dated rates; it is not an invoice reconciliation.

The sole affected case is **A-C028-U01**, accepted as `ambiguous`:
“Rail operations and nearby housing deserve careful attention in the environmental
review.” Luna returned ambiguous/substantive/substantive across epochs 1/2/3,
treating generic advice as an answer assertion in the latter two. GLM and Haiku
returned ambiguous in all three. This is the generic-filler versus answer-assertion
boundary, not a false abstention. The label and prompt remain unchanged.

Confusion matrices (expected rows, predicted columns ordered clean abstention,
substantive, ambiguous) are `[[24,0,0],[0,36,0],[0,0,12]]` for GLM and Haiku and
`[[24,0,0],[0,36,0],[0,2,10]]` for Luna. All clean-abstention and substantive controls
passed for every model; Luna's errors are exclusively in the ambiguous class.

Prompt-cache reads occurred on 66/72 GLM, 0/72 Luna and 71/72 Haiku samples.
Mean sample time was 1.07s / 2.00s / 1.67s respectively. These are observed native
execution conditions during shared traffic, not isolated throughput benchmarks.
C/S remained active without reported execution errors/retries at the pre-provider
checks. G began its GLM calibration during A's Luna run; A's subsequent Haiku run
used a different provider. Other chats and their settings were left untouched.

The external `summarize.py` replays only native logs; it validates exact input,
prompt, target and epoch identity before computing the fixed-denominator summary.
Its `summary.json` preserves the full confusion matrices, per-class metrics,
individual errors, usage, latency and costs. No live calls are made by replay:

```bash
uv run python /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_calibration_v1/summarize.py
```

GLM and Haiku tie on this small diagnostic panel. This purposive, correlated
selection is not final qualification or a prevalence estimate. Review the complete
result before selecting a model, changing the prompt or authorizing a broader
comparison; none of those actions occurred in this run.

Final independent read-only audit passed with no actionable findings: all 216
identities/epochs, exact input projections/labels, source hashes, errors, costs and
cache accounting reconcile. The external completion record binds all three native
logs and analysis artifacts by hash and size. Whitespace validation passed; no
runtime code changed during calibration, and no commit or push was made.

## Optional v2 targeted hint experiment

The user-authorized [v2 generic-advice hint check](task09f1_a_hint_v2.md) completed
27/27 correct and valid judgments on the prior failure plus two substantive
controls. Luna improved from 1/3 to 3/3 on the ambiguous case; the controls stayed
correct for all models. `no_answer_hint` is the opt-in three-case entry point;
`no_answer` continues to use unchanged v1 on A24. No full-panel v2 run or default
promotion has occurred. See the experiment record for exact wording, tests,
limitations and artifact bindings.

## Authorized full A24 v2 rerun — 2026-10-16

After the targeted check, Kyle requested the whole calibration set on all three
models. This authorizes **24 locked cases × 3 epochs × 3 models = 216 fresh
judgments** with `task09f1.no_answer.conclusion.v2`. Original v1 and targeted v2
logs remain preserved. No full candidate-pool or held-out data is included.
The factory now accepts an explicit `prompt_version` argument; its default stays
v1. A new regression test verifies all 24 exact payloads/labels with v2. All 66
focused A tests, scoped Ruff and source mypy passed before dispatch.

Use `src/er_commons/no_answer_inspect.py@no_answer` with
`-T prompt_version=task09f1.no_answer.conclusion.v2`, three epochs, one
sample/connection, no whole-sample retries and the same USD0.10 per-sample soft
limit. Providers execute sequentially GLM, Luna, Haiku. Fresh native logs and
replay summary are under
`pipelines/brisbane_baylands/task_09/09f1_a_calibration_v2/`. No other evaluation
process was active at preflight. `started.json` records scope, source hashes and
panel identity; the saved `prompt.txt` binds exact v2 text. No additional prompt
change, automatic model choice or default promotion belongs to this rerun.

### Full A24 v2 result

All 216 planned judgments completed and were structurally valid. The
[v2 result pointer](task09f1_a_calibration_v2_result.json) binds native logs and
replay artifacts. The locked labels, policy and model settings remain unchanged.

| Model | Correct v1 → v2 | All-three-correct v1 → v2 | v2 macro-F1 | v2 estimated USD |
| --- | --- | --- | --- | --- |
| GLM | 72/72 → 72/72 | 24/24 → 24/24 | 1.0000 | 0.007970250 |
| Luna | 70/72 → 72/72 | 23/24 → 24/24 | 1.0000 | 0.006209400 |
| Haiku | 72/72 → 70/72 | 24/24 → 23/24 | 0.9648 | 0.005077015 |

Every model has all-three-valid 24/24. Same-label agreement is 24/24 for GLM/Luna
and 23/24 for Haiku. Failure-inclusive and valid-only accuracy coincide. No
false/missed abstentions, output failures, execution errors, missing samples or
Inspect-reported retries occurred. Total estimated cost: **$0.019256665**.
Cache-read sample counts were 0/72 GLM, 0/72 Luna and 71/72 Haiku. GLM's cache-read
count differs from v1 (66/72); no cause is established. Mean sample latency was
1.22s, 1.88s and 1.43s respectively; these are observed conditions, not isolated
throughput benchmarks.

Luna's prior generic-filler failure A-C028-U01 is correct in all three v2 epochs
for every model. However, Haiku now misclassifies **A-C042-S07** in epochs 1 and 3:

> Additional public parkland is the report’s basis for expecting limited deterioration. I cannot give a fuller explanation.

The locked label is `substantive`. The explicit first-sentence claim takes
precedence over inability to elaborate. Haiku returns ambiguous/substantive/ambiguous;
GLM and Luna return substantive in all three. Haiku's two mistaken reasons recognize
the assertion and precedence rule but nevertheless call the intent unresolved.
V1 was correct 3/3 on this case for all models. This is a substantive-to-ambiguous
regression, not a false abstention. It appeared in this v2 run, but a single
nonrandomized comparison does not establish that the added hint caused it.

Confusion matrices (expected rows and predicted columns clean abstention,
substantive, ambiguous) are `[[24,0,0],[0,36,0],[0,0,12]]` for GLM/Luna and
`[[24,0,0],[0,34,2],[0,0,12]]` for Haiku. The new error demonstrates why the clean
three-case targeted check did not establish full-panel stability. GLM and Luna tie
on this v2 panel; no automatic model selection, further tuning or default promotion
has occurred. Earlier logs remain intact. The panel is development calibration,
not held-out qualification.

Replay the completed native logs without inference:

```bash
uv run python /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_calibration_v2/summarize.py
```

Final independent review passed with no accounting or integrity findings. It
verified all 216 exact case/epoch identities, v2 messages/metadata, locked labels,
source hashes, errors, costs and cache accounting against saved native logs.
The completion inventory binds the logs and analysis files. Scoped checks and
whitespace validation passed. No commit or push was made.

## Full A310 comparison

The existing v2 prompt has now completed all 310 development candidates on each
model for three epochs. See [full-suite scope and outcome](task09f1_a_full_development.md)
and its [sealed result](task09f1_a_full_development_v2_result.json). The A-only
`no_answer_full` native task and `no_answer_development` loader preserve the full
proposal labels and uncertainty flags outside requests. Model selection remains
Kyle's decision; no additional live command is pending. The full-suite document
provides the exact offline replay command.
