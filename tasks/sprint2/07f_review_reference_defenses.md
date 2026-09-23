# Task 07F: Review Reference Defenses

Status: **Provisional draft; revise after 07E.**

## Abstract and goal

Build the final authoring project in Label Studio. Codex drafts a response to
the original comment from the reviewed question, assertion, evidence, and
logic records; the curator edits the full defense. Follow the shared workflow
in the [Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs and outputs

- Input: original comment and all approved 07B–07E records. The official
  response remains curator context, not independent evidence.
- Codex proposes a concise defense with sentence-level references to supplied
  direct-support IDs or an explicit insufficient-evidence outcome.
- Output: curator-reviewed reference defenses, exact citation mappings, and
  unresolved/failed-case records. Render human-readable citations from
  canonical IDs instead of trusting generated citation strings.

## Research / learning checkpoint and plan

Trial the review form on a small varied subset, checking whether the defense
answers every concern without overclaiming. Revise prompt and form under named
versions before finishing the selected pilot. Record how much editing the
curator performs and why.

## Validation, review, and acceptance

Check every citation ID, sentence-level support, question coverage, canonical
anchor, and final human disposition. Review the defense against the original
comment and evidence, not just the official response. Accept only supported
defenses or explicit insufficient-evidence outcomes. Do not run the target
model, freeze splits, or claim Task 08 eligibility.
