# Task 06B Gate 2 executed migration inventory

The frozen [06A inventory](task06a_code_inventory.md) remains unchanged. Every
listed path is accounted for below; destinations exist and retired/old executable
paths are absent. Historical JSON recipes, configs, schemas and accepted external
artifacts retain original paths and identities. No external artifacts were deleted.

| Original path | Result | Current owner |
| --- | --- | --- |
| `scripts/audit_hierarchy_candidate.py` | retained | `scripts/audit_hierarchy_candidate.py` |
| `scripts/audit_task04d_linking.py` | migrated | `scripts/audit_document_linking.py` |
| `scripts/build_task03j_final_review.py` | migrated | `scripts/build_final_extraction_review.py` |
| `scripts/build_task04_review_bundle.py` | migrated | `scripts/build_extraction_review_bundle.py` |
| `scripts/generate_task03g2_configs.py` | retired | `none; preserved historical recipe` |
| `scripts/generate_task03g2_identity.py` | retired | `none; preserved historical recipe` |
| `scripts/generate_task03h_configs.py` | migrated | `scripts/generate_document_configs.py` |
| `scripts/inspect_task03h_scaling.py` | migrated | `scripts/inspect_conversion_scaling.py` |
| `scripts/materialize_task04c_gate_b.py` | migrated | `scripts/materialize_reviewed_navigation.py` |
| `scripts/prepare_task03g2.py` | retired | `none; preserved historical recipe` |
| `scripts/prepare_task03h.py` | migrated | `scripts/prepare_document_inputs.py` |
| `scripts/prepare_task03j_v4.py` | migrated | `scripts/prepare_document_inputs.py` |
| `scripts/prepare_task04a_review.py` | migrated | `scripts/prepare_extraction_review.py` |
| `scripts/prepare_task04c_gate_a.py` | migrated | `scripts/prepare_reviewed_navigation.py` |
| `scripts/prepare_task04d_gate_c_specs.py` | migrated | `scripts/prepare_document_relink_specs.py` |
| `scripts/publish_task04a_gate_d.py` | migrated | `scripts/publish_extraction_review.py` |
| `scripts/reconcile_task04c_gate_c.py` | migrated | `scripts/reconcile_reviewed_navigation.py` |
| `scripts/record_task04_finding.py` | migrated | `scripts/record_review_finding.py` |
| `scripts/run_chunked_conversion.py` | retained | `scripts/run_chunked_conversion.py` |
| `scripts/run_task03g2f_downstream_replay.py` | retired | `none; preserved historical recipe` |
| `scripts/run_task03j_v4.py` | migrated | `scripts/run_document_collection.py` |
| `scripts/set_task04_finding_register_status.py` | migrated | `scripts/set_review_register_status.py` |
| `scripts/task03h_generation/__init__.py` | migrated | `src/er_commons/document_publication/config_generation/__init__.py` |
| `scripts/task03h_generation/process_templates.py` | migrated | `src/er_commons/document_publication/config_generation/process_templates.py` |
| `scripts/task03h_generation/production_identity.py` | migrated | `src/er_commons/document_publication/config_generation/production_identity.py` |
| `scripts/task03h_generation/shared.py` | migrated | `src/er_commons/document_publication/config_generation/shared.py` |
| `scripts/task03h_generation/specifications.py` | migrated | `src/er_commons/document_publication/config_generation/specifications.py` |
| `scripts/task03h_generation/workflow.py` | migrated | `src/er_commons/document_publication/config_generation/workflow.py` |
| `scripts/validate_task04d_gate_c.py` | migrated | `scripts/validate_document_relink_run.py` |
| `src/er_commons/collection_processing/compatibility_v1_bundle.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/document_performance/task03h_gate1.py` | migrated | `src/er_commons/document_performance/conversion_scaling.py` |
| `src/er_commons/document_performance/task03h_gateb.py` | migrated | `src/er_commons/document_performance/conversion_compatibility_audit.py` |
| `src/er_commons/document_publication/task03g2_preparation.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/document_publication/task03h_preparation.py` | migrated | `src/er_commons/document_publication/input_preparation.py` |
| `src/er_commons/human_review_support/task04/FINDINGS.md` | migrated | `src/er_commons/human_review_support/extraction_review/FINDINGS.md` |
| `src/er_commons/human_review_support/task04/__init__.py` | migrated | `src/er_commons/human_review_support/extraction_review/__init__.py` |
| `src/er_commons/human_review_support/task04/anchor_models.py` | migrated | `src/er_commons/human_review_support/extraction_review/anchor_models.py` |
| `src/er_commons/human_review_support/task04/application.py` | migrated | `src/er_commons/human_review_support/extraction_review/application.py` |
| `src/er_commons/human_review_support/task04/assets/__init__.py` | migrated | `src/er_commons/human_review_support/extraction_review/assets/__init__.py` |
| `src/er_commons/human_review_support/task04/assets/review.css` | migrated | `src/er_commons/human_review_support/extraction_review/assets/review.css` |
| `src/er_commons/human_review_support/task04/assets/review.html` | migrated | `src/er_commons/human_review_support/extraction_review/assets/review.html` |
| `src/er_commons/human_review_support/task04/assets/review.js` | migrated | `src/er_commons/human_review_support/extraction_review/assets/review.js` |
| `src/er_commons/human_review_support/task04/canonical_evidence.py` | migrated | `src/er_commons/human_review_support/extraction_review/canonical_evidence.py` |
| `src/er_commons/human_review_support/task04/config.py` | migrated | `src/er_commons/human_review_support/extraction_review/config.py` |
| `src/er_commons/human_review_support/task04/discovery.py` | migrated | `src/er_commons/human_review_support/extraction_review/discovery.py` |
| `src/er_commons/human_review_support/task04/failures.py` | migrated | `src/er_commons/human_review_support/extraction_review/failures.py` |
| `src/er_commons/human_review_support/task04/final_inputs.py` | migrated | `src/er_commons/human_review_support/extraction_review/final_inputs.py` |
| `src/er_commons/human_review_support/task04/final_pass.py` | migrated | `src/er_commons/human_review_support/extraction_review/final_pass.py` |
| `src/er_commons/human_review_support/task04/final_pass_record.py` | migrated | `src/er_commons/human_review_support/extraction_review/final_pass_record.py` |
| `src/er_commons/human_review_support/task04/final_policy.py` | migrated | `src/er_commons/human_review_support/extraction_review/final_policy.py` |
| `src/er_commons/human_review_support/task04/final_review.py` | migrated | `src/er_commons/human_review_support/extraction_review/final_review.py` |
| `src/er_commons/human_review_support/task04/finding_anchors.py` | migrated | `src/er_commons/human_review_support/extraction_review/finding_anchors.py` |
| `src/er_commons/human_review_support/task04/finding_transaction.py` | migrated | `src/er_commons/human_review_support/extraction_review/finding_transaction.py` |
| `src/er_commons/human_review_support/task04/findings.py` | migrated | `src/er_commons/human_review_support/extraction_review/findings.py` |
| `src/er_commons/human_review_support/task04/gate_d.py` | migrated | `src/er_commons/human_review_support/extraction_review/gate_d.py` |
| `src/er_commons/human_review_support/task04/geometry.py` | migrated | `src/er_commons/human_review_support/extraction_review/geometry.py` |
| `src/er_commons/human_review_support/task04/json_io.py` | migrated | `src/er_commons/human_review_support/extraction_review/json_io.py` |
| `src/er_commons/human_review_support/task04/models.py` | migrated | `src/er_commons/human_review_support/extraction_review/models.py` |
| `src/er_commons/human_review_support/task04/page_selection.py` | migrated | `src/er_commons/human_review_support/extraction_review/page_selection.py` |
| `src/er_commons/human_review_support/task04/presentation.py` | migrated | `src/er_commons/human_review_support/extraction_review/presentation.py` |
| `src/er_commons/human_review_support/task04/records.py` | migrated | `src/er_commons/human_review_support/extraction_review/records.py` |
| `src/er_commons/human_review_support/task04/register_models.py` | migrated | `src/er_commons/human_review_support/extraction_review/register_models.py` |
| `src/er_commons/human_review_support/task04/register_policy.py` | migrated | `src/er_commons/human_review_support/extraction_review/register_policy.py` |
| `src/er_commons/human_review_support/task04/rendering.py` | migrated | `src/er_commons/human_review_support/extraction_review/rendering.py` |
| `src/er_commons/human_review_support/task04/retained_evidence.py` | migrated | `src/er_commons/human_review_support/extraction_review/retained_evidence.py` |
| `src/er_commons/human_review_support/task04/scope_policy.py` | migrated | `src/er_commons/human_review_support/extraction_review/scope_policy.py` |
| `src/er_commons/human_review_support/task04/selection.py` | migrated | `src/er_commons/human_review_support/extraction_review/selection.py` |
| `src/er_commons/human_review_support/task04/table_parser.py` | migrated | `src/er_commons/human_review_support/extraction_review/table_parser.py` |
| `src/er_commons/human_review_support/task04/toc_census.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_census.py` |
| `src/er_commons/human_review_support/task04/toc_census_support.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_census_support.py` |
| `src/er_commons/human_review_support/task04/toc_decisions.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_decisions.py` |
| `src/er_commons/human_review_support/task04/toc_models.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_models.py` |
| `src/er_commons/human_review_support/task04/toc_page_shapes.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_page_shapes.py` |
| `src/er_commons/human_review_support/task04/toc_raw_scan.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_raw_scan.py` |
| `src/er_commons/human_review_support/task04/toc_review_selection.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_review_selection.py` |
| `src/er_commons/human_review_support/task04/toc_table_filters.py` | migrated | `src/er_commons/human_review_support/extraction_review/toc_table_filters.py` |
| `src/er_commons/human_review_support/task04/verification.py` | migrated | `src/er_commons/human_review_support/extraction_review/verification.py` |
| `src/er_commons/human_review_support/task04/warning_evidence.py` | migrated | `src/er_commons/human_review_support/extraction_review/warning_evidence.py` |
| `src/er_commons/human_review_support/task04/warning_policy.py` | migrated | `src/er_commons/human_review_support/extraction_review/warning_policy.py` |
| `src/er_commons/navigation_overlay/task04d_reconciliation.py` | migrated | `src/er_commons/navigation_overlay/linking_reconciliation.py` |
| `src/er_commons/response_inventory/task05d_policy.py` | migrated | `src/er_commons/response_inventory/complete_source_policy.py` |
| `src/er_commons/task03g2f_replay/__init__.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/audit.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/config.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/errors.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/inventory.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/io.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/sources.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/table_audit.py` | retired | `none; preserve sealed references and historical validators` |
| `src/er_commons/task03g2f_replay/workflow.py` | retired | `none; preserve sealed references and historical validators` |

Two isolated pilot test files were retired with their island. Maintained replay
ownership assertions moved to `test_document_publication_maintainability.py`;
Gate 1 exact-closure, historical recipe, deep-corruption, source-free publication,
and invalidation tests remain. Tests still named for historical tasks retain
fixture provenance; their imports and active command assertions use current owners.

New small owners implement the explicit requests and shared boundaries, not new
production policy: config generation request/validation; document input preparation
and collection runner; review request; navigation input/CLI; relink preparation,
regression request and deliberate seal audit. Historical review assets are byte-identical.
The legacy `compatibility_v1.py` readers remain; only the unused bundle adapter was removed.
