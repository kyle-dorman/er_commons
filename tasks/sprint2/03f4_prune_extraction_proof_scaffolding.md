# Task 03F.4: Prune Extraction Proof Scaffolding and Firm Boundaries

Status: **Complete and accepted**. The user accepted the integrated Gate B and
pre-close maintainability result on 2026-08-04. The corrected 222-page Appendix
P transaction completed and checksum reuse verified after separately authorized
lineage corrections and candidate-specific authorization rebinds. Task 03G
remains inactive. Commit was separately authorized; push was not.

## Abstract

Remove executable archaeology left by completed extraction experiments and
rewrite gates, then make the maintained source-to-corpus path obvious to a
human reader. This repository is still a proof of concept: obsolete schemas,
validators, candidate-specific fixtures, and replay paths may be removed
destructively without migration or continued historical-artifact replayability.
Preserve the behavior and capabilities required by the maintained Task 03 path
and its declared Task 03G, Task 03H, and Task 04 consumers. This cleanup changes
code and contracts only: it does not run a PDF, change extraction policy, or
execute Task 03G.

## Goal

Enter Task 03G with one readable production path for each extraction stage, the
smallest executable contract set needed by that path, and explicit boundaries
between content construction, validation, publication, independent handoff
validation, review-cache generation, and optional pilot-level reproducibility
checks. Historical outcomes remain documented in completed task records; their
obsolete executable implementations and schemas do not remain in the repo.

## Inputs

- the accepted Task 03C.1 through Task 03F.3 human-owned implementations and
  their current public interfaces;
- `extraction run-document` and `extraction run-scope` as the intended
  orchestration boundaries;
- the active canonical v1, semantic v2, cross-reference v3, hierarchy-
  correction v1, and corpus-extraction v1.1 contracts;
- completed task outcomes as non-executable historical evidence;
- current imports, configs, tests, Make targets, CLI commands, schemas, and the
  production-identity owned-code/artifact inventory;
- the user decision that selected repeatability and review execution belongs in
  Task 03G, not in every maintained document candidate; and
- the user decision that this proof-of-concept cleanup may be destructive and
  does not require schema migration, compatibility aliases, or retained
  executable verification of superseded candidates; and
- the user decision that Gate B is one integrated implementation and review
  effort, with internal stage validation but no routine user approval gate
  between stages.

## Outputs

1. A checked-in, read-only caller, capability, and artifact inventory
   classifying every candidate below as `keep`, `keep until named successor`,
   `transfer invariant then remove`, or `remove`, with the exact active
   replacement or future task owner named.
2. One production implementation path with named responsibility owners for
   construction, active invariant validation, lifecycle/publication, and
   orchestration.
3. Removal of obsolete packages, modules, schemas, tests, configs, CLI commands,
   Make targets, identity entries, and documentation references after their
   callers and still-required invariants are accounted for.
4. Simplified configuration and runtime APIs with historical comparison,
   reference-candidate, rewrite-review, and mandatory second-build controls
   removed from the maintained path.
5. A refreshed, non-executed production identity covering the exact surviving
   output-affecting implementation and contracts.
6. A Task 03G/03H/04 handoff inventory naming the surviving interfaces for
   repeat execution, semantic comparison, independent candidate validation,
   machine-observation access, and requested review-cache generation.
7. A short outcome inventory recording what was removed, what remains, and why.

## Candidate removal inventory

The inventory step must verify these candidates rather than treating this list
as deletion authorization. Historical POC replayability is not a retention
criterion; current production behavior and declared downstream capability are.

### Completed contract and rewrite scaffolding

- `src/er_commons/corpus_extraction_contract/` and
  `benchmarks/er_bench/schemas/corpus_extraction/v1/records.schema.json`;
- `src/er_commons/cross_reference_materialization/`;
- `src/er_commons/canonical_extraction/comparison.py`;
- `src/er_commons/hierarchy_correction/rewrite_equivalence.py`;
- `src/er_commons/corpus_extraction/preservation.py` and the
  `offline_reference_candidate` path; and
- their historical-only tests, fixtures, configs, documentation references,
  CLI commands, Make targets, and production-identity entries.

### Proof machinery embedded in maintained stages

For semantic materialization, audit `reference.py`, `review.py`, lifecycle,
runtime, workflow, configuration, `mvp_reference_candidate_id`,
`reference_profile`, rewrite-review branches, and the mandatory second fresh
build. The maintained stage should build once, validate active invariants, and
publish once. Retain or relocate only the candidate-neutral review-cache and
semantic-comparison capability needed by Tasks 03G–04.

For cross-reference enrichment, audit `comparison.py`, `policy_correction`,
reference-candidate branches, reference IDs and checksums, comparison outputs,
and the mandatory second fresh build. Remove the separate
`cross_reference_contract` package only after every still-active invariant is
owned by `cross_reference_enrichment.validation` or another clearly named
active validator.

For hierarchy correction, audit the historical acceptance, evaluation, review,
and repeat-build family, including `bounded_acceptance.py`, `evaluation.py`,
`quality_*`, `review*.py`, `repeat_builds.py`, and historical producer/canonical
preservation checks. Current application imports make this a boundary rewrite,
not a blind deletion. Gate A must propose an explicit separation between direct
configured machine-publication policy, document-specific known-limitation
provenance, Task 03G's corpus-generalization test, and Task 04 human usability.
The Appendix P disposition may not silently become corpus-wide acceptance.

For table extraction, audit `comparison.py`, `comparison_relative_root`,
`comparison_scope`, comparison reports, and historical review derivative
switches. Preserve active table construction and validation; Task 03G owns any
selected repeat or review run at pilot scope. Preserve or relocate the generic
ability to render and compare page, table, table-family, and one-to-many region
mapping evidence needed by Tasks 03G–04.

### Completed exploratory document tooling

After relocating any helpers still used by the complete-document producer,
audit removal of `document_extraction/acceptance.py`, `comparison.py`,
`pipeline.py`, `reporting.py`, and `hierarchy_runner.py`, plus hierarchy
`artifact_normalization.py`, `controls.py`, `document_comparison.py`,
`process.py`, `report.py`, `run_comparison.py`, and `workflow.py`. Retain
hierarchy `document.py` and `specification.py` while active downstream callers
remain. Remove completed-task CLI and Make entrypoints for document review,
hierarchy evaluation, first-600 validation, and rewrite comparisons.

### Schema boundary

Audit removal of:

- corpus extraction v1 `records.schema.json`;
- canonical extraction v1 `review_cache.schema.json`; and
- hierarchy correction v1 `review.schema.json`, but only after its historical
  review workflow is removed.

Retain the schemas for canonical records v1, semantic structure v2,
cross-references v3, hierarchy-correction records v1, and corpus extraction
v1.1 only when the maintained pipeline or its declared downstream validation
surface requires them. No schema migration or archival validator is required
for superseded POC artifacts. A review-cache schema may be removed only after a
named replacement contract or deliberately schema-free manifest/recipe covers
the requested-render capability required by Tasks 03G–04.

## Plan / spec requirement

### Gate A — inventory and proposed boundary

Perform read-only import, caller, config, schema, CLI, Make, test, artifact, and
production-identity analysis. For every proposed deletion, record:

- current callers and imports;
- declared Task 03G, Task 03H, and Task 04 consumers;
- whether the surface is a production endpoint, internal owner boundary,
  pilot/review utility, or historical-only proof path;
- current artifact and production-identity consequences;
- active invariants or policies implemented there;
- the surviving owner of each required invariant; and
- the surviving owner of repeatability, independent handoff validation,
  machine observations, review-cache generation, and resource observations;
- source-specific constants or accepted-candidate assumptions that must not
  enter the generalized path; and
- exact fixed-evidence comparisons and tests that will prove preservation after
  cleanup.

Gate A must also freeze a no-PDF old/new comparison for every maintained stage
whose proof implementation will be deleted. The comparison must cover declared
semantic bytes or records, IDs, warnings, failures, reuse, invalidation, and
publication behavior. Its allowed-difference list is limited to refreshed
identity values and explicitly removed proof artifacts. Historical-only paths
may be deleted without equivalence or migration when the matrix proves that no
maintained or declared downstream capability depends on them.

Write the final removal matrix and simplified architecture proposal, inspect the
diff, and stop for explicit approval. Gate A may update this task contract and
documentation only. It may not delete code or schemas, change production
identity, run a PDF, or activate Task 03G.

### Gate B — approved cleanup

Only after separate approval, transfer still-required invariants into their
active owners, revise the hierarchy metrics schema for one honest production
build, simplify the maintained control flow, and remove the confirmed obsolete
surface as one integrated work effort. Use stage-sized internal diffs and run
focused validation after each responsibility boundary, but do not stop for
routine user approval between stages. Reconcile the complete change, run the
full authorized validation, inspect the final diff, and return one Gate B
result for review. Commit remains separately authorized.

Do not preserve compatibility aliases for deleted internal APIs without a
demonstrated current caller. Stop early only if implementation exposes a new
content-policy change, requires a published semantic change beyond the approved
one-build hierarchy metrics revision, needs a PDF or external-artifact run, or
cannot preserve an acceptance invariant through the frozen no-PDF comparisons.

## Gate A inventory and proposed boundary

### Outcome abstract

Gate A completed as a read-only caller, import, configuration, schema, command,
test, artifact, identity, and downstream-capability inventory. No PDF or
external artifact ran. No runtime code, schema, configuration, fixture, CLI,
Make target, or production identity changed.

The inventory supports destructive removal of most completed proof machinery,
but not blind deletion. Several apparently historical modules still sit in the
maintained call graph, candidate identity, or publication artifacts. Their
active invariants must first move to named current owners. The proposed end
state keeps `extraction run-document` and `extraction run-scope` as the only
public extraction orchestration endpoints, makes each document content stage
construct once, validate active invariants, and publish once, and moves selected
repeat comparison and requested review rendering behind candidate-neutral
Task 03G–04 utilities.

Hierarchy-correction v1 requires exactly three `fresh_wall_time_seconds` values
because repeatability was part of the completed proof workflow. The maintained
production path does not need to run every document three times: Task 03G owns
selected repeatability checks. By user direction, Gate B will revise this
measurement shape to record one honest production build, preserve the semantic
hierarchy record families and source-scoped Appendix P limitations, and then
remove the mandatory repeat-build branch. This schema revision is an explicit
allowed difference; it may not change hierarchy content policy.

### Maintained architecture proposal

The proposed production and independent-consumer flow is:

```text
extraction run-document
  -> document content owners
     -> construct once
     -> stage-local active validation
     -> completion-last, no-clobber publication or verified reuse
  -> document transaction completion plus attempt/resource observations

extraction run-scope
  -> exact terminal accounting
  -> sealed target index
  -> immutable cross-document resolutions
  -> candidate handoff

read-only validate-handoff
  -> v1.1 scope validation
  -> successful-document active schema and cross-record validation
  -> inventories, checksums, identity, immutability, and Task 04 status checks

Task 03G selected rerun/compare       Task 03G–04 requested review cache
  -> production entrypoints            -> candidate-neutral render recipe
  -> candidate-neutral comparison       -> disposable checksummed manifest
  -> resource aggregation               -> outside candidate completeness
```

Construction, active invariant validation, publication, and orchestration stay
separate responsibilities. `corpus_extraction` composes existing content owners
and validates their lineage; it does not absorb their extraction policy.
Candidate comparison never authorizes publication. Review rendering never
enters candidate identity or completeness. Task 03G's provisional review never
creates Task 04 reviewer, exclusion, usability, or document-disposition fields.

### Executable surface removal matrix

The classification applies to the named surface and its historical-only tests,
fixtures, configs, commands, Make targets, documentation references, artifact
roles, and identity entries unless a narrower exception is stated.

| Surface | Current caller or consequence | Classification | Surviving owner or prerequisite |
| --- | --- | --- | --- |
| `corpus_extraction_contract/`, corpus v1 schema and fixtures | Still imported by CLI validation, document preflight v1 fallback, document identity digest code, and v1.1 error handling | transfer invariant then remove | Move shared error/digest primitives to current owners, make preflight v1.1-only, and retain `corpus_extraction_contract_v1_1` plus its schema |
| `cross_reference_materialization/` | Self-contained MVP plus dedicated tests; no maintained production caller | remove | `cross_reference_enrichment` is the sole content owner; historical task outcomes retain the result |
| `canonical_extraction/comparison.py` | Dedicated rewrite-comparison tests only | remove | Active canonical construction and validation remain under `canonical_extraction` |
| `hierarchy_correction/rewrite_equivalence.py` | Dedicated rewrite-equivalence test and broad code inventory only | remove | Fixed-evidence Gate B comparison is its final temporary use |
| `corpus_extraction/preservation.py` and `offline_reference_candidate` | Called during successful document publication; emits `preservation_report.json` and changes candidate/control identity | transfer invariant then remove | Final-candidate source/lineage validation, managed-file inventory, checksums, completion seals, and verified reuse remain active; selected reruns move to Task 03G |
| Semantic frozen-reference branch: `reference.py`, reference profile/ID/checksums, rewrite-review output, second fresh build | Mandatory in current semantic workflow and identity | transfer invariant then remove | `semantic_materialization` construction, support, sealing, validation, publication, failure retention, and reuse |
| `semantic_materialization/review.py` and automatic ten-page review branch | Called by candidate lifecycle; rendering mechanics are reusable but the sample is Appendix-P proof | keep until named successor | Relocate to a candidate-neutral requested-render utility, then detach it from publication |
| Semantic baseline preservation comparison | Builds the active v1-to-v2 correspondence/preservation support | keep | `semantic_materialization.support` and active semantic validation |
| Cross-reference comparison, `policy_correction`, reference IDs/checksums, second build, comparison output | Mandatory in current cross-reference workflow and candidate identity | transfer invariant then remove | `cross_reference_enrichment` construction, active validation, publication, failure retention, and reuse; Task 03G owns selected comparison |
| `cross_reference_contract/` | Not called by production, but its validator owns rules not all duplicated by the maintained validator and is identity-bound | transfer invariant then remove | Move source eligibility, status/candidate consistency, deduplication, target-type, table-window, external-qualification, and same-page label-evidence checks to `cross_reference_enrichment.validation` |
| Hierarchy pure construction, records, schema/cross-record validation, identity, failure retention, and publication | Maintained content owner | keep | `hierarchy_correction` responsibility-owned construction and publication modules |
| Appendix P bounded-acceptance record and verifier | Current publication authority and semantic provenance for Appendix P only | keep | Preserve immutable source-specific known-limitation provenance and the source/authorization/semantic lineage join; never generalize its acceptance |
| Hierarchy repeat builds, evaluation, quality, held-out review, historical preservation, and review rendering | Directly imported by the maintained application; also identity-bound | transfer invariant then remove | Gate B revises repeat-derived measurements to one honest build, retains active machine validation/publication, and removes historical proof branches; Task 03G owns selected repeats and corpus-generalization, and Task 04 owns usability |
| Table comparison module and comparison config/report branches | Historical configs enable them; complete-document production explicitly disables comparison | transfer invariant then remove | Retain stable table evidence comparison as a candidate-neutral Task 03G utility, then remove it from `table_extraction` production |
| Table construction, cleanup, routing, families, parser evidence, zero-table mapping, unmatched-region observations | Maintained producer path and Task 04 machine observations | keep | `table_extraction` and complete-document producer validation |
| `document_extraction/{acceptance,comparison,pipeline,reporting,hierarchy_runner}.py` | Historical CLI flows; `producer_conversion` still imports two generic runtime helpers from `pipeline.py` | transfer invariant then remove | Relocate `offline_docling_environment` and `run_log` to maintained producer runtime, then remove completed Task 03A/03E flows |
| Hierarchy evaluation subpackage modules `artifact_normalization`, `controls`, `document_comparison`, `process`, `report`, `run_comparison`, `workflow` | Historical evaluator and review flows | transfer invariant then remove | Move any still-used render/text helpers first; retain `document.py` and `specification.py` only until their remaining active callers move |
| Historical document, hierarchy-evaluation, table-review, first-600, canonical, semantic, cross-reference, held-out CLI commands and corresponding Make targets | Executable completed-task workflows | remove | `extraction run-document`, `extraction run-scope`, current v1.1 validation, and the proposed read-only handoff/review utilities |

### Schema, fixture, and configuration matrix

| Surface | Classification | Reason and replacement |
| --- | --- | --- |
| Canonical records v1 schema | keep | Published canonical record families and Task 04 machine observations |
| Semantic structure v2 schema | keep | Published semantic sections, labels, aliases, bridge, and controls |
| Cross-references v3 schema | keep | Published mention, resolution, alias-extension, and support records |
| Hierarchy-correction records schema | revise then keep | Gate B changes the repeat-derived metrics to represent one honest production build while preserving semantic hierarchy families and validation |
| Corpus extraction v1.1 schema | keep | Maintained stage-two accounting/index/resolution/handoff validation and production identity |
| Corpus extraction v1 schema | transfer invariant then remove | Superseded executable contract; v1.1 becomes the only accepted runtime contract |
| Canonical review-cache v1 schema | keep until named successor | Remove only after a candidate-neutral review utility defines a deliberate schema-free manifest and recipe covering page, overlay, table, family, and one-to-many region evidence |
| Hierarchy review v1 schema | transfer invariant then remove | Gate B preserves active machine validation and source-scoped authorization, then removes the historical held-out/quality review contract |
| Cross-reference contract fixture | transfer invariant then remove | Convert its active negative/zero-result cases into tests of `cross_reference_enrichment.validation`; historical reference-candidate replay is unnecessary |
| Task 03F.2 v1 run spec and identity fixture | remove after v1 transfer | Superseded by the v1.1 non-executed identity and current run boundary |
| Appendix-P reference/comparison configs | transfer active policy then remove proof fields | Keep source identity, content policy, schema, and explicit source-scoped authority; remove candidate-reference IDs, comparison roots/profiles, fixed proof counts, and mandatory review/repeat controls from generalized production configs |

The production configuration may remain explicit per source. Source checksum,
page count, producer options, and an explicit hierarchy disposition are valid
data-driven inputs. Appendix-P candidate IDs, accepted-candidate checksums,
fixed observed counts, historical comparison roots, and fixed review pages are
not generalized production policy.

### Invariant transfer inventory

| Required invariant or capability | Current owner | Proposed surviving owner |
| --- | --- | --- |
| Raw Docling success, complete page accounting, structured-error failure | producer/document shell | unchanged producer validation plus `corpus_extraction` publication gate |
| Page/table/family construction, zero-table mapping, region evidence | table and complete-document stages | unchanged table/producer construction and validation |
| Canonical record shape, geometry, lineage, assets, inventory, completion | canonical stage | unchanged canonical validation and publication |
| v1-to-v2 undeclared-difference rejection and bridge/control support | semantic support/comparison | `semantic_materialization.support` plus `semantic_structure` active validation |
| Cross-reference source eligibility, spans, deduplication, namespace closure, target type, table-window/qualification/evidence, preservation | split between old contract and active validator | `cross_reference_enrichment.validation`, deriving expected alias coverage from sealed upstream input rather than the Appendix-P count 323 |
| Hierarchy construction semantics and cross-record integrity | hierarchy construction/validation | unchanged responsibility-owned hierarchy modules |
| Hierarchy publication authority | strict quality or Appendix-P bounded proof path | explicit configured machine-publication owner plus separate Appendix-P known-limitation provenance under the approved Gate B schema revision |
| Atomic, no-clobber, completion-last publication; retained failure; verified reuse/invalidation | each stage publication module | unchanged stage-local publication modules |
| Scope terminal accounting, sealed index, immutable resolution, handoff | v1.1 validator and corpus resolution | unchanged v1.1/current owners |
| Independent Task 03 candidate validation | internal stage validators plus fixture-only v1.1 command | candidate-neutral read-only `validate-handoff` surface that composes active document and v1.1 validators without rebuilding |
| Selected repeatability and semantic comparison | mandatory stage proof branches | Task 03G calls production endpoints and a candidate-neutral comparator; Task 03H repeats the frozen subset only |
| Machine observations | canonical/semantic/cross-reference records and attempt observations | unchanged published records plus read-only access; never a human registry |
| Resource observations | stage timings and attempt observability | `corpus_extraction.observability`, with pilot/full-scope aggregation owned by Tasks 03G/03H |
| Requested review-cache generation | fixed semantic/table/hierarchy proof flows | candidate-neutral render utility, invoked only for a frozen requested sample by Tasks 03G–04 |

### Declared downstream handoff

Task 03G needs the two production entrypoints, selected full-document repeats,
semantic/identity comparison over records, geometry, assets, indexes and
resolutions, attempt/resource observations, interruption/resume/failure
evidence, and requested sample renders. It does not need automatic comparison
or render branches inside every candidate build.

Task 03H needs the same production endpoints, the frozen Task 03G repeat
subset, exact terminal accounting, immutable stage-one candidates, the sealed
index and resolutions, integrity reports, and a Task 04 handoff path and render
recipe. It does not need historical candidate replay.

Task 04 needs a read-only verified candidate, failures and warnings, page-,
table-, family-, hierarchy-, label-, alias-, mention-, resolution-, mapping-,
asset-, and provenance-level observations, plus regenerable requested renders.
It independently writes the human usability registry. Task 03 artifacts remain
free of reviewer, review-date, exclusion, usability, and final document-
disposition fields, with `task04_status: not_evaluated` at handoff.

### Frozen no-PDF preservation matrix

Gate B must capture old outputs before each proof oracle is removed and run the
new path against the same fixed in-repository or already accepted no-PDF
evidence. Unless listed otherwise, comparisons are byte-exact after normalizing
only candidate/production identity values derived from the intentionally
changed owned-code inventory.

| Stage | Fixed evidence and comparison | Required equal behavior | Allowed differences |
| --- | --- | --- | --- |
| Document producer and table handoff | Synthetic complete-document/table roots, including zero-table and one-to-many region regimes | producer records, assets, table IDs/order/shapes/cleanup/families, mappings, warnings, failure, reuse, publication | deleted comparison/review reports and refreshed identity only |
| Canonical | Existing valid bundle and maintained materializer behavior tests | all canonical record bytes, IDs, geometry, assets, lineage, inventory, completion, failure, reuse/invalidation, publication | deleted rewrite-comparison artifact and refreshed identity only |
| Hierarchy | Existing fixed semantic input and both bounded/strict authority fixtures | eight semantic families, hierarchy, ambiguity/warning records, summary, completion, failure, reuse, publication, source-scoped authorization | refreshed identity, one-build metrics, and removed repeat/quality/review proof artifacts only |
| Semantic | Current frozen reference file-map comparator used once as oracle; generic independent-document and zero-result fixtures | canonical inherited bytes, semantic records, four support roles, warnings, failure retention, reuse/invalidation, completion-last publication | refreshed identity and deleted frozen-reference/rewrite-review/automatic-render artifacts |
| Cross-reference | Current behavioral-reference and policy-correction comparators used once as oracles; zero-alias and zero-mention regimes | remapped inherited records, aliases, mentions, resolutions, three support roles, warnings, failure, reuse/invalidation, completion-last publication | refreshed identity and deleted reference/comparison artifacts |
| Restartable document | Existing no-PDF imported candidate and synthetic source regimes | source selection, owner lineage, raw status, pages, errors, warnings, terminal disposition, managed files, checksum reuse, retained failures, completion-last publication | refreshed IDs and removed `preservation_report.json` only |
| Corpus scope | v1.1 positive/negative fixtures and fixed Task 03F.2 stage-one evidence | terminal accounting, identity, inventory, checksums, index, resolution, immutability, failures, handoff, `task04_status` | refreshed non-executed production identity and removal of explicitly obsolete v1/proof inputs only |

The comparison gate must include success, warning, explicit failure, matching
reuse, tamper invalidation, and publication collision/no-clobber behavior. At
least two synthetic source regimes remain required, including applicable zero-
table, zero-alias, and zero-mention cases. A historical-only package may skip
equivalence only after the caller matrix proves it has no maintained or
declared downstream consumer.

### Artifact and production-identity consequences

Removing reference comparisons, rewrite reviews, mandatory repeats, automatic
review renders, and offline preservation intentionally removes their reports
from new candidate managed-file sets. Existing external candidates and reports
remain immutable historical evidence; they are neither migrated nor rebound.
Review cache stays disposable and outside semantic identity.

The final Gate B identity refresh must enumerate all and only surviving
output-affecting code, schemas, specifications, and configuration. It must
remove corpus-v1, behavioral MVP, comparison, review, repeat-build, and offline-
preservation entries as their owners are removed. It must add any new active
validator or publication owner. The refreshed identity remains
`execution_status: not_executed`; it cannot claim a PDF run, Task 03G/03H
execution, Task 04 readiness, or acceptance, and it cannot rebind an old
candidate.

### Integrated Gate B execution plan

If separately activated, Gate B proceeds through this complete sequence without
routine user approval between items. Each item is an internal validation
boundary, not a new task or authorization gate:

1. freeze the old no-PDF comparison oracles and add candidate-neutral comparison
   and read-only handoff-validation boundaries;
2. transfer corpus-v1 primitives to v1.1/current owners, then remove v1;
3. simplify semantic and cross-reference workflows one stage at a time and
   transfer the old cross-reference contract invariants;
4. revise hierarchy metrics for one production build, preserve active machine
   validation and Appendix P's source-scoped limitations, remove mandatory
   repeat/quality/review branches, and run the focused hierarchy comparison;
5. relocate requested-render and table-comparison capabilities, then remove
   automatic/historical CLI, Make, config, and document-tooling paths;
6. remove the offline preservation oracle after its fixed comparison;
7. refresh the exact non-executed production identity and documentation; and
8. run the complete validation suite, inspect the integrated diff, and return
   the finished Gate B result for one user review.

Gate B was explicitly activated and completed as one integrated effort. The
outcome below was returned for user review before acceptance or Task 03G
revision and was later accepted after the pre-close maintainability pass.

## Gate B outcome

The maintained production path now has two public orchestration endpoints:
`extraction run-document` and `extraction run-scope`. Document content stages
construct once, run their active stage validators, and publish once or
checksum-verify reuse. `extraction validate-handoff` independently verifies a
published v1.1 scope and its successful document candidates without rebuilding.

Active invariants were transferred before deletion. Corpus v1 error and digest
primitives moved into v1.1, document preflight is v1.1-only, and final-candidate
lineage/inventory/completion verification replaces the offline preservation
report. Cross-reference eligibility, resolution consistency, namespace,
target-type, table-window, external-qualification, same-page label-evidence,
support, preservation, and zero-result rules now belong to the active
enrichment validator, with upstream alias coverage derived from sealed input.

Hierarchy correction now records one `build_wall_time_seconds` value and uses
direct machine validation as the general publication authority. Appendix P's
bounded authorization remains an independent, checksummed source/candidate/
semantic-lineage join with `corpus_wide_acceptance: false`. Semantic and
cross-reference stages each build once and no longer contain behavioral-
reference, policy-correction, mandatory second-build, or automatic-render
branches.

Removed executable archaeology includes corpus v1, the old cross-reference
contract and MVP materializer, canonical/hierarchy rewrite comparators,
hierarchy repeat/quality/held-out review machinery, exploratory document flows,
table comparison branches, automatic review paths, completed-task commands,
proof-only configs/schemas/fixtures/tests, and offline preservation. Historical
outcomes remain in completed task records; existing external artifacts were not
migrated or rebound.

Tasks 03G--04 retain candidate-neutral comparison and requested-render support
through `extraction_review`, machine observations through the surviving content
records, attempt/resource observations through corpus extraction, and read-only
handoff validation through corpus resolution. Review manifests remain disposable
and outside candidate identity and completeness.

The initial Gate B production identity was
`exv1-39318d511aac5fe99f6c329668d4386d0a6452acc0180b1a16bcc409dd8d9587`
with `execution_status: not_executed`. It does not rebind a candidate or claim a
PDF run, Task 03G/03H execution, Task 04 readiness, or usability acceptance.

### Post-Gate B live-run review

After the integrated result was returned for review, the user authorized one
complete Appendix P attempt. That review found that Gate B had removed the only
concrete document run spec while retaining a public command that requires one.
A refreshed Appendix P run spec was added and passed production-identity,
source, storage, and resource preflight.

The live transaction then exposed a deeper lineage defect. Current producer
code derives baseline producer
`prv1-c444abe10edab88d92805dddcf57618175d35a17301980e9791c779ba868b4e8`
and hierarchy producer
`prv1-6ea3003b68aa7893d23de618d81b4d24f8b449c8f8eeb5028eb382d9ca60671e`,
while downstream configs still pin historical producer IDs. Current hierarchy
code/config likewise derives
`hcorv1-3171ff0ed1e9ee53b79e387811558c6cda2bf4a5016aca769a4de4361a7b6a7e`,
but the source-scoped bounded evidence authorizes the historical candidate and
a different correction-config checksum. The current orchestration checks these
joins only after expensive owners run.

The first document transaction was stopped and recovered through the workflow
as `cancelled` with no document completion path. Its baseline producer had
finished publication immediately before cancellation and verifies as
`prv1-c444abe10edab88d92805dddcf57618175d35a17301980e9791c779ba868b4e8`.
The separately run hierarchy producer subsequently verified as
`prv1-6ea3003b68aa7893d23de618d81b4d24f8b449c8f8eeb5028eb382d9ca60671e`,
and refreshed canonical candidate
`exv1-ec1e39edd9289787e6c3523d6f1030bbc720aee2bd45757fd9c9d16485810954`
published from the new baseline seal.

The correction also restored the accepted semantic-file digest algorithm;
the historical candidate again verifies as `75a0e36c...dd3d2`. A fresh
deterministic build against the new hierarchy producer derives candidate
`hcorv1-c73d6bb800060269ccc1ecd57352e14943f53cf0d90085dc590442618d80cd88`
and exactly matches accepted aggregate semantic digest `c3036210...4db8` and
all accepted counts. Candidate-neutral review record
`pipelines/brisbane_baylands/review_cache/hcorv1-c73d6bb800060269ccc1ecd57352e14943f53cf0d90085dc590442618d80cd88/hierarchy_authorization_review.json`
has SHA-256 `936d1b5ac6719bb5d62d3cadcdf765321f1fe1f4557698350d8007bef6386323`,
status `ready_for_user_review`, and `publication_authority: false`.

The user separately approved that exact candidate-specific rebind. Candidate
`hcorv1-c73d6bb800060269ccc1ecd57352e14943f53cf0d90085dc590442618d80cd88`
then published under a new source-scoped bounded acceptance without expanding
its authorized uses or setting `corpus_wide_acceptance`. A transitive producer
lineage report proved both refreshed producer outputs equivalent to the pair
used by the earlier accepted comparison, with runtime and identity fields
explicitly excluded from the semantic comparison.

The downstream refresh published semantic candidate
`exv1-f83a030b8a03d1299aab36bd8b21d2a93e49c87c203a8e491b9edd62495e173b`
and cross-reference candidate
`exv1-6dc03aee38f32553eb5f1c52dd9c556e932744e2fd90a84ce4c1378e1b223247`.
The latter exposed and corrected transferred validator assumptions that were
incompatible with the accepted multi-target alias and table-window behavior.
Final production identity
`exv1-5874cac422760759b2f2f8757fff1f950b6e4da90d0878d64993d83633c5c7ac`
is bound to the corrected code and contracts. The user-authorized Appendix P
transaction completed all 222 pages as document candidate
`docv1-c7160cdcaa44b4592b1c20a780738dc5a761e30c2d9dd631dd58c8a9fe188fb0`;
a second invocation checksum-reused that completion in four seconds.

### Pre-close maintainability pass

The final code-quality review found and corrected responsibility, fail-closed,
lineage, schema, diagnostics, validation-policy, and review-recipe weaknesses.
Publication now requires exactly six stage seals and binds the final imported
root to the contained cross-reference completion. Parent and child processes
share a checksummed execution-preflight snapshot; config changes and all
available producer, candidate, authorization, and downstream checksum joins are
rejected before content owners begin. Stage-qualified start, completion, and
failure events preserve useful timing and error context.

Hierarchy publication no longer creates missing bounded authorization. Semantic
handoff values now come from configured, checksummed evidence composed through
the maintained hierarchy verifiers; the semantic code and schema no longer
duplicate Appendix P candidate IDs, digests, paths, counts, or authorization
values. Cross-reference construction and validation share one policy owner,
reject exact duplicate index rows, preserve multi-target aliases, and retain
failure context. Requested review manifests now identify an external renderer,
checksummed inputs, and exact page/evidence mappings without claiming a renderer
was executed.

Because hierarchy candidate identity includes the changed owned code, current
code/config derives
`hcorv1-30385014eb61a4f8acb39f763e3f7a90b1ead92632db3d37b541b8d2f721ad42`
rather than the authorized `hcorv1-c73d6bb8...cd88`. The new fail-fast lineage
gate rejected that stale join before PDF work. The separately authorized
candidate-specific review then matched the accepted semantic digest and every
count exactly; only `candidate_id` and `code_bundle_sha256` changed. Review SHA
`5fa5326f9f7b8d59a9a6038e74c101dd5022cc3be55848aac89aa19aa1a9ff97`
remained non-authoritative. After the user's separate approval, bounded
authorization SHA
`37ffb6de52c80349ec833295830766cec55454ff252e34842623728f20ab9527`
published without expanding scope or limitations.

The refreshed semantic candidate is
`exv1-89a577776954c2f181f873ce8b23cf92004fc14c607759253138d6a68178f6c4`;
the refreshed cross-reference candidate is
`exv1-1da64e0873d2215fba267fb4dfb792fbd419bc76cb80138407bf554f40021509`.
Final non-executed production identity
`exv1-1bd71e02e9f8da505d68bfb58b8dd8d4c1b47aabc8365417028d6daf60c1fcc4`
binds the corrected implementation and contracts. All six document owners
checksum-reused their sealed completions; the resulting 222-page candidate is
`docv1-532b14da43a341a8785166d70613b796872c6bb55d1f12b2a78bb78ad668df40`,
with completion SHA
`ebb4697f92f7d0241159ca456feeeaf803ec76f7868fecaf7a404ddc1c64eb7e`.
A second document invocation checksum-reused it in 0.98 seconds. No PDF ran.
Final validation passed `make fix`, `make validate-extraction-contract`,
`make check` with 396 tests, and `git diff --check`.

Deletion was based on behavioral ownership rather than import reachability:
executable history costs maintenance even when rarely called, while an import
search alone cannot prove that publication, failure, or downstream-review
invariants have a surviving owner. Repeatability is therefore a bounded pilot
control for Task 03G instead of a semantic requirement imposed on every
production candidate.

## Research / learning checkpoint

Use the Python packaging and dependency tools already present in the repo to
distinguish import reachability from behavioral ownership. Explain in the
outcome why executable history creates maintenance cost, why deletion requires
an invariant inventory rather than only an import search, and why repeatability
is better expressed as a bounded pilot control when it is not part of every
production artifact's semantic contract.

## Review pass

Review the proposed final architecture through five lenses:

- **human ownership:** a reader can locate construction, validation,
  publication, and orchestration without following historical branches;
- **behavior:** accepted output policy and failure/restart semantics remain
  unchanged;
- **downstream handoff:** Tasks 03G–04 can repeat selected runs, inspect machine
  observations, independently validate a candidate, and generate requested
  review evidence without restoring deleted archaeology;
- **artifact contract:** every surviving schema and identity input has a current
  producer or consumer, while superseded POC contracts may be deleted without
  migration; and
- **operability:** CLI, Make, config, logging, and tests expose only workflows
  intended for future use.

## Validation

Gate A uses read-only import/caller searches and `git diff --check`.

Gate B must run:

```bash
make fix
make validate-extraction-contract
make check
git diff --check
```

Run the frozen no-PDF old/new comparisons before removing each required oracle,
then add focused behavior tests where an invariant changes owners. Keep active
runtime and contract tests; remove tests whose sole purpose is replaying a
deleted MVP, reference candidate, historical comparison, or rewrite gate. Test
at least two synthetic source regimes, including applicable zero-table,
zero-alias, or zero-mention cases. No PDF or external artifact execution is
authorized.

## Acceptance criteria

- The removal matrix accounts for current and declared future callers,
  invariants, capabilities, artifacts, verification, and identity effects before
  any deletion.
- `extraction run-document` and `extraction run-scope` are the clear public
  orchestration path, backed by named current content owners.
- The maintained path builds each document stage once, validates active
  invariants, and publishes. Named candidate-neutral interfaces remain for Task
  03G's selected reruns and semantic comparisons and for Tasks 03G–04 requested
  review renders.
- No import, config, schema reference, CLI command, Make target, identity entry,
  or test names deleted code or obsolete proof fields.
- The executable schema set exactly matches artifact types the maintained
  pipeline can publish or must validate for Tasks 03G–04; superseded POC schemas
  and validators need not remain executable or migrate historical artifacts.
- Accepted content policy, restartability, immutability, failure evidence, and
  publication behavior pass the frozen no-PDF comparisons and remain covered by
  current behavior tests.
- The production path contains no Appendix-P IDs, fixed observed counts,
  accepted-candidate IDs, or source-specific paths outside fixtures or explicit
  history/configuration evidence.
- A read-only maintained validation surface can verify a Task 03 candidate's
  terminal accounting, identities, inventories, checksums, cross-record
  integrity, stage immutability, index, resolutions, and
  `task04_status: not_evaluated` without rerunning the producer.
- Task 03 still exposes source failures and page-, table-, table-family-,
  hierarchy-, label-, alias-, mention-, resolution-, warning-, and provenance-
  level machine observations required by Task 04. Reviewer, review-date,
  exclusion, usability, and document-disposition fields remain absent from Task
  03 artifacts, and provisional Task 03G review cannot impersonate Task 04.
- The refreshed production identity covers all and only current output-
  affecting code and contracts and remains `execution_status: not_executed`.
  It does not rebind old candidates, claim Task 03H execution, create a Task 04
  input, or imply usability acceptance.
- Documentation describes current architecture and keeps historical detail in
  task outcomes rather than executable compatibility paths.
- No PDF, Task 03G pilot, Task 03H run, or Task 04 acceptance occurs.
- The outcome stops for explicit approval before Task 03G activation.

## Non-goals

- changing extraction, hierarchy, table, semantic, or cross-reference policy;
- changing published record shapes without a separately identified blocking
  defect, except for the explicitly approved one-build hierarchy metrics
  revision;
- migrating superseded schemas or preserving executable replayability for old
  POC candidates;
- running a real source, smoke, representative pilot, or full corpus;
- optimizing model performance or adding OCR/figure linking;
- retaining unused internal APIs for historical reproducibility; or
- activating Task 03G, Task 03H, or Task 04.
