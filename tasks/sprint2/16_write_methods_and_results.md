# Task 16 — Short methods and results writeup

Status: provisional; after accepted Task 15 conclusion-judge revision and
reevaluation, and confirmed Task 14 findings. No writeup implementation active.

## Abstract and goal

Write a concise, mini-paper-style account of the dataset, methods and results,
shorter than a full research paper. Explain what was built, what was measured,
what worked and the limits of the evidence. Use existing tables/charts and a few
selected examples rather than reproducing task logs or prompt-development history.

## Inputs and outputs

Use accepted construction/publication records from Tasks 02–10, the final Task 11
condition, Task 12 reporting/calibration tables, original Task 13 results, Task 14's
selective cases, and the accepted [Task 15](15_revise_conclusion_judge.md) rules,
synthetic qualification, reevaluation and subsequent conclusion review. Present Luna and Haiku only; exclude the archived MiniMax side
experiment from figures, tables, comparisons and the experiment narrative.
Produce a short readable report with figure/table source links
and a compact reproducibility appendix. Choose final format/length at activation;
working target is roughly 1,500–2,500 words plus selected figures/tables.

## Planned contents

1. **Purpose and scope.** Environmental-review evidence-based answering, one
   source-project setting, intended uses and limits; supplied-evidence baseline
   and future search work clearly distinguished.
2. **Dataset construction.** Source documents → comment/response relationships →
   concerns/questions → evidence/reference authoring → review → release. Show
   counts and exclusions at each recoverable step, units, versions, human/model
   roles and source/annotation provenance. Explain transformations and selection
   effects. Mark missing historical measurements unknown rather than inventing them.
3. **Dataset composition and coverage.** Summarize topics, question/evidence types,
   text/table composition, evidence counts, cross-section/document use, context
   sizes, shared evidence, source-edition limits and 19/30 allocation. Use existing
   approved metadata; new semantic annotations require separate scope. Explain
   why the additional thirteen development cases are not independent held-out data.
4. **Methods.** Final prompt/input condition, both target models, three repeats,
   output controls and independent A/G/S/C interfaces. Describe automatic canonical
   citation/evidence matching as a dataset capability, alongside semantic judging.
   Report existing judge-label agreement and limitations without claiming new human
   calibration. A delivery receipt is not proof of cognitive reading; retrieval
   metrics are N/A for the supplied-evidence condition.
5. **Results.** Use Task 15's designated thirty-question reevaluation as the
   revised-condition results, alongside original Task 13 results. Explain the
   evaluator change, saved-answer comparison versus any fresh-generation arm,
   and which result pointer selects each condition. The thirty questions were
   exposed during diagnosis; the reevaluation is not a new untouched held-out test.
   Task 12's pooled 19-development-question views are a reporting preview, not
   the main results. Historical judge accuracy uses separate populations.
   Select figures showing both models, component/joint
   performance, observed at-least-once/every-time success, automatic citation
   measures, and the predeclared Luna associations with citation occurrences,
   distinct response units and distinct documents. Keep development, original
   Task 13 results and revised exposed-test reevaluation separate; show
   denominators and availability.
6. **Discussion and limits.** A few Task 14 and Task 15 cases, source/reference/judge limitations,
   repeat variability, exposure, accounting uncertainty and generalization limits.
   Discuss support-versus-qualification volumes and frozen grounding-failure
   fractions, supported useful qualifications, source contradictions, local
   citation scope, and reference-coverage failures. Distinguish actual claims
   from human interpretations and judge disagreement; preserve unresolved cases.
   Distinguish official response provenance from independent factual validity.
7. **Reproducibility.** Compact artifact/configuration/code identities, runtime,
   evaluation definitions, costs, source rights/access and replay instructions.

Task 11's [internal iteration findings](11_prompt_iteration_findings.md) are for
project learning and are explicitly excluded from the writeup's experiment story.
Mention the final method and development selection/exposure honestly, without a
prompt-by-prompt ablation section or a long negative-results appendix.

## Literature lessons to retain

| Source | Use in this writeup / limit |
| --- | --- |
| [LongDocURL](https://aclanthology.org/2025.acl-long.57.pdf), §§3–5 and appendices | Construction funnel, task/evidence distributions and explicit input conditions. Do not present supplied passages as unrestricted document search. |
| [BRIDGE](https://arxiv.org/html/2603.07931v1), §§2–4 | Evidence structure/modality breakdowns and evaluated N. Our conditions stay fixed across subgroups; do not select each subgroup's best prompt. Passage counts are not annotated reasoning hops. |
| [OpenThoughts](https://arxiv.org/html/2506.04178v1), §§4–6 | Versioned construction recipes, intermediate artifacts and reproducibility. Its training-data conclusions do not relax benchmark reference verification. Detailed intervention findings stay internal to Task 11. |
| [DocScope](https://arxiv.org/html/2605.08888v2), §§2/4 and Appendices B/H | Dataset datasheet, answer-versus-support distinction and annotation limitations. Do not transplant visual-region metrics or claim our small selected review estimates population error. |
| [RbtAct / RMR-75K](https://arxiv.org/html/2603.09723v1), §§3–5 | Atomic concern/response mapping, filtering effects and separate relevance/grounding/actionability dimensions. Keep official relationships separate from inferred semantic links; agency agreement or revision does not establish correctness. |

Source-specific claims must cite the exact paper/version. Construction reporting
should describe the implemented/released artifacts, not copy a paper's claimed
pipeline without checking it. Useful cautions from the literature discussion:
RbtAct's public mapping prompt permits response reuse despite the paper's stated
one-to-one rule; BRIDGE has unequal evaluated subsets and subgroup-best strategies.
These motivate accurate reporting, not a literature critique section in the short
writeup. Keep any such claim appropriately qualified and source-linked.

## Reference-conclusion cleanup reporting

[Task15F](15f_review_reference_conclusions.md) adds an evidence-only review of all49
reference conclusions. Its [result pointer](../../docs/specs/task15f_reference_conclusion_review_result.json)
selects a methods procedure note, per-case proposals/challenges and a conclusion
pitfalls appendix draft. Include the final adjudicated cleanup procedure and
representative pitfalls in methods/appendix. All49 were subsequently approved
and published in15M;15AA added prediction-informed materiality review, published
in [15AC](../../docs/specs/task15ac_reference_result.json). Distinguish these
stages and their approved changes from initial proposal counts. Disclose that
predictions were excluded from this batch but prior experiments motivated the
rubric, the lead had prior exposure, and original test references were re-curated.
Do not describe revised evaluation as untouched held-out testing.

The discussion must retain C's coverage gap: additional conclusion claims absent
from the reference and contradicting none of its required or optional meanings
may be supported or unsupported. C cannot establish their factual support without
evidence. Conclusion-only claims may also escape G's supporting-point/qualification
inputs and may not be caught by S. A C pass therefore does not certify all added
claims. The user accepted numbered reference-point judgments on 2026-10-22,
without a separate additions category. The implemented v6 judge subsequently
added internal-contradiction reasons; that does not close the unsupported-addition
gap. Also report the relevance gap: complete, supported answers can include
unrelated content and still pass. C does not certify relevance or concision, and
extra detail earns no credit. This limitation is accepted for the current
evaluation use; the project is not training models against this score.

Accepted changes require a new reference release, regenerated synthetic data,
judge retesting, generation-prompt alignment and fresh downstream execution.
Use the resulting designated versions, preserving earlier runs as historical.

## Validation, review and acceptance

Check every number against accepted machine-readable tables and every example
against its review record. Distinguish judged pass rates, judge-label agreement,
automatic citation overlap and human observations. Reuse approved aggregate split
metadata without reopening held-out content for construction tuning. Review for
clear methods, adequate source credit, concise presentation and unsupported claims.
Verify links, figures and `git diff --check`; render the chosen final format.

## Non-goals

A full-length paper, comprehensive literature review, new experiments or human
annotation, prompt-development narrative, changing frozen results, search-agent
implementation, or external publication/submission without authorization.

## Outcome

Planning only. Renumbered from Task 15 on 2026-10-21 at the user’s request.
Task 15 now owns C-judge repair and reevaluation; Task 16 owns the short
methods/results narrative and sprint closeout after that outcome is accepted.
Tasks 12–15 supply versioned evidence and illustrations. No new execution or
external publication is authorized by this renumbering.
