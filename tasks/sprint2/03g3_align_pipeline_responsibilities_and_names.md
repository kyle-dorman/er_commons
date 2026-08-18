# Task 03G.3: Align the Pipeline with Explicit Responsibilities

Status: **drafted on 2026-08-18; not activated**. This documentation-only
contract does not authorize implementation, PDF or model execution, a commit,
or Task 03H activation. Task 03H remains blocked until this task is implemented,
validated, accepted, and used to revise the provisional Task 03H contract.

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
make validate-extraction-contract
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

## Outcome

Not started. Fill this section only after Gate A and any separately authorized
Gate B work complete. Record the accepted architecture and glossary, exact
renames and retained exceptions, preservation evidence, identity consequences,
validation, Task 03H revision, and the next explicit decision.
