# Task 03A.8: Cascade Cached Header Evidence

Status: **completed 2026-07-28; closed as exploratory evidence, not accepted**.

## Abstract

Reanalyze the 161 Task 03A.7 family boundaries without rerunning a parser,
renderer, or learned model. Prefer exact normalized native-header matrices,
fall back to the existing exact nested TableFormer labels, and finally compare
exact TableFormer header-text atoms independent of predicted cell and row
grouping. Produce a third review-only family proposal and measure the
incremental contribution of each evidence tier.

## Goal

Recover obvious false splits such as pages 71/72 while retaining exact,
auditable comparisons and preserving genuinely different boundaries such as
pages 526/527.

## Inputs

- immutable Task 03A.4 tables, assignments, and original 192-family proposal
- immutable Task 03A.7 boundary list, crops, and TableFormer predictions
- `configs/brisbane_baylands_2025_deir_task03a8_header_cascade_v1.json`

## Fixed cascade

Apply these tiers in order to each of the same 161 adjacent-page,
same-table-order boundaries:

1. **Native matrix.** Normalize every Camelot header cell with Unicode NFKC,
   collapsed whitespace, trim, and casefold. Remove only leading one-cell
   workbook filename rows matching `^[a-z0-9_]+_v[0-9]+$`. Preserve row and
   column position. Merge when both matrices are non-empty, column counts
   match, and the matrices are exactly equal.
2. **TableFormer nested labels.** If tier 1 does not pass, apply the Task 03A.6
   exact non-empty nested tuple rule to the cached predictions.
3. **TableFormer text atoms.** If tier 2 does not pass, select every non-empty
   cached TableFormer cell marked `column_header`, apply the same text
   normalization, split into Unicode word or individual punctuation atoms,
   preserve multiplicity, sort, and compare exactly. This ignores predicted
   cell boundaries, row assignment, and reading order.
4. Otherwise retain the split.

No fuzzy similarity, semantic aliases, leaf-header inference, geometry
threshold changes, or manual page exceptions are allowed. Join passing edges
transitively without crossing page gaps or table orders.

## Outputs

Write external evidence below:

```text
pipelines/brisbane_baylands/task_03a8_header_cascade_v1/
  pilot_manifest.json
  configuration.json
  environment.json
  boundary_cascade.jsonl
  boundary_cascade.csv
  revised_family_assignments.csv
  revised_table_families.csv
  revised_table_families.md
  inspection_examples.md
  summary.json
  artifact_inventory.json
```

## Research / learning checkpoint

The cascade treats the cheapest and least model-dependent exact evidence as
authoritative first. Later tiers can recover only unresolved boundaries. This
lets the run measure whether TableFormer contributes information beyond the
native header matrix instead of assuming that a learned model is necessarily
the stronger referee.

## Validation

- Unit-test native normalization and filename-row removal.
- Unit-test Unicode atomization, multiplicity, and grouping independence.
- Unit-test tier precedence and transitive revised-family assignment.
- Authenticate every reused upstream file and prediction.
- Require one cascade decision for each of the 161 Task 03A.7 boundaries.
- Require all 627 eligible Task 03A.4 assignments exactly once.
- Require every revised family to remain contiguous with no duplicate
  page/table-order pair.
- Require pages 71/72 to merge and pages 526/527 to remain split.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- No PDF parser, rendering, or learned model runs.
- Each passing boundary identifies exactly one first-successful tier.
- Statistics compare Task 03A.4, Task 03A.7, and Task 03A.8.
- Newly recovered boundaries are directly inspectable through cached crops.
- The result remains an unaccepted proposal.

## Non-goals

- pages 601-6104
- fuzzy or semantic header matching
- changing cached Task 03A.4 or Task 03A.7 evidence
- repairing extracted row data
- accepting a production family policy
- activating Task 03B

## Outcome

Completed 2026-07-28. The command authenticated all 241 cached Task 03A.7
predictions and reanalyzed the same 161 boundaries in 0.11 seconds. No PDF
parser, PDF rendering, network access, or learned model ran.

The cascade produced 130 passing boundaries and 31 exact-evidence
disagreements. It recovered 60 boundaries that Task 03A.7 had left split.
Every passing boundary was resolved by the first tier, exact normalized native
header-matrix equality. The nested TableFormer and grouping-independent atom
tiers uniquely resolved zero boundaries. In this sample, therefore,
TableFormer added no successful family-merge information beyond the preserved
native header grids.

The three proposal stages compare as follows:

| Statistic | Task 03A.4 | Task 03A.7 | Task 03A.8 |
| --- | ---: | ---: | ---: |
| Families | 192 | 122 | 62 |
| Single-page families | 111 | 64 | 38 |
| Multi-page families | 81 | 58 | 24 |
| Longest family, pages | 55 | 65 | 252 |
| Mean pages per family | 3.27 | 5.14 | 10.11 |

The page-71/72 positive control now merges from its identical seven-column
native header matrix despite TableFormer's incorrect six-column prediction on
page 72. The page-526/527 negative control remains split: the native tables
have seven versus forty columns and materially different header content.

The cascade joins one proposed family across pages 22-272 and another across
pages 275-526. Those long ranges are consistent with the user's expectation
that the document contains long contiguous table families, but they remain
review-only proposals. Six newly recovered boundaries link to the immutable
cached crops for inspection.

All 627 eligible Task 03A.4 assignments appear exactly once. Every revised
family is page-contiguous and contains no duplicate page/table-order pair.
External evidence is sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a8_header_cascade_v1/
```
