# Architecture Contract

This file owns the current technical shape: package boundaries, CLI direction,
pipeline stages, and artifact separation. Detailed task history belongs in the
numbered task records and versioned specifications.

## Design principles

- Compose maintained open-source packages before writing project code.
- Keep project code as thin, typed glue around explicit input/output contracts.
- Prefer plain files, manifests, and small CLI commands over hidden notebook
  state or a workflow framework.
- Make every nontrivial stage restartable and observable through a manifest,
  summary, or structured log.
- Add a dependency only when the owning task names the job it solves and the
  reasonable alternatives have been considered.
- Treat human maintainability as a separate gate: ownership, readability,
  typing, testability, and recovery behavior must be understandable from the
  code.

## Repository layout

```text
src/er_commons/          # Package-backed CLI and project glue
pipelines/               # Tracked pipeline specs and wrappers
benchmarks/er_bench/     # Benchmark contracts, schemas, and small fixtures
configs/                 # Checked-in source-scoped configurations
tests/                   # Fast tests for project-owned behavior and contracts
docs/ and tasks/         # Routing, decisions, plans, and task outcomes
```

Large source files, extracted content, model files, review bundles, and run
outputs live under the external root described in
[`data_artifacts.md`](data_artifacts.md).

## Maintained document and collection pipeline

The production dependency direction is:

```text
source_release + artifact_io
  -> document_parsing
     -> hierarchy_inference
     -> document_records
  -> document_publication
  -> collection_processing
  -> extraction_reporting

human_review_support consumes published evidence but is never a production dependency
```

Responsibilities are intentionally one-way:

| Responsibility | Owns |
| --- | --- |
| `document_parsing` | Stable content parsing, heading evidence, routing, and clean table reconstruction. |
| `hierarchy_inference` | Hierarchy evidence and deterministic hierarchy decisions. |
| `document_records` | Record mapping, sections, printed labels, aliases, and document-local reference links. |
| `document_publication` | One-document attempts, lineage, reuse, and atomic publication. |
| `collection_processing` | Scope accounting, target indexes, cross-document resolution, and handoff assembly. |
| `extraction_reporting` | Machine summaries and terminal-status reporting. |
| `human_review_support` | Candidate-neutral review selections, renders, and human findings. |

The public production entry points are:

```text
er-commons documents publish
er-commons collections assemble-handoff
er-commons collections validate-handoff
er-commons collections validate-contract
```

Document publication consumes an explicit v2 document specification. Collection
assembly consumes an explicit v2 collection specification. No source or
Appendix P is selected by an implicit runtime default.

## Publication and identity boundaries

Task 03J uses two main document-stage publications:

1. `dconv1-` conversion bundles bind source bytes, page accounting, Docling
   options, runtime and model inputs, and the conversion inventory.
2. `prv1-` producer bundles bind an exact conversion seal to routing, table,
   and remaining producer policy.

Later document records and publication stages reference those sealed bundles.
They do not copy or mutate them. A complete stage is published only after its
completion record and managed-file inventory are checksummed. Failed attempts
retain diagnostics but cannot impersonate a complete result.

The current full-corpus candidate is the completed Task 03J v4 run. Its generated
lineage directory is named
`pipelines/brisbane_baylands/task_03h_clean_full_v4/`; the retained `task_03h`
stem is an implementation name, not permission to consume Task 03H artifacts.
The exact identity chain is owned by the [Task 03J outcome](../tasks/sprint2/03j_run_final_canonical_extraction.md).

Production identities bind every output-affecting source, scope, package, model,
policy, schema, configuration, and owned-code input. Fixture, smoke, document,
collection, index, resolution, and handoff identities use separate typed
namespaces. A new code or policy identity may reuse a sealed upstream artifact
only when that artifact's owning contract and checksums permit it.

## Extraction representation

The current extraction keeps the following boundaries explicit:

- raw Docling conversion evidence is preserved and is not the canonical table
  representation;
- the clean table pipeline owns canonical table content and table-family
  relationships;
- visible TOC rows and document-index content remain navigation evidence and do
  not become body-section starts or ordinary data-table targets;
- deterministic hierarchy correction is a replaceable evidence layer that
  preserves raw labels, levels, geometry, and provenance; and
- document-local and cross-document reference linking are separate stages with
  their own identity and resolution records.

The stable persisted contracts are the [canonical extraction
specification](specs/canonical_extraction_v1.md), [semantic structure
specification](specs/semantic_structure_v2.md), [cross-reference
specification](specs/cross_references_v3.md), and [restartable corpus
specification](specs/restartable_corpus_extraction_v1_1.md). The chunked
conversion specification defines the independent range-evidence boundary used
by the current production path.

## Review boundary

Human review consumes published Task 03 evidence through a separate
`human_review_support` package. Review selections, requested renders, findings,
usability dispositions, and release-freeze records do not modify machine
records. Task 04's first-pass review is historical. Task 04A allocates a new
review identity bound to Task 03J and owns the final usability registry and
initial release decision. Task 04B is a conditional fresh replay after an
approved Task 04A TOC/navigation stop handoff.

## Configuration and paths

Portable source and workflow configurations stay in Git. The external data root
is loaded only from the required, untracked `ER_COMMONS_DATA_ROOT` setting.
Committed configurations use relative paths or paths rooted by that setting;
they do not depend on a developer's absolute filesystem layout.

Task 03J's exact v4 configuration set is documented in
[`configs/README.md`](../configs/README.md). The smoke and Task 03G.2
configurations remain separate historical or diagnostic inputs and must not be
mixed with current native-v2 production contracts.

## Historical implementation record

The completed Task 03A through Task 03J records preserve implementation detail,
negative experiments, identities, and validation evidence. They are the source
of truth for historical reconstruction, not current entry-point instructions.
Use the active task and the versioned specifications for new work; do not copy
old task-era package names, commands, or artifact roots into a current contract.
