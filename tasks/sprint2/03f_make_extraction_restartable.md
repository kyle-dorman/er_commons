# Task 03F: Make Extraction Batch-Safe and Restartable

Status: **provisional**. Revise this contract from the accepted Task 03E outcome
before activating it.

## Abstract

Extend the validated single-document conversion and canonicalization stages
into a manifest-driven, resource-bounded workflow for the 35 checksum-pinned
model-corpus PDFs. Add document-level fault isolation, cache validation,
checkpointing, atomic publication, bounded concurrency, explicit retry
classification, and corpus-level progress/summary records. Test batch behavior
on small fixtures and already approved pilot inputs; do not run the full corpus.

## Goal

Make a long, heterogeneous local document-inference job safe to stop, inspect,
resume, and verify without a hidden workflow engine or treating directory
existence as proof of success.

## Inputs

- completed Tasks 03B–03E contracts and implementation
- the sealed Task 02 source manifest filtered to 35 `model_corpus` records
- per-document conversion, canonicalization, hierarchy, and validation commands
- Docling's current
  [batch conversion](https://docling-project.github.io/docling/_generated/examples/batch_convert/),
  [conversion status](https://docling-project.github.io/docling/reference/document_converter/),
  timeout, batching, queue, profiling, and accelerator guidance
- local machine and external-volume capacity observations

## Outputs

- a package-backed corpus extraction command driven only by the sealed manifest
  and extraction configuration
- an explicit per-document state machine and corpus progress record
- data-root-relative paths in every persisted record
- cache keys based on source and extraction identities
- bounded concurrency, memory-aware queueing, and timeout configuration
- atomic per-document publication plus corpus completion semantics
- deterministic retry classification and attempt records
- corpus summary and failure records
- tests for resume, stale cache, partial output, retry, no-clobber, and
  completion behavior

## Research / learning checkpoint

Profile the actual stage boundaries and resource shape rather than treating the
workflow as homogeneous “seconds per page.” Very large appendices, dense tables,
page rendering, layout batches, and serialization can have different memory and
runtime tails.

The outcome must explain:

- **The document is the natural transaction and fault-isolation unit.** Page
  checkpoints can aid diagnostics, but publishing arbitrary partial pages as a
  complete document creates ambiguous hierarchy and provenance.
- **Cache correctness is lineage-based.** A valid cache key includes source
  checksum and extraction-contract identity. Filenames, modification times, or
  a nonempty output directory are insufficient.
- **Restartability requires verification before skipping.** Resume logic must
  validate completion records and artifact checksums, not assume previous work
  succeeded.
- **Retry policy depends on failure class.** Resource exhaustion, interruption,
  and transient runtime faults differ from deterministic parser errors or
  contract violations. Retrying malformed content indefinitely is not
  resilience.
- **Document costs are heavy-tailed.** Mean throughput hides the scheduling and
  capacity risk posed by the largest appendices. Record distributions and
  outliers, not only corpus averages.
- **Concurrency trades throughput for failure blast radius.** More simultaneous
  pipelines increase model reuse and device utilization but also peak memory,
  I/O contention, and the amount of work lost on process failure.
- **Partial corpus success is not corpus completion.** Preserve successful
  document work and explicit failures, but publish the corpus completion marker
  only when every required source satisfies the frozen acceptance policy.
- **Missing documents confound LLM evaluation.** A silently partial extraction
  changes the retrieval corpus, so scores across runs no longer measure the
  same task even if prompts and models are unchanged.

## Plan / spec requirement

Freeze a batch-execution plan before implementation. It must define:

1. stage graph and document-level state transitions;
2. complete cache-key inputs and verification;
3. temporary and final paths plus atomic publication;
4. document and corpus completion records;
5. failure categories, retryable states, maximum attempts, and backoff;
6. timeout and cancellation behavior;
7. concurrency, page-batch, thread, device, queue, and memory limits;
8. structured progress, timing, resource, and error logs;
9. resume and stale-output behavior;
10. signal/interruption handling; and
11. exact Make/CLI commands for bounded pilots and the later full run.

Use simple project code plus Docling's maintained APIs. Do not introduce
Airflow, Prefect, Dagster, Celery, a database queue, or a general workflow
framework for this local 35-document job.

## Review pass

- **State correctness:** every transition and completion claim has a
  mechanically verifiable artifact basis.
- **Failure containment:** one failed appendix cannot corrupt or erase completed
  documents.
- **Resource safety:** concurrency and queues are bounded and configurable from
  measured evidence.
- **Reproducibility:** all attempts share recorded source/configuration identity
  and cannot silently mix extraction versions.
- **Portability:** persisted paths remain relative to
  `ER_COMMONS_DATA_ROOT`; local absolute paths may appear only in logs where
  clearly marked as runtime observations.
- **Operational simplicity:** the workflow remains understandable from code,
  manifests, and logs without an orchestration service.

## Validation

- Run multi-document tests on tiny fixtures or approved bounded pilot inputs.
- Simulate interruption before and after atomic publication.
- Verify matching complete outputs are checked and reused.
- Verify stale, checksum-mismatched, partial, and conflicting outputs stop or
  enter the specified recoverable state.
- Exercise retryable and deterministic failure classes.
- Verify the corpus completion record cannot publish with a missing or
  unaccepted document.
- Verify per-document timing and resource observations can be summarized without
  reading large raw artifacts.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- The workflow consumes exactly the 35 ordered manifest records and their frozen
  checksums.
- Per-document work is isolated, restartable, and atomically published.
- Cache reuse depends on verified source and extraction identity.
- Retry and timeout behavior are bounded and failure-class-aware.
- Concurrency and memory controls are explicit rather than inherited from
  mutable defaults.
- A corpus cannot appear complete while any required document is missing,
  partial, stale, or conflicting.
- The implementation remains narrow and package-backed.
- No full-corpus conversion begins.
- The outcome requests user review before Task 03G.

## Non-goals

- the representative production pilot or full 35-document run
- distributed or cloud orchestration
- dynamic autoscaling or a general workflow engine
- automatic repair of deterministic parser errors
- human usability decisions
- retrieval, generation, or evaluation
