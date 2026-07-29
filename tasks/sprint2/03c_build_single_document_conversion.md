# Task 03C: Promote One Complete-Document Producer Run

Status: **complete 2026-07-29; awaiting user review before Task 03D**.

## Abstract

Promote the accepted Task 03A document-extraction implementation from a fixed
ten-page review pipeline into the smallest complete-document producer
boundary. Reuse the pinned Docling converter, sealed-source verification,
content router, and complete clean table pipeline. Verify one
manifest-selected `model_corpus` PDF, convert every physical page, route every
page, complete table reconstruction and complete-document family assignment
where applicable, and atomically publish one immutable task-scoped producer
run.

This task adapts and generalizes the accepted parser implementation. It does
not build a second parser adapter, materialize canonical records, freeze the
final extraction identity, or introduce corpus orchestration.

## Goal

Prove that the accepted Task 03A producer stack can process one complete source
document locally, reproducibly, and safely without pilot-only page selections,
baseline-comparison gates, hidden defaults, remote services, OCR, or
in-memory-only results.

## Accepted inheritance from Task 03A

Task 03A already implemented and accepted:

- `docling==2.115.0` and the locked unified Docling/Camelot environment;
- checksum verification for the sealed source manifest and selected source
  bytes;
- the verified local Heron and table-model inventory;
- the PyPdfium2-backed, native-text-only Docling converter on CPU with four
  threads;
- fail-closed disabling of OCR, TableFormer, VLM conversion, remote services,
  external plugins, picture description/classification, chart extraction,
  code/formula enrichment, and project-owned generative repair;
- raw lossless Docling JSON, conversion-page records, structured errors,
  warnings, timing, resource, configuration, environment, inventory, and
  manifest artifacts;
- the reviewed source-agnostic PDFium/Heron content router;
- the complete clean Camelot table pipeline, including raw and cleaned cells,
  cleanup evidence, footer parsing and ownership, table-family assignment,
  summaries, inventories, and manifests; and
- a package-backed CLI/Make path with fast project-owned tests.

Task 03C must reuse these boundaries. It may extract small reusable functions
or replace pilot-specific configuration types, but it must not reimplement
Docling conversion, PDF parsing, layout inference, table reconstruction,
cleanup, footer ownership, or family assignment.

Pilot-only behavior to remove from the production path includes:

- the fixed six ranges and ten selected pages;
- literal expected range names and page-route assertions;
- comparison against the old Task 03A baseline;
- Task 03A acceptance and timing-comparison gates; and
- durable full-page renders, diagnostic HTML/Markdown, table crops, and debug
  images as required extraction outputs.

The accepted Task 03A roots remain immutable comparison evidence.

## Pre-activation decisions

### Exact source

The user approved this complete manifest-selected source on 2026-07-29:

```text
source_id: deir_appendix_p
official_title: Appendix P - Water Supply Assessment (PDF)
source_role: model_corpus
pdf_page_count: 222
byte_size: 6528561
sha256: 2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1
source_manifest_warnings: []
```

The selection is deliberately larger than the four-page size-minimizing
candidate while remaining bounded for the first complete-document run. A
read-only native-text screen found strong text coverage, with only one page
lacking native text, and identified 17 pages with substantial aligned numeric
content. Visual inspection of physical page 108 confirmed a large ruled table
and a chart, so this source can exercise table, figure, and image-asset
boundaries. The accepted conservative numeric router did not classify any page
as a full-page numeric route during this screen. Table routing is therefore
expected to depend on Heron layout observations, but the exact route count
remains an execution result rather than a task assertion.

Do not silently substitute another document if this source fails native-only
preflight or conversion. Preserve the failure evidence and stop for user
review.

### Producer scope

Task 03C includes full-document routing and the complete clean table stage, not
Docling alone. This follows the Task 03B ownership contract: Docling table
regions are observations, clean Camelot output supplies canonical table
content, and table-family membership may be finalized only after the complete
document has been processed.

If the selected document produces zero table routes, the run may still pass
when the routing observations and explicit no-table table-stage result cover
every page. Real clean-table-to-canonical mapping must then be validated from
accepted Task 03A evidence and a later representative full-document pilot; it
must not be simulated by promoting Docling tables.

### Artifact identity and lifecycle

Task 03C publishes task-scoped producer evidence, not the final candidate
extraction. The final `extraction_id` includes later canonicalization and
hierarchy code that does not exist yet and therefore cannot be frozen here.

Use a deterministic producer-run identity derived from the selected source
checksum, sealed-manifest checksum, effective Docling/model configuration,
routing/table configuration hashes, relevant package versions, and the
project-owned producer-code hash. Publish the completed run below a
task-scoped external root such as:

```text
pipelines/brisbane_baylands/task_03c_single_document/
  <producer_run_id>/
    records/
    documents/<source_id>/producer/
      docling/
      routing/
      tables/
    documents/<source_id>/assets/
      figures/
      images/
    logs/
```

Later tasks may copy or content-address these immutable producer artifacts into
an extraction-version-owned root only after validating their checksums and
identity inputs. Task 03C must not publish the Task 03B extraction completion
record.

### Review derivatives

Raw lossless producer JSON and required extracted figure/image binaries are
durable producer artifacts. Full-page renders, overlays, diagnostic HTML and
Markdown, ruling masks, table crops, and table-debug images are disposable
review derivatives. They do not participate in producer-run completeness and
must not be archived for every page.

Docling may create page images transiently when its internal pipeline or
element extraction requires them. A separately requested review page may be
exported under the Task 03B review-cache contract, never mixed into the
producer artifact inventory.

## Inputs

- completed and accepted Task 03A parser, routing, and table-pipeline code;
- completed Task 03B specification, executable schemas, ID rules, artifact
  layout, and machine-status policy;
- `tasks/sprint2/03a15_rewrite_document_parser_pipeline.md`;
- `tasks/sprint2/03b_define_canonical_extraction_contract.md`;
- `docs/specs/canonical_extraction_v1.md`;
- the sealed Task 02 `source_manifest.json`, completion record, and selected
  `model_corpus` source record;
- the selected checksum-pinned PDF;
- the accepted Task 03A model inventory and locally available model files; and
- current Docling maintainer guidance only where the accepted implementation
  does not already settle status, serialization, timeout, or image-lifecycle
  behavior.

## Outputs

Tracked:

- a short implementation plan and frozen selected-source record in this task;
- narrow production configuration and typed single-document orchestration that
  reuse `src/er_commons/document_extraction/` and
  `src/er_commons/table_extraction/`;
- one package-backed command for a manifest-selected complete document;
- fast offline tests using fixtures or fakes for all project-owned behavior;
  and
- an outcome and architecture walkthrough requesting review before Task 03D.

External:

- one atomically published task-scoped producer run;
- byte-preserved raw Docling `document.json` and required conversion-page
  producer records for the complete document;
- one conversion observation that maps Docling status into the Task 03B
  machine-status vocabulary while retaining raw status, errors, and warnings;
- page-complete routing observations;
- complete clean table-stage artifacts and complete-document table families
  for every routed page, or an explicit verified no-table result;
- extracted figure and image assets required by later canonical records;
- effective configuration, package/model/backend/device identities, source and
  manifest checksums, code identity, timings, counts, relative paths, and output
  checksums;
- a producer-run inventory and terminal completion record published last; and
- separate attempt/failure evidence that cannot be mistaken for a completed
  producer run.

No new parser dependency is expected. Any lockfile change requires a separately
documented compatibility reason and user review before the real run.

## Research / learning checkpoint

Start from a gap analysis between the accepted Task 03A implementation and the
Task 03B producer contract. Consult current primary documentation only for
unsettled production behavior rather than reopening accepted parser choices.

The outcome must explain:

- **Pilot code and production policy are different layers.** The accepted
  converter and router can be reused while fixed page ranges, expected routes,
  and baseline comparisons are removed.
- **The document is the publication unit.** Partial pages may be retained as
  failure evidence, but they cannot look like one completed document because
  hierarchy and table-family membership require complete scope.
- **Parser success and producer completion differ.** A serializable Docling
  result may still contain partial or stage-level errors. Raw status, project
  status, page coverage, table-stage coverage, and publication status remain
  separate.
- **Raw producer identity precedes canonical identity.** Immutable producer
  output can be validated and reused by checksum, but Task 03C cannot claim the
  final extraction identity before later canonicalization code is frozen.
- **Table ownership constrains sequencing.** Docling supplies table-region
  observations; only the complete clean table pipeline supplies table and cell
  content for later canonicalization.
- **Reviewability does not require permanent page renders.** Requested views
  can be regenerated from checksum-pinned sources and recorded configuration
  without multiplying corpus-sized extraction artifacts.
- **Atomic publication needs explicit failure evidence.** Temporary output,
  completed output, and attempt records have different semantics and paths.
- **Hardware is provenance.** CPU, thread count, library versions, model
  revisions, timing, and peak memory are recorded even when they do not enter
  the source checksum.

## Plan / spec requirement

Before editing implementation code, add a brief plan to this task that freezes:

1. the frozen `deir_appendix_p` source identity and selection rationale;
2. the exact Task 03A functions and modules reused without semantic change;
3. the pilot-only configuration and comparison behavior removed from the
   production path;
4. the complete-document page, routing, table-stage, and family-completion
   invariants;
5. the producer-run identity inputs and its distinction from `extraction_id`;
6. the raw Docling serialization and figure/image asset policy;
7. Task 03B machine-status mapping, partial-success rules, and fatal
   conditions;
8. temporary, attempt, final, completion, no-clobber, and verified-reuse
   semantics;
9. timeout, interruption, logging, timing, memory, and error records;
10. the CLI/configuration boundary, which must resolve a source ID through the
    sealed manifest rather than accept an arbitrary PDF path; and
11. fake/fixture seams that keep routine `make check` offline and model-free.

The top-level orchestration should remain a visible sequence:

```text
load and validate configuration
  -> verify release seal, selected source, and model inventory
  -> derive producer-run identity and reserve a temporary directory
  -> convert the complete document with the accepted Docling adapter
  -> route every converted page
  -> run and validate the complete clean table stage
  -> reconcile coverage, statuses, assets, and checksums
  -> publish the immutable final directory and completion record
```

### Activated implementation plan (2026-07-29)

1. Freeze `deir_appendix_p` exactly as approved above: 222 physical pages,
   6,528,561 bytes, SHA-256
   `2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1`.
   It remains the smallest approved source that is both bounded and capable of
   exercising prose, figure, image, and table observations.
2. Reuse `runtime.build_converter`, `runtime.assert_native_only`,
   `runtime.verify_model_inventory`, `pipeline.offline_docling_environment`,
   `pipeline.run_log`, `routing.page_features`, `routing.classify_page`,
   `routing.layout_table_regions`, `table_stage.build_table_request`, and
   `table_extraction.pipeline.run_table_extraction` without changing their
   accepted parser, router, reconstruction, cleanup, footer, or family
   semantics. Extract only narrow source/configuration adapters where the
   existing function signature is pilot-specific.
3. Keep the existing `documents run-review` path unchanged. The new producer
   path has one complete source and removes page-range selection, expected
   range names, expected routes, baseline comparison, Task 03A acceptance
   gates, timing comparison, and mandatory diagnostic/page-image export.
4. Require one raw Docling document and conversion-page set covering physical
   pages 1-222 exactly once; one routing observation per physical page; one
   complete clean table result per positive route; and, when tables exist,
   unique family assignment for every clean table after all routed pages have
   completed. A partial page set can be retained only as attempt evidence and
   cannot publish families or a completed producer run.
5. Derive `producer_run_id` from a canonical JSON payload containing the
   selected source checksum, sealed manifest and completion-record checksums,
   accepted runtime/effective option identity, model-inventory checksum,
   routing/detection/cleanup hashes, relevant package versions, and a
   path-and-content hash of project-owned producer code. Timestamps, hostnames,
   timings, output paths, and generated checksums do not enter the identity.
   This task-scoped ID is not, and does not claim to be, Task 03B's later
   `extraction_id`.
6. Save lossless Docling `document.json`, conversion-page records, and each
   available parser-derived picture crop under durable figure/image asset
   roots with checksums. Do not save full-page renders, HTML/Markdown,
   overlays, masks, ruling images, or table crops as producer-completeness
   artifacts. Existing clean-table debug images remain implementation output
   of the accepted table component but are explicitly excluded from the
   producer inventory and completion contract.
7. Preserve Docling's raw status and map `success` to `complete` or
   `complete_with_warnings`, `partial_success` to `partial`, and terminal
   failure statuses to `failed`. Any non-success raw status, conversion error,
   incomplete or duplicate page coverage, route mismatch, table-stage
   incompleteness, asset-write failure, or checksum/reconciliation failure is
   fatal to final publication. Source-manifest warnings alone may publish as
   `complete_with_warnings`.
8. Write first to a unique temporary directory below the task root. On failure
   or interruption, move recoverable evidence to `attempts/` and write a
   terminal attempt record; never create a final completion record. On success,
   write the artifact inventory, write `completion_record.json` last, and
   atomically rename the directory to `<producer_run_id>/`. Refuse conflicting
   final output. Reuse an existing matching run only after verifying its
   completion record and every inventoried checksum.
9. Record structured stage errors, raw warnings, logs, wall and CPU time, peak
   RSS, output bytes, package/runtime identity, and interruption/failure stage.
   The accepted in-process Docling call has no enforced wall-time kill; record
   that timeout policy explicitly, preserve `KeyboardInterrupt` attempt
   evidence, and leave process isolation and retry scheduling to later batch
   work.
10. Add `documents run-complete --config ...`. The typed checked-in config
    contains the frozen source ID and expected manifest identity; it never
    accepts an arbitrary PDF path. All persisted artifact paths are relative
    to `ER_COMMONS_DATA_ROOT`.
11. Inject converter, table-runner, clock, and memory seams at the orchestration
    boundary. Routine tests use tiny fake Docling results and temporary sealed
    manifests to cover status, page/routing/table reconciliation, identity,
    no-clobber, failure attempts, and verified reuse without network, model
    loading, or real PDF conversion.

## Review pass

- **Reuse:** production code reuses accepted Task 03A responsibilities instead
  of creating parallel conversion or table implementations.
- **Boundary discipline:** project code owns source selection, configuration,
  status, artifact naming, completion, and failure policy; maintained packages
  retain parser and table internals.
- **Failure safety:** interruption, partial conversion, table-stage failure,
  checksum mismatch, or conflicting output cannot publish a completed-looking
  document.
- **Configuration closure:** every behavior-affecting parser, model, router,
  table, cleanup, family, hardware, and serialization option is recorded.
- **Artifact lifecycle:** durable producer artifacts, canonical records, and
  disposable review derivatives remain distinct.
- **Handoff:** Task 03D can consume saved producer artifacts without invoking
  Docling or guessing table ownership, paths, statuses, or lineage.
- **Routine development:** tests do not need network access, model downloads,
  or real PDF conversion.

## Validation

Before the user-approved real run:

- test rejection of a missing, non-`model_corpus`, duplicate, curator-only, or
  checksum-mismatched source;
- verify the Task 02 completion seal and source-manifest checksum;
- test exact production option closure and all forbidden-feature assertions;
- test complete-document page reconciliation and reject partial-page family
  finalization;
- test zero-route and routed-table completion behavior;
- test conversion-status mapping and structured partial/failure records;
- simulate failure before and during publication and verify no final completion
  record appears;
- test that matching completed output is checksum-verified and reused while
  stale or conflicting output stops;
- test that persisted paths remain relative to `ER_COMMONS_DATA_ROOT`;
- test that extraction completeness excludes page renders and diagnostics; and
- confirm routine tests use no network, model download, or full conversion.

After explicit user approval:

- convert every physical page of the selected real document;
- reconcile source-manifest, Docling, routing, and table-stage page counts;
- verify all routed pages complete the clean table pipeline;
- verify table families, when present, are finalized over the complete
  document rather than a partial page subset;
- inspect the raw producer JSON and a small user-guided review-cache sample
  against the original PDF;
- interrupt or simulate a bounded failure without overwriting the successful
  run;
- rerun the same command and verify completed-output reuse; and
- report wall time, CPU time, peak RSS, output bytes, warnings, and errors.

Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- One approved, manifest-selected complete source is processed through a
  package-backed, typed, logged command.
- The production path demonstrably reuses the accepted Task 03A converter,
  router, and clean table pipeline.
- Source, manifest, model, configuration, code, and output identities are
  mechanically verified.
- Raw Docling output accounts for every expected physical page or the run
  publishes only an explicit non-success attempt.
- Routing observations cover every converted page, and every selected table
  route has a complete clean table-stage result.
- Table-family records, when present, use complete-document scope.
- Raw producer JSON, required figure/image assets, table artifacts,
  configuration, statuses, timings, errors, and checksums are durable.
- Page renders and diagnostic/debug derivatives are absent from extraction
  completeness and are generated only through the separate review cache.
- Final publication is atomic and no-clobber; verified identical output is
  reusable, while stale or conflicting output stops.
- No canonical records, final extraction completion record, or batch
  orchestration are implemented.
- Routine tests remain small and offline.
- The outcome explains the architecture and requests user review before Task
  03D is revised or activated.

## Non-goals

- changing the accepted Docling backend, Heron model, router thresholds,
  Camelot reconstruction, cleanup, footer ownership, or family rules;
- downloading or evaluating a new parser, model, or accelerator;
- canonical document, page, section, block, table, table-family, figure, image,
  asset, mapping, or cross-reference records;
- freezing the final extraction identity or publishing its completion record;
- processing more than one real source;
- multi-document scheduling, concurrency, retries, or corpus completion;
- permanent full-page render or diagnostic export;
- human visual-usability decisions;
- OCR, VLM, model-based repair, or LLM enrichment; and
- retrieval, chunking, generation, or evaluation.

## Outcome

Task 03C is complete. It promoted the accepted Task 03A producer stack into a
typed `documents run-complete` command for one manifest-selected complete
document. The production layer owns exact source selection, deterministic
producer identity, raw-status mapping, complete-document coverage, durable-only
asset export, table-stage reconciliation, failure attempts, atomic no-clobber
publication, and checksum-verified reuse. The existing Task 03A review command
and comparison gates remain separate and unchanged.

The published producer run is:

```text
producer_run_id:
  prv1-1de6a628ed1aec3f97c2bc6380001b8d22b118641ebcb9d1be3808adee0ceec7
completion_record:
  pipelines/brisbane_baylands/task_03c_single_document/
  prv1-1de6a628ed1aec3f97c2bc6380001b8d22b118641ebcb9d1be3808adee0ceec7/
  records/completion_record.json
```

Appendix P completed with raw Docling status `success`, zero structured
conversion errors, and exact 222-of-222 physical-page coverage. Docling took
48.06 wall seconds and 160.80 CPU seconds; the complete producer took 66.57
wall seconds, peaked at 5,917,294,592 RSS bytes, and published 159 inventoried
files totaling 376,605,398 bytes. It saved 27 figure assets. The captured
Docling warning, repeated 33 times, reported that a list-item parent was
reconstructed as a list group; it did not affect page coverage or terminal
status, so the producer status is `complete_with_warnings`.

Routing covered all 222 pages: 189 `no_table_route`, 33 `layout_regions`, and
zero `full_page_numeric`. The clean table stage processed all 33 positive
routes in 13.93 seconds and produced 19 logical tables with 19 unique family
assignments and 19 complete-document families. Fourteen routed pages produced
zero clean tables; these are explicit zero mappings and make the table stage
`complete_with_warnings`, not incomplete. No full-page images, diagnostic
HTML/Markdown, ruling masks, or annotated table images were retained.

The second identical command completed in 4.5 seconds by verifying the
completion seal and every inventoried checksum, without rerunning Docling or
Camelot. A bounded offline failure simulation preserved partial artifacts
under an attempt root with a failed attempt record and no completion marker.

A scoped independent review rejected two pre-acceptance published drafts while
the production invariants were tightened. The first retained a temporary table
execution path and staged summary status, and a publish-race failure could
have left a completion marker in attempt evidence. The second still compared
family memberships only as ID sets and did not cross-check all completion
identity fields during reuse. The corrected accepted run above
validates exact table-to-family pairs and source/status/checksum agreement in
addition to the earlier fixes. It
uses an execution-root override while persisting only its deterministic final
path, terminally reconciles its summary, strips invalid attempt completion
markers, validates the family file and symmetric memberships, uses RFC 8785
identity serialization without output-path or formatting inputs, and verifies
the complete on-disk file set during reuse. The earlier immutable drafts remain
external superseded evidence and are not the accepted Task 03C handoff.

The bounded visual review compared original physical pages 13 and 108 with the
saved producer assets. The page-13 map crop preserved its labels, inset,
legend, scale, and title. Page 108 preserved the chart crop, and its clean
Camelot Lattice table retained the visible 36-row, 11-column structure,
grouped header, and values. Poppler reported non-embedded Arial font warnings
while rendering the source review pages, but both review renders were legible.

The main learning is the policy/producer separation. Docling and Camelot still
own parsing; project code now owns whether a whole document is complete and
publishable. A successful parser status is insufficient without exact page,
route, table, family, asset, and checksum reconciliation. Conversely, a
routed region that maps to zero reconstructed tables is useful explicit
evidence rather than an invented table or an automatic document failure.
Producer identity can now be reused immutably, but it intentionally remains
distinct from the later canonical `extraction_id`.

Validation:

```text
make fix
make check
103 passed
git diff --check
passed

real complete-document run
published and checksum-verified

second identical invocation
verified reuse without conversion

bounded pages 13 and 108 visual review
passed
```

Task 03D remains inactive. The next decision is user review of this producer
boundary, warnings, zero-table mappings, and visual sample before revising the
Task 03D canonical-record contract from these actual artifacts.
