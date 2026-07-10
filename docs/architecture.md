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

The initial CLI uses the Python standard library deliberately. It exposes the
artifact root but does not create pipeline behavior. A later task should choose
a maintained library only if it materially improves a concrete command.

For the accepted Brisbane vertical slice, the planned implementation stack is
Docling for conversion, Label Studio Community for human review, BM25S for the
first retriever, and distinct local Ollama models for reference-case curation,
target generation, and rubric judging. These are selected contracts, not yet
installed runtime dependencies: each is added only by the task that implements
its narrow boundary. The benchmark must retain the exact tool/model version and
resolved model digest in its artifacts.

## External data and artifact layout

```text
/Users/kyledorman/data/er_commons/
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

The currently created root contains only empty `datasets/ceqa`, `pipelines`,
and `benchmarks/er_bench` directories. Create deeper folders only when a task
defines what they contain; record their source and schema in a manifest.

## Configuration and paths

`ER_COMMONS_DATA_ROOT` is required in the local, untracked `.env`; no default
artifact root exists in code. The typed Pydantic settings model loads it for the
CLI, while `make` loads and validates the same value for routine commands.
Committed workflow configuration must not depend on a developer's absolute
paths. Future workflow settings should use validated Pydantic contracts rather
than untyped dictionaries.
