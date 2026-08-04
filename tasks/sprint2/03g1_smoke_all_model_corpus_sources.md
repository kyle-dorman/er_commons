# Task 03G.1: Smoke All Model-Corpus PDFs on Bounded Pages

Status: **provisional and inactive**. This task is the next Task 03G execution
subtask, but the docs revision does not authorize its implementation or PDF
run. Activate it explicitly before work begins.

## Abstract

Run a fresh diagnostic smoke on at most ten deterministic physical pages from
each of the 35 checksum-pinned model-corpus PDFs. Reuse the maintained source
verification, Docling conversion, routing, and table-stage components where
their contracts admit bounded pages. Add only the thinnest diagnostic wrapper
needed to express the frozen selection honestly. Publish a smoke summary and
per-source diagnostic artifacts, never complete-document or corpus candidates.

## Goal

Find basic source, parser, routing, table-stage, warning, runtime, or resource
problems across the full variety of the model corpus before paying for complete
documents.

## Inputs

- the revised [Task 03G umbrella](03g_run_representative_extraction_pilot.md);
- the sealed Task 02 source manifest filtered to its ordered 35
  `model_corpus` records;
- current source verification and partial-page selection models under
  `er_commons.document_extraction`;
- maintained Docling conversion, page routing, and clean table-stage
  components; and
- a new smoke-only artifact namespace under the external data root.

## Frozen page-selection rule

For a source with `N` physical PDF pages:

- if `N <= 10`, select every page;
- otherwise select physical pages 1--3, four consecutive pages centered in the
  document, and the final three pages. The centered range begins at
  `floor((N - 4) / 2) + 1`.

This corpus-wide rule covers front, middle, and end regimes without per-file
hand selection and requires at most three contiguous conversion calls per PDF.
It selects 342 pages across the current 35-source manifest because Appendix K4
has four pages and Appendix N1 has eight. Freeze the ordered
`(source_id, physical_page)` list and its checksum before execution.

## Outputs

- one checked-in smoke specification containing the source-selection rule,
  exact ordered source IDs, resolved page lists, configuration, artifact root,
  and resource settings;
- a fresh smoke-run identity distinct from production `docv1-`, `scopev1-`,
  `idxv1-`, `resv1-`, and handoff namespaces;
- for every selected source/page: source identity, conversion status, parser
  records needed to inspect the bounded result, routing outcome, table-stage
  outcome when routed, warnings, and retained error context;
- aggregate counts by source, conversion status, route, tables, warnings, and
  errors;
- per-source and aggregate wall time, observed peak memory where the maintained
  process boundary exposes it, and retained artifact bytes;
- a short outcome that either accepts the smoke or names the first concrete
  remediation Task 03G.x; and
- no render files and no Task 04 review record.

`diagnostic_complete` means only that every requested page has an explicit
outcome. Partial table families and other fragment-level observations must be
marked diagnostic and cannot claim complete-document semantics.

## Plan / spec requirement

Before execution:

1. inventory the current partial-page components and name the smallest wrapper
   needed to call them without weakening complete-document validators;
2. freeze the exact 35-source page list from the formula above;
3. freeze one shared parser/routing/table policy and bounded resource settings;
4. name the exact command, artifact roles, expected runtime/storage, and stop
   conditions;
5. decide whether smoke-only code/configuration is outside production identity
   or requires an identity refresh, and record why; and
6. inspect the spec/diff, then obtain explicit approval before the first PDF
   runs.

Do not add partial-page modes to `extraction run-document` or relax its complete
page-accounting publication gate. A diagnostic command may share maintained
components, but it must publish only smoke artifacts.

## Research / learning checkpoint

Explain why deterministic spread sampling provides broader format coverage than
the first ten pages while remaining simple and reproducible. Explain why a
partial-page diagnostic cannot satisfy a complete-document contract even when
every sampled page succeeds.

## Review pass

- **Selection:** all and only the 35 ordered model-corpus sources appear; every
  resolved page follows the frozen formula and is within the manifest count.
- **Freshness:** the smoke performs new conversion work and does not import an
  old Appendix P or Task 03F candidate as its result.
- **Boundary:** no smoke path writes a complete-document completion, corpus
  accounting, target index, resolution, or handoff.
- **Breadth:** aggregate results retain source IDs and warnings so one bad PDF
  cannot disappear inside totals.
- **POC restraint:** implementation is thin and diagnostic; no speculative
  failure injection, scheduler, database, or generalized workflow engine is
  added.

## Validation

- Verify every selected source checksum and page count against the sealed
  manifest.
- Recompute the exact page list and selection checksum independently.
- Confirm every requested page has one explicit terminal diagnostic outcome.
- Validate table records and assets for pages routed to the table stage.
- Recompute aggregate counts and artifact bytes from per-page/source evidence.
- Confirm no complete-document or stage-two completion artifact exists in the
  smoke namespace.
- Run:

```bash
make validate-extraction-contract
make check
git diff --check
```

## Closure criteria

The subtask is complete when every requested page has an explicit result and
the summary identifies any concrete failures. A failure may close the smoke as
an experiment, but Task 03G.2 remains inactive until the user accepts the smoke
or the required remediation/rerun.

## Non-goals

- complete-document extraction, canonical materialization, or publication;
- corpus target indexing or cross-document resolution;
- proving hierarchy, semantic, or cross-reference sufficiency;
- simulated failures or recovery testing;
- separate human acceptance of each source;
- generated review renders; or
- activating Task 03G.2, Task 03H, or Task 04.
