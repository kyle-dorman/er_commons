# Task 03D: Materialize Core Canonical Records

Status: **complete 2026-07-29; non-release Appendix P core candidate
materialized and verified**.

## Abstract

Implement a deterministic, document-scoped transformation from the complete,
checksum-verified Task 03C.1 Appendix P producer run into the Task 03B
project-owned canonical interface. Consume the saved Docling, routing, clean
table, family, asset, identity, inventory, and completion artifacts without
rerunning Docling, PDFium routing, or Camelot.

Materialize document, page, synthetic root section, block, table, table-family,
figure, image, asset, conversion-observation, routing-observation,
table-stage-observation, and raw-mapping records. Preserve producer reading
order, body-versus-furniture labels, raw and canonical text, geometry,
multi-region provenance, clean rectangular table grids, clean CSV views, and
transitive raw lineage.

This remains a one-document canonicalization pilot. It uses a deterministic
non-release candidate identity so schema-valid records and IDs can be tested,
but it does not freeze the final corpus extraction identity. Final semantic
section hierarchy, printed-page-label inference, and cross-reference extraction
remain later tasks.

## Goal

Give downstream code its first complete, streamable, vendor-isolated canonical
record bundle for one real document while proving that every canonical entity
can be traced to the accepted producer run and checksum-pinned PDF.

## Accepted decisions

- The sole real input is the accepted human-owned Task 03C.1 run for
  `deir_appendix_p`, producer run
  `prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0`.
- Canonicalization consumes the complete producer bundle, not raw Docling JSON
  alone.
- Full-page renders, overlays, diagnostic HTML/Markdown, masks, and debug
  images are not canonical records or completeness requirements. Generate them
  only on demand in the disposable review cache for selected validation pages.
- Canonical tables use the accepted clean Camelot rectangular cell grid plus
  the clean CSV textual view. Do not claim merged-cell spans, header roles, or
  uncertainty fields that the accepted producer and v1 schema do not provide.
- The pilot remains limited to Appendix P. Use a document-scoped, explicitly
  non-release candidate identity and defer the final all-source extraction
  identity.
- Task 03D emits only deterministic synthetic body and furniture root sections
  needed for schema-valid containment. It does not infer semantic heading
  levels or section boundaries.
- Later semantic work remains separate. Task 03E first evaluates Docling's
  maintained hierarchy. If accepted, Tasks 03E.1 and 03E.2 define and
  materialize semantic hierarchy, printed-label evidence, and aliases; Task
  03E.3 keeps reference mentions and resolution behind another review
  boundary.

## Inputs

- completed Task 03B schemas, ordering, ID grammar, provenance policies, and
  artifact contract
- accepted Task 03C.1 producer run and its verified completion record
- saved raw Docling `document.json`, conversion pages, and conversion
  observation
- all 222 saved PDFium routing records and their 34 Docling table-region
  observations
- all clean table page results, 19 logical tables and cell files, clean and raw
  CSV files, 19 exact family assignments, and 19 complete-document families
- all 27 saved picture assets and the producer asset inventory
- the corresponding sealed source-manifest record, release completion record,
  and PDF checksum
- the Task 03C.1 producer identity, runtime configuration, artifact inventory,
  and completion record
- Docling's documented
  [item, group, body/furniture, provenance, table, picture, and JSON-pointer semantics](https://docling-project.github.io/docling/reference/docling_document/)

## Outputs

- a field-level producer-to-canonical mapping specification
- typed canonicalization code isolated from the producer and parser packages
- a package-backed document-scoped canonicalization command with a checked-in
  Appendix P pilot configuration
- a deterministic non-release candidate identity that distinguishes the full
  sealed source release from the ordered one-document materialization scope
- canonical document, page, synthetic section, block, table, table-family,
  figure, image, and asset JSONL records
- a narrow canonical asset-role extension for clean table JSON, clean table
  cells JSON, table-family assignments, and table-family definitions
- canonical conversion, routing, and table-stage observation JSONL records
- raw-to-canonical mapping JSONL records
- a candidate manifest, artifact inventory, canonicalization summary, and
  completion record under a task-scoped pilot artifact root
- validation summaries for counts, canonical order, reading order, references,
  coordinates, text, assets, table mappings, families, and raw lineage
- tiny producer-input-to-canonical-output fixtures covering multi-region text,
  body and furniture, mapped and zero-mapped table regions, document indexes,
  captions, pictures, clean tables, candidate identity scope, and invalid
  references

## Actual Appendix P handoff

The revised mapping and validation must account for these observed producer
facts:

- 222 physical pages and 222 routing records
- 6,931 Docling text items, 27 picture items, 34 Docling table/document-index
  items, 317 groups, and 222 Docling page objects
- body- and furniture-layer items even though the serialized Docling
  `furniture.children` list is empty
- 522 furniture text items: 521 reachable outside pictures and one footer
  nested under a picture that the declared picture policy must account for
- 33 routed pages containing 34 table-region observations because physical page
  84 has two regions
- 19 region-to-one-clean-table mappings and 15 explicit zero-table region
  mappings; the familiar 14 count is zero-table pages, not region mappings
- 19 clean Camelot Lattice tables, 3,669 rectangular cells, 19 exact family
  assignments, and 19 singleton complete-document families
- 27 Docling pictures and 27 checksum-matched saved PNG assets
- seven empty 1-by-1 `document_index` wrappers whose child graphs contain 663
  unique body text items with single-region provenance
- 33 repeated list-parent reconstruction warnings, zero structured errors, and
  terminal producer status `complete_with_warnings`

## Research / learning checkpoint

Inspect the exact saved representations used by this document:

1. follow one ordinary text item from a Docling body-tree position through all
   provenance regions into its canonical block and raw mapping;
2. follow one furniture text item discovered from `content_layer`, not from
   `furniture.children`;
3. follow one mapped Docling table region through its route, clean Camelot
   table, cells, clean CSV, family, observation, and mappings;
4. follow page 84's two regions into one mapped and one zero-table observation;
5. follow one Docling picture into a semantic figure, image, and
   `content_image` asset;
6. follow one `document_index` item and its descendant text items; and
7. follow one item with multiple provenance entries without collapsing its
   valid regions, and account explicitly for any producer-invalid region.

The outcome must explain:

- **Reading order is a model output, not a geometric sort.** Traverse the saved
  Docling body structure and preserve declared order. Use geometry for spatial
  evidence and deterministic table/figure ordering, not to reinvent paragraph
  order.
- **Groups are ordering and lineage evidence, not a new canonical record
  family.** Preserve their raw pointers and traversal effect without inventing
  semantic group entities the canonical schema does not define.
- **Preserved JSON is the immutable input.** Resolve pointers directly against
  the saved dictionary. Revalidating it into a live Docling model may clamp
  producer bounding boxes and would silently change the evidence being
  canonicalized.
- **Furniture is an item-level observation.** Discover it from each item's
  `content_layer`; traversing only the empty serialized furniture root would
  silently discard headers and footers.
- **Block and content labels are producer observations.** Preserve the observed
  label and raw pointer without promoting `section_header`, `caption`,
  `document_index`, or another learned label to unqualified truth.
- **One semantic item may have multiple spatial anchors.** Preserve every valid
  provenance region rather than reducing it to one page or an envelope box.
  For any producer provenance entry whose geometry is malformed or outside its
  declared page, preserve the raw entry verbatim through its raw-object
  lineage, omit it from bounded canonical regions, and emit an explicit
  canonicalization warning. Never clamp, repair, or fabricate a canonical
  region.
- **Docling table regions and canonical tables have different ownership.**
  Docling regions are routing and provenance observations. Only clean Camelot
  outputs become canonical tables.
- **Tables have a bounded dual representation.** Preserve the clean rectangular
  cell grid and clean CSV asset. Do not infer merged spans or semantic header
  roles.
- **Figures, images, assets, and page renders are distinct.** Map each saved
  Docling picture to a semantic figure, an image record, and a checksum-pinned
  content-image asset. Page renders remain disposable review derivatives.
- **Candidate identity is not release identity.** The one-document candidate
  proves deterministic materialization but does not claim that its IDs survive
  later hierarchy work or the final all-source extraction.
- **Data lineage must survive normalization.** Every derived content ID must
  reach a producer artifact, raw object or clean-table record, source manifest,
  and immutable PDF.

## Mapping-policy requirements

Write the field-level mapping specification before implementation. For every
canonical record type, name:

1. producer artifact and raw source path;
2. required and optional fields;
3. ordering and candidate-ID inputs;
4. text and label transformations;
5. page and bounding-box provenance;
6. section, page, caption, table, family, image, asset, and observation
   relationships;
7. raw links and raw-to-canonical mapping roles;
8. validation rules and unsupported cases; and
9. whether a missing or malformed value is fatal, warning-level, or explicitly
   represented as unknown.

The mapping specification must implement these policies:

- Flatten the saved Docling body graph in declared child order, resolve group
  nodes recursively, emit each semantic leaf at most once, and detect cycles,
  unknown pointers, and duplicate traversal.
- Append furniture-layer records in deterministic producer-pointer order after
  body content, consistent with the v1 ordering contract. Do not rely on
  `furniture.children`.
- Emit deterministic synthetic body and furniture root sections when the
  corresponding layer has content. Use `parent_section_id: null`,
  `heading_block_id: null`, raw links to the saved Docling layer anchors, and
  exact inverse ordered-child membership. These roots are containment
  scaffolding, not inferred semantic hierarchy.
- At a Docling table node with one or more clean-table mappings, insert the
  distinct clean canonical tables at that reading-order position and prevent
  table-owned descendant text from being emitted again as duplicate page
  content. Preserve captions as independently emitted blocks and links.
- At a zero-table Docling region, retain the zero mapping and traverse
  descendant semantic text in place when present so source text is not silently
  discarded. Emit an explicit warning or unsupported-state record when no
  descendant content is available.
- Treat the seven observed `document_index` objects as raw table-region
  observations, not canonical tables: each has an empty 1-by-1 Docling cell
  payload, is zero-mapped by the clean table stage, and owns 663 unique
  descendant text items containing the visible index content. Emit those text
  items as individual canonical blocks in declared order; do not concatenate an
  invented index string. Preserve the `document_index` pointer in the
  zero-table observation lineage.
- Map one Docling picture to one canonical figure, one canonical image, and one
  `content_image` asset when the accepted asset inventory has the exact raw
  pointer. Missing, duplicate, or checksum-mismatched picture assets are fatal.
- At picture nodes, traverse explicit captions as independent canonical blocks
  but do not emit other picture-owned descendants as duplicate blocks. Account
  explicitly for the one furniture footer nested under a picture as suppressed
  by this rule rather than silently omitting it.
- Materialize all 34 region-level table-stage observations: 19 with one
  canonical table ID and 15 with an explicit unmapped reason. Do not collapse
  these into the 33 routed pages or 14 zero-table pages.
- Preserve producer warnings verbatim in the responsible conversion or
  table-stage observations. Do not reinterpret them as usability decisions.
- Extend the canonical asset-role enum narrowly with `clean_table_json`,
  `clean_table_cells_json`, `table_family_assignments_jsonl`, and
  `table_families_json`. Represent the raw and clean table JSON, cell, CSV, and
  family files as checksum-pinned assets and links according to their actual
  producer ownership.
- For every raw provenance entry, either emit its unchanged, valid geometry as
  a canonical region or record an explicit warning that identifies the raw
  object, provenance index, and rejection reason. Preserve the complete raw
  entry through lineage in both cases. Invalid geometry must not be silently
  dropped, normalized, clamped, repaired, or replaced with a fabricated
  anchor.

Canonicalization must read saved artifacts only. It must stream or partition
records by family and must not build a corpus-sized in-memory object. The
existing exhaustive bundle validator may be used for this one-document pilot;
Task 03F or later owns the bounded two-pass batch validator.

## Candidate identity and publication

The final corpus `extraction_id` remains deferred. Task 03D must nevertheless
produce schema-valid, deterministically named pilot records:

- define an explicitly non-release candidate identity bound to the full sealed
  source release, the selected ordered materialization scope
  `[deir_appendix_p]`, the accepted producer run and inventory, canonical
  schema and mapping-policy versions, and clean project code identity;
- revise the pre-release identity schema and validator narrowly so the full
  release inventory remains distinct from the selected materialized document
  subset;
- keep the canonical record field named `extraction_id` for contract
  compatibility, but mark the identity and completion record as a
  document-scoped candidate that is not the final corpus extraction;
- publish under a task-scoped pilot root rather than the final
  `datasets/ceqa/derived/brisbane_baylands/<final_extraction_id>/` release root;
- use staging, atomic no-clobber publication, a checksummed inventory, and a
  completion record written last;
- verify every inventoried checksum before reusing a matching candidate; and
- never mutate a completed candidate when hierarchy or corpus scope changes.
  A later interpretation or scope receives a new candidate or final identity.

## Review pass

- **Semantic fidelity:** transformations preserve rather than embellish
  producer observations.
- **Order fidelity:** mixed blocks, clean tables, and figures follow declared
  Docling order, with explicit replacement behavior at table nodes.
- **Spatial fidelity:** rotations, coordinate origins, page dimensions, and
  multi-region provenance remain mechanically verifiable.
- **Table fidelity:** the clean grid, CSV, cleanup evidence, family membership,
  and 34-region crosswalk remain complete without claiming unavailable spans or
  header semantics.
- **Visual fidelity:** figures, images, content assets, and disposable renders
  remain distinct.
- **Vendor isolation:** downstream schemas, records, and tests do not import
  Docling or Camelot.
- **Identity discipline:** the one-document candidate cannot be mistaken for
  the final corpus extraction.
- **Error propagation:** unsupported or ambiguous producer states become
  explicit warnings, records, or failures rather than disappearing.

## Validation

- Validate every emitted record against the revised Task 03B schema bundle.
- Verify deterministic candidate identity, IDs, ordering, and byte-stable JSON
  or JSONL serialization on a second run from identical saved input.
- Verify all page, synthetic section, asset, caption, family, observation, and
  raw-object references resolve.
- Verify one canonical page record exists for each of the 222 expected source
  pages. Do not require or emit full-page render assets.
- Verify the body traversal preserves declared mixed-content order and that
  all 522 furniture items are accounted for despite the empty serialized
  furniture root: 521 emitted outside pictures and one explicitly suppressed
  picture descendant.
- Verify all emitted canonical bounding boxes are within the declared page
  coordinate system. For every raw provenance entry, verify that it either
  appears unchanged as a valid canonical region or is explicitly accounted for
  by a warning with its raw-object pointer, provenance index, and rejection
  reason.
- Verify exactly 34 table-stage observations, 19 one-table mappings, 15
  zero-table mappings, 19 clean tables, and 19 symmetric table-family
  memberships.
- Verify every clean table has a complete rectangular grid matching its shape
  and a checksum-pinned clean CSV asset.
- Verify all seven `document_index` objects remain zero-table observations and
  their 663 descendant text items remain present once in canonical reading
  order.
- Verify all 27 pictures have distinct figure, image, and checksum-valid
  content-image asset records with exact raw pointers.
- Test mapped-table descendant suppression, zero-table descendant fallback,
  captions, group cycles, duplicate traversal, multi-region items, furniture,
  candidate scope, and invalid references with tiny fixtures.
- Verify canonicalization reads the preserved JSON dictionary directly and
  does not round, clamp, or otherwise mutate raw producer geometry before
  validation.
- Generate a small on-demand review-cache sample and compare representative
  canonical text, tables, figures, and geometry to the PDF. The cache remains
  outside extraction completeness.
- Confirm no retrieval cleaning, chunking, inferred hierarchy,
  printed-page-label inference, cross-reference resolution, or human usability
  fields were introduced.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- The Appendix P core candidate can be regenerated from the verified Task
  03C.1 producer run without invoking any producer.
- The candidate identity explicitly names one selected materialized document
  and cannot be mistaken for the final all-source extraction identity.
- IDs, order, serialization, and raw mappings are deterministic within that
  candidate.
- Every canonical content record retains exact producer-object or clean-table
  lineage and all valid page-region provenance; every producer-invalid
  provenance entry remains verbatim in raw lineage and is explicitly
  accounted for without fabricated geometry.
- Every expected source page has exactly one canonical page record; page
  renders remain optional disposable review artifacts.
- Synthetic body/furniture root sections make containment schema-valid without
  claiming semantic hierarchy.
- Clean tables retain their rectangular cell grids, clean CSV views, cleanup
  evidence, region mappings, and complete-document family assignments without
  claiming unrepresented topology.
- All 34 Docling table regions remain explicit observations, including all 15
  region-level zero mappings.
- Document-index and other zero-table content is preserved through explicit
  descendant fallback or an explicit unsupported state; it is never silently
  discarded or promoted to a clean canonical table.
- Figures, images, content assets, and review renders remain distinct.
- Unknown, unsupported, and malformed states are explicit.
- Section hierarchy, printed-page-label inference, and cross-reference work
  remain deferred to revised follow-on tasks.
- The outcome requests user review before hierarchy work begins.

## Non-goals

- changing or rerunning the accepted parser, router, table reconstruction,
  cleanup, footer ownership, or family assignment
- freezing the final corpus extraction identity or release root
- processing a second document or implementing batch orchestration
- semantic section hierarchy or heading-level repair
- printed-page-label inference
- cross-reference mention extraction or resolution
- merged-cell, row-header, column-header, or uncertainty inference beyond the
  accepted clean table representation
- permanent full-page render or diagnostic export
- human usability review or table verification
- furniture removal for retrieval
- passage construction, chunking, or indexing
- LLM-based cleanup, enrichment, or evaluation

## Outcome

Task 03D is complete. The implementation adds a separate
`canonical_extraction` application boundary with strict configuration, verified
plain-data inputs, deterministic candidate identity, saved-dictionary Docling
traversal, clean-table projection, record materialization, schema and
cross-record validation, checksum inventory, completion-last publication, and
checksum-verified reuse. The package imports neither Docling nor Camelot in the
canonicalization path.

The field-level mapping is frozen in
[`docs/specs/task03d_appendix_p_mapping_v1.md`](../../docs/specs/task03d_appendix_p_mapping_v1.md).
The shared v1 schema now keeps the complete 35-source sealed release distinct
from the selected materialization scope. A document candidate must be marked
non-release and binds its ordered source IDs, accepted producer run and
inventory, and mapping policy. Dirty Git state is recorded truthfully for this
non-release candidate, while a future release candidate still requires clean
code. The asset enum was extended only for clean table JSON, clean table cells,
family assignments, and family definitions.

Inspection found one important producer-to-canonical distinction. The 19 saved
`cells.json` files contain 3,776 raw Camelot cells, while the accepted clean
shapes and CSVs contain 3,669 cells. Eight tables remove one empty raw column.
Canonicalization therefore applies the recorded removed-row and retained-column
indices, reindexes the surviving grid, compares every retained cell with the
clean CSV, preserves raw cell assets, and writes separate checksum-pinned clean
table and clean-cell assets. No merged spans or header semantics are inferred.

The completed candidate is:

```text
extraction_id:
  exv1-9e33eb783b4145fa25065121de851d9055dfd6275066dcd80243ecde3b321774
completion_record:
  pipelines/brisbane_baylands/task_03d_canonical_records/
  exv1-9e33eb783b4145fa25065121de851d9055dfd6275066dcd80243ecde3b321774/
  records/completion_record.json
```

It contains 1 document, 222 pages, 2 synthetic roots, 3,706 blocks, 19
tables, 19 table families, 27 figures, 27 images, 146 assets, 222 routing
observations, 34 region-level table-stage observations, one conversion
observation, and 3,798 raw mappings. The 34 table regions split exactly into
19 mapped and 15 zero mapped. All 3,669 clean cells are rectangular and
CSV-matched. All seven `document_index` wrappers remain zero mapped and their
663 unique descendant text items are emitted once.

All 6,931 Docling text items are accounted for: 3,706 emit as blocks and 3,225
are explicitly suppressed as mapped-table or picture-owned descendants.
Furniture accounting is exactly 522 producer items, 521 emitted, and the one
picture-owned footer at `#/texts/312` explicitly suppressed. Thirty-seven
multi-provenance text items retain all valid anchors. The single invalid entry,
`#/texts/4634` provenance index 1, remains verbatim in raw lineage and is
reported as out of page bounds without clamping; its valid provenance index 0
is retained.

The candidate is `complete_with_warnings`: 33 producer list-parent warnings,
15 explicit zero-table mappings, and the one rejected invalid provenance
entry. There are zero structured errors. An independent fresh staging build
matched all 57 candidate-owned files byte for byte. A second normal invocation
checksum-verified reuse without conversion or table parsing.

Disposable 144-DPI review-cache renders and overlays for physical pages 4, 84,
and 104 were validated against the review-cache schema. Visual inspection
confirmed document-index text alignment, the page-84 clean table boundary and
descendant suppression, and the page-104 figure, caption, and surrounding text
geometry. These six derivatives are outside candidate completeness.

Focused tests cover candidate scope, input seals, table cleanup, the page-84
one/zero crosswalk, traversal and cycles, document-index fallback, picture and
furniture suppression, multi-region and invalid provenance, publication
no-clobber behavior, and checksum reuse. Final project validation completed:

```text
make fix
make check
git diff --check
```

The current planned sequence remains inactive pending user review. Task 03E
first evaluates Docling's maintained heading hierarchy. If accepted, Task
03E.1 defines semantic hierarchy, printed-label, alias, evidence, ambiguity,
and correspondence contracts; Task 03E.2 materializes them; and Task 03E.3
pilots reference mentions and within-document resolution.
