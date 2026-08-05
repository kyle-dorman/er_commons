# Configuration

Project settings are typed models loaded from the required local `.env`.
Portable source and extraction-owner configuration stays in Git; the external
data root is resolved only through `ER_COMMONS_DATA_ROOT`.

The maintained production orchestration accepts an explicit Task 03F run spec
through `er-commons extraction run-document` or `run-scope`. A document-owner
selection names the current complete-document, hierarchy-producer, canonical,
hierarchy-correction, semantic, and cross-reference configs for that source.
There are no implicit Appendix P defaults in the public extraction commands.
The checked-in Appendix P document run spec is
`brisbane_baylands_2025_deir_appendix_p_document_v1.json`.

Task 03G.1's `brisbane_baylands_2025_deir_task03g1_smoke_v1.json` is a
separate diagnostic contract. It freezes 342 spread-sampled pages across all
35 model-corpus sources and can be passed only to the separate
`python -m er_commons.smoke_extraction` diagnostic entrypoint. It does not
configure or relax either production orchestration command. Its ordered
`owned_code_paths` inventory binds every runtime module in the human-owned
diagnostic package so a wrapper refactor changes `smokev1-` without changing
the production `exv1-` identity.

The checked-in Brisbane configs remain explicit source-scoped policy and
identity inputs. They are not public completed-task replay commands. Historical
review, repeat-build, comparison, and first-600 configurations were removed in
Task 03F.4 after their active invariants moved to maintained validators or to
candidate-neutral review/comparison utilities.

Task 03G.2 is active for no-PDF preparation. It will add one fresh six-owner
plan for each of `deir_main`, `deir_appendix_d`, and `deir_appendix_p`, plus an
exact document run spec and scope run spec. Use the stem
`brisbane_baylands_2025_deir_task03g2_<source>_<owner>_v1.json`; the two run
specs are `brisbane_baylands_2025_deir_task03g2_document_v1.json` and
`brisbane_baylands_2025_deir_task03g2_scope_v1.json`.

Do not create those files by copying historical Appendix P IDs. The first four
owner plans bind static reviewed policy and newly predicted producer IDs.
Semantic and cross-reference lineage can be completed only from the exact IDs,
completion records, and inventories of newly published Task 03G.2 upstream
candidates. The fresh-lineage schema and offline tests must land before these
configs are added. Every hierarchy disposition is `machine_validation`; no
Task 03E.2d bounded-acceptance path is permitted. PDF execution remains behind
a separate user approval after a production-shaped no-PDF preflight.

Regenerate the reviewed static files and then close their checksums into the
three-source non-executed identity with:

```bash
uv run python scripts/generate_task03g2_configs.py
uv run python scripts/generate_task03g2_identity.py
```

The identity generator preserves the accepted Task 03G.1a recipe at its
historical path before replacing the canonical current recipe. A second run of
the two commands is byte-stable and keeps the document spec bound to the
generated pilot identity.

Stage the exact checked-in three-source catalog and write the no-PDF freshness
report with `uv run python scripts/prepare_task03g2.py`. This reads the sealed
manifest and task-owned artifact namespaces, but it does not open, checksum, or
convert a source PDF. Producer identities are derived later by the approved
execution preflight because they bind verified source and model bytes.
