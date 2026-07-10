# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then return here to decide what to read or skip.

## Current status

The repository is in Sprint 1: define the first benchmark version. The only
active implementation contract is:

```text
tasks/sprint1/01_define_sprint1_benchmark.md
```

Sprint 1 is intentionally a narrow research and specification task. It must
make one benchmark version's user question, scope, CEQA source, provenance,
evaluation policy, and minimal open-source stack explicit before implementation
begins. Its source of truth is `benchmarks/er_bench/sprint1.md`.

## Document roles

- `docs/product.md`: project purpose, current scope, claim boundaries, and
  success criteria. Read when the task changes what the project is for.
- `docs/architecture.md`: package, CLI, pipeline, benchmark, and configuration
  boundaries. Read for technical design or implementation shape.
- `docs/data_artifacts.md`: external data root, artifact layout, Git policy,
  and provenance expectations. Read for any data or generated output work.
- `docs/documentation.md`: documentation ownership and change checklist. Read
  before editing or creating durable docs.
- `docs/todo.md`: active queue and next action. Read to select work; it does
  not replace a task contract.
- `docs/backlog.md`: unselected future ideas only. It does not define current
  scope or record decisions.
- `docs/sprints/`: sprint-level scope, research questions, and ordering.
- `docs/decisions/`: durable accepted choices and non-promoted results.
- `tasks/`: narrow agent-sized contracts with validation and outcomes.

Do not read every document to begin a narrow task. Use the active task's input
list and the roles above.
