# Task 03F: Make Two-Stage Corpus Extraction Restartable

Status: **provisional**. Revise this contract from the accepted Tasks
03E–03E.3 outcomes before activating it.

## Abstract

Extend the accepted single-document producer, semantic-structure materializer,
and cross-reference pilot into a manifest-driven, resource-bounded workflow for
the 35 checksum-pinned model-corpus PDFs. Make each document's first-stage
extraction an independent transaction. After every source reaches an explicit
terminal state, seal a corpus target/alias index and run an immutable second
pass that resolves cross-document reference mentions. Add fault isolation,
cache validation, atomic publication, bounded concurrency, retry
classification, and separate machine records for document completion,
all-source accounting, and candidate handoff. Test the workflow on fixtures and
approved pilot inputs; do not run the full corpus.

## Goal

Make a long, heterogeneous local extraction job safe to stop, inspect, resume,
and verify while preserving the distinction between per-document production,
corpus-wide cross-reference resolution, producer handoff, and Task 04's later
acceptance freeze.

## Inputs

- accepted Tasks 03C.1, 03D.1, and 03E–03E.3 implementations and contracts
- the sealed Task 02 source manifest filtered to 35 `model_corpus` records
- per-document conversion, canonicalization, semantic-structure, label, alias,
  mention, and within-document-resolution commands
- Docling's maintained
  [batch conversion](https://docling-project.github.io/docling/_generated/examples/batch_convert/),
  conversion-status, timeout, batching, profiling, and accelerator APIs
- local machine and external-volume capacity observations

## Outputs

- a package-backed corpus extraction command driven only by the sealed manifest
  and a frozen corpus configuration
- one corpus-scoped `extraction_id`, deterministically derived from the ordered
  35-source scope plus parser, model, configuration, canonical-schema,
  semantic-structure, resolution-policy, and code identities
- distinct producer-run and per-document transaction/completion identities
- an explicit per-document stage-one state machine and progress record
- atomic stage-one publication of hierarchy, printed-label evidence and
  resolution, aliases, reference mentions, and within-document resolutions
- a sealed, checksummed corpus target/alias index built only after all sources
  have explicit terminal states
- an immutable second pass that publishes cross-document resolution records
  without modifying stage-one document candidates
- stage-specific cache keys, retry classes, bounded resource controls, and
  relative persisted paths
- separate machine records for:
  - each document's terminal state;
  - all-source accounting;
  - target-index completion;
  - cross-document-resolution completion; and
  - producer candidate handoff
- tests for resume, stale cache, partial output, retry, no-clobber,
  target-index invalidation, second-pass immutability, and accounting behavior

## Research / learning checkpoint

Profile the actual stage boundaries and resource shape rather than treating the
workflow as homogeneous "seconds per page." The outcome must explain:

- **The document is the stage-one transaction and fault-isolation unit.**
  Arbitrary partial-page publication creates ambiguous hierarchy, labels, and
  provenance.
- **Cross-document resolution is a corpus operation.** A reference target may
  not exist until every document has either published stage one or recorded an
  explicit terminal failure.
- **The second pass is append-only.** Corpus resolution records may point to
  immutable per-document candidates but may not rewrite them.
- **Cache correctness is stage- and lineage-based.** Source checksum and every
  semantic contract that can change an output belong in the appropriate key.
- **Restartability requires verification before skipping.** Directory
  existence, filenames, and modification times are not completion evidence.
- **Failure accounting and acceptance are different.** A failed source can be
  fully accounted for without being a successful extraction. All-source
  accounting, producer handoff, and Task 04 acceptance must have distinct
  records.
- **Document costs are heavy-tailed.** Report distributions and outliers for
  conversion, table work, serialization, and the corpus passes.
- **Page renders are review cache.** They are regenerable and excluded from
  canonical identity and producer-completeness claims.

## Plan / spec requirement

Freeze a two-stage batch plan before implementation. It must define:

1. the complete `extraction_id` inputs and permitted subordinate identities;
2. stage-one document states, temporary/final paths, cache keys, and atomic
   publication;
3. terminal success and failure states and exact all-source accounting;
4. target/alias index inputs, sealing, validation, and invalidation;
5. cross-document-resolution inputs, unresolved reason codes, output paths,
   and the no-mutation invariant;
6. separate completion and handoff records, none of which claim Task 04
   acceptance;
7. failure categories, retry bounds, timeout, cancellation, and interruption
   behavior;
8. concurrency, page-batch, thread, device, queue, memory, and storage limits;
9. structured progress, timing, resource, warning, and error logs;
10. requested review-cache generation and cleanup; and
11. exact Make/CLI commands for bounded pilots and the later full run.

Use narrow project glue around maintained package APIs. Do not introduce a
general workflow engine, service queue, or database scheduler for this local
35-document job.

## Review pass

- **Identity:** one corpus identity governs all accepted stages without
  conflating producer runs or transactions.
- **State correctness:** every transition and completion claim has a
  mechanically verifiable artifact basis.
- **Stage isolation:** second-pass resolution cannot mutate or silently replace
  stage-one candidates.
- **Failure containment:** one failed appendix cannot corrupt or erase completed
  documents or disappear from corpus accounting.
- **Resource safety:** concurrency and queues are bounded from measured
  evidence.
- **Operational simplicity:** the workflow remains understandable from code,
  manifests, and logs without an orchestration service.

## Validation

- Run multi-document tests on tiny fixtures or approved bounded inputs.
- Simulate interruption before and after stage-one atomic publication.
- Verify matching complete outputs are checked and reused.
- Verify stale, checksum-mismatched, partial, and conflicting outputs stop or
  enter the specified recoverable state.
- Verify the target index cannot seal before all sources reach terminal states.
- Verify any changed stage-one candidate invalidates the target index and
  second-pass result.
- Verify second-pass publication leaves stage-one bytes and checksums unchanged.
- Verify missing or failed targets produce explicit unresolved reason codes.
- Verify exact all-source accounting can complete while candidate handoff
  remains blocked under the frozen policy.
- Verify page-render cache is unnecessary for canonical validation or
  completeness.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- The workflow consumes exactly the 35 ordered manifest records and checksums
  under one declared corpus extraction identity.
- Per-document stage-one work is isolated, restartable, and atomically
  published.
- The sealed target index and immutable resolution pass are reproducible and
  independently restartable.
- Cache reuse depends on verified stage inputs and identities.
- Every source reaches an explicit terminal state; no failure is silently
  omitted or represented as success.
- Document terminal state, all-source accounting, candidate handoff, and the
  later Task 04 freeze remain distinct.
- Retry, timeout, concurrency, and memory controls are explicit and bounded.
- The implementation remains narrow and package-backed.
- No full-corpus conversion begins.
- The outcome requests user review before Task 03G.

## Non-goals

- the representative pilot or full 35-document run
- accepting or freezing the corpus for benchmark use
- distributed or cloud orchestration
- automatic repair of deterministic parser or hierarchy failures
- final human usability decisions
- page renders as release artifacts
- retrieval, generation, or evaluation
