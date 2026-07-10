# Task Contracts

Numbered task files are agent-sized implementation contracts. They preserve the
context needed for a later agent to complete one bounded piece of work without
replaying the whole project conversation.

Start with `AGENTS.md`, `docs/index.md`, and `docs/todo.md`. If a task is active,
read only that task and the documents it names. If no task is active, use the
current sprint plan to write the next bounded contract before implementation.
Do not scan every historical task to begin work.

## Ownership

- `docs/todo.md` owns current task order and status.
- `docs/sprints/` owns sprint-level scope and sequencing.
- `docs/decisions/` owns durable accepted choices and non-promoted results.
- `tasks/` owns the task-specific goal, inputs, outputs, research, validation,
  acceptance criteria, non-goals, and outcome evidence.

## Required shape

Every task should include, scaled to its size:

- `Abstract`: what will change, why it matters, and the main boundary.
- `Goal`, `Inputs`, and `Outputs`.
- `Research / learning checkpoint`: sources to inspect, the best practice or
  standard to understand, and the plain-language explanation to preserve.
- `Plan / spec requirement`: no plan, a brief plan, or a decision/spec before
  implementation.
- `Validation` and `Acceptance criteria`.
- `Non-goals` that prevent scope drift.

Use a `Review pass` for ambiguous, multi-file, data-contract, benchmark-policy,
or architecture-changing work. It should select only useful lenses, such as
data/benchmark design, open-source tooling, software architecture, provenance,
or documentation. Small mechanical tasks do not need ceremony.

## Subagent pattern

When delegation is available, favor several small subagents with non-overlapping
questions: source and license discovery, benchmark methodology, package/tool
survey, repo implementation, and verification are common splits. The lead agent
must reconcile evidence, retain claim boundaries, and write the final task
outcome; subagent output is input, not an unreviewed decision.

## Closing a task

Add an `Outcome` section with a short outcome abstract: what changed, what was
learned, validation run, and the precise next decision or task. Keep detailed
logs, counts, source links, and open risks below that summary. Update
`docs/todo.md` only with a compact status and pointer.
