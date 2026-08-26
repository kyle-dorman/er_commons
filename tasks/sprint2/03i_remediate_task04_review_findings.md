# Task 03I: Disposition Task 04 Extraction Findings

Status: **provisional; waits for the first-pass [Task
04](04_review_extraction_and_freeze_release.md) review findings**. This task may
close as a documented no-op when review identifies no accepted extraction defect.

## Abstract

Disposition the extraction-pipeline findings produced by the user-led Task 04
review of Task 03H evidence. Implement only findings that Task 04 classifies as
source-general extraction defects that must be corrected before the next complete
run. Keep review usability decisions in Task 04 and full-corpus execution in Task
03J.

## Goal

Produce a closed, reviewable disposition for every Task 04 finding that could
affect the Task 03 extraction, with bounded repairs and regressions where needed.

## Inputs

- Task 04's user-approved first-pass `records/finding_register.json` and
  `records/task03i_handoff.json` from
  `pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/`, including the
  handoff digest and exact evidence anchors
- the completed [Task 03H](03h_run_full_canonical_extraction.md) outcome
- the maintained source-free pipeline and tests at Task 03I activation
- accepted Task 03 contracts and durable decisions implicated by a finding

## Outputs

- a disposition for each in-scope finding: repair, accepted limitation, duplicate,
  not reproducible, review-only usability issue, or out of scope
- source-general code, configuration, contract, and regression changes for every
  accepted repair
- an identity-impact inventory stating which Task 03J stages must be fresh
- a checksummed disposition record that names the input handoff and finding-register
  digests
- an outcome that either records the validated repairs or explicitly closes no-op

## Research / learning checkpoint

For each accepted defect, inspect the owning stage contract and primary package
documentation before selecting a repair. Record why the failure is an extraction
defect rather than a Task 04 usability judgment, and explain the repair invariant in
plain language.

## Plan / spec requirement

Before implementation, freeze the exact input finding IDs and map each one to its
owning stage, reproducible evidence, expected behavior, identity impact, regression,
and disposition. Ask the user before broadening beyond those findings or running
source PDFs/models.

## Review pass

- verify every change is source-general and does not encode a document-specific
  exception unless an existing accepted contract explicitly permits one
- review ownership, typing, failure diagnostics, restart behavior, and identity
  coverage separately from behavioral correctness
- confirm that findings left to Task 04 cannot alter Task 03J extraction bytes

## Validation

- run focused regressions for every accepted repair
- run the repository's source-free formatting, lint, typing, test, deterministic
  generation, and diff checks
- use only the smallest explicitly authorized source/model qualification needed to
  prove a repair; preserve its lineage separately from Task 03J

## Acceptance criteria

- every supplied extraction finding has one explicit disposition and evidence
- every repaired behavior has a source-general regression and complete identity
  ownership
- maintained code meets the repository's readability and ownership standards
- no Task 03H completion is promoted into Task 03J
- Task 03J has an exact, closed code/configuration baseline to execute
- if there are no accepted extraction defects, the task closes with a no-op outcome
  and Task 03J proceeds unchanged

## Non-goals

- defining or executing Task 04's review process
- deciding final document, page, table, or corpus usability
- rerunning all 35 documents or assembling the final corpus
- opportunistic extraction changes not anchored to a Task 04 finding
- freezing the accepted extraction release
