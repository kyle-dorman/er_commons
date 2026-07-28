# Task 03A.2: Classify Table-Dominant Native-PDF Pages

Status: **completed 2026-07-27; accepted as a conservative routing signal**.

## Abstract

Implement and run a cheap, non-ML preflight that identifies table-dominant
pages before Heron or a table parser runs. Task 03A.1 showed that Appendix G3
contains dense native-text tables that are usable through Camelot Stream in
seconds rather than TableFormer's roughly 107 seconds per page. This task
classifies all 6,104 physical pages of Appendix G3 using native PDFium text
geometry and content-density features only. It does not extract tables or
begin canonical conversion.

## Goal

Produce a reproducible page-level classification and contiguous page ranges
that can route table-dominant pages to the provisional fast Stream path. Show
whether the rule cleanly separates the seven already reviewed positive and
negative controls, measure preflight runtime, and preserve enough features to
audit every decision.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `tasks/sprint2/03a1_validate_table_extraction.md`
- `configs/brisbane_baylands_2025_deir_task03a2_table_router_v1.json`
- the sealed main-report and Appendix G3 PDFs
- pypdfium2's maintained
  [text-page API](https://pypdfium2.readthedocs.io/en/stable/python_api.html)

## Outputs

- a tracked, checksum-pinned classifier specification
- typed project glue and a package-backed CLI command
- one external JSONL and CSV page-feature record per Appendix G3 page
- contiguous table-dominant ranges
- deterministic control and boundary-page renders for review
- a compact summary, environment record, artifact inventory, and manifest
- an accept, revise, or reject outcome for using this preflight as a router

## Research / learning checkpoint

PDFium exposes native page bounds, text, and text rectangles but does not
perform layout analysis. Use those observable primitives rather than claiming
that PDFium understands tables. Explain that page classification, table-region
detection, grid reconstruction, row segmentation, and canonical header
normalization remain separate operations.

The classifier must be deterministic, interpretable, and fast enough to run on
all 6,104 pages. It may use text span, native line count, non-space character
density, digit fraction, and coordinate-key count. It must not use OCR, Heron,
TableFormer, Camelot, an LLM, or a learned classifier.

## Fixed specification

The tracked configuration fixes:

- source release, source roles, SHA-256, page counts, and physical page basis;
- the full Appendix G3 page range, 1 through 6,104;
- negative controls at main-report pages 124 and 1500;
- positive controls at G3 pages 999, 1000, 1001, 2000, and 4000; and
- the precommitted conjunction:
  - native text width span at least 0.70 of page width;
  - native text height span at least 0.75 of page height;
  - at least 80 non-empty native text lines;
  - at least 0.02 non-space characters per PDF square point; and
  - at least 0.35 of non-space characters are digits.

Coordinate-key count is recorded as a diagnostic but is not required, allowing
other dense numeric table schemas to pass. Pages with no native text or an
extraction error must produce an explicit negative/error record.

Do not tune thresholds after viewing the full-run distribution. If a reviewed
boundary page reveals a material error, preserve this run and write a new
configuration ID in a later revision.

## Artifact contract

Write generated outputs outside Git below:

```text
pipelines/brisbane_baylands/task_03a2_table_router_v1/
  pilot_manifest.json
  environment.json
  page_features.jsonl
  page_features.csv
  table_dominant_ranges.csv
  controls.json
  boundary_samples.json
  renders/
  summary.json
  artifact_inventory.json
```

Each page record must include source ID and SHA-256, one-based physical page,
page dimensions, feature values, each threshold result, final classification,
wall time, status, and recoverable error text. The summary must report counts,
fractions, contiguous ranges, runtime, feature minima/maxima, and the fixed
control results.

## Validation

- Verify sealed source roles, page counts, checksums, and bytes before scanning.
- Unit-test threshold boundaries, empty text, and range grouping.
- Require all seven fixed controls to match their expected classification.
- Render every control plus deterministic transition and nearest-threshold
  samples, capped at 40 unique Appendix G3 pages.
- Human-review the rendered boundary sample before accepting the router.
- Rerun one positive and one negative page and require identical normalized
  features and classification.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- All 6,104 G3 pages receive explicit records with no silent omission.
- All seven fixed controls pass.
- The full scan completes without Heron, TableFormer, Camelot, OCR, or network
  access.
- Runtime is materially below Heron-only processing.
- Boundary samples do not show a material narrative-page false positive or
  full-page dense-table false negative.
- The outcome records that this is a routing signal, not table validation.
- No table extraction or full-document conversion begins.

## Non-goals

- extracting or repairing CSV rows
- changing Task 03A.1's provisional Lattice/Stream choices
- proving every classified page has correct table structure
- tuning thresholds from the full-run result
- parallel extraction, canonical schemas, or Task 03B activation

## Outcome

Completed 2026-07-27. The fixed native-PDF classifier successfully processed
all 6,104 physical pages of Appendix G3 with zero page errors. It classified
4,408 pages, or 72.21 percent, as table-dominant and grouped them into 24
contiguous ranges. The full page-level records are preserved as both JSONL and
CSV, and `table_dominant_ranges.csv` is the compact routing view.

The scan took 129.18 seconds, averaging 0.0212 seconds per page and 47.25 pages
per second. This is roughly 231 times faster per page than the 4.89-second mean
from the five Heron-only G3 stress pages in Task 03A.1. The comparison is a
planning contrast rather than a representative production benchmark, but it
confirms that PDFium-native preflight is cheap enough to run before learned
layout analysis.

All seven precommitted controls passed. Main-report pages 124 and 1500 were
negative; G3 pages 999, 1000, 1001, 2000, and 4000 were positive. A normalized
rerun of G3 page 999 and main-report page 124 produced identical features and
classifications. The scan used pypdfium2 5.12.1 with no Heron, TableFormer,
Camelot, OCR, learned classifier, network access, or table extraction.

The distributed visual review covered 40 pages: the five fixed G3 positives
and evenly spaced true/false transition pairs across the full 6,104-page
source. Reviewed positive pages were dominated by one or several dense numeric
tables. Reviewed negative transition pages frequently still contained tables,
but those tables occupied only part of the page. Therefore `false` means
**not table-dominant**, not **no table present**. This is the intended
conservative boundary for deciding when a full-page fast parser is plausible.

The fixed conjunction uses native text width and height span, non-empty line
count, non-space character density, and digit fraction. Coordinate-key count
is diagnostic only. PDFium supplies page bounds, text, and text rectangles; it
does not perform layout analysis, as its maintained
[text-page API](https://pypdfium2.readthedocs.io/en/stable/python_api.html)
notes. The result is therefore a routing signal, not table detection, row
validation, or canonical table acceptance.

The accepted next constraint is narrow: pages classified `true` may be sent to
the provisional fast full-page Stream route, while `false` pages stay on the
general path. Before production extraction, one more bounded test must confirm
that Stream can operate from the full page or a cheap native-text extent
without a Heron-supplied table box. Task 03A.2 does not claim that Stream fixes
wrapped rows or normalized headers.

External evidence is sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a2_table_router_v1/
```

`page_features.csv` and `page_features.jsonl` contain all 6,104 decisions;
`table_dominant_ranges.csv` contains the 24 inclusive ranges;
`boundary_samples.json` and `renders/boundary_contact_sheet.png` own the visual
review sample; and `review_decision.json` records the accepted claim boundary.
No table extraction or full-document conversion began.
