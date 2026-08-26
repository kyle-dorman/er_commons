# Task 04A: Regenerate the Final Review Dataset and Freeze the Release

Status: **provisional; blocked on completed Task 03I and Task 03J handoffs**.
Revise this contract from those accepted outcomes before activation. Do not
infer final identities, paths, record shapes, or checksums in advance.

## Abstract

After Task 03J completes its fresh 35-source extraction, generate a new document
review dataset bound only to the Task 03J corpus and evidence identities. Recheck
the accepted Task 04 extraction findings against their Task 03I dispositions,
review fresh stratified and risk-triggered evidence, record human usability
separately from immutable machine artifacts, and either freeze the accepted
release or stop on a material defect.

This is a new review run, not a continuation of the Task 03H-backed Task 04
bundle. Task 04 items may identify what needs rechecking, but their canonical
IDs, checksums, page anchors, renders, and approval state cannot transfer.

## Goal

1. Produce a deterministic, reviewable dataset derived from the completed Task
   03J handoff without relying on conversation history or stale Task 03H anchors.
2. Verify every applicable Task 04 extraction finding after Task 03I remediation
   and inspect fresh all-source risk samples.
3. Publish a separate human-usability registry and an exact release-freeze
   record, or stop with an evidence-anchored remediation decision.

## Prerequisites and inputs

Activation requires the completed outcomes, validators, and immutable handoffs
from:

- [Task 04](04_review_extraction_and_freeze_release.md): the approved first-pass
  finding register, exact Task 03I handoff, review selection policy, and qualified
  review-workspace implementation;
- [Task 03I](03i_remediate_task04_review_findings.md): the closed disposition of
  every accepted extraction finding and its disposition digest; and
- [Task 03J](03j_run_final_canonical_extraction.md): the fresh corpus identity,
  all 35 terminal source records, machine-candidate handoff, canonical manifests,
  checksums, validator results, and reproducible render inputs.

The following dependencies are intentionally unresolved until Task 03J closes
and must be recorded during Task 04A activation:

- the exact Task 03J corpus, candidate, source, attempt, and implementation
  identities;
- artifact-relative paths and checksums for canonical pages, text, tables,
  table families, warnings, provenance, parser-attempt evidence, and render
  inputs;
- the final Task 03J handoff schema and validator interface;
- which Task 04 findings remain applicable and the exact Task 03J evidence that
  can recheck each one; and
- any new warning, failure, table, geometry, or provenance populations that
  require a revised risk stratum.

If any prerequisite is absent or ambiguous, stop and repair the owning upstream
handoff. Do not reconstruct it from Task 03H artifacts or conversation history.

## Outputs

- a new immutable `reviewv1-` run whose identity declares the `task03j_final`
  pass and binds the exact Task 03J inputs, policy digest, schemas, and review
  implementation;
- checksummed input inventory, deterministic selection manifest, generated
  review-bundle manifest, HTML workspace, and selected render cache;
- an explicit recheck record for every applicable first-pass extraction finding;
- fresh findings and an unresolved-risk report, if any;
- a usability registry keyed by Task 03J corpus and source identity, with page,
  table, or family dispositions only for evidence actually reviewed; and
- a release-freeze record pinning the accepted candidate and all review evidence,
  or a stop record that routes a material defect to a new bounded remediation
  task.

Bulk HTML, renders, and review-cache derivatives remain under
`ER_COMMONS_DATA_ROOT`. Compact schemas, tests, task outcomes, and summary
documentation belong in Git. Task 03J machine artifacts remain immutable.

## Research / learning checkpoint

Before activation:

1. Read the closed Task 03I and Task 03J outcomes and inspect their owning
   schemas and validators rather than assuming the provisional field list above.
2. Compare the final Task 03J handoff with the Task 04 first-pass inventory and
   document how stale evidence is rejected and findings are re-resolved.
3. Recheck the maintained renderer and overlay coordinate contracts, including
   rotated and landscape pages, before trusting visual review geometry.
4. Explain in plain language why a new corpus identity requires a new review
   dataset and why reviewing a sample supports only the recorded usability
   decisions, not a corpus-wide error-rate estimate.

## Plan / gates

### Gate A: activate from closed upstream handoffs

1. Validate the Task 03I disposition and Task 03J handoff with their owning
   validators.
2. Record every exact dependency listed above and reject stale Task 03H-derived
   identities, checksums, pages, or render inputs.
3. Revise this provisional contract to the actual handoff shape and freeze the
   final selection, recheck, artifact, and stop policies.
4. Present the expected review workload before reading source PDFs or producing
   renders.

### Gate B: add and qualify the final-pass generator mode

1. Extend the Task 04 generator with an explicit `task03j_final` mode rather
   than cloning the review framework.
2. Validate selection and record generation on source-free fixtures, including
   stale-anchor rejection and finding re-resolution.
3. Preserve the qualified side-by-side UI, canonical/table overlays, parser
   attempt explanations, warning normalization, and shared image-overlay
   geometry frame from Task 04.

### Gate C: generate and review the Task 03J dataset

1. Allocate the new review identity and generate the deterministic inventory,
   selection, HTML, and selected render derivatives.
2. Recheck every applicable Task 04 extraction finding.
3. Review fresh per-source, warning, failure, page, table, and risk-triggered
   evidence under the frozen policy.
4. Record user-confirmed findings and usability dispositions outside the Task
   03J machine records.

### Gate D: decide and freeze

1. Reconcile all 35 sources and every reviewed item with exact checksums.
2. Publish the usability registry and unresolved-risk report.
3. Freeze only if no material defect remains; otherwise publish a stop record
   and route the defect to a separately approved remediation task.

## Review pass

- **Handoff integrity:** Can every selected item be regenerated from the declared
  Task 03J records without Task 03H evidence?
- **Recheck integrity:** Does every applicable first-pass finding resolve to new
  Task 03J evidence and the exact Task 03I disposition?
- **Review utility:** Are source content, canonical text, tables, parser attempts,
  warnings, failures, and geometric overlays understandable and actionable?
- **Release boundary:** Are human dispositions separate from machine artifacts,
  and does the freeze pin exactly what was reviewed and accepted?
- **Maintainability:** Is final-pass support a narrow extension of the qualified
  review generator with focused tests and no parallel framework?

## Validation

- owning Task 03I and Task 03J validators pass before selection;
- deterministic selection and byte-stable compact records under shuffled input
  discovery;
- exact all-35-source terminal accounting;
- stale Task 03H identity, checksum, anchor, and render-input rejection;
- one explicit outcome for every applicable first-pass finding;
- warning/failure population reconciliation and declared sample coverage;
- per-source page floors, main-report oversampling, and required table strata;
- source/canonical/table overlay checks on portrait, landscape, and rotated pages;
- no broken HTML resources and keyboard-accessible review navigation;
- no writes to Task 03J artifacts or authoritative browser state;
- focused tests, routine repository checks, deterministic-generation checks, and
  `git diff --check`.

## Acceptance criteria

- the review run binds only to validated Task 03J identities and checksums;
- all 35 sources have explicit terminal and human-usability dispositions;
- every applicable Task 04 extraction finding has a closed Task 03I disposition
  and an exact Task 03J recheck;
- reviewed tables are explicitly verified or rejected, while unreviewed tables
  remain unverified and ineligible until a separately versioned review extends
  the registry;
- the usability registry remains separate from Task 03J machine records;
- the release-freeze record pins the Task 03J candidate, registry, selection,
  generated-render manifest, findings, and unresolved limitations; and
- a materially unusable main report or required source produces an explicit stop
  rather than silent exclusion or a prefilled usable disposition.

## Non-goals

- rerunning or repairing extraction inside Task 04A;
- reusing Task 03H production artifacts, review anchors, or approvals;
- reviewing every warning, page, or table;
- storing authoritative decisions in browser state;
- building a hosted review platform or general labeling system;
- OCR, VLM conversion, LLM repair, or visual-question answering; or
- case screening, evidence authoring, retrieval, generation, or scoring.
