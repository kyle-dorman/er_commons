# Task 03E.0: Rewrite Hierarchy Evaluation for Human Ownership

Status: **complete 2026-07-30; human-owned rewrite is exactly equivalent to
the frozen Task 03E machine evidence**.

## Abstract

Replace the completed Task 03E MVP evaluator with readable, typed,
responsibility-specific code that a maintainer can understand, edit, test,
debug, and explain without tracing a machine-oriented comparison module.
Treat the existing implementation and published Task 03E evidence as an
immutable behavioral reference.

This is a maintainability rewrite, not a hierarchy-policy revision. Preserve
the accepted Appendix P producer candidate, comparator semantics, independent
scratch-repeat gate, controls, CLI, report evidence, and Task 03E rejection.
Do not implement the deterministic correction layer owned by Tasks 03E.1 and
03E.2.

## Goal

Make the hierarchy evaluator's public flow read as a short sequence of named
stages. Give document comparison, artifact comparison, scratch execution,
controls, report construction, and publication clear owners. Use named types
at trust and stage boundaries, and make failures identify the artifact,
invariant, expected value, and actual value that caused them.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/documentation.md`
- `tasks/sprint2/03e_evaluate_docling_heading_hierarchy.md`
- the current Task 03E implementation and passing test baseline
- the completed Task 03E producer candidate:

```text
pipelines/brisbane_baylands/task_03c_complete_document/
  prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1/
```

- the completed Task 03E comparison evidence:

```text
pipelines/brisbane_baylands/task_03e_hierarchy_review/
  cmpv2-9106e5d03fa4f1e8f57eadd2b1aa8cc0a02030131f9684964caf6bea86f3aff0/
```

## Outputs

Tracked:

```text
src/er_commons/document_extraction/hierarchy/
src/er_commons/document_extraction/hierarchy_runner.py
tests/test_hierarchy_*.py
tasks/sprint2/03e0_rewrite_hierarchy_evaluation.md
docs/architecture.md
```

The published producer candidate and comparison evidence remain immutable.
If live comparison evidence is needed, write it under a new implementation-
bound comparison identity rather than altering Task 03E evidence.

## Research / learning checkpoint

Use a functional-core/application-shell boundary:

- Pydantic models validate untrusted JSON configuration;
- frozen dataclasses name verified paths, comparison results, and run state;
- pure functions compare one document or one artifact concern;
- subprocess execution and filesystem publication stay explicit edge
  operations;
- the public runner sequences stages without containing their implementation;
- tests target observable responsibility boundaries instead of copying private
  algorithms.

The plain-language lesson is that maintainability comes from visible
ownership, not merely shorter functions. A maintainer should know where to
change one comparison rule, where to inspect one scratch failure, and where a
report field is assembled without searching unrelated process and file code.

## Rewrite contract

1. Preserve the accepted source, baseline producer, hierarchy-enabled producer,
   frozen configuration, producer identity, candidate bytes, and Task 03E
   accept/reject outcome.
2. Preserve item pairing, allowed label transition, hierarchy metadata,
   numbering, reference-preservation, warning, asset, page, table, and
   completion comparisons.
3. Preserve the independent-process scratch-repeat gate. Scratch results must
   be compared as independently serialized artifacts, not as two objects from
   one process.
4. Preserve both fixed main-report diagnostic ranges and their independent
   comparisons with the accepted Task 03A artifacts.
5. Keep one public hierarchy-evaluation command and Make target.
6. Split the 867-line comparison module by domain responsibility. No
   replacement production module may become another multipurpose monolith.
7. Replace cross-stage dictionaries and broad `Any` values with named typed
   state where values are not intentionally arbitrary JSON.
8. Keep persisted JSON shapes explicit and stable. Do not introduce an object
   framework, plugin registry, workflow engine, inheritance hierarchy, or
   dependency-injection container.
9. Make report construction declarative and centralize stable status and
   diagnostic vocabulary.
10. Keep atomic no-clobber publication, completion-last behavior,
    checksum-verified reuse, and retained failure evidence.
11. Add focused tests for comparison policy, scratch independence, controls,
    report construction, and failure diagnostics.
12. Do not add correction features, visible-TOC reconciliation, learned
    inference, an LLM runtime dependency, or semantic materialization.

## Equivalence gate

Use the published Task 03E report and artifacts as the reference. Require:

- identical paired-item, label-transition, hierarchy-change, numbering,
  reference, warning, page, table, asset, and file-inventory conclusions;
- identical pass/fail decisions for producer preservation, scratch
  repeatability, and both fixed main-report controls;
- identical mismatch paths and diagnostic facts for the frozen successful run
  after normalizing only implementation identity, paths, timestamps, and
  timings;
- focused failure tests proving that stable-key collisions, changed geometry,
  changed semantic parents, and any failed independent evidence surface still
  produce the appropriate diagnostic or rejection;
- no modification to either published reference directory.

If the rewrite changes an undeclared semantic conclusion, stop and preserve the
mismatch for user review rather than declaring the task complete.

## Validation

- inspect module sizes, public names, imports, docstrings, and top-level flow;
- run focused hierarchy evaluator tests;
- run the evaluator equivalence test against frozen Task 03E evidence;
- run `make fix`, `make check`, and `git diff --check`;
- verify the published producer candidate and comparison evidence remain
  unchanged;
- inspect the final diff for accidental Task 03E.1 correction behavior.

## Review pass

- **Readability:** can a maintainer follow configuration, verification,
  comparison, controls, report publication, and final decision from the public
  runner?
- **Editability:** does each comparison policy have one obvious owner?
- **Debuggability:** do failures name a document or artifact, JSON path or
  file, invariant, expected value, and actual value?
- **Type boundaries:** are configuration, verified inputs, comparison results,
  scratch results, and persisted reports distinguishable?
- **Behavior preservation:** does the gate compare detailed conclusions rather
  than aggregate counts alone?
- **Scope:** is hierarchy correction still absent and Task 03E.1 inactive?

## Acceptance criteria

- The current machine-oriented evaluator is replaced by cohesive,
  responsibility-specific modules with a short public runner.
- No production module serves as a replacement monolith.
- Untrusted configuration and internal verified state have clear typed
  boundaries.
- Focused tests exercise successful and diagnostic failure paths.
- The complete project check passes.
- The refactored evaluator is semantically equivalent to the published Task
  03E evidence under the declared normalization.
- The published Task 03E producer and comparison directories remain unchanged.
- Documentation routes future work through the human-owned evaluator before
  Task 03E.1.

## Non-goals

- changing Task 03E's hierarchy policy, thresholds, review result, or evidence;
- modifying or rerunning the accepted producer candidate;
- implementing Tasks 03E.1 through 03E.5;
- adding TOC reconciliation, correction rules, semantic sections,
  cross-references, OCR, VLM, LLM, or learned runtime behavior;
- changing canonical extraction schemas or the accepted Task 03D.1 candidate;
- committing or pushing changes unless separately requested.

## Outcome

Task 03E.0 is complete. The four MVP evaluator modules are replaced by the
responsibility-specific `document_extraction/hierarchy/` package. The stable
`hierarchy_runner.py` facade preserves the public CLI import while the
application flow now reads as prepare evaluation, obtain primary candidate,
obtain independent repeat candidate, build three machine-evidence surfaces,
write the report, publish only after a passing gate, and checksum-verify
normal reuse.

The former 867-line mixed comparison module no longer exists. Its
responsibilities now have named owners:

- `specification.py` validates the frozen evaluation contract;
- `document.py` owns stable Docling indexing and semantic reference
  normalization;
- `document_comparison.py` owns hierarchy-only comparison and human-review
  rows;
- `artifact_normalization.py` owns declared volatility and identity
  projections;
- `run_comparison.py` owns complete producer-inventory comparison;
- `process.py` owns independent interpreter execution and completion-path
  validation;
- `controls.py` owns the two fixed main-report diagnostics and review renders;
- `report.py` owns machine-gate composition and persisted report shape; and
- `workflow.py` is the explicit application shell.

No new production module exceeds 353 lines. Pydantic remains at the untrusted
configuration boundary; frozen dataclasses name document indices, producer
identity values, verified control inputs, evaluation context, and report
state. Arbitrary dictionaries remain only at intentional JSON boundaries.
Failure messages now include expected and actual run IDs or completion-path
values where the MVP reported only a generic failure.

Equivalence was proven without mutating or rerunning the producer. The
refactored comparator recomputed the frozen baseline-to-candidate and
candidate-to-independent-scratch reports across all 159 artifacts each and
matched both published Task 03E report objects exactly. The producer identity
still resolves to
`prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1`.
The published producer and comparison roots were read and checksum-verified,
not rewritten.

`make fix`, `make check`, and `git diff --check` pass. The final project suite
contains 162 passing tests, including focused gate/report/process tests and the
external frozen-evidence equivalence test. Task 03E remains rejected as the
sole hierarchy policy. Task 03E.1 subsequently completed the correction
contract; Task 03E.2 remains inactive pending separate user review and
activation.
