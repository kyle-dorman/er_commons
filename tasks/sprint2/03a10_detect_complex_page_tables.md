# Task 03A.10: Detect and Segment Tables on One Complex Page

Status: **completed 2026-07-28; accepted for a fixed-parameter three-page
follow-up**.

## Abstract

Use physical PDF page 527 of Appendix G3 as one bounded stress case for
automatic multi-table detection and segmentation. Run reproducible code over
native PDF content and/or a deterministic page render, preserve every detected
region and diagnostic, and compare the machine result with the visible page.
Do not use manual section labels as detector inputs and do not run TableFormer.

## Goal

Determine whether inexpensive tooling can first flag page 527 as structurally
complex and then recover distinct table regions suitable for independent
parsing.

## Inputs

- sealed Appendix G3 PDF
- preserved Task 03A.4 Camelot Stream result for physical page 527
- exact isolated Camelot environment and lock from Task 03A.1

## Fixed experiment

1. Verify the source PDF checksum and physical page count.
2. Run Camelot's automatic table-region methods on page 527 without supplied
   table coordinates.
3. Deterministically render page 527 and detect horizontal and vertical ruling
   lines with OpenCV morphology.
4. Derive candidate table regions from the resulting line geometry. Section
   names or manually selected row numbers may be used only after detection for
   evaluation, never as segmentation inputs.
5. Save an annotated render, one crop per proposed region, parser outputs, and
   a JSON manifest containing parameters, coordinates, counts, and timings.
6. Stop after this one-page result for user review. Do not generalize the
   thresholds or process another page.

## Outputs

External evidence belongs below:

```text
pipelines/brisbane_baylands/task_03a10_page527_segmentation_v2/
  manifest.json
  parser_probe/
  ruling_probe/
    page.png
    ruling_mask.png
    annotated.png
    regions.json
    crops/
  fusion_probe/
    segmented_tables.json
    annotated_fused.png
    tables/
```

## Validation

- Repeating the command with the same input and parameters produces identical
  region coordinates and crop bytes.
- No manually authored page coordinates or semantic title strings enter the
  detector.
- Every proposed region has page-space and image-space coordinates.
- The manifest distinguishes parser hypotheses from logical region proposals.
- Inspect false merges and false splits against the deterministic render.

## Non-goals

- pages other than physical page 527
- production thresholds or cross-document validation
- TableFormer, OCR, VLM, LLM, or skill-based PDF analysis
- row repair or final canonical CSVs
- revising the Task 03A.9 family proposal

## Outcome

The fixed page-527 run found 34 connected ruled regions and parsed all 34 with
explicit Camelot Lattice areas. Camelot Network contributed one additional
large borderless region after a second overlapping Network region was rejected
by the fixed ruling-rectangle coverage rule. The resulting proposal contains
35 logical tables and completed in 16.7 seconds. Two independent ruling probes
produced identical region JSON and page-render hashes.
