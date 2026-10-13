# GLM Flash and Haiku full-development comparison

The user requests Fireworks GLM Flash and Claude Haiku with the same selected
prompts, medium thinking and the same metrics. This authorizes these two model
comparisons despite the preceding Luna-only scope. No other model, test/reserved
data, later task, prompt tuning, commits or pushes. Preserve every historical seal.
The selected scope is each model's own claims and conclusions, as stated to the
user after the optional clarification window; a later answer may narrow this
before dispatch.

## Fixed semantic comparison

Use the sealed 430-answer, 19-case full-development panel from
`09e1_20261012_luna_conclusion_full_dev_v1`, all 1,056 original claim inputs,
the exact selected simple claims prompt and original visible-review conclusion
prompt. Each provider generates its own 1,056 claims once, then 430 conclusions
using that provider's actual frozen claims. No abstention-gate calls. Compare
with the sealed Luna original arm, retaining its reuse/new-claim provenance.
No clarified/structured prompt arm. Proposed labels stay outside requests and
are read by analysis only after the comparison runs finish or stop.

Same semantic schema, strict local validation, input/evidence visibility,
4096 output cap and aggregation. Render identical prompt text; provider-required
schema framing may differ and must be recorded. Haiku uses adaptive thinking and
native output_config.effort=medium with structured JSON. Fireworks requests
reasoning_effort=medium using its documented reasoning-plus-JSON route: schema
in prompt, no response_format because strict JSON mode disables reasoning.
This matches requested effort labels, not identical cross-model compute budgets;
GLM5.3-specific effort allocation is undocumented. Require live evidence that
thinking is enabled before full dispatch; don't silently substitute no thinking.

## Explicit provider preflight policy

The existing OpenAI exact-counter path and all old strict modes stay unchanged.
This separately named exploratory provider mode accepts Anthropic's documented
estimated count and Fireworks' lack of a documented exact preflight counter.
It never fabricates an exact receipt or claims exact token parity. This is a
versioned provider-specific qualification for the newly requested experiments.

Before paid dispatch, bind the entire rendered request and compute a conservative
input allowance from UTF-8 serialized request bytes plus 8,192 tokens for provider
framing. For Anthropic also call its native estimated counter with the exact
input/schema/thinking fields and retain the request/response. Use the larger of
the byte allowance and estimate+10%+2048. Require allowance+4096 below the smaller
of 200,000 tokens and half the documented context limit. This is an explicit
conservative assumption, not a formal tokenizer guarantee. Never truncate inputs;
request server context-overflow errors. Native input above the bound halts the
run. Preserve estimated/native deltas, usage and all failures. Qualify this path
with invented fixtures and fixed unlabelled longest-input probes before full use.

Reserve costs using this input allowance and full output cap, with dated rates
covering long-context/cache-write premiums. For Haiku, use the input allowance
to select its documented up-to-100,000-token tier or the fivefold higher tier;
reserve every input token at the full five-minute cache-write price and every
output token at that tier's output rate. The renderer fixes five-minute caching.
No cache savings assumed for budgets.
Inspect owns call execution and artifacts, at most 4 concurrent samples/provider,
no automatic retries or replacement of failed semantic results. Stop new scheduling
on failure, retain inflight/partial records. Credentials load internally from `.env`;
never read base.env or print/store credentials/headers. Explicit cache boundaries
may move without changing concatenated input; qualify native cache evidence.

## Qualification and budgets

Before panel execution, at most 8 qualification calls per provider, capped at $1
per provider, covering point/conclusion JSON, reasoning metadata, zero-point
validation and identical/shared-prefix cache diagnostics. Probes are outside
accuracy denominators. Fixing protocol-only issues requires new recorded probe
attempts within the same cap; never repeat a benchmark judgment to improve it.
Freeze final exact model IDs, API settings, schemas, scripts and identities after
qualification and independent review. Pin `claude-haiku-5-5` and
`accounts/fireworks/models/glm-5p3-flash` unless verified unavailable; no substitution.

Full graph has 1,486 calls/provider, 2,972 total. Request caps equal actual selected
counts; wall limit 3,600 seconds per stage. Initial conservative currency caps are
$25 Haiku and $15 GLM for the complete graph, shared across stages (plus separately
bounded qualification). Review rendered allowance totals before dispatch; if the
conservative reservation cannot fit, narrow headroom only with documented evidence
or stop before spending. Expected costs are reported separately from reservations.
No additional model/prompt runs follow automatically.

## Metrics, evidence and closeout

Reuse the frozen full-dev F1 helper and denominator policies: binary class-macro
F1, per-class precision/recall/F1, supports/confusion, balanced accuracy and accuracy;
null/clean abstentions separate. Original claims, conclusion reviews, conclusion
support and final 0/1/2 scores are distinct. Report conditional numeric F1 plus
coverage-aware F1, unscored counts, correct N/A and all-answer final-state agreement.
Report full 19, previous Dev6, added 13, outside C041 and per-case/equal-case summaries.
Failures never become false labels. Preserve exact comparisons of source packets
and disclose provider-owned predictions in conclusion inputs. This tests whole
provider pipelines, not an isolated conclusion-model effect.

Audit native request/result identities, estimated-counter payloads and actual
input allowances, model identity, schema/thinking settings, cost/cache/latency.
Independently recompute metrics and review changed/false-acceptance source cases
with bounded agents. Report provider transport differences and reasoning-budget
non-equivalence. One pass is not stability or human calibration. Source-review
interpretation ambiguities do not change proposed labels.

Run meaningful focused tests, make fix, make check and git diff --check; baseline
4,274 passed, 1 skipped and 3 historical Task 06G failures. Preserve prior artifact hashes,
scan raw/decoded logs for credentials, publish completion last and small tracked
result pointers. No default promotion from a single comparison.

## Primary sources

- https://platform.claude.com/docs/en/models/haiku-5-5/overview
- https://platform.claude.com/docs/en/build-with-claude/effort
- https://platform.claude.com/docs/en/build-with-claude/token-counting
- https://platform.claude.com/docs/en/api/messages/count_tokens
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://platform.claude.com/docs/en/about-claude/pricing
- https://fireworks.ai/models/fireworks/glm-5p3-flash
- https://docs.fireworks.ai/api-reference/post-chatcompletions
- https://docs.fireworks.ai/structured-responses/structured-response-formatting
- https://docs.fireworks.ai/guides/prompt-caching

These sources establish API controls and limits, not cross-provider equal compute
or actual account access. Qualification receipts supply measured runtime evidence.
