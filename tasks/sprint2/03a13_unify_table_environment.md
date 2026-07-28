# Task 03A.13: Unify the Table-Parsing Environment

Status: **completed 2026-07-28; draft awaiting user code review**.

## Abstract

Move the clean Task 03A.12 table parser into the main `er-commons` environment
so Docling and Camelot share one headless OpenCV installation. Use uv's scoped
dependency exclusion to remove RapidOCR's request for the GUI OpenCV wheel,
retain `opencv-python-headless`, and eliminate the isolated-worker subprocess.

Rerun exactly the Task 03A.12 ten-page sample and compare its logical outputs.
Stop for user code review before any first-600-page run.

## Goal

Make the table stage easier to understand, test, profile, and edit by using one
locked Python environment and direct function calls:

```text
before
main orchestrator -> JSON request -> isolated uv subprocess -> page result

after
main orchestrator -> extract_page(...) -> page result
```

The parser separation remains conceptual, not environmental:

```text
ruling detection -> Lattice
simple page      -> Stream
unexplained box -> Network
```

## Inputs

- completed Task 03A.12 code and ten-page artifacts
- the disposable single-environment compatibility probe
- OpenCV packaging guidance: install exactly one `cv2` distribution
- Docling guidance preferring headless OpenCV
- uv scoped dependency-exclusion support
- `configs/brisbane_baylands_2025_deir_task03a13_unified_table_pipeline_v1.json`

## Fixed implementation

1. Add exact `camelot-py==2.0.0` and
   `opencv-python-headless==5.0.0.93` dependencies to the main project.
2. Exclude only `opencv-python` from `rapidocr==3.9.2` through a scoped uv
   exclusion. Do not install two OpenCV distributions.
3. Resolve and sync one main lock. Verify installed distribution metadata and
   `cv2`, Camelot, Docling, and RapidOCR imports.
4. Move the one-page worker implementation under
   `src/er_commons/table_extraction/`.
5. Replace JSON-request subprocess execution with direct typed function calls.
6. Retain independent per-page output directories and result reuse so page
   extraction remains restartable.
7. Run one page at a time. PDFium-backed native operations are not safe under
   the previous in-process thread concurrency; a probe mixed page 243 footer
   text into page 19 and changed its rendered ruling regions.
8. Run only physical pages
   `19, 20, 273, 274, 527, 528, 540, 541, 592, 593`.
9. Compare Task 03A.13 with Task 03A.12 using stable logical fields:
   table IDs, routes, parser choices, shapes, page-space boxes, cleaned CSV
   hashes, footer owners, and family membership.

## Outputs

Tracked:

```text
src/er_commons/table_extraction/page.py
src/er_commons/table_extraction/pipeline.py
src/er_commons/table_extraction/models.py
configs/brisbane_baylands_2025_deir_task03a13_unified_table_pipeline_v1.json
tests/test_table_extraction_*.py
pyproject.toml
uv.lock
```

External:

```text
pipelines/brisbane_baylands/task_03a13_unified_table_pipeline_v1/
  manifest.json
  summary.json
  comparison_to_task03a12.json
  pages/
```

## Validation

- Exactly one installed OpenCV wheel provides `cv2`, and it is headless.
- Camelot, Docling, RapidOCR, and `cv2` import from the main environment.
- One bounded Docling native-PDF conversion succeeds with OCR disabled.
- Full project `make check` passes.
- The ten-page run succeeds without spawning an isolated Python environment.
- Every Task 03A.12 logical table has exactly one Task 03A.13 counterpart.
- Report every semantic mismatch; do not silently loosen the comparison.
- `git diff --check` passes.

## Acceptance criteria

- No table-extraction subprocess or secondary uv project remains in the clean
  Task 03A.13 execution path.
- Only one OpenCV distribution is installed.
- The comparison is exact or any differences are small, explicit, and
  understood.
- The ten-page result remains a draft awaiting user review.
- Pages 1-600 do not run.

## Non-goals

- deleting the historical Task 03A.1 isolated environment or artifacts
- running pages 1-600
- enabling or validating OCR quality
- wrapped-row repair
- changing table thresholds, routes, or family policy
- completing the broader Task 03A review

## Outcome

The main uv lock now contains Camelot 2.0.0, Docling 2.115.0, RapidOCR 3.9.2,
and `opencv-python-headless` 5.0.0.93. The scoped uv exclusion removes
RapidOCR's GUI `opencv-python` dependency. Installed distribution metadata
confirmed that the GUI wheel is absent, and imports of Camelot, Docling,
RapidOCR, and `cv2` all succeeded in the main environment. A native-PDF
Docling conversion also succeeded with OCR disabled.

The isolated request, worker script, subprocess call, and secondary lock are
absent from the Task 03A.13 path. `pipeline.py` calls the package-level
`extract_page(...)` function directly, while completed per-page `result.json`
files remain reusable restart boundaries.

An initial two-thread probe was rejected. It corrupted native PDF state:
physical page 19 received page 243's footer and its detected ruling regions
changed from four to one. The failed probe remains preserved externally as
`task_03a13_failed_parallel_probe_20260728`. The accepted configuration
therefore requires one worker and processes pages sequentially.

The corrected ten-page run completed in 50.30 seconds:

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

The exact comparison found zero missing keys, zero extra keys, and zero stable
field mismatches across all ten page records, 89 logical tables, and 89 family
assignments. No pages outside the fixed sample ran.
