# Task 15G — Implement structured conclusion judging

Status: complete (2026-10-22); semantic qualification awaits the C001 pilot.

## Abstract and goal

Implement the user-accepted required/optional C rules and point-level output.
Use the same frozen Baylands overview and prompt composition in synthetic and
real judgment paths. Preserve all historical prompt/schema identities and results.

## Inputs and outputs

Inputs: section 3 of adequacy_labeling_rules.md, 15F C001 discussion, existing
adequacy contracts/Inspect adapter, Task11E overview binding and context envelope.
Outputs: explicitly versioned structured C prompt, strict input/output models,
input-aware point coverage/aggregate validation, native adapter integration,
shared context composition and regression tests. Reference support remains separate.

## Plan and learning checkpoint

Inspect existing Pydantic strict schemas, native Inspect schema handling, and
frozen context composition before implementation. Reuse these package boundaries.
Separate shape validation from semantic judging: mechanical validation enforces
point IDs, legal statuses and aggregate consistency, not whether meaning matches.
Quote fidelity remains a separate diagnostic. Make the real overview a shared,
verified input rather than copying it into a synthetic-only prompt.

1. Add a new explicit version; preserve old versions and default frozen selection.
2. Implement structured inputs, point judgments, parser and diagnostics.
3. Share exact context composition with native testing and real context envelopes.
4. Run focused contract/context tests and make fix/check; independently review.
5. Update maintained documentation and next-step routing.

## Acceptance and review

Reject duplicate/missing/unknown point IDs, wrong status families and inconsistent
overall decisions. Require input context for structured output validation. Verify
native provider configs/messages share exact prompt and schema identities. Existing
frozen-version tests must remain valid. Review for context drift, historical data
mutation and accidental fallback to old schemas.

## Non-goals

No provider calls, synthetic data generation, label publication, old result edits,
reserved-challenge access, MiniMax use, commits or pushes. C001 synthetic pilot is
next; this task does not claim judge quality or stability from unit tests.

## Outcome

Implemented `task15.binary_adequacy.conclusion_structured.v1` with four-field
input, numbered R/O reference lists and point judgments plus overall Boolean/reason.
The [contract identity](../../docs/specs/task15g_structured_conclusion_judge_v1.json)
pins complete prompt, input/output schema and overview identities. The
[maintainer guide](../../docs/judge_maintainer_guide.md) documents exact APIs.

The strict parser requires the actual input packet, rejects wrong/duplicate/missing
IDs and role statuses, and verifies overall aggregation. Quote membership remains
a separate diagnostic. Judgment ordering is requested for readability but exact ID
coverage, not ordering, controls structural validity. Independent review found no
material contract issues; all30 focused structured-contract tests pass.

The prior synthetic path used a bare C prompt while actual evaluation prefixed the
Task11D14 document overview. The new version shares checksum-verified composition
between native Inspect and real context projections; mismatched overview/prompt
inputs fail closed. Offline tests verify message equality and both Luna/Haiku
provider transports. The old prose synthetic loader and frozen production defaults
remain unchanged; the whole-answer publication/reporting pipeline awaits a new
approved reference release and separate downstream migration.

No provider calls, label/dataset mutations, synthetic generation, commits or pushes.
Next: C001-only synthetic authoring/review and judge stability testing; unit tests
establish implementation integrity, not semantic judge quality.

Validation: `make fix` and `make check` passed (Ruff, mypy, 4,472 tests passed;
1 skipped). The 105 warnings are Inspect dependency deprecations.
`git diff --check` passed. Offline native provider mocks made no live calls.
