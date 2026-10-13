# Task 09E.1 — Dev6 conclusion evidence-boundary comparison

The user authorizes the next evidence-use clarification on the full existing
Dev6 panel, explicitly asking to reduce the concentration on the pet-policy
question. This supersedes the earlier pilot's no-expansion boundary for this
new experiment. Preserve both failed pilots and all historical results.
No structured-explanation appendix is used: compare the original visible
reviewer with one short clarification of existing evidence boundaries.

## Question, inputs and scope

Does making the existing distinction explicit improve conclusion and claim-review
agreement across six questions? The conclusion can use cited source evidence
throughout the original answer; each individual point review remains limited
to that point's own citations. All substantive assertions within the conclusion
must be supported; an assertion inside it cannot be waived as an unrelated
peripheral point. The original [Stage 2 contract](task09e_staged_grounding_v1.md#stage-2-review-the-conclusion-and-earlier-predictions)
supplies full answer evidence, and the existing prompt's own-citation restriction
applies explicitly to point reviews. This is a clarification of that intended
boundary, not newly supplied evidence or a different numeric scoring policy.

Use all 136 eligible answers in the sealed Dev6 panel: C041, C037, C014, C001,
C019 and C056. Read the 09A.3 result pointer before dataset artifacts. Preserve
the exact answer/evidence packets and their bindings. Freeze all 323 actual
claim decisions from the selected simple baseline in the completed
`09e1_20261012_luna_structured_dev6_v1` experiment. Verify original claim-payload
parity and successful result seals. No fresh point or gate calls.

Include all twenty answers without non-conclusion point inputs. Twelve are clean
abstentions; the other eight require substantive conclusion assessment. Do not
classify all zero-point answers as N/A. Check current zero-point rendering and
validation offline; compare clean-abstention predictions separately after labels
are loaded. Prove unchanged full inputs for the seventeen earlier pilot answers.

Only the six selected case artifacts may be opened. No reserved/test payloads,
other development questions, full-19 expansion, later tasks, target generation,
answer rewriting, citation repair, truncation, new models, commits or pushes.

## Exact two-arm comparison

Both arms use the same full original payload and frozen point predictions,
generation schema, validator and existing disagreement gate/0–2/N/A aggregation.

- **Baseline:** exact original `stage_prompt("conclusion")`.
- **Clarified:** that exact prompt followed by this appendix:

```text
Apply these evidence-ownership boundaries without changing the support standard. For the conclusion, assess every substantive assertion and material qualification in the conclusion itself. You may use source evidence cited anywhere in the original answer; a conclusion need not repeat citations already attached to other answer points. Candidate assertions and preliminary point predictions are not evidence. A supported assertion elsewhere does not excuse an unsupported assertion within the conclusion. An unsupported separate answer point does not by itself invalidate an independently supported conclusion, unless the conclusion necessarily depends on it.
For each independent point review, use only that point's own cited source evidence. Evidence cited by another point cannot repair a missing or incorrect citation on the reviewed point. Preserve the original wording, scope and conditions; apply the existing abstention rules and return the unchanged output fields.
```

The appendix is a general ownership and whole-conclusion fidelity reminder
bundle. It contains no pet-policy example, labels, favored answers or requested
explanation format. It can affect attention, interpretations and cost; this does
not isolate the effect of any individual sentence. Existing research and the
[structured pilot's source review](task09e1_luna_structured_conclusion_result.md)
motivate the concrete failure boundary, not a claim that more instructions
necessarily help. Do not alter labels or existing aggregation to improve metrics.

## Execution and stops

One fresh pass over 136 answers per arm, at most 272 generations. There are no
additional repeated calls; broad coverage is the priority and this run does not
estimate repeatability. Use only `gpt-6-luna` Responses generation, medium reasoning,
4,096 output allowance, qualified evidence-prefix caching, exact-token preflight
and native usage parity.

Each arm has four concurrent samples, a $2 conservative reservation cap,
136-generation cap and 3,600-second wall limit. Combined ceiling $4. Separate
cache keys; no saved-result reuse. Load credentials internally from `.env`
without printing or recording secrets. On failure halt new scheduling, retain
in-flight calls and all partial results, and do not retry or replace judgments.
Stop after both arms and independent analysis. No automatic prompt revision,
promotion or expansion, regardless of outcome.

## Analysis fixed before dispatch

Expected labels and reasons stay outside model inputs and preparation. Load
maintained Dev6 expectations only after both summaries exist. Report valid and
all-planned denominators; retain failures as failures, not negative decisions.

The primary report covers all six questions, with an equal-weight per-question
mean as well as the pooled result. Also show the five questions excluding C041,
Dev3 versus the three added cases, and the 119 answers outside the earlier
seventeen-answer pilot. These are broader development checks, not independent
held-out tests: several claims and cases have already informed development.

Report conclusion support agreement on non-null proposed-support cases,
clean-abstention/status accuracy separately, and combined conclusion-state
agreement without conflating null with false. Report claim-review agreement with
unchanged proposed labels over the same 323 original claims, compared with the
frozen baseline decisions; report paired corrections and damaging reversals.
Show final numeric coverage/accuracy on numeric-eligible answers, correct N/A
outcomes separately, and correct final status/score across all eligible answers.
Do not mix abstentions into a numeric-score denominator or credit unscored errors.

Provide per-question counts, false acceptances/rejections, paired improvements
and regressions, original-versus-review disagreements, quotation diagnostics,
exact duplicate-input groups where present, native usage/cache/cost and latency.
No conclusion about stability can follow from one fresh pass.

Independently source-review all changed conclusions, candidate false acceptances
and changed claim reviews. Include a deterministic stable correct example from
each question; distribute review across the six cases instead of making C041 the
central narrative. Separate clear source/citation errors from defensible disputed
readings. A matching label with a faulty rationale is not a clean improvement.
Keep original proposed labels in headline metrics.

A promising result requires a net non-null conclusion agreement gain, including
a gain outside C041, without worse false acceptance or claim-review agreement,
and source review must substantiate the gains. Equal-weight case performance
and clean-abstention regressions remain explicit acceptance concerns. Report
tradeoffs without retrofitting success criteria. Even a promising result does
not automatically qualify a judge or promote defaults.

## Artifacts and validation

Fresh namespace:
`task_09/09e1_20261012_luna_conclusion_evidence_dev6_v1/`. Copy/adapt external
scripts into the new namespace; do not import sealed historical scripts in place.
Freeze this contract, scripts, exact prompts, condition, packet/result bindings
and implementation before dispatch. Preserve all earlier seals and distinguish
fresh preservation checks from inherited audit evidence.

Existing prompt overrides should suffice; no package changes are expected.
Independently review preparation, baseline/candidate payload and schema parity,
zero-point/clean-abstention fixtures, exact counting, budgets and analysis before
dispatch. Run focused tests, external guards, `make fix`, `make check` and
`git diff --check`. Current baseline: 4,271 passed, one skipped and three
historical Task 06G failures. Audit native receipts and decoded Inspect logs,
scan artifacts for credentials, and publish a completion inventory last with
a small tracked result pointer. No defaults or labels change implicitly.
