# Task 03B: Define the Canonical Extraction Contract

Status: **provisional**. Revise this contract from the accepted Task 03A outcome
before activating it.

## Abstract

Translate the accepted Task 03A parser evidence into a versioned,
project-owned canonical extraction contract before production code is written.
Define artifact boundaries, schemas, coordinate and text conventions,
deterministic extraction-scoped identifiers, provenance links, machine status,
and the precise handoff to later usability, retrieval, and evaluation stages.
Do not convert full documents.

## Goal

Create a canonical interface that insulates the benchmark from Docling schema
changes while preserving enough raw structure to verify every later evidence
anchor against the frozen PDFs and page renders.

## Inputs

- the completed Task 03A outcome, parser decision, configuration, and pilot
  artifacts
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/sprints/sprint2_brisbane_draft_eir_defense.md`
- `tasks/sprint2/02_freeze_sources_and_provenance.md`
- the sealed source-manifest schema and model-corpus source records
- Docling's current
  [document model](https://docling-project.github.io/docling/concepts/docling_document/)
  and [lossless JSON output](https://docling-project.github.io/docling/usage/supported_formats/)

## Outputs

- a tracked canonical-extraction specification
- versioned schemas for document, section, page, block, table, figure, image,
  asset, cross-reference, conversion-observation, and manifest records
- an external derived-artifact layout owned by the extraction version
- a deterministic ID grammar and canonical ordering policy
- explicit coordinate, text, hierarchy, nullability, and provenance conventions
- an extraction-version identity and compatibility policy
- tiny valid and invalid fixtures covering key relationships and invariants
- a precise split between Task 03 machine observations and Task 04 human
  usability decisions

## Research / learning checkpoint

Study Docling's parent-child references, body versus furniture trees,
provenance entries, coordinate origins, and page representation. Compare those
vendor concepts with the benchmark's own evidence hierarchy and later target
passage contract. The goal is not to reproduce Docling's schema under new field
names; it is to own the smallest stable interface required by this benchmark.

The outcome must teach these document-extraction design issues:

- **Source identity and representation identity are different.** The PDF
  checksum identifies immutable source bytes. The extraction version identifies
  a derived interpretation of those bytes under one parser, model set,
  configuration, and canonical schema.
- **Stable IDs require a declared stability domain.** Low-level block IDs need
  only reproduce within one frozen extraction version. Pretending they survive
  parser or configuration changes would hide anchor drift.
- **A document is both a tree and a spatial graph.** Reading order and section
  containment are hierarchical, while page provenance, multi-region items,
  captions, tables, and cross-references introduce many-to-many edges. A single
  nested JSON tree is not sufficient as the only canonical interface.
- **Geometry is data, not decoration.** Coordinate origin, units, page
  dimensions, rotation, clipping, and bounding-box multiplicity must be explicit
  or visual verification will be unreliable.
- **Text normalization can destroy evidence.** Dehyphenation, whitespace repair,
  ligature handling, repeated furniture removal, and Unicode normalization may
  help retrieval but must not erase the raw text or make quoted spans
  untraceable. Retrieval normalization belongs later unless the transformation
  is lossless and represented explicitly.
- **Provenance is transitive lineage.** A later statement cites an evidence
  record, which points to canonical anchors, which point to raw parser objects,
  page regions, and the checksum-pinned source. The schema must make that chain
  mechanically traversable.
- **Gold leakage can begin in preprocessing.** Curator-only response data,
  usability decisions, and later reference-evidence labels must not enter the
  model-corpus extraction namespace or target-facing records.

## Plan / spec requirement

Freeze a written data contract before implementation. It must decide:

1. extraction-version inputs: source-release identity and manifest checksum,
   ordered source checksums, Docling and model versions, backend, complete
   configuration hash, canonical-schema version, and relevant project code
   identity;
2. raw-versus-canonical artifact roles and immutability;
3. normalized record families and their serialization formats;
4. ID grammar, canonical ordering, collision handling, and version scope;
5. page-number, printed-page-label, coordinate, rotation, and bounding-box
   conventions;
6. raw text, canonical text, and permitted normalization behavior;
7. representation of multi-page or multi-region entities;
8. tables, cells, figures, captions, images, and asset relationships;
9. conversion status and warnings versus human review status;
10. the inherited `source_edition_override` propagation rule;
11. schema validation and referential-integrity invariants; and
12. which fields later retrieval, curation, target generation, and evaluation
    may consume.

Prefer plain versioned JSON or JSONL records and referenced binary assets unless
the pilot demonstrates a specific need for another maintained format. Do not
introduce a database, graph service, or general schema framework.

## Review pass

Review the proposed contract through:

- **Traceability:** can any canonical text or visual entity be traced to an
  immutable source page and raw parser object?
- **Evolution:** can a changed parser/configuration coexist as a new extraction
  without overwriting v1 or pretending IDs are compatible?
- **Downstream isolation:** can later code consume stable records without
  importing Docling, and can target-facing records exclude curator-only fields?
- **Information preservation:** does normalization keep raw values and avoid
  collapsing ambiguity?
- **Scale:** can 48,341 pages be streamed and validated without loading a
  corpus-sized JSON tree?

## Validation

- Validate positive and negative fixtures against every schema.
- Test ID reproducibility, collision rejection, and ordering invariants.
- Test coordinate bounds, page references, and multi-region provenance.
- Test referential integrity across documents, pages, blocks, tables, figures,
  images, assets, and cross-references.
- Test that curator-only roles and human-review fields are rejected from the
  model-corpus canonical contract.
- Test propagation of `source_edition_override` into document/page machine
  metadata without turning it into a usability decision.
- Inspect the specification and run:

```bash
make check
git diff --check
```

## Acceptance criteria

- A future task can implement the contract without inventing schemas, paths,
  ID rules, or provenance semantics.
- The extraction identity completely names the source, parser/model,
  configuration, and canonical-schema interpretation.
- Raw Docling output remains preserved and distinguishable from project-owned
  canonical records.
- All low-level anchors are deterministic within the frozen extraction version
  and are not claimed stable across materially different conversions.
- The schemas preserve geometry, raw text, canonical text, hierarchy, and
  transitive source provenance.
- Task 03 machine observations and Task 04 human usability decisions have a
  clear, non-overlapping ownership boundary.
- The contract can support later hierarchical retrieval and constrained
  citation without prematurely defining retrieval passages.
- The outcome requests user review before Task 03C.

## Non-goals

- installing or running the production parser
- implementing conversion or canonicalization code
- choosing retrieval chunks, tokenization, overlap, or embeddings
- resolving every document cross-reference
- assigning page exclusions or document usability
- building Label Studio interfaces
- designing LLM prompts, citation-generation behavior, or evaluation rubrics
