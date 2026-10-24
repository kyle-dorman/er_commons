# Task15AD — Final end-to-end benchmark run and closeout

Status: **complete and user-accepted, 2026-10-24**.
[Acceptance and handoff](../../docs/specs/task15ad_acceptance.json);
[sealed real-run result](../../docs/specs/task15ad_real_run_result.json).
49 questions ×2 models ×3 answer repeats produced294 answers and3331 grading
judgments. Estimated charges:$1.776348480 under the approved$40 new-run cap;
no unresolved liabilities. Independent execution, accounting and report replay
passed. All179 nonpassing answers plus12 predeclared passing controls were reviewed;
possible judge errors/ambiguities are recorded without changing grades.

S v9 remains [accepted with its C028 limitation](../../docs/specs/task15ad_s_v9_acceptance.json).
Task15AD is closed; its closeout commit is authorized. No more model calls or push.
Task16 remains separately activated.
The [C/RC prompt experiment is abandoned](../../docs/specs/task15ad_c_rc_experiment_disposition.md)
at the user's request. Accepted C v6/RC v1/S v9 and sealed results remain unchanged.
Implementation, cleanup, validation, acceptance and handoff are complete.

## Abstract and goal

Run the full benchmark workflow once after the support-coverage judge and citation
cleanup are accepted. Produce a final version-bound evaluation and reports, then
seek final-run acceptance and hand off to Task16. The parent Task15 revision
cycle is already closed; this is a separate follow-up. This is an evidence-only workflow;
agentic search and rebuilding raw extraction are outside scope.

## Dependencies and inputs

1. Task15Y: [accepted judge handoff](../../docs/specs/task15y_judge_handoff_v1.md)
   and [exact bindings](../../docs/specs/task15y_judge_handoff_v1.json), one call per
   required point, diagnostic rather than an added overall pass gate. Carry its
   accepted omission limitations. Real-answer projection, execution and C/G report
   joins are15AD implementation work;15Y did not execute those diagnostics.
2. Task15Z: [user-accepted](../../docs/specs/task15z_acceptance.json)
   [retrieval evidence sidecar](../../docs/specs/task15z_retrieval_mapping_result.json)
   and independent review. Required/optional meaning and approved citation bundles
   remain unchanged; explicitly retain15AC. The curator-only sidecar supports future
   retrieval development and does not add a metric or target input to this evidence-only run.
3. Current reference starting point: docs/specs/task15ac_reference_result.json.
   Resolve any15Z successor explicitly and pin its completion hash; do not select
   a directory simply because it is newest.
4. Accepted C rules/prompt/schema and Baylands overview; A/G/S contracts, target
   generation prompt, split and source provenance. Preserve all prior results.

## End-to-end plan

1. Freeze final questions, required/optional points, supporting points, citations,
   source packets and judge input mappings. Validate all49,19development/30test,
   exact anchors and source editions. Publish any accepted15Z successor first.
2. Rebuild affected prepared evidence and generation/judge inputs from that version.
   Verify question/citation changes propagate and that target inputs contain no
   reference conclusions or synthetic expectations. Reuse unchanged sealed sources.
3. Check target prompt, C/A/G/S and support-coverage prompt/schema compatibility;
   retain shared project context. Any substantive rule changes require discussion.
4. Audit C development synthetic compatibility against15AC; retain the accepted
   Luna/v6 judge and242 examples with unchanged reference inputs. Independently
   review the140 affected examples, repair stale expectations/metadata and author
   targeted replacements/controls only after plan approval. Quarantine ambiguous
   expectations rather than changing approved required/optional meaning.
   Author fresh S synthetics across19 development questions using one fixed set
   of approved supporting points and qualifications per question. Perturb only
   the coherent candidate conclusion paragraph, guided by required/optional
   reference points that remain hidden from S. Independently label against the
   visible fixed material, not reference completeness. Select explicit v9; retain
   old support-ablation corpora as historical artifacts. Preserve A/G/15Y
   qualifications subject to offline identity/projection checks.
5. Qualify refreshed C and S suites after independent label review and numerical
   budget approval. Use checkpoints and stop for review after the round. Inspect
   false failures/passes, invalid outputs and repeatability; do not automatically
   tune labels, prompts or models. Reopen another judge only for a demonstrated
   substantive incompatibility. Do not open reserved challenges.
6. Generate fresh Luna and Haiku answers for all49 questions and evaluate A/G/S/C
   plus the diagnostic support-coverage judge. Planning baseline:3 answer repeats
   per model (294answers), one Luna C judgment per answer,6144 C output tokens,
   concurrency16; explicitly select reasoning/output limits at activation. Do not
   silently promote the high-reasoning experiment. Old answers are comparisons only.
7. Rebuild reports with separate19/30results, model comparisons, repeat consistency,
   C model/computed agreement, support-covered/C-missing diagnostics, costs and
   latency. Preserve failed/unavailable slots and separate answer/judge repeats.
8. Review all failures plus a bounded, predeclared pass sample for missed errors,
   including contradiction false positives/negatives. Save unresolved interpretations;
   no post-result relabeling, silent retries or metric changes.
9. Audit native delivery, immutable inputs, accounting, exact roster and report
   replay; seal final publication and request acceptance. Close this follow-up
   when its work is complete. Task16 writing remains separately activated.

## Research, budget and execution gates

Inspect maintained runners and accepted15Y/15Z outcomes before implementation.
Use primary provider/tool documentation if an interface or price needs updating.
Explain the distinction between reference cleanup, judge reliability and answer
quality; final rerunning does not erase exposure from previous adaptive review.

Before paid activation, record numerical total budget, models, reasoning, repetitions,
output limits, concurrency and invalid/retry policy, with a bounded call estimate
including synthetic qualification and one diagnostic call per required point.
Carry prior liabilities and unknown counting fees forward if reusing an existing
budget; do not assume a fresh$40 allowance. Paid qualification is authorized only within the approved preflight plan;
final benchmark generation/evaluation remains separately gated. Stop for an unresolved substantive contract or budget issue,
not merely because scores fail to meet an expectation.

## Validation and acceptance

Appropriate make checks for implementation; full input/projection validation,
independent preflight and final audit, reproducible reports and completion-last
seals. Record every planned slot and exact retries separately. Final references,
synthetics, generation, judgments and reports must share explicit compatible
versions. All49 cases have curation exposure; do not claim a pristine held-out test.

No MiniMax, reserved challenges or agentic search. The final closeout commit is
user-authorized; push remains unauthorized. No automatic
extra tuning cycle. Report residual limitations and hand off to methods/results.

## Qualification checkpoint outcome

C:157 affected/reference-compatibility examples,471 valid judgments,464 label
matches. Numerical gates pass; retain Luna/v6 and the recorded interpretation
limitations. No changes to accepted reference meaning or historical labels.

S:304 paragraph-based examples authored and independently reviewed. The pilot
stopped after64 examples/192 valid judgments, with183 label matches. Unsupported
facts in the conclusion were treated as given premises or minor omissions on two
independent questions. C041/C056 and the remaining13 were not dispatched. One
biological-tracking expectation also needs adjudication; labels remain frozen.
Review the supporting-premise/conclusion-claim boundary before a new S version
or any continuation. A/G/15Y and real-answer integration remain later work.

The configured-rate usage estimate is$0.285779, distinct from the retained
$56.643960600 conservative reservation under the approved$70 cap. No commits or
pushes; all prior releases/results preserved. See the checkpoint for exact counts,
independent reviews, residual uncertainties and source bindings.

## S v7 retest outcome

The user authorized removing the premises-as-given wording, adding the claim
boundary rules and retesting the four completed pilot questions. The
[S v7 result](../../docs/specs/task15ad_s_retest_result.json) records192 valid
judgments,190 matches (98.96%), versus184/192 for v6 on the same adjudicated
expectations. All three unsupported-detail failures are fixed3/3. The biological
tracking inference remains disputed: false2/3 versus1/3 previously. Keep its
successor expected label true and preserve the original label/results separately.

Independent preflight and final audits cover frozen candidate payloads, native
requests, costs and lineage. Retest reserve$9.467094375 plus the entire prior
$56.643960600 reservation totals$66.111054975/$70. Configured cache-aware usage
estimate is$0.03985858 new/$0.325637345 cumulative, not an invoice. No retries or
invalid outputs. Stop for review; no further calls or production promotion.

## Authorized S v7 all19 continuation

Run only the240 reviewed examples from15 questions not yet evaluated with v7,
three repetitions each (720 fresh judgments). Combine them with the completed
64-example v7 retest for304 examples/912 judgments across19 development questions.
Keep all candidate text and expectations unchanged; the previously adjudicated
biological-recovery label remains true in the combined report. Preserve v6 and
v7 pilot publications. Production defaults and real-benchmark execution remain
separately gated.

Before dispatch, independently verify the exact roster, v7 prompt/settings,
source hashes and cumulative accounting. The original full reservation already
included never-dispatched v6 slots for these15 questions. A successor ledger may
replace only that audited, unattempted earmark with the v7 reservation for the
same slots. Retain every attempted or uncertain prior liability at its full bound,
including the v7 four-question retest. Do not reset the$70 cap or count the same
unattempted slots twice. Preserve the original budget records as historical
artifacts and record the substitution explicitly. Dispatch only if both the
combined$70 and existing component subcaps fit.

Use unchanged Haiku/medium/4096, concurrency16,5minute cache,3 repeats,
SDK retries0 and at most2 transport retries. No semantic retries or label tuning.
Keep operational/integrity guards and review each question's outcomes for a new
repeated clear semantic failure; the accepted biological inference limitation
alone does not reopen the prompt. Independently audit final receipts, lineage,
remaining mismatches and predetermined pass controls before review publication.

## S v7 continuation checkpoint

The [partial all19 result](../../docs/specs/task15ad_s_all19_result.json) records
four new questions/192 valid judgments/186 matches. Combined with the accepted
v7 pilot: eight questions,128 examples,384 valid judgments and376 matches.
Eleven questions/176 examples/528 judgments remain unattempted. Two independent
examples explicitly exempt unsupported qualifications because they are outside
the conclusion field, triggering the predeclared early-stop rule. Preserve the
false continuation gate; no further calls before review. C008's ambiguous road
antecedent retains its true label pending discussion. Biological recovery remains
true and is not the new stop trigger.

Exact native preflight and independent audit verified the budget before calls:
replace only the old$34.586364375 never-attempted earmark with$35.372064375 for
those same slots under v7. Retain$31.524690600 full prior attempted reservations.
Total$66.896754975/$70; S$54.096733125/$55. The full reservation remains held after
the stop. New configured-rate usage estimate$0.05022638, cumulative$0.375863725,
not invoices. No retries/errors or frozen-artifact changes; seven offline runner
tests and independent final semantic/accounting audits passed. No production
promotion, final benchmark execution, commit or push.

## S conclusion-only workflow revision

The user corrected the S evaluation boundary after the v7 continuation stop.
The [v8 contract](../../docs/specs/task15ad_s_conclusion_only_v8.md) replaces the
separate-qualification interpretation for future Task15AD work. S sees question
context, original candidate conclusion and supporting points only. Real-answer
projection must not merge qualifications or optional context into the conclusion;
generation and G keep their existing fields and responsibilities.

Author a successor304-example corpus from the reviewed all19 source. Remove the
separate qualifications field from every packet and naturally incorporate its
synthetic scope changes into the conclusion paragraph where present. Preserve
question/support text and all expectations, including the biological true
adjudication. Preserve the C008 road-antecedent ambiguity without silent repair.
Review every changed paragraph and the exact native input contract independently.
Version prompts, strict schemas, projections and evaluation identities together.

This is offline preparation only. Preserve the v6/v7 releases, tests and prior
scores as historical results. They do not establish v8 performance; do not mix
v7 judgments into v8 qualification. No additional budget claim or model calls are
authorized now. Retain the current$66.896754975 reservation and prior liabilities;
reconcile successor slots explicitly before any later paid retest authorization.

## S v8 offline preparation outcome

Implemented strict question/conclusion/support-only S inputs with explicit v8
selection across native judging and real-answer projection. The projection leaves
the original conclusion unchanged; it excludes separate qualifications and optional
context without merging them. Version-bound identities prevent historical/v8
result mixing. Generation schema and G stay unchanged.

Prepared304 successor examples:18 scope sentences moved into the conclusion,
286 conclusions unchanged, every question/support set unchanged,153true/151false.
Independent review read all38 scope variants and checked every packet and source
binding. Existing C008 road ambiguity is preserved; biological recovery remains
true. Two context-integration review findings were fixed and regression-tested.
77 focused tests passed; the preparation result binds the full make-check outcome.
No paid runner, new budget claim, model calls, commit or push. V8 is unmeasured.

## S v9 supporting-material workflow revision

The user clarified that qualifications should enter S as supporting material,
while the original conclusion remains its sole judgment target. The
[v9 contract](../../docs/specs/task15ad_s_support_material_v9.md) supersedes v8
for future Task15AD work. Keep qualifications separate in the input; never append
them to the real conclusion or treat them as extra claims to grade. They can
supply facts/conditions or reveal a material contradiction in the conclusion's
basis. They cannot silently narrow or rewrite the conclusion. Optional context
stays excluded; G and generation schema remain unchanged.

Preserve all304 v8 candidate texts and labels, including18 migrated scope
statements in the conclusions. Add an empty qualifications list to those revised
synthetic packets; do not restore former scope-test statements as supporting
premises for themselves. This corpus alone does not test nonempty qualifications.
Prepare separate invented offline contract-review fixtures for that boundary,
clearly outside all19 metrics and paid dispatch. Independently review the prompt,
projection, strict inputs, synthetic preservation and those fixtures before any
further calls. Preserve v6/v7/v8 and all results. No spending or new budget claims;
future retest must explicitly reconcile the existing$70 cap and prior liabilities.

## S v9 offline preparation outcome

Explicit v9 includes qualifications as supporting material and keeps the original
conclusion as its sole target. Strict four-field input and real-answer/native
projection preserve text and separation; optional context stays excluded. A
qualification may supply a basis, or reveal a defect material to the conclusion's
support, but is not separately graded as a conclusion claim and cannot silently
rewrite conclusion scope. V6/v7/v8 and generation/G behavior remain preserved.

The successor304 packets retain every v8 question/conclusion/support/label and add
empty qualification lists. All18 scope migrations remain in their conclusions;
biological recovery remains true and C008 ambiguity stays flagged. Five separate
invented offline fixtures were independently reviewed for nonempty qualification
roles. They are not all19 additions or performance measurements; the304 corpus
alone does not exercise nonempty qualifications. Independent code/input/semantic
review passed, including171 focused tests. The preparation result binds full
project checks. No model calls, new budget claims, commit or push; v9 is unmeasured.

## Fresh S conclusion-perturbation workflow

The user replaces the previous support-ablation approach with a fresh set:
[fixed-material conclusion perturbations](../../docs/specs/task15ad_s_conclusion_perturbations_v1.md).
Freeze full approved15AC support and qualifications per development question;
only conclusions vary. Author12 variants per case where defensible, targeting228
examples and684 judgments for a later all19 run. Six cases have genuine nonempty
qualifications. Reference R/O points guide authoring but never enter S requests.

New identities and freshly reviewed expectations prevent transfer of old synthetic
ambiguities/adjudications. Earlier results remain unchanged. Independently review
all labels, source/field isolation and fixed-material invariants, then render exact
requests offline and propose cumulative caps retaining prior attempted liabilities.
No provider calls or new budget claim during preparation.

## Fresh S preparation outcome

[Fresh corpus](../../docs/specs/task15ad_s_conclusion_perturbations_result.json):228
new paragraphs,114 true/114 false, across19 fixed-material questions. Independent
review of every label repaired four ambiguous negatives and two minor wordings;
no unresolved examples. Strict input/source invariants and mock native rendering
passed. No prompt changes or provider calls.

Propose36.717491250 new conservative reservation plus40.991453100 retained prior
attempted liabilities =77.708944350 total,64.908922500 S. Retire only the old
25.905301875 never-attempted earmark upon execution approval. Proposed caps80/65;
six-question checkpoint first (72 examples/216 judgments), human review before
remaining13 and afterall19. Budget is proposed, not claimed; no commit/push.

## Fresh six-question checkpoint outcome

User approved$80 total/$65 S caps and only the six-question checkpoint. Ran72
new conclusions across C014,C017,C019,C037,C041,C056 with fixed supporting points
and qualifications, unchanged v9, three repeats, concurrency16. All216 judgments
were valid and matched reviewed labels; all72 examples were unanimous. No provider
errors, retries, prompt changes or label changes. Independent execution/accounting
review passed. This is synthetic development agreement, not real-answer validation.

Configured-rate usage estimate:$0.070473200 new /$0.446336925 cumulative, not an
invoice. Conservative reservation remains$77.708944350 total/$64.908922500 S,
including all prior liabilities and the unattempted remaining earmark. Stop for
human review;13 questions/156 synthetics/468 judgments remain unattempted.

## Fresh all19 continuation outcome

User approved remaining13 under existing caps, then review stop. Ran156 additional
conclusions/468 judgments with unchanged v9 and exact frozen inputs.465/468 matched;
all468 valid, no retries/provider errors. Joined with the preserved216 checkpoint
judgments:681/684 matches,227/228 all-correct examples,228/228 unanimous examples.

Only C028-03 failed (true expectation, false in all three repeats). The conclusion
states a permit-stage acoustical verification requirement directly provided by P1.
The judge adds a broader protection/completeness implication; two explanations
acknowledge adequate support despite false output. Independent semantic review
recommends keeping true. No automatic adjudication, prompt changes or additional
calls. Preserve this limitation for human review before promotion/real predictions.

Existing all19 reservation was reused, not added or reset. New configured-rate
usage estimate0.12939370; cumulative0.575730625 (not invoices). Full historical
liabilities/reservation77.708944350 total/64.908922500 S remain retained.

## Accepted S and real-run preparation

User accepted S v9 with C028-03's completeness leakage and authorized offline
preparation of49 real questions plus grading. The preparation preserves current15AC
questions/references,15Z sidecar and prior releases; fresh target inputs retain212
sealed passages and propagate C034's question change. Prepared294 answer slots
and98 mocked native templates; no provider or counting calls.

New coverage projection/join helpers preserve singleton point isolation, answer
bindings, invalid/missing statuses and diagnostic-only reporting. Independent review
repaired C/G and projection-binding checks. A/G/C remain unchanged; S explicitlyv9.
One grading repeat, zero automatic retries. Proposed40 new pool/120 cumulative
total/90 cumulative S; generation full reserve10.757851125. Exact grading size is
answer-dependent; enforce request-by-request reservations and review stops.
See real-run plan and preparation result for source hashes, audits and validation.

## Real-run authorization and accounting recovery

The user approved a new$40 actual estimated spending cap for generation and
grading, then a review stop. This supersedes the earlier cumulative-cap proposal;
historical qualification reserves remain preserved and do not count as new charges.
Admission holds cover each in-flight request; verified usage settles the charge
and releases the unused hold. Unresolved usage retains its liability and stops
further admission. No provider token-count calls or automatic retries.

The initial17 requests all returned complete responses, but the accounting hook
rejected OpenAI's reported cache-write field on nine Luna responses. Preserved
original code, failed result records and stop marker. Recovered those nine answers
from saved native responses without calls, retained eight Haiku answers, and
independently proved277 slots were never admitted before their first dispatch.
An immutable reviewed clearance preserved the original stop. Independent pricing
reconciled inclusive OpenAI inputs into ordinary, cache-read and cache-write tokens.
Fourteen offline execution/recovery tests passed.

All294 generation requests subsequently completed, with$0.478738210 estimated
charges and no unresolved liabilities or repeated requests. Exact answer-bound
grading packets contain294 A,1699 G,294 S,294 C and750 diagnostic coverage slots
before A-first routing. Generation and grading artifacts live in the separate
external15ad_real_run_20261023_v10 publication; prior releases remain unchanged.

## Completed real-run review stop

The [result pointer](../../docs/specs/task15ad_real_run_result.json) selects the
sealed round and review handoff. All294 generation requests and3331 grading
requests completed once:294 A,1699 G,294 S,294 C,750 diagnostic coverage.
All judge outputs parsed; zero unavailable final slots. One answer fails an
automatic citation check and remains in the denominator. No paid retries or
provider token-count calls. Estimated charges1.776348480, unresolved liabilities0.

Recorded joint passes: Luna75/147 (development27/57,test48/90), Haiku40/147
(development17/57,test23/90). C model/computed agreement294/294. Diagnostic
coverage632/750, with74 covered points marked missing from conclusions; coverage
remains outside the overall gate. Answer-repeat consistency, stage costs and
latency are included in external supplements.

Independent semantic triage covers179 failures and12 predeclared pass controls.
Review hypotheses include overreading excerpt-scoped qualifications, rejecting
ordinary inferences, and treating attributed source differences as candidate
contradictions. Many failures retain independent required-point omissions or
point-owned citation defects. No corrections, reruns or new labels were applied.
This review is not new gold adjudication or exhaustive validation of all passing
points. All49 references retain curation exposure.

Independent audits verify3625 exact native requests, source/settings bindings,
zero duplicate dispatch, usage-based accounting, full report replay, and exact
interim/final review selection. Preserved14 bound repository-module snapshots and
original failed-attempt records. No commit/push. Request acceptance before closure
or separately activating Task16.

## RC naming and future-run integration

User requested a durable name for15Y and its inclusion in every future run,
independent of the decision chain. Use **RC — Required-point Coverage**; retain
its accepted prompt identity and calibration unchanged. This authorizes offline
naming/integration/report work, not more model calls or commits.

Bounded plan: introduce a current-run preparation helper that pairs the maintained
A/G/S/C plan (explicit accepted C v6 and S v9) with a mandatory separate RC plan.
Retain all required-point slots, including skipped/unavailable status; diagnostic
completeness never changes the A/G/S/C overall gate. Compare RC with C per required
point on the same candidate/repeat/reference, keeping C satisfied, missing and
contradicted separate. Publish the full cross-table and inspectable differences
from saved15AD outputs in a new sibling artifact, preserving the sealed round.

Reuse the existing projection/parser/join and native executor boundary instead of
adding a dispatcher or changing historical plan items. The maintainer contracts
and `build_report` implementation show why: legacy item completeness participates
in decision routing. A separate diagnostic plan preserves that invariant. Verify
binding rejection, explicit non-decisions, contradiction distinctions, and unchanged
joint results; independently review the implementation and offline comparison.

RC integration is implemented in `current_judges`: accepted C v6/S v9 decisions
and mandatory separate RC plans/queues, with explicit diagnostic completeness.
Old defaults/runners remain frozen. Independent review and18 focused tests passed;
full `make fix`/`make check`:4625 passed,1 skipped. Saved replay reproduces all294
decision reports unchanged and all750 C/RC cells. The
[offline comparison](../../docs/specs/task15ad_rc_comparison_result.json) records
555 covered/satisfied,74 covered/missing,3 covered/contradicted,39 not-covered/satisfied,
77 not-covered/missing and2 not-covered/contradicted; no unavailable results.
All116 layer differences are inspectable and do not imply116 judge errors.
The original run remains sealed; no model calls, commits or pushes.

## Offline C/RC paired regression preparation

User authorized proposed prompt changes, a small paired regression from observed
real cases, independent label review and a budget proposal before calls. The
[plan](../../docs/specs/task15ad_c_rc_paired_regression_plan_v1.md) adds a general
assertion/condition/unit comparison procedure to separate candidate prompts.
No accepted judge, schema, required/optional meaning or sealed result changed.

The [prepared result](../../docs/specs/task15ad_c_rc_paired_regression_result.json)
contains eight pairs per judge: six semantic flips and two invariant controls.
There are thirty-two pair slots, thirty distinct payloads, drawn from six exposed
real questions. Independent review agreed with all expectations after clarifying
City Engineer approval in four C049 controls; C007 ambiguity is excluded. These
authored controls do not establish pristine held-out accuracy or adjudicate all
original answers. Record both pair-weighted and unique-payload results.

Proposed old/candidate comparison: 192 Luna medium calls, three repeats,
concurrency sixteen, 24-hour caching, zero retries. Offline reservation envelope
$0.790965; proposed fresh cap $3. Exact native delivery/cost preflight is still
required before dispatch. Validation checked schemas, canonical references,
payload isolation, pair invariants, aggregation and review hashes. Documentation
diff check passed. No calls made; stop for user prompt/budget review.

User subsequently approved the proposed C/RC prompts and fresh $3 cap for the
192-call comparison. Execute one round after native preflight and independent
execution review, then stop for user review. No promotion, real-run regrading,
commit or push is authorized. Preserve the sealed preparation and record execution
in a separate sibling artifact with actual estimated charges and liabilities.

The approved comparison completed192/192 calls, no errors/retries, for estimated
actual charges $0.047775430/$3 with zero unresolved liabilities. Native preflight
uses the maintained provider schema normalization, matching successful prior C/RC
wire schemas while retaining strict local validators; original drafts and earlier
mock attempts remain preserved. Independent execution audit reconciled all native
requests, outputs and ledger receipts. No production judge defaults changed.

C binary accuracy moved46/48 to47/48; RC45/48 to47/48. Remaining candidate binary
errors are one staging-only C049 pass and one features-only C045 RC coverage pass,
each occurring in one of three repeats. C binary repeat agreement remains15/16;
RC16/16 becomes15/16 because a formerly consistently wrong case now varies.
Optional C addressed/not-addressed discrepancies remain diagnostic interpretation
questions, with no overall verdict effect and no post-run expectation changes.
This small exposed suite suggests modest improvement, not a reliable resolution
of judge noise. Full evidence is in the result pointer. Stop for user review;
no promotion, further calls, regrading, commits or pushes.

## Real-answer disagreement comparison proposal

User requested testing the new C/RC prompts on the actual real answers where the
judges disagreed, with a budget proposal before any calls. The
[offline plan](../../docs/specs/task15ad_c_rc_real_disagreement_plan_v1.md) selects
116 point disagreements across87 original answers and32 questions. Reuse exact
saved judge packets:87 full C inputs and116 single-point RC inputs. No answer,
reference or expected meaning is edited; original verdicts are not gold labels.

Propose accepted/candidate prompts ×3 repeats:1,218 calls, fresh$6 cap, conservative
offline reservation$4.963051125. Prior observed mean costs extrapolate to about$0.28,
not a guaranteed charge. Candidate-only609 calls is a cheaper but weaker alternative;
the primary proposal uses matched reruns to measure ordinary judge variability.
No calls made. Await budget approval; preserve all sealed runs and accepted defaults.

User approved the fresh $6 cap for both prompts on the unchanged real disagreements,
three repeats (1,218 calls). Execute after native preflight and independent review,
track actual estimated charges and pending liabilities, and stop for review after
the round. No prompt promotion, commits or pushes.

The real-answer comparison completed1,218/1,218 calls without execution errors or
retries. Estimated actual cost:$0.554979370/$6; pending/unknown liabilities:$0.
All native requests, outputs and ledger receipts independently reconciled; exact
original inputs and approved prompt bindings were retained. No gold labels were
assigned and no historical grades or accepted judge defaults changed.

Across116 selected points, accepted→candidate unanimous C statuses:92→94;
unanimous RC labels:98→87. Across87 answers, unanimous C overall verdicts:68→75.
Majority C/RC disagreements:101→96, which does not establish greater accuracy.
Ten selected C majorities and ten RC majorities changed; twelve overall C
majorities changed. Some original differences are genuine conclusion/support
differences, while familiar loading/designation errors persist. This is mixed
evidence, with worse observed RC repeat stability, not a demonstrated broad fix.

The audit found zero C aggregation inconsistencies. It also logged99 nonliteral
quotes out of4,184 (50 accepted/49 candidate), across69 C responses; punctuation,
paraphrase and omitted spans can trigger this diagnostic, so it is not automatically
a semantic-error count. Strict schema parsing and quote fidelity are separate checks.
Full results, changed-case text/reasons and independent reviews are preserved in
the result pointer. Stop for user review; no more calls, commits or pushes.

## C/RC experiment disposition

On 2026-10-24 the user requested backing out the candidate C/RC prompt work and
ending further pursuit. The candidates never entered the maintained judge path;
no runtime rollback is necessary. Retain accepted C v6/RC v1, accepted S v9,
mandatory diagnostic RC integration, and the original full-run grades. Experimental
plans/results remain historical evidence only; their unused budgets are not active.
No further implementation or model calls are required by this task. Final user
acceptance and administrative closeout remain; no commit or push is authorized.

## Retained-code cleanup

User requested a clean, simple, readable and maintainable retained implementation.
Reviewed the Task15AD S dispatch/projection and RC integration changes. Kept the
cleanup to three modules: explicit S packet/version construction replaces nested
conditional dictionary expansions; RC reporting uses named intermediate values
and a straightforward comparison branch; coverage joins share binding-field names,
compute the answer hash once and isolate nullable witness-grounding handling.
No new framework or generalized registry was introduced. Historical S v7/v8 remain
because saved runs depend on their contracts; literal prompts, schemas, defaults,
grading boundaries and RC's diagnostic-only role are unchanged.

Independent code review found no blockers. `make fix` and `make check` passed:
4,625 tests passed,1 skipped, with existing dependency deprecation warnings. Twelve
S projection combinations retain identical plans, sample IDs and payload hashes.
Before/after offline replay exactly reproduces all294 saved reports and750 RC
projections/join rows; prompt/schema and full report hashes match. No model calls,
commits or pushes. Exact cleanup diffs, review and validation evidence are in the
[cleanup result](../../docs/specs/task15ad_code_cleanup_result.json).

## Outcome

User accepted and closed Task15AD on 2026-10-24, authorizing a local commit.
The delivered evaluation contains294 fresh answers over49 questions,3,331 grades
including750 RC diagnostics, sealed reviews and reproducible reports. Retain
C v6, S v9 and RC v1 with A/G unchanged. RC is mandatory diagnostic coverage in
future full runs, outside the decision chain. The attempted C/RC prompt changes
are abandoned and preserved as historical evidence; no grades were replaced.

The key limitation is judge noise: improved agreement or repeat stability alone
does not establish semantic correctness. Keep accepted S/C/RC limitations and
all49 questions' curation exposure explicit. Cleanup preserves exact reports and
contracts; independent review and4,625 tests passed (1 skipped).

Handoff: [Task16](16_write_methods_and_results.md) should use the accepted full-run
pointer and separate19/30 reporting, with historical runs clearly distinguished.
Task16 writing, new model calls, further tuning and push are not authorized by
this closeout. Earlier approval restrictions below/above are historical records
of their respective phases, superseded only by this explicit acceptance.
