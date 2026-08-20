# Restartable Chunked Docling Conversion v1

Status: **Gate B accepted; Gate C not authorized** for
[Task 03H.2](../../tasks/sprint2/03h2_build_restartable_chunked_docling_conversion.md).
The accepted bounded G1 proof does not authorize document-driven G2 inspection,
concurrency benchmarking, a G2 rerun, or live document publication.

## Purpose

Large documents must convert through independently sealed inclusive page ranges without
discarding completed work after a late failure. The aggregate must still expose one
complete, ordered Docling conversion to existing consumers. Completion order, retry
count, and worker count cannot change aggregate bytes or semantic records.

Gate A proves the range ledger, two-pass reference remapping, completion-order
independence, corruption rejection, and restart selection against the immutable sealed
Appendix G1 conversion. It partitions already finalized evidence. It cannot establish
that separately converted ranges equal one contiguous conversion; that requires the
separately approved Gate B comparison.

## Maintainer and installed-source findings

The installed versions are Docling 2.115.0, docling-core 2.88.0, and
docling-ibm-models 3.13.3. The maintained design follows their actual boundaries:

- `DocumentConverter.convert` accepts a one-based inclusive `page_range`. The standard
  pipeline clamps the range to the document, preserves requested page order, and may
  return partial or failed results without raising when `raises_on_error=false`.
- Layout and page assembly run pagewise. Reading order, caption attachment, and
  footnote attachment first partition by page, but text merging scans the complete
  ordered element stream and can merge text across physical pages.
- Heading inference runs after reading order. Numbering families, style ranks, and
  bookmark depths are calibrated over the whole document. The private PDF outline is
  discarded after heading inference and is absent from sealed final JSON.
- `DoclingDocument.add_document` and `concatenate` are not merge contracts. They can
  renumber pages, omit origin or furniture state, reparent selected nodes, and drop
  floating references that are not present in their selected mapping.
- Built-in validation does not exhaustively prove floating-reference, provenance-page,
  asset, exact-coverage, or duplicate-page closure.

Primary maintainer references:

- <https://docling-project.github.io/docling/reference/document_converter/>
- <https://github.com/docling-project/docling/blob/main/docling/pipeline/standard_pdf_pipeline.py>
- <https://github.com/docling-project/docling-core/blob/main/docling_core/types/doc/document.py>
- <https://github.com/docling-project/docling-ibm-models/blob/main/docling_ibm_models/reading_order/reading_order_rb.py>

The consequence is deliberate: live ranges will seal page-level assembled/prediction
evidence, not independently finalized document semantics. After exact page ownership
is established, one aggregate pass will perform reading order, cross-page text merges,
heading inference, image attachment, and durable export. Gate B must additionally
capture or defer source outline evidence because it cannot be recovered from final
Docling JSON.

The outline adapter is single-use by contract. Each authorized source inspection must
construct a fresh `PdfReader`, normalize malformed destinations once, extract the
outline once, and release that reader. Reusing an already normalized reader is an
adapter-contract error. Gate B must lock this fresh-reader ownership with a behavioral
test before the adapter can enter range execution; Gate A does not invoke it.

## Identity and plan

The range-plan identity is `dplan1-<sha256>` over canonical JSON containing:

- source ID, source SHA-256, byte size, and physical page count;
- sealed source-release identity;
- converter, package, model, adapter, and page-evidence contract identities;
- range-planner and child-execution code identities;
- target range size, hard maximum, overlap policy, and every ordered range record; and
- the range-evidence schema.

Aggregate identity is separate: it closes over the plan ID, ordered range IDs,
aggregate-merge code identity, output schema, and global-interpretation policy. A
merge-only change republishes the aggregate while reusing verified children.

Pages are one-based and inclusive. Each plan contains exact, gap-free core intervals
covering `1..page_count` once. A range may read declared left and right overlap pages,
but only its core interval owns output pages. Every overlap page names its core owner
and carries a digest comparison; it is never emitted twice. `max_num_pages` remains
the full source page count because Docling applies that limit to the complete input,
not the requested range length.

Each range ID is `drange1-<sha256>` over the plan ID, source identity, core interval,
read interval, overlap owners, and range-conversion identity. Completion order and
operational resource limits do not enter semantic ordering. An output-affecting child
setting changes the plan; a merge-only setting changes only the aggregate identity.

## Range evidence and reference ledger

Each successful child publishes a completion-last bundle with:

- range identity and exact core/read intervals;
- expected, converted, successful, overlap, and core-owned page lists;
- page-level assembled/prediction evidence plus captured outline evidence when later
  authorized;
- local records and a two-pass mapping from local references to canonical source
  references;
- explicit external seam references with target owner, target kind, and target digest;
- warnings, errors, assets, provenance, resource observations, artifact inventory,
  and checksums; and
- a terminal status requiring every requested page to succeed and zero conversion
  errors. Partial success is not sealable.

Gate A simulates this representation from sealed final evidence. It inventories roots
(`body`, `furniture`), pages, groups, texts, tables, pictures, form items, key-value
items, every `$ref`, floating captions/references/footnotes, group children and parents,
table-cell references, provenance page numbers, page images, picture images, and
external figure asset metadata. The first pass assigns exactly one core owner to every
page-bound record from its provenance pages or recursively derived descendant pages,
creates stable
range-local pointers, and records all cross-range dependencies. The second pass sorts
by canonical physical page and original source position, reconstructs global arrays,
and remaps every local or external pointer to its canonical target.

Aggregate validation requires:

- exact core coverage with no missing, duplicate, or out-of-range page;
- one record at every declared canonical collection index and no extra record;
- closed `body`, `furniture`, group, text, table, picture, caption, footnote, reference,
  cell, comment, page, image, asset, and provenance relationships;
- identical root metadata, item order, geometry, provenance, and source asset metadata,
  with the immutable source inventory independently verified;
- exact heading-overlay and alignment-page coverage; and
- byte-identical stable `document.json`, `heading_overlay.jsonl`, and
  `alignment_pages.jsonl` for Gate A.

An empty root or collection remains an explicit valid owner. A record without direct
provenance inherits the ordered union of descendant provenance. A record with neither
direct nor descendant page evidence remains an explicit document-global record; it
does not silently inherit a neighboring page. Gate A exercises this rule with four
empty key-value groups.

## Boundary selection

The live planner will prefer source-authored boundaries in this order: PDF outline
destinations; cover, divider, or page-label reset; blank separator; transition among
prose, figure, and table regimes; native-text evidence against a split heading or
hyphenated continuation; then table-continuation evidence. The nearest safe boundary
to the target size wins deterministically. If no safe boundary exists before the hard
maximum, the planner cuts the homogeneous regime with overlap and records
`hard_cap_fallback` plus required seam reconciliation.

Gate A does not inspect the PDF. It selects adversarial simulated seams only from
sealed evidence: ordinary prose, heading transitions, caption/table boundaries,
consecutive table pages, furniture transitions, cross-page merged text, and long table
runs. These seams test the ledger; they are not a proposed G2 plan.

## Child and aggregate publication

A child writes payloads and inventory first, verifies them from the staging directory,
then writes `completion_record.json` last and atomically publishes the directory. The
aggregate accepts only children whose plan, source, converter, range, inventory, and
completion identities all match. It verifies all children before loading semantic
payloads, recomposes in canonical range order regardless of completion order, writes
its inventory, verifies the complete candidate, and publishes aggregate completion
last.

Existing final directories are immutable. Identical verified evidence is reusable;
different bytes at an existing identity are a collision. Missing, partial, cancelled,
or corrupt staging work remains retained attempt evidence and cannot impersonate a
completed child.

## Restart and failure semantics

Restart scans the ordered plan and deep-verifies each completed child. Valid children
are reused. The execution queue includes missing children and retained incomplete
staging attempts; it never reruns an earlier valid child. A corrupt or differently
identified immutable final child is a collision and stops reuse rather than being
silently overwritten. Recovery must retain that evidence and publish under a corrected
identity or explicitly reviewed location. Aggregate failure retains all child seals. A
failed merge can be retried without conversion after the exact child set revalidates.

Diagnostics must name the plan, range, path, invariant, and expected/actual value for:
missing range, duplicate core owner, coverage gap, overlap disagreement, identity
mismatch, inventory mismatch, checksum mismatch, malformed record, unresolved
reference, provenance outside the source, missing asset, completion-order difference,
and aggregate byte difference.

## Invalidation

- Source bytes, source page count, Docling/model/runtime configuration, page-assembly
  adapter, or range-conversion contract invalidate affected child ranges and aggregate.
- Range boundaries or overlap policy invalidate the plan, all child identities, and
  aggregate without rebinding older evidence.
- Reference remapping, global reading order, text merge, heading inference, image
  attachment, or aggregate-export changes invalidate aggregate interpretation. A
  page-evidence schema change may also invalidate children.
- Routing or canonical-table changes reuse the verified aggregate conversion and
  rebuild descendants.
- Record mapping, hierarchy correction, document structure, reference linking, or
  collection changes reuse conversion and all unaffected ancestors.
- Worker count, retry timing, logging, or resource observation changes do not alter
  semantic identity unless they change output bytes or accepted policy.

## Resource accounting

Each range records wall and CPU time, peak child RSS, input/output bytes, model-load
time, seal time, warnings, and completion state. The coordinator records concurrent
worker RSS, system memory pressure, swap delta, throughput, and idle time. Concurrency
defaults to one. Gate C may select two only from measured aggregate headroom and
throughput; completion order must remain semantically irrelevant.

Gate A's oracle intentionally materializes the complete 304 MB JSON plus rewritten
copies and is not evidence of bounded memory. The proposed live path releases page
rasters, parsed backends, and range model state after each child seal; the aggregate
loads only lightweight text/layout/page evidence needed by global reading order and
heading inference, while image bytes remain external. Gate B must verify bounded
equivalence, and Gate C must measure the complete G1 range and aggregate peaks. If
that lightweight global state still
exceeds the accepted budget, the design is blocked rather than described as bounded.

## Gate A acceptance boundary

Gate A succeeds only when forward, reverse, and deterministic randomized completion
orders reproduce identical declared projections and stable bytes; corrupt, missing,
duplicated, reordered, and identity-mismatched children fail closed; and restart selects
only missing children while stopping on corrupt immutable finals. Success authorizes a
design review, not Gate B, a PDF
read, Docling/model construction, live range conversion, or Appendix G2 execution.

## Gate B accepted evidence

Run `gateb1-c70b2b...dbabfb` compared four four-page G1 windows around ordinary
prose, cross-page prose with caption/table structure, a long consecutive-table run
with figures, and a positive footnote/figure case. For every window, duplicate
contiguous conversions were deterministic; both overlap copies were exact; and typed,
round-tripped page evidence assembled globally into the exact contiguous document,
heading overlay, alignment, assets, warnings, order, geometry, provenance, and
reference graph. The live page-local projection and asset digests also matched sealed
G1.

The proof exposed why serialized child-final headings are forbidden: thirteen bounded
heading levels compressed differently from the whole-document G1 levels even though
the heading items, targets, order, text, and provenance were exact. The aggregate must
therefore run heading inference once over complete canonical page evidence. Page
evidence also records each assembled element's concrete runtime type and shared
body/header membership; plain union-model JSON is insufficient because it can restore
a container as a figure.

Accepted heading differences must follow one positive floor-preserving compression
offset per window; any other level change is unexplained and fails. The Gate B identity
also binds the prepared sealed-G1 conversion identity, full effective runtime and
package versions, model inventory, runner and adapter bytes, page plan, and resource
limits. Runtime drift cannot reuse the accepted proof identity.

The four-page process-tree peak was at most 2,584,100,864 bytes with no positive swap
growth. This validates the prompt-stop comparison only. Production range and aggregate
memory remain unproven until the complete Gate C G1 qualification.
