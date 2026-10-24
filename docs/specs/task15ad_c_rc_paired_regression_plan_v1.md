# C and RC paired regression proposal

Status: historical executed plan; candidate changes subsequently
[abandoned by the user](task15ad_c_rc_experiment_disposition.md).
Accepted C v6 and RC v1 remain selected. Do not resume this plan.

## Question and prompt change

Can an explicit meaning-comparison procedure reduce both missed material
differences and failures caused by wording or scenario differences?

Add the following block before the output instructions of each accepted prompt.
Keep all existing rules, input boundaries, output schemas and aggregation intact:

> Meaning-comparison procedure:
> - Identify the material assertions in each required point and locate the candidate
>   language conveying each assertion. Accept equivalent wording and ordinary
>   linguistic implications that require no new substantive premise. A matching
>   topic or outcome alone does not supply a missing relationship or method.
> - Compare who or what the claim concerns, the relationship asserted, negation,
>   scope, conditions, timing, and quantities with their units. Apply exact unit
>   conversions when needed. Preserve conjunctions and minimum/maximum bounds.
> - Align scenarios and conditions before finding a conflict. A baseline hazard
>   and an explicitly conditional mitigated outcome may both hold; incompatible
>   claims under the same conditions remain a conflict. Do not invent a condition
>   to reconcile them.
> - Before a positive judgment, check that every material assertion is conveyed
>   and no relevant unresolved contradiction remains. Before a negative judgment,
>   identify the specific missing or incompatible meaning, rather than an absent
>   phrase. Use the existing brief reason field; do not output a separate analysis.

These are candidate instructions, not new required/optional meanings. No question
IDs or case-specific answers enter the prompts. C still judges only the conclusion;
RC still sees only one required point and candidate supporting points, with empty
support IDs on false. RC stays diagnostic and separate from grounding and joint pass.

## Paired cases

Author eight pairs for each judge: sixteen C packets and sixteen RC packets.
The same six source questions motivate both sets, but inputs remain isolated.
Two positive anchors are reused across pairs, giving thirty distinct payloads
across thirty-two pair slots. Report both pair-weighted and unique-payload results.

| Source | Change | Expected pair |
| --- | --- | --- |
| C011/R1 | Complete retail estimation method versus omitted material step | Pass / fail |
| C045/R1 | Actual Specific Plan classification versus merely compatible features | Pass / fail |
| C022/R1 | Non-binding versus binding service arrangement | Pass / fail |
| C049/R2 | Staging and loading versus staging alone | Pass / fail |
| C032/R1 | Baseline hazard resolved under mitigation versus same-condition conflict | Pass / fail |
| C029/R1 | Minimum 36 months versus minimum 3 months | Pass / fail |
| C049/R2 | Meaning-preserving paraphrase | Pass / pass |
| C032/R1 | Meaning-preserving scenario order/wording | Pass / pass |

Questions and reference text remain fixed. C includes all approved required and
optional points and a coherent authored conclusion; other required meanings are
held satisfied. RC perturbs only supporting points. Expected statuses, reasons,
source identities and pair labels live outside judge payloads. Pair partners are
judged separately; neither partner nor its expected label is shown to the judge.

These are controlled derivatives of exposed real cases, not untouched predictions
or held-out evaluation. The unit mistake is intentionally injected, not an observed
feet/inches error. Exclude the unresolved C007 local-resident interpretation rather
than force a label. Independent agent review checks each expected label and any
unresolved ambiguity is quarantined before execution. Agent agreement is not human
gold adjudication.

## Proposed execution

- Compare accepted and candidate prompts on identical packets, three independent
  requests each: 32 packets × 2 prompts × 3 repeats = **192 calls**.
- Same GPT-6 Luna model and medium reasoning; concurrency 16. Maximum output:
  6,144 tokens for C, 4,096 for RC. Standard service, 24-hour prompt caching,
  storage off, truncation disabled; no tools or additional source retrieval.
- No automatic SDK, transport or semantic retries. A malformed/truncated response
  is a result to inspect, not permission to resend. Keep native requests/responses,
  usage, errors and exact prompt/schema/payload hashes.
- Freeze reviewed expectations before calls. Interleave versions with a fixed
  schedule, preserving repeat identity; do not change prompts or labels mid-round.
- Track actual estimated charges plus in-flight/unknown liabilities against the
  new cap. Include cache writes; release only verified unused reservations.
  Earlier completed-run charges remain separate, not speculative new liabilities.
- Report point-status and overall accuracy separately for C; binary accuracy and
  witness validity for RC. Report each pair's expected change/invariance and
  within-packet repeat agreement. Equivalent sufficient RC witness sets are valid;
  do not score exact ID equality as the semantic target.
- Stop admission on cap risk, unexpected billing/settings drift, unknown charges,
  invalid source binding, or payload leakage. Preserve all attempted calls.
  Stop for user review after this single round; no automatic prompt promotion,
  expansion or real-run regrading, even with perfect results.

Budget calculations and final reviewed artifacts are linked in the
[result pointer](task15ad_c_rc_paired_regression_result.json).
Independent review agreed with all thirty-two expectations after making City
Engineer approval explicit in four C049 controls. This removed an incidental
optional-point ambiguity without changing the intended mutations or reference
meaning. The review was independent but not blinded; no unresolved label issues
remain in this prepared set. Execution must verify exact native delivery and its cost bound
before dispatch; exported request drafts are offline preparation only.

Proposed fresh cap: **$3.00**. The offline envelope for all 192 calls is
**$0.790965**, including full output limits and input charged at the cache-write
rate with no cache savings. This is a conservative reservation estimate, not an
expected actual charge or tokenizer-certified maximum. Native preflight must
recheck admission before any dispatch. No new calls have been made; current new
spend is $0. The completed real run's $1.776348480 is separate, with no unresolved
liabilities. There is no automatic transfer of its remaining authorization.

## Why this test

Paired edits distinguish sensitivity to consequential meaning from sensitivity to
wording. Repeats reveal instability; aggregate accuracy alone could conceal opposing
errors. This is a targeted diagnostic, too small and deliberately selected to
establish general judge reliability. Keep the broader accepted calibration suites
for any later promotion decision.

[OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
recommends task-specific cases, retained logs and calibration with human feedback.
[Current Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna)
(checked 2026-10-23) is $0.10 input, $0.01 cached input, $0.125 cache writes and
$0.50 output per million tokens below the long-context threshold. Budget conservatively
at the cache-write rate for all input; do not assume cache hits.
