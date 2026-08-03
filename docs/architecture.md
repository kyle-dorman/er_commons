# Architecture Contract

This file owns the current technical shape: package boundaries, CLI direction,
pipeline and benchmark locations, and artifact separation. Read it for any
package, command, pipeline, benchmark, or configuration change.

## Design principles

- Compose maintained open-source packages before writing project code.
- Keep project code as thin, typed glue around stable input/output contracts.
- Prefer plain files, manifests, and small CLI commands over hidden notebook
  state or a bespoke workflow framework.
- Make every nontrivial stage restartable and observable through a manifest,
  summary, or logs.
- Introduce dependencies only after the active task names the specific job they
  solve and compares the reasonable alternatives.

## Repository layout

```text
src/er_commons/          # Minimal package-backed CLI and future glue modules
pipelines/               # Tracked pipeline specs/wrappers, not generated runs
benchmarks/er_bench/     # Tracked benchmark contract, schemas, and tiny fixtures
configs/                 # Small checked-in configuration files
tests/                   # Fast tests for project-owned glue and contracts
docs/ and tasks/         # Routing, decisions, plans, and execution contracts
```

The initial CLI exposes the artifact root. Task 02 added a `sources` command
group backed by Requests and urllib3 for bounded streaming and retries,
Beautiful Soup for landing-page reconciliation, pikepdf for structural PDF
validation, strict pypdf as a recorded fallback for recoverable published-file
defects, and standard-library `hashlib` for SHA-256. The project code owns the
typed source specification, role isolation, no-clobber publication, manifest,
and verification contracts rather than reimplementing those packages.

For the accepted Brisbane vertical slice, the planned implementation stack is
Docling for conversion, Label Studio Community for human review, BM25S for the
first retriever, and distinct local Ollama models for reference-case curation,
target generation, and rubric judging. These are selected contracts, not yet
installed runtime dependencies: each is added only by the task that implements
its narrow boundary. The benchmark must retain the exact tool/model version and
resolved model digest in its artifacts.

## External data and artifact layout

```text
/Volumes/x10pro/er_commons/
  datasets/
    ceqa/
      raw/               # Immutable source downloads or source references
      normalized/        # Reproducible normalized tables/documents
      derived/           # Task-scoped derivatives; never a hidden source
  pipelines/             # Run manifests, logs, and generated stage outputs
  benchmarks/
    er_bench/
      inputs/            # Versioned references to benchmark inputs
      splits/            # Materialized split artifacts and manifests
      runs/              # Evaluation outputs keyed by benchmark version/run
```

Task 02 populated the versioned Brisbane release below
`datasets/ceqa/raw/brisbane_baylands/`; its generated source manifest owns the
exact contents and schema. Create other deeper folders only when a task defines
what they contain and records their source and schema in a manifest.

## Configuration and paths

`ER_COMMONS_DATA_ROOT` is required in the local, untracked `.env`; no default
artifact root exists in code. The typed Pydantic settings model loads it for the
CLI, while `make` loads and validates the same value for routine commands.
Committed workflow configuration must not depend on a developer's absolute
paths. Future workflow settings should use validated Pydantic contracts rather
than untyped dictionaries.

Task 03C adds a separate complete-document producer policy above the accepted
Task 03A parser components. `documents run-review` remains the fixed comparison
harness; `documents run-complete` resolves one source through the sealed
manifest, verifies the accepted local models, converts and routes every page,
runs complete-document table families, and atomically publishes a task-scoped
producer run. Its `producer_run_id` content-binds source, release, runtime,
models, routing/table policy, packages, and project code. It is reusable raw
producer identity, not the later canonical `extraction_id`. Partial work is
retained only as attempt evidence, and final reuse requires every inventoried
checksum to verify.

Task 03C.1 makes that policy human-owned without changing parser behavior.
`complete_document.py` is the application shell; `producer_identity.py`,
`producer_conversion.py`, `producer_routing.py`, `producer_tables.py`, and
`producer_publication.py` each own one stage responsibility.
`producer_records.py` defines persisted records, `producer_services.py` exposes
only the external seams needed by offline tests, and `producer_artifacts.py`
owns durable Docling export and completed-run verification. Stage validation
uses named fail-closed invariants rather than one compound success boolean.
The v2 configuration and rewritten code intentionally derive a new
`producer_run_id`; semantic acceptance is established independently against
the immutable v1 artifact.

Task 03D adds a package-backed `canonicalize run-document` command that reads
the sealed Task 02 source release and completed Task 03C.1 producer artifacts,
then materializes a deterministic, schema-valid canonical-record candidate.
The command traverses the Docling hierarchy exactly once, preserves raw
geometry and invalid provenance evidence, projects producer table cells
through recorded cleanup indices, and publishes only after independent bundle
validation succeeds.

Candidate identity is content-derived from the selected source, producer
completion and inventory, canonicalization policy, schema, config, mapping
specification, and implementation inputs. A matching completed candidate is
reused rather than rewritten. The task-scoped candidate is an evaluation
artifact, not a promoted benchmark release; downstream hierarchy work consumes
its completion artifact rather than rediscovering producer files.

Task 03D.1 keeps that policy but replaces the MVP's monolithic materializer
with a functional core and explicit application shell. `materialize.py` owns
only stage order and failure preservation. Immutable context and ID allocation,
asset registration, content records, support records, provenance projection,
candidate sealing, and semantic comparison each have one responsibility-owned
module. JSON Schema remains the persisted record contract; frozen dataclasses
name internal stage results, and existing producer Pydantic models validate
producer-owned input records.

Implementation changes receive a new candidate ID through the existing
code-bundle digest without pretending the schema or mapping policy changed.
Promotion requires exact ordered record equivalence after narrow
extraction-ID normalization, exact generated clean-asset bytes, exact
accounting summaries, and an independently rebuilt byte-identical candidate.

Task 03E.0 applies the same human-ownership boundary to hierarchy evaluation.
The stable `hierarchy_runner.py` facade preserves the CLI entry point, while
the `document_extraction/hierarchy/` package gives specification validation,
Docling indexing and semantic comparison, artifact normalization, whole-run
comparison, independent subprocess execution, fixed controls, report
construction, and workflow sequencing separate owners. The workflow is an
application shell; comparison and normalization remain deterministic
functional code.

Hierarchy evaluation is intentionally outside complete-document producer
behavior. The accepted producer identity and bytes therefore remain unchanged
when evaluator code changes. Acceptance is instead grounded in a test that
recomputes both frozen 159-artifact Task 03E comparisons and requires exact
report equality, plus focused failure-path tests. This evaluator does not
correct headings or use a learned component. Task 03E.1 owns correction policy,
Task 03E.2 records the historical implementation and rejected evaluation, Task
03E.2b owns the human implementation, and Task 03E.2d owns bounded acceptance
and publication.

Task 03E.2b replaces the correction MVP with a human-owned functional core and
application shell while preserving its complete semantic payload. The short
semantic runner sequences source observation, visible-TOC analysis, numbering
scope construction, ordered rule evaluation, and hierarchy projection. TOC
region detection, row parsing, reconciliation, level evidence, rule context,
individual rule applications, and scope lifecycle each have one named owner.

Candidate orchestration separately owns preflight, three-process repeat
evidence, candidate records, preservation, quality disposition, and atomic
publication. Held-out preparation, annotation sealing, and evaluation are
distinct modules so an exposed evaluation cannot be silently regenerated.
Quality configuration, frozen-evidence verification, report disposition, and
pass assembly are also separate; a rejected report set is retained as an
explicit `QUALITY_GATE_REJECTED` attempt rather than failing through a
pass-only validation model. The explicit code inventory binds all runtime
modules into candidate identity and tests fail when a new module is omitted.

Task 03E.2d owns the separate policy decision and publication boundary for the
complete Appendix P correction candidate. It retains the strict Task 03E.2
quality rejection unchanged and adds a candidate-bound
`accepted_with_known_limitations` authorization that names the accepted
limitations and verifies the exact post-03E.2a semantic digest reproduced by
Task 03E.2b. Publication may consume either a verified strict quality pass or
this independently verified bounded authorization; neither path can impersonate
the other. The correction payload remains the existing v1 hierarchy-evidence
layer, not a new semantic schema or canonical representation.

## Appendix P dataflow

After the source freeze, the current design is a branch-and-join flow with
three persisted representations of document content. Identities, inventories,
completion records, acceptance evidence, and review reports are additional
control artifacts rather than content representations.

```text
Task 02 sealed PDF and manifest
  -> Task 03C.1 accepted baseline producer -> Task 03D.1 core canonical --+
  -> Task 03E hierarchy-enabled producer -> Task 03E.2d correction -------+
                                                                           |
                                                    Task 03E.4 semantic canonical
```

The two producer candidates occupy the same parser-evidence layer: Task 03C.1
is the accepted baseline for core content, and Task 03E changes only declared
hierarchy surfaces under an independent preservation comparison. Producer
evidence preserves parser-owned Docling output, clean table artifacts, figures,
assets, routing, and lineage. The correction evidence is a replaceable sidecar
over hierarchy-enabled producer item identities; it owns correction features,
TOC reconciliation, rule decisions, corrected levels and roles, hierarchy,
ambiguities, and warnings. The canonical representation is the project-owned
consumer interface. Task 03D.1 is its core-only candidate, and the Task 03E.4
MVP joins it with accepted correction evidence in immutable reference candidate
`exv1-c500c1731aa02a97d3cebe1b582eb8b03671a75b29eb3f1df349edd2f34fe5bf`,
which adds semantic sections, page-label resolution, and aliases. Its
human-owned replacement candidate
`exv1-2cba27c14e4a1aba72080c9803ce72f8dd728595bcd8176b60ffad777af4cf9b`
reproduces every candidate-owned semantic record and review derivative under a
narrow identity-derived normalization. The `workflow` shell sequences verified
runtime paths, identity/reuse, lifecycle, and publication; construction,
producer evidence, support, sealing, and comparison retain separate owners.

Task 03E.3 is only the specification gate for that join and creates no data
layer. Task 03E.4 references detailed Task 03E.2d evidence rather than copying
it, extends existing canonical page and section concepts, and persists only the
semantic facts downstream consumers need. Cross-reference
mentions remain a later enrichment because aliases describe possible targets,
whereas mentions are source spans that point toward those targets.

Active Task 03E.5 begins with a read-only inventory and a separately approved
schema/fixture gate before production code. Its planned schema-major-v3
candidate will remap the complete Task 03E.4 namespace, keep canonical edges
closed over v3-local alias and target IDs, and retain the exact Task 03E.4 IDs
only as correspondence evidence. Document-scoped mention candidates and local
resolution remain immutable stage-one records. Task 03F may append a separate
corpus-resolution result against stable mention IDs; it may not rewrite the v3
candidate. `deferred_cross_document` is reserved for targets identifiable in
the sealed model corpus, while named documents outside that corpus remain
terminal external unresolved records.

Task 03E.3 defines that join as canonical-extraction schema major v2 while
leaving strict v1 and the Task 03D.1 candidate immutable. V2 extends sections,
adds one page-label observation per physical page and one target-alias record
family, and keeps bridge, old/new correspondence, preservation, and bounded-
control verification as checksummed support artifacts. Cross-record validation
is order-sensitive and admits the accepted hierarchy's skipped numeric levels;
visible TOC rows and furniture never induce body sections.

The executable contract lives under `er_commons.semantic_structure`. Its
public `validation` facade only sequences named policies; `sections`,
`page_labels`, `aliases`, `bridge`, `control`, and `correspondence` each own one
reviewable invariant family. `bundle` builds the shared indexes, `handoff`
verifies sealed external evidence, and `normalization` owns the alias text
rule. Bridge validation requires an independently constructed producer-evidence
index, so persisted bridge rows cannot authenticate their own pointers or
unmapped dispositions.
