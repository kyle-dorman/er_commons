# Task 05H: Review and Freeze the Response Inventory

Status: **provisional; inactive until Task 05G is accepted**.

## Abstract

Review the complete Task 05 source units, graphs, diagnostics, anchors, and
derived views; apply corrections through versioned decisions; and publish the
single inventory identity designated for Task 07 and Task 08.

## Goal

Close Task 05 with a compact, auditable, maintainable publication while keeping
source evidence, machine derivation, human correction, and downstream semantic
screening distinct.

## Inputs

- Accepted Task 05D source-unit candidate.
- Accepted Task 05E intra-Volume graph and review views.
- Accepted Task 05G replayed official Draft EIR link layer and usability
  annotations.
- Accepted Task 05B completion and correction contracts.

## Outputs

- curator review register for structural anomalies, ambiguous links, apparent
  orphans, anchors, and representative linked views;
- versioned correction and disposition records;
- sparse non-source-changing correction/disposition overlay;
- final `inventory/`, `diagnostics/`, and `records/` package plus compact
  `review_views/` indexes and rendering recipes; materialized joined views remain
  regenerable working cache;
- Task 07/08 handoff naming exact upstream identities and known limitations;
- final managed-file inventory, publication-time output digests, and compact
  completion record; and
- working/pilot retention recommendation for separate user approval.

## Research / learning checkpoint

Explain the distinction between source fidelity review and later benchmark
eligibility review. Document why only accepted production artifacts are sealed
while working space remains available for iteration.

## Plan

Revise this contract from Task 05G, then use four explicit gates:

1. Freeze the review population and correction semantics.
2. Record findings and sparse non-source-changing dispositions.
3. If a finding changes transcription, segmentation, stable IDs, or resolution
   behavior, stop and route it to the owning stage or a narrow remediation task;
   create new working revisions and return to Task 05G as required.
4. Publish only after the exact corrected inputs pass re-review and the operator
   workflow passes an independent maintainability review.

Do not expose response-outcome labels in the core inventory UI or materialize a
second full corrected candidate when a sparse overlay is sufficient.

## Validation

- Review all terminal processing failures and identity-affecting ambiguities,
  every apparent orphan and unlinked general response, every rule-level
  unresolved category, and a deterministic sample of repetitive nonmatches and
  anchors. A reviewed rule-level disposition may cover a demonstrably homogeneous
  class; repetitive rows do not require individual review.
- Verify correction provenance and prove the source transcription remains
  recoverable and unchanged.
- Validate graph closure, reference accounting, source anchors, managed-file
  closure, stable IDs, and repeatable semantic output.
- Hash accepted Task-05-owned authoritative outputs once, preferably during
  their final write; do not rehash the source PDF or upstream Task 03/04 payload
  trees. Keep regenerable views and caches outside authoritative checksum closure.
- Run focused tests, `make check`, final maintainability review, and
  `git diff --check` before designation.

## Review pass

- **Source fidelity:** Did any accepted correction alter transcription,
  segmentation, or anchors and therefore require upstream replay?
- **Publication:** Does the final release name one exact accepted working revision
  from every owning stage and exclude regenerable payloads from authority?
- **Completeness:** Does every mandatory review class have a human or reviewed
  rule-level disposition?
- **Maintainability:** Can a future curator validate, regenerate, and diagnose
  the release using the documented interface and compact records?

## Acceptance criteria

- Every identifiable unit, relationship mention, and official reference has a
  record or reviewed diagnostic.
- The final inventory is immutable, compactly sealed, independently validatable,
  and designated for Task 07/08.
- Working data, pilots, and superseded candidates are not represented as accepted
  inventory; any material cleanup remains separately authorized.
- No response outcome, eligibility, or cluster decision is smuggled into Task 05.

## Non-goals

- Appendix Q extraction, response classification, eligibility screening,
  clustering, split selection, evidence authoring, retrieval, generation, or
  evaluation.
