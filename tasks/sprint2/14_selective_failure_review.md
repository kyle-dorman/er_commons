# Task 14 — Selective failure and evaluator-disagreement review

Status: complete (2026-10-21). Eight selected answers discussed; final synthesis
confirmed by the user and required quality pass completed. Unresolved judgments
remain recorded. Task 15 plans C-judge repair; Task 16 owns the later writeup.

## Abstract and goal

Explain a small, useful selection of model failures and evaluator disagreements
from the completed runs. Produce evidence-backed examples for Task 16 and
diagnostic findings for Task 15 without
turning this into a comprehensive human-labeling or judge-calibration project.

## Inputs and outputs

Read Task 13's sealed results, Task 12 tables/charts and existing Task 11 manual
findings. Target-model examples are limited to Luna and Haiku; the archived
MiniMax side experiment is excluded. Reuse only previously reviewed/disclosed
judge challenge examples where relevant; reserved challenges remain unopened. Output a small selection manifest, case notes and a concise synthesis
with exact answer/repeat/point IDs and links to source evidence, verdicts and
prior review.

## Plan and research checkpoint

1. Use completed automatic/component tables to select examples, not ad hoc browsing
   of test content. Review six complete answer instances, including reused
   examples, as the intended stopping point. Expand only to answer a named,
   important question left unresolved by those six; document that question and
   the additional selection before reviewing more answers. Twelve is the ceiling,
   not a target; exceeding it requires a separately documented scope change.
   Include both models, a clear failure, a repeat disagreement and at least one
   success/near miss. Include at least one same-question comparison where Luna
   passes the frozen joint criterion and Haiku fails it. Count the paired answers
   as two of the six instances. Select exact repeats from saved score tables
   before reading answer prose and disclose the other repeats' recorded outcomes;
   the selected contrast is illustrative, not evidence of a consistent gap.
2. Prioritize questions that explain a distinct limitation. Use existing reviews
   first; avoid re-reviewing all failed judgments or every answer in a selected
   case. Record the selection rationale and which populations were not reviewed.
3. For each example separate observed judge/check outcome, human interpretation
   and attribution confidence. Consider evidence interpretation/table errors,
   citation-clause gaps, unsupported qualifications, support-to-conclusion
   omissions, answer completeness, input/specification mismatch, reference scope,
   evaluator disagreement and execution/formatting failures. Allow multiple causes;
   do not force a definitive cause where the evidence is ambiguous.
   For the Luna/Haiku pair, compare substantive claims, qualifications, cited
   support and the final conclusion against the same question and supplied
   evidence. Treat the user's impression that Haiku adds more claims and
   qualifications as a hypothesis, not a selection rule or finding. Distinguish
   supported, relevant qualifications from unsupported or unnecessary additions,
   and report evidence that contradicts the hypothesis as well as supports it.
   Do not infer a model-wide tendency from this selected pair.
4. Use Task 13 component outcomes under the Task 12 definitions to inspect
   selected cases where C passes
   despite G/S failure, or C fails despite grounded support. These are diagnostic
   patterns, not proof of hidden model reasoning or of which judge is wrong.
5. Preserve frozen scores beside commentary. Explain source contradictions,
   plausible alternate evidence or reference limitations without silently rescoring.
   Use relevant previously reviewed/disclosed challenge examples instead of conducting a
   new full human judge audit. Report review counts, not population error rates.

Borrow stage-aware examples from [DocScope §§4/B.5/F.6](https://arxiv.org/html/2605.08888v2)
and the distinction between model and answer-extractor errors from
[LongDocURL §5/Appendix G](https://aclanthology.org/2025.acl-long.57.pdf).
Adapt the categories to supplied text/table evidence; no new spatial grounding
metric or evidence-trajectory annotation is required.

## Interactive review workflow

User amendment (2026-10-21): after accepting the roster, the user authorized
offline agent assessment of all six selected inputs, predictions and judgments
before interactive discussion. Discuss single-model units first (U02, U03, U04,
U05), then the matched pair U01 together. Show the question, exact conclusion,
selection reason, what worked/failed and ambiguities, then the full model
supporting response rather than an evidence summary. This supersedes the initial
pair-first order and restriction on batch agent preparation below; it does not
authorize batch human confirmation or advancing discussion without feedback.

The user wants to review the examples iteratively with the agent in the next
chat. Prepare and verify saved materials offline, but do not complete a batch of
interpretive reviews or infer user agreement before that discussion.

1. Verify the accepted Task 13 result pointer and relevant sealed tables. Propose
   a six-answer selection manifest with exact identities, selection rationale,
   frozen outcomes and intended coverage. Discuss the roster with the user before
   beginning case review. Start with the matched Luna-pass/Haiku-fail question.
2. Present one review unit at a time; the matched pair is one discussion unit but
   consumes two answer instances. Show the question, both answers side by side
   where useful, selected evidence excerpts with source IDs, and the frozen
   automatic/A/G/S/C/joint outcomes. Keep additional evidence accessible by link.
3. Use the same compact review form below for every unit. Offer a tentative agent
   interpretation clearly labeled as such, then ask for the user's interpretation,
   corrections and unresolved questions. Follow up on requested evidence within
   the selected scope. Wait for the user's response before finalizing that unit
   or advancing; silence is not agreement.
4. Save the discussion outcome after each unit. Keep agent proposals separate
   from the user's actual comments and confirmation. A review may be accepted
   with an unresolved interpretation; never force agreement or invent a human
   verdict. On resumption, show the last saved status and next pending unit.
5. After six answer instances, summarize supported observations, counterexamples
   and uncertainties for the user. Stop unless a named important question
   justifies additional examples within the ceiling. Complete a bounded evidence
   and wording check, then obtain the user's confirmation of the final synthesis
   before closing Task 14 or handing its confirmed examples to Task 16.

### Review form and saved records

| Field | Required content |
| --- | --- |
| Identity and selection | Review ID; question/case ID; model, run and repeat IDs; why selected; source completion digest. |
| Frozen observations | Original automatic/component/joint outcomes; other repeats' recorded outcomes; no revised score. |
| Answer and evidence | Exact excerpts and source/point IDs supporting the discussion; distinguish supplied evidence from reference answer and judge rationale. |
| Agent assessment | Claim, qualification, support and conclusion comparison; tentative explanation; attribution confidence and alternative explanations. |
| User review | The user's comments/corrections, accurately quoted or labeled as paraphrase; unresolved questions. Leave empty until the user responds. |
| Disposition | Pending discussion, needs evidence, or user-confirmed; accepted interpretation and remaining uncertainty. |
| Writeup use | Proposed short lesson/example and its selection limits; mark pending until confirmed. |

Use a fresh review directory under
`ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_14/` for the selection
manifest, per-unit Markdown forms, revision/event record and final synthesis.
Plain JSON and Markdown are sufficient; no review application is needed.
Preserve earlier form revisions or record changes in the event record so user
corrections remain traceable. Link exact saved inputs; never modify sealed Task
13 artifacts. Keep the task outcome concise and route detailed review history to
these external records. Agent/subagent evidence checks supplement the user's
review; they do not count as human confirmation.

## Validation, review and acceptance

Check excerpts against saved evidence and exact candidate identities. A bounded
second review checks the selected examples and claim wording, not the whole test
set. Each claim distinguishes model error, dataset/evaluator limitation and
unresolved interpretation. State selection bias and the small review's limits.
Confirm the matched comparison is included and any expansion beyond six has a
specific recorded justification. If no eligible Luna-pass/Haiku-fail pair exists,
report that limitation rather than changing the success criterion.
Deliver a handful of useful cases to Task 16, not a new leaderboard. The separately
scoped Task 15 may use disclosed findings to motivate its C-judge revision.
Documentation changes use link/diff inspection and `git diff --check`.

## Non-goals

Exhaustive human failure analysis, new human accuracy/F1 estimates, reannotation,
new model calls, reserved judge-challenge inspection, prompt/judge changes,
correcting the frozen test score, or adding
an experiment because an example is interesting. No commit or push.

## Outcome

Completed eight answers across seven discussion units: six test answers and two
reused development answers, including the matched Luna-pass/Haiku-fail pair.
The two-answer expansion EQ01 examined the deferred conclusion-adequacy question.
The user confirmed the synthesis; uncertainty about C003 scope, the MMRP citation
and the wetland absence claim remains explicit. Frozen scores are unchanged.

The [result pointer](../../docs/specs/task14_result.json) selects the final synthesis,
selection manifest, current state and quality completion. Versioned forms and
journals preserve exact inputs, excerpts, corrections and user comments. The
quality pass found no runtime-code changes requiring refactoring; it corrected
stale selection/status metadata and simplified resume routing. Source/completion
hashes, exact score joins, Markdown links and `git diff --check` passed. Prior
sealed records remain intact. No new model calls, reserved challenges, MiniMax,
commit or push.

Next is [Task 15](15_revise_conclusion_judge.md), planned but not executing.
[Task 16](16_write_methods_and_results.md) remains provisional after its acceptance.
