# Data and Artifact Contract

This file owns external data locations, Git policy, artifact layout, and
provenance expectations. Read it before adding, moving, downloading, or
interpreting data or generated outputs.

## Canonical root

Data and generated artifacts live outside the repository. For this local MVP,
the configured root is:

```text
/Volumes/x10pro/er_commons
```

`ER_COMMONS_DATA_ROOT` must be explicitly set in the local, untracked `.env`.
There is no code fallback. `make bootstrap` validates the setting and creates
these entry points:

```text
datasets/ceqa/
pipelines/
benchmarks/er_bench/
```

The immutable Task 02 source release is under
`datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_deir_sources_v1/`.
Its source files, landing-page captures, and records are governed by the source
freeze manifest. [Decision 002](decisions/002_external_ssd_artifact_root.md)
records why the local MVP uses the external SSD.

## Current pipeline artifacts

The completed Task 03J machine candidate is under:

```text
pipelines/brisbane_baylands/task_03h_clean_full_v4/
  inputs/
  document_parse_evidence/
  hierarchy_inference/
  document_records/
  document_publications/
    documents/<source_id>/<docv1-id>/
    scopes/<scopev1-id>/
      handoffs/<handoffv1-id>/
```

The `task_03h_clean_full_v4` directory name is the generated lineage name for
the Task 03J v4 run. It is not a Task 03H input. The exact production identity,
scope, handoff, and completion checksum are owned by the [Task 03J
outcome](../tasks/sprint2/03j_run_final_canonical_extraction.md).

Each published stage is completion-last, checksummed, no-clobber, and
restartable. Failed attempts retain diagnostics but cannot impersonate a
successful completion. Downstream stages reference sealed upstream artifacts;
they do not copy or mutate them. A matching valid completion may be reused only
when its identity and managed-file inventory verify exactly.

Task 03J remains the immutable extraction source. The accepted Task 04A
usability registry and Task 04D's designated linking-dependent handoff are
separate downstream inputs; their exact identities and closure are retained in
their task outcomes.

## Review artifacts

Task 04 and Task 04A use separate review-run namespaces under:

```text
pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/
  records/
  html/
  review_cache/
```

The accepted Task 04A closure is under
`pipelines/brisbane_baylands/task_04_review/reviewv1-task03j-final-c17/gate_d/`.
Task 04C's overlay namespaces are immutable superseded review evidence. The
designated Task 04D replacement is rooted at
`pipelines/brisbane_baylands/task_04d_relinked_v1/`. It replaces Task 03J only
for linking-dependent use; Task 03J remains the immutable extraction source.
The exact Task 04 identities, validation passes, and superseded namespaces are
retained in the [Task 04A](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md),
[Task 04C](../tasks/sprint2/04c_materialize_human_review_navigation_overlay.md),
and [Task 04D](../tasks/sprint2/04d_relink_frozen_extraction.md) outcomes.

HTML, rendered pages, overlays, and other review-cache outputs are disposable
derivatives. They never become authoritative Task 03 machine state, human
approval state, or extraction identity inputs unless the owning review contract
explicitly checksums them as reviewed evidence.

## Other artifact classes

Future benchmark inputs, splits, and runs belong under:

```text
benchmarks/er_bench/
  inputs/
  splits/
  runs/
```

Task 05's Final EIR Volume 4 inventory uses a separately identified namespace:

```text
pipelines/brisbane_baylands/task_05_response_inventory/<inventoryv1-id>/
  records/
  inventory/
  review_views/
  diagnostics/
```

The completion record must close the exact source identity, extraction or
transcription contract, schema, configuration, implementation, managed-file
inventory, and checksums. This namespace is not part of the Task 03 model
corpus or accepted Draft EIR extraction release; it must not copy the raw PDF.

## Git policy

Track in Git:

- source code, tests, small configs and fixtures;
- documentation, task contracts, decisions, and benchmark specifications; and
- small schemas or manifests needed to explain how an external artifact is
  reproduced.

Do not track in Git:

- raw CEQA downloads or large document collections;
- normalized or derived bulk tables and text corpora;
- generated splits, predictions, reports, run logs, and review caches; or
- downloaded model weights or serialized model artifacts.

## Provenance requirement

Every task that retrieves, normalizes, labels, splits, or evaluates data must
write a compact adjacent manifest or summary containing, at minimum:

- source URL or identifier and access date;
- license or terms reference;
- source version or checksum;
- input and output paths;
- schema, command, and relevant configuration;
- row or file counts;
- random seed and split policy when applicable; and
- recoverable warnings or known limitations.

The manifest is the project-owned explanation of what happened. It lets a later
learner inspect and rerun work without trusting hidden local state.
