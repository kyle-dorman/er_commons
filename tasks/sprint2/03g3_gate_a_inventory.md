# Task 03G.3 Gate A Inventory

Status: **frozen and explicitly accepted on 2026-08-18**. This inventory is the
evidence appendix for
[Task 03G.3](03g3_align_pipeline_responsibilities_and_names.md). It authorizes
no implementation, PDF/model work, commit, or Task 03H activation.

## Inventory method and boundary

The inventory traced imports from `src/er_commons/cli.py`, all maintained
package `__init__.py` files, every Python import under `src/` and `tests/`, the
root `Makefile`, checked-in configs, schemas, fixtures, generators, current
documentation, and retained diagnostic/replay tools. All Python modules below
are in scope, including their direct test imports. Completed task prose,
accepted external artifacts, and accepted v1/v1.1/v2/v3 serialized bytes are
immutable evidence rather than edit targets.

## Executable graph

| Boundary | Current entry | Current behavior |
| --- | --- | --- |
| CLI document | `er-commons extraction run-document` | `corpus_extraction.run_document` performs preflight/reuse, attempt allocation, isolated execution, and publication or retained failure. |
| Document transformations | `corpus_extraction.owner_sequence.OwnerSequence` | Runs `baseline_producer`, `hierarchy_producer`, `canonical`, `hierarchy_correction`, `semantic`, and `cross_references` in that exact order. |
| CLI collection | `er-commons extraction run-scope` | `corpus_resolution.run_scope` runs/reuses documents, collects terminal evidence, and publishes the collection join. |
| Collection join | `corpus_resolution.pipeline.CorpusPipeline` | Publishes accounting, target index, cross-document resolution, handoff, and the validated contract bundle in that order. |
| Read-only handoff | `er-commons extraction validate-handoff` | Verifies one published handoff and successful document candidates without rebuilding. |
| Machine report | `extraction_review.pilot_reporting` | Validates a handoff, aggregates metrics/anomalies, and writes a non-authoritative completion-last report. |
| Human support | `extraction_review.{authorization,comparison,rendering,requests}` | Builds comparison evidence, authorization evidence, and request/render manifests for a human decision. |

The only public production orchestration commands are the three run/validate
commands above plus `extraction validate-contract`. The root `Makefile`,
`tests/test_cli.py`, `configs/README.md`, and current documentation are their
only repository callers.

## Maintained module inventory

Every module in these sets moves, is renamed, or is explicitly retained by the
Gate A map. `__init__` means the package public facade.

- `document_extraction` (21): `__init__`, `artifacts`, `complete_document`,
  `config`, `hierarchy/__init__`, `hierarchy/document`, `producer_artifacts`,
  `producer_config`, `producer_conversion`, `producer_identity`,
  `producer_publication`, `producer_records`, `producer_routing`,
  `producer_services`, `producer_tables`, `routing`, `routing_geometry`,
  `runtime`, `sources`, `table_markers`, `table_stage`.
- `table_extraction` (16): `__init__`, `continuations`, `families`, `fragments`,
  `learned_fallback`, `learned_table_acceptance`, `learned_table_cells`,
  `learned_table_geometry`, `learned_table_page`, `learned_table_text`,
  `learned_table_types`, `models`, `otsl`, `page`, `pipeline`,
  `tableformer_fallback`.
- `canonical_extraction` (28): `__init__`, `assets`, `bundle`, `candidate`,
  `candidate_identity`, `config`, `constants`, `content_records`, `context`,
  `errors`, `geometry`, `identifiers`, `identity`, `inputs`, `layout`,
  `materialize`, `policies/__init__`, `policies/bundle`, `policies/content`,
  `policies/lineage`, `provenance`, `publication`, `record_sets`,
  `support_records`, `table_projection`, `tables`, `traversal`, `validation`.
- `hierarchy_correction` (47): `__init__`, `application`, `bounded_acceptance`,
  `bundle`, `candidate_identity`, `candidate_publication`, `candidate_records`,
  `checks`, `code_inventory`, `configuration`, `constants`,
  `correction_policy`, `decision_builder`, `decisions`, `digests`, `errors`,
  `failures`, `features`, `hierarchy`, `hierarchy_builder`,
  `hierarchy_projection`, `identity`, `inputs`, `level_evidence`,
  `numbering_scopes`, `pdf_observations`, `preflight`, `publication`,
  `publication_authorization`, `regime_builder`, `regimes`,
  `rule_applications`, `rule_context`, `rules`, `scope_lifecycle`,
  `semantic_types`, `single_build`, `source_features`, `text_evidence`, `toc`,
  `toc_analysis`, `toc_builder`, `toc_reconciliation`, `toc_regions`,
  `toc_rows`, `toc_text`, `validation`.
- `semantic_structure` (14): `__init__`, `bundle`, `constants`, `errors`,
  `handoff`, `normalization`, `policies/__init__`, `policies/aliases`,
  `policies/bridge`, `policies/control`, `policies/correspondence`,
  `policies/page_labels`, `policies/sections`, `validation`.
- `semantic_materialization` (19): `__init__`, `aliases`, `baseline`, `bridge`,
  `comparison`, `config`, `construction`, `errors`, `identity`, `inputs`,
  `lifecycle`, `page_labels`, `producer_evidence`, `publication`, `runtime`,
  `sealing`, `sections`, `support`, `workflow`.
- `cross_reference_enrichment` (14): `__init__`, `config`, `construction`,
  `detection`, `identity`, `indexing`, `policy`, `publication`, `resolution`,
  `source_scope`, `storage`, `types`, `validation`, `workflow`.
- `corpus_extraction` (30): `__init__`, `attempts`, `candidates`, `config`,
  `content_owners`, `downstream_replay`, `downstream_replay_validation`,
  `fresh_lineage`, `fresh_preflight`, `hooks`, `identity`, `lifecycle`,
  `lineage_preflight`, `lineage_validation`, `observability`, `outcomes`,
  `owner_diagnostics`, `owner_inputs`, `owner_observations`, `owner_sequence`,
  `owner_validation`, `preflight`, `process`, `publication`, `records`,
  `sources`, `storage`, `task03g2_preparation`, `worker`, `workflow`.
- `corpus_resolution` (20): `__init__`, `accounting`, `attempts`, `bundle`,
  `catalog`, `config`, `document_targets`, `domain`, `evidence`, `handoff`,
  `handoff_validation`, `indexing`, `mentions`, `pipeline`, `preflight`,
  `publication`, `resolution`, `resolver`, `storage`, `workflow`.
- `corpus_extraction_contract_v1_1` (15): `__init__`, `__main__`, `accounting`,
  `artifacts`, `checks`, `errors`, `fixture_validation`, `handoff`, `identity`,
  `indexing`, `model`, `publication`, `resolution`, `synthetic_fixture`,
  `validation`.
- `extraction_review` (6): `__init__`, `authorization`, `comparison`,
  `pilot_reporting`, `rendering`, `requests`.
- `smoke_extraction` (14): `__init__`, `__main__`, `config`, `conversion`,
  `publication`, `records`, `reporting`, `routing`, `selection`, `services`,
  `source_processing`, `table_stage`, `warnings`, `workflow`.
- `task03g2f_replay` (9): `__init__`, `audit`, `config`, `errors`, `inventory`,
  `io`, `sources`, `table_audit`, `workflow`.

The root `extraction_regression.py`, `cli.py`, `settings.py`,
`source_freeze.py`, `source_models.py`, `source_validation.py`, and shared
source-family-catalog code are also affected callers or lower-level inputs.

## Public symbols and caller classes

The maintained package facades currently expose:

- document parsing: `run_complete_document_producer`;
- record mapping: `run_document_canonicalization`, `validate_bundle_integrity`,
  `ContractError`, `extraction_identity_sha256`, `make_record_id`, and
  `pdf_bbox_to_render_pixels`;
- hierarchy: `run_hierarchy_correction`,
  `validate_hierarchy_correction_bundle`, and
  `HierarchyCorrectionContractError`;
- semantic structure/materialization: `run_semantic_materialization`, config
  and input loaders/types, semantic identity helpers, `validate_semantic_contract`,
  `normalize_alias`, `verify_task03e2d_control`, and bridge/error types;
- references: `run_cross_reference_enrichment`;
- document workflow: `run_document`;
- collection workflow: `run_scope`, `validate_handoff`, `ScopeRunSpec`, hooks,
  loaders, and `VerifiedHandoff`;
- v1.1 compatibility contract: validation, identity-build/validation, artifact
  reader, JSON object, and contract-error helpers;
- machine/human support: report, comparison, authorization, request, and render
  types/builders/writers exported from `extraction_review`;
- diagnostics/replay: `run_smoke`, `Task03G2FReplay`, `ReplayPaths`, and
  `ReplayOutcome`.

Tests directly import additional submodule types and helpers from every package
above. Gate B therefore updates all repository imports directly, including
private-name imports already used by tests; it does not preserve old module
paths with forwarding facades. The test/caller groups are:

- parsing and tables: `test_complete_document_*`, `test_document_extraction_*`,
  `test_table_extraction_*`, and the downstream input/identity tests;
- mapping: `test_canonical*`, `test_canonicalization_*`, and
  `test_document_stage_generalization.py`;
- hierarchy: `hierarchy_correction_support.py` and
  `test_hierarchy_correction_*`;
- document structure: `semantic_structure_support.py`,
  `test_semantic_structure_*`, and `test_semantic_materialization_*`;
- references: `test_cross_reference_enrichment*.py`;
- publication: `corpus_extraction_test_support.py` and
  `test_corpus_extraction_*`;
- collection: `corpus_resolution_test_support.py` and
  `test_corpus_resolution_*`;
- reporting/review: `test_extraction_review.py` and
  `test_extraction_review_pilot.py`;
- diagnostics/replay: `test_smoke_extraction.py`,
  `test_task03g2f_replay.py`, and
  `scripts/run_task03g2f_downstream_replay.py`.

## Hidden responsibilities and dependency defects

1. `hierarchy_correction/pdf_observations.py` and `source_features.py` parse PDF
   outline, printed-page metadata, native text, Docling items, and heading/TOC
   evidence inside the inference stage. Parsing must move behind the parsing
   boundary; Task 03H, not Task 03G.3, will make it independently sealable.
2. `document_extraction` currently owns content parsing, heading-enabled
   Docling parsing, routing, and table reconstruction and runs twice under the
   lifecycle word `producer`.
3. `corpus_resolution.resolution.ResolutionBuilder` combines source-family
   catalog sealing, eligible-mention derivation, and cross-document linking.
4. Document-local target indexing and collection target indexing are distinct
   policies and must not be merged. PDF page-label observation and resolved
   printed-page labels are likewise distinct facts.
5. `corpus_extraction.lineage_preflight` and `lineage_validation` form an
   internal cycle through a type-only reverse import. `candidates` and
   `downstream_replay` form a runtime cycle through a lazy reverse import.
6. Collection modules import document-workflow internals instead of a narrow
   published-document evidence interface.
7. Document publication imports generic storage helpers from a parser package.
   Neutral checksum/inventory primitives need a lower-level home.
8. Compatibility-only hierarchy facades (`decision_builder`, `features`,
   `hierarchy_builder`, `regime_builder`, and `toc_builder`) have only internal
   and test callers. They can be removed after direct imports move to their
   real implementations.

## Serialized/configuration inventory

The live Task 03G.2 workflow uses 18 per-source stage configs: two parsing
configs, record mapping, hierarchy inference, document structure, and document
reference linking for each of three sources. It also uses document and scope
run specs, a source-family catalog, target policy, and resolution policy under
`configs/brisbane_baylands_2025_deir_task03g2_*`.

The current serialized workflow keys are `document_owners`,
`baseline_producer`, `hierarchy_producer`, `canonical`,
`hierarchy_correction`, `semantic`, and `cross_references`. The same six role
names appear in document identity/completion evidence. They are maintained
process language and require a versioned successor rather than aliases or an
in-place rewrite.

The checked-in schemas and matching fixtures are:

- `benchmarks/er_bench/schemas/canonical_extraction/v1/records.schema.json`;
- `canonical_extraction/v2/semantic_structure.schema.json`;
- `canonical_extraction/v3/cross_references.schema.json`;
- `hierarchy_correction/v1/records.schema.json`; and
- `corpus_extraction/v1_1/records.schema.json`.

Their exact `$id`, schema bytes, fixtures, accepted configs, and external
artifacts remain immutable. The canonical v1/v2/v3 schemas do not change for a
code move because their record semantics do not change. A new workflow
contract v2 owns renamed run specs and stage-role keys; the v1/v1.1 readers
remain read-only compatibility code for accepted evidence.

## Artifact inventory and disposition

| Current surface | Disposition |
| --- | --- |
| `task_03g2_document_producers/<prv1-id>/` | Immutable accepted path; future parsing evidence uses a new operation-oriented root. |
| `task_03g2_canonical_records/<exv1-id>/` | Immutable accepted path; future repository records use a new root. |
| `documents/<source>/<docv1-id>/` | Preserve accepted candidates; future v2 publication uses a new root or versioned layout. |
| `scopes/<scopev1-id>/{accounting,target_indexes,resolutions,handoffs}` | Preserve product terms and accepted bytes; future collection root is versioned. |
| `canonical/{documents,pages,sections,blocks,tables,table_families,figures,images,assets,target_aliases,cross_references}` | Retain. These are precise repository record/data-model terms. |
| `review_cache`, human render/request manifests, bounded authorization evidence | Retain `review` only because these surfaces solicit or record human judgment. |
| representative pilot report v1 and its `review_evidence_complete` status | Immutable; new machine output becomes versioned `extraction_report` evidence. |

Future roots are `document_parse_evidence/`, `document_records/`,
`document_publications/`, and `collection_runs/`. Gate B must not move or
rewrite any accepted root.

## Documentation, generators, and retained tools

Current documents requiring Gate B updates are `docs/architecture.md`,
`docs/data_artifacts.md`, `docs/index.md`, `docs/todo.md`,
`docs/sprints/sprint2_brisbane_draft_eir_defense.md`, `configs/README.md`,
`pipelines/README.md`, and the provisional Task 03H contract. Existing
versioned specs and completed task outcomes remain historical evidence; a v2
workflow spec is additive.

`scripts/generate_task03g2_configs.py`, `generate_task03g2_identity.py`, and
`prepare_task03g2.py` either remain historical-only or receive new Task 03H/v2
counterparts. `task03g2f_replay` remains a bounded historical replay tool and
updates its imports directly. `smoke_extraction` and the root extraction
regression utility become `parser_smoke` and `parser_regression`; their future
diagnostic identities refresh rather than claiming reuse of old bytes.

## Legacy-name allowlist

The stale-name audit may allow old terms only in:

- immutable schemas, configs, fixtures, accepted external paths, and artifact
  bytes;
- explicit v1/v1.1 read-only readers, validators, and preservation adapters;
- completed task prose, durable decisions, and versioned historical specs;
- identity prefixes and persisted artifact/data-model fields such as `prv1-`,
  `exv1-`, `extraction_id`, `docv1-`, `scopev1-`, and canonical record terms;
- Task 03G.2f task/package/report names identifying that bounded replay;
- Task 04, human authorization, comparison request, render request/cache, and
  `frozen_review` surfaces that genuinely request or record human judgment; and
- ordinary prose about a software responsibility or human ownership.

No forwarding import package, Pydantic field alias, dual write, or acceptance
of v1 keys by v2 models is allowed. `owner` is removed from maintained runtime,
config, schema, diagnostic-code, and artifact-role names outside v1 readers.
