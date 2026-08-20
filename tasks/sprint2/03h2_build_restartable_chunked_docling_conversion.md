# Task 03H.2: Build Restartable Chunked Docling Conversion

Status: **active for contract review and source-free work only**. Task 03H is paused
after Appendix G2's first clean Docling attempt was killed under system-wide memory
pressure. This task may create a branch, preserve and commit the already approved
Task 03H repair baseline, inspect code and sealed artifacts, and run offline tests.
It must check in with the user before any source-PDF read, Docling construction,
model execution, or live document publication.

## Abstract

Appendix G2 exposed a source-general conversion boundary failure. The clean
3,736-page conversion ran for 14,940.61 seconds, reached 13,907,099,648 bytes peak
RSS, and then received `SIGKILL` during a macOS jetsam event. The completion-last
conversion never sealed, the table stage never began, and the automatic retry
started the same monolithic work from scratch before it was stopped.

The current pipeline converts the complete PDF with Docling before it applies the
native-text table router. Docling table-structure extraction is disabled, and the
clean table pipeline owns canonical tables and cells, but Docling still retains
complete-document text, layout, reading order, figures, and provenance. Arbitrarily
splitting and concatenating final Docling JSON could lose cross-range text merges,
heading calibration, references, or boundary evidence.

This task designs, implements, and validates a conversion that is independently
sealed by document-driven page ranges and can resume from the first missing range.
It must prove that deterministic recomposition preserves the accepted semantic
contract before it is allowed to rerun Appendix G2. It also measures whether two
range workers improve throughput without exceeding the aggregate memory budget;
parallel execution is an evidence-based option, not an assumed default.

## Goal

Make large Docling conversion memory-bounded, interruption-safe, and optionally
parallel while preserving one complete, ordered, checksum-verifiable conversion
owner for existing routing and downstream consumers. A failed late range or merge
must not discard completed range work, and completion order must not affect bytes or
semantic records.

## Inputs

- the current approved-but-uncommitted Task 03H repairs, regenerated production
  configurations, and passing full validation baseline;
- sealed Appendix G1 conversion
  `dconv1-97a8d4048839d9ba26c78151d0446e1c1bbef9848183f1ce9b9140c92e4c3f68`,
  shared producer `prv1-159379eb52f63824b22b9ae529044c5c983aa5ef80abcf874502fe6c9e3c1b74`,
  and published document
  `docv1-54e6036f6c7caffc3d2a10fff0239f751b9af91ef9de3ee755e48f7873c9fdef`;
- the retained Appendix G2 failed attempt
  `txv1-770c721abbd9c1428db103d068e076733d6db1e3fb40fd8b9ec398da65f2aa04`
  and its unsealed conversion workspaces;
- the accepted content-parsing, conversion-seal, routing, table-continuation,
  record-mapping, and hierarchy contracts;
- the installed Docling, docling-core, and docling-ibm-models implementations; and
- Task 03H.1's accepted closed-reference, compact-alignment, resource-observation,
  and completion-last publication patterns.

All sealed inputs and retained failures are immutable. The task must not rewrite,
repair in place, or delete them.

## Outputs

- a dedicated `codex/` branch with the reviewed pre-experiment baseline committed;
- a written chunk/range identity and completion contract;
- deterministic range-plan records naming core pages, overlap pages, boundary
  evidence, source identity, converter identity, and stable range IDs;
- independently completion-sealed range bundles and one aggregate conversion seal
  that closes over their identities, inventories, and digests;
- a source-free G1 recomposition/equivalence report;
- if separately approved, a bounded G1 split-versus-contiguous conversion report;
- a source-independent, document-driven boundary selector with explicit hard-cap
  fallback and fail-closed seam diagnostics;
- a sequential-versus-parallel performance report that selects concurrency from
  measured throughput, peak aggregate RSS, swap, and failure behavior;
- focused interruption, corruption, ordering, overlap, seam, identity, and reuse
  tests; and
- a reviewed Appendix G2 execution plan followed by a separate user checkpoint
  before any G2 PDF/model run.

## Research / learning checkpoint

Before selecting the maintained design, inspect and explain:

1. Docling's installed `StandardPdfPipeline` page-range behavior, page assembly,
   reading-order pass, heading-hierarchy pass, image retention, and error semantics.
2. The installed reading-order implementation's actual context boundary. Current
   evidence says ordering, captions, and footnotes are page-local, while text merging
   can cross pages; this must be locked by tests rather than assumed stable.
3. `DoclingDocument` copy/add behavior, especially page dictionaries, body/furniture
   roots, child references, caption/footnote references, images, provenance, and
   non-tree cross-references. Its convenience methods are not accepted as a merge
   contract without closure tests.
4. The accepted project ownership split: Docling/PDFium/Heron owns native text,
   layout, reading order, figures, and provenance; clean Camelot owns canonical
   tables/cells; project logic owns routing, cleanup, table families, and semantic
   hierarchy.
5. Maintainer guidance and source, including:
   - <https://docling-project.github.io/docling/reference/document_converter/>;
   - <https://github.com/docling-project/docling/blob/main/docling/pipeline/standard_pdf_pipeline.py>;
   - <https://github.com/docling-project/docling-core/blob/main/docling_core/types/doc/document.py>;
     and
   - <https://github.com/docling-project/docling-ibm-models/blob/main/docling_ibm_models/reading_order/reading_order_rb.py>.

The outcome must explain in plain language which relationships are page-local,
which cross a range seam, which can be recomputed globally, and which require
overlap evidence.

## Plan / spec requirement

Write the short chunk-conversion specification before maintained implementation.
It must define:

- range-plan identity and deterministic boundary selection;
- inclusive page numbering, core ownership, overlap ownership, and exact full-page
  coverage;
- child completion, aggregate completion, inventory, checksum, and corruption
  behavior;
- reference remapping and closure across body, furniture, groups, text, tables,
  pictures, captions, footnotes, pages, assets, and provenance;
- cross-range text-merge reconciliation and whole-document heading inference;
- failure and resume semantics for missing, partial, corrupt, cancelled, or
  differently identified ranges;
- deterministic merge behavior independent of range completion order;
- resource accounting for one and multiple workers; and
- invalidation boundaries for source, model/runtime, range plan, merge code,
  routing/table code, and downstream-only changes.

Do not preserve a compatibility implementation beside the accepted path. If the
experiment is rejected, revert its isolated commits and retain only the task outcome
and failure evidence.

## Gate 0: Preserve the reviewed baseline

Before experimental implementation:

1. Create a dedicated branch, provisionally
   `codex/task03h2-chunked-docling-conversion`.
2. Inventory the dirty working tree and distinguish the approved Task 03H repair set
   from unrelated user work.
3. Synchronize Task 03H status through the completed G1 publication and failed G2
   attempt.
4. Run the existing full source-free validation and deterministic configuration
   check.
5. Commit only the reviewed baseline and task activation records. Record the branch
   and commit in this task before adding experimental code.

No force reset, destructive checkout, artifact deletion, or history rewrite is
permitted.

### Gate 0 outcome: 2026-08-20

Gate 0 is complete. The reviewed baseline is recoverable on branch
`codex/task03h2-chunked-docling-conversion` at commit `47560a1` (`Preserve Task
03H repair baseline`). The inventory contained 242 Task-03H-owned paths: the approved
clean-run namespace and production recipes, source-independent execution repairs,
their schemas/tests/specifications, synchronized G1/G2 status records, and this task
activation contract. Independent code and documentation reviews found no unrelated
user work in that scope.

The source-free gate passed `make fix`, `make check` with Ruff, strict mypy across 316
source files, and 744 tests, `uv run python scripts/generate_task03h_configs.py
--check`, and `git diff --check`. The deterministic non-executed production recipe is
`exv1-1594625ce741a9db1a883ceb58c70396b55eba50b43d03a33bbd47cb3604642e`.
No source PDF was read and no Docling object or model was constructed.

The review retained one non-blocking source-free follow-up: malformed-outline
normalization currently assumes one extraction call on a fresh `PdfReader`; a second
call on the same reader is not idempotent. Production already creates a fresh reader
and calls once. Gate A must either make that in-memory normalization idempotent or
encode and test fresh-reader ownership before the adapter becomes part of the chunked
conversion design.

## Gate A: Source-free G1 recomposition proof

Use only G1's sealed conversion and derived evidence. Do not read the G1 PDF or
construct Docling.

1. Build a typed ledger of page-local and document-global fields and every internal
   reference class.
2. Partition the sealed evidence at adversarial simulated seams: ordinary prose,
   heading transitions, caption/table boundaries, consecutive table pages,
   furniture transitions, cross-page text continuations, and long table runs.
3. Recompose in forward, reverse-completion, and randomized-completion order while
   emitting physical pages in canonical order.
4. Require exact page coverage and uniqueness, closed references, stable item order,
   geometry/provenance preservation, asset closure, and identical declared semantic
   projections.
5. Target byte identity for stable `document.json`, heading overlay, and page
   alignment outputs. Any non-byte-identical field must be exhaustively classified;
   no semantic difference may be waived implicitly.
6. Corrupt, remove, duplicate, reorder, and identity-mismatch individual ranges and
   prove fail-closed diagnostics name the range and path.
7. Simulate interruption after several range seals and prove resume executes only
   missing ranges before deterministic aggregate publication.

Gate A ends in a design/review checkpoint. It does not authorize source-PDF or model
execution.

## Gate B: Bounded split-versus-contiguous conversion proof

Gate B requires explicit user approval after Gate A review. Select a small,
representative set of already completed G1 pages containing at least one of each seam
class above. Compare fresh bounded range conversions with the corresponding pages and
relationships in the sealed complete G1 conversion.

- Keep the test small enough to stop promptly.
- Record exact page ranges and why each boundary is representative.
- Compare layout labels, text, reading order, cross-page merges, captions, footnotes,
  figures, images, geometry, provenance, headings, warnings, and stable references.
- Exercise overlap reconciliation and prove each overlap page is emitted once.
- Treat any unexplained difference as a blocker; do not proceed to G2 planning.

## Gate C: Document-driven range planning

After separate approval for read-only source inspection, derive boundaries from
source-authored and native-PDF evidence before applying a page-count cap:

1. top-level and attachment-level PDF outline destinations;
2. cover/title or divider pages and page-label/numbering resets;
3. blank or near-blank separators;
4. transitions among prose, figures, and table-dominant page runs;
5. native-text evidence against a split heading/body or hyphenated continuation; and
6. table-continuation evidence such as repeated headers, `continued` markers, and
   uninterrupted table regimes.

Prefer a source-authored boundary near the target size. If no safe boundary exists
before the hard maximum, cut a homogeneous table run with overlap and require the
whole-document table-continuation stage to reconcile the seam. The plan must record
why every cut was chosen and whether it is source-authored, content-derived, or a
hard-cap fallback.

## Gate D: Resource and concurrency selection

Gate D requires explicit approval for its bounded PDF/model benchmark.

1. Measure one representative range sequentially: wall time, CPU utilization,
   per-stage time, peak RSS, swap delta, output bytes, and seal time.
2. Only if one range leaves documented memory headroom, run two comparable ranges
   concurrently with separate child-process isolation.
3. Compare aggregate throughput with sequential execution. Count model-loading
   duplication, contention, memory pressure, swap, and completion variance.
4. Select concurrency `1` unless measured parallelism materially improves throughput
   while remaining below the accepted aggregate memory budget with no jetsam or
   uncontrolled swap growth.
5. Never infer safe concurrency from CPU count alone. Chunk size, model copies,
   operating-system headroom, and user applications are part of the decision.

Range completion order must not affect the aggregate identity or bytes.

## Gate E: Appendix G2 execution and Task 03H resume

Gate E requires a final user check-in with:

- the accepted G1 equivalence results;
- the exact G2 range plan and overlap pages;
- expected range count, per-range time, total critical path, and selected concurrency;
- measured peak and aggregate resource bounds;
- interruption/resume demonstration;
- deterministic configuration and production identity; and
- the safe stopping point before downstream table extraction.

Only after approval may the task run Appendix G2. Every range must seal independently,
the aggregate conversion completion must publish last, and the existing table/router
and downstream stages may begin only after aggregate verification. Stop on an
unexplained semantic mismatch, failed range, memory-pressure event, or budget breach.

## Validation

- focused unit tests for range identity, boundary selection, overlap ownership,
  reference remapping, cross-seam text, heading recomputation, and completion order;
- corruption and interruption/resume tests with contextual diagnostics;
- source-free exact G1 recomposition tests and artifact report;
- after approval, bounded split-versus-contiguous G1 comparison;
- after approval, sequential and two-worker resource benchmark;
- deterministic Task 03H configuration and identity generation;
- behavior-focused tests rather than source-text assertions;
- full repository validation:

```bash
make fix
make check
uv run python scripts/generate_task03h_configs.py --check
git diff --check
```

## Review pass

Before Gate B, independently review:

- semantic preservation across range seams;
- ownership and maintainability of range planning, execution, merge, and sealing;
- identity/invalidation precision and immutable-evidence reuse;
- corruption recovery and failure accounting; and
- whether the implementation actually bounds memory rather than merely moving the
  whole-document allocation to a later stage.

Before Gate E, repeat the review against live bounded evidence and the final G2 plan.

## Acceptance criteria

- The pre-experiment Task 03H baseline is recoverable by branch and commit.
- Completed range bundles are immutable, independently verified, and reusable.
- Aggregate conversion publication requires exact page coverage, one core owner per
  page, closed references, verified children, and completion-last publication.
- Recomposition is deterministic regardless of child completion order.
- Source-free G1 recomposition preserves every declared semantic projection and
  explains every byte difference, if any.
- The bounded live comparison finds no unexplained range-seam difference.
- Document-driven boundaries are preferred and every hard-cap boundary is explicit.
- Cross-page text, heading, caption/footnote, figure/image, table-boundary, geometry,
  provenance, and warning behavior remain covered.
- An interrupted run resumes from the first incomplete range without rerunning valid
  ranges.
- Concurrency is selected from measured aggregate resources and throughput; unsafe
  parallelism remains disabled.
- G2 conversion completes within the accepted memory policy or stops with retained,
  range-specific evidence instead of losing all prior work.
- Existing routing, clean-table, record, hierarchy, and document consumers receive
  one verified complete conversion interface.
- Full validation and deterministic generation pass before Task 03H resumes.

## Non-goals

- skipping table-dominant pages from Docling in this task;
- changing canonical table/cell ownership;
- accepting simple JSON concatenation as a merge strategy;
- changing hierarchy, table-family, or document semantics to hide seam differences;
- OCR, VLM, LLM repair, remote conversion, or GPU migration;
- processing multiple source documents concurrently;
- deleting failed G2 attempts, temporary conversion evidence, or sealed upstream
  bundles;
- resuming Appendix G3 or later sources before G2 publishes; or
- assembling, accepting, or freezing the Task 03H collection.
