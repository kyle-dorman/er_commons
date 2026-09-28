# Evidence review contract

Task 07D separates approved claim relevance from evidence support. The narrow
`pilot_evidence` adapter prepares native Label Studio tasks and normalizes saved
human judgments. It performs no discovery, API operations, or model inference.
The caller verifies the accepted 07C.1 result/export and the accepted source,
handoff and usability seals before supplying `approved_review` and `data_root`.

## Packet and source anchors

`schema_version` is `er_commons.task07d.evidence_packet.v2` for current
section-based review. Historical v1 packets remain supported. Required fields:

- `case_id`, `claims`: exact candidate-claim dictionaries in approved review
  order; IDs come exclusively from `evidence_candidate_claim_ids`.
- `context`: `comment_html`, `concerns_html`, `response_html` copied from trusted
  prepared 07C.1 task data, compared exactly by the adapter. Source text in these
  HTML views must be escaped.
- `source_bindings`: preserved accepted result/export, response inventory,
  handoff, usability, source-version and source metadata references.
- `candidates`: ordered candidate records described below.
- `claim_candidates`: one row per claim, in queue order, containing `claim_id`,
  `candidate_ids`, `overflow_candidate_ids`, and `search_gap`. The historical
  case-level adapter accepts at most three displayed candidates; current claim
  review presents all mapped candidates, including recorded overflow.
- `discovery_attempts`: bounded discovery receipts, including failed searches,
  exact query/reference, filter, engine/options, ordered hits, limits and stop
  reason. Resolved graph traversal records actual accepted edges and hop count.

Each candidate contains `candidate_id`, `source_id`, `edition`, `source_url`,
`physical_pages` (one-based), `printed_labels`, `limitations`, `anchors` and
`quote`. Optional `title` and `pdf_url` improve the readable citation and local
PDF access without replacing source identity. Optional `presentation_header_rows`
is a visually checked display hint: contiguous blank placeholders in those
header rows merge into the preceding nonblank cell. Body cells and canonical
records remain unchanged, and the hint participates in candidate identity. Metadata references in `source_bindings` retain source licensing,
retrieval and acceptance restrictions. Candidate ID is `evidence07d-` plus the
SHA-256 of sorted Unicode JSON for the complete candidate excluding its ID.
Changing context, provenance, or wording changes the candidate identity.

Each anchor contains a data-root-relative JSONL `path`, `record_id_field`,
`record_id`, full exact canonical `record` snapshot, `text_field`, half-open
Unicode `start`/`end`, and exact `quote`. Dotted paths address canonical table
cells, for example `cells.0.text`. The adapter reads the actual JSONL, rejects
duplicate record IDs, compares the complete snapshot and exact text slice, and
checks source identity when present in canonical records. Candidate `quote`
is the ordered anchor quotes joined with two newlines. Full canonical table
snapshots supply readable table cells, including headers; captions, units and
notes require accompanying anchors. No invented flattened table is authoritative.
Canonical records and original sources remain immutable in place.

The preparation caller owns accepted-corpus eligibility; checking a quote alone
cannot establish that a source is approved. Response Volume 4 is rejected as
evidence. Final F1 remains possible only through its explicit accepted exception.

## Human review (original case-level form)

Shared evidence cards are displayed once. Every shown claim/candidate pair has
an independent native choice: `supports`, `partial`, `context`, `contradicts`,
`no_support`, `unusable`. Partial judgments require a note identifying the covered
part **and** remaining gap; contradiction and unusable require a reason. The
normalizer enforces a nonempty note; humans assess its semantic completeness.

Every claim has an explicit overall outcome: `supported`, `partial`,
`conflicting`, `no_support_found`, or `unresolved`. Support, partial and conflict
require a selected evidence set. Partial, conflict, unresolved and any joint
inference require a note. Overall outcomes are human judgments, never aggregates
computed from pair labels or relevance. The validator rejects logically
incompatible selected sets: full support requires a supporting passage or a
reasoned joint set of at least two partial passages, partial requires positive
evidence, and conflict requires contradictory evidence. A no-support outcome
alongside positive pair judgments requires an explanation. Supporting claims do not automatically
establish their parent claims. Search absence never establishes corpus absence.

Case state is `reviewed` or `needs_context`. No human values are preselected.
`reviewed` requires complete valid judgments; `needs_context` preserves partial
work and validation errors and requires an explanatory case note. Overflow is
retained visibly and remains unreviewed until a new bounded presentation.

Normalization checks trusted prepared task equality, native task/annotation and
reviewer IDs, exact known controls, their type and object binding, duplicate
fields and unknown evidence references. It records native annotation, timestamps,
export lineage, packet/task/form/annotation hashes and separate human judgments.
Synthetic save/reload QA is kept in a separate project/export and cannot be
promoted to Kyle's review.

## Rationale and verification

Native [Choices](https://labelstud.io/tags/choices),
[TextArea](https://labelstud.io/tags/textarea) and
[HyperText](https://labelstud.io/tags/hypertext) keep the UI small and preserve
field associations in normal exports. Source entities, retrieval activities and
reviewing actors remain distinct, following the lightweight provenance
separation in [W3C PROV](https://www.w3.org/TR/prov-overview/). Actual save/reload
must still be checked in the installed Label Studio version.

`prepare_task(packet, data_root=..., approved_review=...)` validates consumed
source bytes and immutable claim membership. `build_form(task)` generates XML.
`normalize_review(task, annotation, expected_task=..., export_lineage=...)`
normalizes a saved native result against the verified task. The external run
publishes no-clobber packet, task, form, discovery receipts and manifest with
owned output hashes and implementation identity.


## Claim-at-a-time review (forms v1–v4)

The current prototype uses `prepare_claim_tasks` and `build_claim_form` to
present one approved claim per native task. Preparation first validates the
complete case packet against the approved review, then binds each task to its
stable `claim_id`, full packet hash and form version through `claim_task_id`.
The full verified packet remains in task provenance; only the active claim's
mapped evidence is displayed. Original aliases survive filtering (for example,
a claim using only E03 still calls it E03). The approved concern is visible below the claim; verbatim original comment,
relevance and response context remain expandable. Support judgments never modify
approved relevance.

The current common form allocates the maximum full candidate count across the
packet (at least one control slot for empty packets). CSS hides inactive slots using
the trusted evidence-count marker; dynamic evidence-set choices expose only
active candidates. Hidden slots are not accepted annotation fields: normalization
rejects their results, including empty results. No support values are preselected.

`normalize_claim_review(..., expected_task=..., export_lineage=...)` produces
`er_commons.task07d.claim_evidence_review.v1` with one `claim_review`, stable
`claim_id`/`claim_task_id`, `claim_status` and `claim_note`. Reviewed claims must
pass the same pair/set rules above. Needs-context claims preserve partial work
and validation errors with an explanatory note. Exact trusted task equality,
native provenance and field validation remain mandatory. A claim annotation
contains no case status. Whole-case completion requires the exact expected set
of unique claim IDs, each validated as reviewed; a count of saved annotations
is insufficient. No automatic case-completion helper is provided.

Native sequential queue navigation reduces review burden while retaining
claim-specific decisions for shared evidence. Browser QA checks Submit advances,
independent saved notes, inactive controls, and source identity. The original
case-level functions and sealed prototype remain unchanged historical inputs.


The section-based layout introduced in `task07d.claim_evidence_review.v4` has exact claim and
reviewed question first, reviewer notes/labels on the left and citable excerpts
on the right. Verbatim original comment remains expandable next to the question.
Technical extraction/eligibility notes are collapsed in the reviewer pane.
`build_claim_form(version)` retains exact v1/v2/v3 form bytes for existing tasks;
normalization uses the trusted task's form version when recording its hash.

An optional candidate `citation_relation` object records `kind` (`supplied`,
`corrected`, or `omitted`) and a readable `note`. Corrected/omitted citation notes
are displayed separately from excerpts; routine supplied citations do not add
reviewer warnings. The original response wording is preserved. These metadata
participate in candidate identity; source anchors remain independently exact.
This relation describes how the response cited a source, never whether that
source supports a claim. Discovery searches beyond supplied citations within
the recorded budget; a resolved citation is not a search-completeness test.


Current preparation derives `data.max_candidates` from the full packet and
includes that capacity in claim task identity. Build the project form with
`build_claim_form(max_candidates=tasks[0]["data"]["max_candidates"])`.
Normalization verifies the capacity against the trusted packet and uses it in
the form hash; unknown or inactive controls are still rejected. No arbitrary
three-source limit hides a relevant candidate. Mapping order places essential
passages first; the packet itself remains unchanged by preparation.

Optional candidate `retrieval_reason` is escaped readable text shown only in
reviewer notes. It explains inclusion or records a curator observation without
becoming a source quotation, relevance change, or human support judgment.


## Section and table citation units

Current packet v2 requires `citation_unit` on every candidate. The unit has its
own schema version `er_commons.task07d.citation_unit.v1`, a kind (`section` or
`table`), canonical section ID/snapshot, full breadcrumb, opening heading anchor,
exclusive next-heading anchor, complete section membership, displayed membership,
and any separately cited table units. The table kind also records its canonical
table ID. Candidate identity binds all of these fields; `pilot_citation_units`
verifies them against the actual parsed files, not merely the supplied snapshots.

Narrative display contains the complete ordered heading-defined text before the
next body heading. Separate table citations explicitly account for any table,
caption and notes removed from that narrative unit. It is invalid to append the
next section, omit narrative blocks, splice selected spans into a claimed whole
section, or declare an unbound table exclusion. Attached footnotes stay with the
unit. Running page furniture is not narrative evidence.

Tables remain distinct structured citations with all nonempty cells, caption
and notes. The present validator supports the audited section-tail tables: the
caption/table and following note blocks occupy the end of their parsed section.
It rejects other layouts pending an explicit association rule; it does not infer
arbitrary trailing text to be notes for future corpora.

Display citation labels are deterministic: exact canonical leaf heading or
canonical table caption plus verified printed labels. Source ID is explicit,
and the complete parsed heading path is expandable. Exact blocks/cells remain
beneath this semantic citation identity. Page numbers locate a citation rather
than define its unit. Historical forms v1–v4 remain unchanged; current form v5
still binds the explicit capacity and new prepared task data.

## Context and metric boundary

Source validity and support role are separate. Every displayed section/table,
including background material, must be source-valid and citable. Human judgments
continue to classify each claim/unit relationship. A retrieval reason describing
background does not assign a human `context` label.

The sprint's existing primary retrieval coverage scores only curator-approved
direct-support evidence; context-only records are optional for that denominator.
Omitting optional context is not a missed required evidence record. Context
cannot substitute for support of a substantive claim, and optional context is
not exempt from citation accuracy. No context weighting or new metric is frozen
or implemented by this prototype.


## Current simplified outcome (form v5)

`task07d.claim_evidence_review.v5` retains each source relationship/note and one
explicit overall outcome/note. It removes `c001_set`, `claim_status`, and
`claim_note`; these fields are rejected in current normalized annotations.
There is no second human completion decision or inferred evidence-selection
set. Multiple supporting passages alone do not require a joint-reasoning note.
A supported outcome based only on two or more partial passages still requires
an explanation, as do partial, conflicting, and unresolved outcomes and
no-support outcomes paired with positive source judgments.

`normalize_claim_review` produces `er_commons.task07d.claim_evidence_review.v2`
for v5 tasks. It retains exact native provenance, `claim_review.pairs`, explicit
`outcome` and `note`; it emits no `claim_status`, `claim_note` or `evidence_set`.
`review_complete: true` is a mechanical assertion that a saved annotation has
all required relationships, an explicit outcome, required explanations and
consistent values. Missing relationships/outcomes reject a final review.
Drafts remain native unfinished records and are never promoted automatically.
Historical forms and normalizers v1–v4 remain available with their original rules.

When simplifying an existing draft, retain original task/draft IDs, timestamps,
full native result and exact field mapping. Copy only retained fields into a new
draft without submission. Removed fields stay in migration provenance, not in
the new review. Preserve any existing overall note; nonempty legacy claim notes
need an explicit lossless mapping before migration. Compare saved values and
browser resume against the original. Computed elapsed-age strings may change;
identities, timestamps and judgments must remain exact.


## Case-level citation export decision (2026-09-28)

The benchmark-facing case exports separate reviewed claims and a deduplicated
citation list; the target response likewise presents citations, claims, then a
final answer. Citation-to-claim links are not required in that output. Existing
claim/unit judgments remain lossless review provenance, not mandatory prediction
fields. This is an export contract; the current v5 form and saved reviews remain
unchanged until a separately versioned implementation.

Deduplicate within a case by source document, accepted extraction identity, unit
kind and canonical section/table ID, not by display label, page, candidate ID or
claim ID. A table and its enclosing narrative section remain distinct units.
Preserve verified citation labels, source links, exact anchors and all contributing
review/candidate identities; presentation or discovery differences must not create
duplicate citations or erase provenance. Conflicting source bindings must fail
validation rather than be merged by title.

The final citation levels are `support` and `context`. Any approved supporting
use makes the unique citation `support`, including evidence for a supporting
claim or for a direct claim. Only-context citations are `context`. Thus support
takes precedence over context across reviewed claims, but does not assert that
the citation supports every claim. Claim relevance (direct/supporting) does not
set citation level; the actual evidence judgment does. Context stays optional
for required evidence coverage and remains subject to citation accuracy.

There is no final `partial_support` citation level. Preserve historical partial,
contradictory, unsupported and unusable judgments in the review history; do not
silently relabel them context or full support. A partial-only unit requires an
explicit support/context disposition before publication; a separate approved
supporting use can establish support without erasing the partial judgment.
Rejected candidates are not automatically exported as context.

Validate one citation per semantic identity, support precedence independent of
claim order, distinct tables/sections, exact provenance, and preservation of
claims without mandatory citation links. This reduces repeated citation scoring
and review-output complexity, at the cost of losing explicit attribution in
the benchmark-facing format. Source support must still be assessed from actual
claims and cited content; list membership alone does not establish it.


## Repeatable discovery procedure

[Task 07D search protocol v1](task07d_search_protocol_v1.md) owns the search plan,
query budgets, fixed index settings, agent assignments, source expansion and
coverage receipts for subsequent authorized runs. This specification continues
to own citation units, review semantics and final export aggregation. Historical
prototype search records remain valid history, not retroactive protocol v1 runs.

## Audited citation assembly extensions for remaining cases

The 2026-09-28 expansion retains packet v2 and form v5. Citation-unit versions
are independently validated; these extensions do not modify accepted extraction
records or assign human support judgments.

- Unit v2 permits explicitly audited table associations, bound by a hashed receipt
  to canonical files and section membership. Table captions, cells, source and
  notes remain complete; intervening narrative stays in its section. Current
  receipts cover main sections 1188, 669 and 2698. The historical v1 section-tail
  rule remains unchanged; unreviewed multi-table layouts are not guessed.
- Unit v3 is the exact [Section 8.5.2 boundary overlay](task07d_boundary_override_note.md).
  Its PDF-checked receipt accounts for every original record, excludes the
  mistaken running header and explicitly repairs one inline impact-label order.
  It cannot authorize arbitrary source-boundary changes.
- Unit v4 preserves complete text and figure locations in a section without
  tables. Every figure has its exact canonical snapshot/file binding and an
  ordered link to the original PDF. Source text remains verbatim; figure
  interpretation is not inferred from text. The visual-review limitation belongs
  in reviewer notes, not source quotations. Missing text, figure references or
  display placeholders reject validation.

These are candidate-presentation rules. Unsupported table fragments, ambiguous
notes across headings, and source defects without an audited rule remain explicit
assembly gaps. They are not silently converted into partial source excerpts.


## Bounded MVP disposition of five review flags (2026-09-28)

The user explicitly accepted noisy claim relevance in this completed round and
instructed that no claims be dropped or relabeled for relevance. Preserve all 31.
For SA-Caltrans-33 task164, apply the separately bound user clarification changing
only E03 from partial to context; keep the claim supported. Preserve the native
annotation and record the effective label as a derived clarification.

For tasks184,185,195,197, preserve the submitted source judgments and overall
outcomes despite their consistency warnings. This specific user-authorized MVP
exception permits final case export with warning provenance; it does not weaken
source identity/completeness checks or silently make strict validation pass.
Derive citation levels exclusively from source judgments, never those conflicting
overall outcomes. The tracked `task07d_review_export_status.json` binds the exact
source export and disposition. No additional relabeling is authorized by this
exception, and future review batches retain their ordinary validation rules.


## Implemented case citation export v1

`pilot_case_citations.aggregate_case_citations(packet, reviews)` returns separate
`claims` and `citations` plus an `audit` object. The run writes audit separately.
Claims retain accepted wording/relevance and response-source provenance. Citations
have stable semantic IDs, a support/context level, source/extraction identity,
complete citation units, exact anchors/text, page labels, links and limitations.
No evidence-to-claim mapping is required in the case payload. Native judgments,
all candidates (including exclusions), original review links and aggregation uses
remain in audit files. Presentation-only citation labels do not split identities.
Conflicting structural source bindings fail. Legacy prototype extraction identity
is recovered from verified canonical anchor records, with mixed identities rejected.

The bounded run verifies input manifests/closure, all 31 claims against the accepted
07C.1 handoff, native task bindings and canonical sources before aggregation. It
applies only the exact user-authorized task164 clarification and four accepted
warning signatures. Partial-only citation units require explicit disposition;
overall outcomes never create source support. The final result is routed through
`task07d_final_result.json`. This does not authorize new label corrections or
establish eligibility for the eventual benchmark split.


## Maintained replay and quality gate

Use `make export-pilot-case-citations CASE_EXPORT_DIR=...` or the explicit
`pilot_case_export` module interface for future replay. The sealed external scripts
remain historical evidence. The maintained exporter consumes the same bound input
records and refuses overwrite, input-directory writes, duplicate identities and
unapproved validation exceptions. Its structured warning path retains the complete
normalizer result instead of independently parsing native fields a second time.
See the [maintainer guide](../task07d_maintainer_guide.md). Current code hashes and
exact output comparison are bound separately in `task07d_code_quality_result.json`;
the earlier final-export manifest is never edited to erase its code lineage.
