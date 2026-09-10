# Task 06B conversion boundaries v1

Historical conversion and producer readers derive identity from the stored
preimage, preserving recorded implementation paths even when absent today.
Compact readers validate schema, source, terminal seal and exact managed path/size
closure; they do not open Docling payloads, PDFs or models, and cannot establish
fresh payload-byte equality. Explicit deep audit retains that responsibility.
Completed range readers use the recorded frozen plan and completion. Incomplete
execution continues through `verify_chunk_inputs`, which compares every runtime
binding to current behavior and rejects changed adapters/models/sources.

Current conversion inventory retains its existing explicit content/heading
owners, adds config and identity serialization, and replaces the source-release
glob with only `source_release/models.py` (the consumed manifest contract).
Acquisition code, CLI and task wrappers are excluded. Current producer inventory
retains the existing explicit content list and freezes the existing table package
files as an explicit tuple; it adds the consumed source manifest contract.
Chunk groups retain their original explicit paths and add shared artifact JSON,
range/page contracts, projection/routing/table-marker and heading contracts to
all actual consumers. These are conservative file boundaries: edits within a
shared owner invalidate its consumers even if one function is unaffected.

The ordered tuples in these owners are the executable finite inventories. Missing
listed current dependencies fail; historical readers never resolve those paths.
All new compact readers use the shared invocation verification budget: 1 MiB per
allowlisted hash record and 32 MiB per invocation, with oversized inventory reads
reported as metadata checks. Per-source original manifests remain identity input;
replacement membership never rewrites existing seals or converts unchanged bytes.

Additional bounded owner: `content_parsing/evidence.py` supplies the producer
compact reader and exact closure checks; its existing deep verifier remains.

## Conversion current writer

```text
src/er_commons/artifact_io.py
src/er_commons/artifact_verification.py
src/er_commons/document_parsing/content_parsing/config.py
src/er_commons/document_parsing/content_parsing/identity.py
src/er_commons/source_release/models.py
src/er_commons/document_parsing/content_parsing/artifacts.py
src/er_commons/document_parsing/content_parsing/conversion.py
src/er_commons/document_parsing/content_parsing/conversion_bundle.py
src/er_commons/document_parsing/content_parsing/conversion_execution.py
src/er_commons/document_parsing/content_parsing/conversion_identity.py
src/er_commons/document_parsing/content_parsing/conversion_preflight.py
src/er_commons/document_parsing/content_parsing/conversion_seal.py
src/er_commons/document_parsing/content_parsing/evidence.py
src/er_commons/document_parsing/content_parsing/pdfium_backend.py
src/er_commons/document_parsing/content_parsing/records.py
src/er_commons/document_parsing/content_parsing/publication.py
src/er_commons/document_parsing/content_parsing/routing_geometry.py
src/er_commons/document_parsing/content_parsing/runtime.py
src/er_commons/document_parsing/content_parsing/services.py
src/er_commons/document_parsing/content_parsing/sources.py
src/er_commons/document_parsing/heading_evidence_parsing/alignment_projection.py
src/er_commons/document_parsing/heading_evidence_parsing/errors.py
src/er_commons/document_parsing/heading_evidence_parsing/heading_overlay.py
src/er_commons/document_parsing/heading_evidence_parsing/text_evidence.py
src/er_commons/document_parsing/heading_evidence_parsing/types.py
```

## Producer current writer

```text
src/er_commons/document_parsing/content_parsing/application.py
src/er_commons/document_parsing/content_parsing/chunked_application.py
src/er_commons/document_parsing/content_parsing/config.py
src/er_commons/document_parsing/content_parsing/derived_publication.py
src/er_commons/document_parsing/content_parsing/derived_publication_support.py
src/er_commons/document_parsing/content_parsing/derived_route_reuse.py
src/er_commons/document_parsing/content_parsing/derived_table_reuse.py
src/er_commons/document_parsing/content_parsing/evidence.py
src/er_commons/document_parsing/content_parsing/identity.py
src/er_commons/document_parsing/content_parsing/ordering_projection.py
src/er_commons/document_parsing/content_parsing/ordering_projection_records.py
src/er_commons/document_parsing/content_parsing/page_projection.py
src/er_commons/document_parsing/content_parsing/preparation.py
src/er_commons/document_parsing/content_parsing/publication.py
src/er_commons/document_parsing/content_parsing/range_projection_reuse.py
src/er_commons/document_parsing/content_parsing/records.py
src/er_commons/document_parsing/content_parsing/routing.py
src/er_commons/document_parsing/content_parsing/routing_execution.py
src/er_commons/document_parsing/content_parsing/routing_geometry.py
src/er_commons/document_parsing/content_parsing/services.py
src/er_commons/document_parsing/content_parsing/sources.py
src/er_commons/document_parsing/content_parsing/table_markers.py
src/er_commons/document_parsing/content_parsing/table_processing.py
src/er_commons/document_parsing/content_parsing/table_request.py
src/er_commons/document_parsing/content_parsing/table_stage_reference.py
src/er_commons/document_parsing/table_reconstruction/__init__.py
src/er_commons/document_parsing/table_reconstruction/boundaries.py
src/er_commons/document_parsing/table_reconstruction/continuations.py
src/er_commons/document_parsing/table_reconstruction/families.py
src/er_commons/document_parsing/table_reconstruction/fragments.py
src/er_commons/document_parsing/table_reconstruction/learned_fallback.py
src/er_commons/document_parsing/table_reconstruction/learned_table_acceptance.py
src/er_commons/document_parsing/table_reconstruction/learned_table_cells.py
src/er_commons/document_parsing/table_reconstruction/learned_table_geometry.py
src/er_commons/document_parsing/table_reconstruction/learned_table_page.py
src/er_commons/document_parsing/table_reconstruction/learned_table_text.py
src/er_commons/document_parsing/table_reconstruction/learned_table_types.py
src/er_commons/document_parsing/table_reconstruction/models.py
src/er_commons/document_parsing/table_reconstruction/native_text.py
src/er_commons/document_parsing/table_reconstruction/otsl.py
src/er_commons/document_parsing/table_reconstruction/page.py
src/er_commons/document_parsing/table_reconstruction/page_content.py
src/er_commons/document_parsing/table_reconstruction/page_geometry.py
src/er_commons/document_parsing/table_reconstruction/page_parsers.py
src/er_commons/document_parsing/table_reconstruction/page_persistence.py
src/er_commons/document_parsing/table_reconstruction/page_routing.py
src/er_commons/document_parsing/table_reconstruction/page_types.py
src/er_commons/document_parsing/table_reconstruction/pipeline.py
src/er_commons/document_parsing/table_reconstruction/region_stream_fallback.py
src/er_commons/document_parsing/table_reconstruction/region_stream_geometry.py
src/er_commons/document_parsing/table_reconstruction/region_stream_parser.py
src/er_commons/document_parsing/table_reconstruction/region_stream_text.py
src/er_commons/document_parsing/table_reconstruction/region_stream_types.py
src/er_commons/document_parsing/table_reconstruction/tableformer_fallback.py
src/er_commons/source_release/models.py
src/er_commons/artifact_io.py
src/er_commons/artifact_verification.py
```

Independent review added the actual shared conversion publication record writers,
chunk worker contracts/diagnostics, and aggregate range-store reader dependency.

Shared invocation budget implementation now resides in `artifact_verification.py`;
current conversion/producer/chunk inventories explicitly include this execution
validation dependency. Collection membership validation is extracted into
`collection_processing/source_membership.py` to retain the existing human-size gates.
