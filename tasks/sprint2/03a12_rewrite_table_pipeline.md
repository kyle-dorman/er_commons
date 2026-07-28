# Task 03A.12: Rewrite the Table-Parsing Pipeline

Status: **completed 2026-07-28; draft awaiting user code review**.

## Abstract

Replace the exploratory Task 03A.1 through 03A.11 table scripts with a clean,
readable draft of the table-parsing stage. Preserve the accepted lessons:
cheap deterministic page inspection, a fast whole-page route, explicit
segmentation for multi-table pages, separate ruled and borderless parsers,
footer cleanup, and contiguous family evidence. Do not delete or modify the
exploratory implementation; the rewrite must be independently reviewable.

Stop after a small mixed-page run. The first-600-page comparison is a later
user-approved step.

## Goal

Produce table-extraction code that a human can understand, edit, and rerun
without reconstructing the sequence of experiments that produced it.

## Pipeline boundary

```text
sealed PDF pages
       |
       v
deterministic ruling scan
       |
       +-- zero/one ruled region --> Camelot Stream whole-page parse
       |
       `-- multiple ruled regions --> Lattice per ruled region
                                      + Network for unexplained borderless area
       |
       v
clean per-table CSV + page-space geometry + parser provenance
       |
       v
footer-owned runs first, exact native-header continuity second
       |
       v
reviewable table and family manifests
```

## Inputs

- sealed Appendix G3 PDF and source manifest
- exact isolated `camelot-py==2.0.0` environment from Task 03A.1
- Task 03A.4 through 03A.11 code and artifacts as learning evidence only
- `configs/brisbane_baylands_2025_deir_task03a12_table_pipeline_v1.json`

## Fixed draft

1. Keep Camelot isolated from the main Docling environment.
2. Render each requested page deterministically at the recorded scale.
3. Detect ruled regions using fixed OpenCV horizontal/vertical morphology.
4. Route pages with more than one qualifying ruled component to the complex
   path. This is a provisional rule, exposed in configuration.
5. On the simple path, retain one deduplicated Camelot Stream whole-page table.
6. On the complex path:
   - parse each ruled component through an explicit Lattice area;
   - run Network once on the page;
   - reject Network regions substantially covered by ruled rectangles; and
   - retain unexplained Network regions as borderless tables.
7. Sort final tables in visual reading order and assign stable page-local IDs.
8. Preserve raw CSVs. Produce cleaned CSVs by removing footer-counter rows,
   leading workbook filename rows, and columns empty after those removals.
9. Parse worksheet footers from native text. The geometrically lowest logical
   table owns the footer, not the last parser hypothesis.
10. Group footer owners by identical worksheet ID and consecutive internal
    counters. Group remaining adjacent-page tables only when their exact
    cleaned header matrices and effective column counts match.
11. Preserve configuration, requests, logs, per-page records, table records,
    family assignments, timings, checksums, and an artifact inventory.

## Small test

Run only physical pages:

```text
19, 20, 273, 274, 527, 528, 540, 541, 592, 593
```

This sample contains two moderate multi-table run starts, two extreme
multi-table run starts, ordinary continuations, and the known page-540/541
footer-column case. It is not an accuracy sample.

## Outputs

Tracked draft:

```text
src/er_commons/table_extraction/
scripts/workers/table_extraction_worker.py
configs/brisbane_baylands_2025_deir_task03a12_table_pipeline_v1.json
tests/test_table_extraction_*.py
```

External sample:

```text
pipelines/brisbane_baylands/task_03a12_clean_table_pipeline_v1/
  manifest.json
  configuration.json
  pages/
  tables.jsonl
  family_assignments.jsonl
  table_families.json
  summary.json
  artifact_inventory.json
```

## Research / learning checkpoint

Reuse the already pinned Camelot 2.0 parser boundary and its documented
separation between region detection, grid reconstruction, and text assignment.
Keep OpenCV morphology as deterministic region proposal logic, not semantic
table understanding. Explain in code that Stream, Lattice, and Network provide
different evidence and that parser hypotheses are not logical table IDs.

## Validation

- Unit-test footer parsing, CSV cleanup, bounding-box overlap, visual ordering,
  Network retention, and family assignment with synthetic records.
- Require the source checksum and page count.
- Require the configured sample exactly.
- Require every ruled region to receive either a matched Lattice output or an
  explicit failure record.
- Require unique logical table IDs and exactly one assignment per table.
- Require all outputs to use relative artifact paths.
- Run targeted Ruff, mypy where practical, pytest, and `git diff --check`.
- Inspect the ten-page summary and at least the page-527 and page-592 annotated
  renders.

## Acceptance criteria

- The new code does not import the exploratory Task 03A table modules.
- Main orchestration and isolated parser responsibilities are explicit.
- Configuration owns thresholds and page selection.
- The small run succeeds and its limitations are stated.
- No 600-page run occurs.
- The task stops with the draft awaiting user code review.

## Non-goals

- deleting exploratory code or artifacts
- running pages 1-600
- asserting exact parity with Task 03A.4 or Task 03A.9
- wrapped-row repair
- TableFormer, Docling, OCR, VLM, or LLM table repair
- production acceptance or Task 03B activation

## Outcome

The clean draft is implemented without importing the exploratory Task 03A
table modules. Its tracked responsibilities are split into configuration
models, an isolated one-page Camelot/OpenCV worker, cross-page family logic,
and a restartable manifest-producing orchestrator. Module comments and this
task preserve the detector/parser/family boundaries.

The fixed ten-page sample completed in 30.42 seconds with two page workers:

| Measure | Result |
| --- | ---: |
| Physical pages | 10 |
| Simple Stream pages | 4 |
| Complex segmented pages | 6 |
| Logical tables | 89 |
| Stream tables | 4 |
| Lattice tables | 83 |
| Retained borderless Network tables | 2 |
| Proposed families | 84 |

Pages 527 and 592 each reproduced the reviewed 34 ruled plus one borderless
structure. All ruled regions matched a Lattice return. Footer ownership is now
geometric: table 35 on each run-start page joins the single table on its next
page. The sample also formed the expected page 19/20, 273/274, 540/541, and
592/593 footer pairs. Page 541 cleaned from 238 by 38 to 236 by 37 by removing
its footer row and then its footer-only column; page 540 remained 236 by 37.

Validation passed:

```text
make check
72 passed
Ruff clean
mypy clean across src
git diff --check clean
```

The external review artifact is:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a12_clean_table_pipeline_v1/
```

This remains a draft. It has not processed pages 1-600, established parity
with the exploratory outputs, repaired wrapped rows, or completed the broader
Task 03A review.
