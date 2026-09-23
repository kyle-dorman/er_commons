# Task 07B: Review Comment Questions

Status: **Provisional draft; revise after 07A.**

## Abstract and goal

For the small pilot chosen in [07A](07a_screen_pilot_candidates.md), build a
separate Label Studio project that records what each original comment asks.
Keep the source comment intact and make its distinct concerns explicit before
reading the official response as an answer. Follow the shared workflow in the
[Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs and outputs

- Input: 07A's approved pilot IDs and exact comment text/spans, including any
  source pairing or truncation limits.
- Codex proposes a concise question or concern list from the comment alone.
  The review form presents the original text, proposal, editable concerns,
  source spans when possible, and `unclear`/`needs_context` outcomes.
- Output: versioned, curator-approved question records tied to original comment
  spans. A reviewed question is curator-only authoring guidance, never a
  replacement for the original comment in target-model input.

## Research / learning checkpoint and plan

Test Label Studio's text and span controls on a small fixture and consult its
maintainer documentation for the chosen form. Record whether the form makes
multi-issue comments easy to review. Start with a few cases, revise form and
prompt as needed, then finish the selected pilot batch.

## Validation, review, and acceptance

Verify every approved concern belongs to its original comment and that all
selected cases have an approved or explicit unresolved status. Human review
must catch omitted material concerns and overinterpretation. Accept when the
approved export can be supplied to 07C without altering source text. Do not
infer response facts, evidence support, or formal eligibility here.
