# Missing Chapter Repair v1

Status: implemented and source-free qualified; final acceptance remains owned
by Task 06E after independent Astra review.

## Purpose

This policy restores a whole-chapter semantic target when the accepted body
structure omitted it. It is source-general and independent of response mentions.
It prefers an observed chapter heading split across retained source blocks. A
TOC-plus-children fallback is allowed only when no observed heading qualifies.

The policy extends the existing section family. It does not create a resolver
or copy source text. It changes only the decision-authorized semantic layer and
placement of recovered heading components; all other source-block facts remain
exact. Semantic-structure config `3.0.0`
retains the Task 06D repeated-heading projection and then applies this policy.
Config versions `1.0.0` and `2.0.0` retain their original behavior.

## Representations

`composite_semantic` represents one observed chapter heading in one or more
retained blocks. The first component is the heading owner; any remaining
components use `heading_component`. The section records every component ID and
both source stable keys. Its structural title is the normalized concatenation
of those observed blocks, corroborated by accepted TOC title evidence.

`derived_chapter` represents the bounded fallback. It has no heading block and
no source heading stable key. Its title is structural metadata derived from an
accepted TOC title, never a fabricated canonical block. It has its own section
ID, distinct from its first child.

Both representations require `chapter_marker`, `structural_title`,
`chapter_representation`, `heading_component_block_ids`,
`title_evidence_ids`, `start_record_id`, `following_boundary_record_id`, and a
non-owning `chapter_scope_content_ids` list and `derivation_ref`, plus a
checksum-pinned decision-stream `evidence_ref`. The scope does not replace any
content record's one canonical `section_id`. Exact page membership freezes
the inclusive physical-page range terminating strictly before a later-page
boundary, or on the same page before a later source-order boundary. A
following-heading boundary may separately freeze the first excluded mixed-order
record when that record precedes the retained heading on the same page; its
ID, nullable stable key, and order must revalidate exactly. A document-end
chapter requires an explicit accepted terminal boundary and no scope-start
record.

`start_record_id` is the first member of the complete logical chapter scope,
not necessarily the observed recovered-heading position. When a selected first
subsection precedes furniture-layer chapter-heading blocks in accepted mixed
order, its heading is the chapter start and the recovered components retain
their later positions.

## Eligibility

Every eligible decision requires one source, one exact chapter marker, one
accepted TOC title, a nonempty ordered child-anchor run, an evidenced start and
end, a parent and semantic level, and no existing whole-chapter target.
Children, recovered components, title evidence, and boundaries must be unique
and source-contained. Every child's frozen heading text must parse to the target
chapter marker. Historical section references resolve only through an exact
stable key, source/local-ID tail in the current candidate namespace, or the
validated Task 06D source-section correspondence. Every permitted enclosing
section freezes its source, stable key, heading block/text/order, parent, and
level; its heading must not parse as a numbered structural marker.
Every same-source body record in the accepted mixed-content interval is either
inside a frozen child subtree, an authorized recovered component, or frozen as
direct-content evidence with its ID, nullable stable key, type, global mixed
order, all pages,
and original owner. Direct owners resolve to the accepted parent or a named
unnumbered enclosure.

Observed-heading recovery additionally requires one complete heading block, or
adjacent source-order components on one start page, whose normalized
concatenation exactly equals the TOC title. Components must be non-TOC records
from the same accepted source. A furniture or `page_header` component requires
an explicit decision-level reclassification authorization; no global
`page_header` promotion is permitted.

Fallback additionally requires no recovered component and exactly one accepted
TOC destination equal to the evidenced body start. Children without a title,
a TOC title without a body range, conflicting titles or destinations,
noncontiguous children, and an unsupported gap fail closed. A conflict is
`review_required`; missing evidence is `rejected`.

## Projection and invariants

Projection consumes only eligible decisions. It preserves content identity,
text, geometry, and global order. It adds one chapter section, moves only the
explicitly authorized recovered heading components into that section, and
reparents only the frozen child-section run. Existing descendants remain with
those children. Shared unnumbered enclosures are never reparented. The chapter
instead records the exact ordered body interval from accepted start inclusive
to following boundary exclusive, including recovered components that become
body headings. Every declared heading component and every body record owned by
the selected child subtrees must occur inside that scope in source order. A
composite heading remains the unique direct `heading_owner` at its observed
position; it need not precede a child whose logical content starts earlier.
Direct-content evidence must be the exact complement of those components and
frozen child subtrees. Missing, extra, reordered, foreign, or
differently owned records fail before mutation. Unnumbered intervening
ancestors are permitted only when named by frozen enclosing-topology evidence;
unrelated sections fail closed. Incoming Task 06D
correspondence is merged into, not replaced by, the 06E addition map.

The validator requires exact root-to-self paths, acyclic ancestry, strictly
increasing semantic levels, one direct owner per content record, exact
source-order child inversion, a unique logical start record, complete selected
child-subtree scope, and a scope extent exactly equal to the decision.
Composite sections own exactly one heading at its truthful direct-child
position and every additional component; every `heading_component` is owned by
such a composite, including across root sections. Derived chapters own no
heading. Document-end evidence
uses the closed `document end` sentinel, no stable item key, the configured
physical-page count, and the order immediately after the maximum retained
source-content sequence. Existing semantic sections retain
the canonical-v2 heading invariant unchanged.
For fallback chapters, `start_record_id` must be both the first scope member and
the first descendant anchor; its normalized subsection marker must agree with
the chapter marker. Linking, navigation, and alias-order consumers use the
logical start for both restored representations. Compact v3 validation retains
physical-page membership and canonical marker text for these checks without
changing v1/v2 compact shapes.

Aliases are target-side evidence. The exact structural title and bare chapter
marker target the new whole-chapter section. A derived alias cites the accepted
chapter decision and never the response mention or first subsection. Linking,
navigation, and review consumers use `start_record_id` when a section has no
single heading. A genuine normalized spelling collision remains ambiguous;
each chapter-decision member is validated independently rather than requiring
the alias record itself to be unique.

## Provenance and correspondence

The closed chapter-decision record binds source, rule, decision kind,
representation, title and marker, recovered heading keys/blocks, TOC evidence,
destination pages, ordered child anchors, parent, semantic level, start and
following boundary, inclusive page extent, inference method, status, optional
human decision, and pending materialized target.

Projection publishes a compact one-to-one addition correspondence naming the
new target, retained source blocks, ordered child anchors, exact logical extent,
following boundary kind, exact ordered scope, and direct-content ownership.
Reuse revalidates candidate/source namespace for the target, retained
components, scope, and boundary; the expected decision stream from the
content-addressed extraction identity; direct ID/key/current-owner inverses;
chapter/target uniqueness; and strictly ordered nonoverlapping extents rather
than trusting schema shape alone.
Task 06G owns production replay;
Task 06H owns review of the materialized result.

## Reuse and stops

Source, conversion, producer, record-mapping, and unchanged document evidence
remain reusable under Task 06B. Routine qualification hashes only its new small
records and checked-in policy/schema. It does not open PDFs, load models, render,
or hash preserved large payloads.

Stop before projection on an unresolved schema choice, missing or conflicting
evidence, a changed frozen record, overlap, boundary crossing, content loss,
or a partial qualification population. A fallback needing interpretation must
receive a bounded Task 06E human decision before Task 06G.
