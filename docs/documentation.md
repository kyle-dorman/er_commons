# Documentation Guide

This file owns documentation process and source-of-truth boundaries. Read it
before creating or editing durable docs, task outcomes, or decision notes.

## Ownership

- `AGENTS.md`: agent entry path, work rules, setup, and validation.
- `docs/index.md`: documentation router and read/skip guidance.
- `docs/product.md`: purpose, scope, claims, and success criteria.
- `docs/architecture.md`: technical contracts and boundaries.
- `docs/data_artifacts.md`: artifact roots, Git policy, and provenance.
- `docs/todo.md`: active task status and next action.
- `docs/backlog.md`: unselected future ideas only.
- `docs/sprints/`: sprint scope, research themes, and sequencing.
- `docs/decisions/`: accepted choices and negative/non-promoted results.
- `tasks/`: detailed implementation contracts and outcomes.

## Write rules

- Keep current contracts current; do not turn them into historical logs.
- Put task-specific inputs, outputs, validation, and detailed evidence in the
  numbered task, not the queue.
- Put an accepted data, benchmark, architecture, or policy conclusion in a
  decision note when it should constrain future work.
- Explain the relevant best practice and tradeoff when a task makes a material
  choice. Link to the primary or maintainers' guidance in the task outcome or
  decision note.
- Update routing links when a document moves or a new durable owner is added.

## Docs-change checklist

- Is this information owned by the file being edited?
- Does it duplicate an active task, backlog item, decision, or sprint plan?
- Can a future learner understand why the choice was made?
- Do `AGENTS.md`, `docs/index.md`, and folder READMEs still route correctly?
- Does `git diff --check` pass?
