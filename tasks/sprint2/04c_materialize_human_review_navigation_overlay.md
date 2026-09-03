# Task 04C: Materialize the Human-Reviewed Navigation Overlay

Status: **provisional and inactive; Task 04A prerequisites are published, but
this task still requires explicit review and activation**.

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
  propagated over a contiguous review run; and
- explicit mapping rules for page-level decisions whose page contains mixed
  navigation and substantive content.

Reject browser-local state, superseded `c*` review packages, Task 03H artifacts,
or a decision export that is not the one pinned by Task 04A. Reuse existing
sealed checksums and compact manifests. Do not recompute checksums for large
Task 03J files merely to activate this task.

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

### Gate B: implement the overlay consumer

1. Add a narrow package-owned reader that joins the immutable machine records
   and human decisions.
2. Emit deterministic semantic dispositions for existing entities; fail closed
   when a page label cannot identify the affected entity safely.
3. Add focused fixtures for confirmed new TOCs, rejected machine TOCs, mixed
   pages, run-propagated labels, missing entities, and stale decisions.

### Gate C: reconcile navigation and links

1. Rebuild the derived alias and link view for affected entities only, while
   retaining exact references to unchanged Task 03J records.
2. Attempt additional links for newly confirmed TOCs only when visible
   destination evidence and a unique body target support them.
3. Keep ambiguous or unsupported links unresolved; do not guess from page-level
   labels or heading text alone.
4. Account explicitly for all 725 inherited ambiguous links.

### Gate D: verify and publish

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
