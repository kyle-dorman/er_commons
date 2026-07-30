# Canonical Extraction Contract v1

Status: **MVP candidate for Task 03B review**. This contract defines a
candidate extraction representation. Task 04, not Task 03B, decides whether a
candidate is usable and may freeze it as extraction v1.

## Purpose and boundary

The canonical layer is a project-owned spatial graph over immutable producer
artifacts. It is not a renamed Docling document, a Camelot dataframe, a
retrieval-passage format, or a human-review registry.

Docling with PyPdfium2 and Heron owns native text, layout, reading order,
hierarchy observations, figures, and provenance. PDFium owns native-text page
measurements. Project routing code owns threshold results and route selection.
The clean Camelot pipeline owns reconstructed tables and cells. Project table
code owns cleanup evidence, footer ownership, and complete-document table
families. TableFormer is disabled and its historical cells are never canonical
input.

The executable JSON Schema bundle is
[`records.schema.json`](../../benchmarks/er_bench/schemas/canonical_extraction/v1/records.schema.json).
The prose contract owns invariants that JSON Schema cannot express across
records.

## Producer ownership and mapping matrix

| Layer | Immutable input or output | Meaning owned here | Canonical use |
| --- | --- | --- | --- |
| Sealed source release | Source manifest and completion seal | Source bytes, role, checksum, warnings, and release order | Only `model_corpus` records become documents |
| Docling | Lossless `document.json`, conversion pages, images, and conversion record | Native text, labels, reading order, content layer, figures, and zero/one/many provenance entries | Blocks, hierarchy observations, figures, images, and raw links |
| PDFium router | Page-route JSONL | Native-text measurements, threshold results, and selected route | Routing observations only |
| Heron through Docling | Table-labeled document items and provenance | Candidate table regions | Raw region observations, never canonical cells |
| Camelot clean pipeline | Page/table records, cell JSON, raw and clean CSV | Reconstructed logical tables and producer-normalized cells | Canonical tables and cells with producer lineage |
| Project table cleanup | Cleanup records and cleaned artifacts | Removed footer/filename rows and footer-only columns | Explicit cleanup operations and cell lineage |
| Project footer/family stage | Footer ownership, assignments, and families | Machine continuation evidence over a complete document | First-class table-family records |
| Review cache | Page renders, annotations, masks, HTML, and Markdown | Regenerable inspection aids | Never canonical; generated only for requested review or labeling pages |
| Task 04 | Separate registry keyed by extraction and canonical IDs | Human usability, exclusions, disposition, reviewer, and review date | Never embedded in Task 03 records |

## Why these representations

Docling stores typed content in top-level collections and expresses hierarchy
through JSON-pointer parent and child references. Its body reading order is a
tree, while provenance is a list because an item can occupy multiple regions.
The current API also marks the dedicated furniture root deprecated in favor of
content-layer classification. The canonical contract therefore preserves raw
pointers as producer locators but owns its own hierarchy edges and
`body`/`furniture` classification.

Docling JSON is the lossless producer serialization. Markdown and rendered HTML
are QA views, not canonical inputs. Raw Docling JSON must be saved without
coordinate or confidence rounding.

Camelot Stream reconstructs tables from text alignment; Lattice reconstructs
ruled cells from page geometry. Its cells use bottom-left PDF coordinates and
its parsing report is parser diagnostics, not semantic correctness. Raw cell
geometry, edge evidence, parser flavor, and report values stay in immutable
producer artifacts. Canonical cells come only from the accepted clean table
pipeline and retain their producer row and column lineage.

JSON Schema Draft 2020-12 supplies strict, portable record validation. A local
schema registry is used for offline validation; schemas never retrieve network
references. Cross-record ordering, scope, geometry, and referential checks
remain explicit contract tests because structural schemas cannot prove them.

Primary guidance:

- [Docling document model](https://docling-project.github.io/docling/concepts/docling_document/)
- [Docling API reference](https://docling-project.github.io/docling/reference/docling_document/)
- [Docling serialization](https://docling-project.github.io/docling/concepts/serialization/)
- [Camelot parser behavior](https://camelot-py.readthedocs.io/en/stable/user/how-it-works.html)
- [Camelot API](https://camelot-py.readthedocs.io/en/stable/api.html)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html)

## Extraction identity

`extraction_id` is `exv1-` followed by the complete lowercase SHA-256 of an RFC
8785 serialization of the identity payload. The payload excludes timestamps,
machine names, timing, output paths, and the digest itself. It contains:

1. identity schema version;
2. source release version, sealed manifest path and SHA-256, completion-record
   path and SHA-256, and manifest-ordered `model_corpus` source IDs, SHA-256s,
   and page counts;
3. materialization scope kind and release status, ordered selected source IDs,
   the producer run and checksum-pinned artifact inventory for each selected
   source, and the canonical mapping-policy version and checksum;
4. Docling configuration ID, pipeline and backend classes, effective options,
   package versions, model inventory checksum, and resolved model revisions and
   file checksums;
5. Camelot, PDFium, and OpenCV versions plus routing, detection, cleanup, and
   family configuration hashes;
6. canonical schema, ID, ordering, and serialization policy versions; and
7. project Git commit, truthful dirty-worktree state, and owned-code bundle
   SHA-256.

`source_release.ordered_model_corpus` always preserves the complete sealed
release inventory. `materialization_scope.ordered_source_ids` separately names
the ordered subset actually emitted as canonical documents. Every selected
source must match one full-release checksum and page count, and its producer
run must appear in the same order. A document-scoped candidate is explicitly
`non_release_candidate`; it must not be presented as the final corpus
extraction.

Non-release candidates record `git_dirty` truthfully and may set it to true so
bounded development pilots do not require a user-unrequested commit. A
`release_candidate` must reject dirty code. Any meaning- or behavior-changing
identity field produces a new `extraction_id` and a new artifact root.
Low-level IDs are reproducible only inside that extraction. Identical local
names in different extractions do not identify the same anchor.

## Record IDs and order

Every record ID starts with its complete `extraction_id`, followed by `/`, a
type token, `/`, and a deterministic local key:

```text
<extraction_id>/document/<source_id>
<extraction_id>/page/<source_id>/p000001
<extraction_id>/section/<source_id>/sec000001
<extraction_id>/block/<source_id>/blk000001
<extraction_id>/table/<source_id>/tbl000001
<extraction_id>/table-family/<source_id>/fam000001
<extraction_id>/figure/<source_id>/fig000001
<extraction_id>/image/<source_id>/img000001
<extraction_id>/asset/<source_id>/<role>/ast000001
<extraction_id>/cross-reference/<source_id>/xref000001
<extraction_id>/routing-observation/<source_id>/route-p000001
<extraction_id>/table-stage-observation/<source_id>/stage-p000001-o000001
<extraction_id>/conversion-observation/<source_id>/conv000001
<extraction_id>/raw-mapping/<source_id>/map000001
```

Full digests are used rather than truncated digests, so collision fallback is
not a hidden runtime policy. Type-specific local prefixes are deliberately
redundant with the path namespace because they make IDs easier to scan in
fixtures, logs, labels, and review tools. Duplicate IDs are fatal.

Sources use sealed manifest order. Pages use ascending one-based physical PDF
page number. Sections and blocks use Docling body-tree reading order, followed
by furniture records, with raw producer pointer as the final tie-breaker.
Tables use physical page, top-to-bottom then left-to-right visual position, and
clean producer table ID as tie-breaker. Figures and images use the same spatial
rule. Cross-references and observations use source record order.

Sequential local keys are assigned only after the complete ordered record set
for one document is known. A table-family ID is assigned only after every page
of that document has completed table processing. A partial-page run must set
`document_scope_complete` to false and must not emit table-family records.
Pilot family numbers are provenance evidence only.

## Serialization and artifact layout

Records are UTF-8 JSON Lines, one strict schema-valid object per line, with a
terminal newline. Manifest and identity records are ordinary JSON. Records are
streamed by family; no corpus-sized JSON tree or database is required.
Referenced binaries and producer artifacts keep byte checksums.

Production validation is a bounded two-pass stream per document. Pass one
schema-validates each JSONL object, checks order and counts, and retains only a
compact ID/type/document/page index. Pass two streams the files again to check
references, mappings, geometry, and inverse membership against that index.
The index is discarded after the document is sealed; only document IDs are
retained for the corpus manifest. The in-package `validate_bundle_integrity`
helper is intentionally an exhaustive validator for tiny fixtures or one
already materialized document, not the Task 03G batch implementation.

The executable helper is organized by ownership rather than record count:

- `identifiers.py`, `identity.py`, and `geometry.py` contain independent,
  reusable primitives;
- `bundle.py` provides the indexed view and shared traversal rules for
  references, regions, and raw links;
- `policies/bundle.py` owns extraction identity, IDs, manifest agreement,
  document scope, and ordering;
- `policies/content.py` owns geometry, hierarchy, tables, text, and page
  content; and
- `policies/lineage.py` owns document isolation, raw mappings, producer
  compatibility, cross-references, and captions.

`validation.py` is the ordered checklist of those policies. JSON Schema remains
the first validation layer; the Python policies assume schema-valid records and
enforce only relationships that require the materialized bundle.

The version-owned external root is:

```text
datasets/ceqa/derived/brisbane_baylands/<extraction_id>/
  records/
    extraction_identity.json
    manifest.json
    artifact_inventory.json
    completion_record.json
  canonical/
    documents.jsonl
    pages.jsonl
    sections.jsonl
    blocks.jsonl
    tables.jsonl
    table_families.jsonl
    figures.jsonl
    images.jsonl
    assets.jsonl
    cross_references.jsonl
  mappings/raw_to_canonical.jsonl
  observations/
    conversion.jsonl
    routing.jsonl
    table_stage.jsonl
  documents/<source_id>/producer/
    docling/
    routing/
    tables/
  documents/<source_id>/assets/
    figures/
    images/
  logs/
```

Existing Task 03A roots remain immutable evidence. Producers write immutable
artifacts first. Canonical records reference them by `asset_id` and
`raw_object_ref`. A completion record is published last.

Canonical asset roles include preserved raw Docling, conversion, routing,
table, and image artifacts. The clean table stage additionally uses
`clean_table_json`, `clean_table_cells_json`, and `clean_table_csv`; complete
family lineage uses `table_family_assignments_jsonl` and
`table_families_json`. These checksum-pinned producer artifacts remain
distinct from canonical table and table-family records.

Full-page renders, annotated overlays, diagnostic HTML and Markdown, ruling
masks, and table-debug images are not extraction artifacts and do not
participate in extraction completeness. They are generated only for pages
requested during review or labeling and may be cached separately at:

```text
pipelines/brisbane_baylands/review_cache/<extraction_id>/
  <source_id>/p000001/
    review_cache_entry.json
    page.png
    overlay.png
    diagnostic.html
    diagnostic.md
```

Each cache entry records the extraction ID, checksum-pinned source, physical
page, derivative type, render/configuration hash, generator-code hash, output
checksum, and byte size. Cache entries are disposable and reproducible. They
may be deleted without changing the extraction manifest or canonical IDs. A
converter may render pages transiently when required internally, but must not
archive one render or diagnostic document per parsed page.

## Source and edition provenance

Only sealed `model_corpus` records may become canonical documents. Duplicate,
curator-response, and curator-QA roles are rejected from this namespace.

Each document retains the source manifest warnings verbatim. A warning with
the reviewed `source_edition_override:` prefix additionally becomes a
structured `source_edition_override` object containing the exact warning,
approved source record identifier, and provenance landing-page key. Every page
inherits the identical object. The override is a source-provenance fact, not a
usability, exclusion, or disposition decision.

The mechanical lineage chain is:

```text
canonical record
  -> raw mapping
  -> raw producer object and provenance index
  -> immutable producer asset
  -> sealed source manifest record
  -> checksum-pinned PDF
```

## Geometry

Physical PDF pages are one-based. Printed page labels are nullable strings and
must never replace physical page numbers. Worksheet footer counters are family
evidence, not printed page labels.

Canonical geometry uses PDF points, the full page box, zero rotation, and a
bottom-left origin:

```text
[left, bottom, right, top]
0 <= left < right <= page_width
0 <= bottom < top <= page_height
```

All source regions preserve their producer coordinate system and origin.
Regions include page width, page height, rotation, and an optional render
scale. Multi-page and multi-region entities store a list and must not be
collapsed to an envelope box.

For an unrotated page rendered at `scale = render_dpi / 72`, transform PDF
points to top-left render pixels as:

```text
x_left_px   = left * scale
y_top_px    = (page_height - top) * scale
x_right_px  = right * scale
y_bottom_px = (page_height - bottom) * scale
```

The inverse divides x by scale and subtracts y from page height. Rotated or
cropped pages require an explicit affine transform in the producer observation
before canonicalization; they may not silently use the unrotated formula.
Out-of-bounds or inverted boxes are fatal contract errors.

## Text, hierarchy, and relationships

`raw_text` means unmodified Docling text only. Table text is named
`producer_normalized_text` because the accepted table pipeline already applies
NFKC and whitespace normalization. `canonical_text` initially equals the
responsible producer text. Only explicitly recorded lossless operations are
allowed in Task 03:

- `none`;
- `unicode_nfc` when the original value remains present; and
- `line_ending_lf` when the original value remains present.

Dehyphenation, whitespace repair, ligature substitution, furniture removal,
case folding, and retrieval normalization are not canonical extraction
operations. They belong to later derived passage records.

Sections express containment; ordered child IDs express reading order. Page
regions, captions, images, tables, and cross-references are graph edges.
Cross-reference resolution may remain `unresolved` or `ambiguous`; Task 03B
does not require semantic resolution.

Docling table regions are observations, never canonical tables. Raw mappings
identify the Docling artifact, object pointer, and provenance-entry index.
Table-stage observations map one observed region to zero, one, or many distinct
clean tables. Full-page Stream may map a page-level observation to multiple
tables without a Docling region. Distinct clean tables remain distinct even
when they share one table family.

## Machine status and Task 04 handoff

Conversion, routing, table-stage, and canonicalization status are separate:

- conversion: producer run success, partial result, or failure;
- routing: observed route and threshold evidence;
- table stage: reconstruction, cleanup, footer, and family completion;
- canonicalization: schema, ordering, and referential-integrity completion.

Allowed machine statuses are `not_started`, `running`, `complete`,
`complete_with_warnings`, `partial`, `failed`, and `not_applicable`. No status
means usable, excluded, accepted, or review-complete.

Reviewer identity, review date, usability, exclusion, document disposition,
page disposition, and curator notes are forbidden properties in every Task 03
record. Task 04 owns a separate registry keyed by `(extraction_id,
canonical_id)`. Retrieval and target-facing code may consume only canonical
machine records and later Task 04-approved filters; it may not consume raw
curator-only source roles or Task 04 annotations directly.

## Required integrity checks

An offline validator must:

1. validate every record against its strict schema;
2. require one extraction ID and schema version throughout a manifest;
3. reject duplicate IDs and references outside the extraction;
4. verify all document, page, hierarchy, caption, asset, family, mapping, and
   cross-reference targets;
5. require the fixed canonical order and unique sequence values;
6. check region bounds and page dimensions;
7. preserve zero/one/many table-region mappings without merging table IDs;
8. reject table-family records for incomplete documents and require each table
   to belong to exactly one family when scope is complete;
9. keep machine status families separate;
10. require identical document/page edition-override metadata; and
11. reject Task 04 fields and non-model source roles.

## Compatibility

Adding an optional field without changing meaning is schema-minor compatible.
Changing a required field, ID grammar, ordering, coordinate semantics, producer
ownership, normalization, or status meaning is schema-major incompatible and
creates a new extraction identity. Old extraction roots are never rewritten.

Later tasks may add retrieval passages and human-review registries as separate
derived contracts. They may reference canonical IDs but may not add their
fields to these record schemas.
