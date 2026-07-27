# Task 03C: Build Single-Document Conversion

Status: **provisional**. Revise this contract from the accepted Task 03B outcome
before activating it.

## Abstract

Implement the smallest production conversion boundary: verify one
manifest-selected PDF, run the pinned Docling pipeline, and publish its raw
structured output, page renders, extracted visual assets, configuration,
timings, and conversion record atomically under the external artifact root.
This task owns the parser adapter, not canonical record materialization or
corpus orchestration.

## Goal

Prove that one source document can be converted locally, reproducibly, and
restartably without hidden defaults, remote services, OCR, or in-memory-only
artifacts.

## Inputs

- completed Task 03A parser and configuration decision
- completed Task 03B canonical extraction and artifact contract
- one `model_corpus` source record selected from the sealed
  `source_manifest.json`
- the verified Task 02 completion seal and records it covers
- the corresponding checksum-pinned PDF
- current Docling
  [DocumentConverter](https://docling-project.github.io/docling/reference/document_converter/),
  [pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/),
  and [page/picture export example](https://docling-project.github.io/docling/_generated/examples/export_figures/)

## Outputs

- the pinned production Docling dependency and lockfile update
- narrow typed configuration and parser-adapter code
- one package-backed CLI or Make entrypoint for single-document conversion
- raw lossless Docling JSON for one document
- externally referenced page renders and extracted figure/table/picture assets
  required by the accepted contract
- a per-document conversion record containing input checksum, exact
  configuration, package/model/backend/device identities, status, errors,
  timings, counts, paths, and output checksums
- fast tests using tiny fixtures or fakes for project-owned behavior

## Research / learning checkpoint

Trace Docling's actual execution stages for the selected PDF backend: native
text parsing, page rasterization, layout inference, reading-order assembly,
table-structure recognition, and document serialization. Identify which stages
are deterministic CPU parsing and which depend on learned models or accelerator
kernels.

The outcome must explain:

- **Parser versus model boundary:** the PDF backend recovers native cells and
  geometry; learned components classify and organize regions. A successful file
  open does not imply a successful semantic conversion.
- **Model provenance:** a Python package version does not uniquely identify the
  layout and table weights. Record resolved model artifacts or revisions, not
  only a mutable model name.
- **Partial success is a first-class state:** a converter may return a document
  with page-level or stage-level errors. The wrapper must not equate a
  serializable result with complete success.
- **Rendering is part of observability:** page images and element crops are
  verification artifacts tied to coordinates, not decorative exports.
- **Binary asset strategy affects scale:** referenced images avoid base64
  duplication and corpus-sized JSON, but require atomic path publication and
  referential-integrity checks.
- **Hardware changes are part of reproducibility:** CPU, MPS, CUDA, thread
  counts, batch sizes, and numerical kernels can affect performance and
  occasionally model output. Record them even when semantic IDs remain stable.
- **Library wrappers should expose policy:** the project owns input roles,
  checksums, disabled features, artifact naming, completion semantics, and
  failure behavior; Docling owns conversion internals.

## Plan / spec requirement

Write a brief implementation plan before adding the runtime dependency. It must
freeze:

1. API versus CLI integration and why;
2. the exact explicit parser options and model/backend identities;
3. how OCR, VLM, remote services, external plugins, and generative enrichments
   are mechanically disabled;
4. memory-conscious image export and serialization behavior;
5. temporary-directory, atomic-publication, and no-clobber semantics;
6. timeout and partial-success behavior;
7. conversion-record schema and completion marker;
8. logging and profiling fields; and
9. unit-test seams that avoid downloading models during routine `make check`.

The wrapper must accept a source ID resolved through the frozen manifest, not an
arbitrary untracked path masquerading as benchmark input.

## Review pass

- **Boundary discipline:** project code remains thin and does not reimplement
  layout, table, image, or PDF parsing.
- **Failure safety:** interrupted conversion cannot publish a completed-looking
  document; mismatched sources or existing outputs cannot be overwritten.
- **Configuration closure:** every behavior-affecting option is recorded, and
  unsupported hidden defaults are surfaced.
- **Artifact observability:** raw output, renders, assets, errors, and timings
  are independently inspectable.
- **Routine development:** fast tests do not require network access, model
  downloads, or a full PDF conversion.

## Validation

- Reject a source not present in the manifest and a checksum-mismatched input.
- Verify the Task 02 completion record and sealed source-manifest checksum
  before resolving the input.
- Convert the selected real document or approved bounded page range.
- Verify OCR, VLM, remote services, and generative enrichments remain disabled.
- Verify every page render and extracted asset is contained below the expected
  external directory and linked from the raw output or conversion record.
- Reconcile the converted page count and page-render count with the source
  manifest.
- Interrupt or simulate failure and confirm no completion marker or conflicting
  final directory is published.
- Rerun against matching completed output and verify it is checked and reused
  or safely reported according to the Task 03B contract.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- One manifest-selected source is converted through a package-backed,
  typed, logged command.
- The command verifies source identity before conversion.
- The raw document and page-render inventory account for every expected source
  page or publish an explicit non-success state.
- Raw Docling JSON, page renders, selected visual assets, configuration,
  timings, errors, and output checksums are durable external artifacts.
- The per-document record distinguishes success, partial success, and failure.
- Publication is atomic and no-clobber.
- Routine tests remain small and offline.
- No canonical records or batch orchestration are implemented.
- The outcome includes an architecture walkthrough and requests user review
  before Task 03D.

## Non-goals

- canonical document, page, block, table, figure, or image records
- section hierarchy, printed page labels, or cross-reference resolution
- multi-document scheduling or the full corpus run
- human visual-usability decisions
- OCR or model/LLM-based content repair
- retrieval, chunking, generation, or evaluation
