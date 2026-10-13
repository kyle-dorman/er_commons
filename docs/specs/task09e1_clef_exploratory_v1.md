# Clef exploratory trial — October 12, 2026

The user explicitly requested trying only original inputs that fit, without
truncation or advance exact token counting. This is a scoped exception to Task
09E.1's counting gate for local Clef only, not qualification of an exact counter
or permission for cloud inference.

Use the frozen 69-answer Dev3 panel through the existing Inspect runner. Keep
the 65,536-byte body ceiling. The installed Ollama System One endpoint rejects
context overflow and never truncates; retain any rejection as an unscored error.
Evaluate gates and fitting original points, and attempt conclusions only after
complete valid point decisions. Preserve all 69 answers in coverage denominators.
Do not split points, shorten evidence, change semantics, or retry judgments.

Download only Clef Flash. Pin its digest, quantization, license, runtime and actual
loaded context in fresh external artifacts. Run a tiny invented protocol smoke
first. Bound the panel to 304 calls, one concurrent sample, and 1,800 seconds.
Record native usage and cache fields without claiming exact count parity or cache
savings. Native decision output usage is diagnostic, not generated prose.

Keep default/cloud exact-preflight guards unchanged. Independently review this
exception and focused failure-path tests before the panel run. Preserve the sealed
October 11 artifacts and record this trial in a new namespace.

## Reproduction and runtime

The installed Ollama 0.40.2 automatically selected the Apple MLX asset:
Clef Flash 9.5B, safetensors, MXFP8, Apache-2.0, 12,387,093,750 downloaded
bytes. Digest: `0a2a05d6a581223a9397e6fd2ea92486d4b1a54ec1125065be0c2170ff97ba75`.
The 36-GiB host loaded it fully on GPU. `/api/ps` reported **16,384 tokens** of
context, despite `OLLAMA_CONTEXT_LENGTH=32768`; do not infer a larger allocation
from the environment setting or model marketing. Loaded size: 12,650,319,360 bytes.
`/api/show` resolves the discrepancy: the downloaded model specifies
`num_ctx 16384`, which overrides the environment default. Ollama 0.40.2 passes the
loaded context to the System One scorer as its maximum encoded input size; this
is an enforced limit, not just display metadata. The trial does not change it.
See Ollama 0.40.2's [option precedence](https://github.com/ollama/ollama/blob/v0.40.2/server/routes.go#L130),
[System One context binding](https://github.com/ollama/ollama/blob/v0.40.2/server/routes.go#L991)
and [Clef limit enforcement](https://github.com/ollama/ollama/blob/v0.40.2/mlxrunner/model/clef/encode.go#L25).

The [System One contract](https://docs.ollama.com/api/systemone) states that
oversized input is rejected, never truncated. Native output tokens are a
classification diagnostic, not a prose-generation reservation. Optional
`prompt_eval_cached_count` is retained; absence means unknown. The actual loaded
runtime and native usage are stronger evidence than a byte-to-token estimate.

Current command, after the single `ollama pull clef-flash` and starting Ollama:

```bash
uv run python -m er_commons.grounding_comparison_run \
  --mode run --condition local_clef --exploratory-local-clef \
  --manifest "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/09e_20261011_09a3_small_v1/panel/manifest.json" \
  --output "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/FRESH_CLEF_RUN" \
  --currency-cap 0 --request-cap 304 --output-cap 1 --wall-seconds 1800
```

Load `ER_COMMONS_DATA_ROOT` from the local environment; the CLI does not read
`.env` itself. Output must not exist. The positive output-cap argument is required
by the shared budget object; typed local decisions reserve zero generation tokens.
This command makes no paid calls. The CLI records runtime metadata before and
after; model or runtime drift invalidates the comparison and suppresses analysis.
The frozen manifest still requires all 69 original answers. Cloud commands and
their exact-count gates remain in the [cloud handoff](task09e1_cloud_handoff.md).

The actual trial namespace is
`task_09/09e1_20261012_clef_exploratory_v1/`. Its `smoke.py` is a source-free,
invented three-stage protocol probe through Inspect, separate from `dev3/`.
The smoke produced valid gate, point and conclusion decisions and score 2; it is
not benchmark evidence. The panel is attempted once, with no repair or retuning.

## Measured outcome

The single pass completed all 69 answer records in 915 seconds (15.3 minutes).
It dispatched 258 local requests; all returned structurally valid decisions.
Twenty-one reached stages were skipped before dispatch for exceeding 65,536 bytes.
Sixteen answers were consequently size-blocked. Gate routing and stage dependencies
mean these counts differ from the maximum 304-call offline audit.

| Case | Scored | Classified abstention | Review disagreement | Size-blocked | Ambiguous gate |
| --- | ---: | ---: | ---: | ---: | ---: |
| C041 (22) | 12 | 2 | 8 | 0 | 0 |
| C037 (27) | 10 | 2 | 14 | 0 | 1 |
| C014 (20) | 0 | 3 | 1 | 16 | 0 |
| All 69 | 22 | 7 | 23 | 16 | 1 |

Numeric scores: nine 0s, eight 1s, five 2s. The seven abstention classifications
include **one false exemption against the proposed labels**; they are not seven
verified clean abstentions. All unresolved and size-blocked answers remain
unscored and in the population. C014 produced no numeric scores.

No transport failures, observed token-context overflows, truncation flags, retries,
or paid calls occurred. The largest dispatched body was 33,929 bytes; maximum
native input was 10,238 tokens. The 16K token limit therefore did not reject any
dispatched request in this pass. The byte ceiling was the observed size blocker.
Model digest, runtime version and code identity were unchanged during execution.

Post-run comparisons use uncalibrated synthetic proposals, not ground truth:

- Gate: 68 comparable decisions; six proposed abstentions recognized, one false
  exemption, no misses, one ambiguous/uncompared gate.
- Original point support: 144/166 compared; 27 true-positive, 28 true-negative,
  one false-positive and 88 false-negative decisions relative to proposals.
- Conclusion support: 45/63 substantive conclusions compared; 31 true-positive,
  seven true-negative, one false-positive and six false-negative decisions.
- Twenty-three answers had inconsistent point/review judgments. The analysis
  preserves 139 source-linked disagreement entries for inspection; entries may
  refer to multiple stages of the same answer.

This configuration often rejected points the proposed labels considered supported,
and review inconsistency further reduced numeric coverage. It does not qualify
Clef as a judge. Size-selected coverage and changed quotation/observation contracts
also prevent treating this as a clean model-only comparison with historical Qwen.

Independent review inspected two saved source-linked examples without retuning:
`task09a2-C041-C01-01-545830c610c5` point P2 (CC&R feeding restrictions and
MPOA monitoring/fines, Appendix A section `sec000433`) changed from support
probability 0.295 in the point check to 0.571 in conclusion review. The final answer
correctly stayed unresolved. `task09a2-C014-R02-18-a6228c2cc0c9` received a clean
abstention probability of 0.717 despite asserting that neither development appears
in the cumulative inventory and that F.1 omits both. This illustrates the false
exemption without adjudicating the truth of those substantive assertions.

## Validation

The independent final audit verified all 258 sealed native receipts, all 21
oversized-stage skips, null scores on failures/disagreements, and unchanged code,
configuration and runtime identities. The focused suite passed 268 tests; the
independent exploratory/provider/CLI selection passed 151. Full validation results
are recorded in the [result pointer](task09e1_clef_exploratory_result.json) alongside
the immutable logs. `make fix` and format/lint/type checks passed. Final
`make check`: **4,191 passed, one skipped, the same three historical Task 06G
failures**. An initial check during inference also hit the existing half-second
supervisor timing test; the full post-inference rerun passed that test without
changing its code. Both logs are retained. `git diff --check` passed.

## Caching and preservation

Native receipts report **600,847 input tokens**, **246,313 cache-read tokens**
and zero output tokens across the 258 panel requests. Every receipt reports a
positive cache-read count; cache writes are unknown. This is native evidence of
local prefix reuse, not saved-result replay (none occurred), a controlled cold/warm
latency experiment, or evidence of cloud savings. The invented smoke is excluded
from these totals. Local API charges are zero; electricity costs were not measured.

All 34,055 earlier Task 09 files and 5,352 sealed October 11 offline-result files
passed byte preservation checks. No dataset changes, truncation, point splitting,
reserved/test reads, broader panels, later tasks, commits or pushes were performed.
The locally started Ollama process was stopped after the run; the single downloaded
Clef asset remains available for a future explicitly chosen experiment.
