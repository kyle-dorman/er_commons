# Task 03D Appendix P Canonical Mapping v1

Status: **implementation specification for the approved one-document Task 03D
candidate**.

## Boundary

This mapping consumes only the checksum-verified Task 03C.1 producer run
`prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0`.
It reads saved JSON, JSONL, CSV, cell, image, source-release, and producer
inventory artifacts. It does not invoke Docling, PDFium routing, Camelot, or a
learned model.

The output is a document-scoped, non-release candidate. Its identity retains
the full ordered sealed source-release inventory and separately binds the
selected materialization scope `[deir_appendix_p]`, accepted producer run and
inventory, this mapping policy, canonical schema, and clean project code. It is
not the final corpus extraction identity.

## Shared rules

- Resolve Docling JSON pointers against the preserved `document.json`
  dictionary. Never revalidate the dictionary into a live Docling model.
- Flatten `body.children` recursively through groups in declared order. A
  semantic pointer may be emitted at most once. A group cycle, unknown pointer,
  or duplicate semantic traversal is fatal.
- A mapped Docling table pointer is replaced in reading order by its distinct
  clean canonical tables. Its non-caption descendants are suppressed.
- A zero-mapped table or `document_index` pointer emits its descendant semantic
  text in declared order. A zero mapping with no descendant text is warning
  level.
- Picture captions remain independent blocks. Other picture descendants are
  suppressed, including the one observed furniture footer, which is counted
  explicitly in the summary.
- After body traversal, append every otherwise-unemitted furniture text item in
  ascending producer-pointer index. `content_layer`, not
  `furniture.children`, owns furniture membership.
- Preserve `orig` as `raw_text`. Set `canonical_text` from `orig` using only
  declared NFC or line-ending normalization. Docling's saved `text` remains
  recoverable through the raw JSON link but is not substituted when it removes
  list markers or numbering, because that is not one of the v1 lossless
  canonical operations.
- Convert every valid Docling bottom-left bounding box directly to
  `[left, bottom, right, top]`. Preserve all valid provenance entries. An
  inverted, non-finite, unknown-page, or out-of-bounds entry is omitted from
  canonical regions, preserved through its raw object, and recorded in
  `canonicalization_summary.json.invalid_provenance` with raw pointer,
  provenance index, and rejection reason. Never clamp or fabricate geometry.
- IDs are assigned only after deterministic order is known. Synthetic roots
  use body then furniture order. Blocks follow body traversal then furniture.
  Tables, figures, and images use physical page, top-to-bottom, left-to-right,
  then producer ID or pointer. Observations preserve producer order.
- Raw links use producer-relative JSON pointers. File-root records use `/`;
  JSONL rows use `/<zero-based-row>`; JSON arrays or objects use their exact
  JSON pointer.
- Missing required input, checksum mismatch, ambiguous producer ownership,
  invalid reference, picture asset mismatch, or incomplete rectangular table
  is fatal. Preserved producer warnings and unsupported zero mappings are
  warning level. Nullable schema fields remain explicit `null`.

## Record mapping

| Canonical record | Producer source and path | Field and relationship policy | Raw mapping and validation |
| --- | --- | --- | --- |
| Identity | sealed `source_manifest.json` and release completion; producer `producer_identity.json`, inventory, and completion; checked-in schema, mapping spec, config, and owned code | Preserve the full release in `source_release.ordered_model_corpus`. `materialization_scope` names `document_scoped_candidate`, `release_candidate: false`, ordered selected source IDs, producer run/inventory, and mapping policy. RFC 8785 plus SHA-256 supplies `extraction_id`. | Selected sources must exist unchanged in the full release. Candidate identity, manifest, and completion must agree exactly. |
| Document | selected sealed source record plus producer completion | Copy source ID, checksum, role, title, page count, warnings, and structured edition override. Set complete document scope and link all pages and the one conversion observation. | Source record and PDF checksum must match producer completion and source manifest. |
| Page | `document.json.pages`, routing JSONL | One record for each physical page 1–222. Dimensions come from saved Docling pages and must agree with routing dimensions within recorded producer precision. Printed label is `null`. Link routing observation and page-local content in canonical reading order. | Page order and completeness are fatal invariants. No page render asset is emitted. |
| Synthetic section | saved `#/body` anchor and furniture classification | Emit body and furniture roots only when the layer has content. Parent and heading are `null`. Ordered children are the exact inverse membership of emitted blocks, tables, and figures. | Raw link body to `#/body`; furniture to the set anchor `#/furniture` while membership still comes from item `content_layer`. These roots are scaffolding only. |
| Block | Docling `#/texts/<n>` | Preserve label as `block_type`, `content_layer`, `orig` as both raw and initially canonical text, declared lossless normalization, all valid regions, and raw pointer. The producer's separately normalized `text` remains in raw lineage. Attach to the matching synthetic root. Captions are ordinary caption blocks linked from their table or figure. | One text pointer may emit once. Each block receives text and geometry mappings to the raw Docling asset. Invalid provenance is accounted for in the summary. |
| Table | `tables.jsonl`, raw `table.json`, raw `cells.json`, and clean CSV | The producer's `cells.json` still contains the raw Camelot grid even when cleanup removes rows or columns. Apply `removed_footer_row_indices`, `removed_filename_row_indices`, and `retained_column_indices`, then reindex retained rows and columns to materialize the clean rectangular grid named by `shape_clean`. Preserve the raw cells asset and write separate candidate-owned clean table JSON and clean cells JSON assets. `producer_normalized_text` and `canonical_text` come from retained cells. Link family, captions, table-stage observations, raw and clean table JSON/cells, raw CSV, and clean CSV assets. No spans or header roles are inferred. | Shape and all retained cell positions must be complete and clean cell text must reproduce the clean CSV. Clean CSV checksum is required. Raw links distinguish Camelot reconstruction from project cleanup. Appendix P retains 3,669 of 3,776 raw cells; eight tables lose one empty column and no table loses a row. |
| Table family | `family_assignments.jsonl` and `table_families.json` | Preserve exact complete-document membership and producer family evidence. Sequence by first member table order. | Every table appears in exactly one family and inverse membership is exact. Family assets and a derived-family raw mapping are required. |
| Figure | Docling `#/pictures/<n>` | One semantic figure per picture with every valid picture region, caption block IDs, one image ID, body/furniture root membership, and producer label observation. | Picture pointer must have exactly one inventory asset. Figure gets geometry lineage to raw Docling. |
| Image | producer `asset_inventory.json` and saved PNG | One image per figure, with media type, pixel dimensions, checksum, linked `content_image` asset, and source figure record. | Saved bytes, inventory checksum, pointer, and figure page must agree. Missing, duplicate, or mismatched assets are fatal. |
| Asset | producer inventory and checksummed producer files | Emit checksum-pinned source PDF, raw Docling JSON, routing JSONL, clean-table JSON/cells/raw CSV/clean CSV, family assignment/definition, and content-image records. Roles include the narrow 03D extensions `clean_table_json`, `clean_table_cells_json`, `table_family_assignments_jsonl`, and `table_families_json`. | Paths are relative to the immutable producer or release root. Page renders and diagnostics are excluded. Asset ID role and record role must agree. |
| Conversion observation | `conversion_observation.json` | Preserve complete-with-warnings status, page range, pipeline/backend classes, raw document asset, structured errors, and all 33 warnings verbatim. | Exactly one observation covers pages 1–222 and links the saved Docling JSON. |
| Routing observation | each row of `page_routes.jsonl` | Preserve page, status, route, native-text features, strict/numeric checks, raw table-region pointers, and warnings. | Exactly 222 in physical-page order; each points to its page and raw routing asset. |
| Table-stage observation | routing table regions plus table page results | Emit one record per Docling region, not per page: 34 total. Map 19 regions to one clean table each and 15 to an explicit unmatched reason. Page 84 retains separate mapped and zero-mapped observations. Preserve parser diagnostics and producer warnings. | Region pointer and provenance index identify ownership. Counts 34/19/15 are fatal invariants. The seven `document_index` wrappers remain zero mapped. |
| Raw mapping | all derived content | Emit at least one mapping for every block, table, family, figure, and image. Use text, geometry, producer-table, or derived-family roles as appropriate. | Every raw link resolves to a checksum-pinned asset and compatible producer. The complete chain reaches the sealed source and PDF. |
| Manifest, inventory, summary, completion | materialized JSONL and assets | Manifest names canonical files in contract order. Inventory checksums every candidate-owned file. Summary records counts, traversal accounting, invalid provenance, suppressed picture descendants, and validation results. Completion marks non-release candidate status and is written last. | Publish through staging with atomic no-clobber rename. Reuse requires exact identity, inventory, checksum, completion, and managed-file-set verification. |

## Appendix P acceptance totals

The real run must contain 222 pages and routing observations; 34 region-level
table-stage observations split into 19 mapped and 15 zero mapped; 19 clean
tables with 3,669 rectangular cells; 19 exact family assignments and 19
families; 27 figures, images, and content-image assets; seven zero-mapped
`document_index` wrappers whose 663 unique descendant text items emit once;
and all 522 furniture items accounted for as 521 emitted plus one explicitly
suppressed picture descendant.

The candidate may complete with warnings for the 33 preserved Docling
list-parent warnings, zero-table fallbacks, and any explicitly rejected
producer-invalid provenance. It must contain zero structured errors.

## Unsupported scope

This mapping does not infer semantic hierarchy, printed page labels,
cross-references, merged cells, header roles, uncertainty, retrieval cleaning,
chunks, usability, exclusions, or final release identity. Those changes require
a later candidate or extraction identity and never mutate this completed
candidate.
