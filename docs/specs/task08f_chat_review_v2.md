# Task 08F structured-answer chat contract v2

Process: `task08f.chat_review.v2`. Owner: [08F](../../tasks/sprint2/08f_review_group_answers.md).
Prompt: [v3](../prompts/task08f_reference_answer_v3.md). This is a recording contract,
not a claim of an implemented validator. Supersedes v1 for the combined batch;
[v1](task08f_chat_review_v1.md) remains historical for the earlier health-risk run.

## Intake

Verify [08E result](task08e_combined_review_result.json), completion/file inventory
and dependencies. Retain all 53 dispositions, author only the 49 eligible cases
in saved order, and preserve the four outside-batch deferrals. Bind current case
question, eligibility, exact approved display/amendments and evidence scope.
Nine approved overlays supersede only their named material; do not turn their
pending research into acceptance or discard their valid scoped approvals.
No project-105 intake, new project or new chat is required.

## Two-phase handoff

Phase A runs model preparation for the full 49-case eligible batch before routine
human review. Each isolated invocation uses prompt v3 for one case. Save per-case
attempts, model/input/output identities, restart status, validation and either a
proposed answer or an explicit blocked record. Finish accounting for the whole
batch, then seal a `prepared, awaiting human review` inventory in saved order.
Keep new answer approvals/dispositions blank; inherited 08E eligibility is not
08F answer approval. A prepared render is not an actual human display event.

Phase B verifies that handoff and reviews its saved proposals in chat, one question
at a time from C001. No new chat is required or automatically created. Record
actual displays and feedback in a separate review namespace; preserve sealed
preparation. Targeted model revisions during review bind the original proposal
and subsequent versions. Do not redraft the batch as the user advances.

Preparation publication is distinct from final reviewed publication. The final
handoff requires explicit per-case human approval or disposition, with pending
cases visible. A failed preparation record never becomes an inferred human stop.

## Answer record

Use plain JSON plus the exact human-readable Markdown display. Each answer has
case/version identity and predecessor, exact question binding, and:

- `conclusion`: stable point ID, readable text and citation occurrence IDs.
- `supporting_points`: ordered essential point objects with the same fields.
- `qualifications`: point objects with citations and explicit `applies_to` point
  IDs; permit a qualification to constrain more than one point.
- `optional_context`: separately identified point objects with citations, possibly
  empty. Do not score their absence as missing essential substance.

This is the sole answer, not a duplicate outline accompanying prose. Essential
facts and inference can share a coherent point. Do not impose a bullet count or
numeric importance weights. Citation bindings retain occurrence/candidate identity,
canonical anchors, full text references, edition, pages and required/context role.
A conclusion may share citations with its supporting points. Keep each link.
Citation arrays permit one or more sources per substantive point; no one-citation
cap applies. Bind each occurrence to a stable canonical section/subsection or
complete table and its document/edition and page/anchor locations. Preserve
relevant excerpts/cells as within-unit locators, separate from the canonical
identity used for matching. Keep complete table notes and continuations available;
never treat a matching unit ID as proof of semantic support.

## Display and approval

Present exact question, conclusion, supporting points and attached qualifications,
then optional context, with readable citations and relevant excerpts. Full sources
remain available. Save the exact display after it is actually shown. Capture the
user's feedback verbatim with actor, available timestamp/chat reference and target
version/hash. Do not fabricate unavailable message IDs or timestamps.

Approve the complete structured answer and rendered citations together. Existing
08E approvals are substantive predecessors, not approvals of unseen changed
outputs. A revision creates a new full version requiring explicit approval;
silence, process agreement or a revision request is not approval. Keep all prior
versions. Resume only after explicit case disposition; do not infer advancement.

## Persistence and publication

Create a new namespace below configured Task08 artifact storage, outside all
immutable preparation and review directories. Preserve:

- Intake manifest: result/completion/dependency hashes, ordered cases and scopes.
- Proposal: actual model/invocation, prompt and source-only input bindings, raw
  output, structured answer, citations, predecessor and exact display hash.
- Journal: ordered display/feedback/decision events bound to exact versions.
- Disposition: explicit human approval, stop, hold or deferral, current input and
  eligibility bindings, reasons where relevant. Missing decisions stay pending.
- Checkpoint/handoff: every case's current disposition, answer/citation references,
  full history, limitations, validation, pending/resume position and null next stage.

Use maintained durable/hash helpers where appropriate; qualify compatibility
before use rather than forcing the schema through an incompatible historical API.
Publish completion last with exact managed-file inventory and dependency digests.
Validate source links, point IDs and qualification targets, no context promotion,
exact approval/display binding and full version closure. Do not accept hidden
research, fabricate finding decisions or infer semantic support from valid IDs.

## Evaluation boundary

Follow [Decision 006](../decisions/006_structured_answers_four_part_evaluation.md)
and 08F's partial-credit rubric. Both judge scores are whole-answer 0/1/2; no
point-count fraction, mandatory point weighting or separate label pass. The judges
may explain point failures automatically. Grounding sees the question, generated
answer and its actual sources, not this reference; adequacy additionally sees the
structured reference and can accept alternative valid evidence. No judge execution
or post-08F human calibration is authorized by an answer approval.
