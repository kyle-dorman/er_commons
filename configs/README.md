# Configuration

Project settings are typed Pydantic models loaded from the required local `.env`.
`brisbane_baylands_2025_deir_sources_v1.json` is the reviewed Task 02 source
specification. A validated Pydantic contract checks its stable IDs, source
roles, landing-page membership, exclusions, filenames, and uniqueness before
any acquisition write.

Keep portable configuration in Git and resolve the external data root only
through `ER_COMMONS_DATA_ROOT` in `.env`. See `docs/architecture.md`.
