# LLM-as-a-judge: learning notes for future calibration

Recorded 2026-09-25 after discussing Li et al.,
[From Generation to Judgment: Opportunities and Challenges of LLM-as-a-judge](https://aclanthology.org/2025.emnlp-main.138.pdf)
(EMNLP 2025).

These are design questions and proposed development experiments for Tasks 09
and 12, not a new evaluation contract or authorization to run a judge. The
[Sprint 2 evaluation boundary](sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
continues to own the rubric, staged information access, judge input boundaries and labeling budget.

## Current decision — 2026-10-08

[Decision 006](decisions/006_structured_answers_four_part_evaluation.md) supersedes
conflicting suggestions below: two automatic results and two separate LLM answer
judgments, one structured cited reference answer, and no mandatory labeling after
08F. Human calibration is optional and separately authorized; without it report
uncalibrated automated judgments. Earlier calibration ideas are possible future
experiments, not prerequisites. Grounding includes the question but hides the
reference; adequacy adds the reference and accepts substantively valid alternatives.

## Earlier plan amendment (2026-09-29)

The adopted plan now separates automatic retrieval recall and final-citation
precision/recall/F1 from two answer judgments: grounded correctness and answer
adequacy. It replaces the earlier three judged dimensions. The reference answer
is reviewed once with its reasoning in combined 07E/07F, not as an outline and a
separate polished answer. Both judges use the same frozen scoped question as the
target. The sprint plan owns the exact formulas, reference visibility and gates.

This design follows the practical distinction between deterministic checks and
rubric-based judgments, while retaining human calibration and room for valid
alternative solutions; see [Anthropic's evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
The choice of two dimensions and our support/context policy are project decisions,
not claims that this particular benchmark design has been externally validated.

## What the paper contributes

The survey maps judging attributes, methods, and benchmarks. Useful entry
points are rule augmentation (§4.2.2), evaluating judges (§6), presentation
biases (§7.1), and human–LLM co-judgment (§7.4). It is more useful as a
literature map than as a procedure for deciding whether a particular judge is
trustworthy for our task. The project implications below are our extrapolations,
not findings demonstrated by the paper.

## What a successful judgment establishes

Keep agency-response similarity, support from cited Draft EIR evidence,
responsiveness to the comment, and substantive adequacy of the underlying
analysis distinct. A response can accurately cite the Draft EIR while evading
a criticism of its assumptions. Even perfect rubric agreement establishes only
the capabilities that the rubric measures.

Grounded correctness checks claims and conclusions against cited source text.
Answer adequacy checks responsiveness and essential substance together. Automatic
citation matching measures source selection, not either of those qualities.
Check adequacy judgments and citation precision for penalties against valid
alternative arguments or sources missing from the authored reference. An official response is a curation lead, not proof of truth.

Case selection further limits interpretation: results on comments answerable
from the allowed evidence universe do not establish competence at evaluating
environmental-review adequacy generally.

## Evidence access is part of the evaluation

A judge can assess supplied passages correctly while missing a decisive
qualification or contradiction outside its context. For example, dropping
“if mitigation M is implemented” from an evidence packet can make an
overstated answer appear supported.

Distinguish two proposed development experiments:

- Judge capability with complete, human-reviewed evidence supplied.
- End-to-end evaluation behavior with evidence supplied by the pipeline.

Track context or extraction failures separately from interpretation failures.
“Unsupported by these passages” and “no support found in this search” do not
establish absence of support throughout the corpus. More reasoning cannot
recover evidence the judge never receives.

## Human agreement and disagreement

Agreement with Kyle's locked labels measures agreement with that curator under
the stated rubric; it does not measure agreement among independent reviewers.
When a judge disagrees, distinguish evidence misunderstanding, rubric ambiguity,
reference incompleteness, and defensible differences in interpretation. Ask:
what evidence would persuade us that the judge is right?

Do not conceal ambiguity by repeatedly revising development prompts solely to
match every label. Keep disagreements and reasons visible. Preserve the
existing development/test boundary and report raw counts as well as rates;
a small development set cannot establish broad reliability. The current plan
requires human review of every locked-test prediction even if the judge passes
its provisional gate.

## Proposed controlled challenge set

Use reviewed development answers to create paired variants. Have a human verify
that each variant changes only the intended property and that its expected
judgment follows from the rubric before testing the judge.

| Change | Expected behavior |
| --- | --- |
| Paraphrase while preserving meaning | Both answer scores and citation metrics remain stable when cited IDs are unchanged. |
| Change formatting or add authoritative language without changing substance | Both answer scores remain stable. |
| Remove an essential qualification from the answer | Grounded correctness falls if the conclusion becomes overstated; adequacy may also fall for omission. |
| Replace a citation with a real but irrelevant passage | Grounded correctness falls; automatic final-citation precision may also fall. |
| Omit an essential part of the scoped answer while preserving supported factual claims | Adequacy falls; grounded correctness can remain high if the remaining conclusion stays qualified. |
| Substitute a different valid supporting argument | Grounded correctness stays high; check adequacy and citation-matching penalties for reference incompleteness. |
| Keep every correct citation but reverse the answer's conclusion | Citation scores stay unchanged; grounded correctness falls. |
| Keep citation IDs but substitute an explanation that avoids the question | Citation scores stay unchanged; adequacy falls. |

The question is whether the judge responds to changes in evidence and meaning
while remaining insensitive to presentation. Compare failure types by dimension
before considering a more complex judging architecture. These experiments
supplement, rather than replace, calibration on naturally occurring outputs.

## Revisit when writing Tasks 09 and 12

Use these notes to refine rubric examples and choose a bounded development
challenge set. Decide how to record ambiguous labels and valid alternate
answers, and how to separate judge errors from evidence-packet errors. Any
adopted protocol or gate changes belong in the future task contract and the
sprint evaluation boundary, not implicitly in this note.
