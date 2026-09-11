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

Task 05's separate curator-only response inventory uses the
[response inventory v1 specification](specs/response_inventory_v1.md). Its
source records, normalized relationship edges, sparse corrections, and derived
review indexes remain separate. The contract is intentionally MVP-sized: one
record-schema union and one semantic validator, not a new workflow framework.
The isolated `er-responses validate-spec` command is source-free.
`er-responses build --run-spec <path>` is curator-only and may access only the
exact range or ranges accepted by its strict Task 05C or 05D run specification.
Task 05D declares one `1-744` range, compares and renders every page, freezes a
deterministic review population, and requires a later receipt-reuse invocation
before terminal completion. Both stages write replaceable range receipts and a
nonterminal visual-review packet before terminal publication.
The full-source workflow exposes named preflight, source-record, review, and
publication phases. Its all-page Poppler qualification writes and validates one
atomic page checkpoint at a time, allowing an interrupted pass to resume
without repeating accepted page evidence. Cache rejection reports bounded
mismatched receipt fields before source access, and terminal resource reporting
combines the source pass with the later source-free closure. Candidate
acceptance uses the same public read-only validator available to maintainers;
the writing transition remains separately authorized.
For Task 05D, an exact source-independent same-page comment/response pairing may
promote a response-style comment marker without relaxing the ordinary marker
policy. A numbered source-authored missing response heading is retained as the
terminal `source_response_heading_absent` diagnostic; no response record is
invented. The run specification may allow that diagnostic class, and reviewed
zero, one, or multiple occurrences determine `complete` versus
`complete_with_warnings` from the records.
`er-responses accept` is a separate explicit transition for an already terminal
05D candidate; it writes a compact adjacent acceptance pointer outside the
candidate's managed-file closure and does not change candidate identity.
For Task 05E, `er-responses finalize-05e` verifies one closed source-free review
receipt, binds a passing file-checksummed human-maintainability report, and
atomically wraps the unchanged graph in managed-inventory and completion
records. It does not rerun matching or copy accepted source records. Candidate
acceptance uses the separate `er-responses accept-05e` transition, which
revalidates the terminal candidate and writes a compact adjacent pointer without
changing the candidate's managed closure.

## Review boundary

Human review consumes published Task 03 evidence through a separate
`human_review_support` package. Review selections, requested renders, findings,
usability dispositions, and release-freeze records do not modify machine
records. Task 04's first-pass review is historical. Task 04A allocates a new
review identity bound to Task 03J and owns the final usability registry and
initial release decision. Task 04B is a conditional fresh replay after an
approved Task 04A TOC/navigation stop handoff. When Task 03J is accepted without
regeneration, Task 04C owns the separate derived consumer that combines the
immutable machine candidate with the accepted human TOC layer for semantic
navigation, aliases, and links.

Task 04D owns the fresh replacement-linking boundary. It reuses Task 03J's
sealed extraction through target-alias construction plus Task 04C's accepted
navigation semantics and TOC text, changes only document linking behavior, and
replays linked-document and collection descendants under fresh identities.
Task 04D may not rerun or modify parsing, table reconstruction, hierarchy,
section mapping, printed-page resolution, or existing canonical target-alias
generation. Its only alias extension is the accepted R6/R6a body-derived table
caption evidence; source navigation text and mentions may query but never
generate aliases.

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

Task 04D's validated handoff is the designated downstream replacement.
Linking-dependent consumers pin that handoff; they do not compose Task 03J
machine links with the Task 04C overlay. Task 03J continues to own the
immutable extraction inputs reused by this replacement. The exact identity and
completion evidence are retained in the [Task 04D outcome](../tasks/sprint2/04d_relink_frozen_extraction.md).

Gate C implements the record builder and caller adapters in `relinking.py` and
keeps run-spec resolution, identity derivation, schema enforcement, and
completion-last publication in `relink_publication.py`. This split preserves a
single public command while keeping matching behavior independent from artifact
transaction mechanics.

Collection replay prepares and validates the sealed run once, then executes its
35 sources sequentially with visible progress. Base-lineage membership is
proved from sealed handoff, accounting, inventory-reference, and completion
metadata; the preflight does not hash PDF or preserved document payloads.

## Configuration and paths

### Task 06 reuse boundary

[Task 06B Gate 1](../tasks/sprint2/06b_refactor_pipeline_identity_and_reuse.md)
implements explicit historical seal consumption separately from current writer
recipe validation. Its [verification specification](specs/task06b_verification_boundaries_v1.md)
routes maintained readers and finite behavior inventories. Prepared relink and
publication state shares one verification budget, loads each original manifest
and reviewed-navigation bundle once, and checks per-source compatibility.
Routine accepted-input checks use compact seals and metadata; explicit deep
audits retain byte-verification semantics. Unchanged inherited support digests
are propagated into fresh publications without rehashing their payloads.

Document and collection v3 specifications express original per-source releases
and replacement logical/physical membership. Unchanged sources keep their
accepted manifests and identities. New descendants bind current behavior and
upstream seals; metadata qualification does not claim fresh payload equality.
Gate 2 migrated maintained wrappers to explicit requests and responsibility owners;
see the [command map](pipeline_commands.md) and
[executed inventory](specs/task06b_gate2_executed_inventory.md). Generation and input
preparation live in `document_publication/config_generation` and `input_preparation`;
review support lives in `human_review_support/extraction_review`; diagnostics live
in `document_performance/conversion_scaling` and `conversion_compatibility_audit`.
The retired pilot island has no maintained callers. Historical recipes and schema
literals remain unchanged. Later structural, F1 and review-policy work remains with
06C–06H.

### Qualified source acquisition

`source_release` owns the [Task 06C qualification boundary](specs/task06c_source_qualification_v1.md).
A strict portable request binds the selected URL, semantic policy, finite limits
and explicit substitute provenance. The separate acquisition path supervises
streaming and bounded existing pypdf extraction; it seals observed evidence only
after qualification. Compact reuse checks the owned implementation/tool/request
bindings and exact receipt membership without opening the source PDF. Historical
source-release writers and accepted per-source manifests remain unchanged.

The selected Final F1 is a distinct physical source for the logical Draft F1
slot, with explicit Final edition and the bounded exception in Decision 001.
Its qualification receipt is not a legacy source manifest or a conversion
completion. A separately authorized conversion gate must prepare the measured
manifest/processing adapter and model bindings before executing maintained stages.
The 06B stage and range readers continue to own downstream reuse.

The separately reviewed retained-source boundary uses `local_qualification.py`
to assess exact exception and semantic evidence without opening PDFs. A fresh
`er_commons.recovery.retained_source_completion.v1` receipt seals a
`qualified_with_reviewed_exceptions` record referencing the unchanged source.
Its original failed acquisition is retained. A consumer must explicitly support
this schema, policy/implementation provenance and exception limitations; it is
not interchangeable with the strict acquisition receipt.
`source_release/retained_processing.py` validates that pinned receipt, evaluator
implementation and unchanged source metadata to publish a reference-only
processing manifest. Its `qualified_substitute` role requires exact F1 provenance
and remains distinct from `model_corpus`. Both maintained source resolvers
validate the exception before allowing processing without a new source hash.
The clean-table request also carries the explicit producer manifest path; it
verifies the same sealed source and qualified metadata. Historical requests
without that field retain their original release-path resolution.

`document_publication/background_execution.py` supervises one explicit offline
command with persistent external logs and sampled process-tree, wall-time,
output and swap ceilings. It preserves failed attempts, handles descendants
across process sessions, and does not schedule automatic assistant follow-ups.

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
