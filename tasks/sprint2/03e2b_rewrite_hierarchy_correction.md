# Task 03E.2b: Rewrite Hierarchy Correction for Human Ownership

Status: **closed on 2026-07-31; accepted as the human-owned implementation**.

## Abstract

Replace the completed Task 03E.2/03E.2a MVP with repository-quality code that
humans can read, understand, debug, edit, test, and own. Treat the current MVP
implementation and its corrected Appendix D-to-E behavior as immutable
behavioral reference evidence, not as the finished production implementation.

This is a maintainability rewrite. Preserve verified inputs, semantic records,
TOC parsing and reconciliation, numbering regimes, rule decisions, corrected
hierarchy, ambiguity/warning evidence, CLI behavior, schemas, and fail-closed
publication policy. Do not revise hierarchy policy, rerun the exposed held-out
evaluation, or silently turn its historical rejection into a pass.

## Goal

Make the hierarchy-correction flow understandable from a short public runner.
Give source evidence, feature extraction, TOC analysis, regime construction,
rule evaluation, hierarchy construction, candidate assembly, quality reports,
review preparation, and publication explicit owners and typed stage results.
Failures should name the stage, invariant, source item or artifact, expected
state, and actual state needed to debug them.

## Inputs

- completed MVP [Task 03E.2](03e2_implement_deterministic_hierarchy_correction.md)
- completed Appendix exit fix [Task 03E.2a](03e2a_fix_nested_regime_exit.md)
- verified Appendix P producer and source artifacts
- current schemas, fixtures, configuration, policy, and tests
- a newly frozen complete MVP semantic payload under the external Task 03E.2b
  rewrite-review root
- the immutable historical Task 03E.2 annotations, reports, and failed attempts

## Outputs

Tracked:

- a responsibility-specific, human-owned `hierarchy_correction` package
- a short application shell and semantic pipeline
- named typed stage boundaries instead of cross-stage bags of unrelated JSON
- focused tests at public responsibility boundaries
- an exact semantic-equivalence comparator and report
- updated architecture, task, and routing documentation

External:

```text
pipelines/brisbane_baylands/task_03e2b_human_rewrite_review/
  <comparison_id>/
    reference_semantic.json
    rewritten_semantic.json
    equivalence_report.json
```

The sealed Task 03E.2 review root and rejected candidate attempts remain
immutable.

## Research / learning checkpoint

Use a functional-core/application-shell design:

- Pydantic validates untrusted configuration;
- frozen dataclasses name verified paths, stage inputs, stage outputs, and
  publication state;
- pure domain functions own one feature, matching, rule, hierarchy, or report
  concern;
- plain dictionaries remain only where persisted JSON is the intentional
  contract;
- filesystem, subprocess, rendering, and publication operations remain visible
  edge effects;
- tests exercise public boundaries and invariant failures rather than copying
  private algorithms.

The learning requirement is ownership, not merely fewer lines. A maintainer
must be able to locate one TOC grammar, one match tier, one correction rule, one
hierarchy transition, one candidate record, or one quality report without
following a multipurpose function or shared mutable dictionary across stages.

## Rewrite contract

1. Freeze the complete corrected MVP semantic payload before changing runtime
   code. Record its source, configuration, policy, schema, and code identity.
2. Preserve exact ordered semantic JSON for features, TOC entries,
   reconciliations, regimes, decisions, hierarchy, ambiguities, and warnings.
3. Preserve the Appendix E nested-regime exit reset and the three
   user-confirmed parent relationships.
4. Keep the public CLI commands and persisted v1 record shapes stable.
5. Make the public semantic pipeline read as explicit named stages without
   embedding parser, matcher, rule, or serialization implementations.
6. Split the 881-line TOC module by region detection, row parsing, target
   matching, and result assembly. Match tiers and evidence requirements must
   be declarative and independently testable.
7. Replace the 255-line rule-decision loop with readable rule selection and
   rule-application responsibilities. Preserve rule order and complete
   eligibility evidence.
8. Separate held-out source preparation/sealing from held-out comparison and
   report construction. Rendering, annotation verification, comparison, and
   mismatch classification must have distinct public owners.
9. Separate quality configuration, report production, terminal disposition,
   and pass verification. A rejecting report set must produce an explicit
   quality rejection rather than a Pydantic model error for a pass-only record.
10. Keep candidate identity, record assembly, terminal byte accounting,
    validation, staging, failure retention, and atomic publication visible and
    separately testable.
11. Replace broad cross-stage `dict[str, Any]` use with named dataclasses or
    narrow typed mappings where that reveals an actual domain boundary. Do not
    duplicate the persisted JSON Schema as a second model hierarchy.
12. Keep validators independent from builders while sharing only stable domain
    vocabulary, not implementation decisions.
13. Avoid a framework, registry, generic stage engine, dependency-injection
    container, compatibility aliases, or a new replacement monolith.
14. Remove superseded MVP construction paths after equivalence passes; the
    frozen external payload remains the behavioral reference.

## Equivalence gate

Run the rewritten semantic pipeline in a fresh process over the same verified
producer and require exact byte equality of the complete `semantic` object:

- all 6,931 ordered feature records;
- all visible-TOC rows and reconciliations;
- every numbering regime and item assignment;
- every rule decision, eligible-rule list, evidence record, ambiguity, and
  warning;
- exact roots, edges, direct membership, and unassigned content;
- Appendix E as a level-3 root, with the three confirmed parents unchanged.

The comparison report records reference and rewritten SHA-256 values, exact
first mismatch path if any, record-family counts, source/config/policy/schema
identity, and terminal status. Timings, RSS, process paths, implementation code
digest, and candidate ID are measured separately and are not semantic fields.

Offline candidate assembly must also produce the same summary and payload
records after normalizing only implementation-derived candidate identity,
environment, measurements, terminal inventory hashes, and completion hashes.
If any undeclared semantic value differs, preserve the report and stop for user
review.

## Validation

- inspect module responsibilities, sizes, imports, public names, and docstrings;
- require no production semantic module to become a replacement monolith;
- run focused successful and diagnostic failure tests for each responsibility;
- run a fake end-to-end correction workflow without the real PDF;
- run the external exact semantic-equivalence gate;
- verify the historical Task 03E.2 evidence roots remain unchanged;
- run `make fix`, `make check`, and `git diff --check`;
- perform a final human-maintainability review after tests pass.

## Review pass

- **Readability:** can a maintainer follow verified input through semantic
  stages, candidate assembly, quality disposition, and publication?
- **Ownership:** does each grammar, match tier, rule, hierarchy transition,
  report, and artifact concern have one obvious owner?
- **Debuggability:** do failures identify actionable source and invariant
  context rather than generic mismatch text?
- **Editability:** can one policy implementation change without editing a
  central multipurpose loop or synchronized builder/validator accident?
- **Type boundaries:** are verified inputs, stage results, persisted records,
  and external effects distinguishable?
- **Behavior preservation:** does exact complete-payload evidence—not aggregate
  counts—prove equivalence?

## Acceptance criteria

- The completed MVP is explicitly retained only as reference evidence.
- The production path is composed of cohesive, responsibility-owned modules
  with a short readable public runner.
- Large multipurpose TOC, decision, review, quality, and application flows are
  decomposed without creating another monolith.
- Named types replace cross-stage unstructured state where they improve human
  comprehension and debugging.
- Rejection is an explicit terminal quality disposition, not a pass-model
  validation accident.
- Focused tests cover success, ambiguity, failure, preservation, and
  publication edges.
- Complete semantic output is byte-identical to the frozen corrected MVP.
- All repository checks and the final maintainability review pass.
- No sealed held-out evidence is rewritten, rerun, or promoted as new evidence.
- The task is not complete merely because tests pass; it requires an explicit
  human-quality review outcome.

## Non-goals

- changing heading, TOC, numbering, parent, ambiguity, or warning policy;
- correcting the two tolerated table false boundaries, R04/R05 attribution,
  or `Existing SSF District` depth;
- publishing or promoting a new candidate;
- relabeling exposed pages as a new held-out sample;
- changing Docling, source, producer, canonical, or cross-reference behavior;
- adding OCR, LLM, VLM, embeddings, semantic search, or document-specific
  production exceptions;
- activating Task 03E.3;
- committing or pushing unless separately requested.

## Outcome

The rewrite replaced the MVP construction paths with human-owned modules while
preserving their post-03E.2a behavior. The public application shell now reads
as preflight, exact reuse or new-candidate preparation, three isolated builds,
preservation verification, candidate assembly, explicit quality disposition,
and atomic publication. Candidate identity uses one tested code inventory that
contains every runtime module.

The semantic core now has separate owners for source observations, text
evidence, TOC region detection, TOC row parsing, target reconciliation,
numbering-scope lifecycle, level evidence, rule eligibility, individual
R01-R08 applications, and hierarchy projection. The former large feature,
TOC, decision, and hierarchy entry modules are short compatibility facades.
The Appendix E correction is a named enclosing-stack close event rather than
an implicit special case.

Held-out preparation, annotation sealing, and comparison are separate modules.
No held-out page, annotation, or report was regenerated. Quality configuration,
frozen-evidence verification, report production, report-set disposition, and
pass assembly are also distinct. Rejecting reports are written first and then
raise the typed `QUALITY_GATE_REJECTED` disposition with the rejected report
names; pass assembly is not attempted.

The complete rewritten semantic payload is byte-identical to the frozen
post-03E.2a reference. Both canonical payloads have SHA-256
`c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8` and
contain 6,931 features and decisions, 140 TOC entries and reconciliations, two
regimes, 12 roots, 234 hierarchy edges, 4,571 direct memberships, two
unassigned content items, 17 ambiguities, and 148 warnings. The no-clobber
comparison report is external at:

```text
pipelines/brisbane_baylands/task_03e2b_human_rewrite_review/
  cmpv1-81976bf341f4c6a2033f45a4ead1f6752db566df38d58ff0b4842e7ac0a27a93/
```

An offline aggregate using the final code-derived identity passed JSON Schema
and independent bundle validation. Its summary exactly matched the reference
after normalizing only implementation-derived candidate identity. No candidate
was published or promoted.

`make fix`, `make check`, and `git diff --check` pass: Ruff is clean, mypy is
clean across 131 source files, and all 326 tests pass. The historical held-out
seal and rejected quality-report manifest retain their frozen SHA-256 values
`ae69f47904ba0b270081f3502927f276e9138ba2b4927cffd103ae36b9b3ac15`
and `e13dd0fc14a1f1f7586e6ce97d4f3122e684ffd209876b240d4bd61b4a7f561b`.

The final human-maintainability review accepted the implementation:

- the stage order is readable from short application and semantic runners;
- each grammar, match tier, lifecycle event, rule, review operation, quality
  state, and publication operation has one obvious owner;
- typed contexts and results distinguish verified inputs, semantic stages,
  repeat evidence, candidate records, and terminal failures;
- diagnostics retain stage and report context without parsing exception prose;
- the largest remaining modules are cohesive source-observation, evaluation,
  report-production, or reconciliation owners rather than replacement
  orchestration monoliths;
- exact full-payload evidence, schema-valid offline assembly, focused failure
  tests, and the full repository check jointly establish behavior preservation.

Task 03E.2 and 03E.2a remain MVP/reference history. Task 03E.3 is not activated
by this completion.
