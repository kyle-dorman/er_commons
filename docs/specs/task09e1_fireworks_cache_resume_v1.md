# Fireworks cache qualification, GLM continuation and DeepSeek comparison

The user authorizes fixing and qualifying Fireworks caching before restarting
GLM Flash, and adding DeepSeek Flash only after its own cache qualification.
Final comparison includes historical Luna, updated GLM, DeepSeek, and only the
[patched Haiku result](task09e1_haiku_conclusion_patch_result.md). Original results
remain preserved. This supersedes the preceding pause on GLM/cache work.

## Narrow change and evidence

Fireworks caches exact prefixes within a replica. Its API prefers
`prompt_cache_key` for session affinity. Offline inspection found varying point
IDs and conclusion-review arrays inside schemas before the evidence, breaking
otherwise reusable prefixes. Add an explicit opt-in that leaves the judging
rubric unchanged in the system message and moves the exact schema instructions
after the complete unchanged evidence-first user payload. Derive a deterministic
routing key from model, stage, rubric, evidence and question, excluding variable
claims, answers and schemas. Use separate cache isolation keys only for probes.
No evidence union, padding, truncation, label exposure or semantic prompt tuning.
Default rendering and historical configurations remain unchanged.

Pin `accounts/fireworks/models/glm-5p3-flash` and
`accounts/fireworks/models/deepseek-v4p1-flash`; prompt-schema generation with
native `reasoning_effort=medium`, no native response_format (which disables
reasoning), output cap4096 and unchanged strict local validation. The existing
bounded single-complete-JSON-fence adapter may be extended to the pinned DeepSeek
condition; no syntax/value/schema repairs. DeepSeek maps medium to native high
(scale75), not equal compute with other models. Configure DeepSeek context
conservatively at1,000,000; keep conservative input allowances and overflow errors.

Dated standard rates per million input/cache-read/output tokens:
GLM0.15/0.03/0.50; DeepSeek0.30/0.006/1.20. Cache savings are never assumed when
reserving costs. Credentials load internally from `.env`; never read `base.env`
or print/store credentials or authorization headers.

## Cache gate before evaluation

Fresh external namespace: `09e1_20261012_fireworks_cache_resume_v1`.
Freeze scripts, exact prompts, schema, payload identities, settings and
implementation before paid probes. At most12 qualification calls per model,
$0.50 reserved per model,4096 output per call,900seconds total per model. No automatic
retries. For both point and conclusion stages, select unlabelled inputs with a
long shared evidence/question prefix and varying target content/schema. Probe
old and repaired layouts separately: A, identical A, changed B in sequence.
Use a fresh isolation key for each layout/stage pair. These protocol probes
are excluded from accuracy denominators and never selected by correctness.

Require the repaired exact repeat to show >=50% native cached input, and the
changed-target request to show >=30% cached input plus more cached tokens than
the stable system prompt's UTF-8 byte length+512 (a conservative check that reuse
extends into evidence). Confirm correct model, reasoning enabled somewhere in
each stage, valid schema, usage within allowances and prompt/payload preservation.
Report old/fixed native cache rates. A gate failure stops that model's evaluation;
do not silently weaken thresholds or equate small system-prefix hits with
working evidence reuse. Qualification success is no guarantee of every later hit.

## Authorized evaluation after each model passes

GLM: preserve all1056 original claim outcomes and317 completed native conclusion
outputs, including semantic/schema failures. Retry the one HTTP412 attempt once
in a fresh receipt, retaining its original unknown-usage reservation, and run
107 previously undispatched conclusions. Exactly108 new calls maximum; $2 new
reserved cap and retained history within original$15/1486attempt graph limits.
Five invalid-claim-dependent skipped answers stay unscored. Do not retry already
completed invalid outputs or regenerate correct judgments. Record mixed transport
layout provenance. User reports replenished balance; account billing remains
provider-controlled and the original HTTP cause is not inferred from its receipt.

DeepSeek: one fresh full-development pass,1056 original claims then up to430
conclusions with its own frozen valid claim predictions. At most1486calls and
$25 conservative reservation cap,3600seconds per stage. Use the same selected
original simple claims and original visible-review conclusion prompts as GLM.
No locator appendix or other prompt variant. Valid same-model claim vectors
are required before each conclusion; invalid claims cause explicit skips.

Group scheduling by stable cache-prefix identity, serialize within a group and
allow at most four groups concurrently. Preserve original result identities/order
for aggregation. Completed ordinary model-output parse/schema failures remain
unscored without replacement; transport, model identity, truncation/refusal,
usage, reservation and context failures halt subsequent dispatch. Record all
native cache/usage and unknown-cost attempts; no automatic retries/expansion.

## Metrics and closeout

Same430eligible answers/19devcases,1056claims,392substantive outcomes and38cleanN/A.
No reserved/test use. Report original claims, claim reviews, conclusion support,
final numeric scores, conditional and coverage-aware macro-F1, per-class/confusion,
accuracy, coverage, unresolved counts, cleanN/A, priorDev6/added13/outsideC041 and
per-case/equal-case metrics. Failures remain in full denominators. Comparison
uses patched Haiku only; note its mixed-prompt repair and GLM continuation versus
fresh DeepSeek. No default promotion, inference beyond these runs, later tasks,
commits or pushes.

Bounded independent agents review code/cache gates, native accounting, metric
arithmetic and selected source failures. Run focused regression tests, make fix,
make check and git diff --check (prior suite4303passed,1skipped,3historicalTask06G
failures). Preserve sealed artifacts, scan raw and decoded logs for credentials,
write completion last and publish a small tracked pointer and concise outcome.

Primary sources verified for this change:
- https://docs.fireworks.ai/guides/prompt-caching
- https://docs.fireworks.ai/api-reference/post-chatcompletions
- https://docs.fireworks.ai/structured-responses/structured-response-formatting
- https://docs.fireworks.ai/serverless/pricing
- https://app.fireworks.ai/models/fireworks/deepseek-v4p1-flash
