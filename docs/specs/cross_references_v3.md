# Canonical Cross-Reference Contract v3

Status: **accepted Task 03E.5 production contract**. Gate B was explicitly
approved on 2026-08-03 before production implementation began. The accepted
human-owned implementation is `er_commons.cross_reference_enrichment`; the
earlier `cross_reference_materialization` package is behavioral reference code.

## Boundary and ownership

This contract adds document-scoped cross-reference mentions and deterministic
candidate evidence to canonical-extraction schema major v3. Canonical v1 and v2
remain strict and immutable. The accepted Task 03E.4 candidate
`exv1-2cba27c14e4a1aba72080c9803ce72f8dd728595bcd8176b60ffad777af4cf9b`
is the only production input authorized for the Appendix P pilot.

Task 03E.5 owns exact mention spans, the document target index, ordered local
candidates, local resolution status, unresolved reasons, and the handoff to a
later corpus pass. It does not own hierarchy correction, table or figure
content, response relationships, retrieval context assembly, or curator
judgment. Task 03F may append a separately sealed corpus-resolution result to
a stable mention ID; it may not rewrite a v3 document candidate.

Aliases and mentions remain different facts. An alias is target-side evidence.
A mention is a literal source span. Mention text cannot create a target name.

## Source eligibility

Only `canonical/blocks.jsonl` records satisfying all of these fields are
eligible source records:

- `content_layer == "body"`;
- `is_toc_row == false`; and
- `block_type` is `caption`, `footnote`, `list_item`, or `paragraph`.

Headings, visible-TOC rows, furniture-layer records, table cells, figure-image
content, and raw producer text are excluded. The following lexical surfaces
are also excluded even when an upstream record was classified as body text:

- a complete `Page <n> of <m>` record;
- a standalone target label such as `Table 1` or `APPENDIX P`;
- legal, statutory, regulatory, deed-recordation, and case citations;
- bibliography or reference-list entries; and
- a bare acronym or generic title such as `UWMP` or `Environmental Impact
  Report` without the complete supported named-document form.

Unsupported surfaces are counted in diagnostics and fixtures. They do not
produce canonical cross-reference records or graph edges.

Pattern policy v2 applies reference exclusion structurally. A section whose
normalized heading is `References`, `Bibliography`, or `Works Cited`, with an
optional numeric heading prefix, excludes every block assigned to that section
or one of its descendants. Citation-only blocks outside those sections are
also excluded when they begin with an author or organization followed by a
four-digit publication year. This keeps table-source notes from becoming local
section links without guessing from publication-type words.

## Supported mention grammar

The first production grammar is intentionally narrow:

1. `Section <numeric-key>`, where the key is one or more dot-separated decimal
   components. Singular and plural lead words are distinct grammar branches;
   every individually referenced key requires its own literal span.
2. `Appendix <letter-or-frozen-key>` for one target key per mention.
3. `Table <number-or-frozen-suffix>` and `Figure <number-or-frozen-suffix>`.
4. `Page <resolved-printed-label>` only in prose context. Page-furniture and
   legal recordation uses are unsupported.
5. A bounded named-environmental-document form: `Draft EIR for <title>` or
   `Final EIR for <title>`, where `<title>` is a title-cased name terminated by
   its parenthetical source citation. The rule is grammatical and does not
   enumerate fixture text. A generic document-type substring is not
   independently emitted inside the longer phrase. Whether the named document
   belongs to the deferred model corpus is determined from the checksum-bound
   sealed source manifest, not from a source-specific code constant.
6. Explicit grammar-defined malformed variants used only to exercise the
   `malformed_supported_form` unresolved reason.

For section mentions, explicit target qualifiers are classified before local
numeric lookup. `of this Agreement` remains eligible for local resolution.
Named external works such as `of the 1984 Agreement`, `of the SFPUC 2020
UWMP`, and `of the Project Operating Agreement` are unsupported external
section diagnostics. Legal forms such as `of the Act` or `of the Code` are
statutory diagnostics even when the section number has fewer than four digits.
The qualifier is never discarded and followed by an unscoped local lookup.

Matching uses Python Unicode-code-point offsets and half-open `[start, end)`
intervals. Every mention must satisfy
`canonical_text[start:end] == raw_text`. Mentions cannot cross records. At one
start position, the longest supported form wins. Otherwise non-overlapping
mentions remain in source order. A named-document form suppresses its nested
generic document-type signal.

## Target index and strict candidate policy

The candidate-owned target index has two evidence origins.

### Preserved Task 03E.4 aliases

All 323 accepted aliases and their targets are namespace-remapped into v3.
Every remapped entry retains exact upstream alias and target IDs. Exact alias,
section numeric-prefix, appendix-key, and printed-page lookup operate only on
this preserved set. Multiple matching alias rows that point to the same target
are one target candidate with ordered alias evidence. Different target IDs
remain different candidates.

### New verified table aliases

Task 03E.5 may add a table alias only when target-side canonical evidence
proves all of the following:

1. one eligible, non-TOC block consists only of the exact numbered table label;
2. the label block and canonical table share one physical page;
3. exactly one canonical table occupies that page;
4. the label and table are in the same document;
5. no conflicting numbered label exists for that table; and
6. the evidence records the label block, page, table, source checksum, and
   document-order positions.

Under the accepted Gate B contract, an exact numbered table label case-folds
to `table <number>` with
an optional dot- or hyphen-delimited alphanumeric suffix. No surrounding title,
punctuation, or prose is accepted as a label block.

This rule creates a v3-derived table alias, not an upstream Task 03E.4 alias.
The entry has no upstream alias ID but must retain the upstream table target ID.
Proximity from the mention to a table is never sufficient evidence. A table
mention resolves only through the independently built target index and the
following physical-page window.

### Five-page table-mention window

For an eligible `Table N` mention, consider only exact `table n` target-index
entries whose canonical table occupies a physical PDF page at absolute distance
zero through five from the mention's physical page. Page distance filters
already verified targets; it never creates a target alias.

- one distinct target in the window resolves with its page distance recorded;
- multiple distinct targets in the window remain ambiguous after aliases for
  the same target are deduplicated; and
- no target in the window remains unresolved with
  `outside_table_page_window` when an exact alias exists elsewhere.

An explicit qualified form such as `Table 1 in Reference 1`, `Table 1 from
Reference 1`, or `Table 1 of Reference 1` remains unresolved with
`qualified_external_table_reference`, even if a same-number local target falls
inside the window. The window resolves the Appendix P page-21 `Table 1` mention
to the verified table on page 22 and the page-34 `Table 5` mention to the
verified table on page 39. It deliberately does not perform unrestricted lookup
across the 222-page concatenated PDF.

### Figures remain fail-closed

The current OCR-free v3 pass performs no figure linking and authorizes zero
derived figure aliases. It does not inspect image text, use a visible label
embedded in figure artwork, or resolve from same-section, same-page,
nearest-page, image-order, or visual-proximity signals. This is an intentional
first-pass limitation, not evidence that figure links are unimportant.

The accepted Appendix P candidate has 27 figure records, including decorative
and split images, while 26 lack caption links. Every detected figure mention is
therefore emitted with zero candidates and
`accepted_target_type_unavailable`. Summary counts preserve the observable cost
of this omission for later evaluation. OCR or other figure-label extraction and
linking requires a separately reviewed future contract.

## Resolution and uncertainty

Candidate identity is the target record ID. Alias records are ordered evidence
for that target, not duplicate candidates. Candidates are ordered by target
type precedence, target document order, target ID, and evidence alias order.

- zero candidates: `unresolved` plus exactly one unresolved reason;
- one candidate: `resolved` and no unresolved reason; and
- more than one candidate: `ambiguous` and no unresolved reason.

The closed unresolved vocabulary is:

- `no_local_alias`;
- `deferred_cross_document`;
- `external_document_outside_corpus`;
- `accepted_target_type_unavailable`; and
- `malformed_supported_form`.

`deferred_cross_document` is used only when the literal target is identifiable
in the sealed Task 02 35-document model corpus. A named document outside that
scope uses `external_document_outside_corpus`. These remain local
`unresolved` records, not separate resolution states.

## Provenance and persisted record

Each cross-reference record contains the v3 candidate and document IDs, stable
mention ID, source block ID, mention class, literal text, exact charspan,
pattern version, lookup key, ordered candidates, status, nullable unresolved
reason, inherited source regions, and inherited raw links. Regions and raw
links are copied completely from the source block; the mention does not
synthesize narrower geometry or new lineage.

Every candidate cites a v3-local alias and target. Preserved aliases retain
both upstream IDs. A verified table alias has a null upstream alias ID and the
exact upstream table target ID. No edge may leave the v3 namespace.

## Identity, preservation, and support

V3 remaps the complete v2 namespace. Outside the declared categories below,
Task 03E.4 semantics and assets must remain exactly equivalent after narrow
candidate-ID normalization:

1. identity and schema;
2. cross-reference records;
3. the three cross-reference support files;
4. verified v3-derived table aliases and the corresponding alias inventory
   extension; and
5. terminal manifest, inventory, summary, and completion checksums.

All 323 upstream aliases must have exact bidirectional correspondence. New
table aliases are an explicit, separately counted extension and may target only
existing namespace-remapped tables. Current v3 authorizes no figure alias
extension; future support requires a separate contract revision and review.

The candidate owns:

- `support/cross_reference_target_index.json`;
- `support/cross_reference_summary.json`; and
- `support/cross_reference_preservation.json`.

The target index records every lookup key, evidence origin, candidate target,
and upstream correspondence. The summary reports eligible and excluded source
counts, supported forms, statuses, unresolved reasons, unsupported diagnostic
classes, and table/figure evidence dispositions. Preservation proves the exact
v2 remap, the bounded table-alias extension, all permitted differences, and no
undeclared change.

Publication remains atomic, no-clobber, and completion-last. Matching reuse
requires identity, managed-file inventory, checksums, support roles, source
input, and completion to reverify. A failed attempt remains inspectable without
a completion record.

## Fixture split and review isolation

Development fixtures own representative positive and negative cases, exact
text checksums, spans, candidates, and expected status. Frozen-review fixtures
include the repeated `Section 5.3`, deep section, `herein` adjacency, named
external document, table/figure generalization, true ambiguity, and
bibliography negative controls. Production tuning after opening frozen-review
expectations is forbidden; a mismatch changes the disposition or requires a
new versioned fixture set.

Gate B validated only the original specification, schema, fixtures, and
negative mutations. The behavioral MVP remains under
`er_commons.cross_reference_materialization`. The accepted human-owned
implementation is under `er_commons.cross_reference_enrichment`. Pattern
policy v2 is a post-production precision correction: it retains the v1 fixture
inventory, adds regression tests for the discovered false positives, and uses
an independent correction audit rather than claiming exact equivalence to the
known-flawed v1 behavior.

## Package decision

Python's standard-library regular-expression API provides the exact match
spans required by this closed grammar. The legal-citation surface is explicitly
unsupported, so a legal citation resolver does not simplify the authorized
work. No parsing dependency was added.
