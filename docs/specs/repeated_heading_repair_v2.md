# Repeated heading repair v2

Status: **implemented for the user-approved Task 06D boundary amendment;
production replay remains owned by Task 06G**.

## Responsibility and preserved behavior

The v2 policy retains v1's semantic-projection owner, exact divider/opening
syntax, adjacent-page pair requirement, immediate same-level sibling boundary,
TOC checks, no-fuzzy-match rule, deterministic divider anchor, complete content
conservation, alias redirection, and many-to-one correspondence. It does not
implicitly discover heading pairs beyond the four explicitly qualified groups.
The accepted v1 policy
and qualification-v6 evidence remain immutable historical inputs.

V2 corrects one evidence-model defect: a following chapter divider may occur
later on the same physical page as the preceding chapter's final records. Page
numbers alone cannot order records within that page. Eligibility therefore
requires both of these independent conditions:

1. The selected boundary is the immediate next same-level sibling under the
   same parent.
2. Every content record in both candidate subtrees occurs before the boundary
   heading in the canonical global record order.

The combined candidate page extent may end on, but never after, the boundary
page. Same-page overlap is accepted only when exact record order proves that
all preceding-chapter content comes before the boundary heading. A descendant
at or after the boundary record fails closed. Missing order evidence also fails.

## Exact eligibility policy

An eligible decision contains exactly two accepted body headings on adjacent
physical pages. They are consecutive same-level siblings with the same parent,
chapter marker, and normalized title. The first spelling is `NN TITLE`; the
second is `NN | TITLE`. Their ownership and page extents are present and
nonoverlapping, and their content identities do not overlap. Accepted TOC
evidence must name the same chapter and may resolve only to the retained pair.

A distinct later chapter heading must be the immediate next sibling. Its
section ID, stable key, raw text, page, parent, level, sibling position, and
canonical record order are revalidated during projection. The candidate
subtrees' exact child references, page extents, membership, and global record
order are likewise revalidated. Projection preserves every content record and
its order, removes only the absorbed semantic section, and retains both physical
heading blocks.

Nonadjacent headings, incompatible parents or levels, marker/title differences,
TOC rows, furniture, missing extents, missing order evidence, inserted siblings,
cross-boundary descendants, contradictory destinations, and ambiguous groups
remain rejected or review-required according to the existing v1 distinctions.

## Appendix A amendment

The complete production-shaped topology establishes these boundaries:

| Repaired chapter | Retained extent | Immediate following boundary |
| --- | --- | --- |
| 06 Circulation | pages 311-451, with all records before the boundary | `07 INFRASTRUCTURE`, `sec000662`, `blk004435`, page 451 |
| 07 Infrastructure | pages 451-479, with all records before the boundary | `08 PUBLIC FACILITIES FINANCING`, `sec000748`, `blk004794`, page 479 |
| 08 Public Facilities Financing | pages 479-491, with final page-491 record before the boundary | `09 IMPLEMENTATION`, `sec000783`, `blk004997`, page 491 |
| 09 Implementation | pages 491-501, with all records before the boundary | `APPENDICES`, `sec000798`, `blk005082`, page 501 |

The page-491 Chapter 08 records precede the Chapter 09 divider in canonical
record order. The divider belongs to its own Chapter 09 section. V2 therefore
does not truncate the truthful Chapter 08 page extent and does not assign the
Chapter 09 divider to Chapter 08.

The user selected the earlier plain-form headings as the true boundaries on
2026-09-12. Applying the same accepted rule to the complete sibling topology
qualifies Chapters 07 and 09 as well; their bar-form heading blocks remain
retained content while their duplicate semantic sections are absorbed.
Qualification v8 must derive the complete sibling topology from
the sealed canonical and hierarchy records, preserve qualification v6, bind
this policy and the v2 decision schema, and carry the later bar-form headings
as explicit unchanged controls. It must publish completion last and contain no
PDF, image, model, extraction, or conversion access.

## Replay handoff

Task 06G binds the v8 qualification, this policy, the v2 decision schema, the
current implementation bundle, and all accepted upstream seals into fresh
identities. It rebuilds Appendix A structure and downstream products only.
Task 06H remains responsible for human review of the materialized result.
