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

Task 05H composes those accepted source and graph records with all accepted 05G
reference outcomes. The `response_inventory.release_*` modules keep input
verification, review, storage, supervision, and publication as separate readable
owners. Preparation, review, finalization, publication, and acceptance are
separately authorized supervised stages. Finalization seals review decisions,
limitations, component references, and the Task 07/08 handoff; publication copies
that sealed container without changing its identity. Acceptance writes the
designation pointer only after successful terminal supervision and revalidation.
The [final result](specs/task05h_final_result.json) records the release bindings.

Tasks 07 and 08 resolve the Task 05H acceptance pointer once, then pin the
inventory identity, completion seal, and exact component references for the
whole downstream run. They retain the accepted reference, F1-substitution,
sampled-review, and text-only figure limitations; see the
[Task 05H summary](specs/task05h_final_summary.md). A link or accepted inventory
membership does not establish case eligibility or evidence sufficiency.

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
