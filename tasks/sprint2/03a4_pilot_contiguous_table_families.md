# Task 03A.4: Pilot Contiguous Table-Family Segmentation

Status: **completed 2026-07-28; closed as exploratory evidence, not accepted**.

## Abstract

Run the accepted fast native-PDF parser over Appendix G3 physical pages 1-600
and use its table-level outputs to propose contiguous table families for human
inspection. Task 03A.3 routing ranges are not table families: a range may
contain many schemas, and a page may contain more than one parser-returned
table. This pilot assigns a stable identifier to every fast-parser table and
segments only adjacent pages. It does not search for the same family in
noncontiguous parts of the PDF.

## Goal

Produce a reviewable list of proposed table families with inclusive start and
end pages for G3 pages 1-600. Preserve the underlying per-page, per-table fast
parser result so the user can inspect whether boundaries are useful before any
TableFormer work or full-document family inference.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- completed Tasks 03A.1 through 03A.3
- the sealed Appendix G3 PDF
- Camelot 2.0.0's maintained
  [Stream documentation](https://camelot-py.readthedocs.io/en/stable/user/how-it-works.html)
  and [API](https://camelot-py.readthedocs.io/en/stable/api.html)
- the isolated Task 03A.1 Camelot environment and lock
- `configs/brisbane_baylands_2025_deir_task03a4_table_families_v1.json`

## Outputs

- a tracked, checksum-pinned pilot specification
- raw Camelot Stream CSV, cell, geometry, parsing-report, timing, warning, and
  error evidence for every page and detected table
- a stable identifier for each parser table in the form
  `g3_p<page>_t<table-order>`
- one table fingerprint record per parser-returned table
- one family assignment per eligible table
- a CSV and Markdown table-family list with family ID, start page, end page,
  table count, page count, table orders, and compact header/schema preview
- page-level results including explicit zero-table and failure records
- a manifest, artifact inventory, environment, summary, and review status

## Research / learning checkpoint

Camelot Stream derives table regions from native text when `table_areas` is
not supplied. Its returned objects are parser hypotheses, not ground-truth
logical tables. Preserve every raw return before filtering or grouping.

Explain the distinction among:

- a numeric-table routing range;
- a parser-returned table region;
- a contiguous table family sharing a stable schema; and
- a human-accepted family boundary.

Table family is defined provisionally as a contiguous sequence of
parser-returned tables with compatible table order, column geometry, and
header evidence. Do not claim that a family recurs later in the document.

## Fixed pilot specification

- Source: sealed `deir_appendix_g3`, physical pages 1-600 inclusive.
- Parser: isolated `camelot-py==2.0.0`, `flavor="stream"`.
- Use automatic region detection: do not provide Heron regions,
  `table_areas`, manual columns, header anchors, or footer anchors.
- Keep `split_text=False`, `flag_size=False`, `strip_text=""`,
  `parallel=False`, and Camelot's default Stream tolerances.
- Process restartable batches of at most 25 pages, with at most four isolated
  worker processes.
- Preserve all parser results. A result is family-eligible only when it has at
  least two columns, at least three rows, and at least 20 percent digit
  characters among non-space characters.

For each eligible parser table:

1. derive ordered normalized column boundaries from Camelot cell geometry;
2. identify up to eight leading header rows before the first data-like row,
   where a data-like row contains a coordinate key or at least half of its
   non-empty cells are numeric-like;
3. normalize header tokens to lowercase alphabetic tokens without numbers;
4. record shape, normalized bounding box, header rows/text/tokens, coordinate
   key count, digit fraction, and parsing report; and
5. assign a family only by walking pages forward.

A table may continue the immediately preceding page's same table order only
when:

- the physical pages are adjacent;
- both tables have the same column count;
- maximum absolute normalized column-boundary drift is at most 0.02; and
- either header-token Jaccard similarity is at least 0.50, or one header is
  empty and the boundary drift is at most 0.01.

Otherwise start a new family. Never link across a page gap, never compare a
table to a nonadjacent prior family, and never tune these thresholds from the
pages 1-600 result. The list is deliberately conservative: false splits are
preferable to silently merging different schemas.

## Artifact contract

Write generated evidence outside Git below:

```text
pipelines/brisbane_baylands/task_03a4_table_families_v1/
  pilot_manifest.json
  environment.json
  requests/
  batches/
  pages/
  tables.jsonl
  tables.csv
  family_assignments.jsonl
  family_assignments.csv
  table_families.csv
  table_families.md
  summary.json
  review_decision.json
  artifact_inventory.json
```

Every raw table retains source checksum, physical page, parser order,
configuration, bounding box, shape, parsing report, CSV, cell geometry, and
hashes. Every family assignment points back to exactly one raw table ID.

## Validation

- Verify the sealed source checksum and page count.
- Verify the isolated Camelot lock and package versions.
- Unit-test header-row detection, fingerprint normalization, adjacency,
  geometry drift, header similarity, family splitting, and stable identifiers.
- Require explicit records for all 600 pages with no omissions or duplicates.
- Require every raw table ID and family ID to be unique.
- Require every assignment to resolve to one raw table.
- Require every family to span only contiguous physical pages and one table
  order per page.
- Confirm pages 525 and 526 are eligible to join when their fast-parser
  fingerprints meet the fixed rule, and confirm page 527 cannot affect this
  pilot because it starts outside any inferred backward family relationship.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- Pages 1-600 have complete restartable fast-parser records.
- Every parser-returned table has a stable per-page identifier and preserved
  raw output.
- The family list includes start and end pages and is directly inspectable.
- No family crosses a page gap or claims noncontiguous recurrence.
- The output is labeled a proposal awaiting human review.
- No TableFormer, Heron, Docling, OCR, learned model, or full-document family
  run occurs.

## Non-goals

- accepting family boundaries without user review
- processing pages 601-6104
- finding noncontiguous recurrence
- repairing wrapped rows or malformed CSVs
- canonical header reconstruction
- TableFormer or any learned table model
- activating Task 03B

## Outcome

Completed 2026-07-28. Camelot Stream processed all 600 fixed physical pages in
24 restartable batches with four isolated workers. Every page has an explicit
success record, including two zero-table pages. The parser returned 633 table
hypotheses; 627 met the precommitted shape and numeric-content eligibility
rule. There were no parser errors. Seven warnings were preserved: two
page-level no-table warnings and five automatic-area no-table warnings.

The fixed family rule proposed 192 contiguous families. Eighty-one span
multiple pages, 111 contain one page, and the longest spans 55 pages. The
parallel run took 225.0 wall seconds; summed isolated batch time was 558.3
seconds. Generated evidence occupies approximately 455 MB. No Heron, Docling,
TableFormer, OCR, learned model, manual table area, manual column boundary, or
noncontiguous recurrence search ran.

The reviewed control relationship behaves as intended. Tables
`g3_p00525_t001` and `g3_p00526_t001` are consecutive members of
`g3_family_0162`, which spans pages 472-526. Page 526 has only 0.00316
normalized column-boundary drift from page 525 and identical normalized header
tokens. Page 527 starts two new parser table IDs and two new proposed families,
`g3_family_0164` and `g3_family_0165`; neither is attached backward to the
page-525/526 family.

The preserved result also exposes a material limitation for user review. The
rule visibly over-splits some apparently stable long sections. For example,
the repeated seven-column `MiddleSchool` calculation schema between pages 22
and 272 is divided into many families when Camelot slightly changes inferred
column boundaries or alternately includes the workbook filename in the leading
header rows. Camelot also occasionally returns a second overlapping table
hypothesis on one page. The 192-family list is therefore a conservative
proposal, not an accepted schema inventory.

This pilot intentionally preserves those false splits because the contract
forbids threshold tuning after viewing pages 1-600. The user must inspect the
list and decide whether the next revision should normalize repeated filename
rows, compare a stable subset of column anchors, or introduce a small reviewed
boundary set. No full-document extension or TableFormer work should begin from
this unaccepted list.

External evidence is sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a4_table_families_v1/
```

`table_families.csv` and `table_families.md` contain the proposed start/end
list. `tables.csv` provides one row per stable page/table ID;
`family_assignments.csv` gives every assignment and similarity observation;
and `batches/` preserves the raw CSV, cells, geometry, parsing report, timing,
warning, and error evidence. `review_decision.json` remains
`pending_user_review`.
