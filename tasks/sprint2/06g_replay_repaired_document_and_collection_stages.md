# Task 06G: Replay Repaired Document and Collection Stages

Status: **provisional and inactive; revise from accepted Tasks 06A-06F before
execution. This contract is not authorization to run a replay.**

## Abstract

Combine the qualified replacement F1 and accepted structural/target repairs into
one coherent fresh document/collection lineage. Reuse sealed conversion,
producer, and unaffected evidence wherever the owning contracts allow it.
Rebuild only invalidated descendants and account for every semantic change.

This task publishes a mechanically validated replacement candidate for Task
06H review. It does not accept human usability, replay Task 05F, or promise
that every deferred mention will resolve.

## Goal

- Consume final accepted repair policies from Tasks 06C-06F.
- Preserve accepted Task 02/03J/04A/04D evidence without relabeling it.
- Apply the final policies to F1 without repeating its accepted conversion.
- Rebuild affected document and collection stages under fresh identities.
- Produce explicit old/new source, entity, stage, and review correspondence.
- Deliver complete change accounting and reproducible terminal evidence to 06H.

## Inputs and prerequisite gate

Read `docs/architecture.md`, `docs/data_artifacts.md`, the accepted Task 06A
impact/design record, both Task 06B gate outcomes and filename map, and Tasks
06C-06F outcomes. Do not execute provisional policies or choose unresolved
chapter boundaries during replay.

Baseline Task 04D handoff:
`handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`.
Its production identity is
`exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3`
and its scope is
`scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da`.
Resolve exact paths and seals from the accepted Task 04D outcome and Task 06A
binding table; do not find inputs by newest-directory or filename heuristics.

Task 03J remains immutable extraction evidence under
`pipelines/brisbane_baylands/task_03h_clean_full_v4/`.
Task 04A review is `reviewv1-task03j-final-c17`.
Task 05F partial candidate is
`rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83`.
Task 06A pins unchanged accepted Task 05D/05E candidates and the 511-mention
population; this task consumes their compact census, not their resolver.

Required repair inputs are qualified F1 source and sealed conversion/producer
records from 06C; duplicate-heading policy from 06D; chapter-target policy from
06E; and caption-backed figure policy from 06F. Each must carry accepted schema,
configuration, code identity, tests, and explicit owner/resume stage.

## Current implementation owners

Use Task 06B's closure map if files moved:

- `document_publication`: stage identity, attempts, reuse, downstream replay,
  and completion-last document publication.
- `document_records/document_references/relink_publication.py`: sealed relink
  inputs and atomic linked-document publication.
- `document_records/document_references/relink_replay.py`: prepared sequential
  document replay and collection assembly.
- `collection_processing`: accounting, target index, cross-document resolution,
  handoff assembly and validation.
- `source_family_catalog.py`: explicit source identity and routing evidence.

The shared exact resolver remains beneath machine and reviewed-navigation
adapters. Keep Task 04D's accepted linking policy, including existing qualified
body-caption behavior, unless an accepted preceding subtask explicitly changes
one owned policy. Do not create a Task 06 resolver.

## Outputs

1. A frozen replay specification, stage dependency table, and resource budget.
2. Fresh affected document stage records and terminal document publications.
3. Explicit reused-input references preserving original manifests and seals.
4. A fresh source-family catalog/scope binding where required by substitution.
5. Complete collection accounting, target index, cross-document resolution,
   mechanical handoff, completion records, and inventories.
6. Old/new entity correspondence and complete semantic difference accounting.
7. A review input packet for 06H with no implied human acceptance.

## Research / learning checkpoint

Explain the difference between reusing immutable upstream evidence and copying
its records into a new identity. Explain why a changed source catalog may
invalidate collection or link identities even when a document's content is
unchanged. Record the existing identity contracts and maintainers' primary
serialization/checksum documentation only where an implementation choice needs
support. Do not research live source URLs or add an orchestration framework.

## Plan / spec requirement

### Gate 1: freeze exact mixed-lineage inputs

Task 06A's accepted design must specify how one replacement collection consumes
unchanged sources from their original sealed manifest and F1 from its fresh
source lineage. Preserve original manifest references for unaffected sources.
Do not fabricate a new source release that claims to have acquired all existing
files, or rewrite old manifest membership to accommodate F1.

A compact correspondence record must bind each selected logical source to:
old source identity/manifest, selected source identity/manifest, old and selected
stage completions, allowed reuse basis, change class, and expected descendants.
If existing collection contracts cannot express this safely, stop and complete
the already scoped contract/interface change from 06A/06B before execution.
Do not improvise a private mixed-lineage bypass in a corpus script.

Freeze exact configuration paths, source order, source-family entries, final
policy versions, owned code/schema digests, artifact destinations, and commands.
State whether each stage reads source bytes, model evidence, canonical records,
or only compact metadata. No source/model execution is implicitly authorized
by the word replay.

Record finite elapsed, memory/thread, output-disk, and temporary-disk bounds
from actual preceding evidence. State free-space minimum and source order.
Unknown estimates require a bounded proposal before execution, not guessed
observations. Use visible sequential progress and per-stage failure context.

### Gate 2: implement any remaining source-free integration

Only integration already selected by the accepted predecessor contracts belongs
here. Keep source selection, identity derivation, record construction, and
publication separate. Tests must demonstrate mixed explicit provenance,
correct invalidation, no-clobber behavior, and ordinary sealed reuse without
source reads or large-payload rehashes.

An implementation gap that changes repair semantics returns to its owning task.
Run focused tests, formatting, linting, strict typing, and human code-quality
review before requesting the bounded replay gate.

### Gate 3: separately authorized affected replay

Apply the accepted invalidation table:

| Evidence | Required treatment |
| --- | --- |
| Wrong accepted F1 source and descendants | Preserve; never substitute as valid F1 |
| Qualified Final F1 conversion/producer | Reuse 06C seals; no reconversion |
| F1 later structural/target stages | Apply final 06D-06F policies where eligible |
| Appendix A conversion/producer | Reuse; start at accepted duplicate-repair owner |
| Main-document conversion/producer | Reuse; apply chapter and figure repairs |
| Other documents | Reuse owning stages unless declared dependencies invalidate them |
| Changed document aliases/links/publication | Rebuild only required descendants |
| Collection accounting/index/resolution/handoff | Rebuild with all selected sources |
| Task 04 human usability | Carry evidence for 06H; do not auto-approve |
| Task 05D/05E and accepted 05F outcome | Preserve unchanged; later 05G owns replay |

Determine actual reuse from identity dependencies, not from a desired fixed
number of regenerated documents. A global code/policy identity may require new
link publications for otherwise unchanged documents; explain that distinction
from rerunning extraction. Record every deviation from the frozen table and
stop before an undeclared earlier stage.

Each completed stage seals newly authored outputs once and publishes completion
last. Matching completed stages use the maintained receipt/metadata path. Do
not hash a large PDF to prove a downstream-only stage may resume.

### Gate 4: semantic change accounting

Do not compare raw entity IDs across fresh namespaces and call all differences
content changes. Build validated correspondence using immutable source evidence,
physical page/block provenance, owning-stage mappings, and explicit operation
records. Support one-to-one unchanged mappings, many-to-one duplicate merges,
new chapter/figure targets, removed invalid targets, and substituted F1 entities.

Never create correspondence by fuzzy text similarity. Substituted F1 has new
source content; do not invent entity equivalence with the wrong document.
For unchanged entities compare substantive fields after applying the actual ID
mapping to references, parents, destinations, and provenance pointers. Retain
identity differences separately. Reject incomplete, noninjective unexplained,
or dangling mappings.

Account for all target and alias additions/removals/merges, changed local and
collection links, unresolved cardinalities, and source-family effects. Link
diffs must name old/new source and destination evidence after mapping, exact
reason, and owning repair. Preserve legitimate unresolved outcomes.

Reproduce planning controls independently from canonical evidence: Appendix A
has one logical target for each observed Chapter 06/08 pair; main Chapters 8/9
have real chapter targets and extents; figure candidates use their own eligible
captions. The 78/79 mention and 34/35 figure planning counts are expectations to
reconcile, not assertions to enforce by manufacturing targets. `Figure 4.8`
remains absent unless new independent accepted source evidence proves otherwise.

### Gate 5: publish mechanically validated review candidate

Assemble and validate one coherent collection handoff with exact source order,
accounting, target index, resolution, inventories, and completion links. A
`ready` handoff deliberately retains `task04_status: not_evaluated`; it is not
human approval. Supply 06H with change accounting, correspondence, and exact
review selections, then stop.

## Stop and resume policy

Stop on source/edition mismatch, changed policy, missing seal, unexpected file,
unmapped semantic difference, undeclared extraction dependency, resource
exhaustion, or inconsistent collection membership. Preserve diagnostics and
completed stages; never overwrite accepted predecessors to make replay pass.

Resume only after the cause and exact invalidation scope are understood. A
changed output-affecting input allocates fresh descendant identities. A matching
terminal stage is reused without PDF/model access. Incomplete output cannot
impersonate a terminal completion. Restart tests must cover interruption between
document publication and collection assembly.

## Validation

Use existing synthetic document, relink, collection, and publication fixtures.
Prove mixed source provenance, wrong-source rejection, mapped semantic equality,
merge/add/remove accounting, shuffled input determinism, exact closure,
stale-policy rejection, and no extraction on downstream reuse. Instrument source
reads, conversion calls, and large-file hashing to fail during source-free tests.

Run `make fix`, `make check`, focused replay/collection tests, and
`git diff --check`. After authorized replay, validate compact seals, exact file
sets and sizes, recorded counts, restart reuse, and the complete difference
report. Do not repeat expensive checks without new evidence of a problem.

## Review pass and acceptance criteria

Independently review provenance and edition, minimal invalidation, actual ID
correspondence, unchanged-content proof, precision, and maintainability. Close
only when every selected source and changed entity is accounted, every terminal
stage validates, and 06H can reproduce its review packet from the declared
inputs. Mechanical readiness is this task's terminal boundary.

## Non-goals

Human usability acceptance, Task 05F resolver changes or replay, guaranteeing 66
F1 links, fuzzy matching, source reacquisition, repeated conversion, cleanup,
commit, push, or benchmark/inventory publication.

## Outcome

Pending. Record exact candidate/collection identities, replay commands and
bounds, reused and regenerated stages, correspondence/difference summaries,
validation and restart evidence, resource use, and the precise 06H review gate.
