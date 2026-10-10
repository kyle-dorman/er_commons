# Historical Task 08 umbrella before final closeout

Superseded by the current umbrella; retained as execution history.

# Task 08 — Curate the benchmark through isolated group batches

Status: **08A–08F complete; 08G policy and 08H allocation approved. Final
release closeout is in progress.**

All 49 approved answers are retained. The user approved 19 development and 30 test
cases, with related topics distributed across splits, C002 in test and every
single-case appendix in test. [08G](../08g_review_case_clusters.md) owns the amended
bounded similarity review; [08H](../08h_serialize_and_freeze_benchmark.md) owns final
validation and serialization. The [08F result](../../../docs/specs/task08f_combined_review_result.json)
preserves all answer decisions; the [final result](../../../docs/specs/task08h_final_result.json)
will bind the completed release. This closeout starts no benchmark or judge runs.

The earlier stage amendments below remain historical context. Current stage
outcomes and the 2026-10-09 08G/08H amendments supersede their pending-stage
statements and provisional clustering requirements.

## Current 08D chat workflow — 2026-10-05

The [08D contract](../08d_review_group_claims.md) replaces per-group Label Studio
review for the new combined pass with two chats: complete batch preparation of
all 53 current approved questions, then human review of one prepared claim at a
time. Group membership remains provenance only. The review template repeats all
question, target-claim and source context. Historical health-risk work and its
reconciliation holds are preserved. The practice is stopped; updating the contract
does not start batch preparation, production labeling, new chats or later stages.

## Current 08C presentation amendment — 2026-10-01

Kyle authorized one combined 57-comment wording queue in saved export order,
including both health-risk questions. The [combined process](../../../docs/specs/task08c_combined_chat_review_v1.md)
supersedes separate-group presentation and the historical three-comment limit
for this pass. Require an explicit disposition before each next question. Keep
original group membership as provenance, do not remove similarity candidates,
and preserve historical approvals and downstream work. New health-risk wording
creates a separate version and a later reconciliation hold. No other stage,
project, chat, commit or push is authorized by this amendment.

## Abstract

Turn the accepted exclusive groups into human-approved reference cases through
repeatable stages across all participating batches, with question-by-question chat review at 08E. Separate candidate selection from
question rewriting, reuse versioned review interfaces, and keep labeling out of
the main coordination chat. After all groups finish, review similarities
and agree the final benchmark size and split before serialization. This task
replaces the former up-front 35-candidate gate and rigid 25-case ceiling.
Writing these contracts does not start implementation, projects, or labeling.

## Goal

Produce an auditable benchmark from faithful questions, substantive rebuttals,
and usable original Draft EIR evidence. Retain the agreed 49 accepted cases in the approved 19/30 split. Keep human
selection, evidence-based eligibility, evidence acceptance, and answer approval
explicit. Let cases drop without automatic backfilling.

## Inputs

- [Decision 005](../../../docs/decisions/005_task08_grouped_question_selection.md):
  42 exclusive groups, 606 candidate comments, a starting selection ceiling of
  96, exact grouping identity, and the health-risk priority exception.
- [Current inventory](../../../docs/specs/task07a1_final_result.json) and
  [06H handoff](../06h_review_and_accept_replacement_handoff.md), with inherited
  source, linkage, and usability limitations.
- [Review process](../../../docs/response_comment_human_review_process.md) and
  [Sprint 2](../../../docs/sprints/sprint2_brisbane_draft_eir_defense.md), especially
  source boundaries, eligibility, clustering, and evaluation separation.
- [Sealed pilot](../../../docs/specs/task07e_final_result.json): identify the six
  original comments for reentry, not preapproved Task 08 labels.
- [Artifact contract](../../../docs/data_artifacts.md),
  [architecture](../../../docs/architecture.md), and [task shape](../../README.md).

## Outputs

- Shared, versioned stage prompts, review templates, schemas, and narrow
  preparation/export validators, established only as each stage reaches first use.
- Per-group ranked inventories, source-bound proposals, human decisions, exact
  approved versions, stage exports, and restartable handoffs.
- A compact batch register recording group, stage, attempt, input/output identity,
  template/prompt version, project or chat reference, state, and next action.
- After group authoring closes: reviewed topic similarities,
  agreed split, role-separation and overlap audit, serialized cases, and a frozen release manifest.
- A derived attrition report retaining unreviewed, skipped, stopped, unresolved,
  approved, and final-selected counts separately.

Generated records live under an explicitly recorded Task 08 namespace beneath
`ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/`; final benchmark artifacts
use the documented `benchmarks/er_bench/` layout. Exact directories and schemas
are established during stage setup, not invented as completed outputs here.
Track only small reusable code, configs, schemas, fixtures, and documentation.
Reference sealed upstream material in place; do not modify or copy its releases.

## Subtasks and execution unit

| Contract | Unit and completion product |
| --- | --- |
| [08A — Rank candidates](../08a_rank_group_candidates.md) | One group's saved order with exact source/input bindings; no generated ranking explanations for future groups. |
| [08B — Select candidates](../08b_select_group_candidates.md) | One group's human selections and reasons, reviewed dispositions, full-inventory reconciliation, and chat completion confirmation. |
| [08C — Review question wording](../08c_review_group_questions.md) | **Done:** 53 approved, four deferred; all 57 decisions and exact wording preserved under the combined process amendments. |
| [08D — Review claims](../08d_review_group_claims.md) | Approved response assertions and direct/supporting relationships. |
| [08E — Review evidence](../08e_review_group_evidence.md) | Reviewed support/context sources and evidence-based human eligibility decisions. |
| [08F — Review answers](../08f_review_group_answers.md) | Exact reference answers approved in a dedicated chat. |
| [08G — Review similarities](../08g_review_case_clusters.md) | Whole-pool question review, closest-answer checks and approved topic-balancing policy. |
| [08H — Serialize and freeze](../08h_serialize_and_freeze_benchmark.md) | Agreed final size/split, verified exports, leakage audit, and release. |

Complete one numbered task across all participating batches before moving to the
next: 08B, then 08C, then 08D, then 08E, then 08F. This 2026-10-01
amendment supersedes the former group-through-08F default and preserves completed
health-risk work. A subsequent explicit 2026-10-01 exception authorizes only
C001/M-OSEC-241 and C002/O-Joint-44 to continue through
[08F](../08f_review_group_answers.md) in the existing chat after saved-export validation
and one export-bound human eligibility decision per case. It authorizes no other
group, project rebuild, relabeling, backfill, or 08G/08H.
The [current 08E plan](../08e_review_group_evidence.md) prepares research in batch,
then reviews one question at a time in chat without source deduplication. The explicit 08A preparation
exception permits all remaining groups to prepare saved handoffs ahead of review,
with deterministic comment-ID order and no model invocation for groups of at most
three candidates. Preserve valid completed handoffs and all later human gates.
The separately authorized 08B setup exception permits one blank project per
remaining group after shared intake qualification, ahead of human selections;
see the [setup result](../../../docs/specs/task08b_remaining_groups_result.json).
A group yielding no advancing cases records a zero-case
handoff; its downstream stages are not applicable, not missing approvals. The
batch register accounts for every group and every selected case before 08G.
No requirement to review all 606 candidates or identify 35 before authoring.
Unresolved authoring decisions keep a group open unless Kyle explicitly defers
those cases outside the current accepted pool and closes the batch. Preserve
that deferral separately from rejection or eligibility exclusion; it is a
terminal disposition for this pass, not resolution of the underlying question.
Record deferred counts and reasons, and require an explicit revision to reopen.

Contracts describe reusable stages; they are not duplicated 42 times. Except for the planned cross-batch 08E review, each
execution chat handles one stage for one group, for example “Health-risk group —
08C question wording.” Prepare a self-contained handoff with the contract,
allowed inputs, exact versions, pending decisions, and intended output location.
The user starts the separate chat. Do not create chats or send prompts as part
of contract drafting. The coordination chat receives compact status and process
questions, not candidate labeling or answer approval.

A batch can close while the stage remains available for other groups. Before a
stage's first use, revise its provisional contract from the accepted preceding
batch, qualify its interface, and activate that bounded execution. Under the current task-by-task sequence, reconcile every participating batch's
completion, stop or explicit deferral before advancing to the next task. Later
batches reuse qualified stages; the queue names the active stage and pending
batches. Earlier authorized health-risk progress is retained, not repeated.

## Shared review and versioning contract

08A is model-assisted prioritization, not eligibility classification. 08B, 08D
and 08E use shared stage-specific Label Studio configurations. 08C uses
[`task08c.chat_review.v1`](../../../docs/specs/task08c_chat_review_v1.md): source-only
chat iteration and explicit approval of exact displayed versions. 08F and 08G
also use chat presentation and saved-decision schemas. Astra (`gpt-6-astra`) supplies all
model-assisted ranking, wording, claims, evidence and answer proposals in the
authoring stages. 08G uses the separately approved bounded review. Humans own
selections, eligibility and acceptance. Record actual
model identity rather than attributing an unavailable or different model to Astra.
No paid API integration or live Label Studio model backend is required.

Each stage has two bounded parts:

1. **Prepare once, just before first use:** inspect maintained Task 07 components;
   adapt a shared template, input/output schema, prompt, and validator. Check
   actual queue behavior, proposal prefilling where applicable, saved human
   edits, and export against representative source-free fixtures.
2. **Execute with group identities retained:** 08E may pool source review under
   its named revision; other stages retain per-group execution. Bind input
   versions, generate data/proposals, validate,
   create a separate project from the existing stage template where applicable,
   obtain human decisions, and export only approved advancing records.

A batch chat must not silently change template code or field semantics. A needed
change returns to stage preparation as a named revision, with a compatibility
check and explicit decision about affected earlier batches. Flexible content
lengths and record counts are data, not reasons for a new template. Reject
empty approvals, stale versions, unresolved IDs, or exports different from the
content displayed. Keep proposals separate from human annotations.

The shared `task08b.selection.v2` form implements `task08.selection_gate.v2`: explicit
selection with a reason is the sole 08B human gate to 08C. Its source display
contains original comments and complete linked responses, with existing warnings,
ranking reasons, source limitations, and exceptions preserved in underlying
provenance rather than displayed panels or newly generated narratives. No separate
provisional-eligibility or stopping control remains. Reconcile saved annotations
against the full inventory after chat confirmation of review completion; unanswered
candidates remain unreviewed. Preserve all reviewed dispositions and the maximum
of three selections, allow fewer, and never infer selection from rank. Record both
template and process revision in the batch register and coordination handoff.

The question-wording chat receives original comments and comment-source warnings
only: no response text, response-based ranking rationale, prior answer, or
claims. Keep restricted provenance in a separate record outside that model
packet. Preserve chat proposal versions and verbatim feedback; null proposals
remain unresolved until human disposition. Flag user-added intent unsupported by
the comment. Freeze only exact displayed versions explicitly approved in chat.
Subsequent stages consume the same frozen human-approved question.
Any material question revision creates a new version and invalidates dependent
approvals for explicit re-review; no silent downstream scope changes.

Reenter the six pilot comments in their existing exclusive groups and count them
against the same selection ceiling. They receive fresh Task 08 decisions at
every stage, without automatic selection or reused acceptance. Verify membership
before execution; report any mismatch for an explicit grouping amendment rather
than silently adding a group or changing the 606/96 baseline. Prior Task 07
artifacts remain sealed; I-CJ-4 and I-EA-2 remain stopped.

## Research / learning checkpoint

Planning checked the maintained Label Studio guidance on
[configuration](https://labelstud.io/guide/setup.html),
[predictions](https://labelstud.io/guide/predictions.html), and
[exports](https://labelstud.io/guide/export.html) on 2026-09-30. A reusable
configuration and separately imported data fit shared stage templates. Predictions
and human annotations are distinct; verify saved annotations, not merely visible
suggestions. Recheck installed-version behavior at stage setup.

Preserve a brief learning note at each first-use qualification: what was reused,
why a narrow helper was needed, how a saved decision survives export, and the
tradeoff between stable schemas and explicit revisions. Saved model rankings
are reproducible review inputs; they do not guarantee identical model reruns.

## Plan / spec requirement

The table and shared contract are the umbrella plan. Each stage writes a short
implementation plan before its first setup, naming existing components,
interfaces, fixtures, and validation. Resolve only that stage's open details;
do not prebuild a workflow engine or all review interfaces. Refine later
contracts using real batch outcomes. This drafting turn implements nothing.

## Validation

- Drafting: check relative links, consistency with Decision 005 and Sprint 2,
  required task sections, and `git diff --check`.
- Execution: verify exact upstream versions and complete response closure;
  qualification checks must exercise real queue/save/export behavior before use.
- Verify the amended all-selected 08B inventory, one case per original comment,
  exact approved question reuse, and explicit reasons for stops and exclusions.
- Check explicit 08B selection and 08E human eligibility, approved claims, resolvable evidence,
  and explicit answer-version approval before final case acceptance.
- Validate the accepted 08G topic-review scope and exact approved 08H allocation;
  preserve shared-evidence limitations without claiming semantic independence.
- For eventual code changes use `make fix` and `make check`, plus appropriate
  targeted tests and actual interface qualification. Do not run source/model
  execution as a substitute for docs-only validation now.

## Review pass

Review the draft contracts for context isolation, human decision authority,
source/answer leakage, per-group resumability, template drift, and mutable
upstream assumptions. Review implementation maintainability at first setup and
schema compatibility at each explicit revision. No repeated retrospective or
additional Task 07 pilot is required.

## Acceptance criteria

- Every group has a terminal authoring status with saved selections and stops;
  every accepted case passed all applicable human gates.
- Six pilot comments were offered reentry without changing their historical
  records or bypassing selection. Any grouping mismatch is explicitly resolved.
- Whole-pool similarity review follows completed authoring.
- Final size and allocation are explicitly approved: 49 cases, 19 dev / 30 test.
- Frozen records resolve to their exact sources and approved versions; all
  decisions and counts can be reconstructed from durable handoffs.
- Remaining limitations and downstream Task 09 requirements are explicit.

## Non-goals

No new extraction, automatic label acceptance, automatic group backfilling,
retrospective reopening, visual-model expansion, forced table calculations,
benchmark retrieval/generation/judge runs, or permissions framework. No labeling
in the umbrella chat and no per-group bespoke review implementations.

## Historical initial outcome

The health-risk group completed [08A](../08a_rank_group_candidates.md#outcome--health-risk-group-only)
on 2026-09-30. Its validated four-candidate ranking and source packet are ready
for 08B. Health-risk 08B is now complete: M-OSEC-241 and O-Joint-44 selected,
M-OSEC-243 and M-OSEC-244 excluded, all four reviewed. The shared v2 interface
remains reusable; see the [completion and handoff](../../../docs/specs/task08b_health_risk_result.json).
Health-risk 08C is complete with two explicitly approved frozen questions under
`task08c.chat_review.v1`; see its [completion record](../../../docs/specs/task08c_health_risk_result.json).
Prior proposals and Label Studio preparation remain preserved. Health-risk 08D
has a qualified shared interface and a pending two-case claim-review project; see
its [readiness record](../../../docs/specs/task08d_health_risk_result.json). The remaining
groups are unprocessed; no 08E work is authorized.

## 08B all-selected closeout amendment — 2026-10-01

Kyle confirmed all groups finished and accepted every saved Selected candidate,
including groups above the original maximum. The
[all-group export](../../../docs/specs/task08b_all_groups_export_result.json) records
57 selections across 28 groups, native skips and untouched candidates separately.
This changes the closeout policy only: preserve prior health-risk work, require
qualified v3 handoff intake before remaining-group 08C, and keep later approval
and eligibility gates unchanged.
