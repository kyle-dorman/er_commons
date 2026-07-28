# Task 03A.11: Test Complex-Page Segmentation on Three More Pages

Status: **completed 2026-07-28; accepted through Task 03A.12**.

## Abstract

Hold the Task 03A.10 page-segmentation implementation and thresholds fixed and
run it on physical Appendix G3 pages 19, 273, and 592. These are the starts of
the other native worksheet-footer runs found by Task 03A.9. Preserve detection,
fusion, parsing, timing, and visual-review artifacts for each page.

## Goal

Test whether the page-527 method repeats on additional likely multi-table pages
without changing thresholds from page-specific inspection.

## Fixed method

1. Use the exact Task 03A.10 implementation and default parameters.
2. Process physical pages 19, 273, and 592 independently.
3. Do not tune thresholds between pages.
4. Record automatic Camelot Lattice, Network, and Hybrid counts; ruling-region
   counts; retained Network regions; final logical-table counts; parse
   failures; and timings.
5. Preserve an annotated fused render and separate CSVs for every successfully
   parsed region.
6. Stop for user review before changing the detector or processing more pages.

## Outputs

External artifacts:

```text
pipelines/brisbane_baylands/task_03a11_complex_pages_v1/
  page_00019/
  page_00273/
  page_00592/
  comparison.json
```

## Validation

- Verify the sealed PDF checksum on every invocation.
- Require the same parameter block on all three pages.
- Require every ruling region to have a successful parse or an explicit
  failure record.
- Record unmatched parser returns rather than assigning by list position.
- Run targeted formatting, lint, and `git diff --check`.

## Non-goals

- threshold tuning
- pages other than 19, 273, and 592
- accepting a production routing policy
- TableFormer, OCR, VLM, LLM, or skill-based PDF analysis
- canonical row repair

## Outcome

The fixed implementation completed all three pages without threshold changes:

| Page | Lattice | Network | Hybrid | Ruled regions | Retained Network | Logical tables | Seconds |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 19 | 4 | 2 | 4 | 4 | 0 | 4 | 3.49 |
| 273 | 4 | 2 | 4 | 4 | 0 | 4 | 3.55 |
| 592 | 28 | 4 | 29 | 34 | 1 | 35 | 15.34 |

Every one of the 42 ruling-derived regions matched a Lattice return and
produced a non-empty CSV. The coverage rule rejected all Network regions on
pages 19 and 273 because ruled rectangles already explained them. On page 592
it rejected three overlapping Network regions and retained one lower
borderless table, reproducing the same 34-plus-1 structure seen on page 527.
The cross-run comparison confirms identical parameter blocks across all three
pages.

External evidence is preserved below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a11_complex_pages_v1/
```
