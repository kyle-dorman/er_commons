# Task 07E reference-answer authoring prompt v2

Status: Current MVP drafting guidance, incorporating M-OSEC-273 and
SA-Caltrans-33 chat review lessons. Supersedes v1, which remains preserved.
The owning contract is [Task 07E](../../tasks/sprint2/07e_review_answer_logic.md).
This prompt guides proposals; it does not approve answers or change frozen inputs.

## Prompt

Draft an evidence-supported rebuttal to the frozen question or concern using the
reviewed claims and citation pool. These selected cases challenge the EIR's
analysis; explain why the challenged conclusion, method or presentation is
supported, to the extent the evidence allows. Work on one case at a time.

Address the precise contention and explicitly name the challenged section,
table or finding when material to the question. A request in the comment to
“verify and update” does not mean the reference answer should offer a document
change. Do not invent commitments, recommend edits, write replacement report
language, or convert the rebuttal into a report-improvement plan.

A rebuttal must remain grounded: do not conceal a limitation that defeats or
materially qualifies its reasoning, or imply all calculations are correct merely
because their interpretation is supported. If the evidence cannot support the
rebuttal, flag that for human review rather than force a defense. Keep unrelated
source-quality findings in separate review notes without changing source records.

Use these inputs in priority order:

1. The exact frozen question or concern.
2. Retained claims and their reviewed relationships.
3. Support and context citations, including their actual source text.

Use the official response only when needed to understand a claim's origin or
confirm the response's scope (for example, explanation versus promised revision).
Do not automatically reproduce its argument, add its unsupported assertions,
or narrate its errors. The benchmark answer must stand on the reviewed evidence.
Retained claims guide drafting but do not override what the sources establish.

Before drafting, identify the specific contention being rebutted, the direct
answer, and what each claim and citation
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

Final sentence check: does this sentence advance the supported rebuttal, explain evidence,
provide a useful example, or supply necessary context? If none applies, remove it.
Do not change frozen question scopes, claims, or citation ratings while drafting.
