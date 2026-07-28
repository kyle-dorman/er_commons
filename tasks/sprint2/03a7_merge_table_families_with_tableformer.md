# Task 03A.7: Merge Fast-Parser Families with TableFormer Headers

Status: **completed 2026-07-28; closed as exploratory evidence, not accepted**.

## Abstract

Reanalyze every eligible boundary in the completed Task 03A.4 first-600-page
family proposal. Reuse the preserved Camelot results, run bare accurate
TableFormer only on the unique tables touching adjacent-page, same-order
family boundaries, compare the simple nested header-label tuples accepted in
Task 03A.6, and produce a new review-only family proposal.

## Goal

Measure how much the exact nested-header rule reduces Task 03A.4
over-segmentation, preserve auditable predictions and boundary decisions, and
provide before/after statistics plus representative changed examples for
human inspection.

## Inputs

- completed Task 03A.4 family evidence for physical pages 1-600
- completed Tasks 03A.5 and 03A.6 method
- sealed Appendix G3 PDF
- checksum-pinned accurate TableFormer model
- `configs/brisbane_baylands_2025_deir_task03a7_tableformer_family_merge_v1.json`

## Fixed method

1. Verify the sealed source, Task 03A.4 manifest, inventory, tables,
   assignments, and family list, plus the TableFormer model files.
2. Define a candidate boundary only when the last eligible table in one
   Task 03A.4 family and the first eligible table in another family:
   - occur on consecutive physical pages;
   - have the same parser table order; and
   - are consecutive for that table order in the preserved assignments.
3. Deduplicate tables that touch two boundaries and run one prediction per
   unique table.
4. Reuse the Task 03A.5 crop method: remove only the fixed leading workbook
   filename row, retain every remaining Camelot header row plus the first two
   data rows, add four PDF points of padding, render at 144 DPI, pass preserved
   native-text cells, and run accurate TableFormer once on CPU with eight
   threads.
5. Build the Task 03A.6 signature from every non-empty predicted
   `column_header` cell: Unicode NFKC, collapsed whitespace, trim, casefold,
   group by predicted row, order left-to-right, and deduplicate labels only
   within one row.
6. Merge a boundary only when both signatures are non-empty and exactly equal.
   Ignore leaf identity, spans, end-column offsets, column count, geometry,
   OTSL, and fuzzy similarity. A failed prediction or empty signature cannot
   merge.
7. Join passing boundaries transitively, while retaining all original table
   assignments and never linking across a page gap or table order.

The result is a revised proposal, not an accepted family inventory.

## Outputs

Write generated evidence outside Git below:

```text
pipelines/brisbane_baylands/task_03a7_tableformer_family_merge_v1/
  pilot_manifest.json
  configuration.json
  environment.json
  crops/
  predictions/
  crop_records.jsonl
  header_signatures.jsonl
  boundary_comparisons.csv
  boundary_comparisons.jsonl
  revised_family_assignments.csv
  revised_table_families.csv
  revised_table_families.md
  inspection_examples.md
  summary.json
  artifact_inventory.json
```

## Research / learning checkpoint

TableFormer predictions are local evidence about the two observed edge crops,
not proof that every interior page has the same schema. Exact matching favors
precision over recall: it can leave false splits when TableFormer omits or
misassigns a header, but it avoids fuzzy semantic merges. Transitive merging
is valid only over consecutive passing edges within the original contiguous
sequence.

## Validation

- Unit-test candidate-boundary selection, non-empty exact matching, transitive
  merges, stable revised IDs, and summary statistics.
- Require an explicit success or failure record for every unique edge table.
- Require one decision for every candidate boundary.
- Require all 627 eligible Task 03A.4 assignments to appear exactly once.
- Require revised families to remain contiguous and contain at most one table
  of a given order per page.
- Confirm pages 22-46 merge through the known page 29/30 and 31/32 controls.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- The fast parser is not rerun.
- TableFormer runs only on deduplicated boundary crops.
- Old and revised family statistics are directly comparable.
- Every merge is traceable to two preserved predictions and exact signatures.
- Several changed boundaries have inspectable crops and label tuples.
- The Task 03A.4 artifacts remain immutable.

## Non-goals

- pages 601-6104
- full-page or full-table TableFormer extraction
- canonical CSV repair
- leaf-header detection
- fuzzy header matching
- merging same-page overlapping table hypotheses
- accepting the revised proposal without user review
- activating Task 03B

## Outcome

Completed 2026-07-28. The run verified and reused the immutable Task 03A.4
first-600-page evidence; Camelot did not rerun. Grouping preserved eligible
assignments by parser table order identified 161 adjacent-page cross-family
boundaries. Their deduplicated endpoints required 241 header-plus-two-data-row
crops and TableFormer predictions.

All 241 crops and predictions succeeded. The model loaded once in 1.09 seconds,
TableFormer inference totaled 110.49 seconds, and the complete command took
116.46 seconds. The exact non-empty nested-header rule produced:

- 70 passing boundaries;
- 86 nested-header mismatches; and
- 5 boundaries where at least one predicted header tuple was empty.

There were no crop or prediction failures. Passing edges were joined
transitively without crossing page gaps or table orders. The resulting
review-only proposal changed the family statistics as follows:

| Statistic | Task 03A.4 | Task 03A.7 |
| --- | ---: | ---: |
| Families | 192 | 122 |
| Single-page families | 111 | 64 |
| Multi-page families | 81 | 58 |
| Longest family, pages | 55 | 65 |
| Mean pages per family | 3.27 | 5.14 |

The known control passed: the page-29/30 and page-31/32 edges now join pages
22-46. The same exact tuple also passes later boundaries through page 71, so
the revised family `g3_tf_family_0014` spans pages 22-71 and combines 11
original proposals. The largest revised family spans pages 462-526 and
combines eight original proposals.

All 627 eligible Task 03A.4 table assignments appear exactly once in the
revised assignments. Every revised family is contiguous and has no duplicate
page/table-order pair. Six passing examples, excluding the already reviewed
29/30 and 31/32 boundaries, were selected for inspection. This output remains
a historical proposal; no result was promoted to a production
family contract.

External evidence is sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a7_tableformer_family_merge_v1/
```
