# Task 03A.9: Build Footer-Aware Native Table Families

Status: **completed 2026-07-28; accepted through the clean table pipeline**.

## Abstract

Revise the first-600-page family proposal using native worksheet footers as
explicit page-run evidence. Parse `sheet_id N of M` from full-page native text,
assign each footer only to the highest-order Camelot table on that page, strip
footer rows from the preserved CSV, drop columns that become entirely empty,
and group the footer-owned tables by consecutive counters. Reanalyze remaining
tables using cleaned native headers only. Do not use TableFormer.

## Goal

Represent long exported worksheet runs directly, including the page-527 start
of the family containing page 541, without allowing earlier tables on a
multi-table page to inherit the footer.

## Inputs

- sealed Appendix G3 PDF
- immutable Task 03A.4 tables, assignments, and family proposal
- authenticated Task 03A.8 summary for comparison only
- `configs/brisbane_baylands_2025_deir_task03a9_footer_families_v1.json`

## Fixed method

1. Verify the sealed PDF and all reused Task 03A.4 and Task 03A.8 inputs.
2. Extract native text from physical pages 1-600 with the accepted
   PyPdfium2-backed native path. Do not render pages.
3. Parse the final page-footer match with the fixed case-insensitive pattern
   `(?P<sheet>\d+\.[A-Za-z0-9_]+) (?P<page>\d+) of (?P<total>\d+)`.
4. Form a footer run only across adjacent physical pages with identical
   normalized `sheet`, identical `total`, and an internal page increment of
   exactly one.
5. Assign a page footer only to the maximum parser table order returned on
   that page. If that table is not family-eligible, record the footer without
   assigning an eligible owner. Earlier table hypotheses on the page never
   inherit the footer.
6. Build one footer family from the eligible owner table on every consecutive
   page of a footer run. Footer identity and sequence are direct run evidence;
   changing parser table order does not break the run.
7. For every preserved Camelot CSV:
   - normalize Unicode NFKC, whitespace, and case;
   - remove rows whose joined non-empty cells contain the fixed footer
     `N of M` pattern;
   - drop columns that are entirely empty after footer-row removal;
   - apply the retained columns to the preserved header grid; and
   - remove only leading one-cell workbook filename rows matching
     `^[a-z0-9_]+_v[0-9]+$`.
8. For eligible tables not owned by a footer run, retain contiguous portions
   of their original Task 03A.4 families and merge adjacent-page,
   same-table-order portions only when their cleaned, non-empty native header
   matrices and effective column counts are exactly equal.
9. Assign every eligible parser table exactly once. A revised family may
   contain at most one table per physical page.

The footer family is a printed worksheet run. It is stronger than parser
geometry for page continuity, but it does not claim that every interior row
uses one canonical leaf-header topology.

## Outputs

Write external evidence below:

```text
pipelines/brisbane_baylands/task_03a9_footer_families_v1/
  pilot_manifest.json
  configuration.json
  environment.json
  page_footers.csv
  page_footers.jsonl
  footer_runs.csv
  footer_runs.json
  cleaned_table_signatures.jsonl
  revised_family_assignments.csv
  revised_table_families.csv
  revised_table_families.md
  comparison.json
  inspection_examples.md
  summary.json
  artifact_inventory.json
```

## Research / learning checkpoint

An internal worksheet page counter is provenance-like continuity evidence:
matching identifiers, totals, and consecutive counters identify one exported
print run even when a table parser absorbs the footer or changes column
geometry. Because a page may contain multiple table hypotheses, footer
ownership must be explicit and singular. The result remains document-specific
and provisional until tested on another document.

## Validation

- Unit-test footer parsing, run formation, last-table ownership, footer-row
  stripping, empty-column removal, and cleaned header signatures.
- Require explicit footer or no-footer records for all 600 pages.
- Require no footer to have more than one table owner.
- Require all 627 eligible tables exactly once across revised families.
- Require no revised family to contain two tables from one physical page.
- Confirm four observed footer runs: pages 19-272, 273-526, 527-591, and
  592-600.
- Confirm page 527 table order 2 owns `1 of 65`, page 528 table order 1 owns
  `2 of 65`, and they share one footer family.
- Confirm pages 540/541 clean to 37 effective columns and share that family.
- Run `make fix`, `make check`, and `git diff --check`.

## Acceptance criteria

- No Camelot or TableFormer rerun occurs.
- Native page-text extraction is reproducible and completes over pages 1-600.
- Footer and cleanup evidence is preserved per page and table.
- Earlier tables on multi-table pages do not inherit the footer.
- The output is a review-only proposal with an explicit cross-document
  validation requirement.

## Non-goals

- pages 601-6104
- TableFormer or any learned model
- fuzzy header matching
- canonical row-data repair
- proving the footer rule generalizes to other PDFs
- accepting a production family policy
- activating Task 03B

## Outcome

Completed 2026-07-28. The command verified the sealed PDF and reused Task
03A.4 artifacts, extracted native text from pages 1-600 in 3.30 seconds, and
completed in 3.95 seconds total. Camelot, TableFormer, page rendering, and
network access did not run.

The native text contained footers on 582 pages and formed four exact
consecutive worksheet runs:

| Physical pages | Worksheet | Internal pages |
| --- | --- | ---: |
| 19-272 | `2.HRA_BLOCKS_CancerRiskSchool` | 1-254 of 254 |
| 273-526 | `3.HRA_OTHER_CancerRiskSchool` | 1-254 of 254 |
| 527-591 | `2.HRA_BLOCKS_CancerRiskOnsite` | 1-65 of 65 |
| 592-600 | `3.HRA_OTHER_CancerRiskOnsite` | 1-9 of 65 |

Each footer was assigned to exactly one maximum-order parser table. On page
527, `g3_p00527_t002` owns `1 of 65` and joins
`g3_p00528_t001`, which owns `2 of 65`; the earlier overlapping
`g3_p00527_t001` remains a separate one-page hypothesis. The footer-owned
family continues through page 591 and includes page 548.

Footer-row removal and empty-column cleanup resolves the page-540/541 parser
artifact. Both tables have 37 effective columns after page 541's footer-only
column is removed, and both belong to the page-527 through page-591 footer
family.

The result contains 37 families:

| Statistic | Task 03A.4 | Task 03A.8 | Task 03A.9 |
| --- | ---: | ---: | ---: |
| Families | 192 | 62 | 37 |
| Single-page families | 111 | 38 | 25 |
| Multi-page families | 81 | 24 | 12 |
| Longest family, pages | 55 | 252 | 254 |
| Mean pages per family | 3.27 | 10.11 | 16.95 |

The 37 include the four footer-owned runs plus 33 preserved non-owner,
introductory, or overlapping parser-table hypotheses. All 627 eligible tables
appear exactly once, and no revised family contains two tables from one
physical page.

This is materially stronger evidence for this document, but it is still a
review-only policy. The `sheet_id N of M` convention and last-table ownership
must be tested on another document before promotion. External evidence is
sealed below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a9_footer_families_v1/
```
