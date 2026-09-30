# Task 08 — Curate the benchmark through isolated group batches

Status: **Contracts drafted; execution not started. Only 08A is the active next
contract. 08B–08H are provisional until their first-use readiness review.**

## Abstract

Turn the accepted exclusive groups into human-approved reference cases through
repeatable, single-group review stages. Separate candidate selection from
question rewriting, reuse versioned review interfaces, and keep labeling out of
the main coordination chat. After all groups finish, review cross-group clusters
and agree the final benchmark size and split before serialization. This task
replaces the former up-front 35-candidate gate and rigid 25-case ceiling.
Writing these contracts does not start implementation, projects, or labeling.

## Goal

Produce an auditable benchmark from faithful questions, substantive rebuttals,
and usable original Draft EIR evidence. Aim for 25 accepted cases without
forcing that yield or discarding good cases merely to reach 25. Keep human
selection, two-pass eligibility, evidence acceptance, and answer approval
explicit. Let cases drop without automatic backfilling.

## Inputs

- [Decision 005](../../docs/decisions/005_task08_grouped_question_selection.md):
  42 exclusive groups, 606 candidate comments, a starting selection ceiling of
  96, exact grouping identity, and the health-risk priority exception.
- [Current inventory](../../docs/specs/task07a1_final_result.json) and
  [06H handoff](06h_review_and_accept_replacement_handoff.md), with inherited
  source, linkage, and usability limitations.
- [Review process](../../docs/response_comment_human_review_process.md) and
  [Sprint 2](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md), especially
  source boundaries, eligibility, clustering, and evaluation separation.
- [Sealed pilot](../../docs/specs/task07e_final_result.json): identify the six
  original comments for reentry, not preapproved Task 08 labels.
- [Artifact contract](../../docs/data_artifacts.md),
  [architecture](../../docs/architecture.md), and [task shape](../README.md).

## Outputs

- Shared, versioned stage prompts, review templates, schemas, and narrow
  preparation/export validators, established only as each stage reaches first use.
- Per-group ranked inventories, source-bound proposals, human decisions, exact
  approved versions, stage exports, and restartable handoffs.
- A compact batch register recording group, stage, attempt, input/output identity,
  template/prompt version, project or chat reference, state, and next action.
- After group authoring closes: reviewed clustering decisions, cluster graph,
  agreed split, leakage audit, serialized cases, and a frozen release manifest.
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
| [08A — Rank candidates](08a_rank_group_candidates.md) | One group's saved source-bound order and ranking reasons. |
| [08B — Select candidates](08b_select_group_candidates.md) | One group's human selections, first eligibility pass, skips, and stopping point. |
| [08C — Review question wording](08c_review_group_questions.md) | Selected comments rewritten from comment-only inputs and exact wording approved. |
| [08D — Review claims](08d_review_group_claims.md) | Approved response assertions and direct/supporting relationships. |
| [08E — Review evidence](08e_review_group_evidence.md) | Reviewed support/context sources and second human eligibility decisions. |
| [08F — Review answers](08f_review_group_answers.md) | Exact reference answers approved in a dedicated chat. |
| [08G — Review clusters](08g_review_case_clusters.md) | All-group relationship review in chat after all authoring batches finish. |
| [08H — Serialize and freeze](08h_serialize_and_freeze_benchmark.md) | Agreed final size/split, verified exports, leakage audit, and release. |

Start with the health-risk group, taking it through 08A–08F before starting the
next group by default. A group yielding no advancing cases records a zero-case
handoff; its downstream stages are not applicable, not missing approvals. The
batch register accounts for every group and every selected case before 08G.
No requirement to review all 606 candidates or identify 35 before authoring.
Unresolved authoring decisions keep a group open unless Kyle explicitly defers
those cases outside the current accepted pool and closes the batch. Preserve
that deferral separately from rejection or eligibility exclusion; it is a
terminal disposition for this pass, not resolution of the underlying question.
Record deferred counts and reasons, and require an explicit revision to reopen.

Contracts describe reusable stages; they are not duplicated 42 times. Each
execution chat handles one stage for one group, for example “Health-risk group —
08C question wording.” Prepare a self-contained handoff with the contract,
allowed inputs, exact versions, pending decisions, and intended output location.
The user starts the separate chat. Do not create chats or send prompts as part
of contract drafting. The coordination chat receives compact status and process
questions, not candidate labeling or answer approval.

A batch can close while the stage remains available for other groups. Before a
stage's first use, revise its provisional contract from the accepted preceding
batch, qualify its interface, and activate that bounded execution. Do not wait
for all groups to finish 08A before activating 08B for the first group. Later
batches reuse qualified stages; the active queue identifies the current group
and stage rather than implying every stage is globally complete.

## Shared review and versioning contract

08A is model-assisted prioritization, not eligibility classification. 08B–08E
use shared stage-specific Label Studio configurations. 08F and 08G use chat
presentation and saved-decision schemas. Astra (`gpt-6-astra`) supplies all
model-assisted ranking, wording, claims, evidence, answers, and cluster
suggestions; humans own selections, eligibility, and acceptance. Record actual
model identity rather than attributing an unavailable or different model to Astra.
No paid API integration or live Label Studio model backend is required.

Each stage has two bounded parts:

1. **Prepare once, just before first use:** inspect maintained Task 07 components;
   adapt a shared template, input/output schema, prompt, and validator. Check
   actual queue behavior, proposal prefilling where applicable, saved human
   edits, and export against representative source-free fixtures.
2. **Execute per group:** bind input versions, generate data/proposals, validate,
   create a separate project from the existing stage template where applicable,
   obtain human decisions, and export only approved advancing records.

A batch chat must not silently change template code or field semantics. A needed
change returns to stage preparation as a named revision, with a compatibility
check and explicit decision about affected earlier batches. Flexible content
lengths and record counts are data, not reasons for a new template. Reject
empty approvals, stale versions, unresolved IDs, or exports different from the
content displayed. Keep proposals separate from human annotations.

The question-wording chat receives original comments and comment-source warnings
only: no response text, response-based ranking rationale, prior answer, or
claims. Keep restricted provenance in a separate record outside that model
packet. Subsequent stages consume the same frozen human-approved question.
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
- Verify at most three selections per group, one case per original comment,
  exact approved question reuse, and explicit reasons for stops and exclusions.
- Check both human eligibility passes, approved claims, resolvable evidence,
  and explicit answer-version approval before final case acceptance.
- After all batches, validate cluster candidate checks and human decisions;
  never split confirmed clusters. 08H must record the agreed allocation before
  release, not infer it from the former 10/15 default.
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
- Cross-group clustering is reviewed only after group authoring finishes.
- Final size and development/test allocation are explicitly agreed; 25 is a
  target, more or fewer requires no weak-case padding or automatic truncation.
- Frozen records resolve to their exact sources and approved versions; all
  decisions and counts can be reconstructed from durable handoffs.
- Remaining limitations and downstream Task 09 requirements are explicit.

## Non-goals

No new extraction, automatic label acceptance, automatic group backfilling,
retrospective reopening, visual-model expansion, forced table calculations,
benchmark retrieval/generation/judge runs, or permissions framework. No labeling
in the umbrella chat and no per-group bespoke review implementations.

## Outcome

Not executed. Contracts only; add bounded batch and final outcome references as
execution occurs, without turning this router into a per-candidate ledger.
