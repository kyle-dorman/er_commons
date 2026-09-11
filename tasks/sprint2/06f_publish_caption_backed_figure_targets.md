# Task 06F: Publish Caption-Backed Figure Targets

Status: **complete and accepted. Astra and the user accepted remediation attempt
v10 for MVP correctness and human maintainability. Task 06G production replay
remains inactive.**

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

## Maintained ownership

- `src/er_commons/document_records/document_references/relinking.py:_target_index`
  extends preserved aliases with independently derived table aliases.
- `document_references/table_aliases.py:build_r6_table_aliases` demonstrates
  integration of derived aliases, evidence, target IDs, and deterministic order.
- `document_references/figure_aliases.py` owns FC1 eligibility, provenance,
  accounting, and semantic validation; `indexing.py` reports derived figure
  aliases separately from table aliases.
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

## Frozen plan and specification

The versioned
[`figure_caption_alias_v1`](../../docs/specs/figure_caption_alias_v1.md) policy
freezes the decisions below. The accepted evidence supports the exact
one-distinct-image/one-distinct-caption shape and colon-delimited leading marker,
so no early human-decision checkpoint is required for this attempt. Any evidence
outside that boundary remains rejected or review-required rather than broadening
the rule during qualification.

Implementation must preserve these decisions:

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

Implementation and bounded source-free qualification are complete and accepted
in remediation attempt v10. Astra reviewed functional correctness, provenance,
contract closure, maintainability, and MVP fitness rather than speculative
cybersecurity hardening. The user accepted that review. Task 06G remains
inactive.

### Policy and implementation

The source-general `figure_caption_alias_v1` policy is frozen in
[`docs/specs/figure_caption_alias_v1.md`](../../docs/specs/figure_caption_alias_v1.md).
It requires one distinct attached image, one distinct attached body caption,
same-document/section/single-page joins, explicit body/non-TOC classification,
and a complete colon-delimited leading `Figure <identifier>` marker. It publishes
only the exact normalized marker alias. Full identifiers such as `4.8-5` and
`4.8-8` remain complete and never yield `4.8`.

The pure builder and maintained relinking integration live in
`document_references/figure_aliases.py`, `indexing.py`, `relinking.py`,
`relink_publication.py`, and `linking_policy.py`. The parallel document-linking
v2 alias, support, and policy schemas plus `document_linking_v2.json` express FC1
figure provenance and accounting. Accepted document-linking v1 schema and policy
bytes remain unchanged. Existing aliases retain their meaning and ordering;
exact resolution unions existing figure evidence only for FC1-produced marker
keys, deduplicates by target ID, and preserves different-target collisions rather
than selecting a preferred target. Exact candidate/source/document namespace
binding and the shared semantic FC1 validator now close every published
figure/image/caption/page provenance edge against the canonical streams.

Changed tracked or newly authored files for this attempt are:

- `src/er_commons/document_records/document_references/{figure_aliases,indexing,linking_policy,relink_publication,relinking}.py`;
- `benchmarks/er_bench/schemas/document_linking/v2/{alias,support,linking_policy}.schema.json` and `configs/linking_policies/document_linking_v2.json`;
- `scripts/qualify_figure_caption_aliases.py`;
- `Makefile` and `docs/pipeline_commands.md` for the maintained type gate and
  complete operator entry point;
- `tests/test_figure_caption_aliases.py` and `tests/test_document_relinking_stage.py`;
- `docs/specs/figure_caption_alias_v1.md`, `docs/architecture.md`, this task
  record, and the current routing pages.

### Qualification evidence and accounting

The fresh packet is:

```text
pipelines/brisbane_baylands/task_06_recovery_v1/06f/qualification_v10/
```

under `ER_COMMONS_DATA_ROOT`. Its qualification ID is
`figqualv1-4c8002030423eaf6714ca5fb98ee3926d6cfda030d4cae3cfc367f0959ad8b14`.
The inventory SHA-256 is
`589264619acde4b595c8e0cb6cf51d69fad16da059cc57eb5331ccbb3db5e767`,
the completion-file SHA-256 is
`f6420863cc1e62de6cc82867f01af0d22d9086504b52cd4c3ab7f390dcdd50b6`,
and the qualification-file SHA-256 is
`1b2eaa6f6f594fbdb743b9d91fcc7a3379b782992683539634885a5d1c29f667`.
Attempts v1 through v9 remain preserved as superseded no-clobber evidence. V10
is the accepted attempt for the current code identity. V8 was superseded
after the final bounded managed-file diagnostic improvement changed the owned
qualification-script digest. V9 was superseded when the FC1 builder and validator
were tightened to accept and pass the same input-bundle object rather than
unpacking it into parallel keyword lists. Neither attempt was overwritten.

The v10 packet accounts for every one of 274 canonical figures: 178 are eligible
and 96 are rejected. Rejections comprise 62 `missing_caption` outcomes and 34
`leading_figure_marker_absent_or_invalid` outcomes. It publishes 178 unique
marker aliases and 178 target edges, all with one target after target-ID
deduplication. There are zero review-required decisions, ambiguous aliases,
multiple-target aliases, or collision groups. These counts come from the bound
canonical records, not Task 05 mentions; figures absent from the mention
population remain eligible when their own attachment evidence passes.

Every eligible target retains upstream/local figure identity, image and caption
IDs, page and physical-page provenance, attachment/reference counts, section and
classification evidence, and exact marker. Structural eligibility remains
separate from `text_only_evidence_status: not_evaluated_pending_task06h`; no
caption or image is claimed to supply substantive text-only evidence.

### Validation, invariants, and next review

The prior v7 validation passed 1,781 tests but its mypy result covered only the
483 files under `src/`; Astra correctly identified the qualification script as
outside that gate and found its return annotation error. Remediation adds the
script to the maintained type target, which now covers 484 files. Focused tests
cover exact marker parsing, suffix and punctuation controls,
missing/dangling/cross-document
attachments, cardinality, body versus TOC/furniture classification, repeated
evidence, existing aliases, collisions, deterministic order, exact
source/document namespace binding, FC1-only union accounting,
semantic provenance reconstruction, complete current-identity recomputation,
FC1-only packet membership, packet omission/duplication/tamper rejection,
no-clobber publication, schema closure, and prohibited I/O.

For attempt v10, `make fix` passed with 674 files unchanged. `make check` passed
formatting, lint, mypy over all 484 maintained source/script files, and all 1,781
tests. The focused Task 06F suite passed 71 tests. Fresh packet publication and
the documented `--reuse-existing` invocation both passed and emitted their
resolved paths. `git diff --check` passed. Mention independence is an input-
boundary property established by the builder API and code inspection: no mention
stream is accepted or read by the FC1 builder.

The attempt preserves accepted conversion, producer, canonical
figure/image/caption/page, section-correspondence, Task 06B identity/reuse, and
document-linking v1 evidence unchanged. It did not open a PDF, render or inspect
an image, load a model, rerun extraction, hash preserved PDF/image payloads, or
execute production document, collection, or reference replay. Task 06G remains
inactive, and Task 06H still owns visual/text-only usability review.

### Resolved Astra remediation

The user classified Astra's six v7 code-quality findings as blocking. Attempt v10
implements all six without broadening the FC1 policy or changing its accounting:

1. bounded semantic diagnostics now report the first record identity and field
   path with expected/observed values; packet closure reports bounded sorted
   missing and extra paths;
2. the qualification script's return annotation is corrected and the maintained
   `make type` gate checks both `src` and the script;
3. `with_effective_figure_accounting` is the single pure owner for existing-plus-
   FC1 collision accounting in standalone and relinking validation;
4. relinking constructs one `FigureAliasValidationInputs` object and passes that
   same object through the FC1 builder, immediate validator, retained
   `RelinkBuild`, and publication validator;
5. the ordering test no longer claims mention-independence from an unused value,
   and every semantic/packet mutation requires its intended exception type and
   mutation-specific diagnostic; and
6. every CLI selector has actionable help, the command logs published/reused plus
   the resolved path, and `docs/pipeline_commands.md` owns complete fresh and reuse
   invocations with input-selection guidance.

The design remains proportionate for the MVP. FC1 verifies exact section equality
while relying on the accepted upstream semantic structure for section membership.
Astra and the user accepted attempt v10; Task 06G remains inactive. An
independent read-only maintainability review found no remaining actionable
finding: it verified each of the six remediations, preserved policy scope, focused
and full validation, and the continued Task 06G stop. This was an MVP correctness
and maintainability review, not a cybersecurity audit. A follow-up v10 delta
review also verified literal same-object flow from relinking assembly through the
builder, immediate validator, retained build, and publication validator, with no
material or nonmaterial finding.

### Acceptance

On 2026-09-11, Astra and the user accepted Task 06F remediation attempt v10 for
MVP correctness and human maintainability against `b9349e5`. Astra independently
confirmed closure of all six blocking findings, the recorded identity and three
packet digests, semantic reconstruction and verified reuse, 1,781 passing tests,
the 484-file maintained mypy gate, the focused 71-test result, and unchanged
document-linking v1 policy/schema files. Astra also compared v7 with v10 and
found aliases, target-index entries, and qualification records identical after
mapping the qualification-ID namespace, directly confirming that remediation
preserved the qualified result.

One nonblocking coverage opportunity remains: a future focused test may lock
down diagnostic truncation and record-identification formatting. Direct review
and an exercised long-value case passed, so this does not reopen Task 06F.

## Task 06B interface handoff

Both Task 06B gates now supply the maintained
[command map](../../docs/pipeline_commands.md) and
[executed owner map](../../docs/specs/task06b_gate2_executed_inventory.md).
Use explicit current requests with original per-source accepted manifests and
seals; historical recipe validation does not reopen removed implementation paths.
Document/collection v3 supports declared replacement membership. Compact checks
must retain the shared verification budget and must not claim new payload-byte
equality. This inherited handoff updates interfaces only. Task 06F's accepted
policy does not authorize the separate source, conversion, Task 06G replay, or
Task 06H review gates.
