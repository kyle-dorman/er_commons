# Task 03G.3: Align the Pipeline with Explicit Responsibilities

Status: **complete; Gate B human-maintainability result accepted on
2026-08-18**. Gate A was accepted, the Gate B behavioral MVP was independently
rejected as insufficient for closure, and the resulting maintainability and
recovery rewrite passed the complete offline gate. The user accepted the result
and authorized this local closure commit. No source-PDF/model execution or Task
03H activation was authorized.

## Abstract

Refactor the maintained document-processing code so its package boundaries,
process names, public commands, configuration, tests, and current documentation
describe the transformations the system actually performs. The present code
preserves strong evidence and lifecycle boundaries, but its accumulated terms
such as `producer`, `canonical`, `semantic materialization`, `corpus`, generic
`extraction`, and machine `review` obscure the dataflow and sometimes assign
similar names to different responsibilities.

Use the completed three-document Task 03G.2 pilot and Task 03G.2f
cross-document repair as fixed behavioral evidence. First inventory every
affected caller, artifact contract, and identity consequence and freeze an exact
semantic DAG, vocabulary, and old-to-new mapping. Only after that Gate A is
reviewed and explicitly accepted may Gate B reorganize and rename maintained
code. Preserve extraction behavior, retained evidence, restartability, and
validation; this task changes ownership and language, not parsing, hierarchy,
table, or reference policy.

This is the architecture-closure subtask between the representative pilot and
the all-source Task 03H run. It must leave an explicit content-parsing seam for
Task 03H's independently sealed Docling-conversion boundary, but it does not
silently implement that separately specified restartability work.

## Goal

Make the maintained pipeline understandable from its code layout and names:
each transformation has one clear owner, process names say what operation is
performed, artifact/data-model names say what is produced, document-scoped and
collection-scoped work are visibly distinct, and machine reporting cannot be
confused with Task 04 human review.

The refactor must preserve current behavior and accepted evidence while giving
Task 03H one coherent architecture and vocabulary to execute against.

## Target semantic DAG

Gate A must verify and, where current behavior requires it, narrowly refine this
provisional process graph before implementation:

```text
verify source release
  -> [for each document]
     -> parse stable content --------------------------+
     -> parse heading evidence -> infer hierarchy ----+
     -> reconstruct routed tables --------------------+
                                                         |
                 map parser output to repository records |
                              + infer hierarchy decisions |
                                           -> map records into sections
                                           -> resolve printed page labels
                                           -> construct target aliases
                                           -> detect references
                                           -> resolve document references
                                              -> publish completed document
                                              -> preserve eligible cross-document inputs

published documents
  -> account for the declared collection
  -> index record targets -----------------------------+
  -> index source-owned document targets --------------+
eligible cross-document inputs + shared source-family catalog
  -----------------------------------------------------> resolve cross-document references
                                                        -> assemble and validate handoff
                                                           -> generate machine extraction report
```

Restart/reuse, lineage verification, attempt retention, checksums, validation,
and atomic publication surround this DAG as workflow controls. They are not
additional content transformations. The bounded smoke and retained downstream
replay are diagnostic or recovery entry points, not production DAG stages.

## Provisional process vocabulary

Gate A starts from the following operation-oriented vocabulary. It may propose
a more precise term only when the caller/artifact inventory demonstrates that
the provisional term misstates a real responsibility. The exact glossary and
package grouping require user acceptance before Gate B.

| Process responsibility | Provisional maintained term |
| --- | --- |
| Verify and seal source inputs | `source_verification` |
| Parse stable text, layout, figures, and assets | `content_parsing` |
| Parse heading and nesting evidence | `heading_evidence_parsing` |
| Route, parse, recover, and join tables | `table_reconstruction` |
| Map parser-shaped evidence to repository record types | `record_mapping` |
| Decide heading roles, levels, parents, numbering, and TOC relations | `hierarchy_inference` |
| Apply hierarchy decisions by assigning records to sections | `section_mapping` |
| Resolve printed labels for physical pages | `page_label_resolution` |
| Construct aliases over linkable records | `target_alias_construction` |
| Detect exact source spans that may name targets | `reference_detection` |
| Resolve references against targets in the same document | `document_reference_linking` |
| Validate, seal, reuse, and publish one document | `document_publication` |
| Record one terminal outcome for each declared source | `collection_accounting` |
| Index linkable section, table, figure, and page records | `record_target_indexing` |
| Map sealed source identities to document records | `document_target_indexing` |
| Resolve deferred references between documents | `cross_document_linking` |
| Join required collection evidence for the next workflow | `handoff_assembly` |
| Summarize machine outcomes without assigning usability | `extraction_reporting` |

Use `review` only for a process that requests or records human judgment. Avoid
`finalization`. Avoid overloaded `canonical`, `semantic`, `corpus`, generic
`extraction`, `producer`, and `owner` in maintained process names when a term
above states the responsibility more precisely. These words may remain in
immutable historical evidence or as deliberately chosen artifact/data-model
terms only under the accepted exception inventory.

Do not create one package per DAG box mechanically. Gate A must group closely
coupled operations into the smallest responsibility-oriented packages that keep
dependencies directional and make the document/collection boundary obvious.

## Inputs

- accepted Tasks 03G.1, 03G.1a, 03G.2, and 03G.2a through 03G.2f;
- the current maintained production entry points and package graph;
- the immutable accepted Task 03G.2/03G.2f document, scope, handoff, report,
  and request-only evidence;
- `AGENTS.md`, `docs/architecture.md`, `docs/data_artifacts.md`, and the current
  extraction and cross-reference specifications;
- `tasks/README.md` and the provisional Task 03H contract;
- all checked-in schemas, fixtures, configs, Make targets, CLI help, tests,
  code-identity inventories, and maintained task-specific replay tools that
  call or describe the affected code; and
- the target DAG and provisional vocabulary above.

Historical task prose and sealed artifacts are evidence, not editable inputs.

## Outputs

### Gate A: reviewed architecture and rename contract

- a caller and artifact inventory covering every affected maintained package,
  module, public symbol, import path, command, option/help string, Make target,
  config file/key/path, schema identifier, record type, artifact role/path,
  identity code-bundle input, test/fixture, current documentation reference,
  and retained diagnostic/replay tool;
- one exact current-to-target responsibility map, including moves, renames,
  merges, splits, removals, and deliberately retained names;
- one accepted package dependency graph showing content transformations,
  document workflow controls, collection workflow controls, validation, and
  machine reporting;
- a naming glossary that distinguishes processes from artifacts and data-model
  types and reserves `review` for Task 04 human work;
- an explicit legacy-name allowlist limited to immutable historical evidence,
  versioned compatibility readers, or other inventory-proven necessities;
- a schema, CLI, configuration, and artifact migration decision for every
  maintained serialized or user-facing name;
- an identity/invalidation matrix stating which future `prv1-`, `exv1-`,
  `docv1-`, `scopev1-`, index, resolution, and handoff identities change and
  why; and
- an exact Gate B edit plan and preservation oracle accepted by the user before
  implementation.

### Gate B: implemented and verified architecture

- maintained source and test code organized around the accepted responsibility
  graph and vocabulary;
- consistently renamed public and internal symbols, CLI surfaces, configs,
  schemas, fixtures, artifact roles, reporting terms, current docs, and tests
  wherever Gate A classifies them as maintained;
- no compatibility aliases, duplicate packages, forwarding modules, or dual
  writes unless Gate A identifies a concrete caller or immutable artifact that
  requires them;
- versioned replacement contracts where a persisted schema or artifact name
  changes, without mutating a sealed historical bundle;
- complete owned-code identity inventories and refreshed non-executed future
  recipes/config paths after the final layout is stable;
- exact offline semantic-preservation evidence against accepted Task 03G.2
  artifacts, normalizing only the name, path, schema-version, and derived
  identity fields declared in Gate A;
- updated `docs/architecture.md`, current routing docs, and the provisional
  Task 03H contract using the accepted vocabulary and dependency graph; and
- a concise outcome stating what moved, what intentionally retained its old
  name, what identities changed, and what Task 03H must still implement.

## Research / learning checkpoint

Before Gate A is accepted, inspect primary Python packaging guidance for public
module moves, the project's Pydantic/Typer interfaces, and the versioning rules
of every affected checked-in JSON Schema. Record the smallest migration design
that keeps imports, schemas, identities, and artifact provenance honest.

Preserve these explanations in the outcome:

- A responsibility boundary names a reason for code to change; a DAG box is
  not automatically a package.
- Process names describe transformations; artifact and model names describe
  persisted results. Mixing the two makes callers and lifecycle ownership hard
  to infer.
- A behavior-preserving module move may still change a content-bound identity.
  Identity change is evidence of changed implementation input, not proof of
  changed extraction semantics.
- Historical evidence remains immutable. Current names can improve through a
  new version without rewriting the old record or carrying indefinite aliases.
- Machine validation and reporting are not human review. Task 04 alone owns
  usability judgments and accepted-release disposition.
- A semantic refactor must make the independently sealable content-parsing seam
  clearer, but Task 03H separately owns implementing and exercising that new
  restart boundary.

## Plan / spec requirement

### Gate A — inventory and freeze the design

1. Re-read current routing and verify that no newer task supersedes this one.
2. Generate the full affected-name and caller inventory. Classify every hit as
   maintained process language, artifact/data-model language, immutable
   history, compatibility input, or obsolete code.
3. Trace the executable dependency graph from CLI entry points through
   document publication, collection linking, handoff assembly, and reporting.
4. Reconcile that graph with the target semantic DAG. Identify any hidden
   responsibility, cycle, duplicated policy, or box that should not become a
   package.
5. Propose the exact package grouping, module/symbol names, CLI vocabulary,
   persisted-contract changes, and legacy exception allowlist.
6. Inventory callers and artifacts before proposing deletion of any old path or
   compatibility surface.
7. Define behavior and artifact comparison rules, including the exact fields
   that may differ because names, paths, schema versions, or identities change.
8. Record the invalidation matrix and a no-PDF/no-model validation plan.
9. Stop for user review. Gate A documentation does not authorize Gate B.

### Gate B — implement after explicit activation

1. Move and rename code in dependency order, keeping the repository runnable
   after each bounded slice.
2. Separate transformation code from document and collection workflow control;
   keep validation and publication responsibilities explicit.
3. Update direct callers rather than adding broad forwarding aliases.
4. Version maintained serialized contracts when necessary and retain read-only
   handling only where the accepted inventory requires it.
5. Update configs, code-identity inventories, fixtures, tests, commands, help,
   current docs, and task routing in the same slices as their owners.
6. Remove superseded maintained paths only after caller, identity, artifact,
   and test inventories prove they are unused.
7. Run the complete offline preservation and maintainability gates.
8. If adapter behavior cannot be established without a real invocation, write
   the smallest bounded invocation plan and obtain separate user approval
   before reading PDFs or running a model.
9. Reconcile Task 03H against the accepted architecture and vocabulary, but do
   not activate it.

## Review pass

- **Semantic ownership:** every maintained package has one coherent reason to
  change; orchestration does not absorb content policy.
- **Vocabulary:** operation names are distinct, directional, and used
  consistently across code, tests, commands, configs, and current docs.
- **Document/collection boundary:** local linking and publication finish before
  collection accounting/indexing and cross-document linking begin.
- **Contract honesty:** persisted names are either migrated through a declared
  version or retained under an explicit exception; old bundles are untouched.
- **Identity honesty:** code moves and contract changes refresh future
  identities without rebinding accepted candidates.
- **Maintainability:** dependency direction, module responsibilities, typed
  interfaces, error context, and behavior-focused tests allow a future engineer
  to locate and change one process without learning the full task history.
- **Task boundaries:** no parser policy change, human review, full-corpus run,
  or Task 03H restart implementation is hidden inside the refactor.

## Validation

Gate B must include:

```bash
make fix
make validate-collection-contract
make check
git diff --check
```

Also require:

- a static stale-name audit over maintained source, tests, configs, commands,
  and current docs, with every remaining old term covered by the accepted
  allowlist;
- import, CLI-help, config-loading, schema, artifact-publication, validation,
  and read-only handoff tests through the new public boundaries;
- direct behavior tests for every named responsibility in the accepted DAG;
- complete owned-code identity inventory checks after all moves;
- exact offline comparison against immutable Task 03G.2 evidence using only the
  accepted normalization set;
- handoff, extraction-report, and request-only recipe validation where the
  offline preservation path reaches those consumers;
- before/after snapshots proving no PDF, Docling, Camelot, TableFormer, other
  model, producer, or document attempt was allocated during offline replay;
- verification that retained Task 03G.2 artifacts and attempt inventories are
  byte-unchanged; and
- either an accepted adapter-boundary test or a separately approved bounded
  fresh invocation for any external seam whose behavior cannot be proven from
  immutable evidence alone.

If unrelated repository-wide failures exist, report them separately and still
run the narrow checks that prove the changed responsibilities.

## Acceptance criteria

- Gate A inventories and disposes every affected maintained name and caller;
  implementation does not begin before the user accepts the exact map.
- The maintained code dependency graph matches the accepted semantic DAG, with
  workflow controls distinguished from content transformations.
- The final maintained vocabulary is used consistently across code, public
  commands, configs, schemas, tests, reports, and current documentation.
- `review` is absent from machine-only maintained process names unless an
  accepted exception names the human-review interaction it represents.
- No stale overloaded process name remains outside the accepted exception
  allowlist.
- Parser, table, hierarchy, section, page-label, alias, document-linking, and
  cross-document-linking behavior matches the accepted preservation oracle.
- No accepted Task 03G.2 artifact is rewritten or rebound.
- Every future identity change is explained by the accepted invalidation matrix
  and reflected in refreshed non-executed recipes only after the layout freezes.
- No compatibility alias or duplicate package remains without a demonstrated
  caller or artifact requirement.
- The code leaves a clear content-parsing boundary for Task 03H's independently
  sealed Docling conversion work without claiming that boundary is implemented.
- The provisional Task 03H contract is revised to the accepted vocabulary and
  architecture and remains inactive pending separate activation.
- The user accepts Task 03G.3 before Task 03G closes or Task 03H can activate.

## Non-goals

- changing PDF parsing, routing, table acceptance, continuation, hierarchy,
  page-label, alias, or reference-resolution policy;
- implementing Task 03H's independently sealed Docling conversion lifecycle;
- reading PDFs or running Docling, Camelot, TableFormer, or another model
  without separate explicit approval;
- running the complete 35-source collection or activating Task 03H;
- performing Task 04 human review, assigning usability, or freezing a release;
- rewriting, migrating in place, deleting, or rebinding sealed historical
  candidates and task evidence;
- keeping old maintained names through speculative backward-compatibility
  aliases;
- introducing a workflow engine, database queue, or framework abstraction;
- benchmark case selection, retrieval, generation, judging, or evaluation; or
- committing or pushing unless separately authorized.

## Gate A frozen design

The complete caller, module, schema, config, artifact, test, documentation,
diagnostic, and replay inventory is in the checked-in
[Gate A inventory](03g3_gate_a_inventory.md). The following design is accepted
and frozen. Gate B may not begin until the user separately activates it.

### Accepted responsibility graph

```text
source_release
  -> document_parsing
       content_parsing
       heading_evidence_parsing
       table_reconstruction
  -> hierarchy_inference
  -> document_records
       record_mapping
       document_structure
         section_mapping
         page_label_resolution
         target_alias_construction
       document_references
         reference_detection
         document_reference_linking
  -> document_publication

published-document evidence + source-family catalog
  -> collection_processing
       collection_accounting
       record_target_indexing
       document_target_indexing
       cross_document_linking
       handoff_assembly
  -> extraction_reporting

human_review_support and artifact_comparison consume published evidence;
they are never imported by production processing.
```

`artifact_io` is a neutral lower-level module for checksum, canonical JSON,
inventory, and contained-path primitives that are currently imported from a
parser package by workflow controls. Lifecycle controls remain inside document
or collection publication rather than becoming content transformations.

This grouping deliberately does not create one top-level package per DAG box.
Closely coupled record transformations share `document_records`; the parsing
operations share `document_parsing`; and collection stages share one directional
`collection_processing` package.

### Exact package and public-entry migration

| Current maintained surface | Gate B target | Decision |
| --- | --- | --- |
| `source_freeze.py` and source verification helpers | `source_release` | Group acquire/freeze/verify behavior under the source-release concept; the DAG operation is `source_verification`. |
| `document_extraction` + `table_extraction` | `document_parsing` with `content_parsing`, `heading_evidence_parsing`, and `table_reconstruction` subareas | Remove `producer_*` process names. Move existing heading/PDF observation code from hierarchy without adding Task 03H sealing. |
| `run_complete_document_producer` | `run_document_parsing` | Public transformation name; lifecycle publication remains outside it. |
| `canonical_extraction` | `document_records.record_mapping` | Retain `canonical` only for persisted record/data-model vocabulary. |
| `run_document_canonicalization` | `map_document_records` | Direct hard cut; no forwarding facade. |
| inference core of `hierarchy_correction` | `hierarchy_inference` | Keep TOC reconciliation, scopes, rules, level/parent decisions, hierarchy projection, validation, and candidate lifecycle together. |
| `run_hierarchy_correction` | `infer_document_hierarchy` | Existing decisions are preserved exactly. |
| `semantic_structure` + `semantic_materialization` | `document_records.document_structure` | Merge builder/validator ownership while retaining separate section, page-label, alias, bridge/control, and lifecycle modules. |
| `run_semantic_materialization` | `map_document_structure` | Builds sections, page-label outcomes, and target aliases. |
| `cross_reference_enrichment` | `document_records.document_references` | Keep detection, document-local target indexing, and local linking separate within one group. |
| `run_cross_reference_enrichment` | `link_document_references` | Detect first, then link only against verified document targets. |
| `corpus_extraction` | `document_publication` | Own source selection, lineage/preflight, attempts, isolation, publication/reuse, observability, and downstream recovery. It owns no content policy. |
| `run_document` | `publish_document` | Collection code consumes only its published-document evidence interface. |
| `corpus_resolution` | `collection_processing` | Own collection accounting, both collection target streams, cross-document linking, handoff assembly, and their publication controls. |
| `run_scope` | `assemble_collection_handoff` | Makes the output and scope explicit. |
| `validate_handoff` | `validate_collection_handoff` | Remains read-only. |
| `extraction_review.pilot_reporting` | `extraction_reporting` | Machine aggregation/reporting, never human disposition. |
| `extraction_review.comparison` | `artifact_comparison` | Read-only machine comparison outside publication identity. |
| `extraction_review.{authorization,rendering,requests}` | `human_review_support` | `review` is valid because these surfaces request or record human judgment. |
| `smoke_extraction` | `parser_smoke` | Retained diagnostic, explicitly outside the production DAG. |
| `extraction_regression.py` | `parser_regression.py` | Retained bounded diagnostic. |
| `task03g2f_replay` | retained task-specific package | Its task name identifies immutable bounded recovery evidence; update imports directly. |
| `corpus_extraction_contract_v1_1` | retained v1.1 compatibility validator plus new workflow-contract v2 package | Existing evidence remains readable; new code does not write v1 names. |

The compatibility-only hierarchy facades `decision_builder.py`, `features.py`,
`hierarchy_builder.py`, `regime_builder.py`, and `toc_builder.py` are removed
after their internal/test callers import the real policy modules directly.
Shared replay identity/verification moves below `document_publication.candidates`
to break the current lazy runtime cycle. `DocumentTerminalEvidence` and its
observer become the narrow document-to-collection interface.

### Frozen operation and artifact glossary

| Kind | Frozen term | Meaning |
| --- | --- | --- |
| operation | `source_verification` | Verify the sealed source release and selected source bytes. |
| operation | `content_parsing` | Parse stable text, layout, figures, assets, and parser output. |
| operation | `heading_evidence_parsing` | Observe headings, outline, TOC, numbering, and printed-page evidence without deciding hierarchy. |
| operation | `table_reconstruction` | Route, parse, recover, clean, and join tables. |
| operation | `record_mapping` | Map parser-shaped evidence into repository record types. |
| operation | `hierarchy_inference` | Decide heading roles, levels, parents, numbering, and TOC relations. |
| operation | `section_mapping` | Apply hierarchy decisions to mixed document records. |
| operation | `page_label_resolution` | Resolve printed labels for physical pages. |
| operation | `target_alias_construction` | Construct verified aliases over linkable records. |
| operation | `reference_detection` | Detect exact source spans that may name targets. |
| operation | `document_reference_linking` | Link against targets in the same document. |
| operation | `document_publication` | Validate, seal, reuse, or publish one complete document. |
| operation | `collection_accounting` | Record one terminal outcome per declared source. |
| operation | `record_target_indexing` | Index linkable section, table, figure, and page records. |
| operation | `document_target_indexing` | Map sealed source identities to document records. |
| operation | `cross_document_linking` | Resolve deferred references between documents. |
| operation | `handoff_assembly` | Join required collection evidence for the next workflow. |
| operation | `extraction_reporting` | Summarize machine outcomes without assigning usability. |
| artifact | `canonical` record collections | Stable repository data-model vocabulary, not a process name. |
| artifact | `prv1-`, `exv1-`, `hcorv1-`, `docv1-`, `scopev1-`, `txv1-`, `idxv1-`, `resv1-`, `handoffv1-` | Existing typed identity namespaces; new inputs produce new values. |
| artifact | accounting, target index, resolution, handoff | Accurate collection products retained by name. |
| human process | `review` | Reserved for Task 04, authorization decisions, requested comparisons/renders, and human dispositions. |

`producer`, process-level `canonical`, process-level `semantic`, `corpus`,
generic process-level `extraction`, `owner`, and `finalization` are forbidden in
new maintained process names. Their explicit historical/data-model exceptions
are limited by the Gate A inventory allowlist.

### CLI and Make migration

Gate B makes one hard cut because the repository has no demonstrated external
caller requiring an alias:

```text
er-commons documents publish --document-spec PATH --source-id ID
er-commons collections assemble-handoff --collection-spec PATH
er-commons collections validate-handoff \
  --collection-root DIR --scope-id ID --schema FILE
er-commons collections validate-contract --schema FILE --fixtures DIR

make publish-document DOCUMENT_SPEC=PATH SOURCE_ID=ID
make assemble-collection-handoff COLLECTION_SPEC=PATH
make validate-collection-handoff ...
make validate-collection-contract
```

CLI help snapshot tests must cover group names, command names, option names,
and operation-oriented help. Stable output artifact labels
`document_completion`, `handoff_completion`, and `handoff_id` remain; the
ambiguous output `documents=` becomes `verified_documents=`.

### Versioned config, schema, and artifact migration

Accepted Task 03G.2 v1 configs, schemas, fixtures, and artifacts remain
byte-immutable. Gate B introduces strict v2 workflow models with no aliases,
dual writes, or mixed-key acceptance:

| v1 maintained process key | v2 key |
| --- | --- |
| `document_owners` | `document_processes` |
| `baseline_producer` | `content_parsing` |
| `hierarchy_producer` | `heading_evidence_parsing` |
| `canonical` | `record_mapping` |
| `hierarchy_correction` | `hierarchy_inference` |
| `semantic` | `document_structure` |
| `cross_references` | `document_reference_linking` |
| `ScopeRunSpec` / scope-run config | `CollectionRunSpec` / collection-run config |
| `corpus_catalog_relative_path` | `source_family_catalog_relative_path` |

The persisted v2 document-completion role keys name products rather than
operations: `stable_content_evidence`, `heading_evidence`, `mapped_records`,
`hierarchy_decisions`, `structured_document`, and `linked_document`.

The new schemas are `er_commons.document_run_spec.v2` and a collection workflow
contract under `benchmarks/er_bench/schemas/collection_processing/v2/` with a
new `$id`, fixtures, and strict models. Canonical record schemas v1/v2/v3 and
their `canonical/` paths do not change. Version-specific v1/v1.1 readers are
the only bridge used by the offline preservation oracle.

Future Task 03H configs use operation names and v2 filenames for each source,
plus `_document_v2.json` and `_collection_v2.json`. Future external roots are
`document_parse_evidence/`, `document_records/`, `document_publications/`, and
`collection_runs/`; accepted roots are never moved. The v1 pilot report remains
immutable; new machine reports use an `extraction_report` schema/path and new
human render requests use `render_request` vocabulary.

### Identity and invalidation matrix

All consequences below apply only to future recipes/candidates. Accepted Task
03G.2 candidates and identities remain unchanged and are never rebound.

| Identity/artifact | Gate B consequence | Reason |
| --- | --- | --- |
| source release | unchanged | No source or manifest bytes change. |
| both parsing `prv1-` IDs | change | Code inventories bind module paths/bytes, CLI, configs, environment inputs, and parsing policy. |
| record-mapping `exv1-` | change | New parsing IDs, config/path names, and owned-code digest. |
| hierarchy `hcorv1-` | change | New heading-evidence ID, config, module inventory, and code-bundle paths. |
| structured-document `exv1-` | change | Both parsing IDs, mapped-record and hierarchy IDs, config/spec refs, and owned code change. |
| linked-document `exv1-` | change | Structured-document ID, config/path, and owned-code inventory change. |
| production recipe `exv1-` | change | The production preimage binds all contracts, configs, artifacts, and owned-code paths. |
| `scopev1-` and `txv1-` | change | The run-spec checksum and production identity change. |
| `docv1-` | change | Production identity, control digest, and stage-completion role keys change. |
| accounting | change | It binds the new scope and document evidence. |
| `idxv1-` | change | Scope, production ID, accounting, candidate refs, target streams, and managed inventory change. |
| `resv1-` | change | Index, mention manifest, policy, and resolution bytes change transitively. |
| `handoffv1-` | change | Accounting, index, resolution, and managed handoff preimage change. |
| report/render request | change | Schema/path names and referenced scope/candidate identities change. |

Identity changes prove changed implementation/configuration inputs; they do not
by themselves imply changed extraction semantics.

### Offline preservation oracle

Gate B must use the immutable accepted Task 03G.2/03G.2f evidence and must not
read PDFs or invoke Docling, Camelot, TableFormer, or another model. It must:

1. Snapshot every accepted Task 03G.2 artifact checksum and all producer,
   document, replay, and collection attempt inventories before work.
2. Read accepted v1/v1.1 evidence through an explicit versioned adapter and
   rebuild the v2 future candidate in a new namespace.
3. Normalize only package/config/schema paths and versions, code/config/identity
   checksums, derived IDs and ID-bearing references, the six declared role-key
   replacements, and the renamed report/render schema/path fields.
4. Require exact ordered equality for canonical record semantic payloads,
   page/table/family/continuation decisions, hierarchy decisions, sections,
   printed-page outcomes, aliases, reference spans/candidates/statuses,
   warnings, counts, terminal dispositions, and handoff readiness.
5. Reproduce the accepted three-document report metrics, all 18 eligible and
   resolved cross-document mentions, the fixed ten-page table-link outcomes,
   and request-only recipe validation.
6. Invoke the new workflow twice and require exact second-invocation reuse with
   no new parsing, model, document, replay, or collection attempt.
7. Re-snapshot accepted artifacts and attempts and require them to be
   byte-identical to the pre-work snapshot.

If an external adapter seam cannot be proven from immutable evidence, Gate B
must stop with a bounded invocation plan. No invocation is implied by Gate A.

### Exact Gate B edit order

1. Add neutral `artifact_io` and the narrow published-document evidence
   interface; break the two internal cycles without changing behavior.
2. Move parsing and table code into `document_parsing`; move heading/outline/
   page-label observation out of inference while preserving its exact calls.
3. Move the inference core into `hierarchy_inference`; delete the five
   compatibility facades after direct caller updates.
4. Assemble `document_records` from record mapping, document structure, and
   document reference code, preserving v1/v2/v3 record contracts.
5. Move workflow controls into `document_publication`, replace owner language,
   and add strict v2 document-stage models/read-only v1 adapters.
6. Move collection stages into `collection_processing`, separate the two target
   indexes and the catalog/mention/linking responsibilities, and add the v2
   collection contract/schema/fixtures.
7. Split machine reporting, artifact comparison, and human review support;
   rename parser diagnostics; update the retained Task 03G.2f replay imports.
8. Replace the CLI, Make targets, generators, configs, code inventories, tests,
   and current documentation in the same slices as their owners.
9. Generate refreshed non-executed future Task 03H identities/configs only
   after the layout is stable; never rewrite accepted identity evidence.
10. Run the complete offline oracle, stale-name/allowlist audit, required
    project checks, and revise provisional Task 03H without activating it.

### Research and migration rationale

- Python treats fully qualified module names as import identities, and package
  imports populate parent namespaces. A move therefore requires direct caller
  updates rather than pretending that paths are invisible. See the
  [Python import-system reference](https://docs.python.org/3/reference/import.html).
- [PEP 8's public-interface guidance](https://peps.python.org/pep-0008/#public-and-internal-interfaces)
  treats documented interfaces and explicit `__all__` exports as public. Gate
  B updates those surfaces and tests directly and creates no speculative
  forwarding API.
- The [PyPA distinction between distribution and import packages](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/)
  permits the `er-commons` distribution and `er_commons` import root to remain
  stable while internal packages move.
- [Typer command naming and help](https://typer.tiangolo.com/tutorial/subcommands/name-and-help/)
  make names/help deliberate public surfaces, so the hard-cut CLI receives
  exact help tests.
- [Pydantic aliases](https://docs.pydantic.dev/latest/concepts/alias/) distinguish
  validation and serialization and do not make serialization compatibility
  automatic. Strict v2 models plus explicit v1 readers are more honest than
  accepting both vocabularies inside one model.
- JSON Schema `$id` establishes a schema's base identity. The existing IDs stay
  immutable and the changed workflow contract receives a new versioned ID. See
  the [JSON Schema structuring guidance](https://json-schema.org/understanding-json-schema/structuring).

The smallest migration therefore makes one versioned hard cut for current
workflow names, retains precise artifact vocabulary, and confines legacy names
to explicit historical readers and evidence.

### Gate A review result and stop point

- **Semantic ownership:** pass. The target packages each have one coherent
  reason to change, and orchestration does not absorb content policy.
- **Dependency direction:** pass with two explicit Gate B cycle removals and
  two lower-level interface moves named above.
- **Document/collection boundary:** pass. Local linking and document publication
  finish before collection accounting/indexing/linking/handoff.
- **Contract honesty:** pass. Persisted name changes receive v2 contracts;
  canonical record schemas and accepted evidence stay immutable.
- **Identity honesty:** pass. Every future identity change is declared and no
  accepted candidate is rebound.
- **Review vocabulary:** pass. Machine reporting/comparison is separated from
  actual human review support.
- **Task boundary:** pass. Gate A authorizes no implementation, parser-policy
  change, PDF/model work, Task 04 judgment, or Task 03H activation.

Gate A is complete and explicitly accepted. The next decision is separate
activation of Gate B.

## Outcome

Gate A was activated and completed as a documentation-only pass on 2026-08-18.
The full affected-surface inventory, exact target responsibility graph,
operation/artifact glossary, package and public-interface migration, v2
workflow-contract boundary, legacy-name allowlist, identity invalidation
matrix, offline preservation oracle, and ordered Gate B edit plan are frozen
above and in the linked inventory appendix. No implementation, PDF/model work,
artifact mutation, commit, push, or Task 03H activation occurred.

The user explicitly accepted Gate A and activated Gate B on 2026-08-18.

Gate B's behavioral MVP was implemented first. Maintained code follows the
frozen responsibility graph: source release and neutral artifact I/O feed
document parsing, hierarchy inference, document records, document publication,
collection processing, and machine extraction reporting. Human review support
and artifact comparison are outside the production dependency graph. Old
top-level process packages and the five hierarchy compatibility facades were
removed; direct callers, task-specific replay tooling, tests, CLI commands,
Make targets, and current documentation use the new boundaries.

The public hard cut is `documents publish` and `collections
{assemble-handoff,validate-handoff,validate-contract}`. Strict document and
collection v2 models, schemas, and fixtures use process/product vocabulary,
including `record_target_order_v2`. Native v2 identity builders, records, and
semantic validation now own current execution. Explicit v1 readers preserve
immutable Task 03G.2 evidence without aliases, dual writes, validation projection,
or execution through old keys. Canonical record schema terms,
`producer_run_id`, typed ID prefixes, v1/v1.1 schema strings, accepted config
bytes, historical task paths, and Task 03G.2f names remain only under the Gate A
allowlist.

The user rejected behavioral-MVP quality as insufficient for closure and requested
a separate human-maintainability gate. That second pass split source acquisition,
machine reporting, content/table orchestration, document-record validation, and
document-structure application paths into named responsibilities; introduced typed
execution, page/table, reference, review-selection, and recovery boundaries; made
JSONL and attempt journals atomic; added contextual artifact and record errors;
retained bounded child-process diagnostics; removed overlapping human-review APIs;
and added offline fresh/resume/recovery, corruption, CLI-behavior, contract-semantic,
and responsibility-size tests. Compatibility remains explicit and read-only.

Future code-bound parsing, hierarchy, document, scope, index, resolution, and
handoff identities necessarily change because their owned-code paths and v2
workflow preimages changed. No accepted identity was rebound. The new v2
fixtures are non-executed future recipes; Task 03H must create its exact
all-source configs after it implements the independently sealed content-
conversion boundary.

Final offline validation passed `make fix`,
`make validate-collection-contract`, `make check`, the direct v1.1 compatibility
suite, v2 schema/config and semantic tests, behavior-focused recovery suites,
CLI behavior tests, `compileall`, and `git diff --check`. Strict mypy checked
287 source files and the full suite passed all 595 tests. The
pre-refactor 270-file Task 03G.2 control-evidence manifest retained digest
`4c0bd4c4005dab066bb899351c4afb4a541a5cf15fd33b7a566671294486a0a4`;
all 270 checksums reverified exactly after the refactor. No source PDF was read,
no Docling/Camelot/TableFormer/model call occurred, and no attempt or accepted
artifact was allocated or mutated.

The user accepted this Gate B human-maintainability result and authorized Task
03G.3 closure and a local commit on 2026-08-18. Task 03G.3 is complete. Task
03H's provisional contract uses the accepted architecture but remains inactive
pending separate user authorization.
