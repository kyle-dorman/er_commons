# Repeated heading repair v1

Status: **implemented and source-free qualified for Task 06D; separate Astra
acceptance is pending, and production replay remains owned by Task 06G**.

## Responsibility and rationale

`document_records.document_structure.repeated_heading_policy` owns the pure
classification rule for a chapter divider immediately followed by its repeated
opening-page heading. `repeated_heading_projection` owns topology validation,
projection and correspondence; `repeated_headings` is their small public facade.
The accepted hierarchy, mapped content, conversion and producer evidence remain
immutable inputs. The collection target index and exact resolver consume the
resulting aliases; they do not detect duplicates or select a preferred target.

An alias tie-breaker cannot repair this defect. It could hide one target from a
query, but the hidden target would still own a fragmented section subtree and an
empty divider extent. The semantic projection instead derives one logical
chapter from two retained source blocks, following the W3C PROV distinction
between source entities and a derived entity. The project records this in a
small decision/correspondence record and does not add RDF.

## Exact eligibility policy

Automatic repair requires all of the following:

1. The frozen candidate group contains exactly two accepted body headings.
2. The headings are consecutive same-level siblings and occur on adjacent
   physical pages.
3. Both headings parse as an exact one- or two-digit chapter marker plus title.
   NFC normalization, NBSP-to-space conversion, ASCII-whitespace folding and
   case folding are the only title transformations.
4. The first spelling is `NN TITLE`; the second is `NN | TITLE`. The vertical
   bar is the only ignored typography. Marker or title disagreement rejects the
   repair; fuzzy matching is forbidden.
5. Direct content and child-section ownership do not overlap, and both
   descendant page extents are present and disjoint. Content under either half
   is allowed and must be preserved. The complete union of both descendant
   extents must end strictly before the following chapter boundary; reaching
   the boundary page is a contradiction.
6. A later distinct same-level sibling under the same parent establishes the
   chapter boundary and must be the immediate next sibling after the pair. Its
   section identity, stable heading key, raw heading text and physical page are
   frozen in the decision.
7. Accepted TOC evidence has the same exact marker and title. Resolved
   destination pages, if present, may name either or both retained heading
   pages. A destination outside the pair or a contradictory title requires
   review. An unresolved printed token is retained as a limitation and never
   selects the anchor.

Nonadjacent headings, same-spelling repeats, different parents/levels,
furniture, TOC rows, marker/title differences and a divider followed by a
different chapter remain distinct with reason codes. Missing TOC evidence,
overlapping ownership/ranges, incompatible or absent boundaries, contradictory
destinations, and groups of cardinality other than two are review-required.
Missing extent evidence requires review. Missing source blocks, inserted
siblings, or changed projection topology fail validation.

The classifier operates on an immutable snapshot. Projection never rescans its
own result, so a two-heading repair cannot cascade into a third heading.
Repeated application of the same accepted decision is idempotent only after the
projected anchor, retained absorbed block, merged child order, complete extent,
and immediate following boundary all revalidate against the frozen decision.

## Projection and provenance

The first physical divider is the logical anchor because it provides the
complete chapter start. Its block remains `heading_owner`. The second opening
heading block remains in global source order as `direct_body` owned by the
logical chapter. All direct records formerly owned by the second section move
to the anchor, and its child sections are reparented to the anchor. Descendant
paths, contiguous section sequences and ordered mixed children are recomputed.

Only the absorbed semantic **section record** disappears. No block, table,
figure, source geometry, stable item key or substantive content is deleted.
Both old section targets correspond many-to-one to the new logical target, and
both raw heading spellings retain their own heading evidence while resolving to
that target. Raw spelling arrays preserve multiplicity—even rejected controls
may contain two identical strings—while section, block and stable-key evidence
identities remain unique. The accepted semantic-structure v2 schema remains
unchanged: its
single primary heading stays the divider, while the separate Task 06D decision
record carries the two-heading derivation. The executable decision schema is
[`repeated_heading_decision.schema.json`](../../benchmarks/er_bench/schemas/task06_recovery/v1/repeated_heading_decision.schema.json).

The projected logical target has no production ID until Task 06G derives a
fresh candidate identity. Task 06D records a pending logical target keyed by the
anchor stable key. Task 06G must bind the decision/schema/spec and current owned
code into the new structural identity, then write candidate-local old/new
correspondence. It must build alias seeds for both preserved headings before
grouping normalized aliases.

The build exposes candidate-local many-to-one correspondence separately from
the accepted canonical-v2 manifest, whose four-role support contract remains
unchanged. Task 06G must seal this compact correspondence beside its recovery
handoff rather than append an unversioned fifth canonical-v2 support role. Each
record carries both accepted old targets, both source and retained heading block
IDs, the verified logical content-page extent, the following boundary, and the
affected downstream products.

## Accepted Appendix A qualification

The source-free 06A packet at
`pipelines/brisbane_baylands/task_06_recovery_v1/06a/appendix_a_topology.v1.json`
was read as selected record evidence; no PDF, render, model, conversion, replay
or payload hash was used.

| Chapter | Divider | Opening | Children | Extent and next boundary | Result |
| --- | --- | --- | ---: | --- | --- |
| 06 Circulation | `sec000446`, `blk003146`, key `1f1d44…f8b7`, p311 | `sec000447`, `blk003147`, key `83dbb3…fe11`, p312 | 0 + 6 | source content p311–449; next Chapter 07 starts p452 | eligible; divider anchor |
| 08 Public Facilities Financing | `sec000748`, `blk004794`, key `058478…3e1`, p479 | `sec000749`, `blk004795`, key `b94ff6…d1c3`, p480 | 0 + 4 | source content p479–491; next Chapter 09 starts p492 | eligible; divider anchor |

The Chapter 08 divider's canonical block type is `paragraph`, but its accepted
hierarchy decision is body `heading`, level 3; eligibility uses that accepted
role. Chapters 04, 05, 07 and 09 remain single-heading negative controls.
Section 6.2 remains a nested level-4 child rather than being flattened.

The Chapter 06 TOC token `280` matches the p312 footer. The Chapter 08 token
`447` has no resolved destination; p480 shows footer `448` and p479 has no
footer evidence. Reviewed-navigation destination IDs are null for both. The
logical repair therefore carries no chosen physical TOC destination. This is
not a structural conflict and does not require a human exception.

## Invariants and replay handoff

Validation requires exact content-ID and global-order conservation, one direct
owner per record, acyclic parentage, increasing semantic levels, exact paths,
both heading blocks in source order, complete alias redirection, deterministic
output and explicit rejected/review-required outcomes. The qualification
consumer independently parses the full decision stream, requires zero pending
human-review groups, reconciles status counts, and proves the eligible stream is
its exact subset. Synthetic fixtures cover
both observed shapes, content under both halves, TOC destinations to either or
both pages, nonadjacent and legitimate same-title controls, parent/marker/title
differences, TOC/furniture, conflicting destinations, overlapping ownership,
missing boundaries, three-heading groups, changed inputs and repeated execution.

Task 06G may reuse the exact accepted conversion, producer, mapping and heading
evidence. It must rebuild Appendix A semantic sections/membership/aliases,
document linking/publication, and collection index/resolution/handoff under
fresh policy-bound identities. Unaffected sources use 06B's original-manifest
and sealed-input path. Task 06H reviews the materialized headings, children,
extent, aliases and evidence correspondence after replay. Task 06D acceptance
remains pending the separate Astra review requested by the user.

Canonical-v1 construction bypasses the repair path and does not import its
modules. Only canonical-v2 enables projection, so v1 output-affecting code stays
inside its accepted identity boundary while v2 binds the policy, schema and all
repair implementation modules.

## References

- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
