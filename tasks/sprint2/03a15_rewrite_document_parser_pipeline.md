# Task 03A.15: Rewrite the Document-Parser Pilot Pipeline

Status: **completed 2026-07-28; accepted as the Task 03A parser implementation**.

## Abstract

Replace the Task 03A proof-of-concept document-pilot module with a clean,
maintainable package and one explicit CLI command. Keep Docling responsible
for native text, layout, figures, reading order, and provenance, but disable
TableFormer globally. Route every selected page by content to the clean table
pipeline, which owns all table reconstruction. Run the rewrite into a new
external artifact root, measure it, and compare its non-table invariants and
reviewed table outputs with accepted Task 03A evidence.

The old run remains immutable comparison evidence. If any normalized semantic
JSON differs, stop after writing the comparison report and return the exact
differences for user review.

## Goal

Turn the successful parser experiment into code that a human can understand,
test, and extend without carrying forward the 1,246-line pilot monolith.
Use behavioral equivalence, not visual similarity or aggregate counts, as the
rewrite gate.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/documentation.md`
- `tasks/sprint2/03a_validate_document_parser.md`
- `tasks/sprint2/03a14_run_first_600_table_pipeline.md`
- `configs/brisbane_baylands_2025_deir_task03a_pilot_v1.json`
- the current `src/er_commons/document_pilot.py` proof of concept
- the accepted external run:

```text
pipelines/brisbane_baylands/task_03a_docling_native_pilot_v1/
```

## Outputs

Tracked:

```text
src/er_commons/document_extraction/
configs/brisbane_baylands_2025_deir_task03a15_document_pipeline_v4.json
tests/test_document_extraction_*.py
tasks/sprint2/03a15_rewrite_document_parser_pipeline.md
```

The proof-of-concept `src/er_commons/document_pilot.py` and its monolithic test
file are removed only after the live six-range JSON-equivalence gate passes.

External:

```text
pipelines/brisbane_baylands/task_03a15_clean_document_pipeline_v4/
  configuration.json
  environment.json
  logs/
  ranges/
  timings.jsonl
  comparison_to_task03a.json
  summary.json
  manifest.json
  artifact_inventory.json
```

## Research / learning checkpoint

The rewrite should apply a plain functional-core/orchestration-shell boundary:
typed configuration and comparison rules stay deterministic; Docling
construction and conversion sit behind narrow functions; filesystem and
metrics code are explicit at the edge; the top-level runner reads as a short
sequence of pipeline stages.

Module boundaries must follow real responsibilities, not create a framework.
Prefer small Pydantic records, plain JSON/JSONL artifacts, and direct function
calls. Avoid dependency injection containers, registries, hidden globals, and
backwards-compatibility aliases without callers.

The task outcome must explain why a rewrite is accepted only when semantic
outputs match. Refactoring confidence comes from comparing preserved behavior
at the artifact boundary, while runtime may legitimately vary because model
initialization, operating-system caches, and system load vary.

## Fixed rewrite contract

1. Use the accepted `docling==2.115.0` environment and
   `PyPdfiumDocumentBackend`.
2. Keep Heron layout, CPU with four threads, native text, page images, picture
   images, and parsed pages. Disable TableFormer on every page.
3. Keep OCR, remote services, external plugins, VLM conversion, picture
   description/classification, chart extraction, code/formula enrichment, and
   project-owned generative repair off, with fail-closed assertions.
4. Reuse and verify the immutable model inventory under the original Task 03A
   artifact root; do not redownload models.
5. Reconcile every selected source and checksum against the sealed release.
6. Process the same six contiguous ranges and ten physical pages:
   main 44-46, 1500, and 2000; Appendix A 20; Appendix B 107-109; and Appendix
   G3 1000.
7. Run sequentially. Do not introduce worker concurrency during this rewrite.
8. Write to the new Task 03A.15 artifact root without modifying the accepted
   Task 03A evidence.
9. Expose one package-backed CLI command and one Make target for the fixed run.
10. Keep the orchestration call graph visible from one top-level function.
11. Apply one source-agnostic table router to every page. If either reviewed
    PDFium rule passes, use whole-page Camelot Stream. Otherwise, if Heron
    labels table regions, use Camelot Lattice only in those regions. Otherwise
    do not invoke Camelot.
12. Treat expected pilot routes as assertions, never decision logic:
    main-report page 1500 must reach bounded Lattice through Heron, and
    Appendix G3 page 1000 must reach Stream through its native-text features.

## Equivalence gate

For each of the six ranges, compare:

- `document.json` after replacing generated page/picture image data URIs and
  each table's `data`, which is intentionally no longer produced by
  TableFormer; retain table labels, counts, references, and provenance;
- `conversion_pages.json` after replacing only
  `predictions.tablestructure`; retain parsed-page data, Heron layout,
  assembly, reading order, page geometry, and confidence;
- the stable fields of `conversion_record.json`: source identity and checksum,
  physical page range, conversion status, errors, captured warnings, inherited
  source warnings, pipeline class, and backend class.

Require the same range set and emit per-file old/new SHA-256 values plus a
bounded structural diff for every mismatch. Require exact equality for ranges
without routed tables. Preserve differences on routed table pages as
informational because TableFormer ownership was intentionally removed.

Require exactly two table routes in the pilot. Invoke the complete clean table
pipeline for each routed source, including source validation, page parsing,
raw and cleaned CSVs, cleanup evidence, native footer parsing, geometric footer
ownership, family assignment, summaries, manifests, and inventories. Do not
call the page extractor directly from the document pipeline.

If any compared JSON differs:

1. write `comparison_to_task03a.json` and `summary.json`;
2. mark the run `semantic_mismatch`;
3. do not remove the proof-of-concept implementation;
4. do not update Task 03A or the queue as accepted; and
5. stop for user review.

## Timing comparison

Record wall time, CPU time, peak RSS, status, error count, and output bytes for
each range. Compare range and total wall times with the accepted run, but do
not require timing equality. Report absolute and percentage differences and
identify the Appendix G3 stress page separately because it dominates the
pilot.

## Validation

- Unit-test configuration scope, contiguous range construction, source
  reconciliation, forbidden-option assertions, JSON normalization, structural
  diff limits, timing comparison, and mismatch stop behavior.
- Confirm the clean package does not import the proof-of-concept module.
- Unit-test the strict, numeric, layout-fallback, and no-table route boundaries.
- Confirm the CLI uses the tracked fixed configuration.
- Run the ten-page pipeline once into the new artifact root.
- Require exact normalized non-table invariants across all six ranges.
- Require exact pilot route decisions and complete table-pipeline manifests,
  cleanup evidence, footer ownership, and family assignments.
- Run:

```bash
make fix
make check
git diff --check
```

## Review pass

- **Readability:** can a reviewer follow configuration, source resolution,
  converter construction, one range conversion, comparison, and sealing
  without jumping through unrelated code?
- **Behavior preservation:** does the artifact comparison cover the semantic
  parser boundary rather than only counts or Markdown?
- **Failure safety:** does any mismatch stop acceptance while retaining both
  runs and the diff?
- **Provenance:** can the new manifest identify the sealed sources, exact
  configuration, model inventory, old baseline, code state, and every output?
- **Scope:** did the rewrite avoid introducing canonical schemas, retrieval
  chunks, OCR, generative repair, or full-corpus conversion?

## Acceptance criteria

- The monolithic proof-of-concept is replaced by a readable package with
  cohesive modules and focused tests.
- One explicit CLI/Make path reproduces the fixed ten-page run.
- All four ranges without routed tables match the accepted run exactly.
- Routing is source-agnostic and produces only main page 1500 bounded Lattice
  and G3 page 1000 whole-page Stream in the fixed pilot.
- Both routed pages complete the full clean table pipeline. Differences from
  the earlier TableFormer-bearing document JSON and Task 03A.1 exploratory
  raw serialization are recorded but are not acceptance gates.
- Timing and resource results are preserved in a detailed summary.
- The accepted Task 03A run is unmodified.
- Remaining parser limitations are documented as known model/data limitations,
  not hidden by the rewrite.
- The outcome states whether Task 03A can close and the precise remaining
  boundary before Task 03B.

## Non-goals

- changing the reviewed router thresholds, backend, or page selection
- source- or page-specific routing branches
- using Heron or TableFormer cell reconstruction
- rerunning pages 1-600 or pages 601-6104
- defining canonical extraction schemas or IDs
- retrieval chunking, OCR, VLM, LLM repair, or human usability adjudication

## Outcome

Completed and accepted on 2026-07-28. The proof-of-concept document module was
replaced by the cohesive `document_extraction` package and one package-backed
CLI/Make path. The final v4 run converted all ten selected pages successfully
with zero errors. All four ranges without routed tables matched the accepted
Task 03A JSON exactly. Differences on the two routed table pages are preserved
as informational because TableFormer was intentionally disabled and the clean
table pipeline now owns those structures.

The content-based router produced exactly two table routes without source- or
page-specific decision branches. Main-report page 1500 used Heron's detected
region as evidence for bounded Camelot Lattice. Appendix G3 page 1000 passed
both reviewed PDFium numeric signals and used whole-page Camelot Stream. The
remaining eight pages did not invoke Camelot.

Both routed pages entered through the complete `run_table_extraction`
orchestration. Each source-scoped run verified the sealed source, extracted
the page, wrote raw and cleaned CSVs, recorded cleanup evidence, parsed native
footer metadata, assigned footer ownership, assigned every table to a family,
and sealed a summary, inventory, and manifest. G3 page 1000 reproduced the
established cleanup behavior: the 184-by-35 parser result became a 183-by-34
clean table after removing its footer row and footer-only column. Its parsed
`2.5 25 of 85` footer belongs to the table and its assignment is recorded in
`appendix_g3_table_family_0001`.

Measured Docling range time was 9.30 seconds versus 112.03 seconds for the
TableFormer-bearing baseline, a reduction of 102.73 seconds or 91.70 percent.
The two complete table-pipeline runs added 1.02 seconds for main page 1500 and
4.80 seconds for G3 page 1000. End-to-end pipeline wall time, including model
startup, routing, table stages, comparisons, and sealing, was 35.60 seconds.
Peak RSS was 1,928,282,112 bytes. The final artifact contains 91 inventoried
files totaling 182,528,656 bytes.

The stopped v1 and v2 external runs remain immutable diagnostic evidence. The
old monolithic module and test were removed only after the v3 gate passed. A
post-acceptance maintainability pass separated routing-to-table integration,
acceptance policy, and reporting into cohesive modules; introduced validated
threshold and table-request models; and reran the same pilot as v4.
Task 03A can close. Task 03B remains inactive until its provisional contract
is revised around the accepted ownership boundary: Docling supplies native
text/layout/provenance, the reviewed router selects table work, and the clean
table pipeline owns table reconstruction, cleanup, footers, and families.
