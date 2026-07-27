# Task 03D: Materialize Core Canonical Records

Status: **provisional**. Revise this contract from the accepted Task 03C outcome
before activating it.

## Abstract

Implement a deterministic transformation from preserved raw Docling output into
the Task 03B canonical document, page, block, table, figure, image, and asset
records. Preserve reading order, body-versus-furniture labels, raw and canonical
text, geometry, multi-region provenance, and links to page renders and extracted
assets. Do not infer the final section hierarchy or resolve cross-references.

## Goal

Give downstream code a stable, streamable, project-owned representation of
document content without importing Docling or losing the evidence needed to
audit parser decisions.

## Inputs

- completed Task 03B schemas, ID grammar, and artifact contract
- completed Task 03C raw Docling output and conversion record
- the corresponding source-manifest record and PDF checksum
- Docling's documented body/furniture, item, provenance, table, picture, and
  JSON-pointer semantics

## Outputs

- typed canonicalization code isolated from the parser adapter
- canonical document, page, block, table, figure, image, and asset records for
  the Task 03C input
- deterministic version-scoped IDs and canonical order
- raw-to-canonical mapping records
- validation summaries for counts, referential integrity, coordinates, text,
  reading order, and assets
- tiny fixtures covering multi-page provenance, furniture, tables, captions,
  pictures, and invalid references

## Research / learning checkpoint

Inspect how Docling represents `TextItem`, `TableItem`, `PictureItem`, groups,
the body and furniture trees, and one-or-more provenance entries. Follow a
single paragraph, table, and figure from raw JSON through page coordinates and
rendered pixels into the proposed canonical records.

The outcome must explain:

- **Reading order is a model output, not a geometric sort.** Sorting by top-left
  coordinates fails on columns, sidebars, captions, and floating elements.
  Preserve the parser's declared order and the original geometry so errors are
  visible and later alternatives remain possible.
- **Block type and content type are uncertain observations.** A region labeled
  `section_header`, `caption`, or `table` reflects model inference. Canonical
  records should preserve the observed label and source provenance rather than
  promote it to unqualified truth.
- **One semantic item may have multiple spatial anchors.** Paragraphs, tables,
  and list structures can span pages or regions. Flattening to exactly one page
  and box creates false provenance.
- **Tables need dual representation.** Preserve topology and cell-level
  provenance separately from a deterministic text rendering. Markdown or plain
  text alone cannot represent merged cells, row/column headers, or extraction
  uncertainty.
- **Figures, pictures, and renders are distinct.** A detected semantic figure,
  an extracted/rasterized asset, and a full-page verification render have
  different identities and lifecycles.
- **Canonicalization should be conservative.** Preserve raw text and explicit
  transformations. Do not silently dehyphenate, remove repeated furniture,
  rewrite ligatures, or merge blocks because the result seems better for RAG.
- **Data lineage must survive normalization.** A normalized record store is
  useful only if every derived ID can be mapped back to raw vendor references
  and immutable source regions.

## Plan / spec requirement

Write a mapping specification before implementation. For each canonical record
type, name:

1. the raw Docling source types and paths;
2. required and optional fields;
3. ordering and ID inputs;
4. text and label transformations;
5. page and bounding-box provenance;
6. parent, child, caption, table, and asset relationships;
7. validation rules and unsupported cases; and
8. whether a missing or malformed value is fatal, warning-level, or explicitly
   represented as unknown.

Canonicalization must consume saved raw JSON, not rerun Docling. It must stream
or partition outputs by document/record family rather than constructing one
corpus-sized object.

## Review pass

- **Semantic fidelity:** transformations preserve rather than embellish parser
  observations.
- **Spatial fidelity:** rotations, coordinate origins, page dimensions, and
  multi-region provenance remain mechanically verifiable.
- **Table and visual fidelity:** structured content and assets do not collapse
  into text-only placeholders.
- **Vendor isolation:** downstream schemas and tests do not require Docling
  imports.
- **Error propagation:** unsupported or ambiguous vendor states become explicit
  records or failures rather than disappearing.

## Validation

- Validate every output record against the Task 03B schemas.
- Verify deterministic IDs and byte-stable canonical serialization on a rerun
  from identical raw input.
- Verify all page, parent, asset, caption, and raw-object references resolve.
- Verify exactly one canonical page record and one linked full-page render
  exist per expected source page.
- Verify bounding boxes are within the declared page coordinate system.
- Compare canonical reading order and representative text against raw Docling
  output and page renders.
- Test multi-region and invalid-reference fixtures.
- Confirm no retrieval-specific cleaning or chunking was introduced.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Core canonical records can be regenerated from saved raw Docling JSON without
  invoking the parser.
- IDs, order, serialization, and raw mappings are deterministic within the
  extraction version.
- Every canonical content record retains exact page-region and raw-object
  provenance.
- Every expected source page has exactly one canonical page record and one
  linked full-page render.
- Tables retain structure and a deterministic textual view without claiming
  unreviewed correctness.
- Figures, extracted assets, and page renders remain distinct and linked.
- Detected figures and visual elements are represented explicitly even when
  they have no usable text; none are silently discarded.
- Unknown, unsupported, and malformed states are explicit.
- Section hierarchy and cross-reference resolution remain deferred to Task 03E.
- The outcome requests user review before Task 03E.

## Non-goals

- changing the parser or its configuration
- final section hierarchy or heading-level repair
- printed-page-label inference
- cross-reference resolution
- human usability review or table verification
- furniture removal for retrieval
- passage construction, chunking, or indexing
- LLM-based cleanup, enrichment, or evaluation
