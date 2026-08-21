# Task 03H.3: Defer Aggregate Reading Order Until Table Evidence

Status: **complete; parent Task 03H remains paused at the separate G2 range-RSS gate**.

## Abstract

Change the Task 03H chunked document path so dense per-range pages do not invoke
Docling reading-order interpretation before the project has had an opportunity to
route and extract tables. Each range must still capture lossless Docling/PDFium
evidence and Heron layout evidence. The existing project routing and custom table
extractor remain separate responsibilities and retain their current extraction
algorithms. After all range bundles are sealed, aggregate the verified evidence,
build a reduced ordering-only projection using confirmed table outcomes, and run
Docling reading order and heading hierarchy once over that projection. Publish the
ordered non-table content together with canonical custom tables, explicit failures,
and references to untouched raw evidence.

This is an implementation subtask of Task 03H. It must not start source-PDF or
model execution until the implementation and offline validation are complete and
the user separately authorizes a representative production test.

## Goal

Implement and test the accepted 11-step execution DAG documented in
`tasks/sprint2/03h_run_full_canonical_extraction.md` and `docs/architecture.md`,
with a restartable, source-free boundary at every range bundle.

## New-chat entrypoint

Start by rereading `AGENTS.md`, `docs/index.md`, `docs/todo.md`, this task, the
parent Task 03H contract, and `docs/architecture.md`. Inspect the current working
tree and current v2 code/config identities, but do not inspect or reuse historical
Task 03H artifacts. Confirm that the implementation and offline gates are green,
that no production worker is active, and that the user has approved the bounded
PDF/model qualification below. If approval is absent, remain source-free and report
the exact next approval needed.

Before selecting documents, write the selection and resource plan to a new attempt
manifest under the current v2 artifact namespace. The manifest must name the exact
source IDs, page ranges, code/identity versions, resource limits, timing fields,
and stop conditions. Never place source bytes or large semantic payloads in the
repository or this task file.

## Inputs

- Current chunked conversion runtime and range-evidence contracts.
- Existing source-native routing implementation.
- Existing Camelot/OpenCV and low-level TableFormer fallback pipeline.
- Existing aggregate Docling adapter and publication contracts.
- The accepted clean-run namespace and identity rules for
  `task_03h_clean_full_v2`.
- Official Docling documentation/source for pipeline stages, reading-order
  invocation, and profiling hooks:
  <https://docling-project.github.io/docling/reference/pipeline_options/> and
  <https://github.com/docling-project/docling/blob/main/docling/pipeline/standard_pdf_pipeline.py>.

## Required design decisions before implementation

Write a short implementation note in this task before editing code that answers:

1. Which existing range artifact carries raw Docling cells/elements, Heron layout
   evidence, and page-local images without invoking aggregate reading order?
2. How will the orchestration invoke existing routing and table extraction without
   changing their internals or falsely treating a route as an extraction success?
3. What exact success, partial, and failure records can authorize suppression in
   the reduced ordering projection?
4. What bounded fallback preserves unresolved text when extraction fails, while
   preventing another dense-page reading-order explosion?
5. How are page ownership, overlap deduplication, table continuation seams, and
   global table-family reconciliation preserved?
6. Which identities, manifests, and completion seals change, and which existing
   range seals remain reusable after an interruption?

The note must identify any ambiguity that requires user approval rather than
silently choosing a lossy behavior.

### Accepted source-free design decision

Use a purpose-built, slim page-evidence projection for routing and table
orchestration. Do not reconstruct a fake aggregate document payload before
table extraction. The projection will contain only page-local inputs required
by the existing routing/table boundary: physical page identity, source and
range provenance, page geometry, native-text measurements, Heron table-region
observations, and boundary-marker evidence. It will not contain aggregate
reading-order output, heading levels, or any other interpretation produced by
the global Docling pass. The existing routing and table algorithms remain
unchanged; the new orchestration adapts the projection into their existing
request contracts and records extraction outcomes separately from routing.

## Plan

1. Inventory the current adapter, range bundle, routing, table, aggregation, and
   publication contracts; add characterization tests before changing behavior.
2. Split range conversion from aggregate interpretation while retaining lossless
   raw evidence and Heron output.
3. Invoke the existing per-range routing and table extraction stages as separate
   orchestration steps; preserve explicit page-local success/failure artifacts.
4. Seal each range bundle completion-last and make downstream retries reuse sealed
   range outputs without constructing Docling or re-running extraction.
5. Aggregate only verified range evidence and construct a reduced ordering view.
   Suppression must be based on confirmed table artifacts, never routing alone;
   raw evidence remains immutable.
6. Run Docling reading order and heading hierarchy once on the aggregate ordering
   view, with the Docling TableFormer PDF stage disabled.
7. Merge ordered non-table content, existing global table reconciliation outputs,
   explicit failures/fallbacks, and raw-evidence references into the canonical
   document package.
8. Update identities, manifests, schemas, documentation, and restart/reuse logic
   only where the contract actually changes.

## Validation and testing plan

### Offline unit and contract tests

- Range conversion captures raw cells/elements and Heron layout evidence without
  calling aggregate reading order.
- Routing remains independent from extraction and emits the existing route types.
- Successful extraction suppresses only the corresponding confirmed table text in
  the ordering view.
- Route-only, partial, failed, and unmatched extraction cases retain unresolved
  text and explicit failure evidence.
- Raw range payloads are byte/content stable before and after projection.
- Range overlap ownership and deterministic page ordering remain unchanged.
- Completion-last seals reject incomplete, corrupted, or mismatched bundles.
- Restart after interruption reuses valid range bundles and does not rerun Docling,
  routing, or table extraction for reused ranges.
- Aggregate reading order and heading hierarchy are invoked exactly once.
- The Docling TableFormer PDF stage remains disabled in the aggregate group.
- Global table continuation/family reconciliation receives the same page-local
  artifacts and preserves existing outputs.
- Canonical publication records ordered non-table content, custom tables, explicit
  failures/fallbacks, and raw-evidence references.

### Offline integration and maintainability checks

- Run focused chunked-conversion, routing, table-reconstruction, aggregation, and
  publication tests, then the complete repository gate (`make check` or its
  documented equivalent).
- Add a small synthetic dense-page fixture that would make the old per-range
  reading-order path impractical; prove the new range path completes without it.
- Enable Docling pipeline timing instrumentation in a bounded test and persist
  stage timings in diagnostics without making timing part of semantic identity.
- Perform an independent recovery/ownership review: a future maintainer must be
  able to locate raw evidence, routing, table outcomes, projection policy, and the
  single aggregate interpretation call from public seams.
- Run deterministic Task 03H config/identity generation and `git diff --check`.

### Authorized representative execution, only after approval

This task has a deliberately bounded real-input qualification. It must not run the
35-document corpus; that work belongs to the parent Task 03H after this subtask is
accepted.

The two qualification documents are fixed in advance from the checked-in manifest:

- `deir_appendix_c` — 86 pages, the table-heavy qualification. Existing Task 03G
  evidence identifies several learned-fallback-positive pages in this appendix,
  making it the stronger dense/table routing case while remaining below 200 pages.
- `deir_appendix_o` — 54 pages, the non-table-heavy qualification. Existing Task
  03H preparation evidence identifies it as an ordinary mixed figure and
  wind-analysis control, making it the contrasting non-table case.

These classifications are manifest/evidence selections, not claims derived from
new PDF inspection in this task. If the current source manifest or page counts do
not match 86 and 54 at execution time, stop for review rather than silently
substituting another document.

The new-chat operator must first obtain explicit user approval for PDF/model work,
then run the following in order:

1. **Small-range timing wave.** Select several short, diverse page ranges from the
   available corpus, including at least one ordinary text range, one dense/table-like
   range, and one mixed range. Keep the ranges small enough to stop safely. Run the
   old and new orchestration paths when both are available, recording wall time,
   CPU time, peak RSS, swap growth, page count, element/cell counts, table route,
   extraction outcome, and Docling stage timings. Preserve the raw range bundle and
   timing report for every attempt.
2. **Two-document qualification.** Select exactly two documents under 200 pages:
   one demonstrably table-heavy and one demonstrably not table-heavy. Record the
   source IDs, page counts, selection evidence, and the reason each represents its
   class before execution. Process each document through the new path only, with
   one worker and the current approved resource guards. Do not add a third document
   without a new user decision.
3. **Per-document checks.** Verify range completion seals, raw-evidence checksums,
   Heron/layout evidence, route decisions, page-local table success/partial/failure
   records, reduced-projection provenance, exactly one aggregate reading-order and
   heading pass, disabled Docling TableFormer PDF stage, global table reconciliation,
   and canonical publication references.
4. **Restart check.** Reinvoke each completed document using the same identity and
   confirm that valid range and downstream seals are reused without new PDF/model,
   routing, table, or aggregate interpretation work.
5. **Comparison report.** Produce a compact source-free report comparing the old
   timing baseline (where available) with the new path, including dense-page speedup,
   peak resources, extraction coverage, unresolved-text/fallback counts, and any
   semantic differences. Keep the report diagnostic; it does not authorize corpus
   execution.

Stop and return to the user if either document exceeds its resource guard, produces
unexpected loss or ordering, cannot be classified confidently, or requires changing
the custom table extractor. No 35-document run, collection completion, historical
artifact reuse, or production claim is part of Task 03H.3.

## Acceptance criteria

- The maintained implementation follows all 11 DAG stages and the custom table
  extractor remains a separate, unchanged algorithmic component.
- No raw Docling evidence is deleted or rewritten by table suppression.
- Suppression is authorized by extraction evidence, with explicit failure and
  fallback behavior for every attempted table page.
- Aggregate reading order and heading hierarchy run once, after projection, and
  the Docling TableFormer PDF stage is disabled.
- Range bundles, identities, restart/reuse, overlap ownership, and global table
  reconciliation remain deterministic and restartable.
- Focused tests, full offline validation, deterministic generation, and an
  independent maintainability review pass.
- The authorized qualification includes a documented small-range timing wave and
  exactly two sub-200-page documents: one table-heavy and one non-table-heavy.
- The qualification report records timings, resource peaks, extraction outcomes,
  fallback/unresolved-text counts, and restart reuse, and explicitly leaves the
  35-document run to parent Task 03H.
- No source PDF/model execution occurs before separate user approval.

## Non-goals

- Rewriting Camelot, OpenCV, or the low-level TableFormer fallback algorithms.
- Enabling Docling's TableFormer PDF stage.
- Changing source-native routing policy or table-family semantics without a new
  reviewed task.
- Deleting historical artifacts or reusing earlier Task 03H roots.
- Running the 35-document corpus, claiming production completion, or closing Task
  03H.

## Review pass

The independent architecture, provenance/restartability, and human-maintainability
review is complete. The maintained path has named owners for range capture, page
projection, routing, table extraction, evidence classification, aggregate ordering,
and publication. The review removed the optional pre-aggregate callback and its
no-op path, made the callback part of the required runtime service contract, and
kept the accepted breaking API change explicit. The persisted page and ordering
contracts now reject unknown fields, invalid page identities, duplicate references,
missing suppression fields, non-absolute table-stage roots, identity drift, and
incomplete page/decision coverage. Range reuse also verifies projection source and
range provenance.

The pre-aggregate callback is split into readable helpers for core-page coverage,
table-stage loading, and evidence-to-decision joining. It loads the existing
validated table-stage representation and permits an empty table view only for the
explicit `not_applicable` outcome. Raw range evidence remains immutable; suppression
is still limited to confirmed extraction evidence in the ordering-only view.

The cleanup audit found no retained Task 03H.3 timing-wave runner or inspection-only
production module. The older `scripts/inspect_task03h_scaling.py` remains because it
is a referenced Task 03H.1 artifact, and the explicitly user-excluded
`scripts/classify_volume4.py` was not read or changed. No historical artifact was
deleted.

The final source-free/offline gates passed: 823 tests, Ruff format and lint with
`scripts/classify_volume4.py` excluded, strict mypy across 340 source files,
deterministic Task 03H generation/check, and `git diff --check`. The separately
authorized Appendix C/O qualification and downstream publication comparison remain
external diagnostic evidence under the approved Task 03H artifact namespace; they
did not authorize a corpus or collection run.

## Outcome

Implemented the accepted 11-stage restartable chunked path. Ranges now retain
lossless pre-global Docling evidence and slim page-local routing inputs; the real
pre-aggregate callback runs routing and the complete existing table stage; the
aggregate consumes a strict ordering projection and performs reading order and
heading interpretation once; and publication includes ordered non-table content,
canonical tables, explicit fallback decisions, and raw-evidence references. The
implementation passed the authorized two-document qualification, its restart and
downstream checks, the independent maintainability/recovery review, and the complete
offline gate. Parent Task 03H remains open and paused independently at its G2
range-RSS stop condition.
