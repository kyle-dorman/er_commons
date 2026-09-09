# Task 05D: Build the Complete Source-Unit Inventory

Status: **complete and accepted through Task 05D.1 remediation**.

## Abstract

Generalize the accepted Task 05C pilot orchestration to one complete Volume 4
working candidate, qualify that source-free behavior, and then, only after a
second authorization, process all 744 physical pages. Preserve the accepted
parser semantics and keep extraction, relationship resolution, and immutable
publication as separate transitions.

Task 05D produces one accepted working source-unit revision for Task 05E. It
does not create the final `inventoryv1` release.

## Goal

Produce a complete, deterministic transcription and structural inventory from
which later relationship graphs and review views can be derived without
ordinarily reopening the PDF.

## Authorization gates

Contract revision does not authorize either execution gate.

1. **Source-free implementation gate:** after explicit authorization, generalize
   the 05C run specification, orchestration, receipts, qualification policy,
   validators, fixtures, tests, and maintained command for stage `05d`. Use only
   checked-in fixtures, compact accepted metadata, and the accepted managed 05A
   and 05C evidence named below. Do not open, render, extract, hash, or copy the
   source PDF. Stop and present the gate outcome.
2. **Full-source gate:** only after Gate 1 passes and receives separate explicit
   authorization, open `feir_volume_4` and process exactly physical pages
   `1-744`. Compare and render those pages as specified below. Do not access
   Volume 5 or Appendix Q, traverse document-wide page-label or outline
   metadata, add pages, recompute the source checksum, or copy source bytes.

Neither gate authorizes cleanup, commit, push, Task 05E, or any later Task 05
stage. A terminal candidate may publish only after its required visual
dispositions close.

## Inputs and binding

- Accepted Task 05C completion
  `completionv1-5853fa56753aa6e032687cdd727c72bac1c8cec0abf34cc6d2fac1e9b358e571`,
  managed inventory
  `fileinventoryv1-58b8910295f4f3adf9675fb8ec98170e2977ed3d5026f3f02cf3b9c8a15620a6`,
  accepted activity
  `activityv1-5ef86aaad50e772cf07b9153e333e36672c503b3ab1c922a0290be9fb8a6df85`,
  and semantic digest
  `ac874b8671ea40a07d76602d35c404dc641bb2fd7338178eb838b5ff2af145d3`.
  The completion and inventory paths relative to the Task 05 artifact root are
  `pilots/pilotv1-5ef86aaad50e772cf07b9153e333e36672c503b3ab1c922a0290be9fb8a6df85/records/stage_completion.json`
  and
  `pilots/pilotv1-5ef86aaad50e772cf07b9153e333e36672c503b3ab1c922a0290be9fb8a6df85/records/managed_file_inventory.json`.
  They are respectively 940 bytes with SHA-256
  `b60e2f3454d8d62f1b9322e3ee3c5479f766c6a408f23cb01e08591f26cc41fb`
  and 1,125 bytes with SHA-256
  `ec95dcda606d8e448cdb0e0cda4ce3b2f1c1c20f9f38e1e7a03060e741bf9cd8`.
  The semantic digest is supplied by that candidate's managed
  `diagnostics/build_summary.json`; it is not a field of the completion record.
- Accepted 05C parser rules, run behavior, fixtures, qualification evidence, and
  producer-code, schema, and configuration bindings at repository commit
  `42ac3d5`.
- Accepted 05A structural-regime evidence at
  `working/05a/source_free_v1/records/structural_regime_profile.json`, inherited
  through 05C for signature comparison rather than added as a new 05D activity
  dependency role.
- Frozen `feir_volume_4` source record bound through Task 02 metadata: source ID,
  release membership, expected relative path, recorded checksum, byte size,
  744-page count, and terminal release state.

The 05D activity and managed-file inventory must carry identical ordered
dependency references with exactly the stage-owned roles `source_record` and
`task05c_completion`. Preflight verifies compact metadata and recorded sizes;
it does not hash the PDF or recursively hash upstream artifact trees.

## Frozen full-run scope and operating policy

- Declare one operational and semantic range, `1-744`, containing exactly 744
  one-based physical pages. This deliberately chooses coarse restart granularity
  because the accepted pilot shows the complete source pass is small, while
  splitting the source would introduce artificial unit-boundary risk.
- The sole range receipt remains replaceable working evidence. A reusable
  receipt must match the source and dependency bindings, run-spec, code, schema,
  and configuration digests, exact range, managed observation files and sizes,
  and range semantic digest.
- A failed receipt is never reusable. Preserve its bounded diagnostic and
  traceback. Do not retry a structural, schema, binding, determinism, or source
  fidelity failure automatically. A transient tool failure may be retried only
  by a deliberate rerun of the unchanged specification.
- Treat only the actual end of physical page 744 as the terminal source
  boundary. The pilot-only page-372 censoring rule and its
  `Response M-OSEC-137` warning must not carry into 05D.
- Require at least 1 GiB of free Task-05 working space at preflight and stop
  before publication if available space drops below 512 MiB. Record elapsed
  time, maximum resident memory, cache size, and candidate size. The pilot-based
  planning envelope is approximately three minutes, 200 MiB of cache, and an
  8 MiB candidate; these are review estimates, not acceptance limits.
- Retain the accepted 120-second page-specific Poppler timeout, visible INFO
  progress, strict cached-observation validation, atomic writes, and
  completion-last behavior.

## Outputs

One candidate under
`pipelines/brisbane_baylands/task_05_response_inventory/working/05d/<revision-id>/`
containing:

- `activity`, `page`, `page_continuation`, `marker_candidate`, `source_span`,
  `commenter`, typed `submission`, `source_unit`, `membership_claim`, raw
  `reference_mention`, `source_placement_exception`, and `diagnostic` records;
- one exact managed-file inventory and one terminal `stage_completion` record;
- one source-derived text store with stable IDs and no copied source or upstream
  payload;
- exact page/range and record-count accounting;
- a qualification report with per-page PDFium/Poppler comparison, render
  identity, review selection, and disposition;
- a derived structural-accounting report covering primary page states, marker
  dispositions, units, diagnostics, duplicate or discontinuous official-label
  sequences, and suspected omissions; the report introduces no new semantic
  record type and may not guess missing units;
- compact build, repeatability, failure, runtime, memory, and storage summaries;
  and
- after explicit user acceptance, one compact adjacent acceptance record naming
  the unchanged working revision, activity, completion, managed inventory,
  semantic digest, and its sole declared downstream consumer, Task 05E. The
  acceptance record is outside the candidate's managed-file closure and does
  not alter its completion or semantic identity.

`submission_kind` distinguishes `letter` and `meeting`; these are not separate
record types. Working output receives no `inventoryv1` identity or final-output
checksum pass.

## Research / learning checkpoint

Confirm the maintained `pypdfium2 5.12.1` page-local text-and-geometry boundary
and Poppler `pdftotext`/`pdftoppm 26.07.0` comparison and rendering interfaces
selected by Tasks 05A and 05C. Record observed versions and reopen package
selection only if an accepted 05A escalation trigger occurs.

Explain in plain language:

- why one `1-744` range is safer than introducing operational boundaries into
  source units for this small source;
- why source units close before graph resolution;
- how receipt reuse proves restart behavior without claiming a second
  independent source extraction; and
- why automated comparison and rendering cover every page while human review
  remains deterministic and risk-directed.

## Plan

1. In Gate 1, preserve the accepted source parser and generalize only the
   stage-specific orchestration needed for `05d`, its working namespace,
   dependencies, full-source scope, qualification policy, completion counts,
   and acceptance record.
2. Repair the dormant full-source count-key mismatch so the schema, producer,
   completion writer, and validator consistently use
   `general_response_units`. Require complete 05D count reconciliation rather
   than only General Response accounting.
3. Prove source-free schema validity, exact `1-744` scope enforcement, failure
   isolation, terminal-publication blocking, managed-file closure, receipt
   reuse, shuffled-input semantic determinism, and preservation of every 05C
   parser and maintainability test. Run repository validation and stop.
4. If Gate 2 is separately authorized, execute one fresh full-source pass. Use
   PDFium for bounded text and geometry, compare every page independently with
   Poppler, and render every page once at 96 DPI into replaceable cache.
5. Materialize the nonterminal candidate and review packet. Complete the exact
   human review population below without expanding source scope or changing
   parser policy during the run.
6. After review closes, publish the terminal working candidate, rerun the same
   specification using the complete range receipt without rereading the PDF,
   and require the same activity, completion, counts, and semantic digest.
7. Perform the review pass and present the named 05D working revision for
   acceptance. Only explicit user acceptance writes the adjacent acceptance
   record; Task 05E continues to bind the unchanged 05D completion. Do not
   activate Task 05E implicitly.

A material failure is a source-binding mismatch, invalid anchor or schema,
unclassified nonempty page, source structure the v1 contract cannot represent,
nondeterministic semantic output, unsafe restart state, unexplained omission,
or extraction/render disagreement that cannot be closed by an explicit visual
disposition. Preserve a compact stop record and route output-affecting repair
to a separate bounded remediation task; do not change policy inside the source
run.

## Deterministic qualification and human review

- Compare PDFium and Poppler tokens on all 744 pages. Token-multiset F1 below
  `0.98` is a review trigger, never an automatic transcription or rejection.
- Render all 744 pages once as grayscale PNG at 96 DPI into replaceable cache.
- Freeze the human review population before dispositions. It contains:
  - the first, lower-median, and last physical page for every populated primary
    page state;
  - the first and last page of every General Response 1-8 unit;
  - physical pages 1, 2, 4, 38, 39, 83, 84, 368-372, 551-555, 668-671, 721,
    722, and 744 retained as accepted high-risk and boundary controls;
  - both endpoint pages of the first, lower-median, and last cross-page
    continuation records by source order;
    and
  - every page triggered by low comparison score, missing or invalid geometry,
    title-page evidence, revision markup, `mixed_markers`, `layout_exception`,
    ambiguous marker, structural diagnostic, duplicate/discontinuous label
    sequence, or a signature not represented in the accepted 05A/05C evidence.
- Define the lower median as the item at zero-based index
  `(count - 1) // 2` after sorting by physical page and stable record identity.
  Deduplicate the union by physical page and review it in ascending order.
- Every required page must receive `accepted` or `requires_followup` with a
  reviewer, reason, and evidence identity. Any `requires_followup` disposition
  blocks terminal publication and routes the finding to a bounded remediation
  decision.
- A structural signature is the deterministic tuple of primary page state;
  sorted marker-kind/disposition pairs with multiplicity; sorted submission
  kinds with multiplicity; continuation-in and continuation-out booleans; and
  title, revision, blank, geometry-validity, and layout booleans. Gate 1 derives
  and freezes the accepted baseline from the exact managed 05A structural-regime
  profile plus the accepted 05C source records and qualification report. A new
  tuple triggers review; it becomes a stop condition only when the existing
  contract or parser cannot represent it correctly. A diagnostic or label
  finding contributes every physical page reached through its ordered subject
  IDs and source anchors; failure to resolve an implicated page is itself a
  material accounting error.

## Validation

- Before PDF access, validate fixtures and the exact full-run specification;
  reject every scope other than the single ordered range `1-744` and reject
  pilot namespaces, pilot dependencies, or pilot-only warnings in stage `05d`.
- Account for 1/1 completed range, 744/744 emitted pages, zero failed ranges,
  every marker disposition, and every 05D-owned record family through
  record-derived completion counts.
- Require exactly one General Response unit for each label 1-8, exactly one
  evidence-backed General Response 9 placement exception, and no synthesized
  General Response 9 unit.
- Require zero open operational range-boundary diagnostics. Any genuine
  ambiguity must use an allowed v1 diagnostic code, name its exact subjects,
  carry a terminal disposition for 05D, and appear in the structural-accounting
  report.
- Require every page to have one primary state. Non-unit content must be
  explained by that state or an explicit diagnostic; every accepted or rejected
  marker must have a disposition, and no suspected omission may disappear from
  accounting.
- Validate raw-text digests, half-open Unicode anchors, separate PDFium slots
  and geometry, source consistency, stable IDs, foreign keys, exact dependency
  agreement, managed-file closure, and shuffled-input semantic determinism.
- Validate every all-page comparison and render row, the exact deterministic
  human-review population, nonempty contained render files, review counts, and
  accepted terminal dispositions.
- Confirm receipt reuse with the unchanged run specification, code, schema,
  configuration, source binding, file sizes, and semantic digest. The reuse run
  must perform no PDFium, Poppler, rendering, source hashing, or source copying.
- Confirm no source or upstream payload is copied, the source PDF checksum is
  not recomputed, upstream trees are not recursively hashed, and no whole-output
  byte-hash pass is added.
- Run focused tests, the maintained response-inventory contract and 05D
  run-spec validators, explicit Ruff `C901`, `make check`, and
  `git diff --check`.

## Review pass

- **Completeness:** Is every page, marker, structural region, General Response,
  and suspected omission accounted for exactly once or explicitly diagnosed?
- **Source fidelity:** Do every-page comparisons and the required visual sample
  support the stored original text, boundaries, and anchors?
- **Operations:** Did the single-range receipt, space guards, failure isolation,
  completion-last publication, and no-source-read reuse behave as specified?
- **Maintainability:** Are stage policy, parsing rules, review selection,
  failures, diagnostics, validators, and fixtures readable, typed, independently
  testable, and within the accepted complexity gate?
- **Scope:** Did the run preserve raw mentions without relationship, target,
  response-outcome, eligibility, or publication policy?

## Acceptance criteria

- Both gates close in order and the full-source gate accesses exactly pages
  `1-744` without opening Volume 5 or Appendix Q.
- The candidate is schema-valid, closes exact page/range and record accounting,
  contains General Responses 1-8 plus the single General Response 9 placement
  exception, and carries no artificial range-boundary warning.
- Required visual review accepts transcription, segmentation, and anchors across
  every populated state and every triggered risk; no material or new regime
  remains undispositioned.
- Receipt reuse reproduces the accepted activity, completion, counts, managed
  closure, and semantic digest without rereading the source.
- Any remaining ambiguity is explicit, source-anchored, terminal for 05D, and
  bounded in the structural-accounting report.
- After explicit user acceptance, one adjacent acceptance record names the exact
  working revision and holds it fixed for Task 05E without changing candidate
  closure. An output-affecting change creates a new revision and revalidates
  downstream consumers; it does not mutate the accepted candidate.
- The source-unit candidate is sufficient for ordinary Task 05E graph
  construction without reopening the PDF.

## Source-free implementation gate outcome

Gate 1 completed on 2026-09-08 without opening, rendering, extracting, hashing,
or copying the source PDF. The accepted 05A and 05C compact artifacts were
binding-checked, and the accepted 05A profile contributed its regime vocabulary
while the accepted 05C records and qualification rows supplied 80 comparable
structural-signature digests.

The implementation adds a strict 05D v2 run specification and schema, the exact
single `1-744` range, all-page qualification evidence, deterministic review
selection and structural accounting, full-range receipt reuse, completion-last
publication, exact completion-count reconciliation, and an explicit post-review
acceptance command. The acceptance command is implemented but was not run; it
writes outside candidate closure only after a later explicit acceptance.

The source-free integration test uses 744 synthetic pages. Its first invocation
creates the frozen review packet without completion; its second invocation uses
the one complete receipt and cached qualification evidence, makes no reader or
qualifier call, and writes completion last only after all required dispositions
are accepted. The page-372 pilot warning is absent, while the actual page-744
source boundary remains terminal.

Validation evidence:

- 77 focused response-inventory tests passed;
- the maintained response-inventory contract accepted all 8 fixtures;
- `make validate-response-inventory-complete-spec` accepted exactly 744 pages
  with run-spec SHA-256
  `262c76b75da81aa1cdc1fd8e7915b7e71e019fc5543efe61f3cdbf683102c5a9`;
- source-free accepted-artifact binding and signature reconstruction passed;
- explicit Ruff `C901`, all Ruff checks, and mypy passed;
- `make check` passed all 1,298 repository tests; and
- `git diff --check` passed.

One full range is operationally safer here because there is no artificial
restart edge at which a source unit can be censored. Source units close before
graph resolution so transcription and boundaries remain independently
reviewable. Receipt reuse proves restartability from the same frozen evidence;
it does not claim an independent second extraction. Automated comparison and
rendering therefore cover every page, while human effort remains reproducible
through the frozen controls, state samples, continuation samples, and
evidence-triggered population.

Gate 2 was separately authorized on 2026-09-08 and stopped at nonterminal
review. Its exact outcome is recorded below.

## Full-source gate stopped outcome

Gate 2 was explicitly authorized on 2026-09-08 and accessed only
`feir_volume_4` physical pages `1-744`. It did not access Volume 5 or Appendix Q,
traverse document-wide labels or outlines, recompute the PDF checksum, or copy
source bytes.

The first invocation under Gate 1's original code identity wrote a complete
range receipt for activity
`activityv1-79be12fc60258f66af92ec10e34c77e389b5bce9e09c6b387c6d7c2513f73afc`.
It was deliberately interrupted before qualification or candidate publication
when the pre-publication review found missing candidate-size evidence and a
partial-publication recovery risk. That old cache is preserved and was not
reused after the source-free repair changed code identity.

The repaired specification has SHA-256
`46690ce1bb75dbcfff95a06f984f1da1820a2c364e0491ab4f67c3179a8eed7c`.
Its fresh full-source invocation produced activity
`activityv1-03b3cd8a0d71a4ff166cbf27d5628118ef3372f6555bd1b1d232f7bdbbd1f281`
and stopped correctly at `review_required`. Preserved evidence contains one
complete exact-range receipt, 744 ordered observations, 744 PDFium/Poppler
comparison rows, 744 nonempty 96-DPI renders, 2,028 source units, 4,069 marker
candidates, zero diagnostics, and a frozen 675-page review population. No
managed inventory, completion, terminal candidate, review disposition file, or
acceptance record was published.

Review confirmed two structural findings:

- Physical page 682 visibly contains italic `Comment O-SAMCEDA-7`, followed by
  `Response O-SAMCEDA-7`. The parser retained the comment marker as
  `needs_review` and emitted the response unit but omitted the comment unit.
  This is a material, source-anchored inventory omission and cannot receive an
  `accepted` disposition.
- Physical pages 155-157 contain `Comment SA-CHSRA-29` and its discussion, but
  the source itself has no `Response SA-CHSRA-29` heading before
  `Comment SA-CHSRA-30`. Structural accounting correctly reports the missing
  response label. The inventory may not invent a unit; the anomaly needs an
  explicit diagnostic/terminal-policy decision.

The low PDFium/Poppler scores inspected during the stopped review corresponded
to legible revision markup, tables, figures, or superscript footnotes rather
than unreadable renders. Broad review stopped after the material omission was
confirmed, so the remaining frozen population was not blanket-dispositioned.

Per the contract, output-affecting repair must occur in a separate bounded
source-free remediation decision. A changed parser or diagnostic policy creates
a new code identity and cannot reuse this activity's receipt as proof for a
terminal candidate. Gate 2 therefore remains incomplete: receipt-reuse
publication, full review closure, candidate validation, and user acceptance
have not occurred.

The remediation should also move the existing periodic Poppler progress log
from the 05C qualifier to the 05D all-page qualifier and reconcile the current
warning-free completion policy with the contract's treatment of a genuine
source-label ambiguity. These are source-free changes; neither authorizes a new
PDF pass.

The bounded remediation is specified by
[Task 05D.1](05d1_remediate_full_source_inventory_findings.md). Its contract
was accepted and its R1 source-free implementation and validation gate
completed on 2026-09-09. Its production rules are source-independent; the
stopped run's labels and pages remain regression evidence, not parser,
completion, or acceptance policy. The changed identity rejected both stopped
receipts. Separately authorized R2 then completed one fresh exact `1-744` run,
all required visual review, source-free receipt-reuse publication, and a final
reuse verification. After the R3 code-quality repairs, a separately authorized
post-R3 replay reproduced the same topology and exact visual evidence under the
new identity. The exact terminal identities, counts, and explicit acceptance
pointer are recorded in Task 05D.1. Task 05D is complete and accepted; Task 05E
remains inactive pending its own revised contract and authorization.

## Non-goals

- Immutable `inventoryv1` publication or final-output hashing.
- Intra-Volume relationship resolution, Draft EIR target resolution, derived
  linked views, or response-outcome, eligibility, clustering, or benchmark
  decisions.
- Appendix Q or Volume 5 extraction, global commenter deduplication, fuzzy or
  model-based parsing/linking, OCR/model escalation without a separate decision,
  or a workflow framework.
- Cleanup, commit, push, or activation of Task 05E.
