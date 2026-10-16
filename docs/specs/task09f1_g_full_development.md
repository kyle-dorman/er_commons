# G full-development v3 comparison

Kyle authorized the full G candidate pool on GLM, Luna and Haiku using the
accepted-for-comparison explanation-first v3 prompt, with three repetitions and
correctness, all-three-correct, p90 latency and cost reporting. This is the
broader development set, not the held-out benchmark questions.

## Frozen scope

The [candidate publication](task09f1_grounding_candidates_v2_result.json) contains
615 points from the 19 development questions. Use all **611 binary eligible cases**:
247 supported and 364 unsupported, giving **1,833 judgments per model / 5,499 total**.
Four unresolved cases remain explicitly excluded from binary scoring and inference:
G-C001-032, G-C017-033, G-C028-017 and G-C036-022. The six published duplicate
exclusions and 57 mechanical citation/loading fixtures are not semantic cases.
Preserve their prior dispositions; do not manufacture labels to fill the pool.

The labels are independently reviewed agent proposals, not human-approved gold.
The 36 accepted calibration cases overlap this set and retain exact payloads and
labels. Report both full-pool and calibration/non-calibration partitions (36/575).
These correlated development examples do not establish held-out qualification.
No prompt tuning or relabeling follows automatically from disagreements.

## Execution

Reuse native Inspect through the G-specific full-development loader and
`point_grounding_full` task. Each request contains only question, point_text and
owned evidence. Labels, mechanisms and review notes remain outside model input.
Use the exact [v3 prompt](task09f1_grounding_judge_prompt_v3.md), with reason-first
native schemas for Luna/Haiku and prompt-only JSON guidance for GLM.

At preflight check for concurrent provider traffic. Run models sequentially,
four concurrent samples and four static connections per model, following the
existing A full-development execution scale. Other settings remain: three epochs,
4,096 maximum output tokens, medium reasoning, 120-second request and 45-second
attempt timeout, 150-second sample limit, two native transport retries and zero
whole-sample retries. Result caching is off; native prompt caching remains on where
configured. Preserve errors and invalid outputs without semantic rerolls.
The USD0.10 soft limit is per sample; no hard aggregate invoice or wall-time cap
is claimed. Stop after the 5,499 scheduled observations; native recovery can add
transport attempts. No custom scheduler, transport or budget framework.

Fresh outputs belong under
`pipelines/brisbane_baylands/task_09/09f1_g_full_development_v3/` beneath the configured
external root. Freeze manifest, source hashes, separate inputs/labels, exclusions,
exact prompt, generation settings and implementation before dispatch. Preserve
one native log per model and seal reports only after independent review.

## Metrics and validation

Correct judgments use all 1,833 planned observations per model as denominator.
Cases correct all three times use 611 cases; missing/invalid/failed observations
prevent a pass. Report valid coverage, false accepts/rejects, confusion, instability,
mechanism breakdowns and the 36/575 overlap partitions alongside requested metrics.

P90 latency is the nearest-rank 90th percentile (sorted value at ceil(0.9*n)) of
native sample completion minus start time, in seconds. It includes time spent
within a sample waiting/retrying; it is measured at concurrency four, not a
single-request hardware benchmark. Report timing coverage and model-run elapsed
time separately. Cost uses exclusive native uncached/cache-read/cache-write/output
token buckets and frozen profile rates, not invoice reconciliation. Reasoning
tokens are already included in output tokens.

Before calls, test source integrity, development scope, exclusions, label separation,
unchanged calibration behavior, task configuration and reporting denominators/
latency/cost. Run full project checks and independent preflight review. After calls,
recompute from raw logs, verify identities/settings/schema order, audit accounting,
and inspect salient failures against sources. A/C/S and prior results remain
unchanged. No automatic model selection or default replacement.

## Completed outcome

All 5,499 scheduled judgments completed. The
[result pointer](task09f1_g_full_development_v3_result.json) binds inputs, native
logs, reports and independent audits. The v3 prompt stayed fixed throughout.

| Model | Correct / 1,833 | Correct all three / 611 | P90 sample seconds | Estimated USD |
| --- | --- | --- | --- | --- |
| GLM | 1,824 | 607 | 1.937620 | 1.16136086 |
| Luna | 1,822 | 604 | 2.866966 | 0.44425775 |
| Haiku | 1,819 | 605 | 2.668517 | 1.04246132 |

Total estimated cost: **USD2.64807993**. GLM had three invalid outputs, one per
repetition of G-C045-027, retained without replacement. All other outputs were
valid. No execution errors, reported retries or result-cache reuse occurred.
GLM had 2 false accepts / 4 false rejects; Luna 0 / 11; Haiku 4 / 10.

Outside the calibration overlap, correct / 1,725 and all-three-correct / 575 are
GLM 1,718 and 572; Luna 1,714 and 568; Haiku 1,714 and 570. Calibration overlap
results are GLM 106/108 and 35/36, Luna 108/108 and 36/36, Haiku 105/108 and 35/36.
This fresh run includes the same diagnostic cases without reusing their outputs.

GLM leads this run on agreement, all-three consistency and latency. Luna costs
less than half as much and produced only valid outputs, with no false accepts
against the proposed labels. Haiku has fewer all-three failures than Luna but
more erroneous judgments and higher cost. These small accuracy differences do
not establish general superiority. Several disagreements involve plausible
wording or proposed-label issues; the source review preserves those separately
without changing labels or scores. No model or default was automatically selected.

Validation: full `make check` passed with **4,913 passed, one skipped**, plus
formatting, lint and type checks. Independent review recomputed every observation,
all-three counts, p90 and token costs, and verified request settings and the
36/575 partitions. The full run uses four active samples and four provider
connections. A brief GLM dispatch pause for runtime auditing remains included
in native timings; no judgments were discarded or repeated.

Reporting learning: native logs distinguish a base model configuration from
the effective task/request configuration. The header retained one connection;
the task plan, every request and runtime semaphore used four. Reporting verifies
each layer separately and normalizes typed optional schema defaults before
comparison. Two preserved reporting-only revisions correct those validations;
the frozen execution manifest, prompts, inputs and generation settings were not
changed. Native raw outputs are scored as emitted.

Offline replay uses `scripts/analyze_point_grounding_development.py` with the
run root and `--reporting-revision` pointing to `reporting_revision_v2.json`.
Reporting is create-only; preserve the published analysis directory. The external
`audit_independent.py` records the separate reproducible audit.


## Subsequent user selection — 2026-10-16

Kyle selected **Luna with prompt v3**, prioritizing its observed valid outputs and
lower cost. The [selected configuration](../../configs/point_grounding_selected_v1.json)
binds the exact model/prompt/schema/profile identities to this preserved comparison;
the [G handoff](task09f1_point_grounding_handoff.md) owns the current selection and
09G/Task 12 boundary. The full-development factory already defaults to Luna/v3.
The sealed comparison and its pre-selection result pointer remain unchanged.
