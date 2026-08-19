# Configuration

Project settings are typed models loaded from the required local `.env`.
Portable source and document/collection configuration stays in Git; the external
data root is resolved only through `ER_COMMONS_DATA_ROOT`.

The maintained production orchestration accepts an explicit v2 document specification
through `er-commons documents publish` and a v2 collection specification through
`er-commons collections assemble-handoff`. A document-process selection names content
parsing, heading-evidence parsing, record mapping, hierarchy inference, document
structure, and document-reference linking for that source. There are no implicit
Appendix P defaults in the public commands.
The checked-in Appendix P document run spec is
`brisbane_baylands_2025_deir_appendix_p_document_v1.json`.

Task 03G.1's immutable `brisbane_baylands_2025_deir_task03g1_smoke_v1.json`
remains historical evidence. The maintained
`brisbane_baylands_2025_deir_task03g1_parser_smoke_v2.json` is its
responsibility-named diagnostic successor. It freezes 342 spread-sampled pages across all
35 model-corpus sources and can be passed only to the separate
`python -m er_commons.parser_smoke` diagnostic entrypoint. It does not
configure or relax either production orchestration command. Its ordered
`owned_code_paths` inventory binds every runtime module in the human-owned
diagnostic package so a wrapper refactor changes `smokev1-` without changing
the production `exv1-` identity.

The checked-in Brisbane configs remain explicit source-scoped policy and
identity inputs. They are not public completed-task replay commands. Historical
review, repeat-build, comparison, and first-600 configurations were removed in
Task 03F.4 after their active invariants moved to maintained validators or to
candidate-neutral review/comparison utilities.

Task 03G.2 is closed. Its accepted fresh six-owner plans cover `deir_main`,
`deir_appendix_d`, and `deir_appendix_p`, with an exact document run spec and
scope run spec. Their historical stem is
`brisbane_baylands_2025_deir_task03g2_<source>_<owner>_v1.json`; the two run
specs are `brisbane_baylands_2025_deir_task03g2_document_v1.json` and
`brisbane_baylands_2025_deir_task03g2_scope_v1.json`.

Those files are immutable checksum-bound evidence and must not be regenerated or
rewritten. Every hierarchy disposition is `machine_validation`; no Task 03E.2d
bounded-acceptance path is permitted.

The historical preparation used these commands to generate and close the files:

```bash
uv run python scripts/generate_task03g2_configs.py
uv run python scripts/generate_task03g2_identity.py
```

Do not rerun them against the accepted v1 paths. They remain maintained only as
bounded historical tooling and compatibility evidence.

`scripts/prepare_task03g2.py` likewise remains a bounded, source-PDF-free
compatibility check for the accepted configuration set; it is not a current
production entry point.

Task 03G.3 adds strict v2 document and collection contracts for future execution.
Their keys use responsibility names and do not accept the v1 `document_owners`,
producer, semantic, or corpus-process keys. The Task 03G.2 configs remain checked-in
checksum inputs and are read only through explicit v1 compatibility loaders. Do not
use aliases to mix the two versions.

The checked examples are fixtures, not production recipes:

- `benchmarks/er_bench/fixtures/document_publication/v2/document_run_spec.json`
- `benchmarks/er_bench/fixtures/collection_processing/v2/collection_run_spec.json`

Their schemas live beside the corresponding package name under
`benchmarks/er_bench/schemas/`. Run `make validate-collection-contract` for the
collection fixture gate. Task 03H owns the first real all-source v2 specifications:

- `brisbane_baylands_2025_deir_task03h_document_v2.json` selects the exact ordered
  35-source production scope;
- `brisbane_baylands_2025_deir_task03h_collection_v2.json` selects the matching
  collection handoff policy;
- `brisbane_baylands_2025_deir_task03h_source_family_catalog_v1.json` contains the
  exact full-scope source identities and reviewed conservative aliases; and
- `task03h_templates/` contains the six current source-neutral owner templates; and
- `task03h/<source_id>/` contains the 210 generated source-specialized process configs.

Generate or byte-check the 210 templates, catalog, specs, and native-v2 identity with:

```bash
uv run python scripts/generate_task03h_configs.py
uv run python scripts/generate_task03h_configs.py --check
```

The generator reads only the sealed manifest and release completion metadata; it does
not read source PDFs or model files. The checked fixture examples remain non-runnable.
