# Task 09E — Implement the grounding judge

Status: **provisional; not started**. Refresh against accepted 09B/09C outcomes
before execution. Writing this contract does not authorize model execution.
Parent: [Task 09](09_build_evaluation_and_qualify_judges.md).

## Abstract

Implement one independently runnable grounded-correctness judge over the exact
question, structured answer and actual cited evidence. Its purpose is to assess
what those citations establish, without seeing the reference answer or assuming
that matching a citation ID proves the answer correct.

## Goal

Produce a versioned grounding prompt, strict result schema and restartable scorer
using the runner qualified in 09B and grounding packets validated in 09C.
Keep its code, input contract, fixtures and judgment distinct from adequacy.

## Inputs

- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
  and the [evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary).
- Accepted 09B model/runtime/runner decision and 09C grounding packet contract;
  read [architecture](../../docs/architecture.md) before implementation.
- 09A development-only synthetic answers, with expectations stored separately;
  use only the tuning subset designated before prompt development.
- [Artifact contract](../../docs/data_artifacts.md) for external run storage.

## Outputs

- A separately versioned grounding prompt, result schema, scorer and fixtures.
- Saved packet/prompt/model/configuration identities, raw calls, parsed results,
  latency, failures and recovery receipts under the configured external root.
- A compact outcome explaining boundaries, local smoke results and limitations;
  broad synthetic qualification belongs to 09G.

## Research / learning checkpoint

Recheck [Inspect model grading](https://inspect.aisi.org.uk/model-graded.html)
against the selected runner: generic grader defaults are not our rubric and
reference/history interpolation must not leak into this call. Review
[Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
if 09B retains Ollama. Explain why schema validity guarantees a readable result,
not a correct judgment; preserve the project-specific whole-answer score rules.

## Plan / spec requirement

Write a short prompt/input/output spec before code; retain shared transport and
storage utilities from 09B without sharing semantic prompts with 09F.

1. Accept only the scoped question, structured answer with point-citation links,
   and actual resolved cited passages. Exclude reference answers, gold roles,
   automatic matching scores, target identity and synthetic expected outcomes.
2. Delimit answer/source text as data, including any attempted grading
   instructions. Neither official responses nor uncited substitute sources are
   evidence. Missing citations remain explicit; never silently repair them.
3. Anchor whole-answer scores: `2` supported and qualified; `1` a material
   unsupported secondary assertion while remaining actual citations establish
   the conclusion; `0` unsupported/contradicted conclusion or necessary premise.
   Do not average statement scores or penalize harmless missing optional context.
4. Require concise diagnostics for every substantive point, including additions:
   point IDs/text, actual source IDs/locators, supported/unsupported/contradicted
   findings, unjustified inferences and missing material qualifications. Verify
   diagnostic source references resolve in this packet; do not request hidden
   reasoning or introduce another primary score.
5. Handle clean abstention as grounding N/A. An abstention flag containing
   substantive claims does not exempt those claims from assessment. Distinguish
   schema/input/runtime failures from semantic `0` and N/A.
6. Save grounding independently before any adequacy call reveals reference
   material. Reuse a result only when all input/configuration identities match;
   keep bounded retries and all failed attempts visible.

## Validation

- Fixture checks prove forbidden fields never enter rendered requests and
  reference changes cannot change grounding packet bytes.
- Check central versus secondary unsupported claims, misleading missing
  conditions, supported-but-incomplete answers, wrong citations, valid alternate
  citations, scope errors, abstention and injected grading instructions.
- Verify invalid scores/diagnostic locators, timeouts and malformed outputs are
  recorded as failures rather than successful zero scores; test safe resume.
- Use development tuning cases only for an authorized bounded live smoke.
  Run relevant tests plus `make fix`, `make check`, and `git diff --check`.

## Review pass

Use one bounded independent review of information isolation and rubric fidelity,
and one of readable scorer ownership and recovery. Resolve findings before 09G.

## Acceptance criteria

- Grounding runs independently with pinned artifacts and source-linked results.
- Tests enforce information boundaries and distinguish score/N/A/error states.
- Smoke results are described as uncalibrated automated judgments, not human
  agreement; open model weaknesses are passed to 09G without invented thresholds.

## Non-goals

Adequacy implementation, changing references, new human labeling, target
generation, broad model comparisons, full challenge tuning or test-split use.

## Outcome

Pending execution. Record accepted identities, validation and the 09F/09G handoff.
