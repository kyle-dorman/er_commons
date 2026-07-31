# Task 03E.2d: Accept and Publish the Appendix P Hierarchy Correction

Status: **completed on 2026-07-31 with known limitations**.

## Abstract

Accept the known-flawed post-Task 03E.2a hierarchy semantics as sufficient for
the bounded Appendix P vertical slice, then run the human-owned Task 03E.2b
implementation over the complete 222-page document and publish one immutable,
checksum-verified hierarchy-correction candidate.

Preserve the original Task 03E.2 quality rejection and held-out evidence
unchanged. Record a separate, candidate-bound `accepted_with_known_limitations`
publication authorization rather than relabeling the rejected quality reports
as passes. The accepted limitations remain visible downstream and Appendix P
acceptance remains a hypothesis to test across heterogeneous documents in Task
03G, not a corpus-wide quality claim.

This task publishes the existing hierarchy-evidence representation. It does
not define another semantic schema, create canonical sections, or add a new
mapping layer.

## Goal

Produce the completed hierarchy-correction candidate that Tasks 03E.3 and
03E.4 can consume, with exact provenance for both the accepted post-03E.2a
semantics and the user-approved limitations that permit publication.

## Inputs

- the completed, rejected Task 03E.2 candidate attempt, source-only annotation
  seal, quality reports, and terminal reject manifest
- the completed Task 03E.2a nested-regime exit fix and scratch semantic
  aggregate
- the accepted Task 03E.2b human-owned implementation and its exact semantic
  equivalence report under comparison
  `cmpv1-81976bf341f4c6a2033f45a4ead1f6752db566df38d58ff0b4842e7ac0a27a93`
  in `pipelines/brisbane_baylands/task_03e2b_human_rewrite_review/`
- frozen post-Task 03E.2a semantic SHA-256
  `c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8`
- immutable Task 03E producer and Task 03D.1 canonical reference candidates
- current hierarchy-correction v1 schemas, specification, configuration,
  fixtures, validators, and hierarchy-correction CLI
- explicit user acceptance on 2026-07-31 of the known limitations for this
  bounded Appendix P stage

## Accepted limitations

The publication authorization must identify, not erase or reinterpret:

- the frozen Task 03E.2 development and held-out quality rejection;
- the two observed false table boundaries;
- the frozen R04/R05 attribution disagreements;
- the known `Existing SSF District` level disagreement;
- the accepted non-blocking page-2000 R06 `content` ambiguity;
- all other ambiguities and warnings in the exact post-Task 03E.2a payload; and
- that Task 03E.2a repaired the Appendix E nested-regime exit without creating
  a new held-out evaluation or changing the historical rejection.

Acceptance means these limitations are tolerable for the Appendix P semantic
contract and later representative-pilot hypothesis. It does not mean the
historical strict quality gate passed, that the hierarchy is defect-free, or
that the behavior is accepted for all 35 model-corpus documents.

## Outputs

Tracked:

- a small, explicit bounded-acceptance configuration and record contract
- independent validation for a candidate-bound
  `accepted_with_known_limitations` publication authorization
- a narrow publication seam that accepts either a verified strict quality pass
  or the verified bounded acceptance without weakening either verifier
- focused tests for exact limitation inventory, frozen evidence checksums,
  semantic binding, publication, reuse, tampering, and failure preservation
- a durable decision note recording the bounded acceptance and its scope
- updated architecture, dataflow, routing, and downstream task documentation

External:

```text
pipelines/brisbane_baylands/task_03e2_hierarchy_correction/<candidate_id>/
  records/identity.json
  records/input_inventory.json
  records/environment.json
  records/completion_record.json
  artifacts/item_features.jsonl
  artifacts/visible_toc_entries.jsonl
  artifacts/toc_reconciliation.jsonl
  artifacts/regimes.jsonl
  artifacts/decisions.jsonl
  artifacts/hierarchy.json
  artifacts/ambiguities.jsonl
  artifacts/warnings.jsonl
  records/summary.json
  records/metrics.json
  records/artifact_inventory.json

pipelines/brisbane_baylands/task_03e2_hierarchy_review/<candidate_id>/
  bounded_acceptance.json
  reports/
  repeat_builds/
```

The published candidate uses the existing hierarchy-correction semantic record
shapes. The bounded-acceptance record is external publication evidence, not a
fourth semantic representation and not a canonical record.

## Research / learning checkpoint

Compare an explicit exception/waiver record with weakening the original
quality thresholds. Preserve the safer pattern: keep measured evidence and its
original disposition immutable, bind a separate human policy decision to the
exact candidate semantics and known limitation inventory, and make downstream
scope explicit.

The outcome must explain:

- **Evidence and disposition are different.** A quality report can remain a
  valid rejection while a later human decision accepts the measured behavior
  for a narrower purpose.
- **Acceptance must be content-bound.** The authorization binds the exact
  semantic digest, source/producer identity, correction policy, implementation,
  frozen reject evidence, and enumerated limitations.
- **Publication is not silent promotion.** Downstream consumers can determine
  that this candidate was accepted with known limitations rather than through
  the original zero-error gate.
- **No new data model is needed.** The v1 correction payload remains the
  hierarchy-evidence layer; only its publication authorization changes.
- **Appendix P is not corpus proof.** Task 03G must test the accepted behavior
  on heterogeneous structures before Task 03H can run.

## Plan / spec requirement

1. Freeze the bounded-acceptance record shape, exact limitation vocabulary,
   evidence digests, and verification rules before changing publication code.
2. Keep the existing strict `hierarchy_quality_gate_pass` path unchanged.
3. Add a separate verified publication-authorization type for
   `accepted_with_known_limitations`; do not create a fake quality pass.
4. Bind the authorization to the candidate ID, exact semantic SHA-256, Task
   03E.2 reject evidence, Task 03E.2a correction evidence, Task 03E.2b
   equivalence evidence, and checked-in acceptance policy.
5. Run the current human-owned semantic pipeline in fresh processes over all
   222 Appendix P pages. Require exact semantic equality to the frozen
   post-Task 03E.2a payload.
6. Reverify producer and Task 03D.1 preservation, candidate inventory,
   independent repeatability, and resource evidence.
7. Publish atomically with completion last only after the bounded authorization
   verifies. Preserve every failed attempt without a completion record.
8. Invoke the normal command again and require checksum-verified reuse through
   the same bounded-acceptance verification path.
9. Record the published candidate ID and exact Task 03E.3 handoff.

## Review pass

- **Decision integrity:** no historical reject, annotation, report, or checksum
  is rewritten or described as a pass.
- **Scope:** acceptance is limited to the Appendix P vertical slice and the
  later representative-pilot hypothesis.
- **Semantic preservation:** the complete semantic payload exactly matches the
  frozen post-Task 03E.2a behavior reproduced by Task 03E.2b.
- **Publication safety:** acceptance evidence is candidate-bound, independently
  verified, no-clobber, and required for reuse.
- **Layer discipline:** no new semantic schema, duplicate hierarchy payload, or
  canonical mapping is introduced.
- **Maintainability:** the new authorization path is small, named, typed, and
  separate from semantic construction and strict quality evaluation.

## Validation

- Verify the frozen annotation seal, reject manifest, Task 03E.2a evidence, and
  Task 03E.2b comparison bytes before building.
- Require the exact post-Task 03E.2a semantic SHA-256 and full ordered counts:
  6,931 features and decisions, 140 TOC entries and reconciliations, two
  regimes, 12 roots, 234 hierarchy edges, 4,571 direct memberships, two
  unassigned content items, 17 ambiguities, and 148 warnings.
- Require all three fresh semantic builds to match byte-for-byte.
- Revalidate schemas and independently reconstruct hierarchy and membership.
- Reverify every producer and Task 03D.1 preservation surface.
- Require the bounded-acceptance record to fail closed for a changed candidate,
  semantic digest, evidence digest, limitation set, status, or scope.
- Require strict quality-pass verification to retain its original behavior.
- Verify completion-last publication, full inventory checksums, no-clobber
  reuse, and one simulated failed attempt.
- Confirm no held-out annotation, evaluation report, producer, canonical
  reference, or historical failed attempt changed.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- One complete Appendix P hierarchy-correction candidate is atomically
  published and checksum-reused.
- Its semantic payload is byte-identical to the accepted post-Task 03E.2a
  reference reproduced by Task 03E.2b.
- Publication is authorized by a verified
  `accepted_with_known_limitations` record, never by falsifying the strict
  Task 03E.2 quality outcome.
- The named limitation categories are explicit in the acceptance record, and
  the complete ambiguity and warning artifacts remain checksum-bound and
  queryable.
- Candidate identity, provenance, preservation, repeatability, inventory, and
  completion gates pass independently.
- Task 03E.3 receives the exact immutable candidate completion and acceptance
  artifacts and needs no new upstream hierarchy or mapping policy.
- The outcome requests user review before Task 03E.3 is revised and activated.

## Non-goals

- repairing or retuning hierarchy semantics
- rerunning or relabeling the exposed held-out evaluation
- changing Task 03E.1 correction rules or hierarchy-correction v1 semantic
  record shapes
- creating semantic canonical sections, page-label records, or aliases
- changing Task 03D.1 canonical records
- claiming corpus-wide hierarchy acceptance
- activating or executing Task 03E.3

## Activation note

The user explicitly accepted the known-flawed post-Task 03E.2a semantics on
2026-07-31 and requested this full Appendix P publication task. This activates
Task 03E.2d as the sole implementation task. Activation authorizes the bounded
acceptance and task work; it does not claim that a candidate has already been
published or that any validation has passed.

## Outcome

Task 03E.2d published and checksum-reused the complete human-owned Appendix P
hierarchy-correction candidate under a separately verified
`accepted_with_known_limitations` authorization. The original Task 03E.2
development and held-out rejection, source annotations, failed attempt, and
all producer, canonical, and rewrite evidence remain byte-identical to their
pre-run fingerprints. The strict quality gate did not pass and was not
relabeled.

The immutable handoff is:

```text
candidate_id:
  hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1
completion:
  pipelines/brisbane_baylands/task_03e2_hierarchy_correction/
    hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1/
    records/completion_record.json
bounded acceptance:
  pipelines/brisbane_baylands/task_03e2_hierarchy_review/
    hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1/
    bounded_acceptance.json
bounded acceptance SHA-256:
  5335737128fcbac2b1f2d41c42712af0534e2d15141ccf1150c37ffbf70f328c
```

The accepted payload SHA-256 is exactly
`c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8`.
It contains 6,931 features and decisions, 140 visible-TOC entries and
reconciliations, two regimes, 12 roots, 234 edges, 4,571 direct memberships,
two unassigned content items, 17 ambiguities, and 148 warnings. Three fresh
processes produced that same semantic digest. The completed 15-file candidate
passed checksum inventory, JSON Schema, human-owned cross-record validation,
independent hierarchy reconstruction, producer preservation, Task 03D.1
preservation, and completion-last publication. A second normal CLI invocation
returned the same completion path with unchanged candidate and authorization
tree fingerprints.

The checked-in policy freezes seven limitation categories, the exact semantic
digest and counts, the historical rejection and annotation seal, the Task
03E.2a reference, and Task 03E.2b equivalence evidence. Tests fail closed for
changed candidate or semantic identity, status, scope, limitation inventory,
evidence digest, no-clobber authorization, and publication failure; the
simulated failed publication retained an attempt record without a completion
record. The original strict-pass verifier and its focused regressions remain
unchanged.

The learning result is that evidence and disposition are separate records. A
measured rejection can remain immutable while an authorized human accepts its
exact behavior for a narrower use. This follows the accountability pattern in
the [NIST Risk Management Framework authorize
step](https://csrc.nist.gov/Projects/risk-management/about-rmf/authorize-step):
retain the assessment package, make an explicit acceptance decision, and keep
the decision's terms visible. Weakening the original thresholds would have
erased which gate failed; the separate authorization instead content-binds the
candidate identity, source and producer, correction policy and implementation,
frozen reject evidence, exact semantic payload, limitation inventory, and
Appendix P-only scope.

Publication therefore is not silent promotion and did not create a fourth
semantic representation. The existing correction-v1 payload remains the
hierarchy-evidence layer; `bounded_acceptance.json` is external control
evidence. Appendix P acceptance is not proof for all 35 model-corpus documents:
Task 03G must test this hypothesis on heterogeneous document structures before
Task 03H.

`make fix`, `make check`, and `git diff --check` pass with clean Ruff, clean
mypy, and 332 tests. Task 03E.3 now has exact immutable completion and
authorization inputs. The user accepted this Task 03E.2d outcome and identified
Task 03E.3 as next. Task 03E.3 remains provisional and inactive until its
contract is revised against this handoff and explicitly activated.
