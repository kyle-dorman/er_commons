# Task 03F.1: Define the Restartable Corpus Extraction Contract

Status: **active as of 2026-08-03**. Begin with Gate A only. Do not implement,
delete runtime code, or run source PDFs before the required approvals.

## Abstract

Inventory the accepted document pipeline and freeze the machine contract for a
restartable two-stage corpus workflow. Identify every Appendix-P-specific
runtime constraint, obsolete implementation, and missing corpus abstraction.
Then define identities, state transitions, artifact layouts, cache keys,
failure behavior, target-index sealing, immutable cross-document resolution,
and bounded validation before production code changes.

## Goal

Give Task 03F.2 and Task 03F.3 a complete, reviewable contract that a new agent
can implement without guessing what constitutes completion, reuse, failure,
corpus identity, or accepted Task 03E.5 behavior.

## Inputs

- accepted Tasks 03C.1 and 03D.1 implementations and immutable candidates;
- Task 03E.2d's Appendix-P-only correction candidate and bounded-acceptance
  record;
- accepted Task 03E.3 semantic schema/validator and Task 03E.4 human-owned
  materializer;
- accepted Task 03E.5 pattern-policy-v2 candidate
  `exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`
  and the `cross_reference_enrichment` production implementation;
- the sealed Task 02 manifest and exact ordered 35-record `model_corpus` scope;
- current CLI, configuration, identity, publication, validation, and artifact
  code for every stage; and
- `docs/architecture.md`, `docs/data_artifacts.md`, and maintained Docling
  guidance for batch conversion, statuses, timeout, batching, profiling, and
  accelerator behavior.

The earlier `cross_reference_materialization` package and behavioral MVP
candidates are historical reference evidence, not accepted downstream
production owners.

## Outputs

- a Gate A read-only coupling and deletion inventory;
- a checked-in two-stage workflow specification after Gate A approval;
- executable schemas and small valid/invalid fixtures for state, completion,
  accounting, target-index, resolution, and handoff records;
- an exact production `extraction_id` preimage and subordinate identity model;
- a stage-by-stage cache and invalidation table;
- a relative external-artifact layout added to `docs/data_artifacts.md`;
- an architecture update naming responsibility owners and immutable boundaries;
- exact CLI/Make interfaces for fixture validation, an optional bounded
  engineering smoke, Task 03G, and Task 03H; and
- revised provisional Task 03F.2 and Task 03F.3 contracts grounded in the
  accepted specification.

## Gate A — read-only implementation and coupling inventory

Inspect, but do not edit or execute, the current producer, core
canonicalization, hierarchy correction, semantic materialization, and
cross-reference commands. Report:

1. which components already accept a manifest-selected document;
2. every frozen Appendix P source ID, checksum, page count, candidate ID,
   review sample, mapping name, CLI description/default, or output path;
3. which constraints are accepted policy versus pilot-only scaffolding;
4. duplicated MVP/reference and human-owned implementations, their live
   callers, identity role, tests, and deletion eligibility;
5. the smallest stable responsibility interfaces needed by stage one;
6. current atomic-publication, completion-last, reuse, and retained-failure
   behavior that must be preserved;
7. missing state, corpus-index, second-pass, and accounting contracts; and
8. a proposed file-level keep/generalize/delete plan.

Stop for explicit user approval before writing the specification, schemas,
fixtures, architecture/data-artifact changes, or provisional implementation
contracts. Gate A does not authorize code deletion or a PDF run.

## Gate B — checked-in contract

After Gate A approval, freeze:

1. **Identity:** the complete production `extraction_id` preimage over the
   ordered 35-source manifest scope, parser/model/configuration, schemas,
   hierarchy policy, Task 03E.5 policy, and owned code; subordinate fixture,
   smoke, pilot, producer-run, transaction, and candidate identities cannot
   impersonate it.
2. **Stage one:** states, permitted transitions, temporary/final paths,
   completion-last publication, interruption behavior, retry classes, and
   verification required for reuse.
3. **Scope:** a complete PDF is the source transaction. Synthetic page subsets
   are fixtures; a real first-N-page run is explicitly incomplete and cannot
   publish a document completion record.
4. **Accounting:** run-scope accounting is exact for the declared scope. Task
   03F fixtures and any smoke account only for their subordinate scope; Task
   03H alone requires 35 terminal source records.
5. **Target index:** eligible terminal stage-one inputs, collision behavior,
   deterministic ordering, sealing, validation, and invalidation.
6. **Second pass:** stable mention references, target evidence, candidate
   ordering, ambiguity, missing/failed-target reasons, output paths, and the
   byte-level no-mutation invariant.
7. **Handoff:** separate document completion, scope accounting, index
   completion, resolution completion, candidate handoff, and Task 04 freeze.
8. **Resources:** bounded concurrency, page batching, threads, device, queues,
   memory, storage, timeout, cancellation, and retry policy.
9. **Observability:** structured progress, timing, resource, warning, error,
   and heavy-tail summaries.
10. **Removal:** exact proof required before deleting Appendix-P-only or
    superseded code, and exact Appendix P preservation required after
    generalization.
11. **Commands:** fixture-only validation, optional smoke, Task 03G pilot, and
    Task 03H full-run entrypoints with no ambiguous default that silently
    selects Appendix P.

Stop for explicit user approval after the checked-in contract and focused
contract tests pass. Gate B approval activates the revised Task 03F.2 only; it
does not authorize Task 03F.3, a real-source smoke, Task 03G, or Task 03H.

## Bounded-input guidance

Prefer synthetic multi-document fixtures for interruption, retry, invalidation,
missing targets, alias collisions, and second-pass tests. If implementation
confidence later requires real inputs, propose no more than two small sealed
model-corpus PDFs and process every page of each. Selection, expected cost, and
the exact command require separate approval. The smoke tests integration only;
heterogeneous adequacy and configuration acceptance belong to Task 03G.

## Research / learning checkpoint

Use maintained primary documentation for Docling batch/status/resource APIs
and the standard-library or currently adopted package behavior that materially
constrains the design. Explain why document-level transactions, content-bound
cache keys, immutable stage joins, and separate accounting/handoff records fit
this local 35-document workload better than page checkpoints or a workflow
engine.

## Validation

- Validate every new schema against its valid fixture and declared negative
  mutations.
- Verify the identity fixture changes when any bound semantic input changes.
- Verify illegal state transitions and premature completion/index/handoff
  claims fail.
- Verify first-N real-source state cannot satisfy document completion.
- Verify fixture/smoke scope cannot satisfy 35-source production accounting.
- Verify Task 03E.5 local mention status remains immutable under second-pass
  fixture records.
- Inspect the documentation diff and run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- A future agent can implement Tasks 03F.2–03F.3 without inventing identity,
  lifecycle, cache, failure, artifact, resource, or resolution semantics.
- The keep/generalize/delete inventory distinguishes accepted policy from
  Appendix-P pilot scaffolding and historical reference code.
- The contract pins the accepted Task 03E.5 candidate and policy exactly.
- The 35-source production identity is defined without pretending Task 03F
  executed or terminally accounted for those sources.
- Whole-document bounded validation is distinct from Task 03G's representative
  pilot and Task 03H's full run.
- No runtime implementation or source-PDF execution occurs.
- The outcome requests explicit user approval before Task 03F.2 activation.

## Non-goals

- runtime generalization or code deletion
- producer, semantic, or cross-reference execution
- selecting or running the representative Task 03G pilot
- executing or accounting for the full 35-source corpus
- changing hierarchy, mention, table, or figure-linking policy
- accepting Appendix P's correction behavior corpus-wide
