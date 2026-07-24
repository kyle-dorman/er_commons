# Task 02A: Move the Local Artifact Root to the External SSD

## Abstract

Move this checkout's empty ER Commons data/artifact root from the nearly full
internal drive to `/Volumes/x10pro/er_commons` before Sprint 2 source
acquisition begins. Update the durable path contract, bootstrap the documented
entry-point directories, and validate that routine project commands resolve the
new location. Do not download or generate benchmark data.

## Goal

Make the external SSD the explicit, durable local artifact root for this MVP so
the upcoming source-freeze and extraction stages do not consume the internal
drive.

## Inputs

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/documentation.md`
- `docs/todo.md`
- `.env` and `.env.example`
- the mounted `/Volumes/x10pro` filesystem

## Outputs

- `/Volumes/x10pro/er_commons` with the three documented bootstrap directories
- this checkout's `.env` configured for the new root
- tracked documentation and examples that consistently name the new canonical
  root
- an accepted decision note explaining the local-only MVP storage choice

## Research / learning checkpoint

Inspect the mounted volume's capacity and write access plus the current artifact
root's contents before moving the contract. Preserve the project invariant that
the root has no hidden fallback and that substantial artifacts remain outside
Git.

The practical lesson to retain is that a configurable path still needs one
documented canonical value for the active checkout. Changing only the untracked
`.env` would leave future users and agents with a stale data contract.

## Plan / spec requirement

This small prerequisite needs no separate implementation plan. Update the
configuration and all path-owning documentation in one bounded pass, bootstrap
the root through the existing Make target, and verify the resolved paths.

## Validation

```bash
make bootstrap
make paths
make check
git diff --check
```

Also verify that the old root remains empty and that the new root contains only
the documented entry-point directories.

## Acceptance criteria

- `ER_COMMONS_DATA_ROOT` resolves to `/Volumes/x10pro/er_commons`.
- The new root is writable and contains `datasets/ceqa`, `pipelines`, and
  `benchmarks/er_bench`.
- Tracked path references agree with the new canonical root.
- No source documents, model weights, or benchmark outputs are created.
- Routine validation passes.

## Non-goals

- Freezing or downloading the Brisbane source corpus
- Configuring remote GPU compute or Google Drive synchronization
- Designing deeper artifact directories before their owning tasks
- Moving unrelated data already stored on `/Volumes/x10pro`

## Outcome

Completed 2026-07-24. The checkout now resolves
`ER_COMMONS_DATA_ROOT=/Volumes/x10pro/er_commons`, and `make bootstrap` created
only `datasets/ceqa`, `pipelines`, and `benchmarks/er_bench` below that root.
The previous internal root contained only the same empty bootstrap directories
and was removed after verification.

Tracked path-owning documentation, `.env.example`, and the local untracked
`.env` now agree. Decision 002 records why the local MVP uses the external SSD
and explicitly defers remote compute and cloud synchronization. No corpus,
model, or benchmark artifact was created.

Validation passed:

```text
make bootstrap
make paths
make check
git diff --check
```

`make check` reported Ruff formatting and lint clean, mypy clean, and two
passing tests. The next action is to write the bounded Task 02 source-freeze
contract.
