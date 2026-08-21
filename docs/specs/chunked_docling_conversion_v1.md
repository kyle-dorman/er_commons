# Restartable Chunked Docling Conversion v1

Status: **accepted production contract**. [Task
03H.2](../../tasks/sprint2/03h2_build_restartable_chunked_docling_conversion.md)
closed after the complete G1 validation run and downstream pipeline passed Gate C and
the human-ownership review. Appendix G2 will first use this path during the real Task
03H execution; this specification does not itself authorize PDF/model execution.

## Purpose

Large documents convert through a source-neutral runtime that publishes independently
sealed inclusive page ranges without
discarding completed work after a late failure. The aggregate must still expose one
complete, ordered Docling conversion to existing consumers. Completion order, retry
count, and worker count cannot change aggregate bytes or semantic records.

Gate A proved the range ledger, two-pass reference remapping, completion-order
independence, corruption rejection, and restart selection against the immutable sealed
Appendix G1 conversion. It partitions already finalized evidence. It cannot establish
that separately converted ranges equal one contiguous conversion; Gate B supplied that
bounded comparison, and Gate C supplied the complete G1 production-path proof.

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
adapter-contract error. Behavioral coverage locks this fresh-reader ownership; Gate A
did not invoke it.

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
- typed assembled page elements, body/header membership, page size, heading-style
  text cells, and an independently checksummed page raster;
- the exact captured PDF outline, page alignment rows, warnings, resource observation,
  artifact inventory, and checksums; and
- a terminal status requiring every requested page to succeed and zero conversion
  errors. Partial success is not sealable.

Children do not publish independently finalized `DoclingDocument` objects or
child-local document references. The aggregate compares duplicate overlap page and
alignment evidence exactly, selects every core page once in physical order, restores
the typed page evidence, and runs Docling reading order and heading inference once.
Docling therefore creates body, furniture, group, text, table, picture, caption,
footnote, provenance, and cross-page relationships only in the canonical aggregate.

Aggregate validation requires:

- exact core coverage with no missing, duplicate, or out-of-range page;
- exact overlap agreement and one alignment row per physical page;
- closed `body`, `furniture`, group, text, table, picture, caption, footnote, reference,
  cell, comment, page, image, asset, and provenance relationships;
- stable root metadata, item order, geometry, provenance, and asset metadata;
- exact heading-overlay and alignment-page coverage; and
- the ordinary deep-audited `SealedConversion` interface required by existing
  routing, table, mapping, hierarchy, and publication consumers.

Gate A's retired finalized-JSON graph/remapping oracle established reference and
completion-order invariants against sealed G1 evidence. It is validation history, not
part of the maintained production runtime.

## Boundary selection

The maintained production policy requires no preliminary PDF inspection. Every Task
03H source with more than 300 physical pages uses deterministic 225-page core
intervals, a 275-page hard maximum, and one comparison page on each available side.
Sources at or below 300 pages retain the simpler monolithic path. The fixed intervals
are derived only from the sealed source page count; exact overlap comparison and the
one whole-document interpretation pass make source-authored seam selection
unnecessary for correctness.

Gate A does not inspect the PDF. It selects adversarial simulated seams only from
sealed evidence: ordinary prose, heading transitions, caption/table boundaries,
consecutive table pages, furniture transitions, cross-page merged text, and long table
runs. These seams establish that fixed production intervals may cross arbitrary
content transitions without losing canonical document semantics.

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

Each range records conversion wall and CPU time, peak child RSS, warnings, completion
state, and the subprocess supervisor's process-tree RSS, wall time, system-memory, and
swap observations. The aggregate records the same supervisor observations separately
from its sealed creation evidence so a reuse check cannot be mistaken for creation
cost. Production concurrency is one; completion order remains semantically irrelevant.

Gate A's oracle intentionally materialized the complete 304 MB JSON plus rewritten
copies and is not evidence of bounded memory. The maintained live path releases page
rasters, parsed backends, and range model state after each child seal; the aggregate
loads only lightweight text/layout/page evidence needed by global reading order and
heading inference, while image bytes remain external. Gate B verified bounded
equivalence, and Gate C measured the complete G1 range and aggregate peaks. The
accepted production setting is one sequential worker.

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
growth. This validates the prompt-stop comparison only; the complete Gate C evidence
below owns the production resource conclusion.

## Gate C accepted production evidence

Run `gatec1-53d220...fe1124` converted all 2,488 G1 pages through 12 independently
sealed, document-driven ranges and completion-last aggregate
`dconv1-08a9a7...a2a25b`. Resume deep-verified and reused the retained first child
without a Docling/model call, then executed only the remaining children. The aggregate
reproduced the stable monolithic document, heading overlay, alignment, and asset
inventory byte for byte after one whole-document reading-order, text-merge, and
heading pass.

The largest range process-tree peak was 7,174,422,528 bytes and aggregate peak was
8,894,840,832 bytes with no positive swap growth. Two measured range peaks project
above the 10 GiB concurrent ceiling, so production concurrency is one and no unsafe
parallel trial is permitted without a new reviewed resource contract.

The aggregate also passed the isolated routing, clean-table, mapping, hierarchy,
structure, linking, and publication path. Routing was byte-identical, all 17,068 table
files were semantically exact, and all canonical/support publication files were
semantically exact under the declared code-bound identity and lineage normalization.
The final human-ownership pass separated planning, worker execution, range storage,
Docling adaptation, global aggregation, process supervision, completion, publication,
and workflow coordination into named package owners with public recovery seams.

This G1 evidence is sufficient to productionize the path. Appendix G2 does not require
a separate rehearsal: Task 03H must bind its exact plan and identity, obtain user
authorization, run one worker, and retain each verified range so a late failure resumes
without discarding completed work.
