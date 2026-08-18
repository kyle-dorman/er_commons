# Task 03G.2a: Remediate Main-Report Table Boundaries

Status: **implementation and execution validation complete as of 2026-08-05**.
The first fresh Task 03G.2 main-report attempt exposed one deterministic
table-family invariant failure. The user reviewed the three conflicting
boundaries, authorized this bounded repair, and directed the fresh three-source
scope to continue after a successful main-report restart. The refreshed main
baseline completed and sealed, proving this repair. A separate downstream
document-index/canonical failure is recorded in proposed [Task
03G.2b](03g2b_preserve_document_index_text.md).

## Abstract

Correct the source-independent boundary semantics exposed by the failed
`deir_main` baseline producer. A separately captioned table must remain split,
a genuine repeated-header continuation may tolerate the narrowly observed
bottom gap, and a repeated header-only edge fragment must remain diagnostic
evidence rather than an ordinary logical table. Preserve both failed attempts
and refresh the code-bound pilot identity before restarting the full scope.

## Goal

Make continuation decisions, logical-table materialization, and family
assignment agree on the three observed regimes without page IDs, source IDs,
or silent content correction.

## Inputs

- retained failed producer `prv1-22f794115a1a558fb4b791c7127959ef1c897c693e3c130fb9ffe5e4269577d5`;
- reviewed main-report boundaries 1059--1060, 1499--1500, and 1723--1724;
- Task 03G.1a continuation and inherited-header policy;
- maintained page, continuation, family, producer-validation, and identity code; and
- active [Task 03G.2](03g2_run_three_document_full_pilot.md).

## Outputs

- terminal continuation decisions that override older footer/header family heuristics;
- a corroborated repeated-header continuation rule that relaxes only the
  narrowly missed left-bottom threshold while retaining every other signal;
- explicit retained evidence for repeated header-only edge fragments, excluded
  from logical tables, family assignments, and canonical input;
- focused synthetic and retained-artifact offline regressions for all three
  main-report boundaries;
- refreshed Task 03G.2 production, scope, transaction, and producer identities; and
- a fresh full-scope invocation that restarts `deir_main` and continues through
  Appendix D, Appendix P, stage two, handoff validation, and checksum reuse if
  every preceding stage succeeds.

## Design

1. A right-page structural marker remains a hard rejection. Rejected and
   ambiguous table pairs block footer and exact-header family unions.
2. An otherwise passing pair may waive only `left_table_not_at_page_bottom`
   when exact non-empty headers match, both sides contain body rows, and the
   observed left-bottom fraction is at most 0.22. Right-edge placement, span,
   raw columns, column boundaries, and retained types must still pass.
3. A repeated header-only fragment is recognized only when the right page has
   one candidate whose cleaned rows are exactly its non-empty header matrix,
   the left edge table has body rows with the same header, no new marker exists,
   and edge geometry is compatible. Preserve the page-local parser artifacts
   and an explicit fragment record, but exclude that candidate from logical
   table/family/canonical views.
4. Existing failed attempts are immutable. Changed code must produce a new
   Task 03G.2 identity; no old attempt directory is deleted or resumed.

## Research / learning checkpoint

The failure was cross-layer disagreement, not proof that every merge was
wrong. Family heuristics cannot independently override an explicit boundary
decision. Repeated headers are strong corroboration but not identity by
themselves, while a header with no body rows is evidence about a continuation,
not a second data table.

## Plan

1. Implement pure boundary and fragment-classification seams.
2. Add behavior tests for hard split, corroborated continuation, threshold
   bounds, header-only suppression, family authority, and artifact accounting.
3. Re-evaluate the retained failed artifacts without PDF/model execution.
4. Run focused tests, `make validate-extraction-contract`, `make check`, and
   `git diff --check`.
5. Refresh Task 03G.2 identity and repeat execution preflight.
6. Run the full scope. Stop on any new real contract failure; otherwise validate
   the handoff, produce the required pilot report/request, and run one identical
   checksum-reuse invocation.

## Validation

- the 1059--1060 pair is rejected and placed in distinct families;
- the 1499--1500 pair is accepted and placed in one continuation family;
- page 1724 contributes a retained header-only fragment but zero logical tables;
- every other retained main continuation changes only when explained by the
  generic rules above;
- producer and corpus contracts pass; and
- the refreshed main document covers all 2,092 physical pages before the scope
  may advance.

## Acceptance criteria

- no document-specific exception or historical Appendix P lineage is added;
- the failed main evidence remains immutable;
- the refreshed main document completes before Appendix D or Appendix P starts;
- all three documents and stage two validate before reuse; and
- one identical scope invocation proves checksum reuse without reconstruction.

## Non-goals

- changing unrelated table detection or parser thresholds;
- deleting failed attempts or temporary producer evidence;
- generated review renders, OCR, or manual table correction;
- running sources outside the Task 03G.2 three-document scope; or
- activating Task 03H or accepting the extraction release.

## Outcome

- Retained-artifact comparison preserved the 1059--1060 split, merged the
  1499--1500 continuation, projected page 1724's header-only fragment to zero
  logical tables, and found no unexplained continuation changes.
- Focused tests, the extraction contract, the 487-test project check, strict
  typing, lint, and diff validation passed.
- Refreshed production identity
  `exv1-749dd82e63cad206a72ad5e32652e107b3ba858c574226fd5b03bdcd6d4e4d08`
  passed exact three-source source/model preflight with no historical or
  bounded authorization.
- Fresh main baseline producer
  `prv1-9fcd49227703767d60d26ebdcf699f60aa7d44b745e022c396364b01fd250be6`
  covered all 2,092 pages and sealed successfully at the boundary that had
  failed before. Its fresh hierarchy producer also completed and sealed.
- Canonical materialization then exposed the distinct Task 03G.2b failure.
  Appendix D and Appendix P have no completed result from this invocation.
