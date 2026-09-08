# Task 05A: Qualify and Profile the Response Source

Status: **planned; first Task 05 subtask; not activated**.

## Abstract

Bind Task 05 to its exact upstream records and inspect a bounded, representative
set of Final EIR Volume 4 pages to learn the source grammar before designing the
inventory contract. Select the smallest maintained extraction or transcription
route that preserves exact text and anchors.

## Goal

Replace placeholder assumptions with a source-grounded structural-regime profile,
route decision, representative pilot set, and realistic workload estimate.

## Inputs

- [Task 05 umbrella](05_build_curator_only_response_inventory.md).
- Frozen Task 02 record for `feir_volume_4`.
- Task 03J extraction completion, Task 04A usability freeze, and Task 04D
  designated handoff named by the umbrella.
- Existing exploratory Volume 4 outputs as diagnostic evidence only; they are not
  production inputs or accepted counts.

## Outputs

- compact prerequisite-binding record using upstream identities and manifests;
- bounded structural-regime profile covering contents, General Responses 1-9,
  agency and organization letters, public comments, Planning Commission
  material, continuation pages, multi-part units, and apparent exceptions;
- bounded representative page/range selection with an explicit selection reason;
- examples of comment, response, membership, and reference markers;
- extraction-versus-transcription route decision and reusable-component audit;
- estimated page, unit, review, runtime, and temporary-storage workload; and
- proposed 05B amendments based on observed source structure.

## Research / learning checkpoint

Compare maintained native-PDF extraction options already available in the
project. Explain why the selected route is sufficient for this structured
source and which information still requires human review. Record why reusing a
component does not make Volume 4 part of the Task 03 corpus.

## Plan

1. Validate compact upstream completion and identity metadata without recursively
   hashing large payloads.
2. Present the exact page/range read plan before opening the source PDF.
3. After explicit source-read authorization, inspect only the bounded selection.
4. Record structural regimes, ambiguities, extraction risks, and storage/runtime
   estimates.
5. Select the route and revise provisional Task 05B; do not implement it.

## Validation

- Confirm path, recorded byte size, source ID, source-release membership, and
  terminal upstream states without recomputing the source PDF checksum.
- Ensure the representative selection covers every known structural regime and
  records what remains unobserved.
- Compare extracted text and anchors visually on the selected pages.
- Confirm the route decision has explicit rejection reasons for alternatives.
- Run `git diff --check` for documentation-only changes.

## Acceptance criteria

- Upstream identities are exact and no superseded linking view is selected.
- The source grammar is understood well enough to define stable source-unit and
  anchor contracts.
- The proposed pilot is bounded but structurally varied.
- Runtime and storage estimates distinguish working, pilot, and final output.
- Task 05B can proceed without reopening basic source-boundary questions.

## Non-goals

- Production code, schemas, a full-page scan, or a complete inventory.
- Rehashing the source PDF or upstream Task 03/04 payload trees.
- Appendix Q extraction, response classification, or eligibility review.
