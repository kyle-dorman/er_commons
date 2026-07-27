# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then return here to decide what to read or skip.

## Current status

This section is the source of record for the current sprint and active task.
`docs/todo.md` owns the detailed queue and next action.

Sprint 1 accepted the first benchmark contract: a Brisbane Draft-EIR defense
task. Sprint 2 is current. [Task
02](../tasks/sprint2/02_freeze_sources_and_provenance.md) completed the
versioned source freeze, and no numbered task is currently active.

The accepted benchmark contract is `benchmarks/er_bench/sprint1.md`; the
durable rationale is
[Decision 001](decisions/001_brisbane_draft_eir_defense_benchmark.md).
Sprint 2 is the smallest source-to-evaluation vertical slice. The next action
is to write the bounded Task 03 canonical-extraction contract from Task 02's
frozen manifest and outcome. Its provisional position is recorded in the
[Sprint 2 plan](sprints/sprint2_brisbane_draft_eir_defense.md); later detailed
task contracts are still created one at a time immediately before execution.

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

Do not read every document to begin narrow work. When a task is active, use its
input list and the roles above. When no task is active, use `docs/todo.md` and
the current sprint plan only to write the next bounded task contract.
