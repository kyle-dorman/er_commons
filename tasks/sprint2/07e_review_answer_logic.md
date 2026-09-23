# Task 07E: Review Answer Logic

Status: **Provisional draft; revise after 07D.**

## Abstract and goal

Build a Label Studio project for the short logical bridge between the
comment's concerns and reviewed evidence. The bridge states what the evidence
establishes, which response assertions it supports, and which concerns remain
unanswered. Follow the [Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs and outputs

- Input: approved 07B questions, 07C assertions, and 07D evidence judgments.
- Codex proposes a concise assertion-to-evidence explanation using only
  supplied IDs. The curator edits each reasoning step, its citations, and any
  explicit insufficient-evidence conclusion in the focused review project.
- Output: reviewed answer-logic records that serve as the benchmark's evidence
  summary, with cited material statements, question coverage, and unresolved
  gaps. Context-only evidence cannot carry a substantive factual step on its
  own.

## Research / learning checkpoint and plan

Trial a few cases to learn whether an assertion map, short prose, or both are
easiest to review. Record the chosen form and why. Revise the proposal prompt
when it bridges a gap without evidence or repeats the official response as
though it were independent proof.

## Validation, review, and acceptance

Validate all cited evidence IDs, direct-support status, question links, and
human approval. Review for missing steps, unsupported inference, and scope
creep. Accept an adequate logic record or a clear stop/insufficiency outcome
per pilot case. Do not write the final reference defense here.
