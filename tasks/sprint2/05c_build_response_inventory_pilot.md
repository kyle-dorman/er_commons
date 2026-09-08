# Task 05C: Build and Qualify the Response Inventory Pilot

Status: **provisional and inactive; begin only in a new chat with explicit authorization**.

## Abstract

Implement the smallest maintainable producer satisfying the accepted Task 05B
contract, then qualify it on a bounded vertical slice covering every observed
Volume 4 structural regime.

## Goal

Expose structural, scaling, recovery, and usability failures before committing
to the 744-page run.

## Inputs

- Accepted Task 05B specification, schemas, fixtures, and identity recipe.
- Task 05A representative page/range selection.
- Frozen `feir_volume_4` source record.

## Outputs

- typed package-backed producer exposed through the isolated proposed
  `er-responses build --run-spec <path>` command, with structured logging and
  restartable bounded range processing; the adapter must not modify the sealed
  Task 04D central CLI module;
- bounded `pilots/<pilotv1-id>/` candidate without copied source bytes;
- source-unit, anchor, membership, raw-reference, and diagnostic records for the
  selected ranges;
- fixture/evidence comparison, repeatability report, error register, runtime and
  storage observations, and human visual-review packet; and
- proposed 05D amendments based only on observed failures.

## Research / learning checkpoint

Document the maintained package boundary used for PDF text/layout access and
why project code remains narrow glue. Explain the restart unit and recovery
behavior in plain language.

## Plan

Revise this contract from Task 05B before activation. Implement and validate
source-free first. Present the exact bounded source-read plan before execution.
Run only the accepted pilot, stop on material contract failure, and route any
repair through a bounded amendment or remediation task rather than expanding
into full production. Obtain explicit user authorization before reading or
rendering the selected source PDF pages.

## Validation

- Cover observed start/end boundary forms across representative Volume 4
  General Responses 1-8 plus the General Response 9 placement exception and
  representative ordinary, cross-linked, meeting, continuation, multi-page,
  and ambiguous structures; do not extract all eight responses merely to
  satisfy the pilot.
- Check exact text and page anchors against source renders for the accepted set.
- Prove restart behavior and deterministic semantic output.
- Measure peak working space and verify no source or upstream payload copying.
- Complete maintainability review before approving the producer for a full run.
- Run focused tests, `make check`, and `git diff --check`.

## Review pass

- **Architecture:** Is the producer thin glue over a maintained PDF boundary?
- **Maintainability:** Are parsing rules, failures, restart behavior, and fixtures
  readable and independently testable?
- **Operations:** Are runtime, working-space use, logging, and recovery bounded
  enough for the complete run?
- **Source fidelity:** Do selected text, unit boundaries, and page anchors match
  the source across every observed structural regime?

## Acceptance criteria

- The pilot accounts for every selected page and region.
- Known source regimes produce correct units or explicit diagnostics.
- The producer is readable, typed, testable, restartable, and operationally
  bounded.
- No output-affecting repairs remain hidden inside the proposed 05D run.

## Non-goals

- Processing all 744 pages, resolving relationships or Draft EIR targets,
  outcome classification, or final publication.
- Preserving unlimited working attempts or turning pilot files into canonical
  inventory by renaming them.
