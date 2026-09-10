# Task 06F: Publish Caption-Backed Figure Targets

Status: **provisional and inactive; refine from accepted Task 06A/06B and
preceding repair outcomes before authorizing implementation**.

## Abstract

Expose existing canonical figures through exact, independently evidenced figure
aliases. The accepted Task 04D index has no figure targets although canonical
figures, images, and attached captions exist. Repair target publication in the
existing document linking/alias path; do not rerun extraction or generate aliases
from response mentions. Structural resolution and visual-evidence usability
remain separate decisions.

This task implements and tests the extension. Its name describes the capability,
not authorization to publish a production replacement. Task 06G owns that replay;
Task 06H owns visual review and the accepted handoff.

## Goal

1. Build exact aliases from a figure's own eligible attached body caption.
2. Publish every independently eligible figure in the approved document scope,
   including figures never mentioned in Task 05.
3. Preserve zero/one/multiple-target outcomes after target-ID deduplication.
4. Retain original image and caption provenance without inventing figure content.
5. Keep image-dependent evidence unavailable to text-only model support unless
   independently eligible text states the substantive evidence.

## Inputs and prerequisites

Read the entry documents, Task 06 umbrella, `docs/architecture.md`, and
`docs/data_artifacts.md`, followed by:

- Task 06A's exact canonical figure/caption census and negative controls;
- Task 06B's accepted ownership, identity/reuse, and cleanup outcomes;
- Task 06D/06E's changed section correspondence where figure placement depends
  on repaired chapter structure;
- accepted canonical figures, images, blocks, and target-alias identities from
  06A's compact binding packet;
- Task 04D linking specification/policy and accepted Task 05F rule expectations;
- `docs/specs/document_linking_v1.md`, `docs/specs/semantic_structure_v2.md`,
  and `docs/specs/canonical_extraction_v1.md` as applicable to record families.

Planning evidence records 79 Draft EIR figure mentions with 35 distinct labels,
all routed to `deir_main`. Source-free qualification found unique evidence for
78 mentions and 34 figure targets; `Figure 4.8` had no exact target. Reproduce
these checks against the 06G replacement rather than treating counts as truth
independent of input identity. These are query regression checks, not the input
population for alias generation.

## Current ownership to inspect

- `src/er_commons/document_records/document_references/relinking.py:_target_index`
  extends preserved aliases with independently derived table aliases.
- `document_references/table_aliases.py:build_r6_table_aliases` demonstrates
  integration of derived aliases, evidence, target IDs, and deterministic order.
- `document_references/indexing.py` currently reports zero derived figure aliases.
- `document_references/relinking.py:_with_target_pages` already recognizes
  canonical figure records when attaching target page evidence.
- `document_structure/aliases.py:build_target_aliases` supports figure target
  types and groups normalized aliases by target identity.
- `collection_processing/record_target_indexing.py:RecordTargetIndexBuilder`
  checks aliases against sealed target streams and aggregates them.

After 06B, follow the accepted owner map if filenames change. Extend the existing
path rather than creating an independent figure index inside Task 05F or the
collection aggregator. A figure alias must enter the same persisted alias stream
consumed by maintained linking and handoff validation.

## Outputs

- A versioned exact figure-caption eligibility and identifier policy.
- Narrow alias-construction, accounting, schema/policy, and validator changes.
- Focused synthetic fixtures covering attachments, exact markers, and collisions.
- Compact census of eligible/ineligible canonical figures with reasons.
- Figure/image/caption provenance and review selections for Task 06H.
- Explicit downstream invalidation and expected Task 05G query accounting.

No production collection is published here. Separately specified source-free
record qualification may use fresh working space under the external root. Do
not open PDFs, render new images, invoke models, or hash preserved image/PDF
payloads to perform this implementation task.

## Research / learning checkpoint

Explain the difference between the identity of a figure and evidence that a
model can use. A caption may label an image without conveying its substantive
content. The [W3C PROV data model](https://www.w3.org/TR/prov-dm/) separates a
derived entity from the source entities used to produce it. Apply that principle
to aliases derived from canonical caption attachments; keep image provenance
available without claiming the alias contains the image's meaning.

Review the existing R6 table extension for reuse of publication mechanics, not
for reuse of its spatial guessing rule. Figures already have explicit canonical
caption attachments, and those attachments must be the authority here.

## Plan / spec requirement

Freeze these decisions before code changes:

1. Enumerate canonical record fields used to join figure, image, and attached
   caption records; validate every reference within the bound document.
2. Require a body figure and its own body caption, excluded from TOC/list-of-
   figures/furniture classifications under accepted evidence.
3. Freeze attachment cardinality. The observed positives have one image and one
   attached caption. Additional shapes remain explicit ineligible/review cases
   unless independently qualified and added to the accepted policy.
4. Freeze the exact leading `Figure <identifier>` grammar, including allowed
   case, whitespace, punctuation delimiters, and digit/letter components.
5. Require the caption to begin with that identifier; do not mine nearby prose
   or an internal occurrence later in the caption.
6. Parse the complete identifier before comparing. `4.8-5` and `4.8-8` never
   create an alias for `4.8`; avoid a regex boundary that truncates at a hyphen.
7. Specify marker-only and optional full-caption aliases consistently with the
   accepted 05F exact-rule interface. Do not broaden 05F matching here.
8. Deduplicate repeated evidence for the same figure target ID, retaining
   provenance. Different target IDs sharing an identifier remain ambiguous.
9. Define deterministic alias sequencing, evidence references, policy identity,
   and accounting. Reuse the maintained alias and linked-document contracts.
10. Specify structural target status separately from review/usability status and
    the text-only benchmark exclusion carried through the eventual handoff.

The rule applies to all eligible figures in 06A's approved scope; do not encode
`deir_main`, the 35 mentioned labels, or a 34-target allowlist in the builder.
The scope may be bounded by configuration, but eligibility is source-general.
If existing schema fields cannot carry caption attachment provenance, version a
small extension and enumerate readers/validators; do not silently drop evidence.

## Implementation sequence

1. Bind accepted inputs and freeze the caption grammar and cardinality policy.
2. Implement a small pure builder over canonical figure/image/caption records.
3. Integrate through existing derived aliases and exact target indexing.
4. Add explicit counts/reasons for every candidate figure, including rejected
   attachments and collision groups; do not hide them by dropping rows.
5. Extend contract validation to verify target existence and attachment evidence.
6. Verify preserved canonical content and old aliases under namespace mapping.
7. Run focused fixtures and required checks, then independent code review.
8. Deliver replay and usability-review expectations to Task 06G/06H.

## Required fixtures and expectations

| Fixture | Expected result |
| --- | --- |
| One image, one attached body caption, exact leading marker | Figure alias with caption and image provenance |
| Eligible figure absent from all Task 05 mentions | Still indexed |
| Repeated caption evidence for one target ID | One logical target after deduplication |
| Two distinct figure IDs with one marker | Ambiguous; neither chosen arbitrarily |
| Missing image, missing caption, or dangling attachment | Explicit failure/ineligibility under frozen policy |
| Multiple images or captions beyond qualified cardinality | Review/ineligible; no preferred-item heuristic |
| Captionless image with nearby figure prose | No alias |
| TOC/list-of-figures caption or furniture | No body figure alias |
| Identifier occurs later in caption | No alias under leading-marker rule |
| Caption begins `Figure 4.8-5` | Exact 4.8-5 target, never 4.8 |
| Requested `Figure 4.8` with only 4.8-5 and 4.8-8 present | Zero exact targets |
| Figure/caption attached across document identities | Validation rejection |
| Existing figure alias for same ID | No duplicate logical target |
| Existing alias conflicts with a different figure ID | Explicit collision |
| Task 05 mention text changes with source records fixed | Unchanged aliases |

Include exact-identifier suffix and punctuation controls that defeat prefix
matching. Test body/TOC status from accepted classification, not only block type.
Fixtures must exercise source-general records outside the observed main document.

## Invalidation and reuse matrix

| Evidence/product | Treatment |
| --- | --- |
| Source, chunked conversion, producer, canonical figures/images/captions | Reuse sealed evidence |
| Existing section placement | Consume 06D/06E replacement correspondence when changed |
| Independent figure content/attachment | No extraction rewrite |
| Alias/linking policy and linked-document product | Fresh affected product in 06G |
| Document publication | Replay from changed alias/link stage |
| Collection target index/resolution/accounting/handoff | Rebuild in 06G |
| Existing unchanged aliases | Preserve meaning/provenance with namespace correspondence |
| Review/visual usability | New target review or validated evidence reuse in 06H |
| Task 05D/05E/05F accepted records | Preserve; Task 05G owns subsequent exact-rule replay |

Figures alone do not invalidate conversion or semantic extraction. Combined
replay may rebuild main-document structure because Task 06E changes chapters;
that separate dependency is not permission to re-extract figures.

## Review and downstream handoff

For each distinct prospective target, provide its figure ID, image ID, attached
caption ID/text, physical page, classification evidence, and exact aliases.
The packet must permit a reviewer to distinguish image-dependent support from
substantive text in a caption. Reuse accepted renders only under 06B/06H's
correspondence policy; new rendering requires its own source gate.

Preserve the expected 78 supported mention/34 target check and the absent
`Figure 4.8` check as comparisons to reproduce, not guaranteed link counts.
Any newly found ambiguity or absence is reported individually. Task 05G may
resolve structural references while text-only evidence remains excluded.
No textual description of an image is invented to clear that exclusion.

## Validation and review pass

- Validate every attachment, source identity, body classification, and exact
  identifier before alias publication.
- Verify zero/one/multiple cardinality after deduplication by target ID.
- Verify deterministic alias ordering and stable outcomes on repeat invocation.
- Verify changed input/policy identity rejects stale qualified output.
- Use existing no-clobber and completion-last publication mechanics; incomplete
  record qualification must remain visibly incomplete.
- Check that canonical image/caption records and unrelated alias meaning remain
  unchanged; no standalone large-payload hash is needed for that check.
- Run `make fix`, `make check`, and `git diff --check` and record actual results.
- Review parsing clarity, evidence diagnostics, consumer/schema coverage, and
  separation of target identity from evidence usability.

## Acceptance criteria and stops

All eligible canonical figures in the approved scope can enter the maintained
index through independently derived aliases. Exact collisions remain explicit;
more-specific figure markers cannot satisfy a less-specific request. Tests,
provenance, usability handling, and replay instructions pass review.
Stop on unqualified attachment shapes, contradictory classification, or a schema
boundary not covered by the accepted design. Escalate bounded evidence gaps
without rerunning extraction. Implementation acceptance does not authorize 06G.

## Non-goals

OCR, figure extraction, image captioning, fuzzy matching, figure-content analysis,
new review apps, Task 05F rule changes, source acquisition, cleanup, commit,
push, Task 05G execution, or benchmark publication.

## Outcome

Pending. Record policy and owner, coverage and collision counts, validations,
review findings, and exact inputs delivered to Task 06G/06H.
