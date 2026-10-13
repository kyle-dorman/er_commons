# Task 09E.1 — Structured conclusion assessment result

The [bounded pilot](task09e1_luna_structured_conclusion_v1.md) is complete.
**Set the candidate aside:** it improved repeatability and explanation
inspectability, but conclusion agreement fell from 36/51 to 32/51. It fails the
prespecified improvement criterion. No default, claims configuration or labels
changed; no additional inference or expansion follows.

## What was actually new

We already had structured JSON, separate claim and conclusion judgments, source
grounding and necessary-premise instructions. The candidate added four headings
inside the existing top-level explanation: Interpretation, Evidence, Inference,
and Verdict basis, with concise fidelity reminders and a 250-word limit.
It did not add a decomposition call or change schemas, field order, evidence,
claim review, scoring or the disagreement gate. This is a structure-plus-guidance
bundle, not a formatting-only intervention or evidence about internal reasoning.

Both fresh arms used the same seventeen answers and 59 frozen original claim
judgments, with three repetitions. The existing visible-verdict reviewer was the
baseline. The prior conclusion-only run remains historical context, not a fresh
comparator. Original claim agreement on these selected cases remains 54/59
(91.5%), or 162/177 on the repeated denominator.

## Results against unchanged proposed labels

| Measure | Fresh baseline | Structured |
| --- | --- | --- |
| Conclusion agreement | **36/51 (70.6%)** | 32/51 (62.7%) |
| Claim-review agreement | 173/177 (97.7%) | **174/177 (98.3%)** |
| Claim corrections / damaging reversals versus frozen originals | 15 / 4 | 15 / 3 |
| Numeric scores returned | 33/51 (64.7%) | 33/51 (64.7%) |
| Correct numeric scores / all attempts | **23/51 (45.1%)** | 22/51 (43.1%) |
| Correct among returned numeric scores | **23/33 (69.7%)** | 22/33 (66.7%) |
| Same conclusion across all three repeats | 10/17 | **15/17** |
| Same final status and score across repeats | 11/17 | **16/17** |
| Unanimous claim-review slots across repeats | 55/59 | **59/59** |

All 102 calls validated; no retries or saved-response reuse. The paired conclusion
comparison has three proposal-aligned improvements and seven regressions.
Proposed conclusion false acceptances remain zero in both arms; false rejections
rise from 15 to 19. Claim-review errors change from one false acceptance and
three false rejections to three false acceptances and no false rejections.
The slightly higher aggregate claim agreement therefore hides a new concrete
citation-ownership regression.

The eleven original trouble answers fall from 24/33 to 20/33 conclusion agreement.
The six controls tie at 12/18. C041 accounts for 22/33 versus 17/33; C037 improves
4/6 to 6/6; C001 declines 1/3 to 0/3. C014, C019 and C056 remain 3/3 each.
Repetitions are not independent new answers, and stable withheld/wrong judgments
are not correct scores. This fresh baseline differs slightly from the preceding
run, which is why the comparison uses fresh arms.

All 51 candidate explanations include the four headings and meet the word limit:
94–179 words, median 152. This confirms format compliance, not source fidelity.

## What independent source review found

Two reviewers examined all 102 observations, changed claim reviews and the
selected controls. The detailed source records remain separate from headline
agreement; labels were not adjusted to rescue the result.

**Pet-policy scope dominates the lost agreement.** All seven changed C041
conclusion decisions concern the same attachment of “for the feral-cat
feeding-station ban” to an enforcement list. Sources establish MPOA monitoring
and fines for that ban, while leases and association enforcement appear in the
separate pet policy. The candidate more often attaches the final phrase to the
whole list and rejects the unsupported transfer. Those explanations can be
source-grounded under that reading. Some accepting explanations explicitly use
a narrower attachment. The headings expose the choice but do not settle the
ambiguity. Five net lost label matches are not proof of five new factual mistakes.

**A real citation-boundary error remains.** C001's structured assessment rejects
all three conclusions because their direct citation supplies methodology, even
while acknowledging relevant result sources elsewhere in the answer. That
imposes a restriction beyond the current full-answer conclusion interpretation.
The baseline does this twice. Conversely, C019's structured claim review accepts
P4 in all three repeats by borrowing S2 despite that point's own S3 citation.
This violates the unchanged point-owned evidence boundary; the baseline correctly
rejects all three. More structure did not make these two evidence rules consistent.

**A matching verdict can still have a faulty explanation.** All three C037 C01
candidate conclusions match proposals, versus one baseline. One candidate
assessment cleanly uses answer-cited S3 to support the full assertion. Two instead
describe the Appendix D assertion inside the conclusion as unsupported by its
direct citation but dispensable to the central answer. The evidence does support
that assertion in S3, but treating part of the conclusion as an unrelated
peripheral statement is not a clean rationale improvement.

**There is a concrete claim-review benefit.** Three baseline C041 reviews wrongly
reject the bounded assertion that the supplied measure specifies no separate
monitoring or penalty procedure. The candidate correctly accepts all three.
It also avoids one baseline C001 review that omits the original claim's
development-phase extension. These four between-arm improvements are offset by
the three new C019 citation errors. Fifteen proposal-aligned corrections to frozen
pet-policy claim predictions remain in both arms.

Keep the existing version. The useful learning is that explicit explanations
make interpretation and evidence-ownership errors inspectable; they do not
resolve the policy boundary or ambiguous labels. Further work should address
those concrete issues under a separately selected test rather than assume a
longer or more regular explanation improves the judge.

## Cost, caching, safeguards and limitations

| Arm | Cache reads / writes | Input / output tokens | Estimated cost | Median call time |
| --- | --- | --- | --- | --- |
| Baseline | 183,332 / 72,196 | 255,681 / 46,640 | $0.034193120 | 9.21 s |
| Structured | 198,853 / 69,068 | 268,074 / 75,449 | $0.048361830 | 14.59 s |

Total estimated API cost **$0.082554950**, about eight cents. Conservative
reservation was $0.488711025 against the $2 ceiling. All native payer fields
report `developer`; actual invoice/free-token treatment is unverified.
Cache reads cover 71.70% and 74.18% of input tokens. Separate cache keys and fresh
response IDs distinguish provider caching from saved-result reuse.

Both arms used Luna Responses, medium reasoning, 4,096 output allowance and four
concurrent samples per arm; they ran concurrently. Native audit passes all
102 request/configuration hashes, original-payload and common-schema checks,
exact-count/native-usage parity and decoded Inspect records. Transmitted counter
bodies are reconstructed from the tested adapter, not separately transport-recorded.
Quotation quality remains diagnostic. Final raw/decoded credential scans passed.

Validation: 348 focused tests and 12 external guards pass. Independent preflight
also checked all 34 arm/sample renders. `make fix` and `git diff --check` pass;
`make check` has 4,271 passed, one skipped and only the same three historical
Task 06G failures. No package changes, commits or pushes. Preservation confirms
all 816 files in the preceding experiment by existence/size and 87 consumed/seal
bindings by fresh hash, retaining the older sealed audit chain.

These are familiar, deliberately difficult development cases, heavily overlapping
C041, with only two proposed-negative conclusions and no live clean abstentions.
Agreement is against synthetic proposals, not adjudicated human truth. The result
does not qualify a judge, prove a general effect of structured explanations, or
justify relabeling. The [result pointer](task09e1_luna_structured_conclusion_result.json)
binds the native audit, independent source reviews, validation and final inventory.
