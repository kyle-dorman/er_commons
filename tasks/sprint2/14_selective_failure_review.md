# Task 14 — Selective failure and evaluator-disagreement review

Status: provisional; after Task 13. No new review or locked-content access now.

## Abstract and goal

Explain a small, useful selection of model failures and evaluator disagreements
from the completed runs. Produce evidence-backed examples for Task 15 without
turning this into a comprehensive human-labeling or judge-calibration project.

## Inputs and outputs

Read Task 13's sealed results, Task 12 tables/charts and existing Task 11 manual
findings. Target-model examples are limited to Luna and Haiku; the archived
MiniMax side experiment is excluded. Reuse earlier judge challenge examples where
relevant. Output a small selection manifest, case notes and a concise synthesis
with exact answer/repeat/
point IDs and links to source evidence, verdicts and prior review.

## Plan and research checkpoint

1. Use completed automatic/component tables to select examples, not ad hoc browsing
   of test content. Start with six examples, with a provisional ceiling of twelve
   complete answer instances including reused examples. Refresh that bound before
   work; expanding it requires a documented scope change. Include both models,
   a clear failure, a repeat disagreement and at least one success/near miss.
2. Prioritize questions that explain a distinct limitation. Use existing reviews
   first; avoid re-reviewing all failed judgments or every answer in a selected
   case. Record the selection rationale and which populations were not reviewed.
3. For each example separate observed judge/check outcome, human interpretation
   and attribution confidence. Consider evidence interpretation/table errors,
   citation-clause gaps, unsupported qualifications, support-to-conclusion
   omissions, answer completeness, input/specification mismatch, reference scope,
   evaluator disagreement and execution/formatting failures. Allow multiple causes;
   do not force a definitive cause where the evidence is ambiguous.
4. Use Task 12's component intersections to inspect selected cases where C passes
   despite G/S failure, or C fails despite grounded support. These are diagnostic
   patterns, not proof of hidden model reasoning or of which judge is wrong.
5. Preserve frozen scores beside commentary. Explain source contradictions,
   plausible alternate evidence or reference limitations without silently rescoring.
   Choose a few relevant historical challenge examples instead of conducting a
   new full human judge audit. Report review counts, not population error rates.

Borrow stage-aware examples from [DocScope §§4/B.5/F.6](https://arxiv.org/html/2605.08888v2)
and the distinction between model and answer-extractor errors from
[LongDocURL §5/Appendix G](https://aclanthology.org/2025.acl-long.57.pdf).
Adapt the categories to supplied text/table evidence; no new spatial grounding
metric or evidence-trajectory annotation is required.

## Validation, review and acceptance

Check excerpts against saved evidence and exact candidate identities. A bounded
second review checks the selected examples and claim wording, not the whole test
set. Each claim distinguishes model error, dataset/evaluator limitation and
unresolved interpretation. State selection bias and the small review's limits.
Deliver a handful of useful cases to Task 15, not a new leaderboard.
Documentation changes use link/diff inspection and `git diff --check`.

## Non-goals

Exhaustive human failure analysis, new human accuracy/F1 estimates, reannotation,
new model calls, prompt/judge changes, correcting the frozen test score, or adding
an experiment because an example is interesting. No commit or push.

## Outcome

Planning only. This task begins after the locked evaluation and remains selective.
