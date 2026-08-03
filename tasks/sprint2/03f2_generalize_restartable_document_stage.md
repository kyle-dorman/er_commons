# Task 03F.2: Generalize the Restartable Document Stage

Status: **complete as of 2026-08-03**. The behavioral MVP remains immutable
reference evidence. Its replacement passed the separate behavioral-
equivalence and human-maintainability gates. Task 03F.3, real-source smoke
execution, Task 03G, and Task 03H remain inactive pending explicit review and
approval.

## Abstract

Replace Appendix-P-only production constraints with one manifest-selected,
contract-bound, complete-document transaction. Add the stage-one state,
identity, publication, reuse, failure, resource, and observability behavior from
the v1 restartable corpus contract while preserving the accepted Appendix P
candidate offline. Remove only code whose deletion proof passes.

## Goal

Provide Task 03F.3 with immutable, independently restartable document candidates
and terminal records without implementing corpus accounting, indexing, or
second-pass resolution.

## Inputs

- `docs/specs/restartable_corpus_extraction_v1.md`;
- the v1 corpus-extraction schema, fixtures, and offline validator;
- the sealed Task 02 manifest and source resolver;
- accepted producer, canonical, hierarchy, semantic, and Task 03E.5 owners;
- immutable Appendix P candidate
  `exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`;
- the approved Task 03F.1 keep/generalize/delete inventory.

## Outputs

- manifest-driven stage-one configuration with required source ID;
- `scopev1-`, `txv1-`, and `docv1-` identity builders;
- project-owned state events, document completion, attempt, resource, and
  observability records matching the v1 schema;
- one application shell composing existing content-policy owners;
- checksum-closed reuse and retained-failure behavior;
- required-argument `extraction run-document --run-spec PATH --source-id ID`;
- exact offline Appendix P comparison evidence;
- caller/identity/artifact proof for each deletion actually made.

## Implementation plan

1. Separate reusable source, stage, and publication inputs from historical
   Appendix P configuration literals.
2. Implement one-document process isolation and the declared state machine.
   Page batches remain internal execution units; retry restarts the transaction.
3. Require Docling `SUCCESS` plus project validation. Preserve raw statuses and
   structured errors; never publish `PARTIAL_SUCCESS`.
4. Compose baseline producer, hierarchy disposition, canonical, semantic, and
   document-local reference owners behind narrow typed interfaces.
5. Publish completion last by atomic rename and verify exact managed-file
   closure before reuse.
6. Compare generalized Appendix P output to frozen artifacts after only the
   approved identity/namespace normalization. Do not rerun its PDF.
7. Delete `cross_reference_materialization` and any superseded entrypoint only
   if no caller, identity, artifact-verification, or coverage responsibility
   remains.

## Research / learning checkpoint

Confirm the installed Docling version's status, timeout, batch, accelerator,
and structured-error behavior against maintained documentation and source.
Explain why outer process isolation supplies the hard cancellation boundary
that cooperative `document_timeout` does not.

## Validation

- multi-document synthetic source selection;
- every legal transition and rejection of illegal/premature completion;
- full-page accounting and first-N rejection;
- `SUCCESS` publication plus partial/failure retention;
- interruption before and after completion-last atomic publication;
- checksum-valid reuse and stale/partial/conflicting output rejection;
- deterministic retry classification and resource-bound validation;
- exact offline Appendix P record, asset, support, warning, and policy
  preservation after declared normalization;
- import/caller, owned-code-inventory, and immutable-artifact checks for every
  deletion;
- `make validate-extraction-contract`, `make fix`, `make check`, and
  `git diff --check`.

## Acceptance criteria

- Any manifest-selected `model_corpus` source can be configured without a
  source-specific runtime literal or CLI default.
- Only a complete PDF with Docling `SUCCESS` and all project gates can publish.
- Reuse, failures, cancellation, and attempts are explicit and verifiable.
- Accepted Appendix P semantic and cross-reference behavior is exact offline.
- No corpus index, second pass, real-source execution, or corpus-wide hierarchy
  acceptance occurs.
- The outcome requests explicit approval before Task 03F.3 activation.

## Non-goals

- real-source smoke or PDF execution
- scope accounting, corpus target-index, resolution, or handoff implementation
- Task 03G/03H execution
- hierarchy-policy changes or corpus-wide quality acceptance
- OCR, figure linking, workflow engine, database queue, or compatibility facade

## Behavioral MVP outcome — reference only

The Task 03F.2 behavioral MVP is accepted as reference evidence under production
identity
`exv1-eac11135056bbbc278b61875591e3876e69dbb08192ac96ec0e5ac4b2b32765e`.
The MVP `corpus_extraction` application shell selects
one complete `model_corpus` source from the sealed Task 02 manifest, binds it to
that identity, and composes the existing producer, hierarchy, canonical,
semantic, and cross-reference owners behind typed handoffs. The required CLI is
`extraction run-document --run-spec PATH --source-id ID`; neither argument has
a source-specific default.

Stage one now records immutable state transitions, attempts, resource policy,
and observability; persists retry numbering across invocations; reconciles the
publication-before-event interruption window; terminates the complete child
process group at the outer deadline; and publishes completion last by atomic
rename. Reuse recomputes the document identity and control digest, verifies
the source identity, upstream completion seals, inventory, checksums, and exact
managed-file closure, and rejects stale, partial, or conflicting candidates.
Docling `SUCCESS` remains distinct from project publication success, while raw
statuses and structured errors remain retained. A production-identity recipe
now binds the complete owner configuration/schema/code set used by this stage.

The installed Docling behavior was checked against maintained documentation
and source: conversion status and structured errors are result data;
`document_timeout` is cooperative per-document processing control; batch sizes,
queue capacity, accelerator device, and CPU threads are explicit inputs. The
outer child-process group is therefore the hard cancellation boundary. The
checked-in resource policy runs one document at a time with four-page and
four-stage batches, queue capacity 100, four CPU threads, CPU execution,
declared memory/storage estimates, an 86,400-second outer deadline, a
15-second cancellation grace period, and one retry.

The accepted Appendix P candidate was compared offline without rerunning its
PDF. The comparison was exact across 28 files, 16 record streams, 3 assets, 7
support files, and 5 warning/policy checks, with manifest digest
`3671e6ce1069855fa8428659e146ffd41d6d964a1ef289fd7c5f4eaec9c6cb0e` and
zero mismatches. The comparison record was persisted under the Task 03F
artifact root at
`offline_preservation/exv1-eac11135056bbbc278b61875591e3876e69dbb08192ac96ec0e5ac4b2b32765e/preservation_report.json`.
The historical `cross_reference_materialization` package was
not deleted because tests and immutable-artifact verification remain proven
callers; no deletion satisfied the full caller/identity/artifact/coverage
proof.

Validation passed `make validate-extraction-contract`, `make fix`, all 508
tests plus Ruff and mypy through `make check`, and `git diff --check`.
Independent review found no remaining blocking defect after retry, resource,
cancellation, retained-failure, join, identity, preservation, and crash-window
fixes. No PDF, real-source smoke, corpus accounting, index, resolution, or
handoff execution occurred.

## Human-owned outcome

The replacement is bound to production identity
`exv1-bedd4c50a9614a74a6406d60148a08c44579f0b504bc3568042499f578c0cf7f`.
It preserves the validated MVP behavior while replacing the two control-heavy
modules with short application shells and named owners for preflight, attempts,
candidate identity/reuse, publication, observability, owner inputs, owner
validation, and owner observations. The runtime and content-owner shells are
104 and 131 lines; no production function exceeds 77 lines. Typed records own
persisted identity and recovery events, structured logging covers execution,
reuse, recovery, publication, and failure, and public fault-injection hooks
replace tests coupled to private orchestration details.

Tests now mirror those ownership boundaries: identity/lifecycle,
workflow/publication/recovery, storage/process/preservation, and owner policy
live in focused modules. Objective maintainability tests bound shell, module,
and function size and prohibit private workflow test seams. The replacement
passed exact offline Appendix P preservation under its own identity, all 511
repository tests, Ruff, mypy, contract validation, and `git diff --check`.
Independent review found no production-code blocker; its two documentation and
test-organization blockers were corrected before closure. No PDF or real-source
execution occurred.

Task 03F.3 remains provisional. Revise its contract only after the human-owned
Task 03F.2 implementation is accepted, and obtain explicit user approval before
activation or any real-source smoke.
