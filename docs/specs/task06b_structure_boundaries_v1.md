# Task 06B structure and mapping inventory correction v1

This pre-edit scope supplement authorizes only existing inventory-owner edits:
`document_records/document_structure/code_inventory.py`,
`document_records/record_mapping/materialize.py`, and
`hierarchy_inference/code_inventory.py`. The acceptance matrix explicitly excludes
CLI help from structure identity. The latter two currently include the root
CLI, and the former two discover future modules via globs. Replace those globs
with the frozen lists below and remove only the CLI dependency. Retain existing
cross-owner dependencies, config/schema/policy inputs and historical records.
No execution algorithm, preserved recipe or artifact is changed.

Structure additionally binds actual table ownership/layout/no-table helpers and
the hierarchy terminal-seal verification chain invoked by its handoff reader.
The validation owner is included because candidate_records calls its publication
tail validator; unrelated hierarchy inference algorithms are not executed by
that reader. Schema bytes are bound through the existing explicit schema inputs.

## Ordered structure module paths

- `src/er_commons/document_records/document_structure/__init__.py`
- `src/er_commons/document_records/document_structure/aliases.py`
- `src/er_commons/document_records/document_structure/baseline.py`
- `src/er_commons/document_records/document_structure/bridge.py`
- `src/er_commons/document_records/document_structure/bundle.py`
- `src/er_commons/document_records/document_structure/code_inventory.py`
- `src/er_commons/document_records/document_structure/comparison.py`
- `src/er_commons/document_records/document_structure/config.py`
- `src/er_commons/document_records/document_structure/constants.py`
- `src/er_commons/document_records/document_structure/construction.py`
- `src/er_commons/document_records/document_structure/errors.py`
- `src/er_commons/document_records/document_structure/handoff.py`
- `src/er_commons/document_records/document_structure/identity.py`
- `src/er_commons/document_records/document_structure/inputs.py`
- `src/er_commons/document_records/document_structure/lifecycle.py`
- `src/er_commons/document_records/document_structure/normalization.py`
- `src/er_commons/document_records/document_structure/page_labels.py`
- `src/er_commons/document_records/document_structure/parser_evidence.py`
- `src/er_commons/document_records/document_structure/policies/__init__.py`
- `src/er_commons/document_records/document_structure/policies/aliases.py`
- `src/er_commons/document_records/document_structure/policies/bridge.py`
- `src/er_commons/document_records/document_structure/policies/control.py`
- `src/er_commons/document_records/document_structure/policies/correspondence.py`
- `src/er_commons/document_records/document_structure/policies/page_labels.py`
- `src/er_commons/document_records/document_structure/policies/sections.py`
- `src/er_commons/document_records/document_structure/producer_alignment.py`
- `src/er_commons/document_records/document_structure/publication.py`
- `src/er_commons/document_records/document_structure/replacement_evidence.py`
- `src/er_commons/document_records/document_structure/runtime.py`
- `src/er_commons/document_records/document_structure/sealing.py`
- `src/er_commons/document_records/document_structure/sections.py`
- `src/er_commons/document_records/document_structure/support.py`
- `src/er_commons/document_records/document_structure/validation.py`
- `src/er_commons/document_records/document_structure/workflow.py`

## Additional structure cross-owner paths

- `src/er_commons/document_records/record_mapping/layout.py`
- `src/er_commons/document_records/record_mapping/no_table_handoff.py`
- `src/er_commons/document_records/record_mapping/table_text_ownership.py`
- `src/er_commons/hierarchy_inference/bounded_acceptance.py`
- `src/er_commons/hierarchy_inference/candidate_records.py`
- `src/er_commons/hierarchy_inference/candidate_storage.py`
- `src/er_commons/hierarchy_inference/candidate_verification.py`
- `src/er_commons/hierarchy_inference/bundle.py`
- `src/er_commons/hierarchy_inference/checks.py`
- `src/er_commons/hierarchy_inference/config.py`
- `src/er_commons/hierarchy_inference/constants.py`
- `src/er_commons/hierarchy_inference/digests.py`
- `src/er_commons/hierarchy_inference/progress.py`
- `src/er_commons/hierarchy_inference/publication.py`
- `src/er_commons/hierarchy_inference/publication_authorization.py`
- `src/er_commons/hierarchy_inference/record_schema.py`
- `src/er_commons/hierarchy_inference/validation.py`

## Ordered mapping module paths

- `src/er_commons/document_records/record_mapping/__init__.py`
- `src/er_commons/document_records/record_mapping/assets.py`
- `src/er_commons/document_records/record_mapping/bundle.py`
- `src/er_commons/document_records/record_mapping/candidate.py`
- `src/er_commons/document_records/record_mapping/candidate_identity.py`
- `src/er_commons/document_records/record_mapping/config.py`
- `src/er_commons/document_records/record_mapping/constants.py`
- `src/er_commons/document_records/record_mapping/content_records.py`
- `src/er_commons/document_records/record_mapping/context.py`
- `src/er_commons/document_records/record_mapping/context_assembly.py`
- `src/er_commons/document_records/record_mapping/context_preparation.py`
- `src/er_commons/document_records/record_mapping/context_types.py`
- `src/er_commons/document_records/record_mapping/errors.py`
- `src/er_commons/document_records/record_mapping/geometry.py`
- `src/er_commons/document_records/record_mapping/identifiers.py`
- `src/er_commons/document_records/record_mapping/identity.py`
- `src/er_commons/document_records/record_mapping/inputs.py`
- `src/er_commons/document_records/record_mapping/layout.py`
- `src/er_commons/document_records/record_mapping/materialize.py`
- `src/er_commons/document_records/record_mapping/no_table_handoff.py`
- `src/er_commons/document_records/record_mapping/policies/__init__.py`
- `src/er_commons/document_records/record_mapping/policies/bundle.py`
- `src/er_commons/document_records/record_mapping/policies/content.py`
- `src/er_commons/document_records/record_mapping/policies/lineage.py`
- `src/er_commons/document_records/record_mapping/provenance.py`
- `src/er_commons/document_records/record_mapping/publication.py`
- `src/er_commons/document_records/record_mapping/record_sets.py`
- `src/er_commons/document_records/record_mapping/support_records.py`
- `src/er_commons/document_records/record_mapping/table_artifacts.py`
- `src/er_commons/document_records/record_mapping/table_cleanup.py`
- `src/er_commons/document_records/record_mapping/table_families.py`
- `src/er_commons/document_records/record_mapping/table_projection.py`
- `src/er_commons/document_records/record_mapping/table_records.py`
- `src/er_commons/document_records/record_mapping/table_regions.py`
- `src/er_commons/document_records/record_mapping/table_text_ownership.py`
- `src/er_commons/document_records/record_mapping/tables.py`
- `src/er_commons/document_records/record_mapping/traversal.py`
- `src/er_commons/document_records/record_mapping/validation.py`
