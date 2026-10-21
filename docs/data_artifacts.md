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
usability registry and Task 04D's original linking-dependent handoff are
separate upstream inputs. Task 06H's accepted replacement handoff and Task 05H's
immutable response inventory supply the later boundaries; exact identities and
closure are retained in their task outcomes.

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
original Task 04D linking replacement is rooted at
`pipelines/brisbane_baylands/task_04d_relinked_v1/`. Task 06H accepted the later
repaired handoff; Task 03J remains the immutable extraction source.
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
  releases/                 # frozen role-separated benchmark releases
```

Task 05's Final EIR Volume 4 inventory uses separate working, pilot, and final
publication layers:

```text
pipelines/brisbane_baylands/task_05_response_inventory/
  working/
    05h/accepted.json         # pointer written after supervised acceptance
    cache/                    # replaceable renders and materialized views
    <stage>/<revision-id>/    # named working revisions
  pilots/<pilotv1-id>/        # bounded qualification candidates
  <inventoryv1-id>/           # immutable releases; accepted.json designates the current one
    records/
    inventory/
    review_views/
    diagnostics/
```

Working and pilot outputs are not immutable releases. A compact gate record may
name one accepted working revision for declared downstream Task 05 consumers;
hold that revision fixed until those consumers finish. An output-affecting
change creates a new named revision rather than modifying one already consumed.
Do not promote working revisions as durable inputs beyond Task 05. Retain
compact configs, counts, findings, and fixtures needed to explain an accepted
decision, but allow regenerable records, HTML, renders, joined views, and caches
to be replaced or pruned after separate approval. Do not preserve every failed
iteration as a full payload.

Task 05 trusts the Task 02 source record and its recorded checksum for the
744-page Volume 4 PDF. Routine preflight verifies compact completion metadata,
expected path and byte size, source membership, and terminal state; it does not
reread the PDF solely to recompute its hash. Task 03J, Task 04A, and Task 04D
are likewise pinned through their exact identities, inventories, and compact
completion records without recursively hashing or copying their large payloads.
A deep byte audit is exceptional: use it only when a seal is missing, recorded
metadata disagree, corruption is suspected, or an explicitly approved archival
boundary requires it.

The 05H completion record closes the exact upstream identities, accepted Task
05 stages, schema, configuration, implementation, authoritative managed files,
counts, and final checksums. Hash newly authored authoritative records once at
publication, preferably while writing large Task-05-owned files. Routine reuse
then checks the sealed inventory, exact file set, and sizes. Regenerable review
views and caches remain outside checksum closure unless a curator decision
explicitly cites one as reviewed evidence. The final `review_views/` directory
contains compact ordered unit/edge indexes and rendering recipes; joined text,
HTML, and renders live in `working/cache/` and are regenerated from the single
source-text store. Store source-derived text once;
later graphs, target links, corrections, and release descriptors reference
stable IDs rather than duplicate payloads. The Task 05 namespace is not part of
the Task 03 model corpus and must not copy the raw PDF.

The Task 05H designation pointer is
`pipelines/brisbane_baylands/task_05_response_inventory/working/05h/accepted.json`,
relative to `ER_COMMONS_DATA_ROOT`. It remains outside the immutable release's
managed-file closure and is written last, after supervised acceptance succeeds.
Tasks 07 and 08 resolve it once and pin its inventory identity and completion
seal together with `inventory/components.json` and
`records/task07_task08_handoff.json`; they must not select the newest working
revision or silently follow a changed pointer during a run. Component references
retain the accepted 05D source text in its existing store and reference 05E/05G
artifacts without copying their payloads. The
[replacement result](specs/task07a1_final_result.json) binds the current pointer,
immutable release and downstream handoff. The [original result](specs/task05h_final_result.json)
preserves its historical release and acceptance. Explicit supersession changes
only the designation after verifying exact prior acceptance bytes. All inherited reference outcomes, substitution
warnings, sampled-review limits, and text-only evidence exclusions travel with
that handoff.

## Task 06 repair artifacts

The accepted repair and replacement handoff live under
`pipelines/brisbane_baylands/task_06_recovery_v1/`. They reference sealed
upstream source, conversion, producer, and review evidence in place; unchanged
sources retain their original manifests. [Task 06](../tasks/sprint2/06_repair_reference_sources_and_target_index.md)
routes the accepted subtasks. The [06G outcome](../tasks/sprint2/06g_replay_repaired_document_and_collection_stages.md)
owns replay namespaces and attempt history; the
[06H outcome](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
owns the accepted replacement handoff and sampled-review limitations.

## Git policy

### Tracked and external files

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

## Task 08F reviewed artifacts

The current combined human-reviewed export is
`task_08/08f_reviewed_20261009_v3/`, designated by
[the reviewed result](specs/task08f_combined_review_result.json). It consolidates
49 approved answers and the explicitly approved bounded supplements. Earlier
preparation and reviewed exports remain immutable. The final handoff binds exact
case records, human decisions, source inputs, supplemental history inventories,
validation and independent audit; completion is written last over the exact file
inventory. Generated combined answer rendering does not claim a new chat display.
Future consumers must use this designated handoff rather than infer authority from
filenames or historical preparation placeholders.


## Task 08 frozen benchmark release

The [Task 08 final result](specs/task08h_final_result.json) designates
`benchmarks/er_bench/releases/task08_20261009_v1/`. It freezes all 49 approved
cases and the approved 19/30 allocation. `target/` contains only exact questions
and case IDs. `curator/` retains answers, citations, approvals, source-comment
mapping and attrition. `corpus/` binds the full 35-document accepted source set
and usability/edition provenance for a later retrieval builder; it is not a
case-specific gold-source list or a target prompt payload.

`handoff.json` and completion-last `completion.json` bind the exact file set,
validation and independent audit. The included `provenance/verify_release.py`
checks the frozen release and dependencies through the repository's `uv` runtime.
This is an artifact-specific verification snapshot, not a new production CLI.
Keep source artifacts in place and preserve source terms; local release does not
imply public redistribution permission. Later loaders must enforce the declared
role boundary; directory separation alone is not filesystem access control.

The current revised question/answer release is selected by the
[09F v2 publication pointer](specs/task09f_question_publication_v2_result.json).
It retains the split and corpus and preserves its predecessor releases. The
release snapshots the [maintained adequacy policy](specs/adequacy_labeling_rules.md)
for provenance; publication does not migrate synthetic labels, prompts or runtime.
Case-specific calibration material stays outside that general policy and outside
judge prompt examples. Authorized design exposure is recorded in release provenance.

## Task 12 reporting artifacts

Offline reports live beneath `pipelines/brisbane_baylands/task_12/` in a fresh
explicit namespace. JSON/CSV tables preserve exact model/run/repeat/candidate/point
identities, automatic diagnostics and separate historical judge agreement. PNG
and SVG charts derive from those tables. `manifest.json` binds consumed source
files, frozen configuration, accepted reviews, implementation and runtime;
`completion.json` seals output bytes. Identical replay verifies byte equality;
changed inputs or implementation require a new namespace. No upstream seal is
modified. The [result](specs/task12_result.json) selects the accepted publication;
preview and visual-QA directories are not designated results.

## Task 13 locked artifacts

A fresh `pipelines/brisbane_baylands/task_13/` run holds preflight bindings,
all 180 planned slots, split-only projected inputs, exact requests/responses and
per-slot completion inventories. The create-only ledger reserves liability before
wire dispatch, retains uncertain liabilities, and never retries an attempted key.
A task-wide `paid_run_claim.json` binds the sole paid namespace, preventing a
second ledger from resetting the spending cap. Partial attempts remain intact;
resume under an active contract can process untouched slots but never replays a
partial slot automatically. Historical policy stops remain in sealed ancestor
snapshots; closure does not authorize another run.

The run's completion seal is written only after every worker drains. A separate
sealed reporting publication feeds `test_30_review/`, containing final figures,
tables and `START_HERE.html`; provenance remains adjacent. Preflight or billing
failure is not a completed evaluation and does not produce a results gallery.

The accepted Task 13 publication is selected by
[its result pointer](specs/task13_result.json). The final sealed run is
`pipelines/brisbane_baylands/task_13/locked_test_continue_20261020_v4/`; the
sealed reporting directory is the sibling `locked_test_reporting_20261020_v4/`
and the final gallery is `test_30_review/START_HERE.html`. All 180 evaluations
are complete: 90 per model, all 30 questions and three fresh answers each.
Development results and synthetic judge diagnostics remain separate.

## Task 14 selective review artifacts

The completed [Task 14 contract](../tasks/sprint2/14_selective_failure_review.md)
owns a fresh review namespace beneath
`pipelines/brisbane_baylands/task_14/`. Its selection manifest binds exact saved
Luna/Haiku answer, repeat and point identities to the designated Task 13 report
and supplied evidence. Six answer instances are the intended stopping point;
the same-question Luna-pass/Haiku-fail pair counts as two. A named unresolved
question and recorded additional selection are required before expanding toward
the twelve-answer ceiling.

Keep structured case notes and an append-only user-review journal outside all
upstream seals. Each record identifies the displayed version, evidence links,
frozen outcomes, agent interpretation, user feedback and explicit disposition;
unreviewed proposals remain pending. Revisions preserve earlier displayed text
and decisions. A concise final synthesis distinguishes accepted interpretations,
uncertainty and selection limitations. This review adds commentary; it does not
rescore answers, change frozen publications or authorize new model calls.

## Task 15 planned judge-revision artifacts

The [Task 15 plan](../tasks/sprint2/15_revise_conclusion_judge.md) owns fresh
versioned artifacts under `pipelines/brisbane_baylands/task_15/` for C policy,
synthetic expectations/reviews, six/nineteen-question development comparisons,
full-thirty reevaluation, native receipts and bounded conclusion review. It does
not overwrite Task 09/11/12/13 publications. Saved-answer comparisons preserve
original candidate identities and automatic/A/G/S outcomes; any fresh-generation
arm has separate identities and evaluations. Result pointers distinguish original
and revised conditions. No Task 15 run has started; the contract owns activation,
exposure disclosure, numerical limits and selection gates. Task 16 consumes the
accepted publications for writing.

## Historical and development artifact routing

Completed curation, judge qualification and prompt experiments retain their
original namespaces and seals. Their detailed directory histories are in the
[artifact history](history/artifact_history.md); task outcomes and result pointers
own exact identities. Use the [judge maintainer guide](judge_maintainer_guide.md)
and [reporting maintainer guide](reporting_maintainer_guide.md) for current
interfaces, not commands or run descriptions in historical records.

Development inputs and reserved judge challenges stay separate from test inputs.
Only the model-visible payload enters requests; restricted expectations and source
mappings remain evaluation evidence. Synthetic diagnostics cannot establish
benchmark performance. Saved generation/evaluation attempts retain native
requests, counts, outputs, failures and identity bindings; incomplete or uncertain
attempts cannot be reused as successful results or silently dispatched again.

The archived [Task 13A MiniMax side experiment](../tasks/sprint2/13a_minimax_cloud_comparison.md)
remains under `pipelines/brisbane_baylands/task_13a/`. Preserve its publications,
receipts and seals in place; exclude it from presented benchmark results and
Task 14 review. Luna/Haiku results are selected only by the Task 13 pointer.
