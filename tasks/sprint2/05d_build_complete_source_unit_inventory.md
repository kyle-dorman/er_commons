# Task 05D: Build the Complete Source-Unit Inventory

Status: **provisional; inactive until Task 05C is accepted**.

## Abstract

Run the frozen Task 05 producer over all 744 Volume 4 pages and create the
complete working source-unit candidate without mixing relationship-policy
experiments into the production run.

## Goal

Produce a complete candidate transcription and structural inventory from which
all later graphs and review views can be derived.

## Inputs

- Accepted Task 05C producer, configuration, pilot evidence, and run plan.
- Frozen `feir_volume_4` source record bound through Task 02 metadata.

## Outputs

- restartable full-source processing evidence;
- complete source span, commenter, letter/meeting, comment, response, general
  response, membership, raw reference mention, and diagnostic records;
- exact page/range accounting and terminal attempt records;
- unmatched-structure and suspected-omission report; and
- complete source-unit working candidate with a compact stage summary.

## Research / learning checkpoint

Explain the chosen full-run unit, expected critical path, disk budget, retry
policy, and why source units are completed before graph resolution.

## Plan

Revise this contract from the accepted pilot. Freeze implementation, config,
run order, restart policy, space guards, and expected outputs before reading the
full source. Process ranges restartably. Do not repair source-general behavior
inside the run; preserve a compact stop record and route a material defect to a
separate bounded task. Obtain explicit user authorization before starting the
744-page source run.

## Validation

- Account for every PDF page and processing range exactly once.
- Verify General Responses 1-9 and all detected structural regions have records
  or explicit diagnostics.
- Compare full-run structural signatures with the accepted Task 05A profile and
  Task 05C pilot. A previously unseen structural regime is a stop-and-review
  condition, not an invitation to repair the running producer.
- Review a deterministic varied sample of original comment, response, and
  general-response text and anchors across every known regime, plus every
  anomaly-triggered sample.
- Review deterministic warning samples and all terminal failures.
- Confirm stable semantic output on a repeated bounded reconstruction.
- Confirm the run does not recompute the source PDF hash, recursively hash
  upstream trees, or copy source/upstream payloads.
- Record file counts and sizes for the accepted working revision without adding
  a whole-output byte-hash pass.

## Review pass

- **Completeness:** Is every page, structural region, and General Response 1-9
  accounted for exactly once?
- **Source fidelity:** Are sampled original texts, boundaries, and anchors
  correct rather than merely schema-valid?
- **Operations:** Did restart, resource guards, and failure isolation behave as
  the accepted run plan specified?
- **Scope:** Did the run remain structural, with raw mentions preserved but no
  relationship or eligibility policy added?

## Acceptance criteria

- Full source accounting closes with no silent drops.
- The source-unit candidate is schema-valid and sufficient for graph
  construction without reopening the PDF for ordinary cases.
- Reviewed text, segmentation, and anchors are correct across every known regime,
  and no unseen regime remains undispositioned.
- Any remaining ambiguity is explicit and bounded.
- Task 05E can consume one named accepted working revision and holds it fixed
  while resolving relationships.

## Non-goals

- Immutable `inventoryv1` publication, internal relationship resolution, Draft
  EIR target resolution, derived linked views, or human eligibility review.
