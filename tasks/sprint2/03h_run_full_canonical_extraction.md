# Task 03H: Publish and Validate the Full Document Collection

Status: **paused pending separate user approval to restart from the first ordered
source under the reviewed post-[Task 03H.1](03h1_profile_and_repair_full_document_scaling.md)
execution plan**. Task 03H.1 closed on 2026-08-19; that closure does not authorize
PDF/model execution. Task 03H was activated
by user direction on 2026-08-18. Tasks 03G.1,
03G.2, all observed-failure remediation, and the [Task
03G.3](03g3_align_pipeline_responsibilities_and_names.md) architecture and
naming refactor are accepted and closed. Activation begins with the no-PDF
preparation phase: implement and offline-validate the independently sealed
content-parsing restart boundary and write the short run plan required below.
Check in with the user before source-PDF or model execution.

## Restart boundary after Task 03H.1

The next Task 03H execution is a new full-corpus run, not a continuation of the
historical "remaining 29" or "remaining 30" queue below. Before execution, regenerate
and validate the production identity and all run specifications from the accepted
Task 03H.1 code, reconcile the exact 35-source manifest order, write a new serial run
plan beginning with the first source, and check in with the user before any PDF/model
work. Historical first-wave and K2 results remain diagnostic evidence only; they do
not count toward the new run's 35 terminal records.

Starting from the beginning does not mean blindly recomputing expensive conversion.
For each source in order, Task 03H first validates the current conversion identity,
completion, inventory, page accounting, and exact source/model/runtime bindings. An
exact current seal is reused without constructing Docling; a missing, stale, or
invalid seal is rebuilt and recorded normally. All post-Docling stages are regenerated
under the current compact schemas. No compatibility reader or historical downstream
bundle is maintained merely to preserve the stopped run.

The new Task 03H owns corpus execution, all 35 terminal document records, collection
assembly and validation, and the eventual deletion manifest for superseded
non-Docling artifacts. Before collection handoff, it must run the explicit deep audit
over every hierarchy candidate selected for the collection; ordinary restart lookup
trusts completion-sealed inventories and immutable published files without rehashing
large semantic payloads. None of this work is required to close Task 03H.1.

## Preparation checkpoint: 2026-08-18

The preparation-only implementation blocker is cleared in code, subject to the full
repository validation recorded at handoff. Content parsing now publishes a separately
identified `dconv1-` bundle before derived routing and tables. Reuse verifies the
identity derivation, exact managed file set, every checksum, completion-to-inventory
seal, source and release linkage, terminal status, full expected/converted/document
page lists, raw success, zero conversion errors, and asset accounting. Only a cache
miss constructs `DocumentConverter`. The derived `prv1-` identity names the exact raw
conversion ID and persists its completion and inventory checksums. Offline tests cover
reuse, routing-only invalidation, interruption after raw publication, corrupted or
logically incomplete raw evidence, and non-duplicated failure retention. No source PDF
or model has been invoked during this checkpoint.

The frozen Task 02 model-corpus scope contains 35 sources and 48,341 pages. Task 03G
measurements support a conservative planning rate of 0.55 seconds per page per
producer configuration. Two required conversion configurations therefore imply
96,682 page-passes and about 14.8 conversion-hours at concurrency one. Concurrency two
would have a theoretical 7.4-hour conversion floor, but two observed large-document
peaks could exceed 30 GB on this approximately 36 GiB host. The launch default is
therefore document concurrency one until the first wave supplies Task 03H measurements.
About 1 TiB is currently free. Prior producer evidence suggests roughly 170-200 GB for
two full producer views; retaining both independently sealed conversion bundles and
compatibility views could raise conversion-plus-producer use to roughly 300-400 GB
before downstream artifacts. These are capacity estimates, not reservations. A
complete validated candidate and handoff is not credibly promised in one overnight
window until the first wave measures the new boundary and downstream critical path.

The proposed first wave is the following five-source, 554-page set:

- `deir_appendix_f2` (16 pages), covering an accepted continuation boundary;
- `deir_appendix_l` (36 pages), covering a learned-fallback positive;
- `deir_appendix_o` (54 pages), an ordinary mixed figure and wind-analysis control;
- `deir_appendix_c` (86 pages), covering several learned-fallback positives; and
- `deir_appendix_e` (362 pages), covering hierarchy complexity and the prior nested-
  regime risk.

The known rotated-page positive occurs in the 2,328-page K2 part 5 source, so it is not
misrepresented as a small or medium first-wave member. It is the first post-wave risk
source if the five-source gate passes. Reserve one to two hours for the first wave,
including all document processes and exact reuse checks; update the forecast from its
observed critical path before scheduling the other sources.

The configuration gate is complete. The checked-in production-full inputs are:

- document spec: `configs/brisbane_baylands_2025_deir_task03h_document_v2.json`,
  SHA-256 `1271011c66d62173d8a29b7a7deb5b56c991f47302510762642a9d8c8371b716`;
- collection spec: `configs/brisbane_baylands_2025_deir_task03h_collection_v2.json`,
  SHA-256 `ca2d4f9ca6caadfac5a6a8847c39ff37b54344a4b8e6b09f02f0fadde7dfc60d`;
- full source-family catalog:
  `configs/brisbane_baylands_2025_deir_task03h_source_family_catalog_v1.json`,
  SHA-256 `dabdc76d765859c59b8e90cc9681f394362dbbb0e4b5683bb073be067cefacff`;
- 210 unique source-specialized templates below `configs/task03h/`; and
- native-v2 production identity
  `exv1-2062cbc522311109775485bd6b816c030b601f65abbb404514b36c3526aad332`.

These source-free closeout values will change again when Task 03H regenerates its
execution identity after Task 03H.1 is committed; they are not approval to execute.

The source-free readiness report is
`pipelines/brisbane_baylands/task_03h/inputs/task03h_preparation_readiness.json`
under the external artifact root. It records 35 sources, 48,341 pages,
1,519,926,399 source bytes, 6,389 preserved manifest warning entries, no existing
Task 03H completion marker, and false values for both source-PDF and model-file reads.
The complete catalog is staged beside it with exact checked-in bytes. Multipart K1/K2
aliases are part-specific; a bare logical-appendix reference is not silently assigned
to one file.

Reproduce the source-free preparation with:

```bash
uv run python scripts/prepare_task03h.py
```

The exact first-wave execution commands are:

```bash
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_f2
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_l
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_o
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_c
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_e
```

The five commands will run serially and then repeat for each source to prove
zero-Docling reuse. The collection command remains withheld
until all eligible document terminal states exist; its later exact interface is:

```bash
make assemble-collection-handoff COLLECTION_SPEC=configs/brisbane_baylands_2025_deir_task03h_collection_v2.json
```
The user granted that PDF/model approval on 2026-08-18; the execution result is
recorded below.

## First-wave execution checkpoint: 2026-08-18

The user approved the five-source PDF/model wave. Initial execution started serially
and stopped fail-closed at Appendix C before Appendix E or any collection work; the
wave later resumed after the bounded remediations below.

- Appendix F2, Appendix L, and Appendix O published complete document candidates and
  identical invocations returned the same completion paths in 0.73, 0.85, and 0.85
  seconds, respectively. Their first complete runs took 39.37 seconds for L and 47.23
  seconds for O; F2's initial timing was interrupted by the remediations below.
- The first F2 attempt exposed two source-independent stale paths from the accepted
  responsibility rename: hierarchy code inventory still named `configuration.py`,
  and final-source lineage validation still read `record_mapping/documents.jsonl`
  instead of `canonical/documents.jsonl`. Both failures were retained, fixed with
  direct regression tests, and the sealed F2 Docling conversions were reused.
- Appendix C's source-release repair warning exposed a projection defect: canonical
  conversion observations retained Python warnings but not source-manifest warnings.
  The mapping now retains both warning classes and passes the schema with focused
  regression coverage. C's two Docling conversions and producer publications remain
  sealed and reusable.
- After that repair, Appendix C reached hierarchy inference and failed terminally
  because its PDF outline has two non-clickable grouping bookmarks that each own a
  child subtree: `Appendix A Exhibits.pdf` owns 25 valid ordered children and
  `Appendix B Exhibits.pdf` owns four. Inspection confirmed matching visible body
  headings on the immediately preceding pages 52 and 81. The user authorized a
  bounded extension: fuzzy-match the appendix identifier only, require one unique
  body heading on the immediately preceding page plus wholly valid ordered child
  destinations, retain the original parent-child structure, and emit
  `OUTLINE_CONTAINER_RECOVERED`. Any non-match remains fatal.
- The code fixes and bounded outline-container recovery advanced the production
  identity to
  `exv1-b894b665a8f4809edc9d0ceaec1628839d7e6ffd3beb7e2934c2717694625cbd`.
  The successful earlier document completions remain valid immutable evidence under
  their earlier identities, while all conversion and producer stages remained
  reusable during the final-identity rebuilds.
- Appendix E exposed one source-independent contradiction in the frozen hierarchy
  implementation: a verified picture caption inside a detected TOC region was
  selected for R01 exclusion even though the written policy and validator require
  all verified picture captions to reach R08 as content. The R01 builder and both
  validator paths now apply the documented caption exception, with a direct
  `toc_region=true` regression test. E then completed without rerunning either
  Docling producer.
- F2, L, O, C, and E are all sealed under the current production identity. Their
  final-identity downstream rebuilds took 9.39, 10.05, 11.46, 20.06, and 37.25
  seconds, respectively; identical invocations reused the same completion paths in
  0.72, 0.74, 0.74, 0.78, and 0.97 seconds. All five terminal states are
  `complete_with_warnings`. C records exactly two `OUTLINE_CONTAINER_RECOVERED`
  diagnostics, binding Appendix A and B to visible headings on pages 52 and 81.

The final repository gate passes Ruff formatting and lint, strict mypy across 290
source files, all 615 tests, deterministic Task 03H generation, and
`git diff --check`. No collection work has started; the remaining 30 document
sources are the next execution boundary.

## K2 part 5 execution checkpoint: 2026-08-19

The user approved `deir_appendix_k2_part_5_of_5` as the first post-wave risk
source. Its first attempt exposed excessive peak memory while serializing Docling's
embedded page and picture rasters. The approved source-independent repair now saves
all 111 figure crops as managed assets, removes 2,328 page rasters and 111 picture
rasters from the durable JSON, and streams both large JSON records atomically. The
conversion identity binds this externalization policy, and bundle verification
rejects embedded rasters or inconsistent externalization accounting.

The repaired run completed and sealed both 2,328-page Docling conversions and both
derived routing/table producers. Each raster-free `document.json` is 1,471,964,647
bytes and each streamed `conversion_pages.json` is 22,514,010,872 bytes. The two
producer configurations agree on 693 no-table pages, 802 full-page-numeric pages,
833 layout-region pages, and 1,819 clean tables. The production identity is now
`exv1-b1a340675b1a871baa3a17732df4a5649df9dd4973671373ba9f7ddb20644b28`;
the repository gate passed Ruff, strict mypy across 290 source files, all 618 tests,
deterministic Task 03H generation, and `git diff --check` before execution.

K2 did not publish a complete document candidate. Record mapping failed on
`appendix_k2_part_5_of_5_p00233_t001` because it requires every clean table to name
a Docling layout-region ID. Full-page-numeric tables are intentionally extracted
from the complete page rather than from a Docling layout region, so they have no
truthful region ID. This affects all 819 Camelot Stream tables produced through that
route, not only the first table reported on page 233. The automatic retry proved
restart isolation: it reused both exact producer seals without Docling or table
reconstruction, then reproduced the same mapping failure. Both failed attempts are
retained; no hierarchy, document-structure, reference-linking, or collection stage
ran for K2.

The next approval boundary is a source-independent mapping-contract correction:
allow an absent region ID only for full-page-numeric tables, continue requiring a
region ID for layout-region tables, and require layout-region mappings to cover
exactly the layout-derived clean tables. Do not invent a synthetic Docling region for
a full-page extraction. After focused regression coverage and identity regeneration,
resume K2 from its sealed producer evidence before starting another source.

## Performance halt checkpoint: 2026-08-19

Subsequent source-independent mapping and hierarchy work advanced K2 beyond the
failure described above, but exposed an unacceptable full-document critical path.
Corrected record mapping took 1,875.85 seconds, used about 16 GB peak RSS, and wrote
an approximately 4.6 GB candidate. Hierarchy inference then ran for 5,681.90 seconds
before a terminal outline invariant failed. A later hierarchy/bookmark-owned identity
change invalidated the baseline derived producer and caused another 5,626.79-second
routing/table rebuild. The heading producer was stopped at the user's direction.

Profiling identified a quadratic-like per-page alignment: every traversed text scans
and renormalizes every parsed text-line cell on that page. Hierarchy also constructs
the complete feature seeds twice. Separately, each raw conversion view contains a
1,471,964,647-byte `document.json` and a 22,514,010,872-byte
`conversion_pages.json`; those payloads are physically repeated in derived
compatibility views and reread for hashing. The size, copying, invalidation, whole-
object JSON, late-validation, and observability problems are coupled rather than a
bounded K2 exception.

The user stopped K2 and split all performance and storage remediation into active
[Task 03H.1](03h1_profile_and_repair_full_document_scaling.md). No further Task 03H
source or collection work may start until Task 03H.1 profiles the sealed evidence,
repairs the source-general boundaries, passes its offline budgets, and the user
explicitly approves resumption. Existing sealed K2 conversions/producers and retained
attempt evidence remain immutable and reusable; incomplete workspaces are not
authorized for deletion.

## Abstract

Run the frozen document and collection workflow across all 35 checksum-pinned
model-collection PDFs without treating document parsing as one restart boundary. For
each required source/configuration pair, publish the expensive Docling
conversion as independently sealed immutable evidence before routing, table
reconstruction, record mapping, or later processes consume it. Prove that boundary
on a small, diverse full-document wave before scheduling the remaining corpus;
afterward, pipeline work as capacity allows while retaining the stage seals.

Publish immutable per-document candidates, seal the collection
target/alias index, publish cross-document resolution records, and account
explicitly for every source and terminal state. Produce a candidate handoff and
machine integrity evidence for Task 04. Task 04 independently decides
usability and freezes the accepted extraction release; Task 03H does not
silently represent a failed source as a successful extraction.

## Goal

Produce a reproducible, internally consistent candidate corpus whose successes,
failures, lineage, hierarchy, labels, aliases, and cross-references can be
independently validated before benchmark use.

## Inputs

- user-approved Task 03G umbrella outcome and strict Task 03G.3 v2 configuration,
  identity, and capacity settings
- the sealed Task 02 manifest filtered to its 35 ordered, checksum-pinned
  `model_corpus` records
- responsibility-oriented packages and commands accepted in Task 03G.3, plus the
  behavioral contracts accepted in Tasks 03C.1 and 03D.1, the
  Task 03E.2d correction acceptance, and Tasks 03E.3–03F
- accepted pilot evidence and `/Volumes/x10pro/er_commons` capacity
- measured Task 03G conversion and downstream timings sufficient to forecast
  the first full-corpus execution window

## Outputs

- one immutable, completion-last Docling conversion bundle for every required
  successful source/configuration pair, including source checksum, conversion
  configuration, model/package/runtime identity, managed-file inventory,
  checksums, warnings, and an explicit success seal
- derived routing and table evidence that names its exact sealed Docling input
  and can be rebuilt without rerunning conversion when that input remains valid
- immutable parser evidence, canonical records, inferred hierarchy,
  printed-label evidence and resolutions, aliases, reference mentions,
  within-document resolutions, content assets, and mappings for every
  successful stage-one document
- one explicit terminal success or failure record for every required source
- a sealed target/alias index over terminal stage-one results
- immutable cross-document-resolution records, including explicit unresolved
  reasons for unavailable or ambiguous targets
- separate target-index, resolution, all-source-accounting, and candidate-
  handoff completion records
- collection manifest, machine report, checksums, warnings, configuration, and
  software/model/runtime identities
- producer-side completeness, schema, referential-integrity, coordinate,
  asset, stage-immutability, and rerun reports
- page-, table-, table-family-, hierarchy-, label-, alias-, mention-, and
  resolution-level machine observations for Task 04, with no human-review
  fields
- an exact Task 04 input path and review-cache recipe

Page renders are not canonical outputs. Generate only the predeclared Task 04
review sample as regenerable cache, outside extraction identity and
completeness.

## Research / learning checkpoint

The outcome must explain:

- **A zero exit code is not a release proof.** Source accounting, artifact
  integrity, schema validity, referential integrity, stage immutability,
  rerun checks, and warning visibility are separate layers.
- **Accounting is not success.** Every source can have a terminal record even
  when policy blocks candidate handoff or later acceptance.
- **Machine handoff is not Task 04 freeze.** Task 03H reports exactly what was
  produced; Task 04 determines what is usable for the benchmark.
- **The corpus pass cannot rewrite documents.** Cross-document resolutions are
  new records over a sealed target index.
- **Extraction recall bounds retrieval recall.** Later analysis must distinguish
  absent/unusable evidence from ranking and synthesis failures.
- **Extraction changes invalidate anchors.** A new parser, hierarchy,
  configuration, schema, or resolution policy creates a new identity and
  requires explicit benchmark migration.
- **Warnings and failures are release data.** Parser anomalies, source
  exceptions, partial outcomes, and unresolved references must remain
  queryable.
- **Expensive inference and deterministic interpretation have different
  restart boundaries.** A routing, table, canonical, hierarchy, resolution, or
  reporting correction must not rerun valid Docling conversion merely because
  the old parsing lifecycle sealed them together. Only a source-byte,
  Docling/model/configuration, conversion-adapter, or conversion-contract
  change can invalidate the corresponding conversion bundle.
- **An overnight target requires an honest forecast.** Pilot timings, source
  pages, model multiplicity, concurrency, memory, free space, and downstream
  throughput must support the intended window before launch. Missing the
  forecast is reported as operational variance; it is never hidden by calling
  incomplete work successful.

## Plan / spec requirement

Write a short run plan immediately before execution. Confirm:

1. all source, corpus, parser, model, configuration, schema, hierarchy, and
   resolution identities;
2. a preparation phase that implements and offline-validates the split
   conversion identity, raw seal, derived-stage consumer, and no-converter
   reuse path before any Task 03H PDF allocation;
3. that Docling conversion has its own content-bound identity, managed-file
   inventory, completion-last publication, checksum-verifiable reuse path, and
   consumer validation independent of routing/table policy identity;
4. exact commands, bounded concurrency, memory/disk limits, interruption
   behavior, and retry settings;
5. a conservative wall-clock and capacity forecast from Task 03G evidence for
   the intended first execution window selected in the run plan. State whether
   a complete validated candidate and handoff can credibly finish within that
   window; if not, report the estimate and revised schedule before allocating
   the corpus run;
6. a first wave of four to six diverse small or medium documents that runs
   through the complete document pipeline. Select the exact sources in the run
   plan from page count, layout/table regime, rotation, and learned-fallback
   evidence; do not select only easy controls;
7. that the first wave passes conversion sealing, derived producer stages, all
   document processes, and reuse verification before the remaining conversions
   are scheduled;
8. after the first wave passes, a work queue that may convert the remaining
   documents and start later stages as each conversion seal becomes available,
   without waiting for all 35 conversions or weakening resource limits;
9. stage-specific invalidation and restart behavior:
   - record-mapping or later-process changes reuse sealed Docling and derived parsing
     evidence when their identities still verify;
   - routing or table changes reuse sealed Docling evidence and rebuild the
     affected derived parsing and downstream stages;
   - source bytes, Docling/model/configuration, conversion-adapter, or
     conversion-contract changes invalidate only the affected conversion
     identity and require an explicit scope decision before rerun;
   - an operational retry or resource-setting change that leaves all
     output-affecting inputs unchanged resumes or checksum-reuses the existing
     identity rather than inventing a new semantic version;
   - a source-specific failure retries only that source, while a shared-stage
     change invalidates only that stage and its descendants;
10. stage-one monitoring, interruption, atomic publication, terminal-state,
   and all-source-accounting requirements;
11. target-index sealing and second-pass no-mutation checks;
12. candidate-handoff policy for failures, including the hard stop for a
   material main-report failure;
13. fixed-subset rerun checks;
14. Task 04 machine-record and review-cache handoff; and
15. retention and isolation of failed or rejected versions.

If the maintained runtime cannot seal and reuse Docling conversion separately
from routing and tables, that is a pre-execution implementation blocker. Do
not compensate by launching a monolithic 35-document parsing run.

Do not change accepted parser, Task 03E.2d hierarchy, schema, or resolution
policy during the run. A material new failure mode stops the candidate for an
explicit Task 03G or owning earlier-task revision.

## Review pass

- **Source accounting:** all and only the 35 model-corpus sources have terminal
  records.
- **Candidate integrity:** every published artifact is checksummed, contained,
  referenced, and covered by the appropriate completion record.
- **Restart isolation:** downstream identities reference exact Docling seals,
  and invalidation tests prove which stage must rebuild for each change class.
- **Stage isolation:** target-index and cross-document passes preserve
  stage-one bytes.
- **Structural consistency:** IDs, hierarchy, labels, aliases, references,
  coordinates, assets, and mappings satisfy the frozen contracts.
- **Warning visibility:** no failure, warning, anomaly, or source exception is
  erased by aggregation.
- **Independent freeze:** the candidate does not claim Task 04 acceptance.

## Validation

- Reconcile inputs against all 35 ordered manifest records and checksums.
- Validate every Docling conversion bundle independently before a derived
  producer consumes it; reject missing, partial, stale, or checksum-mismatched
  conversion evidence.
- Reconcile expected pages for every successful extraction; preserve explicit
  failure coverage rather than fabricating page success for failed sources.
- Validate every artifact role, schema, checksum, contained path, and identity.
- Validate global ID uniqueness and all document, page, block, section, table,
  table-family, figure, image, asset, mapping, alias, mention, and resolution
  relationships.
- Validate bounding boxes against page dimensions and coordinate frames.
- Validate every referenced content asset.
- Verify the target index contains exactly the eligible terminal stage-one
  outputs.
- Verify cross-document resolution leaves stage-one checksums unchanged.
- Recompute aggregate counts instead of trusting separately maintained totals.
- Reinvoke the accepted Task 03G.2 pilot subset under the Task 03H contract and
  verify the exact reuse or rebuild behavior frozen after Task 03G.
- Exercise the invalidation matrix without rerunning PDFs: a downstream-only
  identity change must reuse sealed Docling evidence, a routing/table identity
  change must rebuild from it, and a conversion-owned change must refuse reuse.
- Interrupt a bounded fixture workflow and verify it resumes from the first
  missing or incomplete source while preserving earlier valid seals.
- Require the checksum-reuse invocation to make zero Docling calls for every
  verified raw conversion candidate and zero model calls for every other
  verified reusable model-owned artifact.
- Compare observed wave and full-run timings against the preflight forecast and
  report the critical path, idle time, retries, and completion variance.
- Verify human-review fields are absent and all Task 02 warnings propagate,
  including K2's `source_edition_override`.
- Verify requested review renders are reproducible cache and excluded from
  completeness.
- Verify Git contains no bulk source or generated extraction artifacts.
- Run:

```bash
make check
git diff --check
```

## Acceptance criteria

- All 35 sources have explicit terminal records under one corpus identity.
- Every successful document has a verified immutable stage-one candidate;
  failures remain failures with deterministic reasons.
- Every successful required Docling conversion has its own verified immutable
  completion, and routing/table or downstream remediation can reuse it without
  model execution when conversion-owned inputs are unchanged.
- The diverse first wave completes end to end before remaining corpus
  conversion is scheduled.
- No completed main-document raw conversion runs twice under the same frozen
  raw-conversion identity.
- A material native-extraction failure in the main report blocks candidate
  handoff and requires a new decision.
- The target index and cross-document resolution are complete under the frozen
  policy and do not mutate document candidates.
- All-source accounting, candidate handoff, and the later Task 04 freeze are
  represented by distinct records.
- Schemas, IDs, coordinates, checksums, assets, references, and fixed-subset
  rerun checks pass for published candidates.
- Task 04 receives complete machine observations and source-failure records
  without prefilled human dispositions.
- Page renders are absent from canonical completeness claims.
- Generated bulk artifacts remain outside Git.
- The outcome reports exact success/failure counts, pages, bytes, timings,
  warnings, unresolved references, validation commands, forecast variance,
  and Task 04 input.
- For the first execution window, “done by morning” means a complete validated
  candidate and handoff, not merely finished Docling conversions. Elapsed time
  is an operational target rather than a corpus-validity acceptance criterion;
  if only an earlier phase fits the window, the run plan must say so before
  launch.
- The candidate is not called accepted or frozen until Task 04 independently
  validates it.

## Non-goals

- assigning final usability or document dispositions
- reviewing every page or table semantically
- OCR, LLM repair, or visual-question answering
- extracting Final EIR Volume 4 comments and responses
- case screening, evidence authoring, retrieval, generation, or scoring
- changing parser, hierarchy, schema, or resolution policy during the run
