# Task 09C — Build judge evidence packets and validation

Status: provisional; revise from accepted 09A/09B outcomes before activation.
This planning contract does not start inference or mutate benchmark inputs.

## Abstract

Build deterministic, source-bound inputs for two independent judges. Preserve
the exact evidence needed to assess an answer while preventing reference and
synthetic-label leakage. The [Task 09 umbrella](09_build_evaluation_and_qualify_judges.md)
owns sequence; this task owns packet construction, not judgment.

## Goal

Produce inspectable grounding and adequacy packets from saved structured answers
and the frozen corpus, with explicit citation-resolution and context diagnostics.

## Inputs

- [08H release](../../docs/specs/task08h_final_result.json), development membership,
  target-only questions, curator references, source identities and completion seal.
- Accepted [09A](09a_create_synthetic_challenges.md) variant schema and
  [09B](09b_choose_harness_and_qualify_local_judge.md) transport/context limits.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [sprint evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary),
  [architecture](../../docs/architecture.md), and [artifact rules](../../docs/data_artifacts.md).

## Outputs

- Versioned packet schemas and narrow, typed package-backed builders/resolvers.
- Separate grounding and adequacy packets with exact source locators, point links,
  input hashes, citation-resolution status and context-size diagnostics.
- External manifest binding input answer/version, case, release, source inventory,
  packet policy and deterministic outputs; no rewrite of frozen source artifacts.
- Fixtures demonstrating information separation, invalid-citation handling,
  complete table context and explicit overflow behavior.

## Research / learning checkpoint

Inspect the maintained source-unit/citation assembly interfaces before inventing
another resolver. Use Decision 006 and the frozen release schemas as authorities.
Review [Inspect custom scorers](https://inspect.aisi.org.uk/scorers.html) if 09B
selects Inspect, and the accepted runtime's context controls. Explain why supplying
the wrong or incomplete passage can look like judge failure, and why declared
metadata separation is insufficient unless the serialized request is checked.

## Plan / spec requirement

Write a brief packet specification and boundary table before implementation:

| Input | Grounding | Adequacy |
| --- | --- | --- |
| Exact scoped question and candidate answer, including point links | Include | Include |
| Actual candidate-cited passages and unresolved-citation markers | Include | Include |
| Approved structured reference and reviewed evidence pool | Exclude | Include |
| Gold support/context classifications | Exclude | Only as required by the adequacy contract |
| Synthetic expected scores, edit/failure labels and generator rationale | Exclude | Exclude |
| Automatic matching scores and target/generator identity | Exclude | Exclude |
| Official-response claims as evidence | Exclude | Exclude |

1. Verify the exact frozen release and development allowlist before loading cases;
   reject held-out cases in development preparation. Keep expected-score records
   in a separate analysis channel rather than passing whole variant records.
2. Resolve declared citation IDs to the frozen canonical section/table identities.
   Preserve point-to-citation links and invalid raw tokens. Never replace a wrong
   citation with the source the answer should have used, or augment grounding
   from the reference's evidence pool.
3. Reuse accepted unit assembly for headings, source order, table continuations,
   captions, units and notes. Bind added context to its source and record why it
   is included; do not silently expand grounding to uncited evidence. Preserve
   inherited text-only figure and extraction limits.
4. Build two independent allowlisted payloads, not a shared conversation with
   references progressively exposed. Shared transport is allowed; hidden fields
   must not appear in prompt text, metadata visible to the model or chat history.
5. Preflight complete request length with the selected model/output reserve.
   Oversized packets receive an explicit non-score status and diagnostic. Do not
   silently truncate, summarize, omit qualifications or claim unsupported context
   fits. Any alternative context policy requires an explicit recorded revision.
6. Treat answer/source text as untrusted quoted content. Preserve adversarial
   content for robustness tests without promoting it to judge instructions.

## Validation

Check exact serialized payloads for forbidden sentinel strings, including
expectations nested in provenance. Cover reordered/split points, joint citations,
real irrelevant sources, repeated/unknown IDs, verified alternative evidence,
table notes, abstentions with assertions and context overflow. Verify deterministic
hashes and unchanged upstream artifacts. Run `make fix`, `make check` and
`git diff --check` for implementation/documentation changes.

## Acceptance criteria

- Packets preserve actual evidence and citation relationships without repairing
  candidate answers or exposing synthetic expectations to either judge.
- Grounding cannot access the reference or gold roles; adequacy can evaluate
  alternative arguments using actual cited passages.
- Missing required source files, forbidden inputs and oversized packets are
  explicit infrastructure/input failures, distinct from rubric scores. An answer
  deliberately citing an unknown ID is instead a valid challenge packet with an
  unresolved-citation marker; it must reach semantic assessment without repair.
  Schema diagnostics do not become a fifth semantic metric.
- Future 09E/09F tasks can consume these packets independently through 09B.

## Review pass

Review information boundaries and citation/table completeness separately; integrate
findings before accepting the packet specification and implementations.

## Non-goals

No judge prompts/scoring, reference relabeling, source repair, new retrieval
condition, model-generated source summaries, target runs or test-case development.

## Outcome

Pending. Record schemas, evidence policy, validation and unresolved context limits.
