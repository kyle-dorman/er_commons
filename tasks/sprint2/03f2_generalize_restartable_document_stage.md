# Task 03F.2: Generalize the Restartable Document Stage

Status: **active as of 2026-08-03**. The user accepted Task 03F.1 Gate B and
authorized this contract as the next bounded task. Task 03F.3, real-source
smoke execution, Task 03G, and Task 03H remain inactive.

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
