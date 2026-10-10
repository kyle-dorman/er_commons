# Task 09D — Implement automatic retrieval and citation metrics

Status: provisional; revise from accepted preceding outcomes before activation.
No retrieval or target run is authorized by this planning contract.

## Abstract

Implement deterministic reference-set matching with auditable denominators and
edge cases. Keep retrieval discovery and final citation selection separate from
semantic judgments. The [Task 09 umbrella](09_build_evaluation_and_qualify_judges.md)
owns sequence and [the sprint](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#automatic-citation-metrics)
owns exact formulas; this task implements, rather than redesigns, those rules.

## Goal

Produce reproducible per-case and aggregate metrics from saved answer citations,
frozen reference roles and actual retrieval receipts when available.

## Inputs

- [08H release](../../docs/specs/task08h_final_result.json), case/split membership,
  canonical citation units and approved support/context pools.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  accepted [09A](09a_create_synthetic_challenges.md) answers and
  [09C](09c_build_judge_evidence_packets.md) resolution diagnostics.
- [Architecture](../../docs/architecture.md), [artifact rules](../../docs/data_artifacts.md)
  and invented retrieval receipts for fixtures. Production retrieval starts in
  Task 10; synthetic answers do not establish which passages a target received.

## Outputs

- Pure typed metric functions and a small maintained CLI/report adapter.
- Versioned per-case records with canonical sets, invalid tokens, raw hits,
  denominators, neutral-context counts, validity/N/A status and separate metrics.
- Macro/micro summaries with explicit eligible counts and complete-case recall;
  inspectable fixtures and a compact explanation of reference-match limitations.

## Research / learning checkpoint

Read the sprint formula/edge-case contract and the released role projections.
Inspect existing canonical citation resolution rather than inventing text matching.
[ALCE](https://arxiv.org/abs/2305.14627), linked by Decision 006, motivates separating
answer and citation quality; it does not define this project's support/context
formulas. Explain why correct alternate evidence may lose matching credit and why
correct citation IDs do not establish a sound argument.

## Plan / spec requirement

Write a compact test table and metric-record specification before implementation.
Use per-case sets of canonical section/table units:

- `S`: reviewed support. `C`: reviewed context-only, disjoint from `S`; any
  reviewed support use wins over context use for that unit.
- `R`: distinct units actually returned within the recorded condition/budget.
- `A`: distinct resolvable units explicitly cited by the final answer's links.
- `U`: distinct invalid/unresolvable attempts as stable raw identifier tokens.

Implement these formulas without substituting one set for another:

- Retrieval recall: `|R ∩ S| / |S|`.
- Final-citation recall: `|A ∩ S| / |S|`.
- Final-citation precision: `|A ∩ S| / (|A \ C| + |U|)`.
- Final-citation F1: `2 * precision * recall / (precision + recall)`.

Known context is neutral; unmatched valid citations and invalid attempts remain
in precision's denominator. Deduplicate valid and invalid repeated IDs while
retaining original point links for audit. With nonempty `S` and an empty scored
final set, including context-only output, all three final-citation metrics are
zero. Empty `S` makes required-reference metrics N/A and excludes the case from
applicable aggregates; report it separately. F1 is zero when precision and recall
are both zero. Compute micro scores from summed applicable raw counts, then micro
F1 from micro precision/recall; compute macro means over eligible case scores.

Do not fabricate `R` for synthetic variants or report absent receipts as zero
retrieval performance. Mark retrieval unavailable for such records. Distinguish
unavailable inputs from measured empty retrieval. Fixture receipts must be labeled
invented and cannot be published as target-run evidence. Preserve malformed-answer
diagnostics and raw citation attempts; never silently drop invalid rows to inflate
aggregates. Resolve any extraction ambiguity explicitly before freezing that rule.

Specify the receipt interface now; Task 10 owns the final fragment-to-canonical
anchor projection. A fragment inheriting a section ID cannot earn full-unit credit
without the required anchors actually being present. Exercise this with fixtures
and leave production projection qualification to Task 10/12.

For eventual retrieval receipts, retain the top-five primary condition, diagnostic
recall at 1/3/5/10/20, and complete-case recall. A deeper ranked hit is not a passage
delivered to the model. Record budget-achievable recall ceilings where `|S|` exceeds
the unit budget, without changing the reference denominator. Multi-query unions
apply only to separately approved conditions, not the baseline.

## Validation

Use hand-calculated fixtures for perfect/empty/partial results, context-only sets,
support/context overlap, repeated IDs, invalid attempts, unmatched valid sources,
empty `S`, missing versus empty retrieval, citation/retrieval divergence, abstention,
and macro/micro differences. Confirm extra repeated citations cannot improve scores
and reversed answer text with unchanged links leaves automatic metrics unchanged.
Run `make fix`, `make check` and `git diff --check`.

## Acceptance criteria

- Formula and edge-case fixtures match the sprint contract exactly.
- Every summary can be reconstructed from per-case counts and eligibility states.
- Retrieval availability and actual receipt provenance remain explicit.
- Automatic outputs stay outside both judge packets and remain separate results.

## Review pass

Use a bounded independent arithmetic/edge-case review and check maintainability of
pure functions, thin I/O adapters and source identity reuse.

## Non-goals

No BM25 implementation, target inference, judge scoring, blended benchmark score,
new support labels, alternative-evidence promotion or held-out test evaluation.

## Outcome

Pending. Record validation, exact metric schema and downstream receipt requirements.
