# Task 08E question research packet v1

The current [08E task](../../tasks/sprint2/08e_review_group_evidence.md) owns
scope. This contract implements Phase A only. A prepared packet is advisory,
awaiting human review; it does not establish eligibility or authorize 08F.

## Inputs and saved plans

`group_evidence_research.create_plan` accepts an exact case snapshot containing
`case_id`, `approved_claims` and all frozen question, original comment, response
context, support chains, citation leads, exclusions, required rechecks and holds.
The caller verifies the entire sealed 08D input before constructing snapshots.
The full snapshot is copied into the packet, not selectively reconstructed.

The `task08e.research_plan.v1` plan binds that snapshot with `input_sha256`.
Every track requires a question-specific `objective`, positive `queries` budget
and positive `follow_up_queries` allowance. `rationale` explains complexity.
Tracks are `direct_claims`, `question_gaps`, `definitions_methods`,
`broader_context` and `counterevidence`. Save the plan before executing searches.
Expanded budgets require saved numbered revisions, predecessor hash and reasons.
Save exact query expressions before execution; retain failed attempts unchanged.
Every saved query intent must end in its matching maintained receipt or an
explicit `aborted_before_receipt` diagnostic bound to the intent and error.
Each track retains such references in `aborted_query_diagnostics`, with a named
failure explanation in the packet's gaps or limits. An aborted invocation is
not an empty search result; retries use a fresh identity.
Pass a numbered immutable plan through `run_query(plan_path=...)`; the packet
records its `plan_filename`. Earlier queries retain their original plan binding.

Use maintained `pilot_evidence_search` retrieval. Its lexical ranking finds
candidates, not truth or support. Beyond-claim searches may use a question-part
identifier in the legacy `claim_ids` receipt field; explicitly mark its purpose
as question research rather than inventing an approved claim.

## Packet and source occurrences

`task08e.research_packet.v1` retains `frozen_input`, `plan_sha256`, `sources`,
`claim_findings`, `beyond_claim_findings`, `track_results`, `model_provenance`,
`remaining_gaps` and `limitations`. Status is initially `working`, then
`prepared, awaiting human review` after assembly. `human_decisions` is always
`[]`; `eligibility` and `disposition` are always null in Phase A.

Each source is a maintained 07D/08E canonical candidate plus `occurrence_id`.
Retain repeated occurrences with distinct IDs: never deduplicate a question's
sources or pool sources across questions. Maintained citation-unit validation
checks exact sections, source editions, pages, canonical anchors, table families,
notes and render receipts. `table_render_checks` requires one entry per table
occurrence: exact `occurrence_id` and `candidate_id`, `status: agent_checked`,
`actor`, substantive `comparison`, `limitations`, null
`human_usability_decision`, and `renders` containing every physical page with
a byte-bound `ref`. Missing pages or changed render bytes fail validation.
Individual candidate validation checks exact record
snapshots and excerpts. An occurrence ID is presentation identity and does not
alter the maintained candidate identity.

`group_evidence_mixed` extends the maintained canonical loaders and anchors for
complete sections containing both tables and figures. Its versioned unit retains
every direct member, all table cells and continuation members, and explicit
original-PDF figure locators. It enforces the existing canonical next-heading
boundary; it cannot repair source hierarchy. The unit is subject to table review
checks for every section page. Figure content is not converted into text evidence.
This avoids dropping a relevant forecast paragraph merely because its section
contains multiple media types.

Each approved claim has exactly one `claim_findings` record containing a unique
`finding_id`, exact `claim`, `citations`, `limitations` and `remaining_gaps`.
Each citation binds both `occurrence_id` and `candidate_id`, gives a verbatim
`excerpt` contained in the validated source, and proposes `relationship`
(`Support`, `Partial`, `Context`, `Not support`, `Contradicts`) plus `reason`.
An uncited claim requires an explicit bounded-search gap. It cannot assert
that evidence does not exist.

`beyond_claim_findings` retain unique `finding_id`, one non-claim `track`,
`summary`, grounded `citations` and `limitations`. They cannot contain a new
`claim` object. Definitions, assumptions, contextual reasoning and conflicting
material remain separate from approved response claims. Unsourced unresolved
questions belong in `remaining_gaps`, not asserted factual findings.

Every `track_results` entry retains exact `query_receipts`, `stop_reason` and
`remaining_leads`. A receipt retains maintained fields, including query/index
identity, expression, purpose, hits and completed/error status. Add
`inspected_hits` with exact source/record IDs, disposition and reason. Returned
hits are not implicitly inspected. Every returned record needs an explicit
disposition; screen its text for specific relevance and inspect full units for
pertinent leads. Generic uninspected defaults do not establish semantic coverage. A track without searches needs a specific
`not_applicable_reason`, independently reviewed for adequacy.

`model_provenance` records Astra model identity, semantic `input_sha256`, prompt
and raw output hashes, and `input_ref`, `prompt_ref`, `output_ref` byte bindings.
References are data-root-relative `{path, sha256}` objects. Save actual model
input, prompt and raw output; a model's claim that it searched is not a receipt.

## Qualification and publication boundary

`validate_packet` checks exact frozen inputs, all claim versions, all five
tracks, bounded receipt counts, source-unit integrity, excerpts and blank human
fields. Semantic coverage and summary faithfulness require independent review;
passing structural checks is insufficient to publish a batch. Review must
specifically examine exclusions, required rechecks, counterevidence, rendering
checks and honest search limits. Table machine/render checks do not replace
any remaining human source-usability decision.

`group_evidence_publication` owns the original ordered 50-case closure, held/deferred exclusions,
immutable file inventory, independent-review receipts and completion-last seal.
It must revalidate actual packet bytes before exporting or resuming. Working
or blocked cases remain explicit and cannot masquerade as prepared. Human chat
review starts only in a separately authorized chat with exact display bindings.

## Design notes and research

Reuse the maintained search, canonical-source and rendering boundaries rather
than writing another parser. Keep explicit input/output/model relationships as
recommended by [W3C PROV](https://www.w3.org/TR/prov-overview/). The
[SQLite FTS5 documentation](https://www.sqlite.org/fts5.html) explains lexical
search and BM25 ranking; neither implies semantic evidence support. Standard
JSON plus checked hashes keeps these small glue contracts restartable and
inspectable without another workflow framework.

## Runtime and publication

The project Python build lacks FTS5. The qualified execution command and isolated
dependencies are recorded in the external `fts_runtime_qualification.json`;
use that explicit runtime for live searches. Its actual FTS tests must pass
without a skip. Do not reinterpret runtime errors as empty search results.

Before publication, save each `independent_review.json` bound by semantic
`packet_sha256`, with reviewer `worker`, `coverage`, `export_fidelity`,
`scope_exclusions`, `counterevidence`, empty `blocking_findings` and `status: pass`.
This is an agent quality check, never a human evidence decision. The publisher
compares all raw saved receipts, checks the accepted corpus identity and complete
canonical table continuations, and verifies original PDF bytes and URLs against
the exact retrieval manifests pinned by the intake audit. An internally consistent
alternate document edition is rejected. Publication requires an explicit
`--qualification` receipt and saves checksummed references to that receipt and
`REVIEW_INSTRUCTIONS.md`. It creates blank initial journals, readable
`REVIEW.md` files and complete `SOURCES.html` views retaining every repeated source
occurrence. Its completion inventory retains prior versions and failures.
`verify_prepared_result` checks exact file closure and checksums before resuming;
new human-review journals belong outside the sealed preparation directory.

## Explicit research reopening supplement

The 2026-10-07 user authorization reopens C014, C020 and C024 for question-first
research, with the original 08D decisions preserved. These snapshots contain zero
approved direct/supporting claims. Research can still produce grounded findings
for question gaps, definitions, broader context and counterevidence. The direct
claim track must explicitly explain the absence of released claims; retained
unclear or rejected claims remain leads, not approved claims.

`group_evidence_extension` binds the explicit authorization and verifies the
original 08D handoff before projecting the three snapshots. The supplement uses
the same packet/source/query/render validation and blank chat-journal contracts.
A separately sealed combined index references the unchanged 50-case seal and the
three-case supplement in original saved order. It verifies both child inventories,
exact case rows and totals; the four 08C deferrals remain excluded. Reopening is
research authorization, never a human evidence decision or eligibility finding.

The combined handoff's review instructions govern the 53-case queue. Original
50-case instructions remain historical and are superseded only for explicitly
reopened membership. No earlier source, claim or evidence approval is broadened.
