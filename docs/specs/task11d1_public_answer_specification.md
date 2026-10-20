# Public answer specification — Task 11D.1

This generic specification translates the accepted policies into respondent-facing
obligations. It contains no reference answers, case-specific required items or
judge predictions. Frozen judges and their input projections remain unchanged.
The V5 prompt is its concise executable form; V6 adds unrelated invented examples.

| Requirement | Respondent obligation | Policy owner |
| --- | --- | --- |
| Conclusion completeness | Answer every requested part in the conclusion itself, retaining material conditions; supporting fields cannot repair omissions | Adequacy C |
| Explanation | Explain the requested relationship, mechanism or calculation; list inputs only when a list is the requested answer | Adequacy answer formats and S |
| Complete list | Include all and only the requested substantive items; equivalent wording/grouping is allowed | Adequacy C |
| Joint support | Supporting premises jointly establish the actual conclusion and add explanatory substance | Adequacy S |
| Point validity | Nonblank text and globally unique nonblank point IDs; every answered point including optional context needs a supplied citation | Answer validator |
| Field links | applies_to contains existing answer point IDs or is empty; it never contains free-text scope descriptions | Answer validator |
| Local grounding | Each point and factual qualification is fully established by its own cited passages, including necessary conditions | Grounding rules |
| Cross-passage claim | Cite all sources required to establish the claim; other points' citations do not transfer | Grounding rules |
| Scope | Preserve scenario, time, location, quantities, uncertainty and negation; establish matched baselines before claiming change | Grounding and adequacy |
| Consistency | Conclusion and support must agree; material contradictions cannot be canceled by other correct facts | Adequacy S and source review |
| Abstention | Explicit insufficiency in conclusion, no other prose; a supported negative or conditional answer is substantive | No-answer rules |
| Relevant coverage | Include information material to the question, without requiring exhaustive reproduction of evidence | Grounding and adequacy |

Sources: [grounding](grounding_labeling_rules.md),
[adequacy](adequacy_labeling_rules.md), [no-answer](no_answer_labeling_rules.md).

## Evaluation boundary

Question, evidence and these general obligations are public. Reference answers,
per-case expectations, manual case diagnoses and judge decisions are evaluation-only.
The external alignment audit records generation/evaluation visibility mismatches
and possible question/reference ambiguities separately from true source errors.
Those diagnoses do not change frozen scores or enter generation requests.

Before dispatch, manual review distinguishes: factual contradiction, unsupported
relationship, missing material premise or condition, own-citation defect,
metadata/projection mismatch, reference ambiguity, and nonessential omitted detail.
A manual completeness defect requires a stated effect on interpretation of the
requested answer; reviewers must not require every source detail in the conclusion.
A mitigation detail can appear in support when the conclusion accurately summarizes
both the relevant risk and corrective condition. Merely naming generic mitigation
is insufficient only when it leaves a materially misleading conclusion. Judge
failures remain reported even when manual review diagnoses an interface limitation.
