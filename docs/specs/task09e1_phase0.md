# Task 09E.1 Phase 0: legacy stage execution cleanup

This checkpoint preserves the Task 09E behavior at `f0c57a0`. It precedes all
Task 09E.1 semantic and provider changes.

## Plan and boundary

The staged Inspect adapter currently owns both sample orchestration and the
native per-stage request/preflight/attempt/persistence loop. Standalone abstention
imports that private loop from a different pipeline adapter. Move the loop,
its counter/validator types and native dependencies into `grounding_stage_runtime`.
Both Inspect adapters will call its explicit `run_stage` function. Keep sample
aggregation, scheduling and final sample persistence in their existing owners.
This is a narrow ownership change, not a provider abstraction or a second runner.

Before moving code, freeze invented fixtures for successful staged execution with
an abstention gate, point/conclusion disagreement, malformed point output,
missing exact preflight and standalone abstention. Capture complete persisted
request, schema, stage input, preflight, response and result objects. Normalize
only elapsed time; verify completion seals separately. These small fixtures contain
no benchmark data or live model output.

Move the execution body unchanged. Update direct callers and test patch targets;
add no compatibility aliases. Preserve prompts, schemas, quote validation,
interstage observations, strict errors, two-attempt transient retry policy, model
checks, exact counter gates, CLI behavior and artifact names/formats. Existing
regressions additionally cover overflow, counter mismatch, zero-point handling,
leakage and failure routing. No sealed specification, config or artifact is edited.
New code hashes must be recorded by the new experiment; historical identities
remain historical.

## Validation checkpoint

Run the golden fixtures against the old implementation before extraction, then
against the extracted owner. Run focused grounding, packet/preflight, transport
and counter tests, followed by independent behavioral and maintainability review.
The main task owns final repository-wide validation and the Phase 1+ specification.

The tradeoff is one small module in exchange for removing a dependency between
peer Inspect pipeline adapters. Request formatting and token qualification remain
in their already qualified owners; duplicating or generalizing those policies here
would obscure the behavior-preserving boundary.

## Implemented checkpoint

The extraction follows the plan with the `run_stage` body unchanged except for
its name. Five golden scenarios passed against the original implementation before
extraction and after extraction. The focused suite passed **254 tests** covering
stage/abstention/single-call adapters, CLI routing, request preflight, native
transport and exact Ollama counting. Static checks pass for the changed Python
files. Independent review is complete; Phase 1+ may proceed under its reviewed
comparison contract.

The golden inventory is `tests/fixtures/task09e_phase0/`; its companion test
checks completion hashes before removing elapsed-time fields from comparisons.
Only invented fixture content was read. No model executed and no dataset or
historical artifact changed.

## Independent review

Reviewed the extraction and both caller diffs against `f0c57a0`, including test
patch targets and repository callers. A separate AST comparison confirmed the
entire extracted function is identical after normalizing only its renamed
function identifier. No prompt, schema, condition, attempt bound, error policy,
preflight check or persistence field changed. All affected callers import the
new owner; no old private-function caller remains. The new module removes the
peer-adapter import without introducing a dependency cycle or provider framework.

The reviewer independently ran the five golden scenarios plus staged and
abstention adapter regressions: **35 passed**. `git diff --check` passed.
Completion seals are checked before elapsed-time normalization. No blocking
behavioral-parity or maintainability finding remains for this bounded extraction.
This review does not extend to subsequent Task 09E.1 semantic/provider changes.
