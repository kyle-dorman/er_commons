# ER Commons

`er-commons` is a small, reproducible Python workspace for environmental-review
data work. The first planned capability is `er_bench`, a CEQA-oriented benchmark
and evaluation harness. That benchmark is deliberately the first component, not
the project boundary: later work may add data preparation or other reusable
environmental-review workflows when a scoped task justifies them.

The repository favors maintained open-source tools and thin, explicit glue code.
Before new custom code is added, a task should establish that an existing package,
format, or command-line tool does not cleanly solve the need.

## Quick start

```bash
make bootstrap
make about
make paths
make check
```

Project commands require `ER_COMMONS_DATA_ROOT` in a local `.env` file. This
checkout is configured for `/Users/kyledorman/data/er_commons`; use
`.env.example` to create the file on another machine. `make` loads the value and
validates it before commands that use project settings.

## Layout

```text
er_commons/                         # Git repository: code, docs, configs, tests
  src/er_commons/                   # Small package-backed command-line glue
  pipelines/                        # Versioned pipeline specifications and notes
  benchmarks/er_bench/              # Versioned benchmark contract and schemas
  configs/                          # Small, reviewable configuration files
  docs/                             # Product, architecture, planning, decisions
  tasks/                            # Narrow agent-sized implementation contracts

/Users/kyledorman/data/er_commons/  # Not tracked by Git: data and run artifacts
  datasets/ceqa/                    # CEQA source files and normalized derivatives
  pipelines/                        # Pipeline manifests and generated run outputs
  benchmarks/er_bench/              # Benchmark inputs, snapshots, and run results
```

See [docs/index.md](docs/index.md) for routing and current status. Agents should
start with [AGENTS.md](AGENTS.md).
