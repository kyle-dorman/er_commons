# Task 03F.3: Implement the Scoped Corpus Resolution Workflow

Status: **provisional**. Revise from the accepted Task 03F.2 outcome and
activate only after its explicit approval gate.

## Abstract

Add scope-exact accounting over immutable stage-one candidates, seal a
checksummed target/alias index only after every source in that declared scope
has a terminal state, and publish an append-only cross-document resolution
pass without changing any stage-one byte.

## Required boundaries

- Fixture, optional engineering-smoke, Task 03G pilot, and Task 03H production
  scopes have distinct identities and accounting.
- Task 03H alone requires terminal records for all 35 model-corpus sources.
- Changed stage-one candidates invalidate the index and resolution result.
- Failed or missing targets remain explicit and cannot be represented as
  successful extraction or confident resolution.
- Any real-source engineering smoke requires separate approval, uses no more
  than two predeclared small PDFs, and processes all pages of each.
- The smoke cannot accept production configuration or activate Task 03G.

## Provisional validation

- deterministic index ordering, sealing, reuse, and invalidation;
- ambiguous, unavailable, failed-target, and external-document outcomes;
- exact scope accounting with candidate-handoff blocking policy;
- second-pass reproducibility and byte-level stage-one immutability;
- interruption before and after index and resolution publication;
- optional separately approved whole-document smoke; and
- `make fix`, `make check`, and `git diff --check`.

The accepted Task 03F.2 outcome must replace this provisional outline with the
exact inputs, outputs, schemas, commands, validation, and acceptance gates.
