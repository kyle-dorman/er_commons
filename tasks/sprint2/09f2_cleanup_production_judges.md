# Task 09F.2 — Consolidate production judges

Status: **complete**, explicitly requested by Kyle on 2026-10-16 and required
for closing 09F and 09F.1. Their model selections and evaluation evidence stand.

## Abstract and goal

Keep one maintainable native Inspect execution path for independent A/G/S/C calls.
Remove exploratory judge runtimes, direct API executors, obsolete prompts and
experiment commands. Retain GLM/Fireworks and local Ollama capabilities alongside
selected Luna A v2 / G v3 / C v8 and Haiku S v6. Preserve exact selected semantics,
strict invalid-output handling, input isolation, and immutable evaluation evidence.

## Inputs and outputs

Inputs: selected configurations, current native Inspect adapters, development
loaders, 09F/09F.1 handoffs, and historical Ollama infrastructure. Outputs: compact
shared provider configuration, thin component adapters, focused regression tests,
a current maintainer guide and corrected task/status routing.

## Research / learning checkpoint

Inspect's [model API](https://inspect.aisi.org.uk/models.html) supplies native
providers, generation settings and model costs; its
[structured output](https://inspect.aisi.org.uk/structured.html) support carries
provider schemas. Use those boundaries directly. Shared transport configuration
must not merge component inputs, rubrics or scores. Avoid rebuilding scheduling,
retry, budget or receipt frameworks. Verify installed Inspect behavior in tests.

## Plan and review

1. Audit imports/callers and independently review provider, semantic and removal
   boundaries. Save the pre-cleanup checkout outside Git before removing untracked
   exploratory implementations.
2. Flatten selected prompts byte-for-byte; consolidate provider settings and
   selection validation; retain component-specific projection and strict parsing.
3. Remove unused experimental code/config/tests/commands after extracting live
   loader helpers. Keep source snapshots and immutable historical evidence for
   offline historical replay; no compatibility aliases without an active caller.
4. Test input isolation, selected prompt/schema identities, all retained native
   providers, strict failure handling and development loaders. Update maintained
   docs and task closeout after independent review and full checks.

## Preservation and validation

Pre-cleanup source archive and SHA inventory live under the configured artifact
root at `pipelines/brisbane_baylands/task_09/09f2_cleanup_20261016/`.
Existing run directories and result pointers remain immutable. No live inference,
label changes, held-out access, commit or push belongs to this task.
Run focused offline checks, `make fix`, `make check`, and `git diff --check`.
Review imports/CLI targets for orphaned runtime paths and document historical
replay from snapshots. Unrelated document/collection code stays unchanged.

## Acceptance criteria

All four selected judges use native Inspect with shared provider configuration;
GLM/Fireworks and Ollama remain supported. No production caller depends on an
exploratory runner or hand-written cloud transport. Selected prompt/schema bytes
and failure semantics remain fixed. Tests and the current guide describe the
retained interface, and 09F/09F.1 closeout explicitly includes this cleanup.

## Non-goals

Prompt tuning, new provider comparison, combined answer routing/reporting (Task12),
new benchmark policy or a general evaluation framework.

## Outcome

A/G/S/C now share one native Inspect provider/configuration layer, with selected
prompts as the defaults. Luna A/G/C and Haiku S remain selected; Fireworks/GLM and
both local Ollama profiles remain explicit alternatives. Retired 35 source modules,
36 obsolete test files, 12 experimental configs and two historical report scripts
from the active checkout; all are recoverable in the checksummed source archive.
The [production guide](../../docs/judge_maintainer_guide.md) owns supported interfaces.

Independent review found no blockers. Exact selected prompt/schema bytes match
all four originals; 169 parser and 118 input observations agree with the archived
cores. Eight provider-schema comparisons match. Native cloud HTTP mocks and eight
Ollama wire cases pass; the complete development loaders retain 246 C / 490 S /
310 A / 611 G examples. All 103 preexisting result pointers remain unchanged.

`make fix`, `make check` and `git diff --check` pass: **3,975 tests passed, one
skipped**, including format/lint/type checks. The initial full check caught two
stale test references to retired constants; the corrected tests and final full
check pass. Eight warnings originate in Inspect's dependency deprecation.
No live inference, label edits, held-out access, commit or push occurred.

Learning: consolidating provider mechanics prevents settings drift without merging
judgment semantics. Exact byte/schema and parser parity gives stronger protection
than rerunning live judgments during a mechanical cleanup. Native Ollama uses the
existing aliases, but their actual identity/context remains unqualified for this
new adapter; historical exact-rendering helpers are retained separately.

09F and 09F.1 are now complete including their cleanup requirement. 09G is next;
Task 12 still owns answer routing and combined reporting. The
[cleanup receipt](../../docs/specs/task09f2_cleanup_result.json) binds the archived
source, final checks and current production inventory.
