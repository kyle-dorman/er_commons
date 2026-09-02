# Configuration

Project settings are typed models loaded from the required local `.env`.
Portable source and document/collection configuration stays in Git; the
external data root is resolved only through `ER_COMMONS_DATA_ROOT`.

The maintained production orchestration accepts an explicit v2 document
specification through `er-commons documents publish` and a v2 collection
specification through `er-commons collections assemble-handoff`. A document
selection names content parsing, heading-evidence parsing, record mapping,
hierarchy inference, document structure, and document-reference linking for
that source. Public commands have no implicit Appendix P defaults.

## Current Task 03J inputs

Task 03J used the generated v4 configuration set for the ordered 35-source
run:

- `brisbane_baylands_2025_deir_task03h_document_v4.json` selects the document
  policies and source order;
- `brisbane_baylands_2025_deir_task03h_collection_v4.json` selects the
  collection handoff policy;
- `brisbane_baylands_2025_deir_task03h_v4_source_family_catalog_v1.json`
  contains the full-scope source identities and aliases;
- `task03h_templates/` contains the source-neutral owner templates; and
- `task03h/v4/<source_id>/` contains the 210 generated source-specialized
  process configurations.

The `task03h` stem is the implementation's retained lineage name for the
Task 03J v4 run. These files are the exact checked-in inputs for the completed
candidate, not an instruction to start another extraction. Older v1-v3
configuration sets remain historical evidence.

Verify the generated files without changing them with:

```bash
uv run python scripts/generate_task03h_configs.py --check
```

The generator reads the sealed source manifest and release completion metadata;
it does not read source PDFs or model files. Regeneration, a new production
identity, or a new source/model run requires a separately scoped task.

## Historical and fixture configurations

The checked examples are fixtures, not production recipes:

- `benchmarks/er_bench/fixtures/document_publication/v2/document_run_spec.json`
- `benchmarks/er_bench/fixtures/collection_processing/v2/collection_run_spec.json`

Their schemas live under `benchmarks/er_bench/schemas/`. Run
`make validate-collection-contract` for the collection fixture gate.

The Task 03G.1 smoke configuration remains a separate diagnostic endpoint and
cannot configure or relax production document or collection commands. Task
03G.2 configurations and their compatibility tools are immutable historical
evidence; do not regenerate or mix their v1/v1.1 vocabulary with the current
native-v2 production contracts.
