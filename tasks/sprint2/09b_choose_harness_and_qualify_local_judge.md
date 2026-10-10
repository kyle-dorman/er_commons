# Task 09B — Choose the harness and qualify local inference

Status: provisional; revise from the accepted 09A outcome before activation.
This contract does not authorize model downloads or runs during planning.

## Abstract

Choose the smallest maintainable evaluation runner and establish whether the
local judge candidate can process representative evidence at a practical speed.
This is a bounded infrastructure decision, not full judge implementation or proof
of semantic reliability. The [Task 09 umbrella](09_build_evaluation_and_qualify_judges.md)
owns sequence and shared boundaries.

## Goal

Select Inspect AI or a thin package-backed runner, then document an executable
transport/output contract for independently implemented grounding and adequacy
judges. Treat `gemma3:12b` through Ollama as a candidate requiring qualification.

## Inputs

- Accepted [09A](09a_create_synthetic_challenges.md) outcome and a small development
  tuning sample (exclude 09A reserved final-check variants), with synthesis
  expectations excluded from model inputs.
- [08H release](../../docs/specs/task08h_final_result.json), its 19-development /
  30-test boundary, [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  and the [evaluation contract](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary).
- [Architecture](../../docs/architecture.md), [artifact rules](../../docs/data_artifacts.md),
  installed runtime/hardware capabilities and available local model metadata.

## Outputs

- A compact decision note: selected runner, rejected alternatives, dependency
  versions, ownership boundaries, and why the choice fits saved-answer evaluation.
- A minimal maintained inference adapter or selected-framework integration,
  portable configuration and separate request/result schemas.
- External qualification receipts recording exact inputs, raw outputs, validation,
  elapsed time, token/context settings, failures and repeatability observations.
- Exact model digest/quantization, Ollama version, runner version, prompt/schema
  hashes, decoding settings and an estimated full challenge-run duration.

## Research / learning checkpoint

Inspect's [providers](https://inspect.aisi.org.uk/providers.html),
[model grading](https://inspect.aisi.org.uk/model-graded.html), and
[logs](https://inspect.aisi.org.uk/eval-logs.html) describe provider integration,
custom grading and trace retention. Compare these to the work a thin runner must
own: retries, persistence, resumption, input separation and reporting. Review
[Harbor's task format](https://docs.harborframework.com/tasks/overview) briefly;
its environment/verifier model is a considered alternative, not a required agent
sandbox for this saved-answer workflow. Review
[Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).
Explain that schema-valid output is not evidence of correct judgment. These
primary sources were checked on 2026-10-09; verify behavior against chosen versions.

## Plan / spec requirement

1. Write a short comparison using the same representative saved answer and
   separate prototype grounding/adequacy inputs. Timebox the comparison to a few
   hours; do not implement two production harnesses.
2. Inspect local capability and resolve exact model identity. Any download or
   model change must be explicit in the execution scope, never a silent fallback.
3. Define transport, timeouts, bounded infrastructure retries, concurrency,
   immutable attempt storage and exact-input resumption before implementing glue.
   Preserve malformed outputs and semantic failures; never retry until a desired
   score appears. Result errors must remain distinct from rubric scores.
4. Exercise short, typical and large development evidence packets for both input
   shapes. Measure complete context fit including output reserve, valid structured
   results, practical latency and a few obvious semantic contrasts. Temporary
   prototype prompts are not accepted 09E/09F judge implementations.
5. Record pass/hold findings and actual throughput. If context, reliability or
   runtime is unsuitable, report a concrete model/runtime decision rather than
   broadening prompt experimentation or silently switching to hosted inference.

## Validation

Use transport fixtures for timeout, malformed response, retry limits and resumed
attempt behavior. Validate exact request/result serialization and no reference or
expectation leakage into the grounding prototype. Save measured context and timing
evidence; record unsupported runtime options rather than implying determinism.
Run `make fix`, `make check` for implementation and `git diff --check` for docs.

## Acceptance criteria

- One runner is selected with a maintainable, minimal integration boundary.
- Candidate qualification is supported by saved local receipts or an explicit
  blocker; no untested model capability is marked passed.
- Both independent judge input shapes can be served without silent truncation,
  score substitution, swallowed failures or hidden model fallback.
- Exact identities and practical run-budget findings are recorded for 09C–09G.

## Review pass

Use bounded tooling/architecture and provenance reviews. Check that convenience
features cannot leak labels, mutate prior attempts, or turn failures into scores.

## Non-goals

No benchmark target runs, held-out test use, agentic environment, broad framework
survey, model sweep, full semantic calibration or final judge prompt freeze.

## Outcome

Pending. Record the selected stack, measured limits, validation and next-task
contract revisions here when executed.
