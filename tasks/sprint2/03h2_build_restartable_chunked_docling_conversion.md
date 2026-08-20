# Task 03H.2: Build Restartable Chunked Docling Conversion

Status: **Gates A–C complete at the human-maintainability bar; stopped before Gate D**. Task 03H is paused
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

### Gate A outcome: 2026-08-20

Gate A passed and is stopped at its mandatory source-free review boundary. The
accepted design is recorded in
[`docs/specs/chunked_docling_conversion_v1.md`](../../docs/specs/chunked_docling_conversion_v1.md).
Its smallest maintainable contract separates strict range identities, exhaustive
document-graph closure, two-pass reference recomposition, and completion-last child
publication. The live design does not concatenate finished `DoclingDocument` objects:
page assembly can be retained per range, but cross-page text merging and heading
inference must run once over canonical whole-document evidence.

The independently reviewed Gate A result is reusable child plan
`dplan1-90ae463c9815d787cc57713070167dd91ff9ce44312da27dea81789bfb897aef`
and aggregate
`dagg1-6c89ba8ab4f1e58ac9250f363caaae6526499ecc9363b6e6206d96928b3d830a`
below `pipelines/brisbane_baylands/task_03h2_chunked_docling_conversion/gate_a/`.
Eight independently completion-sealed range bundles cover adversarial cuts at pages
13/14, 24/25, 52/53, 59/60, 70/71, 86/87, and 2190/2191. The aggregate deep audit
closed 2,488 pages, 464,945 collection records, 933,992 `$ref` occurrences,
4,125 heading-overlay records, 2,488 alignment records, 79 figure-asset metadata records,
and all 56 multi-page semantic objects. Four empty key-value groups with no direct or
descendant page evidence are explicit document-global records rather than silently
inheriting a neighboring page. The plan intentionally includes the
noncontiguous 23-page text object crossing the 70/71 seam.

Each overlap duplicates a semantic projection: the page record, every record whose
direct or derived provenance includes that page, heading-overlay records, alignment
record, and asset metadata. Recomposition compares those digests to the canonical core
owner. Child verification independently checks its complete manifest, core/read
coverage, local pointers, item ownership/order, overlap projection, heading targets,
alignment pages, asset targets, inventory, and completion before reuse.

Forward, reverse-completion, and seeded-random completion orders reproduced the four
stable sealed outputs byte-for-byte:

- `document.json`: 303,909,779 bytes,
  `eef9750dc18dd3dc07192ad847764712a3823348e6ce998c04c3d19012c7609c`;
- `heading_overlay.jsonl`: 428,008 bytes,
  `24d94963c27a713259ae123e54220cff0939cbf4ec0859b16f7c03328eb175c0`;
- `alignment_pages.jsonl`: 5,313,117 bytes,
  `5f76d057e94b0fa97f42ffe47d61b29f4451006b13b318c0ced172864ea9e0c0`;
  and
- `asset_inventory.json`: 24,711 bytes,
  `af61d1b902765f773f21dee6ff42a6897d0aaedd6cb96bbfe3bcd0d410339ee6`.

The sealed real-G1 mutation matrix rejects missing, duplicate, reordered,
foreign-identity, page/record-, heading-, alignment-, and asset-overlap corruption,
and projection-incomplete children with contextual
diagnostics; focused tests also reject byte corruption. The interruption simulation
retains three verified children, selects only the remaining five, and completes
canonical aggregate recomposition without re-executing a valid child.
The aggregate inventory and every child inventory are full-byte audited; publication
discovers a child or aggregate only after its completion record exists.

Child and aggregate invalidation are separate and code-bound. During the review, a
merge-only diagnostic repair changed aggregate `dagg1-7e13ba...111c6` to
`dagg1-a1b7e2...196d5` while retaining the then-current plan
`dplan1-2119e...98134` and reusing all eight child seals. Later child-validation
strengthening correctly produced the accepted plan and aggregate above.
Task 03H's existing monolithic production identity remained unchanged.

This proof preserves already materialized global semantics. It does **not** prove that
independently converted ranges reproduce a contiguous conversion, because the sealed
final JSON no longer contains the transient PDF outline or pre-global reading-order
state. That question belongs to the separately approved bounded Gate B comparison.
No PDF was read, no Docling object or model was constructed, and no live document was
published. The harness materializes the complete sealed JSON and therefore does not
prove memory boundedness. The live design must release page raster/backend/model state
after each child, retain only lightweight page evidence for the global reading-order
and heading passes, and measure that aggregate peak in Gate C. The 79 figure
metadata records were reproduced after full verification of the immutable source
bundle; Gate A did not copy PNG bytes into its aggregate. Gate A itself did not
authorize Gate B; the separate approval and accepted result are recorded below.

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

### Gate B outcome: 2026-08-20

Gate B passed under live run
`gateb1-c70b2b1e1ef5128b3c6059e5b0e22148308b428494ae1648c71a791374dbabfb`.
The bounded proof used four four-page G1 windows, each with two adjacent core ranges
and one page of overlap across each side of the cut:

- pages 85–88 at 86|87: ordinary-prose calibration;
- pages 12–15 at 13|14: cross-page prose, heading and furniture transitions, and a
  caption/table boundary;
- pages 421–424 at 422|423: consecutive tables inside a long table run plus figures;
  and
- pages 1404–1407 at 1405|1406: positive footnote and figure coverage.

Each seam ran in a fresh sequential child process. Two independent contiguous
conversions established determinism, left and right overlapping conversions produced
exact duplicate overlap evidence, declared core ownership emitted each physical page
once, and a source-free global pass over restored page evidence reproduced the bounded
contiguous document exactly. Document bytes, heading overlay, alignment rows, figure
assets, warnings, text and reading order, cross-page merges, captions, footnotes,
geometry, provenance, and every stable reference were exact split versus contiguous.
All live page-local semantics, heading targets, alignment rows, and asset digests also
matched the sealed complete G1 conversion.

Thirteen heading levels differed between bounded windows and the sealed whole document:
three at 13|14, six at 422|423, and four at 1405|1406. The heading items, text,
provenance, order, and targets were exact; only their compressed levels differed.
Each seam follows one positive, floor-preserving compression offset: one level at
13|14, four at 422|423, and three at 1405|1406. Arbitrary level differences fail. This
is the expected document-global behavior already identified in Gate A and confirms
that range workers must retain page evidence while heading inference runs once over
the complete aggregate. No child-final heading level may be accepted as canonical.

The strongest observed process-tree peak was 2,584,100,864 bytes, the longest seam
worker took 8.94 seconds, the longest isolated seam process took 12.78 seconds, and no
positive swap growth occurred. These four-page measurements prove prompt bounded-stop
behavior, not the memory bound of a production-sized range or the complete aggregate;
Gate C owns that measurement across the complete G1 qualification.

Two retained development attempts diagnosed and corrected project-owned evidence
issues before the accepted run: streaming JSON decimals needed a JSON-native
normalization, and the first page round-trip lost the runtime distinction between a
container and a figure. The maintained page evidence now records explicit element
types plus shared body/header membership, and its focused regression reproduces that
failure. A third retained attempt established the exact bounded-versus-whole-document
heading classification before the final report made it explicit. The final run and all
four seam inventories deep-verify. Its identity binds the exact prepared sealed-G1
conversion payload, full runtime options and package versions, model inventory,
runner/helper bytes, page plan, and resource limits. Gate C and G2 did not start.

The reviewed Gate A and Gate B work remains intentionally uncommitted at the user's
direction. Do not stage or commit it until the complete Gate C G1 qualification has
finished and its evidence has been reviewed.

## Gate C: Full G1 chunked-path qualification

Gate C requires separate approval for its G1 PDF reads and Docling/model execution.
It must validate the maintained path end to end against the immutable sealed G1
conversion before any G2 source inspection or planning.

1. Derive a document-driven G1 range plan from source-authored and native-PDF
   evidence before applying a page-count cap. Use outline destinations, dividers and
   page-numbering resets, blank separators, prose/figure/table transitions, native
   text that must not be split, and table-continuation evidence. Prefer a
   source-authored boundary near the target size. If no safe boundary exists before
   the hard maximum, cut a homogeneous table run with overlap and require the global
   table-continuation stage to reconcile the seam. Record every cut's evidence class
   and rationale.
2. Run the complete G1 range plan sequentially with one fresh isolated child process
   per range. Seal and deep-verify each child independently before reuse.
3. Demonstrate interruption and resume after at least one valid child seal. The
   resumed invocation must make zero Docling/model calls for every verified child and
   retain failed or incomplete attempt evidence without mutating valid bundles.
4. Recompose all canonical pages, run document-global reading order, cross-page text
   merge, heading inference, image attachment, and durable export exactly once, then
   publish the aggregate completion last.
5. Compare the aggregate with sealed monolithic G1. Stable document, heading overlay,
   alignment, assets, warnings, order, geometry, provenance, and reference projections
   must be exact; every difference must be classified and reviewed or Gate C stops.
6. Feed the verified aggregate through the existing G1 routing, clean-table, record,
   hierarchy, and document-publication path in an isolated qualification namespace.
   Verify exact reuse or explain every code-bound descendant difference without
   rewriting the sealed G1 baseline.
7. Record per-range and aggregate wall/CPU time, peak process-tree RSS, system memory
   pressure, swap delta, input/output bytes, model-load time, seal time, warnings, and
   completion state.
8. Only if the full sequential run leaves documented headroom, run two comparable G1
   ranges concurrently with separate child-process isolation. Select concurrency `1`
   unless two workers materially improve throughput within the accepted aggregate
   memory budget with no jetsam or uncontrolled swap growth.
9. Independently review the sealed G1 qualification, recovery behavior, aggregate
   memory, downstream compatibility, and selected concurrency. Stop for user review
   before G2 inspection. Completion of Gate C is the checkpoint at which the current
   uncommitted Task 03H.2 work may be reviewed for staging and commit.

Range completion order must not affect aggregate identity or bytes. Never infer safe
concurrency from CPU count alone; chunk size, model copies, operating-system headroom,
and user applications are part of the decision.

### Gate C outcome: 2026-08-20

Gate C passed under run
`gatec1-53d220f716dbb5a9ae1ec031b9ef86c2c14884c0744beee7227708504afe1124`
and plan
`dplan1-9ee18ee84e5d6e3134fffbd6e674353116793b832f9fef5d7ebc4fb80a3d552e`.
The document-driven plan covered all 2,488 G1 pages in 12 core ranges with one-page
comparison overlap: 1–232, 233–447, 448–669, 670–887, 888–1107, 1108–1332,
1333–1590, 1591–1811, 1812–1957, 1958–2146, 2147–2232, and 2233–2488. Every range
remained below the 275-page hard maximum. The sealed plan records the source-authored,
native-text, page-regime, figure/table-transition, or homogeneous-table-run evidence
used for each cut.

All 12 range children completed in fresh sequential processes and sealed independently.
The first child was deliberately retained as an interruption checkpoint; the resumed
invocation deep-verified and reused it with zero Docling/model calls, then executed only
the remaining 11 children. A second invocation verified the completed conversion in
6 seconds without recomputation. No child completion was mutated.

The completion-last aggregate is
`dconv1-08a9a730efde0a5607ea2cc38c4b821e91c435fc0b1520a4cd4c612a44a2a25b`.
It runs reading order, cross-page text merging, heading hierarchy, image attachment,
and durable export once over canonical physical-page order. Its stable document,
heading overlay, alignment, and asset inventory are byte-identical to sealed monolithic
G1: `eef9750d...c7609c`, `24d94963...b175c0`, `5f76d057...a9e0c0`, and
`af61d1b9...339ee6`, respectively. Page coverage, warnings, references, geometry,
provenance, assets, and aggregate input interface also close exactly.

The largest range process-tree peak was 7,174,422,528 bytes RSS. Aggregate assembly
peaked at 8,894,840,832 bytes, took 328.92 seconds, observed no positive swap growth,
and retained at least 15,676,375,040 bytes available system memory. Two measured range
peaks project to 14,348,845,056 bytes, above the accepted 10 GiB concurrent ceiling.
Gate C therefore selects one worker and intentionally does not execute a two-worker
trial. This is a measured safety decision, not a CPU-count heuristic.

The verified aggregate then completed the entire G1 downstream path in an isolated
qualification namespace. Producer
`prv1-44774afd5475af0f5a4415a5a6e8e76dd32b9e2c0f3a53fe39e1053535a38bb8`
finished in 6,978.06 seconds. Routing is byte-identical: 412 no-table pages, 2,060
layout-region pages, and 16 full-page-numeric pages. The clean table stage reproduced
2,076 routed pages, 3,735 logical tables and assignments, 2,361 families, and the same
eight zero-table pages. All 17,068 compared table files are semantically exact; 14,979
are already byte-identical, while the remainder differ only in code-bound identity,
configuration lineage, or observations.

Record mapping, hierarchy, structure, and cross-reference linking completed as new
sealed descendants. Their historical and qualification inventories were all
independently rehashed, including 806.64 MB hierarchy bundles on each side. Canonical
publication `docv1-b62932c4076202e1c950847e36625dd2a163f5a71bd0136b4ef246bcc03b78b6`
then completed in 40.50 seconds. All 18 canonical/support files are semantically exact.
The comparison removes only timestamps/timings, code-bound stable IDs, the artifact-root
prefix before the preserved document-relative path, and two hierarchy seal hashes that
are separately deep-verified and required to match the bounded-control record. Unknown
hashes, changed relative paths, changed identity relationships, and every other field
remain fatal. Routing, table, stage, publication, and final qualification completions
all deep-verify; the sealed report reuses in 3.4 seconds.

The first records qualification preflight failed before candidate creation because a
generated config still pointed at the historical producer root while naming the new
producer ID. That retained development failure did not mutate any sealed artifact. The
fixed template binds both producer ID and qualification root, and focused behavior tests
cover the semantic comparison and fail-closed normalization rules.

Independent post-run review found no unexplained semantic, recovery, lineage, resource,
or publication difference. Gate C is accepted. G2 was not inspected, Gate D did not
start, and the current branch remains intentionally uncommitted for user review as
requested.

Final repository validation passes `make fix`, `make check` with 790 tests and strict
mypy across 323 source files, deterministic Task 03H config checking, Gate C completed-
run reuse, downstream report reuse, and `git diff --check`.

### Human-ownership reopening: 2026-08-20

The user reviewed the Gate A–C implementation as behavioral MVP evidence and rejected
its code quality for closure. Passing artifacts and tests do not make the current
machine-oriented proof runners understandable, debuggable, or safely editable by a
human maintainer. Gates A, B, and C therefore remain open as engineering gates even
though their immutable behavioral evidence remains valid.

Before Gate D or any G2 inspection, replace the large task scripts with short
application shells and responsibility-owned package modules. A future maintainer must
be able to locate planning, child execution, process isolation, evidence capture,
recomposition, downstream qualification, semantic comparison, publication, recovery,
and diagnostics without tracing thousand-line scripts or untyped dictionaries. Tests
must exercise those public seams, exact contextual failures, corrupt/incomplete reuse,
and dependency direction. Objective maintainability checks must reject a regression to
monolithic orchestration.

This refactor is source-free. It may use unit fixtures, small synthetic Docling objects
that do not construct models, and read-only hashes/metadata from already sealed
evidence. It must not read the G1 PDF, construct or execute Docling models, rerun the
full G1 pipeline, inspect G2, mutate accepted evidence, stage, or commit. Behavioral
preservation comes from the existing offline suite and immutable Gate A–C reports; a
new full-G1 run is neither required nor authorized.

### Human-ownership outcome: 2026-08-20

The source-free refactor now passes the human-ownership gate. The four task runners
are 32, 54, 60, and 34 lines and contain only argument parsing and delegation.
Maintained responsibilities now have named package owners for contracts, input and
identity validation, process supervision, Docling adaptation, converted-range storage,
global aggregation, reporting, downstream stages, semantic comparison, publication,
and read-only evidence audit. The source-free Gate A graph and recomposition facade is
62 lines; partitioning, validation, records, diagnostics, and reconstruction have
separate owners.

Recovery is exercised through real public seams rather than report-only simulation.
Tests cover missing and corrupt children, exact executor calls, aggregate-only retry,
transplanted completion rejection, strict completion schemas, first-failure retention,
incomplete final directories, resource stops, backend-release failures, output-byte
reseals, and lineage closure. Existing completed results are reusable only after exact
run/plan/source/aggregate identity checks, completion-to-inventory verification, full
managed-byte hashing, and stage-specific child or downstream closure. CLI, help, and
reporting-only changes no longer invalidate expensive child conversion; semantic
worker and aggregate owners remain code-bound separately.

The structural maintainability gate rejects a runner over 65 lines, a qualification
owner over 320 lines, a function over 95 lines, reverse runner imports, or tests that
dynamically load implementation scripts. The focused Gate A–C/downstream suite passes
91 tests. Full repository validation passes formatting, Ruff, strict mypy across 367
source files, and 835 tests. Deterministic Task 03H configuration checking and
`git diff --check` also pass. Independent recovery review found no remaining P1
closure blocker.

A read-only audit rehashed the immutable accepted evidence without opening a PDF or
executing Docling/models: Gate A 8 files/312,385,570 bytes; Gate B 130
files/28,054,518 bytes; Gate C 5,266 files/3,137,009,668 bytes; its aggregate 87
files/318,341,881 bytes; and downstream 17,214 files/2,106,839,463 bytes. Identities,
terminal status, completion-to-inventory seals, exact managed file sets, every managed
byte, and recorded pass claims all remain valid. This audit preserves the accepted
behavioral evidence; it is not a new live qualification of the refactored code, and
the user explicitly prohibited a full G1 rerun for this refactor.

No G1 PDF was read, no Docling object or model was constructed or executed, G2 was not
inspected, and no accepted evidence was mutated. The working tree remains intentionally
unstaged and uncommitted for user review. Gate D and every G2 action still require a
separate user authorization.

## Gate D: G2 document-driven range planning

Only after Gate C passes and the user separately approves read-only G2 source
inspection may the task derive G2 boundaries using the same accepted evidence classes.
The G2 plan must record every core range, overlap, expected range identity, boundary
rationale, hard-cap fallback, and conservative duration/resource forecast derived from
Gate C. Gate D performs no G2 Docling/model execution and stops for review.

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
- after approval, complete sequential G1 chunked qualification and a bounded
  two-worker G1 benchmark when headroom permits;
- exact downstream G1 compatibility/reuse proof from the recomposed aggregate;
- reviewed document-driven G2 range plan derived only after G1 qualification;
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

After Gate C, independently review the complete live G1 qualification before any G2
inspection. Before Gate E, repeat the review against that evidence and the final G2
plan.

## Acceptance criteria

- The pre-experiment Task 03H baseline is recoverable by branch and commit.
- Completed range bundles are immutable, independently verified, and reusable.
- Aggregate conversion publication requires exact page coverage, one core owner per
  page, closed references, verified children, and completion-last publication.
- Recomposition is deterministic regardless of child completion order.
- Source-free G1 recomposition preserves every declared semantic projection and
  explains every byte difference, if any.
- The bounded live comparison finds no unexplained range-seam difference.
- A complete chunked G1 execution, aggregate, and downstream qualification preserves
  the accepted sealed G1 contract or explains every reviewed code-bound difference.
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
