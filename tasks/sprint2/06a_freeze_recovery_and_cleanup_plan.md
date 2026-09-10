# Task 06A: Freeze the Recovery and Cleanup Plan

Status: **complete; source-free planning packet independently reviewed (2026-09-10)**.
The user authorized 06A evidence qualification and planning outputs on 2026-09-10.
No implementation, PDF access, acquisition, model execution, or 06B work is
included in this authorization.

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

The source-free qualification produced exact accepted-input and 35-source
bindings, a complete code migration inventory, repair populations and structural
controls, review-correspondence candidates, and bounded downstream specifications.
The packet preserves original conversion entities; new execution identities will
reference them rather than reinterpret their old recipes through renamed code.
No implementation or later execution gate ran.

### Packet and interfaces

The working namespace is root-relative:

```text
pipelines/brisbane_baylands/task_06_recovery_v1/06a/
```

The [recovery/reuse specification](../../docs/specs/task06_recovery_plan_v1.md)
owns record fields, verification limits, resource ceilings, command boundaries,
and remaining gate decisions. The [code inventory](../../docs/specs/task06a_code_inventory.md)
owns all 29 tracked scripts and 61 task-named/support package files, exact
rename/remove/retain destinations, operational symbols, caller evidence,
dependency/invalidation rows and migration tests. These are 06B instructions,
not completed refactors. Historical artifact names and recipes remain unchanged.

| External packet file | Purpose |
| --- | --- |
| `accepted_input_bindings.json` | Recorded schemas, paths, digests, sizes, states, designations and observed verification limits |
| `source_slots.json` | All 35 original source slots, 03J/04D accounting and document identities, producer/conversion correspondence |
| `chunk_conversion_bindings.json` | Exact retained chunk plans, ordered range receipts and aggregate conversion correspondence |
| `mention_populations.v1.json` | All 511 existing mention IDs/outcomes and overlapping repair/control memberships |
| `f1_substitution_evidence.v1.json` | Wrong-source metadata, stored selected Final URL, 66 mentions and two revision contexts |
| `appendix_a_topology.v1.json` | Paired headings, stable keys, parents/children, extents, aliases, TOC evidence and structural controls |
| `main_chapter_evidence.v1.json` | Recovered heading candidates, TOC/child evidence, boundaries and fallback schema constraints |
| `figure_evidence.v1.json` | Independently eligible figure/image/caption associations and comparison to mentions |
| `review_correspondence_candidates.v1.json` | All 757 accepted TOC decisions with historical page/entity mapping, 35 usability scopes and conditional future reuse |
| `repair_read_manifest.v1.json` | Bounded selected-record reads and explicit no-payload-hash accounting |

`packet_inventory.json` closes 13 planning records totaling 7,283,202 bytes
and pins both repository specifications. The inventory itself is 5,709 bytes,
SHA-256 `83c314339a05a86abb433874b9d7ff82833696ff065451812be7b8937dfb34e7`.
Only these newly authored outputs were hashed for publication. The inventory
and independent reviews are not source acceptance, a replacement collection
completion, or new human usability approval.

### Findings and minimum replay

The F1 census distinguishes two revision-context units from the three F1
mention IDs they contain; no Draft/Final equivalence is inferred from either.
The original 35-source, 48,341-page scope is preserved as the baseline. The
accepted Task 05F population remains 295 links and 216 nonlinks across 511
mentions. F1 has 66 wrong-source outcomes, figures 79 absent-target outcomes,
and Chapters 8/9 have 19 outside-routed-source outcomes. Population membership
is by mention ID; two Appendix A mentions additionally carry duplicate-heading
context while retaining their existing more-specific-target nonlink outcome.
Do not add overlapping control sets. Comment-authored,
Appendix Q, ambiguous, and generic-source controls remain explicit.

Chapter 8 and Chapter 9 have recoverable number/title blocks misclassified as
`page_header` on physical pages 1855 and 2015. Their candidate extents are
1855–2014 and 2015–2084, bounded by the next chapter start (Chapter 10 at 2085).
These observations favor recovery from existing evidence before the fallback.
06E must qualify the split number/title representation, roles and coherent
children; no global promotion of page headers or new human decision is implied.
The TOC-plus-children fallback remains available when recovery fails its controls.

Appendix A's Chapter 06 and 08 pairs support a logical-chapter hypothesis, not
an automatic text-similarity merge. 06D owns the retained representative heading,
ordered child placement and destination interpretation; unresolved interpretation
requires human review. Preserve both blocks and their original stable keys.
The dividers have no section children, while the opening headings own six and
four child sections. TOC evidence is asymmetric: Chapter 06 token `280` matches
the opening page 312 footer; Chapter 08 token `447` differs from opening page
480 footer `448`, and divider page 479 has no footer. Reviewed-navigation
resolved destinations are null. 06D must resolve this evidence before choosing
a representative destination; a text match cannot settle it.

Independent caption qualification found 178 eligible exact body-caption figure
associations among 274 main-document figure records. Comparison reproduces 34
referenced targets supporting 78 of the 79 mentions, with no exact collision.
`Figure 4.8` has no exact target and stays unresolved. Caption-based target
publication does not establish text-only substantive evidence usability.

For unchanged sources, preserve original manifests and conversion/producer seals.
Mapping and hierarchy are sibling inputs: hierarchy changes do not themselves
invalidate record mapping. 06D/06E rebuild the necessary derived heading,
hierarchy/structure and downstream products; 06F extends target aliases from
existing figure evidence. New F1 is separately qualified and converted in 06C,
and that conversion is reused in 06G. Collection index/resolution must account
for changed targets including incoming links from otherwise unchanged documents.
05D/05E and accepted partial 05F remain untouched until 05G's separate replay.

### Learning and review

A recorded recipe explains how old evidence was produced; it is not a requirement
that the old source-code path still exist today. Integrity checks establish the
stated seal/metadata guarantees; compatibility establishes whether a new consumer
can use that evidence. A source heading and a TOC-derived structural inference
must remain distinguishable in provenance. The research checkpoint applied
[DVC stage reuse](https://doc.dvc.org/user-guide/pipelines/run-cache) and
[W3C provenance](https://www.w3.org/TR/prov-o/) to existing records without adding
a workflow engine or RDF dependency.

The independent code review checked inventory completeness, actual callers,
old-reader/new-writer separation and scope. Integration corrected generic
basename caller matches, preserved record mapping as a sibling of hierarchy,
and identified the live relink flag `--link-spec` (the historical specification
uses `--run-spec`). 06B must correct that command documentation during migration.

### Verification and independent review result

Qualified 1,207 unique binding records and 353 managed-inventory checks,
including exact file closure for all 70 accepted 03J/04D document publications.
All 35 pairs retain the same five prelink stage references. The packet binds
20 chunked sources and 318 completed ranges with exact contiguous core coverage.
Producer/conversion inventories were checked by named membership and size;
no broader unmanaged-directory closure or fresh payload equality is claimed.

The binding lane hashed 23,830,850 bytes including early stopped probes and
canonical-JSON seal checks; its largest hashed file was 1,027,692 bytes, beneath
the 1 MiB per-file and 32 MiB lane limits. Qualified binding reads total
196,184,909 bytes plus recorded exploratory probes. The repair lane hashed zero
bytes; its initial selected-file ledger is 88,977,234 bytes with supplemental
reads separately listed. Exploratory passes repeated selected records, so the
ledger is not presented as a precise task-wide I/O total. The largest selected
repair file was 50,042,036 bytes, below the 512 MiB file read ceiling. Review
passes read the new packet only, with zero upstream hashes.

Oversized accepted source manifests, index completions and inventories retain
recorded digests and are explicitly metadata-checked. A hierarchy inventory's
native canonical-JSON seal is distinguished from a file-byte SHA-256; an early
probe stopped on that interpretation mismatch and was corrected without editing
accepted evidence. This qualification is not a deep byte audit.

Three independent reviews passed: code/scope and packet correspondence,
repair evidence/controls, and accepted bindings/chunk coverage. Their versioned
records are `independent_code_and_scope_review.v1.json`,
`independent_repair_review.v1.json`, and `independent_bindings_review.v1.json`.
Review corrected two initially missed Appendix A mention contexts, added actual
list-of-figures table controls, and separated null projected TOC destinations
from observed printed tokens/footer evidence. No 06A blocker remains; structural
interpretation and new-evidence correspondence belong to the named later gates.

Docs were checked for local-link targets and whitespace with `git diff --check`.
No implementation test suite was run for this documentation/evidence task.

### Remaining decisions and readiness

06B is the next bounded task, with Gate 1 proving sealed reuse/identity and Gate 2
performing only the enumerated cleanup and integrated proof. It remains inactive
until implementation is authorized. Both gates must pass before any F1 processing.
The recovery specification assigns every remaining implementation/qualification
choice to 06B–06H. Unknown delivered F1 bytes, pages and title are intentionally
unknown; 06C has numeric planning ceilings and must freeze its acquisition spec
before contacting the stored URL, then separately bound and authorize conversion.
No settled source-choice decision needs reopening.

No implementation code, source PDFs, renders, models, extraction/replay, large
accepted-payload hashing, artifact deletion, commit or push was performed.
