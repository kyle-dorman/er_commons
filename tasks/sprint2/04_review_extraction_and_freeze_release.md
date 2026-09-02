# Task 04: Pilot Extraction Review and Qualify the Review Workspace

Status: **complete; first-pass review and independent human-maintainability gate
passed**. This task used
retained Task 03H evidence only as a diagnostic review dataset and hands accepted
extraction findings to [Task 03I](03i_remediate_task04_review_findings.md). The
post-03J regeneration, recheck, usability decision, and release freeze belong to
provisional [Task 04A](04a_regenerate_review_and_freeze_release.md).

## Abstract

Build and qualify a small, read-only local HTML workspace for user-led review
of document-processing evidence. Exercise it first against the mostly, but not
fully, extracted 35-source evidence retained from completed [Task
03H](03h_run_full_canonical_extraction.md). Review all retained document-
processing failures, deterministic samples of warnings, valid pages from every
source that has them, and a bounded mix of table evidence. Oversample the main
report because it contains the benchmark's primary evidence and a defect there
has greater downstream consequence than the same isolated defect in an
appendix.

This task tests the review workflow and produces an evidence-anchored finding
list. It does not accept the Task 03H corpus. Accepted extraction defects pass
to Task 03I; review-tool defects remain in Task 04. Task 03J then runs all 35
sources under a fresh namespace and identity. Task 04A owns all work that can
only be specified from the resulting Task 03J handoff.

## Goal

1. Prove that one person can inspect the extraction efficiently in a normal
   browser without navigating raw artifact trees or entering decisions into a
   labeling system.
2. Produce a complete, versioned, evidence-anchored list of first-pass Task 03H
   extraction findings for Task 03I, while keeping tool feedback and usability
   observations separate.

## Inputs

- the immutable Task 02 source release and all 35 source identities;
- the historical Task 03H evidence root
  `pipelines/brisbane_baylands/task_03h_clean_full_v3/`, as it existed during
  the first pass, including successful, partial, failed, retried, and
  incomplete document attempts; available canonical records; warnings; tables
  and table families; mappings; source PDFs; and render recipes;
- the completed Task 03H outcome and accepted Task 03 contracts;
- the existing candidate-neutral `human_review_support` selection and
  generated-render manifest concepts;
- user observations discussed in Codex during the first-pass review;

Task 03H was intentionally an incomplete diagnostic backing dataset. Missing or
failed publication was review evidence, not permission to fabricate a canonical
ID or describe Task 03H as the accepted corpus. The superseded Task 03H tree
was removed after Task 03J closure; its first-pass review records remain
historical evidence and are ineligible for Task 03J reuse.

## Outputs

### First pass against Task 03H

- a checksummed review-input inventory covering all 35 sources and distinguishing
  available, partial, failed, retried, incomplete, and absent evidence;
- a versioned deterministic selection manifest recording population counts,
  strata, sample sizes, ordering, selection reasons, and the exact main-report
  oversampling achieved;
- a locally generated, read-only HTML review bundle with four queues:
  document-processing failures, warning samples, valid-page samples, and table
  samples;
- requested page renders, overlays, and other review-cache derivatives only for
  selected items, with an exact generated-review manifest;
- one citeable review-item ID for every visible item so the user can discuss an
  issue in Codex without copying internal paths;
- a versioned finding register with stable finding IDs, exact evidence anchors,
  user-confirmed descriptions, and finding class;
- a separate review-tool feedback list describing navigation, presentation,
  missing context, or other workflow defects; and
- an exact Task 03I handoff containing only accepted extraction findings.

Bulk HTML, renders, and generated review artifacts remain under
`ER_COMMONS_DATA_ROOT` and outside Git. Gate A must document their exact
artifact-relative root and lifecycle before implementation. Only compact
contracts, schemas, tests, and summary documentation belong in the repository.

### Review UI geometry repair

The first-pass UI exposed a review-tool defect: on some pages, especially when
the browser constrained the page image by viewport height, the canonical boxes
were drawn against the full page container while the image was painted inside a
different `object-fit: contain` rectangle. The resulting scale mismatch made
boxes on the right edge visibly drift farther to the right, while boxes on the
left could appear displaced in the opposite direction. This was not evidence
that the underlying extraction geometry had moved.

The UI now gives each page an aspect-ratio-preserving surface sized from the
canonical page width and height. The PDF image and SVG overlay occupy that
same surface, and the image no longer applies an independent contain/max-height
layout. The repair is presentation-only: it does not alter canonical records,
table geometry, provenance, or review-item identity. The regression
`tests/test_build_task04_review_bundle.py::test_html_page_shares_aspect_ratio_surface_between_image_and_overlay`
ensures future HTML changes keep the image and overlay in one geometry frame.

The durable first-pass records use one immutable review-run root per pass:

```text
pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/
  records/
    input_inventory.json
    selection_manifest.json
    review_bundle_manifest.json
    finding_register.json
    task03i_handoff.json       # first pass only
  html/
  review_cache/
```

Gate A must add and validate the compact first-pass schemas under
`benchmarks/er_bench/schemas/task04_review/v1/` for the input inventory, selection
manifest, review-bundle manifest, finding register, and Task 03I handoff. Task 04A
owns the usability-registry and release-freeze records. Each JSON record is written completion-last and
contains the schema version, review-run identity, upstream identities, input/output
checksums, and relative paths. The HTML and render directories are disposable
derivatives of the records and never become authoritative review state.

A `reviewv1-` identity binds the `task03h_first` pass, source or candidate
identities, selection-policy digest, schema versions, and implementation identity.
Review-item IDs are deterministic within that run from the source identity, queue,
selection-policy digest, and exact evidence anchor. Finding IDs bind the review-item
ID, finding class, normalized expected and observed behavior, downstream consequence,
and inventory-derived typed evidence anchors. Human disposition/status is explicitly
excluded, so changing only status updates the same finding in place. Task
04A must allocate a new review run; first-pass IDs and anchors are references only,
never transferable evidence.

## Task 03 / Task 04 coupling

The task is deliberately re-entrant:

```text
Task 03H diagnostic evidence
  -> Task 04 first-pass tool pilot and review
  -> Task 03I finding disposition and bounded extraction repair
  -> Task 03J fresh 35-source extraction
  -> Task 04A regenerated review, usability registry, and release freeze
```

- Task 04 owns first-pass human inspection, review-tool quality, usability
  observations, and the finding register.
- Task 03I owns only accepted source-general extraction defects from the first
  pass. It may close without code changes.
- Task 03J owns the fresh all-source execution and machine handoff. It cannot
  reuse Task 03H production completions.
- A material finding never causes Task 04 to mutate extraction artifacts. It
  returns to the owning Task 03 stage and produces a new identity.
- Review-tool defects do not enter Task 03I. Source-authored problems and
  benchmark-usability observations remain distinct from extraction defects.
- First-pass Task 03H review items may seed a recheck, but their canonical IDs,
  checksums, and approval state never transfer automatically to Task 03J.

Task 04 closes its scope after the user-approved first-pass finding register.
Task 03I and Task 03J close independently before Task 04A begins.

## Review selection contract

Gate A must inventory the retained Task 03H evidence and freeze exact counts
before generating a review bundle. Selection is deterministic and reports its
complete population, but the review is diagnostic and risk-based rather than a
statistical quality estimate.

### Queue 1: document-processing failures

- expose every distinct retained failed, cancelled, incomplete, or terminal
  processing attempt that contributes to a source, including range, aggregate,
  producer, downstream, and document-publication failures, plus every source
  lacking the expected publication;
- group duplicate retries for navigation while preserving the complete attempt
  history, failure signature, distinct failure reasons, affected stage or range,
  and retained evidence;
- never sample away a distinct failure; and
- allow a partial source to appear in this queue and in the other queues when
  valid page evidence also exists.

### Queue 2: warning samples

- normalize warnings by owning process, stable diagnostic code, and message
  fingerprint before sampling;
- show population and per-source counts so repeated propagation cannot look
  like thousands of independent defects;
- normalize variable paths, IDs, page values, and similar instance-specific
  fields out of the message fingerprint where doing so preserves meaning;
- report normalized-class cardinality and its review workload at Gate A;
- include at least one deterministic example of every normalized warning class
  when the frozen cardinality remains bounded, otherwise use a user-approved
  risk-stratified cap while keeping the complete class population visible;
- include every novel or high-risk warning selected by the frozen severity
  policy; and
- use additional source/document-type strata and controls without reviewing
  every warning instance.

### Queue 3: valid-page samples

- include every source with available valid page evidence;
- select every available valid page when fewer than three are available;
  otherwise use a floor of three physical-PDF pages per source, covering early,
  middle, and late document regions before risk-triggered additions;
- distinguish physical PDF pages from printed labels and deduplicate chunk-
  overlap evidence by source plus physical page;
- cover ordinary body content as well as relevant layout, hierarchy, label,
  alias, reference, figure/caption, and table regimes; and
- allocate the main report at least three times the median per-appendix valid-
  page sample and cover its front matter and every major numbered chapter.

### Queue 4: table samples

- include bounded valid controls and warning-triggered examples;
- represent ordinary tables, complex geometry, multi-page families, zero/one/
  many region mappings, full-page numeric routes, layout-region routes, and
  continuation behavior where those populations exist;
- oversample main-report tables relative to the median individual appendix
  allocation when enough distinct candidates exist; and
- do not claim that this pilot verifies every table that later retrieval or
  case authoring may use. Only tables actually reviewed are verified and
  eligible. Later admission of an unreviewed table as evidence requires a
  separately versioned bounded review and registry extension.

One selected page may carry several queue reasons, but the HTML bundle should
present it once and expose all reasons. Gate A may increase these minimums after
inventory, but it must obtain user approval before reducing them or replacing
main-report chapter coverage with purely proportional sampling.

### Gate A decisions recorded 2026-08-26

The first-pass review uses one deterministic successful candidate per source for
page and table selections. Duplicate successful candidate identities remain in
the provenance inventory and failure/history queue, but do not multiply the
source-level page or table workload. The representative is selected by the
frozen candidate ordering recorded in the selection manifest.

Warning review is class-based, not occurrence-based: after normalization by
message fingerprint, select one deterministic example for every bounded class
while retaining total, per-source, and owner/code propagation counts. When the
same normalized message is emitted under multiple owner/code labels, it is one
review item with the labels shown as contributing pipeline observations. Thus a
warning repeated thousands of times or passed through multiple stages does not
produce duplicate human review items. This preserves prevalence and propagation
evidence without letting repetition dominate the review.

The table cap is six selected tables from the main report, plus the two largest
multi-page table families from each available appendix document. If a document
has fewer than two qualifying families, select all of its qualifying families;
if it has none, create no table item for that document. The first-pass retained
population therefore forecasts 6 main-report items plus 34 appendix items,
for 40 table items. Warning triggers annotate these items where possible; an
additional table item requires a separately approved extension to this cap.

## Review workspace contract

The workspace is a read-only inspection aid, not a labeling system:

- no forms, adjudication choices, accounts, database, browser-local
  authoritative state, or mutation of Task 03 artifacts;
- source and queue navigation, filters, previous/next links, nearby-page
  context, and stable item URLs or anchors;
- source render beside canonical text, hierarchy, tables, and the relevant
  machine observation;
- prominent source ID, candidate/attempt ID, physical page, printed label,
  applicable canonical IDs, and evidence checksums;
- a plain-language `why selected` explanation and population context on every
  item; and
- clear missing-evidence cards rather than broken links or silent omission.

Prefer generated static HTML, CSS, and the smallest replaceable JavaScript
needed for navigation. A standard-library localhost server may serve the
checksummed bundle when browser `file:` restrictions prevent safe relative
resource access; it must not become a persistent application service. Add no
runtime dependency unless Gate A demonstrates that the maintained standard-
library and existing project tools cannot meet a required behavior.

The user reviews in the browser and describes issues in Codex. Codex then
normalizes the discussion into the durable finding register; the HTML bundle
does not store decisions.

## Finding contract

Every finding must have:

- a stable finding ID and class: `extraction_defect`, `review_tool_defect`,
  `source_authored_issue`, or `usability_observation`;
- exact source, attempt/candidate, physical-page, warning, table/family, and
  canonical anchors where they exist;
- a concise user-confirmed description, expected behavior, observed behavior,
  and downstream consequence;
- links and checksums for the review item and backing evidence; and
- status showing whether the user accepted it for Task 03I, retained it within
  Task 04, or rejected it as not reproducible or not material.

Before Task 04 pauses, reconcile every issue discussed in Codex into the
register and obtain user approval of the exact extraction-finding subset sent
to Task 03I. Conversation alone is not a durable handoff.

The first-pass `task03i_handoff.json` is a checksummed projection of that approved
register. It contains only `extraction_defect` findings, their exact evidence anchors,
the finding-register digest, and the upstream Task 03H identities/checksums. Tool,
source-authored, and usability findings remain in the register but are excluded from
the handoff. Task 03I records its disposition against this handoff; Task 03J receives
the closed disposition and its digest before allocating a fresh production identity.

## Research / learning checkpoint

Before implementation:

1. Inspect the existing `human_review_support` models, requested-render
   manifests, extraction reports, and candidate-neutral comparison utilities.
2. Compare a self-contained static bundle with a standard-library local server
   against browser local-file restrictions described by [MDN's same-origin
   guidance](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Same-origin_policy).
3. Apply [WCAG 2.2 keyboard
   accessibility](https://www.w3.org/TR/WCAG22/#keyboard-accessible) and
   [logical focus-order
   guidance](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html) to
   queue and previous/next navigation.
4. Inspect primary documentation for the retained PDF renderer and any existing
   overlay utilities before adding rendering glue.
5. Explain in plain language why main-report oversampling is importance-weighted
   risk coverage, not an unbiased corpus estimate, and why review records must
   remain separate from immutable extraction records.

## Plan / gates

### Gate A: inventory and freeze the review specification

1. Validate the exact Task 03H evidence root without mutating it.
2. Inventory all 35 sources, attempts, available page/canonical evidence,
   warnings, tables, mappings, and reproducible render inputs.
3. Freeze the four queue populations, sample counts, ordering, random seed or
   deterministic selection rule, main-report oversampling, missing-evidence
   behavior, finding schema, and external artifact layout.
4. Present the selection and workload forecast to the user before rendering or
   implementation that reads source PDFs.

### Gate B: build and qualify the bounded review workspace

1. Extend existing candidate-neutral review support rather than create a
   parallel framework.
2. Generate the selection manifest and minimal HTML bundle from synthetic and
   source-free fixtures first.
3. After explicit user approval, render only the selected Task 03H pages and
   generate the complete checksummed bundle.
4. Run a short user-led tool-qualification sample spanning all four queues.
5. Correct only review-workspace defects and rerun its focused tests before
   beginning extraction review.

Gate B qualification correction (2026-08-26): user review rejected the first
presentation as insufficiently reviewable. The replacement bundle uses a wide
side-by-side source-page/canonical-evidence view with geometric block and table
overlays; renders canonical table cells; chooses content-rich early, middle,
and late pages instead of literal boundary pages; gives every warning class an
exact or explicitly labeled representative context page; and groups 43 retained
non-success attempts into nine source histories labeled as recovered or still
unresolved. All 116 warning classes have page context, all 110 valid-page items
contain canonical text, and the approved 40-family table sample remains six
main-report families plus up to two largest multi-page families per appendix.
The immutable Task 03H evidence was read but not changed.

Follow-up presentation correction (2026-08-26): table-family cards now expose
the retained parser attempts for every selected physical page, including
returned versus retained candidate counts. On pages where standalone canonical
text boxes fall inside a table rectangle, the review pane places the table grid
first and groups those overlapping text fragments in an explicit review section;
this preserves potentially useful evidence while distinguishing it from an
independent prose column.

### Gate C: complete the first-pass Task 03H review

Status: **complete**. The user accepted the first material extraction finding and the review
workspace reached a sufficient first-pass behavioral stopping point on
2026-08-26. Green behavior tests do not close this gate.

1. The user reviews the bundle and discusses observations in Codex.
2. Maintain separate extraction, tool, source-authored, and usability finding
   classes.
3. Reconcile every discussed issue, exact anchor, and user disposition.
4. Obtain approval of the complete first-pass register and exact Task 03I input.
5. Close Task 04 without accepting or freezing Task 03H.

## MVP outcome and maintainability gate

Task 04 qualified the four-queue review workspace against retained Task 03H
diagnostic evidence and incorporated the user-driven presentation corrections
recorded above. The review produced an accepted source-general table ownership
defect for Task 03I: verified full-page tables can retain duplicate standalone
canonical text inside their bounds. That established the behavioral MVP; task
closure followed only after the separate maintainability gate below.

The maintainability pass replaced the monolithic generator with typed,
responsibility-owned modules under `human_review_support.task04`, thin CLIs,
readable HTML/CSS/JavaScript assets, strict discriminated schemas, staged atomic
publication, recoverable finding updates, exact source/candidate/object anchors,
and an explicit maintainer runbook. Production discovery requires the sealed
35-source readiness scope and exact staged-catalog path, size, and checksum.
Review identity binds maintained code, schemas, rendering behavior, and package
versions including Pillow. The supported workflow can approve and close the
finding register without hand-editing authoritative JSON.

An independent closure audit found no remaining P1 or P2 maintainability or
traceability blockers. Source-free validation passed Ruff, strict mypy over 38
Task 04 production/CLI/test files, 62 focused Task 04 tests, all three CLI help
surfaces, the complete 982-test repository check, Task 03H deterministic config
generation, and `git diff --check`. No PDF, model, or corpus regeneration ran.

Task 04 closed only after the review implementation passed a separate
human-maintainability gate. A future maintainer can find one named
responsibility, understand its typed inputs and outputs, edit it without reading
one monolithic workflow, reproduce or diagnose a failed build from path-rich
records and logs, and validate the change through public package seams. The gate
requires bounded responsibility-owned modules, a thin CLI shell, readable HTML/
CSS/JavaScript assets, strict and runtime-validated record contracts, safe staged
publication, explicit identity dependencies, and behavior plus maintainability
tests. The independent review confirmed those properties.

After that gate closes, Task 03I owns the extraction-finding disposition, Task
03J owns the fresh extraction, and Task 04A owns all post-03J review regeneration
and release work.

## Review pass

- **Review utility:** Can the user understand why an item is present, inspect
  the relevant source and extracted evidence together, navigate without raw
  paths, and cite the item naturally in Codex?
- **Selection:** Does every source appear honestly, are failures complete, are
  warning populations visible, are valid controls free of survivorship bias,
  and is the main report materially oversampled?
- **Evidence:** Do physical pages, printed labels, canonical IDs, geometry,
  table mappings, attempt history, and checksums resolve to the declared input?
- **Task ownership:** Are tool defects confined to Task 04, extraction defects
  routed only through Task 03I, full execution confined to Task 03J, and the
  final release decision deferred to Task 04A?
- **Maintainability:** Is the generator narrow, typed, testable, understandable,
  restartable, and based on existing project concepts rather than a bespoke
  review framework?

## Validation

- deterministic selection and ordering under shuffled input discovery;
- exact all-35-source accounting, including no-page and partial sources;
- failure-attempt completeness and duplicate-retry grouping;
- warning normalization, population reconciliation, severity additions, and
  sample reproducibility;
- per-source valid-page floors, physical-page deduplication, main-report
  oversampling, and major-chapter coverage;
- table-stratum and multi-reason item coverage;
- source/candidate/render checksum validation and stale-anchor rejection;
- missing-resource and broken-link checks for every generated HTML item;
- keyboard-only navigation, visible focus, and logical focus order in a local
  browser;
- proof that the workspace writes no Task 03 artifact or authoritative browser
  state;
- focused tests plus the repository's routine formatting, lint, typing, test,
  deterministic-generation, and diff gates; and
- `git diff --check` for contract-only changes before activation.

## Acceptance criteria

### First-pass acceptance

- all 35 sources appear exactly once in the source inventory and honestly in
  every applicable queue;
- every retained distinct document-processing failure and its full retry
  history is inspectable;
- warning populations reconcile exactly and the frozen bounded warning policy
  has deterministic reviewed samples without disguising capped classes;
- every source with valid page evidence meets the valid-page floor;
- the main report meets the declared oversampling and major-chapter coverage;
- the table sample covers every available required stratum without claiming
  exhaustive table usability;
- every item has a stable review ID, selection reason, exact provenance, and
  checksummed backing evidence;
- the user can complete review in the local browser and cite findings in Codex
  without navigating raw artifact directories;
- review-tool findings and extraction findings are separately complete;
- the user approves the versioned finding register and exact Task 03I handoff;
  and
- no Task 03H artifact is called the accepted or frozen extraction release.

## Non-goals

- repairing extraction behavior inside Task 04;
- running the fresh full corpus outside Task 03J;
- regenerating review evidence from Task 03J or making the final usability and
  release-freeze decision, which belong to Task 04A;
- treating Task 03H as the final release candidate;
- reviewing every warning, page, or table;
- storing decisions, comments, or authoritative progress in the browser;
- building Label Studio configuration, a hosted service, accounts, permissions,
  a database, or a general review platform;
- OCR, VLM conversion, LLM repair, or visual-question answering;
- extracting Final EIR Volume 4 comments and responses;
- case screening, evidence authoring, retrieval, generation, or scoring; or
- treating main-report oversampling or the bounded review as a statistical
  estimate of corpus-wide error prevalence.
