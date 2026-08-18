# Restartable Corpus Extraction Contract v1.1

## Status and amendment boundary

This document began as the Task 03F.3 Gate A executable-contract corrigendum to the
accepted [v1 contract](restartable_corpus_extraction_v1.md). It preserves the
v1 production meaning, stage-one records, and typed ID prefixes while replacing
the pre-runtime synthetic stage-two shapes with records that can prove the v1
prose requirements. No `idxv1-`, `resv1-`, or `handoffv1-` runtime artifact was
published under the earlier shapes, so this correction does not reinterpret an
immutable stage-two artifact.

Gate B implements the corrigendum under
`contract_revision: task_03f3_gate_b`. This revision authorizes the synthetic
runtime and its checked artifacts; it does not approve a real-source smoke, run
a PDF, or claim Task 03G, Task 03H, or Task 04 completion. The refreshed
production identity remains `execution_status: not_executed`.

The first Gate B implementation served transiently as the behavioral oracle for
the human-owned `er_commons.corpus_resolution` replacement. Executable
equivalence held verified Task 03F.2 evidence fixed and proved byte-identical
stage-two artifacts across success, terminal-failure, and interrupted-
publication scenarios. After the replacement passed that gate and its separate
maintainability review, the unused MVP package, dedicated equivalence test, and
retained identity copy were removed. The accepted result remains in the Task
03F.3 outcome; only the maintained implementation remains executable.

Task 03F.2's accepted human-owned production identity
`exv1-bedd4c50a9614a74a6406d60148a08c44579f0b504bc3568042499f578c0cf7f`
is immutable reference evidence. The refreshed production identity binds this
corrigendum and its executable validator. Existing `docv1-` candidates remain
bound to their original `exv1-` identity and cannot be relabeled.

Task 03F.4 made v1.1 the sole executable corpus contract, removed the v1
package/schema/fixtures and offline preservation proof branch, and added
read-only handoff validation over published scopes and successful document
candidates. The checked production-identity fixture derives the current ID
from this contract and retains `execution_status: not_executed`; older
identities remain immutable historical evidence only.

## Standards and representation

Identity preimages use [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html)
JSON Canonicalization Scheme bytes followed by SHA-256. RFC 8785 supplies
invariant primitive serialization, no inter-token
whitespace, deterministic property sorting, and UTF-8 output. Identity inputs
therefore use the I-JSON-compatible values already accepted by v1 and do not
normalize Unicode during canonicalization.

Persisted records use JSON Schema Draft 2020-12 with closed object shapes.
JSON Schema owns record structure and local conditional requirements. Python
owns cross-record derivation, artifact-byte verification, ordering, joins,
identity recomputation, exact coverage, and invalidation.

## Preserved v1 boundaries

The following v1 behavior is unchanged:

- the ordered 35-source production scope and `exv1-` production namespace;
- `scopev1-`, `txv1-`, and `docv1-` derivation;
- Task 03F.2 `SourceIdentity`, `StateEvent`, `AttemptRecord`, and
  `DocumentCompletion` bytes;
- complete-PDF transaction scope, Docling `SUCCESS` publication gate, retained
  failures, completion-last atomic publication, checksum-closed reuse, and
  recovery;
- immutable local mention text, spans, source records, and local-first
  outcomes; and
- the distinction between machine handoff and Task 04 acceptance.

Stage-two or handoff-only fields must not be added to Task 03F.2's
`DocumentRunSpec`. Its exact byte checksum contributes to `scopev1-` and the
`docv1-` control digest. Gate B must instead define a separate `ScopeRunSpec`
that references the exact document-run-spec artifact. Handoff-only policy enters
only `handoffv1-`; non-output operational settings enter attempt evidence; any
output-affecting corpus policy belongs in the production `exv1-` contract.

## Scope run specification

Gate B adds a separate closed `ScopeRunSpec`. It references the exact unchanged
Task 03F.2 document run specification and declares the same unique
manifest-ordered source sequence, a sealed corpus catalog, target and resolution
policy digests, target ordering version, and handoff blocking policy. The
document run specification still derives `scopev1-`; stage-two configuration
does not silently alter existing `docv1-` semantics. Each output-affecting
stage-two field enters its declared subordinate identity.

The package-backed interface is:

```text
er-commons extraction run-scope --run-spec PATH
make run-extraction-scope RUN_SPEC=PATH
```

Both commands require an explicit specification and have no default source or
production scope.

## Artifact references

Every byte-sensitive reference is closed:

```json
{
  "path": "scope-relative/path",
  "sha256": "lowercase-64-hex",
  "byte_size": 123
}
```

Paths are reviewable locators, while checksums and byte sizes prove exact
content. A validator must resolve a reference below the declared artifact root,
read the bytes independently, and verify both fields. Logs or another generated
record cannot substitute for referenced bytes.

## Exact terminal accounting

Accounting retains one manifest-ordered row per declared source. Each row adds
the source ordinal, attempt number, exact terminal-event and attempt-record
references, and the success or failure evidence required by its disposition.

Successful `complete` or `complete_with_warnings` rows normally require:

- a verified Task 03F.2 terminal event and `AttemptRecord` for the same source,
  transaction, attempt, and disposition;
- a `docv1-` candidate;
- exact `DocumentCompletion` and candidate-inventory references; and
- `failure_class: null`.

Task 03G.2f also permits a downstream-only replay row. It carries a sealed
`replayv1-` record, null attempt/event fields, the prior document completion
and inventory, exactly five reused upstream owner completions, and one
replacement cross-reference completion. Its publication record must state
`document_attempt_allocated: false`. This path cannot represent failure and
does not enter document-attempt closure.

A `failed_terminal` row requires:

- a verified terminal event and `AttemptRecord` for the same source,
  transaction, attempt, and disposition;
- a nonempty failure class identical to the retained attempt;
- no candidate, completion, or candidate inventory; and
- retained evidence references.

Earlier attempts for the same source may end only in `failed_retryable` or
`cancelled`. The accounting row must name the latest contiguous attempt.
Arbitrary exceptions, running attempts, and unverified paths are not terminal
evidence. Accounting completion includes the RFC-8785/SHA-256 digest of the
closed accounting payload so downstream identities bind exact accounting bytes.

## Unavailable-source catalog

The unavailable catalog contains one record for every failed accounting row and
no other source. It repeats the full source identity, manifest ordinal,
transaction, attempt, `failed_terminal` disposition, failure class, and exact
terminal-event, attempt-record, and retained-evidence references. Records are in
manifest order and must be byte-for-byte equivalent to their accounting
evidence. A list of source IDs alone is insufficient.

## Corpus index identity and completion

`index_id` is `idxv1-` plus the SHA-256 of the RFC 8785 bytes of this closed
preimage:

```text
schema_version
production_extraction_id
scope_id
accounting payload SHA-256
ordered eligible-candidate payload SHA-256
unavailable-source payload SHA-256
serialized entry-stream SHA-256
entry_count
serialized document-target-stream SHA-256
document_target_count
ordering_policy_version
target_policy_sha256
managed-inventory SHA-256
```

The completion carries the exact artifact references whose verified bytes must
produce those preimage digests. The preimage excludes `index_id`, completion
bytes, attempt UUIDs, timestamps, host information, timings, logs, and
publication location. All successful
candidates appear even when contributing zero index entries. A separate
source-indexed `document_targets.jsonl` stream is derived directly from each
successful candidate's sealed `documents.jsonl` bytes. It is not derived from
aliases, and its checksum and count enter `idxv1-`. Entries are
serialized as JSONL and ordered by normalized lookup key, target type, manifest
source ordinal, target ID, then alias ID. Duplicate evidence for one exact
alias-target pair collapses; cross-target collisions remain explicit. The
completion persists the preimage, recomputes `index_id`, verifies inventory
closure, and is written last.

Any accounting, candidate completion, candidate inventory, alias stream, target
stream, unavailable catalog, entry stream, ordering policy, or target-policy
change invalidates index reuse. Unrelated stage-one candidates do not change.

## Independently derived mention input

The mention-input manifest contains one manifest-ordered candidate row for every
successful candidate, including candidates with zero eligible mentions. Each
row binds its document completion, candidate inventory before resolution, and
exact `canonical/cross_references.jsonl` stream. Its eligible mentions include
candidate-local sequence, stable mention ID, original mention class, lookup
key, explicit catalog evidence, target type, and the ordered intended target
source IDs derived from the shared sealed source-family catalog.

The validator independently reads every referenced stage-one stream and selects
exactly records with `resolution_status: unresolved` and
`unresolved_reason: deferred_cross_document`. It derives the intended target
source IDs from the same sealed catalog evidence and compares the complete
ordered manifest. Omitting a mention from both a declared ID list and output
therefore fails. Records with `external_document_outside_corpus`, local
resolutions, or any other local reason do not enter the second pass.

Eligible mentions are ordered by source ordinal, candidate-local sequence, then
stable mention ID.

Resolution joins intended source IDs to the independently derived sealed
document-target stream. Display-title or extracted-alias equality is not a
second eligibility test. One intended successful source with one document
target resolves; multiple intended sources or targets are ambiguous; a
successful source without a document record is `target_unavailable`; and a
failed or absent intended source is respectively `target_source_failed` or
`target_not_in_scope`.

## Corpus resolution identity and dispositions

`resolution_id` is `resv1-` plus the SHA-256 of the RFC 8785 bytes of this closed
preimage:

```text
schema_version
production_extraction_id
scope_id
index-completion SHA-256
mention-input-manifest SHA-256
serialized resolution-stream SHA-256
counts payload SHA-256
before/after inventory payload SHA-256
resolution_policy_sha256
managed-inventory SHA-256
```

The resolution completion carries the exact references that realize each
preimage digest. The after inventories cover every successful candidate and
must exactly equal
the before inventories in the independently derived mention manifest. A
resolution row references one stable mention, the source candidate, sequence,
lookup key, target type, intended target source IDs, ordered candidate targets,
status, optional unresolved reason, and reason evidence.

Candidate cardinality remains mechanical: zero is `unresolved`, one is
`resolved`, and more than one is `ambiguous`. Resolved and ambiguous records
have no unresolved reason or reason evidence. Candidate targets must occur in
the sealed index in its exact order and match the authorized target type.

For zero candidates, the deterministic precedence is:

1. any intended target source is successful and in scope:
   `target_unavailable` with that source's candidate and index evidence;
2. otherwise any intended target source failed in scope:
   `target_source_failed` with that same source's unavailable evidence;
3. otherwise every intended target source is known to the production corpus but
   outside the declared scope: `target_not_in_scope` with source-manifest and
   scope evidence; and
4. otherwise reject the record as unsupported.

An unrelated failed source cannot justify `target_source_failed`. External
documents remain terminal stage-one records and receive no corpus result.

## Candidate handoff identity

`handoff_id` is `handoffv1-` plus the SHA-256 of the RFC 8785 bytes of this
closed preimage:

```text
schema_version
production_extraction_id
scope_id
accounting, index, and resolution completion SHA-256 values
blocking-policy SHA-256
derived status
ordered blocking-reasons SHA-256
task04_status: not_evaluated
managed-inventory SHA-256
```

The handoff record carries the exact prerequisite and policy references behind
the preimage digests. All prerequisite completions must verify before a handoff
record is valid.
Missing, stale, or invalid prerequisites are publication errors, not a valid
`blocked` handoff.

- `terminal_failures_allowed` always produces `ready` with no blocking reasons.
- `all_sources_successful` produces `ready` with no reasons when there are no
  terminal failures.
- `all_sources_successful` produces `blocked` with exactly one deterministic
  `terminal_source_failure` reason per failed source in manifest order.

`complete_with_warnings` is successful under both policies. Every blocking
reason binds the failed source ordinal, source ID, transaction, and exact
unavailable-source evidence. Task 03F cannot set any Task 04 status other than
`not_evaluated`.

## Corpus-stage operational envelopes

Accounting, index, resolution, and handoff use one operational publication
envelope separate from semantic identities. Each stage has an identity-owned
attempt workspace, append-only `selected -> running -> terminal` events, a
retained attempt record, managed inventory before semantic completion,
completion last, atomic rename into an absent destination, and reconciliation
for publication-before-event interruption. Failed attempts have no semantic
completion. Timing, resource observations, logs, and attempt UUIDs do not enter
semantic IDs.

Reuse requires identity recomputation, prerequisite verification, checksum and
byte-size verification, exact managed-file closure, and a single matching
completion. Partial, stale, conflicting, missing, extra, or corrupt destinations
fail closed. No-clobber publication applies to all four corpus stages.

## Executable validation boundary

The v1.1 schema and fixtures live under
`benchmarks/er_bench/{schemas,fixtures}/corpus_extraction/v1_1/`. The v1.1
Python validator owns:

- exact terminal-attempt, completion, source, and accounting joins;
- unavailable-catalog equality;
- RFC 8785 identity derivation and one-field sensitivity;
- independent stage-one mention derivation and zero-mention candidate coverage;
- index and resolution ordering, cardinality, target type, and evidence;
- source-specific unresolved-reason precedence;
- before/after stage-one immutability;
- exact handoff status and blocking-reason derivation; and
- prerequisite, checksum, inventory, and invalidation checks.

Fixtures are synthetic and make no source-execution claim. The production
identity fixture binds the exact ordered 35-source contract while retaining
`execution_status: not_executed`.

## Gate boundary

Gate A ended after the corrigendum and offline gate passed. Gate B owns only the
synthetic runtime implementation, generated-artifact validation, exact reuse,
interruption tests, and the human-ownership rewrite. A source-PDF engineering
smoke was explicitly waived by user decision. A bounded variant may be
contracted under Task 03G, but Tasks 03G, 03H, and 04 remain outside this
contract and inactive.

The human-owned replacement completes with the non-executed production identity
recorded in the checked canonical identity fixture. The earlier Gate A and Gate
B MVP identities remain historical recipe evidence. None claims a completed
source run.
