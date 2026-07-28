# Task 03A.3: Classify Numeric Table-Bearing G3 Pages

Status: **completed 2026-07-27; accepted as the G3 numeric-table routing signal**.

## Abstract

Revise the Task 03A.2 routing signal without overwriting it. Task 03A.2
correctly identified pages dominated by tables, but it classified partial
continuation pages such as G3 page 526 as negative because the table occupied
only part of the page. For routing, that would unnecessarily send a native
numeric table continuation toward the expensive general path. Create a new
classifier version that identifies G3 pages bearing substantial native numeric
table data regardless of how much vertical space the table occupies.

Page 526 is a continuation of the table run containing page 525, not the
different table family beginning on page 527. Preserve that reviewed
relationship explicitly; do not infer its run membership from forward
adjacency.

## Goal

Classify all 6,104 Appendix G3 pages as numeric-table-bearing or general-path
candidates using a cheap, deterministic PDFium preflight. Compare the result
with Task 03A.2, review newly included partial pages and true negatives, and
produce contiguous routing ranges without running any table parser.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- completed Tasks 03A.1 and 03A.2
- the sealed Appendix G3 PDF
- the immutable Task 03A.2 page-feature records
- `configs/brisbane_baylands_2025_deir_task03a3_numeric_table_router_v1.json`
- pypdfium2's
  [text-page API](https://pypdfium2.readthedocs.io/en/stable/python_api.html)

## Outputs

- a new tracked classifier specification and configuration ID
- explicit positive partial-page and negative controls fixed before the run
- one new page-level JSONL and CSV classification record per G3 page
- inclusive numeric-table-bearing ranges
- a comparison against Task 03A.2 showing newly included and excluded pages
- review renders covering page 525-527, partial continuations, negatives, and
  distributed transitions
- a summary, review decision, artifact inventory, and manifest

## Research / learning checkpoint

Whole-page text bounds are distorted by repeated headers and footers and do not
measure the actual table height. For this G3-specific routing problem, use
observable numeric-table signals that remain present on continuation pages:
wide native text, enough non-empty lines, enough non-space text density, and a
high digit fraction. Coordinate-key count remains diagnostic because some G3
table families do not use the same lookup-key syntax.

Explain that detecting a likely numeric table page does not identify table-run
membership, reconstruct rows, or validate CSV output. The page 525-526
relationship is reviewed metadata, not evidence that every adjacent page
belongs to the same schema.

## Fixed rule

Create a new configuration rather than modifying Task 03A.2. A successful page
is `numeric_table_bearing` when all are true:

- text width span is at least 0.70 of page width;
- there are at least 20 non-empty native text lines;
- non-space character density is at least 0.005 per PDF square point; and
- at least 0.50 of non-space characters are digits.

Do not require text-height dominance or 80 lines. Preserve Task 03A.2's original
classification in the comparison record. Do not tune the rule after viewing
the full new run.

Before the run, render and fix a small set of negative controls selected by
physical page number, not classifier output. Positive controls must include
pages 525, 526, 527, 975, 1153, 1246, 3642, 4877, 5369, 5683, and 6101.
Record pages 525 and 526 as reviewed family `pre_527_continuation`; record page
527 as `new_family_start`.

## Artifact contract

Write generated outputs outside Git below:

```text
pipelines/brisbane_baylands/task_03a3_numeric_table_router_v1/
  pilot_manifest.json
  environment.json
  page_classifications.jsonl
  page_classifications.csv
  numeric_table_ranges.csv
  comparison_with_task03a2.json
  controls.json
  boundary_samples.json
  review_decision.json
  renders/
  summary.json
  artifact_inventory.json
```

Every page retains the Task 03A.2 features, old classification, new threshold
results, new classification, and reason. The new stage may reuse immutable
Task 03A.2 features only after verifying its manifest, source checksum, record
count, page sequence, and artifact checksum.

## Validation

- Verify the sealed source and all reused Task 03A.2 evidence.
- Unit-test the new conjunction and old-to-new comparison.
- Require every fixed positive and negative control to pass.
- Confirm pages 525 and 526 are positive and page 527 is separately labeled.
- Visually review fixed controls and distributed classification transitions.
- Rerun raw PDFium features for page 526 and one negative control and require
  equality with the reused Task 03A.2 records.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- All 6,104 pages receive explicit classifications with no omission.
- Page 526 and the other fixed partial-table positives use the fast-candidate
  class.
- Reviewed negatives do not become numeric-table false positives.
- The scan remains non-ML, native-text-only, and far cheaper than Heron.
- The output states that false means general-path candidate, not no table.
- No Camelot, TableFormer, Heron, OCR, or full extraction runs.

## Non-goals

- automatically inferring all table-family or run boundaries
- extracting CSVs
- fixing wrapped rows or headers
- changing Task 03A.2 artifacts
- activating Task 03B or extracting all fast candidates

## Outcome

Completed 2026-07-27. The fixed Task 03A.3 rule classified all 6,104 physical
Appendix G3 pages with zero errors. It marked 6,067 pages, or 99.39 percent, as
numeric-table-bearing fast-route candidates and left 37 pages as general-path
candidates. The positive pages form seven inclusive ranges:

```text
21-272
275-1339
1342-1593
1596-2634
2638-3527
3531-4987
4990-6101
```

This broad result matches the appendix's visual structure: nearly all pages
are dense calculation tables, while the remaining pages are covers, section
dividers, or sparse mixed-layout calculation summaries. A negative remains a
general-path candidate, not a claim that the page contains no table.

The run verified and reused all 6,104 immutable Task 03A.2 page-feature
records. It pinned the upstream manifest, inventory, and feature-file
checksums; verified the source identity and sequential one-based page record;
and applied the new conjunction in 0.058 seconds. This classification time
excludes the deterministic review renders. A raw PDFium rerun of page 526 and
negative control page 1 reproduced every Task 03A.2 feature except timing.

All 17 fixed controls passed. Page 526 changed from Task 03A.2 negative to the
new fast-route class because its 52 native lines, 0.00667 character density,
0.602 digit fraction, and 0.832 page-width span pass the partial-page rule.
Pages 525 and 526 retain reviewed family
`pre_527_continuation`; page 527 is separately labeled
`new_family_start`. These labels preserve the user's reviewed relationship and
do not generalize adjacency into automatic schema or run inference.

Compared with Task 03A.2, the new rule keeps all 4,408 prior positives and adds
1,659 partial or formerly non-dominant numeric-table pages. It excludes no
Task 03A.2 positive. Visual review covered all fixed controls plus distributed
classification transitions, capped at 40 rendered pages. Newly included
samples are dense full or partial numeric tables. Reviewed negatives include
blank/title pages and pages with small tables mixed with formulas, notes, or
summary content, which remain appropriate for the general path.

The accepted output is still only a router. PDFium exposes native text and
geometry but does not reconstruct table cells. Task 03A.3 therefore does not
identify all table-family boundaries, fix wrapped rows, or validate CSV
output. The next task must preserve source page and geometry evidence around
any fast CSV derivative and must treat pages 525-526 as one reviewed table run
distinct from the family beginning on page 527.

External evidence is sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a3_numeric_table_router_v1/
```

`page_classifications.csv` and `page_classifications.jsonl` contain every
page-level decision; `numeric_table_ranges.csv` is the compact routing view;
`comparison_with_task03a2.json` records the 1,659 additions;
`renders/boundary_contact_sheet.png` owns the visual review sample; and
`review_decision.json` records the accepted claim boundary. No Camelot,
TableFormer, Heron, OCR, or table extraction ran.
