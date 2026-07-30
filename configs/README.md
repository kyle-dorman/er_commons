# Configuration

Project settings are typed Pydantic models loaded from the required local `.env`.
`brisbane_baylands_2025_deir_sources_v1.json` is the reviewed Task 02 source
specification. A validated Pydantic contract checks its stable IDs, source
roles, landing-page membership, exclusions, filenames, and uniqueness before
any acquisition write.

Keep portable configuration in Git and resolve the external data root only
through `ER_COMMONS_DATA_ROOT` in `.env`. See `docs/architecture.md`.

`brisbane_baylands_2025_deir_task03d_appendix_p_v1.json` freezes the
document-scoped, non-release Appendix P canonicalization scope and the exact
accepted Task 03C.1 producer run. Run it with `make run-canonical-document`.

`brisbane_baylands_2025_deir_task03e_hierarchy_evaluation_v1.json` freezes the
Task 03E hierarchy options, review pages, controls, comparison surface,
thresholds, and stop rules before any live conversion. Its candidate producer
configuration is
`brisbane_baylands_2025_deir_task03e_appendix_p_v1.json`.
