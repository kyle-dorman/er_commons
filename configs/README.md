# Configuration

Project settings are typed Pydantic models loaded from the required local `.env`.
This directory will hold small, versioned workflow configuration files once a
numbered task defines a CEQA source contract or benchmark run. Follow the
`kelp_aef` pattern when that happens: validated Pydantic contracts around a
simple human-reviewable file format, rather than untyped dictionaries.

Keep portable configuration in Git and resolve the external data root only
through `ER_COMMONS_DATA_ROOT` in `.env`. See `docs/architecture.md`.
