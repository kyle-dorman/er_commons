# Task 04C: Materialize the Human-Reviewed Navigation Overlay

Status: **Gates A through C are complete; Gate D is superseded by active Task
04D's replacement-linking work**.

## Abstract

Materialize a derived semantic and linking view that combines the immutable
Task 03J machine candidate with Task 04A's accepted human TOC decisions. Task
04A keeps human judgments separate from machine extraction, but the current
pipeline has no consumer that applies those judgments to semantic placement,
target aliases, or reference links. This task closes that downstream-use gap
without regenerating or mutating Task 03J.

The result is an overlay-backed release view, not a corrected machine
extraction. Human-confirmed TOCs may change which existing entities are treated
as navigation and which machine-generated aliases or links are eligible.
Creating missing TOC rows or destination links requires explicit entity-level
evidence and a fresh derived identity; page labels alone are not permission to
invent targets.

## Goal

1. Define a stable join from every accepted Task 04A TOC decision to its Task
   03J source, page, and affected canonical entities.
2. Publish a deterministic review-adjusted semantic/navigation view while
   preserving Task 03J and Task 04A as immutable inputs.
3. Recompute or conservatively invalidate affected TOC aliases and document
   links, including links made possible by newly confirmed TOCs.
4. Preserve the 725 Task 04A ambiguous links as unresolved unless this task has
   sufficient entity-level evidence to resolve an individual link.
5. Provide downstream tasks one coherent accepted machine-plus-human identity
   rather than requiring each consumer to reinterpret browser exports.

## Inputs and activation boundary

Activation requires:

- Task 04A's frozen Task 03J release identity, usability registry, TOC decision
  register, unresolved-risk report, and release-freeze record;
- the exact Task 03J semantic structure, tables, target aliases, document-local
  links, collection resolution records, and immutable handoff referenced by
  that freeze;
- an accounting of accepted `toc` and `not_toc` decisions, including decisions
  propagated over a contiguous review run.

Reject browser-local state, superseded `c*` review packages, Task 03H artifacts,
or a decision export that is not the one pinned by Task 04A. Reuse existing
sealed checksums and compact manifests. Do not recompute checksums for large
Task 03J files merely to activate this task.

## Accepted activation decisions

- Gate A may read compact review records and sealed machine records, but it may
  not read source PDFs or model files, generate renders, or run a parser/model.
- Task 04A Gate D's frozen release and completion records are authoritative over
  older internal workflow labels such as `pending_human_review` and the immutable
  Task 03J handoff's `task04_status: not_evaluated`.
- Apply a human decision only to existing entities supported by exact
  correspondence evidence. Preserve the original machine placement as
  provenance and do not infer corrected body ownership.
- Mixed navigation/substantive pages are not expected workload or an activation
  prerequisite. If one is encountered and entity membership is not independently
  explicit, record `insufficient_entity_evidence`, leave the page unchanged, and
  route it to later review.
- Reconsider only aliases and links in the affected closure of a human/machine
  navigation disagreement. Account for all 725 inherited ambiguous links, but
  leave links outside that closure unresolved and unchanged.
- Do not create missing TOC rows, aliases, targets, or links from a page-level
  decision. A later gate may add a link only from unique source- and target-side
  entity evidence.
- Check in again before any source-PDF read, render generation, human review, or
  Gate B implementation.

## Outputs

- a versioned overlay schema and compact manifest binding the accepted Task
  04A registry to the Task 03J extraction and handoff identities;
- deterministic page-to-entity correspondence records with explicit mixed-page
  and insufficient-evidence outcomes;
- a derived semantic-placement view identifying confirmed navigation content,
  rejected machine-positive navigation, and unchanged machine content;
- a derived target-alias and link view that records retained, invalidated,
  newly resolved, and unresolved outcomes with exact reasons;
- before/after accounting for TOC entities, aliases, links, and the 725 inherited
  ambiguous links;
- a compact completion or stop record and focused review bundle for every
  materially changed navigation/link outcome; and
- updated downstream routing that requires the combined Task 03J plus Task 04A
  overlay identity.

Large canonical records remain external artifacts. Only new compact records are
checksummed; existing sealed large-file digests are referenced, not recomputed.

## Research / learning checkpoint

1. Trace one Task 04A false-negative TOC page and one false-positive machine TOC
   through canonical blocks, tables, semantic placement, aliases, document-local
   links, and collection resolution.
2. Identify the narrow existing owners for semantic placement, alias generation,
   and link validation. Decide whether each can consume an overlay directly or
   needs a derived read model.
3. Explain why a page-level label is enough to guide review eligibility but may
   be insufficient to create row-level aliases or destination links.
4. Compare query-time overlay joins with materialized derived records. Prefer the
   smallest design that gives downstream tasks deterministic identities and
   avoids reinterpreting review decisions independently.

## Plan / gates

### Gate A: specify correspondence and identity

1. Validate the compact Task 04A freeze and register without rehashing large
   Task 03J files.
2. Census the affected sources, pages, canonical entities, aliases, and links.
3. Define page-to-entity correspondence, mixed-page handling, unresolved
   behavior, and the derived identity preimage.
4. Present expected work and any need for source-PDF reads before execution.

Gate A completed source-free on 2026-09-03. The accepted plan is
`navoverlayplanv1-72af852ffe39c272ce958147c74974008269b6e72db2c0c7b03e0f66ba366741`
under `pipelines/brisbane_baylands/task_04_navigation_overlay/`. Its exact
Task 04A census contains 5,624 candidate pages across all 35 sources and 757
accepted decisions: 60 TOC and 697 Not TOC. The correspondence census found
351 machine/human agreements and 406 disagreements, comprising 15 newly
confirmed navigation pages and the 391 rejected machine-positive pages.

The disagreement closure covers 406 pages in 15 sources and 5,823 existing
page-resident entities. It found no existing alias, local-link, or collection
resolution records in the conservative affected closure. All 725 inherited
ambiguous links are accounted for outside that closure and remain unresolved.
No mixed page was present in the accepted inputs; the versioned contract and
focused fixture nevertheless fail closed with no mapped entities when explicit
mixed-page evidence is encountered.

The publication binds the exact Task 04A Gate A census, Gate D freeze and
completion, accepted decision bytes, all 35 sealed Task 03J candidate records,
the collection handoff identity, schema bundle, policies, and owning
implementation. It was reproduced twice to the same no-clobber namespace.
No source PDF or model file was read, no render was generated, no source-PDF
checksum was recomputed, and no large Task 03J file was rehashed. Gate B remains
paused for the required user check-in.

Four earlier Gate A development publications remain as unreferenced trial
evidence: `navoverlayplanv1-0f8b955fab11f7af2ccbaeecc46df164c69b78a46977c4b7ca60c5aacd62615b`,
`navoverlayplanv1-c27bdc687d3365029ab9c82ef6daf45f38a808e898f40e3ca44bce181ed990dc`,
`navoverlayplanv1-a08f851cab72a470f2b8eebf727f450f801fa302c1c3c02a572c99180258fec9`,
and `navoverlayplanv1-c3fb23b45fb6940905fbf24892ee28104d79f97b9302f0738b1377bf4075a2d1`.
They are not accepted inputs and were not deleted without cleanup authorization.

### Gate B: implement the overlay consumer

1. Add a narrow package-owned reader that joins the immutable machine records
   and human decisions.
2. Emit deterministic semantic dispositions for existing entities; fail closed
   when a page label cannot identify the affected entity safely.
3. Add focused fixtures for confirmed new TOCs, rejected machine TOCs, mixed
   pages, run-propagated labels, missing entities, and stale decisions.

Gate B completed source-free on 2026-09-04. The accepted semantic view is
`navsemanticv1-ae00c6e6f70839f1ca15404c9dff14161f0a3e9aaa9e7902f51f65b36023c8fc`
under `pipelines/brisbane_baylands/task_04_navigation_overlay/`. It contains one
application record for each of the 757 accepted human decisions and 5,800
unique sparse entity overrides: 72 human-confirmed navigation entities (57
blocks and 15 tables) and 5,728 human-rejected machine-navigation blocks.

Application accounting is 45 mapped machine-TOC/human-TOC agreements, 303
mapped machine-Not-TOC/human-Not-TOC agreements, 15 applied confirmations, 391
applied rejections, and three entityless machine-Not-TOC/human-Not-TOC decisions
left unchanged fail-closed. Those three still belong to Gate A's 351 agreement
count; they are separated here because there is no entity on which to apply a
semantic disposition.

The read model preserves each entity's original `semantic_placement`,
`is_toc_row`, and section owner as machine provenance. Its only authoritative
override is `effective_navigation`; an entity absent from the sparse view
inherits its machine classification. The 23 unique associated sections remain
context only and are not reclassified, because a page decision cannot safely
rewrite a potentially spanning section. Five spanning entities aggregate two
consistent reviewed-page decisions into one disposition.

This sparse materialized-overlay design was selected over copying the canonical
corpus or forcing every consumer to repeat the review join. It gives the changed
semantics a deterministic identity while keeping unchanged machine content as a
read-through. It also avoids inventing corrected body placement from a page
label; Gate B can exclude content from navigation without claiming whether its
proper placement is `direct_body`, `heading_owner`, or another machine role.

The package reader, nested schemas, thin reproduction command, completion-last
publication, no-clobber reuse, identity rederivation, sealed-size checks, and
focused stale/mixed/missing/conflict tests passed. The accepted Gate A plan was
reproduced to its unchanged identity after Gate B was added, and the Gate B
publication was reproduced twice to the same namespace. No source PDF or model
file was read, no render was generated, no large Task 03J file was rehashed,
and no Task 03J or Task 04A artifact was written.

### Gate C: reconcile navigation and links

1. Rebuild the derived alias and link view for affected entities only, while
   retaining exact references to unchanged Task 03J records.
2. Attempt additional links for newly confirmed TOCs only when visible
   destination evidence and a unique body target support them.
3. Keep ambiguous or unsupported links unresolved; do not guess from page-level
   labels or heading text alone.
4. Account explicitly for all 725 inherited ambiguous links without treating
   the full inherited population as a rebuild or re-review queue.

Gate C was replaced source-free on 2026-09-04 after review showed that the 15
human-confirmed TOCs were still being consumed as malformed canonical tables.
The accepted replacement is
`navlinkv1-978dbf3f3363eeb4265c75f60efd80bb3995234586e1821f060fe70a9c11bed4`
under `pipelines/brisbane_baylands/task_04_navigation_overlay/`. For every
confirmed TOC it reconstructs ordered text from preserved Docling
`document_index` cells, publishes that text for model-facing document
exploration, and feeds the same 560 logical entries to link reconciliation. The
old 570 table rows and six-link namespace remain immutable superseded evidence;
they are not inputs to the effective view.

The 560 entries close as 216 unsupported entry shapes, 87 unsupported target
types, 120 entries without a target alias, 108 without any usable printed-page
destination, one destination/target page mismatch, and 28 uniquely resolved
entries. There are no empty or still-ambiguous target entries. When either the
marker or printed-page label has multiple candidates, Gate C intersects the two
candidate-page sets and links only if exactly one existing body target remains.
This recovers 11 of the 18 formerly ambiguous target markers, including
`6.3.4 -> 53`, while leaving the other seven unresolved without guessing. It
also recovers ten entries that had one body target but a repeated printed-page
label.

The identity binds the accepted Gate A and Gate B completions, exact Gate
A-pinned ambiguity record, sealed candidates, every compact candidate-to-range
lineage record, all 15 checksummed raw Docling page records, policy, schemas,
and both implementations. The publication was reproduced to the same
no-clobber namespace. Gate C creates no alias, invalidates no existing alias,
link, or collection resolution, and carries all 725 inherited ambiguities
forward unchanged. No source PDF, render, or model was read or generated, and
no upstream artifact was written. Gate D was later superseded by Task 04D.

### Gate D: verify and publish

Superseded on 2026-09-04 by Task 04D. Task 04C's accepted semantic view,
Docling-text TOC projection, reconciliations, and validation evidence remain
immutable inputs, but its link view will not be designated as the final
downstream machine handoff.

1. Review every newly created, invalidated, or changed link outcome and a sample
   of unchanged controls.
2. Publish the derived overlay identity and compact completion record.
3. Update downstream tasks to pin Task 03J, Task 04A, and this overlay together.

## Validation

- exact Task 04A decision and Task 03J identity binding;
- deterministic output under shuffled discovery and repeated builds;
- one correspondence outcome for every accepted TOC decision;
- no writes to Task 03J or Task 04A artifacts;
- no large-file checksum recomputation;
- no new alias or link without entity-level source and target evidence;
- explicit retained, invalidated, resolved, or unresolved accounting for every
  affected link and all 725 inherited ambiguous links;
- stale, mixed, missing, and conflicting decisions fail closed;
- focused tests, routine repository checks, maintainability review, and
  `git diff --check` pass.

## Review pass

- **Identity and provenance:** Does the overlay pin the exact Task 04A freeze,
  decision register, correspondence census, and sealed Task 03J identity chain
  without trusting directory names or mutable browser state?
- **Entity correspondence:** Does every accepted decision have one deterministic
  page outcome, with changes limited to exact existing entities and uncertain or
  unexpected mixed content left unchanged?
- **Navigation and linking:** Is the affected closure complete without widening
  into all aliases or all 725 ambiguous links, and is every new or invalidated
  outcome supported by inspectable entity evidence?
- **Architecture and maintainability:** Does one narrow package own the derived
  read model without making `human_review_support` a production dependency, and
  can maintainers understand, test, reproduce, and validate it independently?
- **Artifact integrity:** Are Task 03J and Task 04A read-only, are existing sealed
  large-file digests reused, and are only new Task 04C records checksummed and
  published completion-last?

## Acceptance criteria

- downstream consumers have one deterministic interface for Task 03J plus the
  accepted Task 04A human layer;
- newly confirmed TOCs participate in semantic/navigation handling without
  rewriting machine extraction;
- rejected machine TOCs no longer influence the derived navigation/link view;
- added links are evidence-backed and all remaining ambiguity is explicit;
- the 725 inherited ambiguous links are fully accounted for, even when retained
  unresolved; and
- the published overlay remains reproducible from immutable compact decisions
  and already sealed Task 03J records.

## Non-goals

- regenerating source PDFs, parser/model outputs, or Task 03J canonical records;
- activating Task 04B or implementing a source-general extraction repair;
- treating a page-level TOC label as proof of every row, target, or link;
- resolving ambiguous links by guessing;
- changing benchmark cases, retrieval, generation, or scoring; or
- addressing the post-MVP TOC-run segmentation backlog item.
