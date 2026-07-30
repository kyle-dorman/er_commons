# Task 03D.1: Rewrite the Canonical Materializer for Human Ownership

Status: **complete 2026-07-30; human-owned rewrite is semantically equivalent
to the Task 03D reference**.

## Abstract

Replace the completed Task 03D MVP materializer with readable, typed,
responsibility-specific code that a new maintainer can understand, edit, test,
and debug without tracing one 900-line record-building function. Preserve the
completed Task 03D candidate as an immutable behavioral reference. Accept the
rewrite only after an independent record-level comparison finds no unexplained
semantic change.

This is a maintainability rewrite, not a canonical-policy revision. Source
selection, producer selection, traversal, table cleanup, record fields,
ordering, IDs, warnings, schema, validation, candidate identity inputs, and
publication policy remain unchanged.

## Goal

Make the Task 03D canonicalizer easy to navigate and diagnose. The public
runner should read as a short sequence of named stages. Intermediate state
should have named types. Each record family and artifact concern should have
one obvious owner. Failures should name the violated invariant and enough
context to locate the source record.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/documentation.md`
- `tasks/sprint2/03d_materialize_canonical_records.md`
- the current Task 03D implementation and its 139-test passing baseline
- the completed non-release reference candidate:

```text
pipelines/brisbane_baylands/task_03d_canonical_records/
  exv1-9e33eb783b4145fa25065121de851d9055dfd6275066dcd80243ecde3b321774/
```

## Outputs

Tracked:

```text
src/er_commons/canonical_extraction/
tests/test_canonicalization_*.py
tests/test_canonical_extraction_tables.py
tasks/sprint2/03d1_rewrite_canonical_materializer.md
```

External:

```text
pipelines/brisbane_baylands/task_03d_canonical_records/<new-candidate-id>/
pipelines/brisbane_baylands/task_03d1_rewrite_review/<comparison-id>/
```

The reference candidate and Task 03D mapping/configuration policy remain
unchanged.

## Research / learning checkpoint

Use a functional-core/orchestration-shell boundary:

- frozen dataclasses name validated runtime state and ID registries;
- JSON Schema remains the authoritative persisted-record shape contract;
- small `TypedDict` definitions may document internal JSON fragments where
  they materially improve static checking without duplicating the full schema;
- pure builders own one record family or one relationship;
- filesystem publication and Git inspection remain explicit edge operations;
- test seams stay narrow and concrete rather than becoming a dependency
  injection framework.

Python dataclasses derive ordinary initialization and representation behavior
from annotated fields, which makes them appropriate for small internal state
objects:
<https://docs.python.org/3/library/dataclasses.html>.
`TypedDict` describes dictionary-shaped values to static type checkers while
preserving plain runtime dictionaries:
<https://docs.python.org/3/library/typing.html#typing.TypedDict>.
Pydantic remains appropriate at untrusted configuration boundaries, but
duplicating the complete published JSON Schema as a second model hierarchy
would create two persisted contracts to maintain:
<https://docs.pydantic.dev/latest/concepts/models/>.

The plain-language lesson is that a type or module should reveal ownership. A
maintainer should be able to find page geometry, IDs, assets, content records,
observations, summary construction, validation, and publication without
following a shared mutable dictionary across unrelated policies.

## Rewrite contract

1. Keep the accepted Appendix P source, producer run, mapping policy, schema,
   configuration, traversal policy, cleanup behavior, and candidate scope.
2. Preserve the completed Task 03D candidate byte-for-byte as reference
   evidence. Never mutate or republish it.
3. Let the existing code-bundle digest produce a new candidate ID. Do not
   increment the semantic policy/configuration version for a behavior-preserving
   source rewrite.
4. Keep one public `canonicalize run-document` command and one Make target.
5. Reduce `materialize.py` to a readable application shell. Move asset
   registration, build context/IDs, content-record construction, observation
   construction, summary/manifest construction, and output writing into
   cohesive modules with narrow public surfaces.
6. Replace cross-stage bags of unrelated values with named frozen dataclasses.
   Use plain dictionaries only where they are the intentional JSON record
   representation.
7. Keep record-family builders explicit. Avoid a generic record factory,
   plugin registry, inheritance tree, workflow engine, or broad dependency
   injection container.
8. Replace large compound acceptance checks with named invariants that report
   the failed record family, expected value, and actual value.
9. Keep schema validation and cross-record validation as independent gates.
10. Keep completion-last, atomic no-clobber publication, failed-attempt
    retention, and checksum-verified reuse fail-closed.
11. Add a fake end-to-end materialization test that reaches publication without
    loading Docling, Camelot, models, or the real PDF.
12. Keep focused tests at responsibility-level boundaries. Tests may assert
    policy and serialized behavior, but should not reproduce private
    implementation steps.

## Equivalence gate

Build a new Appendix P candidate only after all offline gates pass. Compare it
with the completed Task 03D reference after normalizing only declared
identity-dependent values:

- replace the old and new extraction IDs with one comparison token in every
  canonical record, observation, mapping, manifest, and summary;
- ignore only project-code digest, Git state, extraction/identity digest,
  candidate-relative terminal hashes, and IDs derived from the extraction ID;
- require exact ordered JSON equality for every canonical collection,
  observation collection, and raw-mapping collection after normalization;
- require exact byte equality for generated clean-table and clean-cell assets;
- require exact external asset roles, paths, checksums, sizes, media types, and
  producers after ID normalization;
- require exact warning/error content and counts;
- require the same 222 pages, 3,706 blocks, 19 tables, 3,669 cells, 19
  families, 27 figures/images, 146 assets, 34 table-stage observations, and
  3,798 raw mappings;
- require identical invalid-provenance evidence and complete Docling text and
  furniture accounting;
- independently rebuild the new candidate in fresh staging and require every
  candidate-owned file to match byte-for-byte.

Write a compact machine-readable comparison report with compared paths,
normalization policy, old/new hashes, exact mismatch paths, timings, and final
status. If any non-declared semantic field differs, retain both candidates,
stop for user review, and do not mark Task 03D.1 complete.

## Validation

Before the live run:

- inspect module sizes, imports, public names, docstrings, and top-level call
  flow;
- run focused unit and fake end-to-end tests;
- mutation-test named count, text-accounting, table, geometry, and publication
  invariants;
- run `make fix`, `make check`, and `git diff --check`;
- confirm no production code retains the old monolithic record builder.

After the live run:

- confirm the reference candidate checksums remain unchanged;
- record fresh-build and checksum-reuse timings;
- run the independent semantic comparison and inspect any mismatches;
- independently rebuild all new candidate files and compare their bytes;
- verify a second invocation reuses without traversal or table rebuilding;
- preserve one simulated failure without a completion marker.

## Review pass

- **Readability:** can a maintainer follow preflight, identity, record
  construction, validation, and publication from the public runner?
- **Editability:** can one record family or invariant change without editing a
  central multipurpose function?
- **Debuggability:** do failures identify the responsible stage, record family,
  pointer or producer ID, expected value, and actual value?
- **Type boundaries:** are configuration, verified inputs, build context,
  records, and published JSON clearly distinguished?
- **Behavior preservation:** does comparison cover ordered records and
  lineage, not only aggregate counts?
- **Scope:** did the rewrite avoid changing Task 03D schema or policy and avoid
  activating Task 03E?

## Acceptance criteria

- The 1,255-line `materialize.py` and its approximately 900-line
  `_build_records()` function are replaced by cohesive human-owned modules and
  a short explicit runner.
- No new production module becomes a replacement monolith.
- Internal state and record collections have named typed boundaries.
- Named invariant failures provide actionable diagnostic context.
- Offline tests cover a complete fake run and failure-safe publication edges.
- The complete project check passes.
- The new live candidate is semantically equivalent to the Task 03D reference
  under the declared normalization.
- The old reference candidate remains checksum-valid and unchanged.
- Documentation routes future maintainers to the replacement and records why
  the new candidate ID is implementation-bound rather than a policy revision.

## Non-goals

- changing canonical schemas, fields, IDs, ordering, mapping, or validation
  policy;
- changing Docling traversal, table cleanup, family assignment, source or
  producer selection, warning policy, or geometry interpretation;
- correcting the retained invalid provenance entry;
- adding hierarchy, printed-page labels, cross-references, batching, retries,
  remote compute, OCR, VLM, LLM repair, retrieval, or evaluation;
- promoting the one-document candidate as a corpus release;
- activating Task 03E;
- committing or pushing changes unless separately requested.

## Outcome

Task 03D.1 is complete. The Task 03D MVP remains intact as immutable reference
evidence, while the production path now uses a responsibility-specific,
human-owned materializer. The schema, mapping policy, source/producer
selection, configuration, record fields, ordering, warnings, validation, and
publication behavior did not change.

The former 1,255-line `materialize.py` is now a 149-line application shell
whose public flow is visible directly: verify inputs, build identity, reuse or
reserve staging, build context, register assets, build content and support
records, validate and seal, then publish or preserve failure evidence. The
former approximately 900-line `_build_records()` function no longer exists.
Its responsibilities now have named owners:

- `context.py` owns immutable geometry, traversal, and deterministic ID maps;
- `assets.py` owns ordered asset registration and generated clean-table views;
- `content_records.py` owns blocks, tables, families, figures, images,
  synthetic sections, and page reading order;
- `support_records.py` owns documents, pages, observations, and explicit raw
  mappings;
- `record_sets.py` owns typed record-family boundaries;
- `candidate.py` owns named Appendix P invariants, schema and bundle gates,
  serialization, summary, inventory, and completion sealing;
- `provenance.py` owns valid-region projection and verbatim rejected evidence;
- `comparison.py` owns independent semantic promotion evidence.

No production construction module exceeds 455 lines. Raw-mapping roles are
explicit rather than inferred from ID substrings, page membership uses a named
page-ID index, and invalid provenance is returned as a typed projection rather
than accumulated through a caller-owned mutation. Named acceptance failures
now report the invariant, expected value, and actual value.

The input boundary retains the typed sealed manifest and selected source, and
reuses the producer's existing Pydantic models for summary, completion,
conversion, and page routes. Eleven unused eagerly loaded payloads were
removed. Table cleanup, parser, shape, geometry, CSV, and family evidence are
now named frozen fields rather than a raw-record escape hatch. Saved Docling
JSON intentionally remains plain preserved evidence, and the published JSON
Schema remains the single persisted canonical-record contract.

The completed human-owned candidate is:

```text
extraction_id:
  exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28
completion_record:
  pipelines/brisbane_baylands/task_03d_canonical_records/
  exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28/
  records/completion_record.json
```

Its new ID is caused by the existing code-bundle digest, not a semantic-policy
revision. The Task 03D configuration and mapping-policy version remain
unchanged.

Independent comparison against reference candidate
`exv1-9e33eb783b4145fa25065121de851d9055dfd6275066dcd80243ecde3b321774`
passed with 57 compared paths and zero mismatches. All 14 ordered JSONL
collections matched exactly after replacing only extraction-ID-derived
strings. Identity differed only in the declared project-code and derived hash
fields. Manifest, summary, warning/error, completion, and inventory
projections matched under their narrow declared hash normalization. All 38
generated clean-table and clean-cell assets matched byte-for-byte.

The durable comparison report is:

```text
pipelines/brisbane_baylands/task_03d1_rewrite_review/
  cmpv1-1b5a3ec1aba2f380b938de6cadde5383cffedbd6c3286fb79c4836d46d5de939/
  comparison_report.json
```

The accepted counts remain 222 pages, 3,706 blocks, 19 tables, 3,669 clean
cells, 19 table families, 27 figures, 27 images, 146 assets, 34 table-stage
observations, and 3,798 raw mappings. Text, furniture, document-index, table
mapping, and invalid-provenance accounting matched exactly. An independent
fresh staging build matched all 57 candidate-owned files byte-for-byte.

Measured fresh-build time improved from 4.22 seconds for the reference to 3.42
seconds for the rewrite. Checksum-verified reuse improved from 1.95 to 1.40
seconds. Timing is diagnostic rather than a semantic gate.

Offline coverage now includes the typed context and asset boundaries, input
and table models, content geometry, named candidate invariants, deterministic
serialization and sealing, semantic comparison mismatch paths, and a complete
fake application publication/reuse/failure path. Final validation passed:

```text
make fix
make check  # 154 passed
git diff --check
```

The reference candidate remains checksum-valid and unchanged. Task 03E now
points to the human-owned candidate and remains inactive pending user review.
