# Task 03A.5: Test TableFormer on One Over-Split Boundary

Status: **completed 2026-07-28; exact TableFormer merge test inconclusive**.

## Abstract

Test whether bare TableFormer structure predictions can adjudicate one known
Task 03A.4 over-split without running TableFormer across a full table or
document. Use the two boundary pairs separating proposed families 0014, 0015,
and 0016: physical pages 29/30 and 31/32. Derive four header-plus-two-data-row
crops reproducibly from preserved Camelot cell geometry, run the installed
accurate TableFormer model directly, and compare structure signatures.

## Goal

Determine whether TableFormer supplies consistent evidence for merging the
three fast-parser proposals into one candidate family spanning pages 22-46.
Measure actual model-load, crop-generation, and per-crop inference time.

## Inputs

- completed Task 03A.4 evidence
- sealed Appendix G3 PDF
- page/table IDs `g3_p00029_t001` through `g3_p00032_t001`
- preserved Camelot CSV, cells, and geometry
- the checksum-pinned Task 03A TableFormer model snapshot
- installed Docling 2.115.0 and `docling-ibm-models` 3.13.3
- `configs/brisbane_baylands_2025_deir_task03a5_tableformer_boundary_v1.json`

## Outputs

- a tracked, checksum-pinned test specification
- deterministic crop boxes and input PNGs
- the selected Camelot cells passed as native-text tokens
- raw TableFormer table records, cells, OTSL sequences, and timings
- exact structure signatures for each crop
- comparisons for page 29 versus 30 and page 31 versus 32
- a merge, do-not-merge, or inconclusive recommendation
- manifest, environment, summary, and artifact inventory

## Fixed method

- Run physical pages 29, 30, 31, and 32 only.
- Use table order 1 on every page.
- Select the leading Camelot header rows and the first two data rows.
- Remove only leading workbook-filename rows matching the fixed
  case-insensitive pattern `^[a-z0-9_]+_v[0-9]+$`; preserve every other row.
- Compute the crop from the union of selected Camelot cell boxes plus four PDF
  points of padding, clipped to the page.
- Render at TableFormer's native 144-DPI input scale with PDFium.
- Convert preserved Camelot cell boxes from bottom-left PDF coordinates to
  Docling top-left page coordinates and pass non-empty cells with unique IDs.
- Instantiate the installed accurate TableFormer once on CPU with eight
  threads and run the four crops sequentially.
- Do not run Heron, Docling conversion, OCR, TableFormerV2, or any page outside
  the four fixed pages.

The primary structure signature is:

- predicted column count;
- predicted row count;
- exact OTSL sequence; and
- ordered cell topology tuples containing row/column offsets, spans, and
  column-header flag.

Recommend merging all three proposed families only when both boundary pairs
have identical primary structure signatures. Otherwise return inconclusive or
do-not-merge with the preserved differences. Do not tune the signature after
viewing predictions.

## Artifact contract

Write generated evidence outside Git below:

```text
pipelines/brisbane_baylands/task_03a5_tableformer_boundary_v1/
  pilot_manifest.json
  configuration.json
  environment.json
  crops/
  predictions/
  crop_records.json
  comparisons.json
  summary.json
  artifact_inventory.json
```

## Validation

- Verify source, Task 03A.4 inputs, model artifacts, and configuration hashes.
- Unit-test filename-row removal, crop conversion, and exact signature
  comparison.
- Require four non-empty crops with selected header and data rows.
- Require one explicit prediction or failure record per page.
- Verify crop pixels and cell boxes remain in bounds.
- Record actual model-load and per-crop wall time.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- The four inputs and predictions are restartable and auditable.
- The recommendation follows the fixed exact comparison.
- Runtime is observed rather than projected.
- No family list is silently rewritten.
- No TableFormer work occurs beyond this boundary test.

## Non-goals

- rerunning Task 03A.4
- changing the 192 preserved proposals
- testing other boundaries
- designing a production merge algorithm
- full-table extraction or CSV repair
- TableFormer across pages 1-600

## Outcome

Completed 2026-07-28. The repository code derived four deterministic crops
from the preserved Camelot cell geometry for physical pages 29-32. Each input
contains the actual table header plus two data rows. The fixed workbook
filename pattern removed the extra filename row from page 29, while preserving
the `Risk Calculation Part 2`, `MiddleSchool`, grouped result header, leaf
columns, units, and data context on all four pages. The generated contact sheet
confirms that the intended content is present and legible.

The full command completed in approximately 35 seconds. Inside the recorded
stage timings, model construction took 1.16 seconds, all crop rendering took
0.084 seconds, and the four sequential TableFormer inferences took 1.74
seconds total:

| Physical page | Inference seconds |
| ---: | ---: |
| 29 | 0.488 |
| 30 | 0.436 |
| 31 | 0.377 |
| 32 | 0.434 |

The remaining command time includes Python and model-library startup plus
verification of the large sealed source checksum and upstream artifacts. This
test therefore confirms that small header crops are dramatically cheaper than
the prior approximately 107-second full dense-table observation.

TableFormer predicted the same coarse shape for all four crops: four rows,
seven columns, 32 OTSL tokens, and 22 cells. However, the exact structures did
not match at either boundary:

- pages 29/30 differed at three OTSL positions and in two grouped-header span
  tuples on each side;
- pages 31/32 differed at two OTSL positions and in one grouped-header span
  tuple on each side.

For pages 29/30, one prediction grouped header columns 0-4 and 4-6, while the
other grouped 0-2 and 4-7. For pages 31/32, the right-side grouped header
changed from columns 4-7 to 2-7. These span differences are not supported by
the visible crops, which show the same logical seven-column schema. They are
TableFormer prediction instability, not affirmative evidence of different
families.

The precommitted rule required exact OTSL and cell-topology equality at both
boundaries. The formal recommendation is therefore
`inconclusive_do_not_merge_from_exact_tableformer_signature`. Task 03A.5 does
not rewrite the Task 03A.4 family list. The useful learning is narrower:
TableFormer header crops are fast, but exact predicted spanning-header
topology is too unstable to serve as a strict automatic family-merge key for
this example. A later decision could compare only stable leaf-column and
normalized-header evidence, but that would be a new rule requiring a new
task—not a post-run relaxation of this test.

No Heron, Docling conversion, OCR, TableFormerV2, or pages beyond 29-32 ran.
External evidence is sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a5_tableformer_boundary_v1/
```

`crops/contact_sheet.png` owns the four review inputs;
`predictions/page_*.json` preserves raw cells and OTSL;
`comparisons.json` records the exact differences and recommendation; and
`summary.json` records timings.
