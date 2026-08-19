# Task 03H.1: Profile and Repair Full-Document Scaling

Status: **closed on 2026-08-19 by explicit user approval**. This task
may inspect and replay already sealed K2 evidence, but it must
not read another source PDF, construct Docling, run a model, resume Task 03H, delete
retained Docling evidence, or assemble the collection without new user approval. By
user decision,
superseded non-Docling bundles may be removed only after their replacements are sealed
and validated; no deletion occurs during the audit or before an exact deletion manifest.
This is MVP work: the accepted implementation uses one clean current schema and does
not retain compatibility aliases, readers, writers, branches, duplicate data, or
historical downstream contracts. One-time regeneration or migration tooling may read
frozen Docling evidence during the repair, but it is not part of the maintained
runtime after cutover.

## Abstract

Task 03H exposed a source-general scaling failure that is too large to repair as
incidental live-run work. One 2,328-page document created approximately 24 GB per raw
conversion view, duplicated those bytes across raw and derived publications, spent
31 minutes materializing canonical records, and spent more than 94 minutes in
hierarchy inference before failing. A later identity change rebuilt an otherwise
reusable producer for another 94 minutes. Earlier bad table traversal also created
about 2.15 million canonical blocks and drove the process to a sampled 67.2 GB
physical footprint.

This task makes every expensive boundary measurable and explains the 24 GB artifact
byte by byte. It then replaces superlinear scans, whole-object processing, physical
compatibility copies, overly broad invalidation, and late validation with bounded,
restartable behavior. Task 03H remains paused at its sealed K2 checkpoint until this
task demonstrates acceptable time, memory, storage, and reuse behavior without
reading a PDF or running a model.

## Goal

Make complete-document processing scale approximately linearly with the records it
actually consumes, prevent sealed raw evidence from being physically copied into
each descendant, and make an unchanged expensive stage reusable without rereading
or rehashing tens of gigabytes. No single K2-sized downstream replay may take hours,
and stage diagnostics must identify the responsible operation before a long run is
scheduled.

## Inputs

- the two sealed, raster-externalized K2 part 5 `dconv1-` conversion bundles;
- sealed and retained K2 derived producers and failed document attempts;
- the five completed first-wave documents as small controls;
- the active Task 03H configuration and identity inputs;
- current content parsing, record mapping, heading evidence, hierarchy inference,
  publication, inventory, and artifact I/O implementations;
- prior Task 03A.14 evidence that 600 pages and 681 clean tables completed in 19.66
  minutes, as a comparison rather than a present performance promise; and
- the measurements and live samples recorded below.

## Observed performance and size ledger

These are measured facts from the stopped K2 work, not forecasts:

| Boundary | Observed result | Problem |
| --- | ---: | --- |
| one raster-free `document.json` | 1,471,964,647 bytes | Large, but not most of the 24 GB view |
| one `conversion_pages.json` | 22,514,010,872 bytes | About 21.0 GiB and 15 times `document.json`; field composition is unexplained |
| two required raw configurations | about 48 GB before derived outputs | The semantic need for each differing byte is unproven |
| physical compatibility views | repeated 1.47 GB and 22.51 GB files under several `prv1-` identities | Descendants amplify storage and copy/hash time instead of referencing the raw owner |
| first baseline producer build | 9,159.33 seconds, about 2.54 hours | One producer already exceeds an acceptable downstream critical path |
| first heading producer build | 9,258.11 seconds, about 2.57 hours | The two producers alone exceeded five hours before mapping or hierarchy |
| stale pre-externalization attempts | about 5.30 GB `document.json` apiece | Retention is unbounded and has no accepted cleanup policy |
| corrected record mapping | 1,875.85 seconds in one retained attempt and 2,564.52 seconds in another, about 31.3 and 42.7 minutes | Peaked near 16 GB RSS and wrote an approximately 4.6 GB candidate |
| hierarchy inference | 5,681.90 seconds, about 94.7 minutes, then failed | Expensive feature work preceded a terminal outline check |
| current-identity baseline producer | 5,626.79 seconds, about 93.8 minutes | A hierarchy/bookmark change invalidated routing and tables |
| earlier incorrect mapping | about 2.15 million canonical blocks | Duplicated raw table descendants and reached a sampled 67.2 GB physical footprint |
| corrected table traversal | suppressed 1,062,177 raw table-descendant texts but retained about 1,092,851 text events | Remaining record density and output size still need explanation |
| publication/inventory | live sample in file reads and SHA-256 updates | Reuse and publication repeatedly touch huge bytes whose sealed digests already exist |

The stopped current attempt completed its baseline producer and was interrupted during
the heading producer. It did not publish a K2 document completion. Existing sealed
conversions and producers are immutable inputs. Incomplete `.tmp` and failed-attempt
directories remain inspectable and must not be deleted until retention is accepted.

## Known slow or amplifying boundaries

The task must account for every item below. Measurements may disprove an item, but it
may not be silently omitted.

1. `conversion_pages.json` averages about 9.7 MB per page. Its dominant keys,
   repeated values, and actual downstream consumers are unknown.
2. Two conversion configurations persist near-duplicate complete-source projections.
3. Derived producers materialize complete raw compatibility views instead of naming
   and selectively reading the immutable conversion bundle.
4. Repeated identities and retained incomplete attempts multiply those physical
   copies, with no bounded retention or cleanup report.
5. Completion, inventory, publication, and reuse reread and SHA-256 multi-GB payloads
   even when an already verified immutable seal binds exact digests.
6. Producer code inventory is too broad: a bookmark/hierarchy-only change invalidated
   baseline routing/table output and caused a 93.8-minute rebuild.
7. Routing and all 1,819 tables can therefore rerun after an unrelated change.
8. Record mapping reads a 1.47 GB object, materializes roughly 1.09 million text
   events plus records, and serializes a multi-GB candidate with high peak memory.
9. The earlier mapper emitted raw table-cell descendants beside canonical clean
   tables, doubling content. Its repair needs a scaling regression, not only an
   example test.
10. Large JSON inputs are loaded as whole Python object graphs. Stable serialization
    and validation also make additional full-data passes and temporary byte objects.
11. Hierarchy loads the full 22.5 GB conversion-page record although alignment uses
    only a subset of its fields.
12. `extract_item_observations()` calls `align_parsed_line()` for every text;
    `align_parsed_line()` scans and normalizes every `textline_cell` on that page for
    every text. Work is approximately
    `sum(text_items_on_page * textline_cells_on_page)`, quadratic-like on dense pages.
13. `single_build.py` calls `build_feature_seeds()` twice, repeating the complete
    traversal before and after outline observations.
14. Outline failure was detected only after 94.7 minutes. Cheap outline and input
    invariants are not front-loaded.
15. Progress events expose whole-stage wall time but not load, projection, copy,
    hash, routing, tables, feature indexing, alignment, validation, serialization,
    and sealing costs.
16. Forecasting uses page count but not bytes, text/cell density, routed pages, table
    count, or output records, so it missed this critical path and memory risk.

## Gate A checkpoint 1: metadata and JSON-field ledger

The source-free inspector and its focused tests are implemented in
`document_performance/task03h_gate1.py`. Reproduce the metadata ledger with:

```bash
uv run python scripts/inspect_task03h_scaling.py
```

The external report is
`pipelines/brisbane_baylands/task_03h/performance/task03h_gate1_scaling_ledger.json`.
It reads filesystem metadata plus small seal and event records, and explicitly records
false for source-PDF bytes, model files, Docling construction, and large-payload reads.
It found 16 K2 paths for the two large JSON roles: ten sealed and six incomplete,
totalling 166,237,338,997 logical bytes. Among checksum-known sealed paths, only
25,457,940,166 bytes are unique content while 94,471,937,429 bytes are duplicate
logical bytes beyond one copy. These are separate inodes and not hard links; whether
APFS shares any physical extents remains unproven.

Five sealed paths contain the exact same 22,514,010,872-byte
`conversion_pages.json` checksum. They account for 112,570,054,360 logical bytes, of
which 90,056,043,488 are duplicates beyond one content copy. The two raw conversion
configurations have byte-identical conversion-page evidence. Their `document.json`
records have the same 1,471,964,647-byte size but two distinct checksums; the exact
heading-overlay comparison below resolves that difference.

The one-time full field scan used development-only `ijson` 3.5.1 with its `yajl2_c`
backend. It read one sealed JSON file, constructed at most one `pages[]` item at a
time, read no PDF/model bytes, and completed in 765.94 seconds with 791,035,904 bytes
peak RSS. Its external report is
`pipelines/brisbane_baylands/task_03h/performance/task03h_conversion_pages_profile.json`.

The 22,514,010,872 bytes split into 14,456,885,143 bytes when the 2,328 page records
are re-encoded and 8,057,125,729 bytes for the top-level assembled result,
confidence, wrapper, and formatting. Within the page records, the overlapping field
measurements rank the dominant semantic payloads as:

- page-owned `assembled`: 8,056,607,248 bytes;
- page predictions: 3,857,016,188 bytes;
- `assembled.elements`: 3,761,100,450 bytes;
- `assembled.body`: 3,747,997,204 bytes;
- complete `parsed_page`: 1,628,307,922 bytes; and
- the 2,561,773 `parsed_page.textline_cells` actually used by hierarchy:
  1,497,475,708 bytes.

Parent and child field measurements overlap and must not be summed. The near equality
between page-owned assembled bytes and the top-level remainder motivated the exact
reconstruction proof below. The current hierarchy access pattern
needs only page number, 91,626 bytes of page dimensions, and about 1.50 GB of text-line
cells. The measured hierarchy-owned JSON projection below is substantially smaller
than this field-only estimate. JSON remains the default design candidate; page
sharding and streaming/projection must be evaluated before any alternative format.

The timing ledger also corrected the earlier incomplete runtime summary. The original
baseline and heading producer stages took 9,159.33 and 9,258.11 seconds, so those two
stages alone exceeded five hours. Later retained evidence includes the 5,681.90-second
hierarchy failure, a 5,626.79-second unrelated producer rebuild, and record-mapping
runs of 1,875.85 and 2,564.52 seconds. The remaining source-free Gate A measurements
are recorded below.

The raw conversion observations further separate model time from derived-producer
time. The two Docling conversions took 3,148.83 and 3,247.94 wall seconds, about 52.5
and 54.1 minutes, with peaks of 18,537,938,944 and 16,744,497,152 RSS bytes. The
matching first derived producer summaries took 9,127.60 and 9,223.74 seconds. After
subtracting the raw conversion observations, about 5,978.76 and 5,975.80 seconds,
roughly 99.6 minutes each, remain for compatibility materialization, verification,
routing, table reconstruction, serialization, inventory, and publication. A later
raw-reusing baseline rebuild took 5,594.97 seconds, independently confirming that
the non-Docling producer path alone costs about 93 minutes. Existing records do not
split those operations further, so Gate A must add that substage telemetry before
choosing the producer repair.

The clean-table summaries provide one more existing split. Baseline and heading table
reconstruction took 5,284.61 and 5,257.03 seconds, about 88.1 and 87.6 minutes. Both
processed the same 1,635 routed pages and published the same 1,819 logical tables,
including 819 Stream and 763 Lattice tables. The two conversion-page inputs are
byte-identical and the table policy is shared, so the current ownership model spent
almost three hours rebuilding the same routing/table result twice. After subtracting
both raw conversion and table wall time, approximately 694 and 718 seconds remain in
the initial stages for compatibility copying, conversion verification/loading,
routing, summary construction, inventory hashing, and publication. The later
raw-reusing producer spent about 310 seconds outside the table pipeline. These are
aggregate residuals, not yet direct substage measurements.

The two raw configurations are also not two independent semantic extractions. A
streaming whole-file comparison found the first `document.json` difference at one
heading `level` value. Replacing only serialized `level` integers with a common value
made the complete 1,471,964,647-byte files produce the same SHA-256,
`5a53731ce73f7b91644763dbf42fd05b235254f64789a727068f557d22146a2d`.
There are 4,751 level fields and exactly 4,739 differ: 26 change from level 1 to 2,
477 to 3, 3,004 to 4, one to 5, and 1,231 to 6. No other serialized byte differs.

This matches Docling 2.115.0's local implementation: the document-level assembled
unit is created by concatenating every page's `elements`, `headers`, and `body`, and
the optional heading-hierarchy model subsequently assigns levels on the already
assembled `DoclingDocument`. The evidence therefore supports one common conversion
and table reconstruction with a separately identified heading-level overlay. Gate A
must specify and test that split; it must not preserve a second 54-minute conversion,
88-minute table pass, and 24 GB view merely to store 4,739 integer changes.

The reproducible synthetic alignment report is
`pipelines/brisbane_baylands/task_03h/performance/task03h_alignment_scaling.json`.
It runs only generated strings and reads no sealed payload, source PDF, or model. At
250, 500, 1,000, and 2,000 texts paired with the same number of page cells, the
current implementation performed 62,500, 250,000, 1,000,000, and 4,000,000 normalized
comparisons. Its observed doubling ratios were 4.20, 3.83, and 4.05. The proposed
single normalized page index preserved exact `LayoutEvidence` results with doubling
ratios of 1.73, 1.98, and 1.94. At size 2,000 the current scan took 2.210 seconds and
the indexed build plus all lookups took 0.00333 seconds, a measured 664-times speedup.
This establishes the current quadratic-like behavior and the linear replacement
before production code changes.

## Gate A checkpoint 2: exact duplication and JSON projection

The remaining source-free checks completed against the same sealed K2 evidence. They
did not read a source PDF or model, construct Docling, rerun a table parser, or mutate
an accepted artifact.

The table-bundle report is
`pipelines/brisbane_baylands/task_03h/performance/task03h_table_bundle_comparison.json`.
Baseline and heading contain the same 10,678 paths. Of these, 8,694 files are
byte-identical. Another 1,983 JSON/JSONL files become identical after removing only
runtime measurements such as `wall_seconds`, `inference_seconds`, and aggregate
pipeline durations. The remaining differing path is the producer-owned
`configuration.json`; its pipeline identity is intentionally different. There are
zero semantic table differences. The two approximately 88-minute table passes
therefore produced the same substantive result and must become one shared sealed
routing/table bundle.

The exact assembled reconstruction report is
`pipelines/brisbane_baylands/task_03h/performance/task03h_assembled_reconstruction.json`.
A one-event-at-a-time scan compared every item under page-owned and global
`elements`, `headers`, and `body`. Counts and semantic event SHA-256 digests match
exactly for 1,087,988 elements, 4,868 headers, and 1,083,120 body items. The scan
completed in 1,437.22 seconds with 157,188,096 bytes peak RSS. This proves the global
assembled section is the exact concatenation of page-owned data. Future raw evidence
should retain one durable occurrence and derive the compatibility view; choosing
which occurrence owns the bytes remains a Gate B schema/recovery decision.

The provisional hierarchy alignment projection remains JSON. Its profile and bytes
are:

- `pipelines/brisbane_baylands/task_03h/performance/task03h_alignment_projection_profile.json`;
- `pipelines/brisbane_baylands/task_03h/performance/task03h_alignment_projection.jsonl`.

The one-page-per-line projection contains page number, dimensions, and the exact
current normalized-text alignment state. It has 2,328 page records, 382,632 normalized
keys, and 99,554 ambiguous keys. It is 26,175,668 bytes, only 0.116 percent of the
22,514,010,872-byte source and 860 times smaller. It built in 84.80 seconds from the
sealed JSON, read back and decoded completely in 0.124 seconds, and peaked at
336,199,680 RSS bytes. These measurements support a JSON-first repair; they do not
choose JSON Lines over page-sharded JSON or rule out a later measured alternative.

A direct SHA-256 pass over the 22,514,010,872-byte sealed input took 58.17 wall
seconds and reproduced its inventory digest
`22d534770a0b2f3c2e3182ed1cf6066e34658c27d2655518320a3a2a1b821276`.
Hashing alone therefore cannot explain the 310-718-second non-table residual, though
repeated verification contributes to it. The code path also performs a full
`shutil.copytree()` of the raw documents before routing, then inventories the copied
bytes. Gate A intentionally did not create another 24 GB copy merely to benchmark a
behavior already selected for removal. Gate B telemetry must directly separate
reference resolution, routing, serialization, inventory, and publication, and its
regression must prove the copy path is never called.

Gate A's evidence now supports the provisional repair design below. No Arrow,
Parquet, SQLite, JSON Lines, or page-sharded JSON choice is accepted yet. The durable
schema and ownership decision remains a user review boundary before Gate B changes
accepted contracts.

The repository check passed formatting, Ruff, and strict mypy across 292 source
files. Pytest passed 637 of 639 tests. The two failures are the Task 03H production-
identity checks: adding development-only `ijson` changed the whole-file
`pyproject.toml` reference embedded in the production identity. Gate A deliberately
did not regenerate Task 03H's production identity merely to absorb an unrelated
profiler dependency. This is direct evidence for the owner-specific identity repair:
Gate B must bind the projected runtime dependencies each production stage actually
owns, while development/profiling dependencies remain outside those identities.

## Outputs

- a source-free inspector reporting exact bytes by artifact and semantic role,
  `conversion_pages.json` bytes/counts by field and page, largest outliers,
  cross-configuration/path duplication, consumer-required fields, and retained
  workspace bytes by state and identity;
- a machine-readable K2 baseline binding sealed input digests, command, code
  identity, elapsed/CPU time, peak RSS, read/write bytes, record counts, and output
  bytes for every stage and substage;
- an accepted design selecting the smallest durable representations and reference
  boundaries only after the byte/consumer inventory is complete;
- indexed heading alignment without a per-text full-page cell scan or repeated cell
  normalization;
- one-pass feature construction, with outline facts applied without rebuilding all
  feature seeds;
- projected or streaming large-record readers/writers where consumers do not require
  the full object graph;
- derived publications that bind immutable raw completion/inventory digests without
  copying raw payloads into every descendant;
- stage-owned identities proving hierarchy/bookmark changes do not rebuild
  conversion, routing, tables, or record mapping;
- cheap preflight checks before expensive extraction, plus fine-grained progress and
  cost observations;
- an exact retention/deletion manifest that preserves valid Docling seals and removes
  superseded non-Docling work only after validated replacement; and
- updated Task 03H forecasts based on bytes, density, and table counts as well as
  pages.

## Research / learning checkpoint

Before choosing a format or optimizing code:

- use Python's maintained [`cProfile` guidance](https://docs.python.org/3/library/profile.html)
  to distinguish high call counts, hot loops, and cumulative algorithmic cost;
- use Python's maintained [`tracemalloc` guidance](https://docs.python.org/3/library/tracemalloc.html)
  for allocation snapshots, while separately recording process RSS because it does
  not cover every native allocation;
- compare the measured access pattern with the official [Apache Arrow columnar
  format](https://arrow.apache.org/docs/format/Columnar.html) and [Apache Parquet
  overview](https://parquet.apache.org/docs/overview/) before selecting either;
- assess newline-delimited JSON, page-sharded JSON, SQLite, Arrow IPC, and Parquet
  against the actual nested schema, projection needs, deterministic identity,
  corruption detection, and human inspectability; and
- explain plainly that faster serialization cannot repair an O(n squared) lookup,
  and a better algorithm cannot by itself repair 24 GB of duplication.

The format is not predetermined. A new dependency requires a measured advantage over
standard-library streaming or sharding and an explicit version/migration boundary.

## Gate A proposed repair design

This design is provisional until the user reviews the completed Gate A evidence. It
does not select a non-JSON storage format. The measured JSON-first path is:

1. **One common page conversion.** Define one conversion identity for page parsing,
   layout predictions, parsed text lines, page assembly, and base `document.json`.
   Heading-level policy is not part of that identity because the two current
   conversion-page files are byte-identical and the two documents differ only in
   4,739 level integers.
2. **One heading overlay.** Publish the optional Docling heading result as a small,
   separately identified sequence of stable text references and old/new level values
   over the common document. Applying the overlay must reproduce the current heading
   document exactly. Its identity owns heading options, bookmark inputs, Docling
   heading code/version, and the common document seal.
3. **One routing/table bundle.** Give routing and clean tables their own completion-
   last identity derived from the common conversion, source, routing/table policy,
   and table runtime. Content and heading views reference the same table bundle.
   Before implementation, compare the two current table trees semantically and
   explain any identity-only byte differences.
4. **Reference, do not copy.** Remove `materialize_conversion_input()`'s 24 GB
   `copytree` compatibility view. Derived records name the exact upstream completion,
   inventory, and managed-file digest/path. Consumers resolve that reference through
   one maintained boundary.
5. **JSON-first hierarchy projection.** Derive a separately sealed JSON Lines stream
   with one page record containing page number, dimensions, and an exact normalized-
   text alignment index. Each normalized key records absence implicitly, one unique
   line count, or ambiguity. This preserves current alignment semantics while
   avoiding the 22.51 GB load and Cartesian scan. Compare JSON Lines with page-sharded
   JSON for recovery, random access, inventory size, and human inspection before
   choosing between them.
6. **Audit and slim the raw replay bundle.** Keep valid sealed Docling bundles
   immutable, but do not accept the 22.51 GB `conversion_pages.json` schema as an
   inevitable Docling output. Prove whether `assembled.elements` equals the ordered
   union of `assembled.body` and `assembled.headers`; map every page prediction,
   parsed-cell, geometry, assembled, confidence, and wrapper field to its exact
   replay/provenance consumer; compare those semantics with `document.json`; and
   classify each field as required, reconstructable, audit-only, or redundant.
   Benchmark compact JSON, page-sharded JSON, streamed JSON/JSON Lines, compression,
   normalized ID/reference forms, SQLite, Arrow IPC, and Parquet only where the
   access pattern supports them. A candidate must reproduce every required
   post-Docling input without Docling execution. For future conversions, retain each
   required evidence class once. Existing K2 may be read by one-time task-scoped
   regeneration tooling, but the final runtime does not maintain a legacy bridge or
   dual-schema path.
7. **Hash while consuming.** A downstream process verifies the smaller projection it
   actually streams and compares that digest to its sealed inventory entry. It does
   not copy or hash unused 22 GB raw payloads. A separate deep-audit command continues
   to verify every raw byte before release/handoff.
8. **Owner-specific invalidation.** Common conversion changes invalidate all
   descendants; routing/table changes invalidate the shared table bundle and its
   descendants; heading-overlay changes invalidate only heading-dependent consumers;
   hierarchy-rule changes invalidate only hierarchy and later stages. Production
   identities bind owner-specific runtime dependency projections, not the complete
   development dependency file.
9. **One-pass hierarchy features.** Build the normalized page indexes once, construct
   feature seeds once, and apply outline matches as a linear overlay. Run cheap input
   and outline structural checks before the full traversal.
10. **Named substage observations.** Record verification, document load, reference or
    compatibility materialization, routing, table execution, reconcile, inventory,
    and publication separately, with processed units, bytes, throughput, peak RSS,
    and ETA.

Gate A completed the four evidence checks that bounded this design: the table trees
are semantically equivalent, global assembled data is exactly reconstructable from
the page sequence, the JSON alignment projection is measured on all sealed K2 pages,
and direct hash timing plus existing stage records bound the non-table residual. The
single-occurrence raw schema, JSON Lines versus page-sharded JSON choice, and direct
new-path substage telemetry are Gate B design/implementation decisions and remain a
user review boundary.

## Plan / spec requirement

### Gate A: measure and design without PDF/model execution

1. Freeze a read-only ledger of the exact sealed K2 inputs and stopped attempts.
2. Add low-overhead stage/substage time, byte, count, and memory metrics.
3. Produce the field-level byte and consumer matrix for the 22.5 GB record.
4. Profile bounded synthetic density fixtures and a short sealed K2 page range.
5. Attribute cost among load, hash, copy, parse, index, align, map, validate,
   serialize, and seal operations.
6. Specify ownership/reference, format, indexing, identity, invalidation, migration,
   and retention changes. Preserve semantics or state each intentional change.
7. Propose numeric per-stage budgets from the baseline. Check in with the user before
   Gate B if the design changes a durable schema, dependency, or accepted contract.

### Gate B: implement and prove the repair

1. **Freeze the migration inputs.** Inventory every valid sealed Docling bundle and
   every superseded downstream bundle for all 35 sources. Bind exact completion,
   inventory, file digests, schemas, and current terminal state. Do not read a PDF,
   run a model, or delete anything.
2. **Audit `conversion_pages.json` completely.** Prove the page-level
   `elements` versus `body`/`headers` relationship with counts and semantic digests;
   reconcile all bytes to predictions, parsed cells, geometry, assembled structures,
   confidence, formatting, and wrappers; compare overlap with `document.json`; and
   assign every field an owner, consumer, provenance purpose, and retention class.
3. **Specify replay invariants.** Define the exact post-Docling behaviors a smaller
   replay bundle must reproduce: routing inputs, table inputs, heading evidence,
   document reconstruction or compatibility views, diagnostics, corruption
   detection, and deep audit. A field may be removed only when equivalence or exact
   reconstruction is tested.
4. **Benchmark raw replay representations.** On sealed K2 evidence, measure compact
   JSON, page-sharded JSON, streamed JSON/JSON Lines, optional compression, and
   normalized ID/reference structures. Evaluate SQLite, Arrow IPC, and Parquet only
   if justified by the measured access pattern. Record bytes, build/read time, random
   and sequential access, peak RSS, restart granularity, inventory overhead,
   corruption isolation, and human inspectability.
5. **Benchmark hierarchy representations separately.** Compare the measured 26.18 MB
   JSON Lines alignment projection with page-sharded JSON and any justified indexed
   variant. Do not confuse this hierarchy-only input with the complete replay bundle
   or select a format before both benchmarks finish.
6. **Choose and version two schemas.** Select one complete post-Docling replay schema
   and one hierarchy-alignment schema. Document owners, field semantics, deterministic
   serialization, identity preimages, reconstruction rules, migration boundaries,
   and the single supported MVP version. Do not maintain old readers, writers,
   aliases, or dual-schema data. Check in with the user if the measured evidence does
   not support the JSON-first path or requires a new runtime dependency.
7. **Accept frozen Docling evidence under narrow identities.** Fully verify each
   reusable sealed Docling result once, derive a conversion-owned identity from source bytes,
   Docling options/models/packages, conversion code, and output-schema version, and
   bind the immutable Docling files as source evidence for one-time regeneration.
   Development, hierarchy, routing, table, and downstream code must not affect this
   identity. The final runtime need not preserve a historical compatibility adapter.
8. **Implement streaming replay derivation.** Derive the selected smaller replay
   bundle from existing valid Docling evidence without constructing the full 22 GB
   object graph. Hash the legacy input during that same pass, publish completion last,
   retain interrupted attempts, and prove deterministic output plus restart safety.
   Mark task-only migration code explicitly and remove it after every separately
   approved legacy input has been regenerated and the maintained creation path is
   independently reproducible; it is not part of the final MVP runtime.
9. **Implement one common conversion and heading overlay.** Store one base document
   and common page evidence per source. Represent heading hierarchy as a small stable
   overlay that exactly reproduces the accepted heading document rather than a second
   conversion and raw view.
10. **Implement one shared routing/table bundle.** Route pages and reconstruct clean
    tables once per source under a separately sealed identity. Baseline and heading
    consumers reference that same bundle. Regression tests must prove the current two
    K2 table trees remain semantically equivalent after runtime metadata is excluded.
11. **Replace copies with closed references.** Remove the 24 GB `copytree`
    compatibility path. Derived records bind exact owner ID, schema version,
    completion digest, inventory digest, managed path, byte size, and file digest.
    Wrong, missing, corrupt, or mismatched references must fail before downstream
    computation.
12. **Fix hierarchy complexity and failure latency.** Build each normalized page
    index once, perform constant-time alignment lookups, build feature seeds once,
    and apply outline observations without a second full traversal. Run cheap source,
    outline, and structural contradictions before expensive feature work.
13. **Bound record mapping.** Preserve the corrected table-descendant suppression,
    identify remaining million-record amplification, and stream or shard mapping,
    validation, and serialization where full-object materialization is unnecessary.
    Add scale tests for output count, memory, and approximately linear growth.
14. **Replace routine deep hashing with tiered verification.** During first derivation,
    hash large inputs while consuming them. Normal reuse verifies small seal records
    and the exact smaller artifact it reads; it neither copies nor rehashes unused
    multi-GB payloads. A separate explicit deep-audit command verifies every raw byte.
15. **Narrow every stage identity.** Prove the invalidation matrix: conversion changes
    invalidate all descendants; replay-schema changes invalidate replay consumers;
    routing/table changes invalidate the shared table bundle; heading changes
    invalidate heading-dependent stages; hierarchy changes invalidate hierarchy and
    later stages only; development-only dependencies invalidate no production stage.
16. **Add named telemetry and admission forecasts.** Measure verification, streaming
    load, projection, overlay, routing, tables, mapping, indexing, validation,
    serialization, inventory, and publication separately. Report units, bytes,
    throughput, peak RSS, elapsed time, and ETA; forecast from bytes, text/cell
    density, routed pages, table count, and expected records rather than pages alone.
17. **Validate on controls and sealed K2.** Add behavior, corruption, interruption,
    recovery, reproducibility, and synthetic scaling tests first. Replay K2 from
    sealed Docling evidence only, compare semantic outputs, and enforce the accepted
    time, memory, I/O, and storage budgets without PDF/model execution.

**Fail-fast timing rule.** Before every potentially long test or replay, name its
applicable budget and ensure it publishes enough progress to estimate completion. If
elapsed time already exceeds the budget, or a stable evidence-based ETA shows the
budget will be missed, stop the process safely, retain the inspectable attempt, and
check in with the user with the measured cause and repair options. Do not allow a run
to continue for hours merely to confirm a known budget failure. The existing K2
acceptance limits remain: no individual downstream stage over 30 minutes, total
downstream critical path under 60 minutes, peak RSS below 16 GiB, and synthetic
doubling below 2.5 times after fixed startup cost.

**Mandatory stop after step 17.** Gate B ends here. Report the selected schemas,
semantic comparisons, timing, memory, storage, identity behavior, test evidence, and
maintainability findings to the user. Do not begin the 35-source process, collection
assembly, or deletion until the user explicitly approves the next execution gate.

### Gate B outcome

Gate B completed on 2026-08-19 and is stopped at the required boundary. It did not
read a source PDF or model, construct Docling, process another source, assemble the
collection, or delete any retained artifact.

- The maintained MVP uses `er_commons.docling_conversion.v2` for one common base
  document plus separately sealed heading overlay and hierarchy alignment records.
  `conversion_pages.json` is not part of the current schema. The alignment format is
  plain `er_commons.hierarchy_alignment_page.v1` JSON Lines, one page per line.
- All 12 retained Docling bundles for the six sources present at the checkpoint were
  deep-audited once: 51,039,246,600 managed bytes matched their completion and
  inventory seals. Existing Docling bundles remain immutable.
- The task-only K2 migration read and hashed the 22,514,010,872-byte legacy replay
  record in one bounded pass and produced a 26,310,692-byte, 2,328-page alignment
  stream in 117.64 seconds with 334,528,512 bytes peak RSS. The heading overlay has
  4,739 records, is 470,128 bytes, and built in 36.61 seconds.
- Baseline and heading now reference one conversion and one routing/table owner rather
  than copying the 24 GB raw view. Narrow identities keep hierarchy/bookmark changes
  out of conversion, routing/table, and mapping invalidation.
- The final sealed K2 mapping candidate is
  `exv1-1fb6bf9ef25bfe5d86aff84b6a0913c954f09c38057e1110504aaf4ad3883a31`.
  It completed in 497.23 seconds with 10,797,793,280 bytes peak RSS. Its 18 managed
  files total 1,208,222,347 bytes, down from 5,127,627,705 bytes and 3,655 files in
  the corrected legacy candidate. The 3,919,405,358-byte reduction is 76.44 percent.
  Every declared document, page, section, block, table, figure, image, routing,
  conversion, and table-stage semantic projection is identical; the removed material
  is the explicitly documented duplicate/raw-detail representation.
- Exact reuse returns after identity and seal verification without parsing the 1.47 GB
  document: 6.66 seconds and 159,350,784 bytes peak RSS. A separate deep-audit path
  remains available for full-byte verification.
- Constant-time alignment passes the synthetic doubling limit. The Gate B source-free
  hierarchy boundary built 2,155,028 features once from the base document and 26 MB
  alignment stream in 73.39 seconds with 9,726,672,896 bytes peak RSS.
- After separate user approval, the full K2 hierarchy candidate
  `hcorv1-86e0155179103b75d6cab13b03f257c8fe7c911ee89a29c036dac59bac6af540`
  sealed successfully. The complete run took 1,021.78 seconds; no individual stage
  exceeded 30 minutes. Candidate validation and streamed assembly took 643.56 seconds.
  Peak RSS was 14,731,198,464 bytes, below 16 GiB, with zero swaps. The managed
  preterminal payload is 3,860,116,654 bytes (15.04 percent of the former
  25,671,550,861-byte producer), and the final bundle occupies 3.6 GiB on disk.
  A second invocation checksum-verified and reused the exact sealed candidate in
  29.74 seconds without rebuilding hierarchy.
- Normal reuse now verifies the completion-to-inventory seal, exact file set and
  sizes, and every small identity, input, summary, metrics, inventory, and completion
  record without opening the 3.86 GB semantic payload. The real sealed K2 candidate
  fast-verified in 0.68 seconds with 137,576,448 bytes peak RSS. The separately named
  deep-audit path retains bounded chunk hashing of every managed byte and detects
  same-size semantic corruption.
- Candidate schema validation and streamed publication now emit named progress with
  processed/total units, elapsed time, throughput, and ETA at bounded intervals. This
  closes the observability gap exposed by the 643.56-second K2 assembly stage.
- Fast reuse is deliberately an immutable-publication lookup, not a claim that every
  semantic byte was reauthenticated. It detects seal, path, size, and small-record
  corruption; the audit-only command below detects same-size semantic corruption and
  cannot build a missing candidate or open a source PDF:

  ```bash
  uv run python scripts/audit_hierarchy_candidate.py \
    --candidate-root <existing-hcorv1-root> \
    --candidate-id <hcorv1-id>
  ```

- The final independent maintainability/recovery review tightened candidate identity
  over alignment/base-document loaders, both exact conversion seals, and `uv.lock`;
  added two-sided directory fsyncs for publication and failed-attempt renames; moved
  progress throttling outside the per-record hot path; and added application-level
  interruption coverage for semantic validation, mid-stream output, post-inventory,
  and post-completion failures. All partial attempts retain inspectable evidence and
  permit a clean retry.
- A 20,004-record source-free schema benchmark validated 9,226 records per second and
  projects K2's 4.31 million schema records at 467.15 seconds, or 7.79 minutes, below
  the 30-minute stage limit. The already sealed K2 performance candidate remains
  immutable historical evidence; the final provenance hard cut intentionally derives
  a new identity for future candidates and does not require a replacement K2 run to
  close this scaling task.
- Final validation passes deterministic Task 03H generation, Ruff formatting and
  lint, mypy across 316 source files, all 732 tests, and `git diff --check`.
- Named telemetry now separates seal verification, semantic load, table projection,
  context indexing, asset registration, content mapping, support assembly, and
  serialization/validation/inventory. Admission uses bytes and record-density inputs
  as well as page count.

The selected design remains JSON-first. JSON Lines beat page sharding on inventory
overhead while remaining directly inspectable; gzip reduced bytes but weakened direct
inspection/random access; SQLite added opacity without a measured speed need; and the
nested sequential access pattern did not justify Arrow or Parquet. The temporary
legacy adapter and replay entrypoints were removed during Gate C; regenerated current
specifications now come from explicit Task 03H templates rather than historical task
configurations.

### Transfer to the restarted Task 03H

Corpus execution is not unfinished Task 03H.1 work. After this task closes, Task 03H
will restart from the first ordered source under regenerated current specifications
rather than continue a historical "remaining sources" queue. That new run owns all
35 terminal document records, collection readiness and handoff validation, and the
later exact deletion manifest for superseded non-Docling bundles. It may reuse an
existing Docling conversion only when the current conversion identity and complete
seal validate exactly; otherwise Task 03H records the source as requiring conversion.
No other source, collection assembly, artifact deletion, or Docling rerun is required
to close Task 03H.1.

### Gate C: human ownership before closure

The passing Gate B implementation is not closure evidence by itself. The user reopened
this task because critical paths remained machine-shaped: broad dictionaries hid
required fields, publication modules mixed unrelated lifecycle responsibilities,
tests reached through private helpers, and several optimized functions were too dense
for a human owner to safely modify or debug. Gate C is a semantic-preserving cleanup;
it does not authorize source PDF/model execution or corpus processing.

Gate C must:

1. replace untyped top-level semantic and prepared-input dictionaries with named,
   immutable domain records and remove the unsafe whole-candidate serialization path;
2. split semantic validation, terminal sealing, streamed storage, fast seal lookup,
   and deep byte audit into explicit owners without placeholder terminal records or
   duplicate invariant implementations;
3. retain the exact lifecycle phase and processed/total progress when an attempt is
   interrupted, expose public audit results, and make operational errors name the
   responsible artifact and phase;
4. split dense numbering-scope, conversion-bundle, table-loading, and other mixed
   modules around independently testable responsibilities while keeping byte and
   semantic outputs unchanged;
5. close typed-preflight holes, including mandatory model-inventory verification on
   a real conversion cache miss, and prove reuse checks happen before expensive
   semantic loads or construction;
6. remove hidden historical-template and task-only migration dependencies from the
   maintained runtime instead of preserving backward compatibility for MVP artifacts;
7. use public or injected responsibility seams in behavior tests; keep private helper
   tests only inside the low-level module that owns serialization or durability; and
8. add objective maintainability gates for module/function size, dependency direction,
   typed lifecycle vocabulary, and public navigation, followed by deterministic
   identity regeneration, `make check`, `git diff --check`, and an independent final
   human-ownership/recovery review.

Gate C acceptance requires a future maintainer to locate conversion preparation,
semantic construction, validation, streamed writing, seal lookup, byte audit, failure
retention, and each optimized hierarchy policy through one named owner apiece. Green
tests without that ownership structure do not close the gate.

Gate C now meets that ownership test:

- content parsing separates typed preparation, conversion execution, conversion-seal
  validation, derived publication, references, and the public application shell;
- hierarchy separates typed semantic construction, semantic and terminal validation,
  streamed storage, completion-last publication, fast immutable-seal verification,
  deep byte audit, progress, and authorization capabilities;
- record mapping separates prepared identity metadata from semantic loading, table
  records/cleanup/families/artifacts/regions, traversal preparation, immutable context
  types, deterministic ID assembly, publication, and recovery;
- document structure derives identity and checks reuse before loading large document
  views, loads the common base once, constructs once, and distinguishes fast sealed
  metadata reuse from explicit deep audit;
- Task 03H generation is a small CLI over explicit current templates, specification
  assembly, production-identity closure, deterministic I/O, and orchestration; the
  task-only migration adapter and legacy replay entrypoints are deleted; and
- the independent final review found no remaining P0 or P1 issue after repairing exact
  inventory shape/totals, model-preflight TOCTOU, owner-specific staging verification,
  completion-last durability, interruption/retry evidence, direct dependency closure,
  contextual JSONL errors, authorization sequencing, and post-rename diagnostics.

## Review pass

- **Complexity:** no density-dependent nested scan remains on the K2 critical path.
- **Artifact semantics:** every retained field has an owner and consumer; provenance
  evidence is not discarded for size alone.
- **Storage:** raw bytes have one immutable owner per genuinely distinct conversion;
  descendants reference rather than clone them.
- **Restart isolation:** a change invalidates only its owner and descendants;
  verification does not secretly repeat the expensive stage.
- **Memory:** large collections are streamed, projected, compactly indexed, or
  processed pagewise; peak use includes native allocations.
- **Failure latency:** corrupt lineage and cheap contradictions fail before expensive
  mapping or feature extraction.
- **Operations:** progress reports current substage, processed/total units,
  throughput, bytes, elapsed time, and evidence-based ETA.
- **Maintainability:** optimized code remains typed, readable, testable, restartable,
  and debuggable.

## Validation

- Preserve semantics against sealed small controls and accepted K2 outputs; document
  any intentional contract revision.
- Add synthetic scale tests. After fixed startup cost is removed, doubled text/cell
  inputs must remain below 2.5 times elapsed work and 2.5 times peak managed memory;
  call counts must confirm indexed rather than Cartesian alignment.
- Verify feature seeds are built once per hierarchy candidate.
- Verify a hierarchy/bookmark-only change makes zero conversion, routing, table, and
  record-mapping calls and does not copy or hash their payload bytes.
- Verify derived producers contain no physical copies of raw `document.json` or
  `conversion_pages.json`, while wrong, missing, or corrupt raw seals are rejected.
- Verify normal immutable reuse consults seal digests without rereading all payload
  bytes. Retain a separate deep-audit command that verifies every byte.
- Verify interruption/restart at load, transform, serialization, and publication
  boundaries without duplicate terminal records.
- Reconcile the 24 GB composition report exactly to filesystem byte counts.
- Replay K2 downstream stages from sealed evidence only and record wall/CPU time,
  peak RSS, I/O, output bytes, and counts per substage.
- Run focused tests, then:

```bash
make check
git diff --check
```

No validation may invoke Docling, a model, or a source PDF without separate approval
for a final end-to-end confirmation after the sealed-evidence gate passes.

## Acceptance criteria

- The 22.5 GB record is exactly explained by field and consumer; unexplained bulk is
  not accepted as an implementation detail.
- Heading alignment is indexed and scaling tests reject the former quadratic-like
  behavior.
- Feature seeds build once, and cheap outline/input failures occur before expensive
  traversal.
- Derived publications reference sealed raw evidence and no longer multiply the two
  largest files across producer identities.
- Normal reuse does not copy, parse, or rehash unchanged multi-GB payloads; a deep
  integrity audit remains available.
- A hierarchy-only edit reuses conversion, routing, tables, and mapping exactly.
- The K2 sealed-evidence replay meets Gate A budgets and, at minimum, no individual
  downstream stage exceeds 30 minutes, total downstream critical path is under 60
  minutes, and peak RSS stays below 16 GiB on this host. Stop for review rather than
  silently relaxing a bound.
- The retained artifact tree has a measured amplification ratio and no unowned 24 GB
  compatibility copy.
- The maintained MVP has one current schema per owned artifact and no historical
  compatibility code or duplicate legacy downstream data. Docling and table outputs
  are compared semantically, but an explained, tested change is allowed rather than
  hidden behind compatibility behavior.
- Any substage over 10 minutes reports throughput and ETA instead of appearing hung.
- A test or replay whose elapsed time or stable ETA breaches its named budget is
  stopped safely and reviewed rather than allowed to run to an hours-long failure.
- Full repository validation and a separate maintainability/recovery review pass.
- Task 03H restarts only after the user reviews this outcome, approves Task 03H.1
  closure, and separately approves the new Task 03H execution boundary.

## Outcome

Task 03H.1 explains and removes the 24 GB replay amplification, replaces repeated raw
views with closed owner references, restores linear hierarchy scaling, streams large
candidate publication, makes ordinary restart lookup subsecond on the measured K2
seal, preserves an explicit full-byte audit, and retains crash-inspectable attempts.
The full K2 hierarchy proof completed within the accepted time and memory limits.
Gate B's performance and recovery evidence remains accepted. Gate C completed the
human-ownership refactor, deterministic identity refresh, full repository gate, and
independent cross-owner recovery review. The user approved the reviewed scope for
local commit and closed Task 03H.1 on 2026-08-19. Task 03H remains separately paused
until the user approves its new full-corpus execution boundary.

## Non-goals

- running missing Docling conversions, processing source PDFs/models, or assembling
  the collection before the sealed-evidence implementation and replay gates pass;
- rerunning K2 Docling conversion or any PDF/model work;
- modifying or deleting valid sealed Docling evidence;
- deleting any superseded downstream target before its validated replacement and
  exact deletion manifest exist;
- retaining historical downstream schemas, compatibility aliases, dual readers or
  writers, or duplicate regenerated data after the MVP cutover;
- changing hierarchy, table, or reference semantics merely to reduce bytes;
- choosing a storage format before the access/byte inventory;
- parallelizing a superlinear or memory-amplifying implementation to hide its cost;
- accepting a five-hour document because it has many pages; or
- freezing Task 03H or beginning Task 04.
