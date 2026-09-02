# Task 03J: Run the Final Full-Corpus Extraction Attempt

Status: **complete** (2026-09-02).

## Abstract

Run the maintained extraction pipeline end to end across all 35 model-corpus
sources under one genuinely fresh namespace and production identity. Publish the
complete machine candidate and accounting handoff for Task 04A without reusing Task
03H production artifacts or changing extraction behavior during execution.

## Goal

Produce one internally consistent, restartable, validated full-corpus candidate
from the post-Task-03I code and configuration baseline.

## Inputs

- the closed [Task 03H](03h_run_full_canonical_extraction.md) first-attempt outcome
- the completed [Task 04](04_review_extraction_and_freeze_release.md) first-pass
  `records/finding_register.json` and `records/task03i_handoff.json` from
  `pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/`, plus the closed
  [Task 03I](03i_remediate_task04_review_findings.md) committed code, tests,
  production identity, recorded Task 04 input checksums, and validation outcome
- the immutable Task 02 source freeze and accepted Task 03 contracts
- a newly generated source-free run specification, namespace, and identity

## Outputs

- terminal records for all 35 ordered sources under one Task 03J corpus identity
- verified conversion, producer, downstream, document, and collection completions
  for every successful source, with explicit retained failures where applicable
- exact all-source accounting, warnings, timings, resource observations, and reuse
  evidence
- the machine-candidate and review-cache handoff required for Task 04A's final
  usability decision and release freeze
- a checksummed machine handoff that names the Task 03J corpus identity and the
  committed Task 03I production identity; [Task 04A](04a_regenerate_review_and_freeze_release.md)
  must use these to allocate a new final
  review-run namespace

## Research / learning checkpoint

Before execution, review the Task 03H operational evidence and Task 03I identity
inventory. Explain the selected chunk/resource policy, expected critical path,
restart boundaries, and stop conditions in the activation briefing.

## Plan / spec requirement

Prepare the complete source-free run plan before reading a source PDF or model. The
plan must freeze the source order, process configurations, generated identities,
fresh artifact root, resource guards, retry policy, ETA method, disk budget, and
failure-continuation behavior. Obtain explicit user approval before the first
source/model command.

The Task 03J namespace must be absent before preparation. Reuse is allowed only
between attempts created within Task 03J under compatible closed identities. Task
03H and Task 03I qualification artifacts are evidence only.

## Review pass

- verify complete source and terminal accounting
- verify containment, checksums, identities, page coverage, geometry, assets, and
  cross-record relationships
- verify restart and reuse behavior without reopening avoidable large payloads
- reconcile warnings and failures without converting them into silent success
- verify the candidate remains independent of Task 04 and Task 04A human dispositions

## Validation

- run the complete source-free repository gate and deterministic configuration check
  before execution
- verify each document completion and a bounded exact reuse checkpoint before moving
  past it
- stop safely on a material correctness, identity, resource, or publication failure;
  operationally continue past a source failure only when the frozen plan explicitly
  authorizes terminal failure accounting
- run final document, collection, and handoff validators and recompute aggregate
  counts from their owned artifacts

## Acceptance criteria

- all 35 sources have explicit terminal records under one Task 03J corpus identity
- all successful stages are checksum-verified, contained, identity-consistent, and
  restartable
- no Task 03H production completion contributes to Task 03J output
- no extraction code, policy, or configuration changes during the run without a
  separately closed task and new identity
- the final collection and Task 04A handoff pass their owning validators
- exact success/failure counts, pages, bytes, timings, warnings, and resource use are
  recorded
- Task 04A can make the independent final usability and release-freeze decision from
  the published handoff

## Outcome

Task 03J completed the ordered 35-source run under production identity
`exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773`.
All 48,341 pages reached checksum-verified document publication: 35 documents
finished `complete_with_warnings`, zero sources failed, and no source remained
unavailable. The run reused only compatible, checksum-valid components created
inside the Task 03J v4 lineage; it did not consume Task 03H production
completions.

The final collection is:

- scope `scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893`;
- target index `idxv1-eb1133607e64ed28305cf5d997ed213151697cd6d5d28f8d2ba56420208cba9a`,
  containing 98,704 entries for all 35 eligible candidates and no unavailable
  sources;
- resolution `resv1-b1cdbc0d27cd5f8b5e53d062639b8122ddd921f89b748e30cc810f3c02793c70`,
  containing 72 resolved, zero ambiguous, and zero unresolved deferred mentions;
  and
- ready handoff
  `handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325`,
  whose completion record is at
  `pipelines/brisbane_baylands/task_03h_clean_full_v4/document_publications/scopes/scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893/handoffs/handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325/records/completion_record.json`
  with SHA-256
  `8bd72f2712a20de5aa865575566e4d5b187d7fccc02ba02dd0f92d87bf04117a`.

The owning handoff validator verified all 35 documents and retained
`task04_status: not_evaluated`. A second collection invocation returned the same
handoff with the attempt-record count unchanged at four, proving checksum reuse
without republishing. Before execution, deterministic v3 and v4 configuration
checks passed, and the complete repository gate passed formatting, Ruff, strict
mypy over 397 source files, and 990 tests. Task 04A remains a separate,
explicitly activated human-usability and release-freeze task.

## Non-goals

- repairing newly discovered behavior inside the running task
- assigning human usability dispositions or freezing the release
- OCR, LLM repair, or visual-question answering
- extracting Final EIR Volume 4 comments and responses
- case authoring, retrieval, generation, or benchmark scoring
