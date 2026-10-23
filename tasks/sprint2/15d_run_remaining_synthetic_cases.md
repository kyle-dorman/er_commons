# Task 15D — Remaining thirteen synthetic-question comparison

Status: complete with reviewed disagreements (2026-10-21).

## Goal and authorization

After reviewing three rounds on the original six, the user explicitly requested
continuation to the other thirteen. This is a new continuation decision; preserve
the earlier stopped gate and the observed critical error. Run both Luna and Haiku
on the remaining 234 synthetic candidates, three judgments each, without tuning.
This synthetic stage is distinct from the umbrella's saved-target 15D comparison.

## Inputs and outputs

Use the sealed Task15B publication and explicit unchanged Task15 C prompt/native
adapter. Select the complement of original six by case ID, exactly 13 questions
and 234 candidates; original 106 are not dispatched again. New results live in
`task_15/judge_synthetic_remaining13_20261021_v1` under the artifact root.
Preserve raw native logs, exact input/label sidecars, triples, every disagreement,
independent reviews, grouped analysis and completion-last seal/result pointer.

## Execution and analysis contract

Three native epochs × 234 × 2 = 1,404 logical judgments, up to 2,808 generation
attempts with one native transport retry. Sixteen connections per provider,
two concurrent tasks, 4,096 output tokens, 150 seconds per sample. No semantic
rerolls. Dated configured-price conservative estimate including retries is $9.56,
not a live billing guarantee or hard dollar cap. Native Inspect owns execution.

Freeze prompt/settings/input identities before dispatch. Report single-call
agreement, round1, any/all/majority of3, each expected-label class, critical
negatives and invalids. Compare with original-six results without rerunning them.
Keep tuning and audit partitions separate: four familiar-development audit
questions are now evaluated without intervening tuning; they are not unseen
generalization evidence. Expected labels remain reviewed proposals, not human gold.

## Plan, validation and review

Verify sealed loader, complement selection and unchanged native configuration;
independently inspect the bounded runner. Execute once, then verify unique
model/sample/epoch coverage. Review every mismatch/invalid result in bounded
independent groups; distinguish confirmed judge errors from label ambiguities.
Preserve exact rationales and report recurring mechanisms and variability.
Verify metrics, artifact hashes and original seals; run diff checks for docs.
No package changes are expected; existing adapter checks remain applicable.

## Non-goals

No prompt/label changes, selected-judge promotion, fresh target generation,
saved-target reevaluation, thirty-question test execution, original reserved
challenge access, MiniMax, commit or push. No outcome-driven tuning on audit.

## Outcome

The [result pointer](../../docs/specs/task15d_remaining_synthetic_result.json)
selects the sealed run and combined nineteen-question analysis. All 1,404 new
judgments are valid. Remaining-thirteen agreement is 691/702 Luna and 694/702
Haiku; any-of-three agreement is 232/234 for both, all-three 229/234 Luna and
231/234 Haiku. All 91 expected-positive candidates pass every round.

Combining the unchanged original-six records gives 2,040 valid observations on
340 candidates: Luna 1,008/1,020 agreement,338/340 any-of-three and334/340 all-three;
Haiku 1,006/1,020,336/340 and335/340 respectively. These are proposed-label
agreement, not human accuracy. Audit agreement is 241/243 Luna and 240/243 Haiku;
all audit mismatches concern C027, with no tuning or label changes afterward.

All 19 new disagreements (six distinct candidates) received lead and independent
semantic review. Haiku misses the C029 location substitution 3/3; Luna 1/3. Luna
accepts unconditional perpetual habitat obligations 2/3 and an absolute C027
conflict guarantee 2/3; the latter materiality judgment has moderate confidence.
Omitted intersection controls, omitted professional pre-permit verification and
an added guarantee after a complete lighting-measures list remain disputed policy
boundaries. Keep their exact interpretations in the external reviews; they are
not automatically confirmed judge errors. The lighting case specifically touches
the user's accepted incidental conclusion-only claim coverage gap.

`review.md` groups all mechanisms and `review.html` exposes every candidate and
all three rationales for both models. Separate Haiku/Luna semantic review receipts
and independent metric audit verify all 2,040 unique identities, exact input/config
bindings, aggregate/round/partition metrics and intact historical seals. No package
code changed; artifact validation and `git diff --check` passed. Execution took
about 4m54s; dated-price estimated cost $0.4977, not a billing receipt.

Next discuss these boundary cases and the confirmed errors before selecting or
changing a production judge. This result does not activate saved-target comparison,
test reevaluation, further prompt tuning or Task 16. Original labels, frozen
selection and publications remain unchanged; no commits or pushes.
