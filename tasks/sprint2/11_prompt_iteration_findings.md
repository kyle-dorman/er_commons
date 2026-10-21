# Task 11 — Prompt iteration findings

Status: Complete (2026-10-20). Internal development analysis synthesized from
accepted task outcomes.
This is a reading guide to the experiments, not a new evaluation, revised score
publication or part of the short Task 16 methods/results writeup. The linked task
records and their result pointers own exact outputs, identities and evidence.

## Accepted configuration and evidence boundary

The final configuration retains V6b's explicit field contract and three unrelated
invented examples, adds the focused conclusion/support check from
[11D.12](11d12_conclusion_focus.md), and adds the shared document overview from
[11D.14](11d14_document_overview.md). Qualification rewrites and extra citation
checks were not retained. Both additions were explicitly accepted by the user
after reviewing their limitations; neither acceptance asserts universal improvement.
[11E](11e_freeze_development_baseline.md) freezes the exact configuration and its
all-19 development results.

The main controlled comparisons below use edition-neutral inputs and references,
unchanged passage bodies and citation IDs, Luna medium and Haiku adaptive-medium
reasoning, 12,288 target-output tokens and 4,096 judge-output tokens. Frozen Luna
A/G/C and Haiku S cores remain fixed. References and evaluator feedback never enter
generation. The summary/overview conditions change context for **both targets and
judges**, so unchanged judge cores do not mean identical evaluator inputs.

A records substantive-answer routing here; G grades individual support/qualification
points; S checks supporting sufficiency; C checks conclusion adequacy. Point G does
not establish conclusion citation completeness. “All checks” is the recorded
descriptive conjunction, not a substitute for the final reporting contract. A pass
under these judges is not a certificate of factual correctness.

## How the working control was established

| Intervention and hypothesis | Evidence and decision |
| --- | --- |
| Explicit field semantics and invented examples should make the public contract executable. | [11D.1](11d1_public_rubric_prompt_comparisons.md): rules-only V5b had 5/12 diagnostic passes; V6b with examples had 10/12; extra evidence-first procedure V7 had 6/12. All 36 corrected outputs were structurally valid. Retain V6b as a useful comparator; no arm met the original promotion rule. The observed score difference is not a general causal effect. |
| Lighter question wording might reduce C014 scope confusion without supplying search hints. | [11D.3](11d3_test_light_question_wording.md): original wording C 2/2 versus revised 0/2, with source/judge disputes in both. No demonstrated improvement; retain the published question. The detailed proposal had already been rejected for giving too many clues. |
| Alternative models might cover questions Luna missed. | [11D.4](11d4_compare_alternative_models.md): neither Haiku nor GLM added coverage beyond Luna's five of six. Haiku truncation and GLM format failures were separate from semantic failures. This did not establish that the uncovered question was defective. |
| A larger output allowance should remove Haiku's truncation. | [11D.5](11d5_raise_haiku_output_cap.md): increasing 4,096 to 12,288 removed both C014 output-limit failures; validity became 12/12, but C014 remained 0/2. The completed C014 outputs exceeded the old allowance. Strong evidence for resolving that completion constraint, not for resolving answer quality. |
| Neutral metadata and clearer instructions might resolve several observed failures together. | [11D.6](11d6_simplify_context_and_qualifications.md) prepared the new condition offline. The bundled V10 test in [11D.8](11d8_compare_v10_luna_haiku.md) produced Luna 5/12 and Haiku 3/12 all-checks passes. Multiple changed inputs prevent attributing the historical difference to an individual instruction. This motivated fresh nonadditive comparisons. |

Historical comparisons used different budgets and metadata conditions. They must
not be pooled with the neutral-input experiments as interchangeable baseline runs.

## Single-change comparisons and refinements

[11D.9](11d9_single_change_ablations.md) first ran a fresh neutral-input V6b baseline:
Luna 8/12 and Haiku 4/12 all-checks passes. Each separate arm then added only one
change to that baseline on predefined relevant questions, with two fresh repeats
per model/question. Later refinements reused saved controls; they did not rerun
controls or pair random seeds.

| Change, hypothesis and targeted evidence | Observed gain, regression and decision |
| --- | --- |
| **Qualification rewrite**, C041/C017/C037/C056: suppress unsupported or unrequested gaps while retaining material conditions. Inspect qualification G, relevance, useful omissions and movement across fields. | Haiku qualification G changed 19/24 → 18/20, but support G fell 37/38 → 34/38. Fewer caveats did not establish better answers. Unsupported different-storm wording appeared; electricity omissions also existed in baseline. The [11D.10](11d10_qualification_examples.md) whole-answer rule plus include/omit examples yielded Haiku qualification G 14/18, with animal/electricity gains but flooding regressions and unsupported certainty. Luna lost a useful battery exclusion in one answer. Reject the additions; do not infer that examples alone caused the changes because rule and examples changed together. |
| **Citation clause check**, C019/C014/C056: ensure each compound point owns all supporting citations. Inspect point G and exact clause-to-passage links. | Luna all-G answers improved 5/6 → 6/6; Haiku changed 1/6 → 0/6. The [11D.11](11d11_citation_example.md) replacement example left Haiku with seven failed G points, the same count as baseline, despite a higher point percentage. Missing name-mapping citations and unsupported review-to-model relationships persisted. New conclusion citation omissions and a storm-description error were outside point G. Reject the change: insufficient demonstrated mechanism-level benefit, not proof that a small instruction caused all observed regressions. The replacement also removed an existing illustration. |
| **Conclusion/support check**, C041/C017/C014: move necessary facts from supporting fields into the conclusion and retain their basis in support. Primary measures C/S plus direct text review. | Initial check: Luna C 3/6 → 5/6, but all-G answers 5/6 → 3/6; Haiku S 5/6 → 3/6. [11D.12](11d12_conclusion_focus.md) focused the check: Luna electricity C 0/2 → 1/2 → 2/2 across baseline/prior/focused conditions, with storage and excluded battery benefits visibly transferred. Overall Luna C stayed 5/6, S became 4/6; Haiku C stayed 2/6 and S recovered to 6/6. Haiku electricity still omitted storage from conclusions. Retain by explicit user acceptance as a useful focused addition with mixed effects, not a universal completeness fix. |
| **Generic project summary**, C041: remove uncertainty about whether appendix policies apply to the project. | [11D.9](11d9_single_change_ablations.md) found no change in answer-level component rates. [11D.13](11d13_provenance_caveat_review.md), an offline review, explained the mismatch: the summary described the project but did not bind supplied documents to it. Haiku provenance caveats already existed in baseline; they were not newly created by the conclusion check. No adoption of the generic summary. |
| **Document overview atop the accepted focused check**, C041: supply explicit document/project context. | [11D.14](11d14_document_overview.md): Haiku provenance caveats disappeared in both fresh repeats across all fields, versus 2/2 saved controls. Haiku C improved 0/2 → 1/2, but all-checks stayed 0/2; Luna all-checks changed 2/2 → 1/2. Text review supports the intended provenance improvement despite unrelated failures. Retain by user acceptance. The overview bundles identity, appendix inventory and review stage and reaches judges too; this does not isolate which element matters. |

## Consolidation and broader development check

[11D.15](11d15_fixed_six_consolidation.md) tested the accepted combination on the
fixed six, three times per model. Luna achieved 15/18 all-checks passes; Haiku 6/18.
Both models showed no C041 project-applicability doubts. Electricity storage reached
the conclusion in two of three repeats for each model. The combination remained
inconsistent, and Haiku retained unsupported caveats and citation-scope errors.
Comparison with the two-repeat baseline is descriptive: repeat counts differ and
the accepted combination changes both prompting and judge context.

[11E](11e_freeze_development_baseline.md) made no configuration change and evaluated
114 fresh answers. All were valid and fully evaluated. Luna all-checks was 29/57,
Haiku 6/57; original-six results were 14/18 and 3/18, while additional-13 results
were 15/39 and 3/39. The lower fresh-six scores demonstrate variation under the
same configuration, not a new prompt regression. The additional 13 had prior
judge-development exposure and are not independent held-out evidence.

Provenance doubts remained absent on animals. Luna included the electricity storage
assumption and battery exclusion in all three conclusions. However, both models
still left material habitat and lighting conditions in support without carrying
them into conclusions. Haiku also made a real wetland-table error; Luna invented
a park-stage inconsistency. Source contradictions, reference coverage disputes,
local-versus-global absence interpretation and overview/source edition mismatches
remain separate limitations. Preserve original scores alongside manual findings.

## What the evidence supports

The strongest operational finding is removal of the specific Haiku truncation
constraint. The strongest prompt-level leads are the visible electricity transfer
and disappearance of project-applicability doubts, with later observations supporting
persistence on those cases. Broader generalization remains weak. Qualification and
citation refinements did not deliver sufficient consistent benefit to retain.

Two or three unseeded repeats, adaptively exposed questions, changing point counts
and stochastic judges do not establish statistical significance or unique causes
for every output difference. Repeat IDs are identities, not paired random draws.
Changed answers were not separately rejudged under both old and new contexts to
isolate evaluator effects. Independent manual review explains plausible mechanisms
and disagreements; it does not retroactively relabel observations.

For future interpretation, compare the intended judge and failure mechanism first,
then inspect other fields for displaced errors or useful omissions. Report point
and answer denominators separately. Preserve rejected versions, negative results,
raw outputs and execution failures. Keep source/reference defects separate from
model defects. No new run, prompt revision or held-out access follows from this
analysis; the accepted 11E configuration and sealed artifacts remain unchanged.


## Closeout verification

A bounded independent fact audit checked numerical comparisons, point/answer
denominators, accepted/rejected decisions and causal qualifications against the
linked outcomes. No factual corrections were required. Local links and
`git diff --check` passed. This completes Task 11's internal analysis; no further
Task 11 work is pending. No new model calls or artifact changes were made.
