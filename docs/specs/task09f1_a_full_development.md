# A full-development v2 comparison

Kyle clarified that the requested full suite means all **310 A development
candidates**, not the locked A24 calibration panel. The accepted execution uses
the existing `task09f1.no_answer.conclusion.v2` prompt on GLM, Luna and Haiku,
three repetitions each: **930 judgments per model, 2,790 total**. No prompt tuning,
label changes, benchmark test/reserved access or model selection is included.

## Frozen inputs and labels

The [candidate publication](task09f1_no_answer_candidates_v1_result.json) binds
`09f1_a_candidates_20261016_v1` to the 19 development questions and its completion
seal. Exact model input remains only `candidate_conclusion`. All 310 unique
payloads and proposed labels are retained: 97 clean abstentions, 175 substantive,
38 ambiguous. These labels are agent-reviewed proposals, **not human gold**.
The accepted A24 calibration subset overlaps this development pool.

All 33 `requires_human_attention` cases remain included. Report those separately
from the 277 unflagged cases without relabeling or silently excluding them. Their
three-epoch observation counts are 99 and 831 respectively, per model. Original
review notes and uncertainty flags remain native sample metadata, never requests.
The 20 deterministic guard fixtures are not model calls or semantic test cases.

## Native execution

A-only entry point: `no_answer_full` in `er_commons.no_answer_inspect`; it loads
only this explicit publication through `er_commons.no_answer_development`.
V2 is selected explicitly for this full run; earlier factory defaults and logs
are preserved. The [native execution boundary](task09f_inspect_native.md) still
applies: Inspect owns generation, SDKs, connection management, retries, epochs,
logging and resumption. No custom transport/scheduler/budget framework is added.

No other evaluation process was active at preflight. Use four concurrent samples
and four static connections per model, models sequentially GLM/Luna/Haiku. Recheck
traffic before moving providers. Response caching remains disabled. Transport
retries remain two Inspect retries with the inherited provider SDK policies;
whole-sample retries stay zero. Continue past sample execution errors so other
planned observations can finish; preserve them in accounting. Invalid judgments
are never rerolled. Other settings stay 4,096 output tokens, medium reasoning,
120-second request/45-second attempt timeouts and a 150-second sample limit.
The USD0.10 limit is per-sample and soft, not a hard aggregate invoice ceiling.
Native transport recovery can increase billed attempts beyond 2,790 judgments.

Fresh artifacts live under
`pipelines/brisbane_baylands/task_09/09f1_a_full_development_v2/` beneath the configured
external data root. `started.json` records authorization, exact source/prompt/data
identities, settings and traffic check. Use one fresh native log per model:

```bash
uv run --env-file .env inspect eval src/er_commons/no_answer_inspect.py@no_answer_full \
  -T condition_id=fireworks_glm --epochs 3 --max-samples 4 --max-connections 4 \
  --retry-on-error 0 --no-fail-on-error --cost-limit 0.10 --log-model-api --display plain \
  --log-dir /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_full_development_v2/glm
```

Then use `openai_generation` / `luna` and `anthropic_generation` / `haiku` after
reviewing the preceding completed log. No earlier responses are reused.

## Requested reporting

- Correct judgments / 930, using all planned observations as denominator.
- Cases correct in all three epochs / 310; missing/invalid outputs prevent a pass.
- Unstable cases: three valid classifications with at least two distinct labels.
  Report incomplete/invalid cases separately; neither is a semantic prediction.
- Total estimated cost, mean/median/p95 sample latency, and model-run elapsed time.
- Valid coverage, output and execution failures, retries, cache usage, per-class
  confusion and abstention errors, plus flagged/unflagged partitions.

“Correct” means agreement with the published proposed labels. These are correlated
synthetic development cases; this is not held-out qualification. Preserve every
raw explanation and error. Bounded independent review checks data/prompt isolation,
accounting and salient disagreements; do not automatically adjudicate labels.

## Completed outcome

All 2,790 planned judgments completed with the existing v2 prompt and unchanged
labels. The [result pointer](task09f1_a_full_development_v2_result.json) binds the
sealed native logs, full report and independent review.

| Model | Correct /930 | Correct all three /310 | Unstable cases | Estimated USD | Mean sample seconds |
| --- | --- | --- | --- | --- | --- |
| GLM | 911 | 300 | 6 | 0.103468 | 1.124 |
| Luna | 914 | 302 | 5 | 0.081640 | 1.791 |
| Haiku | 885 | 292 | 6 | 0.060486 | 1.335 |

Total estimated cost: USD0.24559349. GLM had one trailing-comma JSON failure,
retained as invalid without a replacement judgment; all other outputs were valid.
No execution errors or Inspect-reported retries occurred. Haiku had provider
prompt-cache reads in 926 samples. No model was selected.

Luna has the highest agreement in this run, but the small difference from GLM
does not establish broad superiority. GLM made six false-abstention judgments
(four against substantive labels); Luna made none but missed five abstentions.
Haiku made three false abstentions and missed fourteen. The full report retains
confusion, ambiguity errors, latency distributions and uncertainty partitions.

Validation: 79 focused A tests passed; full `make check` passed with 4,875 tests
passed and one skipped, plus formatting, lint and type checks. Independent review
verified all 2,790 observations, exact prompt/input/label isolation, epoch
identities, source hashes and reporting. No accounting findings remain.

Offline replay (no model calls):

```bash
uv run python /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f1_a_full_development_v2/summarize.py
```

Kyle subsequently selected Luna with the existing v2 prompt. The
[selected A handoff](task09f1_a_inspect_handoff.md) closes A's 09F.1 development
scope and records the remaining 09G/Task 12 work. The sealed comparison remains
an unchanged pre-selection result; no further inference or relabeling is implied.
