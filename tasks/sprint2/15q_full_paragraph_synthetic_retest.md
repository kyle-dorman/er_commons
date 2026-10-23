# Task15Q — Full paragraph synthetic regeneration and judge retest

Status: complete; user accepted Luna with v6 (2026-10-22).

## Abstract and authorization

The user accepted the paragraph/internal-contradiction direction and explicitly
approved all four proposed steps: regenerate a full suite on 19 development
questions, cover positive and negative families, independently review/freeze labels,
then run Luna and Haiku three rounds each at concurrency16/model. The user
increased the cumulative spending cap from $20 to $30. Prior conservative liability
is $17.008511775 (sealed Task15P), leaving $12.991488225. Preserve every prior run.

## Inputs, outputs and scope

Use human-approved Task15M R/O references and unchanged v6 judge rules, prompt,
shared Baylands overview, schema and validation. Plain candidate paragraphs only;
no candidate IDs, pair inventories, or reason-quality scoring/review. Author a new
full suite, aiming around 20 cases per question (roughly 380), allowing useful
variation rather than forcing inapplicable families. Cover complete answers,
meaning-preserving changes, optional details/qualifications, compatible additions,
required omissions and deficient why/how explanations, reference contradictions,
internal contradictions in both orders, and combined defects. Include positive
controls for compatible different-scope statements and omission of optional facts.

All candidates are newly authored rather than merely replaying the earlier 65
negatives. Freeze agent-proposed overall labels and source/provenance metadata
before calls. Judge reasons are unscored working explanations; no exhaustive
expected list or point vector is required. Report model-final and independently
computed verdict agreement, positive/negative errors, structural validity,
consistency, repeatability, cost and latency. Save sealed data and run publications.

## Plan and learning checkpoint

1. Split authoring across bounded independent question groups; read current rules
   and transformations v4 plus the unchanged approved references. New examples
   should be clear and meaningful, not trivially near-duplicates or disputed labels.
2. Cross-review every candidate and overall label before publication; resolve or
   exclude ambiguity before inference. Verify fresh prose, exact question/reference
   bytes, development-only membership, family/sign coverage and no metadata leakage.
3. Reuse the maintained native Inspect v6 runtime and previously audited execution
   controls, adjusting population and budget only. Review the bounded runner and
   accounting independently. Freeze inputs and validate offline before paid calls.
4. Execute each planned slot once, three rounds/model, medium reasoning, up to16
   concurrent/model, no semantic retries. Reserve before chunks and carry previous
   liability; uncertain attempts remain charged. Stop before exceeding $30.
5. Review every overall/structural/consistency failure, preserving disagreements
   without changing labels. Do not grade internal reason lists or point vectors.
   Audit counts/costs and publish completion-last; report strengths and limitations.

## Validation and acceptance

Use existing source/schema tests and meaningful offline execution/accounting tests.
No runtime changes are planned; prior 4527-test check remains applicable unless code
changes. Run targeted regression checks and git diff --check. Independent author
review and execution/result audit must pass. Full planned population and all errors
remain in reported denominators. Use prior results for background only: new text
prevents a clean paired accuracy comparison or causal improvement claim.

## Non-goals

No reference/question edits, A/G/S or production-default changes, MiniMax, reserved
challenge access, target-answer generation, commits or pushes. Task16 and downstream
whole-answer reruns retain their separate gates. This familiar development synthetic
suite is not held-out benchmark qualification.

## Frozen execution population

The reviewed publication contains 382 fresh paragraph candidates across all 19
questions: 154 expected passes and 228 failures, producing 2292 planned judgments.
All eight transformation families are represented. Three independent cross-reviews
bound every author file; pre-inference fixes clarified a solar-accounting omission,
a three-year fencing antecedent, and for-sale versus owner-occupied housing. No
reference text changed. The [synthetic result](../../docs/specs/task15q_structured_synthetic_result.json)
selects the sealed publication and provenance. Runtime regression checks passed139
focused tests; 13 offline execution/accounting tests passed. The unchanged runtime
retains Task15P's full4527-test validation. Independent dataset and runner audits
passed before dispatch; the largest individual question reservation is$3.797028.

## Outcome

All four authorized steps are complete. The [sealed judging result](../../docs/specs/task15q_structured_judging_result.json)
selects the full report, raw receipts, independent audit and exhaustive exception
review. All 2292 calls completed without retries or semantic replacement calls.

Luna agreed on 1143/1146 (99.74%); Haiku agreed on 1145/1146 (99.91%), with its one
invalid output retained in the denominator. Model-final and computed verdicts
coincided on every structurally valid output. No valid output falsely accepted an
expected failure. Three Luna disagreements are repeats of C006-Q-EX-01: whether
'certified mechanic checking every machine before operation' conveys the required
finding of proper running condition. This remains a disputed equivalence boundary,
not a confirmed clear judge mistake. Haiku C036-Q-CT-01 round1 omitted O1–O6 and is
structurally invalid despite its correct raw false Boolean. All four exceptions
were reviewed; labels remained frozen. Internal contradiction explanations were
not separately reviewed or scored, and point-vector accuracy was not computed.

Configured run cost estimate $1.35220864; conservative new liability $8.53121310,
cumulative $25.539724875 of the user-authorized $30 cap, leaving $4.460275125.
Runtime 10m45s; median model-call times 6.14s Luna and 5.22s Haiku. Source identities,
all planned slots, 38 native logs, positive/negative and repeat metrics, exceptions,
and every budget reconciliation passed independent audit. Publication inventory
and final diff checks passed. No runtime edits, commits, pushes or default promotion.

The broad positive/negative suite supports the v6 format on these familiar cases;
new candidates preclude a paired claim of improvement over previous versions.
Shared source questions and repeated variants limit independence. The remaining
C006 interpretation can be discussed without silently correcting the result.
Task15M downstream steps and Task16 still require their previously recorded gates.

## User acceptance and next step

The user accepted the results as good enough and explicitly selected continued
use of Luna with the new rules and v6 prompt. Retain the earlier single-judgment
operating choice; the three-round runs were qualification diagnostics, not a new
voting requirement. Use paragraph input, numbered reference points and
`internal_contradictions` reasons, with the established structural/consistency
checks. Remaining C006 equivalence uncertainty stays documented; no label revision
or additional tuning is required by this acceptance.

This completes step6 of the Task15M nine-step plan. Step7 is next: align the
answer-generation prompt with the accepted conclusion requirements and present the
concrete revision for user review before fresh generation. Preserve original
frozen configurations/results; subsequent evaluation must explicitly select Luna
and v6. Step8 still requires its separate run population/model/repetition/budget
agreement, and step9 updates reports before separately activated Task16 writing.
