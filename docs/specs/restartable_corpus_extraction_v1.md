# Restartable Corpus Extraction Contract v1

## Status and scope

This specification freezes Task 03F.1's two-stage machine contract. It defines
records and validation; it does not implement extraction, delete historical
code, approve a real-source smoke, or run a PDF. Task 03F.2 owns stage-one
implementation and Task 03F.3 owns corpus accounting, indexing, and resolution.

The production scope is the manifest-ordered 35 `model_corpus` records in
`brisbane_baylands_2025_deir_sources_v1`. A fixture, engineering smoke, Task 03G
pilot, or Task 03H execution has a separate typed scope identity and cannot
claim production completion merely because it references the production
`extraction_id`.

## Why two stages

A complete PDF is the smallest source transaction that preserves Docling's
document context, table-family behavior, hierarchy evidence, and exact source
accounting. Page batches are bounded execution units only. Publishing pages as
independent checkpoints would make document completion ambiguous and could join
incompatible parser state. A database or workflow engine is unnecessary for 35
documents: immutable directories, typed JSON records, checksums, and atomic
rename provide inspectable restartability with less hidden state.

Stage one independently publishes each complete document candidate. After every
source in one declared run scope has a terminal accounting row, stage two seals
one corpus target index over eligible successful candidates and appends
cross-document resolutions against stable Task 03E.5 mention IDs. Stage two
never rewrites a stage-one byte.

```text
sealed manifest + production contract
              |
      manifest-selected documents
       /       |       \
 stage-one  stage-one  stage-one     complete-PDF transactions
       \       |       /
        exact scope accounting       control record
                 |
        sealed corpus target index   control/derived index
                 |
      immutable corpus resolutions   derived records
                 |
          candidate handoff          control record, not Task 04 acceptance
```

## Identity model

### Production extraction identity

The production `extraction_id` is `exv1-` plus the lowercase SHA-256 of the RFC
8785 serialization of the identity preimage, excluding `extraction_id` and
`identity_sha256`. The preimage has these closed sections:

1. `production_scope`: release ID, manifest path and checksum, release-completion
   path and checksum, exact ordered source IDs, and the RFC-8785/SHA-256 digest
   of ordered `{source_id, sha256, pdf_page_count}` records. The checked fixture
   pins 35 sources and digest
   `a1028e3f7da542b572ec5de7f6724900b43f90ad48f671c200d9ef0777b8706e`.
2. `producer_contract`: Docling pipeline/backend, effective semantic options,
   package versions, model commits and file hashes, routing/table/cleanup/family
   policies, configuration schema, and an ordered owned-code inventory.
3. `canonical_contract`: canonical v1, semantic v2, and cross-reference v3
   schemas; mapping, ID, order, and serialization policies; and owned code.
4. `hierarchy_contract`: maintained Docling hierarchy options, correction
   policy/schema/code, and the rule that Appendix P's bounded authorization is
   document-specific evidence rather than corpus-wide acceptance.
5. `cross_reference_contract`: accepted Task 03E.5 pattern-policy v2,
   five-page table window, zero derived figure aliases, source-manifest digest,
   specification/schema/configuration, and owned code.
6. `corpus_workflow_contract`: this specification, schema, state machine,
   publication versions, and output-affecting workflow code.

Every owned-code inventory contains ordered relative path and checksum pairs as
well as its bundle digest. Git commit, dirty state, timestamps, host name,
measured duration, and review renders are provenance, not semantic identity.
Operational controls belong to a subordinate run-scope identity unless changing
them can change output bytes; any such output-affecting control must also be
promoted into the production preimage.

### Subordinate identities

Typed prefixes prevent scope impersonation:

| Role | Prefix | Meaning |
| --- | --- | --- |
| production semantic contract | `exv1-` | the exact 35-source output contract |
| fixture/smoke/pilot/full execution scope | `scopev1-` | declared ordered subset and operational policy |
| document transaction | `txv1-` | one source, attempt number, and stage-one inputs |
| document candidate | `docv1-` | completed stage-one managed bytes |
| corpus target index | `idxv1-` | eligible candidate set and ordered index bytes |
| corpus resolution | `resv1-` | index plus immutable stage-one mention inputs |
| candidate handoff | `handoffv1-` | completed control-record set and policy |

Production identity defines intended semantics; Task 03H later records execution
of all 35 sources. The identity fixture makes no execution or terminal claim.

## Stage one

### State machine

Each attempt writes append-only events with contiguous sequence numbers:

```text
selected -> running -> complete
                    -> complete_with_warnings
                    -> failed_retryable
                    -> failed_terminal
                    -> cancelled
```

Only `complete`, `complete_with_warnings`, and `failed_terminal` are terminal for
scope accounting. Retrying `failed_retryable` or `cancelled` creates a new
transaction with an incremented attempt number; it never edits an earlier
attempt. A successful document completion exists only for a complete PDF and
must be the last candidate-owned record written before atomic publication.
First-N or page-subset diagnostics are explicitly incomplete and cannot publish
a document completion or enter a corpus index.

Docling status is preserved separately. Publication requires raw status
`SUCCESS`, zero unaccepted structured errors, exact page accounting, all
project validators, and a checksum-closed managed file set. `PARTIAL_SUCCESS`,
`FAILURE`, `SKIPPED`, timeout, or a non-raising result is attempt evidence only.

### Responsibility interfaces

The stage-one application shell composes, without absorbing, these owners:

- manifest source selection and verification;
- baseline and hierarchy-enabled producer conversion;
- explicit hierarchy correction/disposition;
- core canonical construction;
- semantic structure materialization;
- Task 03E.5 document-local mention and resolution policy;
- identity derivation, validation, publication, and reuse.

Every boundary consumes a verified completion plus inventory and produces a
typed result. Appendix P's accepted bytes are the offline preservation oracle:
Task 03F.2 must compare new outputs to the frozen candidate after only the
contract-declared identity/namespace normalization. No new Appendix P PDF run is
authorized for that proof.

### Publication and reuse

Work occurs below an attempt directory. Publication validates content, writes
the managed inventory, writes completion last, and atomically renames into an
absent final directory. Reuse requires identity, completion, inventory,
checksums, exact managed-file closure, source identity, full-page accounting,
and upstream seals to verify. Stale or partial destinations fail closed. Failed
work is retained without a completion marker.

## Scope accounting

A run-scope record declares `fixture`, `engineering_smoke`, `representative_pilot`,
or `production_full`. Its ordered sources must be an exact ordered subset of the
production manifest; only `production_full` may contain all 35 and reference the
production execution role. Accounting contains exactly one row per declared
source and recomputed counts by terminal disposition. It can complete only when
every row is terminal.

Successful rows reference a verified document completion and candidate.
Terminal failures retain source identity, attempt evidence, and failure class but
cannot name a completed candidate. Accounting completion does not imply index,
resolution, handoff, hierarchy quality, or Task 04 acceptance.

## Sealed corpus target index

Only checksum-verified `complete` or `complete_with_warnings` stage-one
candidates in the completed scope accounting are eligible. Failed sources remain
in a separate unavailable-source catalog so resolution can distinguish
`target_source_failed` from absence or an external document.

Index entries are ordered by normalized alias, target type, manifest source
ordinal, target ID, then alias ID. Duplicate evidence for one alias-target pair
collapses; the same lookup key across different targets remains an explicit
collision and never becomes a confident link. Completion binds the exact
accounting record, ordered eligible candidate completions, unavailable-source
catalog, entry count, serialized index checksum, inventory, and index ID.
Any changed candidate or accounting byte invalidates the index.

The corpus index is distinct from Task 03E.5's document-local
`support/cross_reference_target_index.json`.

## Immutable second pass

The second pass covers each stage-one mention with status
`deferred_cross_document` exactly once. It references the stable v3 mention ID,
source candidate completion and inventory, corpus index completion, lookup key,
ordered candidates, evidence, and disposition. It does not copy or modify the
stage-one mention.

Zero, one, or multiple candidates imply unresolved, resolved, or ambiguous.
Missing/failed targets use explicit `target_not_in_scope`,
`target_source_failed`, or `target_unavailable` reasons grounded in accounting
and the unavailable-source catalog. Named documents outside the sealed corpus
remain terminal external records and do not enter this pass. Resolution
completion binds exact input candidate bytes, index completion, output digest,
counts, inventory, and byte-identical before/after stage-one inventories.

## Handoffs

These records are independent and ordered:

1. per-document completion;
2. scope-accounting completion;
3. corpus-index completion;
4. resolution completion;
5. candidate handoff;
6. later Task 04 freeze/acceptance.

A handoff declares its blocking policy. It may be `ready` only when its required
document dispositions and all three corpus control completions verify. It
explicitly records `task04_status: not_evaluated`; Task 03F cannot issue a Task
04 freeze.

## Cache and invalidation

| Stage | Reuse key | Reuse proof | Invalidated by |
| --- | --- | --- | --- |
| producer | source + models + effective parser/table options + owned code | producer completion, inventory, exact files | any bound input/code byte |
| hierarchy | producer + policy/schema/config/code + document disposition | correction completion and authorization | producer or policy evidence |
| core canonical | producer + mapping/schema/config/code | candidate completion and exact inventory | any upstream or mapping change |
| semantic/local references | canonical + hierarchy + v2/v3 policy/schema/code | candidate completion, supports, exact inventory | any upstream/policy change |
| scope accounting | scope identity + terminal rows | exact row closure and recomputed counts | source order or terminal row change |
| corpus index | accounting + eligible candidate completions | ordered index digest and inventory | any accounting/candidate byte |
| corpus resolution | index + stable mention inputs | exact coverage, output digest, immutable inputs | index or stage-one byte change |
| handoff | accounting + index + resolution + policy | every referenced completion | any prerequisite or policy change |

## Resources, cancellation, and observability

Run-scope configuration explicitly bounds document concurrency, page batching,
stage batch sizes, queues, device, CPU threads, memory and storage estimates,
cooperative Docling timeout, outer process deadline, cancellation grace, and
retry counts. Default document concurrency is one. Multiplying document workers
by inference threads requires an explicit bound.

Docling `convert_all(..., raises_on_error=False)` may be used as an in-process
iterator, but it is not a checkpoint system. Current Docling document
concurrency is experimental; page and stage batches affect memory and throughput.
`document_timeout` is cooperative at pipeline control checkpoints, at latest
between batches, and cannot preempt an in-flight native or model call. It is
not a hard kill. A hard deadline therefore requires one-document process isolation. Profiling is
enabled for corpus evidence, but timings and host measurements remain
non-identity observability records.

Persist structured progress, raw Docling status/errors, stage timings, warning
and failure categories, attempts, retries, peak memory, output bytes, and
heavy-tail summaries. Logs never substitute for typed completion records.

Maintained sources consulted 2026-08-03:

- [DocumentConverter API](https://docling-project.github.io/docling/reference/document_converter/)
- [Batch conversion example](https://docling-project.github.io/docling/_generated/examples/batch_convert/)
- [Pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/)
- [Accelerator guidance](https://docling-project.github.io/docling/usage/gpu/)
- [Docling CLI](https://docling-project.github.io/docling/reference/cli/)

## Commands

Task 03F.1 implements offline fixture validation:

```bash
er-commons extraction validate-contract \
  --schema benchmarks/er_bench/schemas/corpus_extraction/v1/records.schema.json \
  --fixtures benchmarks/er_bench/fixtures/corpus_extraction/v1
make validate-extraction-contract
```

Task 03F.2 adds the document command with required paths and no Appendix P
default. Later runtime commands remain reserved for Task 03F.3:

```bash
er-commons extraction run-document --run-spec PATH --source-id SOURCE_ID
er-commons extraction run-scope --run-spec PATH
make run-extraction-scope RUN_SPEC=PATH
```

The run specification declares `engineering_smoke`, `representative_pilot`, or
`production_full`; the same entrypoint validates role-specific authority. Task
03F.3 may add named Make aliases, but none may infer a source or scope.

## Removal proof

Before deleting a file, Task 03F.2 must show: no live CLI/import caller; no
accepted identity inventory requires it; immutable artifacts remain verifiable;
replacement tests cover its accepted behavior; and the offline Appendix P
comparison is exact. This presently identifies
`cross_reference_materialization` as a candidate, not an authorized deletion.

## Executable contract boundary

The JSON Schema owns closed record shapes and typed namespaces. The offline
Python validator owns RFC-8785 identity derivation, legal state transitions,
full-document completion, exact scope closure, target eligibility and ordering,
second-pass coverage and immutability, prerequisite invalidation, and handoff
ordering. Fixtures are synthetic and make no real execution claim. The separate
production identity preimage pins the 35-source contract without claiming that
Task 03H ran it.
