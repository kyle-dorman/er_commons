# Task 05B: Define the Response Inventory Contract

Status: **active; source-free contract definition authorized**.

Activated 2026-09-08 after explicit acceptance of Task 05A. This activation
authorizes contract research, specification, schemas, fixtures, validators, and
source-free review against already retained Task 05A evidence. It does not
authorize reopening the source PDF, adding pages, accessing Volume 5, or running
the Task 05C pilot.

## Abstract

Turn Task 05A's observed source grammar into a small, explicit record,
provenance, identity, correction, and publication contract before production
implementation begins.

## Goal

Freeze the semantic and artifact boundaries needed for a maintainable producer
and independently validatable inventory.

## Inputs

- Completed and accepted Task 05A outcome, including its cross-volume General
  Response 9 exception and representative evidence.
- [Task 05 umbrella](05_build_curator_only_response_inventory.md).
- Current architecture and data/artifact contracts.

## Outputs

- versioned specification and compact JSON Schemas for source spans, commenters,
  letters or meetings, comments, responses, general responses, raw reference
  mentions, resolved edges, diagnostics, review views, corrections, inventories,
  and completion records;
- explicit page-state, cross-page continuation, marker-candidate, and
  source-placement-exception records;
- deterministic stable-ID preimages and text/page anchor rules;
- explicit boundaries among raw Unicode source text, normalized display text,
  PDFium character-slot geometry, visual style/revision evidence, and manual
  transcription;
- correction/versioning semantics that never overwrite sealed source evidence;
- artifact and identity dependency graph;
- terminal unresolved-reason vocabulary;
- synthetic and bounded source-derived fixtures; and
- validators plus a proposed 05C pilot gate.

## Research / learning checkpoint

Review normalized relationship modeling, provenance, and manifest practices.
Explain why source units, processing activities, human corrections, resolved
edges, and materialized review views remain separate instead of becoming one
wide mutable table.

## Plan

Define and review the data contract source-free, then validate it against only
the already authorized bounded Task 05A evidence. Do not reopen the PDF or add
source pages during 05B. Keep publication identity independent from working
paths and runtime timestamps.

The contract must encode the Task 05A findings rather than rediscover them:

- Volume 4 contains eight General Responses; the advertised ninth is an explicit
  cross-volume placement exception, not a missing Volume 4 extraction.
- Page state precedes unit construction and distinguishes blanks, labeled
  blanks, section openers, zero-comment sections, continuations, unit starts,
  mixed-marker pages, figures/tables, revision markup, and layout exceptions.
- Marker candidates carry line position, PDF coordinates, style/rule evidence,
  and their disposition. Inline references and nested source headings cannot
  become boundaries merely because they contain `Comment` or `Response`.
- Membership is separate from unit text and supports many-to-many and forward
  references.
- Poppler and renders qualify source fidelity but are not production semantic
  dependencies.

## Validation

- Validate positive, negative, one-to-many, many-to-one, dangling-reference,
  continuation-page, cross-volume-placement, inline-marker, nested-heading,
  blank-page, visual-revision, and correction fixtures.
- Prove stable IDs and semantic records are deterministic under input discovery
  reordering.
- Verify schemas distinguish raw mentions from resolved relations and Draft EIR
  target links.
- Verify all eight Volume 4 General Responses are representable and General
  Response 9 cannot be synthesized as a Volume 4 source unit.
- Verify final identity binds source and upstream identities by compact records,
  not repeated payload hashes.
- Complete a data-contract, provenance, maintainability, and downstream-consumer
  review; run the source-free repository gate.

## Review pass

- **Data contract:** Can every observed source unit, relation, ambiguity, and
  correction be represented without a catch-all mutable row?
- **Provenance and identity:** Does each derived record point to exact source and
  activity evidence without hashing whole upstream payloads into new IDs?
- **Downstream use:** Can Tasks 05C-05G, Task 06, and Task 07 consume only the
  fields they own without copying text or inventing policy?
- **Maintainability:** Are schemas, validators, identity preimages, and recovery
  behavior understandable without reconstructing the planning conversation?

## Acceptance criteria

- Every future artifact has one owner and an explicit dependency.
- Ambiguity and corrections are representable without mutating raw transcription.
- Text offsets, PDFium character slots, geometry, and visual revision evidence
  cannot silently substitute for one another.
- The contract supports bounded working and pilot iteration plus one immutable
  final publication.
- Task 05C can implement one short public workflow without inventing schema or
  identity policy.

## Non-goals

- Reading new source pages, production parsing, full-source execution, graph
  resolution, or curator eligibility decisions.
- A generic workflow engine, graph database, or content-addressed storage system.
