# Task 03F.4: Prune Extraction Proof Scaffolding and Firm Boundaries

Status: **provisional — contract drafted, not active**. Review and explicit
approval are required before implementation. Task 03G remains inactive until
this task is accepted.

## Abstract

Remove executable archaeology left by completed extraction experiments and
rewrite gates, then make the maintained source-to-corpus path obvious to a
human reader. Preserve accepted behavior and current data contracts, but stop
shipping old candidates, comparison branches, replay workflows, schemas, CLI
commands, and configuration fields that have no future caller. This is a
code-and-contract cleanup only: it does not run a PDF, change extraction policy,
or execute Task 03G.

## Goal

Enter Task 03G with one readable production path for each extraction stage,
one active schema per published artifact type, and explicit boundaries between
content construction, validation, publication, and optional pilot-level
reproducibility checks. Historical outcomes remain documented in completed task
records; their obsolete executable implementations do not remain in the repo.

## Inputs

- the accepted Task 03C.1 through Task 03F.3 human-owned implementations and
  their current public interfaces;
- `extraction run-document` and `extraction run-scope` as the intended
  orchestration boundaries;
- the active canonical v1, semantic v2, cross-reference v3, hierarchy-
  correction v1, and corpus-extraction v1.1 contracts;
- completed task outcomes as non-executable historical evidence;
- current imports, configs, tests, Make targets, CLI commands, schemas, and the
  production-identity owned-code/artifact inventory; and
- the user decision that selected repeatability and review execution belongs in
  Task 03G, not in every maintained document candidate.

## Outputs

1. A checked-in, read-only caller and artifact inventory classifying every
   candidate below as `keep`, `transfer invariant then remove`, or `remove`,
   with the exact active replacement named.
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
6. A short outcome inventory recording what was removed, what remains, and why.

## Candidate removal inventory

The inventory step must verify these candidates rather than treating this list
as deletion authorization.

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
publish once.

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
not a blind deletion. The accepted Appendix P known-limitation disposition must
become direct configured production policy rather than a replay of the old
acceptance workflow.

For table extraction, audit `comparison.py`, `comparison_relative_root`,
`comparison_scope`, comparison reports, and historical review derivative
switches. Preserve active table construction and validation; Task 03G owns any
selected repeat or review run at pilot scope.

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
v1.1 unless the inventory proves a current published artifact requires another
schema.

## Plan / spec requirement

### Gate A — inventory and proposed boundary

Perform read-only import, caller, config, schema, CLI, Make, test, artifact, and
production-identity analysis. For every proposed deletion, record:

- current callers and imports;
- artifact and schema identity consequences;
- active invariants or policies implemented there;
- the surviving owner of each required invariant; and
- exact tests that will prove preservation after cleanup.

Write the final removal matrix and simplified architecture proposal, inspect the
diff, and stop for explicit approval. Gate A may update this task contract and
documentation only. It may not delete code or schemas, change production
identity, run a PDF, or activate Task 03G.

### Gate B — approved cleanup

Only after separate approval, transfer still-required invariants into their
active owners, simplify the maintained control flow, and remove the confirmed
obsolete surface. Work in stage-sized commits or reviewable diffs so active
behavior can be checked after each boundary change. Do not preserve compatibility
aliases for deleted internal APIs without a demonstrated current caller.

## Research / learning checkpoint

Use the Python packaging and dependency tools already present in the repo to
distinguish import reachability from behavioral ownership. Explain in the
outcome why executable history creates maintenance cost, why deletion requires
an invariant inventory rather than only an import search, and why repeatability
is better expressed as a bounded pilot control when it is not part of every
production artifact's semantic contract.

## Review pass

Review the proposed final architecture through four lenses:

- **human ownership:** a reader can locate construction, validation,
  publication, and orchestration without following historical branches;
- **behavior:** accepted output policy and failure/restart semantics remain
  unchanged;
- **artifact contract:** every surviving schema and identity input has a current
  producer or consumer; and
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

Add focused behavior tests where an invariant changes owners. Keep active
runtime and contract tests; remove tests whose sole purpose is replaying a
deleted MVP, reference candidate, historical comparison, or rewrite gate. No
PDF or external artifact execution is authorized.

## Acceptance criteria

- The removal matrix accounts for callers, invariants, artifacts, verification,
  and identity effects before any deletion.
- `extraction run-document` and `extraction run-scope` are the clear public
  orchestration path, backed by named current content owners.
- The maintained path builds each document stage once, validates active
  invariants, and publishes; selected reruns and review renders are deferred to
  Task 03G.
- No import, config, schema reference, CLI command, Make target, identity entry,
  or test names deleted code or obsolete proof fields.
- The executable schema set exactly matches artifact types the maintained
  pipeline can publish or currently validate.
- Accepted content policy, restartability, immutability, failure evidence, and
  publication behavior remain covered by current behavior tests.
- The refreshed production identity covers all and only current output-
  affecting code and contracts and remains `execution_status: not_executed`.
- Documentation describes current architecture and keeps historical detail in
  task outcomes rather than executable compatibility paths.
- No PDF, Task 03G pilot, Task 03H run, or Task 04 acceptance occurs.
- The outcome stops for explicit approval before Task 03G activation.

## Non-goals

- changing extraction, hierarchy, table, semantic, or cross-reference policy;
- changing published record shapes without a separately identified blocking
  defect;
- running a real source, smoke, representative pilot, or full corpus;
- optimizing model performance or adding OCR/figure linking;
- retaining unused internal APIs for historical reproducibility; or
- activating Task 03G, Task 03H, or Task 04.
