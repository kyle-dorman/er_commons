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

## Task 08 group artifacts

The authorized combined 08C pass uses the separate
`task_08/08c_combined_20261001_v1/` namespace with immutable input completion,
restricted provenance, historical bindings, numbered journal snapshots and
progress checkpoints. It does not replace historical per-group records; see the
[combined review contract](specs/task08c_combined_chat_review_v1.md).


Task 08 uses `pipelines/brisbane_baylands/task_08/<group>/<stage>/` beneath the
configured data root. Each saved ranking has a fresh no-clobber directory with
its input packet, advisory proposal, handoff, validation, versioned interface
snapshots, manifest and completion. Working drafts stay distinct from completed
packets. The compact batch register references completed packets and pending
next stages; it does not assign human labels. Upstream releases remain in place.

Remaining-group 08A preparation uses fresh `<group>/08a/ranking_v2/` outputs
and a separate `preparation_20260930_v2/` progress ledger and qualification receipts.
Each group transitions through pending/running to completed or blocked, independent
of the others. Small-group manifests distinguish deterministic preparation with
no model invocation from Astra-ranked groups. Source-page supplements preserve
exact page text separately from original source units. Register merges preserve
preceding bytes and all concurrent non-08A rows; health-risk v1 remains sealed.


08B v2 uses a fresh `<group>/08b/selection_v2/` directory for trusted prepared
inputs/interface snapshots, project receipts, verification and later versioned
native exports. Shared synthetic qualification is under
`task_08/qualification/08b_selection_v2/`, outside dataset annotations. V1 remains
preserved; v2 also retains a predecessor snapshot, supersession record and later
export-bound chat confirmation. The mutable
batch register preserves its preceding bytes before updates; sealed 08A and
historical review artifacts remain unchanged.

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

## Task 08C wording artifacts

First-use health-risk artifacts use `task_08/health_risk/08c/wording_v1/`.
Comment-only model packets and imported review tasks remain separate from the
restricted source mapping and upstream references. Shared source-free UI
qualification uses `task_08/qualification/08c_wording_v1/`. Proposals and native
exports are versioned and no-clobber; only explicitly approved exact saved text
can enter the eventual frozen handoff. A pending review receipt is not completion.

Chat review uses a fresh `task_08/health_risk/08c/chat_review_v1/` namespace and
references the original `wording_v1/` packet/proposal in place. Save immutable
journal snapshots, displayed versions, verbatim feedback, explicit decisions and
validated exports. The current handoff records `task08c.chat_review.v1`. Preserve
previous batch-register bytes and existing project artifacts; workflow amendment
does not migrate or fabricate human approvals.

## Task 08D claim artifacts

Health-risk first use is under `task_08/health_risk/08d/claims_v1/`. The active
source packet is `input_v3/packet.json`; earlier preparation revisions remain
preserved and unused. Separate two-pass inventories, proposal revisions,
independent reviews, trusted prepared tasks, project receipts and pending-review
handoffs retain exact source and question bindings. No saved human approval is
inferred from a prepared project. Qualification fixtures and their automated
annotations live separately under `task_08/qualification/08d_claim_review_v1/`.
Only a validated saved human export can publish advancing claims; unresolved
scope and all other dispositions remain in the stage history.

The v2 interface replacement uses `task_08/health_risk/08d/claims_v2/`, referencing
unchanged v1 source/inventory/proposal files. It preserves the prior project and
unsaved draft without migration. Separate `qualification/08d_claim_review_v2/`
records verify the removed source-ID control, larger editors and fixed source
bindings. Prior readiness and batch-register bytes remain preserved.

## Task 08E evidence artifacts

The original 50-case Phase A run uses `task_08/08e_combined_20261006_v1/`.
The authorized C014/C020/C024 supplement uses `task_08/08e_supplement_20261007_v1/`;
its authorization and frozen inputs preserve the historical holds and claims.
The combined 53-case handoff uses `task_08/08e_combined_53_20261007_v1/` and
references both separately sealed components without modifying either.
Each case retains its exact input, five-track plan and budget revisions, planned
queries and raw receipts, source occurrences, Astra provenance, research packet,
table-render checks and independent coverage/export review. The preparation
completion seals each component only after all its cases validate. Human journals
begin empty and later review must live outside that preparation seal. This path
does not reuse historical human decisions or create a shared source queue.
See the [current packet contract](specs/task08e_batch_research_v1.md) and
[chat contract](specs/task08e_chat_review_v1.md).

Shared synthetic qualification and the read-only upstream audit live in fresh
`task_08/qualification/08e_*` directories, outside health-risk dataset decisions.
Preserve invented canonical inputs, prepared task/form snapshots, project IDs,
browser evidence, native annotations/exports, validators and independent reviews.
Simulated advance labels always export zero advancing claims and no next stage.
Qualification is not a health-risk evidence packet or eligibility decision.
Live `health_risk/08e/investigation_v1/` artifacts bind the accepted 08D
`claims_v2/exports/investigation_v1/handoff.json`. Preserve the exact input closure,
source-only search receipts, Astra prompts/proposals and amendments, every hit
and reference disposition, fresh render/association audits, assembled canonical
packets, blank native project snapshots and subsequent saved decisions. The batch
register is updated only after saving its previous bytes. Investigation does not
establish source support or eligibility; eligibility tasks bind saved evidence.
See the [08E task](../tasks/sprint2/08e_review_group_evidence.md) for readiness.

Remaining-group 08B setup uses `task_08/selection_setup_20260930_v2/` for its
compact review index, per-group project receipts and preserved register snapshots.
Trusted queues remain under each `<group>/08b/selection_v2/prepared/`; the shared
intake revision qualifies in `task_08/qualification/08b_intake_v2/`. Synthetic
annotations stay separate from dataset projects. Setup receipts indicate readiness
only, retaining full source and template identities for later confirmed exports.

Combined Task 08D preparation stores fresh `input/` packets and separate context
notes, per-case `cases/` model inventories/proposals/invocation receipts,
independent `review/` findings, and a checksummed prepared queue beneath the
explicitly named Task 08 batch root. The preparation handoff seals blank decisions;
a subsequent `human_review/events.jsonl` is an append-only writable journal outside
that seal. Preserve earlier model revisions and all historical health-risk/practice
artifacts. The [chat specification](specs/task08d_combined_chat_review_v1.md)
owns startup, mutation checks and export gates.

## Task 08F preparation artifacts

Combined Phase A uses a fresh `task_08/08f_preparation_20261008_v1/` namespace.
Its frozen intake and per-case prompts contain only current approved evidence
scopes, retaining complete canonical text and table cells. Numbered attempt
directories retain exact invocation, raw output, process/event logs, validation,
short excerpt locators and proposed displays, including failures and retries.
The ordered handoff and readable review material are sealed by an exact
completion-last file inventory. Existing 08E eligibility is provenance; all new
08F approvals and final dispositions remain null. Later human display events,
feedback and revisions must live outside this preparation seal. Synthetic
qualification stays under `task_08/qualification/08f_*`.


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
