# Task 03B: Define the Canonical Extraction Contract

Status: **complete 2026-07-29; MVP and human-maintainability pass implemented**.
The user explicitly requested an MVP implementation followed by a separate
code-cleanup pass. Both passes are complete. Do not activate Task 03C until the
user reviews this contract.

## Abstract

Translate the accepted Task 03A parser and table-pipeline evidence into a
versioned, project-owned canonical extraction contract before canonicalization
or full-document production conversion begins. Define producer ownership,
artifact boundaries, executable schemas, coordinate and text conventions,
deterministic extraction-scoped identifiers, provenance links, machine status,
and the precise handoff to later usability, retrieval, and evaluation stages.
Do not convert or canonicalize real documents.

## Goal

Create a canonical interface that insulates the benchmark from both Docling
and Camelot schema changes while preserving enough raw structure to verify
every later evidence anchor against the frozen PDFs and page renders.

## Inputs

- the completed Task 03A outcome, parser decision, configuration, and pilot
  artifacts
- `tasks/sprint2/03a15_rewrite_document_parser_pipeline.md`
- the accepted `document_extraction` and `table_extraction` package boundaries
  and their final Task 03A.15 external artifacts
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/sprints/sprint2_brisbane_draft_eir_defense.md`
- `tasks/sprint2/02_freeze_sources_and_provenance.md`
- the sealed source-manifest schema and model-corpus source records
- Docling's current
  [document model](https://docling-project.github.io/docling/concepts/docling_document/)
  and [lossless JSON output](https://docling-project.github.io/docling/usage/supported_formats/)
- Camelot's current Lattice, Stream, table, cell, and parsing-report
  documentation

## Outputs

- a tracked canonical-extraction specification
- versioned executable schemas for document, section, page, block, table,
  table-family, figure, image, asset, cross-reference, routing-observation,
  table-stage-observation, conversion-observation, raw-to-canonical mapping,
  and manifest records
- an external derived-artifact layout owned by the extraction version
- a producer-ownership and mapping matrix covering raw Docling output, routing
  observations, clean table-pipeline output, canonical records, and QA/debug
  assets
- a deterministic ID grammar and canonical ordering policy
- explicit coordinate, text, hierarchy, nullability, and provenance conventions
- an extraction-version identity and compatibility policy
- tiny valid and invalid fixtures covering key relationships and invariants
- offline contract tests that validate the schemas, fixtures, IDs, ordering,
  coordinates, and referential integrity without running a parser
- a precise split between Task 03 machine observations and Task 04 human
  usability decisions

## Research / learning checkpoint

Study Docling's parent-child references, body versus furniture trees,
provenance entries, coordinate origins, and page representation. Trace the
accepted routing records and clean table-pipeline records through reconstructed
tables, cleaned cells, footer ownership, and table-family assignment. Compare
those producer concepts with the benchmark's own evidence hierarchy and later
target passage contract. The goal is not to reproduce either producer's schema
under new field names; it is to own the smallest stable interface required by
this benchmark.

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
- **Producer ownership is part of meaning.** Docling with PyPdfium2 and Heron
  owns native text, layout, reading order, figures, and provenance. The reviewed
  PDFium/Heron router owns page-level routing observations. The clean Camelot
  pipeline owns reconstructed tables and cells, while project code owns cleanup
  evidence, footer ownership, and table-family assignment. TableFormer remains
  disabled and its historical cells are not canonical input.
- **Detection regions and reconstructed tables are not one-to-one.** One
  Docling table-labeled region may correspond to zero, one, or several clean
  logical tables. Preserve an explicit crosswalk rather than forcing one
  producer's region boundaries onto the other producer's table boundaries.
  Several small reconstructed tables may remain distinct canonical tables while
  belonging to one table family that signals they should be read together.
- **Table families are machine-derived canonical entities, not usability
  judgments.** Finalize their deterministic membership and IDs only with the
  complete document in scope. Scope those IDs to the extraction version; pilot
  and partial-run family numbers are evidence, not stable canonical IDs.
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
   ordered source checksums, Docling and model versions, Camelot and PDFium
   versions, backend, routing/table/cleanup/family configuration hashes,
   canonical-schema version, and relevant project code identity;
2. immutable producer-artifact roles for raw Docling output, routing
   observations, raw and cleaned table-stage output, and QA/debug assets,
   distinct from canonical records;
3. normalized record families and their serialization formats, including
   first-class table-family records;
4. ID grammar, canonical ordering, collision handling, and version scope;
   table-family IDs must be finalized over one complete document and must not
   depend on a pilot or partial-page subset;
5. page-number, printed-page-label, coordinate, rotation, and bounding-box
   conventions, including explicit transforms between bottom-left PDF points
   and top-left render pixels;
6. raw text, canonical text, and permitted normalization behavior;
7. representation of multi-page or multi-region entities;
8. tables, cells, table families, Docling table-region observations, their
   zero/one/many crosswalks, figures, captions, images, and asset relationships;
9. separate conversion, routing, table-stage, and canonicalization machine
   statuses and warnings; none may imply Task 04 human usability;
10. the inherited `source_edition_override` propagation rule;
11. schema validation and referential-integrity invariants; and
12. which fields later retrieval, curation, target generation, and evaluation
    may consume.

Prefer plain versioned JSON or JSONL records and referenced binary assets unless
the pilot demonstrates a specific need for another maintained format. Do not
introduce a database, graph service, or general schema framework.

The Task 03 page, table, and table-family records contain machine-derived
content and observations only. Reviewer, review-date, exclusion, usability,
and document-disposition fields belong in a separate Task 04 registry linked
by canonical IDs. Task 03B must define that handoff without defining or
populating Task 04 decisions.

## Review pass

Review the proposed contract through:

- **Traceability:** can any canonical text or visual entity be traced to an
  immutable source page and the responsible raw producer object?
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
- Test referential integrity across documents, pages, blocks, tables,
  table families, figures, images, assets, mappings, and cross-references.
- Test zero-, one-, and multiple-table mappings from Docling table-region
  observations without merging distinct clean tables.
- Test that table-family IDs are complete-document and extraction-version
  scoped and cannot be finalized from a partial-page subset.
- Test that conversion, routing, table-stage, and canonicalization statuses
  remain distinct and cannot imply human usability.
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
- Raw Docling output and clean table-pipeline output remain preserved and
  distinguishable from each other and from project-owned canonical records.
- All low-level anchors are deterministic within the frozen extraction version
  and are not claimed stable across materially different conversions.
- Clean table-pipeline records, not disabled TableFormer cells, supply canonical
  table content; Docling table-labeled regions remain provenance and routing
  observations linked through explicit zero/one/many mappings.
- Table families are first-class machine-derived canonical records whose IDs
  and membership are finalized only over a complete document and scoped to the
  extraction version.
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
- changing the accepted Docling, routing, table reconstruction, cleanup,
  footer-ownership, or family-assignment algorithms
- running schemas or mappings over real Task 03A artifacts
- choosing retrieval chunks, tokenization, overlap, or embeddings
- resolving every document cross-reference
- assigning page exclusions or document usability
- building Label Studio interfaces
- designing LLM prompts, citation-generation behavior, or evaluation rubrics

## Outcome

The first implementation pass added:

- [`docs/specs/canonical_extraction_v1.md`](../../docs/specs/canonical_extraction_v1.md),
  which freezes producer ownership, extraction identity, versioned artifact
  layout, record serialization, deterministic IDs and order, coordinates,
  text, hierarchy, mappings, machine status, provenance, compatibility, and
  the Task 04 boundary;
- one strict JSON Schema Draft 2020-12 bundle with executable definitions for
  extraction identity, manifest, document, section, page, block, table,
  table-family, figure, image, asset, cross-reference, routing observation,
  table-stage observation, conversion observation, and raw mapping records;
- a tiny complete valid bundle that exercises multi-region provenance,
  zero/one/many table-region mappings, complete-document families, figures,
  images, cross-references, assets, raw lineage, and the inherited
  `source_edition_override`;
- mutation-based invalid fixtures for every required record family; and
- project-owned offline invariant checks for RFC 8785 identity hashing,
  extraction-scoped typed IDs, reference scope, exact order and counts,
  geometry, hierarchy, table topology, family symmetry, mapping coverage,
  permitted text normalization, source-edition propagation, and nested
  human-review leakage.

Research confirmed that Docling content is a normalized graph whose body order
and zero/one/many provenance must not be collapsed into one nested tree.
Docling JSON is the lossless producer artifact, and its raw pointers are
locators rather than canonical IDs. Camelot cells use bottom-left PDF geometry;
its parsing metrics are diagnostics rather than correctness or usability.
The contract therefore keeps Docling table regions as observations and takes
canonical table content only from the accepted clean Camelot pipeline.

An independent review initially found acceptance-blocking false positives:
identity fields were not content-bound, references were untyped, ordering was
single-document only, geometry combinations could contradict each other,
table-family pointers could diverge, statuses could imply impossible outputs,
and raw mapping or nested review leakage was insufficiently constrained. The
MVP was hardened against those cases before handoff.

User review then made two contract changes. Local IDs now use explicit,
type-specific prefixes such as `tbl`, `fam`, and `fig`; ID policy version 2
enforces them even though the path namespace already distinguishes record
types. Full-page renders, overlays, diagnostic HTML and Markdown, ruling masks,
and table-debug images were removed from canonical asset roles and extraction
completeness. A separate strict review-cache schema makes those derivatives
disposable and reproducible on demand for selected review or labeling pages.

Initial MVP validation completed:

```text
uv run pytest tests/test_canonical_extraction_contract.py -q
32 passed

make check
77 passed

git diff --check
passed
```

No parser ran, no real Task 03A artifacts were canonicalized, and no external
derived directory was created. A later read-only smoke test verified the
mounted source release and accepted v4 artifact hashes but did not use those
bytes to replace the intentionally tiny synthetic fixture.

The requested cleanup pass preserved the schema, fixture, and public-helper
behavior while replacing the original 560-line mixed-purpose validator.
Reusable identity, ID, coordinate, bundle-index, and traversal concepts now
have small modules. Cross-record rules are grouped by human ownership:
bundle/serialization, document content, and provenance/lineage. The public
validator is an ordered 21-policy checklist, so a maintainer can see the full
contract flow without reading every implementation first. Compound tests were
split into single-policy examples with names that state the invariant.

Cleanup validation completed:

```text
uv run ruff check src/er_commons/canonical_extraction \
  tests/test_canonical_extraction_contract.py
passed

uv run mypy src/er_commons/canonical_extraction
passed

uv run pytest tests/test_canonical_extraction_contract.py -q
42 passed

make check
87 passed

git diff --check
passed
```

No canonical schema or fixture semantics changed during cleanup. Task 03B is
complete as an MVP. At Task 03B closure, Task 03C remained inactive pending
user review of that handoff.
