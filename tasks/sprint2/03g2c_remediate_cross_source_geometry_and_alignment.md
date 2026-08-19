# Task 03G.2c: Remediate Cross-Source Geometry and Producer Alignment

Status: **completed on 2026-08-05; Task 03G.2d owns the downstream target-index
stream repair**.
Task 03G.2b succeeded and the fresh 2,092-page main document completed all six
owners. The resumed scope then exposed two source-general failures: Appendix D
contains native-PDF text rectangles outside its visible page canvas, and the
fresh Appendix P producer pair contains 18 otherwise identical page-15 map
labels whose Docling bounding boxes differ by less than 0.2 PDF point.
After both corrected Appendix D producers sealed, canonical materialization
also exposed 75 Docling text items whose every saved provenance region is
wholly outside the visible page.
After canonical suppression accounted those items, hierarchy correction exposed
three Appendix D PDF outline leaves whose destination is absent.
The resumed hierarchy build then exposed 17 exact stable-key collision groups
covering 34 Appendix D text representations on pages 304-323. Both fresh
producers retain the same pointers, parent collections, and ordering.
After hierarchy correction completed, semantic materialization exposed a legacy
Appendix-P-only assumption that every visible TOC row had an exact target;
Appendix D correctly retains non-exact reconciliation rows with null targets.

## Goal

Handle both observed representations without weakening source, lineage, or
bridge closure: routing measures visible PDF geometry only, and the semantic
join accepts only uniquely corresponding text items with exact text, original
text, physical page, and character span plus tightly bounded bbox drift.

## Plan

1. Clip partially visible native text rectangles to the routing page canvas
   and ignore fully off-canvas rectangles. Continue rejecting non-finite,
   non-positive, or unsupported page geometry.
2. Validate the rule on synthetic geometry and every affected Appendix D page
   observed in the retained failed producer attempts: 18, 55, 56, 342, 344,
   346, 350, and 351.
3. Preserve the hierarchy producer's stable-key namespace. For unmatched
   baseline items, permit a correspondence only when text, original text,
   physical page, and character span match exactly, bbox coordinates differ by
   at most 0.5 PDF point, and the match is unique in both directions.
4. Reject missing, excess, out-of-tolerance, or ambiguous correspondences.
5. Suppress a canonical text block only when all its saved provenance is
   invalid, retain every rejected provenance object verbatim in canonical
   diagnostics, and account the producer pointer through a dedicated semantic
   bridge disposition. Do not clamp or fabricate a canonical region.
6. Refresh the Task 03G.2 identity, repeat source/model and execution preflight,
   and resume the complete scope only after the identity consequence for the
   already completed main producer is explicit.
7. Omit only a PDF outline leaf with a missing or out-of-range destination and
   persist a `TOC_TARGET_MISSING` warning containing its title. Continue failing
   closed when an invalid outline node owns children, because reparenting that
   subtree would invent hierarchy. Task 03H extends this rule only for a
   destinationless appendix container whose children all have valid ordered
   destinations and whose appendix identifier uniquely fuzzy-matches a visible
   body heading on the page immediately preceding the first child. Bind that
   container to the evidenced heading, retain its children without reparenting,
   and emit `OUTLINE_CONTAINER_RECOVERED`; otherwise continue failing closed.
8. Preserve every exact duplicate producer text representation. Leave ordinary
   stable keys unchanged; for a colliding base identity only, derive a tagged
   key from the base key, semantic parent collection, and occurrence ordinal
   within that parent collection. Require the two fresh producers to align on
   those keys; do not use absolute collection indices or coalesce content.
9. Derive a visible-TOC target alias only from an exact reconciliation. Preserve
   missing, ambiguous, page-conflict, level-conflict, and order-conflict rows as
   diagnostics without inventing an alias target; continue failing closed when
   an exact reconciliation lacks canonical semantic content.

## Identity consequence

The routing correction changes producer-owned code. The maintained producer
identity intentionally hashes that shared code for every source, so the
corrected identity predicts new baseline and hierarchy producer IDs for the
main document as well as Appendix D and Appendix P. Reusing the old main
producer under the new identity would make the code-bound lineage claim false.
No compatibility alias or untracked patch is authorized.

## Validation

- clipped routing coverage remains within `[0, 1]` and is expressed in the
  displayed page coordinate system;
- all eight observed Appendix D pages route without geometry exceptions;
- Appendix P aligns all 6,931 producer text items, including exactly 18 bounded
  bbox correspondences beyond the 6,913 exact stable-key matches;
- Appendix D canonicalization accounts for all 30,067 producer text pointers,
  emits 23,199 blocks, suppresses 6,868 table, figure, or all-invalid-provenance
  items, records 84 rejected provenance entries, and has zero unaccounted text;
- Appendix D retains all 120 valid outline nodes and reports exactly three
  destinationless leaf bookmarks without changing producer or canonical content;
- all 30,067 Appendix D producer text items receive unique keys, including the
  34 items in 17 exact-collision groups, while non-colliding keys are unchanged;
- an ambiguous bounded correspondence fails closed;
- the main document-index projection and Task 03G.2a boundary behavior remain
  covered by their existing regressions;
- `make validate-extraction-contract`, `make check`, and `git diff --check`
  pass before PDF execution resumes; and
- no historical Appendix P producer, correction, semantic, cross-reference, or
  bounded-acceptance lineage is reused.

## Non-goals

- changing source PDF bytes or suppressing visible text;
- globally rounding producer stable keys;
- fuzzy text matching, OCR, or many-to-many bridge repair;
- clamping an invisible Docling text region onto the page or assigning it a
  fabricated full-page region;
- bypassing producer identity to retain an obsolete main producer ID; or
- accepting incomplete stage-two accounting after a failed document.

## Outcome

The source-general geometry, alignment, provenance, outline, collision, and
exact-TOC repairs completed successfully. Six fresh producers and all twelve
canonical, hierarchy-correction, semantic, and cross-reference owner
candidates are checksum-valid. The three document candidates completed with
warnings, and exact scope accounting records three successes and zero
failures. Project validation passed with 512 tests.

The first target-index build then failed before publication because stage-one
outcome observation sealed only `documents.jsonl` as a target stream even
though valid aliases also name sections, pages, and tables. Task 03G.2d owns
that post-producer evidence-wiring defect. No Task 03G.2c producer or completed
owner stage needs to be regenerated for the repair.
