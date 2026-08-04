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
