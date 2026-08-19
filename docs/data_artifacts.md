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

Task 03F.2's no-PDF preservation evidence is external under
`pipelines/brisbane_baylands/task_03f_corpus_extraction/offline_preservation/`
and keyed by production extraction identity. The report for
`exv1-bedd4c50a9614a74a6406d60148a08c44579f0b504bc3568042499f578c0cf7f`
binds the run-spec checksum and both inventory checksums, and records the exact
record, asset, support, warning/policy, and managed-file comparison. It is
control evidence only; it does not represent a source-PDF execution or a new
document candidate.

The target index is document-scoped stage-one evidence, not Task 03F's later
corpus index. The preservation support must prove that all 323 accepted aliases
and targets are bidirectionally namespace-remapped while retaining upstream IDs
as correspondence evidence. A separately counted table-alias extension is
permitted only from an exact standalone numbered label on the same page as
exactly one canonical table; it retains the upstream table target ID and has no
upstream alias ID. Mention candidates use only exact-number table targets within
ten physical pages, record the page distance, retain multiple distinct targets
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
    inputs/<checksum-named-input>.json
    accounting/<accounting_id>/
    target_indexes/<target_index_id>/
    resolutions/<resolution_id>/
    handoffs/<handoff_id>/
    attempts/<stage>/<stage_id>/<attempt>/
    contract_bundle.json
  attempts/<document_transaction_id>/
```

Task 03F.3 publishes these stage-two artifacts under synthetic tests and
reconstructs `contract_bundle.json` for the same schema and cross-record gate
used by the offline fixtures. Its maintained human-owned implementation passed
byte-identical equivalence against the transient Gate B MVP on the fixed Task
03F.2 evidence; the unused MVP code and dedicated equivalence test were then
removed. No source-PDF execution is implied by the implementation or its tests;
the optional smoke was waived and any variant belongs to a future activated
Task 03G contract.

Each final document, accounting, index, resolution, and handoff directory is
no-clobber, checksum-inventoried, completion-last, and atomically published.
Attempt directories retain diagnostics but cannot contain or impersonate a
valid completion. Scope records reference immutable document candidates rather
than copying or rewriting them. Review renders remain under the existing
disposable `review_cache` and outside semantic identity.

Task 03F.4 removed new-candidate proof artifacts such as rewrite-comparison
reports, mandatory repeat evidence, automatic render outputs, and the document
stage `preservation_report.json`. Existing external artifacts remain immutable
historical evidence and are not rebound or migrated. Current managed files
contain only content, active support/control records, identity, inventory,
checksums, attempts, and completion artifacts required by maintained validators.

Requested page, table, family, hierarchy, and region evidence is generated
separately under `review_cache`. A candidate-neutral render-plan manifest records
the exact sample and verifies immutable input checksums; a generated-review
manifest checksums any disposable outputs. Neither participates in candidate
identity, completeness, publication, acceptance, or Task 04 status.
`collections validate-handoff` verifies a published native-v2 handoff and
successful document candidates read-only without rebuilding them.

Task 03G.1 adds a separate diagnostic-only namespace:

```text
pipelines/brisbane_baylands/task_03g1_model_corpus_smoke/<smokev1-id>/
  attempts/<attempt-id>/
```

Its per-range parser records, page outcomes, routed table artifacts, resource
observations, inventory, and `diagnostic_summary.json` are incomplete smoke
evidence. They are not document candidates or stage-two artifacts and cannot
contain a complete-document completion, accounting, target index, resolution,
or handoff. The `smokev1-` identity binds the checked-in smoke spec, current
production extraction identity, and smoke-owned code without rebinding an
immutable `exv1-` candidate. Interrupted attempts remain inspectable; a later
invocation allocates a new attempt, while an existing diagnostic-complete root
is no-clobber.

Task 03G.1a's bounded affected-page regression is separate from both the
immutable Task 03G.1 smoke and production candidates:

```text
pipelines/brisbane_baylands/task_03g1a_remediation_v1/
  regression_manifest.json
  warning_scope.json
  routing_geometry.json
  learned_fallback[_vN]/<source_id>/pages/page_<NNNNN>/fallback/<region_id>/
  continuation_decisions.json
  report.json
  artifact_inventory.json
  completion.json
```

The checked-in regression manifest binds exact source checksums, pages,
controls, and expected dispositions. Per-region learned evidence retains the
trigger, checksum-bound model identity, native-token snapshot, normative crop,
raw prediction, measurements, and acceptance or abstention decision. Accepted
tables may also flow through ordinary page/table/family validation; abstained
regions have no canonical table IDs. The aggregate report is candidate-neutral
control evidence, publishes no document or corpus completion, is
checksum-inventoried, and writes its completion record last. It cannot replace
or mutate the `smokev1-`, `prv1-`, or `exv1-` roots it compares.
The original report and finalization pointer were superseded after user review
found that matched-column counts had been mistaken for OTSL grid dimensions.
The behavioral MVP reevaluation lives under
`pipelines/brisbane_baylands/task_03g1a_remediation_v5/`; v1 through v4 remain
immutable diagnostic/development evidence and are never silently overwritten.
The human-maintainability rewrite's first fresh v6 run is retained as explicit
failure-path evidence because a model-adapter boundary error caused safe
`model_failure` abstentions. The corrected, complete v7 run under
`pipelines/brisbane_baylands/task_03g1a_remediation_v7/` is normative. It
retains exact commands, refactor-preservation evidence, and the refreshed
production identity reference. The user accepted and closed Task 03G.1a on
2026-08-05; the immutable artifact's recorded pre-acceptance status is
historical evidence rather than the current task status.

Task 03G.2 owns completely fresh producer, document-content, and scope roots:

```text
pipelines/brisbane_baylands/task_03g2_document_producers/<prv1-id>/
pipelines/brisbane_baylands/task_03g2_canonical_records/<exv1-id>/
pipelines/brisbane_baylands/task_03g2_hierarchy_correction/<hcorv1-id>/
pipelines/brisbane_baylands/task_03g2_representative_pilot/
  documents/<source_id>/<docv1-id>/
  scopes/<scopev1-id>/
```

The three selected sources are `deir_main`, `deir_appendix_d`, and
`deir_appendix_p`. The first invocation may consume only their sealed Task 02
source records, current reviewed policies/models/code, fresh checked-in owner
plans, and checksum-sealed runtime lineage produced inside this task. It may
not reference any historical Appendix P `prv1-`, canonical `exv1-`,
`hcorv1-`, cross-reference `exv1-`, `docv1-`, or bounded-acceptance artifact.
Semantic and cross-reference runtime lineage records are derived only after
their fresh upstream candidates publish; they are managed control inputs and
must be inventoried rather than hidden in mutable process state.

The current authorization is preparation-only. No Task 03G.2 external root or
candidate should be created until the fresh-lineage implementation and config
schemas pass offline validation, and no source verification or PDF/model work
may occur before separate user approval. Review requests remain under the
existing candidate-neutral `review_cache/<candidate-id>/` root and do not enter
candidate identity or completion.

The stage-two corpus index lives below
`scopes/<run_scope_id>/target_indexes/`; it is not the Task 03E.5
document-local `support/cross_reference_target_index.json`. Corpus resolution
records similarly append references to stable stage-one mention IDs and must
prove that every stage-one managed-file inventory is byte-identical before and
after resolution.

Task 03G.3 does not rename or move any accepted Task 03G.2 or Task 03G.2f
artifact. Those roots, their v1/v1.1 schemas, and every derived identifier remain
historical evidence. Future runs use responsibility-oriented roots defined by their
new versioned run specifications:

```text
pipelines/brisbane_baylands/task_03h/
  inputs/
  document_parse_evidence/
    docling_conversions/<dconv1-id>/
    <prv1-id>/
  hierarchy_inference/<hcorv1-id>/
  document_records/<exv1-id>/
  document_publications/
    documents/<source-id>/<docv1-id>/
    scopes/<scopev1-id>/
```

Each `dconv1-` directory is an independently inventoried, completion-last raw
conversion bundle. Each `prv1-` directory names the exact upstream conversion seal in
`records/conversion_input.json`; its copied `documents/` tree is a compatibility view,
not a second inference result. Conversion attempts are retained only under
`docling_conversions/attempts/`, while derived-stage failures remain in the producer
attempt stream. Neither failure stream carries a completion marker.

Within a document-record candidate, `canonical/` remains the stable record-family
directory. Within a collection scope, `accounting/`, `target_indexes/`,
`resolutions/`, and `handoffs/` remain precise artifact names. Code and config path
changes intentionally produce new future identities even when normalized semantic
records compare exactly; accepted identities are never rebound.

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
