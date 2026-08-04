# Task 03G.1a: Remediate Smoke-Discovered Extraction Failures

Status: **provisional and inactive**. Task 03G.1 identified and the user
selected the four bounded improvements below on 2026-08-04. Creating this
contract does not authorize implementation, model or PDF execution, production
identity changes, or a smoke rerun. Revise and explicitly activate it after
Task 03G.1 closes.

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

- the completed diagnostic evidence and eventual outcome from [Task
  03G.1](03g1_smoke_all_model_corpus_sources.md);
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
- a refreshed production `exv1-` identity if maintained production behavior or
  identity-bound inputs change, plus a separate smoke identity decision for
  smoke-only accounting code;
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

## Non-goals

- OCR or raster-form extraction;
- fixing native-text pages that received `no_table_route` for reasons other
  than rotated coordinate mismatch;
- using TableFormer on pages with a non-empty clean-parser result;
- global learned-table parsing or generative repair;
- document-specific thresholds, aliases, or cell corrections;
- rewriting immutable Task 03G.1 smoke artifacts;
- complete extraction of all 35 documents; or
- activating Task 03G.2, Task 03H, Task 04, or committing changes.
