# Task 11F — Review and clean up target-generation code

Status: Complete; user-requested maintenance after Task 11 closeout.

## Abstract and goal

Make the maintained Task 11 generation, context projection and evaluation code
readable and easy to edit while preserving exact requests, persisted formats,
frozen configuration and historical results. Task 12 remains provisional.

## Inputs and outputs

Read the Task 11 umbrella, 11C.1 maintenance boundaries, architecture and artifact
contracts. Review Task 11 source and tests, including uncommitted experimental
adapters. Produce focused refactors, regression checks and a concise maintainer
map. Preserve preexisting working changes.

## Plan and learning checkpoint

Use bounded independent reviews for generation adapters, context projection and
evaluation orchestration. Prefer explicit named stages and shared pure helpers
where responsibilities already repeat; avoid frameworks and speculative APIs.
Use existing native Inspect interfaces and standard Python facilities, with no
new dependencies. The 11C.1 maintenance approach remains applicable: source
identity can change, but normal request bytes, policy and historical results cannot.
Explicitly documented failure-handling fixes may reject previously unchecked
invalid configuration/accounting or preserve receipts after cleanup errors.

## Validation and acceptance

Review changes for exact request/schema/configuration preservation. Run relevant
offline fixtures followed by `make fix`, `make check` and `git diff --check`.
Perform a final bounded review of the integrated diff. Record concrete fixes,
remaining limitations and where maintainers should edit each responsibility.

## Non-goals

No model or counting calls, prompt/judge revisions, benchmark policy changes,
locked-test/reserved content access, Task 12 implementation, commits or pushes.
Never modify sealed external scripts, reports, runs or result pointers. Historical
scripts remain execution snapshots; do not turn them into a new framework.

## Review findings and changes

- Alternative-model adapters repeated the same execution, usage validation,
  failure capture and candidate sealing. They now share `execute_generation`;
  each version still owns its native request gates and authorized settings.
- Context execution mixed configuration/schema preparation with transport.
  Named helpers now separate those stages, with fixed limits named explicitly.
- Judge-context assembly mixed grounding locator checks and reference projection
  into one branch-heavy function. Separate helpers make the evidence and
  reference boundaries visible; edition projection already had suitable boundaries.
- The legacy Luna runner accepted malformed numeric limits and metadata inconsistent
  with its native transport. Configuration is validated before creating a run;
  returned model/usage is checked before publishing a valid candidate. Skipped
  receipts now retain attempt and repeat identity.
- Client-close exceptions could escape finalization and lose the final accounting
  receipt. All reviewed Task 11 execution paths now retain cleanup errors and
  original diagnostics, mark the attempt unsuccessful and seal the result without
  retrying. Raw output remains evidence even when cleanup fails.

These last two items intentionally strengthen future failure handling. Normal
request settings, prompt/schema bytes, identity recipes and projection semantics
remain unchanged. The original sealed runs and their source snapshots remain the
record of past execution; no result pointer was rewritten.

## Maintainer map and learning

| Responsibility | Edit here |
| --- | --- |
| Legacy Luna limits and generation | `target_generation.validate_config`, `generate_one`, `run` |
| Shared alternative-model attempt lifecycle | `alternative_target_generation.execute_generation` |
| Historical provider/cap-specific request gates | `alternative_target_generation.ReceiptHooks`, `haiku_output_generation.ReceiptHooks` |
| Accepted context execution and schema setup | `context_comparison.execute`, `_execution_config`, `_expected_schema` |
| Target/judge context and evidence/reference transformations | `context_projection.project_target`, `project_judge` and their named helpers |
| Saved-candidate evaluation | Existing four-module boundary documented in 11C.1 |

Sharing a lifecycle is useful where failure/accounting behavior must change
consistently. Keeping version-specific request gates explicit makes historical
conditions reviewable. Small pure projection helpers make isolation checks easy
to edit without touching transport. No new dependency or workflow framework was
needed. Sealed experiment/report scripts remain snapshots; Task 12 must explicitly
choose any reporting logic it promotes into maintained code.

## Outcome and validation

Completed the bounded code review and cleanup. Independent cross-review found no
blocking regressions. Before/after invented-fixture comparisons preserved target,
A/G/S/C and edition projection outputs and hashes, plus native request, candidate,
result and receipt content for alternative transports (excluding nondeterministic
Inspect IDs/timing and their derived seals). New regression fixtures exercise
invalid configuration, returned-model/usage failures, skipped repeat identity and
cleanup exceptions after successful and failed requests.

`make fix`, `make check` and `git diff --check` passed. Full verification:
4,201 tests passed, one skipped, 89 warnings; formatting, lint and type checks
passed. Initial validation caught a missing test import and a type-narrowing issue;
both were corrected before the final full check. No model/counting calls, prompt
changes, historical artifact edits, commits or pushes were made.

Task 11 remains complete with limitations. Task 12 remains provisional and is the
next reporting/readiness step. The bounded legacy CLIs still support their original
fixed panels/repeats; this cleanup does not introduce an all-19 production command.
