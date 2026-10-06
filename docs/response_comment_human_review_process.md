# Comment and Response Human Review Process

Status: **Current workflow guidance for preparing Task 08 review.** This
consolidates the reusable Task 07 lessons and Kyle's 2026-09-30 execution plan. Task
08 contracts may refine the operational details; this document does not establish
case eligibility, benchmark splits, or permission to run a benchmark.

## Purpose and boundaries

Use this process to turn a comment and its linked official responses into a
human-approved, evidence-grounded reference answer. The human reviewer decides
what to include, what wording to approve, and whether a draft advances to the
next authoring stage. Astra
(`gpt-6-astra`) supplies all model-assisted dataset-label proposals and
revisions. It never accepts a label automatically. Preserve stages designated
human-only, including pilot-fit screening and Task 08 eligibility decisions.
Question selection and approval are separate human review gates. Astra first
proposes a saved within-group ranking, and later proposes question wording for
selected comments; neither is an accepted label.

Keep the original comment, response records, sources, proposed labels, human
edits, and final dispositions distinguishable. A response's assertion is not
thereby true; a relevant claim is not thereby supported; retrieved or cited
evidence is not thereby sufficient for a rebuttal. Deterministic validation can
check IDs, hashes, source anchors, and record closure, but it does not make
semantic review decisions.

The six approved Task 07 answers, their reviews, question scopes, 31 claims,
source ratings, and accepted MVP limitations remain sealed. Their six original
comments reenter Task 08 with fresh selection and review decisions; no historical
approval carries forward automatically. Historical Task 07 task records own
case-specific findings and exact artifact evidence; this document carries
forward reusable procedure only.

## Batch and interface boundary

For the authorized 2026-10-01 combined 08C pass, the
[combined review contract](specs/task08c_combined_chat_review_v1.md) overrides
separate-group presentation: all 57 selections, saved order, one active question,
and fresh explicit decisions including the two historical health-risk cases.


The [Task 08 umbrella](../tasks/sprint2/08_curate_grouped_benchmark.md) owns
reusable stage contracts. Work within one group at each authoring stage and use
a separate, self-contained chat per group/stage; keep labeling out of the main
coordination chat. A saved approved handoff, not full conversation history,
supplies the next stage. Complete each task across participating batches before
advancing to the next, preserving completed health-risk work. The current
[08E task](../tasks/sprint2/08e_review_group_evidence.md) prepares question-wide
research in batch, then reviews one question at a time in chat without source
deduplication. Preserve independent evidence decisions and separate human
eligibility; no second aggregate claim-adequacy pass. No 35-candidate gate applies.

Prepare and qualify one shared versioned interface per applicable stage, including
input, proposal, decision and export contracts. 08C uses the
[shared chat process](specs/task08c_chat_review_v1.md), not a mandatory Label Studio
project. Label Studio stages create separate projects using their shared configuration.
Do not let batch chats customize template code or field meanings silently.
Revise shared interfaces explicitly, test queue/save/export behavior, and decide
whether affected earlier batches require follow-up. 08C chat qualification checks
version displays, feedback, explicit approval and exact export. Answer review and later
all-group clustering stay in chat with versioned approval records.

## 1. Rank and select candidates, then review question wording

### Group candidates for human comparison

Use the exclusive groups accepted in
[Decision 005](decisions/005_task08_grouped_question_selection.md): the four named
health-risk table-analysis candidates first, otherwise general response,
otherwise cited appendix, otherwise comment source. Combine
main-report and no-recorded-citation comments in the final source groups. Do not
subdivide general-response or appendix groups by source. Each comment appears
once; retain all underlying response and citation links as provenance.

08A may prepare all remaining accepted groups ahead of human review using
separate saved handoffs. For groups with at most three candidates, prepare complete
source context in stable comment-ID order with no model invocation; record
“ranking not needed—group has at most three candidates.” Human selection remains
required even for these small groups. Separately authorized 08B batch setup may
prepare blank projects ahead of review; it does not select candidates or close
groups. The [shared intake revision](specs/task08b_intake_v2.md) preserves
historical v1 and both v2 handoff paths. For larger groups,
Astra first reads the group's original comments and complete linked responses,
then saves an ordered candidate list with exact input bindings and inherited
flags. Future 08A batches do not generate ranking explanations, explanatory
quote anchors, or narrative source warnings/review limitations; retain original
source context and provenance. The completed health-risk v1 packet is preserved.
Prefer clear questions and substantive rebuttals; deprioritize rant-like asks,
weak responses, and revision dependence without automatic eligibility decisions.
Saved rankings are revisitable artifacts, not a promise of identical model reruns.

The original review guidance suggested up to three candidates per group. Kyle's
2026-10-01 all-group completion instruction supersedes that ceiling for closeout:
retain every saved Selected candidate. Native Label Studio skips remain distinct
from form Reviewed skip or Excluded records; untouched candidates stay unreviewed.
The export-bound `task08.selection_closeout.v1` process records that explicit
completion and policy amendment without changing native annotations.

These groups organize review; they do not determine eligibility or create
benchmark clusters. Verify response links and complete linked-response context
before relying on a group assignment.

### Selection as the 08B human gate

Use original comments and complete linked response context when comparing
candidates. Under `task08.selection_gate.v2`, the shared `task08b.selection.v2`
form records only selection and selection reason. Explicit selection with a reason
is the sole 08B human gate to 08C; eligibility concerns can go in that reason.
Do not rewrite questions during selection or prefill decisions. Display only the
original comment and complete linked responses as source content: remove source
warning/review-limitation panels, advisory ranking reasons, and the source-bound
ranking record. Retain existing provenance, including all limitations and the
O-Joint-44 incidental-revision exception, in underlying artifacts; do not generate
replacement narratives or rerun 08A. Keep response context and selection reasons
outside the later comment-only wording packet. Preserve reviewed skips, exclusions,
unresolved decisions, and unanswered candidates distinctly. The 2026-10-01
closeout retains all saved Selected records without a per-group cap; fewer,
including zero, are acceptable. A selected
comment may still fail wording or evidence review; do not automatically refill
its group when it drops out.

### Separate wording task and frozen question

After selection, use an isolated wording-review chat for the selected batch.
Work through one comment at a time: show only that original and its current
question, iterate until an explicit disposition, then move down the queue in
the same chat. A human may explicitly leave a case unresolved. Preserve all
versions and feedback in the group journal. For both Astra's actual input packet
and the human wording-review display, include only the original comment, its
comment-source warnings, and any proposed focused question. Exclude response
text, response-based ranking reasons, and prior pilot answers. Astra and the
human reviewer must interpret the question from the comment itself; do not use the official
response to resolve ambiguous intent or supply a missing ask.
One comment yields at most one independently answerable question. Keep the
comment's central issue, scope, uncertainty, attribution, and material
qualifications. Rewrite or simplify only when straightforward; if doing so
would split independent asks, invent an ask, or remove a difficult qualification,
leave the proposal unresolved, explain the obstacle and discuss it with the user
before recording any disposition. Do not force a question or automatically exclude.

Astra proposes reasonable, consistent wording after selection; retain original
wording when already suitable and explain that choice. Display the proposal
with the original in a separately identified per-comment chat block. Preserve
each displayed version and verbatim human feedback. A human may approve, exclude
or leave a case unresolved. Freeze only after explicit approval of the exact
displayed version; feedback or requested edits alone are not approval. A later
revision requires fresh approval. Flag user clarification beyond the source and
do not silently incorporate unsupported intent. Existing proposals and source
bindings remain preserved when changing review interfaces.
The approved question is then frozen and reused unchanged for evidence
discovery, target generation, and both evaluation-judge stages. Preserve the
original comment and any rewrite/skip reason. A reviewed question is guidance
for authoring; it is not a finding that the commenter is factually correct or
that the official response answers the concern.

### Learning: recommendation-shaped comments

The health-risk 08C review showed that a recommendation can support a faithful
question even when the initial model proposal is unresolved. First identify whether
the commenter is asking for information, challenging a conclusion, or recommending
an action. For a recommendation, ask whether the project or EIR would adopt or
include the recommended action, preserving its stated purpose and qualifications.
Do not presume that the action was omitted or rejected, or ask why it was rejected,
unless the original comment supports that framing. A claimed benefit remains the
commenter's intended benefit, not an established result.

Several measures may elaborate one explicitly linked recommendation, but shared
subject matter alone does not make independent asks a single question. Retain a
package only when the source supports that relationship and it can be answered as
one recommendation without hiding separate decisions. Otherwise leave the proposal
unresolved and discuss it. A successful human revision is a lesson to try this
framing, not evidence that every multi-ask comment can be made to fit.

Reusable prompt instruction:

> If the comment recommends an action, consider “Would the project/EIR include
> [the recommended action], with the aim of [the stated purpose]?” Preserve all
> material conditions, scope, uncertainty and attribution. Use only details in the
> original comment. Do not invent a rejection, an explanation request or a proven
> benefit. Do not bundle independent asks merely to obtain one question.

This learning belongs to question review (Task 07B / 08C); Task 07C reviews
response claims. It changes no sealed pilot or approved health-risk wording.
The [prospective v2 wording prompt](prompts/task08c_chat_review_v2.md) incorporates
it for future use; the completed batch retains its pinned v1 prompt.

## 2. Review response claims and relationships

For the new Task 08 combined pass, the [08D contract](../tasks/sprint2/08d_review_group_claims.md)
owns a two-phase chat flow: prepare and validate all claims and reasoning first,
then review one precomputed claim at a time in a separate chat. Each card repeats
the approved question, full claim, full supporting target when applicable,
relationship rationale, response passage and supplied references. The new flow
supersedes mandatory Label Studio/per-group presentation for this pass; historical
reviews remain intact. Practice decisions never become production approvals.

Use the complete linked response closure as the source for claim extraction.
Inventory substantive claims before relevance filtering so unrelated response
material remains auditable. Put claims that directly answer the question first.
Keep claims that do not pass relevance review in the record, but do not send
not-relevant or unresolved claims into evidence discovery.

Write each claim as a concrete, independently assessable assertion:

> **[Subject] [specific assertion], under [conditions], for [time/place/comparison].**

Use only scope details present in the source. Preserve negation, attribution,
uncertainty, quantities, and necessary qualifications. Split separate conclusions
or claims that need different relevance decisions; keep related reasons and
qualifications together. Do not inflate the inventory by turning every number
or incidental fact into its own claim.

Make the relationship structure explicit:

- A **direct claim** identifies which approved question or part of it the claim
  addresses.
- A **supporting claim** links to the direct claim it helps explain and states
  how it materially strengthens that claim's reasoning. Shared topic or
  vocabulary alone is not a support relationship.
- A **not-relevant** claim stays in the reviewed response inventory but does
  not advance to evidence review.
- An **unclear** relationship remains unresolved and stops that claim or case
  from advancing until a human decision resolves it.

Attach exact response passages, supplied citations, and drafting explanations
as provenance beneath the claim, not as substitutes for clear claim wording.
When a claim or relationship changes, recheck and update its linked targets;
do not leave a stale relationship attached to revised content. Human approval
confirms the response claim and its relevance relationship, not its truth or
evidentiary support.

## 3. Discover evidence and review citation summaries

Search from approved claims and supplied references, but do not assume the
official response cited the best passage. A relevant uncited methodology
section may explain a claim better than a cited footnote. Search for supporting
material, counterevidence, and conditions that limit the proposed explanation.

For every candidate citation, preserve its exact canonical section or table
identity, source provenance, and anchor. Present the full citable unit, with a
focused summary that tells the reviewer:

- what the relevant passage says, including its subject, units, dates, and
  conditions;
- which claim or claims it relates to;
- whether it is proposed as support or context, and why it is included; and
- for a long unit, which specific passage, table, or subsection matters and how
  the larger unit bounds its interpretation.

Do not let a summary replace the source text. Do not impose a small source-count
cap that hides the questioned passage or plausible counterevidence. Order the
questioned/core material first, then supplementary sources with their discovery
reason. A support judgment applies to the reviewed claim-source relationship;
one source's label does not automatically apply to another claim. Context can
explain an answer without being required support.

Keep search receipts, hit dispositions, exact anchors, exclusions, and bounded
search gaps. State what was not established and why. A gap in a bounded search
does not prove that evidence is absent from the full corpus. A case that lacks
adequate support may stop even when every citation identity validates.

At the end of evidence review, conduct the evidence-based human eligibility
review using the original comment, frozen question, resolved response, exact
evidence, source usability, and relevant cross-references. Record its own reason
and input version. Earlier selection does not establish eligibility. This is
single-curator review, not independent agreement.

## 4. Draft and revise the proposed rebuttal

Follow the current [Task 07E authoring prompt](prompts/task07e_reference_answer_authoring_v2.md)
and present the review in this order:

1. Frozen question or concern.
2. Retained claims and their direct/supporting relationships.
3. Citation summaries, with support/context roles and source locations.
4. One proposed rebuttal.

The rebuttal should answer the precise contention, lead with the supported
conclusion, and explain how the reviewed evidence bears on it. Use useful
examples without confusing their subject, units, or year with the central
calculation. Preserve material limitations and uncertainty. Keep source-audit
observations outside the answer unless they change what can responsibly be
concluded. Explain omitted sources to the reviewer rather than padding the
answer with them.

Kyle gives feedback in ordinary chat; Astra revises. Preserve proposal versions
and relevant feedback separately. Explicit approval must bind to the exact
displayed answer version. A request for revision, feedback on the workflow, or
silence is not answer approval. Stop when the evidence cannot support a
responsible answer instead of drafting a forced rebuttal.

## 5. Exclude or stop a case at any stage

Allow a human to exclude a whole comment during question review and to stop a
case at any later review stage if it proves unsuitable. Preserve completed
partial work and record the stage, reason, and decision provenance. A stopped
case cannot advance as approved. Do not erase the comment or its history, turn a
stop into an ordinary skip without a reason, or silently reopen an earlier
human decision. Case-level exclusion and Task 08 eligibility remain human
decisions.

## 6. Provenance and acceptance checks

For every model-assisted proposal or revision, record the actual model identity,
prompt version, input identity, output/version identity, and relevant human
feedback and decision. Do not retroactively attribute historical Task 07 runs
whose model identity or settings were not recorded. Keep original proposals,
human changes, and accepted versions separate and versioned.

Before advancing a stage, verify exact input bindings and source IDs, complete
response-link closure where applicable, question and claim identity, citation
anchor resolution, and explicit human disposition. Test the review interface
through its actual task queue and saved export before scaling a batch; a rendered
preview alone does not establish that proposals prefill or decisions export
correctly. Reject an approved record that is empty or whose saved version does
not match the version presented for approval.

Do not infer active review time from chat or record timestamps. Report actual
proposal counts, saved revisions, corrections, unresolved dispositions, and
their denominators instead. Task 08 separately owns eligibility, clustering,
split selection, and its documented attrition waterfall; successful authoring
does not establish any of those decisions.

## After all group batches

After all groups have terminal authoring dispositions, review proposed clusters
across the accepted pool in dedicated chats, one suggestion at a time. Model
similarity suggestions do not create edges. Retain human relationship decisions,
duplicate checks, and a split-leakage audit; shared evidence alone is not an edge.
Agree final size and development/test allocation before serialization. Twenty-five
is a flexible target; do not truncate a larger accepted pool or force weak cases.

## Task 07 learning records

The procedures above consolidate durable lessons from the [07A screening
outcome](../tasks/sprint2/07a_screen_pilot_candidates.md), [07B question
review](../tasks/sprint2/07b_review_comment_questions.md), [07C response-claim
review](../tasks/sprint2/07c_review_response_assertions.md), [07C.1 claim and
relevance review](../tasks/sprint2/07c1_review_claims_and_relevance.md), [07D
evidence discovery](../tasks/sprint2/07d_discover_and_review_evidence.md), and
[07E answer review](../tasks/sprint2/07e_review_answer_logic.md). Those task
records remain authoritative for counts, case-specific corrections, accepted
limitations, and sealed artifacts.
