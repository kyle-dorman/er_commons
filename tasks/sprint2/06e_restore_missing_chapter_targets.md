# Task 06E: Restore Missing Chapter Targets

Status: **complete and accepted; Astra accepted the v12 functional
implementation and the contract-preserving v13 maintainability cleanup passed
independent equivalence review**.

## Abstract

Restore independently evidenced chapter targets that are missing from the main
Draft EIR. Prefer recoverable body chapter headings. When those headings are
unrecoverable in accepted records, the user accepts a fallback derived from
accepted TOC identity/title evidence and a coherent sequence of body children.
The fallback must be represented honestly as derived structure, without
inventing a source heading or redirecting a chapter to its first subsection.

This task implements and validates that source-general representation. Task 06G
owns production replay, and Task 06H owns targeted human review and acceptance.
It does not reopen PDFs or rerun conversion.

## Goal

1. Give a whole-chapter citation a distinct, complete structural target.
2. Establish title, chapter identity, start, and extent independently of Task 05
   response mentions.
3. Preserve source blocks, subsection identity, and truthful evidence lineage.
4. Fail closed on missing, conflicting, or noncontiguous structural evidence.
5. Integrate with existing semantic, alias, linking, and review interfaces.

## Inputs and prerequisites

Read the repository entry documents, Task 06 umbrella, `docs/architecture.md`,
`docs/data_artifacts.md`, and these bounded inputs:

- Task 06A's accepted chapter evidence census and design choices;
- Task 06B's accepted reuse/identity and cleanup gate outcomes;
- Task 06D's accepted logical-chapter decisions and correspondence shape;
- accepted Task 03J structure, Task 04A TOC dispositions, and Task 04D navigation
  correspondence named by 06A's compact pointers;
- `docs/specs/semantic_structure_v2.md`, `docs/specs/document_linking_v1.md`,
  and `docs/specs/cross_references_v3.md`;
- `benchmarks/er_bench/schemas/canonical_extraction/v2/semantic_structure.schema.json`.

Planning evidence identifies no main-document Chapter 8 or 9 target despite
body sections 8.1–8.6 and 9.1 onward. Accepted TOC titles are `Chapter 8
Alternatives` and `Chapter 9 Subsequent EIR Analysis and Findings`. Task 05
contains eight and eleven official mentions respectively. These mention counts
are downstream regression populations, never target-construction inputs.

## Current ownership and contract constraint

`src/er_commons/document_records/document_structure/sections.py` constructs
semantic sections from accepted heading keys. Its `_build_heading_nodes` and
`_finalize_sections` assume a real heading block owned as the first child.
`document_structure/policies/sections.py:_validate_semantic_section` enforces
that assumption, together with stable heading evidence and parent levels.
The current schema admits semantic sections and body/furniture synthetic roots;
it does not authorize an invented semantic heading for a missing chapter.

`document_structure/aliases.py` derives aliases from canonical and reconciled
TOC evidence. `collection_processing/record_target_indexing.py` merely consumes
sealed targets. A collection-only alias pointing at Section 8.1/9.1 would evade
the structural problem and is forbidden.

Trace the 06A-selected owner after 06B changes. Keep the new representation
inside existing document structure and publication contracts, not in a separate
chapter resolver or review application.

## Outputs

- A versioned representation for independently supported missing chapters.
- Narrow builder, schema, validator, and alias changes with focused fixtures.
- A provenance contract identifying title evidence and the ordered body range.
- Compact qualification accounting for body-heading recovery, fallback,
  already-present, absent, conflicting, and review-required cases.
- Exact 06G invalidation instructions and 06H chapter review selections.

No production candidate or collection is published here. Separately specified
record-only qualification may write fresh bounded working evidence. Source
PDFs, new extraction, final usability decisions, and Task 05 replay are outside
this implementation authorization.

## Research / learning checkpoint

Read the semantic specification's heading ownership, direct membership, and
implicit extent invariants. Explain why the fallback changes a data contract,
even when the requested alias is only `Chapter 8`.
The [W3C PROV data model](https://www.w3.org/TR/prov-dm/) provides the distinction
between source evidence and derived entities. Use explicit derivation to avoid
claiming a TOC-supported chapter is an observed body heading. No RDF dependency
or generalized provenance framework is required.

## Plan / spec requirement

Before implementation, freeze one representation and its consumer contract.
The approved fallback principle does not permit an implementer to invent an
unversioned field or incompatible section kind.

### Body-heading-first decision

1. Inspect the sealed body blocks, heading decisions, and accepted structural
   evidence named by 06A for independently recoverable chapter headings.
2. If an actual body heading exists but was misclassified, identify the owning
   correction and its evidence; do not synthesize replacement source text.
3. If no recoverable heading exists, record that outcome and apply the bounded
   TOC-plus-children fallback. Do not rerun a PDF to search for a preferred case.
4. Existing valid chapters remain unchanged; never create a parallel target.

### Fallback eligibility

Require all of the following:

- exact chapter marker and independently accepted TOC title in the same source;
- an unambiguous link from accepted TOC evidence into the body chapter range;
- a coherent ordered run of body children belonging to that chapter prefix;
- an evidenced start and end, including the following chapter or document end;
- no intervening conflicting chapter, repeated numbering scope, or unsupported
  gap that makes the proposed extent ambiguous;
- no existing distinct target already representing the full chapter.

Numbered children alone cannot supply a missing title. A TOC row alone cannot
supply a body extent. Neither can an official response saying what it cites.
Repeated chapter numbers in appendices must remain source/scope separated.

### Representation and invariants

Specify the target kind, inference method, nullable heading fields, title source,
ordered child membership, and derivation references in a closed versioned
schema. Prefer the smallest extension of the existing section family that can
honestly represent a headingless structural group; do not choose a new family
without documenting why existing consumers cannot support that extension.

Keep actual source blocks unchanged. Store the TOC-derived title as structural
metadata with an evidence reference, never as a fabricated canonical block.
The group has its own target ID; its first subsection remains a different ID.
Freeze parent/level policy without assuming numeric depth equals semantic level.
Retain one direct owner per existing content record and ordered child subtree.
Use tree-based extent if adequate; if another extent representation is needed,
explain why and prevent two independently drifting definitions of boundaries.

Define source-to-replacement correspondence for changed section paths and IDs.
Record start/end evidence, exact TOC record references, ordered child IDs, and
policy identity in the smallest existing provenance representation. Name every
consumer affected by nullable headings or a new section kind, including review
rendering, linking target-page lookup, and document semantic validation.

## Implementation sequence

1. Confirm evidence/design prerequisites and versioned representation.
2. Write focused fixtures for recovery and fallback before builder changes.
3. Add one deterministic construction path and one matching semantic validator.
4. Extend aliases from independent title/marker evidence; retain true collisions.
5. Adapt affected consumers with explicit cases for the derived group.
6. Validate mixed recovered, existing, and derived chapters in one document.
7. Run repository checks and an independent human maintainability review.
8. Deliver replay/review expectations to 06G/06H; stop before production replay.

## Required fixtures and expectations

| Fixture | Expected result |
| --- | --- |
| Main Chapter 8 evidence, body heading absent | Distinct fallback chapter with complete accepted child run |
| Main Chapter 9 evidence, body heading absent | Same rule; correct end evidence |
| Recoverable actual chapter heading | Body-based target, no fallback duplicate |
| Existing valid chapter target | Preserved, no added target |
| Accepted TOC title plus coherent child run in another source | Same source-general fallback |
| Children present but no accepted title | No target; missing-title outcome |
| TOC title present but no body range | No target; missing-boundary outcome |
| Conflicting TOC titles/destinations | Review required, no guessed title |
| Noncontiguous children or intervening chapter | Reject/review; no range spanning unrelated content |
| Repeated numbering in appendix and main source | Distinct scope; no cross-source substitution |
| First child not independently identified as chapter start | No inferred start from numbering alone |
| Chapter at document end | Explicit accepted end evidence required |
| Invalid child ownership or cyclic grouping | Validation failure |
| Task 05 mentions added/removed while source inputs fixed | Identical chapter targets and aliases |

Include target-ID inequality assertions for Chapter 8 versus Section 8.1 and
Chapter 9 versus Section 9.1. Test all eligible chapter candidates, not only
numbers 8 and 9, using 06A's source-free census as the qualification population.

## Invalidation and reuse matrix

| Evidence/product | Treatment |
| --- | --- |
| Source/Docling chunks/conversion/producer records | Reuse sealed evidence |
| Body text, images, tables, source TOC rows | Preserve original content |
| Heading decisions | Rebuild only if actual heading recovery changes them |
| Sections, parent paths, affected aliases | Fresh structure-stage descendants in 06G |
| Page-label evidence | Reuse when declared inputs match |
| Document linking and publication | Replay affected documents in 06G |
| Collection descendants | Rebuild against coherent replacement scope in 06G |
| Existing review dispositions | Rebind only unchanged evidence; derived chapters need review |
| Task 05D/05E/05F | Preserve; Task 05G later consumes replacement handoff |

Follow 06B's accepted identities rather than remapping old records into a new
namespace without validated correspondence.

## Human review fallback

The review packet must display accepted TOC title/destination, actual body
children, proposed start/end, neighboring structure, and whether the heading
was recovered or the group was derived. Clearly label derived titles.
Ambiguity remains an explicit unresolved outcome; a reviewer may request a
bounded additional evidence gate, but this task does not authorize PDF access.
A review decision cannot invent source heading text or silently relax the rule.

If a Chapter 8/9 boundary or title needs human interpretation, resolve it in a
bounded structural-decision checkpoint here before 06G. Use existing records
and accepted renders; obtain a separate bounded rendering gate only if new
source access is needed. Persist the reviewed evidence and disposition as inputs
to the derived structure. A blocking chapter decision leaves 06E incomplete;
do not wait for terminal 06H review to choose a boundary needed by 06G.
06H subsequently reviews the materialized result. A changed interpretation
returns through 06E and fresh 06G replay before renewed acceptance.

## Validation and review pass

Verify schema closure, target existence, unique direct membership, acyclic
ancestry, complete extent, truthful title provenance, and source isolation.
Verify old accepted records remain readable under their original schema.
Check deterministic construction, changed-policy identity rejection, and no
partial qualification advertised as complete. Use maintained storage helpers
for any approved record qualification rather than a custom checkpoint system.
Run `make fix`, `make check`, and `git diff --check`. Review implementation
readability, consumer coverage, failure explanations, and recovery instructions.

## Acceptance criteria and stops

A tested source-general representation can express Chapters 8/9 with truthful
provenance and their own extents/IDs. Missing evidence closes explicitly, with
no aliases to the first subsection or out-of-source chapters. All changed
consumers and invalidated descendants are named. Stop on unresolved schema
choice or evidence conflicts; return a bounded decision instead of guessing.
No implementation acceptance substitutes for 06G replay or 06H human acceptance.

## Non-goals

Inventing body text, general TOC reconstruction, fuzzy matching, PDF reruns,
source acquisition, cleanup, commit, push, Task 05G, or benchmark publication.

## Outcome

### Complete-subtree evidence amendment (2026-09-12)

Task 06G replay-v18 exposed a frozen-evidence defect: qualification v13 used
block-only endpoints for ten Chapter 8/9 child leaves even though accepted owned
tables extend those subtrees. Qualification v17 preserves the v13 policy and
source authority and changes only those ten `child_topology.extent_end_page`
values. Its amendment recipe verifies the full v13 completion-to-inventory
managed-file chain and seals every consumed compact record and result-controlling
module. A separate current-code source-free projection completed as
`exv1-259528836c331c29e4921673f7c28109b262cdbc999418023e176be2f74fe0ea`
with zero undeclared differences. Production acceptance remains owned by Task
06G; Task 06H remains the later human review boundary.

Implementation and compact qualification are complete and accepted. Astra
accepted the v12 functional implementation; independent review confirmed the
behavior-preserving v13 maintainability cleanup has byte-identical decisions.
The source-general `missing_whole_chapter_v1`
policy uses observed retained heading components when they pass exact
same-source, start, adjacency, role, and TOC-title checks. Its closed fallback
creates a headingless `derived_chapter` only from an accepted title, exact body
start/destination, frozen child topology, and explicit following or document-end
boundary. Canonical semantic schema/config version 3 is parallel to v1/v2,
retains the 06D repeated-heading capability, and adds the 06E projection. The
parallel `configs/task06/v1/deir_main/document_structure.json` binds the v13
packet and records 06D as source-local/not applicable rather than importing
Appendix-A decisions into `deir_main`.

For `deir_main`, both observed candidates qualify without a content-choice
checkpoint: Chapter 8 is `CHAPTER 8` + `ALTERNATIVES`, pages 1855–2014, and
Chapter 9 is `CHAPTER 9` + `SUBSEQUENT EIR ANALYSIS AND FINDINGS`, pages
2015–2084 before the Chapter 10 boundary. The packet contains two eligible,
zero rejected, and zero review-required records at
`pipelines/brisbane_baylands/task_06_recovery_v1/06e/qualification_v13/` under
the external root. The Astra-accepted v12 packet remains immutable as the
functional baseline; the preserved v1–v11 attempts were superseded as policy
wording and closed decision provenance were tightened to include verified
child topology, source-order boundaries, and explicit source-role and
reclassification-authority facts. The v13 inventory digest is
`80d695f53dd08d12381a7c15b3e6f7e798e33648dab39a00ca048b6e15f6ef2b`;
its completion digest is
`1522d2796c3bd917b8b6544e3c5ee68d760e2b08063fc2a70af193e48ac5d497`.
The frozen policy, decision-schema, semantic-v3-schema, and closed
correspondence-schema digests are
`bffa5a81d8b7d4e58fdef4fa67a0dcb8deb845fc9a45a0154da693c02e20cc71`,
`d5a2b8324b347813b7c60bf86036420e1a61a640c1cedcb223ed0efc71b92b61`,
`8f0a996f84a007074d5da41bc5fe4c07b18d38011276bfe5173f8a689ec4ec48`,
and `71bc7d297475c07c5cdeb33d5826f9bfed241ece1f9308f494824379c75d72e9`.
Fragmented TOC destination tokens remain documented in upstream 06A evidence,
but are not a v13 qualification limitation because the selected recovered-heading
path does not use them. If observed recovery later fails, fallback still requires
an early bounded human decision before 06G.

Construction creates distinct whole-chapter IDs, preserves every source block,
uses `heading_owner` plus `heading_component`, reparents only the frozen child
run, publishes full-title and bare-chapter aliases with decision provenance,
and emits addition correspondence as a fifth v3-only sealed support artifact;
the four canonical-v2 support roles remain unchanged. Section validation, alias validation,
document-link target pages, navigation reconciliation, and TOC review display
use the logical chapter start independently of a later recovered heading and
distinguish recovered from derived titles. Collection indexing remains
shape-agnostic. Production replay, source/model/PDF work, 06F, and terminal
replacement review were not executed.

The Astra remediation additionally resolves accepted parent IDs through exact
source/local identity or the retained 06D correspondence, freezes unnumbered
enclosing topology and every child's parsed chapter marker, validates terminal
boundaries against retained source content, and permits only decision-named
heading-component layer changes. It rejects unrelated intervening sections,
7.x children under Chapter 8, orphan heading components, subsection chapter
aliases, and semantically inconsistent correspondence reuse. Composite review
labels now say `recovered title`; `derived title` is reserved for fallback.
The v13 candidate retains the v12 correction that carries the true 06D
source-section correspondence through
construction, validates every member of ambiguous chapter-alias collisions,
qualifies document-end evidence against its closed sentinel before projection,
and freezes the accepted heading facts that prove each permitted enclosing
ancestor is not a numbered structural section.
It also freezes exact non-owning mixed-order chapter scope. The logical Chapter
8 scope now starts at its first selected child anchor `blk017273`, before the
later recovered heading blocks, records 17 enclosure-owned direct blocks
including `blk017276`–`blk017280`, and ends
at the first Chapter 9 body anchor `blk018692` while retaining the later
`CHAPTER 9` boundary heading. Chapter 9 likewise starts at its first selected
child anchor `blk018692`, before recovered heading block `blk030330`, and
records 19 direct blocks including `blk018700`–`blk018702` and
`blk018715`–`blk018718` before the Chapter 10 heading. These records retain
their canonical owners; only the frozen numbered children are reparented.
Nullable-key and multi-page nontext records are supported through record-ID,
global-order, complete page-membership, and ownership evidence. The v13
qualification digest is
`ecbd34ddf03620c56f64f8f96e02034392f9e76261b862d69334b4c5837a024a`;
both decision streams have digest
`7deccdb1014590669049865cc9d9f8bd16eb80a068fa13302828d54efac980f1`.

The maintainability cleanup names global mixed-content index versus family
record-sequence ordering explicitly, centralizes logical section-start
selection for structural and linking consumers, makes projection and
correspondence failures evidence-addressable, and removes misleading unused
fixture defaults without changing published record or schema shapes. Its fresh
v13 decision streams are byte-identical to v12. Focused validation passes 47
tests across the 06E matrix, canonical structure/input identity, publication,
and old-version regression. The final repository check covers navigation and
1,726 tests plus formatting, lint, and mypy. Independent equivalence review
found no material findings.

## Task 06B interface handoff

Both Task 06B gates now supply the maintained
[command map](../../docs/pipeline_commands.md) and
[executed owner map](../../docs/specs/task06b_gate2_executed_inventory.md).
Use explicit current requests with original per-source accepted manifests and
seals; historical recipe validation does not reopen removed implementation paths.
Document/collection v3 supports declared replacement membership. Compact checks
must retain the shared verification budget and must not claim new payload-byte
equality. These remain inherited reuse constraints; Task 06G production replay
and Task 06H replacement review are separately gated.
