# Task 03A.14: Run the Unified Table Pipeline on Pages 1-600

Status: **completed 2026-07-28; accepted within its first-600-page G3 scope**.

## Abstract

Run the user-reviewed Task 03A.13 table parser on physical Appendix G3 pages
1-600. Preserve the fixed parser parameters and sequential execution, write
restartable per-page artifacts, and validate the large run before considering
the table stage accepted.

This is a production-style validation of the clean code, not a parser-policy
redesign.

## Goal

Confirm that the unified parser completes pages 1-600 without corrupt native
PDF state, missing pages, duplicate table IDs, or incomplete family
assignments. Recheck the ten Task 03A.13 review pages against their accepted
page and table outputs.

## Inputs

- completed Task 03A.13 code and ten-page artifacts
- sealed `deir_appendix_g3` source
- `configs/brisbane_baylands_2025_deir_task03a14_first_600_table_pipeline_v1.json`

## Fixed execution

1. Preserve every Task 03A.13 detection, parsing, cleanup, and family rule.
2. Process exactly physical PDF pages 1-600, sequentially.
3. Reuse completed per-page `result.json` artifacts on restart.
4. Do not run TableFormer, Docling table structure, OCR, a VLM, or LLM repair.
5. Compare the ten embedded review pages with Task 03A.13 using stable page
   fields, table IDs, parser choices, geometry, shapes, cleaned CSV hashes, and
   footer ownership. Family IDs are not compared because the 600-page context
   can legitimately renumber or extend families.

## Outputs

Tracked:

```text
configs/brisbane_baylands_2025_deir_task03a14_first_600_table_pipeline_v1.json
tasks/sprint2/03a14_run_first_600_table_pipeline.md
```

External:

```text
pipelines/brisbane_baylands/task_03a14_first_600_table_pipeline_v1/
  manifest.json
  summary.json
  comparison_to_review_sample.json
  pages/
  tables.jsonl
  family_assignments.jsonl
  table_families.json
```

## Research / learning checkpoint

This task tests the restartable artifact boundary under a materially larger
workload. A large local batch should fail visibly and resume from independently
complete page results rather than relying on an opaque long-lived process.

## Validation

- The configuration admits exactly pages 1-600 and rejects other expanded
  scopes.
- All 600 page results exist once and are ordered.
- Every logical table ID is unique and has exactly one family assignment.
- Page/table regression fields on the ten reviewed pages match Task 03A.13.
- Summarize routes, parser counts, families, wall time, artifact size, and any
  warnings or failures.
- Inspect annotated outputs for representative simple and complex pages,
  including pages 19, 527, and 592.
- Run `make check` and `git diff --check`.

## Acceptance criteria

- The 600-page run completes restartably with no missing pages.
- No native-state corruption like the rejected threaded probe appears.
- Reviewed sample-page extraction remains exact or every mismatch is explicit
  and understood.
- The result remains reviewable; it does not silently become the full
  6,104-page extraction.

## Non-goals

- pages 601-6104
- changing table thresholds or family policy
- wrapped-row repair
- deleting exploratory or failed-probe artifacts
- accepting the broader Task 03A or activating Task 03B

## Outcome

The unified sequential parser completed all 600 physical pages in 1,179.83
seconds (19.66 minutes) and wrote a 983,594,448-byte manifested artifact. All
600 page directories contain a completed `result.json`, with no gaps or
duplicates.

| Measure | Result |
| --- | ---: |
| Physical pages | 600 |
| Simple pages | 592 |
| Complex segmented pages | 8 |
| Logical tables | 681 |
| Stream tables | 590 |
| Lattice tables | 88 |
| Retained Network tables | 3 |
| Proposed families | 103 |
| Footer-owned tables | 582 |

All 681 table IDs are unique and all have exactly one family assignment. The
families comprise four footer runs and 99 singleton tables:

| Footer family | Physical pages |
| --- | ---: |
| `g3_table_family_0022` | 19-272 |
| `g3_table_family_0029` | 273-526 |
| `g3_table_family_0068` | 527-591 |
| `g3_table_family_0103` | 592-600 |

The embedded regression comparison matched all stable fields for the ten
Task 03A.13 review pages, their 89 tables, and footer ownership, with zero
missing keys, extra keys, or field mismatches. Family IDs were intentionally
excluded from that comparison because the larger context renumbers them.

Pages 2 and 4 returned zero tables; visual inspection confirmed that both are
blank. One of four detected ruled regions on page 18 did not receive a Lattice
result. Visual inspection showed that it is the small boxed `60%` input beside
`MERV13`, a detector false positive rather than a missed table. The three
actual page-18 tables all parsed. No Lattice parser return was left unmatched.

Pages 527 and 592 each retained the reviewed 34 ruled tables plus one
borderless Network table. Their annotated images were visually inspected and
their footer-owned table 35 correctly begins the page 527-591 and 592-600
runs, respectively.

The parser repeatedly emitted the source-PDF warning `Resources missing or
invalid from Page id 52567`, which was already observed in earlier G3 runs.
It did not interrupt extraction or create an incomplete page. The top-level
summary now records blank pages, unmatched detector regions, unmatched parser
returns, and restart reuse counts explicitly.

### Provisional lock-in

The user accepted this table-parsing stage on 2026-07-28 as the retained local
implementation. The table inventory changed from the exploratory Stream pass
on 38 pages: eight complex pages gained 78 spatially distinct tables, while
30 simple pages lost one duplicate hypothesis each, for a net change from 633
to 681 tables. Pages 527 and 592 each changed from overlapping whole-page
hypotheses to 34 ruled tables plus one borderless table.

The retained code is intentionally provisional across documents. Before using
it as a corpus-wide contract, test the routing, footer ownership, cleanup, and
family behavior on documents other than Appendix G3. Wrapped-row repair and
the broader Task 03A review remain open.
