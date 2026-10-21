# Sprint 2: Brisbane Draft-EIR Defense Vertical Slice

## Goal

Produce a reproducible, evidence-grounded evaluation of Luna and Haiku answering
comment-derived questions about the 2025 Brisbane Baylands Draft EIR. This is a
single-project, supplied-evidence benchmark. It measures answering from approved
source passages; it does not measure retrieval or establish general CEQA competence.

The frozen release has 49 questions: 19 development and 30 test. The completed
locked test preserves all 180 planned answers (two models, three repeats per
question). Task 14's eight-answer review and required quality pass are complete.
Task 15 plans the requested conclusion-judge revision and reevaluation; the
writeup is now Task 16. No new model run is active or authorized by this plan.

## Accepted execution decisions

### Source corpus boundary

The source corpus comprises the official 2025 Draft EIR main report and
appendices. Separately published chapter PDFs are duplicate/recovery sources.
Final EIR responses are curator-only material and never target evidence. The
[Task 03J extraction](../../tasks/sprint2/03j_run_final_canonical_extraction.md),
[Task 06H accepted handoff](../../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
and [Task 05H response inventory](../../tasks/sprint2/05h_review_and_freeze_response_inventory.md)
own exact corpus, usability, provenance and linking boundaries.

### Canonical extraction boundary

Preserve producer outputs, immutable canonical records and regenerable review
cache as separate layers. Native text/table extraction, source anchors and the
accepted human usability registry determine usable evidence. No OCR or implicit
visual interpretation is part of this condition. Canonical table content comes
from the clean table pipeline; source observations and human review remain
separate. Consume the matching extraction, review and handoff identities rather
than mixing lineages. The [architecture](../architecture.md) and
[artifact contract](../data_artifacts.md) own maintained implementation and storage.

### Task 08 eligibility, clustering, and split boundary

The [08H release](../specs/task08h_final_result.json) freezes 49 human-approved
questions and the exact 19-development/30-test allocation. Each case preserves
its original comment, single scoped question, approved answer and source evidence.
Human review determines eligibility: essential evidence cannot depend on later
revisions, Final EIR analysis, unavailable external or visual evidence, or unusable
source content. No automatic eligibility decision is inferred from provenance.

Related topics and source passages cross the split. The
[08G review](../../tasks/sprint2/08g_review_case_clusters.md) owns the limited
similarity assessment; this is neither an unseen-topic nor unseen-evidence test.
The [Task 08 umbrella](../../tasks/sprint2/08_curate_grouped_benchmark.md) owns
selection and authoring provenance. Changes require a named revision, not an
implicit merger, resplit or reference correction.

### Model-assisted reference-case authoring

Human approval owns the frozen question, evidence and reference answer. Model
proposals remain distinguishable from human decisions. Preserve support/context
roles, source anchors, exact approved text and revision history. Reference answers,
curator reasoning and official responses stay out of target inputs. The
[Task 07 umbrella](../../tasks/sprint2/07_pilot_reference_case_authoring.md) and
[Task 08 umbrella](../../tasks/sprint2/08_curate_grouped_benchmark.md) own the
completed authoring process and its limitations.

### First baseline: supplied evidence

[Decision 007](../decisions/007_evidence_only_first_baseline.md) defines the condition:
the exact question and all approved cited passages, complete and unranked, with
stable citation IDs. [Task 10](../../tasks/sprint2/10_prepare_evidence_only_inputs.md)
owns the target-only projection and its isolation from reference content.

Use the [11E frozen configuration](../specs/task11e_frozen_generation_v1.json)
for exact Luna/Haiku identities, prompts, invented nonbenchmark examples, shared
document overview, reasoning settings and 12,288-token output allowance. The
three native unseeded repeats are retained individually. Do not select favorable
repeats, replace failures or tune on test outcomes. The
[Task 13 outcome](../../tasks/sprint2/13_run_locked_test.md) owns the completed
zero-retry execution, operational limits and sealed identities.

### Deferred retrieval design

BM25, agentic search and retrieval-versus-supplied-evidence comparisons require
separately scoped work. The [historical plan](../history/sprint2_history.md#deferred-retrieval-design)
retains earlier retrieval proposals for reconsideration; none constrains this
condition or authorizes implementation.

### Model roles

Keep reference authoring, target generation and automated judging separate.
Presented results include Luna and Haiku only. MiniMax is an archived side
experiment, excluded from presented results and further exploration; its evidence
remains in [Task 13A](../../tasks/sprint2/13a_minimax_cloud_comparison.md).
The [09G freeze](../specs/task09g_judge_freeze_v1.json) owns selected judge identities.
The same frozen scoped question reaches targets and judges; the original comment
cannot introduce additional unasked scoring requirements.

## Execution sequence

1. **[Task 14 — Selective review](../../tasks/sprint2/14_selective_failure_review.md): complete.**
   The result pointer selects the confirmed eight-answer synthesis and quality
   records. Frozen scores stay unchanged and unresolved judgments remain explicit.
2. **[Task 15 — Revise conclusion judge](../../tasks/sprint2/15_revise_conclusion_judge.md): planned.**
   Revise C rules/prompt, regenerate synthetic tests, iterate on the original six
   then all nineteen development questions, freeze, reevaluate all thirty test
   questions and review conclusion outcomes. Prefer same-answer C comparisons to
   isolate evaluator changes; resolve any requested fresh-generation arm and
   numerical execution limits before calls. The thirty are exposed to the redesign,
   so reevaluation cannot be described as fresh held-out qualification. Preserve
   the original experiment and keep A/G/S and target settings fixed initially.
3. **[Task 16 — Methods/results writeup](../../tasks/sprint2/16_write_methods_and_results.md): provisional.**
   After Task 15 acceptance and separate activation, explain construction,
   methods, original/revised results and limits using versioned figures and
   reviewed examples. Keep development, test and synthetic diagnostics separate.
   Finish with a next-project decision.

Completed implementation and maintenance are documented in numbered task outcomes.
The [sealed Task 13 result](../specs/task13_result.json) selects the test publication;
the [Task 12 result](../specs/task12_result.json) selects development reporting.
The [reporting maintainer guide](../reporting_maintainer_guide.md) owns reuse.
Earlier sequencing and superseded proposals are preserved in the
[historical sprint snapshot](../history/sprint2_history.md).

## UI and artifact boundary

Use a structured chat review for Task 14, with persistent selected-answer IDs,
evidence references, observations, Kyle's feedback and unresolved questions.
Do not start a full labeling interface or human-calibration study. Generated
reviews, figures, tables and underlying data stay under `ER_COMMONS_DATA_ROOT`;
tracked documentation contains contracts and compact pointers. Preserve sealed
source artifacts and make review commentary a separate derivative.

## Benchmark evaluation boundary

The maintained [reporting definitions](../specs/task12_reporting_v1.md), their
amendments in the [reporting guide](../reporting_maintainer_guide.md), and the
[09G freeze](../specs/task09g_judge_freeze_v1.json) own exact scoring and joins.
A classifies answer routing; G evaluates required supporting/qualification points;
S measures support sufficiency; C evaluates the conclusion independently. Joint
success requires applicable automatic/A/G/S/C results on the same answer.
Citation recall/F1 is diagnostic, with no new joint-success threshold.

Retain failures, unavailable judgments, N/A values and planned denominators.
Never combine passing components across repeats. Report all 30 test questions
together, separate from development. Synthetic challenge diagnostics do not
establish human calibration or an untouched held-out judge qualification.
Reserved judge challenges remain reserved. Task 14's selective commentary neither
changes frozen scores nor estimates population error rates or human agreement.

### Structured answer output

The frozen schema uses a conclusion, supporting points, material qualifications,
optional context and explicit citation links. Target and reference may differ
in wording and point count. Citation validity and abstention routing follow the
frozen contracts; a substantive assertion cannot avoid grounding checks merely
by carrying an abstention status.

### Automatic citation metrics

Use sets of canonical section/table units within each case; keep invalid citation
attempts in a separate set:

- `S`: reviewed support units; `C`: reviewed context-only units, disjoint from `S`.
  A unit used as support anywhere in the reviewed case belongs to `S`.
- `R`: units actually returned to the target within the recorded retrieval budget.
- `A`: units explicitly cited by the final model output, not everything retrieved.
  Point-to-citation links declare sources used by the structured answer; repeated
  IDs count once for these metrics while their individual links remain auditable.
- `U`: distinct invalid/unresolvable citation attempts, represented by stable raw
  identifier tokens. They cannot match support/context units.

**Retrieval recall (deferred retrieval conditions only)** is `|R ∩ S| / |S|`. It measures whether supporting sources
reached the model, including results across queries only in a separately approved
multi-query condition. Searching a document does not count as retrieving every
reference unit inside it.
For the current supplied-evidence baseline, report retrieval recall as not
applicable, not perfect recall from the provided reference passages.

**Final-citation recall** is `|A ∩ S| / |S|`.
**Final-citation precision** is `|A ∩ S| / (|A \ C| + |U|)`.
**Final-citation F1** is `2 × precision × recall / (precision + recall)`,
using the final-citation metrics above, not the retrieved-unit set `R`.
Known context citations are neutral: they neither satisfy required recall nor
count as false positives. Valid but unmatched citations stay in the precision denominator; invalid attempts
enter through `U` and are flagged by mechanical validation, never silently
discarded to improve precision. Deduplicate
invalid repeated identifiers as well. If `S` is nonempty but the scored final
citation set is empty (`A \ C` and `U` both empty, including context-only
output), define precision/recall/F1 as `0`. If `S` is empty, required
citation metrics are not applicable; report that case separately. F1 is `0` when
precision and recall are both `0`. Record numerators, denominators, optional-context
counts and per-case scores; aggregate as separate macro/micro reports with explicit
eligible case counts rather than a single blended benchmark score.

These are reference-set matching metrics, not proof of correctness. Alternative
valid evidence missing from the authored reference can lower measured precision;
preserve it for error analysis or separately authorized human review without
silently editing the frozen test reference. Likewise, all right citations can accompany a reversed conclusion or
unsupported inference. Automatic citation scores do not establish logical use.
Canonical-ID/anchor projection, schema validity, allowed corpus and citation
resolution remain deterministic checks independent of the frozen A/G/S/C judgments.

### Judge qualification and labeling budget

Treat judge results as uncalibrated automated judgments. The
[judge maintainer guide](../judge_maintainer_guide.md) and completed
[09G task](../../tasks/sprint2/09g_challenge_and_freeze_judges.md) own qualification
provenance and limitations. Human reference approval is not judge validation.
Task 14 provides bounded, evidence-backed interpretation; new calibration,
reannotation, model calls or scoring revisions require separate scope.

## Completion gate

The sprint is ready for a second-project decision when the sealed locked test is
reproducible, citations and reporting are verified, selected human-reviewed
examples explain material limitations, Task 15's revised evaluation is accepted,
and Task 16 presents the methods and
results with explicit scope and uncalibrated-judge limitations.
