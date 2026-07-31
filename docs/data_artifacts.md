# Data and Artifact Contract

This file owns external data locations, Git policy, artifact layout, and
provenance expectations. Read it before adding, moving, downloading, or
interpreting data or generated outputs.

## Canonical root

Data and generated artifacts live outside the repository at:

```text
/Volumes/x10pro/er_commons
```

The root contains these entry points:

```text
datasets/ceqa/
pipelines/
benchmarks/er_bench/
```

`ER_COMMONS_DATA_ROOT` must be explicitly set in the local, untracked `.env`.
There is no code default. `make bootstrap` validates the setting and creates the
three documented entry-point directories. Task 02 created the first deeper
versioned release:

```text
datasets/ceqa/raw/brisbane_baylands/
  brisbane_baylands_2025_deir_sources_v1/
```

Its `sources/`, `landing_pages/`, and `records/` contents are immutable,
manifested external artifacts. Do not create other deeper data folders until
their owning task defines the role. [Decision
002](decisions/002_external_ssd_artifact_root.md) records why this local MVP
uses the external SSD.

Task 03 producer and canonicalization artifacts live under the pipeline
workspace:

```text
pipelines/brisbane_baylands/task_03c_single_document/<producer_run_id>/
pipelines/brisbane_baylands/task_03d_canonical_records/<candidate_id>/
```

A Task 03D candidate is complete only when its
`records/completion_record.json` exists and validates. Candidate identity binds
the selected source release, producer inventory, schema, policy, config,
mapping specification, and implementation inputs, so a matching completed
candidate can be reused without mutation. These task-scoped candidates are not
promoted `datasets/.../derived` releases.

Rendered pages and overlays used for bounded visual review are disposable
review aids under:

```text
pipelines/brisbane_baylands/review_cache/<candidate_id>/
```

Maintainability rewrites may store their independent semantic comparison under:

```text
pipelines/brisbane_baylands/task_03d1_rewrite_review/<comparison_id>/
```

The comparison report is evidence about two immutable candidates. It does not
promote either candidate into a corpus release.

Task 03E hierarchy comparisons use the same pattern:

```text
pipelines/brisbane_baylands/task_03e_hierarchy_review/<comparison_id>/
```

The compared producer candidates remain immutable. The review report records
the frozen sample, metrics, observed regressions, and the pre-disposition
recommendation or status. The completed task record and accepted decision note
own the later explicit user disposition; neither changes the frozen report.
For Task 03E, that durable decision is [Decision
003](decisions/003_deterministic_hierarchy_correction.md). The report is not
itself a canonical candidate or accepted release.

Task 03E.2 correction candidates and their held-out review evidence use
separate roots:

```text
pipelines/brisbane_baylands/task_03e2_hierarchy_correction/<candidate_id>/
pipelines/brisbane_baylands/task_03e2_hierarchy_review/<candidate_id>/
```

The candidate's `records/input_inventory.json` is the authoritative manifest
for verified external correction inputs: the producer completion and inventory
plus the source PDF, with their paths and checksums. `records/identity.json`
separately content-binds the source manifest and checked-in correction policy,
configuration, schema, and code bundle. Development fixtures and held-out
manifests are evaluation inputs, not candidate-owned producer inputs.
`records/environment.json` records Python/platform, `uv.lock`, and
resolved-package evidence for diagnosis without creating a second semantic
identity surface. Source-only held-out annotations and their evaluation remain
external review evidence, not producer or canonical records.

Task 03E.2d publishes under these existing roots rather than creating another
hierarchy data layer. Its candidate-bound `bounded_acceptance.json` lives beside
the external review evidence, binds the exact correction semantic digest and
known limitation inventory, and authorizes publication without changing the
historical Task 03E.2 reject reports. The completed candidate continues to use
the existing correction v1 artifact layout and completion-last contract.

## Git policy

Track in Git:

- source, tests, configs, small deterministic fixtures, documentation, task
  contracts, decision notes, and benchmark specifications;
- small schemas and source manifests that explain how to reproduce an artifact.

Do not track in Git:

- raw CEQA downloads or large document collections;
- normalized or derived bulk tables and text corpora;
- generated benchmark splits, predictions, reports, run logs, and caches;
- downloaded model weights or serialized model artifacts.

## Provenance requirement

Every task that retrieves, normalizes, labels, splits, or evaluates data must
write a compact adjacent manifest or summary. At minimum capture source URL or
identifier, access date, license/terms reference, source version or checksum,
input/output paths, schema version, command and relevant config, row or file
counts, random seed/split policy when applicable, and recoverable warnings.

The manifest is project glue worth owning: it is how a later learner can see
what happened without trusting hidden local state.
