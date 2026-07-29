# Task 03C.1: Rewrite the Complete-Document Producer for Human Ownership

Status: **completed 2026-07-29; accepted as the human-owned Task 03C
implementation**.

## Abstract

Replace the completed Task 03C reference implementation with a readable,
typed, testable producer that a new maintainer can understand without first
reverse-engineering one large orchestration function. Preserve the accepted
Task 03C producer policy and immutable v1 artifact as the behavioral baseline.
Publish the rewrite under a new code-bound producer identity and accept it only
after an independent artifact comparison finds no unexplained semantic change.

This is a maintainability rewrite, not a parser experiment. Docling, PDFium,
the content router, Camelot, cleanup, footer ownership, family assignment,
source selection, and publication policy remain unchanged.

## Goal

Make the complete-document producer easy to read, test, diagnose, and extend
while retaining Task 03C behavior. The top-level runner should read as a short
sequence of named stages, persisted records should have typed contracts, and
each validation failure should identify the invariant that failed.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/documentation.md`
- `tasks/sprint2/03c_build_single_document_conversion.md`
- the current Task 03C implementation and its 103-test passing baseline
- the accepted immutable v1 producer:

```text
pipelines/brisbane_baylands/task_03c_single_document/
  prv1-1de6a628ed1aec3f97c2bc6380001b8d22b118641ebcb9d1be3808adee0ceec7/
```

## Outputs

Tracked:

```text
src/er_commons/document_extraction/
configs/brisbane_baylands_2025_deir_task03c_appendix_p_v2.json
tests/test_complete_document_*.py
tasks/sprint2/03c1_rewrite_complete_document_producer.md
```

External:

```text
pipelines/brisbane_baylands/task_03c_single_document/<new-producer-run-id>/
pipelines/brisbane_baylands/task_03c1_rewrite_review/<comparison-id>/
```

The v1 run and v1 configuration remain unchanged reference evidence.

## Research / learning checkpoint

Use a functional-core/orchestration-shell boundary:

- typed configuration and artifact validation are deterministic functions;
- conversion, routing, table execution, metrics, Git inspection, and
  filesystem publication are explicit edge operations;
- the public runner shows the stage sequence without embedding stage
  implementation details;
- test seams are narrow callables or protocols, not a dependency-injection
  framework.

Python's standard-library guidance recommends `subprocess.run()` for ordinary
child-process calls, so Git metadata collection must replace silent
`os.popen()` calls with checked, argument-list subprocess calls:
<https://docs.python.org/3/library/subprocess.html#using-the-subprocess-module>.
Use `typing.Protocol` only where structural typing makes a real external seam
clear:
<https://docs.python.org/3/library/typing.html#typing.Protocol>.
Use Pydantic models at JSON/configuration trust boundaries and plain frozen
dataclasses for internal runtime state.

The plain-language lesson is that types and modules should expose ownership.
They are not decorations: a maintainer should be able to locate source
verification, identity, conversion, routing, table reconciliation, and
publication without tracing a mutable dictionary through hundreds of lines.

## Rewrite contract

1. Keep the accepted Appendix P source, package versions, local models,
   backend, CPU/four-thread runtime, router thresholds, table configuration,
   durable asset policy, and no-timeout policy.
2. Preserve the v1 producer artifact and configuration byte-for-byte.
3. Increment the producer policy/configuration version because project code is
   identity-bound; never pretend rewritten code has the v1 identity.
4. Keep one public `documents run-complete` command and one Make target.
5. Make the public orchestration sequence visible and keep stage modules
   cohesive. Avoid a framework, registry, inheritance tree, or generic workflow
   engine.
6. Replace untyped cross-stage dictionaries with named Pydantic records where
   they are persisted and small dataclasses where they are internal.
7. Replace compound boolean validation with named checks that report the exact
   failed invariant.
8. Keep final publication atomic and no-clobber. Preserve failed staging
   evidence without a completion marker.
9. Keep checksum-verified reuse fail-closed, including identity, summary,
   completion, inventory, and exact on-disk file-set reconciliation.
10. Provide deterministic seams for converter construction, table execution,
    clocks, memory sampling, IDs, and Git state. Routine tests must remain
    offline and may not load models or process the real PDF.
11. Add one end-to-end fake-producer test covering preflight through atomic
    publication, plus focused tests for identity, conversion, table validation,
    reuse, failure preservation, and race-safe publication.
12. Remove the reference implementation only after the replacement passes all
    offline gates and the live semantic comparison.

## Equivalence gate

Compare the new complete-document run with v1 after removing only declared
volatile or identity-dependent fields:

- require exact source identity and 222-page conversion coverage;
- require exact normalized `document.json` and `conversion_pages.json`;
- require exact route records and route counts;
- require the same routed pages, zero-table mappings, logical tables, exact
  table-to-family pairs, clean CSVs, cells, and durable figure assets;
- require the same machine status, warning/error content, and publication
  invariants;
- treat timestamps, wall/CPU time, peak RSS, output byte counts, Git state,
  configuration/code identity, run IDs, and artifact-relative paths as
  declared non-semantic differences.

Write a bounded comparison report with old/new hashes and exact mismatch paths.
If any non-declared semantic field differs, retain both runs and stop for user
review without marking this rewrite accepted.

## Validation

Before the live run:

- run the focused complete-document tests;
- run `make fix`, `make check`, and `git diff --check`;
- confirm no production module imports the removed reference implementation;
- inspect module sizes, public names, docstrings, and the top-level call graph;
- mutation-test the named table and completed-run invariants with focused
  corruptions.

After the live run:

- confirm v1 checksums remain unchanged;
- run the same Appendix P source through the replacement;
- verify completed-output reuse without conversion;
- produce and inspect the independent semantic comparison report;
- simulate one bounded failure and confirm it cannot publish a completion
  marker.

## Review pass

- **Readability:** can a maintainer follow the run from source selection to
  publication and find each policy in one obvious module?
- **Testability:** do tests exercise public or responsibility-level boundaries
  rather than reproduce implementation details?
- **Failure safety:** are staging, failed-attempt, reuse, and publication-race
  behaviors explicit and fail-closed?
- **Behavior preservation:** does equivalence cover artifact semantics rather
  than aggregate counts alone?
- **Scope:** did the rewrite avoid changing parser, router, table, canonical
  extraction, or batch policy?

## Acceptance criteria

- The 634-line reference orchestrator is replaced by cohesive human-owned
  modules and a short explicit runner.
- Persisted stage records are typed and validation errors name failed
  invariants.
- Offline tests cover the full fake run and all destructive publication edges.
- The complete project check passes.
- The new live run is semantically equivalent to v1 under the declared
  normalization.
- The old immutable run remains unchanged.
- Documentation routes future maintainers to the replacement and records why
  its new producer identity is required.

## Non-goals

- changing Docling, Heron, PDFium, Camelot, router thresholds, cleanup, footer,
  family, or durable-asset behavior;
- resolving the repeated Docling list-parent warning;
- changing zero-table policy or interpreting table-of-contents structure;
- canonical record materialization or activating Task 03D;
- multi-document batching, concurrency, retries, scheduling, or remote compute;
- OCR, VLM, LLM repair, retrieval, generation, or evaluation.

## Outcome

Completed and accepted on 2026-07-29. The 634-line reference orchestrator was
removed from the production import path and replaced by responsibility-specific
modules for application sequencing, typed records, identity, conversion,
routing, tables, publication, services, configuration, and durable artifacts.
The public runner now exposes the complete stage order directly: preflight,
staging, conversion, routing, tables, reconciliation, and atomic publication.
Persisted producer-owned records use strict Pydantic contracts; internal run
state uses small frozen dataclasses; and expensive or nondeterministic edges
use one explicit `ProducerServices` record.

The rewrite replaced the table stage's compound boolean gate with named
invariants for page coverage, table counts, unique IDs, assignment coverage,
exact table-to-family pairs, summary counts, zero-table mappings, and review
derivative exclusion. Completed-run reuse similarly reports named failures for
identity, inventory, checksums, terminal records, source lineage, and the exact
managed file set. Git state now uses checked, shell-free `subprocess.run()`
calls instead of silent `os.popen()` calls. Failure attempts record real start
and finish timestamps, preserve partial work, strip invalid completion markers,
and publication races cannot overwrite a final directory.

The offline suite increased from 103 to 112 passing tests. New focused tests
cover configuration/source identity, total status mapping, canonical identity,
lineage pointers, table-invariant corruptions, completion/inventory corruption,
unrecorded files, failure preservation, publication races, one complete fake
publication, checksum-verified reuse, and a fake conversion failure. Ruff,
strict mypy across 44 source files, all tests, and `git diff --check` pass.

The accepted human-owned run is:

```text
producer_run_id:
  prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0
completion_record:
  pipelines/brisbane_baylands/task_03c_single_document/
  prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0/
  records/completion_record.json
```

It reproduced the reference run's 222 pages, 189/33/0 route counts, 27 assets,
19 logical tables, 19 exact table-to-family assignments, 19 families, 14
explicit zero-table mappings, 33 repeated Docling list-parent warnings, and
`complete_with_warnings` status. End-to-end wall time was 65.69 seconds versus
66.57 seconds for v1. Docling wall time was 47.52 versus 48.06 seconds; table
wall time was 12.69 versus 13.93 seconds. Peak RSS was 5,765,447,680 bytes
versus 5,917,294,592. A second invocation checksum-verified and reused v2 in
4.91 seconds without conversion or table parsing.

The independent report at:

```text
pipelines/brisbane_baylands/task_03c1_rewrite_review/
  v1_to_v2_prv1-93dfb032/comparison.json
```

records `semantic_match`. The raw Docling document JSON, conversion pages,
asset inventory, all 222 route records, route summary, table records, family
assignments, family definitions, and table-stage observation match byte for
byte. All 33 page results match after removing only `wall_seconds`; all 76
raw/clean CSV, cell, and table-record payloads match byte for byte. Conversion,
table, producer-summary, and completion records match after removing only the
declared identity, path, timestamp, resource, byte-count, and timing fields.

All 159 v1 inventoried files remain present and checksum-valid. Eight untracked
macOS `.DS_Store` files were added after v1 publication, so strict whole-tree
reuse correctly rejects that externally contaminated directory even though no
sealed producer file changed. The v2 run has no unrecorded files and passes
strict reuse.

The main learning is that human ownership comes from visible responsibilities
and executable invariants, not merely smaller functions. The rewrite is
accepted because a new maintainer can locate each policy and because the
artifact boundary proves the refactor did not silently change extraction.
Task 03D remains inactive pending revision from the reviewed producer artifacts.
