# Architecture Contract

This file owns the current technical shape: package boundaries, CLI direction,
pipeline stages, and artifact separation. Detailed task history belongs in the
numbered task records and versioned specifications.

## Design principles

- Compose maintained open-source packages before writing project code.
- Keep project code as thin, typed glue around explicit input/output contracts.
- Prefer plain files, manifests, and small CLI commands over hidden notebook
  state or a workflow framework.
- Make every nontrivial stage restartable and observable through a manifest,
  summary, or structured log.
- Add a dependency only when the owning task names the job it solves and the
  reasonable alternatives have been considered.
- Treat human maintainability as a separate gate: ownership, readability,
  typing, testability, and recovery behavior must be understandable from the
  code.

## Repository layout

```text
src/er_commons/          # Package-backed CLI and project glue
pipelines/               # Tracked pipeline specs and wrappers
benchmarks/er_bench/     # Benchmark contracts, schemas, and small fixtures
configs/                 # Checked-in source-scoped configurations
tests/                   # Fast tests for project-owned behavior and contracts
docs/ and tasks/         # Routing, decisions, plans, and task outcomes
```

Large source files, extracted content, model files, review bundles, and run
outputs live under the external root described in
[`data_artifacts.md`](data_artifacts.md).

## Maintained document and collection pipeline

The production dependency direction is:

```text
source_release + artifact_io
  -> document_parsing
     -> hierarchy_inference
     -> document_records
  -> document_publication
  -> collection_processing
  -> extraction_reporting

human_review_support consumes published evidence but is never a production dependency
```

Responsibilities are intentionally one-way:

| Responsibility | Owns |
| --- | --- |
| `document_parsing` | Stable content parsing, heading evidence, routing, and clean table reconstruction. |
| `hierarchy_inference` | Hierarchy evidence and deterministic hierarchy decisions. |
| `document_records` | Record mapping, sections, printed labels, aliases, document-local reference links, and the shared exact local target-resolution engine. |
| `document_publication` | One-document attempts, lineage, reuse, and atomic publication. |
| `collection_processing` | Scope accounting, target indexes, cross-document resolution, and handoff assembly. |
| `extraction_reporting` | Machine summaries and terminal-status reporting. |
| `human_review_support` | Candidate-neutral review selections, renders, and human findings. |
| `navigation_overlay` | Source-free Task 04C input binding, page/entity correspondence, sealed Docling TOC-text projection, sparse effective-navigation read model, TOC-specific linking adapter, and derived publication. |

The public production entry points are:

```text
er-commons documents publish
er-commons documents relink
er-commons collections assemble-handoff
er-commons collections validate-handoff
er-commons collections validate-contract
```

Document publication consumes an explicit v2 document specification. Collection
assembly consumes an explicit v2 collection specification. No source or
Appendix P is selected by an implicit runtime default. Historical Task 04C
utilities are retained in its task record rather than listed as production
interfaces.

## Publication and identity boundaries

Task 03J uses two main document-stage publications:

1. `dconv1-` conversion bundles bind source bytes, page accounting, Docling
   options, runtime and model inputs, and the conversion inventory.
2. `prv1-` producer bundles bind an exact conversion seal to routing, table,
   and remaining producer policy.

Later document records and publication stages reference those sealed bundles.
They do not copy or mutate them. A complete stage is published only after its
completion record and managed-file inventory are checksummed. Failed attempts
retain diagnostics but cannot impersonate a complete result.

The current full-corpus candidate is the completed Task 03J v4 run. Its generated
lineage directory is named
`pipelines/brisbane_baylands/task_03h_clean_full_v4/`; the retained `task_03h`
stem is an implementation name, not permission to consume Task 03H artifacts.
The exact identity chain is owned by the [Task 03J outcome](../tasks/sprint2/03j_run_final_canonical_extraction.md).

Production identities bind every output-affecting source, scope, package, model,
policy, schema, configuration, and owned-code input. Fixture, smoke, document,
collection, index, resolution, and handoff identities use separate typed
namespaces. A new code or policy identity may reuse a sealed upstream artifact
only when that artifact's owning contract and checksums permit it.

## Extraction representation

The current extraction keeps the following boundaries explicit:

- raw Docling conversion evidence is preserved and is not the canonical table
  representation;
- the clean table pipeline owns canonical table content and table-family
  relationships;
- visible TOC rows and document-index content remain navigation evidence and do
  not become body-section starts or ordinary data-table targets;
- deterministic hierarchy correction is a replaceable evidence layer that
  preserves raw labels, levels, geometry, and provenance; and
- document-local and cross-document reference linking are separate stages with
  their own identity and resolution records.

The stable persisted contracts are the [canonical extraction
specification](specs/canonical_extraction_v1.md), [semantic structure
specification](specs/semantic_structure_v2.md), [cross-reference
specification](specs/cross_references_v3.md), [document-linking
specification](specs/document_linking_v1.md), and [restartable corpus
specification](specs/restartable_corpus_extraction_v1_1.md). The chunked
conversion specification defines the independent range-evidence boundary used
by the current production path.

Task 05's curator-only response inventory uses the
[response inventory v1 specification](specs/response_inventory_v1.md). Its
source units, relationship graph, exact reference outcomes, review, and final
publication remain separate from the Task 03 model corpus. The maintained
`er-responses` CLI validates explicit run specs and uses separate acceptance
transitions; the [Task 05 umbrella](../tasks/sprint2/05_build_curator_only_response_inventory.md)
routes the completed stages and their detailed execution contracts.

`response_lists` owns the bounded explicit full-ID list grammar and shared-prefix
evidence checks. `saved_evidence.replay_saved_source` can replay the qualified
744-page source from accepted observations and verified render evidence without
opening the PDF. It writes fresh producer receipts and requires explicit renewal
of unchanged review evidence. A source/graph replacement may reuse the reference
baseline only after proving that all historical source semantics remain and the
only additions are intra-volume mentions and their spans. The reference replay
then checks every report outcome against the accepted predecessor, allowing only
the verified source/graph provenance changes.

Task 05H composes those accepted source and graph records with all accepted 05G
reference outcomes. The `response_inventory.release_*` modules keep input
verification, review, storage, supervision, and publication as separate readable
owners. Preparation, review, finalization, publication, and acceptance are
separately authorized supervised stages. Finalization seals review decisions,
limitations, component references, and the Task 07/08 handoff; publication copies
that sealed container without changing its identity. Acceptance writes the
designation pointer only after successful terminal supervision and revalidation.
The [replacement result](specs/task07a1_final_result.json) records current release
bindings; the [original result](specs/task05h_final_result.json) remains historical.

An explicitly bound supersession preserves the previous immutable acceptance
record and changes only the current designation pointer after the replacement
passes supervised acceptance. The request pins the exact previous pointer bytes;
a different intervening designation fails closed.

`pilot_screening` is a narrow downstream adapter: it verifies a saved 07A sample
and prepares one unrated Label Studio task with source IDs and readable text.
It neither discovers response links nor imports tasks or assigns ratings. The
[form README](../configs/label_studio/README.md) owns the isolated review setup;
Task 07A owns the completed export and migration boundary.

`pilot_questions` is the comment-only Task 07B adapter. It verifies an explicit
one-case drafting packet and proposal, prepares a concerns prediction without
approval, and normalizes saved reviews against trusted prepared task data.
Only explicit approved, nonempty numbered lists can advance; original text,
proposal, and source bindings remain separate from curator edits. Import/API
execution stays in the external trial record.

`pilot_claims` is the Task 07C adapter. It verifies sealed response packets and
separate proposals, renders full source context with a claims prediction, and
normalizes saved reviews against trusted task data. Edited claims bind current
source passages; immutable proposal quotes remain drafting provenance. Explicit
approved records alone can advance, with content/export-bound IDs and complete
proposal lineage rather than inferred per-claim split/merge ancestry.

`pilot_claim_relevance` is the separate Task 07C.1 combined review adapter. It binds
combined claim/relevance proposals to the sealed source and predecessor review,
keeps stable claim identities independent of edited content, and validates
supporting paths plus explicit removals. Removal clicks on addition slots with
no proposed claim or current text are recorded as `unused_slot_removals`,
separate from substantive claim deletions; native fields remain preserved.
`pilot_relevance_form` generates native
fixed-slot controls; capacity changes preserve saved annotations through a separate
project migration. The [combined review contract](specs/claim_relevance_review_v1.md)
owns uncertainty and evidence-queue boundaries. The combined UI is approved;
case acceptance still requires an explicit, validated human review.

`pilot_evidence` is the Task 07D evidence-review adapter. It checks immutable
reviewed claim membership and exact canonical record snapshots/text spans,
prepares one native task per claim with only its mapped evidence, and normalizes
explicit human support judgments against trusted task data. The original
case-level adapter remains available for preserved prototype records. A saved
claim does not assert case completion. Discovery and local
Label Studio operations remain in the external run. Source eligibility comes
from the pinned accepted handoffs, not from a matching quote. The
[evidence-review contract](specs/evidence_review_v1.md) owns support, partial
coverage, gaps and provenance; relevance never establishes evidence support.
Current review shows the exact claim and reviewed question above separate
reviewer-note and source-excerpt panes. Versioned forms preserve historical
normalization while citation metadata distinguish supplied, corrected and
omitted references. Discovery may search beyond response citations. `pilot_citation_units` verifies
current packet-v2 heading boundaries and complete section/table membership
against parsed sources; exact anchors remain below semantic citation identities.

`pilot_context_repair` refreshes a fixed sample using directed response closure;
cycles are deduplicated and other comments cannot enter the context.
`pilot_label_migration` verifies protected exports, joins annotations by stable
comment ID, reconciles missing-only imports, and compares every completed result.
Original annotation provenance stays separate from the replacement inventory and
new Label Studio IDs/timestamps. API operations remain in the external execution
record rather than in the pure transformation helpers.

Tasks 07 and 08 resolve the Task 05H acceptance pointer once, then pin the
inventory identity, completion seal, and exact component references for the
whole downstream run. They retain the accepted reference, F1-substitution,
sampled-review, and text-only figure limitations; see the
[Task 05H summary](specs/task05h_final_summary.md). A link or accepted inventory
membership does not establish case eligibility or evidence sufficiency.

`group_ranking` is the Task 08A adapter. It checks accepted grouping and inventory
bindings, reuses directed response closure, retains original text and flags, and
seals an advisory order. Preparation, proposal validation and saved-handoff
validation are separate commands; no human decisions or Label Studio projects
are created. The [ranking contract](specs/task08a_ranking_v1.md) owns the shared
format and first-use qualification. Historical v1 code and schemas remain
unchanged for its sealed validation path. `group_ranking_v2` owns the simplified
order-only proposal and explicit deterministic bypass for at most three candidates.
Its source adapter retains accepted general-response membership provenance and
complete linked closure; separately bound page context preserves omitted footnotes.
08B uses qualified version dispatch through `task08b.intake.v2`; no dummy v1
rationale fields are permitted. `group_selection_batch` handles create-only
native project setup, exact input checks and guarded register updates. The
[intake specification](specs/task08b_intake_v2.md) owns historical compatibility
and source-page display; human gates remain in the selection process.

`group_selection` is the Task 08B adapter: it revalidates the sealed ranking,
prepares a blank ordered queue with exact source display, and keeps original
comments separate from response and advisory context. `group_selection_export`
validates native saved decisions against trusted rebuilt tasks, including all
untouched candidates, the historical selection ceiling and export-bound chat completion.
`group_selection_closeout` separately implements the explicit 2026-10-01
all-selected closeout: no cap, native skips retained without blocking completion,
and full inventory/source checks. Historical replay and project forms remain unchanged.
Selection is the sole 08B label gate; evidence-based eligibility remains later. The
shared [selection contract](specs/task08b_selection_v2.md) owns the form, reasons and
qualification boundary. API operations stay in each external execution record.

## Review boundary

Human review consumes published evidence through `human_review_support`.
Selections, requested renders, findings, usability dispositions, and release
records do not modify machine records. Task 04A owns the original usability
registry; Task 06H owns the accepted replacement review. The original Task 04D
linking handoff remains distinct from the Task 06H repaired handoff. Their
exact correspondence and limits live in the [04D](../tasks/sprint2/04d_relink_frozen_extraction.md)
and [06H](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
outcomes.

Task 06F's maintained figure-alias owner is
`document_records.document_references.figure_aliases`. Its
[caption policy](specs/figure_caption_alias_v1.md) derives exact marker aliases
from a figure's own canonical image/caption attachments. Collection indexing
consumes the sealed aliases. Structural figure identity and text-only evidence
usability remain separate decisions.

The exact local target-resolution engine is shared beneath both callers and is
owned by `document_records.document_references`. It owns exact typed alias
matching, target-ID deduplication, optional destination-page intersection,
deterministic ordering, and neutral candidate-cardinality outcomes. The machine
linker and navigation overlay remain separate adapters for source parsing,
caller-specific policy around the shared query, and schema-specific
publication. `navigation_overlay` may depend on this core; the core may not
depend on human-review or overlay packages.

The reusable production stage is specified in
[`specs/document_linking_v1.md`](specs/document_linking_v1.md). A single
package-backed `er-commons documents relink` interface accepts a sealed
canonical document, versioned linking policy, and optional sealed reviewed
navigation. It publishes the complete replacement linked-document product,
then delegates downstream-only document publication to the maintained replay
publisher. Collections continue through the existing assembly interface under
a fresh scope. Corpus-specific audits may compare this path but may not own a
resolver, publisher, or identity recipe.

Task 04D's validated handoff is the original linking-dependent replacement.
Task 06H's accepted repaired handoff supersedes it for later reference consumers;
Task 05G pinned that replacement. Neither handoff is assembled by composing
Task 03J machine links with the Task 04C overlay. Task 03J continues to own the
immutable extraction inputs. Exact identities and completion evidence are in
the [Task 04D outcome](../tasks/sprint2/04d_relink_frozen_extraction.md) and
[Task 06H outcome](../tasks/sprint2/06h_review_and_accept_replacement_handoff.md).

Record-building and caller adaptation live in `relinking.py`; run-spec
resolution, identity, schema enforcement, and completion-last publication live
in `relink_publication.py`. The [document-linking specification](specs/document_linking_v1.md)
owns their contract. Collection replay uses sealed membership and compact
completion evidence without rehashing preserved source or document payloads;
the [06G outcome](../tasks/sprint2/06g_replay_repaired_document_and_collection_stages.md)
owns its completed execution details.

## Configuration and paths

### Task 06 reuse boundary

The [Task 06B verification specification](specs/task06b_verification_boundaries_v1.md)
separates historical seal consumption from current writer recipe validation.
Routine reuse checks exact compact seals, membership, and inventories; a deep
payload-byte audit is a separate operation. Unchanged sources keep accepted
manifests and identities while changed descendants bind current behavior and
upstream seals. The [maintained command map](pipeline_commands.md) and
[executed owner inventory](specs/task06b_gate2_executed_inventory.md) name current
interfaces and migration evidence.

### Repeated chapter-heading projection

Task 06D places repeated divider/opening repair after accepted hierarchy
projection and before alias grouping. `repeated_heading_policy` owns typed
classification, `repeated_heading_projection` owns topology reconstruction and
accounting, and `repeated_headings` is a small public facade. The classifier requires
exact chapter/title agreement, adjacent same-level sibling topology,
nonoverlapping ownership/extents whose union ends before a frozen compatible
following chapter boundary, and accepted TOC correspondence. Ambiguous groups
remain unprojected. Canonical-v1 bypasses and does not import this v2-only
repair path.

For an eligible pair, the divider section becomes the logical chapter anchor;
both physical heading blocks and all content remain in source order, while the
opening section's children and direct records move to the anchor. Alias
construction redirects both heading spellings and exact TOC aliases to that
single target. A fresh candidate identity binds the policy, decision schema,
closed qualification packet, and owned code. Task 06G materialized the output
and wrote adjacent many-to-one target correspondence; resolvers and collection
indexing consume the aliases and never rediscover duplicates.

### Qualified source acquisition

`source_release` owns the [Task 06C qualification boundary](specs/task06c_source_qualification_v1.md).
The selected Final F1 is a distinct physical source for the logical Draft F1
slot, with its Final edition and reviewed substitution provenance. Acquisition,
retained-source qualification, conversion, and downstream use have separate
receipts and gates; a failed acquisition remains preserved evidence. Maintained
consumers validate the exact exception before using the source without another
PDF hash. The [Task 06C outcome](../tasks/sprint2/06c_qualify_and_process_replacement_f1.md)
owns the source and receipt details.

`document_publication/background_execution.py` supervises an explicit offline
command with persistent external logs and finite process, time, output, and swap
limits. It preserves failed attempts and does not schedule automatic follow-ups.

### Current configuration

Portable source and workflow configurations stay in Git. The external data root
is loaded only from the required, untracked `ER_COMMONS_DATA_ROOT` setting.
Committed configurations use relative paths or paths rooted by that setting;
they do not depend on a developer's absolute filesystem layout.

Task 03J's exact v4 configuration set is documented in
[`configs/README.md`](../configs/README.md). The smoke and Task 03G.2
configurations remain separate historical or diagnostic inputs and must not be
mixed with current native-v2 production contracts.

## Historical implementation record

The completed Task 03A through Task 03J records preserve implementation detail,
negative experiments, identities, and validation evidence. They are the source
of truth for historical reconstruction, not current entry-point instructions.
Use the active task and the versioned specifications for new work; do not copy
old task-era package names, commands, or artifact roots into a current contract.

### Task 07D repeatable discovery and citation assembly

`pilot_evidence_search` builds a source-bound SQLite FTS5 cache and produces
ordered BM25 receipts from fixed query plans. The index is a derived external
artifact, not the source of truth or the frozen evaluation retriever. Case-level
agent assignments use the [saved per-claim prompt](prompts/task07d_claim_citation_search_v1.md)
and [search protocol](specs/task07d_search_protocol_v1.md). Current execution uses
an FTS5-enabled system Python; the repository's uv SQLite lacks that extension.
The package raises a capability error rather than substituting another search.

`pilot_citation_units` validates ordinary and audited table units.
`pilot_citation_boundary_overrides` owns the narrowly source-bound Section 8.5.2
overlay; `pilot_citation_visual_sections` preserves text plus explicit figure
locations without inferring visual evidence. All outputs bind unchanged canonical
records. Packet preparation and human-review normalization remain in
`pilot_evidence`; discovery proposals never become human support labels.


`pilot_case_citations` owns pure Task07D case-level citation aggregation after
source/review validation. It separates unchanged claims and deduplicated support/
context citations from lossless review audit, rejects conflicting source identities
and incomplete judgments, and never derives support from claim relevance or overall
outcomes. The sealed Task07D export records its bounded orchestration script and
explicit user dispositions; it does not mutate Label Studio or upstream artifacts.


Task07D maintainability boundaries and replay are documented in the
[maintainer guide](task07d_maintainer_guide.md). `pilot_evidence_forms` owns native
layout versions separately from task/review logic; `pilot_citation_records` owns
shared source-record operations while unit-specific policy remains in the citation
modules. `pilot_case_export` owns verified file I/O and publication around the pure
aggregator, replacing machine-specific one-off orchestration as the maintained
entrypoint. `ReviewValidationError` exposes rejected parsed judgments for audit;
only a manifest-bound explicit disposition can accept its exact warning signature.

## Task 08C comment-only wording

The [combined pass](specs/task08c_combined_chat_review_v1.md) uses
`group_wording_combined` for v3 closeout verification and an ordered 57-comment
safe packet, and `group_wording_combined_chat` for sequential versioned decisions.
Historical v1 group validators and artifacts retain their original semantics.
Proposals are generated only when their question becomes active.


`group_wording_input` owns deterministic extraction and restricted provenance
separation. `group_wording_chat` owns versioned chat-event replay and exact
approved-text export under [task08c.chat_review.v1](specs/task08c_chat_review_v1.md).
Use plain JSON events and existing schema/hash helpers; feedback and displayed
proposals remain distinct from explicit human decisions. No response context enters
drafting/review inputs. `group_wording` and `group_wording_export` preserve the
historical qualified Label Studio path; it is no longer the required 08C workflow.

`group_claims_input` verifies frozen 08C questions and independently reconciles
complete response closure. `group_claims_inventory` checks two-pass accounting;
`group_claims` builds the shared native claim form and trusted no-clobber review
packet. `group_claims_export` validates exact saved claims and current direct
support targets; `group_claims_workflow` binds publication to imported task IDs
and the current project form. Semantic approval remains human-only. See the
[08D interface](specs/task08d_claim_review_v2.md) for holds and relationship rules.

Claim-review v2 removes editable source-ID controls; the exporter derives each
existing claim's exact anchors from trusted proposal data. Unbound additions
remain held for source-bound re-review. The v1 normalizer remains available for
preserved exports; mixed-version queues are rejected.

## Task 08F preparation interfaces

`group_answer_intake` verifies the consolidated 08E seal and dependency closure,
resolves current scoped approvals, and validates canonical source units before
building isolated source-only inputs. `group_answer_records` checks structured
points, citation membership, exact excerpt locators and qualification attachments;
its readable display is the same answer, not a second prose artifact.
`group_answer_batch` records ephemeral Astra calls and immutable attempts, resumes
without overwriting successful versions, and publishes completion last after all
cases have proposals or explicit blockers. Mechanical checks and advisory model
notes never establish human approval. The [08F contract](../tasks/sprint2/08f_review_group_answers.md)
owns the separate later human review boundary.

`pilot_citation_wsa_boundary` provides a source-specific C022 Appendix P Section 8
audit. It retains the canonical section identity and every member while recognizing
three internal statutory callouts; exact source hashes and rendered-page evidence
constrain the exception. It grants no human evidence or answer approval.

## Task 08E evidence interfaces

For the combined pass, `group_evidence_batch` verifies the full sealed 08D intake;
`group_evidence_research` validates independent question packets and five-track
plans; `group_evidence_discovery` saves query intent before maintained retrieval
and wraps canonical section assembly. `group_evidence_chat` records exact displays,
version-bound decisions and restart checkpoints; preparation exports stay blank.
`group_evidence_publication` requires raw-receipt fidelity, accepted source bindings,
complete table families and independent coverage review before sealing all cases.
`group_evidence_extension` binds explicit research-only reopening, preserves
historical claim decisions, and composes separately sealed batches in upstream
order without rewriting the original preparation. Combined verification checks
both child seals and exact case-row fidelity.
These modules reuse the maintained source and journal boundaries below. The
[current research contract](specs/task08e_batch_research_v1.md) supersedes historical
claim-only and native-project workflows for this pass.

`group_evidence` adds qualification-only version bindings, summary editing and
an explicit case eligibility form around maintained `pilot_evidence` native
controls and normalization. `group_evidence_fixtures` writes invented canonical
sections/tables in a fresh external directory. It cannot load a live handoff or
publish advancing claims. Source-unit validation and citation aggregation remain
owned by the maintained 07D modules; no historical disposition or case acceptance
is a default. The [08E specification](specs/task08e_evidence_review_v1.md) separates
qualified shared behavior from prospective live-loader gates. An accepted 08D
replacement and fresh binding verification are required before live activation.

The [investigation revision](specs/task08e_investigation_v1.md) adds
`group_evidence_live`: it replays the accepted investigation-only 08D export,
preserves approved support chains and unresolved scope, and binds native evidence
and later eligibility exports to exact tasks, forms and reviewers. All downstream
advancement lists remain empty. `group_evidence_units` handles freshly audited
canonical table families and parsed narrative boundaries, including notes split
across sections. It checks unchanged record snapshots, extraction and page
identities, every continuation member, render bindings and complete narrative
coverage. Ordinary and visual units continue using maintained 07D helpers.

Live native storage `task08e.packet_reference.v1` carries checksum-bound external
packet references. The live exporter verifies compact native identities before
hydrating temporary full packets for maintained normalization, retaining both
identities. This avoids duplicating large canonical packets in browser state while
keeping complete visible source units. Caches are call-local and do not bypass
future file checks.

The [citation-first revision](specs/task08e_citation_first_v1.md) adds
`group_evidence_citation_review` over the same exact source packets. It transposes
claim proposals into citation tasks with independent approved-claim relationships,
including optional additional links. Its exporter retains unreviewed pairs,
source limits and human native records without inventing aggregate claim outcomes.
It uses the shared source renderer and compact transport. Citation exports have
their own version and must not be coerced into legacy claim-review records;
future eligibility preparation must bind this exact saved export directly.

The [combined 08D chat path](specs/task08d_combined_chat_review_v1.md) adds
`group_claims_combined_input` for verified frozen-question/source intake,
`group_claims_batch` for deterministic assembly and sealed preparation,
`group_claims_chat` for exact cards and append-only decisions, and
`group_claims_chat_cli` for file-backed resumption. Two-pass model inventories
remain independent of human decisions. Revisions invalidate dependent approvals;
the exporter requires a separate version-bound case disposition and preserves
unanswered scope. Historical native interfaces retain their existing semantics.

## Task 09A synthetic authoring

`synthetic_intake` verifies the frozen release and projects only development
questions, current substantive answers and allowed source packets. Exact approved
answers and historical metadata stay in separate restricted controls.
`synthetic_records` owns the strict output contract, literal source checks and
reconstructable edits. These checks establish artifact validity, not correctness
of proposed scores. `synthetic_batch` owns isolated Astra calls and immutable,
bounded attempt recovery; `synthetic_publication` owns separate answer,
expectation/edit records, coverage, independent-review bindings and deterministic
final-check reservations. No harness, judge or target runner is introduced.

Later judge packet builders must project the answer and permitted evidence;
they must not forward complete synthetic records, whose IDs and provenance can
reveal perturbation categories. Consistently anonymize category-bearing point IDs
and qualification attachment links as well as outer variant IDs. Ambiguous expectations and duplicate variants
are retained but excluded from comparison and final-check reservation pools.

## Task 09B qualification boundary

`judge_qualification_packets` makes a bounded, checksum-bound development-only
projection from the sealed 09A handoff. It separates model payloads from selection
provenance and expectations; grounding receives only cited sources, while adequacy
also receives the reference and reviewed sources. This temporary qualification
projection is not the general 09C packet subsystem.

The prototype `judge_qualification` inference runner was retired by 09F.2.
Its sealed results and source snapshot retain historical qualification evidence.
Current local diagnostics use the native Inspect Ollama profiles described in the
[production judge guide](judge_maintainer_guide.md). The offline packet projection
remains because 09C still consumes it; it is not a judge runtime.

## Task 09C judge packet boundary

`judge_packets` projects complete sealed source units into strict, separate
model payloads. Raw substantive types are checked before IDs are anonymized,
and known-source assembly errors retain their source locator. It reuses 09B's
answer/locator projection, preserves full source
text and table structure, and keeps raw citation/point mappings and input hashes
outside model inputs. Unknown candidate citations get explicit unresolved entries;
missing known-source content raises an infrastructure/input error. It performs
no retrieval, citation repair, semantic scoring or source summarization.

`judge_packet_publication` verifies frozen development membership, reservation,
corpus/source identity and selected answer/reference bindings before publishing
explicitly selected variants or controls. It uses metadata-first 09B JSONL routing
to avoid decoding reserved rows. `judge_packet_requests` emits plain Inspect
samples, checks payload integrity, and reuses 09B's native Ollama request assembly.
Complete requests remain
blocked as `context_unverified` without an exact model-bound token counter;
`context_overflow` blocks dispatch at 49,152 input/output tokens. Request preflight
uses the explicit supported output reserve (1,500 or the authorized 3,000-token
experiment); frozen packet diagnostics retain their original 1,500-token default. Future judge tasks own their prompts, counters and scoring.
The old qualification runner is retired. See [09C](../tasks/sprint2/09c_build_judge_evidence_packets.md)
for usage, validation and limits.

## Task 09D automatic metric boundary

`automatic_metric_inputs` resolves verified occurrence locators to the existing
source/extraction/kind/unit identity, preserves malformed/invalid attempts, and
checks explicit receipt mappings and anchor completeness. `automatic_metrics`
owns pure set arithmetic and aggregation. `automatic_metric_inspect` provides
saved-answer solvers and two thin scorers; Inspect owns execution, sample records,
logs and metric reporting. It has no inference path or separate evaluation runner.

Prepared inputs are restricted scoring metadata, never judge payloads. The entrypoint
accepts an explicit prepared sample array; callers remain responsible for verified
development selection through existing release routing. It does not discover or
load benchmark partitions. Task 10 supplies qualified search-record/fragment maps
and delivery receipts. See the [metric and receipt contract](specs/task09d_automatic_metrics_v1.md)
for nullable status, exact counts and primary versus diagnostic retrieval.

## Production A/G/S/C judge boundary

The [production judge guide](judge_maintainer_guide.md) owns current interfaces.
`judge_inspect` supplies one native Inspect provider/configuration layer for
OpenAI, Anthropic, Fireworks and Ollama. `no_answer`, `point_grounding` and
`adequacy_binary` own separate prompts, projections and strict result parsers;
their Inspect adapters supply independent samples and scorers. No judge receives
another judge's predictions. Development loaders retain explicit frozen data seals.

`configs/judges_selected_v1.json` and `configs/judge_models_v1.json` are the current
selection and provider contracts. Exact selected prompt/schema identities are
validated before selected dispatch. Inspect owns transport, generation, retries,
concurrency and logs. Invalid output remains a non-decision. Task 12 owns routing
and combined reporting; 09G owns challenge/freeze.

09F.2 retired the older staged/whole-answer grounding and adequacy runners,
hand-written cloud transports and experiment dispatch. Their source is recoverable
from the external checksummed cleanup archive, and completed evidence stays sealed.
The local `ollama_request` and `ollama_token_counter` utilities retain offline
historical request rendering and exact token preflight without an inference path;
that preflight does not qualify the new native Inspect Ollama request.

## Fresh synthetic point expectations

`synthetic_regeneration` reconstructs only prior development slots from sealed
reservation metadata and original approved source packets. It does not consume
old synthetic answers or walk reserved/test payloads. `synthetic_stage_expectations`
checks point-ID coverage, literal assertion/source spans, point-owned citation
links and deterministic point/conclusion score consistency. The versioned
`task09a2` schema and prompt keep labels outside answer content.

`synthetic_batch` freezes the selected schema and code before source-only authoring.
`synthetic_publication` preserves the external prior reservation and emits a
predecessor-slot map instead of drawing a new split. Its comparison eligibility
includes unresolved, duplicate and independent-review exclusions. Point labels
remain author proposals, not evaluator predictions or human calibration. The
[09A.2 contract](../tasks/sprint2/09a2_regenerate_point_expectations.md) owns scope
and the fresh result; existing judge pipelines are not invoked or modified.

For bounded point-prompt comparisons, `grounding_run --pipeline points` reuses the
staged Inspect adapter while skipping abstention/conclusion calls. It retains
zero-point samples, emits null answer scores, and aggregates validated point flags
without answer-level accuracy. The [v2 comparison contract](specs/task09e_point_scope_v2.md)
owns the frozen inputs and source-review requirements.

The combined 09A.3 panel adapter (`grounding_dataset_panel`) verifies the new
publication, eligibility and record-specific origins independently of the preserved
four-answer panel loader. `grounding_run --dataset-version 09a3` selects it;
`dev6_additions` loads only the additional three cases. An explicit
`freeze_dataset_panel(..., full_dev=True)` publication and `full_dev` loader
selection support the user-authorized full development comparison; the default
stays at six cases and exact sealed development membership is required. Restricted stage expectations
are canonical-ID-mapped metadata, never model input. Inspect reports stage-level
agreement and coverage separately from final scores; missing/invalid predictions
are not false labels. The [combined rerun contract](specs/task09e_09a3_small_v1.md)
owns authorized counts and experiment bounds.


Task 09E.1 retains historical strict judge behavior while extracting the shared
legacy stage executor into `grounding_stage_runtime`. New `grounding_comparison_*`
modules separately own sealed Dev3 loading, semantic/quotation validation, provider
wire mappings, exact preflight and budgets, Inspect execution, offline audits and
post-run proposed-label analysis. Binary-only observations cross stage boundaries.
The live CLI is create-only; incomplete attempts never trigger automatic replay.
See the [comparison contract](specs/task09e1_comparison_v1.md) and
[cloud handoff](specs/task09e1_cloud_handoff.md) for qualification gates and commands.
Clef execution and its uncounted local exception are retired. Historical receipts
remain unchanged. The maintained three-model profile selects GLM with Luna/Haiku
alternatives, while legacy Ollama paths remain for local integration checks.
See the [maintainer guide](grounding_judge_guide.md) and
[09E.2 cleanup](../tasks/sprint2/09e2_cleanup_grounding_judges.md).

Pure sample/metrics contracts live in `grounding_records` and `grounding_metrics`;
source-text traversal and local transport policy have separate owners. Cloud
prompts are frozen independently of legacy prompt wording. Provider configuration
is validated before rendering. The shared cloud budget stops further reservations
on transport uncertainty, cancellation, storage/receipt failures and native
identity/usage mismatch, including requests already waiting on token counting.
Explicitly pinned development panels are checked against original source/answer
projections without loading labels; post-run analysis alone consumes expectations.
Coverage-aware metrics separate original claims, reviews, conclusions and scores.

Bounded generation experiments may supply a nonempty per-stage prompt override;
its actual rendered request and configuration identity are preserved in receipts.
Default prompts remain unchanged. OpenAI sampling overrides are explicitly
validated against the selected reasoning mode, and cache controls are rendered
only when configured for that model. Exact counting omits generation-only
sampling fields while retaining the full generation request's hash binding.
See the [settings/prompt contract](specs/task09e1_settings_prompts_models_v1.md).

The comparison evaluator accepts validated stage-specific prompt mappings, so
fresh point decisions flow into conclusions with independently selected review
instructions. Luna can opt into an evidence-prefix cache breakpoint: two text
blocks concatenate to the original JSON exactly, while implicit caching still
covers exact duplicates. The exact counter retains nested breakpoint markers.
Schema differences and short prefixes can still prevent reuse; neither provider
caching nor prompt overrides reuse saved judgments. See the
[bounded pipeline outcome](specs/task09e1_luna_cache_pipeline_result.md).

The bounded [frozen-claims conclusion experiment](specs/task09e1_luna_conclusion_blind_v1.md)
adds explicit Luna-only stage options. Blind review projects prior observations
to IDs before native rendering and counting; original observations remain offline
for validation and the unchanged disagreement gate. Conclusion-only mode has its
own genuine output schema without point reviews and a separate aggregator using
frozen point decisions directly. Default requests and scoring are unchanged;
the experimental paths do not invent reviews or silently suppress disagreements.

## Evidence-only target input preparation

`evidence_only_sources` verifies the frozen release and canonical source files;
`evidence_only` projects strict target payloads, separate evaluator mappings and
split datasets, then publishes and replays a sealed file set. The default loader
reads development only. It performs no model calls or retrieval. Whole-unit
boundaries are inherited from approved evidence; recorded anchor text and tables
are replayed against bound canonical files. See the [Task 10 format](specs/task10_evidence_only_v1.md)
for current qualification status and the Task 11 delivery/context boundary.


## Luna evidence-only generation

`target_generation` owns the bounded Task 11B initial-three smoke. It verifies the
11A development bindings, renders only the Task 10 payload with a generic pinned
prompt/schema, and uses native Inspect/OpenAI generation. A narrow SDK HTTP hook
counts and records the actual request before dispatch; it does not reimplement
transport. Target settings are separate from frozen judge settings. Create-only
attempt receipts preserve raw responses, valid candidates and explicit failures;
uncertain attempts are never automatically resubmitted. See the
[11B contract](../tasks/sprint2/11b_build_luna_generation.md) for limits and command.
Whole-answer evaluation remains 11C work.
