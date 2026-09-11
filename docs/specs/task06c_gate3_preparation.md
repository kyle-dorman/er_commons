# Task 06C Gate 3 preparation

The user authorized Gate 3 conversion and requested a persistent background
session to avoid repeated agent polling. `tmux` is installed. Conversion has
**not started**: required local model readiness failed before source execution.
This record owns the measured blocker and concrete remediation proposal. It
does not authorize a model download or claim conversion completion.

## Local model readiness

Read-only filename and cache metadata inspection found no `model_inventory.json`
under the external root. The historical configured directory
`pipelines/brisbane_baylands/task_03a_docling_native_pilot_v1/` is absent.
The inspected external root, user Hugging Face cache and user Library caches
also contain no `tableformer_accurate.safetensors` or `tm_config.json`.

Heron is present in the user Hugging Face cache at snapshot
`8f39ad3c0b4c58e9c2d2c84a38465abf757272d8`: six files totaling
171,764,371 bytes, including 171,658,996 bytes of weights. These are metadata
observations; payload digests have not been verified. The TableFormer cache
contains only `refs/v2.3.0`, pointing to
`fc0f2d45e2218ea24bce5045f58a389aed16dc23`, with no snapshot or blobs.
A revision pointer alone is not an installed model.

The [frozen execution specification](task06c_source_qualification_v1.md)
requires: “Missing models or inventory stop before conversion” and “Model
remediation needs its own concrete proposal.” Gate 3 authorization permits the
prepared conversion once its prerequisites pass, but does not lift that explicit
model-download boundary.

## Confirmed cause of the missing model directory

A follow-up read-only investigation traced the retained v4 conversion identity
`dconv1-30676c6d68ddb689503cf7271470ed17f36002be7c67894b467b52cc37e991d4`
to the original inventory digest
`26d1707784bdd2ac4cd6fc2e0ea19c3017831e89da3323313b4dfe8cd436f245`.
That compact record still retains both model snapshots and every model file's
size and SHA-256, confirming the earlier run used them.

The September 2 cleanup transcript directly explains the missing model home.
In Codex task `01a0407b-7e0b-7551-83af-e9c40797cbca`, transcript lines
5294/5300 contain the assistant's obsolete-pilot cleanup proposal and the user's
approval. Line 5323, at 19:29:54 UTC, executes a deletion list containing the
entire `task_03a_docling_native_pilot_v1` directory. Line 5337, at 19:31:23 UTC,
explicitly reports that directory deleted; line 5343 verifies the surviving
roots. This was the earlier approximately 252-GiB cleanup, not the later
53-GiB cleanup described in the abbreviated memory summary.

The cleanup incorrectly classified a directory containing shared runtime models
as disposable pilot output. The user approved cleanup based on that
classification; the dependency-preservation error belongs to the assistant.
This explains the original inventory/model directory's deletion, but does not
establish why the separate Hugging Face cache has no TableFormer payload.

A broader filename search of the home directory and external disk found no
replacement before it was stopped once the deletion was confirmed; it was not
exhaustive. macOS denied access to protected locations including both Trash
folders. No model bytes were read, restored or downloaded. Future cleanup must
preserve model/inventory dependencies referenced by live processing configs,
even when their parent directory has an old task name.

## Proposed model remediation

Upon separate approval:

1. Create a fresh external `06c/gate3_models_v1/` beneath the recovery root.
   Materialize and verify the existing Heron snapshot into contained ordinary
   files. Do not mutate the shared cache or recreate the historical inventory.
2. Download only the accurate TableFormer weights and configuration from
   `docling-project/docling-models` at immutable commit
   `fc0f2d45e2218ea24bce5045f58a389aed16dc23`:
   `model_artifacts/tableformer/accurate/tableformer_accurate.safetensors` and
   `model_artifacts/tableformer/accurate/tm_config.json`.
3. Require the existing accepted digests respectively:
   `2a7d6c924b3cd12fb99a09280ca9c33a89c5d60b93253617d2e088c1a40374d9` and
   `984e122ceb8ccf84d84c9d2882f6f2302a44b4f1e577babd6289892c36f3cffd`.
   Stop on any mismatch; preserve bounded failure evidence.
4. Write a new model inventory binding immutable snapshot revisions, per-file
   sizes and SHA-256 digests, current installed package versions, and the
   accepted Apache-2.0 Heron / CDLA-Permissive-2.0 TableFormer license references
   recorded by Task 03A. Validate using the maintained model and fallback
   readers before deriving conversion identities.

Proposed remediation ceilings: 512 MiB total downloaded bytes, 1 GiB new model
namespace including copied cache files and partials, 64 GiB starting free disk,
1,800 seconds total, 2 GiB process-tree RSS, one transfer at a time, no retry,
15-second connect and 60-second read timeouts. The source PDF is neither
redownloaded nor rehashed. No model execution belongs to inventory preparation.
Once verified, the already authorized Gate 3 may use these installed files with
network access disabled.

## Prepared processing policy

[Content parsing config](../../configs/task06c/feir_appendix_f1/content_parsing.json)
and [chunk policy](../../configs/task06c/feir_appendix_f1/chunked_conversion.json)
freeze the qualified 756-page, 68,389,743-byte source and stream digest, a fresh
processing lineage, and the separate model-inventory path. The model inventory
and processing manifest paths are proposed outputs, not existing evidence.
The original source and accepted manifests remain untouched.

Use the existing fixed-size planner to avoid an extra whole-source profiling
pass. Core ranges are 1–200, 201–400, 401–600 and 601–756; corresponding read
ranges are 1–201, 200–401, 400–601 and 600–756. Each has at most one overlap
page on each side, assigned to exactly one owning core. Final identity-bound
plan publication must wait for the verified manifest and model inventory.

Use one worker, CPU four threads including learned fallback, 10 GiB summed
process-tree RSS, 3,600 seconds per range, 86,400 seconds for the full invocation,
32 GiB new output including partials and logs, 64 GiB initial free disk, no
positive swap growth, and 15 seconds termination grace. No automatic retry is
planned. Matching completed ranges remain reusable after a failure.

The detached `tmux` command will run a supervising process around the maintained
`run_chunked_document_parsing` entrypoint via `scripts/run_chunked_conversion.py`.
It produces conversion and producer evidence only. Its status and logs live
outside sealed stage directories. The supervisor must terminate descendants
across process-session boundaries because existing range workers start separate
sessions. Offline environment variables and four-thread library limits apply
before importing the conversion runtime.

A background session avoids keeping an agent turn open during model execution.
It is not a scheduled assistant follow-up: inspect its durable status and logs
when the user returns. Gate 4 closure and later target/handoff work remain
separate from this run.

## Preparation implementation and review

`source_release/retained_processing.py` supplies the metadata-only receipt
validator and no-clobber processing-manifest adapter. New manifests retain the
`qualified_substitute` role and are accepted only after exact Final F1 receipt,
policy, implementation and provenance checks. Ordinary source processing keeps
its existing byte-validation behavior. The adapter was checked against the
actual accepted receipt without publishing a manifest or rereading the PDF.

`document_publication/background_execution.py` supplies the explicit command
supervisor. Its output accounting allows the maintained internal range symlinks
without counting target bytes twice, rejects external links, and reserves
65,536 bytes for terminal metadata. Limits are sampled, not instantaneous OS
allocation quotas. Tracked descendants survive parent/session changes in the
supervisor's process registry; an arbitrary process that deliberately double
forks and reparents between samples is outside this guarantee. The maintained
worker parents remain alive during their children’s execution.

The [independent review](task06c_gate3_review.md) found no outstanding
implementation issue after two supervisor fixes and independently passed all
25 focused adapter/supervisor tests. A normal Docling source path is inspected
by MIME before suffix in the installed package; the retained `.part` filename
does not justify rewriting or duplicating the PDF. Live source/model integration
remains unexecuted because the model precondition failed.

## Approved restoration outcome

On September 10, 2026 (local time), the user approved downloading the missing
files. Two pinned TableFormer files totaling 212,765,448 bytes were downloaded;
six existing Heron files were copied from cache. Every restored file matches
its exact retained v4 SHA-256 and byte size. The new inventory includes the
accurate TableFormer subset needed by this run; the unused fast variant was
not restored. Both maintained model validation and lazy fallback initialization
passed without loading a predictor.

The fresh `06c/gate3_models_v1/model_inventory.json` has SHA-256
`9ea427dc522944feb94fd40be13ce09adb9d65afa795112718e9a9ebc2ab1e18`.
The restoration and supervisor receipts are in `gate3_models_v1/restoration.json`
and `gate3_model_restore_attempt_v1/execution.json`. Restoration took 6.003
seconds, peaked at 131,268,608 sampled process-tree RSS bytes, and showed no
swap growth; 384,529,819 model bytes were restored in total. The pinned snapshot
files are regular contained files rather than links into the shared cache.

The fresh processing manifest, preflight, range plan, config copies and launch
script live under `06c/gate3_inputs_v1/`. Source verification used the retained
receipt and metadata, with no standalone PDF hash. The identity-bound plan is
`dplan1-dc4cd61060268d03034abe695115c3365db5a74f1029c39be5feb0f72f808b43`.
Its file SHA-256 is
`3d89f90ac6489a021e1245def866a564e2d006dd40fc6c87e667f082b065eead`.
Independent review verified compact source/model/plan references, file metadata,
installed model-path expectations and all frozen launch limits. No accepted
artifact or original per-source manifest was changed.
