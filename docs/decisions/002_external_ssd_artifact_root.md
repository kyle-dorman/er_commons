# Decision 002: External SSD Artifact Root for the Local MVP

Status: accepted 2026-07-24.

## Decision

Use `/Volumes/x10pro/er_commons` as the canonical
`ER_COMMONS_DATA_ROOT` for the local MVP. Keep repository source and small
tracked contracts in Git, while raw documents, canonical extractions, page
renders, indexes, local model artifacts, and benchmark runs remain under this
external root.

The root remains explicit in the local, untracked `.env`; the application has
no built-in fallback. The checked-in `.env.example` records the expected path
for this workspace, and another machine must deliberately configure its own
available root.

## Why

The previous root, `/Users/kyledorman/data/er_commons`, was empty, but the
internal drive had little remaining capacity before source acquisition began.
Sprint 2 will retain full source PDFs, structured conversion output, extracted
images, and requested review-cache derivatives. Task 03B later made full-page
renders reproducible cache entries rather than mandatory extraction artifacts;
that lifecycle refinement does not change the external-root decision. The
mounted external SSD has substantially more available space and keeps those
artifacts off the constrained internal disk.

The MVP will run locally. Remote A40 compute and periodic cloud synchronization
are deferred; adopting either later requires a bounded task that preserves the
same provenance, restartability, and canonical-artifact contracts.

## Consequences

- The external SSD must be mounted at `/Volumes/x10pro` before data commands
  run.
- `make bootstrap` creates only the documented entry-point directories.
- A missing volume must fail visibly rather than redirecting work to an
  internal default.
- The next Sprint 2 task remains source freezing; this decision does not
  acquire or transform corpus data.

## Supersedes / excludes

- Supersedes `/Users/kyledorman/data/er_commons` as this workspace's canonical
  artifact root.
- Does not define a remote scratch layout, backup provider, or synchronization
  schedule.
