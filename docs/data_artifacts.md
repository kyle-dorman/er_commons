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

Task 03J is the current machine candidate, not the final usability release.
Task 04A must bind a new review run to its exact identities. Superseded Task
03H and pilot trees may remain as historical evidence under quarantine or the
artifact root, but they are not eligible inputs to the current review.

## Review artifacts

Task 04 and Task 04A use separate review-run namespaces under:

```text
pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/
  records/
  html/
  review_cache/
```

The completed first-pass Task 04 records are historical and bind the old
Task 03H diagnostic pass. Task 04A allocates a new `reviewv1-` run bound to the
Task 03J candidate. Its source-free MVP preparation record binds sealed
upstream identities and file metadata without recomputing large file
checksums; its production TOC census is now the completed source-free Gate B
output. The corrected Gate C reviewer is published under
`reviewv1-task03j-final-c17/`, with source renders, 757 persisted TOC decisions,
117 stable TOC-review run cards, and 224 stable machine-positive page cards.
Labels do not change card membership; Hide reviewed provides the pending-only
view. Explicit TOC and Not TOC controls can change or clear each label, and
positive rejection still applies through the contiguous run end. Intentional
blanks and the one-off `Basic Project Information` run suffixes remain excluded. The package also
contains a Task 03I recheck record.
Task 04A's accepted Gate D closure is published additively under
`reviewv1-task03j-final-c17/gate_d/`. It contains the source-usability registry,
725 unresolved ambiguous-link dispositions, Task 03I recheck disposition,
accepted-risk report, release freeze, and completion record. The freeze pins the
55,949-byte human decision record and sealed Task 03J identities without
rehashing large upstream artifacts.

Task 04C will use a separate derived namespace for the accepted
machine-plus-human navigation and linking view. It references sealed Task 03J
checksums and Task 04A's compact review records rather than mutating or
rehashing large upstream artifacts.

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

Task 05's Final EIR Volume 4 inventory has a separate curator-only namespace.
It is not part of the Task 03 model corpus or the accepted Draft EIR extraction
release. Its source, transcription/extraction route, identities, and acceptance
records must remain separately documented.

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
