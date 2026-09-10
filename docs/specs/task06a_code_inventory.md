# Task 06A code migration and dependency inventory

Format: `task06a_code_inventory.v1`. Static source audit, 2026-09-10. This is a future 06B specification; no listed migration or execution has occurred. The Task 06A outcome owns acceptance and links the qualified external evidence. Paths below are repository-relative.

The inventory enumerates all 29 tracked script files and all 61 tracked task-named package files plus the mandatory v1 bundle adapter. Caller evidence uses exact repository paths and fully qualified module names (script filenames for top-level wrappers), never unqualified generic module basenames. Relative package imports are covered by the package migration checks below. Evidence is textual across tracked source, scripts, tests, configs, schemas/identity fixtures, Makefile, and docs/tasks. Counts are search hits by file, not exhaustive runtime call graphs. Dynamic/external callers cannot be disproved by absence of hits.

## Per-file migration

Every rename records new future execution provenance only. Preserve accepted generated configs, old code-inventory entries, old identity preimages, persisted schema/record names, and artifact directories verbatim. Do not create callable aliases absent a demonstrated supported external caller. All removal rows require the specific retirement checks below; they never authorize deleting accepted artifacts.

| Current path | Responsibility | Classification/action | Exact destination/interface owner | Caller and evidence references |
| --- | --- | --- | --- | --- |
| `scripts/audit_hierarchy_candidate.py` | Deep-audit one existing hierarchy candidate without running hierarchy or a PDF. | maintained; retain | `scripts/audit_hierarchy_candidate.py` | tests: 1 (`tests/test_hierarchy_candidate_audit_script.py`); docs/history: 1 (`tasks/sprint2/03h1_profile_and_repair_full_document_scaling.md`) |
| `scripts/audit_task04d_linking.py` | Audit the implemented Task 04D no-page-section rules without publishing. | maintained; rename/refactor | `scripts/audit_document_linking.py` | docs/history: 1 (`tasks/sprint2/04d_relink_frozen_extraction.md`) |
| `scripts/build_task03j_final_review.py` | Build the Task 03J final-pass Gate C review package. | maintained; rename/refactor | `scripts/build_final_extraction_review.py` | docs/history: 1 (`docs/task04_maintainer_runbook.md`) |
| `scripts/build_task04_review_bundle.py` | Build one deterministic, checksummed first-pass Task 04 review bundle. | maintained; rename/refactor | `scripts/build_extraction_review_bundle.py` | tests: 1 (`tests/test_task04_maintainability.py`); docs/history: 2 (`docs/task04_maintainer_runbook.md`, `tasks/sprint2/04_review_extraction_and_freeze_release.md`) |
| `scripts/generate_task03g2_configs.py` | Generate the reviewed, source-specialized Task 03G.2 config set. | one-off; remove after Gate 1 | `none; preserved historical recipe` | docs/history: 1 (`tasks/sprint2/03g3_gate_a_inventory.md`) |
| `scripts/generate_task03g2_identity.py` | Refresh the exact three-source Task 03G.2 non-executed identity recipe. | one-off; remove after Gate 1 | `none; preserved historical recipe` | docs/history: 1 (`tasks/sprint2/03g3_gate_a_inventory.md`) |
| `scripts/generate_task03h_configs.py` | CLI facade for deterministic Task 03H production-spec generation. | maintained; rename/refactor | `scripts/generate_document_configs.py` | tests: 1 (`tests/test_task03h_human_ownership.py`); configs/identities: 1 (`configs/README.md`); docs/history: 1 (`tasks/sprint2/03h2_build_restartable_chunked_docling_conversion.md`) |
| `scripts/inspect_task03h_scaling.py` | Write the source-free Task 03H.1 Gate 1 scaling ledger. | maintained; rename/refactor | `scripts/inspect_conversion_scaling.py` | docs/history: 2 (`tasks/sprint2/03h1_profile_and_repair_full_document_scaling.md`, `tasks/sprint2/03h3_defer_reading_order_until_table_evidence.md`) |
| `scripts/materialize_task04c_gate_b.py` | Publish the source-free Task 04C Gate B semantic navigation view. | maintained; rename/refactor | `scripts/materialize_reviewed_navigation.py` | runtime: 1 (`src/er_commons/navigation_overlay/materialization.py`); tests: 1 (`tests/test_navigation_overlay_gate_b.py`) |
| `scripts/prepare_task03g2.py` | Stage and audit Task 03G.2 inputs without reading source PDFs. | one-off; remove after Gate 1 | `none; preserved historical recipe` | docs/history: 2 (`tasks/sprint2/03g3_gate_a_inventory.md`, `tasks/sprint2/06a_freeze_recovery_and_cleanup_plan.md`) |
| `scripts/prepare_task03h.py` | Stage and audit Task 03H inputs without reading source PDFs or model files. | maintained; rename/refactor | `scripts/prepare_document_inputs.py` | runtime: 1 (`scripts/task03h_generation/production_identity.py`); tests: 1 (`tests/test_task03h_configs.py`); configs/identities: 3 (`benchmarks/er_bench/fixtures/document_publication/v2/task03h_production_identity.json`, `benchmarks/er_bench/fixtures/document_publication/v3/task03h_production_identity.json`); docs/history: 1 (`tasks/sprint2/03h_run_full_canonical_extraction.md`) |
| `scripts/prepare_task03j_v4.py` | Prepare the fresh Task 03J v4 namespace without reading PDFs or models. | maintained; rename/refactor | `scripts/prepare_document_inputs.py` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `scripts/prepare_task04a_review.py` | Prepare Task 04A Gate A from Task 03J machine artifacts only. | maintained; rename/refactor | `scripts/prepare_extraction_review.py` | docs/history: 1 (`docs/task04_maintainer_runbook.md`) |
| `scripts/prepare_task04c_gate_a.py` | Publish the source-free Task 04C Gate A navigation-overlay plan. | maintained; rename/refactor | `scripts/prepare_reviewed_navigation.py` | runtime: 1 (`src/er_commons/navigation_overlay/preparation.py`); tests: 1 (`tests/test_navigation_overlay_gate_a.py`); configs/identities: 1 (`benchmarks/er_bench/schemas/navigation_overlay/v1/gate_a_specification.schema.json`) |
| `scripts/prepare_task04d_gate_c_specs.py` | Prepare Task 04D's sealed production identity and 35-source link run. | maintained; rename/refactor | `scripts/prepare_document_relink_specs.py` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `scripts/publish_task04a_gate_d.py` | Publish Task 04A Gate D from accepted compact c17 review records. | maintained; rename/refactor | `scripts/publish_extraction_review.py` | docs/history: 1 (`docs/task04_maintainer_runbook.md`) |
| `scripts/reconcile_task04c_gate_c.py` | Publish the source-free Task 04C TOC text and navigation-link view. | maintained; rename/refactor | `scripts/reconcile_reviewed_navigation.py` | runtime: 1 (`src/er_commons/navigation_overlay/reconciliation.py`) |
| `scripts/record_task04_finding.py` | Record one validated Task 04 finding and refresh the Task 03I handoff. | maintained; rename/refactor | `scripts/record_review_finding.py` | runtime: 1 (`src/er_commons/human_review_support/task04/FINDINGS.md`); tests: 1 (`tests/test_task04_maintainability.py`); docs/history: 1 (`docs/task04_maintainer_runbook.md`) |
| `scripts/run_chunked_conversion.py` | Run or resume one explicit restartable chunk-conversion plan. | maintained; retain | `scripts/run_chunked_conversion.py` | runtime: 2 (`scripts/task03h_generation/production_identity.py`, `src/er_commons/chunked_conversion/runtime/execution.py`); configs/identities: 3 (`benchmarks/er_bench/fixtures/document_publication/v2/task03h_production_identity.json`, `benchmarks/er_bench/fixtures/document_publication/v3/task03h_production_identity.json`) |
| `scripts/run_task03g2f_downstream_replay.py` | CLI for the bounded Task 03G.2f downstream replay. | one-off; remove after Gate 1 | `none; preserved historical recipe` | tests: 1 (`tests/test_task03g2f_replay.py`); docs/history: 2 (`tasks/sprint2/03g3_gate_a_inventory.md`, `tasks/sprint2/06a_freeze_recovery_and_cleanup_plan.md`) |
| `scripts/run_task03j_v4.py` | Run the Task 03J v4 source queue serially with durable progress evidence. | maintained; rename/refactor | `scripts/run_document_collection.py` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `scripts/set_task04_finding_register_status.py` | Approve or close a validated Task 04 finding register. | maintained; rename/refactor | `scripts/set_review_register_status.py` | runtime: 1 (`src/er_commons/human_review_support/task04/FINDINGS.md`); tests: 1 (`tests/test_task04_closure_blockers.py`); docs/history: 1 (`docs/task04_maintainer_runbook.md`) |
| `scripts/task03h_generation/__init__.py` | Deterministic Task 03H production-spec generation owners. | maintained; rename | `src/er_commons/document_publication/config_generation/__init__.py` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `scripts/task03h_generation/process_templates.py` | Specialize six source-neutral current Task 03H process templates. | maintained; rename | `src/er_commons/document_publication/config_generation/process_templates.py` | tests: 1 (`tests/test_task03h_human_ownership.py`) |
| `scripts/task03h_generation/production_identity.py` | Close the Task 03H production identity over exact artifacts and owned code. | maintained; rename | `src/er_commons/document_publication/config_generation/production_identity.py` | tests: 1 (`tests/test_task03h_human_ownership.py`) |
| `scripts/task03h_generation/shared.py` | Shared paths and deterministic JSON/file operations for Task 03H generation. | maintained; rename | `src/er_commons/document_publication/config_generation/shared.py` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `scripts/task03h_generation/specifications.py` | Generate the Task 03H source catalog and collection/document run specs. | maintained; rename | `src/er_commons/document_publication/config_generation/specifications.py` | tests: 1 (`tests/test_task03h_human_ownership.py`) |
| `scripts/task03h_generation/workflow.py` | Orchestrate deterministic Task 03H generation without source PDF/model reads. | maintained; rename | `src/er_commons/document_publication/config_generation/workflow.py` | tests: 1 (`tests/test_task03h_human_ownership.py`) |
| `scripts/validate_task04d_gate_c.py` | Run the source-free Task 04D Gate C population and regression controls. | maintained; rename/refactor | `scripts/validate_document_relink_run.py` | docs/history: 1 (`tasks/sprint2/04d_relink_frozen_extraction.md`) |
| `src/er_commons/collection_processing/compatibility_v1_bundle.py` | Project v2 workflow evidence into the immutable v1.1 validation contract. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | configs/identities: 4 (`benchmarks/er_bench/fixtures/document_publication/v2/task03h_production_identity.json`, `benchmarks/er_bench/fixtures/document_publication/v3/task03h_production_identity.json`) |
| `src/er_commons/document_performance/task03h_gate1.py` | Build a source-free ledger of Task 03H K2 scaling evidence. | maintained diagnostic; rename/refactor | `src/er_commons/document_performance/conversion_scaling.py` | runtime: 1 (`scripts/inspect_task03h_scaling.py`); tests: 1 (`tests/test_task03h_gate1_scaling.py`) |
| `src/er_commons/document_performance/task03h_gateb.py` | Audit and benchmark the Task 03H.1 post-Docling MVP schemas. | maintained diagnostic; rename/refactor | `src/er_commons/document_performance/conversion_compatibility_audit.py` | runtime: 1 (`scripts/inspect_task03h_scaling.py`); tests: 1 (`tests/test_task03h_gateb_scaling.py`) |
| `src/er_commons/document_publication/task03g2_preparation.py` | Stage and audit Task 03G.2 inputs without touching source PDF bytes. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 1 (`scripts/prepare_task03g2.py`); tests: 1 (`tests/test_task03g2_preparation.py`); configs/identities: 3 (`benchmarks/er_bench/fixtures/document_publication/v2/task03h_production_identity.json`, `benchmarks/er_bench/fixtures/document_publication/v3/task03h_production_identity.json`) |
| `src/er_commons/document_publication/task03h_preparation.py` | Stage and audit Task 03H inputs without reading source PDF or model bytes. | maintained; rename/refactor | `src/er_commons/document_publication/input_preparation.py` | runtime: 1 (`scripts/prepare_task03h.py`); tests: 2 (`tests/test_task03h_configs.py`, `tests/test_task03h_human_ownership.py`); configs/identities: 3 (`benchmarks/er_bench/fixtures/document_publication/v2/task03h_production_identity.json`, `benchmarks/er_bench/fixtures/document_publication/v3/task03h_production_identity.json`) |
| `src/er_commons/human_review_support/task04/FINDINGS.md` | Review presentation/documentation asset; retain behavior and relative asset loading. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/FINDINGS.md` | docs/history: 1 (`docs/task04_maintainer_runbook.md`) |
| `src/er_commons/human_review_support/task04/__init__.py` | Public seams for the maintainable Task 04 review-bundle application. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/__init__.py` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `src/er_commons/human_review_support/task04/anchor_models.py` | Immutable typed records used by the Task 04 finding-anchor workflow. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/anchor_models.py` | runtime: 1 (`src/er_commons/human_review_support/task04/finding_anchors.py`) |
| `src/er_commons/human_review_support/task04/application.py` | Importable application seam for one complete Task 04 review-bundle build. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/application.py` | runtime: 3 (`src/er_commons/human_review_support/task04/__init__.py`, `src/er_commons/human_review_support/task04/final_pass.py`) |
| `src/er_commons/human_review_support/task04/assets/__init__.py` | Readable static assets for the generated Task 04 review workspace. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/assets/__init__.py` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `src/er_commons/human_review_support/task04/assets/review.css` | Review presentation/documentation asset; retain behavior and relative asset loading. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/assets/review.css` | `presentation.py:25,59,69` loads all three assets through `_ASSET_PACKAGE` using importlib.resources; preserve package-data loading and application review tests. |
| `src/er_commons/human_review_support/task04/assets/review.html` | Review presentation/documentation asset; retain behavior and relative asset loading. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/assets/review.html` | `presentation.py:25,59,69` loads all three assets through `_ASSET_PACKAGE` using importlib.resources; preserve package-data loading and application review tests. |
| `src/er_commons/human_review_support/task04/assets/review.js` | Review presentation/documentation asset; retain behavior and relative asset loading. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/assets/review.js` | `presentation.py:25,59,69` loads all three assets through `_ASSET_PACKAGE` using importlib.resources; preserve package-data loading and application review tests. |
| `src/er_commons/human_review_support/task04/canonical_evidence.py` | Read canonical page, text, table, and family evidence for Task 04. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/canonical_evidence.py` | runtime: 6 (`src/er_commons/human_review_support/task04/application.py`, `src/er_commons/human_review_support/task04/final_pass.py`) |
| `src/er_commons/human_review_support/task04/config.py` | Review policy constants for the completed Task 04 first pass. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/config.py` | runtime: 4 (`src/er_commons/human_review_support/task04/application.py`, `src/er_commons/human_review_support/task04/findings.py`); tests: 1 (`tests/test_task04_verification.py`) |
| `src/er_commons/human_review_support/task04/discovery.py` | Resolve Task 03H review inputs without interpreting canonical content. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/discovery.py` | runtime: 5 (`src/er_commons/human_review_support/task04/application.py`, `src/er_commons/human_review_support/task04/final_inputs.py`); tests: 2 (`tests/test_task04_closure_blockers.py`, `tests/test_task04_verification.py`) |
| `src/er_commons/human_review_support/task04/failures.py` | Interpret retained Task 03H attempt histories for the failure queue. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/failures.py` | runtime: 1 (`src/er_commons/human_review_support/task04/selection.py`) |
| `src/er_commons/human_review_support/task04/final_inputs.py` | Resolve Task 03J review inputs without rehashing large artifacts. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/final_inputs.py` | runtime: 1 (`src/er_commons/human_review_support/task04/final_review.py`) |
| `src/er_commons/human_review_support/task04/final_pass.py` | Source-free Gate A preparation for the Task 03J final review pass. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/final_pass.py` | runtime: 2 (`src/er_commons/human_review_support/task04/__init__.py`, `src/er_commons/human_review_support/task04/final_inputs.py`); tests: 1 (`tests/test_task04a_final_pass.py`) |
| `src/er_commons/human_review_support/task04/final_pass_record.py` | Record assembly for the source-free Task 04A Gate A preparation. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/final_pass_record.py` | runtime: 1 (`src/er_commons/human_review_support/task04/final_pass.py`) |
| `src/er_commons/human_review_support/task04/final_policy.py` | Frozen policy values for the Task 03J final review pass. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/final_policy.py` | runtime: 1 (`src/er_commons/human_review_support/task04/final_pass.py`) |
| `src/er_commons/human_review_support/task04/final_review.py` | Build the corrected Task 03J final-pass reviewer after Gate C approval. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/final_review.py` | runtime: 2 (`scripts/build_task03j_final_review.py`, `src/er_commons/human_review_support/task04/__init__.py`) |
| `src/er_commons/human_review_support/task04/finding_anchors.py` | Typed evidence anchors derived from immutable Task 04 selection records. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/finding_anchors.py` | runtime: 2 (`src/er_commons/human_review_support/task04/__init__.py`, `src/er_commons/human_review_support/task04/findings.py`); tests: 1 (`tests/test_task04_closure_blockers.py`) |
| `src/er_commons/human_review_support/task04/finding_transaction.py` | Recoverable staged publication for Task 04 finding-derived records. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/finding_transaction.py` | runtime: 1 (`src/er_commons/human_review_support/task04/findings.py`); tests: 2 (`tests/test_task04_closure_blockers.py`, `tests/test_task04_findings.py`) |
| `src/er_commons/human_review_support/task04/findings.py` | Typed, human-facing updates to Task 04 findings and the Task 03I handoff. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/findings.py` | runtime: 1 (`src/er_commons/human_review_support/task04/__init__.py`) |
| `src/er_commons/human_review_support/task04/gate_d.py` | Publish the compact Task 04A Gate D release decision. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/gate_d.py` | runtime: 2 (`scripts/publish_task04a_gate_d.py`, `src/er_commons/human_review_support/task04/__init__.py`); tests: 1 (`tests/test_task04a_gate_d.py`) |
| `src/er_commons/human_review_support/task04/geometry.py` | Page-coordinate transforms used only by the Task 04 review presentation. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/geometry.py` | runtime: 2 (`src/er_commons/human_review_support/task04/canonical_evidence.py`, `src/er_commons/human_review_support/task04/final_pass.py`); tests: 1 (`tests/test_build_task04_review_bundle.py`) |
| `src/er_commons/human_review_support/task04/json_io.py` | Path-rich JSON readers at the Task 04 untyped artifact boundary. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/json_io.py` | runtime: 18 (`src/er_commons/human_review_support/task04/canonical_evidence.py`, `src/er_commons/human_review_support/task04/discovery.py`); tests: 3 (`tests/test_build_task04_review_bundle.py`, `tests/test_task04_closure_blockers.py`) |
| `src/er_commons/human_review_support/task04/models.py` | Typed internal contracts for the Task 04 review-bundle application. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/models.py` | runtime: 29 (`src/er_commons/human_review_support/task04/__init__.py`, `src/er_commons/human_review_support/task04/anchor_models.py`); tests: 6 (`tests/task04_test_support.py`, `tests/test_build_task04_review_bundle.py`) |
| `src/er_commons/human_review_support/task04/page_selection.py` | Deterministic page and table selection policies for Task 04. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/page_selection.py` | runtime: 1 (`src/er_commons/human_review_support/task04/selection.py`); tests: 1 (`tests/test_task04_policy.py`) |
| `src/er_commons/human_review_support/task04/presentation.py` | Static HTML presenters for the read-only Task 04 review workspace. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/presentation.py` | runtime: 2 (`src/er_commons/human_review_support/task04/application.py`, `src/er_commons/human_review_support/task04/final_review.py`); tests: 1 (`tests/test_build_task04_review_bundle.py`) |
| `src/er_commons/human_review_support/task04/records.py` | Identity, schema validation, record writing, and atomic Task 04 publication. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/records.py` | runtime: 7 (`scripts/prepare_task04a_review.py`, `src/er_commons/human_review_support/task04/application.py`); tests: 3 (`tests/test_task04_closure_blockers.py`, `tests/test_task04_review_schemas.py`) |
| `src/er_commons/human_review_support/task04/register_models.py` | Typed outputs and lifecycle states for Task 04 register publication. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/register_models.py` | runtime: 2 (`src/er_commons/human_review_support/task04/findings.py`, `src/er_commons/human_review_support/task04/register_policy.py`) |
| `src/er_commons/human_review_support/task04/register_policy.py` | One-way lifecycle invariants for the Task 04 finding register. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/register_policy.py` | runtime: 1 (`src/er_commons/human_review_support/task04/findings.py`) |
| `src/er_commons/human_review_support/task04/rendering.py` | Injectable PDF page rendering boundary for Task 04 disposable assets. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/rendering.py` | runtime: 3 (`src/er_commons/human_review_support/task04/application.py`, `src/er_commons/human_review_support/task04/final_pass.py`) |
| `src/er_commons/human_review_support/task04/retained_evidence.py` | Compact exact-object evidence retained independently of rendered Task 04 pages. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/retained_evidence.py` | runtime: 1 (`src/er_commons/human_review_support/task04/records.py`) |
| `src/er_commons/human_review_support/task04/scope_policy.py` | Typed production and fixture boundaries for Task 04 input discovery. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/scope_policy.py` | runtime: 3 (`src/er_commons/human_review_support/task04/__init__.py`, `src/er_commons/human_review_support/task04/discovery.py`); tests: 2 (`tests/task04_test_support.py`, `tests/test_task04_verification.py`) |
| `src/er_commons/human_review_support/task04/selection.py` | Assemble the four deterministic Task 04 review queues. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/selection.py` | runtime: 3 (`src/er_commons/human_review_support/task04/application.py`, `src/er_commons/human_review_support/task04/final_review.py`) |
| `src/er_commons/human_review_support/task04/table_parser.py` | Interpret retained table-parser attempt evidence for human review. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/table_parser.py` | runtime: 1 (`src/er_commons/human_review_support/task04/selection.py`) |
| `src/er_commons/human_review_support/task04/toc_census.py` | Build a source-free machine-detectable TOC candidate census. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_census.py` | runtime: 2 (`src/er_commons/human_review_support/task04/final_pass.py`, `src/er_commons/human_review_support/task04/toc_raw_scan.py`); tests: 1 (`tests/test_task04a_final_pass.py`) |
| `src/er_commons/human_review_support/task04/toc_census_support.py` | Small parsing helpers shared by the source-free TOC census. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_census_support.py` | runtime: 3 (`src/er_commons/human_review_support/task04/final_pass.py`, `src/er_commons/human_review_support/task04/toc_census.py`) |
| `src/er_commons/human_review_support/task04/toc_decisions.py` | Load and preserve stable TOC decisions across review regenerations. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_decisions.py` | runtime: 2 (`src/er_commons/human_review_support/task04/final_review.py`, `src/er_commons/human_review_support/task04/gate_d.py`); tests: 1 (`tests/test_task04a_final_pass.py`) |
| `src/er_commons/human_review_support/task04/toc_models.py` | Typed domain objects for Task 04A TOC census and review policy. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_models.py` | runtime: 6 (`src/er_commons/human_review_support/task04/final_review.py`, `src/er_commons/human_review_support/task04/gate_d.py`); tests: 1 (`tests/test_task04a_final_pass.py`) |
| `src/er_commons/human_review_support/task04/toc_page_shapes.py` | Classify page shapes used to bound positive-TOC review suppression. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_page_shapes.py` | runtime: 2 (`src/er_commons/human_review_support/task04/final_review.py`, `src/er_commons/human_review_support/task04/toc_review_selection.py`); tests: 1 (`tests/test_task04a_final_pass.py`) |
| `src/er_commons/human_review_support/task04/toc_raw_scan.py` | Optional raw Docling machine-artifact scan for the TOC census. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_raw_scan.py` | runtime: 2 (`src/er_commons/human_review_support/task04/final_pass.py`, `src/er_commons/human_review_support/task04/toc_census.py`) |
| `src/er_commons/human_review_support/task04/toc_review_selection.py` | Select a bounded false-negative TOC review sample from the Gate B census. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_review_selection.py` | runtime: 1 (`src/er_commons/human_review_support/task04/final_review.py`); tests: 1 (`tests/test_task04a_final_pass.py`) |
| `src/er_commons/human_review_support/task04/toc_table_filters.py` | Table-shape filters for the Task 04A possible-TOC review queue. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/toc_table_filters.py` | runtime: 1 (`src/er_commons/human_review_support/task04/final_review.py`); tests: 1 (`tests/test_task04a_final_pass.py`) |
| `src/er_commons/human_review_support/task04/verification.py` | Injectable source and document-publication verification adapters for Task 04. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/verification.py` | runtime: 2 (`src/er_commons/human_review_support/task04/application.py`, `src/er_commons/human_review_support/task04/discovery.py`); tests: 2 (`tests/task04_test_support.py`, `tests/test_task04_verification.py`) |
| `src/er_commons/human_review_support/task04/warning_evidence.py` | Discover warning occurrences and resolve honest page context for Task 04. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/warning_evidence.py` | runtime: 1 (`src/er_commons/human_review_support/task04/selection.py`) |
| `src/er_commons/human_review_support/task04/warning_policy.py` | Warning normalization and class-based sampling policy for Task 04. | maintained/historical reader; rename | `src/er_commons/human_review_support/extraction_review/warning_policy.py` | runtime: 2 (`src/er_commons/human_review_support/task04/presentation.py`, `src/er_commons/human_review_support/task04/selection.py`); tests: 1 (`tests/test_task04_policy.py`) |
| `src/er_commons/navigation_overlay/task04d_reconciliation.py` | Source-free Task 04D reconciliation over accepted TOC text and body aliases. | maintained; rename | `src/er_commons/navigation_overlay/linking_reconciliation.py` | runtime: 1 (`scripts/audit_task04d_linking.py`); tests: 1 (`tests/test_navigation_overlay_link_resolution.py`) |
| `src/er_commons/response_inventory/task05d_policy.py` | Shared immutable scope and warning policy for Task 05D. | historical policy support; rename | `src/er_commons/response_inventory/complete_source_policy.py` | runtime: 6 (`src/er_commons/response_inventory/acceptance.py`, `src/er_commons/response_inventory/contract.py`) |
| `src/er_commons/task03g2f_replay/__init__.py` | Human-owned Task 03G.2f replay orchestration and evidence auditing. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | No qualified direct reference found; relative imports/package exports require the package migration checks below. |
| `src/er_commons/task03g2f_replay/audit.py` | Candidate-neutral evidence audit for the retained Task 03G.2f pilot. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 1 (`src/er_commons/task03g2f_replay/workflow.py`); tests: 1 (`tests/test_task03g2f_replay.py`) |
| `src/er_commons/task03g2f_replay/config.py` | Reviewable paths and source configuration for the bounded Task 03G.2f replay. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 4 (`scripts/run_task03g2f_downstream_replay.py`, `src/er_commons/task03g2f_replay/__init__.py`); tests: 1 (`tests/test_task03g2f_replay.py`) |
| `src/er_commons/task03g2f_replay/errors.py` | Stable, context-rich failures for the Task 03G.2f replay. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 5 (`src/er_commons/task03g2f_replay/audit.py`, `src/er_commons/task03g2f_replay/inventory.py`); tests: 1 (`tests/test_task03g2f_replay.py`) |
| `src/er_commons/task03g2f_replay/inventory.py` | Read-only inventory seals used to prove a downstream-only replay. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 1 (`src/er_commons/task03g2f_replay/workflow.py`); tests: 1 (`tests/test_task03g2f_replay.py`) |
| `src/er_commons/task03g2f_replay/io.py` | Small exact-byte helpers shared by replay orchestration and auditing. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 4 (`src/er_commons/task03g2f_replay/audit.py`, `src/er_commons/task03g2f_replay/sources.py`) |
| `src/er_commons/task03g2f_replay/sources.py` | Source-level preparation for the bounded downstream replay. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 1 (`src/er_commons/task03g2f_replay/workflow.py`) |
| `src/er_commons/task03g2f_replay/table_audit.py` | Candidate-neutral assertions for the reviewed table-link change window. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 1 (`src/er_commons/task03g2f_replay/audit.py`); tests: 1 (`tests/test_task03g2f_replay.py`) |
| `src/er_commons/task03g2f_replay/workflow.py` | Short application shell for the bounded Task 03G.2f replay. | one-off/unused adapter; remove after Gate 1 | `none; preserve sealed references and historical validators` | runtime: 2 (`scripts/run_task03g2f_downstream_replay.py`, `src/er_commons/task03g2f_replay/__init__.py`) |

## Migration conditions and verification

The 06B Gate 1 implementation must precede every removal. Historical recipe
validation must validate the recorded canonical preimage and compact seals
without reopening its recorded source-code paths. A new writer hashes its new
explicit behavior inventory and references accepted upstream seals; it must not
claim the old product was produced by the current recipe.

- `prepare_task03g2.py`, `task03g2_preparation.py`, and both Task03G2 generators
  are fixed historical v1/pilot preparation. Current configuration documentation
  explicitly prohibits regeneration of that lineage. Their direct test owner is
  `tests/test_task03g2_preparation.py`; preserve historical record acceptance in
  reader tests, then retire only generator-specific coverage. Old generated
  fixtures and configs remain untouched.
- `run_task03g2f_downstream_replay.py` and all nine `task03g2f_replay` files form
  an isolated pilot replay/audit island. Imports are internal, the script, and
  `tests/test_task03g2f_replay.py`; production replay already belongs to
  `document_publication/downstream_replay.py`. Retire the island and its execution
  tests together after transferring any still-needed negative seal/inventory
  coverage to maintained replay tests. Do not port its fixed pilot source map.
- `compatibility_v1_bundle.as_v1_validation_view` has no runtime caller found;
  the file remains in four historical production inventory fixtures and the
  maintainability allowlist. Remove the executable and the obsolete allowlist
  entry only after old-reader tests accept those unchanged historical fixtures.
  Keep `collection_processing/compatibility_v1.py`,
  `document_publication/compatibility_v1.py`,
  `extraction_reporting/compatibility_v1.py`, and
  `corpus_extraction_contract_v1_1/`: they are distinct compatibility support,
  not proven one-offs by this audit.
- `scripts/task03h_generation/` is maintained Task03J generation. Move its six
  files together into the named package owner; retain internal one-way imports.
  Tests `test_task03h_configs.py`, `test_task03h_human_ownership.py`, and
  `test_chunked_conversion_production_policy.py` explicitly import generator
  files (including dynamic `importlib` calls). Update those tests to the new
  package and distinguish legacy fixture validation from fresh generation.
- Merge the two maintained input-preparation wrappers at the stated destination;
  preserve v4 resource/identity checks in `input_preparation.py`, with explicit
  input paths. Eliminate the implicit v3 versus v4 choice. Readiness records
  named `task03h_preparation_readiness.json` remain readable: review `discovery.py`
  and `tests/task04_test_support.py` depend on this historical artifact name.
- Move the 45-file `human_review_support/task04/` package as one maintained review
  owner, preserving its package assets and all historical schema literals. All
  relative and absolute imports, package asset lookups, wrappers, and
  `tests/test_task04*.py` plus `tests/task04_test_support.py` migrate together.
  `final_review.build_task03j_final_review` becomes
  `build_final_extraction_review`; preparation/publication entry functions use
  responsibility names. The review interface still consumes explicit sealed
  extraction/review bindings; renaming is not a review disposition.
- Conversion diagnostics remain a maintained optional capability, not production
  dependencies. Their historical report schemas stay readable. Moving their
  two owners does not authorize running their expensive benchmark, deep-audit,
  or source-consuming branches in 06B.

For each row Gate 2 records: old/new path, exact imports updated, changed tests,
new command smoke result, preserved historical recipe acceptance, and semantic
comparison result. Repeat `git ls-files scripts` and task-name searches after
migration. Any remaining old path must be labeled historical record/schema,
historical-input reader, or documented external caller. Search absence alone is
insufficient deletion proof. A newly discovered supported caller blocks that
removal until migrated or explicitly retained; it does not authorize a broad
compatibility shim.

## Explicit interfaces and operational symbols

These are proposed 06B interfaces, not commands available today. Existing
`er-commons documents publish`, `documents relink`, `collections assemble-handoff`,
`collections validate-handoff`, and `scripts/run_chunked_conversion.py` retain
their public purpose. The renamed scripts stay thin package callers.

| Future script/interface | Required explicit inputs / validation |
| --- | --- |
| `generate_document_configs.py` | `--generation-spec PATH [--check]`; spec names templates, ordered source bindings, output config directory, identity output, model descriptor and policies. No release/version environment default. `--check` compares proposed current outputs, never re-derives accepted historical recipes. |
| `prepare_document_inputs.py` | `--document-spec PATH --collection-spec PATH --output-root PATH`; derive catalog/identity references from specs, bounded metadata-only input qualification. |
| `run_document_collection.py` | `--document-spec PATH --source-id ID` repeatable or explicit declared full selection, `--progress-root PATH`; resume terminal sources, no implicit v4 config or global import-time settings. Source/conversion access requires later task authorization. |
| `prepare_document_relink_specs.py` | `--preparation-spec PATH`; explicit old handoff/identity, replacement recipe, per-source accepted input bindings, reviewed navigation, output namespace and policies. |
| `prepare_reviewed_navigation.py`, `materialize_reviewed_navigation.py`, `reconcile_reviewed_navigation.py` | `--input-spec PATH --output-root PATH`; explicit accepted extraction/review/navigation references; preserve per-source checks and existing source-free boundary. |
| `prepare_extraction_review.py`, `build_extraction_review_bundle.py`, `build_final_extraction_review.py`, `publish_extraction_review.py` | `--review-spec PATH --output-root PATH`; explicit pass identity, old evidence references, correspondence and scope. Rendering is a separately requested operation. Historical pass names remain supported by record readers. |
| `record_review_finding.py`, `set_review_register_status.py` | Preserve existing finding/register arguments with explicit target review root; migrate imports only. |
| `audit_document_linking.py`, `validate_document_relink_run.py`, `inspect_conversion_scaling.py` | Explicit run/spec/root and operation selection; compact accepted-input check is separate from deliberate deep audit/benchmark. No fixed source/root fallback. |

| Current operational symbols | Future treatment / owner |
| --- | --- |
| `task03h_generation/shared.py`: `RUN_VERSION`, `ER_COMMONS_TASK03H_RUN_VERSION`, `TASK_TEMPLATE_ROOT`, `TASK_ROOT`, `TASK_CONFIG_ROOT`, `MANIFEST_RELATIVE`, `MANIFEST_SHA256`, `COMPLETION_SHA256`, `CATALOG_*`, `DOCUMENT_SPEC_*`, `COLLECTION_SPEC_*`, `IDENTITY_*`, `TARGET_POLICY`, `RESOLUTION_POLICY` | `config_generation` validated generation-spec fields; rename task-root locals to `run_root`/`template_root`/`config_root`. Preserve old values only in original corpus config/recipe. `CHUNKED_PAGE_THRESHOLD` remains explicit policy with the current value 300 preserved in historical recipes; it is not a new source-independent algorithm decision. |
| Preparation modules: `DOCUMENT_SPEC`, `COLLECTION_SPEC`, `CATALOG`, `TASK_ROOT`, `SCHEMAS`; v4 wrapper `DATA_ROOT`, `IDENTITY`, `CATALOG_RELATIVE` | Read from explicit preparation request, load settings inside main, keep schema ownership declared. Do not carry fixed corpus selection behind the new filename. |
| `run_task03j_v4.py`: `SPEC`, `RUN_ROOT`, `LOG_ROOT`, `PROGRESS`, `LOGGER` | Request-derived paths and responsibility-based logger; historical `task03j_progress.jsonl` stays unchanged. Fatal-pattern behavior requires synthetic equivalence tests. |
| `navigation_overlay/preparation.py`: `SCOPE_ID`, `TASK04A_REVIEW_ID`, `TASK04A_GATE_A_ID`, `EXPECTED_SOURCE_COUNT`, `_TASK03J_RELATIVE`, `_REVIEW_RELATIVE`, `_OUTPUT_RELATIVE`; `task03j_root` request field | Explicit bound extraction/review/scope fields; `extraction_root` in future API. Old JSON keys `task03j`/`task04a` remain historical-reader keys, not blindly rewritten. `materialization.py` and `reconciliation.py` fixed-root constants receive the same treatment. |
| `prepare_task04d_gate_c_specs.py`: `BASE_IDENTITY`, `BASE_DOCUMENT_SPEC`, `BASE_COLLECTION_SPEC`, `REPLAY_AUTHORIZATION`, `PRODUCTION_IDENTITY`, `DOCUMENT_SPEC`, `LINK_SPEC`, `COLLECTION_SPEC`, `SOURCE_CATALOG` | Explicit preparation-spec references; old checked configs remain immutable. |
| `document_performance/task03h_gate1.py`: `TASK_ROOT`, `SOURCE_ID`; related `task03h_gateb.py` imports | Explicit diagnostic input selection/output root; rename exported task-era functions by operation. Persisted task03h schema strings retained. |
| `human_review_support/task04/config.py`: `SCHEMA_VERSION`, `REVIEW_PASS`; final-pass and retained-evidence task-specific fields | Historical reader support preserved; new requests choose pass and seals explicitly. Do not rewrite historical schema string `er_commons.task04_review.v1`. |
| `response_inventory/task05d_policy.py`: `TASK05D_RANGE`, `TASK05D_PAGE_COUNT`, `TASK05D_ALLOWED_WARNING_CODES` | Rename module to `complete_source_policy.py`; symbols to `ACCEPTED_COMPLETE_RANGE`, `ACCEPTED_COMPLETE_PAGE_COUNT`, `ACCEPTED_WARNING_CODES` with documentation that 1–744 is an accepted historical corpus recipe, not a generic future source default. All actual import consumers migrate together. |
| `response_inventory/pilot_policy.py`: `TASK05C_PILOT_RANGES`, `TASK05C_RIGHT_CENSORED_RANGE`, `TASK05C_FIXED_REVIEW_PAGES` | Rename symbols to `ACCEPTED_PILOT_RANGES`, `ACCEPTED_RIGHT_CENSORED_RANGE`, `ACCEPTED_PILOT_REVIEW_PAGES`; retain exact historical policy values. |
| Makefile `TASK05E_REVIEW_ROOT` | `RELATIONSHIP_REVIEW_ROOT` required caller input for mutation; existing accepted root stays documented corpus evidence. Other hardcoded source/render/qualification roots in review target become explicit variables. |
| `task04_status`, `task04_freezes`, `task04d_handoff_id`, `er_commons.task05e.*`, `er_commons.task05f.*`, `task05f_qualified_exact_rules_v5`, smoke task03g1 schema/policy names | Retain as historical persisted contract values. New Task05G bindings may extend records under its own contract; 06B must not silently rename them or alter matching. |

## Stage dependency and invalidation specification

Read modes: **M** checks contained paths, sizes, closure, recorded identity and
bounded compact seals under the packet's hash ceilings; **T** reads specifically
selected payload records to transform them later, never a checksum sweep;
**N** creates and seals new output; **D** is a deliberate separately authorized
byte audit. Metadata checking cannot detect same-size unread corruption.
All new stage recipes bind their actual behavior code, policies, schema and
runtime inputs; old recipes remain recorded historical entities.

| Stage / current owner | Input seal and current recipe | Actual dependencies and proposed boundary | Reused evidence / invalidated output / consumers | Read and validation |
| --- | --- | --- | --- | --- |
| Acquisition / `source_release` | Original release manifest and completion; acquisition source specification | Network retrieval/title qualification affects new source records. Unchanged accepted bytes remain original entities regardless of downloader edits. New Final F1 gets its own explicit substitution record. | Original release for 34 slots; new F1 acquisition and all F1 descendants only. Conversion consumes source-specific seal. | M old; N streamed single hash for later authorized F1; reject source-ID/edition ambiguity. |
| Conversion plan / `chunked_conversion/runtime/planning.py`, `range_contract.py` | Source, converter/package/model/adapter/planner/merge bindings in `RangePlan.inputs`, plan identity | Current `verify_chunk_inputs` invokes fresh preparation and compares plan to current runtime. Split completed-plan consumption from incomplete-range resume; resume still demands compatible conversion behavior. | Reuse all completed original plans/range coverage for unchanged sources; planner change affects future plan, never forces accepted ranges to execute. Range worker consumes explicit plan. | M old; synthetic changed-adapter incomplete resume must reject. |
| Range conversion / `runtime/inputs.py`, `docling_adapter.py`, `range_store.py`, `worker.py` | Plan plus page-evidence and range behavior identities | Bind adapter, source bytes, Docling options/packages/models, page contract, range bounds. CLI/wrapper/planner provenance is not automatically range behavior. | Accepted range receipts and payload references reused; changed source/model/adapter invalidates affected future range and aggregate. | M accepted; N only later source run; fail converter/model/PDF sentinels in 06B. |
| Aggregate conversion / `content_parsing/conversion_identity.py`, chunk aggregate owners | `dconv1` payload includes source, entire sealed release, models/packages, conversion code; `chunk1` additionally binds plan and coordinator code | Current conversion inventory includes all `source_release/**/*.py`; remove acquisition-wide behavior from future conversion inventory, retain exact adapter/shared helpers. Bind explicit original per-source seal even in mixed replacement collection. | All unchanged conversion seals stay usable after filename, CLI, acquisition or F1-manifest changes; actual conversion changes invalidate affected aggregate/descendants. | M accepted; compare recorded preimage without present-day path existence; D remains distinct. |
| Producer / `content_parsing/identity.py`, producer preparation/publication | `prv1`, exact conversion seal plus routing/table config/code | Routing/table behavior owns producer invalidation, not conversion. Keep table reconstruction/shared serialization dependencies explicit. | Conversion preserved; new producer only where actual policy changed, then heading/mapping consumers as needed. | M/T/N; perturb routing and assert conversion remains reusable. |
| Heading evidence / `heading_evidence_parsing` | Producer/conversion heading evidence and stage configuration/identity | Accepted body evidence remains source evidence; no chapter fallback fabricated into producer records. | Reuse old evidence; 06D/E derive structure from selected records. Changed heading policy invalidates heading descendants only. | M/T; compare stable keys/page provenance. |
| Hierarchy / `hierarchy_inference` | Heading stage + hierarchy policy/code/schema | Repeated-title decisions require topology/TOC correspondence; 06D owns new decision policy. | Conversion/producer retained; affected hierarchy, structure, aliases and descendants new; mapping stays reusable when its producer inputs are unchanged. | T/N; positive duplicates plus real-child/independent-heading controls. |
| Record mapping / `document_records/record_mapping` | Producer stage seal + mapping code/config (`record_mapping/config.py:42-43`) | Mapping and hierarchy are sibling inputs: no hierarchy binding exists in the mapping config. Preserve mapped raw blocks; derive chapter role/heading decisions in hierarchy/structure when possible. | Unchanged mapping reused; only changed mapping inputs/behavior invalidate mapping. Hierarchy changes separately invalidate structure and descendants. | M/T/N; stable content/key conservation and explicit new IDs. |
| Semantic sections / `document_structure` | Mapped records, heading/hierarchy/printed-page evidence, semantic v2 schema and code inventory | 06E adds recovered/fallback chapter provenance and extent; 06D topology decisions feed structure. Current structure code inventory globs its package and lists cross-owner helpers; freeze explicit future paths. | Original body text/figures retained; new sections/aliases only for approved affected sources; linking/index consumers updated. | T/N; extent/children coherence and next-unit boundary controls. |
| Target aliases / `document_structure`, `document_references` | Section/figure/table evidence, catalog, alias policy | `normalize_alias` is shared behavior. Figure captions independently qualify aliases in 06F; mentions never create targets. | Accepted canonical figure records reused; aliases, link products, target indexes invalidate when policy changes. | T/N; collision/destination controls; perturb shared normalizer across all consumers. |
| Reviewed navigation / `navigation_overlay`, `reviewed_navigation.py` | Accepted review/TOC freeze, completion/inventory, canonical correspondence | Presentation changes do not invalidate conversion. Reuse only proved page/content/destination evidence; load shared bundle once per prepared run. | Unchanged/equivalent review carried with explicit correspondence; changed structure destinations need 06H review. Links consume effective navigation. | M/T; per-source coverage retained; wrong F1 review never reused. |
| Document linking / `document_references/relink_publication.py` | `RelinkIdentityInputs`: structure completion/inventory, source document seals, policy/catalog/schema/code and optional reviewed navigation | New link identity binds exact accepted old inputs; old reader validates historical production identity without live code. Resolve shared review once; no underlying source preparation. | All upstream conversion/producer reused; changed targets/navigation/link policy creates linked document and publication descendants. | M/T/N; end-to-end no-source sentinels, spec-drift rejection. |
| Document publication / `document_publication` | Source identity, linked document seal, production/scope/candidate identity and managed inventory | `downstream_replay` currently calls `prepare_document_run` and deep `verify_candidate`; replace with explicit accepted-source path. New authoritative output still seals exact closure completion-last. | Old candidates retained; fresh descendants reference them. Avoid copies of unchanged sealed upstream trees. | M old; N new; D one observed inventory pass, never repeated hashing. |
| Collection accounting / `collection_processing` | Document completions, ordered source selection/scope recipe | Add explicit mixed accepted source-manifest membership; source slots remain exactly 35, F1 exception only. | Unaffected documents reused; new accounting/scope when composition changes. Index/resolution/handoff consume accounting. | M/N; reject duplicate/missing slot and mismatched source seal. |
| Collection target index / `collection_processing` | Accounting + document target/alias products + target policy | Changed section/figure/edition provenance changes target products; unchanged target evidence referenced. | New index after repaired documents, no source/producer work. Resolution consumes index. | M/T/N; full old/new target correspondence and deterministic order. |
| Collection resolution / `collection_processing` | Target-index seal, mention inputs, source catalog and resolution policy | Changed target candidates require cross-document resolution replay with fixed mention inputs. | Reuse extracted mentions; new links/diagnostics; handoff consumes resolution. | M/T/N; exact collision/nonlink controls, no response-source re-extraction. |
| Collection handoff / `collection_processing` | Accounting/index/resolution completions + schema/contract bundle | Fresh handoff binds coherent replacement components and substitution/correspondence records. | Original 04D handoff remains designated until 06H accepts replacement. | M/N; complete closure, terminal states and 35-slot reconciliation. |
| Task04 review correspondence / `human_review_support` | Original review dispositions, source/page/content/target references | 06H owns unchanged/remapped/changed/unproven classification, never source-ID-only reuse. | Reuse actual equivalent evidence; new decisions only changed/unproven evidence. Usability consumer binds replacement handoff. | M/T/N; ID-only changes do not force rereview. |
| Task05 source production / `response_inventory/full_workflow.py`, `workflow.py`, `run_spec.py` | Accepted 05D revision/acceptance, source/ranges/models + `owned_code_digest` | Current digest globs almost all response package, so reference/review edits invalidate source producer. Split source-producer inventory from relationship/reference/presentation inventories. | Accepted 05D source records retained; no Task06 replay. 05E/05F consumers still bound to original seals. | M; synthetic 05F/review edit leaves source-producer digest stable. |
| Task05 relationship / `relationship_baseline.py`, `relationship_candidate.py` | Accepted 05D source records + rules/review and accepted 05E pointer | Own relationship matching/record/serialization helpers; exclude unrelated 05F code. | Accepted 05E graph retained through 06; 05G changes bindings only when its contract requires. | M; own-rule perturbation invalidates relationship only. |
| Task05 references / `reference_baseline.py` | Accepted 05D/E, 04A usability, 04D handoff/index, 05F rules | Include cross-package `document_structure/normalization.py` (currently absent from response package glob) plus actual reference helpers. | 05F partial population retained; 05G consumes 06H replacement and replays affected references. | M now; T/N only 05G; shared normalization perturbation must invalidate references. |
| Task05 presentation / `review_tool.py`, static assets | Accepted records + review presentation inputs | Presentation digest is separate from source/relationship/reference production. | View regeneration alone changes presentation; accepted source records untouched. | M/T/N later; no producer identity churn. |

## Mandatory Gate 1 changes and finite scope

The concrete current defects are: `conversion_identity.conversion_code_paths`
adds the entire acquisition package and `build_conversion_identity` binds the
release-wide manifest; `verify_chunk_inputs` derives a live conversion before
reading accepted plans; `preflight._verify_production_contract` passes the current
project root to old production validation; `sources.resolve_manifest_source`
opens and hashes the source PDF; `storage.verify_candidate` hashes each managed
file then calls `artifact_inventory` to hash them again; and relink execution
loads reviewed navigation in both `_resolve_reviewed_navigation` and
`_load_reviewed_navigation`. Response `owned_code_paths` globs the response
package but omits the external shared normalizer used by `reference_baseline`.

Gate 1 edits are restricted to these identity/preparation/verification owners,
their maintained `conversion_seal`, `production_identity`, `downstream_replay`,
`relink_replay`, `reviewed_navigation` collaborators, and the minimum config/schema
models needed for explicit per-source accepted seals and verification mode.
No extraction, table, hierarchy, resolver, or caption semantics change here.
Gate 2 then applies the enumerated migrations and their direct imports/tests,
future code inventory paths, Make interfaces and current docs. Historical
fixtures are tested as sealed records, not rewritten to match the new checkout.

Mandatory synthetic tests: old recorded missing-code-path fixture accepted as
old evidence but not current execution; unchanged 34-source membership with a
new F1 manifest retains old conversion seals; completed ranges reusable while
incompatible incomplete resume rejects; CLI/review/acquisition-only edits do
not invalidate conversion; model/adapter/source perturbations do; routing
invalidates producer only; chapter policy invalidates structural descendants;
normalization affects all true consumers. Inject failures on PDF open/hash,
large-payload hash, model load and converter execution through both relinking
and downstream publication. Reject extra/missing paths, metadata/identity/spec
mismatch and incomplete seals. Deep-audit same-size corruption is tested only
on synthetic bytes. Record one shared review verification per prepared run.

Use the existing tests named in 06B plus the migration-specific test owners
above; finish future implementation with `make fix`, `make check` and independent
human-maintainability review. 06A itself executes none of these implementation
or production checks.

The live relink CLI flag is `--link-spec`, as defined by `src/er_commons/cli.py`.
Gate 2 corrects the historical `--run-spec` example in
`docs/specs/document_linking_v1.md` when publishing the supported command map.

The source-free repair inspection found Chapters 8/9 in canonical `page_header`
blocks on physical pages 1855/2015, with split number/title blocks. The minimum
06E owner is a derived heading-evidence/role decision in
`hierarchy_inference` or semantic structure, consuming the unchanged mapped blocks. Preserve
raw heading blocks and producer seals; do not merely add an alias to the first
child. Preserve record mapping unless its own inputs/behavior change. Rebuild heading/hierarchy descendants from accepted evidence where the
existing role mapping excludes these blocks. If recoverable chapter evidence
fails the structural controls, the explicit TOC/coherent-children fallback
remains available. 06D uses the same preserved-evidence decision boundary for
repeated-heading topology; neither repair invalidates conversion or producer.

## Gate 1 file boundary and inventory freeze

Before Gate 1 edits, freeze explicit leaf-path behavior lists in the existing
inventory owners. 06A fixes responsibilities and cross-owner dependencies;
06B derives the final ordered paths from actual imports before coding and tests
the perturbation matrix. It may not substitute package-wide globs or treat this
as permission to refactor every dependency. The Gate 1 implementation file set
is the following (all beneath `src/er_commons/`):

- `artifact_io.py` (bounded verification seams/shared canonical serialization,
  only if the existing owners cannot enforce limits without this small change);
- `document_parsing/content_parsing/conversion_identity.py`, `identity.py`,
  `conversion_seal.py`, `preparation.py`;
- `chunked_conversion/runtime/inputs.py`, `planning.py`;
- `document_publication/production_identity.py`, `preflight.py`, `sources.py`,
  `storage.py`, `downstream_replay.py`, `config.py`, `records.py`;
- `document_records/document_references/relink_publication.py`,
  `relink_replay.py`, `reviewed_navigation.py`, `relinking_config.py`;
- `collection_processing/config.py`, `preflight.py` (mixed source membership);
- `response_inventory/code_inventory.py`, `run_spec.py`, `workflow.py`,
  `full_workflow.py`, `reference_baseline.py` (inventory selection only);
- `cli.py` (thin named verification-mode dispatch only).

Schema input boundaries are existing
`benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json`,
`collection_processing/v2/collection_run_spec.schema.json`, and
`document_linking/v1/document_link_run.schema.json` under the same schema root.
Add the minimally versioned successor for an incompatible closed-object change;
do not rewrite historical schema meaning. Response schemas under
`response_inventory/v1/run_spec.schema.json`, `v2/run_spec.schema.json`,
`v3/relationship_run_spec.schema.json`, `v4/relationship_run_spec.schema.json`,
and `v5/reference_run_spec.schema.json` are preserved old-reader inputs. New
per-stage inventories need no historical record mutation. Any new adjacent
input-binding schema is limited to fields specified by the recovery plan.

Cross-package identity inputs that must not be missed include
`artifact_io.py` (`canonical_json_sha256`, `json_bytes`, `jsonl_bytes`, publication
serialization), `document_records/document_structure/normalization.py`
(`normalize_alias`), and the stage's existing record/schema identity builders
(e.g. `response_inventory/contract.py:build_record_id`). These are dependencies
to enumerate, not authorization to change their algorithms. Other unchanged
cross-owner paths already listed in the current conversion, hierarchy and
structure inventory owners remain audit inputs; omitting them requires an
actual dependency explanation. A newly necessary implementation file outside
this bounded set must be named and justified in the 06B pre-edit specification;
a material expansion returns to scope review instead of an open-ended
"collaborators" allowance.
