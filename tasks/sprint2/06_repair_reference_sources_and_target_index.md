# Task 06: Repair Reference Sources and Target Index

Status: **provisional umbrella and inactive; its final scope and subtasks must be
designed in a new chat before source access or implementation**.

## Abstract

Repair four upstream defects discovered while qualifying Task 05F:

1. the accepted `deir_appendix_f1` source is not the advertised Transportation
   Impact Assessment; it is a 75-page Bayshore Mobility Study; and
2. repeated chapter-divider and opening-page headings in `deir_appendix_a`
   become separate section targets, creating exact collisions such as
   `06 CIRCULATION` versus `06 | CIRCULATION`; and
3. canonical Draft EIR figures and their captions exist, but Task 04D did not
   publish figure targets or aliases in its designated target index; and
4. the main Draft EIR has no chapter-level targets for Chapter 8, Alternatives,
   or Chapter 9, Subsequent EIR Analysis and Findings, even though accepted TOC
   evidence and body subsection boundaries identify both chapters.

Use the City of Brisbane's Final EIR Appendix F1 as an explicit, provenance-
marked substitute for the unavailable Draft EIR F1. Implement one
source-general repair for duplicate chapter targets, rebuild only invalidated
document and collection descendants under fresh identities, add exact caption-
backed figure targets, conduct a targeted human recheck, and return one
replacement handoff to Task 05G.

This is an MVP recovery umbrella. Its current gates preserve discovered work and
open questions; they are not an accepted execution contract. It must not
redesign source acquisition, canonical extraction, human review, or Task 05F
resolution.

## Observed stop evidence

### F1 source identity

- The accepted source catalog labels `deir_appendix_f1` as `Appendix F1 -
  Transportation Impact Assessment`, sourced from Draft EIR Document Center ID
  `553`.
- The accepted source record instead has 8,223,907 bytes and 75 pages. The
  server-provided filename was
  `BayshoreMobilityPlan_web_202606171407158172.pdf`, and inspection identified
  the document as `Appendix F: Bayshore Mobility Study`.
- The current source therefore appears complete as a PDF but is the wrong
  document. This is a source-identity failure, not a truncation or parser
  failure.
- The accepted Final EIR landing-page inventory records Document Center ID
  `2972`, labelled `Appendix F1 - Transportation Impact Assessment (PDF)`, at
  `https://www.brisbaneca.gov/DocumentCenter/View/2972/Appendix-F1---Transportation-Impact-Assessment-PDF`.
- Task 05D contains 66 Draft EIR F1 mentions in 58 official-response units: 61
  mentions in 56 responses and 5 mentions in 2 General Responses. There are no
  comment-authored F1 mentions.
- Two response passages explicitly revise F1: `Response SA-Caltrans-6` revises
  Table 6 and `Response SA-Caltrans-9` revises the San Francisco Municipal
  Transit (Muni) section. The other 64 mentions do not explicitly establish
  whether Draft and Final wording are identical.

Task 05F closed these 66 outcomes as
`upstream_source_identity_repair_required`. No result from the accepted 75-page
`deir_appendix_f1` may become a replacement link. These deferred references
remain for Task 05G after this recovery is complete.

### Duplicate chapter targets

The accepted Task 04D index contains two distinct `deir_appendix_a` section
targets for each of these logical chapters:

- physical pages 311 and 312: `06 CIRCULATION` and `06 | CIRCULATION`;
- physical pages 479 and 480: `08 PUBLIC FACILITIES FINANCING` and
  `08 | PUBLIC FACILITIES FINANCING`.

The paired targets are body-layer siblings with the same parent. One is the
chapter-divider heading and the other is the repeated opening-page heading.
They are not two substantive chapters. This is an upstream duplicate-target
problem and must not be hidden by a Task 05F tie-breaker.

### Missing figure targets

Task 05D already preserves 79 Draft EIR figure mentions comprising 35 distinct
labels, and Task 05F routes all of them to `deir_main`. The accepted Task 04D
index contains zero figure targets even though the existing canonical
`deir_main` extraction contains figure records, image records, and attached
caption blocks. This is a target-publication gap, not a Task 05D mention-
extraction failure and not a reason to rerun Task 03 extraction.

A source-free qualification against the currently designated canonical
candidate found unique exact caption evidence for 78 mentions and 34 distinct
figure targets, with zero collisions. Each prospective target has one image,
one attached body caption beginning with the requested `Figure <identifier>`,
and no TOC classification. `Draft EIR Figure 4.8` has no exact target and must
remain unresolved rather than being guessed from more specific figures such as
`4.8-5` or `4.8-8`. These counts are planning evidence and must be reproduced
against the replacement handoff before acceptance.

Figure resolution and evidence usability remain separate. A structurally
resolved image target may preserve citation provenance while remaining
`unavailable_to_text_only_model` and excluded from initial benchmark support.
Caption text alone is metadata unless it independently contains the cited
substantive evidence.

### Missing main-document chapter targets

Task 05D contains 8 official mentions of `Draft EIR Chapter 8` and 11 official
mentions of `Draft EIR Chapter 9`. Their response context consistently concerns
the main Draft EIR's alternatives and subsequent-EIR analyses. Corpus-wide exact
lookup instead finds identically numbered chapters inside Appendix E's Cultural
Resources Technical Report. Task 05F correctly rejects those appendix aliases
as `exact_alias_only_outside_routed_source`.

The accepted main-document body contains `8.1` through `8.6` and `9.1` onward,
while accepted TOC evidence states `Chapter 8 Alternatives` and `Chapter 9
Subsequent EIR Analysis and Findings`. It has no distinct Chapter 8 or Chapter 9
body target. This is an upstream target-publication gap. Do not hide it by
aliasing a whole-chapter citation to Section 8.1 or 9.1. Gate A must identify the
smallest source-general way to represent a chapter start and extent from
accepted structural evidence before implementation.

## Goal

1. Preserve the accepted Task 02, Task 03J, Task 04A, Task 04D, Task 05D, Task
   05E, and Task 05F Gate 1 artifacts unchanged.
2. Acquire and identify the Final EIR Appendix F1 only after a separate source
   gate, recording that it is an edition substitute rather than the original
   Draft EIR file.
3. Produce a correct canonical and target stream for the replacement F1.
4. Collapse or canonically designate repeated chapter-divider/opening-header
   pairs through one source-general, fail-closed rule.
5. Materialize exact figure targets from independently eligible canonical
   figure-caption evidence without deriving targets or aliases from Task 05D
   mention text.
6. Materialize proper main-document Chapter 8 and Chapter 9 targets and exact
   aliases from independently accepted structure and TOC evidence, without
   deriving targets or titles from Task 05D mention text.
7. Replay the minimum invalidated document, linking, publication, collection,
   index, resolution, handoff, and usability descendants under fresh
   identities.
8. Give Task 05G one coherent replacement Task 04 handoff and usability
   registry for a separate source-free replay of the accepted Task 05F rules.

## Inputs

- immutable Task 02 source release and landing-page inventory;
- accepted Task 03J conversion, producer, canonical, hierarchy, publication,
  and collection records;
- accepted Task 04A review and usability registry;
- Task 04D's designated linked-document and collection handoff;
- accepted Task 05D and Task 05E records;
- Task 05F Gate 1 baseline and reviewed rule-qualification findings; and
- the maintained source-acquisition, document-publication, collection, human-
  review, and response-inventory implementations.

The Final EIR F1 PDF is not an input until the source gate is explicitly
authorized and its exact URL, expected response metadata, destination, and
resource limits are frozen.

## Outputs

- a compact source-substitution record connecting the advertised Draft F1, the
  incorrect accepted source, and the Final EIR F1 substitute without claiming
  byte or edition equivalence;
- a fresh source and document lineage for replacement `deir_appendix_f1`;
- a source-general duplicate chapter-heading policy with focused fixtures;
- exact caption-backed figure targets and aliases derived from existing
  canonical `deir_main` evidence;
- proper Chapter 8 and Chapter 9 targets and aliases derived from accepted
  main-document structural and TOC evidence;
- fresh affected canonical, semantic, alias, link, publication, collection,
  target-index, resolution, and handoff records;
- exact before/after accounting for F1 and Appendix A targets and all collection
  effects;
- a targeted human review and replacement usability registry covering F1 and
  Appendix A, with explicit correspondence for unaffected sources; and
- a compact handoff authorizing Task 05G to replace Task 05F's current Task
  04A/04D bindings and replay from the unchanged accepted Task 05D/05E records.

Large artifacts remain beneath `ER_COMMONS_DATA_ROOT`. Git contains only the
contract, small configuration, implementation, tests, and compact summaries.

## Fixed boundaries

- Never modify, overwrite, or relabel the accepted source release or Task
  03J/04A/04D artifacts.
- Do not present the Final EIR F1 as the original Draft EIR F1. Preserve its
  landing page, Document Center ID, retrieval metadata, edition, and
  substitution reason.
- F1 links produced through the substitute default to `usable_with_warning`.
  The two explicitly revised locations must additionally identify the relevant
  response and state that the linked text is revised Final EIR content.
- Absence of an explicit revision in the other 64 mentions is not proof of
  Draft/Final textual identity.
- Task 05D and Task 05E consume Final EIR Volume 4 and remain unchanged unless
  source-free validation proves an identity dependency that this contract has
  overlooked.
- Do not rerun Task 03 extraction merely to publish figure targets already
  supported by canonical figure, image, and caption records.
- Resolve a figure only from its own attached body caption beginning with the
  exact requested identifier, after deduplication by figure target ID. Do not
  infer a target from nearby prose, a list of figures, or a Task 05D mention.
- Keep structural figure resolution separate from visual-evidence and model-
  support usability. Text-only benchmark support must exclude image-dependent
  evidence unless an independently eligible textual source states that
  evidence.
- Appendix Q remains outside this task.
- Do not introduce fuzzy or semantic reference matching.
- Do not map a whole-chapter citation to its first numbered subsection merely
  because that subsection is the closest existing navigation point.
- Do not create a second extraction pipeline, resolver framework, review app,
  or artifact system.
- Do not run a standalone or repeated full-file hash over a large PDF. If the
  maintained downloader can calculate a digest during the one authorized
  acquisition stream without rereading the file, present that behavior at the
  source gate and obtain approval before using it.
- No gate authorizes cleanup, commit, push, Task 05G, or benchmark publication.

## Research / learning checkpoint

Before implementation:

1. Trace the accepted Draft F1 acquisition from landing-page entry through the
   source manifest and explain why label/URL checks passed despite the served
   document identity mismatch.
2. Inspect the maintained acquisition validator and propose the smallest
   source-general semantic identity check based on advertised label, response
   metadata, and extracted first-page/title evidence. Do not require a new
   framework or LLM.
3. Trace the two Appendix A duplicate pairs from producer blocks through
   hierarchy, sections, aliases, and the Task 04D target index. Identify the
   narrow owning stage and test several unaffected chapter-opening controls.
4. Produce an identity-impact table naming which F1, Appendix A, other-document,
   collection, review, and Task 05 records are reusable or invalidated.
5. Explain in plain language why source replacement requires new F1 conversion
   evidence, while the Appendix A repair should reuse sealed producer evidence
   unless inspection proves otherwise.
6. Trace figure records and attached captions through target construction and
   the Task 04D handoff, confirming that the extension can reuse sealed
   canonical evidence and identifying the smallest invalidated descendants.
7. Trace Chapters 8 and 9 from accepted TOC entries through body subsection
   boundaries and target publication. Propose a source-general chapter-target
   rule, its provenance representation, and negative controls for missing,
   conflicting, or noncontiguous chapter evidence.

## Plan and authorization gates

### Gate A: source-free recovery plan

1. Validate compact accepted pointers, completions, inventories, paths, sizes,
   and identities without rehashing large payloads.
2. Freeze the complete F1 impact population, the two Appendix A duplicate
   pairs, all 79 Draft EIR figure mentions, and the 19 Chapter 8/9 mentions plus
   their exact negative controls.
3. Select the smallest source-identity validation, duplicate-target repair,
   figure-target extension, and missing-chapter-target repair.
4. Publish no artifacts. Present the exact acquisition, implementation, replay,
   expected runtime/disk use, and review plan for user approval.

### Gate B: acquire and qualify replacement F1

After separate authorization only:

1. Retrieve exactly Final EIR Document Center ID `2972` into a fresh no-clobber
   source namespace.
2. Record URL, access time, HTTP metadata, server filename, byte size, page
   count, advertised label, detected title, and edition. Follow the approved
   no-rehash policy.
3. Verify that the document is the Transportation Impact Assessment and that
   expected internal material such as the Existing Traffic Conditions Memo is
   present before accepting it as the substitute.
4. Stop on redirects to a different document, inconsistent title/metadata,
   incomplete structure, resource overrun, or uncertain edition identity.

### Gate C: implement source-general repairs

After separate authorization only:

1. Add the smallest acquisition identity check in the existing source-freezer
   boundary.
2. Repair repeated chapter-divider/opening-page headings in the owning existing
   canonical or hierarchy component. Require adjacent-page, compatible-text,
   shared-parent, and heading-role evidence; fail closed when evidence differs.
3. Preserve both source blocks and provenance while exposing one logical target.
4. Extend the existing target-index path to publish an eligible canonical
   figure only when its own attached body caption begins with one exact figure
   identifier. Deduplicate by target ID and fail closed on zero or multiple
   targets.
5. Extend the owning structural/target-publication path to expose a chapter
   target only from accepted source structure. Require exact chapter identity,
   coherent subsection boundaries, and independently accepted title evidence;
   do not use response mention text or substitute the first subsection target.
6. Add focused tests for the observed Chapter 06 and 08 shapes, nonadjacent
   repeated headings, legitimate same-title sections, TOC rows, furniture, and
   different-parent controls, plus captionless figures, unparsed captions,
   duplicate identifiers, TOC/list-of-figures rows, the absent `Figure 4.8`,
   Chapters 8 and 9, and missing/conflicting chapter-boundary controls.
7. Run formatting, linting, strict typing, focused tests, and a human code-
   quality review before any replay.

### Gate D: fresh affected replay

After separate authorization only:

1. Allocate a fresh recovery namespace and identities.
2. Run replacement F1 through the maintained document pipeline. Do not reuse
   the incorrect F1 conversion or descendants.
3. Reuse Appendix A's sealed conversion/producer evidence and rebuild from the
   narrow invalidated stage unless Gate A proves a source/model rerun necessary.
4. Reuse unaffected document evidence through explicit identity correspondence;
   never copy records into a mismatched identity.
5. Rebuild every collection-level descendant affected by changed F1 or Appendix
   A targets, including target indexing, cross-document resolution, accounting,
   and handoff assembly.
6. Apply the accepted Task 04D linking policy through maintained interfaces.

### Gate E: compare and review

1. Prove that all undeclared sources and canonical content are unchanged.
2. Account for every added, removed, merged, or redirected F1 and Appendix A
   target and every changed document or collection link.
3. Confirm one logical target for Chapters 06 and 08 and retain both physical
   heading blocks as provenance.
4. Confirm proper main-document Chapter 8 and Chapter 9 targets, exact aliases,
   chapter extents, and provenance without redirecting either to Section 8.1 or
   9.1.
5. Review the replacement F1 title/structure, its Task 05F-referenced targets,
   the two revised passages, the duplicate-heading repairs, neighboring pages,
   all distinct caption-backed figure targets, and selected unaffected
   controls. Record visual usability separately from exact target identity.
6. Publish a fresh usability registry and handoff only after terminal human
   dispositions. Rebind unaffected source dispositions through an explicit
   checksummed correspondence record rather than repeating the full review.

### Gate F: hand off to Task 05G

1. Publish one compact accepted replacement handoff and usability registry.
2. Name the exact Task 05F partial candidate and unchanged Task 05D/05E records
   that Task 05G must consume.
3. Record the expected accounting changes for all 66 F1 mentions, the two
   revised-content warnings, Appendix A collisions, all 79 figure mentions, and
   all 19 Chapter 8/9 mentions.
4. Stop without replaying Task 05F or activating Task 05G automatically.

## Validation

- Exact no-clobber source and artifact containment.
- Complete F1 source identity, edition, and substitution provenance.
- No use of the incorrect 75-page F1 as a replacement source.
- Source-general duplicate-heading tests and negative controls.
- Exact figure-target construction tests and complete zero/one/many accounting.
- Exact chapter-target construction tests and missing/conflicting-boundary
  controls.
- Exact changed/unchanged document and collection accounting.
- Schema, identity, inventory, restart, receipt-reuse, and partial-state tests.
- Targeted visual review for replacement F1 and repaired Appendix A headings.
- Task 04D handoff and Task 04A-style usability validation.
- Complete Task 05G handoff expectations over the same 511 in-scope mentions.
- `make fix`, `make check`, and `git diff --check` before terminal publication.

## Review pass

- **Source claims:** Is the Final F1 always described as an edition substitute,
  with the two known revisions clearly distinguished?
- **Repair ownership:** Is duplicate suppression implemented where logical
  targets are created rather than as a Task 05F exception?
- **Replay scope:** Are only invalidated stages rebuilt, with explicit reuse of
  sealed unaffected evidence?
- **Precision:** Are more-specific chapter, figure, table, section, and page
  references preserved rather than downgraded to document links?
- **Chapter targets:** Do Chapter 8 and Chapter 9 have their own structural
  targets and provenance rather than aliases to their first subsections?
- **Maintainability:** Is the recovery understandable and debuggable without a
  new framework or corpus-specific hardcoding?

## Acceptance criteria

- A fresh, correctly identified F1 substitute is accepted with explicit edition
  provenance and no claim that it is the original Draft file.
- Chapters 06 and 08 each expose one logical target while retaining both source
  heading blocks as provenance.
- The fresh collection and Task 04 handoff are internally coherent, complete,
  deterministic, and validated.
- F1 and Appendix A receive targeted human dispositions; unaffected Task 04A
  dispositions are rebound through verified correspondence.
- Task 05G can account for all 66 F1 references and the affected Appendix A
  references without using fuzzy matching or the incorrect F1 source.
- Task 05G can structurally resolve every uniquely supported exact figure
  reference, retain `Figure 4.8` as absent unless new exact canonical evidence
  exists, and exclude image-dependent evidence from text-only model support.
- No accepted artifact is mutated and no large PDF is independently or
  repeatedly rehashed.

## Non-goals

- Reconstructing an unavailable original Draft EIR F1 from the Final edition.
- Proving that the 64 non-revision F1 passages are textually identical across
  editions.
- Rebuilding the unchanged Final EIR Volume 4 response inventory or relationship
  graph without a demonstrated identity dependency.
- Resolving missing page targets or non-Draft-EIR figure targets.
- Broad heading deduplication without the required structural evidence.
- Task 05G replay, Task 05H publication, case authoring, or benchmark release.

## Questions before activation

1. Confirm whether a digest computed once during the authorized download stream
   is acceptable, while standalone and repeated large-file hashing remain
   prohibited. If not, Gate A must define a non-digest source identity compatible
   with the maintained pipeline before acquisition.
2. Confirm the default F1 policy: all substitute links are
   `usable_with_warning`, with an additional revised-content annotation for
   `SA-Caltrans-6` and `SA-Caltrans-9`.
