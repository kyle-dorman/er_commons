# Task 06B Gate 2 generation and input lane v1

Frozen before edits. Move the six `scripts/task03h_generation` owners to
`document_publication/config_generation` with one-way imports. Current generation
requires a strict JSON generation spec declaring repository/data roots, six
process templates, ordered per-source original manifests, output paths, names,
model inventory descriptor, source-family aliases, resource/chunk policies and
finite document/collection code inventories. No environment version/default
corpus selection remains. Shared metadata uses the Gate 1 invocation budget.
`--check` compares proposed current bytes; it never rewrites historical recipes.

Merge `prepare_task03h.py` and `prepare_task03j_v4.py` into the thin
`prepare_document_inputs.py` caller of `input_preparation.py`. The request names
both run specs and output root, with explicit data/repository roots when required.
Derive recipe/catalog references from specs. Retain schema, source scope, unique
process-config, fresh-template, resource and completed-output checks, generalized
from 35/210 to the declared source count. Preserve the historical readiness schema
and filename for reader compatibility; add an explicit current request binding.

Replace `run_task03j_v4.py` with thin `run_document_collection.py` and a package
`collection_runner.py` owner. The CLI requires a document spec, repeatable source
IDs or explicit all-sources selection, and a progress root. Preserve fatal regexes,
serial order, retained terminal progress and exit codes; progress records are
observations, not candidate completions. No import-time settings or fixed v4 roots.

Synthetic validation covers non-corpus scopes, exact generation/check behavior,
unchanged semantic specialization, safe no-clobber paths, source/model sentinels,
current code inventories, fatal-pattern equivalence, and identity-bound resume.
All accepted external evidence and tracked historical generated configs remain
unchanged. Root owns current docs/Make routing and separate one-off removals.

## Implemented interfaces and evidence

| Previous owner | Current owner |
| --- | --- |
| `scripts/task03h_generation/{__init__,shared,process_templates,specifications,production_identity,workflow}.py` | `src/er_commons/document_publication/config_generation/` with the same six filenames |
| `scripts/generate_task03h_configs.py` | `scripts/generate_document_configs.py --generation-spec PATH [--check]` |
| `scripts/prepare_task03h.py`, `scripts/prepare_task03j_v4.py`, `document_publication/task03h_preparation.py` | `scripts/prepare_document_inputs.py` and `document_publication/input_preparation.py` |
| `scripts/run_task03j_v4.py` | `scripts/run_document_collection.py` and `document_publication/collection_runner.py` |

The checked generation request schema lives at
`benchmarks/er_bench/schemas/document_config_generation/v1/request.schema.json`.
The current runtime chunk-selection contract remains strictly greater than 300
pages; the request must declare that accepted threshold. Proposed document and
collection specs, catalog, producer controls, chunk policy, and identity shapes
are validated before writing. Every output is compared first, then missing files
are created without overwriting existing different bytes. Code dependencies are
explicit finite reviewed request fields, never package globs.

Synthetic tests cover generation/check byte equality, original source-manifest
bindings, invalid replacement membership, changed controls, source/model access
sentinels through full input readiness, more-than-300-page metadata selection,
fatal runner equivalence, ordered source selection, exact-spec resume and
mid-invocation spec mutation. The runner records its single loaded spec digest
and compares stable filesystem metadata before/after each subprocess; ordinary
access-time updates are ignored. Preparation shares parsed process controls and
its invocation budget with nested validators, and verifies observed input stamps
before recording readiness. CLI help smoke tests pass for all three new scripts.

The lane's focused validation passed 80 tests; scoped mypy passed. Independent
review found and resolved missing proposal validation, repeated unbudgeted
control reads, repeated runner spec hashing, and an access-time-sensitive guard.
Historical recipes/configs and accepted artifacts were not regenerated.
