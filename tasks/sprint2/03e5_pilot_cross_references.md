# Task 03E.5: Pilot Canonical Cross-References

Status: **complete and accepted as of 2026-08-03**. Task 03F remains a separate
boundary; its Task 03F.1 contract is now active without reopening this task.
The corrected, human-owned Task 03E.4 candidate was the immutable input. Gate A
was approved with a precision-first direction, and Gate B was explicitly
approved before production implementation. Schema-v3 MVP reference candidate
`exv1-e3e81078dfb21b3d0718cd935004077e163dffc180bbc3d80f4a54391caa67f6`
passed the behavioral gate but is not accepted as the production
implementation. The user rejected its machine-oriented code and
fixture-specific named-document constant. The separate human-owned rewrite has
passed its original equivalence and maintainability gates, then failed the
user's resolved-link audit on external-section and bibliography false
positives. It remains immutable correction-baseline evidence. Pattern-policy
v2 corrected those failures and passed a bounded correction audit,
reproducibility, checksum reuse, and the full project check. The accepted
candidate is
`exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`.
No external parsing dependency or full-corpus scan was added.
The user chose an OCR-free first pass: detect figure mentions but skip figure
linking entirely, retain their unresolved disposition, and evaluate the impact
before designing a later figure-linking stage.
Table mentions use a strict five-physical-page window over independently
verified exact-number table targets. This resolves the page-21 `Table 1`
mention to page 22 while leaving qualified external forms such as `Table 1 in
Reference 1` unresolved.

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
- canonical document, block, table, figure, page, and section anchors
- checksum-pinned source and raw producer lineage
- the sealed Task 02 source manifest and its exact ordered 35-document
  `model_corpus` scope, used only to distinguish corpus-deferred documents from
  named external documents that Task 03F cannot resolve
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
- a narrow project-package extraction/resolution implementation with tiny
  fixtures; add an external parsing dependency only if the frozen inventory
  demonstrates a material fit
- a new immutable Appendix P canonical candidate under the existing
  completion-last lifecycle; it remaps the accepted Task 03E.4 namespace and
  adds cross-reference records, their support evidence, and terminal records
  while semantically preserving all 323 accepted aliases after identity
  normalization; it may add only independently verified v3-derived table
  aliases under the frozen Gate B rule
- deterministic mention, within-document resolution, and unresolved-reference
  summaries under the candidate-owned support roles
  `cross_reference_target_index`, `cross_reference_summary`, and
  `cross_reference_preservation`
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
  mention text may not invent or relabel a target. Table aliases require the
  separately specified target-side evidence before those mentions can resolve;
  current v3 authorizes no derived figure aliases.
- **Cross-document resolution is two-pass.** Other-document targets do not
  exist until Task 03F completes per-document semantic stage one and seals a
  corpus target index.
- **The canonical source graph differs from later graphs.** Task 05 owns
  comment/response relationships, Task 06 owns a curator traversal view, and
  Task 07 owns reviewed case-clustering edges.

## Bounded first action and approval stops

Use two explicit approval stops before production implementation.

**Gate A — read-only inventory proposal (approved 2026-08-03).** Before changing repository files or
adding code or dependencies, scan only eligible canonical body-block text in
the accepted Appendix P candidate. Eligible source records are exactly records
from `canonical/blocks.jsonl` with `content_layer == "body"`,
`is_toc_row == false`, and `block_type` in `caption`, `footnote`, `list_item`,
or `paragraph`. Exclude furniture, visible-TOC rows, headings, table-cell text,
figure-image content, and raw producer text. Report the observed forms, exact
text checksums, proposed half-open spans, negative controls, and proposed
development/frozen-review split, then stop for explicit user approval. The
proposal must include, at minimum:

- block 250: `Figure 1` and `Appendix A` in one source record;
- blocks 255 and 260: repeated `Section 5.3` mentions;
- block 261: two appendix mentions in one sentence;
- block 274: the deep section mention `Section 6.1.1.2`;
- blocks 279–280: multiple section mentions and `herein` context;
- block 335: `Table 1` body usage;
- block 405: a named external Draft EIR document reference outside the sealed
  35-document Task 03F corpus; and
- block 287 plus page-furniture/TOC controls: statutory `Section 10912`,
  `Section 21000`, and `Section 21080` plus non-body text must not become
  confident internal links.

**Gate B — checked-in contract fixtures (approved 2026-08-03).** Only after Gate A approval, write
the supported-grammar specification, executable v3 schema, small checked-in
fixture inventory, development/frozen-review split, and negative mutations.
Run their focused validation and stop again for explicit user review. Gate B
may add specification, schema, fixture, responsibility-owned contract
validation, and validation-test files, but it may
not add production mention detection, candidate generation, materialization,
publication code, an external dependency, or a generated Task 03E.5 candidate.

Only explicit approval of Gate B authorizes production implementation. Neither
gate authorizes a full-corpus scan.

## Plan / spec requirement

Freeze before implementation:

1. supported mention classes, source-record eligibility, overlap precedence,
   boundary handling, and exact half-open source-span rules;
2. target types and lookup behavior for exact aliases, section-number prefixes,
   appendix letters, and printed pages; mention text cannot create target
   aliases. A table alias may be added only from an exact standalone numbered
   label on the same physical page as exactly one canonical table, with no
   conflicting label. Eligible table mentions consider only exact verified
   targets at physical-page distance zero through five; multiple targets remain
   ambiguous, and qualified `in/from/of Reference N` forms remain unresolved.
   Current v3 authorizes zero derived figure aliases;
   explicit caption links or independently verified TOC-to-printed-page
   alignment may be considered only by a future reviewed contract revision;
3. deterministic normalization and collision handling;
4. the exact rule `0 candidates -> unresolved`, `1 -> resolved`, and `>1 ->
   ambiguous`; use `deferred_cross_document` only when the literal target is
   identifiable in the sealed 35-document Task 02 model-corpus scope, and use
   `external_document_outside_corpus` when the named document is outside that
   scope;
5. source record, literal matched text, half-open character span, inherited
   region, raw-lineage, pattern version, lookup key, candidate, and evidence
   fields;
6. ordering and ID rules;
7. schema-major-v3, identity, code-inventory, support, no-clobber reuse,
   completion-last publication, and failed-attempt consequences;
8. exact permitted differences from Task 03E.4: identity/schema,
   cross-reference records, the bounded verified-table-alias extension, the
   three named cross-reference support roles serialized as
   `support/cross_reference_target_index.json`,
   `support/cross_reference_summary.json`, and
   `support/cross_reference_preservation.json`, and terminal checksums only;
9. corpus target-index and second-pass handoff; and
10. unsupported forms and warning/failure policy, including legal/statutory and
    bibliography-like citations that are not canonical document references.

Production extraction and materialization began only after Gate B passed
explicit user review. Keep mention detection, target-index
construction, candidate generation, validation, comparison, identity, and
publication as distinct responsibility owners; do not place the stage in one
monolithic parser or application function.

The schema-major-v3 stage-one mention ID is candidate-scoped and stable within
the immutable candidate. Every candidate entry uses v3-remapped local
`alias_record_id` and `target_record_id` values so the v3 graph remains
referentially closed. Separate upstream alias and target evidence fields
preserve the exact accepted Task 03E.4 IDs. All 323 upstream aliases and their
targets must have exact bidirectional correspondence. A v3-derived table alias
has no upstream alias ID but must retain the exact upstream table target ID and
the frozen target-side label/page evidence. Current v3 authorizes no figure
alias extension; future support requires a separate contract revision and
review. Task 03F may publish a separate result referencing the mention ID and
corpus-index identity, but may not rewrite the local candidate list or status.

Character offsets are Python Unicode-code-point offsets into the source
block's `canonical_text`, expressed as a half-open `[start, end)` interval.
Mentions may not cross source records, and every record must satisfy
`canonical_text[start:end] == raw_text`. The mention inherits the complete
source block regions and raw links without synthesizing new provenance.

Freeze a closed unresolved-reason vocabulary containing at least
`no_local_alias`, `deferred_cross_document`,
`external_document_outside_corpus`, `accepted_target_type_unavailable`, and
`malformed_supported_form`, with exact precedence when more than one could
apply. Emit a canonical unresolved record only for text accepted by the frozen
supported grammar, including a grammar-defined malformed form. Legal,
statutory, bibliographic, or other unsupported reference classes produce
diagnostic counts and fixture evidence only; they do not produce canonical
cross-reference records or graph edges.

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
- Verify every candidate cites a v3-local alias record and target. Preserved
  aliases carry exact Task 03E.4 upstream alias and target IDs; a verified
  table alias carries a null upstream alias ID plus the exact upstream table
  target ID and independent label/page evidence.
- Verify every preserved v3 alias and target ID has exact bidirectional
  correspondence to Task 03E.4. Verify every derived table alias has no
  upstream alias, has an exact upstream table target, and satisfies the frozen
  target-side evidence rule. No canonical edge may leave the v3 namespace.
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
  Appendix P candidate and diagnoses unsupported surfaces explicitly without
  creating canonical records for them.
- Resolution state agrees mechanically with the candidate set.
- Other-document references remain explicit for Task 03F rather than being
  dropped or guessed when their target document is within the sealed corpus;
  named documents outside that corpus remain explicit terminal unresolved
  records and are not promised to Task 03F as resolvable work.
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

## Gate B review checkpoint

Gate B added only:

- `docs/specs/cross_references_v3.md`;
- `benchmarks/er_bench/schemas/canonical_extraction/v3/cross_references.schema.json`;
- the development, frozen-review, valid-contract, and negative-mutation
  fixtures under `benchmarks/er_bench/fixtures/canonical_extraction/v3/`;
- the contract-only validator under
  `src/er_commons/cross_reference_contract/`; and
- `tests/test_cross_reference_contract.py`.

The checked-in contract is deliberately asymmetric. Exact target-side table
labels can create a table alias only under the same-page/single-table rule;
the resulting exact-number targets are eligible for a mention only within a
five-physical-page window. Distance filters verified targets and never creates
one; multiple distinct in-window targets remain ambiguous, while qualified
external-reference forms remain unresolved. Appendix P figure records include decorative and
split images and almost all lack caption links. By explicit user decision, the
OCR-free first pass skips figure linking altogether: current v3 authorizes zero
derived figure aliases, keeps figure mentions visible but unresolved, and
reports their counts so the impact can be evaluated. The focused Gate B
contract suite keeps canonical v1/v2 strict. The user explicitly approved this
checkpoint before the production package and candidate were built.

## Behavioral MVP outcome

The responsibility-separated implementation lives under
`er_commons.cross_reference_materialization`. Detection, target indexing,
resolution, construction, validation, identity, publication, and workflow each
have named owners. Python's standard-library regular expressions were
sufficient for the frozen grammar, so no runtime dependency was added.

The completed candidate
`exv1-e3e81078dfb21b3d0718cd935004077e163dffc180bbc3d80f4a54391caa67f6`
contains 300 exact-span mentions over 2,246 eligible body blocks: 227 section,
20 appendix, 45 table, 7 figure, and 1 named-document mention. The two lexical
`page` hits were deed-recordation citations and were correctly routed to
diagnostics rather than canonical records. Local status is 261 resolved, 38
unresolved, and 1 ambiguous. The sole
ambiguous record is the frozen `Section 4` collision. All seven figure mentions
remain explicitly unresolved under the approved OCR-free policy.

The candidate preserves all 323 accepted Task 03E.4 aliases and their targets,
adds 11 independently verified table aliases, and adds zero figure aliases.
The page-21 `Table 1` resolves to the page-22 table at distance 1, and the
page-34 `Table 5` resolves to the page-39 table at the maximum accepted distance
of 5. Qualified external-reference table forms remain unresolved. The three
candidate-owned support roles record the target index, aggregate outcomes, and
zero-undeclared-difference preservation result.

Two fresh MVP builds were byte-identical. Completion-last publication, checksum
reuse, and retained-failure behavior passed. The MVP is immutable behavioral
reference evidence, not the accepted production implementation.

## Human-owned rewrite outcome

The accepted implementation lives under `er_commons.cross_reference_enrichment`.
It replaces fixture-shaped procedural code with named domain concepts:
`MentionPolicy`, `MentionRule`, `BlockExclusion`, `DetectedMention`,
`TargetIndex`, `TargetIndexBuilder`, `MentionResolver`, `Resolution`,
`CandidateSource`, and `CrossReferenceCandidateBuilder`. Detection, policy,
catalog classification, indexing, resolution, construction, validation,
comparison, identity, storage, publication, and workflow have separate public
owners. The workflow is a short orchestration shell over those responsibilities.

Named environmental documents now use the bounded grammatical forms
`Draft EIR for <title>` and `Final EIR for <title>`. The detector contains no
Genentech or other fixture-specific document constant. A new unseen-title test
passes, and deferred-versus-external disposition is driven by target-side keys
derived from the checksum-bound sealed model-corpus manifest. Mention text does
not invent corpus membership.

Human-owned candidate
`exv1-4a65944e4ce99a445953ea2904ca0e0c4b20fdd5412e9b89e7b6dac0254cc464`
exactly matches the sealed MVP across all 19 canonical record and
cross-reference support paths after normalizing only candidate-derived IDs and
the corresponding target-index checksum pointer. Comparison
`cmpv1-e8c14b267c556a7609cde4275223e7210ee0bd699b53c4daac29e18988f93d65`
has zero mismatches. The first comparison attempt correctly stopped on a
numeric-prefix parsing difference and retained both failed builds without
completion records; the readable helper was corrected before publication.

The accepted candidate therefore retains the reviewed behavior: 300 mentions,
261 resolved, 38 unresolved, one ambiguous `Section 4`, 11 verified table
aliases, zero figure aliases, and seven unresolved figure mentions. Two fresh
builds were byte-identical, and checksum reuse passed. `make fix`, `make check`,
and `git diff --check` passed with strict mypy and 435 tests. This task did not
scan or resolve the other 34 model-corpus PDFs. At this rewrite checkpoint,
Task 03F remained provisional and required later review and activation.

## Pattern-policy v2 correction outcome

The user audit found five incorrect resolved section links: two bibliography
occurrences, two references qualified by another named document, and one
low-numbered statutory reference. The same correction pass found three
already-unresolved mentions qualified by the separate Project Operating
Agreement. Pattern-policy v2 makes source scope and qualifier semantics
explicit:

- sections headed `References`, `Bibliography`, or `Works Cited`, plus all
  descendants, are excluded through accepted `section_id` relationships;
- author-year citation-only blocks outside those sections are excluded without
  requiring a publication-type keyword;
- `of this Agreement` remains eligible for local resolution;
- named external agreements, plans, reports, assessments, EIRs, and UWMPs are
  external-section diagnostics; and
- `of the Act` and `of the Code` are statutory diagnostics regardless of the
  number of digits in the section key.

Corrected candidate
`exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`
contains 292 mentions: 256 resolved, 35 unresolved, and one ambiguous. It
retains all 45 table mentions and the unchanged five-page policy. Independent
correction comparison
`cmpv1-78eca6da7a13a0202d9dfe673902e5b1579b077eaca7a887917c16ad061cd74c`
proves 17 preserved paths exact, eight policy-explained removals, zero added
mentions, zero changed shared mentions, and zero unexplained removals. Two
fresh builds were byte-identical, checksum reuse passed, and failed prepublish
audit attempts were retained without completion records. `make fix`, `make
check`, and `git diff --check` pass with strict mypy and 439 tests.

The final review found two literal appendix links whose surrounding prose does
not match the named appendix contents. Visual inspection confirmed that both
letters are printed in the source PDF, so they are source-authored
cross-reference noise rather than extraction mistakes. By explicit user
decision, Task 03E.5 retains literal source fidelity and does not add
document-specific B-to-C or D-to-E corrections. This bounded noise is accepted
for the first pass and must be handled by downstream retrieval/query-time model
reasoning if encountered. It does not authorize a general semantic override
layer or weaken the structural and qualifier exclusions above.
