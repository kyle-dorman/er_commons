# Decision 006 — Structured answers and four-part evaluation

Status: accepted by Kyle in chat on 2026-10-08. This records the design decision;
it does not start 08F, model runs, judge implementation or benchmark execution.
It supersedes conflicting earlier requirements for duplicated prose/claim outputs,
no point-to-citation links, and mandatory post-08F human prediction labeling.
The [Sprint 2 evaluation boundary](../sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
owns metric formulas and operational evaluation rules.

## Grounding simplification — 2026-10-16

Kyle accepts independent supporting-point grounding, adequacy S and adequacy C.
Grounding checks each supporting point's factual assertions against its own cited
passages, including material factual qualifications through an explicit projection.
Uncited substantive support is not exempt. S receives all original support without
filtering, source passages or grounding predictions; C's input stays unchanged.
The replacement answer contract does not require conclusion citations. There is
no conclusion-grounding call, point re-review or prediction forwarding.

Reporting adds a strict all-checks-pass result: every required point-grounding
judgment passes, S passes and C passes. Preserve separate component results,
error/abstention statuses and the four benchmark result dimensions. Empty support
and unavailable judgments cannot create success. This derived result is not
another judge or a replacement for diagnostic reporting.

This supersedes the conclusion-grounding and grounding 0/1/2 requirements below
for the planned replacement; historical contracts/results retain their semantics.
[09F.1](../../tasks/sprint2/09f1_revisit_grounding_judge.md) owns no-answer and
grounding policy, component contracts and three-model comparisons.
[Task 12](../../tasks/sprint2/12_integrate_evaluation_and_reporting.md) owns routing
integration, combined reporting, denominator policy and real-answer composition
validation; Task 13 publishes results using that frozen contract. This
decision does not migrate published references, alter automatic citation metrics,
change S/C policy or activate runtime work/provider calls.

## Adequacy policy update — 2026-10-14

The maintained [adequacy labeling rules](../specs/adequacy_labeling_rules.md)
supersede this decision's adequacy scoring, alternative-answer and answer-layout
language for future implementation and labeling. They require reference-equivalent
conclusions covering all question parts, independent supporting-reasoning judgments,
and gated 0/1/2 aggregation. Explicit abstentions skip adequacy judging; reporting
denominators remain deferred. Context-only citations stay metadata in revised
answers, and complete-list conclusions use bullets. Grounding and automatic metric
contracts are unchanged. Prior runs retain their original semantics; runtime
migration and the new diagnostic/input contract remain separate work.

## One structured answer, not two authoring products

08F produces one human-approved structured reference answer per eligible case,
reusing the approved 08E question, argument framing and evidence roles:

- **Conclusion:** direct answer to the question, with citations supporting it.
- **Supporting points:** the few essential facts or visible reasoning steps,
  each linked to its supporting citation IDs. Several sources may jointly support
  a point; citations are not a substitute for a justified inference.
- **Material qualifications:** cited conditions and limits attached to the
  conclusion or point they constrain. They are required answer substance when
  their omission would change or overstate the conclusion.
- **Optional context:** clearly separate background, with citations; it is not
  an essential answer point or required citation credit.

Use readable sentences, not atomized fact fragments or a long provision inventory.
There is no parallel flowing-text answer, duplicate claims list, separately
labeled logic graph, or second essential-points labeling pass. Approve the exact
structured answer and citations together in 08F; preserve versions and feedback.
No unseen reformatted answer inherits approval automatically.

The target model uses the same general structure, but may choose its own number,
wording and organization of points. A valid alternative argument can earn full
credit. It receives the exact question and allowed corpus access under the frozen
retrieval/tool budget, never reference answers or curator claim hints. Preserve
actual tool calls, returned passages, failures and budgets automatically.
This decision does not expand the existing retrieval condition or tool permissions.

## Four separate evaluation results

1. **Automatic evidence discovery:** retrieval recall against required reference
   evidence actually returned to the model within its budget.
2. **Automatic final citation selection:** precision, recall and F1 against
   required reference evidence. Known optional context is neutral. Invalid
   citations remain failures; alternate valid evidence can lose reference-match
   credit without being semantically wrong.
3. **LLM grounded correctness:** are the model's statements, conclusion and
   visible reasoning justified by its cited passages in the question's scope?
4. **LLM answer adequacy:** does the answer correctly and sufficiently address
   the question's essential substance, allowing valid alternative explanations?

Report the four results separately, not as a blended score. Mechanical schema,
citation resolution and corpus checks are validation diagnostics, not a fifth
semantic score. Keep the existing anchored 0/1/2 answer-level judge rubrics.

Grounding receives the question, model answer with point-to-citation links, and
actual cited passages. Hide the reference answer, gold support/context labels,
reference-matching scores and target identity. The question establishes scenario,
time and other scope; a passage can be accurately quoted but misapplied.

Adequacy is a separate judge call receiving the same question and model answer,
the structured reference answer and reviewed evidence, with access to the model's
cited passages for alternative arguments. It assesses substance, not wording or
citation-ID agreement. Neither judge receives official responses as evidence.
Do not overwrite grounding after revealing the reference or expose automatic
matching scores to either judge.

The dimensions overlap. A false central explanation can fail both. A supported
but incomplete answer may pass grounding and fail adequacy. A missing condition
hurts grounding when its omission makes an assertion misleading or unsupported;
a coverage omission alone belongs to adequacy. Do not force errors into mutually
exclusive categories or treat topical relevance as sufficient adequacy.

## Partial credit and wrong citations

Both judgments score the whole answer 0/1/2, not the proportion of bullets passing.
Grounding 1 applies to a material unsupported supporting assertion when the
remaining actual citations independently justify the conclusion. Grounding 0
applies when the central conclusion or a necessary premise lacks cited support,
even if the conclusion happens to be true. Do not substitute a better source for
the model's wrong citation. Valid alternative citations can earn full grounding.

Adequacy 1 generally applies to a correct conclusion missing an essential
explanation, condition or question component. Adequacy 0 applies when the central
question is unanswered, materially misframed or answered incorrectly. Omitting
optional context has no penalty. A decisive missing condition can fail both
judgments; minor points cannot compensate by sheer count. Report mean answer-level
scores and 0/1/2 distributions with denominators, keeping abstention/N/A separate.

## Interpretability without more gold labels

Each judge returns its answer-level score and concise, source-linked diagnostics:
model point IDs/text, supporting or conflicting passages, unsupported inferences,
missing qualifications, and (for adequacy) missing essential reference points.
Check every substantive model point, including additions outside the reference.
Absence from the reference is not evidence of falsity. Unsupported means the
cited material does not establish the assertion; contradicted means it conflicts.
These are automated explanations, not new human labels, extra primary scores or
claims about the model's hidden reasoning.

## Labeling budget and limits

08F is the final planned substantive case-labeling pass: structured answers,
point citations and material qualifications are reviewed together. Later schema,
serialization and evaluation work must not introduce a new per-case labeling
requirement. This does not eliminate separately planned cluster/split decisions.

The prior plan's mandatory human development-score calibration and review of
every test prediction are no longer prerequisites. Without separately authorized
human calibration, label answer scores **uncalibrated automated judgments** and
report that limitation. Automated development sanity/challenge checks can detect
obvious problems but cannot establish human agreement or judge reliability.
Any later human calibration is optional, separately authorized work; do not claim
agreement rates or human validation from reference-answer approval alone.
Freeze judge prompts/configurations before test use; do not tune on test outputs
or silently expand the reference pool to improve scores.

## Rationale

Separating discovery, citation selection, grounding and adequacy identifies where
an answer failed. A structured cited answer supplies the reference and its
inspectable support without maintaining duplicate annotations. This is a project
choice, consistent with separating answer and citation quality in
[ALCE](https://arxiv.org/abs/2305.14627) and using claim-level diagnostic checks in
[RAGChecker](https://arxiv.org/abs/2408.08067), not external validation of our rubric.
