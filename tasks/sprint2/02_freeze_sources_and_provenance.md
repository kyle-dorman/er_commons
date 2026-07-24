# Task 02: Freeze Brisbane Sources and Provenance

## Abstract

Create one immutable, reproducible source release for the Brisbane Draft-EIR
defense benchmark before document extraction begins. Inventory the authoritative
City of Brisbane source pages, acquire the complete 2025 Draft EIR main report
and every official appendix, retain the separately published chapter PDFs only
for recovery or QA, retain the separately published original comment
submissions as curator QA and provenance, and acquire Final EIR Volume 4 as the
canonical curator-only response source. Validate every file and write a
versioned manifest that preserves source role, URL, access time, checksum, byte
size, MIME and detected file type, and PDF page count.

This task freezes original bytes and acquisition provenance. It does not run
Docling, apply OCR, assess page usability, parse responses, or begin case
curation.

## Goal

Produce a complete, restartable, checksummed source snapshot from which Task 03
can build the canonical extraction without rediscovering source files or
guessing which documents belong to the model-facing corpus.

## Inputs

- `AGENTS.md`
- `docs/index.md`
- `docs/todo.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/documentation.md`
- `docs/sprints/sprint2_brisbane_draft_eir_defense.md`
- `benchmarks/er_bench/sprint1.md`
- `docs/decisions/001_brisbane_draft_eir_defense_benchmark.md`
- `docs/decisions/002_external_ssd_artifact_root.md`
- the mounted, configured `ER_COMMONS_DATA_ROOT`
- the authoritative City of Brisbane
  [2025 Draft EIR page](https://www.brisbaneca.gov/237/2025-Draft-EIR)
- the authoritative City of Brisbane
  [2025 DEIR Comments page](https://www.brisbaneca.gov/570/2025-DEIR-Comments)
- the authoritative City of Brisbane
  [2026 Final EIR page](https://www.brisbaneca.gov/774/2026-Final-EIR)

The 2025 Draft EIR page owns discovery of the original main report, official
appendices, and duplicate chapter files. The 2025 DEIR Comments page owns
discovery of the separately submitted original written-comment PDFs. The 2026
Final EIR page owns discovery of curator-only Volume 4. Do not substitute
revised Final-EIR volumes or appendices for an original Draft-EIR source or an
original comment submission.

## Outputs

- A versioned raw-source release below
  `/Volumes/x10pro/er_commons/datasets/ceqa/raw/brisbane_baylands/`, with the
  exact release directory and internal layout fixed in the implementation plan
  before any network write.
- Original downloaded bytes for:
  - the complete 2025 Draft EIR main-report PDF;
  - every appendix published on the official 2025 Draft EIR page;
  - every original written-comment submission published on the official 2025
    DEIR Comments page, retained only for curator QA and provenance;
  - Final EIR Volume 4 as the canonical curator-only response source; and
  - separately published Draft EIR chapter PDFs, retained only as recovery or
    QA duplicates.
- Saved snapshots of the authoritative landing pages used to discover the
  release, with their own access timestamps and checksums.
- An authoritative, machine-readable source manifest adjacent to the raw
  release. The manifest must contain:
  - manifest schema version and source-release version;
  - stable source ID, official title or link label, document type, and source
    role;
  - landing-page URL, linked file URL, and final resolved URL;
  - UTC access timestamp and any available HTTP response metadata useful for
    later verification;
  - local path relative to `ER_COMMONS_DATA_ROOT` and original filename;
  - SHA-256 checksum and byte size;
  - delivered MIME type, detected file type, and PDF-signature result;
  - PDF page count;
  - retrieval and validation status plus recoverable warnings; and
  - a reference to the applicable visible-terms note, with a per-file override
    only where the visible terms differ.
- A corpus-level acquisition record containing the command, configuration or
  source-specification version, software versions, aggregate file and byte
  counts, landing-page provenance, and warnings.
- A corpus-level visible-terms and access note. It records what was visible at
  acquisition time but makes no legal, licensing, reuse, or redistribution
  conclusion.
- Narrow package-backed acquisition and verification glue, a reviewable source
  specification or configuration, and fast tests. Track only code, small
  configs or schemas, and test fixtures in Git; keep PDFs, page snapshots, and
  generated acquisition records under `ER_COMMONS_DATA_ROOT`.

The manifest must use mechanically validated roles equivalent to:

- `model_corpus`: the complete main report and original official appendices;
- `curator_only_response_source`: Final EIR Volume 4;
- `curator_qa_original_submission`: original written-comment submission PDFs;
  and
- `recovery_qa_duplicate`: separately published Draft EIR chapter PDFs.

Chapter duplicates must never be counted as additional model-corpus documents.
Original comment submissions must never be exposed as model evidence. Volume 4
is the sole canonical source for response-aligned comment and response units;
the separate submissions preserve original-document provenance and provide a
QA comparison rather than replacing or extending the Volume 4 inventory.

## Research / learning checkpoint

Before selecting implementation dependencies, inspect the live authoritative
City pages, their visible terms or copyright notice, redirect behavior, and a
representative sample of the linked PDFs. Compare the Python standard library
with maintained open-source HTTP and PDF-validation packages for streaming
downloads, redirects, reliable page counts, and clear failure handling. Add a
runtime dependency only when it materially simplifies this bounded job.

Use primary guidance for the integrity design: Python's
[`hashlib`](https://docs.python.org/3/library/hashlib.html) documentation for
streaming SHA-256 and the
[BagIt specification, RFC 8493](https://www.rfc-editor.org/rfc/rfc8493.html),
as a checksum-manifest precedent. The task does not need to implement a full
BagIt package if a smaller project manifest preserves the required invariants.

Record the practical lessons in the task outcome:

- public availability establishes discovery and access provenance, not a reuse
  license;
- the linked URL, final resolved URL, and downloaded checksum describe
  different parts of source identity; and
- source roles prevent curator-only or duplicate material from leaking into the
  model corpus.

Use small bounded subagents, where available, for non-overlapping source-page
reconciliation, tooling research, and validation review. The lead agent must
verify and integrate their evidence.

## Plan / spec requirement

Write a brief implementation plan before any source download. It must freeze:

1. the source-release ID, external directory layout, manifest shape, and stable
   source-ID convention;
2. the source-role enum and the expected completeness checks for each role;
3. the source-specification or discovery boundary between reviewed expected
   sources and live landing-page links;
4. streaming, timeout, redirect, retry, temporary-file, and atomic-rename
   behavior;
5. no-clobber and versioning behavior for an existing file whose bytes do not
   match the frozen manifest;
6. the chosen HTTP and PDF-validation tools and why they fit better than the
   alternatives; and
7. the exact live command, verification-only command, and generated artifact
   locations.

The workflow must be restartable. A matching existing file is verified and
reused. A missing file may be retrieved. A checksum mismatch, changed official
source, incomplete main report, unreadable PDF, or unresolved inventory gap is
a stop condition requiring an explicit repair or new source-release decision;
the command must not silently overwrite, skip, or substitute content.

Reconcile the reviewed expected inventory against all three live landing pages
before acquisition. Preserve link labels and ordering as provenance, but
identify documents by stable semantic IDs rather than page position.
Investigate and record landing-page irregularities, including duplicated,
missing, mislabeled, or out-of-order multipart appendix links and repeated
submissions from the same commenter. In particular, the currently visible
Appendix K2 sequence must be checked rather than trusted by label alone. Do not
hardcode a final source count until the authoritative inventory has been
reconciled.

## Review pass

Review the completed implementation and artifacts through these lenses:

- **Source completeness and role isolation:** every intended original source is
  represented once in the correct role, duplicates are explicit, and excluded
  Final-EIR material is absent.
- **Provenance and reproducibility:** a later run can recover the same source
  identity and detect upstream changes from the manifest without relying on
  hidden local knowledge.
- **Tooling and architecture:** custom glue is narrow, typed, logged,
  restartable, and built around maintained packages or standard formats rather
  than a general downloader framework.
- **Failure safety:** partial downloads, server errors, redirect changes,
  checksum mismatches, and malformed PDFs produce recoverable evidence and
  cannot masquerade as a successful freeze.

## Validation

- Unit-test source-role validation, stable IDs, manifest serialization,
  duplicate URLs or paths, checksum mismatch behavior, partial-download
  cleanup, and no-clobber behavior using tiny local fixtures without a live
  network dependency.
- Run the real source-freeze command once, then run its verification-only or
  idempotent second pass against the frozen release.
- Reconcile the manifest with all three authoritative landing pages and record
  every discrepancy or redirect.
- Verify that every expected file:
  - exists at the manifest path;
  - is non-empty;
  - matches its recorded byte size and SHA-256 checksum;
  - has a PDF signature and can be opened by the selected validator; and
  - has a positive page count matching the manifest.
- Validate unique source IDs and local paths, allowed source roles, required
  manifest fields, relative-path containment under `ER_COMMONS_DATA_ROOT`, and
  aggregate counts.
- Confirm mechanically that only the main report and original Draft EIR
  appendices have `model_corpus` role, only Volume 4 has
  `curator_only_response_source` role, original submissions have
  `curator_qa_original_submission` role, and chapter PDFs have
  `recovery_qa_duplicate` role.
- Inspect the visible-terms note and any per-file overrides against the saved
  landing-page snapshots.
- Confirm that Git contains no PDFs, raw page snapshots, partial downloads, or
  generated bulk artifacts.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- The reviewed inventory accounts for the complete main report, every official
  original appendix, every separately published original written-comment
  submission, all retained chapter duplicates, and curator-only Final EIR
  Volume 4, with no unresolved landing-page anomaly.
- Every acquired file has a stable ID, correct source role, official and
  resolved URLs, UTC access time, relative path, SHA-256 checksum, byte size,
  delivered and detected type, positive PDF page count, and validation status.
- The main report and original appendices are the only model-facing sources;
  Volume 4, original comment submissions, and chapter duplicates are
  mechanically excluded from that role.
- The second pass reproduces or verifies the frozen release without
  redownloading valid files or overwriting changed ones.
- The source release, manifest, logs, and raw landing-page snapshots remain
  outside Git under the configured external root; tracked code, config, schema,
  fixtures, and documentation remain small.
- The visible-terms note preserves the access evidence without making a reuse
  determination or blocking the local learning pilot.
- Failures are explicit and restartable, and the completion outcome reports
  exact per-role file counts, aggregate bytes and pages, warnings, validation
  commands, and the precise Task 03 extraction input.

## Non-goals

- Docling installation, configuration, conversion, or canonical extraction
- OCR or image-to-text processing
- text normalization, sections, block IDs, images, figures, or page renders
- page-level extraction usability review or exclusion decisions
- comment, response, general-response, relationship, or orphan parsing
- candidate eligibility, evidence authoring, clustering, splitting, or human
  review UI work
- BM25 retrieval, target generation, judge calibration, or evaluation
- acquisition of revised Draft EIR Volumes 1 through 3, Final EIR Volume 5,
  Final-EIR appendices including Appendix Q, notices, or comment materials not
  published on the official 2025 DEIR Comments page
- publication, bulk redistribution, or a legal reuse determination
- a general CEQA crawler, downloader framework, cloud sync, backup system, or
  remote-compute layout
