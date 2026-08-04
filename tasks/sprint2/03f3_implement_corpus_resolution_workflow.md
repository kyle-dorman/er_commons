# Task 03F.3: Implement the Scoped Corpus Resolution Workflow

Status: **complete as of 2026-08-04 after the human-ownership rewrite and
retention cleanup**. The Gate B synthetic runtime served as a transient rewrite
oracle. Its human-owned replacement passed exact artifact equivalence,
substantive maintainability checks, the executable v1.1 contract, and the full
repository gate; the unused MVP package, equivalence test, and retained identity
copy were then removed. By user decision, the optional real-source smoke is
skipped. Provisional Task 03F.4 owns broader extraction cleanup and boundary
work before Task 03G; both tasks remain inactive pending separate approval.

## Abstract

First amend the executable corpus contract so its persisted records can prove
the identity, invalidation, failure-evidence, exact-coverage, immutability, and
handoff claims already required by the accepted prose specification. After
separate approval, implement exact run-scope accounting over immutable Task
03F.2 document candidates, seal a corpus target index, publish an immutable
cross-document resolution pass, and produce a separately gated candidate
handoff. No stage-one byte may change.

## Goal

Make fixture, optional engineering-smoke, Task 03G pilot, and Task 03H full
scopes independently restartable and impossible to confuse with one another or
with Task 04 acceptance. The durable evidence must be independently derivable
from verified Task 03F.2 artifacts rather than trusted because two generated
records agree with each other.

## Accepted handoff and inputs

- accepted human-owned Task 03F.2 production identity
  `exv1-bedd4c50a9614a74a6406d60148a08c44579f0b504bc3568042499f578c0cf7f`
  as immutable reference evidence;
- Task 03F.2's public `RunSpec`/`load_run_spec` and
  `er_commons.corpus_extraction.run_document` interfaces;
- Task 03F.2 `SourceIdentity`, `StateEvent`, `AttemptRecord`, and
  `DocumentCompletion` records;
- Task 03F.2 candidate identity, completion-last publication, upstream-seal,
  checksum-closure, reuse, retained-failure, and recovery behavior;
- `docs/specs/restartable_corpus_extraction_v1.md` and the executable corpus
  contract, subject to the explicit Gate A amendment below;
- the exact ordered Task 02 `model_corpus` scope;
- stable Task 03E.5 `deferred_cross_document` mention IDs and immutable local
  outcomes from verified stage-one `canonical/cross_references.jsonl` streams;
- verified stage-one aliases and targets from candidate-owned canonical streams,
  with document-local `support/cross_reference_target_index.json` retained as a
  distinct support artifact rather than treated as the corpus index; and
- verified stage-one completions, inventories, terminal attempts, and hierarchy
  dispositions for the declared run scope.

The earlier Task 03F.2 behavioral MVP identity
`exv1-eac11135056bbbc278b61875591e3876e69dbb08192ac96ec0e5ac4b2b32765e`
is historical reference evidence only. Adding Task 03F.3 output-affecting code
changes the production owned-code inventory and therefore requires a new
production `exv1-` identity. An existing `docv1-` candidate remains bound to its
original production identity and may not be rebound or copied into the new
namespace as if it had been produced under the amended contract.

## Outputs

### Gate A — executable-contract amendment

- an explicit amendment note identifying every accepted v1 prose/schema/
  validator mismatch and whether the corrected executable contract retains the
  v1 namespace or introduces a successor version;
- closed RFC 8785 preimages and derivation validators for `idxv1-`, `resv1-`,
  and `handoffv1-` identities;
- record shapes that bind scope accounting to exact terminal Task 03F.2
  evidence; the corpus index to exact accounting and candidate-completion bytes;
  resolution to an independently derived mention-input manifest, index seal,
  output digest, inventory, and before/after candidate inventories; and handoff
  to exact prerequisite digests and blocking evidence;
- a typed unavailable-source record joined to source identity, terminal
  transaction, disposition, failure class, and retained evidence references;
- reason-specific target evidence for `target_not_in_scope`,
  `target_source_failed`, and `target_unavailable`;
- exact `ready`/`blocked` derivation and blocking-reason rules;
- corpus-stage publication, reuse, interruption, and attempt envelopes, or an
  explicit amendment explaining which lifecycle evidence is operational rather
  than part of the semantic record;
- expanded positive and negative fixtures plus responsibility-owned validator
  changes; and
- a refreshed production-identity recipe that binds the approved amendment and
  complete output-affecting owned-code inventory without making an execution
  claim.

### Gate B — synthetic implementation

- exact manifest-ordered run-scope validation and terminal accounting;
- a public typed read-only Task 03F.2 evidence observer returning either one
  checksum-verified successful completion or one verified latest terminal
  failure, including recovery and publication reconciliation;
- a deterministically ordered sealed corpus target index and unavailable-source
  catalog;
- exactly one corpus-resolution record per independently derived eligible
  `deferred_cross_document` mention, plus completion and inventory;
- byte-level stage-one immutability proof;
- candidate handoff with exact blocking evidence and
  `task04_status: not_evaluated`;
- required-argument `extraction run-scope --run-spec PATH` and
  `make run-extraction-scope RUN_SPEC=PATH` interfaces;
- restartable accounting, index, resolution, and handoff publication; and
- generated-artifact validation through both the amended JSON Schema and its
  cross-record Python validator.

## Gate A — amend before runtime implementation

The accepted prose specification is stricter than its current executable record
shapes. Before implementing a runtime workflow:

1. Bind the index to the exact accounting bytes, ordered eligible candidate
   completions and inventories, complete unavailable-source evidence, serialized
   entries, entry count, inventory, and identity preimage. A changed accounting
   or candidate byte must recompute the index identity and reject reuse.
2. Derive eligible mentions independently from every verified successful
   candidate, including candidates with zero eligible mentions. Bind the ordered
   input manifest, exact source inventories, output bytes, counts, inventory,
   and resolution identity. Removing the same mention from both a self-declared
   ID list and output list must fail.
3. Join each accounting row to the exact manifest source and latest
   scope-terminal Task 03F.2 transaction. Successful rows require a verified
   candidate; failed rows require a verified terminal attempt and cannot name a
   candidate.
4. Ground every unresolved reason in the specific intended target document and
   accounting/catalog evidence. An unrelated failed source cannot justify
   `target_source_failed`.
5. Freeze exact identity preimages, persisted identity evidence, invalidation,
   no-clobber publication, completion-last behavior, and reuse verification for
   the index, resolution, and handoff stages.
6. Derive handoff status from verified prerequisites and policy. Record why a
   handoff is blocked; reject unjustified `ready` and `blocked` claims.
7. Decide how stage-two and handoff-only policy enters configuration without
   silently invalidating `docv1-` candidates through Task 03F.2's whole-run-spec
   digest. Any change to the accepted stage-one identity boundary must be
   explicit in the amendment and preservation tests.
8. Expand fixtures for `complete_with_warnings`, retry and cancellation history,
   target collisions, zero-mention candidates, all three corpus unresolved
   reasons, terminal external-record exclusion, blocked handoffs, identity
   mutations, stale prerequisites, and every publication crash window.

Run focused contract validation, inspect the diff, and stop for explicit user
approval. Gate A may change specifications, schemas, fixtures, offline
validators, and identity recipes only. It may not add runtime stage-two code,
run `run-document` or `run-scope`, delete historical code, or execute a PDF.

## Gate B — implementation after separate approval

### Orchestration and ownership

Implement one short `run-scope` application shell with separate, named owners
for:

- scope preflight and exact manifest-ordered subset validation;
- Task 03F.2 invocation and public terminal-evidence observation;
- accounting construction and validation;
- corpus target-index construction;
- cross-document resolution;
- subordinate identities;
- records and serialization;
- storage, publication, recovery, and reuse;
- handoff policy and publication; and
- structured observability.

Tests must use public typed boundaries and public fault-injection hooks rather
than private orchestration helpers. Extend the objective Task 03F.2
maintainability checks for shell, module, and function size, responsibility-
aligned test organization, and complete owned-code inventory coverage.

### Workflow

1. Load the explicit run specification, verify the new production identity, and
   require the declared sources to be a unique exact manifest-ordered subset.
   Reuse Task 03F.2's `scopev1-` identity; do not invent a second identity for
   the same declared scope.
2. For each declared source, call or checksum-reuse Task 03F.2's public
   `run_document` boundary. Continue after one source reaches a verified
   terminal failure. Never interpret an arbitrary exception or unclosed attempt
   as a terminal accounting row.
3. Seal accounting only after the public evidence observer verifies exactly one
   scope-terminal outcome for every source. Reconcile the accepted
   publication-before-event crash window before accounting success.
4. Build the corpus index only from checksum-verified successful candidates.
   Aggregate candidate-owned aliases and targets without regenerating them,
   rerunning mention detection, or mutating document-local support. Preserve
   cross-target lookup-key collisions as ambiguity.
5. Join failed sources through accounting and terminal-attempt evidence into the
   unavailable-source catalog.
6. Independently enumerate stage-one mentions whose immutable local outcome is
   `unresolved` with reason `deferred_cross_document`. Order them by manifest
   source ordinal, candidate-local sequence, and stable mention ID.
7. Resolve each eligible mention exactly once against targets of the authorized
   type. Preserve exact sealed-index candidate order. Named external documents
   whose stage-one reason is `external_document_outside_corpus` do not enter the
   second pass and must remain byte-identical.
8. Reverify all stage-one candidate inventories before and after resolution.
9. Publish accounting, index, resolution, and handoff through the amended
   completion-last, no-clobber, interruption-safe lifecycle. Before reuse or
   handoff, reconstruct the durable contract bundle and run both schema and
   cross-record validation.

## Research / learning checkpoint

Explain why an immutable branch-and-join index makes invalidation and provenance
visible, why failed sources remain catalog evidence rather than disappearing,
and why independently derived input manifests are necessary to prove exact
coverage. Document why the chosen stage-two record and identity amendment is the
smallest correction that makes the accepted prose claims executable.

## Validation

### Gate A

- each amended schema against every valid fixture and declared negative
  mutation;
- exact recomputation and mutation sensitivity for `idxv1-`, `resv1-`, and
  `handoffv1-`;
- omission of an eligible mention from both declared IDs and output fails;
- failed-target reasons require matching source-specific failure evidence;
- changed accounting, candidate, index, mention-input, resolution, prerequisite,
  or handoff-policy bytes invalidate only the contract-declared downstream
  identities;
- external stage-one mentions cannot enter second-pass eligibility; and
- `make validate-extraction-contract`, focused contract tests, `make fix`,
  `make check`, and `git diff --check`.

### Gate B

- fixture, engineering-smoke, pilot, and production scope-identity separation;
- exact manifest-subset order, row closure, aggregates, and terminal evidence;
- Task 03F.2 reuse, successful completion, terminal failure, retry,
  cancellation, and publication reconciliation through the public observer;
- deterministic index order, authorized target types, collision preservation,
  sealing, reuse, and invalidation;
- resolved, ambiguous, `target_not_in_scope`, `target_source_failed`, and
  `target_unavailable` cases with specific evidence;
- exact independently derived mention coverage, including zero-mention
  candidates, and byte-identical stage-one inventories;
- exact exclusion and preservation of terminal external stage-one records;
- interruption and reconciliation before and after each independent publication;
- exact `ready`/`blocked` handoff derivation and rejection of Task 04 claims;
- actual generated artifacts validated through the amended executable contract;
- responsibility-aligned modules, public test seams, maintainability bounds, and
  complete owned-code inventory; and
- exact offline Appendix P preservation under the refreshed production identity,
  without rerunning its PDF.

Run:

```bash
make validate-extraction-contract
make fix
make check
git diff --check
```

## Acceptance criteria

- The executable contract can independently prove every identity, lifecycle,
  invalidation, failure, coverage, immutability, and handoff claim required by
  the accepted specification.
- The accepted Task 03F.2 implementation is reused through public typed
  boundaries; stage-one orchestration, evidence verification, and content policy
  are not duplicated.
- Every declared source has exactly one verified scope-terminal accounting row.
- Only checksum-verified successful candidates enter the corpus index.
- Every eligible mention is derived from immutable stage-one bytes and receives
  exactly one separate corpus result; terminal external records receive none.
- Changed upstream or control bytes invalidate exactly the declared downstream
  reuse boundary.
- All runtime artifacts pass the same schema and cross-record gates as the
  expanded contract fixtures.
- The new code has short application shells, named responsibility owners,
  structured logging, public test seams, and objective maintainability checks.
- Handoff prerequisites remain distinct and Task 04 is not claimed.
- No representative pilot or full 35-source run occurs.
- The outcome requests explicit approval before Task 03G activation.

## Optional real-source engineering smoke

Gate B implementation and synthetic acceptance do not authorize a PDF run. If
integration confidence later requires a smoke, propose no more than two
predeclared small sealed `model_corpus` PDFs, process every page, estimate cost,
name the exact command and expected artifacts, and obtain separate approval.
The smoke retains a subordinate identity and cannot satisfy Task 03G or Task
03H accounting.

## Non-goals

- changing stage-one content, hierarchy policy, or Task 03E.5 mention policy;
- rebinding an old `docv1-` candidate to a new production identity;
- representative-pilot selection or production-configuration acceptance;
- unapproved real-source execution or full-corpus extraction;
- Task 04 usability review or freeze;
- deleting extraction implementations outside the transient Task 03F.3 rewrite
  scaffolding; broader cleanup belongs to provisional Task 03F.4; or
- OCR, figure linking, distributed scheduling, a database, or a workflow engine.

## Gate A outcome

Gate A introduced the versioned v1.1 corrigendum while preserving the accepted
v1 stage-one records, identities, and Task 03F.2 evidence. The corrected schema
and responsibility-owned offline validators now prove exact terminal
accounting, unavailable-source evidence, independently derived mention
coverage, stage-one byte immutability, closed subordinate identity preimages,
source-specific unresolved reasons, mechanical handoff status, and separate
operational publication envelopes.

The deterministic synthetic corpus covers `complete`,
`complete_with_warnings`, `failed_terminal`, successful zero-mention
candidates, terminal external-record exclusion, all three corpus unresolved
reasons, cross-target ambiguity, retained retry/cancellation attempts, and a
policy-blocked handoff. Checked negative mutations reject missing byte sizes,
false accounting counts, stale subordinate IDs or prerequisites, interrupted
attempts that claim publication, false handoff readiness, and Task 04 claims.
The refreshed non-executed production identity is
`exv1-0e99ab6635d7addf403fefb782c7f6a82994473370de8b2460c6e3c80563e60f`.

No runtime stage-two workflow, `run-scope` interface, source-PDF execution,
engineering smoke, Task 03G activation, or Task 03H activation occurred. Gate B
requires a separate explicit approval.

## Gate B outcome

Gate B adds a separate closed `ScopeRunSpec`, the required
`extraction run-scope --run-spec PATH` and
`make run-extraction-scope RUN_SPEC=PATH` interfaces, and responsibility-owned
runtime modules for scope preflight, Task 03F.2 terminal-evidence observation,
accounting, indexing, resolution, handoff, publication, and contract-bundle
validation. The document run specification remains unchanged and continues to
derive `scopev1-` and `docv1-`; stage-two policies enter only their declared
downstream identities.

Synthetic end-to-end tests prove continuation after a verified terminal source
failure, exact successful reuse, resolved and source-failed corpus outcomes,
blocked and ready handoffs, byte-identical before/after stage-one inventories,
cancel-and-retry before atomic rename, and reconciliation after publication but
before terminal attempt recording. Every generated bundle passes the same
Draft 2020-12 schema and cross-record validator as the checked fixtures. The
human-ownership gate bounds the application shell, modules, functions, public
fault-injection seams, and production owned-code inventory.

The refreshed Gate B production identity recipe is
`exv1-bd4dee857ca90df1c22db148a7e605938bcae90958bb471eb1db7e40c6e1f565`
with `execution_status: not_executed`. The Gate A identity recipe is retained as
historical evidence. No source PDF, engineering smoke, representative pilot,
full-corpus run, or Task 04 review occurred.

## Human-ownership rewrite

The user accepted the Gate B ideas and synthetic behavior as the Task 03F.3
MVP, but rejected that implementation as the repository's maintained
implementation. It was retained only while replacing the active
`er_commons.corpus_resolution` implementation behind the same public CLI and
artifact contract with code organized for human ownership.

Completion now requires two independent gates:

1. **Behavioral equivalence:** the reference MVP and replacement must produce
   byte-identical contract artifacts for the accepted deterministic scenarios,
   including success, verified terminal failure, reuse, interruption before
   publication, and reconciliation after publication. Both outputs must pass
   the same v1.1 schema and cross-record validator.
2. **Human maintainability:** the replacement must use explicit typed domain
   boundaries, short application shells, named responsibility owners,
   centralized serialization/publication behavior, public fault seams, and
   responsibility-aligned tests. Review must assess cohesion and readability,
   not merely line-count thresholds.

The reference package was never an alternate production path or reachable from
the CLI. Once equivalence and maintainability passed, its package, dedicated
equivalence test, and retained identity copy had no future caller and were
removed. The active production identity is refreshed after that cleanup. The
optional engineering smoke is explicitly waived rather than passed; a bounded
variant belongs in the future Task 03G contract and requires Task 03G
activation before execution.

## Human-ownership outcome

The transient Gate B implementation established the accepted orchestration and
its non-executed identity
`exv1-bd4dee857ca90df1c22db148a7e605938bcae90958bb471eb1db7e40c6e1f565`.
The maintained `er_commons.corpus_resolution` package uses typed stage
builds, explicit accounting/index/resolution/handoff input types and builders,
a separate terminal-evidence collector, immutable corpus-catalog and scope-input
owners, a focused attempt journal, and a 32-line public workflow shell.
Persisted JSON remains dictionary-shaped only at the executable contract
boundary.

The equivalence gate holds the exact Task 03F.2 evidence fixed and requires
byte-identical stage-two contract artifacts for successful, verified terminal-
failure, and interrupted-publication scenarios. Existing public interruption
tests separately prove both accepted crash windows and reuse. Maintainability
tests verify named construction owners, typed control boundaries, module and
function bounds, public fault seams, and complete production owned-code
coverage. After those gates passed, the MVP package, its four-scenario
executable equivalence test, and its retained identity copy were removed under
the project retention policy. The passing equivalence result remains recorded
here; executable archaeology does not.

The final maintained production identity is
`exv1-3cbbe57424f72ca8800456b23c887e1b2b65693917a8b33ac40791f3630852ea`
with `execution_status: not_executed`. `make validate-extraction-contract`,
`make fix`, `make check`, and `git diff --check` pass; the full check contains
527 tests. No source PDF, engineering smoke, Task 03G pilot, Task 03H run, or
Task 04 review occurred. Broader proof-scaffolding removal and production-
boundary simplification are explicitly deferred to provisional
[Task 03F.4](03f4_prune_extraction_proof_scaffolding.md).
