# Task 03G.2: Prepare and Run the Fresh Three-Document Full Pilot

Status: **active for no-PDF preparation only**. The user approved a completely
fresh configuration and downstream chain for the main Draft EIR, Appendix D,
and Appendix P on 2026-08-05. Do not verify source PDF bytes, open or convert a
PDF, run Docling/Camelot/TableFormer, or invoke the pilot until the preparation
diff and production-shaped preflight are reviewed and the user separately
approves PDF execution.

## Abstract

Prepare, then separately run, the maintained complete two-stage workflow on
exactly three full model-corpus PDFs. Every source receives fresh
source-specialized configuration and every content owner builds a new
downstream candidate. Appendix P's historical producers, canonical records,
hierarchy correction, semantic candidate, cross-reference candidate, document
candidate, and bounded authorization remain immutable evidence and are not
inputs to this pilot.

The first invocation must construct the pilot in a new namespace. After that
fresh result is accepted, one identical invocation verifies checksum reuse.
One shared automatic contract and one aggregate anomaly summary replace
separate per-document human acceptance records.

## Goal

Show that the POC can build three complete immutable document candidates from
sealed source PDFs, derive exact pilot accounting, a sealed target/alias index,
immutable cross-document resolutions, and a non-authoritative handoff without
borrowing any completed Appendix P content lineage.

## Frozen source scope

In sealed-manifest order:

1. `deir_main` — Complete 2025 Baylands Specific Plan Draft EIR, SHA-256
   `0b81e84176c86205c07d9ae6b2a9994fcd45405e516546bcfc7ab9b1f88cf83f`,
   65,818,524 bytes, 2,092 pages;
2. `deir_appendix_d` — Biological Resources Technical Report, SHA-256
   `0e0d0dc3d5c9d75ca52ec698f3943da59e560e69dde8dfa4763c9afd6673e1c3`,
   62,423,471 bytes, 356 pages; and
3. `deir_appendix_p` — Water Supply Assessment, SHA-256
   `2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1`,
   6,528,561 bytes, 222 pages.

Preparation may read the sealed manifest records that carry these values, but
the execution gate owns local source-file checksum and page-count verification.
The exact pilot total is 2,670 physical pages.

## Fresh configuration and lineage contract

The preparation pass must add one document run spec, one scope run spec, and a
fresh source-specialized six-owner plan for each of the three sources. Use the
following stable filename stem:

```text
configs/brisbane_baylands_2025_deir_task03g2_<source>_<owner>_v1.json
```

where `<source>` is `main`, `appendix_d`, or `appendix_p`, and `<owner>` is
`baseline_producer`, `hierarchy_producer`, `canonical`,
`hierarchy_correction`, `semantic`, or `cross_references`. The document and
scope specs use:

```text
configs/brisbane_baylands_2025_deir_task03g2_document_v1.json
configs/brisbane_baylands_2025_deir_task03g2_scope_v1.json
```

Do not create these configs against the current loaders. First implement and
test a fresh-lineage configuration boundary that separates reviewed static
policy from runtime-derived upstream references:

- baseline and hierarchy producer IDs are derivable before PDF conversion from
  the source seal, reviewed configuration, models, packages, and code;
- canonical configuration binds the newly predicted baseline producer ID;
- hierarchy-correction configuration binds the newly predicted hierarchy
  producer ID and selects `machine_validation` with no bounded-acceptance path;
- semantic runtime lineage is derived only after the fresh canonical and
  hierarchy-correction candidates publish, and binds their exact IDs,
  completion records, inventories, plus the two fresh producer IDs;
- cross-reference runtime lineage is derived only after the fresh semantic
  candidate publishes, and binds its exact ID, completion, and inventory; and
- the final `docv1-`, accounting, index, resolution, and handoff identities are
  derived from the newly sealed stage outputs, never predicted by copying an
  Appendix P identifier.

The semantic plan must use `strict_quality_gate`. It must not carry Appendix
P's historical expected counts as acceptance evidence. Shared structural
invariants are authoritative; observed source-qualified counts belong in pilot
observations and the aggregate anomaly summary.

All 18 source/owner plans and their referenced policy bytes enter the new
pilot production identity. The identity and run-spec scope are exactly the
three selected sources, not a claim that all 35 model-corpus documents were
configured or executed. Refreshing the identity must not rewrite the accepted
post-03G.1a recipe or any historical candidate.

## Artifact namespace and resources

Use only these new task-owned external roots:

```text
pipelines/brisbane_baylands/task_03g2_document_producers/
pipelines/brisbane_baylands/task_03g2_canonical_records/
pipelines/brisbane_baylands/task_03g2_hierarchy_correction/
pipelines/brisbane_baylands/task_03g2_representative_pilot/
pipelines/brisbane_baylands/review_cache/<fresh-candidate-id>/
```

The first four roots must not contain a completed candidate selected by the
pilot before its first invocation. Candidate-neutral review artifacts remain
outside all candidate identities.

Freeze this resource policy:

```json
{
  "document_concurrency": 1,
  "page_batch_size": 4,
  "stage_batch_size": 4,
  "queue_capacity": 100,
  "cpu_threads_per_document": 4,
  "device": "cpu",
  "memory_estimate_bytes": 17179869184,
  "storage_estimate_bytes": 107374182400,
  "docling_timeout_seconds": null,
  "outer_process_deadline_seconds": 86400,
  "cancellation_grace_seconds": 15,
  "retry_limit": 1
}
```

Concurrency one is a deliberate POC setting: the current scope runner is
sequential, it keeps peak resource use bounded, and Task 03G.2 is not a
throughput experiment.

## Inputs

- accepted Tasks 03G.1 and 03G.1a;
- the sealed Brisbane source manifest and completion record;
- the non-executed post-03G.1a recipe as predecessor policy evidence;
- maintained content-owner implementations and complete two-stage interfaces;
- the common canonical, hierarchy, semantic, cross-reference, target-index,
  and corpus-resolution contracts; and
- candidate-neutral comparison and render-request support.

## Outputs

### No-PDF preparation

- a fresh-lineage configuration implementation and focused offline tests;
- 18 source-specialized owner plans, the exact three-source document/scope
  specs, a sealed three-document corpus catalog, and real target/resolution
  policy digests;
- a new non-executed pilot production identity and exact config checksums;
- a read-only freshness report proving no selected completed candidate exists
  in the task-owned roots and no config names a historical Appendix P ID or
  bounded authorization;
- a production-shaped static preflight that validates the fresh templates,
  config joins, resources, and empty task namespace without source PDF access;
  the two producer IDs per source are derived only by the separately approved
  execution preflight, which verifies the source and model seals; and
- the exact execution, handoff-validation, reuse, and reporting commands ready
  for separate approval.

### Separately approved PDF execution

- one fresh terminal result for each source and all six fresh owner stages;
- exact pilot accounting, sealed target/alias index, immutable resolutions,
  and pilot handoff with `task04_status: not_evaluated`;
- aggregate page, table, family, hierarchy, label, alias, mention, resolution,
  warning, runtime, peak-memory, and artifact-size observations;
- one combined source-qualified anomaly summary;
- one checksummed render request and recipe, with no generated renders; and
- one identical second invocation proving verified checksum reuse.

## Automatic validation and anomaly policy

Apply one shared fail-closed contract to all three documents: source and
lineage seals; schema and inventory closure; completion-last publication;
complete physical-page coverage; valid coordinates, record IDs, references,
assets, tables, families, hierarchy, labels, aliases, and mentions; exact
scope accounting; index closure over successful candidates; immutable stage
one before and after resolution; warning scope; and handoff validation.

The combined anomaly sample is diagnostic, not another acceptance system. It
must include every error or abstention class, every hierarchy ambiguity class,
every unresolved/ambiguous cross-reference class, all nonzero warning classes,
and deterministic extrema for tables/families and runtime/resource use. Cap
ordinary examples at five source-qualified records per class after including
all three sources when available. Do not generate a separate acceptance file
for each document.

## Stop conditions

Stop before allocating a PDF attempt if configuration, identity, source scope,
resource admission, namespace freshness, or static lineage preflight fails.
During execution, preserve normal attempt evidence and stop the affected
document on any owner exception, timeout, invalid completion, lineage mismatch,
schema/inventory/checksum failure, incomplete page coverage, or publication
conflict. The scope may finish terminal accounting for already declared
documents, but do not perform the reuse invocation after any failed terminal
document or invalid stage-two/handoff result.

Open a POC-sized Task 03G.x only when the observed failure requires code or
policy change. A transient failure already covered by `retry_limit: 1` may use
the one configured retry without a new task; do not add simulated failures.

## Commands and approval boundary

Preparation may run offline config/identity tests and the project checks. It
must stop after presenting the preparation diff, new identity, freshness
evidence, static preflight result, and exact command paths. Producer IDs are
not predicted without verifying the source and model bytes; they belong to the
separately approved execution preflight.
The later execution commands will have this shape, with exact checked-in paths
substituted by the preparation outcome:

```bash
uv run er-commons extraction run-scope \
  --run-spec configs/brisbane_baylands_2025_deir_task03g2_scope_v1.json

uv run er-commons extraction validate-handoff \
  --extraction-root <task03g2-representative-pilot-extraction-root> \
  --scope-id <published-scopev1-id> \
  --schema benchmarks/er_bench/schemas/corpus_extraction/v1_1/records.schema.json

# Run the identical run-scope command once more only after accepting the fresh
# first invocation, then verify that all eligible stages report checksum reuse.
```

Do not run these commands, source verification, render generation, or any
parser/model command during the current no-PDF preparation authorization.

## Research / learning checkpoint

A fresh build and a reuse check answer different questions. The first proves
that current policy can construct every stage from the sealed PDFs. The second
proves that the same identity finds and verifies those immutable bytes without
reconstruction. Runtime-derived lineage is not hidden configuration: it is the
checksummed handoff from one newly published owner to the next.

One automatic contract plus an aggregate anomaly review scales because every
document receives the same executable invariants while unusual evidence stays
source-qualified. Human effort is spent on the pilot as a system and on real
anomalies, not on three parallel acceptance bureaucracies.

## Review pass

- **Freshness:** every first-invocation owner and downstream artifact is new;
  Appendix P historical IDs and bounded acceptance are absent from inputs.
- **Completeness:** each successful document covers every manifest page and all
  six owners before document publication.
- **Two-stage integrity:** accounting is exact, the index uses verified
  successful candidates, resolution does not mutate stage one, and the
  handoff remains pilot-only.
- **Aggregate sufficiency:** one source-qualified summary covers structural
  regimes and downstream consequences without per-file acceptance records.
- **Identity:** static plans and runtime handoffs are both checksummed and the
  pilot identity claims exactly the configured three-source scope.
- **POC restraint:** no chaos tests, repeated fresh builds, generated renders,
  or speculative remediation enter this task.

## Validation

During preparation:

```bash
make validate-extraction-contract
make check
git diff --check
```

After separate PDF approval, additionally verify all three source files and
page counts, execute the scope, validate the published handoff read-only,
verify the render request/recipe without rendering, repeat the identical scope
command once, and prove reuse without new content-owner reconstruction.

## Closure criteria

Task 03G.2 closes only after the preparation is accepted, the separately
approved fresh invocation has an explicit outcome, the handoff and aggregate
report validate, and the one reuse invocation has an explicit outcome. Task
03G remains open until the user accepts Task 03G.2 and any real remediation;
only then may Task 03H be revised for activation.

## Non-goals

- all-35 complete extraction or terminal accounting;
- any historical Appendix P content or authorization reuse;
- separate human acceptance records for the three sources;
- simulated failure, fault injection, or production reliability engineering;
- generated review renders or Task 04 dispositions;
- Final EIR comments/responses or standalone comment PDFs;
- OCR, generative repair, or pilot-local silent correction; or
- activating Task 03H or calling the extraction release accepted.
