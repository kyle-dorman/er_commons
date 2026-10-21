# ER Commons

`er-commons` is a small, reproducible Python workspace for environmental-review
data work. The first planned capability is `er_bench`, a CEQA-oriented benchmark
and evaluation harness. That benchmark is deliberately the first component, not
the project boundary: later work may add data preparation or other reusable
environmental-review workflows when a scoped task justifies them.

The repository favors maintained open-source tools and thin, explicit glue code.
Before new custom code is added, a task should establish that an existing package,
format, or command-line tool does not cleanly solve the need.

## Current milestone

The first benchmark has 49 questions: 19 development and 30 test. Development
execution, offline reporting and the reporting code-quality pass are complete.
[Task 13](tasks/sprint2/13_run_locked_test.md) is closed with all 180 evaluations
complete: Luna and Haiku each answered all 30 test questions three times.
The sealed test report and final gallery preserve the frozen evaluation definitions
and all original receipts. Presented results cover Luna and Haiku only.
[Task 13B maintenance](tasks/sprint2/13b_locked_code_quality.md) is complete.
No task is active; Tasks 14–15 remain provisional.

Use the [docs index](docs/index.md) for accepted inputs and status, the
[queue](docs/todo.md) for next actions, and the
[reporting maintainer guide](docs/reporting_maintainer_guide.md) for charts,
tables and future model comparisons. Generated reports live outside Git.

## Quick start

```bash
make bootstrap
make about
make paths
make check
```

Project commands require `ER_COMMONS_DATA_ROOT` in a local `.env` file. This
checkout is configured for `/Volumes/x10pro/er_commons`; use `.env.example` to
create the file on another machine. `make` loads the value and validates it
before commands that use project settings.

## Layout

```text
er_commons/                         # Git repository: code, docs, configs, tests
  src/er_commons/                   # Small package-backed command-line glue
  pipelines/                        # Versioned pipeline specifications and notes
  benchmarks/er_bench/              # Versioned benchmark contract and schemas
  configs/                          # Small, reviewable configuration files
  docs/                             # Product, architecture, planning, decisions
  tasks/                            # Narrow agent-sized implementation contracts

/Volumes/x10pro/er_commons/         # Not tracked by Git: data and run artifacts
  datasets/ceqa/                    # CEQA source files and normalized derivatives
  pipelines/                        # Pipeline manifests and generated run outputs
  benchmarks/er_bench/              # Benchmark inputs, snapshots, and run results
```

See [docs/index.md](docs/index.md) for routing and current status. Agents should
start with [AGENTS.md](AGENTS.md).
