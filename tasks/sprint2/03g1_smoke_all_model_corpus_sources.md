# Task 03G.1: Smoke All Model-Corpus PDFs on Bounded Pages

Status: **complete and accepted as an MVP diagnostic as of 2026-08-04**. The
bounded smoke, one-source-at-a-time inspection, remediation handoff, and
human-maintainability rewrite are complete. No complete-document or corpus
candidate was published.

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

## Frozen pre-execution specification

The checked-in
`configs/brisbane_baylands_2025_deir_task03g1_smoke_v1.json` is the executable
smoke specification. Static reconciliation against the sealed manifest metadata
resolved all and only the 35 ordered `model_corpus` sources, 342 selected pages,
and ordered-pair RFC 8785 SHA-256
`b2b9dc65c61c4b69d88076bbb6ec93f66261dea61fc50faf9184f129658136f0`.
This reconciliation read the source manifest and its completion seal only; it
did not hash, open, inspect, or convert any PDF.

The wrapper reuses the maintained offline Heron/PyPdfium2 converter, native-text
router, and clean Camelot table stage with the accepted Task 03C thresholds.
It runs one source at a time, gives Docling four CPU threads, disables table
review derivatives, and requires 20 GiB free before starting each source. A
source-local failure is retained and the smoke continues; a low-disk stop marks
every remaining requested page explicitly as not run. No scheduler, database,
parallel source pool, OCR, TableFormer, or generative repair is introduced.

The exact future command is:

```bash
uv run python -m er_commons.smoke_extraction \
  --spec configs/brisbane_baylands_2025_deir_task03g1_smoke_v1.json
```

That command is the PDF boundary and must not run before the user approves it.
It will first verify source bytes and page counts, then write a fresh
`smokev1-` directory below
`pipelines/brisbane_baylands/task_03g1_model_corpus_smoke/`. Each selected page
will receive a terminal diagnostic outcome backed by bounded Docling records,
routing evidence, and table-stage evidence when routed. The terminal summary is
named `diagnostic_summary.json`; forbidden complete-document, accounting,
target-index, resolution, and handoff completion names are checked absent.
Interrupted invocations remain below `attempts/<attempt-id>/`; rerunning the
same command allocates a fresh attempt until one diagnostic-complete summary is
published no-clobber at the `smokev1-` root.

The planning range is one to six wall-clock hours and 100 MiB to 5 GiB retained.
These are operational estimates, not acceptance limits; the breadth run spans
342 heterogeneous pages in 99 conversion calls, and routed table pages
dominate the uncertainty. Peak RSS is observed at the maintained in-process
conversion seam. The run stops before a new source if free space falls below
20 GiB and otherwise continues through source-local failures so all requested
pages receive explicit outcomes.

The new package and module entrypoint are diagnostic-only and are unreachable
from `extraction run-document` and `extraction run-scope`, so they do not
refresh the production `exv1-` identity. Instead, `smokev1-` binds the
checked-in spec, the current production extraction identity, and checksums of
the smoke-owned code. Changing maintained production inputs must first change
the bound production identity; changing smoke policy or wrapper code changes
only `smokev1-`.

## Research / learning checkpoint

Explain why deterministic spread sampling provides broader format coverage than
the first ten pages while remaining simple and reproducible. Explain why a
partial-page diagnostic cannot satisfy a complete-document contract even when
every sampled page succeeds.

The spread rule samples front matter, a centered interior run, and document-end
material under one source-independent formula. It therefore covers more likely
format regimes than the first ten pages while remaining deterministic and easy
to audit. Success still says nothing about unsampled pages, complete page
accounting, cross-page table families outside the fragments, or completion-last
publication, so it cannot satisfy a complete-document contract.

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

## Activation history

The user explicitly activated Task 03G.1 on 2026-08-04 and asked to begin the
task while checking in before any PDF run. Activation authorizes the frozen
smoke specification, diagnostic-only implementation, tests, documentation,
and no-PDF validation. The user separately authorized and monitored the PDF
run, then accepted the diagnostic at MVP level and authorized the
human-maintainability rewrite. Those historical approvals do not activate Task
03G.1a, Task 03G.2, Task 03H, or Task 04.

## Inspection handoff

The user completed one-document-at-a-time inspection of all 35 smoke sources
and selected four improvements: warning scope/accounting, rotated-page routing
geometry, a bounded learned-parser fallback for credible regions with zero
Camelot output, and conservative cross-page continuation recovery. Provisional
[Task 03G.1a](03g1a_remediate_smoke_extraction_failures.md) now owns the full
evidence, regression pages, boundaries, design requirements, and future
acceptance criteria.

This handoff removes remediation implementation from Task 03G.1 without
discarding its findings. The accepted closure leaves Task 03G.1a inactive;
implementation, model/PDF execution, identity changes, smoke rerun, acceptance,
and commit remain separately authorized boundaries.

## Human-maintainability gate

The user accepted the smoke behavior at MVP level on 2026-08-04 but rejected
the diagnostic wrapper as code a human should maintain. Task 03G.1 cannot close
until the wrapper is maintainable, testable, debuggable, understandable, and
editable.

The rewrite must preserve the accepted diagnostic behavior while replacing the
monolithic workflow with named responsibility owners for external services,
bounded source/page processing, routing, summaries and terminal validation,
identity evidence, and publication. `run_smoke` remains the short application
facade. Behavior-focused no-PDF tests must exercise success, source-local
failure, range-accounting rejection, routed-table omission, resource stop,
forbidden publication detection, and summary construction without relying on
private workflow internals.

The smoke configuration must bind every runtime module introduced by the
rewrite. The resulting code-bundle change produces a fresh `smokev1-` identity
if the command is invoked again; it does not change the maintained production
`exv1-` identity or mutate the completed MVP smoke. A real-PDF run, smoke rerun,
Task 03G.1 acceptance, and commit remain separate user decisions.

### Rewrite candidate

The candidate replaces the 442-line multi-responsibility workflow with a short
application shell and separate owners for services, routing, bounded source
processing, typed internal records, reporting/terminal validation, and
identity/publication. Tests consume the named owners rather than importing
private workflow helpers. The checked-in spec now binds the public facade and
all runtime modules, so the rewrite changes only future `smokev1-` identity.

No PDF or model ran during the rewrite. Eight focused no-PDF behavior tests
and four objective maintainability gates pass, including exact
selection/manifest reconciliation, source-local conversion
failure, range over-return rejection, missing table outcome, low-disk terminal
accounting, forbidden production-artifact detection, truthful table-request
paths, absence of review renders, a short application shell, bounded ownership
units, public test seams, and complete runtime identity coverage. The v1.1
extraction-contract validator and the complete 408-test project check pass,
including strict mypy, Ruff, and formatting gates. A read-only preservation
check rebuilt all 35 source summaries and the aggregate summary from the
immutable MVP's 342 retained page outcomes; every stable field matched exactly.
The user accepted the quality threshold for closure.

## Outcome

Task 03G.1 is complete and accepted as a bounded MVP diagnostic. Fresh smoke
`smokev1-c88449d823cebdc561216f5058acf9bbd60cec6fa67b2c78ccfe240d20ff597e`
retained one terminal outcome for all 342 deterministic pages across all 35
model-corpus PDFs. All conversions completed: 206 pages were `complete` and
136 were `complete_with_warnings`; no page or source error occurred. Routing
sent 8 pages through `full_page_numeric`, 87 through `layout_regions`, and 247
through `no_table_route`. The clean table stage completed for all 95 routed
pages and emitted 87 logical tables.

The run took 892.85 wall seconds, observed approximately 3.78 GB peak RSS, and
retained approximately 1.13 GB before its terminal inventory and summary. Its
reported 63,959 warning entries are not a trustworthy source-warning count:
the smoke copied source-level warnings onto each sampled page and summed them.
Raw warning evidence remains preserved, and scope-correct warning accounting
is explicitly owned by provisional Task 03G.1a rather than retroactively
rewriting the immutable smoke.

The user inspected all 35 sources one document at a time and selected four
material improvements for [Task
03G.1a](03g1a_remediate_smoke_extraction_failures.md): warning
scope/accounting, rotated-page routing geometry, a bounded learned-parser
fallback for credible regions with zero Camelot output, and conservative
cross-page continuation recovery. Raster-form OCR and other unselected parser
expansions remain outside that contract.

The first wrapper was behaviorally sufficient but failed the separate
human-maintainability gate. The accepted rewrite replaces its 442-line
multi-responsibility workflow with a 133-line application shell and named
service, routing, source-processing, record, reporting, and publication owners.
Eight no-PDF behavior tests and four objective maintainability tests pass. A
read-only preservation check reconstructed all 35 source summaries and the
aggregate summary from the immutable 342 page outcomes with exact equality on
every stable field. The rewrite changes only future `smokev1-` identity; it
does not change production `exv1-`, rerun PDFs, or mutate the accepted smoke.

Final validation passed:

```text
make validate-extraction-contract
  restartable_extraction_contract_v1_1=valid
make check
  Ruff format and lint: passed
  strict mypy: 226 source files passed
  pytest: 408 passed
git diff --check
  passed
```

The next decision is whether to revise and activate provisional Task 03G.1a.
Task 03G.2 remains inactive until the required remediation is accepted.
