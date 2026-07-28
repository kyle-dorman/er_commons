# Task 03A.6: Compare Nested TableFormer Header Labels

Status: **completed 2026-07-28; nested labels support the merge**.

## Abstract

Reanalyze the four preserved Task 03A.5 TableFormer predictions with a simpler
family signature. Group every non-empty cell that TableFormer marked
`column_header` by predicted row, order labels left-to-right, normalize the
text, and represent the result as a nested tuple. Ignore predicted spans,
leaf-header identity, column count, geometry, and OTSL topology.

## Goal

Test whether exact nested header-label tuples support merging the known
Task 03A.4 over-split across page boundaries 29/30 and 31/32 without rerunning
TableFormer or changing the preserved family list.

## Fixed rule

- Reuse only Task 03A.5 predictions for physical pages 29-32.
- Verify the upstream manifest, inventory, and four prediction checksums.
- Select non-empty `table_cells` with `column_header=true`.
- Normalize each label with Unicode NFKC, whitespace collapse, trim, and
  `casefold()`.
- Group by `start_row_offset_idx`.
- Within a row, order by `start_col_offset_idx` and then original prediction
  order.
- Drop duplicate normalized labels only when they occur in the same predicted
  row.
- Do not inspect or require leaf headers.
- Do not use spans, end-column offsets, column count, geometry, OTSL, fuzzy
  similarity, or special-case text.
- Recommend merging families 0014-0016 only if pages 29, 30, 31, and 32 have
  one identical nested tuple.

## Outputs

Write external evidence below
`pipelines/brisbane_baylands/task_03a6_nested_header_labels_v1/`:

- `header_signatures.json`
- `comparisons.json`
- `summary.json`
- `environment.json`
- `artifact_inventory.json`
- `pilot_manifest.json`

## Validation

- Unit-test normalization, row grouping, ordering, deduplication, and exact
  comparison.
- Require four verified predictions and one signature per page.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- The result is a deterministic reanalysis of preserved predictions.
- No model or PDF parser runs.
- The Task 03A.4 list remains unchanged as historical exploratory evidence.

## Non-goals

- identifying leaf headers
- using predicted spans or geometry
- rerunning TableFormer
- testing other boundaries
- rewriting family assignments

## Outcome

Completed 2026-07-28. The checksum-verified Task 03A.5 predictions for pages
29-32 all produced the same exact nested header-label tuple:

```text
(
  (
    "risk calculation part 2: ∑r1*cdpm",
    "middleschool",
  ),
  (
    "lookup",
    "x (utm)",
    "y (utm)",
    "z (m)",
    "3rd trimester",
    "total (per million)",
  ),
)
```

Both boundary comparisons, page 29 versus 30 and page 31 versus 32, pass.
Under the fixed simple rule, Task 03A.6 recommends merging
`g3_family_0014`, `g3_family_0015`, and `g3_family_0016` into one proposed
family spanning physical pages 22-46.

This result uses every non-empty TableFormer cell marked `column_header`,
grouped by predicted row and ordered left-to-right. It does not decide which
row is the leaf, and it ignores spans, end-column offsets, column count,
geometry, OTSL, and fuzzy similarity. The result shows that TableFormer's
header text and row assignment are stable on this boundary even though its
grouped-header colspan predictions are not.

No model or PDF parser ran. The Task 03A.4 family list remains unchanged until
the user decides whether to promote this nested-label rule into a revised
family pass.

External evidence is sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a6_nested_header_labels_v1/
```

`header_signatures.json` contains all four tuples; `comparisons.json` records
the exact matches and merge recommendation; and `summary.json` records that no
model, parser, or family-list rewrite occurred.
