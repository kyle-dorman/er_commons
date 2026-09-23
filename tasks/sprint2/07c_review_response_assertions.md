# Task 07C: Review Official-Response Assertions

Status: **Provisional draft; revise after 07B.**

## Abstract and goal

Build one Label Studio project for decomposing each pilot case's official
response into candidate facts, qualifications, and conclusions. A reviewable
assertion map prevents an apparently relevant section citation from silently
standing in for an unsupported boundary or other material fact. Follow the
[Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs and outputs

- Input: approved 07B questions; exact individual and incorporated general
  responses with their separate source IDs, spans, and relationship warnings.
- Codex proposes atomic assertions with response span, type, qualification,
  attribution, and question link. The curator can split, merge, amend, reject,
  or mark an assertion unresolved in the stage-specific Label Studio form.
- Output: reviewed assertion records with stable IDs, retained unassigned
  claims, source attribution, and explicit unresolved issues. These are claims
  made by the response, not verified facts about the Draft EIR.

## Research / learning checkpoint and plan

Compare the proposed form with the
[backlog claim-map design](../../docs/backlog.md) and test its ability to retain
response spans and qualifications without forcing every assertion into one
question. Trial a few cases, refine the prompt and form, then review the pilot
batch. Keep general-response attribution visible.

## Validation, review, and acceptance

Check source-span integrity, ID uniqueness, coverage of material response
statements, and explicit treatment of qualifications and conclusions. Human
review determines whether the decomposition is faithful. Accept when each
pilot response has a reviewed assertion map or an unresolved stop. Do not
treat response citations as verified support or draft a defense here.
