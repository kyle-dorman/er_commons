# AGENTS.md

## Project

This is a Python project managed with `uv`. It is building a reusable,
evidence-oriented workspace for environmental-review data, beginning with a
CEQA-oriented benchmark called `er_bench`.

The current project plan is intentionally discovery-first. Do not silently
assume the benchmark task, label policy, data source, licensing, or evaluation
metric before the active task records them. The initial purpose is to create a
small, reproducible benchmark foundation that can later support broader
environmental-review workflows.

## Entry path

Read this file first. Then read `docs/index.md` and `docs/todo.md`. Use the
index to choose the smallest set of context docs needed for the task.

For docs work, also read `docs/documentation.md`. For implementation, read the
active numbered task under `tasks/`. For data or artifact work, read
`docs/data_artifacts.md`. For architecture, workflow, CLI, or package changes,
read `docs/architecture.md`.

After a new chat, resume, or context compaction, reread this file,
`docs/index.md`, and `docs/todo.md`. If `docs/todo.md` names an active task,
read that task before editing; when no task is active, use the current sprint
plan to write the next bounded task contract before implementation.

## Working approach

- Prefer lots of small, independently scoped subagents for research, code
  inspection, implementation, validation, and review when the environment
  permits delegation. Give each one a bounded question and integrate their
  evidence rather than asking one agent to do an entire ambiguous project.
- Work in small steps. State the immediate question, expected artifact, and
  validation before undertaking a larger implementation.
- Learning is a product requirement. Explain the relevant best practice,
  package choice, data contract, and tradeoff in the task outcome or a compact
  decision note; do not only produce an opaque artifact.
- Research best practices early for nearly every planning task. Prefer primary
  documentation, maintainers' guidance, standards bodies, and original source
  material. Record sources and why the selected approach fits the project.
- Prefer maintained open-source packages, well-defined file formats, and
  command-line tools. Write custom Python only as glue around a clear boundary
  or when a task documents why existing tools do not fit.
- Keep glue code narrow, typed, readable, restartable, and easy to replace.
  Do not build a framework, a bespoke workflow engine, or a hidden notebook
  dependency prematurely.
- Keep data contracts explicit: source, license, retrieval date, schema,
  version, transformations, and benchmark split must be discoverable from
  tracked documentation or a generated manifest.
- Treat unverified project-plan assumptions as questions for Task 01, not as
  facts to embed in code.

## Data and artifacts

Keep the repository limited to source, tests, small configs, docs, task files,
and benchmark specifications. The canonical untracked data/artifact root is:

```text
/Volumes/x10pro/er_commons
```

`ER_COMMONS_DATA_ROOT` must be set in the local, untracked `.env`; the project
has no built-in default artifact root. Use `make bootstrap` to create the
documented directories after setting it. Do not commit raw source datasets,
normalized large tables, benchmark runs, downloaded documents, or generated
reports. See `docs/data_artifacts.md` for the complete layout and provenance
contract.

## Implementation rules

- Favor package-backed CLI commands over notebook-only workflows.
- Keep each pipeline stage artifact-producing and restartable. Write a compact
  manifest or summary whenever a stage downloads, normalizes, labels, splits,
  or evaluates substantial data.
- Start with the Python standard library where it is sufficient. Add a runtime
  dependency only after checking the maintained open-source option that
  simplifies a real task.
- Keep configuration reviewable and checked in; no absolute data paths in
  committed configs when a relative path or environment-rooted setting works.
- Use structured logging for command progress and artifact locations. Prefer
  `logging` over `print` for workflow code.
- Add short docstrings to changed functions explaining purpose and invariants.
- Avoid broad abstractions and backwards-compatibility aliases before there is
  a demonstrated caller or artifact to protect.

## Setup and validation

Use `make` for routine project commands. Run setup with:

```bash
make bootstrap
```

Use the root `Makefile` as the default validation entrypoint:

```bash
make fix
make check
```

For docs-only changes, inspect rendered Markdown or the diff and run:

```bash
git diff --check
```

## Task contract

`tasks/README.md` owns the detailed task shape. A task must be small enough for
a future agent to resume from the file alone. Larger, ambiguous, data-contract,
benchmark-policy, or architecture-changing tasks need a short plan, a
best-practice research step, explicit learning notes, and a scoped review pass
before implementation.
