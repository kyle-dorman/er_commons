# Canonical Semantic-Structure Contract v2

Status: **accepted Task 03E.3 implementation specification**.

## Boundary and ownership

This contract defines the Task 03E.4 join between immutable Task 03D.1 core
canonical records and the Task 03E.2d accepted-with-known-limitations hierarchy
correction. It is canonical-extraction schema major v2. Canonical v1 and
candidate `exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28`
remain immutable.

The extraction-ID algorithm remains RFC 8785 canonical JSON plus SHA-256 and
therefore retains the `exv1-` prefix. The identity payload changes and must
produce a different candidate ID. Schema v2 binds the complete v1 baseline,
both producer identities, producer comparison, hierarchy correction completion
and inventory, both semantic digest roles, this specification, schema, code,
bridge, correspondence report, and compact bounded-acceptance control.

Ownership remains separated:

- Docling owns raw items, pointers, roles, levels, text, geometry, and order.
- Task 03E.2b owns deterministic corrected roles, levels, and hierarchy.
- Task 03E.2d owns the Appendix P publication disposition and limitations.
- canonical v2 owns stable sections, membership, page-label resolution, target
  aliases, identity, invariants, and downstream isolation.

Detailed features, TOC entries, reconciliations, regimes, decisions,
ambiguities, and warnings stay in the checksum-pinned correction candidate.
Canonical records contain only compact evidence references. Bridge,
correspondence, preservation, and control verification are checksummed support
artifacts, not canonical record families or a fourth content representation.

## Versioned persisted shapes

The executable definitions live in
`benchmarks/er_bench/schemas/canonical_extraction/v2/semantic_structure.schema.json`.
Task 03E.4 shall combine these changed definitions with the unchanged v1 record
families into one closed v2 bundle. All JSON objects remain strict; undeclared
properties fail. JSONL arrays use their declared semantic order. JSON objects
used in identities use RFC 8785 bytes; materialized JSON and JSONL use stable
UTF-8, sorted keys, compact separators, and one terminal newline.

### Sections and mixed content

The existing `section` family is extended; no separate semantic-section family
is created. Every section requires:

- `section_kind`: `synthetic_body_root`, `synthetic_furniture_root`, or
  `semantic`;
- nullable `semantic_level` in 1–6;
- `section_path_ids`, the exact root-to-self ancestry;
- parent, heading, and ordered direct children;
- `inference_method`; and
- for semantic sections, a stable heading key and checksum-pinned correction
  evidence reference.

There is exactly one synthetic root for each populated layer. Synthetic roots
have no level or heading. Corrected hierarchy roots become direct children of
the body root at their heading positions. A semantic child level must be
strictly greater than its semantic parent's level. Missing levels are valid:
the accepted input includes level-3 roots and edges such as 1→3, 1→4, 2→6,
and 3→6. Paths encode ancestry, not numeric depth. Repeated heading text is
valid; heading stable keys and section IDs remain unique.

Each semantic section begins at its heading block. The heading is the section's
first direct child and is owned by exactly one section. Section extent is
implicit in the ordered tree: the subtree ends immediately before the next
heading at the same or a shallower accepted level. Redundant start/end offsets
are forbidden.

Blocks, tables, and figures retain one direct `section_id` and add a compact
placement value:

- `heading_owner` for the heading block;
- `direct_body` for ordinary direct body membership;
- `pre_root` for the two accepted unassigned pre-root items;
- `toc_content` for visible TOC material;
- `furniture` for retained furniture; and
- `inherited_nontext` for tables and figures inserted at their Task 03D.1
  mixed-order position under the deepest active semantic section.

Visible TOC rows remain ordinary body blocks under the body root and never
start sections. A TOC-derived alias may target only its reconciled body section.
Furniture stays under the furniture root. Tables and figures never own headings.
Caption blocks retain their existing membership and table/figure links.
`ordered_child_ids` must exactly invert parent and membership pointers in the
Task 03D.1 global mixed-content order; set equality is insufficient.

## Physical pages and printed labels

Physical page number is the stable one-based PDF identity. It is never replaced
by a printed label. Exactly one `page_label_observation` exists for every
physical page, including pages with no Docling item or visible footer.

Each observation records explicit PDF `/PageLabels` evidence, visible-footer
evidence, a resolved state (`resolved`, `unknown`, or `conflict`), a nullable
resolved value, and whether synthesized library defaults were rejected.
Evidence state is `present`, `absent`, or `conflict` with ordered source
references.

Resolution precedence is:

1. one explicit `/PageLabels` value resolves the page;
2. when explicit metadata is absent, one page-wide visible-footer consensus
   may resolve it after all anchored observations on that page agree;
3. differing explicit and visible evidence or multiple visible values is a
   conflict with a null resolved value; and
4. no qualifying evidence is unknown with a null value.

A raw hierarchy feature is evidence, not by itself a resolved canonical field.
Task 03E.4 must aggregate and validate the entire page before applying rule 2.
Synthesized pypdf defaults never count as source evidence. Appendix P has no
explicit `/PageLabels`; pypdf's `1`–`222` strings must be rejected. Its feature
file represents 221 pages, with 167 non-null visible labels and no item for page
2, but v2 must emit all 222 outcomes independently of item presence.

## Deterministic target aliases

`target_alias` is one new canonical family, serialized after assets and before
future cross references. It contains target-side names only; mention text,
source spans, and mention-derived candidates are forbidden.

One record represents one `(alias_kind, normalized_alias)` key and carries one
or more ordered targets. One target is `unique`; more than one is `ambiguous`.
Targets are limited to document, page, section, table, and figure records.
Appendix aliases target sections. Printed-page aliases require a resolved page
label. TOC evidence requires an exact reconciliation evidence reference and a
semantic body-section target; a TOC block can never be a target.

Normalization `nfc_nbsp_ascii_whitespace_casefold_v1` applies Unicode NFC,
maps NBSP to ASCII space, trims, collapses whitespace, and case-folds. It does
not remove punctuation, numbering, diacritics, or suffixes. Records are ordered
by document, then target-type precedence (`document`, `section`, `table`,
`figure`, `page`), first-target physical or mixed-content order, alias kind,
and normalized UTF-8 bytes. Targets within one ambiguous alias are also in
document order; sequences are contiguous.

## Cross-producer bridge

The bridge never assumes pointers or internal IDs are interchangeable. Every
row binds a stable item key, hierarchy-producer pointer, baseline-producer
pointer, Task 03D.1 canonical target, and disposition. It is justified by the
machine-pass producer comparison
`33574f6b15dc128a7bf58d6e2ab1a35c867ce1df493fe317a46bed1b8e8bf364`,
which aligned all 6,931 stable keys and all 159 artifact paths without an
unexpected change.

All 246 accepted headings map uniquely to canonical blocks. Of 4,571 direct
members, 2,255 map to blocks and 2,316 require an explicit disposition: 2,314
are descendants of the 19 Docling tables replaced by clean canonical tables,
and two are picture-suppressed list items. The only permitted unmapped
dispositions are therefore:

- `canonical_table_replacement_descendant`; and
- `canonical_figure_suppressed_descendant`.

Missing keys, duplicate stable keys, pointer disagreement, incompatible target
type, target collision, changed producer evidence, or any generic unmapped
reason is fatal. Tables and figures enter semantic order through Task 03D.1's
replacement positions, not by selecting an arbitrary descendant feature.
Validation receives the verified producer pointer/disposition index as a
separate input and requires its stable-key set and every row to match exactly;
the bridge payload is never allowed to authenticate its own pointers.

## Control provenance and limitations

The canonical identity and manifest carry a compact reference, not a copy, of
the bounded authorization. Verification fails closed unless all of these match:

- hierarchy candidate `hcorv1-aab01b14...469348b1`, status
  `complete_with_ambiguities`, 15 managed files, inventory canonical digest
  `8242a22a...35c3a`;
- semantic-file-set digest `75a0e36c...dd3d2` and reconstructed aggregate
  digest `c3036210...4db8`, which have distinct meanings;
- bounded-acceptance raw SHA-256 `53357371...328c`, authorization ID, status,
  Appendix P/222-page scope, non-corpus disposition, and the exact three
  authorized uses;
- all seven ordered limitation categories and exact semantic counts; and
- the producer comparison digest above.

The complete ambiguity and warning artifacts remain inherited evidence. The
two false table boundaries, R04/R05 attribution disagreements, Existing SSF
District level disagreement, and Task 03E.2a evaluation limitation are not
silently repaired or described as correct. The main-report page-2000 R06
control is not an Appendix P canonical warning; only the authorization's
limitation reference is retained.

## Identity, publication, and preservation

Task 03E.4 must issue a new candidate. Identity binds baseline candidate
completion/inventory, both producer completion/inventories, producer comparison,
correction completion/inventory, both semantic digests, bounded control,
schema, this specification, config, bridge, and owned code. Matching completed
candidates are reusable only after identity, inventory, completion, managed
file set, support files, and bounded control all reverify. Publication is
atomic, no-clobber, and completion-last; failures retain attempt evidence and no
completion record.

The old-to-new correspondence report permits only these categories:

1. identity and schema;
2. semantic sections and membership;
3. page-label resolution and observations;
4. target aliases; and
5. semantic support and completion.

After extraction-ID normalization, all undeclared Task 03D.1 semantics must be
byte-equivalent: document/page order, block/table/family/cell/figure/image
payloads, geometry, assets, observations, raw lineage, and page mixed-content
order. The completed Task 03D.1 candidate is never rewritten.

## Machine status and review isolation

Canonical machine status describes materialization integrity. The separate
source semantic disposition remains `accepted_with_known_limitations`; it may
not impersonate a strict quality pass. Inherited ambiguities and warnings
produce `complete_with_warnings` when materialization otherwise succeeds.
Unknown page labels and represented alias collisions are non-fatal. Missing
bridge coverage, hierarchy inconsistency, control drift, schema failure, or an
undeclared baseline difference is fatal.

Task 04 reviewer, usability, exclusion, disposition, and gold fields remain
forbidden. Task 03E.3 fixtures contain no cross-reference mentions. Task 03E.4
materializes only this contract; Task 03E.5 separately owns mention extraction
and resolution.

## Research rationale

JSON Schema Draft 2020-12 supplies closed structural shapes while project code
owns cross-record order, graph, and coverage invariants. Because v1 records are
closed and identity-bound, a parallel schema major is safer and reviewable
than weakening existing records. [JSON Schema Draft
2020-12](https://json-schema.org/draft/2020-12)

RFC 8785 provides deterministic, hashable JSON identity bytes without changing
the logical JSON model. It does not normalize Unicode strings, so alias
normalization remains an explicit semantic policy before serialization. [RFC
8785](https://www.rfc-editor.org/rfc/rfc8785.html)

ISO 32000-2 defines PDF page labels through the document page-label number tree;
library-generated ordinal strings in its absence are convenience values, not
source metadata. [ISO 32000-2 page-label
semantics](https://pdf-issues.pdfa.org/32000-2-2020/clause12.html#H12.4.2)
