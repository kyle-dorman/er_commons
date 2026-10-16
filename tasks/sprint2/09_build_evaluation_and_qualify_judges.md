# Task 09 — Build evaluation and freeze the judge components

Status: **complete with documented limitations**, including 09F.2 production
cleanup and the documentation-only [09G freeze](09g_challenge_and_freeze_judges.md).
The [freeze manifest](../../docs/specs/task09g_judge_freeze_v1.json) binds the
committed implementation, selected configurations and existing evaluation evidence.
Next: Task 10 retrieval, then Task 11 target generation and Task 12 integration.

## Abstract and goal

Build independently testable evaluation components before retriever/target
implementation. Automatic retrieval and citation metrics remain separate from
A (no-answer classification), G (point grounding), S (support sufficiency) and
C (conclusion adequacy). Synthetic development comparisons expose weaknesses;
reviewed proposed labels are not human gold or proof of general reliability.

## Current outputs and ownership

- Selected models: Luna A v2 / G v3 / C v8; Haiku S v6. Native Inspect owns
  execution, with Fireworks/GLM and local Ollama diagnostic alternatives retained.
- [Production guide](../../docs/judge_maintainer_guide.md): supported interfaces,
  input isolation, failure handling, provider settings and historical replay.
- [Current question publication](../../docs/specs/task09f_question_publication_v2_result.json):
  49 cases, unchanged 19-development / 30-test split.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
  and current component rules own evaluation semantics. A uses three classifications;
  G/S/C decisions are binary. Earlier 0/1/2 judge records remain historical.
- [Task 12](12_integrate_evaluation_and_reporting.md) owns whole-answer routing,
  evidence delivery/adapter checks, joins, denominators, strict joint reporting and
  the real-development integration check. It is not complete through this freeze.

## Completed subtask records

| Task | Retained outcome |
| --- | --- |
| [09A](09a_create_synthetic_challenges.md), [09A.2](09a2_regenerate_point_expectations.md), [09A.3](09a3_add_clean_abstentions.md) | Synthetic development data, proposed expectations, coverage and immutable reservation history |
| [09B](09b_choose_harness_and_qualify_local_judge.md) | Historical harness/local inference comparison and limitations |
| [09C](09c_build_judge_evidence_packets.md) | Separate packet projection, source integrity and context diagnostics |
| [09D](09d_implement_automatic_metrics.md) | Offline automatic metric validation and retrieval-receipt contract |
| [09E](09e_implement_grounding_judge.md), [09E.1](09e1_compare_cloud_and_decision_judges.md), [09E.2](09e2_cleanup_grounding_judges.md) | Historical grounding experiments, provider comparisons and earlier cleanup |
| [09F](09f_implement_adequacy_judge.md) | Selected C/S judges and full-development comparison |
| [09F.1](09f1_revisit_grounding_judge.md) | Selected A/G judges and full-development comparisons |
| [09F.2](09f2_cleanup_production_judges.md) | Shared native provider configuration, selected-only cores, offline parity and full checks |
| [09G](09g_challenge_and_freeze_judges.md) | Documentation-only freeze of existing outcomes; no new inference |

## Validation and learning

Component records contain independent policy/data reviews, repeated evaluations,
failure analysis and runtime tests. Cleanup preserved exact selected prompt/schema
identities, parser/projection behavior and all historical result pointers. Final
implementation checks passed: 3,975 tests, one skipped, plus formatting/lint/types.
The 09G closeout verifies bindings and documentation only.

The original 09G reserved-development final-check requirement was explicitly
superseded by Kyle's documentation-only scope. Historical reserved variants remain
preserved; no new reserved check or benchmark-test qualification is claimed.
Full-development comparisons include correlated variants and calibration overlap.
They support model selection, not independent or human-calibrated accuracy.
Separate component scores cannot establish a measured joint pass rate.

## Non-goals and downstream gates

No further prompt cycles, model comparisons, label changes or inference are required
to close Task 09. No test answers entered judge development. Retrieval/target work
belongs to Tasks 10/11; Task 12 must validate actual routing and reporting before
Task 13's separately authorized locked benchmark execution. Native Ollama aliases
remain diagnostic, with runtime identity/context unqualified for the new adapter.

## Outcome

The development-selected evaluator is frozen with known limitations. Production
source, dependency lock, models, prompts, schemas, settings, policies, data-publication
pointers and comparison evidence are bound in the 09G manifest. Earlier task records
preserve historical experiments and commands; current execution follows the
production guide. Task 10 is next.
