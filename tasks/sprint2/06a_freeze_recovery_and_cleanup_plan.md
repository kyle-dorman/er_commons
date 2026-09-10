# Task 06A: Freeze the Recovery and Cleanup Plan

Status: **current planning entry; not executed**. The task-plan authoring is
authorized. Running this source-free evidence qualification is a subsequent
bounded action; no implementation, PDF access, acquisition, or model execution
is authorized by the existence of this contract.

## Abstract

Turn the [Task 06 umbrella](06_repair_reference_sources_and_target_index.md)
into exact input bindings, a cleanup inventory, and a minimum replay plan.
Determine what can be reused before moving code or changing identity recipes.
Give Task 06B a finite refactor scope and Tasks 06C–06H enough evidence to freeze
their implementation and execution specifications without repeating discovery.

The output is a source-free planning packet, not a new extraction candidate.
Read selected existing records and compact seals; do not rerun their producers.

## Goal

1. Bind the accepted source, conversion, producer, document, collection, review,
   and response evidence to exact recorded identities and relative paths.
2. Prove the planned dependency boundaries by tracing current code and contracts.
3. Classify task-named scripts, modules, and operational constants by actual use.
4. Freeze the observed repair populations and their independently sourced target
   evidence, including negative controls and review-reuse requirements.
5. Identify concrete schema/interface decisions that each subsequent task owns.
6. Produce the resource and authorization plan for new F1 processing and the
   later downstream replay; do not invent missing remote-file metadata.

## Inputs and reading order

Read `AGENTS.md`, `docs/index.md`, `docs/todo.md`, `docs/documentation.md`,
`docs/architecture.md`, `docs/data_artifacts.md`, and the umbrella first. Then:

- [Task 03J outcome](03j_run_final_canonical_extraction.md): accepted conversion,
  producer, and original document/collection lineage;
- [Task 04A outcome](04a_regenerate_review_and_freeze_release.md): usability and
  accepted TOC decisions;
- [Task 04D outcome](04d_relink_frozen_extraction.md): designated linking handoff;
- [Task 05F](05f_resolve_official_draft_eir_references.md): exact accepted 05D/05E
  bindings, partial candidate, rule inventory, populations, and stop evidence;
- `configs/README.md`, `pipelines/README.md`, and root `Makefile`: supported
  commands and the historical/current distinction;
- `docs/specs/semantic_structure_v2.md`, `docs/specs/document_linking_v1.md`,
  and `docs/specs/chunked_docling_conversion_v1.md`: only relevant contracts.

Use the umbrella's accepted-input table as a locator, not as a substitute for
validating the compact records. Do not automatically load every historical task
or every canonical payload. If the external root is unavailable, finish the
code/script inventory and mark exact artifact qualification incomplete.

## Research / learning checkpoint

Explain three distinctions in the outcome: a recorded historical recipe versus
code that is runnable today; artifact integrity versus compatibility for reuse;
and source evidence versus derived structural inference.

Use the [DVC run-cache documentation](https://doc.dvc.org/user-guide/pipelines/run-cache)
as a dependency-scoping reference, and [W3C PROV-O](https://www.w3.org/TR/prov-o/)
for the distinction between an entity and a new derived entity. Apply the ideas
to existing local records; introducing DVC, RDF, or a workflow engine is not
part of the task. Reuse the umbrella's research links before seeking more.

## Plan / spec requirement

### 1. Bind accepted evidence without a deep audit

For each selected input, record its role, source ID, artifact identity, schema,
root-relative path, recorded completion/inventory digests, size, terminal state,
and the accepted task or pointer that designates it. Check containment, file
existence, expected sizes, record cross-references, and exact managed-file names
where available. Hash compact binding records only; trust existing recorded
digests of large sealed payloads under the umbrella's verification policy.

Explicitly distinguish `metadata_checked` from `bytes_verified`. Neither size
agreement nor matching stored digests proves that unread payload bytes agree.
Stop the affected binding on missing seals, size/path disagreement, or ambiguous
designation; do not repair the evidence or silently start a full hash scan.

Trace each source from collection accounting to document identity and upstream
stage seals. Enumerate the 35 logical source slots, retaining the original
manifest for unaffected sources and a future replacement binding for F1.

### 2. Build the stage and identity-impact table

Each row must name: stage owner, input seal, current identity recipe, actual
behavior dependencies, proposed change, reused evidence, invalidated output,
downstream consumers, read/hash mode, and validation method. Cover:

- source acquisition and semantic source qualification;
- conversion planning, chunk ranges, aggregate conversion, and producer stages;
- heading evidence, hierarchy, record mapping, semantic sections, and aliases;
- reviewed navigation, document linking/publication, and all collection stages;
- Task 04 review correspondence and Task 05 source/relationship/reference stages.

Trace the audited problems in `document_parsing/content_parsing/conversion_identity.py`,
`chunked_conversion/runtime/inputs.py`, `document_publication/preflight.py`,
`document_publication/storage.py`,
`document_records/document_references/relink_publication.py`,
and `response_inventory/code_inventory.py`. Paths are beneath
`src/er_commons/`; verify them before using them as edit instructions.

Freeze the intended invalidation matrix in 06B. In particular, source-acquisition
code or a changed release-wide manifest must not force reconstruction of the
unchanged documents' already accepted conversion evidence.

### 3. Classify task-specific executable code

Enumerate all tracked `scripts/` files, then follow imports into task-named
package modules and inspect task-specific operational variables in maintained
owners. Search callers in source, scripts, tests, Make targets, configs, identity
recipes, and current documentation. Use static searches as evidence, not proof
that dynamic/external callers do not exist.

For each candidate, record:

| Field | Required decision |
| --- | --- |
| Current path/symbol | Exact file and relevant task-specific constants |
| Responsibility | What it does, independently of the old task number |
| Callers and evidence consumers | Runtime, tests, configs, identities, recorded artifacts |
| Classification | Maintained capability, one-off execution, or historical artifact support |
| Action | Rename/refactor, remove, or retain with an explicit purpose |
| Destination/interface | Concrete new path/command for maintained code |
| Identity effect | Owning future recipe and preserved historical references |
| Verification | Tests and searches proving the intended migration |

Mandatory candidates include `prepare_task03g2.py`, its preparation module,
`run_task03g2f_downstream_replay.py` and isolated orchestration,
`scripts/task03h_generation/`, Task 03J wrappers, Task 04 preparation/review
scripts, and `collection_processing/compatibility_v1_bundle.py`. This list is
an audit queue, not advance permission to delete them all.

Do not rename archived artifact directories, accepted schemas/record types,
source IDs, or historical identity strings merely to remove a task number.
Keep corpus-specific configuration where it represents a real input. A reusable
script must accept explicit inputs instead of hiding one-off selections behind
a generic filename. Preserve an old callable alias only for a demonstrated
current caller, with a documented migration boundary.

### 4. Qualify repair evidence and review correspondence

Freeze a manifest of the 511 Task 05F mentions by existing mention ID and
outcome, with explicit membership in the F1, figure, Chapter 8/9, duplicate-
heading, and negative-control populations. Do not add overlapping counts as
though they were disjoint. The umbrella owns the recorded starting totals.

For Appendix A, collect both heading blocks, stable keys, hierarchy decisions,
parents/children, physical pages, section extents, aliases, and accepted TOC
destinations. Inspect surrounding chapter-opening controls and repeated titles
that are real children or separate sections. Do not promote a merge from text
similarity alone.

For main Chapters 8/9, locate any recoverable body headings before designing the
fallback. Collect accepted TOC title/destination evidence and ordered subsection
coverage, competing boundaries, and the start of the following structural unit.
List what the current schema cannot express and assign its resolution to 06E.

For figures, enumerate independently eligible canonical figure/image/caption
records before comparing them with response mentions. Reproduce the preliminary
34-target/78-mention expectation or report the exact discrepancy. Keep the
missing `Figure 4.8`, list-of-figures rows, and competing captions as controls.

For F1, preserve the wrong-source metadata and all 66 mention IDs, including the
two revision contexts. Record the selected Final F1 URL from accepted inventory;
do not contact it during this task. No reuse of the wrong F1's review is allowed.

Map review decisions to their actual page/content/target evidence. Classify
reuse as unchanged evidence, remapped equivalent evidence, changed evidence, or
unproven correspondence. A changed target ID alone does not require rereview;
unchanged source ID alone does not justify reuse.

### 5. Freeze bounded downstream specifications

Name the source-substitution, chapter-decision, figure-provenance, reuse-
correspondence, and handoff fields required by the umbrella. Prefer extensions
to existing records or small adjacent records. Identify owning validators and
consumers; do not build a generic artifact registry.

Specify the future root-relative working namespace, exact maintained commands,
allowed stages/sources, and stop/resume behavior. For F1, derive or propose
numeric byte/page/time/disk limits from available evidence and mark estimates
as estimates; 06C must freeze concrete ceilings before any network request.
Use known runtime observations to estimate costs without running a benchmark.
Record extraction/model-call expectations separately from metadata/read costs.

Freeze an explicit hashing allowlist by record role and concrete per-file and
per-invocation byte ceilings. Include accepted completion, inventory, acceptance,
and descriptor records only where within those limits, plus small current code,
config, and schema inputs. A JSON/JSONL suffix does not make a payload compact.
Source PDFs, images, model weights, and preserved canonical payload trees are
excluded from routine hashing regardless of file size. Define bounded record-
reading selections separately from hashing, so transformation reads cannot
silently become checksum scans. 06B must consume and test these limits.

## Outputs

A small tracked decision/specification note under `docs/specs/` may hold the
approved reusable interface decisions; task-specific findings belong here in
the outcome. Larger enumerations belong in the future Task 06 working root.
Use plain Markdown tables or small JSON/JSONL records, whichever fits each
consumer, with explicit format/version and compact input references.

The packet must contain accepted-input bindings; the dependency/replay matrix;
the complete script rename/remove/retain inventory; repair evidence and controls;
review correspondence candidates; resource/command plan; and a finite decision
list assigning every unresolved item to one subsequent task and gate.

## Validation and review pass

- Reconcile the accepted 35-source scope and 511 mention population; preserve
  recorded 295 links/216 nonlinks as the comparison baseline.
- Verify every proposed deletion against callers and identity references.
- Independently review source/identity reuse, structural evidence, and task scope.
- Check that each later task can start from this packet and its own contract.
- Confirm no command used source PDFs, model files, extraction, network source
  discovery, or large-payload hashing; report the actual verification limits.
- Inspect the documentation diff and run `git diff --check`.

## Acceptance criteria and stops

06A is complete when the packet binds real accepted evidence, makes 06B's file
scope executable, and supplies a concrete decision/qualification path for every
later task. Unknown remote F1 metadata may remain unknown, but numeric limits
and the method for resolving it before conversion must be specified.

Stop the affected work on a baseline mismatch, unprovable seal correspondence,
or need for PDF/model access. Continue independent code/doc planning. Do not
describe an unexecuted qualification as passed or activate 06B automatically.

## Non-goals

Implementation, deletion/renaming of executable code, source acquisition,
conversion, production replay, new human dispositions, acceptance publication,
artifact cleanup, commit, push, and Task 05G execution.

## Outcome

Pending execution. The planning packet and exact live artifact checks have not
been produced by writing this contract.
