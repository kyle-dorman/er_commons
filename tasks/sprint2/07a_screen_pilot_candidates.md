# Task 07A: Screen Pilot Candidates

Status: **Draft for user review; first proposed Task 07 subtask.**

## Abstract and goal

Build the first Label Studio project and review at least 50 distinct
comment-response pairs from the accepted Task 05H inventory. Learn which
pairs are good material for the Task 07 authoring pilot. This is a pilot-fit
screen, not Task 08 eligibility or an automated filter of the whole inventory.
The [Task 07 umbrella](07_pilot_reference_case_authoring.md) owns the shared
batch workflow and provenance rules.

## Inputs and outputs

- Input: one pinned 05H handoff, resolved individual/general-response views,
  relationship IDs, reference warnings, and usable-source status. Preserve
  one-to-many and many-to-one relationships rather than inventing a pair.
- Select a reproducible, varied review batch of at least 50 distinct pairs;
  record selection method and coverage across commenters, issues, response
  types, explicit references, and known source limitations.
- Output: Label Studio screening project, checked-in form/schema and small
  import/export helpers, Codex proposal batch, and curator-reviewed decisions.
  Each decision has `great_fit`, `ok_fit`, or `skip_for_pilot`, multiple reason
  codes where useful, a brief rationale, source IDs, and reviewed input version.
- Output: ranked or priority-grouped great fits, a small varied selection
  (initial target 6–10), and an attrition/coverage summary. If the great-fit
  pool is inadequate, review another named batch before selecting the pilot.

## Research / learning checkpoint

Check the installed Label Studio version and official import/export guidance
before choosing the form. Try a small real-looking fixture to learn whether
rating, multiple skip reasons, and optional notes are comfortable to edit.
Explain the difference between *pilot fit* and formal case eligibility.

## Plan and review loop

Define review criteria before the first 50 decisions: a great fit has a clear
comment concern, identifiable response, and manageable evidence-checking path;
an OK fit is usable but more complex. Reasons distinguish a likely eligibility
problem (for example unavailable required evidence) from a pilot deferral
(for example too many intertwined issues). Codex proposes ratings in a
separate task; the curator reads and decides on every pair. Trial a small batch,
revise the form or prompt in a new named version, then complete the 50+ review.
Select for both quality and variety, not simply ease or Codex score.

## Validation, acceptance, and non-goals

Verify distinct source relationships, complete human dispositions, valid
reason codes, proposal/review separation, reproducible sampling, and exported
counts. Review the interface and screening definitions before using the chosen
subset downstream. Accept when 50+ pairs have human decisions and the selected
pilot and rationale are recorded. Do not inspect every inventory pair, declare
formal eligibility, or start question authoring in this subtask.
