# Task 03G.1a: Remediate Smoke-Discovered Extraction Failures

Status: **complete and accepted as of 2026-08-05**. Task 03G.1 identified and the user
selected the four bounded improvements below, then explicitly activated this
task as one end-to-end remediation. Activation authorizes design,
implementation, no-PDF tests, and the bounded real-PDF/TableFormer regression
needed to prove all four repairs. The user accepted the behavioral and
human-maintainability outcome and authorized this local closure commit on
2026-08-05. A full Task 03G.1 smoke rerun, Task 03G.2 activation, and pushing
remain separate boundaries.

## Abstract

Correct four concrete failure mechanisms exposed by the all-source bounded
smoke: warning counts at the wrong scope, unnormalized rotated-page routing
geometry, credible table regions that yield no canonical Camelot table, and
unlinked cross-page continuations. Keep each repair source-agnostic,
independently reviewable, and conservative. This task may improve maintained
production extraction only after its identity and regression consequences are
specified; it cannot silently repair document-specific content or broaden into
OCR.

## Goal

Turn the smoke's four accepted findings into readable, tested extraction
behavior while preserving raw evidence, existing successful parses, immutable
artifacts, and explicit ambiguity.

## Inputs

- the completed [Task 03G.1](03g1_smoke_all_model_corpus_sources.md) diagnostic,
  immutable smoke candidate
  `smokev1-c88449d823cebdc561216f5058acf9bbd60cec6fa67b2c78ccfe240d20ff597e`;
- the sealed Task 02 source manifest and checksum-pinned PDFs used by the
  smoke;
- maintained warning, native-text routing, clean Camelot table-stage, family,
  and production-identity code;
- Task 03A.5 negative TableFormer boundary evidence and Appendix G3 page 1000
  dense-table collapse evidence; and
- the fixed regression pages named under each work package below.

## Outputs

- one reviewed design specifying warning scopes, coordinate normalization,
  learned-fallback acceptance measurements, continuation evidence, artifact
  roles, and identity impact before implementation;
- four responsibility-owned repairs with focused behavior tests;
- a candidate-neutral fixed-page regression report that distinguishes
  accepted tables, unresolved regions, rejected continuations, and unchanged
  successful baseline outputs;
- explicit refreshed upstream producer (`prv1-`) and downstream production
  (`exv1-`) identity consequences when maintained behavior or identity-bound
  inputs change, starting from production identity
  `exv1-1bd71e02e9f8da505d68bfb58b8dd8d4c1b47aabc8365417028d6daf60c1fcc4`,
  plus a separate `smokev1-` decision for smoke-only accounting code;
- exact commands and retained evidence for any approved real-PDF/model run;
  and
- a recommendation either to rerun Task 03G.1 or to proceed with a smaller
  affected-page regression, without activating Task 03G.2.

## Work package 1: warning scope and accounting

Appendix K2 part 4 carried 6,354 source-manifest warning entries, of which
4,110 strings were unique. The smoke wrapper copied the source-level list onto
each of ten page outcomes and summed those page counts, inflating the source
aggregate to 63,540. The same multiplication appeared repeatedly during the
35-source inspection.

Preserve the raw source warning evidence. Deduplicate exact source-manifest
warning strings and count that set once per source. Attach and count page- or
conversion-local warnings only at their actual scope. Do not suppress,
reinterpret, or repair malformed-stream, resource-repair, or source-authored
warnings. Define summary fields so a reader can reconstruct every aggregate
from its scoped evidence without relying on display-time heuristics.

## Work package 2: rotated-page routing geometry

Appendix K2 part 5 physical pages 2326--2327 are stored with 90-degree PDF
rotation and contain dense native-text spreadsheets, but both received
`no_table_route`. Page and text rectangles were not normalized into one
orientation before coverage measurement: observed text-height coverage was an
impossible 1.386, while width coverage was 0.557 and 0.263 against the 0.70
gate.

Normalize page and native-text geometry into one declared coordinate system
before computing routing coverage. Retain the existing source-independent
thresholds unless reviewed evidence supports a separate policy change. Add
the two pages as positive regressions and add unrotated and non-table pages as
controls so the fix cannot be satisfied by routing every rotated page.

## Work package 3: bounded learned-parser fallback

Run the checksum-pinned accurate TableFormer model only when a credible Heron
table-region crop maps to zero canonical Camelot tables. Fixed positive
evidence includes Appendix C pages 42, 43, 45, 84, and 85; Appendix L page 17;
Appendix H page 2571; Appendix K1 part 3 pages 1394--1397 and 2789; and Appendix
K1 part 4 pages 1278--1281 and 2557. These pages include sparse-rule laboratory
tables and native-text checklists for which routing succeeded but
reconstruction returned zero tables.

Before model execution, freeze acceptance measurements against retained native
text, region geometry, token coverage, observable row/column structure, and
header evidence. An accepted learned result must pass the ordinary cleanup,
family, validation, and artifact contracts. A rejected prediction remains an
explicit unresolved table observation with no canonical cells. Do not invoke
the fallback when Camelot already returned a non-empty result, restore
TableFormer globally, bypass cleanup, or overwrite prior evidence. Preserve
Appendix G3 page 1000 and the Task 03A.5 grouped-header crops as negative
controls.

## Work package 4: cross-page continuation recovery

Define a conservative, source-independent decision for adjacent page
fragments. Fixed evidence includes Appendix F2 pages 14--15 and Appendix G1
pages 1243--1244 and 1245--1246. Appendix K1 part 4 pages 1278--1281 provide a
later multi-page continuation sequence once their page-level tables can be
reconstructed.

Candidate evidence may include a table ending near the bottom of page N, a
headerless fragment beginning near the top of page N+1, compatible column
count and normalized geometry, compatible cell types, and no credible terminal
or new-table marker. Preserve every page artifact and printed header exactly.
Represent an inherited semantic header explicitly as inherited, never as
source-printed content. Column-count or boundary disagreement, including
Appendix F2 page 15, requires reviewed schema or geometry reconciliation;
ambiguous candidates remain separate and diagnosable. Never join tables from
proximity alone or fabricate missing source text.

## Plan / spec requirement

Before implementation:

1. inventory the current warning, router, table-parser, family, schema, and
   identity responsibilities and name the smallest owner for each change;
2. freeze the positive and negative regression manifest with source checksums,
   pages, region identities where applicable, and expected claims;
3. specify TableFormer acceptance measurements and unresolved-region schema
   before running the model;
4. specify continuation acceptance and inherited-header representation before
   changing family assignment;
5. decide which changes refresh production `exv1-`, smoke `smokev1-`, or both,
   without rebinding completed artifacts;
6. name the exact no-PDF tests, real-PDF/model commands, artifact roots,
   expected runtime/storage, and stop conditions; and
7. inspect the contract and design, then obtain explicit approval before
   implementation or any PDF/model run.

Implementation, real-source/model execution, smoke rerun, acceptance, and
commit remain separately reviewable boundaries.

The user's activation authorizes the first three of those boundaries as one
continuous task: finish the reviewed design, implement all four packages, and
run only the bounded affected-page PDF/model regression needed to validate
them. The full smoke rerun, acceptance/closure, and commit remain separate.
Case-level abstention is required when learned output or continuation evidence
is weak, but an all-abstention result does not demonstrate a working repair.
The implementation must recover validated positive cases for both learned
fallback and continuation recovery while preserving negative and ambiguous
controls.

## Research / learning checkpoint

Use maintainers' documentation for PDF rotation semantics, Docling/TableFormer
prediction structure, and the existing Camelot and project family contracts.
Preserve a short explanation of:

- why warning provenance and warning counts require explicit scope;
- why coordinates must be transformed before comparing page coverage;
- why a learned fallback needs an abstention path and cannot be judged only by
  whether it emitted cells; and
- why continuation linking is a logical relationship between immutable
  page-level observations rather than permission to rewrite them.

### Reviewed design frozen before the bounded regression

The checked-in regression manifest is
`configs/brisbane_baylands_2025_deir_task03g1a_regression_v1.json`. It binds
the source checksums, fixed pages, expected warning counts, positive and
negative routing outcomes, learned-fallback recovery gate, and accepted,
rejected, or not-triggered continuation controls. Region identity is the tuple
`(source_sha256, physical_pdf_page, provenance_index, bbox)`; a smoke-local
Docling array pointer is retained as lineage but is not the stable identity.

Responsibility is divided as follows:

- `smoke_extraction/conversion.py`, `source_processing.py`, and `reporting.py`
  own source-, conversion-, and page-scoped warning evidence and aggregation;
- `document_extraction/routing_geometry.py` owns coordinate normalization,
  while `routing.py` owns source-independent classification;
- `table_extraction/learned_fallback.py` is the stable caller facade;
  `tableformer_fallback.py`, `otsl.py`, and the `learned_table_*` modules
  separately own verified model execution, topology, native-text ownership,
  logical cells, acceptance policy, typed results, and page integration;
- `table_extraction/continuations.py` owns adjacent-boundary decisions and
  inherited-header evidence, while `families.py` owns only the resulting
  logical union; and
- the producer and canonical validators own cross-artifact enforcement rather
  than re-deciding any of these policies.

Source warnings remain verbatim in one source-owned record even when every
conversion fails. Exact source strings are counted once per source, conversion warnings once per
conversion, and page warnings once per page; the summary exposes every scoped
subtotal. PDF text rectangles are first transformed from the source canvas
into displayed bottom-left PDF coordinates. A narrow, orientation-independent
dense-partial route then permits a sheet covering at least 35 percent of page
height to omit only the full-page height signal while still requiring every
other strict signal. It cannot route a shorter or otherwise sparse fragment.

The learned fallback triggers per unmatched Heron region, never merely because
a page is interesting and never when Camelot already mapped the region. It
uses the checksum-pinned accurate model, retains the exact crop, native tokens,
raw prediction, measurements, and decision, and requires at least 90 percent
eligible native-text character coverage with no duplicate assignment. Logical
cells retain row and column spans; a rectangular CSV is only a review
derivative. Invalid structure, geometry, token conservation, cleanup, or
canonical validation produces a named abstention with no canonical table.
Success for this task requires validated recovery on at least 9 of the 17
fixed positive pages, while individual regions may still abstain.

Continuation evaluation is restricted to the last table on page N and first
table on adjacent page N+1. Acceptance requires bottom/top proximity,
compatible normalized horizontal and raw-column boundaries, and no caption or
section-header marker above the right fragment. Retained-column type evidence
must also be compatible; explicit missing-value placeholders can continue into
numeric evidence. A new marker hard-rejects the pair; other failed signals are
ambiguous. Accepted inherited-header evidence names the source table but marks
the projected content unresolved. It hashes the existing leading-row heuristic
only as a diagnostic pointer, never labels those possibly body-like rows as a
printed header, inserts header text into target cells, or changes either page
artifact.

The maintained geometry, learned fallback, and continuation modules change
producer behavior and therefore require a fresh `prv1-` and downstream
production `exv1-` recipe before any new complete-document publication.
Span-aware canonical representation also changes the canonical schema digest.
The warning-accounting repair is smoke-only, but any future smoke run binds the
new production identity plus the changed smoke-owned code and therefore gets a
fresh `smokev1-`. Existing producer, canonical, and smoke artifacts remain
immutable.

This design follows the maintained Docling distinction between the more
accurate TableFormer mode and native-cell matching in its
[pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/)
and [model catalog](https://docling-project.github.io/docling/usage/model_catalog/).
Docling's [advanced options](https://docling-project.github.io/docling/usage/advanced_options/)
support bounded page processing, while the pinned
[docling-ibm-models implementation](https://github.com/docling-project/docling-ibm-models)
is the authoritative prediction structure. The geometry adapter is isolated
because [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) exposes PDFium
page and text geometry without imposing this project's routing coordinate
contract.

## Implementation and bounded-regression outcome

All four work packages now have maintained owners and behavior tests. The
candidate-neutral retained report is under
`pipelines/brisbane_baylands/task_03g1a_remediation_v1/` and was initially
sealed by `artifact_inventory.json` plus completion-last `completion.json`.
During user review, an overlay of one `invalid_otsl` abstention exposed that
TableFormer's `num_cols` is the count of post-processed matched columns after
gap compression, not necessarily the original OTSL grid width. The v1 report
and its `task_03g1a_remediation_final_v1/` pointer are therefore superseded
diagnostic evidence, not the accepted interpretation.

The behavioral MVP reevaluation is retained immutably under
`pipelines/brisbane_baylands/task_03g1a_remediation_v5/`. It reconstructs the
rectangular grid from the original OTSL sequence, maps source tokens through
the uncompressed `docling_responses` evidence, and uses the original predicted
cell boxes. A declared 3-pixel maximum crop overshoot absorbs only bounded
model/render rounding (the fixed set's maximum was 2.544 pixels); larger or
non-monotonic geometry still abstains. Unmatched native tokens are recovered
only when their centers fall within exactly one predicted cell, and any
remaining printed leading/header text forces abstention rather than a
headerless table. A clipped top-edge line wholly above the predicted structural
grid remains retained as crop-fringe evidence but is excluded from table-cell
coverage. The v2 through v4 reruns remain immutable, non-normative development
evidence; v3 exposed the missing-header acceptance gap and v4 exposed the
crop-fringe distinction.

The human-maintainability rewrite is retained under
`pipelines/brisbane_baylands/task_03g1a_remediation_v7/`, which is now the
normative bounded regression pending user acceptance. The stable
`learned_fallback.py` facade delegates to separate OTSL, native-text ownership,
cell construction, acceptance-policy, page-integration, and model-execution
owners. Warning accounting, routing geometry, continuation decisions, family
union, producer validation, and canonical span projection also have named
owners. The refactor gate caps learned modules at 350 lines and functions at 80
lines, requires every runtime owner in production identity, and keeps behavior
tests at the public facade. Exact replay matched all 35 v5 fallback attempts,
including cells and measurements, and every persisted continuation decision.
A first fresh refactor run under v6 safely abstained when the model adapter
returned Docling's stage wrapper instead of its low-level predictor; v6 remains
immutable failure-path evidence. The corrected adapter validates its predictor
interface, and the fresh v7 model run exactly reproduces v5 behavior.

- Warning scope: K2 part 4 retains all 6,354 raw entries and 4,110 exact unique
  strings. The prior ten-page multiplication was 63,540 entries; the new
  source-scoped contribution is 4,110, while conversion/page warnings remain
  separate.
- Routing: K2 part 5 page 2326 passes the normalized strict route; page 2327
  passes the declared dense-partial route. Unrotated page 1 preserves its
  Heron `layout_regions` route and blank rotated page 2328 remains
  `no_table_route`.
- Learned fallback: all 35 unmatched Heron regions were rerun on all 17 fixed
  positive pages. Twenty-six regions were accepted, recovering validated
  tables on 14 pages and exceeding the frozen `>=9` gate. Nine regions abstain:
  seven `unmatched_leading_text`, one
  `native_text_coverage_below_threshold`, and one
  `non_monotonic_grid_geometry`. No `invalid_otsl` abstentions remain. G3 page
  1000 retained its `camelot_stream` 183-by-34 table with zero fallback
  attempts.
- Continuations: F2 14--15, G1 1243--1244, and G1 1245--1246 accept; the
  geometry-compatible G1 1244--1245 boundary hard-rejects its new-section
  marker. Newly reconstructed K1 part 3 pages add one valid 1396--1397
  continuation; 1394--1395 and 1395--1396 remain ambiguous. K1 part 4
  1278--1279 is no longer evaluable because all page-1278 learned candidates
  abstain; 1279--1280 and 1280--1281 remain ambiguous because their raw column
  geometry and types disagree. Page artifacts remain unchanged and inherited
  content is explicitly unresolved rather than fabricated.

The production identity recipe advances from
`exv1-1bd71e02e9f8da505d68bfb58b8dd8d4c1b47aabc8365417028d6daf60c1fcc4`
to `exv1-a0908c8fad342acde9d195a4223391bef29884cea1711c66d611f13fa995adee`.
It binds the enabled fallback policy, dense-partial threshold, continuation
policy/modules, original-grid OTSL interpretation, unique-cell native-token
recovery, leading/header completeness, 3-pixel bbox tolerance, span-aware
canonical schema, and changed code. Future producer runs therefore derive
fresh per-source `prv1-` identities. No producer or canonical candidate was
executed or rebound. The old smoke spec still pins the old production identity,
so a future Task 03G.1 rerun must first receive a new spec/`smokev1-`; this task
did not run or mutate the smoke.

The bounded commands were:

```bash
# Set CONFIGURATION_JSON and ARTIFACT_ROOT to one of the six exact retained
# pairs listed in task_03g1a_remediation_v7/commands.json, then run:
uv run python -c "from pathlib import Path; from er_commons.settings import load_settings; from er_commons.table_extraction.pipeline import run_table_extraction; root=load_settings().data_root; run_table_extraction(root, Path('$CONFIGURATION_JSON'), artifact_root_override=Path('$ARTIFACT_ROOT'))"

make validate-extraction-contract
make check
git diff --check
```

`task_03g1a_remediation_v7/commands.json` retains the exact five positive
configuration paths, the G3 negative-control configuration, and validation
commands; each configuration is the copied byte-level input to its table-stage
run.

The full 35-source smoke rerun and Task 03G.2 remain unexecuted. The user
accepted and closed Task 03G.1a on 2026-08-05; Task 03G.2 has its own separate
preparation and PDF-execution authorization boundaries.

## Review pass

- **Evidence:** every positive and negative page is checksum-bound and each
  expected claim is explicit.
- **Precision:** fallback and continuation logic can abstain; ambiguous output
  is never silently promoted.
- **Regression:** existing non-empty Camelot tables, unrotated routing, family
  assignments, and page artifacts remain unchanged unless a reviewed contract
  explicitly requires a change.
- **Identity:** maintained behavior changes receive a fresh identity recipe;
  completed smoke and production artifacts remain immutable.
- **Maintainability:** warning scope, geometry normalization, fallback
  selection/acceptance, and continuation decisions have separate named owners
  and behavior-focused tests.
- **Boundary:** no OCR, generative repair, document-specific exception, global
  TableFormer restoration, or proximity-only merge enters this task.

## Validation

- Recompute warning aggregates from raw scoped evidence and prove the K2 part
  4 source list is counted once rather than once per sampled page.
- Prove K2 part 5 pages 2326--2327 route using normalized geometry and that
  fixed unrotated/non-table controls do not regress.
- For every learned-fallback region, retain the trigger, prediction,
  measurements, acceptance or abstention decision, and canonical validation
  result.
- Prove a non-empty Camelot result never enters or is replaced by the fallback.
- Evaluate accepted, rejected, and ambiguous continuation boundaries and prove
  inherited headers are marked rather than fabricated.
- Verify artifact inventories, checksums, no-clobber publication, and identity
  bindings for every new candidate-neutral or production artifact.
- Run targeted tests, then:

```bash
make validate-extraction-contract
make check
git diff --check
```

The final human-maintainability candidate passed the v1.1 extraction-contract
validator, Ruff formatting and linting, mypy over 240 source files, all 453
project tests, and `git diff --check`. Its six nested inventories and aggregate
363-file inventory verify, and completion was written last. These results prove
implementation and bounded-regression readiness. The user subsequently
accepted the outcome on 2026-08-05. No full smoke rerun or Task 03G.2 execution
is implied.

## Acceptance criteria

- Warning totals are scope-correct and every raw warning remains recoverable.
- Rotated-page coverage is geometrically valid and the two fixed K2 pages no
  longer fail routing because of orientation mismatch.
- Zero-output credible regions either produce validated canonical tables or
  explicit unresolved observations; no weak learned output is silently
  accepted.
- Accepted continuation links preserve page evidence and meet the frozen
  multi-signal rule; ambiguous boundaries remain separate.
- Positive and negative regressions pass, identity handling is explicit, and
  the user accepts the outcome before any Task 03G.1 rerun or Task 03G.2
  activation.

## Closure outcome

All four remediation packages and the separate human-maintainability gate are
accepted. The immutable v7 bounded regression is the normative task evidence;
v5 remains behavioral-reference evidence and v6 remains retained safe-failure
evidence. The accepted non-executed production recipe is
`exv1-a0908c8fad342acde9d195a4223391bef29884cea1711c66d611f13fa995adee`.
Task 03G.1a publishes no complete-document or corpus candidate and does not
itself activate Task 03G.2. The user subsequently reviewed and activated Task
03G.2 for its separate no-PDF preparation pass on 2026-08-05.

## Non-goals

- OCR or raster-form extraction;
- fixing native-text pages that received `no_table_route` for reasons other
  than rotated coordinate mismatch;
- using TableFormer on pages with a non-empty clean-parser result;
- global learned-table parsing or generative repair;
- document-specific thresholds, aliases, or cell corrections;
- rewriting immutable Task 03G.1 smoke artifacts;
- complete extraction of all 35 documents; or
- activating Task 03G.2, Task 03H, or Task 04; or pushing the local closure
  commit.
