# Task 09E.1 — Frozen-claims conclusion results

The [authorized three-arm test](task09e1_luna_conclusion_blind_v1.md) is complete.
All 153 fresh calls validated. Hiding previous verdicts reduced claim-review
agreement and numeric coverage. Conclusion-only judging improved conclusion
agreement slightly and returned every numeric score, but retained original claim
errors and did not resolve the main pet-policy interpretation problem. No default
is promoted and no additional inference is scheduled.

## Matched results

Seventeen unchanged answers, 59 frozen actual claim judgments, three repetitions
per arm. Original claim accuracy on these selected cases was **54/59 (91.5%)**;
that is 162/177 on the repeated comparison denominator. This selected difficult
set is different from the previous full Dev6 population.

| Result | Prior verdicts visible | Prior verdicts hidden | Conclusion only |
| --- | --- | --- | --- |
| Claim-review agreement | **174/177 (98.3%)** | 168/177 (94.9%) | No new claim reviews; original 54/59 retained |
| Corrections / damaging reversals | 14 / 2 | 15 / 9 | Not applicable |
| Conclusion agreement | 35/51 (68.6%) | 36/51 (70.6%) | **39/51 (76.5%)** |
| Numeric scores returned | 36/51 (70.6%) | 29/51 (56.9%) | **51/51 (100%)** |
| Correct numeric scores / all attempts | 26/51 (51.0%) | 21/51 (41.2%) | **34/51 (66.7%)** |
| Correct among returned numeric scores | 26/36 (72.2%) | 21/29 (72.4%) | 34/51 (66.7%) |
| Same conclusion in all three repeats | 13/17 | 11/17 | 12/17 |
| Same final status and score in all repeats | 12/17 | 13/17 | 12/17 |

All accuracy figures mean agreement with unchanged proposed labels, not adjudicated
human truth. Corrections/reversals count repeated judgments, not distinct claims.
Review decisions were unanimous across three repeats for 56/59 visible claim slots
and 57/59 blind slots. Frozen originals were not rerun, so this does not measure
an improvement in original-judge repeatability. Stable unresolved statuses are
not stable correct scores.

The eleven originally inconsistent answers have **24/33 conclusion agreement in
every arm**. The six controls account for the difference: 11/18 visible, 12/18
blind, 15/18 conclusion-only. There is no demonstrated net conclusion-accuracy
gain on the original trouble set.

Claim-review gains on the original trouble set tie at 120/123, versus frozen
108/123. Visible preserves all 54/54 repeated control judgments; blind drops to
48/54. Of 15 visible unresolved scores, 13 involve only proposal-aligned
corrections, one only a wrong reversal and one both. The disagreement gate often
withholds a score because the reviewer improves on the original. That is existing
gate behavior, not a new correctness failure or authorization to override it.

## What source review found

Two independent reviewers examined all 153 conclusion observations, every claim
change and the selected controls. No labels changed.

**Conclusion evidence ownership is applied inconsistently.** C001's overall
below-threshold conclusion cites a methodology section directly, while results
appear in other sources cited in its supporting points. Visible rejects all three,
blind two, and conclusion-only none. C037's temporary-productivity-loss conclusion
has the same pattern: the decisive evidence is cited elsewhere in the answer;
rejections are two, two and one. These ten rejections impose a direct-conclusion-
citation-only rule. The existing full-answer conclusion contract supports the
proposed positive labels; its explicit own-citation restriction applies to point
reviews. Conclusion-only reduced this policy-application problem, rather than
adding a new grounding capability.

**Blind claim review borrows evidence it should not use.** In C001 it repairs a
point's buildout-only citation with development evidence from another point. In
C019 it supplies a missing conditional-approval letter from another point's
citations. Both happen in all three blind repetitions: six damaging reversals.
Visible review correctly retains those original unsupported judgments.

**The recurring conclusion scope remains ambiguous.** C041 supplies 33 observations
per arm and has exactly 22/33 conclusion agreement in each. Its recurring wording
attaches leases, association enforcement and MPOA fines to the feeding-station
ban, while the sources describe some mechanisms for a separate pet policy.
Literal rejections are defensible; accepting explanations often redistribute the
mechanisms between policies. Higher agreement with these proposed positive labels
is not automatically a semantic improvement. This is distinct from the simpler
pet-policy claim wording, where ordinary coordination supports the accepted
summary reading and explains the reviewer corrections.

All five damaging C041 claim reversals across reviewing arms reject the bounded
statement that the supplied measure specifies no separate monitoring or penalty
procedure. They demand an absence proof broader than the claim actually makes.
The original grading-versus-recovery distinction passes all six fresh reviews.
Procedural introductions and explicitly separated policy summaries remain supported.

The conclusion-only arm deliberately removes the second-review disagreement gate.
Its full numeric coverage is therefore expected, while its 34 correct scores
versus 26 visible scores combines a task change, genuine conclusion differences
and removal of withholding. It is not proof that claim review is unnecessary:
the visible reviewer substantially improves claim agreement. Do not promote blind
review or remove review as a default on this evidence alone.

## Cost, caching and validation

All arms used `gpt-6-luna` Responses, medium reasoning, the qualified cache layout
and 4,096 output allowance. Separate arm cache keys; no saved-result reuse, retries
or extra probes. The visible arm started first; the other two overlapped later,
with four concurrent samples per arm. Runtime is not a controlled speed benchmark.

| Arm | Native cache reads / writes | Input / output tokens | Estimated cost | Median call time |
| --- | --- | --- | --- | --- |
| Visible | 181,727 / 73,801 | 255,681 / 44,441 | $0.033278195 | 9.73 s |
| Blind | 182,860 / 71,960 | 254,973 / 46,532 | $0.034104900 | 10.40 s |
| Conclusion only | 166,272 / 66,477 | 232,902 / 23,086 | $0.021530645 | 6.39 s |

Total list-rate estimate **$0.088913740**, about nine cents; conservative reservation
was $0.721495500 against the $3 combined ceiling. Native payer fields report
`developer` on all calls; actual invoice/free-token treatment is unverified.
Cache reads cover roughly 71% of input tokens in each arm. Caching succeeded and
does not imply identical generated judgments.

Independent audit passes all 153 native results, distinct response IDs, request
hashes/projections, model settings, exact-count/native-usage parity and decoded
Inspect records. The counter body is reconstructed from the tested adapter rather
than separately transport-recorded. Optional missing/nonliteral quotations remain
diagnostic and never change semantic scores. Credential scans passed.

Validation: 348 focused tests and 12 external guards pass; independent reviewer
also reran 104 focused tests. `make fix` and `git diff --check` pass. `make check`
has 4,271 passed, one skipped and only the same three historical Task 06G failures.
No package defaults, labels, upstream artifacts, commits or pushes changed.
Preservation verifies 78 consumed/seal bindings by fresh hash, 3,276 Dev6 and 533
pilot files by existence/size, and the sealed chain retaining the earlier
50,869-file full audit. Fresh checks and inherited evidence remain distinguished.

This is a deliberately difficult, familiar development sample: 15 proposed-positive
and only two proposed-negative conclusions, no live clean-abstention examples,
and heavy C041 overlap. All six repeated proposed-negative conclusions were
rejected, but that tiny denominator cannot establish false-acceptance reliability.
There are 17 unique complete inputs; repetitions are not independent new answers.
No qualification, broad generalization or further run follows automatically.

The [result pointer](task09e1_luna_conclusion_blind_result.json) binds analysis,
independent source reviews, native audit, validation and completion inventory in
the fresh external namespace. The frozen contract remains unchanged.
