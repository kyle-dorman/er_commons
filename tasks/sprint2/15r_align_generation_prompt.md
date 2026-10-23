# Task15R — Align the generation prompt with accepted conclusion rules

Status: complete; approved prompt changes implemented.

## Goal and authorization

Implement the user's approved step7 wording changes: a complete natural-paragraph
conclusion, substantive why/how explanation, necessary scope/qualifications, a
preference for including supported detail when unsure whether it is necessary,
and an explicit whole-conclusion contradiction check. Preserve the answer schema,
evidence/citation requirements, support requirements and abstention behavior.

## Plan and validation

Create a new prompt from the frozen Task11D12 prompt; do not mutate historical
prompt bytes or run bindings. Change only answer requirements1 and5. Keep the
shared Baylands overview unchanged and delivered by the existing composition path.
Bind the new prompt and predecessor hashes in a compact specification, review the
diff, independently check scope and wording, and run git diff --check. No new tests
are needed for this text-only change; verify all other prompt sections byte-for-byte.

The prior step7 discussion supplies the approved wording and user preference.
This implements those decisions, without further policy research or model calls.
Step8's models, population, repetitions and separate budget remain unselected.
No new synthetics, target generation, A/G/S edits, reference exposure, commits or pushes.

## Outcome

Created [the revised generation prompt](../../docs/prompts/task15r_conclusion_alignment_v1.md)
and its [hash-bound selection](../../docs/specs/task15r_generation_prompt_v1.json).
Only requirements1 and5 changed: natural-paragraph completeness, explicit why/how
substance and connection, fuller supported answers when uncertain, and a check for
incompatible claims throughout the conclusion. All remaining prompt bytes are
unchanged, including examples, citations, supporting-point duties, scope and
abstention requirements. The original frozen prompt and overview hashes verified.

An independent review confirmed scope and all specification hashes; git diff
--check passed. No model calls or runtime changes. Step7 is complete; step8 still
needs the run models, population, repetitions and separate budget agreement.
No commits or pushes.
