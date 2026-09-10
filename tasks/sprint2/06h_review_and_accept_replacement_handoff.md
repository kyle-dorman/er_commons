# Task 06H: Review and Accept Replacement Handoff

Status: **provisional and inactive; revise from accepted Task 06G before review
execution. Mechanical handoff readiness is not human acceptance.**

## Abstract

Review changed F1, Appendix A, and main-document targets; reuse accepted human
review for provably unaffected evidence; and publish one explicitly accepted
replacement handoff/usability binding for Task 05G. The replacement preserves
Final-F1 edition warnings and distinguishes figure target identity from whether
text-only benchmark models can use the evidence.

The terminal result authorizes a later, separately scoped Task 05G consumer
update and replay. It does not run that replay or publish the final Task 05
inventory.

## Goal

- Close every required review item with evidence-backed human dispositions.
- Rebind unaffected accepted review through exact correspondence rather than
  repeating the whole-corpus review.
- Establish source and target usability independently from exact link identity.
- Accept one coherent replacement candidate through a compact explicit record.
- Give Task 05G exact inputs, warnings, and reconciliation expectations.

## Inputs and prerequisite gate

Read the umbrella, Tasks 06A-06G accepted outcomes, `docs/data_artifacts.md`,
`docs/architecture.md`, the human-review contract selected by 06A, and Task
05G's provisional replay contract. Resolve current code owners using Task
06B's completed filename mapping; do not assume historical names survived.

Baseline accepted review is `reviewv1-task03j-final-c17`, with closure beneath
`pipelines/brisbane_baylands/task_04_review/reviewv1-task03j-final-c17/gate_d/`.
Baseline Task 04D handoff is
`handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`.
Task 06A binds their exact completions, inventories, and review payload seals.
Do not change either accepted closure.

Task 06G supplies the proposed replacement mechanical handoff, document/source
identity correspondence, changed-target and link accounting, and exact source
and page references. Task 06C supplies F1 title/edition qualification and both
known revised-location references. Tasks 06D-06F supply repair evidence and
negative controls. Bind all inputs explicitly before generating a review view.

Task 05F's accepted partial outcome is
`rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83`:
511 mentions, 295 links, and 216 explicit nonlinks. The frozen impact population
includes 66 F1 mentions, 79 figure mentions, and 19 Chapter 8/9 mentions.
These populations describe review/replay expectations, not guaranteed links.

## Current implementation and contract owners

- `human_review_support`: candidate-neutral review selection, renders, findings,
  and dispositions. Reuse existing review interfaces.
- `document_records/document_references/reviewed_navigation.py`: sealed review
  evidence and exact source coverage used by relinking.
- `collection_processing/handoff_assembly.py`: mechanical readiness with
  `task04_status: not_evaluated`.
- `response_inventory/run_spec.py:Task04ReferenceBindings` and
  `reference_baseline.py`: current 05F consumer bindings and usability loading.

The existing consumer pins old IDs and a 35-source gate-D registry shape. Task
05G owns its replacement-binding implementation and resolver replay. This task
must deliver a reviewed explicit contract it can consume; do not silently edit
05F literals or replace old files to masquerade as the old accepted review.

## Outputs

1. A frozen bounded review specification and complete selection ledger.
2. Exact reviewed evidence references, human dispositions, and unresolved-risk
   accounting for all selected items.
3. A fresh usability registry bound to selected sources and target limitations.
4. A checksummed correspondence record rebinding accepted unaffected decisions.
5. One compact acceptance record naming replacement mechanical handoff, registry,
   correspondence, source-substitution evidence, and review closure.
6. A Task 05G handoff describing preserved inputs and expected reconciliation.

Generated views are derivatives. A render or view becomes authoritative review
evidence only when a disposition explicitly binds it and the review contract
seals it. Do not copy whole canonical payloads into the review registry.

## Research / learning checkpoint

Inspect existing review schemas and restart behavior before adding fields.
Explain why exact target resolution is different from evidence usability, why
an edition substitute needs explicit warnings, and why unchanged decisions can
be rebound only with evidence of correspondence. Cite primary PDF-rendering or
schema documentation when needed; use the existing maintained tools and avoid
a new review application or general review workflow framework.

## Plan / spec requirement

### Gate 1: freeze the review population and resource limits

Derive selections from accepted source and target evidence plus complete 06G
change accounting. Do not let whichever pages happen to be easy to render define
the population. Every ledger row names source, target/page, reason, evidence
references, expected review question, and required disposition.

Required selections include:

- Final F1 title, edition, structure, qualified internal material, and the exact
  candidate targets implicated by the 66 frozen references;
- Table 6 and Muni evidence associated with `Response SA-Caltrans-6` and
  `Response SA-Caltrans-9`, preserving response context and Final revision claim;
- both Appendix A duplicate pairs, physical pages 311/312 and 479/480, their
  neighboring structural context, and retained source heading blocks;
- main-document Chapter 8 and Chapter 9 starts, titles, first/last subsection
  boundaries, actual extents, and transitions to neighboring chapters;
- every distinct eligible caption-backed figure target, including its image and
  attached caption, plus the absent `Figure 4.8` control;
- accepted negative controls from 06D-06F and a bounded selected set of unchanged
  source/target evidence validating correspondence.

Freeze exact page/render ranges, resolution, maximum pages, elapsed/memory/thread
limits, disk budget, evidence destination, and resume command before any new
PDF/render access. Derive bounds from actual candidate sizes and prior rendering
evidence; do not invent runtime. Reuse matching accepted renders where their
source bytes, page, render settings, and evidence identity prove equivalence.
New source access/rendering requires its explicit bounded gate.

### Gate 2: verify unaffected review correspondence source-free

For every reused disposition, bind old review item and evidence seal, old source
and entity identity, selected source/entity identity, actual 06G correspondence,
review-policy compatibility, and reuse reason. Validate coverage and reject
ambiguous, missing, many-to-one unexplained, or dangling mappings.

Do not compare raw namespaced IDs and treat differences as changed content.
Apply the explicit entity mapping and compare substantive evidence fields.
Conversely, do not infer equivalence from similar titles or page numbers.
Changed F1 source evidence cannot inherit the wrong source's usability approval.
Merged Appendix A targets and new main-document targets require their declared
review, even when the source PDF bytes are unchanged.

If a review policy changed, identify which dispositions it invalidates rather
than blindly reusing or repeating every review. Preserve accepted old decisions
as historical evidence; write fresh bindings outside their closure.

### Gate 3: separately authorized targeted review

Use the maintained review interface and keep terminal human dispositions apart
from machine findings. Each required item must finish as accepted, accepted with
an explicit limitation, rejected/repair required, or another existing reviewed
terminal status. Missing review is not acceptance.

Review Appendix A's single logical chapter target while preserving both physical
heading blocks. Review main chapters as whole chapter targets with their own
provenance and extents, never aliases to Sections 8.1/9.1. Review figures from
their attached body captions and images, excluding TOC/list-of-figures evidence.

For F1, state Final edition and substitution reason at every appropriate source
and downstream handoff boundary. Substitute links default to
`usable_with_warning`. The two explicitly revised locations additionally name
the response and indicate revised Final content. No explicit revision in the
other 64 mentions is not evidence of Draft/Final equivalence.

Separate figure target identity, visual evidence quality, and model-support
eligibility. An exactly identified figure may remain
`unavailable_to_text_only_model`; captions are metadata unless they independently
state the substantive evidence. Do not promote image-dependent evidence into
text-only benchmark support simply because a figure alias now resolves.

A rejected item returns to its owning repair task with exact evidence and
invalidation scope. Do not alter production targets inside the review app.
A repaired candidate receives a new binding and only affected review is repeated.

### Gate 4: close usability and mechanical validation independently

Verify Task 06G's handoff is mechanically ready and that the review ledger has
complete terminal coverage. Validate fresh registry source identities against
the selected replacement scope, including Final F1 substitution evidence.
Preserve target-specific limitations separately when source-level status alone
cannot express them.

Record all known risks, unresolved specific targets, edition limitations, and
review reuse counts. A ready collection may still fail the human gate. A human
approval cannot repair an invalid inventory or mismatched candidate identity.
Only a candidate passing both boundaries may be proposed for acceptance.

### Gate 5: explicit acceptance and Task 05G handoff

Prepare a concrete compact acceptance record and present the candidate evidence
for explicit user acceptance. Write the acceptance pointer only after that
acceptance, outside the candidate's immutable managed closure. Bind the exact
handoff, registry, correspondence, review completion, source substitution,
validation summary, and accepted limitations. Repeat acceptance must validate
and reuse the same record; conflicting acceptance must fail closed.

The downstream handoff names unchanged accepted 05D/05E inputs and the accepted
05F partial candidate. It specifies that Task 05G updates the frozen consumer
bindings and replays accepted rules against the replacement upstream evidence.
It carries per-mention reconciliation expectations for all 511 outcomes,
including 66 F1 mentions, 79 figure mentions, 19 chapter mentions, Appendix A
changes, existing collisions, 11 comment-authored exclusions, and both Appendix
Q verification outcomes. Do not guarantee all F1 references link or downgrade
specific references to document targets for a better count.

Stop after accepted handoff publication. No automatic Task 05G execution follows.

## Stop and resume policy

Retain nonterminal review progress and exact evidence IDs. Resume matching
review packets without rerendering accepted evidence. Stop on source/target
binding drift, incomplete correspondence, conflicting dispositions, missing
review evidence, unexpected files, or exceeded render limits. A new candidate
invalidates only review whose evidence or policy actually changed, with an
explicit correspondence proof for everything reused.

Never infer acceptance from elapsed time, a mechanical completion, or absence
of findings. No accepted registry or source manifest may be overwritten.

## Validation

Synthetic tests cover complete/incomplete coverage, wrong candidate/source,
invalid mapping, incorrect reuse after source substitution, changed render
settings, dangling target restrictions, conflicting dispositions, registry
membership, acceptance without terminal review, and repeated/conflicting
acceptance. Test source-free resume with PDF reads/rendering disabled.

Run focused human-review/handoff tests, `make fix`, `make check`, and
`git diff --check` for implementation. After bounded review, verify compact
seals, exact record closure, counts, correspondence, and acceptance bindings;
do not rehash PDFs or repeat the entire visual review.

## Review pass and acceptance criteria

Independently inspect precision, edition warnings, whole-chapter extents,
figure usability, unaffected review reuse, and readable audit trails. Close
only with terminal dispositions, validated correspondence, a fresh coherent
registry, mechanically valid handoff, explicit user acceptance, and a complete
Task 05G contract. Record remaining unresolved targets honestly.

## Non-goals

Reextracting documents, editing accepted artifacts, resolver qualification,
Task 05G replay, Task 05H final publication, benchmark case eligibility decisions,
cleanup, commit, push, or a new review application.

## Outcome

Pending. Record selected/reused review counts, terminal dispositions and risks,
exact replacement handoff/registry/correspondence/acceptance identities,
validation, authorization evidence, and the Task 05G handoff location.

## Task 06B interface handoff

Both Task 06B gates now supply the maintained
[command map](../../docs/pipeline_commands.md) and
[executed owner map](../../docs/specs/task06b_gate2_executed_inventory.md).
Use explicit current requests with original per-source accepted manifests and
seals; historical recipe validation does not reopen removed implementation paths.
Document/collection v3 supports declared replacement membership. Compact checks
must retain the shared verification budget and must not claim new payload-byte
equality. This handoff updates interfaces only; the task's provisional policy and
separate source, conversion, replay or review authorization boundaries still apply.
