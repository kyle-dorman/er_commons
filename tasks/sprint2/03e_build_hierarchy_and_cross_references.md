# Task 03E: Build Hierarchy and Cross-Reference Candidates

Status: **provisional**. Revise this contract from the accepted Task 03D outcome
before activating it.

## Abstract

Derive the canonical section hierarchy, printed-page-label observations, and
explicit cross-reference candidate graph from the core records produced by
Task 03D. Preserve the signals and ambiguity behind every inferred relationship
rather than forcing uncertain headings, page labels, or references into a
single authoritative target. Do not use an LLM or define retrieval passages.

## Goal

Represent the Draft EIR as both an ordered document and a provenance-preserving
semantic graph so later curation, retrieval, citation rendering, and human
review can navigate sections and references without weakening exact page/block
anchors.

## Inputs

- completed Task 03B canonical contract
- completed Task 03D core canonical records and raw mappings
- Docling heading labels, levels, group structure, and body order
- PDF outline/page-label metadata where present
- source titles, appendix identities, visible numbering, and canonical page
  renders
- current Docling
  [heading-hierarchy options](https://docling-project.github.io/docling/reference/pipeline_options/)

## Outputs

- canonical section records and heading paths
- printed-page-label observations with method and provenance
- explicit cross-reference mention records
- zero-or-more candidate target records per mention, with resolution state and
  deterministic evidence for each candidate
- section/page/block graph edges that preserve exact low-level anchors
- fixtures covering nested numbering, missing levels, ambiguous references,
  appendix aliases, page-label mismatches, and unresolved targets
- validation summaries for hierarchy and graph integrity

## Research / learning checkpoint

Inspect how heading levels are produced by the selected Docling configuration.
The layout model may identify a region as a section header without establishing
its level; bookmarks, numbering, typography, and learned or heuristic hierarchy
inference are separate signals. Review current research on
[document-tree reconstruction](https://aclanthology.org/2024.findings-emnlp.628/)
and [reading-order relations](https://aclanthology.org/2024.emnlp-main.540/)
to distinguish a linear sequence from a semantic section tree.

The outcome must explain:

- **Reading order and hierarchy are different latent structures.** A correct
  sequence of blocks does not determine whether a heading is a sibling, child,
  caption, or continuation.
- **PDF outlines are evidence, not ground truth.** Bookmarks may be incomplete,
  stale, overly coarse, or absent even when visible headings are clear.
- **Heading induction is multi-signal inference.** Numbering patterns,
  typography, indentation, bookmarks, parser labels, and prior heading context
  can disagree. Preserve the evidence and deterministic rule that produced a
  level.
- **Printed labels differ from PDF page identity.** Keep zero- or one-based
  internal indices, one-based PDF page numbers, page-tree labels, and visible
  printed labels distinct. Appendix page `3.5-17` is not interchangeable with
  PDF page 17.
- **Cross-reference resolution is entity linking.** “See Appendix G, Section
  4.2, page 3.5-17” requires mention parsing, aliases, candidate generation, and
  target resolution. Precision errors create false evidence paths; recall
  errors hide useful context.
- **Ambiguity belongs in the data model.** Store the raw mention, candidate set,
  rule/evidence, and `resolved`, `ambiguous`, or `unresolved` state. Do not
  convert uncertainty into a fabricated single edge.
- **Semantic units and physical anchors coexist.** A section or table can be a
  human citation unit while one or more exact pages, blocks, and table regions
  remain the verification units.
- **Hierarchy quality affects later LLM evaluation.** Heading paths influence
  BM25 terms and passage boundaries; wrong links can inflate apparent
  retrieval recall or feed irrelevant context that looks authoritative.

## Plan / spec requirement

Write a hierarchy and linking specification before implementation. It must
define:

1. heading-signal precedence and conflict representation;
2. section start/end and containment rules;
3. synthetic root and unknown-level behavior;
4. title, appendix, section, table, figure, and page-label alias normalization;
5. printed-label observation methods and confidence/evidence fields;
6. supported cross-reference patterns and intentionally unsupported language;
7. candidate generation, deterministic resolution, and ambiguity rules;
8. graph-edge types and referential-integrity invariants;
9. whether failures are fatal, warnings, or unresolved records; and
10. how later tasks may extend the graph without rewriting canonical source
    transcription.

Prefer deterministic parsing and explicit candidate records. Do not add an LLM
linker, embeddings, fuzzy semantic search, or a general knowledge-graph
framework.

## Review pass

- **Hierarchy fidelity:** inspect nested, skipped, repeated, and appendix-specific
  heading patterns.
- **Identity discipline:** verify printed labels never replace physical PDF
  page identity.
- **Linking precision:** ensure uncertain aliases or references produce
  candidate or unresolved records rather than confident false links.
- **Provenance:** every inferred section and edge retains the source blocks and
  rule that produced it.
- **Downstream safety:** graph metadata helps curation and retrieval without
  introducing curator labels or target-facing gold information.

## Validation

- Validate section paths and parent/child edges as an acyclic rooted forest per
  document or the exact structure specified in Task 03B.
- Verify every section range resolves to ordered canonical blocks and pages.
- Verify page-label records distinguish PDF and printed identities.
- Test exact, aliased, ambiguous, missing, and malformed cross-reference
  fixtures.
- Confirm unresolved references remain discoverable and no mention disappears.
- Inspect representative hierarchy and reference outputs against page renders.
- Confirm repeated execution yields identical sections, candidates, and edges.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Canonical sections have deterministic identities, paths, source evidence, and
  exact block/page membership.
- Printed-page-label observations never overwrite PDF page numbers or indices.
- Every supported cross-reference mention is preserved with zero or more
  candidate targets and an explicit resolution state.
- Ambiguity and unsupported patterns are visible rather than silently dropped.
- No LLM, embedding model, retrieval index, or curator-only response content is
  used.
- The hierarchy remains connected to exact low-level anchors needed for later
  evidence verification.
- The outcome requests user review before Task 03F.

## Non-goals

- perfect resolution of every natural-language reference
- response/general-response linking in Final EIR Volume 4
- semantic evidence selection or citation approval
- chunking, BM25 indexing, embeddings, or graph retrieval
- human page-usability or table-correctness judgments
- LLM-assisted hierarchy repair or entity linking
