# Task 07E reference-answer authoring prompt v1

Status: MVP drafting guidance derived from Kyle's M-OSEC-273 chat review.
The owning contract is [Task 07E](../../tasks/sprint2/07e_review_answer_logic.md).
This prompt guides proposals; it does not approve answers or change frozen inputs.

## Prompt

Draft a reference answer to the frozen question using the reviewed claims and
citation pool. Work on one case at a time.

Use these inputs in priority order:

1. The exact frozen question or concern.
2. Retained claims and their reviewed relationships.
3. Support and context citations, including their actual source text.

Use the official response only when needed to understand a claim's origin.
Do not automatically reproduce its argument, add its unsupported assertions,
or narrate its errors. The benchmark answer must stand on the reviewed evidence.
Retained claims guide drafting but do not override what the sources establish.

Before drafting, identify the direct answer and what each claim and citation
contributes. Distinguish direct support, illustrative examples and explanatory
context. Keep numbers attached to their correct subject, units and years.
Account for every reviewed citation: use those that contribute, and explain an
omission separately to the reviewer instead of padding the answer. Context should
help explain the answer, not merely appear in a citation list.

Lead with the direct conclusion. State concrete facts and explain their connection
to the concern. Use “for example” when a calculation illustrates a broader point
without establishing identical values for every calculation. Give each paragraph
one purpose and separate distinct findings. Cite the sources supporting each point.

Avoid editorial phrases such as “needs qualification,” “should not be presented
as verified,” and “the reviewed sources establish.” Say what happened or what the
source says. Include a limitation only when it changes the conclusion or prevents
a misleading answer; state it plainly. Do not mix answer content with an audit of
the official response or a history of corrected citations.

Present the review in this order:

1. Frozen question / concern.
2. Retained claims and relationships; label summaries as summaries.
3. Citation summaries, with support/context ratings and source locations.
4. Proposed answer with source labels resolving to the frozen citation pool.

Kyle gives feedback in ordinary chat. Codex revises and preserves version history;
Kyle is not expected to edit text directly. Bind explicit approval to the exact
shown answer. Feedback on workflow or prompting is not approval of another answer.

Final sentence check: does this sentence answer the question, explain evidence,
provide a useful example, or supply necessary context? If none applies, remove it.
Do not change frozen question scopes, claims, or citation ratings while drafting.
