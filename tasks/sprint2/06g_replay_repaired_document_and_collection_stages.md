# Task 06G: Replay Repaired Document and Collection Stages

Status: **Complete and accepted. The user accepted the successful v38 execution
and finalization outcome on 2026-09-12 and authorized its local commit. Push
remains unauthorized.**

## Abstract

Combine the qualified replacement F1 and accepted structural/target repairs into
one coherent fresh document/collection lineage. Reuse sealed conversion,
producer, and unaffected evidence wherever the owning contracts allow it.
Rebuild only invalidated descendants and account for every semantic change.

This task publishes a mechanically validated replacement candidate for Task
06H review. It does not accept human usability, replay Task 05F, or promise
that every deferred mention will resolve.

## Goal

- Consume final accepted repair policies from Tasks 06C-06F.
- Preserve accepted Task 02/03J/04A/04D evidence without relabeling it.
- Apply the final policies to F1 without repeating its accepted conversion.
- Rebuild affected document and collection stages under fresh identities.
- Produce explicit old/new source, entity, stage, and review correspondence.
- Deliver complete change accounting and reproducible terminal evidence to 06H.

## Inputs and prerequisite gate

Read `docs/architecture.md`, `docs/data_artifacts.md`, the accepted Task 06A
impact/design record, both Task 06B gate outcomes and filename map, and Tasks
06C-06F outcomes. Do not execute provisional policies or choose unresolved
chapter boundaries during replay.

Baseline Task 04D handoff:
`handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`.
Its production identity is
`exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3`
and its scope is
`scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da`.
Resolve exact paths and seals from the accepted Task 04D outcome and Task 06A
binding table; do not find inputs by newest-directory or filename heuristics.

Task 03J remains immutable extraction evidence under
`pipelines/brisbane_baylands/task_03h_clean_full_v4/`.
Task 04A review is `reviewv1-task03j-final-c17`.
Task 05F partial candidate is
`rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83`.
Task 06A pins unchanged accepted Task 05D/05E candidates and the 511-mention
population; this task consumes their compact census, not their resolver.

Required repair inputs are qualified F1 source and sealed conversion/producer
records from 06C; duplicate-heading policy from 06D; chapter-target policy from
06E; and caption-backed figure policy from 06F. Each must carry accepted schema,
configuration, code identity, tests, and explicit owner/resume stage.

## Phase 1 frozen replay plan

This is an MVP data-pipeline replay and evidence-maintenance task. Review must
prioritize functional correctness, provenance, contract closure,
maintainability, reproducibility, and MVP fitness. It is not a cybersecurity
project or security audit, and speculative hardening is outside scope.

### Accepted inputs and preserved boundaries

All paths below are relative to `/Volumes/x10pro/er_commons/` unless absolute.
Selection is by the stated path, identity, and seal, never newest-directory
discovery. Phase 2 preflight must compactly verify these records without opening
or rehashing preserved PDF/image payloads. The accepted repository basis is
commit `ff5613075c1e73d66e487381566e33dbfc6778f4`.

| Evidence | Exact accepted binding |
| --- | --- |
| Original 35-source release | `datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_deir_sources_v1/records/source_manifest.json`; manifest SHA-256 `fede3e4af815378b77a7f7f54c863ef095328da789859d4f4b25a524f3408f38`; completion SHA-256 `d1175d6bf54d2c557293cb7bb0e1191250a9b5db2aef5c9e563ebe01e58767a6`; 48,341 pages |
| Task 03J production | `pipelines/brisbane_baylands/task_03h_clean_full_v4/`; production `exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773`; handoff `handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325`; scope `scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893`; handoff completion SHA-256 `8bd72f2712a20de5aa865575566e4d5b187d7fccc02ba02dd0f92d87bf04117a` |
| Task 03H source-family catalog | `pipelines/brisbane_baylands/task_03h_clean_full_v4/inputs/brisbane_baylands_2025_deir_task03h_v4_source_family_catalog_v1.json`; SHA-256 `ad20c9abcb0d1b45c9bb7de5925f026c5e4c209c98da632bc7b3fc52c3006b9c`; comparison input only because its physical F1 binding is superseded |
| Task 04A review | `pipelines/brisbane_baylands/task_04_review/reviewv1-task03j-final-c17/`; `records/toc_review_decisions.json` SHA-256 `eb3c1242f13b76ffc0c1ac165954348cb6de560dbba8d58aba53c8d8237f46df`; `gate_d/usability_registry.json` SHA-256 `0453aaf13cb7762e7718ce869ee3f1521a67625224bd35c83b641cc5ae8d47e1`; 757 decisions and 35 usability rows |
| Task 04D baseline | `pipelines/brisbane_baylands/task_04d_relinked_v1/`; production `exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3`; scope `scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da`; handoff `handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`; handoff completion SHA-256 `387a07d62d96e4c5aba6f1f3d51f7f9026719b0d7de1b4eece06bed9fd78bc81`; target index `idxv1-31a3eacee1d03001d44f79d2fa15563cfd416b9a80c02e8d178d0843e4bb4a00`, completion reference SHA-256 `a661cfefed67927b7536fe791eb6f6dcfe705dc044e4e4dc9867977790cdfa31`; resolution `resv1-193a7e357cc4565b514457feb2473316dbf5765c5794bd13f0bbb90d17b42965`, SHA-256 `abc50336b20b77e7e92d9621eb2827fb8f29fc6d5c7385f7c440b33302940d95` |
| Accepted Task 05 controls | 05D `revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030`, acceptance-pointer SHA-256 `e124c7da14f1307631a27a118b5a7811af5aa70597fc300260fcc1f3a3f3b6fe`; 05E `revisionv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1`, acceptance-pointer SHA-256 `4ee50aad363505b244e28d8e6d2e62e8afc397822e83306f1b736fcfaae3bf48`; 05F `rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83`, rule-receipt SHA-256 `5088c82be0530ad02992f9fcd40fc5874864f5dbcce0468a51297fbf61331fc7`, semantic digest `8dcd3af81b10003c49ee0588bd01a5ce8f5e778f41159bdf8b3769794dbf80ac` |
| Task 06A recovery packet | `pipelines/brisbane_baylands/task_06_recovery_v1/06a/`; packet inventory SHA-256 `83c314339a05a86abb433874b9d7ff82833696ff065451812be7b8937dfb34e7`; `accepted_input_bindings.json` SHA-256 `8f7502ff26f31a341e355d051bf8b77511c6264dd9ad3740a51ed2cd62c7e3cf`; `source_slots.json` SHA-256 `534cb008c6a337cee76dd8b23479d95c014d030997caa5b4dc055f896c68c640` |
| Task 06B reuse qualifications | `pipelines/brisbane_baylands/task_06_recovery_v1/06b/gate2_conversion_qualification_v1/qualification.json`, SHA-256 `b61ee0e9b83ee52ceb6141f265c3a75fcaf83ee7b643e6b474894bf4b83c5803`; `06b/gate2_document_qualification_v1/qualification.json`, SHA-256 `5da9fcd49f9ef14706f9984bcc72d89d455154ad2d5f61e385ba3b7e00e67dfb`; 35 conversion/producer pairs, 20 chunked sources, 318 ranges, and 70 accepted document candidates |
| Final F1 selected source | Logical slot `deir_appendix_f1`, physical source `feir_appendix_f1`, source SHA-256 `e13c5b53f0f4da6a91f52ac784acce06619eeffd3fe053542d7ce1593b957e5e`, 68,389,743 bytes, 756 pages; manifest `pipelines/brisbane_baylands/task_06_recovery_v1/06c/gate3_inputs_v1/source/records/source_manifest.json`, seal SHA-256 `99ccc11d5229bb67f591a0fbce82934d04e6d6e4ba4b8dc84eacfc59ab0ac593`; completion SHA-256 `f29ebf55265062b157ba7248dd70a8d397321c8b57074afabbcaa4148f9a71c0` |
| Final F1 reusable processing | Conversion `dconv1-b6c5f62355c98d7ad588c455caaa987f7c7d99f896a86a219f2b0821c5693356`, completion SHA-256 `b98a1dabf3e1d6473c1530a98b65d00dacee57191c46402a378b3c4203f652a2`, inventory SHA-256 `05c555fb3fb4cbf0e049312fc0bbda8eb7f5c38c8ec979b64e831c90a8b3c441`; producer `prv1-01c8e77c10303f8d54d4a34ebe38b489699386897a8d4c78a931f371bafbcb36`, completion SHA-256 `52fb25b80048af7dcc67e54ffee1914984a1e4f647ef12d1f9a84d5bd3013e1e`, inventory SHA-256 `a2150e2473e2dbd4d73aff1a036625d4ce58da3a1ae46f4820da228f27f17211`; four-range plan `dplan1-dc4cd61060268d03034abe695115c3365db5a74f1029c39be5feb0f72f808b43` |
| Appendix A accepted repair | 06D packet `pipelines/brisbane_baylands/task_06_recovery_v1/06d/qualification_v8/`; completion SHA-256 `c5c6a2b7f2196dd1d3f49c8ab47fe5dd61f1a55013980112b92211591b644ebd`; inventory SHA-256 `8f046456effb7f1b22bbb170f85b7b7829a246c158acf343e4aa5dee0d7ea48b`; exact reusable mapping, hierarchy, Task 03J structure, and Task 04D linked-candidate paths are selected from Task 06A `source_slots.json` and checked against this packet before identity generation |
| Main accepted repairs | 06E packet `pipelines/brisbane_baylands/task_06_recovery_v1/06e/qualification_v13/`, completion SHA-256 `1522d2796c3bd917b8b6544e3c5ee68d760e2b08063fc2a70af193e48ac5d497`, inventory SHA-256 `80d695f53dd08d12381a7c15b3e6f7e798e33648dab39a00ca048b6e15f6ef2b`; 06F packet `pipelines/brisbane_baylands/task_06_recovery_v1/06f/qualification_v10/`, identity `figqualv1-4c8002030423eaf6714ca5fb98ee3926d6cfda030d4cae3cfc367f0959ad8b14`, completion SHA-256 `f6420863cc1e62de6cc82867f01af0d22d9086504b52cd4c3ab7f390dcdd50b6`, inventory SHA-256 `589264619acde4b595c8e0cb6cf51d69fad16da059cc57eb5331ccbb3db5e767`; exact reusable mapping, hierarchy, Task 03J structure, and Task 04D linked-candidate paths are selected from Task 06A `source_slots.json` and checked against both packets before identity generation |

The old 75-page `deir_appendix_f1` source (SHA-256
`dd51b7e5f0d511abc34617c10afde270e27d5dfe5df7ae9b7048cc206528ac78`)
and every descendant remain immutable comparison evidence, never valid selected
F1 input. Accepted conversion, producer, canonical record, hierarchy, review,
and Task 06B reuse boundaries remain intact. Task 05 products are read-only
controls. No extraction, PDF reopening, image rendering, model loading, or
preserved PDF/image payload hashing belongs to this replay.

The accepted Task 06D/06E task outcomes and current routing records are the
authority for their later acceptance. Their sealed packets retain
publication-time `acceptance pending` wording and remain immutable; Phase 2
must neither edit that wording nor misinterpret it as current rejection.

### Hard source-free integration gate before production

The repository is not yet executable against the accepted mixed lineage. The
only Task 06 document structure config,
`configs/task06/v1/deir_main/document_structure.json`, still contains all-zero
baseline, producer, and hierarchy placeholders and no authorization. There are
no final Appendix A, Final F1, relink-preparation, document-generation, or
collection-generation specs. The maintained mixed-membership verifier currently
requires `MODEL_CORPUS`, while the accepted Final F1 manifest truthfully records
`qualified_substitute`; it also requires a standalone
`er_commons.recovery.source_substitution.v1` shape that the sealed 06C records do
not claim to implement. Finally, linking-v2 enables FC1 globally although only
`deir_main` has an accepted 06F qualification packet, and that packet is bound
to the old main linked namespace
`exv1-d1bbac8a4979836add501c88c3522b908aeefee66b95cf8cef07abda1c30d28c`.
The maintained spec preparer currently clones Task 04D bindings without
expressing mixed membership or per-source resume stages, while relink preflight
and publication require repaired candidates to remain members of the old
handoff/production and retain the old structured completion. Those checks must
be extended to verify the replacement lineage, not bypassed or weakened.

As the first source-free subphase after explicit Phase 2 authorization, and
before any production artifact write, a narrow integration change must:

1. freeze deterministic request/identity recipes for Final F1, Appendix A, main,
   the 32 preserved documents, and their collection descendants;
2. let the maintained verifier consume the truthful qualified-substitute role
   and a standalone substitution record derived only from sealed 06A/06C
   evidence, without changing either predecessor's semantics or bytes;
3. support the declared mixed lineage: preserved Task 04D products plus fresh
   Final F1 and repaired Appendix A/main products by versioning the relink
   contracts to distinguish `base_membership_ref`, selected replacement
   document/completion, and required correspondence/change class;
4. reconstructively validate the accepted 06F FC1 policy/evidence against the
   rebuilt main candidate and compare every result to the old namespace-bound
   packet, without reopening model or source stages;
5. gate FC1 alias publication to this rebuilt `deir_main` validation;
6. version the authority-aware template-to-resolved-spec boundary and bind each
   no-clobber concrete spec digest into its downstream identities; and
7. prove these properties, deterministic identities, exact closure, no-clobber,
   and prohibited source/model operations with focused synthetic tests.

This gate may add only narrow maintained integration glue and tracked specs. If
it changes a 06D, 06E, or 06F repair decision, stop and return to that owner. Its
exact diff, focused tests, generated identities, specs, and paths require Astra
review and user acceptance at the frozen preflight checkpoint before production
replay; the current Phase 1 plan does not authorize implementing or executing
it.

### Reuse, rebuild, and dependency rationale

| Product | Phase 2 treatment | Reason |
| --- | --- | --- |
| All 35 source payloads; all accepted conversions/producers | Reuse by compact seal; Final F1 uses the 06C lineage | Source selection changed one logical slot, but no accepted upstream processing needs repetition |
| Final F1 heading evidence, mapping, hierarchy, semantic structure, aliases/links, publication | Reuse the 06C conversion/content producer, build the separate heading-evidence producer source-free from that conversion, then build every listed descendant fresh | The replacement has no accepted Task 03J/04D heading or later descendants; never correspond it to the wrong old F1 by text similarity. If one producer is proposed for both content and heading roles, the integration gate must prove that six-role identity contract explicitly |
| Appendix A structure/membership, aliases/links, publication | Build from the accepted 06D projection; reuse mapping/hierarchy/content/geometry/page labels | Duplicate Chapter 06/08 targets change semantic membership and destinations, not upstream canonical evidence |
| Main structure/membership, aliases/links, publication | Build from the accepted 06E projection; reconstructively validate the accepted 06F FC1 policy/evidence on that rebuilt candidate; reuse mapping/hierarchy/content/geometry/page labels | Chapter 8/9 and FC1 extend accepted semantic targets without reopening extraction, while the old namespace-bound 06F packet remains comparison evidence |
| Other 32 document structures | Preserve accepted Task 04D semantics and upstream records | No document-local repair applies |
| Other 32 linked publications | Republish/relink under the fresh global production identity, with mapped semantic equality required | Incoming targets, source catalog, scope, and collection policy are identity dependencies even when local content is unchanged |
| Collection accounting, target index, cross-document resolution, handoff, inventories, correspondence | Build fresh for all 35 selected slots | Every collection product depends on selected membership and/or changed targets |
| Task 04A usability | Carry correspondence only; do not auto-accept | Task 06H owns human review/acceptance |
| Task 05D/05E/05F products | Preserve unchanged | Task 05G owns consumer replay after accepted 06H handoff |

Source order remains Task 06A's 35 slots. At ordinal 10 the logical
`deir_appendix_f1` slot selects physical `feir_appendix_f1`; Appendix A remains
ordinal 18 and `deir_main` ordinal 25. Reuse means a new record references and
validates an immutable predecessor; it does not copy the predecessor into a new
identity or claim that its source was reacquired.

### Frozen namespaces, commands, and ordering

The exact first-attempt external roots are
`pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/` and
`execution_attempt_v1/`. The monitored `replay_v1/` root owns
`document_progress/`, all document/link/publication/collection products,
`correspondence_v1/`, `comparison_v1/`, and `identity_checkpoints_v1/`, so the
32-GiB cap covers the whole production replay rather than only final assembly.
Every readiness pass also allocates a fresh sibling
`finalization_attempt_vN/`. The tracked request set will be
`configs/task06/v1/task06g_generation_v1.json`,
`task06g_document_v1.json`, `task06g_collection_v1.json`,
`task06g_relink_preparation_v1.json`, `task06g_link_v1.json`,
`task06g_comparison_v1.json`, and `task06g_execution_v1.json`, plus explicit
per-source structure specs for Appendix A, `deir_main`, and `feir_appendix_f1`.
These tracked files are frozen **templates and generation recipes**, not files
that production may edit in place. Runtime-resolved concrete specs are separate
artifacts under the predetermined no-clobber root
`replay_v1/resolved_specs_v1/`.
The source-free gate adds one narrow execution driver,
`scripts/run_task06g_replay.py`, whose only responsibility is to validate the
reviewed execution spec and invoke the maintained commands below in order. It
also adds source-free `scripts/preflight_task06g_resume.py`,
`scripts/launch_task06g_initial.py`, `scripts/launch_task06g_resume.py`, and
`scripts/finalize_task06g_readiness.py` for the explicit resume, cumulative
resource, and terminal readiness gates below, plus
`scripts/resolve_task06g_specs.py` for the allowlisted spec-resolution contract
and `scripts/preflight_task06g_prelaunch.py` for recovery before any supervisor
attempt exists.
None may own repair or resolution policy. No path may be
selected by a glob or recency. The whole external `06g/` namespace was absent
during Phase 1 inspection. At the initial preflight, before the first resolver
write, `replay_v1/` and `execution_attempt_v1/` must be absent. A supervised
resume instead requires the existing `replay_v1/` and preserved prior execution
attempts; it never treats their presence as permission to overwrite them.

Output identity review is staged because maintained document candidate IDs bind
both a control digest and a content digest that exists only after candidate
content is built. Phase 2 therefore freezes and reviews an **identity recipe
checkpoint** before production: canonical serialization/version, constructors
and owned-code inventory, exact config and schema digests, accepted upstream
IDs/completions, source order and substitution, policy/repair packets, output
roots, terminal-state rules, and the fields feeding each control/content
digest. Structure candidates bind the selected source/producer, mapped-record
and hierarchy identities, accepted repair packet, config, and owned code;
document candidates bind `production_extraction_id`, source ID, generated
content digest, and a control digest over hierarchy disposition, run-spec
digest, stage completions, and terminal state; linked documents bind the sealed
source document, reviewed navigation, applicable alias packet, policy, schemas,
and linker code; collection identities bind the ordered 35-source selection,
selected document completions, collection/link specs, and collection code.

During an authorized replay, those frozen constructors may derive literal
content digests, candidate IDs, scope ID, index ID, resolution ID, and handoff ID
at runtime. This expected derivation does not itself require another approval.
Each stage must immediately publish an **identity result checkpoint** recording
the literal ID, all canonical digest inputs/references, and an independent
recomputation against sealed output before a dependent stage starts. Stop on a
recomputation mismatch, conflicting duplicate, unexplained identity, or
unexpected dependency. A terminal exact match is expected reuse during an
accepted resume and must be recorded as such. Populating an allowlisted field
from its declared verified checkpoint is authorized runtime resolution, not a
config change. Any change to the reviewed recipe, frozen template/config,
schema, policy, owned code, upstream binding, selected source/order, namespace,
terminal-state rule, or any non-allowlisted resolved field does require a
revised plan and Astra/user review; changing one of those inputs is not ordinary
runtime derivation.

Identity checkpoints live outside already sealed stage namespaces at
`replay_v1/identity_checkpoints_v1/stages/<ordered-stage-key>.json`. Each is a
schema-validated no-clobber record binding the frozen recipe-checkpoint SHA-256,
the stage completion path/SHA-256, the derived literal ID and preimage, and the
independent recomputation result. A final
`identity_checkpoints_v1/inventory.json` closes the exact checkpoint set before
Task 06G readiness; existing terminal checkpoints are verified on resume and
never rewritten. This preserves each stage's own completion-last boundary while
giving the runtime derivations a managed closure.

Concrete spec resolution is a separate staged checkpoint. The frozen generation
recipe enumerates every template digest, generator/code digest, destination
path, schema/digest, downstream consumer, and exact JSON-pointer allowlist.
The only permitted runtime values are an individually named ID field for a newly
produced heading, mapping, hierarchy, structure, document, or link candidate;
`path`, `sha256`, and `byte_size` within that stage's completion and inventory
references; the derived `production_extraction_id`; collection `scope_id`,
`accounting_id`, `target_index_id`, `resolution_id`, and `handoff_id`; and
`path`, `sha256`, and `byte_size` within the corresponding collection completion
or inventory references. The relink-preparation template also explicitly
allowlists `/document_roots/feir_appendix_f1`,
`/document_roots/deir_appendix_a`, and `/document_roots/deir_main`; each full
root is resolved from its verified published `docv1-*` checkpoint. Constant
authority fields and all other document roots remain frozen. The reviewed
recipe must enumerate the full JSON pointer and source checkpoint for every
occurrence; wildcards, suffix matching, and generic "related ID" permissions
are forbidden. If implementation needs any other runtime field, stop and add
its exact pointer to the reviewed template/recipe before execution.
Every value must come solely from a verified identity result checkpoint for an
already completed upstream stage, except `production_extraction_id`. That value
is derived source-free before execution from the frozen production-identity
recipe and the canonical bytes of its already resolved collection spec. The
initial phase independently recomputes it and publishes a distinct
pre-execution production-identity checkpoint atomically beside the concrete
initial specs; it requires no fictitious stage completion and introduces no
phase-manifest/spec cycle. The `00_initial/` phase manifest explicitly lists and
seals this checkpoint as a distinct managed artifact; the aggregate resolved-
spec inventory and final readiness inventory must include its path, SHA-256,
and byte size even though it is not stage-completion-backed. A spec may not
predict or populate its own output ID.
Source identities/order, accepted input paths or seals, policies, expected
counts, schemas, code identities, commands, resource limits, and namespaces are
never runtime-resolved fields.

For each stage, the resolver copies the frozen template, changes only its
declared allowlisted pointers, independently recomputes the cited identity
checkpoint, validates the complete concrete spec against its pinned schema, and
canonically serializes it to its predetermined phase path. Specs are not
published one file at a time: the resolver builds the phase's complete specs,
per-spec receipts, and phase manifest in a fresh same-filesystem staging
directory, writes the phase manifest last, validates the directory, and
atomically renames it no-clobber beneath `resolved_specs_v1/`. A crash before
rename preserves only staging evidence; a crash after rename leaves a complete
immutable phase. In explicit resume mode it reuses a published phase only after
every existing byte, digest, receipt, manifest entry, and source checkpoint
reproduces exactly; every other collision fails. It also fails if a
non-allowlisted field differs, a required value lacks a verified checkpoint, or
regenerated bytes/digest are nondeterministic. Templates are never overwritten.
Each downstream identity and completion binds the authority-aware concrete spec
reference it consumed, not only the template or generation recipe.

Per-spec receipts record template, generator, schema, populated pointer/value
sources, resolved path, byte size, SHA-256, and independent validation result.
Each predetermined stage directory, beginning with `00_initial/`, publishes a
no-clobber phase manifest after all specs required for its next consumer are
ready; runtime loaders require both the per-spec receipt and that phase-manifest
entry. After the last resolution, an equivalently staged and atomically
published `resolved_specs_v1/aggregate_v1/` contains the aggregate
`resolved_spec_manifest.json` and `artifact_inventory.json` closing the exact
phase/spec/receipt set plus the distinct pre-execution production-identity
checkpoint; their digests are required by final comparison and Task 06G
readiness.
Resume verifies and reuses an exact resolved spec or publishes the next
predetermined stage spec; it never edits an existing one. Any template,
generator, policy, schema, accepted-input or upstream identity recipe change—or
any undeclared resolved-field change—stops execution and requires revised Astra
and user review.

Publication has one owner. `resolve_task06g_specs.py` alone stages, validates,
and atomically publishes every resolved-spec phase. The relink preparer's
maintained construction is split into a pure `build_specs`/validation boundary
that returns deterministic values and canonical bytes without writing; the
resolver invokes that boundary for the relink phase. `00_initial/` owns the
production identity plus initial document, collection, and execution specs.
Later document phases own only specs unlocked by their preceding checkpoints;
the relink phase verifies and reuses the initial production/document/collection
specs and publishes only its new relink/link outputs. The comparison phase does
the same for comparison/closure specs. Neither `prepare_specs` nor its CLI may
republish or collide with an earlier phase.

Current preparation is repository-authority-specific at several layers, so a
loader-only exception is insufficient. The source-free integration gate must
version the whole narrow boundary: `load_preparation_spec` retains repository
authority for templates/code but resolves declared runtime inputs and outputs
under the artifact root; the preparer's pure builder returns deterministic
values to the resolver, which alone publishes to the predetermined artifact
phase rather than forcing `repo_root`; generated-reference construction
emits `authority: artifact_root`; production-identity contract references carry
that authority; and `prepare_document_inputs`, relink preparation/preflight, and
publication hash resolved document/link/collection specs under the declared
artifact root. Only specs beneath this `resolved_specs_v1/` root with a matching
receipt and completed phase-manifest entry are accepted during execution; the
aggregate manifest and inventory close the final set for readiness. Repository
validation remains mandatory for templates, schemas, policies, and owned code.
The integration must not add arbitrary external-spec discovery or weaken those
checks.

The relevant identity/completion schemas are versioned so document and relink
candidates carry an authority-aware `resolved_spec_ref` with path, SHA-256, and
byte size, and collection production/scope/accounting/index/resolution/handoff
identities carry the concrete collection/link spec references they consume.
In particular, collection preparation may not discard the collection-spec
digest. These references are identity inputs. The per-spec receipt and phase
manifest provide path closure, but do not substitute for binding the concrete
spec digest into every downstream identity that it controls.

The following command sequence is the accepted Phase 2 checkpoint. It becomes
executable only after the source-free integration gate has generated and
validated the frozen identity recipes, specs, and exact maintained argv without
material drift from this plan. Runtime-derived literal IDs need not exist yet.
Then run it in this order from the repository root with accepted
commit/config/code digests pinned. Any material command or contract change still
requires renewed review before launch:

```bash
uv run python scripts/generate_document_configs.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json --check
uv run python scripts/resolve_task06g_specs.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --phase initial \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1
uv run python scripts/prepare_document_inputs.py \
  --document-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_document_v1.json \
  --collection-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_collection_v1.json \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1 \
  --resume-existing
uv run python scripts/launch_task06g_initial.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1 \
  --attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --launch-record-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/initial_launch_v1
```

The initial preflight must prove `replay_v1/` and `execution_attempt_v1/` absent
before the spec resolver creates the dedicated production root and initial
concrete specs. `prepare_document_inputs.py --resume-existing` then stages only
the reviewed compact inputs into that same root. Inspect its exact initial
managed-file closure before launch. The supervisor requires that output root to
exist and the disjoint attempt root not to exist. The initial launcher validates
the prepared-input closure, writes its immutable launch packet before dispatch,
and creates detached tmux session `er-commons-06g-replay-v1`. The packet contains
`launch_intent.json`, which seals the argv recipe and all inputs, and
`dispatch_record.json`, which binds that intent digest and records the exact
materialized argv without a self-digest cycle, and `packet_manifest.json`,
written last. The launcher builds and validates all three in a fresh sibling
staging directory and atomically renames the complete packet no-clobber before
dispatch. Together they seal the repository
working directory, environment assumptions, accepted input identities,
execution-spec reference, output/progress/attempt namespaces, tmux name, durable
log path, requested start time, and effective resource limits. The driver argv
includes the launch-intent path and SHA-256; the supervisor's status and terminal
`execution.json` record the exact materialized command, which must equal the
dispatch record.
The execution driver then
invokes exactly three separate `run_document_collection.py` commands in this
order—`feir_appendix_f1`, `deir_appendix_a`, `deir_main`—because `--source-id`
is singular; each uses the resolved `00_initial/task06g_document_v1.json` and
the no-clobber attempt-specific `replay_v1/document_progress/attempt_v1/`. It
next invokes `resolve_task06g_specs.py --phase relink`; that resolver consumes
the first downstream concrete `task06g_relink_preparation_v1.json` and calls the
preparer's pure builder without letting the preparer publish files. It then runs
`collections relink-and-assemble` with the resolved `task06g_link_v1.json`, then
the resolved correspondence/comparison publisher and closure validator. Before
each command, the resolver must publish the concrete spec and receipt enabled by
the preceding verified identity result checkpoint.

The final closure argv includes the maintained handoff check. The execution
driver reads the runtime-derived scope ID from the newly sealed collection
identity, independently recomputes it under the frozen recipe, and records the
literal argv before invoking:

```bash
uv run er-commons collections validate-handoff \
  --collection-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/document_publications \
  --scope-id <runtime-derived-and-recomputed-scope-id> \
  --schema benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json
```

The repository does not yet expose the required 06G correspondence/comparison
publisher or final packet validator. The integration gate must add narrow,
maintained CLIs, freeze their argv recipes and non-runtime arguments in the
execution spec, and obtain review at the preflight checkpoint. A literal scope
ID is an authorized runtime substitution only after recomputation; a placeholder
reaching a child command or a missing closure command is a hard stop.

The accepted source-free gate must make `--help` and generated-spec inspection
the authority for final flag spelling. If it exposes a different maintained
selector, revise this command block and obtain review again before launch; do
not improvise at the terminal. The document runner selects only the three fresh
or structurally repaired source descendants; using `--all-sources` with the
current generator is prohibited because it classifies every entry as a fresh
build. The relink/assembly contract then republishes all 35 downstream link
descendants under the fresh global identity. Per-source work is serial in the
frozen source order, followed by collection accounting, target index,
resolution, correspondence/difference reports, handoff, inventory, and
completion last. The single supervisor therefore records and limits every
production stage, not only final collection assembly.

The interval between creation of `replay_v1/` and creation of
`execution_attempt_v1/` has its own runnable, source-free recovery path. If the
initial resolver or compact-input preparation exits before supervisor launch,
do not use the supervised attempt-v2 resume flow and do not delete the partial
root. First require `execution_attempt_v1/` and every tmux/process for this
replay to be absent. Then allocate a fresh no-clobber sibling receipt root such
as `prelaunch_recovery_v1/` and run:

```bash
uv run python scripts/preflight_task06g_prelaunch.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1 \
  --execution-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v1
uv run python scripts/resolve_task06g_specs.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --phase initial \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1 \
  --resume-existing \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v1/recovery_receipt.json
uv run python scripts/prepare_document_inputs.py \
  --document-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_document_v1.json \
  --collection-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_collection_v1.json \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1 \
  --resume-existing
uv run python scripts/launch_task06g_initial.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1 \
  --attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --launch-record-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/recovery_launch_v1 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v1/recovery_receipt.json
```

The recovery packet is deliberately not `initial_launch_v1/`. Any ordinary
initial packet published before the interruption is immutable prior-launch
evidence and cannot be retrofitted with a later recovery receipt or allowance.
The recovery preflight records whether that packet is absent, complete, or
partial; preserves every observed byte; and includes it in the external-byte
ledger. If `recovery_launch_v1/` itself is already a complete atomically
published packet but tmux/process and `execution_attempt_v1/` are all absent,
replace only the final launcher command above with this exact-match packet reuse
form:

```bash
uv run python scripts/launch_task06g_initial.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1 \
  --attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --launch-record-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/recovery_launch_v1 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v1/recovery_receipt.json \
  --reuse-launch-packet-exact
```

The prelaunch receipt binds the accepted commit, generation recipe, template,
generator, schema, policy, accepted-input seals, intended namespace, observed
managed paths, and the fact that no supervisor attempt has started. It
classifies a published `00_initial/` phase only as absent or an independently
regenerated exact match. Resolver staging directories are preserved as failed
evidence and a retry uses a fresh staging directory; they are never promoted or
overwritten. Compact-input recovery relies only on its maintained exact-byte
behavior: an identical staged source-family catalog is reused, a differing one
fails, an identical readiness record is reused, and any candidate completion
marker stops preparation. The recovery-aware initial launcher independently
verifies and binds the recovery-receipt path/SHA-256 in its launch intent and
therefore in the supervised driver binding, then still creates
`execution_attempt_v1/`; no production stage or attempt number was consumed
before that dispatch. It sets
the supervisor's output allowance to 32 GiB minus preserved sibling recovery
and abandoned-staging bytes and a bounded prospective external-evidence
reserve. The replay tree remains counted by the supervisor, so it is not
subtracted twice; the launch packet also states the resulting maximum additional
bytes. Any unexplained file, completed candidate,
non-identical phase/spec/receipt/readiness/catalog, changed binding, or evidence
that a supervisor began is a hard stop requiring a reviewed new replay
namespace. Prelaunch receipt and abandoned staging bytes enter the same 32-GiB
evidence ledger and final inventory.

A launcher crash before its packet rename leaves only preserved staging and a
retry builds a fresh staging directory. A crash after rename but before dispatch
leaves a complete recovery packet: the explicit reuse form independently verifies every
byte, manifest entry, input, effective allowance, tmux/process absence, and
attempt-root absence, then dispatches the originally sealed argv and requested
start record without rewriting the packet. Any partial final packet, mismatch,
live or ambiguous process, or evidence that the supervisor started is a hard
stop; it is never handled by silently allocating another packet or attempt.

### Execution envelope, restart, and failure recovery

Budget up to 86,400 seconds, four CPU threads, process-tree RSS at most 10 GiB,
new outputs at most 32 GiB, and require at least 64 GiB free before launch.
Phase 1 observed 688 GiB free, 36 GiB RAM, 14 logical CPUs, and tmux 3.7c. There
is no sealed timing for this exact mixed-lineage workload, so reserve a
conservative 3–6-hour operator window beneath the 24-hour hard limit; runtime
is an estimate, not an acceptance criterion. Use detached tmux session
`er-commons-06g-replay-v1`, not a foreground interactive turn.

Launch through `python -m er_commons.document_publication.background_execution`
with the exact working directory, command, environment assumptions, accepted
input identities, output namespace, start time, limits, session name, and log
path sealed first in `initial_launch_v1/launch_intent.json` and
`dispatch_record.json`; the supervisor independently records process timing,
the exact dispatched command, exit, and accounting beneath
`execution_attempt_v1/`. The ordinary initial launcher deducts the bounded
external launch-packet/evidence reserve from its supervisor allowance; the
recovery-aware form additionally deducts the exact preserved recovery and
abandoned-staging bytes. Stream stdout/stderr to
`execution_attempt_v1/command.log` and current state to
`execution_attempt_v1/status.json`. Return
control after launch; inspect with `tmux attach -t er-commons-06g-replay-v1` and
`tail -f .../06g/execution_attempt_v1/command.log`. On resume, inspect this session and
attempt first; never start another run because status has not changed.

Completed content-addressed stages with exact inputs may be reused. An
interrupted or failed supervisor is never restarted in its existing attempt
directory: `background_execution` rejects any pre-existing `attempt_root`.
Resume preflight must require the same reviewed Git/config/code/recipe digests,
confirm that the prior tmux/process is no longer live, read and preserve every
prior `execution_attempt_vN/status.json`, `command.log`, and terminal
`execution.json` when present, validate the existing `replay_v1/` managed-file
closure, and classify each descendant as terminal exact-match, incomplete, or
absent. It must stop on an unexplained final-namespace partial, conflict, or
changed output-affecting input; it never deletes or overwrites one to make
resume pass.

An accepted resume allocates a fresh sibling `execution_attempt_v{N+1}/` and a
fresh tmux session such as `er-commons-06g-replay-v1-attempt-v2`, while keeping
the same `replay_v1/` output root and frozen execution spec. The driver uses the
maintained candidate lookup and completion verification to reuse terminal
exact-match stages and writes only missing descendants. Every attempt uses a
fresh `replay_v1/document_progress/attempt_vN/`, so the runner's write-mode
source logs cannot overwrite a prior attempt's logs. Incomplete staging and
attempt evidence remain preserved; an incomplete stage cannot impersonate a
terminal completion. No resume requires `replay_v1/` to be absent, and no prior
execution-attempt or progress directory is reused. A changed
recipe/config/code/upstream binding allocates a new reviewed replay namespace
and identities rather than a resume attempt.

Incomplete-state handling is explicit. Attempt-local or staging output without
a terminal completion is abandoned in place and referenced by the resume
receipt; the fresh attempt uses a new attempt-specific staging path and may
publish only through the maintained atomic no-clobber transition. An incomplete
directory already occupying an identity-addressed final path is not resumed,
deleted, renamed, or treated as reusable: preflight stops and requires a
reviewed recovery/new replay namespace. Thus a same-root resume is runnable only
when every existing final identity is either absent or a verified terminal
exact match.

The first resume is runnable as the following two separately gated commands;
later resumes increment every `v2` suffix together. The preflight writes only
its own no-clobber receipt, must leave `execution_attempt_v2/` and
`document_progress/attempt_v2/` absent, and records that the new attempt
references existing `replay_v1/` plus prior `execution_attempt_v1/`. It sums
the existing replay tree separately from all preserved sibling execution,
resume-preflight, launch, and finalization-attempt evidence plus a bounded
external-metadata reserve. Because `background_execution` already counts the
whole replay tree plus the current attempt, the receipt sets
`supervisor_max_output_bytes` to 32 GiB minus only preserved sibling bytes and
the prospective external reserve; subtracting replay bytes there would count
them twice. It separately records `maximum_additional_bytes` as 32 GiB minus
replay bytes, preserved sibling bytes, and the reserve. If that additional
allowance is not positive, resume stops before launch:

```bash
uv run python scripts/preflight_task06g_resume.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1 \
  --prior-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --next-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v2 \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/resume_preflight_v2
uv run python scripts/launch_task06g_resume.py \
  --resume-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/resume_preflight_v2/resume_receipt.json
```

The narrow launcher verifies the sealed receipt and reviewed execution spec,
then records and starts exactly `er-commons-06g-replay-v1-attempt-v2` with fresh
`execution_attempt_v2/` and `document_progress/attempt_v2/`. Its supervisor argv
uses the receipt's reduced `supervisor_max_output_bytes`, so the current
`replay_v1/` plus current attempt cannot make aggregate preserved 06G bytes
exceed 32 GiB during execution. It passes the explicit resume-receipt path and
SHA-256 in the supervised driver's argv and binds both into the no-clobber
launch record; the supervisor's terminal `execution.json` therefore captures
that binding in its recorded command. The driver rejects a resume if either
receipt value is missing or mismatched. The launcher cannot relax any other
reviewed limit.

Each document/collection stage publishes its own completion last within its
managed namespace. Successful child artifacts alone do not make Task 06G ready:
after the child exits, the supervisor still performs descendant cleanup, final
disk accounting, terminal budget checks, and only then writes
`execution_attempt_vN/execution.json`. The supervised child therefore must not
publish Task 06G readiness or completion.

After the tmux session ends, a separate source-free finalizer must read a
terminal `execution.json` with `status: succeeded`, zero return code, no failure
reason, and no surviving descendants; recompute and validate all final artifact,
correspondence, comparison, accounting, index, resolution, handoff, inventory,
and identity checkpoints. Every finalizer run uses a fresh no-clobber sibling
`finalization_attempt_vN/`, so failed validation diagnostics remain preserved.
It confirms the 32-GiB cap still holds including its own canonically serialized
bounded metadata and every execution, prelaunch-recovery, resume-preflight,
initial/resume launch, abandoned-staging, and
finalization-attempt record explicitly enumerated in the resume ledger. It
writes a terminal validation receipt in `finalization_attempt_vF/`, then builds
a finalization-specific Task 06G candidate in a fresh same-filesystem staging
directory. Inside that staging directory it writes the inventory, readiness
receipt, and completion record in that order, validates the complete candidate,
and atomically renames it no-clobber to
`replay_v1/readiness_candidates/finalization_vF/`. No file is changed after the
rename. Readiness and completion are excluded from the pre-readiness inventory;
completion is the last managed record written in staging and seals both that
inventory and the readiness receipt.

The inventory closes the exact pre-readiness set: the stage checkpoint packet,
the distinct pre-execution production-identity checkpoint, resolved-spec
closure, artifacts, correspondence, comparisons, selected execution/finalization
evidence, the selected initial/recovery launch packet or resume launch record,
every preserved superseded launch packet, any prelaunch-recovery receipt and
abandoned resolver or launch staging, and any resume receipt.
Readiness binds that inventory
SHA-256, the selected execution-attempt path and terminal `execution.json`
SHA-256, the finalization receipt, and the exact selected initial/recovery
launch-intent and dispatch-record references or resume launch-record
path/SHA-256. For
a recovered initial attempt it also binds the prelaunch-recovery receipt; for a
later attempt it binds the resume receipt. Completion binds the same evidence
plus the canonical
readiness-receipt path and SHA-256, avoiding an inventory/readiness hash cycle
while proving which readiness record precedes completion last. None may rely on
mutable `status.json`. Its reviewed argv is:

```bash
uv run python scripts/finalize_task06g_readiness.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --execution-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_vE \
  --finalization-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/finalization_attempt_vF \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v1
```

Here `vE` is the exact succeeded execution attempt selected in the resume
ledger, while `vF` is the next fresh finalization-attempt ordinal. They are
independent: a failed `finalization_attempt_v2` against successful
`execution_attempt_v2` may be followed by `finalization_attempt_v3` against the
same execution evidence. The finalizer must reject glob, recency, reused
finalization roots, or mutable-status selection.
It inspects the command sealed in `execution.json`: a resumed command requires
the exact bound resume receipt and digest. An initial command requires the exact
bound selected initial/recovery launch-intent path/digest and a matching dispatch
record; that intent must either declare no prelaunch recovery or bind the exact
recovery-receipt path/digest and reduced allowance. The finalizer verifies the same chain
and rejects invented, missing,
or conflicting recovery evidence. It serializes all prospective records and
rechecks the aggregate cap before atomic publication.
The integration gate must add and test this narrow finalizer. If child stages
complete but the supervisor later fails, completed exact-match stages remain
reusable, but readiness is prohibited. Resume through a fresh execution attempt
so one supervisor run can finish successfully, then run the finalizer against
that succeeded attempt. If final artifact validation fails, publish no
readiness/completion; seal a failure record only inside that fresh
`finalization_attempt_vF/`, preserve diagnostics, and resolve the owning
contract before retrying in another finalization-attempt namespace.

A crash before the atomic rename leaves only attempt-specific staging and
diagnostic evidence, which remains preserved and cannot block a fresh
finalization attempt. A crash after the rename leaves a complete immutable
candidate that must verify as an exact match and be reused. Tests must inject
interruptions after staged inventory, after staged readiness, after staged
completion, and immediately after rename. A partial directory at the final
`readiness_candidates/finalization_vF/` path is impossible under the required
same-filesystem atomic transition; if observed, stop as a contract violation.

### Expected accounting and old/new invariants

The Task 04D baseline is 35 documents, 48,341 pages, target-index count 99,172,
and 72/72 cross-document decisions resolved. Mechanical source replacement gives
exactly 35 documents and 49,022 pages (`48,341 - 75 + 756`). The selected-source
order is unchanged apart from physical F1 identity at logical slot 10.

The new absolute target-index count is deliberately not fabricated before Final
F1 descendants exist. Reconcile it as old 99,172 minus every old-F1 target plus
every Final-F1 target plus itemized Appendix A/main/FC1 mapped deltas. The
72 baseline resolution decisions are a comparison population, not a promised
new count: compare all old/new decisions after entity mapping and explain every
added, removed, changed, or legitimately unresolved outcome. Task 05F remains
exactly 511 mentions = 295 links + 216 explicit nonlinks because Task 05 is not
replayed.

Required correspondence proves semantic equality for the 32 preserved
documents after ID mapping; exactly four Appendix A many-to-one groups—Chapter
06 source pages 311/312 with six children and extent 311–451, Chapter 07 source
pages 451/452 with ten children and extent 451–479, Chapter 08 source pages
479/480 with four children and extent 479–491, and Chapter 09 source pages
491/492 with five children and extent 491–501. Main Chapter 8 spans 1855–2014
and Chapter 9 spans 2015–2084, bounded by Chapter 10 at 2085. Main FC1 counts
remain 274 canonical figures, 178 eligible, 96 rejected, 178 unique aliases and
edges, with zero ambiguity, collision, or review. Figure 4.8 remains absent.
Final F1 entities are new-source additions with no invented equivalence to
wrong-F1 entities.

Classify all 757 accepted Task 04A decisions as unchanged,
remapped-equivalent, changed, or unproven; review evidence from wrong F1 cannot
transfer to Final F1. Reconcile the four Task 06 planning populations—66
wrong-F1 mentions, 79 figure-target-absent mentions, 19 Chapter 8/9
outside-routed-source mentions, and the two overlapping Appendix A contexts—
without treating them as promised post-repair link counts. Also compare the
5,088 ordinary-reference outcomes and 560 navigation claims (410 linked, 150
unresolved), preserving all 28 inherited Task 04C navigation links unless a
mapped repair explicitly changes one. Every alias, target, local link,
collection link, source-family, and unresolved delta must name its
source/destination evidence and owning repair.

### Preflight validation and hard stop conditions

Before any production write, record and validate: exact accepted Git commit and
reviewed integration diff/config digests; exact `ER_COMMONS_DATA_ROOT`; all
accepted seals above plus 06A/06B inventories and 06C–06F completion/inventory
closures; 35 unique logical slots in frozen order; Final F1 physical identity,
edition, manifest, role, page/byte metadata and logical substitution; review
registry once; the frozen identity recipes and deterministic recomputation
checks; initial output paths absent or, for resume, the existing `replay_v1/`
closure plus fresh `execution_attempt_vN/`; for prelaunch recovery, an absent
first execution attempt, a sealed fresh recovery receipt, and exact recovery of
the initial phase and compact-input closure; at least 64 GiB free; resource
controls active; FC1 qualification applicable only to `deir_main`; and sentinels
that fail on conversion, extraction, model, PDF/image open/render, or
preserved-payload hashing.

Stop without production replay on any commit/config/code drift after acceptance;
placeholder or missing spec; missing/mismatched seal or managed-file closure;
unexpected output; insufficient space; source/order/edition mismatch; wrong
source role or substitution shape; FC1 outside main; need for source/model work;
undeclared earlier-stage invalidation; Task 05/06H write target; unmapped or
dangling correspondence; 35/49,022 accounting failure; resolution population
or result delta not reconciled to the 72-decision baseline; Figure 4.8
unexpectedly resolving; unexplained ambiguity or collision; resource-limit
breach; or inability to guarantee completion-last.
Preserve diagnostics and return the semantic issue to 06D/06E/06F or the
integration issue to 06G planning as appropriate.

After successful execution, validate exact managed-file closure, inventories,
identities, accounting, correspondence, preservation invariants, all stated
old/new comparisons, `task04_status: not_evaluated`, and restart reuse. Require
the selected supervisor attempt's terminal `execution.json` to record
`status: succeeded` after its final accounting, then run the separate finalizer
and read the completion-last Task 06G record. Run `make fix`, `make check`, and
`git diff --check`, then perform an independent maintainability and
evidence-closure review. Update this task and current routers to review-ready
with acceptance pending, and stop before Task 06H and Task 05G.

### Phase boundary and approval

Phase 1 changed planning documentation only. Astra scrutinized the
mixed-lineage and qualified-substitute contract closure; standalone substitution
record semantics; FC1 per-source gating; deterministic identity construction;
whether republishing all 35 linked documents is the minimum required global
identity consequence; exact CLI/spec closure; correspondence completeness;
49,022-page accounting and 72-decision baseline reconciliation;
staged runtime identity derivation; fresh-attempt/same-replay restart behavior;
supervisor-terminal readiness ordering; and the 3–6-hour/10-GiB/32-GiB
envelope. The material findings were remediated, including the final distinction
between frozen templates and allowlisted runtime-resolved specs. Astra accepted
the revised plan and the user approved it and authorized Phase 2 on 2026-09-11.
Execution must follow this accepted plan exactly; commit and push remain separate
and unauthorized.

### Authorized replay-v2 prelaunch amendment (2026-09-11)

The first Phase 2 prelaunch stopped before any supervisor attempt or source/model
execution. `replay_v1/` contains only its immutable initial resolved-spec packet.
Compact-input preparation correctly rejected that packet because one inherited
`document_link_run.schema.json` reference retained its pre-implementation digest
while the current schema had changed. The integration gate now validates every
repository-authoritative production-identity artifact and owned-code reference,
so this mismatch cannot recur silently.

The user authorized a bounded fresh-lineage recovery after Astra supported it.
Preserve `replay_v1/` exactly as failed prelaunch evidence. The replacement uses:

- output namespace `06g/replay_v2/`;
- recovery receipt `06g/prelaunch_recovery_v2/recovery_receipt.json`;
- launch packet `06g/initial_launch_v2/`;
- tmux session `er-commons-06g-replay-v2`;
- the still-fresh first supervisor namespace `06g/execution_attempt_v1/`.

Every replay-root binding in the document, collection, per-process, relink,
comparison, resolver, execution, launch-validation, and staged-checkpoint
templates changes from `replay_v1` to `replay_v2`. The production contract
revision and extraction version also advance from replay v1 to replay v2, and
all resulting repository/config/schema bytes are frozen again. No accepted
source, conversion, producer, canonical-record, review, 06B reuse, or 06C-06F
evidence identity changes. The command policy and resource limits remain the
same.

Before resolving v2, run the source-free prelaunch recovery command against the
absent `replay_v2/` root. Its exhaustive sibling seal must include `replay_v1/`;
the execution spec must also declare `replay_v1/` in `ledger_sibling_roots`.
The launch packet then carries both the recovery receipt and cumulative resource
ledger. Resolve and stage v2 with:

```bash
uv run python scripts/preflight_task06g_prelaunch.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2 \
  --execution-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v2
uv run python scripts/resolve_task06g_specs.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --phase initial \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2/resolved_specs_v1 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v2/recovery_receipt.json
uv run python scripts/prepare_document_inputs.py \
  --document-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2/resolved_specs_v1/00_initial/task06g_document_v1.json \
  --collection-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2/resolved_specs_v1/00_initial/task06g_collection_v1.json \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2 \
  --resume-existing
uv run python scripts/launch_task06g_initial.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v2 \
  --attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --launch-record-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/initial_launch_v2 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v2/recovery_receipt.json
```

Astra must review the resolved v2 specs, recovery seal, compact inputs, exact
commands, and cumulative ledger before launch. Stop only for a new material
deviation after that review; otherwise the existing Phase 2 execution authority
continues.

### Authorized replay-v3 mixed-lineage amendment (2026-09-11)

The v2 recovery receipt successfully sealed `replay_v1`, and v2 initial spec
resolution completed, but compact preparation stopped before staging inputs or
starting a supervisor. The legacy fresh-template preflight admitted only wholly
fresh Task 03G2/03H roots; it could not express Task 06G's frozen Task 03H
prefixes plus fresh Task 06G suffixes. Preserve `replay_v2/` and
`prelaunch_recovery_v2/` exactly.

The user authorized one bounded v3 contract extension. A mixed-lineage document
may admit historical artifact/input roots only for the exact prefix enumerated by
its sealed `reused_completions`. Every newly executed role's output root and
every dependency on a non-reused role must remain contained by `06g/replay_v3/`.
Historical roots are not selected by namespace alone: the existing compact
completion reference, identity, source, and inventory checks remain mandatory,
and the staged resolver still independently republishes their checkpoints before
resolving any dependent config.

The v3 lineage uses `replay_v3/`, `prelaunch_recovery_v3/`,
`initial_launch_v3/`, and tmux session `er-commons-06g-replay-v3`; the first
supervisor attempt remains `execution_attempt_v1/`. Its recovery receipt must
seal `replay_v1/`, `prelaunch_recovery_v2/`, and `replay_v2/`. All three are
explicit cumulative ledger roots alongside `initial_launch_v3/`. The production
contract revision, extraction version, schemas, templates, runtime owner set,
and repository references are frozen again. No repair policy, source identity,
conversion/producer artifact, accepted review, or 06C-06F evidence changes.

After source-free validation and freezing, use:

```bash
uv run python scripts/preflight_task06g_prelaunch.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3 \
  --execution-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v3
uv run python scripts/resolve_task06g_specs.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --phase initial \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3/resolved_specs_v1 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v3/recovery_receipt.json
uv run python scripts/prepare_document_inputs.py \
  --document-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3/resolved_specs_v1/00_initial/task06g_document_v1.json \
  --collection-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3/resolved_specs_v1/00_initial/task06g_collection_v1.json \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3 \
  --resume-existing
uv run python scripts/launch_task06g_initial.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v3 \
  --attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --launch-record-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/initial_launch_v3 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v3/recovery_receipt.json
```

Review the resolved v3 specs, compact preparation closure, prelaunch recovery
seal, launch-packet dry validation, and cumulative ledger before dispatch. Stop
for new repair-policy changes, source/model execution requirements, or another
material scope change; otherwise launch under the continuing Phase 2 authority.

### Authorized replay-v4 prelaunch continuation (2026-09-11)

The v3 recovery receipt sealed all earlier evidence and v3 initial resolution
completed, but full compact preparation exposed an implementation-routing bug:
the preparer applied the new mixed-lineage root to all 35 documents instead of
only the three `fresh_build` selections. No inputs or supervisor attempt were
created. Preserve `replay_v3/` and `prelaunch_recovery_v3/` exactly.

Independent review confirmed the correction is the accepted policy expressed
at the correct boundary: all 32 `sealed_inputs` rows retain legacy Task 03H
validation, while only F1, Appendix A, and main use their explicit reused-stage
prefix and a fresh Task 06G suffix. This changes no repair policy, source/model
access, stage scope, accepted input, or resource limit. The no-clobber
continuation therefore uses `replay_v4/`, `prelaunch_recovery_v4/`,
`initial_launch_v4/`, and tmux session `er-commons-06g-replay-v4`; the first
supervisor namespace remains `execution_attempt_v1/`.

The v4 recovery receipt must seal `replay_v1/`,
`prelaunch_recovery_v2/`, `replay_v2/`, `prelaunch_recovery_v3/`, and
`replay_v3/`. The execution ledger declares those five preserved roots plus
`initial_launch_v4/`. After source-free validation and freezing, use:

```bash
uv run python scripts/preflight_task06g_prelaunch.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4 \
  --execution-attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v4
uv run python scripts/resolve_task06g_specs.py \
  --generation-spec configs/task06/v1/task06g_generation_v1.json \
  --phase initial \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4/resolved_specs_v1 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v4/recovery_receipt.json
uv run python scripts/prepare_document_inputs.py \
  --document-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4/resolved_specs_v1/00_initial/task06g_document_v1.json \
  --collection-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4/resolved_specs_v1/00_initial/task06g_collection_v1.json \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4 \
  --resume-existing
uv run python scripts/launch_task06g_initial.py \
  --execution-spec /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4/resolved_specs_v1/00_initial/task06g_execution_v1.json \
  --replay-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v4 \
  --attempt-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/execution_attempt_v1 \
  --launch-record-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/initial_launch_v4 \
  --prelaunch-recovery-receipt /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/prelaunch_recovery_v4/recovery_receipt.json
```

Review the actual resolved v4 packet, preparation closure, recovery seal,
launch-preflight path, cumulative accounting, exact commands, identities, and
limits before launch. A successful independent review authorizes dispatch under
the continuing Phase 2 approval.

### Authorized replay-v5 prelaunch continuation (2026-09-11)

The v4 recovery receipt and initial resolved packet passed, but compact
preparation stopped before staging inputs because the reused-completion caller
labeled a compact JSON completion hash with a diagnostic stage-specific role
rather than the verification budget's existing `completion` role. The hash
allowlist and all payload prohibitions remain unchanged. Independent review
accepted the caller-only correction and confirmed it changes no repair or
execution policy. Preserve `replay_v4/` and `prelaunch_recovery_v4/` exactly.

The no-clobber continuation uses `replay_v5/`, `prelaunch_recovery_v5/`,
`initial_launch_v5/`, tmux session `er-commons-06g-replay-v5`, and the still
unused `execution_attempt_v1/`. Its recovery receipt and cumulative ledger add
both v4 roots to all previously preserved evidence. Apply the v4 command block
with every active v4 namespace/session replaced by v5. Review the actual v5
resolved packet, complete compact preparation, launch-preflight evidence,
accounting, identities, commands, and limits before dispatch. Continue under
the existing Phase 2 authorization unless a material stop condition appears.

### Authorized replay-v6 prelaunch continuation (2026-09-11)

The v5 recovery and document preparation checks passed, then collection
preflight stopped before input publication because it imposed original-manifest
list order on an explicit v3 replacement membership. Task 06G instead freezes
the accepted Task 06A/Task 04D 35-slot order. Independent review confirmed the
correct boundary: explicit production replacement membership must contain every
original model-source logical slot exactly once, while order remains identical
across membership physical IDs, collection IDs, document processes, source
catalog, and generation recipe. Pilot and legacy non-membership manifest-order
rules remain unchanged. This changes no selected member, repair policy, or
source/model access.

Preserve `replay_v5/` and `prelaunch_recovery_v5/` exactly. The no-clobber
continuation uses `replay_v6/`, `prelaunch_recovery_v6/`,
`initial_launch_v6/`, tmux session `er-commons-06g-replay-v6`, and the unused
`execution_attempt_v1/`. Add both v5 roots to cumulative recovery and ledger
accounting. Apply the v4 command block with active namespace/session set to v6,
then independently review the complete resolved/prepared/launch-preflight
packet before dispatch under the continuing Phase 2 authorization.

### Authorized replay-v7 supervised recovery (2026-09-11)

The v6 packet and compact preparation passed independent review and the exact
detached command launched. `execution_attempt_v1/` then failed terminally in
about two seconds, before any document process ran. The retained F1 runner log
proved the command entry still selected legacy production-scope preparation;
that path compared the physical F1 substitute to original logical IDs and would
also hash original PDF payloads. Parent and worker execution preflight also
dropped v4 containment and reused-role bindings. Preserve the complete v6
replay, launch packet, progress attempt, and failed supervisor evidence.

Independent review accepted the narrow integration repair: document v4 routes
through the maintained authority-aware prepared-input path, and parent/worker
validation both receive the same v4 replay boundary and explicit reused-stage
prefix. No source/model bytes, repair policy, selected stage, or evidence
identity is broadened. Guarded command-entry and parent/worker tests prohibit
PDF/image/model access.

Changed code requires `replay_v7/`, `prelaunch_recovery_v7/`, and
`initial_launch_v7/`; the fresh supervised namespace is
`execution_attempt_v2/`, with progress at
`replay_v7/document_progress/attempt_v2/` and tmux session
`er-commons-06g-replay-v7`. Recovery and cumulative accounting must seal all
earlier evidence plus `prelaunch_recovery_v6/`, `replay_v6/`,
`initial_launch_v6/`, and `execution_attempt_v1/`. Independently verify that
the old v6 tmux/process is stopped, validate the complete v7 publish-to-worker
path and actual artifacts, then dispatch attempt v2 under the continuing Phase
2 authorization.

### Authorized replay-v8 source-free aggregate recovery (2026-09-11)

The v7 resolved packet, compact preparation, launch preflight, and detached
launch passed. `execution_attempt_v2/` then failed terminally after the F1
heading producer ran. The retained evidence identifies two integration defects:
record mapping combined the accepted 06C producer ID with the replay-v7
producer root, and accepted aggregate preparation fell through to PDF-aware
routing/table reconstruction. The resulting replay-v7 heading producer is not
eligible for reuse or promotion. Preserve `replay_v7/`,
`prelaunch_recovery_v7/`, `initial_launch_v7/`, and
`execution_attempt_v2/` exactly, including the failed and out-of-contract
predecessor evidence in cumulative resource accounting.

The bounded repair restores the already accepted Gate 3 treatment. Runtime
resolution binds both producer ID and producer root to the owning stage
checkpoint. F1 heading publication consumes the accepted 06C aggregate
projection and table metadata, inherits preserved table payloads by hard link
with their sealed inventory digests, and prohibits PDF/image/model access,
conversion, routing extraction, table extraction, and preserved PDF/image/model
payload rehashing. Compact table records remain readable for semantic closure. It
retains the accepted heading-view configuration and fails closed on projection,
table-policy, inventory, or hard-link incompatibility. This changes no repair
policy, selected source, stage boundary, or provenance authority.

The no-clobber continuation uses `replay_v8/`,
`prelaunch_recovery_v8/`, `initial_launch_v8/`, tmux session
`er-commons-06g-replay-v8`, and fresh supervisor namespace
`execution_attempt_v3/`, with progress at
`replay_v8/document_progress/attempt_v3/`. Recovery and the execution ledger
must enumerate all earlier evidence through the four retained v7/attempt-v2
roots plus the active v8 launch packet. Validate the complete mixed-lineage
preparation and launch-preflight path before freezing v8, then independently
review the actual v8 specs, identities, inventories, commands, bounds, stop
conditions, and source-free guards before launch. Proceed under the user's
continuing Phase 2 authorization; stop for a new repair-policy change,
source/model execution requirement, or other material scope change.

### Authorized replay-v9 payload-safe accounting continuation (2026-09-11)

The v8 code/spec review and repository checks passed, but its recovery command
stopped before publishing a recovery receipt or creating a replay/supervisor
root. Cumulative evidence enumeration correctly rejected an attempted hash of
the preserved replay-v7 F1 table image. A durable failure record is retained at
`prelaunch_recovery_v8/failure.json`; `replay_v8/`, `initial_launch_v8/`, and
`execution_attempt_v3/` were never created.

The bounded correction keeps exact path, size, and digest accounting while
obtaining prohibited PDF/image/model payload digests from their contained
sealed artifact inventories. It verifies inventory containment, normalized
paths, file presence and size, digest form, uniqueness, and exact managed-file
closure without opening those payloads. Compact evidence remains hashed
directly. This restores the accepted resource-accounting contract without
changing sources, repair policy, stage scope, or model/extraction boundaries.

Use fresh `replay_v9/`, `prelaunch_recovery_v9/`, and `initial_launch_v9/`
namespaces with tmux session `er-commons-06g-replay-v9`. The still-unused fresh
supervisor root remains `execution_attempt_v3/`, with progress at
`replay_v9/document_progress/attempt_v3/`. Add the v8 failure root to recovery
and cumulative accounting, validate the full path, and obtain independent
review before launch under the continuing Phase 2 authorization.

Independent review passed for the frozen v9 code/spec closure and again for the
actual recovery, resolved initial packet, and prepared inputs. The detached
replay launched from `/Users/kyledorman/Documents/er_commons` at
`2026-09-12T01:47:03.737442+00:00` in tmux session
`er-commons-06g-replay-v9`. The supervisor command, offline/thread environment,
input identities, 32-GiB cumulative budget, 10-GiB RSS bound, 64-GiB free-space
floor, 24-hour limit, and source-free stop conditions are sealed by
`initial_launch_v9/launch_intent.json` and `dispatch_record.json`. Durable
progress and terminal status belong to `execution_attempt_v3/`; execution-result
acceptance and the separate finalizer remain pending. On resume, inspect this
session and these artifacts and do not start another replay.

### Authorized replay-v10 qualified-source mapping repair (2026-09-11)

Replay v9 passed prelaunch review and started, but failed terminally after
19.3009 seconds in Final F1 record mapping. Preserve `prelaunch_recovery_v9/`,
`replay_v9/`, `initial_launch_v9/`, and `execution_attempt_v3/` exactly. The
fresh source-free heading producer completed; no mapping checkpoint or later
document completion exists, so the accepted stage plan rebuilds heading
evidence in the next namespace rather than importing an unsupported
cross-namespace checkpoint.

The failure exposed three adjacent legacy assumptions in record mapping: input
selection admitted only `model_corpus`, candidate identity omitted a selected
`qualified_substitute`, and the canonical document schema rejected that
truthful role. The bounded repair uses the maintained retained-processing
validator, includes the verified selected physical source in legacy identity
membership, admits `qualified_substitute` without relabeling it, and binds the
validator into mapping-owned identity. This completes the already accepted
mixed-lineage and truthful-provenance requirement; it does not change the F1
source, repair policy, stage scope, conversion/producer reuse, or source/model
execution boundary.

Use fresh `replay_v10/`, `prelaunch_recovery_v10/`, and
`initial_launch_v10/` namespaces, supervisor `execution_attempt_v4/`, progress
`replay_v10/document_progress/attempt_v4/`, and tmux session
`er-commons-06g-replay-v10`. Recovery and cumulative accounting include all
four v9 roots. Freeze the amended schema/code/templates, validate the full
source-free preparation path, obtain independent review, then launch under the
user's continuing authorization. Actively observe logs and stage checkpoints
through the early-runtime window; an initial successful dispatch alone is not
launch acceptance.

### Authorized replay-v11 source-free hierarchy continuation (2026-09-11)

V10 recovery, initial resolution, compact preparation, and the qualified-source
mapping repair passed, but independent prelaunch review found a later prohibited
operation before launch: fresh F1 hierarchy unconditionally read PDF bookmarks,
page labels, and native heading text. Preserve `prelaunch_recovery_v10/` and
`replay_v10/` exactly; `initial_launch_v10/` and `execution_attempt_v4/` were
not created.

The accepted source-free rule necessarily excludes those independent PDF
observations from this replay. The bounded v11 repair adds an explicit
`producer_evidence_only` hierarchy mode for Final F1. It continues hierarchy
inference from the sealed heading-view document and alignment projection while
supplying empty outline, page-label, and native-heading observations; the
legacy `source_pdf` mode remains the default for other tasks. The resolved
config digest and hierarchy owned-code bundle bind this evidence-mode choice.
Focused tests make both PDF reader calls fatal and prove the source-free branch
does not invoke them. This does not claim semantic equivalence to a PDF-aware
hierarchy run; it is the explicit evidence limitation required by the accepted
replay boundary and must remain visible in v11 provenance and comparisons.

Use `replay_v11/`, `prelaunch_recovery_v11/`, `initial_launch_v11/`, tmux
`er-commons-06g-replay-v11`, and the still-unused
`execution_attempt_v4/` with progress under
`replay_v11/document_progress/attempt_v4/`. Include v10 recovery and replay in
cumulative accounting, rerun complete preparation and independent review, and
launch only after the source-free hierarchy path passes. Continue active early
runtime observation after dispatch.

### Authorized replay-v12 structured-link input repair (2026-09-11)

V11 launched after review and the active early-runtime watch caught a terminal
failure after 51.0885 seconds. Preserve `prelaunch_recovery_v11/`,
`replay_v11/`, `initial_launch_v11/`, and `execution_attempt_v4/` exactly.
Production execution proved Final F1 heading parsing, qualified-source record
mapping, producer-evidence-only hierarchy, and document structure complete.
Reference linking then combined the structure candidate ID and seals with the
mapping-stage artifact root, so its exact upstream completion path did not
exist.

The v12 resolver binds `document_reference_linking.artifact_relative_root` to
the document-structure checkpoint's owning artifact root alongside the already
bound structure ID, completion digest, and inventory digest. Process checkpoints
now publish that root as an exact derived output and verify it on resume. This
is an authority-pair closure, not a source, repair-policy, or linking-policy
change. The prelaunch frozen owner set also explicitly includes the hierarchy
mode config, input, execution, and code-inventory modules identified during the
v11 review.

Use fresh `replay_v12/`, `prelaunch_recovery_v12/`, `initial_launch_v12/`,
`execution_attempt_v5/`, progress
`replay_v12/document_progress/attempt_v5/`, and tmux
`er-commons-06g-replay-v12`. Include all four v11 roots in recovery and
cumulative accounting. Revalidate and independently review the full packet,
then launch and actively watch past Final F1 reference linking and the remaining
early-runtime window.

### Authorized replay-v13 complete timing-handoff repair (2026-09-11)

V12 passed independent prelaunch review and launched. The active watch proved
all six Final F1 process checkpoints complete, including the repaired
authority-paired reference-linking input, before the worker failed terminally
after 51.9099 seconds while constructing its final `PipelineResult`. Preserve
`prelaunch_recovery_v12/`, `replay_v12/`, `initial_launch_v12/`, and
`execution_attempt_v5/` exactly, together with the separately retained typo
preflight root `prelaunch_re_v12/` already in cumulative accounting.

The failure was a closed-handoff bookkeeping omission: the accepted reused
content owner was deliberately not invoked, so it had no entry in the timing
map even though `PipelineResult` requires exact six-owner timing closure. The
v13 repair records `0.0` for every intentionally reused owner, matching the
existing Task 06B downstream-replay convention, while retaining positive
elapsed timings only for owners invoked in this attempt. It does not synthesize
stage events, copy historical elapsed time, weaken exact closure, or change any
source, model, repair-policy, identity, dependency, or provenance boundary.

Use fresh `replay_v13/`, `prelaunch_recovery_v13/`, `initial_launch_v13/`,
`execution_attempt_v6/`, progress
`replay_v13/document_progress/attempt_v6/`, and tmux
`er-commons-06g-replay-v13`. Include every v12 root above in recovery and
cumulative accounting. Revalidate and independently review the full packet,
then launch and actively watch beyond the prior failure point for at least the
first several minutes or through terminal completion, whichever occurs first.

### Authorized replay-v14 tmux-binding prelaunch correction (2026-09-11)

V13 recovery, resolution, and compact preparation completed without starting a
supervisor, but prelaunch inspection found its frozen tmux field still named
the prior v12 session. Preserve `prelaunch_recovery_v13/` and `replay_v13/`
exactly. No `initial_launch_v13/` or `execution_attempt_v6/` exists, and no v13
tmux session was created.

The bounded v14 amendment changes only the replay namespace and tmux binding,
adds the two v13 prelaunch roots to cumulative accounting, and refreezes the
path-dependent templates and generation recipe. The v13 timing-handoff repair
is otherwise unchanged. Use fresh `replay_v14/`, `prelaunch_recovery_v14/`,
`initial_launch_v14/`, progress `replay_v14/document_progress/attempt_v6/`,
unused `execution_attempt_v6/`, and tmux `er-commons-06g-replay-v14`. Repeat
the complete preparation and independent review gate, then launch and actively
observe the first several minutes or terminal completion.

### Authorized replay-v15 final-root preflight alignment (2026-09-11)

V14 passed independent review and launched. The active watch caught a terminal
failure after 52.0678 seconds, after all six Final F1 process owners completed.
Preserve `prelaunch_recovery_v14/`, `replay_v14/`, `initial_launch_v14/`, and
`execution_attempt_v6/` exactly.

The runtime resolver correctly placed and sealed the linked document beneath
the document-structure root, but the pre-execution publication snapshot still
derived its allowed final root from the unresolved template's older
document-records path. The bounded v15 repair aligns each of the three
reference-linking templates with the already accepted structure-root authority
pair. Runtime resolution remains mandatory and unchanged. Focused source-free
preflight tests require the snapshot's allowed root to equal the structure
root. This changes no repair policy, source/model access, process dependency,
or provenance meaning.

Use fresh `replay_v15/`, `prelaunch_recovery_v15/`, `initial_launch_v15/`,
`execution_attempt_v7/`, progress
`replay_v15/document_progress/attempt_v7/`, and tmux
`er-commons-06g-replay-v15`. Include all four v14 roots in recovery and
cumulative accounting, repeat complete preparation and independent review,
then launch and actively observe beyond the prior failure and through the first
several minutes or terminal completion.

### Authorized replay-v16 generator-root correction (2026-09-11)

V15 recovery, resolution, and compact preparation completed without supervisor
launch. Independent review then found the newly frozen maintained template
generator had transposed the mapping and linking root assignments even though
the checked-in v15 templates were correct. Preserve `prelaunch_recovery_v15/`
and `replay_v15/` exactly; `initial_launch_v15/` and
`execution_attempt_v7/` do not exist.

The bounded correction restores record mapping to `document_records` and sets
both document structure and reference linking to `document_structure`, matching
the accepted runtime authority pair and preflight invariant. Use fresh
`replay_v16/`, `prelaunch_recovery_v16/`, `initial_launch_v16/`, the still
unused `execution_attempt_v7/`, progress
`replay_v16/document_progress/attempt_v7/`, and tmux
`er-commons-06g-replay-v16`. Account both v15 prelaunch roots, refreeze and
revalidate the full generator closure, obtain independent review, then launch
and actively observe the first several minutes or terminal completion.

### Replay-v16 terminal failure and material 06D stop (2026-09-11)

V16 passed complete source-free preflight and independent review, then launched
under the accepted detached supervisor. The active launch watch observed the
terminal failure after 60.5483 seconds. Final F1 completed all six process
owners and published its staged document checkpoint successfully. Appendix A
then reused its first four accepted stages and failed before document-structure
publication when the repeated-heading projection correctly rejected a frozen
following boundary that was not the immediate next same-level sibling. Preserve
`prelaunch_recovery_v16/`, `replay_v16/`, `initial_launch_v16/`, and
`execution_attempt_v7/` exactly. The supervisor's terminal `execution.json`
records `status: failed`, return code 1, peak RSS 2,045,558,784 bytes, and peak
output 250,283,212 bytes. No tmux session remains.

Compact-record-only diagnosis found that the accepted Chapter 06 decision
names `07 | INFRASTRUCTURE` on page 452 as its following boundary, while the
actual immediate sibling is `07 INFRASTRUCTURE` on page 451. The accepted
Chapter 08 decision similarly names `09 | IMPLEMENTATION` on page 492, while
the actual immediate sibling is `09 IMPLEMENTATION` on page 491. The accepted
06A topology packet omitted both plain-form headings, and the 06D outcome
therefore described Chapters 07 and 09 as single-heading negative controls.
Chapter 08's accepted descendant extent ends on page 491, so merely substituting
the actual immediate boundary would also violate the accepted strict
extent-before-boundary rule.

This is not another 06G namespace, resolver, identity, or launch defect.
Weakening adjacency, changing the selected boundary, changing page-491
ownership, or newly repairing Chapters 07/09 would materially alter the
accepted 06D repair contract. Per the authorized stop conditions, do not create
or launch replay v17 until a bounded review amends and accepts the 06D evidence
or explicitly authorizes a revised boundary policy. That review can use the
already available compact canonical and topology records; no PDF, image, model,
extraction, or conversion access is required.

### Authorized replay-v17 record-order amendment (2026-09-12)

The user selected the earlier plain-form headings as the true Chapter 07 and
Chapter 09 boundaries and authorized the bounded v2 repair. Complete compact
topology validation established the same divider/opening pattern for Chapters
07 and 09, so the one accepted rule now qualifies Chapters 06-09 explicitly.
The v2 decision evidence freezes exact mixed-content orders and rejects any
descendant at or after its immediate boundary; it does not truncate truthful
same-page extents. `APPENDICES` is the exact terminal Chapter 09 boundary.

Preserve qualification v6 and superseded pre-review qualification v7. Bind the
completion-last `06d/qualification_v8/` packet, v2 policy/schema, and its
generator identity. Preserve all four v16 roots and include them in cumulative
accounting. Use fresh `replay_v17/`, `prelaunch_recovery_v17/`,
`initial_launch_v17/`, `execution_attempt_v8/`, progress
`replay_v17/document_progress/attempt_v8/`, and tmux
`er-commons-06g-replay-v17`. Revalidate complete mixed-lineage preparation and
all frozen identities, obtain independent prelaunch review, then launch and
actively watch the first several minutes or terminal completion. Stop on a new
repair-policy change, source/model requirement, or other material deviation.

### Authorized replay-v18 frozen-owner closure (2026-09-12)

Replay v17 completed source-free recovery, initial resolution, and preparation,
but independent review stopped it before launch because the prelaunch generator
closure did not explicitly freeze the changed v2 repeated-heading runtime
owners. Preserve `prelaunch_recovery_v17/` and `replay_v17/` exactly;
`initial_launch_v17/`, `execution_attempt_v8/`, and v17 tmux were not created.

The bounded v18 amendment adds the exact v2 policy, schema, qualification
recipe/generator, classifier, projector, qualification publisher, and facade to
the frozen generator/runtime set. These bytes are now present in both the
generation recipe and resolved production identity. No semantic policy,
dependency, source/model boundary, or execution command changed. Use fresh
`replay_v18/`, `prelaunch_recovery_v18/`, `initial_launch_v18/`, the still
unused `execution_attempt_v8/`, progress
`replay_v18/document_progress/attempt_v8/`, and tmux
`er-commons-06g-replay-v18`. Include the two v17 roots in cumulative accounting,
repeat full validation and independent review, then launch and actively watch
the first several minutes or terminal completion.

### Authorized replay-v19 complete-subtree amendment (2026-09-12)

Replay v18 passed the corrected Appendix-A duplicate-heading stage, then failed
source-free main-document structure validation because accepted Task 06E
qualification v13 froze one Chapter 8 child's block-only page endpoint as 2008
while its already owned tables continue through page 2010. A full compact-record
census found the same evidence defect in ten Chapter 8/9 child leaves. This is
not a new repair policy: the accepted policy already requires complete descendant
subtree extents. Preserve `prelaunch_recovery_v18/`, `replay_v18/`,
`initial_launch_v18/`, and failed `execution_attempt_v8/` exactly.

The bounded amendment publishes `06e/qualification_v17/` from the sealed v13
completion, inventory, and exact three-file managed closure. It freezes the
Task 04D completion, compact sections/blocks/tables/figures, decision schema,
policy document, amendment generator, extent projector, qualification publisher,
and decision/policy implementation. Its only decision changes are the ten
allowlisted `child_topology.extent_end_page` corrections. The exact current-code
projection is preserved at
`06e/qualification_v17_projection_validation/exv1-259528836c331c29e4921673f7c28109b262cdbc999418023e176be2f74fe0ea/`;
it completed with two correspondence rows, all 23 inventory entries verified,
and zero undeclared differences. Earlier v14-v16 packets and projections remain
preserved as superseded evidence.

Replay v19 freezes the added amendment, projection, comparison, alias,
construction, bridge, sealing, and validation owners and binds qualification
v17 completion/inventory plus projection completion/inventory. Use fresh
`replay_v19/`, `prelaunch_recovery_v19/`, `initial_launch_v19/`,
`execution_attempt_v9/`, progress `replay_v19/document_progress/attempt_v9/`,
and tmux `er-commons-06g-replay-v19`. The accepted source-free preflight derives
production identity
`exv1-0015e2df7111b1ec65634328fb9237a4e9898d2025962e9e0e92b951b25d2e82`,
records zero PDF bytes and model files read, and retains the existing commands,
limits, stop conditions, and repair policies. Launch only after independent
review, then actively observe the early document stages before returning control.

### Authorized replay-v20 oversized-metadata resolver continuation (2026-09-12)

Replay v19 passed independent review and launched under active observation. All
three document commands completed: Final F1, Appendix A, and the main document
published their verified stage checkpoints. The replay then failed terminally
after 136.1524 seconds while building the relink phase because the compact
verification budget attempted to freshly hash the accepted Task 04D
`contract_bundle.json`, whose 39,442,998 bytes exceed the one-file hash limit.
Preserve `prelaunch_recovery_v19/`, `replay_v19/`, `initial_launch_v19/`, and
failed `execution_attempt_v9/` exactly. The terminal record reports return code
1, peak RSS 2,054,750,208 bytes, and peak output 595,712,278 bytes.

The bounded v20 correction follows the maintained oversized accepted-reference
pattern: require the already frozen SHA-256 and byte size, verify artifact-root
containment, existence, and exact size without rehashing the file, record that
limitation explicitly, and then allow the separate bounded semantic JSON read
needed for base-collection validation. It also corrects the relink preparation
and mixed-lineage authorization bindings from superseded Task 06E qualification
v15 to the accepted completion-last `06e/qualification_v17/` packet. A guarded
read-only reproduction of the complete v19 relink builder passes with 35 ordered
documents, exactly three replacement rows, no contract-bundle hash, and no
PDF/image/model access. No repair policy, selected source, stage dependency,
identity meaning, resource limit, or source/model execution boundary changes.

Use fresh `replay_v20/`, `prelaunch_recovery_v20/`, `initial_launch_v20/`,
`execution_attempt_v10/`, progress `replay_v20/document_progress/attempt_v10/`,
and tmux `er-commons-06g-replay-v20`. Include all four preserved v19 roots in
recovery and cumulative accounting. Repeat the full initial resolution, compact
mixed-lineage preparation, launch preflight, and independent review, then launch
under the continuing authorization and actively observe through the document
commands and past relink resolution before returning control.

### Authorized replay-v21 downstream-only identity continuation (2026-09-12)

Replay v20 passed preflight and independent review, launched in tmux, and was
actively observed through its terminal failure after 136.2038 seconds. All three
document commands and the repaired relink resolver completed. The collection
command published one completion-last linked candidate for the first preserved
source, `deir_appendix_k4`, with preservation passed and zero undeclared
differences, then failed before publishing that source's downstream document.
Preserve `prelaunch_recovery_v20/`, `replay_v20/`, `initial_launch_v20/`, and
failed `execution_attempt_v10/` exactly, including that terminal linked candidate.

The failure was an identity-shape mismatch at the downstream-only boundary. A
normal v4 document build executes six resolved process configs and must bind all
six. A downstream replay executes none of them: it consumes the authority-aware
resolved document run spec, five verified reused stage completions, and the fresh
linked completion. The existing identity model already represents that truthful
closure as document identity v3. The bounded correction permits spec-only
identity construction only from the downstream replay caller; ordinary v4 builds
still fail if their six process-config references are absent. This changes no
identity preimage field, source, repair or link policy, dependency, provenance
meaning, resource limit, or source/model execution boundary.

Use fresh `replay_v21/`, `prelaunch_recovery_v21/`, `initial_launch_v21/`,
`execution_attempt_v11/`, progress `replay_v21/document_progress/attempt_v11/`,
and tmux `er-commons-06g-replay-v21`. Include all four v20 roots in recovery and
cumulative accounting. Validate the full relink and downstream identity path,
repeat complete source-free preparation and independent review, then launch and
actively observe beyond the first preserved-source downstream publication and
through the first several minutes or terminal completion.

### Authorized replay-v22 preflight-path correction (2026-09-12)

Replay v21 stopped during preflight because the operator supplied a mistyped
attempt parent, `/Volumesnth/x10pro/...`, rather than the accepted sibling under
`/Volumes/x10pro/.../06g/`. Preflight correctly created no replay, launch,
attempt, progress, or supervisor artifact, but its immutable accepted receipt
records that unusable path under `prelaunch_recovery_v21/`; preserve that root
exactly and include it in cumulative accounting. The next attempt ordinal
therefore remains 11: replay-lineage ordinals count frozen preparation packets,
while attempt ordinals count supervisor executions.

The bounded prevention rejects prelaunch replay, attempt, and receipt roots
unless their resolved parents are identical and validates the attempt ordinal
before publishing a receipt. Use fresh `replay_v22/`,
`prelaunch_recovery_v22/`, `initial_launch_v22/`, still-unused
`execution_attempt_v11/`, progress
`replay_v22/document_progress/attempt_v11/`, and tmux
`er-commons-06g-replay-v22`. This changes no repair policy, identity meaning,
dependency, provenance, resource limit, or source/model execution boundary.
Repeat the full source-free preparation and independent prelaunch review, then
launch and actively observe beyond the prior 136-second failure boundary and
through the first several minutes or terminal completion.

### Authorized replay-v23 recorded-identity verification continuation (2026-09-12)

Replay v22 passed complete source-free preparation and independent review, then
attempt 11 was actively observed through terminal failure after 137.3843
seconds. All three repaired document commands completed. The collection command
published completion-last K4 linked and downstream document candidates before
the compact candidate metadata verifier rejected the persisted downstream
identity. Preserve `prelaunch_recovery_v22/`, `replay_v22/`,
`initial_launch_v22/`, and failed `execution_attempt_v11/` exactly. The failed
replay also contains a second K4 diagnostic descendant published by a
post-failure reproduction after the code identity changed; retain it as
non-attempt diagnostic evidence and account for the entire root.

The defect is a stale verifier preimage: document identity v3/v4 writers bind
the authority-aware resolved-spec reference and, for v4, the six resolved
process-config references, while the compact metadata verifier recomputed only
the legacy control fields. The bounded correction reconstructs the exact
versioned controls already persisted in the identity record. It changes no
identity preimage, source, repair/link policy, dependency, provenance meaning,
resource limit, or source/model execution boundary. The original v22 K4
downstream candidate verifies under the corrected reader.

Use fresh `replay_v23/`, `prelaunch_recovery_v23/`, `initial_launch_v23/`,
`execution_attempt_v12/`, progress `replay_v23/document_progress/attempt_v12/`,
and tmux `er-commons-06g-replay-v23`. Include all v22 roots in recovery and
cumulative accounting. Repeat full source-free preparation, production-shaped
K4 verification, and independent prelaunch review, then launch and actively
observe beyond K4 and through the first several minutes or terminal completion.

### Authorized replay-v24 verifier-owner freeze continuation (2026-09-12)

Independent v23 prelaunch review correctly stopped before launch because the
newly changed compact metadata verifier owner,
`src/er_commons/document_publication/storage.py`, was not in the frozen
generator or production-identity owner inventories. Preserve
`prelaunch_recovery_v23/` and `replay_v23/` exactly; no v23 launch, attempt, or
progress namespace exists, so attempt 12 remains unused.

Replay v24 adds that runtime owner to both maintained freezes and refreshes all
dependent hashes. This is provenance closure for the already-reviewed verifier
correction, not a change to identity, repair/link policy, dependency semantics,
resource limits, or the source/model execution boundary. Use fresh
`replay_v24/`, `prelaunch_recovery_v24/`, `initial_launch_v24/`, still-unused
`execution_attempt_v12/`, progress
`replay_v24/document_progress/attempt_v12/`, and tmux
`er-commons-06g-replay-v24`. Repeat full source-free preparation and independent
review before launch, then actively observe beyond K4 and through the first
several minutes or terminal completion.

### Authorized replay-v25 resolved-config verification-role continuation (2026-09-12)

Replay v24 passed preparation and independent review, then attempt 12 was
actively observed through terminal failure after 138.6745 seconds. It completed
all three repaired documents and successfully published linked and downstream
document descendants for the first nine preserved sources. It then published
the Final F1 linked candidate and stopped before its downstream descendant.
Preserve `prelaunch_recovery_v24/`, `replay_v24/`, `initial_launch_v24/`, and
failed `execution_attempt_v12/` exactly.

The first fresh v4 source exposed a compact-budget role mismatch. Its identity
correctly binds all six authority-aware resolved process configs, but upstream
verification labeled each hash with a dynamic role such as
`resolved_content_parsing_config`; the accepted compact allowlist uses the
semantic role `config`. The bounded correction retains the exact authority,
path, size, SHA-256, and source ID checks while using that existing allowlisted
role. Preserved v3 candidates have no process-config refs, explaining why the
first nine sources passed. This changes no repair/link policy, identity,
dependency, provenance meaning, resource limit, or source/model execution
boundary.

Use fresh `replay_v25/`, `prelaunch_recovery_v25/`, `initial_launch_v25/`,
`execution_attempt_v13/`, progress `replay_v25/document_progress/attempt_v13/`,
and tmux `er-commons-06g-replay-v25`. Include all v24 roots in recovery and
cumulative accounting. Repeat complete source-free preparation, v3/v4 verifier
tests, and independent prelaunch review, then launch and actively observe past
Final F1 and through the first several minutes or terminal completion.

### Authorized replay-v26 accepted FC1 alias-schema continuation (2026-09-12)

Replay v25 passed preparation and independent review, then attempt 13 was
actively observed through terminal failure after 212.3630 seconds. All three
repaired documents completed, and linked plus downstream document candidates
published for the first 24 collection sources, including Final F1. Source 25,
`deir_main`, then failed during pre-completion output validation. Preserve
`prelaunch_recovery_v25/`, `replay_v25/`, `initial_launch_v25/`, failed
`execution_attempt_v13/`, and the two source-free main-relink diagnostic roots
exactly.

The failure is a frozen schema dependency mismatch. Task 06F already accepted
and emits `linking_v2_fc1_body_figure_caption`; Task 06G correctly used its v2
support and completion schemas but still selected the legacy v1 alias schema,
which cannot represent that accepted origin. The bounded correction selects the
existing `document_linking/v2/alias.schema.json` and freezes it in the production
contract. It changes no alias row, FC1 repair policy, identity meaning, source,
dependency semantics beyond closing the accepted producer/consumer version,
resource limit, or source/model execution boundary.

Use fresh `replay_v26/`, `prelaunch_recovery_v26/`, `initial_launch_v26/`,
`execution_attempt_v14/`, progress `replay_v26/document_progress/attempt_v14/`,
and tmux `er-commons-06g-replay-v26`. Include all v25 and diagnostic roots in
recovery and cumulative accounting. Validate the full source-free `deir_main`
relink and downstream boundary, repeat independent prelaunch review, then launch
and actively observe beyond source 25 and through completion or a later failure.

### Authorized replay-v27 v2 alias-seal correction (2026-09-12)

Independent v26 review validated the actual `deir_main` relink products and
downstream identity source-free, but correctly blocked launch because the link
template's v2 alias path still carried the legacy v1 SHA-256 and byte size.
Preserve `prelaunch_recovery_v26/`, `replay_v26/`, and
`diagnostic_v26_main_schema_gate/` exactly; no v26 launch, attempt, or progress
namespace exists, so attempt 14 remains unused.

The v27 correction refreshes that one nested authority reference to the existing
v2 alias schema's exact digest and size and regenerates the frozen template
digest. It changes no schema content, emitted row, FC1 policy, identity meaning,
dependency, provenance, resource limit, or source/model execution boundary. Use
fresh `replay_v27/`, `prelaunch_recovery_v27/`, `initial_launch_v27/`,
still-unused `execution_attempt_v14/`, progress
`replay_v27/document_progress/attempt_v14/`, and tmux
`er-commons-06g-replay-v27`. Repeat exact generation, source-free preparation,
and independent review, then launch and actively observe beyond source 25.

### Authorized replay-v28 relink verification-envelope correction (2026-09-12)

Replay v27 passed the complete source-free gate and independent review, then
attempt 14 ran for 291.5413 seconds. All three repaired documents completed and
31 of 35 linked candidates published before the collection relink stopped at
`deir_appendix_g2`. The accepted G2 `tables.jsonl` is 649,451,594 bytes, which
exceeds the generic 512-MiB per-file evidence-read cap; later accepted inputs
include a 1,174,032,051-byte G3 table file and the 35-source canonical-record
manifest totals 5,001,823,926 bytes, exceeding the generic 2-GiB cumulative cap.
This was not a supervisor resource stop: peak RSS was 8,092,909,568 bytes,
output was 4,605,126,676 bytes, and swap growth was zero.

Preserve `prelaunch_recovery_v27/`, `replay_v27/`, `initial_launch_v27/`, failed
`execution_attempt_v14/`, and `diagnostic_v27_g2_sandbox/` exactly. The bounded
v28 correction gives relink verification an explicit 2-GiB per-file and 8-GiB
cumulative canonical-record read envelope while retaining the accepted 10-GiB
RSS, 32-GiB output, 64-GiB free-space, zero-swap-growth, and 24-hour supervisor
limits. It also durably emits captured child output before propagating a failed
reviewed command. This changes no accepted input, source order, repair/link
policy, identity preimage, dependency, provenance meaning, output namespace,
or source/model execution boundary; it only sizes source-free verification for
the already-frozen accepted manifest and closes failure observability.

Use fresh `replay_v28/`, `prelaunch_recovery_v28/`, `initial_launch_v28/`,
`execution_attempt_v15/`, progress `replay_v28/document_progress/attempt_v15/`,
and tmux `er-commons-06g-replay-v28`. Repeat generation, source-free preparation,
the full 35-source verification path, and independent review before launch;
then actively observe beyond source 32 and through terminal status.

The preserved G2 diagnostic initially used redundant hardlinked input scaffolds.
Those non-output directory entries were removed after their authoritative roots
were verified present, and the action is recorded by the diagnostic's no-clobber
scaffolding manifest. The retained diagnostic-owned packet is exactly 89 files
and 664,841 bytes, with zero protected payloads and zero symlinks; both evidence
record construction and verification pass. Evidence accounting may ignore a
producer-inventory row whose referenced file is absent from a partial snapshot,
but continues to reject unsafe paths, symlinks, malformed or size-mismatched
present rows, conflicting digests, and every retained PDF/image/model payload
lacking exact inherited inventory evidence.

### Authorized replay-v29 bounded-memory correction (2026-09-12)

Replay v28 passed generation, full source-free preparation, all three independent
prelaunch reviews, and the complete 1,937-test repository gate. Attempt 15 ran
all three repaired documents and produced 33 of 35 terminal linked candidates,
clearing the earlier G2 verification-budget failure. At 329.2265 seconds the
supervisor terminated the attempt because system-wide macOS swap usage grew by
220,856,320 bytes from its launch baseline. Peak process-tree RSS was
9,443,524,608 bytes, peak output was 7,299,869,904 bytes, no child survived, and
collection handoff, comparison, and final completion were not published.
Preserve `prelaunch_recovery_v28/`, `replay_v28/`, `initial_launch_v28/`, and
`execution_attempt_v15/` as failed evidence.

The identified pipeline memory-pressure defect is cumulative in-process object
retention, not a source, repair, or identity deviation. Because the swap metric
is system-wide, attempt 15 cannot prove that this defect alone caused every byte
of observed swap growth. The collection loop retained every full `RelinkBuild`,
including remapped canonical rows, until final handoff. Replay v29 retains only
the two terminal completion paths per source and releases the full build before
downstream publication. JSONL storage also reads and writes line-wise, preserving
the exact serialization while avoiding duplicate whole-file text buffers. The
zero-swap-growth, 10-GiB RSS, 32-GiB cumulative-output, source-free, source-order,
identity, provenance, and no-clobber policies remain unchanged.

Use fresh `replay_v29/`, `prelaunch_recovery_v29/`, `initial_launch_v29/`,
`execution_attempt_v16/`, progress `replay_v29/document_progress/attempt_v16/`,
and tmux `er-commons-06g-replay-v29`. The preserved-evidence ledger adds the four
v28 roots and must close at 88 roots before the v29 recovery receipt. Validate
the compact-result lifetime and byte-equivalent streaming behavior, repeat the
full source-free preparation and independent byte-level launch review, and then
actively observe through terminal status.

### Authorized replay-v30 same-source memory correction (2026-09-12)

Replay v29 recovery and preparation passed, but no launch packet or execution
attempt was created. A guarded 35-source no-write validation proved zero swap
growth and removed cumulative build retention, yet peak process-tree RSS was
10,485,497,856 bytes—only 251,920,384 bytes below the unchanged 10-GiB limit
before adding the real supervisor and driver overhead. Preserve
`prelaunch_recovery_v29/` and `replay_v29/`; attempt 16 remains unused.

The remaining overlap held both the upstream canonical row graph and its fully
remapped output graph during publication. After all build and FC1-equivalence
semantics finish, replay v30 replaces the in-memory source with its compact
sealed root and manifest before writing and verifying the already-built rows.
The publisher consumes only that root, manifest, and completed build, so output
bytes, identity, provenance, order, validation, and no-clobber behavior do not
change. Fresh v30 preparation must freeze this owner and add both v29 roots to
the ledger. Use `replay_v30/`, `prelaunch_recovery_v30/`,
`initial_launch_v30/`, still-unused `execution_attempt_v16/`, progress
`replay_v30/document_progress/attempt_v16/`, and tmux
`er-commons-06g-replay-v30`. Launch only after guarded memory validation and
independent review show adequate headroom under the unchanged limits.

### Authorized replay-v31 in-place remap freeze (2026-09-12)

Replay v30 recovery and preparation are preserved prelaunch; attempt 16 remains
unused. The first same-source boundary did not reduce peak during build because
the remapped graph had already been copied. The reviewed v31 optimization
remaps non-FC1 canonical rows in their existing in-memory containers after
target-index construction. It retains the copying path for `deir_main`, whose
FC1 equivalence requires upstream IDs, and indexes R6 table markers under both
upstream and local target IDs so chapter-scoped navigation remains identical.
A complete copy-versus-in-place build regression closes ordinary references,
nested R6 navigation, provenance, and exact serialized output equivalence.

The authoritative 35-source guarded run peaked at 6,282,838,016 bytes, leaving
4,454,580,224 bytes beneath the unchanged 10-GiB cap, with zero swap growth,
zero prohibited access, zero writes, all 35 schemas valid, and 5,051,045,327
accepted bytes read. Freeze those exact owners in fresh `replay_v31/` and
`prelaunch_recovery_v31/`, add both v30 roots to the ledger, and use
`initial_launch_v31/`, still-unused `execution_attempt_v16/`, progress
`replay_v31/document_progress/attempt_v16/`, and tmux
`er-commons-06g-replay-v31` after final review.

### Authorized replay-v32 external-reserve correction (2026-09-12)

Replay v31 recovery and preparation are preserved prelaunch; no launch packet,
progress root, supervisor attempt, or tmux session was created, so attempt 16
remains unused. Final accounting review found that the generated initial-launch
packet is approximately 22.77 MB, while the fixed external-metadata reserve was
only 16 MiB. That reserve understated launch-owned metadata even though the
attempt-root `command.log` and `status.json` are already counted dynamically by
the supervisor.

Replay v32 raises only the external-metadata reserve to 64 MiB and makes the
launcher reject any actual assembled packet larger than the ledger reserve.
The cumulative cap remains exactly 32 GiB: the larger reserve reduces the
supervisor allowance by the same amount. The guarded 35-source memory result,
zero-swap policy, source-free boundary, identities, provenance, repair policy,
commands, and output semantics are unchanged. Preserve
`prelaunch_recovery_v31/` and `replay_v31/`, add both roots to the cumulative
ledger, and use fresh `replay_v32/`, `prelaunch_recovery_v32/`,
`initial_launch_v32/`, still-unused `execution_attempt_v16/`, progress
`replay_v32/document_progress/attempt_v16/`, and tmux
`er-commons-06g-replay-v32`. Launch only after the regenerated frozen packet,
recovery preflight, source-free preparation, and independent review pass.

### Replay-v32 terminal handoff-selection failure (2026-09-12)

Replay v32 passed recovery, preparation, three independent prelaunch reviews,
and the complete repository check, then launched under tmux
`er-commons-06g-replay-v32` into fresh `execution_attempt_v16/`. Active
observation continued beyond the prior failure window. All three document
commands and all 35 relink/downstream document publications completed before
collection assembly failed terminally after 360.835 seconds. Peak RSS was
6,324,207,616 bytes, peak output was 12,256,152,925 bytes, swap growth remained
zero, and no process survived. Preserve `prelaunch_recovery_v32/`,
`replay_v32/`, `initial_launch_v32/`, and `execution_attempt_v16/` exactly.

The failure is a bounded evidence-selection defect. The three freshly processed
documents each truthfully retain both an ordinary process candidate and its
downstream replay descendant. The collection contract already declares
`downstream_replay_only`, but terminal observation used the generic candidate
lookup and therefore rejected the two matching lineage levels as ambiguous.
Candidate selection now propagates the declared evidence kind, retains the
generic ambiguity guard, verifies the selected replay, and never chooses by
recency or filesystem order. Focused collection/replay/publication tests pass.
This changes no source, repair, identity preimage, or output row.

A fresh full replay is not launchable under the accepted cumulative cap.
Preserved 06G evidence now totals 30,228,685,365 bytes; after the 64-MiB reserve,
only 4,063,944,139 bytes remain, while replay v32 itself required
12,256,071,647 bytes. The accepted contract also forbids applying changed code
to a same-root resume. Proceeding therefore requires renewed review of a
material dependency/provenance amendment that publishes only fresh handoff and
comparison descendants from the exact verified v32 terminal relink candidates,
or a material resource-policy amendment. The amended frozen owner inventory
must also add `document_publication/outcomes.py`, which controls this selection
but was not bound by the v32 production identity. Do not launch another attempt
until one of those contracts is accepted.

## Current implementation owners

Use Task 06B's closure map if files moved:

- `document_publication`: stage identity, attempts, reuse, downstream replay,
  and completion-last document publication.
- `document_records/document_references/relink_publication.py`: sealed relink
  inputs and atomic linked-document publication.
- `document_records/document_references/relink_replay.py`: prepared sequential
  document replay and collection assembly.
- `collection_processing`: accounting, target index, cross-document resolution,
  handoff assembly and validation.
- `source_family_catalog.py`: explicit source identity and routing evidence.

The shared exact resolver remains beneath machine and reviewed-navigation
adapters. Keep Task 04D's accepted linking policy, including existing qualified
body-caption behavior, unless an accepted preceding subtask explicitly changes
one owned policy. Do not create a Task 06 resolver.

## Outputs

1. A frozen replay specification, stage dependency table, and resource budget.
2. Fresh affected document stage records and terminal document publications.
3. Explicit reused-input references preserving original manifests and seals.
4. A fresh source-family catalog/scope binding where required by substitution.
5. Complete collection accounting, target index, cross-document resolution,
   mechanical handoff, completion records, and inventories.
6. Old/new entity correspondence and complete semantic difference accounting.
7. A review input packet for 06H with no implied human acceptance.

## Research / learning checkpoint

Explain the difference between reusing immutable upstream evidence and copying
its records into a new identity. Explain why a changed source catalog may
invalidate collection or link identities even when a document's content is
unchanged. Record the existing identity contracts and maintainers' primary
serialization/checksum documentation only where an implementation choice needs
support. Do not research live source URLs or add an orchestration framework.

## Plan / spec requirement

### Gate 1: freeze exact mixed-lineage inputs

Task 06A's accepted design must specify how one replacement collection consumes
unchanged sources from their original sealed manifest and F1 from its fresh
source lineage. Preserve original manifest references for unaffected sources.
Do not fabricate a new source release that claims to have acquired all existing
files, or rewrite old manifest membership to accommodate F1.

A compact correspondence record must bind each selected logical source to:
old source identity/manifest, selected source identity/manifest, old and selected
stage completions, allowed reuse basis, change class, and expected descendants.
If existing collection contracts cannot express this safely, stop and complete
the already scoped contract/interface change from 06A/06B before execution.
Do not improvise a private mixed-lineage bypass in a corpus script.

Freeze exact configuration paths, source order, source-family entries, final
policy versions, owned code/schema digests, artifact destinations, and commands.
State whether each stage reads source bytes, model evidence, canonical records,
or only compact metadata. No source/model execution is implicitly authorized
by the word replay.

Record finite elapsed, memory/thread, output-disk, and temporary-disk bounds
from actual preceding evidence. State free-space minimum and source order.
Unknown estimates require a bounded proposal before execution, not guessed
observations. Use visible sequential progress and per-stage failure context.

### Gate 2: implement any remaining source-free integration

Only integration already selected by the accepted predecessor contracts belongs
here. Keep source selection, identity derivation, record construction, and
publication separate. Tests must demonstrate mixed explicit provenance,
correct invalidation, no-clobber behavior, and ordinary sealed reuse without
source reads or large-payload rehashes.

An implementation gap that changes repair semantics returns to its owning task.
Run focused tests, formatting, linting, strict typing, and human code-quality
review before requesting the bounded replay gate.

### Gate 3: separately authorized affected replay

Apply the accepted invalidation table:

| Evidence | Required treatment |
| --- | --- |
| Wrong accepted F1 source and descendants | Preserve; never substitute as valid F1 |
| Qualified Final F1 conversion/producer | Reuse 06C seals; no reconversion |
| F1 heading evidence and later structural/target stages | Build the separate heading producer source-free from the accepted 06C conversion, then apply accepted repair policies where eligible |
| Appendix A conversion/producer | Reuse; start at accepted duplicate-repair owner |
| Main-document conversion/producer | Reuse; apply chapter and figure repairs |
| Other documents | Reuse owning stages unless declared dependencies invalidate them |
| Changed document aliases/links/publication | Rebuild only required descendants |
| Collection accounting/index/resolution/handoff | Rebuild with all selected sources |
| Task 04 human usability | Carry evidence for 06H; do not auto-approve |
| Task 05D/05E and accepted 05F outcome | Preserve unchanged; later 05G owns replay |

Determine actual reuse from identity dependencies, not from a desired fixed
number of regenerated documents. A global code/policy identity may require new
link publications for otherwise unchanged documents; explain that distinction
from rerunning extraction. Record every deviation from the frozen table and
stop before an undeclared earlier stage.

Each completed stage seals newly authored outputs once and publishes completion
last. Matching completed stages use the maintained receipt/metadata path. Do
not hash a large PDF to prove a downstream-only stage may resume.

### Gate 4: semantic change accounting

Do not compare raw entity IDs across fresh namespaces and call all differences
content changes. Build validated correspondence using immutable source evidence,
physical page/block provenance, owning-stage mappings, and explicit operation
records. Support one-to-one unchanged mappings, many-to-one duplicate merges,
new chapter/figure targets, removed invalid targets, and substituted F1 entities.

Never create correspondence by fuzzy text similarity. Substituted F1 has new
source content; do not invent entity equivalence with the wrong document.
For unchanged entities compare substantive fields after applying the actual ID
mapping to references, parents, destinations, and provenance pointers. Retain
identity differences separately. Reject incomplete, noninjective unexplained,
or dangling mappings.

Account for all target and alias additions/removals/merges, changed local and
collection links, unresolved cardinalities, and source-family effects. Link
diffs must name old/new source and destination evidence after mapping, exact
reason, and owning repair. Preserve legitimate unresolved outcomes.

Reproduce planning controls independently from canonical evidence: Appendix A
has one logical target for each observed Chapter 06/08 pair; main Chapters 8/9
have real chapter targets and extents; figure candidates use their own eligible
captions. The 78/79 mention and 34/35 figure planning counts are expectations to
reconcile, not assertions to enforce by manufacturing targets. `Figure 4.8`
remains absent unless new independent accepted source evidence proves otherwise.

### Gate 5: publish mechanically validated review candidate

Assemble and validate one coherent collection handoff with exact source order,
accounting, target index, resolution, inventories, and completion links. A
`ready` handoff deliberately retains `task04_status: not_evaluated`; it is not
human approval. Supply 06H with change accounting, correspondence, and exact
review selections, then stop.

## Stop and resume policy

Stop on source/edition mismatch, changed policy, missing seal, unexpected file,
unmapped semantic difference, undeclared extraction dependency, resource
exhaustion, or inconsistent collection membership. Preserve diagnostics and
completed stages; never overwrite accepted predecessors to make replay pass.

Resume only after the cause and exact invalidation scope are understood. A
changed output-affecting input allocates fresh descendant identities. A matching
terminal stage is reused without PDF/model access. Incomplete output cannot
impersonate a terminal completion. A same-recipe retry keeps `replay_v1/` but
allocates a new `execution_attempt_vN/`; supervisor attempt roots are never
reused. Restart tests must cover interruption between document publication and
collection assembly and a child success followed by supervisor-terminal
failure. Neither case may publish Task 06G readiness prematurely.

## Validation

Use existing synthetic document, relink, collection, and publication fixtures.
Prove mixed source provenance, wrong-source rejection, mapped semantic equality,
merge/add/remove accounting, shuffled input determinism, exact closure,
stale-policy rejection, and no extraction on downstream reuse. Instrument source
reads, conversion calls, and large-file hashing to fail during source-free tests.

Run `make fix`, `make check`, focused replay/collection tests, and
`git diff --check`. After authorized replay, validate compact seals, exact file
sets and sizes, recorded counts, restart reuse, and the complete difference
report. Do not repeat expensive checks without new evidence of a problem.

## Review pass and acceptance criteria

Independently review provenance and edition, minimal invalidation, actual ID
correspondence, unchanged-content proof, precision, and maintainability. Close
only when every selected source and changed entity is accounted, every terminal
stage validates, a fresh supervisor attempt has a terminal succeeded
`execution.json` after final accounting, the separate finalizer has published
Task 06G completion last, and 06H can reproduce its review packet from the
declared inputs. Mechanical readiness is this task's terminal boundary.

## Non-goals

Human usability acceptance, Task 05F resolver changes or replay, guaranteeing 66
F1 links, fuzzy matching, source reacquisition, repeated conversion, cleanup,
commit, push, or benchmark/inventory publication.

## Outcome

Complete and accepted on 2026-09-12. The exact candidate and collection
identities, replay command and bounds, reused and regenerated stages,
correspondence and difference summaries, restart evidence, resource use, and
the precise Task 06H review gate are recorded in the Phase 2 outcome below.

## Task 06B interface handoff

Both Task 06B gates now supply the maintained
[command map](../../docs/pipeline_commands.md) and
[executed owner map](../../docs/specs/task06b_gate2_executed_inventory.md).
Use explicit current requests with original per-source accepted manifests and
seals; historical recipe validation does not reopen removed implementation paths.
Document/collection v3 supports declared replacement membership. Compact checks
must retain the shared verification budget and must not claim new payload-byte
equality. This handoff updates interfaces only; the task's provisional policy and
separate source, conversion, replay or review authorization boundaries still apply.

## Phase 2 bounded replay-v36 correction (2026-09-12)

Preserve replay v32 and every v33-v35 recovery, prelaunch, launch, diagnostic,
and attempt artifact. Attempt 17 failed before collection publication because
the full production-shaped comparison exposed a link-policy implementation
leak: the shared mention resolver used the global figure-alias switch after
per-source alias construction had correctly disabled figure aliases. The exact
affected population is 701 non-main figure mentions across 21 sources,
including 92 Final F1 mentions. Their accepted result remains unresolved with
`accepted_target_type_unavailable`, no candidates, no cross-document evidence,
and no FC1 support. Only `deir_main` may consume the accepted Task 06F figure
authority.

Replay v36 is the fresh source-free descendant. It repairs that implementation
boundary, adds a sealed-output policy gate after each relink, and restores the
complete v32-shaped graph: rebuild the three repaired document descendants,
relink and republish all 35 document candidates, rebuild collection handoff and
comparison, then validate terminal closure. It reuses all accepted conversion,
producer, canonical-record, review, and Task 06B-06F evidence without opening
or hashing PDF/image/model payloads. The launch must regenerate and byte-compare
the full initial resolved packet, verify compact inputs and imported candidate
file sets/sizes against their sealed inventories without payload hashing, and
derive all staged paths and checkpoint bindings from the v36 namespace.

Use `replay_v36/`, `prelaunch_recovery_v36/`, `initial_launch_v36/`,
`execution_attempt_v18/`, `replay_v36/document_progress/attempt_v18/`, and tmux
session `er-commons-06g-replay-v36`. The cumulative preserved-plus-new output
cap is 52 GiB, minimum free space is 64 GiB, RSS is capped at 10 GiB, and swap
growth remains forbidden. The larger cumulative cap is a reviewed accounting
amendment required to preserve v32-v35 while producing one honest full replay;
it does not authorize source/model execution or broader repair policy. Run the
actual prelaunch dry path and obtain independent review of the frozen v36
packet before launch. After launch, actively observe through the early failure
window. Stop only for a new repair-policy change, a source/model execution
requirement, or another material scope deviation.

### Replay-v36 preparation failure and bounded v37 continuation

The actual prelaunch recovery and initial resolution passed for v36, but compact
preparation stopped before staging inputs or starting a supervisor. The frozen
document-process templates still carried v32 output-root fields, so fresh-lineage
validation correctly rejected them. Preserve `prelaunch_recovery_v36/` and
`replay_v36/` exactly; `initial_launch_v36/` and `execution_attempt_v18/` were
never created.

Replay v37 changes only path-dependent process-template roots and their derived
owner/identity bindings. Ten templates are copied into `configs/task06/v4/`:
all six Final F1 process templates plus the structure and link templates for
Appendix A and main. They target `replay_v37` and retain the accepted stage
semantics. Use `prelaunch_recovery_v37/`, `replay_v37/`,
`initial_launch_v37/`, `execution_attempt_v19/`,
`replay_v37/document_progress/attempt_v19/`, and tmux
`er-commons-06g-replay-v37`. V36 recovery/replay join the preservation ledger;
the 52-GiB cumulative cap and all source/model prohibitions remain unchanged.

### Replay-v37 comparison failure and bounded v38 continuation

Replay v37 passed the full source-free preparation and independent packet
review, then launched attempt 19 in `er-commons-06g-replay-v37`. It completed
all three repaired document commands, all 35 relink/downstream candidates, the
per-source figure-policy gate, and collection accounting, indexing, resolution,
contract, and handoff with zero swap growth. The first comparison pass then
failed terminally after 388.189 seconds on
`cross-reference/deir_appendix_f1/xref000001`. Preserve the complete v37
recovery, replay, launch, and failed attempt-19 evidence.

The failure was a comparison authority-projection defect, not a repair-policy
change: canonical cross-reference rows encode the source in their record and
document IDs and do not carry the synthetic `source_id` field the comparator
had assumed. The bounded correction authorizes the exact observed Final F1
source substitution population from those canonical IDs: 66 removed Draft F1
rows and 331 added Final F1 rows. It also records Task 06F as owner of the exact
31 main-document figure transitions from
`accepted_target_type_unavailable` to `no_local_alias`, without fabricating a
target or broadening the figure policy.

A source-free production-shaped comparison then exposed one accepted Task 04C
navigation link whose unchanged source-local target retained an older extraction
namespace. The relinker now rebinds reviewed source-local record IDs by their
record type, source, and local ID while preserving stable navigation IDs. A
runtime gate requires all 28 accepted Task 04C links to remain uniquely resolved
to the same source-local targets, rejecting malformed or duplicate decisions
before collection publication.

Replay v38 is the fresh no-clobber descendant. It retains all v37 repair
decisions, templates, source-free restrictions, limits, and stage graph while
refreshing only the affected code and owner identities. Use
`prelaunch_recovery_v38/`, `replay_v38/`, `initial_launch_v38/`,
`execution_attempt_v20/`, `replay_v38/document_progress/attempt_v20/`, and tmux
`er-commons-06g-replay-v38`. Cumulative preserved evidence is 42,898,306,813
bytes; the 64-MiB reserve leaves 12,869,159,171 bytes for attempt 20. V37 peaked
at 12,374,863,442 output bytes, leaving a 494,295,729-byte margin under the
unchanged 52-GiB cap. Run the actual prelaunch path and independent frozen-packet
review before launch, then actively observe through document, relink, collection,
and comparison gates. Any resource-cap exceedance remains a material deviation;
do not raise the cap silently.

### Replay-v38 execution and finalization outcome

The reviewed v38 packet launched attempt 20 through
`initial_launch_v38/` and tmux `er-commons-06g-replay-v38`. The exact driver
binding SHA-256 was
`83a225a990312a3ada1e4050be0f219fe0f99a6feaf52aff899d56bd4f1851e4`.
The supervisor completed successfully in 414.510 seconds with return code zero,
9,548,333,056 peak RSS bytes, 12,382,222,153 peak output bytes, and zero swap
growth. All three repaired document commands and all 35 relink/downstream
candidates completed. Runtime gates verified 701 disabled-source figure mentions,
479 enabled `deir_main` figure mentions, and all 28 inherited Task 04C navigation
links before collection publication. The preserved runtime log labels the combined
1,180-mention population as disabled-source mentions; that label is inaccurate, but
the gate's enabled/disabled policy and result are correct. The terminal handoff is
`handoffv1-3603a7974be9b9dc7471dfd9a64e27468a2bdc67d44cef4944b8c24a5d60f8b9`.

Correspondence and comparison completed successfully. Ordinary-reference
population changed from 5,088 to 5,353 rows: 4,543 unchanged, 479 changed, 66
removed Draft F1 rows, and 331 added Final F1 rows. Every delta has an accepted
Task 06C, 06D, 06E, or 06F owner; `task04_status` remains `not_evaluated` for
Task 06H.

The first separate finalization attempt exposed the pre-existing assumption
that every execution ordinal must exist, contradicting the explicitly unused
attempt 18. Preserve `finalization_attempt_v1/failure.json`. The independently
reviewed finalization-only amendment binds the original v38 generation and
finalizer owner, the corrected finalizer/wrapper owners, successful attempt 20,
the exact launch and output seals, attempts 1-17/19/20, and unused attempt 18.
No production replay was required.

Finalization attempt 2 then atomically published a candidate before its
post-publication verifier attempted to hash a preserved PNG. Preserve
`finalization_attempt_v2/` and
`replay_v38/readiness_candidates/finalization_attempt_v2/` as unaccepted
evidence. The second reviewed amendment binds those exact artifacts and changes
only replay-root revalidation: prohibited payload identity comes from contained
sealed inventories and current file size, never payload hashing.

Finalization attempt 3 passed. Its validation receipt is
`finalization_attempt_v3/validation_receipt.json`; the accepted review-ready
candidate is
`replay_v38/readiness_candidates/finalization_attempt_v3/`. Its artifact
inventory precedes readiness, readiness precedes completion, and
`completion.json` is last. The readiness inventory records 101,647 files and
55,419,121,470 cumulative bytes across 118 external evidence roots, leaving
415,453,378 bytes below the 52-GiB cap. It binds finalization amendment v2
SHA-256 `79793f06cdac949d34db004b3c3b4e5898e97aa82eda0510b9567e2ab9dd7c75`.

The user accepted the successful execution and finalization result on
2026-09-12. Task 06G is complete. Task 06H and Task 05G were not started. The
user authorized a local commit of this outcome; push remains unauthorized.
