# Task 03F.2: Generalize the Restartable Document Stage

Status: **provisional**. Revise from the accepted Task 03F.1 contract and
activate only after its explicit approval gate.

## Abstract

Replace Appendix-P-only production constraints with manifest-selected,
contract-bound document inputs and implement one atomic, restartable stage-one
transaction. Simplify the runtime by deleting obsolete or duplicate code that
the approved Task 03F.1 inventory proves has no accepted caller, identity, or
verification responsibility.

## Required boundaries

- Preserve accepted Appendix P output exactly under the Task 03F.1 comparison
  and identity-normalization contract.
- Generalize mechanism, not corpus-wide hierarchy acceptance.
- Keep one complete PDF as the publication unit.
- Remove ambiguous Appendix P CLI defaults from production entrypoints.
- Do not implement the corpus target index or second pass.
- Do not execute new real-source PDFs or activate Task 03F.3 without explicit
  approval.

## Provisional validation

- fixture-level source selection across multiple document identities;
- interruption before and after atomic publication;
- checksum-valid reuse plus stale, partial, and conflicting output rejection;
- deterministic failure retention and retry classification;
- exact accepted Appendix P semantic/cross-reference preservation;
- code-inventory and caller tests for every approved deletion; and
- `make fix`, `make check`, and `git diff --check`.

The accepted Task 03F.1 outcome must replace this provisional outline with the
exact inputs, outputs, removal list, validation commands, and acceptance gates.
