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

## Implementation plan

Frozen 2026-07-24 before source acquisition.

### Release and layout

The immutable release ID is
`brisbane_baylands_2025_deir_sources_v1`. Its root is:

```text
datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_deir_sources_v1/
  sources/
    model_corpus/
    curator_only_response_source/
    curator_qa_original_submission/
    recovery_qa_duplicate/
  landing_pages/
  records/
    source_manifest.json
    acquisition_record.json
    completion_record.json
    landing_page_inventory.json
    visible_terms_note.md
  logs/
```

All paths stored in records are relative to `ER_COMMONS_DATA_ROOT`. Stable
source IDs are semantic lowercase identifiers, such as `deir_main`,
`deir_appendix_k2_part_2`, `deir_comment_document_0570`, and `feir_volume_4`;
landing-page order and City Document Center IDs are preserved separately and
never define identity.

The manifest is one versioned JSON document containing release metadata,
landing-page records, source records, role aggregates, warnings, and the
source-specification checksum. Each source record contains the fields required
under Outputs above. The acquisition record contains the exact command,
software versions, source-specification identity, aggregate counts, landing
page provenance, and warnings. The landing-page inventory materializes every
link label, position, Document Center ID, URL, selection disposition, stable
source ID, and role from the saved snapshots. A completion record is published
last and seals the manifest, acquisition record, ordered inventory, and
visible-terms note with SHA-256 and byte size; offline verification requires
all five records.

### Inventory and role checks

The reviewed source specification lives at
`configs/brisbane_baylands_2025_deir_sources_v1.json`. It is authoritative for
stable IDs, expected City Document Center IDs, roles, local filenames, and
which live links belong to the release. The live pages remain authoritative
for official labels, ordering, linked URLs, and change detection. Acquisition
stops unless the specification and live links reconcile exactly.

Expected completeness is one complete main report plus every original Draft
EIR appendix as `model_corpus`, every separately published Draft EIR chapter
as `recovery_qa_duplicate`, every PDF on the official comments page as
`curator_qa_original_submission`, and exactly Final EIR Volume 4 as
`curator_only_response_source`. The exact counts are frozen only after the
reviewed inventory resolves the Draft page's Appendix K2 label anomaly.
Revised Final-EIR volumes, Volume 5, Final-EIR appendices and notices, and
Draft-page notices or FAQs are rejected by the role checks.

The live reconciliation found that the Draft page omits K2 part 2 and labels
two distinct links as part 5. On 2026-07-24 the user approved a narrow repair:
use Final-EIR Document Center record 2965 for K2 part 2, use Draft-EIR record
537 for K2 part 5, and treat Draft record 569 as the duplicate/mislabeled
landing-page slot. The repaired part retains `model_corpus` role but must carry
a machine-readable `source_edition_override` warning and its Final-EIR landing
page provenance. Later response screening must flag any candidate whose
evidence depends on this part for explicit review. This exception does not
authorize any other Final-EIR appendix substitution.

### Retrieval and publication behavior

Requests streams each GET through a client with explicit connect/read
timeouts, bounded GET-only urllib3 retries, exponential backoff, `Retry-After`
support, redirect history, and a project user agent. Downloads go to a unique
same-directory `.part` file while SHA-256 and byte size are calculated. A
successful response must have a PDF signature, open with the selected
validators, have a positive page count, and complete or explicitly warn on
structural checks before an atomic same-filesystem no-clobber publication.
Failures remove only the temporary file.

A matching existing final file is checksummed, validated, and reused. A
mismatch, changed live inventory, unexpected redirect host, malformed PDF,
incomplete response, or conflicting final path stops the release. Existing
files are never overwritten. A missing source may be retrieved only during
freeze mode; verify mode is network-free and requires every manifest artifact
to exist and validate.

Landing pages and the visible copyright page are fetched, checksummed, and
saved before source retrieval after their inventories reconcile. Their linked
and final URLs, redirect histories, access times, and response metadata are
recorded just like the PDF provenance.

### Packages and commands

Requests plus urllib3 provide streaming, redirects, response metadata, and a
declarative bounded retry policy with less project code than `urllib.request`
or HTTPX plus a separate retry layer. Beautiful Soup provides maintained HTML
parsing rather than selector logic built on regular expressions. Pikepdf
provides page counts plus structural and stream checks. Strict pypdf parsing is
a recorded fallback for a published PDF that Poppler and pypdf can open but
pikepdf rejects; the fallback never erases the primary validator's warning.
Standard library `hashlib` supplies streaming SHA-256. This mirrors BagIt's
completeness, relative-path containment, and checksum-validation invariants
without implementing a BagIt package.

The live and verification commands are:

```bash
make freeze-brisbane-sources
make verify-brisbane-sources
```

They wrap the package-backed CLI and the reviewed specification. Generated
artifacts remain below the release root above; no source bytes or generated
records enter Git.

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

## Outcome

Completed 2026-07-24. The package-backed source workflow froze and independently
verified `brisbane_baylands_2025_deir_sources_v1` below:

```text
/Volumes/x10pro/er_commons/datasets/ceqa/raw/brisbane_baylands/
  brisbane_baylands_2025_deir_sources_v1/
```

The release contains 96 unique PDFs totaling 1,630,758,324 bytes and 51,407
pages:

| Source role | Files | Bytes | Pages |
| --- | ---: | ---: | ---: |
| `model_corpus` | 35 | 1,519,926,399 | 48,341 |
| `curator_only_response_source` | 1 | 9,217,817 | 744 |
| `curator_qa_original_submission` | 29 | 26,338,011 | 272 |
| `recovery_qa_duplicate` | 31 | 75,276,097 | 2,050 |

The reviewed configuration reconciles every Document Center link on the
[Draft EIR](https://www.brisbaneca.gov/237/2025-Draft-EIR),
[comments](https://www.brisbaneca.gov/570/2025-DEIR-Comments), and
[Final EIR](https://www.brisbaneca.gov/774/2026-Final-EIR) pages. All 140 live
PDF links returned directly without HTTP redirects. The manifest accounts for
excluded notices, Final-EIR material, and the duplicate Draft K2 link rather
than silently omitting them. The ordered landing-page inventory preserves all
140 labels and positions with 96 selected and 44 explicitly excluded links.

The City Draft page omitted Appendix K2 part 2 and linked two records labeled
part 5. The user approved a narrow documented repair: model-corpus K2 part 2 is
Final-EIR record 2965 (70,207,279 bytes, 1,048 pages), while part 5 is Draft
record 537 (43,974,745 bytes, 2,328 pages). Part 2 carries a
`source_edition_override` warning. Task 03 must propagate that flag into
page-usability records, and later response/case screening must explicitly
review any case whose evidence depends on that part.

Every acquired file has a stable ID, role, official and resolved URL, UTC
access time, HTTP metadata, contained relative path, original filename,
SHA-256, byte size, delivered and detected type, PDF signature, positive page
count, validation status, warnings, and terms-note reference. Sixteen records
had parser-repair warnings; a seventeenth carries only the K2 provenance
override. The two-page chapter duplicate `deir_chapter_duplicate_07` is
readable by Poppler and strict pypdf but lacks the `/Root` dictionary pikepdf
expects, so the manifest preserves the primary-validator failure and fallback.
Most remaining warnings are low-level repaired-object diagnostics, dominated
by K2 part 4, and remain attached to their source records.

The final completion record hashes the manifest, acquisition record, ordered
landing-page inventory, and terms note and is published only after those
required records exist. The network-free verifier requires that marker and
validates all sealed checksums, so a crash between record writes cannot
masquerade as a completed release.

Requests and urllib3 reduced custom streaming and retry code; Beautiful Soup
owns HTML parsing; pikepdf and strict pypdf own PDF parsing; `hashlib` owns
streaming SHA-256. The workflow mirrors [RFC
8493](https://www.rfc-editor.org/rfc/rfc8493.html) completeness, relative-path,
and checksum invariants without implementing BagIt. The practical lessons are:
public availability is access provenance rather than a reuse license; linked
URL, resolved URL, and checksum are distinct source-identity evidence; and
mechanical roles keep duplicate and curator-only material outside the model
corpus.

The visible-terms note records the saved
[Copyright Notices](https://www.brisbaneca.gov/copyright) page without making
a reuse conclusion. No PDF, page snapshot, partial download, or generated
release record exists in Git. Validation passed:

```text
make fix
make check
make freeze-brisbane-sources
make verify-brisbane-sources
git diff --check
```

The precise Task 03 input is `records/source_manifest.json` in the release
above, filtered to the 35 `model_corpus` records and pinned to their recorded
checksums. Task 03 should write the bounded canonical-extraction contract
before installing or running Docling; no extraction began in this task.
