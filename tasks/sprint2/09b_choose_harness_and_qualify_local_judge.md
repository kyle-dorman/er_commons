# Task 09B — Choose the harness and qualify judge inference

Status: **Complete with operational and semantic limitations, including the additional-model comparison.**
The user authorized Inspect AI, local Ollama, both Gemma 4 12B and Qwen3.5 9B,
original 16-bit precision first, downloads/internal storage, minimal integration,
qualification and review. No container or judge tools. A local closeout commit
was separately authorized after the accepted MVP quality pass; no push is authorized.

## Abstract and goal

Select a maintainable saved-answer evaluation runner and qualify local inference
for later, separately implemented grounding and adequacy judges. Successful
inference is not proof of judge accuracy. The [umbrella](09_build_evaluation_and_qualify_judges.md)
owns sequencing; 09C–09G remain provisional and unstarted.

## Inputs and boundaries

- [09A handoff](../../docs/specs/task09a_final_result.json), committed at `eee4edc`:
  546 variants across 19 development cases, including 423 development variants,
  118 reserved final checks and five exclusions. Unchanged controls remain separate.
  Select by final reservation and `comparison_eligible`, not the earlier
  `agreement_eligible` field or representative-record list.
- Preserve the frozen 19-development/30-test benchmark split. No test questions,
  references or reserved answer payloads are inspected for this qualification.
- Grounding receives the question, saved answer and its actual cited evidence.
  Adequacy independently receives the permitted reference and reviewed evidence.
  Neither receives expectations, edits, categories, revealing IDs, gold roles,
  pipeline provenance or official responses. Anonymize nested point links too.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [architecture](../../docs/architecture.md) and [artifact rules](../../docs/data_artifacts.md)
  remain authoritative. Synthetic expectations are proposals, not human labels.

## Selected design and learning notes

**Inspect AI is the evaluation framework; Ollama is the serving runtime; Gemma
and Qwen are the models.** Those are separate choices. Inspect organizes samples,
solvers, scorers and logs; Ollama executes model weights; the model supplies the
judgment. A Python environment manages dependencies. With no tool execution,
a container adds little to this task's actual boundary: explicit data projections
and local-only inference. This is not a general claim that an environment is a
security sandbox.

A small invented example: a passage assigns monitoring to an association, while
an already-saved answer assigns it exclusively to the city. An Inspect `Sample`
represents that saved answer and allowed evidence. A `Task` joins a loader
`solver` with a custom `scorer`; the solver copies the answer without generating
a new one. The grounding scorer sees only actual citations. An independent
adequacy scorer also sees the reference. Neither gets the expected score.

Inspect supplies the execution/scoring lifecycle, evaluation logs and viewer.
We still implement our information boundaries, rubric/schema, exact model identity,
context protection, raw native API receipts and checksum-bound recovery. A thin
project runner would remove framework concepts initially but leave execution and
reporting machinery to maintain locally. Only the Inspect integration was built;
there is no second production runner. The native transport remains replaceable.

Ollama was chosen for convenient Mac installation and model management. Direct
llama.cpp gives more explicit serving/file control; MLX is Apple-focused. Neither
alternative was implemented or performance-qualified. Harbor's sandbox workflow
is unnecessary for text-only scoring. Prime Intellect Verifiers supports evaluation
as well as training, but its interface transition offers little benefit in this
non-training arc. The new `verifiers.v1` preview is distinct from its legacy
interface, not a deprecated v1 waiting for v2.

Primary documentation checked October 10:

- Inspect [tasks](https://inspect.aisi.org.uk/tasks.html),
  [custom scorers](https://inspect.aisi.org.uk/custom-scorers.html),
  [logs](https://inspect.aisi.org.uk/eval-logs.html), and
  [providers](https://inspect.aisi.org.uk/providers.html).
- Ollama [structured outputs](https://docs.ollama.com/capabilities/structured-outputs),
  [context allocation](https://docs.ollama.com/context-length),
  [Mac support](https://docs.ollama.com/macos),
  [Gemma tags](https://ollama.com/library/gemma4/tags), and
  [Qwen tags](https://ollama.com/library/qwen3.5/tags).
- [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md),
  [MLX-LM](https://github.com/ml-explore/mlx-lm),
  [Harbor](https://docs.harborframework.com/tasks/overview), and
  [Verifiers announcement](https://www.primeintellect.ai/blog/verifiers-v1).

### Native API and identity choices

Inspect's built-in Ollama provider uses OpenAI compatibility. In Ollama 0.40.2,
that route does not forward `truncate:false` or `shift:false`. The custom Inspect
scorer therefore uses HTTPX to call native `/api/chat`, retaining the exact request
and raw HTTP response separately. `log_model_api=True` does not capture this direct
HTTP call. See pinned [native flags](https://github.com/ollama/ollama/blob/v0.40.2/api/types.go#L159-L176)
and [compatibility conversion](https://github.com/ollama/ollama/blob/v0.40.2/openai/openai.go#L801-L813).

A model tag is not enough identity. Qwen's `9b-bf16` tag reports actual GGUF **F16**,
while Gemma's `12b-it-bf16` reports **BF16**. Both are 16-bit formats; expanding
weights to FP32 would not restore absent precision. Qwen's first load triggered
Ollama's [compatibility migration](https://github.com/ollama/ollama/blob/v0.40.2/compatmigrate/migrate.go#L1-L8),
which preserved the original and created a llama.cpp-compatible representation.
The first smoke inference remains evidence under its original identity and is
excluded from the comparison. Seven later preflight attempts blocked the changed
digest without making model calls. A new alias pins the converted representation;
post-call alias, loaded-model and runtime checks now precede accepted judgments.

## Implementation and bounded plan

`judge_qualification_packets` makes only these temporary qualification projections:
six control packets for C041/short, C037/typical and C014/large, each in both
judge shapes, plus two eligible C041 development contrasts. It verifies the 09A
bindings before intake, filters reserved rows before decoding selected answer
payloads, allowlists nested fields and preserves complete source text/tables.
Provenance/expectations remain separate. The initial projection was never sent to
a model; reviewed `qualification_packets_v2` removes nested receipt/extraction paths.

`judge_qualification` runs one saved-answer Inspect Task per attempt. Failures are
not scores. Requests, native responses, model/runtime checks, Inspect logs and
elapsed time are immutable; completion seals an exact inventory. The run binds
packets, settings, prompts/schema, Inspect version and an adapter source snapshot.
Only verified successes are reused as successful judgments. On resume, permanent
or exhausted failures are retained without blocking later unfinished packets; the
CLI exits nonzero if any result failed. There is no automatic retry; at most two
attempts allow one explicit infrastructure retry. Semantic/output/context and
identity/request failures cannot retry under unchanged settings. New settings
require a fresh namespace.

Execution uses Inspect 0.3.278, HTTPX 0.28.1 and Ollama 0.40.2 with llama.cpp/Metal,
loopback only, cloud disabled, one loaded model/request, f16 KV cache, temperature
0, seed 42, thinking disabled, 1,500 output tokens and a 300-second timeout.
Inherited model sampling defaults are also preserved in identity receipts.
The original comparison used no 8-bit/4-bit fallback or hosted inference.

Start with six size/shape controls plus two contrasts per candidate, then one
repeat per shape and a recorded interruption/resume. Qwen's full large inputs
were rejected at 32,768 tokens: they require 35,057 and 36,437 input tokens.
Increase allocation to **49,152 (48K)**, preserving the output reserve, and rerun
only those rejected packets. Short repeats and Gemma use 48K. Qwen typical timings
remain 32K measurements; do not present a fully fixed-context speed benchmark.
No evidence is shortened and no prompt is tuned to a desired score.

The restart probe interrupts after request persistence, before provider I/O;
resumption retains the incomplete attempt and makes the outstanding call.
Completed resumption must make zero provider calls. This does not demonstrate
recovery from an interrupted active generation.

## Current interfaces and artifacts

Use `make prepare-judge-qualification QUALIFICATION_PACKETS=DIR` to reproduce the
bounded projection. Use `make run-judge-qualification` with `QUALIFICATION_PACKETS`
(the JSON file), `QUALIFICATION_OUTPUT`, `QUALIFICATION_MODEL`,
`QUALIFICATION_IDENTITY` and `QUALIFICATION_CONTEXT`; optional output/timeout
variables override the documented defaults. A local alias must expose the exact
context and its identity file must include digest and runtime version. Changed
code/configuration requires a new output directory, not an overwritten attempt.

Models are stored internally in `~/.ollama/models`; they load into memory when
used. Initial internal free space was about 383 GiB. Receipts live externally at
`pipelines/brisbane_baylands/task_09/09b_20261010_v1/` beneath the configured data
root. Setup logs retain installation, original and converted model identities,
context revisions, source snapshots, test/review evidence and the longer research
notes. No source material is sent to a new external provider.

## Validation and review

Run `make fix`, `make check` and `git diff --check`. Focused tests cover reserved
routing, input projections, identity/context mismatch, missing token evidence,
HTTP errors/timeouts, malformed output, output limits, retries, interrupted
attempts, checksum tampering and adapter snapshot drift. Independent packet,
runner and receipt reviews must resolve actionable findings before closeout.

## Acceptance and non-goals

The deliverable is one maintained integration plus measured operational capability,
limitations and a later challenge-run budget. Schema validity does not imply a
correct judgment. No 09C–09G activation, test evaluation, benchmark target generation,
reserved final checks, ensemble, broad model sweep, training, commits or pushes.

## Outcome

Operational qualification and independent review are complete.
The [result pointer](../../docs/specs/task09b_final_result.json) binds the external
summary and exact namespace inventory.

**Selected operational default:** Inspect + native Ollama, Qwen3.5 9B **F16**,
49,152-token context, with the settings above. Gemma 4 12B BF16 is a tested
alternative. Both completed eight selected packets and two repeats successfully;
no lower-precision fallback was needed. This selects infrastructure for subsequent
judge development, not accepted semantic judges.

| Candidate | Short calls (warm repeats) | Typical calls | Large calls | Largest input |
| --- | ---: | ---: | ---: | ---: |
| Qwen F16 | 19–25 s | 38–41 s | 120–127 s | 36,437 tokens |
| Gemma BF16 | 29–31 s | 46–74 s | 244–262 s | 40,196 tokens |

Hardware: M3 Max, 14 CPU/30 GPU cores, 36 GiB unified memory. Ollama reported
roughly 16.9 GiB loaded for Qwen at 48K and 22.9 GiB for Gemma. Sampled system swap
rose from about 0.9 GiB initially to about 10 GiB with Qwen and 17 GiB with Gemma.
These are shared-machine observations, not isolated hardware benchmarks or exact
peak-memory measurements. Both models remain installed internally (about 58.4 GiB
including the preserved Qwen compatibility representation); about 306.7 GiB remained
free. Models were unloaded and the temporary local server stopped after testing.

For **(423 development variants + 19 controls) × 2 judges = 884 calls**, an
illustrative equal mix of short/typical/large packets gives **14.8 hours Qwen** or
**28.1 hours Gemma**, excluding recorded model-load time and adding actual cold
starts separately. All-short versus all-large scenarios span 5.4–29.4 hours for
Qwen and 7.4–62.1 hours for Gemma. These are not confidence bounds: population size
weights, future prompts, output lengths, retries and machine load are unmeasured.
No prompt-cache discount is assumed. Reserved final checks are excluded.

### Measured limitations and restart evidence

- The 32K Qwen requests failed visibly at the actual complete input lengths;
  48K worked. This does not establish the advertised 262K context ceiling.
  Actual responses were far shorter than the 1,500-token cap; a future verbose
  Gemma judgment may exceed the 300-second timeout even when its input fits.
- Qwen assigned score 2 to the grounding contrast despite missing cited support
  for feeding-station restrictions, MPOA monitoring and fines. Independent
  inspection confirmed that specific defect; the exact 0/1 distinction remains
  rubric-dependent.
- Gemma also assigned 2, despite an explanation saying 1 was appropriate. It
  additionally assigned 2 to the adequacy contrast that incorrectly substitutes
  exclusive city enforcement authority; Qwen assigned 0. These are diagnostic
  counterexamples, not an accuracy estimate or prompt-tuning exercise.
- Thinking was disabled and inherited model sampling defaults were recorded,
  not normalized into a general model-quality benchmark. Neither configuration
  is established as the model's best judgment setup.
- Both short output texts matched their repeats exactly. Gemma held 48K fixed;
  Qwen compared 32K originals with 48K repeats. Two examples do not prove general
  determinism. Both completed-resume checks made zero provider calls; Gemma's
  saved proof also ran with the local server stopped.
- The interrupted Qwen request survives unchanged in attempt 001; successful
  attempt 002 uses identical request bytes. This tests a pre-provider interruption,
  not active-generation recovery.
- The ledger contains 31 attempts: 21 successful inferences (including the initial
  smoke inference excluded from comparison), nine transport errors (seven preflight
  identity refusals and two context refusals), and one pre-provider interruption.
  Only 23 native inference requests were made; 20 successes form the qualified
  base/repeat comparison. Failed and superseded evidence remains immutable.

### Validation and follow-through

Independent packet, runner and receipt audits resolved nested provenance leakage,
runtime/retry/error guards, post-call model identity drift and missing offline
reuse proof. Exact input boundaries, receipt inventories, checksum integrity,
repeat equality and runtime arithmetic were independently verified. The final
namespace seal is additionally verified after publication.

`make fix` passed. Final `make check`: **3,443 passed, one skipped, three
pre-existing Task 06G historical commit-pin failures**, matching the 09A outcome.
Formatting, lint and types passed; all **30 new focused tests** passed.
`git diff --check` passed. The failing historical code/tests were not changed.

09C–09G remain unstarted. The next authorized task should refresh 09C from the
09A handoff and this outcome. It must retain complete evidence and validate actual
packet length; later 09E/09F must address the observed semantic failures before
09G can challenge/freeze any judge. No benchmark targets, test evaluation, reserved
final-check variants, commits or pushes were performed.

## Authorized additional-model qualification

On October 10 the user requested Nemotron 3 Nano 4B BF16 and Ornith 1.5 9B
using the same eight development packets and two short repeats. Preserve the
original sealed namespace; write new receipts under
`09b_20261010_additional_models_v1`. Use the unchanged adapter, 48K context,
1,500 output tokens, 300-second timeout and thinking disabled. Inspect published
precision and actual runtime identity before comparison. Capture failures without
silent model substitution; review receipts, reuse evidence and duration estimates
before closing the extension. No later task or reserved/test evaluation is authorized.

### Additional-model outcome

The unchanged adapter evaluated the same eight packets plus q01/q03 repeats at
48K. Nemotron's `4b-bf16` tag actually reports **F16**; Ornith 1.5 9B reports
**Q4_K_M**, with its packaged vision projector unused by these text-only calls.
The comparison therefore includes different precisions and inherited sampling
defaults. Both use llama.cpp/Metal, thinking disabled and the original output cap.

| Additional candidate | Base completion | Short repeats | Typical calls | Large calls |
| --- | --- | ---: | ---: | ---: |
| Ornith 1.5 9B Q4_K_M | 7/8 | 19–21 s | 33–44 s | Grounding failed at 191 s; adequacy 168 s |
| Nemotron 3 Nano 4B F16 | 8/8 | 10–13 s | 34–35 s | 93–107 s |

Ornith's first repeat includes a 3.6-second cold load; these are observed timings,
not isolated throughput measurements. Ollama reported approximately 8.2 GB loaded
for Ornith and 8.6 GB for Nemotron. Largest input counts were 36,437 and 42,512
respectively. All inputs fit the 48K allocation with the original output reserve.
Ornith q07 exhausted all 1,500 output tokens before completing JSON; it is an
`output_limit` failure, not a score, and was not retried with a larger budget.

Ornith lowered both contrast scores to 1, identifying missing cited support and
the City/association authority substitution. However, it falsely rejected the
q05 grounding control (score 0): S4 explicitly supports the temporary loss of
macroinvertebrate productivity it claimed was unsupported. Nemotron assigned 2
to both contrasts, missing the unsupported claims and authority substitution.
These independently reviewed examples do not establish overall accuracy or a
model ranking. Qwen remains the operational development default; Nemotron is a
lighter, faster tested alternative, while Ornith is not fully qualified under
this output budget. No model is accepted as an accurate judge.

All four short repeated output texts matched their originals exactly at fixed
48K. With the server stopped, the saved reuse probe verified four successful
receipts with zero provider calls. No additional active-generation interruption
claim is made. Twenty inference calls produced 19 successes and one output-limit
failure, all preserved in a separate namespace; the original 428-file seal is
unchanged. Models remain installed locally, but were unloaded and the server stopped.

For the same illustrative 884-call workload, Nemotron extrapolates to **12.0 hours**
under equal short/typical/large weights, excluding recorded model loads and adding
actual cold starts separately. All-short/all-large scenarios span 2.8–24.5 hours;
these are not confidence intervals. Ornith has no successful full-run estimate
because the large grounding probe failed. No broader challenge run was performed.

Primary research: [Ornith package](https://ollama.com/library/ornith-1.5:9b),
[Ornith reported benchmarks](https://ornith.ai/ornith_1_5.html),
[Nemotron package](https://ollama.com/library/nemotron-3-nano:4b-bf16), and
[NVIDIA's specific 4B card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16).
The 4B model is compressed from Nemotron Nano 9B v2; it is not the 30B MoE described
in the generic family listing. NVIDIA's reasoning-off HaluEval result is relevant
background, not a Mac/Ollama judge-accuracy measurement. Ornith's coding/agent
benchmarks use configurations different from this nonthinking Q4 test.

The extension changes no production code. All 30 focused regression tests passed, and an
independent receipt/semantic audit accepted this addition; the original full-suite
result and its three known historical failures remain the implementation baseline.
The result pointer retains the original result and binds the additional namespace.

## Authorized Ornith concise-output probe

The user authorized an Ornith-only prompt experiment: append an explicit short
evidence-ID instruction, first test q02 (472 tokens, the longest original short
response), and proceed to the failed large q07 only if JSON remains valid, output
shrinks and the missing-support diagnostic survives. Keep the 1,500-token cap and
all other settings. Use a separate external adapter snapshot and namespace
`09b_20261010_ornith_concise_v1`; do not change the production prompt or run other
models. Preserve all prior sealed evidence and benchmark boundaries.

### Concise-output probe outcome

One Ornith q02 call tested the exact additional instruction: “Cite evidence using
its supplied ID, such as S1. Give one brief sentence explaining its relevance.
Do not reproduce passages or inventory every source.” The output shrank only
472→451 tokens (4.4%), still quoted long passages, and regressed from score 1 to 2,
losing the diagnostic about unsupported feeding-station/MPOA/fine claims. JSON
was valid, but the conditional gate failed. **q07 was not run**, and the cap remains
1,500. This does not establish that concise prompts generally harm accuracy;
it records one unsuccessful wording change on one packet.

Independent review verified the exact prompt-only change, unchanged payload,
schema/model/settings and all 12 attempt files. Offline reuse succeeded with the
server stopped and no new attempt. No production code or prompt was changed;
no implementation tests were necessary for this external prompt experiment.
The negative result is sealed separately and linked from the result pointer.
Ornith remains limited under the existing output budget; earlier evidence stands.

## Small Qwen development-speed probe

The user set Ornith aside and authorized a final smallest-Qwen comparison for
fast development cycles. Use Qwen3.5 0.8B, the smallest model in the selected
family, starting with its published 16-bit package (about 1.8 GB). Retain the
original adapter/prompt, 48K context and 1,500-token cap; run the same eight
packets and two short repeats in `09b_20261010_qwen_small_v1`. Evaluate speed,
structured output, context handling and repeatability separately from semantic
quality. No other models, reserved inputs, later tasks or commits are authorized.

### Small-Qwen outcome and development roles

**Use Qwen3.5 0.8B F16 for fast live integration smoke checks.** Keep Qwen3.5 9B
F16 as the substantive judge-development baseline, whose accuracy is still
unqualified. Ornith is set aside at the user's request; retain its evidence and
installed files without further runs. These roles do not select an accurate judge.

The 0.8B package's `bf16` tag reports actual F16. First load triggered Ollama's
compatibility conversion; the postflight identity guard rejected that call and
seven subsequent attempts refused before inference. A new alias pins the
converted representation: `er09b-qwen-small-48k:v2`. It then completed all eight
packets and two repeats with the original adapter, 48K context, thinking off and
1,500-token cap. Ollama reported roughly 2.8 GB loaded. Short calls took 3.5–6.4 s,
typical calls 6.3–7.3 s, and large calls 22.3–23.3 s. Both repeated output texts
matched exactly. Offline completed-result reuse made zero provider calls.

All eight scores were 1. The q02 explanation used a claim from the answer itself
as support instead of identifying missing cited evidence; q04 called the wrong
City authority correct. Other rationales described fully supported claims while
assigning 1. Thus this model can exercise transport, structured-output parsing,
logging and restart plumbing, but must not drive rubric/prompt selection,
semantic regression decisions or reported benchmark judgments. Deterministic
fixture tests remain preferable where no actual model call is needed.

An illustrative 884-call equal-size mix takes 2.9 hours, excluding recorded loads
and adding cold starts/retries; all-short/all-large scenarios span 1.3–5.6 hours.
This estimate shows possible integration-test speed, not an endorsement of a
full semantic challenge run with this model. Eight stable base calls total about
79 seconds, compared with about 412 seconds for the original Qwen9B base calls;
these runs are not hardware-isolated and the older typical measurements used32K.

Use the existing `make run-judge-qualification` interface with
`QUALIFICATION_MODEL=ollama/er09b-qwen-small-48k:v2`, `QUALIFICATION_CONTEXT=49152`,
and the extension's `setup/er09b-qwen-small-48k_v2_identity.json` as
`QUALIFICATION_IDENTITY`. Supply an approved packet file and fresh output directory;
the existing local server setup is still required. No new runner or dependency
was introduced. Receipts and identities are preserved in
`09b_20261010_qwen_small_v1`; the result pointer binds its completion and summary.

Independent review accepted all 18 attempt seals: ten qualified successes, one
post-call identity refusal and seven preflight refusals; eleven native inference
requests total. Input/settings/identity checks, repeats and runtime arithmetic
passed. No implementation changed; existing test evidence is retained and
`git diff --check` passed. No reserved/test inputs or later tasks were used.

## Authorized MVP code-quality pass

The user requested maintainable MVP code rather than a one-off script or
production-grade provenance. Review the two qualification modules and tests,
fix concrete correctness/maintenance issues, extract focused helpers within the
existing module boundary, and retain unchanged prompts and model settings.
Keep existing seals/receipts immutable; changed code uses fresh output folders.
Use deterministic fixtures, `make fix`, `make check`, and independent review.
No new model calls, frameworks, dependencies, later tasks or commits are needed.

### MVP quality-pass outcome

The runner now separates request construction, provider checks, output validation,
attempt execution and resume decisions into named helpers in the existing module.
This keeps source snapshots reconstructable without introducing a framework or
new dependency. The already narrow packet projection remains unchanged.

Concrete fixes: local HTTP clients ignore proxy environment variables; accepted
trailing-slash URLs resolve correctly; empty/invalid packet selections fail early;
postflight verifies the actual loaded context. Permanent request and identity
failures are distinct from transient transport errors. Resume retains failed
packets and continues unfinished ones instead of aborting the batch. Unexpected
execution failures retain useful diagnostics rather than becoming retryable
network errors. Make targets explain missing settings.

Result handling for maintainers:

- `success`: reuse the verified result without a model call.
- `transport_error`: one explicit retry is allowed, up to two attempts total.
- `request_error`, `identity_changed`, malformed/output/context failures, or
  `execution_error`: retain the failed result under unchanged settings; inspect
  the receipt before creating a corrected run.
- Two interrupted attempts: return `retry_exhausted` without writing a third
  attempt. This invocation-level result is not a fabricated completed receipt.
- Any failure leaves the CLI exit status nonzero, while later packets can finish.

Independent review accepted the refactor and independently ran **49 focused tests**.
The new cases exercise proxy isolation, endpoint normalization, loaded context,
permanent-error handling and continuing a partially failed batch. Saved requests
for all eight base packets were compared directly: prompts, rubrics, schema and
native request payloads are unchanged. No live model calls were needed.

Earlier qualification runs remain immutable evidence of their archived adapter.
Because implementation identity changes, use a fresh output directory for the
refactored runner; do not attempt to resume old qualification namespaces with it.
The small-model/live-smoke and 9B/accuracy-evaluation roles remain unchanged.

Quality-pass validation: `make fix` passed; formatting, lint and types passed.
Final `make check`: **3,462 passed, one skipped, the same three known Task 06G
historical failures**. There are no new failures. `git diff --check` passed.
The result pointer links the compact quality-pass summary and check logs; no
new model calls, dependency additions, commits or pushes were made.

## Closeout acceptance

The user approved the MVP quality pass and closed 09B, authorizing a local commit
of its code, tests, dependencies and documentation. Earlier no-commit statements
describe the qualification runs before this separate approval. 09C remains
provisional and unstarted; its contract must be refreshed from these outcomes.
