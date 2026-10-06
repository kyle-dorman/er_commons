# Task 08F reference-answer prompt v1

Prompt: `task08f.reference_answer.v1`. Owner:
[08F](../../tasks/sprint2/08f_review_group_answers.md); recording and presentation:
[chat review v1](../specs/task08f_chat_review_v1.md).
Use Astra (`gpt-6-astra`) for every draft and revision. Run only after the case's
human eligibility decision is verified against the current validated 08E export.
This prompt proposes answers; it cannot approve answers or determine eligibility.

Status: historical; superseded for new drafts by [v2](task08f_reference_answer_v2.md).

## Prompt

Draft or revise one concise, evidence-grounded answer to the supplied exact frozen
question. Work on only the active case. Address its central issue and material
qualifications directly. Evidence may support, limit, contradict or fail to
establish an official-response claim. Do not force a rebuttal or assume the
response is correct because the claim wording and relevance were approved.

Use the exact frozen question, approved claims and version-bound relationships,
actual reviewed source text, saved citation–claim judgments and notes, retained
unresolved links/question parts, source usability and material warnings. Read
source text rather than relying only on summaries. The official response provides
claim origin and context; unsupported response assertions are not source evidence.
Do not import historical answers, other groups' labels or unprovided evidence.

Preserve the scope of every approved claim and the exact frozen question.
Supporting-to-supporting chains are valid inputs; retain every intermediate
version and rationale. They do not automatically establish their ancestor claims.
A blank relationship is unreviewed; partial support is not full support. Preserve
contradictions and qualifications. Do not invent an aggregate evidence rating,
resolve upstream question gaps by inference or request renewed claim labeling.

Lead with the conclusion that the evidence permits. Explain how concrete facts
bear on the question. Keep subjects, receptors, scenarios, units, dates and source
editions distinct. State uncertainty and unestablished points plainly when they
matter to the answer. A bounded search does not prove corpus-wide absence.
An unresolved part need not prevent a useful qualified answer, but do not conceal
that part or quietly narrow the frozen question to make it answerable.

Cite only supplied citation IDs using the supplied source labels. Use citations
that materially help assess the answer, including limiting or contradictory
sources when relevant. Preserve their exact source locations. Do not add new
calculations, evidence, commitments, mitigation changes or report-edit proposals.
Do not pad the answer with every retrieved source or process observations.

Keep provenance, model history, raw hashes, approval mechanics and source-audit
history outside the proposed answer. Include a source limitation in the answer
when omitting it would mislead. Keep prose plain and focused; each sentence should
answer the question, explain relevant evidence or express a necessary qualification.

Return the proposed answer, its supplied citation IDs and the concise citation
information needed for review. If a material ambiguity remains, identify it in a
short separate review note for discussion during drafting. Do not create another
claim-by-claim review or final aggregate-support step. If a responsible answer
cannot yet be proposed, explain the obstacle without assigning human eligibility
or stop decisions.

For revision, use the recorded feedback and exact previous displayed version.
Return a full new proposed version, preserving all prior versions externally.
No change becomes approved until the user sees and explicitly approves that exact
answer and its citations. Never interpret silence, process feedback or a request
for revision as answer approval.
