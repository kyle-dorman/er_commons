# Curator-Only Response Inventory Contract v1

Status: **Task 05B accepted; source-free and MVP-scoped**.

## Purpose and boundary

This contract defines the smallest durable record and identity boundary needed
to build the Final EIR Volume 4 curator inventory. It does not parse the PDF,
resolve production relationships, access Volume 5, or add Volume 4 to the Task
03 model corpus.

The contract encodes the accepted Task 05A evidence:

- Volume 4 contains General Responses 1 through 8. General Response 9 is a
  cross-volume placement exception and cannot be emitted as a Volume 4 unit.
- Page state is decided before unit construction.
- Comment and response boundaries require line position, geometry, style/rule
  evidence, and continuation state. A matching substring alone is insufficient.
- Raw Unicode offsets, PDFium character slots, geometry, visual evidence, and
  manual transcription are different evidence types.
- Membership claims are separate from unit text and may later support
  one-to-many, many-to-one, and forward relationships.
- Poppler and page renders are qualification evidence, not semantic production
  dependencies.

## MVP design decision

The repository carries one JSON Schema resource with a discriminated union of
individual record shapes, one Python semantic validator, and compact fixtures.
JSON Schema owns required fields, primitive types, short enums, and closed row
shape. Python owns rules that cross records: identity derivation, foreign keys,
offsets, graph evidence, correction behavior, General Response accounting, and
managed-record closure.

This follows JSON Schema 2020-12's distinction between a schema resource and
the assertions it applies, while keeping application semantics in readable
project code. The schema declares both its dialect and stable resource ID, as
recommended by the [JSON Schema core specification](https://json-schema.org/draft/2020-12/json-schema-core).

The provenance model borrows only the W3C PROV starting concepts: source and
produced records are entities, processing or review is an activity, and output
records are derived from exact inputs. It does not implement PROV-O, RDF, or
JSON-LD. The intentionally small subset follows the
[W3C PROV-O starting-point model](https://www.w3.org/TR/prov-o/#description-starting-point-terms).

Dependency references bind a role, stable upstream identity, authority, and
relative record path without rehashing upstream payload trees. Managed files
use relative paths and byte counts; working outputs may defer their own digests
until 05G publication. This provides the exact-file closure relevant to the
project without adopting BagIt; the final checksum practice is consistent with
[RFC 8493](https://datatracker.ietf.org/doc/rfc8493/).

## Record ownership

| Record | Owner | Purpose |
| --- | --- | --- |
| `activity` | 05C-05G owning stage | Compact config, schema, tool, and input binding. |
| `page` | 05C/05D | Raw Unicode text stored once, physical page state, page box, rotation, and character-slot count. |
| `page_continuation` | 05C/05D | Explicit forward page transition before unit construction. |
| `marker_candidate` | 05C/05D | Line, raw-text offset, PDFium-slot, rectangle, style/rule evidence, and disposition. |
| `source_span` | 05C/05D | Ordered page-local fragments into raw page text; it copies no text. |
| `commenter` | 05C/05D | One source-declared commenter occurrence, not global entity resolution. |
| `submission` | 05C/05D | A typed `letter` or `meeting` container with its own stable identity. |
| `source_unit` | 05C/05D | A comment, response, or General Response referencing ordered spans. |
| `membership_claim` | 05C/05D | Raw General Response membership evidence, unresolved at this stage. |
| `reference_mention` | 05C/05D | Raw mention plus resolver domain; no resolution is stored in the row. |
| `semantic_edge` | 05E | One normalized intra-Volume edge supported by one or more mention or membership IDs. |
| `draft_eir_link` | 05F | Separate exact link to a Task 04D target with Task 04A usability. |
| `diagnostic` | Owning stage | Typed unresolved, warning, or failure outcome. |
| `source_placement_exception` | 05C/05D | General Response 9's explicit Volume 5 placement without a synthetic unit. |
| `correction` | 05G | Append-only text, metadata, segmentation, anchor, or link decision. |
| `review_view` | 05E/05G | Ordered IDs and a rendering recipe; it stores no joined text. |
| `managed_file_inventory` | Each stage | Exact dependencies and managed files for one accepted candidate. |
| `stage_completion` | Each stage | Completion-last status, counts, warnings, and inventory reference. |

No reverse-edge records are authoritative. Reverse adjacency is validated or
materialized from `semantic_edge`. No joined text, HTML, render, normalized
matching corpus, or review UI is authoritative.

## Text and anchor contract

`page.raw_text` is the unnormalized result of bounded PDFium Unicode extraction
and is stored once. Its SHA-256 digest is checked against its UTF-8 bytes.
Deterministic matching or display normalization is a named implementation
projection and may be cached, but it cannot replace raw text or supply source
offsets.

Every `source_span` is an ordered list of half-open page-local Python Unicode
code-point intervals `[text_start, text_end)`. The interval must slice the
referenced page's raw text. A span may cross pages by containing ordered
fragments.

PDFium character-slot intervals and PDF-point rectangles are spatial evidence.
Character-slot endpoints are either both present or both null, and need not
equal Python offsets. Rectangles use displayed PDF points after the repository's
explicit crop/rotation transform. The page record preserves width, height, and
rotation so a later reviewer can reconstruct that basis.

Manual transcription is an accepted `text_overlay` correction. Effective
review text is derived from immutable raw text plus accepted overlays; it is not
written back to a page or span record.

## Marker and page-state rules

The closed MVP page states are:

```text
blank, labeled_blank, section_opener, zero_comment_section, continuation,
unit_start, mixed_markers, figure_or_table, revision_markup, layout_exception
```

The selected state is the page's primary disposition. Cross-cutting evidence is
captured by marker, continuation, span, and diagnostic records rather than by
creating combinations of state strings.

An ordinary accepted comment start requires a line-initial candidate with bold
and solid-rule evidence. An ordinary accepted response start requires italic
and dotted-rule evidence. Inline references and nested source headings use
their own dispositions and cannot become boundaries merely because the text
contains `Comment` or `Response`. A genuinely ambiguous candidate closes as
`needs_review`; it is not guessed into a unit.

## Stable identities

All semantic IDs use:

```text
<typed-prefix>-sha256(RFC8785(canonical preimage))
```

Every preimage contains `schema_version` and `record_type`, followed by the
fields declared in `response_inventory.contract.ID_RULES`. The code is the
executable source of truth; the important policy is:

- page IDs use source ID and one-based physical page;
- spans use source ID and ordered page/raw-text intervals; character slots,
  rectangles, and revision marks remain evidence outside stable identity;
- unit IDs use source ID, unit kind, official label, and ordered span IDs;
- mentions use source unit, mention span, and raw mention digest;
- semantic edges use relation type and endpoint IDs, while evidence IDs remain
  outside the edge identity so repeated evidence does not duplicate the edge;
- corrections use action, old/replacement IDs, and evidence IDs;
- file inventories bind exact dependencies and managed files;
- completion IDs bind stage, status, managed inventory, and counts.

Runtime timestamps, working paths, discovery order, display normalization,
confidence/disposition changes, and copied upstream payload hashes are not
semantic identity inputs. A duplicate official label at a different anchor
therefore remains a different unit; an identical semantic record found in a
different traversal order remains identical.

The sole final release ID is:

```text
inventoryv1-sha256({schema_version, stage: 05g,
                    stage_completion_id, managed_file_inventory_id})
```

It is assigned only by 05G. Working and pilot records never receive this final
designation.

## Reference and graph contract

Every raw mention declares one resolver domain:

```text
intra_volume, draft_eir, final_eir, appendix_q, external, unknown
```

Task 05E may resolve only `intra_volume` mentions and membership claims into
`semantic_edge`. One edge may cite multiple evidence IDs. Ambiguous candidates
remain diagnostics; they do not create multiple guessed edges.

The accepted intra-Volume edge vocabulary is `comment_response`,
`response_response`, `response_general_response`,
`general_response_membership`, `general_response_response`, and
`general_response_general_response`. The final two types are directional: a
General Response explicitly refers to an individual response or another
General Response.
Normalized evidence records its exact resolver rule; undeclared fuzzy or
semantic matching remains invalid.

Task 05F may resolve only `draft_eir` mentions into `draft_eir_link`. Final EIR,
Appendix Q, external, and unsupported forms receive terminal diagnostic
outcomes. Each Draft EIR link names the exact Task 04D target ID, handoff ID,
and Task 04A registry ID alongside the usability decision; its 05F activity
binds the same handoff and registry identities. A reverse graph is derived, not
copied. Semantic
similarity, fuzzy matching, and benchmark-clustering edges are outside Task 05.

Raw 05C/05D mentions may remain unresolved. Once the owning resolver closes,
each in-scope mention must have either a resolved edge/link or a terminal
diagnostic that names the mention as a subject: 05E closes `intra_volume`, and
05F closes the remaining domains. Every edge endpoint must exist, and every
edge must retain one or more raw evidence IDs.

## Terminal diagnostic vocabulary

The closed v1 diagnostic codes are:

| Group | Codes |
| --- | --- |
| Structure | `page_unclassified`, `marker_ambiguous`, `span_gap`, `source_response_heading_absent`, `unit_boundary_ambiguous`, `geometry_text_mismatch` |
| Intra-Volume graph | `dangling_reference`, `ambiguous_reference`, `orphan_unit`, `cycle_detected` |
| Official references | `unsupported_reference_form`, `unresolved_target`, `unusable_target`, `visual_only_reference`, `final_eir_only`, `external_reference`, `appendix_q_verification_required` |

`terminal` means that the owning stage has made an explicit final disposition
for that subject under the current contract. It does not imply an error. Cycles
and orphans are review diagnostics and may be valid source structure; dangling
or ambiguous references cannot produce guessed links.

General Response 9 uses `source_placement_exception`, not a diagnostic, because
its known cross-volume placement is an accounted source fact rather than a
failed extraction.

## Correction and replay rules

Corrections append evidence; they never mutate page text, spans, units, mentions,
or edges in place.

| Correction | Unit/edge identity | Replay |
| --- | --- | --- |
| `text_overlay` | Preserved | No; effective review text changes. |
| `metadata_disposition` | Preserved | No; sparse review metadata changes. |
| `resegment` | Replacement unit IDs | Yes, from source-unit construction onward. |
| `reanchor` | Replacement span/unit IDs | Yes, from source-unit construction onward. |
| `relink` | Replacement edge/link IDs | Yes, from the owning resolver onward. |

Structural correction records name both target and replacement IDs. A material
05G finding routes back to the owning stage, creates a fresh working revision,
and revalidates affected descendants. A text overlay includes reviewer, reason,
time, evidence, and replacement text, but those review metadata do not change
the source-unit identity.

## Artifact dependencies and publication

```text
Task 02 source record + accepted 05A evidence
  -> 05C pilot: pages, candidates, spans, entities, raw mentions
  -> 05D accepted complete source-unit revision
  -> 05E intra-Volume edges and compact review indexes
  -> 05F Draft EIR links and terminal reference outcomes
  -> 05G correction decisions and sole inventoryv1 release
```

Task 03J, Task 04A, and Task 04D enter only through their compact owning
identities, inventories, and completion records. Routine validation does not
rehash or copy their payloads. Task 05F alone consumes linking-dependent Task
04D records and Task 04A usability.

The required dependency roles are deliberately short: 05C binds the source
record and 05A completion; 05D binds the source and 05C completion; 05E binds
05D; 05F binds 05D, 05E, Task 04A, and Task 04D; and 05G binds 05D-05F.

Each activity declares the small set of dependency roles owned by its stage;
empty or role-incomplete dependency sets are invalid. Each stage writes a
managed-file inventory and then a completion record. A failed or incomplete
candidate cannot impersonate a completed revision. An accepted working revision
is held fixed while its declared consumers run; output-affecting changes create
a new revision. Only 05G hashes and publishes the final authoritative package.

## Source-free validator and fixtures

The maintained source-free gate is:

```bash
make validate-response-inventory-contract
```

It checks:

- JSON Schema validity and every individual record;
- RFC 8785 typed identity derivation and uniqueness;
- page text digests and half-open raw-text anchors;
- separation of nullable character-slot evidence from Python offsets;
- foreign keys and source consistency;
- marker style/rule evidence for ordinary unit starts;
- relationship evidence and resolver-domain ownership;
- resolved-or-terminal mention accounting;
- correction replay semantics;
- General Responses 1-8 plus the required General Response 9 placement
  exception; and
- an identical semantic digest under reversed discovery order.

The compact fixture set combines related cases rather than creating one file per
field. `valid_mvp_bundle.json` covers the eight General Responses, placement
exception, ordinary and inline markers, a cross-page continuation, letter
container, commenter, membership, local and Draft EIR references, multiple
edge evidence, geometry disagreement, text overlay, review view, managed-file
inventory, and completion. `valid_page_states.json` covers the remaining page
states, nested-heading rejection, and nullable character-slot evidence.
`valid_graph_cardinality.json` covers one-to-many and many-to-one direct-pair
relationships plus raw forward/reverse reference forms. The MVP bundle also
covers a terminal dangling reference without creating a guessed edge.
`invalid_cases.json` covers prohibited General Response 9 construction, invalid
offsets, weak boundary evidence, incorrect correction replay, and a dangling
foreign key.

## Proposed Task 05C public workflow

Task 05C should implement one isolated command rather than modify the sealed
Task 04D central CLI module:

```text
er-responses build --run-spec <path>
```

The new console-script name is proposed here; 05C owns its small adapter and
packaging entry rather than reopening `er_commons.cli`.

The portable run specification must name the `feir_volume_4` source record,
accepted 05A completion, exact bounded page ranges, one pilot output namespace,
schema/config/code digests, cache policy, and stop behavior. The restart unit is
one declared contiguous page range. A range is complete only after page,
marker, span, entity, raw-mention, diagnostic, and accounting outputs validate.
The command must stop on a new structural regime, source mismatch, invalid
anchor, or unclassified page; it must not repair policy during the run.

Task 05C must first pass its source-free fixture gate. Reading or rendering its
89-page proposed pilot remains separately authorized.

## Explicit deferrals

The MVP does not define global person/organization deduplication, a rich
commenter ontology, fuzzy or embedding links, confidence calibration, graph
storage, full PROV graphs, OCR/model records, arbitrary geometry polygons,
word-token identities, a rule language, bi-temporal history, permissions,
content-addressed storage, stored reverse edges, joined-text views, HTML/UI
schemas, or Task 08 outcome, eligibility, and clustering fields.
