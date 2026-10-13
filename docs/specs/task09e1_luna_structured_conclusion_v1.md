# Task 09E.1 — Structured conclusion assessment pilot

The user requests the more structured approach after reviewing the
[three-arm conclusion results](task09e1_luna_conclusion_blind_result.md). Existing
JSON decisions, claim/conclusion separation, necessary-premise checks and source
grounding are already implemented. This test adds a concise, evidence-linked
written assessment of the conclusion in the existing explanation field. It does
not add a new decomposition stage, another model or a new scoring rule.

## Question and fixed comparison

Does explicitly recording the conclusion's meaning, supporting evidence and
necessary connection improve conclusion agreement and source fidelity compared
with the existing visible-verdict reviewer? Keep that reviewer because the last
test found useful claim corrections and weaker results with hidden verdicts.
Do not compare a new structured run only with historical outputs: run both arms
fresh on the same frozen inputs.

Reuse exactly the seventeen answers and 59 original claim predictions sealed in
`09e1_20261012_luna_conclusion_blind_v1`. Read the 09A.3 pointer first and verify
the consumed files against that completion inventory. The eleven original trouble
answers and six controls remain unchanged. Do not regenerate claims or gate
decisions, rewrite answers, add evidence, repair citations, truncate, or expand
the panel. Prior judgments and all permitted evidence are visible in both arms;
labels, prior explanations and review outcomes are not model inputs.

- **Baseline:** unchanged `stage_prompt("conclusion")` and generation schema.
- **Structured:** exactly that prompt plus the appendix below, using the same
  schema, original point-review instructions, source boundaries and aggregation.

## Exact candidate appendix

Append the following text after the baseline prompt:

```text
In the existing top-level explanation string, provide a concise, evidence-linked assessment using these headings: Interpretation; Evidence; Inference; Verdict basis.
Interpretation: state the relationship actually asserted by the original conclusion, preserving its subjects, actions, material quantifiers, modality, conditions, exceptions and timing. Do not silently rewrite it into a weaker, stronger or differently scoped assertion.
Evidence: identify the relevant cited source IDs and brief exact excerpts that support or fail to support that relationship. Keep each source statement attached to its own subject and conditions; the original text remains authoritative.
Inference: distinguish what the evidence states directly from any connection needed to support the conclusion. Identify a missing necessary connection, if any; do not treat an unrelated unsupported statement as a necessary premise. If materially different readings are plausible, identify them briefly without silently substituting one for the original wording.
Verdict basis: summarize the material support or mismatch underlying the conclusion_supported value under the unchanged rubric.
Keep the explanation within 250 words. Provide an auditable assessment, not a step-by-step reasoning trace. Retain all existing output fields and independent point-review instructions; add no JSON fields. Explanation formatting or quotation quality does not itself determine semantic support.
```

This is an explanation-structure plus fidelity/inference-reminder bundle, not a
pure formatting experiment. Required headings are a prompt request; incomplete
headings or nonliteral excerpts remain diagnostics, not a new invalid-output or
semantic failure condition. Existing structural/source-ID validation remains.
The schema, field order and semantic validator are unchanged. Explanation text
does not prove the model's internal reasoning process or establish correctness.

## Research and expected learning

The [earlier research review](../llm_judge_learning_notes.md#research-review--2026-10-12)
informed the evidence-linked claims pilot; its application to conclusions is an
untested hypothesis. [Official OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
supports task-specific criteria, scoped comparative evaluation and inspecting
agreement with labels. It does not establish that this particular appendix works.
Preserve Luna-only and existing Inspect execution; do not adopt another service,
model, human-labeling requirement or default from general documentation.

The preceding source review found real citation-ownership errors and ambiguous
pet-policy conclusion wording. Distinguish those cases in analysis. Do not embed
their desired answers or tailored examples in the prompt, silently change labels,
or treat a higher score obtained by weakening the original conclusion as a gain.

## Execution bounds

Run three fresh repetitions per answer and arm: 51 calls per arm, 102 total.
Use `gpt-6-luna` Responses, medium reasoning, 4,096 output allowance, qualified
evidence-prefix caching, exact-token preflight and native usage parity. Each arm
has four concurrent samples, a $1 conservative reservation cap, 51-request cap
and 1,800-second wall limit. Total ceiling $2; separate arm cache keys and no saved
response reuse. Load credentials inside code from `.env` without exposing values.

On failure halt new scheduling, retain in-flight calls and partial results, and
do not retry or replace judgments. Stop after the two arms and independent
analysis regardless of outcome. No automatic expansion, prompt revision, default
promotion, other models, reserved/test content, later tasks, commits or pushes.

## Prespecified analysis

Load the maintained Dev6 labels only after both summaries exist, and use only the
same seventeen selected answers for comparison. Report conclusion agreement,
false acceptances/rejections, original-vs-review claim agreement, corrections and
damaging reversals, numeric coverage/accuracy and repeated-input consistency.
Give valid-output and all-planned-slot denominators. Break down the eleven trouble
answers, six controls and cases; preserve duplicate/repetition limitations.

Report paired improvements/regressions, and source-review every changed conclusion,
false acceptance and changed point-review judgment. Check at least one stable
correct control per case. Inspect the structured explanation's fidelity to the
actual conclusion, source statements, scope, premise connection and final verdict.
Report heading coverage/length separately from semantic accuracy. Do not count a
fluent explanation, increased token use or agreement between stages as correctness.
The prior conclusion-only arm remains historical context, not a fresh comparator.

A promising result needs a net conclusion-agreement gain without added false
acceptances, reduced claim-review agreement or new source-grounding errors. It
must not depend solely on defensible alternative readings of ambiguous labels.
Report other tradeoffs without retrofitting success criteria. Even a promising
small result does not automatically promote or authorize a broader run.

## Artifacts and validation

Fresh namespace: `task_09/09e1_20261012_luna_structured_conclusion_v1/`. Copy/adapt
external scripts into this namespace; never import them from a sealed historical
directory where bytecode might mutate the inventory. Freeze contract, scripts,
prompts, condition, inputs, prior completion and implementation before dispatch.
Package changes are not expected: the existing prompt-override path suffices.

Independently review input/source boundaries, exact appendix, launcher, budget
and analysis before dispatch. Run focused tests, external guards, `make fix`,
`make check` and `git diff --check`. Current baseline is 4,271 passed, one skipped
and three historical Task 06G failures. Audit native receipts, caching/costs and
decoded Inspect logs, scan final artifacts for credentials, verify prior seals,
and publish completion last with a small tracked result pointer. Preserve all
earlier results, defaults and the selected simple claims configuration.
