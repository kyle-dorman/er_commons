# Task 03E: Build Hierarchy and Printed-Page Labels

Status: **provisional; scope split recorded 2026-07-29**. Revise this contract
from the accepted Task 03D outcome before activating it. Cross-reference
mention extraction and candidate resolution are deferred to a future Task
03E.1 contract written only after Task 03E is accepted.

## Abstract

Replace Task 03D's synthetic containment-only roots with a deterministic
canonical section hierarchy and add printed-page-label observations. Preserve
the signals and ambiguity behind inferred heading levels, boundaries, and page
labels rather than forcing uncertain evidence into one unqualified structure.
Do not extract or resolve cross-references in this task.

## Goal

Represent the Draft EIR as both an ordered document and a
provenance-preserving section tree so later curation, retrieval, citation
rendering, human review, and Task 03E.1 cross-reference linking can use semantic
paths without weakening exact page and content anchors.

## Inputs

- completed Task 03B canonical contract
- accepted Task 03D core canonical records, synthetic roots, observations, and
  raw mappings
- Docling heading labels, group structure, body order, typography, and
  provenance retained through Task 03D
- PDF outline and page-label metadata where present
- source titles, appendix identities, visible numbering, and canonical page
  geometry
- on-demand review-cache renders for selected validation pages
- current Docling
  [heading-hierarchy options](https://docling-project.github.io/docling/reference/pipeline_options/)

## Outputs

- canonical semantic section records and heading paths beneath the retained
  document roots
- deterministic reassignment of blocks, tables, and figures from synthetic
  roots into inferred sections
- printed-page-label observations with method, evidence, and explicit unknown
  or ambiguous states
- section, page, block, table, and figure graph edges that preserve exact
  low-level anchors
- a reviewed alias inventory for document, appendix, section, table, figure,
  and printed-page targets that Task 03E.1 may consume
- fixtures covering nested numbering, missing levels, repeated headings,
  ambiguous levels, appendix aliases, absent outlines, and printed-label
  mismatches
- validation summaries for hierarchy, membership, labels, aliases, and graph
  integrity

## Research / learning checkpoint

Inspect how heading levels are produced by the selected Docling configuration.
The layout model may identify a region as a section header without establishing
its level; bookmarks, numbering, typography, and deterministic hierarchy
inference are separate signals. Review current research on
[document-tree reconstruction](https://aclanthology.org/2024.findings-emnlp.628/)
and [reading-order relations](https://aclanthology.org/2024.emnlp-main.540/)
to distinguish a linear sequence from a semantic section tree.

The outcome must explain:

- **Reading order and hierarchy are different latent structures.** A correct
  sequence of blocks does not determine whether a heading is a sibling, child,
  caption, or continuation.
- **Task 03D roots are scaffolding, not semantic findings.** Retain stable body
  and furniture roots as containment anchors while replacing their flat
  child membership with reviewed inferred sections and direct children.
- **PDF outlines are evidence, not ground truth.** Bookmarks may be incomplete,
  stale, overly coarse, or absent even when visible headings are clear.
- **Heading induction is multi-signal inference.** Numbering patterns,
  typography, indentation, bookmarks, parser labels, and prior heading context
  can disagree. Preserve the evidence and deterministic rule that produced a
  level.
- **Printed labels differ from PDF page identity.** Keep internal indices,
  one-based physical PDF page numbers, page-tree labels, and visible printed
  labels distinct. Appendix page `3.5-17` is not interchangeable with physical
  page 17.
- **Ambiguity belongs in the data model.** Unknown or conflicting heading and
  label evidence must remain explicit rather than becoming a fabricated
  confident value.
- **Semantic units and physical anchors coexist.** A section can be a human
  citation unit while exact pages, blocks, tables, and figure regions remain
  the verification units.
- **Hierarchy quality affects later LLM evaluation.** Heading paths influence
  BM25 terms and passage boundaries; wrong containment can inflate apparent
  retrieval recall or feed irrelevant context that looks authoritative.
- **Cross-reference linking depends on reviewed targets.** Task 03E should
  establish section paths, printed labels, and normalized aliases before Task
  03E.1 parses mentions or proposes targets.

## Plan / spec requirement

Write a hierarchy and printed-label specification before implementation. It
must define:

1. heading-signal precedence and conflict representation;
2. section start, end, containment, and direct-membership rules;
3. how Task 03D synthetic roots are retained and extended;
4. title, appendix, section, table, figure, and page-label alias normalization;
5. printed-label observation methods, confidence, evidence, and unknown states;
6. behavior for skipped, repeated, malformed, and absent heading levels;
7. graph-edge types and referential-integrity invariants;
8. whether failures are fatal, warnings, or explicit unknowns;
9. deterministic ordering and candidate-identity consequences; and
10. the exact reviewed target and alias handoff to Task 03E.1.

Prefer deterministic parsing and explicit evidence records. Do not add an LLM
hierarchy repairer, embeddings, fuzzy semantic search, cross-reference parser,
or general knowledge-graph framework.

## Review pass

- **Hierarchy fidelity:** inspect nested, skipped, repeated, and
  appendix-specific heading patterns.
- **Root continuity:** verify semantic sections extend rather than accidentally
  duplicate or orphan the Task 03D containment roots.
- **Identity discipline:** verify printed labels never replace physical PDF
  page identity.
- **Ambiguity:** ensure uncertain heading levels or labels remain explicit.
- **Provenance:** every inferred section, label, membership, and alias retains
  its source blocks and deterministic rule.
- **Downstream safety:** graph metadata helps curation and retrieval without
  introducing curator labels, target-facing gold information, or premature
  cross-reference edges.

## Validation

- Validate section paths and parent/child edges as the exact acyclic rooted
  structure specified by the revised Task 03B contract.
- Verify every section range and direct membership resolves to ordered
  canonical blocks, tables, figures, and pages.
- Verify every core content record belongs to exactly one direct section and
  the inverse ordered-child relationship is exact.
- Verify printed-page-label observations distinguish physical PDF identity,
  page-tree labels, and visible printed labels.
- Test nested, skipped, repeated, absent, malformed, and ambiguous heading
  fixtures.
- Test exact, absent, conflicting, and appendix-specific printed-label
  fixtures.
- Verify the alias inventory is deterministic, provenance-backed, and contains
  no inferred cross-reference mentions or targets.
- Inspect representative hierarchy and printed-label outputs with on-demand
  review-cache renders.
- Confirm repeated execution yields identical sections, memberships, labels,
  aliases, and edges.
- Confirm no cross-reference mention extraction or candidate resolution was
  introduced.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Canonical sections have deterministic candidate identities, paths, source
  evidence, and exact content/page membership.
- Synthetic Task 03D roots remain valid containment anchors and all semantic
  sections are connected beneath them.
- Printed-page-label observations never overwrite physical PDF page numbers or
  indices.
- Unknown and conflicting hierarchy or label states are visible rather than
  silently forced.
- The reviewed target and alias inventory is sufficient for a future Task
  03E.1 contract to define supported cross-reference patterns and deterministic
  candidate resolution without reopening source transcription.
- No cross-reference mention or candidate records are emitted.
- No LLM, embedding model, retrieval index, or curator-only response content is
  used.
- The hierarchy remains connected to exact low-level anchors needed for later
  evidence verification.
- The outcome requests user review before Task 03E.1 is written.

## Handoff to Task 03E.1

Do not write the detailed Task 03E.1 execution contract until Task 03E is
accepted. Its intended scope is already fixed at the routing level:

- extract supported cross-reference mentions from canonical source text;
- preserve raw mention text, spans, and provenance;
- generate zero-or-more targets from the reviewed Task 03E section,
  printed-page, table, figure, document, and appendix aliases;
- record `resolved`, `ambiguous`, or `unresolved` state and deterministic
  evidence; and
- avoid LLM linking, embeddings, fuzzy semantic search, curator-only content,
  and retrieval-specific graph construction.

## Non-goals

- cross-reference mention extraction, pattern definition, candidate generation,
  or target resolution
- perfect semantic hierarchy for every irregular source
- response/general-response linking in Final EIR Volume 4
- semantic evidence selection or citation approval
- chunking, BM25 indexing, embeddings, or graph retrieval
- human page-usability or table-correctness judgments
- LLM-assisted hierarchy repair or entity linking
