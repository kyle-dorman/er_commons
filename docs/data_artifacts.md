# Data and Artifact Contract

This file owns external data locations, Git policy, artifact layout, and
provenance expectations. Read it before adding, moving, downloading, or
interpreting data or generated outputs.

## Canonical root

Data and generated artifacts live outside the repository at:

```text
/Volumes/x10pro/er_commons
```

The root currently contains these deliberately empty entry points:

```text
datasets/ceqa/
pipelines/
benchmarks/er_bench/
```

`ER_COMMONS_DATA_ROOT` must be explicitly set in the local, untracked `.env`.
There is no code default. `make bootstrap` validates the setting and creates the
three documented entry-point directories. Do not create or populate deeper data
folders until the task defines their role. [Decision
002](decisions/002_external_ssd_artifact_root.md) records why this local MVP
uses the external SSD.

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
