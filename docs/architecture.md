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
