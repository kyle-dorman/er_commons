# Task 05B: Define the Response Inventory Contract

Status: **provisional; inactive until Task 05A is accepted**.

## Abstract

Turn Task 05A's observed source grammar into a small, explicit record,
provenance, identity, correction, and publication contract before production
implementation begins.

## Goal

Freeze the semantic and artifact boundaries needed for a maintainable producer
and independently validatable inventory.

## Inputs

- Accepted Task 05A outcome and representative evidence.
- [Task 05 umbrella](05_build_curator_only_response_inventory.md).
- Current architecture and data/artifact contracts.

## Outputs

- versioned specification and compact JSON Schemas for source spans, commenters,
  letters or meetings, comments, responses, general responses, raw reference
  mentions, resolved edges, diagnostics, review views, corrections, inventories,
  and completion records;
- deterministic stable-ID preimages and text/page anchor rules;
- explicit source transcription versus normalized display-text boundary;
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

Revise this provisional contract from Task 05A before activation. Define and
review the data contract source-free, then validate it against only the bounded
Task 05A evidence. Keep publication identity independent from working paths and
runtime timestamps.

## Validation

- Validate positive, negative, one-to-many, many-to-one, dangling-reference,
  continuation-page, and correction fixtures.
- Prove stable IDs and semantic records are deterministic under input discovery
  reordering.
- Verify schemas distinguish raw mentions from resolved relations and Draft EIR
  target links.
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
- The contract supports bounded working and pilot iteration plus one immutable
  final publication.
- Task 05C can implement one short public workflow without inventing schema or
  identity policy.

## Non-goals

- Reading new source pages, production parsing, full-source execution, graph
  resolution, or curator eligibility decisions.
- A generic workflow engine, graph database, or content-addressed storage system.
