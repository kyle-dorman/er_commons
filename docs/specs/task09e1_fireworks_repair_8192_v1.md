# GLM empty-review repair, DeepSeek output allowance and failure overlap

The user authorizes a clarification and retry of the nine new GLM failures,
doubling DeepSeek's output allowance, and a comparison of failure patterns across
models. Publish only current configurations in the updated table: historical Luna,
updated Haiku, patched GLM and continued DeepSeek. Preserve all predecessor results.

## Inputs and boundaries

Use the sealed [Fireworks result](task09e1_fireworks_cache_resume_result.json),
its original input bindings and same full-development 09A.3 population:
19 cases, 430 eligible answers, 1,056 original claims, 392 substantive conclusions
and 38 clean N/A answers. No reserved/test data, label edits, default promotion,
other models, later tasks, commits or pushes. Fresh external namespace:
`09e1_20261012_fireworks_repair_8192_v1`.

Research rationale is the immediately preceding verified Fireworks native API,
cache and reasoning documentation, saved in the predecessor research receipt.
Retain its tested evidence-prefix layout, routing keys, pinned model identifiers,
native medium effort, prompt-schema mode and strict local validation. DeepSeek's
native medium maps to high; its output limit includes reasoning. No further
cache redesign or paid qualification probes are necessary: these rendering paths
already passed native cache gates. Bind those gates and verify current requests
offline; report actual new-run native cache usage separately.

## Authorized generations

GLM: exactly the nine new zero-point review errors from the 108-call continuation.
Append only: "Review only the individual claims supplied in the claim list. When
the supplied claim list is empty, return an empty point_reviews list. Do not
invent a claim ID or add the conclusion itself as a claim review; assess the
conclusion only in the conclusion fields."
Use unchanged inputs, schemas, complete empty vectors, medium effort and 4,096
output limit. Maximum nine calls, $0.10 new conservative reservation and 600 seconds.
Keep all other outputs, including twenty older invalid conclusions and five
invalid claims. Store original failures and separate patched totals. No retry of
these nine if the clarification fails.

DeepSeek: set maximum output to 8,192 for both stages. Preserve 47 valid original
claim results and the one completed invalid-locator result. Retry the single
truncated request once and run 1,007 previously undispatched claims: exactly
1,008 new claim attempts. Then run conclusions only for complete valid same-model
claim vectors (zero-claim answers remain eligible). No GLM clarification or
other semantic prompt changes for DeepSeek. Maximum 1,438 new calls, $35 new
conservative reservation and 3,600 seconds per stage. Retain historical costs
separately; do not confuse reservations with spending.

Keep individual parse/schema errors as failed outputs without retries. With the
larger DeepSeek allowance, a correctly accounted native length finish is also a
failed individual output, with its dependent conclusion skipped; it must not
discard unrelated remaining claims. This explicit per-item stop-policy revision
avoids another single verbose output stopping the entire requested comparison.
Unaccounted usage, transport, refusal, model mismatch, budget/context failures
still stop further dispatch. No automatic increase beyond 8,192 or retry loop.
Serialize within stable prefix groups, at most four groups concurrently.
Load credentials internally from `.env`; never read `base.env` or display keys.

## Metrics and failure analysis

Freeze analysis selection and formulas before opening new outcomes against labels.
Same full denominators, coverage-aware class-macro F1, conventional conditional F1,
accuracy counting every failure as wrong, explicit coverage and separate N/A.
Report original claims, reviews within conclusions, conclusion support and final
numeric scores separately, with per-class/per-case and prior-Dev6/added-13/outside-C041
breakdowns. Present only updated configurations, marking selective prompt repairs
and mixed output-limit provenance; historical outcomes stay linked as evidence.

Compare exact canonical claim/answer IDs, not just question names. Separate valid
semantic disagreement from invalid output, unresolved original/review disagreement,
dependent skip and undispatched items. Provide pairwise/shared/unique failure
overlap, question-level rates with denominators, and bounded source review of
representative common and model-specific errors. Repeated variants within a
question are correlated; overlap does not establish independent model weaknesses
or prove the synthetic proposed label correct. Do not infer mechanisms from
aggregate rankings alone.

Independent agents review preflight/cost/cache/preservation, native receipts,
metric arithmetic and selected source examples. Run focused offline tests,
required repository validation if implementation changes, and final diff checks.
Verify prior inventories, scan raw and decoded artifacts for credentials, seal
completion last, then publish a compact tracked pointer and current outcome.
