# Task 03G.2b: Preserve Document-Index Text Through Table Extraction

Status: **complete as of 2026-08-05**. The fresh Task 03G.2
main-report baseline and hierarchy producers completed after Task 03G.2a, but
canonical materialization failed closed because ordinary table extraction
suppressed text owned by Docling `document_index` objects. The user explicitly
selected a post-producer correction so both sealed producers and all parser
evidence remain immutable and reusable.

## Abstract

Keep document-index and table-of-contents structures in the canonical text
stream even when a parser can recover a grid from their page regions. The
canonical consumer resolves each producer region's existing raw Docling
pointer, retains all sealed page-local parser and family evidence, but derives
a filtered logical-table view in which every `document_index` observation has
zero canonical tables. Reuse the freshly sealed main-report producers to
validate the correction without rerunning Docling, Camelot, or TableFormer,
then resume the three-source pilot only after the canonical and downstream
main-document stages succeed.

## Observed failure

- fresh baseline producer:
  `prv1-9fcd49227703767d60d26ebdcf699f60aa7d44b745e022c396364b01fd250be6`;
- fresh hierarchy producer:
  `prv1-ccd103d5a798e8b44c8a959635dff5d0dc491e6c8384635d3240ba07a9b16fb4`;
- first failed transaction:
  `txv1-1ef4e2386707007657508c01fb2837cacb5322229487aaff84dff2ba6b3fa80e`;
- checksum-reuse retry:
  `txv1-14dc4c2eb5d700f8df36451b1beb37e0e9abdb303f9b4f51ca063fb5a49c7c6b`;
- 34 Docling `document_index` objects exist in the main source; 24 were
  materialized as logical tables, suppressing all 7,092 of their descendant
  text pointers; and
- canonical materialization rejected both attempts with
  `document-index descendants were not emitted`.

The retry reused both completed producers and reproduced the canonical failure
in seconds. This is deterministic policy disagreement, not a transient model
failure. The scope was stopped after its sequential policy began Appendix D;
that orphan worker was terminated and produced no completion record.

## Goal

Make the verified producer-to-canonical projection and the existing canonical
document-index invariant agree: document-index descendants remain emitted text
and cannot be replaced by clean table records. Producer artifacts remain
truthful parser evidence rather than being mutated into consumer policy.

## Plan

1. Resolve every verified region mapping's existing `raw_object_ref` against
   the sealed Docling document before canonical traversal.
2. Add a pure canonical-input projection that recognizes only
   `label == "document_index"`, preserves the producer bundle unchanged,
   records an explicit exclusion, and removes the mapped clean table plus any
   now-empty family only from the canonical logical-table view.
3. Add synthetic tests for mapped document indexes, zero-table document
   indexes, ordinary table preservation, mixed families, closed region
   mappings, and deterministic projection.
4. Reproject the retained fresh main producer offline and require all 9,852
   document-index descendant pointers to be emitted, with zero overlap against
   suppressed text and no unrelated table decision changes.
5. Refresh the code-bound Task 03G.2 production and canonical identities, run
   project validation, repeat source/model preflight, and require the predicted
   baseline and hierarchy producer IDs to remain exactly unchanged.
6. Resume the full scope only after both completed producer inventories and
   completion seals verify reuse. Rebuild canonical and later stages under the
   new identity without allocating a PDF/model attempt for `deir_main`.

## Validation

- every `document_index` observation has an explicit zero-canonical-table
  projection regardless of parser success;
- all document-index descendant text pointers are emitted by canonical
  traversal;
- ordinary table regions, the Task 03G.2a boundary outcomes, assets, and page
  accounting are unchanged;
- retained parser, learned-fallback, table, and family evidence remains
  discoverable and byte-unchanged in the sealed producer;
- the baseline and hierarchy producer IDs remain
  `prv1-9fcd49227703767d60d26ebdcf699f60aa7d44b745e022c396364b01fd250be6`
  and
  `prv1-ccd103d5a798e8b44c8a959635dff5d0dc491e6c8384635d3240ba07a9b16fb4`;
- the main document completes all six owner stages before Appendix D or
  Appendix P resumes; and
- `make validate-extraction-contract`, `make check`, and `git diff --check`
  pass before any new PDF allocation.

## Non-goals

- changing Docling's labels or hierarchy graph;
- treating all tables of contents by text heuristics;
- changing producer routing, parser thresholds, or the learned fallback;
- deleting the two failed canonical attempts or fresh producer evidence;
- reusing historical Appendix P lineage or bounded authorization; or
- executing Appendix D, Appendix P, stage two, handoff, or reuse before the
  main document succeeds.

## Outcome

The canonical-only projection removed 24 parsed document-index tables and 18
now-empty families from the canonical view while preserving the sealed
producer artifacts byte-for-byte. All 9,852 document-index descendant pointers
were emitted as text with zero overlap against canonical suppression. Both main
producers checksum-reused under their existing IDs, and the rematerialized main
document completed all six owner stages as
`docv1-e97fbcf3c8f51a982eafe920dce150c76badf9159f07b74ef36a52627d792992`.
Task 03G.2c owns the later, distinct failures observed only after the scope
resumed Appendix D and Appendix P.
