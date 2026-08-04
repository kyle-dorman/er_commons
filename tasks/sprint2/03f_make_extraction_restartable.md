# Task 03F: Make Two-Stage Corpus Extraction Restartable

Status: **decomposed; Tasks 03F.1–03F.3 complete as of 2026-08-04**. Task
03F.4 is provisional after contract review and requires explicit activation.
It owns destructive proof-of-concept cleanup and production-boundary work
before Task 03G. This umbrella closes only after Task 03F.4 is separately
accepted. Task 03G and Task 03H remain provisional.

## Abstract

Turn the accepted Appendix P producer, semantic-structure, and cross-reference
pipeline into a narrow, manifest-driven two-stage corpus workflow. Stage one
treats each complete PDF as an isolated, restartable transaction. Stage two
seals a target/alias index over an explicitly bounded run scope and appends
cross-document resolution records without modifying stage-one candidates.

Task 03F builds and tests the capability; it does not execute the 35-document
corpus. Task 03G owns the representative full-document pilot, and Task 03H owns
the full run and its 35-source terminal accounting.

## Accepted handoff

The production cross-reference input is the accepted Task 03E.5
pattern-policy-v2 candidate
`exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`,
not the behavioral MVP or original human rewrite. It contains 292 mentions:
256 resolved, 35 unresolved, and one ambiguous. It preserves all 323 Task
03E.4 aliases, adds 11 verified table aliases, and adds zero figure aliases.

The frozen downstream policy includes:

- structural exclusion of complete reference sections and author-year
  bibliography entries;
- qualifier classification before local numeric-section lookup;
- exact target-side table evidence plus the five-physical-page mention window;
- zero derived figure aliases and an OCR-free first pass;
- checksum-bound corpus membership for named-EIR classification; and
- literal preservation of the two accepted source-authored appendix-link
  inconsistencies without document-specific correction.

Task 03F may generalize the mechanism but may not weaken this behavior, mutate
the accepted candidate, add figure linking, or broaden Appendix P's bounded
hierarchy acceptance into a corpus-wide quality claim.

## Execution boundary

Task 03F implementation validation uses synthetic multi-document fixtures. The
optional Task 03F engineering smoke was waived; Task 03G must separately
contract any bounded full-document variant before running it. A first-N-page
source run is not a completed stage-one transaction and may be used only as an
explicitly incomplete diagnostic, never as restartability, hierarchy, alias,
or corpus-index evidence.

Task 03G selects the heterogeneous full-document pilot. Task 03H alone consumes
all 35 sources and requires every source to reach an explicit terminal state.

## Subtasks

1. [Task 03F.1](03f1_define_restartable_extraction_contract.md) — complete:
   the corpus identity, state, artifact, cache, failure, index, resolution, and
   bounded-validation contract is accepted.
2. [Task 03F.2](03f2_generalize_restartable_document_stage.md) — complete:
   preserve the accepted atomic restartable behavior while replacing the MVP
   with readable, responsibility-owned stage-one code; no historical code was
   deleted because the full deletion proof did not pass.
3. [Task 03F.3](03f3_implement_corpus_resolution_workflow.md) — complete:
   implemented scoped accounting, target-index sealing, immutable
   cross-document resolution, and invalidation without real-source execution;
   the optional engineering smoke was waived for a future Task 03G variant.
4. [Task 03F.4](03f4_prune_extraction_proof_scaffolding.md) — provisional:
   inventory future capability and active invariants, then destructively remove
   obsolete POC schemas, validators, proof paths, and public surfaces after
   separate Gate B approval while preserving the maintained Task 03G–04 path.

Only an explicitly activated subtask is active. Revise each provisional
contract from the accepted prior outcome before implementation.

## Shared requirements

- The sealed Task 02 manifest remains the sole source of the ordered
  35-document production scope and checksums.
- One corpus `extraction_id` binds that production scope and every semantic
  input that can change output; bounded test or smoke runs have subordinate
  run-scope identities and cannot impersonate the production run.
- A complete PDF is the stage-one publication and fault-isolation unit.
- Cache reuse requires validation of identities, managed files, checksums, and
  completion records before skipping work.
- Target-index and second-pass publication are append-only relative to stage
  one and are invalidated by any changed stage-one candidate.
- Document completion, run-scope accounting, target-index completion,
  resolution completion, candidate handoff, and Task 04 acceptance are
  distinct records.
- Concurrency, queues, memory, threads, device use, timeouts, retries, storage,
  and cancellation behavior are explicit and bounded.
- Page renders are regenerable review cache outside canonical identity and
  completeness.
- Use narrow project glue around maintained packages; do not introduce a
  workflow engine, scheduler service, or database queue.

## Removal and generalization policy

Task 03F.2 replaced Appendix-P constants and CLI assumptions with
manifest-selected, contract-bound document inputs where those components are
part of the production path. Task 03F.4 inventories current callers, declared
Task 03G–04 consumers, tests, identity inputs, active invariants, review-cache
needs, and independent-validation needs before deletion.

Delete obsolete facades, duplicate orchestration, hard-coded defaults, and
superseded behavioral-reference implementations when they have no accepted
runtime or verification owner and their required behavior is covered by the
human-owned implementation and tests. Do not retain compatibility aliases for
unproven callers. This POC cleanup may remove superseded schemas, validators,
fixtures, and executable replay support without migration or continued
verification of historical candidates. It may not remove capabilities required
by the maintained Task 03 path or declared Tasks 03G–04 without first naming and
testing their successor.

## Umbrella acceptance criteria

- Tasks 03F.1–03F.4 are separately accepted under their own validation gates.
- The runtime consumes manifest-selected complete documents without
  Appendix-P-only production constraints.
- The accepted Appendix P semantic and cross-reference behavior remains exact
  under the declared identity normalization.
- Per-document stage one is isolated, atomic, restartable, and verifiable.
- Scoped target-index and second-pass results are reproducible, independently
  restartable, and cannot mutate stage one.
- Production 35-source identity is distinct from fixture, engineering-smoke,
  Task 03G pilot, and Task 03H execution state.
- No full-corpus conversion begins.
- The outcome requests explicit user approval before Task 03G activation.

## Non-goals

- representative-pilot selection or execution
- full 35-document extraction or terminal accounting
- corpus acceptance or Task 04 usability decisions
- automatic parser or hierarchy repair
- corpus-wide acceptance of Appendix P's bounded hierarchy policy
- OCR or figure-link support
- distributed or cloud orchestration
- retrieval, generation, or evaluation
