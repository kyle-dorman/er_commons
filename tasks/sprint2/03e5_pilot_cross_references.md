# Task 03E.5: Pilot Canonical Cross-References

Status: **active and ready to start as of 2026-08-03**. The corrected,
human-owned Task 03E.4 candidate is accepted as this task's immutable input.
No Task 03E.5 implementation, dependency installation, or generated artifact
has started; the first action is the bounded inventory and specification gate
below.

## Abstract

Pilot deterministic cross-reference mention extraction and within-document
candidate resolution on the accepted Appendix P semantic candidate. Preserve
exact source text spans and provenance, generate zero-or-more targets from a
candidate-owned index derived from accepted aliases and explicitly specified
structural keys, and retain resolved, ambiguous, or unresolved local states
with explicit cross-document deferral reasons.

This document-scoped task cannot resolve references to canonical targets in
other Draft EIR PDFs that have not yet been extracted. Preserve those mentions
as explicit unresolved records with a deferred reason for Task 03F's corpus
second pass; unavailable targets cannot become alias-based candidates.

## Goal

Validate a provenance-preserving canonical mention and candidate contract
without using LLM linking, embeddings, fuzzy semantic search, curator-only
response content, or retrieval-specific graph construction.

## Inputs

- accepted Task 03E.4 semantic candidate
  `exv1-2cba27c14e4a1aba72080c9803ce72f8dd728595bcd8176b60ffad777af4cf9b`,
  its `complete_with_warnings` completion, 25 candidate-owned files, and exact
  222-page/248-section/3,706-block/19-table/27-figure record scope; pin the
  completion record at
  `6746089db221ff933634c437d16a5ce53e049429df9b8c4d821cc9366e07aa49`,
  artifact inventory at
  `b7e00444914b1565558c364ecda248d9ada515d5f924466e470566ed466490f5`,
  manifest at
  `c4b1dbb407b8398a57b449e92dee7b8aa082cb964978de679dbd807396cd4981`,
  and empty v2 cross-reference stream at
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- final Task 03E.4 comparison report
  `cmpv1-3b06172ae6b4ca1c2bdb049a57cee8d85b37e78673626306e47f4b09cedbb890`,
  with zero mismatches across 25 candidate files and 31 review files
- Task 03E.4 provenance showing that hierarchy acceptance originates in the
  Task 03E.2d bounded-acceptance record and remains
  `accepted_with_known_limitations`
- all 323 accepted Task 03E.4 target aliases: document, semantic-section,
  appendix, and resolved printed-page aliases; the accepted candidate contains
  no materialized table or figure aliases
- canonical block, table, figure, page, and section anchors
- checksum-pinned source and raw producer lineage
- immutable canonical-extraction v1 cross-reference shape and semantic v2
  schema, whose executable contract intentionally requires
  `cross_references == []`; Task 03E.5 must define a new schema-major contract
  rather than weakening v1 or v2
- maintained open-source options for deterministic citation and reference
  parsing, evaluated before adding custom parsing glue

## Outputs

- a supported mention-pattern and candidate-resolution specification plus a
  frozen fixture inventory before production code
- canonical-extraction schema major v3, fixtures, and responsibility-owned
  cross-record validation for literal mentions, half-open exact character
  spans, ordered candidates, evidence, unresolved reasons, and deferred
  cross-document resolution; v1 and v2 remain strict and immutable
- package-backed extraction/resolution code with tiny fixtures
- a new immutable Appendix P canonical candidate under the existing
  completion-last lifecycle; it remaps the accepted Task 03E.4 namespace and
  adds cross-reference records, their support evidence, and terminal records
  while semantically preserving all 323 accepted aliases after identity
  normalization
- deterministic mention, within-document resolution, and unresolved-reference
  summaries
- independent preservation evidence against Task 03E.4
- a sealed candidate-owned target index and exact alias/index handoff to Task
  03F; it is document-scoped evidence, not the later corpus index

## Research / learning checkpoint

Compare Python's standard-library regular-expression span API with maintained
deterministic citation utilities against the exact source forms observed in
Appendix P. Python match objects expose exact start/end spans
(<https://docs.python.org/3/library/re.html#re.Match.span>). `eyecite` is a
maintained legal-citation extractor, but its default resolution is oriented to
legal resources and may drop citations it cannot definitively resolve
(<https://freelawproject.github.io/eyecite/find.html>,
<https://freelawproject.github.io/eyecite/resolve.html>). Evaluate it only for
the legal-citation boundary; do not add it or another broad dependency unless
the frozen fixtures show a material fit. JSON Schema Draft 2020-12 remains the
closed shape layer for the new schema major
(<https://json-schema.org/draft/2020-12>).

The outcome must explain:

- **Aliases and mentions are separate data.** Task 03E.4 defines potential
  targets; this task locates source spans that may refer to them.
- **Hierarchy acceptance remains upstream.** This task inherits Task 03E.2d's
  bounded acceptance through Task 03E.4 and does not reinterpret it.
- **Candidate generation is not confident resolution.** Zero, one, or several
  candidates remain visible with deterministic evidence.
- **Local status and later work are separate.** Zero, one, and more than one
  candidates mechanically mean `unresolved`, `resolved`, and `ambiguous`.
  `deferred_cross_document` is an unresolved reason, not a fourth local status.
  Task 03F appends a separate result that refers to the stable mention ID; it
  does not rewrite the sealed per-document record.
- **Structural keys are target-side evidence.** A mention such as `Section
  5.3` may match the exact numeric prefix of an accepted section alias, but
  mention text may not invent or relabel a target. Table and figure aliases
  require separately specified target-side evidence before those mentions can
  resolve.
- **Cross-document resolution is two-pass.** Other-document targets do not
  exist until Task 03F completes per-document semantic stage one and seals a
  corpus target index.
- **The canonical source graph differs from later graphs.** Task 05 owns
  comment/response relationships, Task 06 owns a curator traversal view, and
  Task 07 owns reviewed case-clustering edges.

## Bounded first action

Before adding code or dependencies, scan only canonical body-block text in the
accepted Appendix P candidate and freeze a small checked-in fixture inventory.
Exclude furniture, visible-TOC rows, headings used only as targets, table-cell
text, figure-image content, and raw producer text from the first pilot source
surface. The inventory must include, at minimum:

- block 250: `Figure 1` and `Appendix A` in one source record;
- blocks 255 and 260: repeated `Section 5.3` mentions;
- block 261: two appendix mentions in one sentence;
- block 274: the deep section mention `Section 6.1.1.2`;
- blocks 279–280: multiple section mentions and `herein` context;
- block 335: `Table 1` body usage;
- block 405: a named external Draft EIR document reference; and
- block 287 plus page-furniture/TOC controls: statutory `Section 10912` and
  non-body text must not become confident internal links.

Record exact canonical text checksums and half-open character spans. Split the
fixtures into development and frozen review cases before pattern tuning. This
inventory is evidence for the specification, not permission to run the full
corpus.

## Plan / spec requirement

Freeze before implementation:

1. supported mention classes, source-record eligibility, overlap precedence,
   boundary handling, and exact half-open source-span rules;
2. target types and lookup behavior for exact aliases, section-number prefixes,
   appendix letters, and printed pages; table/figure mentions are detected but
   remain unresolved because Task 03E.4 contains no accepted table/figure
   aliases, and mention text cannot create target aliases;
3. deterministic normalization and collision handling;
4. the exact rule `0 candidates -> unresolved`, `1 -> resolved`, and `>1 ->
   ambiguous`; use the `deferred_cross_document` unresolved reason only when
   the literal mention identifies a target document outside Appendix P;
5. source record, literal matched text, half-open character span, inherited
   region, raw-lineage, pattern version, lookup key, candidate, and evidence
   fields;
6. ordering and ID rules;
7. schema-major-v3, identity, code-inventory, support, no-clobber reuse,
   completion-last publication, and failed-attempt consequences;
8. exact permitted differences from Task 03E.4: identity/schema,
   cross-reference records, cross-reference support, and terminal checksums
   only;
9. corpus target-index and second-pass handoff; and
10. unsupported forms and warning/failure policy, including legal/statutory and
    bibliography-like citations that are not canonical document references.

Do not implement until the specification, executable schema, fixtures, and
negative mutations pass review. Keep mention detection, target-index
construction, candidate generation, validation, comparison, identity, and
publication as distinct responsibility owners; do not place the stage in one
monolithic parser or application function.

The schema-major-v3 stage-one mention ID is candidate-scoped and stable within
the immutable candidate. Every candidate embeds the accepted Task 03E.4 alias
record ID, target ID and type, lookup key, and match method; target IDs are
restricted to the exact accepted alias-target set. Task 03F may publish a
separate result referencing the mention ID and corpus-index identity, but may
not rewrite the local candidate list or status.

Character offsets are Python Unicode-code-point offsets into the source
block's `canonical_text`, expressed as a half-open `[start, end)` interval.
Mentions may not cross source records, and every record must satisfy
`canonical_text[start:end] == raw_text`. The mention inherits the complete
source block regions and raw links without synthesizing new provenance.

Freeze a closed unresolved-reason vocabulary containing at least
`no_local_alias`, `deferred_cross_document`,
`accepted_target_type_unavailable`, `malformed_supported_form`, and
`unsupported_reference_class`. Unsupported text remains visible in diagnostic
counts and never becomes a confident edge.

## Review pass

- **Package leverage:** maintained parsing is used where it clearly fits.
- **Traceability:** every mention resolves to literal canonical text and exact
  low-level anchors.
- **Uncertainty:** no candidate is silently forced to one target.
- **Scope:** within-document resolution is distinguished from deferred
  cross-document work.
- **Source eligibility:** furniture, TOC rows, target headings, and unsupported
  table/figure source surfaces cannot leak into the body-block pilot.
- **Schema ownership:** v3 adds mention semantics without weakening the strict
  empty-cross-reference v2 contract.
- **Leakage:** no Final EIR response, curator label, usability field, or
  benchmark evidence enters the canonical graph.

## Validation

- Test section, appendix, page, table, figure, document, malformed, repeated,
  overlapping, ambiguous, unresolved, statutory, bibliography-like, furniture,
  TOC, and deferred cross-document fixtures.
- Verify exact source spans, regions, aliases, candidates, status, evidence, and
  deterministic ordering.
- Require `canonical_text[start:end] == raw_text` for every mention and preserve
  the complete source block and raw lineage unchanged.
- Verify candidates target only accepted canonical target types.
- Verify every candidate cites an accepted alias record and its exact target.
- Report full-document mention counts by supported class, resolution status,
  unresolved reason, and source eligibility; a zero count for a supported
  class is an unsupported outcome unless the frozen inventory predicted it.
- Require exact preservation of all Task 03E.4 records and assets outside the
  four declared difference categories after extraction-ID normalization.
- Require a mutation suite proving wrong span endpoints, reordered candidates,
  status/candidate disagreement, unsupported targets, self-authenticating
  evidence, TOC/furniture leakage, and undeclared Task 03E.4 differences fail.
- Confirm repeat execution and fresh staging are byte-identical.
- Verify checksum-valid reuse and one retained simulated failure without a
  completion record.
- Confirm no LLM, embedding, fuzzy semantic retrieval, response inventory, or
  curator decision enters the stage.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Supported mentions have exact text, spans, provenance, candidates, and
  deterministic evidence.
- The pilot consumes only eligible canonical body blocks from the accepted
  Appendix P candidate and records unsupported surfaces explicitly.
- Resolution state agrees mechanically with the candidate set.
- Other-document references remain explicit for Task 03F rather than being
  dropped or guessed.
- The canonical cross-reference output is sufficient to build a sealed corpus
  second pass without mutating completed per-document stage-one artifacts.
- Task 06 can later consume canonical edges without owning extraction or
  resolution semantics.
- The implementation is human-owned: each stage responsibility is locatable,
  owner-level tests avoid private-sequence coupling, and the public workflow is
  a short orchestration shell.
- The outcome requests user review before Task 03F activates.

## Non-goals

- full-corpus or cross-document resolution
- response/general-response links in Final EIR Volume 4
- case clustering or split-leakage edges
- semantic evidence selection or citation approval
- graph retrieval, BM25, embeddings, or LLM entity linking
- creating or repairing target aliases from mention text
- mutating Task 03E.4 hierarchy, labels, aliases, canonical text, geometry,
  tables, figures, assets, observations, or accepted controls
- cross-record, table-cell, figure-image, or image-only mention extraction
- legal or bibliographic linking beyond the frozen supported grammar
- Task 03F orchestration, corpus-index publication, or restartability work
- manual forced resolution or document-specific exception tables
- corpus-wide precision, recall, or generalization claims
