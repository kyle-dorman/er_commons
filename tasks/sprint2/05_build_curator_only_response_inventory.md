# Task 05: Build the Curator-Only Response Inventory

Status: **planned umbrella; decomposed into provisional Tasks 05A through 05G;
not activated**.

## Abstract

Build a complete, separately identified inventory of the comment and response
units in Final EIR Volume 4. Preserve source structure, provenance, explicit
relationships, and official Draft EIR references without adding Volume 4 to the
Task 03 model corpus.

Task 05 is an umbrella, not an executable contract. Only Task 05A may be
activated first. Tasks 05B through 05G remain provisional and must be revised
from the accepted preceding outcome before activation. This prevents source
discovery, contract design, implementation, full-source execution, graph
resolution, human QA, and publication from accumulating inside one task.

## Goal

Produce one curator-only inventory that later Task 06 and Task 07 work can pin,
while keeping every semantic transition independently reviewable:

```text
frozen source
  -> bounded structural understanding
  -> record and identity contract
  -> qualified producer
  -> complete source-unit inventory
  -> intra-Volume response graph
  -> Draft EIR target links
  -> reviewed and frozen inventory
```

## Fixed boundaries

- Final EIR Volume 4, source ID `feir_volume_4`, is curator-only and never
  enters the Task 03 model corpus.
- Task 03J remains the immutable extraction source. Linking-dependent use pins
  Task 04D's designated replacement handoff and Task 04A's accepted usability
  registry; it does not compose superseded Task 03J links with Task 04C.
- Appendix Q is not a second Task 05 extraction source. Record
  `requires_appendix_q_verification` when Volume 4 lacks necessary full-letter,
  attachment, or testimony context.
- Inventory construction is deterministic. No LLM creates, segments, links,
  triages, or repairs source units.
- Task 05 human review decides transcription, segmentation, anchor, and link
  correctness. Task 07 owns response-outcome judgment, two-pass eligibility,
  substantive-link classification for clustering, and benchmark acceptance.
- A linked response remains a separately identified source unit. Derived review
  views never flatten away its ID, anchor, or relationship provenance.
- Every unmatched unit or reference has an explicit diagnostic; nothing is
  silently dropped or guessed into a one-to-one relationship.

## MVP hashing and storage policy

Task 05 must remain cheap to iterate:

- Bind the 744-page source PDF by the already-frozen Task 02 source record,
  checksum, byte size, and source ID. Routine Task 05 preparation, pilots,
  reruns, and validation must not reread the PDF solely to recompute its hash.
- Bind Task 03J, Task 04A, and Task 04D through their owning completion records,
  identities, inventories, and recorded checksums. Do not recursively rehash
  their large document or collection payloads.
- Check existence, expected path, recorded size, identity membership, terminal
  state, and compact completion metadata before use. Rehash a large sealed input
  only when its owning validator requires it, recorded metadata disagree, or a
  specific integrity concern is approved for investigation.
- Keep mutable experiments under
  `pipelines/brisbane_baylands/task_05_response_inventory/working/`, using
  `<stage>/<revision-id>/` for records and `cache/` for replaceable renders and
  materialized views. Working artifacts are not authoritative releases and are
  excluded from final production identity. Material cleanup still requires
  explicit approval.
- Keep pilots bounded under `pilots/<pilotv1-id>/`. Retain only the compact
  decision evidence needed by the next task; do not duplicate the source PDF or
  sealed upstream payloads.
- At each gate, name one accepted working revision for every declared downstream
  Task 05 consumer and hold it fixed until those consumers finish. It is not a
  no-clobber release: if evidence requires a change, create a new working
  revision and compact decision record rather than modifying a consumed revision
  or preserving a full copy of every attempt.
- Publish one immutable accepted release only under `<inventoryv1-id>/` in Task
  05G. Earlier task outputs are working candidates, not releases.
- Store source-derived text once. Graphs, target links, corrections, and release
  descriptors reference stable IDs rather than copying payloads.
- Hash compact schemas, configs, decisions, manifests, and authoritative final
  records once at publication. For a large Task-05-owned output, calculate its
  digest while writing it when practical. Routine reuse checks the sealed
  inventory, exact file set, and sizes; a separate deep byte audit is exceptional
  rather than part of every task gate or rerun.
- Treat HTML, renders, joined review views, and other regenerable caches as
  non-authoritative unless a curator decision explicitly cites one as reviewed
  evidence.

## Inputs

- Frozen Task 02 source record for `feir_volume_4`.
- Final EIR Volume 4, `Responses to Comments on the DEIR (Chapters 11 through
  13)`, a 744-page PDF beneath the external artifact root.
- Task 03J production extraction
  `exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773`.
- Task 04A accepted usability registry under
  `reviewv1-task03j-final-c17/gate_d/`.
- Task 04D designated handoff
  `handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`.

The source path relative to `ER_COMMONS_DATA_ROOT` is:

```text
datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_deir_sources_v1/
  sources/curator_only_response_source/feir_volume_4.pdf
```

## Subtasks

1. [Task 05A](05a_qualify_and_profile_response_source.md): bind upstream inputs,
   profile representative Volume 4 structures, select the bounded route, and
   estimate workload without implementing the production producer.
2. [Task 05B](05b_define_response_inventory_contract.md): freeze schemas,
   identities, anchors, correction semantics, artifact dependencies, and
   source-free validators.
3. [Task 05C](05c_build_response_inventory_pilot.md): implement the narrow
   producer and qualify it on a bounded, structurally varied pilot.
4. [Task 05D](05d_build_complete_source_unit_inventory.md): complete the
   source-unit run and name one accepted working revision without
   relationship-policy experiments or immutable release publication.
5. [Task 05E](05e_build_response_relationship_graph.md): resolve intra-Volume
   comment and response relationships and publish graph diagnostics and views.
6. [Task 05F](05f_resolve_official_draft_eir_references.md): resolve official
   Draft EIR references against Task 04D and annotate Task 04A usability.
7. [Task 05G](05g_review_and_freeze_response_inventory.md): conduct curator QA,
   record sparse dispositions, route output-affecting corrections back to their
   owning stage, and publish the sole immutable Task 05 release after re-review.

Unexpected failures do not silently enlarge the active task. Preserve a compact
stop record, define a bounded remediation task only when evidence requires it,
and create a fresh accepted candidate when output-affecting code or policy
changes.

## Final outputs

The accepted namespace must contain `records/`, `inventory/`, `review_views/`,
and `diagnostics/`. At minimum it preserves:

- stable comment, response, general-response, commenter, and letter IDs;
- exact Volume 4 page and text anchors plus original text;
- explicit one-to-many and many-to-one response relationships;
- raw and resolved response, general-response, and Draft EIR references;
- Task 04A usability annotations without copying the registry;
- orphan, ambiguous, unresolved, and Appendix-Q-needed diagnostics;
- compact linked-view indexes and rendering recipes that preserve unit, edge,
  anchor, and ordering provenance without duplicating source text; and
- one final identity, managed-file inventory, publication-time output digests,
  and compact completion record.

## Umbrella acceptance criteria

- Tasks 05A through 05G close in order, with only one active at a time.
- Each task owns one semantic transition and revises its successor from observed
  evidence.
- The final inventory accounts for every identifiable source unit or diagnostic
  and validates graph relationships in both directions.
- Repeated construction from the same sealed inputs produces the same semantic
  records and stable IDs.
- No large sealed upstream input is repeatedly rehashed or copied as routine
  Task 05 validation.
- Working and pilot iterations remain separate from the immutable final
  publication, and the final package is independently understandable and
  restartable.

## Non-goals

- Adding Volume 4 or Appendix Q to the model corpus.
- Extracting Appendix Q as part of Task 05.
- Response-outcome classification, eligibility screening, clustering, or split
  selection; Task 07 owns those decisions.
- Benchmark retrieval, reference-defense authoring, target generation, judging,
  or evaluation.
- A workflow framework, permissions system, content-addressed artifact store, or
  repeated integrity scan of previously sealed large artifacts.
