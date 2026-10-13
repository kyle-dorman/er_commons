# GLM fourteen-output repair and three-model Dev6 conclusion clarification

The user authorizes two sequential experiments: retry the fourteen older GLM
empty-claim-list failures with the already successful clarification, then test
the proposed conclusion clarification on Luna, Haiku and GLM using Dev6. Stop
and report after Dev6; the user decides whether to continue. DeepSeek is set aside.

## Inputs and boundaries

Read the [09A.3 pointer](task09a3_final_result.json) before dataset artifacts.
Use the sealed [latest comparison](task09e1_fireworks_repair_8192_result.json),
its bound predecessor records and native receipts. Preserve every previous
artifact, all twelve dataset exclusions and the development/reserved/test split.
New external namespace: `task_09/09e1_20261013_glm14_conditions_dev6_v1`.
No new claims, labels, answers, evidence, truncation, model substitutions,
DeepSeek calls, default promotion, later-task work, commits or pushes.

The existing Dev6 set is C041, C037, C014, C001, C019 and C056: 136 eligible
answers, 323 individual claims, 124 substantive conclusions and twelve clean
abstentions. Freeze each model's current actual claims from the latest comparison,
including accepted Haiku replacements. Within a model, both arms receive the
same complete claim vector, original answer, question, evidence and schema.
An invalid original claim prevents the dependent conclusion call in both arms;
that answer remains a failure in the full 136/124 denominators. Zero-claim answers
remain eligible; they are not all clean abstentions.

The fourteen GLM repair targets may span the full development panel. This
authorizes only those fourteen selected calls outside Dev6, not a full-panel
semantic prompt trial. Reading retained full-panel results for patched totals
does not authorize additional inference. The C029 habitat-management example
that motivated the semantic clarification is outside Dev6 and is not directly
retested: Dev6 tests broader effects and regressions.

## Phase A: exact fourteen-output repair

Derive exactly fourteen older failures from the latest bound validation inventory:
their original supplied claim list is empty and their invalid response invents
a claim review. Verify native records and exact IDs; do not include the nine
already repaired outputs or other invalid-output categories. Append the same
successful formatting clarification to the original conclusion prompt:

```text
Review only the individual claims supplied in the claim list. When the supplied claim list is empty, return an empty point_reviews list. Do not invent a claim ID or add the conclusion itself as a claim review; assess the conclusion only in the conclusion fields.
```

Use the pinned GLM model, medium reasoning, 4,096 output allowance, qualified
evidence-prefix rendering and unchanged validator/aggregation. Fourteen calls
maximum, $0.15 conservative reservation ceiling, 900-second wall limit. Attempt
each once. Preserve invalid outcomes; no automatic replay. Store patched
full-development totals separately from the unchanged previous result.

Phase A must terminate before Phase B starts. Semantic validation failures do
not prevent the independently authorized comparison; unresolved transport or
account/usage problems halt that provider pending diagnosis, without replay.

## Phase B: fresh paired Dev6 arms for each model

Use one fresh baseline pass and one fresh candidate pass per model. Original
claim decisions remain frozen; no prior conclusion result substitutes for a
fresh baseline. Luna and Haiku use the selected original conclusion prompt.
Both GLM arms additionally contain the Phase A empty-list instruction, so the
semantic contrast does not mix in the formatting repair.

The candidate adds exactly this text after its baseline prompt:

```text
A correct main answer does not compensate for an unsupported substantive assertion in the conclusion. Apply the same standard to conditions and scope in claims and conclusions. Accept ordinary paraphrases, but preserve qualifications that change the meaning.
```

No other semantic instruction, structured-explanation requirement, claim-prompt
change or evidence-ownership change. Existing grounding already checks conclusion
support. This tests clearer application of that existing rule; it does not add
a new judging dimension. The [prior research application](../llm_judge_learning_notes.md#applying-the-research-to-the-conclusion-stack--2026-10-12)
and the latest source review motivate the change. Earlier broader/structured
prompt failures remain relevant regression evidence. No general benefit from
more instructions is assumed.

Retain exact currently qualified model IDs, API/schema modes, medium reasoning,
4,096 output caps, cache rendering and native counting policies. Luna uses the
existing exact counter; Haiku uses its native estimated count plus conservative
allowance; GLM uses its documented exploratory conservative allowance. Bind
prior qualification receipts, verify new complete requests offline and report
actual native cache/cost behavior. No new paid cache probes are required.

Each arm permits at most 136 calls and 3,600 seconds. Conservative currency caps
per arm: Luna $2, GLM $2, Haiku $6; all six arms together at most $20. These are
reservations, not expected charges. Freeze exact smaller dispatch counts and
rendered reservation totals before dispatch; they must fit without assuming
cache savings. Maximum new calls across both phases is 830. At most four
concurrent requests per provider; separate arm identities/cache routing and
no saved-result reuse. Retain the existing finite request timeouts.

Preparation selects 136 Luna, 136 Haiku and 135 GLM requests per arm; one GLM
answer is skipped because its frozen original claim is invalid. Thus the actual
maximum is 828 calls including fourteen repairs. Conservative offline plans
fit the caps: repairs $0.0674812; Luna baseline/candidate
$1.9516783/$1.9614771; Haiku $2.190025125/$2.196706125; GLM
$1.09513995/$1.10044545. Luna's live exact counter and Haiku's estimated counter
remain required before their individual paid dispatches; those checks may block
requests and must never be bypassed to spend the offline planning estimate.

Keep per-item JSON/schema/semantic failures as failures without replacement.
Transport uncertainty, unknown usage, model mismatch, refusal, context or budget
failures halt new dispatch for the affected provider; retain inflight records.
Do not increase output/time/budget limits or retry failed benchmark requests
automatically. Other independently healthy providers may finish their bounded
arms. Credentials load internally from `.env`; never read `base.env`, print
values or persist authorization headers.

## Frozen analysis and interpretation

Freeze analysis formulas, selection and scripts before paid calls. Expected
labels/reasons stay outside model requests and preparation. Compare new outputs
to labels only after all planned arms have terminal summaries or explicit stop
records. Phase A patched totals and Phase B fresh comparisons remain separate.

Report conclusion and claim-review class-macro F1, per-class confusion and
false acceptance/rejection, full-denominator accuracy (failures are wrong),
conditional metrics plus coverage, numeric-score F1/accuracy/coverage and
unresolved disagreement counts. Report twelve clean N/A outcomes separately.
Original claims are unchanged contextual baselines, not newly measured gains.
Provide per-question and equal-case metrics, outside-C041 results, paired fixes
and regressions on exact IDs, and source review of changed conclusion verdicts,
new false acceptances and representative claim-review reversals.

For each model, a promising semantic result requires a net substantive conclusion
agreement gain, including a gain outside C041, no increase in false acceptances,
no loss of claim-review agreement or clean-N/A correctness, and source-supported
improvements. Numeric-score results and validation regressions remain explicit
even when this gate passes. Report tradeoffs without changing the gate after
observing outcomes. A tie is not improvement. No automatic expansion or promotion.

Development labels are synthetic proposals; source interpretation disputes do
not change them in this experiment. Variants are correlated, provider-owned
vectors differ, selective historical claim repairs remain, and one fresh pass
per arm does not establish stability or equal cross-provider compute.

## Verification and publication

Use Inspect and existing maintained adapters; copy needed external helpers into
the fresh namespace rather than importing from sealed predecessor directories.
Independently review exact fourteen selection, Dev6/vector/request parity,
zero-point behavior, budgets/counting/cache routing, stops and frozen metrics
before dispatch. Run focused offline guard/metric tests. If package code changes,
run `make fix` and `make check`; otherwise preserve the current 4,324-pass,
one-skip, three-historical-Task-06G-failure validation and run relevant external
tests plus `git diff --check`.

Independently audit native usage, identities, costs and all denominators; verify
consumed prior inventories, scan raw and decoded artifacts for credentials,
review the report, write the completion inventory last, and publish a small
tracked result pointer. Stop after reporting Phase A and Dev6 results.
