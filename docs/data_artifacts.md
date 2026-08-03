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

Task 03E.4's behavioral MVP/reference candidate is
`exv1-c500c1731aa02a97d3cebe1b582eb8b03671a75b29eb3f1df349edd2f34fe5bf`
under the existing Task 03D canonical-record root. Its inventory includes the
cross-producer bridge, Task 03D.1-to-v2 correspondence and preservation
reports, and compact bounded-control verification as support files. They are
control evidence, not canonical record families. The completed human-owned
replacement is
`exv1-2cba27c14e4a1aba72080c9803ce72f8dd728595bcd8176b60ffad777af4cf9b`;
its no-clobber comparison report lives under
`pipelines/brisbane_baylands/task_03e4_human_rewrite_review/`. Neither rewrite
artifact mutates the reference. The immutable Task 03D.1 and Task 03E.2d roots
remain external inputs. The exact ten-page renders and overlays live separately
under the disposable review cache keyed by candidate ID.

Task 03E.5's schema-major-v3 behavioral MVP candidate
`exv1-e3e81078dfb21b3d0718cd935004077e163dffc180bbc3d80f4a54391caa67f6`
remains immutable reference evidence. Initial human-owned candidate
`exv1-4a65944e4ce99a445953ea2904ca0e0c4b20fdd5412e9b89e7b6dac0254cc464`
is immutable correction-baseline evidence under the same canonical-record
root. Accepted corrected candidate
`exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`
is also published there. Its bounded correction report is under
`pipelines/brisbane_baylands/task_03e5_policy_correction_review/`; the original
zero-mismatch rewrite report remains under
`pipelines/brisbane_baylands/task_03e5_human_rewrite_review/`. In addition to
remapped canonical records and
terminal artifacts, its managed file set will include these candidate-owned
support roles:

```text
support/cross_reference_target_index.json
support/cross_reference_summary.json
support/cross_reference_preservation.json
```

The target index is document-scoped stage-one evidence, not Task 03F's later
corpus index. The preservation support must prove that all 323 accepted aliases
and targets are bidirectionally namespace-remapped while retaining upstream IDs
as correspondence evidence. A separately counted table-alias extension is
permitted only from an exact standalone numbered label on the same page as
exactly one canonical table; it retains the upstream table target ID and has no
upstream alias ID. Mention candidates use only exact-number table targets within
five physical pages, record the page distance, retain multiple distinct targets
as ambiguous, and reject qualified external-reference forms. Current v3
authorizes zero derived figure aliases; any
future exact-caption or independently verified TOC/page support requires a
separately reviewed contract revision. Publication remains atomic,
no-clobber, and completion-last; matching reuse requires verification of
identity, managed files, checksums, support roles, and completion. Failed
attempts remain inspectable without a completion record. Task 03F's separate
corpus-resolution artifacts may reference stable v3 mention IDs but may not
mutate any completed document candidate.

Task 03F's restartable corpus workflow will use this relative layout:

```text
pipelines/brisbane_baylands/task_03f_corpus_extraction/<extraction_id>/
  documents/<source_id>/<document_candidate_id>/
  scopes/<run_scope_id>/
    accounting/<accounting_id>/
    target_indexes/<target_index_id>/
    resolutions/<resolution_id>/
    handoffs/<handoff_id>/
  attempts/<transaction_or_stage_id>/
```

Each final document, accounting, index, resolution, and handoff directory is
no-clobber, checksum-inventoried, completion-last, and atomically published.
Attempt directories retain diagnostics but cannot contain or impersonate a
valid completion. Scope records reference immutable document candidates rather
than copying or rewriting them. Review renders remain under the existing
disposable `review_cache` and outside semantic identity.

The stage-two corpus index lives below
`scopes/<run_scope_id>/target_indexes/`; it is not the Task 03E.5
document-local `support/cross_reference_target_index.json`. Corpus resolution
records similarly append references to stable stage-one mention IDs and must
prove that every stage-one managed-file inventory is byte-identical before and
after resolution.

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
