# Task 08F structured reference-answer prompt v3

Prompt: `task08f.reference_answer.v3`. Owner: [08F](../../tasks/sprint2/08f_review_group_answers.md).
Recording: [chat v2](../specs/task08f_chat_review_v2.md). Use Astra (`gpt-6-astra`)
only after execution authorization and verified current 08E eligibility. This
prompt makes proposals, never human approvals. Prior prompt/output versions remain
preserved. Do not use the older two-case intake for the combined batch.

## Invocation modes

Phase A invokes this prompt once per eligible case within the full batch job,
with isolated case inputs and saved outputs. Work only on the supplied case; do
not request human approval or advance the queue from inside a preparation call.
Return a proposal or explicit material obstacle, never an approved answer.
Phase B reuses those proposals for human review and invokes this prompt only
for targeted revisions needed by feedback, preserving predecessor versions.

## Prompt

Finalize one structured, cited reference answer to the exact supplied question.
Reuse the approved 08E framing and scoped citations, including exact amendments.
Read the supplied reviewed source text, not just its summaries. Preserve material
scope, source-edition limits and historical holds. Work on only the active case.

Return one conclusion, the essential supporting points, material qualifications
attached to the points they constrain, and optional context separately. Each
substantive point must link to supplied approved citation occurrence IDs. Use
readable sentences; do not return parallel prose, a duplicate claims inventory,
an extra rubric or a separate logic graph. Use the chat v2 record shape. Give
concise source labels/pages for the human display and keep technical provenance
in the saved record. Do not force a fixed number of points or cite every source. Use one citation when
sufficient and multiple for genuinely combined support; no one-citation cap applies.
Use supplied stable section/subsection/table identities, retaining exact relevant
excerpts or cells as locators within them. Do not invent sentence-level IDs or
replace precise available units with chapter-wide citations. Preserve table notes,
continuations and necessary context.

Explain the evidence-based inference connecting premises to the conclusion. A
citation on a related topic is insufficient. Check each assertion and each
required premise against its actual cited passages. Include a necessary condition
with the point it qualifies, not as optional background. Distinguish documented
absence from unsuccessful search. Do not depend on visual-only figure inference,
new calculations or outside knowledge absent from approved evidence.

Official responses and response claims are not answer evidence. Even approved
claims cannot supply facts or causal reasoning missing from the reviewed sources.
For example, significant regional emissions alone do not establish that vegetation
cannot affect them. Do not substitute what a source should say for what it says.
A wrong central citation cannot be repaired by a reasonable-sounding conclusion.

Make essential reasoning explicit enough to distinguish a missing secondary
explanation from a failure of the central answer. Do not assign point weights,
predict judge scores or label hypothetical mistakes. The eventual grounding judge
checks actual model citations; adequacy judges essential substance, allowing other
valid arguments. Their 0/1/2 scores allow partial credit based on materiality,
not bullet counts. Optional context is not required coverage.

Do not silently narrow/rewrite the question, change historical claims, promote
unreviewed research or import old approvals from another lineage. If the current
scope cannot support a responsible answer, identify the specific material obstacle
in a separate review note for the human; do not invent support or decide eligibility.

For revisions, bind the exact previous display and recorded feedback, return the
complete new structured answer, and identify substantive changes. All prior
versions remain. No proposed change is approved until the user sees and explicitly
approves its exact displayed version and citations.
