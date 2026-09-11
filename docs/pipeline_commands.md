# Maintained pipeline commands

Task 06B separates current execution requests from immutable historical evidence.
Run commands from the repository with `uv run python scripts/<name>.py` (or the
package CLI shown below). Paths in a request are resolved by its typed loader;
read that loader's schema before preparing a new request. `--help` performs no
source or model work. Commands that execute or render require the active task's
applicable authorization; their presence here is not production authorization.

| Operation | Interface and required selection | Owner / contract |
| --- | --- | --- |
| Qualify a selected source | `er-commons sources validate-qualification-spec`, `sources acquire-qualified`, `sources reuse-qualified`, each with `--spec PATH` | [Task 06C qualification contract](specs/task06c_source_qualification_v1.md); validation/reuse are source-free, acquisition requires separate authorization and never starts conversion |
| Supervise a background command | `python -m er_commons.document_publication.background_execution --help` | Explicit command/attempt/output paths and finite limits; use within tmux for persistent execution; [06C preparation](specs/task06c_gate3_preparation.md) |
| Propose or check current configs | `generate_document_configs.py --generation-spec PATH [--check]` | `document_publication/config_generation`; [request schema](../benchmarks/er_bench/schemas/document_config_generation/v1/request.schema.json) |
| Qualify selected run inputs | `prepare_document_inputs.py --document-spec PATH --collection-spec PATH --output-root PATH` | `document_publication/input_preparation.py`; compact bounded manifest/recipe checks |
| Execute declared documents | `run_document_collection.py --document-spec PATH --source-id ID --progress-root PATH` (repeat IDs, or select `--all-sources`) | `document_publication/collection_runner.py`; serial, spec-bound progress; actual execution may open sources |
| Prepare relink contracts | `prepare_document_relink_specs.py --preparation-spec PATH` | `document_records/document_references/preparation_spec.py`; explicit accepted roots, old recipe, new paths, policies and v2/v3 schemas |
| Qualify caption-backed figures | `uv run python scripts/qualify_figure_caption_aliases.py --structured-root DIR --source-id ID --source-document-id ID --output-root DIR [--reuse-existing]` | [Figure-caption policy](specs/figure_caption_alias_v1.md); source-free selected-record qualification with a fresh no-clobber output, or exact current-identity verification when reuse is explicit |
| Prepare/materialize/reconcile reviewed navigation | `prepare_reviewed_navigation.py`, `materialize_reviewed_navigation.py`, `reconcile_reviewed_navigation.py`, each with `--input-spec PATH --output-root PATH` | `navigation_overlay/input_specs.py`; explicit extraction/review/scope/schema bindings |
| Publish one document / relink / assemble | `er-commons documents publish`, `documents relink`, `collections assemble-handoff` | Existing commands retain their explicit document/link/collection specs; use `--help` for selectors |
| Compact historical reuse | `read_accepted_conversion`, `read_accepted_producer`, `read_accepted_range`, prepared publication inputs | [Verification contract](specs/task06b_verification_boundaries_v1.md); recorded identities, seals, metadata and closure; no fresh payload equality claim |
| Inspect conversion metadata | `inspect_conversion_scaling.py --data-root PATH --run-relative-root PATH --source-id ID --output-root PATH --ledger` | `document_performance/conversion_scaling.py`; source/model-free ledger |
| Profile or deep audit conversion evidence | Same diagnostic command, explicitly select its profile, benchmark, or `--deep-audit-legacy-conversions` operation | `conversion_scaling.py`, `conversion_compatibility_audit.py`; these operations can read/hash large selected payloads and are separate from compact reuse |
| Audit no-page section rules | `audit_document_linking.py --entries PATH --document-publications-root PATH --linking-policy PATH --policy-schema PATH --operation no-page-sections` | `navigation_overlay/linking_reconciliation.py`; selected implemented rule scope only |
| Deep regression audit | `validate_document_relink_run.py --operation deep-regression-audit --validation-spec PATH --data-root PATH --link-spec PATH --navigation-root PATH --output PATH` | `navigation_overlay/relink_run_validation.py`; explicit populations/context, byte audit, in-memory relinking; no candidate publication |
| Prepare/build/publish review | `prepare_extraction_review.py`, `build_extraction_review_bundle.py`, `build_final_extraction_review.py`, `publish_extraction_review.py`, each with `--review-spec PATH --output-root PATH` | [Review runbook](task04_maintainer_runbook.md); historical profiles and rendering opt-in |
| Update reviewed findings | `record_review_finding.py`, `set_review_register_status.py` with explicit `--review-root` and finding/status arguments | Existing finding/register semantics retained |

`make finalize-response-relationship-candidate` requires
`RELATIONSHIP_REVIEW_ROOT` and `QUALITY_REPORT`. The review builder requires
`RELATIONSHIP_ROOT`, `SOURCE_RECORDS`, `QUALIFICATION`, `RENDER_ROOT`,
`REVIEW_TOOL_ROOT`, and `SERVED_ROOT`. No mutation target silently selects an
accepted review root.

Current run specs retain original per-source manifests. A replacement collection
uses explicit logical-to-physical membership; an F1 replacement or wrapper rename
does not make the other documents fresh conversion outputs. Original task-named
configs, schema literals, seals, identities, and human decisions remain historical
contracts. A historical reader does not require old implementation files to exist.

## Task 06F figure qualification

Select the sealed linked-candidate root that directly contains
`records/manifest.json` and the four canonical streams. The source ID and document
ID must match that manifest's extraction namespace; do not infer them from Task 05
mentions. A fresh review attempt uses a new output directory:

```bash
uv run python scripts/qualify_figure_caption_aliases.py \
  --structured-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_04d_relinked_v1/document_links/linked_candidates/deir_main/exv1-d1bbac8a4979836add501c88c3522b908aeefee66b95cf8cef07abda1c30d28c \
  --source-id deir_main \
  --source-document-id exv1-d1bbac8a4979836add501c88c3522b908aeefee66b95cf8cef07abda1c30d28c/document/deir_main \
  --output-root /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06f/qualification_v10
```

To verify and reuse that exact packet after publication, repeat the same command
with `--reuse-existing`. Reuse fails if the selected records, code, policy,
schemas, requested IDs, managed-file closure, or semantic reconstruction differ.
The command logs whether it published or reused the packet and its resolved path.
Neither form opens PDFs or images, hashes preserved PDF/image payloads, loads a
model, or runs Task 06G production replay.
