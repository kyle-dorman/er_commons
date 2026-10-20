# Task 11D.2 answer review contract

Status: prospective clarification for offline Task 11D.2; no candidate promotion,
live evaluation authorization, or replacement of historical judgments.

## Retained public instructions

Retain [V6b](../prompts/task11d1_luna_v6b.md) unchanged, including its explicit
field semantics and unrelated invented examples. SHA256:
`8f947e68e67b94318aed40c46e3b23fc39fc9a49d4b3904dd88e510edb46080f`.
The [public answer specification](task11d1_public_answer_specification.md)
continues to require a complete conclusion, explanatory support, claim-local
citations, preserved scope and explicit abstention when appropriate.

These generic obligations are respondent-facing. The evaluator-only findings
below, approved references, per-case requirements and judge explanations must
not enter generation requests. This document is not a generation prompt.

## What each evaluation establishes

| Check | Evidence and scope | What a pass does not establish |
| --- | --- | --- |
| Frozen G | Each supporting point and factual qualification against its own cited passages, jointly | Conclusion factuality or question completeness |
| Frozen S | Whether stated supporting premises and applicable qualifications establish the actual conclusion | Source factuality or agreement with the approved answer |
| Frozen C | Conclusion compared with the approved reference | Independent verification of every conclusion assertion against sources |
| Manual conclusion-source review | Every material conclusion assertion against its own cited passages, jointly | A replacement G/C score or permission to revise the reference |

The [grounding rules](grounding_labeling_rules.md) exclude the conclusion as a
separate G item. The [adequacy rules](adequacy_labeling_rules.md) separate source
truth, logical sufficiency and reference agreement. Preserve those boundaries:
an all-G/S/C diagnostic pass can coexist with a manual conclusion-source defect.
Evidence omitted by a frozen input projection must be reported as a visibility
limitation, not silently supplied to that judge after the fact.

## Separate manual review record

For each planned candidate, retain run, case, candidate, repeat and attempt IDs,
candidate hash, packet hash, reviewed conclusion point ID and review-contract
version (`task11d2.answer_review.v1`). Bind a manual finding to the exact claim,
its owned citation IDs, source location and reviewer rationale. Never transfer a
judgment between repeats or repair a candidate by combining their outputs.

Use `pass`, `material_defect`, `unresolved`, or `not_evaluated` for the manual
conclusion-source result. Report planned candidate count, reviewed count and each
status count separately. Use reviewed substantive conclusions as the explicit
pass/defect/unresolved denominator; show abstentions and unavailable or invalid
outputs outside that denominator without dropping them from planned coverage.
For a future complete fixed-six pair, planned coverage is twelve candidate
observations, not twelve independent questions. Do not fold these reviews into
G's point denominator. Record any claim-level counts separately.

Whole-answer manual review also checks stated-premise logic and completeness.
Distinguish factual contradiction, unsupported relationship, missing material
premise or condition, own-citation defect, metadata/projection mismatch,
reference ambiguity and nonessential detail. A fact present in the source does
not repair a necessary premise absent from the candidate's supporting fields.
Preserve blind review and any subsequent disagreement diagnosis separately.

## Materiality and acceptance

For an omission to be a material defect, identify the requested answer or actual
candidate claim, the missing condition or relationship, and how its absence
changes interpretation. Do not require exhaustive source coverage or identical
wording across fields. A relevant mitigation detail is not automatically a
mandatory conclusion item. A qualified summary may leave its precise mechanics
in support if the conclusion remains accurate; a materially misleading summary
cannot be repaired by an unrelated caveat elsewhere.

Report frozen diagnostic results, manual results and selection status separately.
For any future authorized comparison, predeclare the selection gate before
dispatch. Retaining 11D.1's gate requires complete valid substantive coverage in
both repeats, all applicable frozen G/S/C passing, and no unresolved material
manual source, logic or completeness defect. A manual disagreement never changes
the frozen score. This offline task selects no candidate and starts no 11E work.

## Evaluator-only sensitivity note: C037

The historical V6b repeat-2 manual review marked omitted corrective timing as a
material defect. Preserve that record unchanged. Its conclusion correctly says
that greater restored acreage does not establish avoidance of temporary
functional loss; its support describes a possible phasing gap requiring
additional mitigation. The supplied two-year grading requirement, with a City
alternative, is relevant context but does not itself guarantee no temporary
functional loss.

Under the explicit materiality test, absence of that precise requirement alone
does not establish a defect. A claim that the extended gap is an unavoidable
post-mitigation outcome, or that no corrective timing requirement exists, would
have a concrete misleading effect. Report this as sensitivity of the historical
manual classification to a clarified standard, not a retrospective pass,
rescoring, or V6b promotion. Do not add the two-year detail to frozen C's required
answer merely because it appears in source evidence.

## Learning and version boundaries

The [11D.1 outcome](../../tasks/sprint2/11d1_public_rubric_prompt_comparisons.md)
records V5b rules-only at 5/12 frozen diagnostic passes, V6b with invented examples
at 10/12 (5/6 in each repeat), and V7 with an added verification procedure at
6/12. Examples had the strongest observed pattern; more process instructions
regressed on this diagnostic. These are six adaptively exposed tuning cases,
not causal evidence, independent twelve-case samples or benchmark estimates.
V6b was not qualified: frozen failures and manual findings remain.

This clarification adds separate reporting, not a new judge or reference.
Grounding/no-answer semantic changes and grounding interface changes require
new versions under their locked contracts; Task 11 does not authorize changes
to frozen policies. A future metadata projection or changed-question condition
must have fresh identities and a separately bounded plan. The exact question
proposal follows the approval boundary in
[Task 11D.2](../../tasks/sprint2/11d2_resolve_evaluation_contract.md).
