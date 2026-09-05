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

Task 04C uses a separate derived namespace under
`pipelines/brisbane_baylands/task_04_navigation_overlay/`. Its completed
source-free Gate A plan is
`navoverlayplanv1-72af852ffe39c272ce958147c74974008269b6e72db2c0c7b03e0f66ba366741`.
Gate B semantic view
`navsemanticv1-ae00c6e6f70839f1ca15404c9dff14161f0a3e9aaa9e7902f51f65b36023c8fc`
binds that plan and materializes only the 5,800 changed block/table navigation
dispositions. It references sealed Task 03J checksums and Task 04A's compact
review records rather than mutating or rehashing large upstream artifacts.
Replacement Gate C reconciliation
`navlinkv1-978dbf3f3363eeb4265c75f60efd80bb3995234586e1821f060fe70a9c11bed4`
contains 15 model-facing TOC text pages, 560 ordered text entries, 560 entry
dispositions, 28 added navigation links, an empty alias overlay, and 725
inherited unresolved-link dispositions. It traces every text page through the
accepted candidate, stable producer, Docling conversion, core-owned range, and
checksummed raw page record. The old six-link table-row namespace remains
immutable superseded evidence, not the effective view. Gate D remains
incomplete and is superseded by Task 04D.

Task 04D completed Gates A through D. Its final Gate C
validation is retained under
`pipelines/brisbane_baylands/task_04d_gate_c_final_pass1/`, with a byte-identical
repeat under `task_04d_gate_c_final_pass2/`; earlier Gate C
evidence remains under `pipelines/brisbane_baylands/task_04d_gate_c/` and
the subsequent `task_04d_gate_c_post_cleanup/` and
`task_04d_gate_c_replay_bridge/` namespaces, including the superseded
`task_04d_gate_c_execution_fix/` validation. Its
generic reviewed-navigation bundle is retained under
`pipelines/brisbane_baylands/task_04d_reviewed_navigation/`. These are
validation and input evidence rather than machine publications. The designated
replacement is rooted at
`pipelines/brisbane_baylands/task_04d_relinked_v1/` under production identity
`exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3`.
Its ready collection handoff is
`handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`
in scope
`scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da`.
The versioned run contract checksum-reuses the five sealed
pre-link document products for all 35 successful Task 03J sources, then
publishes only fresh linked-document, downstream document, and collection
descendant identities. Optional reviewed navigation is checksum-bound through
the same generic run specification. Independent validation verified all 35
documents and the complete handoff identity closure. This handoff replaces
Task 03J only for downstream linking-dependent use; Task 03J remains the
immutable extraction source, and Task 04A and Task 04C artifacts remain
immutable evidence.

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
