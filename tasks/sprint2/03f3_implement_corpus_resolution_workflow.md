# Task 03F.3: Implement the Scoped Corpus Resolution Workflow

Status: **provisional and inactive**. The shared semantics are grounded by Task
03F.1 Gate B. Activate only after Task 03F.2 is accepted; that outcome may
update concrete module, command, and candidate references but cannot change the
v1 contract without an explicit amendment.

## Abstract

Add exact run-scope accounting over immutable stage-one candidates, seal the
corpus target index, publish an immutable cross-document resolution pass, and
produce a separately gated candidate handoff. No stage-one byte may change.

## Goal

Make fixture, optional engineering-smoke, Task 03G pilot, and Task 03H full
scopes independently restartable and impossible to confuse with one another or
with Task 04 acceptance.

## Inputs

- accepted Task 03F.2 document transaction and completion interfaces;
- `docs/specs/restartable_corpus_extraction_v1.md` and executable v1 contract;
- the exact ordered Task 02 `model_corpus` scope;
- stable Task 03E.5 `deferred_cross_document` mention IDs and local outcomes;
- verified stage-one completions, inventories, aliases, targets, and terminal
  failure records for the declared scope.

## Outputs

- exact scope accounting and completion;
- unavailable-source catalog retaining failed source identities;
- deterministically ordered sealed corpus target index and completion;
- one resolution per eligible stable mention plus completion and inventory;
- byte-level stage-one immutability proof;
- candidate handoff with declared blocking policy and
  `task04_status: not_evaluated`;
- required-argument `extraction run-scope --run-spec PATH` and
  `make run-extraction-scope RUN_SPEC=PATH` interfaces;
- restartable index, resolution, and handoff attempts.

## Implementation plan

1. Validate the typed run scope and exact manifest-ordered subset.
2. Seal accounting only after every source has a terminal state; successful
   rows require verified candidates and failed rows cannot claim them.
3. Build the corpus index only from verified successful candidates while
   retaining failed-source catalog entries. Preserve cross-target alias
   collisions as ambiguity and seal deterministic order.
4. Resolve every eligible deferred mention exactly once. Ground unavailable and
   failed-target reasons in accounting; leave external documents out of scope.
5. Reverify all stage-one inventories before and after resolution.
6. Publish accounting, index, resolution, and handoff independently with
   completion-last no-clobber lifecycle and exact invalidation.
7. If separately approved, run no more than two predeclared small PDFs in an
   engineering smoke; process every page and retain its subordinate identity.

## Research / learning checkpoint

Explain why an immutable branch-and-join index makes invalidation and provenance
visible, and why failed sources remain catalog evidence rather than disappearing
from target resolution.

## Validation

- fixture, smoke, pilot, and production scope-identity separation;
- exact row closure, ordering, aggregates, and terminal-state requirements;
- deterministic index order, collisions, sealing, reuse, and invalidation;
- ineligible candidate and failed-source catalog behavior;
- resolved, ambiguous, missing, failed-target, unavailable, and external cases;
- exact mention coverage and byte-identical stage-one inventories;
- interruption before/after each independent publication;
- handoff blocking policies and rejection of Task 04 claims;
- optional separately approved whole-document smoke only;
- `make validate-extraction-contract`, `make fix`, `make check`, and
  `git diff --check`.

## Acceptance criteria

- Every declared source has exactly one terminal accounting row.
- Only verified successful candidates enter the corpus index.
- Changed accounting or candidate bytes invalidate index and resolution reuse.
- Cross-document records append to stable mention IDs without mutation.
- Handoff prerequisites remain distinct and Task 04 is not claimed.
- No representative pilot or full 35-source run occurs.
- The outcome requests explicit approval before Task 03G activation.

## Non-goals

- changing stage-one content or Task 03E.5 policy
- representative-pilot selection or production-configuration acceptance
- unapproved real-source execution or full-corpus extraction
- Task 04 usability review/freeze
- OCR, figure linking, distributed scheduler, database, or workflow engine
