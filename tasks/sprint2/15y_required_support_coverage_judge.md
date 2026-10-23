# Task15Y — Judge required-point coverage in model support

Status: provisional; task specification only. User has not activated implementation
or new paid calls.

## Abstract and goal

Add a separate diagnostic judge to distinguish required answer content absent
from the entire response from content present in supporting points but omitted
from the conclusion. Each required reference point gets its own independent
binary judgment. This supplements C, S and G; it does not replace them or add an
overall benchmark pass requirement.

This is follow-up1 of3:15Y, then15Z citation review, then
[15AD final end-to-end run](15ad_final_end_to_end_run.md).

## Inputs

- Approved structured references: `docs/specs/task15ac_reference_result.json`.
- Selected saved answers: `docs/specs/task15t_retry_result.json`; high-reasoning
  experiment separately selected by `docs/specs/task15w_haiku_16k_retry_result.json`.
- Preserve canonical required-point IDs when joining diagnostics;15AC provides
  reversible sequential wire-ID mappings for C. C034 has a new question, so older
  answers must be labeled historical-question diagnostics, not current-version results.
- Current judge contracts and adapters via `docs/judge_maintainer_guide.md`.
- Task15X review and discussion: C032 Haiku repeat2 contains required detention
  replacement in S4, accepted by G, but omits it from its conclusion. S passes;
  G fails a separate qualification Q3. This is an exposed diagnostic example.

## Proposed contract and outputs

One request per required reference point, containing the shared project overview,
question, that one required point, and all candidate supporting points with IDs.
Do not expose the candidate conclusion, other judges' verdicts, source passages,
reference support prose or optional reference points. Supporting points may jointly
convey the required meaning. The initial scope is supporting_points only; separate
qualifications and optional_context do not silently enter this coverage check.

Return `covered: true/false`, supporting-point IDs and a concise reason. Binary
false includes missing, incomplete or incompatible coverage; do not introduce a
third semantic label. Accept equivalent meaning without incidental wording.
Define mixed correct/conflicting support explicitly before implementation. Invalid
outputs and unavailable calls remain operational states, never false labels.

Produce a versioned general rule/prompt/schema, narrow existing-runner integration,
bounded development validation and an identity-bound diagnostic report. Join each
required point to C's corresponding point judgment, preserving C missing versus
contradicted, and to relevant G results without equating coverage with grounding.
Report support-covered/C-missing separately from support-missing/C-missing and
other combinations. Do not infer missing source knowledge merely from missing
response content. Keep candidate repeats distinct from judge repeats.

## Research / learning checkpoint and plan

Inspect maintained C/S/G contracts and native adapter reuse before selecting the
smallest implementation. Explain coverage versus source grounding, inference
support and conclusion adequacy. Review binary semantic-coverage evaluation
practice using primary documentation before implementing; record the chosen
approach without creating a new framework.

On activation, finalize the input boundary and mixed-claim rule, freeze reference
version and predeclare a small development validation set. Include paraphrase,
coverage spanning support points, partial coverage, unrelated support, and
contradiction controls. Inspect both expected labels, not only known C failures.
Specify model, numerical budget, concurrency, population and stopping conditions
before any paid dispatch. Existing spending approvals do not activate this task.

## Validation, review and acceptance

- Verify one required point per request and isolation from C verdict/conclusion.
- Test schema, point IDs, semantic controls, exact identity joins and restartability.
- Conduct a bounded independent rule/implementation review; run appropriate
  `make fix`, `make check` and `git diff --check` after implementation.
- Save new artifacts beneath a fresh Task15 namespace, completion-last with
  provenance and a compact result pointer. Report disagreement and limitations.
- Overall scores remain unchanged. Coverage of a disputed required label does not
  settle whether that label should be mandatory.15AA resolved C017 storage as optional
  and removed VMT from C014; consume the published decisions, not older proposals.

## Non-goals

No implementation, synthetic generation or paid calls in the task-writing turn.
No label, C/S/G, target-prompt or historic-score changes; no new target generation,
MiniMax, reserved challenges, commits or pushes. Task16 remains separately gated.
