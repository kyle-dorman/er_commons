# Task 05F: Resolve Official Draft EIR References

Status: **provisional; inactive until Task 05E is accepted**.

## Abstract

Resolve official-response references to Draft EIR targets through Task 04D's
designated linking-dependent handoff and annotate Task 04A usability, keeping
this cross-system graph separate from intra-Volume response relationships.

## Goal

Produce precise, auditable response-to-Draft-EIR links and explicit terminal
outcomes for references that cannot or should not resolve.

## Inputs

- Accepted Task 05D raw reference mentions and Task 05E graph/views.
- Task 03J immutable extraction identity.
- Task 04A accepted usability registry.
- Task 04D designated handoff and target-resolution view.

## Outputs

- census of Draft EIR, Final EIR, Appendix Q, external, visual, and other
  reference forms;
- reviewed source-general resolution rules and negative controls;
- exact response-to-Task-03 target links with mention provenance;
- Task 04A usability annotations;
- unresolved, ambiguous, unusable, visual-only, Final-EIR-only, external, and
  Appendix-Q-needed terminal records; and
- complete rule-level and reference-level accounting.

## Research / learning checkpoint

Review the Task 04D precision-first resolver boundary and explain why official
response references are curator-only discovery seeds, not proof that the cited
target answers the comment and not Task 07 cluster edges.

## Plan

Revise this contract from the observed Task 05 reference population. Inspect
each candidate rule separately, including collisions and negative controls,
before promotion. Resolve only through the designated Task 04D view. Reference
sealed upstream metadata; do not copy or recursively rehash its payloads. Group
observed forms into a small enumerated rule set. Rare or unknown forms may close
as `unsupported_reference_form`; the task is not obligated to invent a parser
for every wording. If a form requires new Task 03/04 target or alias policy, or
if materially different parser regimes make the work no longer bounded, stop
and split qualification from application before continuing.

## Validation

- Every raw reference mention has one classified outcome.
- Every resolved link names one uniquely resolved compatible target with exact
  source and target evidence.
- Report collisions, target-type conflicts, unusable targets, and unsupported
  reference forms without guessing.
- Prove determinism under input reordering and validate the complete promoted
  rule population.
- Confirm no mutation of Task 03J, Task 04A, Task 04D, Task 05D, or Task 05E.

## Review pass

- **Precision:** Could any rule select a plausible but wrong target or cross a
  Draft/Final EIR boundary?
- **Coverage:** Is every observed form classified even when unsupported?
- **Provenance:** Can each link be reconstructed from exact response mention,
  Task 04D target evidence, and Task 04A usability metadata?
- **Scope:** Does any candidate require upstream alias policy or a distinct
  parser regime that belongs in a separate task?

## Acceptance criteria

- Resolution is exact, deterministic, source-general, and precision-first.
- Final-EIR and Appendix-Q references cannot masquerade as Draft EIR evidence.
- Task 04A usability is visible to downstream curation without entering source
  transcription.
- All unpromoted cases remain discoverable with explicit reasons.

## Non-goals

- Fuzzy or embedding-based resolution, evidence sufficiency judgment, search
  expansion, case eligibility, clustering, or reference-defense authoring.
