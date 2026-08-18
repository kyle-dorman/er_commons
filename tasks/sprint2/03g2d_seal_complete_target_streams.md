# Task 03G.2d: Seal Complete Target Streams

Status: **completed on 2026-08-05**.

## Abstract

The fresh three-document pilot completed all six content owners per source and
published exact scope accounting. Target-index construction then failed before
publication because the document outcome observer exposed only
`documents.jsonl` as its sealed target-record input. Valid aliases in the same
completed candidates also target sections, pages, and tables.

This task repairs only the stage-one-to-stage-two evidence wiring. It must
reuse all checksum-valid producers and completed downstream owner stages and
must not invoke Docling, a table parser, a PDF reader, or a model.

## Goal

Expose the complete ordered set of canonical target-record streams to the
corpus index so every alias target is checked against the sealed document
candidate that owns it.

## Inputs

- the three checksum-valid Task 03G.2 document candidates;
- their canonical `documents.jsonl`, `sections.jsonl`, `tables.jsonl`,
  `figures.jsonl`, and `pages.jsonl` streams;
- the completed scope-accounting stage; and
- the retained failed target-index attempt and exception evidence.

## Outputs

- deterministic five-stream outcome evidence for each successful document;
- focused regression coverage for non-document alias targets;
- refreshed production identity and run-spec pin if the maintained identity
  inventory requires it; and
- a resumed stage-two target index, resolution, handoff, contract bundle, and
  exact checksum-reuse invocation.

## Research / learning checkpoint

Inspect the existing stage-one candidate inventory, outcome observer, index
builder, and v1.1 contract validator. Preserve the provenance rule in plain
language: an alias is usable only when its target ID occurs in one of the
explicitly sealed semantic target streams from the same completed candidate.
Merely finding an ID elsewhere in the candidate is insufficient.

## Plan

1. Name the five target streams once in deterministic semantic order and emit
   checksum references to each from successful document evidence.
2. Keep target-index validation fail closed when an alias points outside those
   streams or any referenced stream differs.
3. Add a synthetic non-document alias regression and retain the existing
   document-alias and exact-reuse behavior.
4. Refresh identity only if required by the maintained code bundle, prove all
   six producer IDs are unchanged, and reuse every checksum-valid owner stage.
5. Resume from target-index construction; do not allocate producer, PDF,
   parser, or model work.

## Validation

- focused corpus extraction and corpus resolution tests;
- `make validate-extraction-contract`;
- `make check`;
- `git diff --check`;
- exact on-disk verification of all six producers, twelve downstream owner
  candidates, three document candidates, and scope accounting before resume;
- all fresh aliases resolve to IDs present in the five sealed target streams;
  and
- a second identical scope invocation checksum-reuses the completed result.

## Acceptance criteria

- target-index construction accepts the current 4,893 alias targets without
  weakening missing-target rejection;
- no historical Appendix P lineage is read as an input;
- no producer, PDF, parser, or model work is rerun; and
- the final handoff and contract bundle validate under the v1.1 contract.

## Non-goals

- changing aliases or canonical semantic content;
- treating blocks, assets, images, or table families as target streams;
- repairing unrelated extraction warnings; or
- activating Task 03H.

## Outcome

Successful document evidence now seals the five deterministic semantic target
streams. The current 4,893 alias targets all join to those streams, while a
new negative regression preserves rejection of targets absent from all five.
The fresh scope published ready handoff
`handoffv1-56a0e83e80cf28201885692e936abc4b715d82106f11b00b9573d9d8ff1329c0`
and passed independent v1.1 validation. An identical second invocation returned
the same bundle and handoff bytes without a new document attempt. All six
producer and twelve downstream owner IDs remained unchanged and reused.

Aggregate reporting then exposed a separate review-only path mismatch for the
page-label observation stream. Task 03G.2e owns that final reporting repair;
it does not affect production identity or extraction artifacts.
