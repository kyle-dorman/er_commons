# Task 09E.1 — Compare cloud and decision-model grounding judges

Status: **Planned; ready for a new implementation chat.** Written October 11,
2026. This planning turn authorizes no execution. The implementation scope below
captures the user's requested overnight preparation and bounded local trial;
cloud trials follow credential setup and an explicit run budget.

The user requested a committed baseline on
`codex/task09e-grounding-checkpoint`, then an implementation branch
`codex/task09e1-cloud-decision-judges` from that baseline. Start the new chat on
the implementation branch. That checkpoint precedes this task's Phase 0 cleanup;
the cleanup is work for the new chat, not part of preparing the baseline commit.

## Abstract

Prepare seven model/API conditions to test whether stronger models and native
classification APIs improve the staged grounding judge. Keep the same 69 Dev3
answers, evidence visibility and deterministic scoring rules. Separate quotation
validation from semantic decisions, and measure provider caching rather than
assuming it will reduce costs. Inspect continues to own execution, samples,
logs and aggregation. Build maintainable adapters, not production orchestration.

## Goal

Deliver working, offline-tested integrations and a bounded Clef local result,
plus reproducible, budgeted cloud commands ready for the user's next session.
Report unsupported provider capabilities honestly; missing keys must not block
unrelated implementation or offline validation. This task does not qualify a
production judge or expand the evaluation beyond Dev3.

## Inputs

Read these after AGENTS.md, docs/index.md and docs/todo.md:

- [Task 09 umbrella](09_build_evaluation_and_qualify_judges.md),
  [09E](09e_implement_grounding_judge.md) and its
  [current result pointer](../../docs/specs/task09e_final_result.json).
- Read the [09A.3 result pointer](../../docs/specs/task09a3_final_result.json)
  **before opening dataset artifacts**. Its combined publication contains 442
  answers, 430 comparison-eligible records and 38 clean abstentions. Keep the
  twelve review exclusions and all 419 predecessor records unchanged.
- [Staged judge contract](../../docs/specs/task09e_staged_grounding_v1.md),
  [abstention contract](../../docs/specs/task09e_abstention_v1.md),
  [point-scope prompt](../../docs/specs/task09e_point_scope_v2.md),
  [9B outcome](../../docs/specs/task09e_09a3_qwen9b_v1.md), and
  [small-model outcome](../../docs/specs/task09e_09a3_small_v1.md).
  Historical claims about missing point labels are superseded by 09A.3.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [architecture](../../docs/architecture.md),
  [artifact contract](../../docs/data_artifacts.md), and
  [documentation guide](../../docs/documentation.md).
- Relevant code: `grounding_run`, `grounding_dataset_panel`,
  `grounding_staged_inspect`, `grounding_stages`, `grounding_abstention`,
  `grounding_abstention_inspect`, `judge_packet_requests`,
  `judge_qualification`, and `ollama_token_counter` under `src/er_commons/`.

Use external paths relative to `ER_COMMONS_DATA_ROOT`:

- Dataset: `pipelines/brisbane_baylands/task_09/09a3_20261011_abstentions_v1/published/`.
- Frozen panel: `pipelines/brisbane_baylands/task_09/09e_20261011_09a3_small_v1/panel/manifest.json`.
- 9B baseline: `pipelines/brisbane_baylands/task_09/09e_20261011_09a3_qwen9b_v1/`.
- Quote diagnostic: `pipelines/brisbane_baylands/task_09/09e_20261011_quote_diagnostic_v1/analysis.json`.
  This is an unofficial offline diagnostic, not a replacement baseline.

Verify pointers and checksums before reuse. Preserve all prior artifacts and
uncommitted work. Do not rewrite hash-bound specifications to describe new runs.

## Candidate conditions and research checkpoint

These are researched starting identities as of October 11, 2026. Verify official
availability, exact endpoint, model identity, SDK compatibility and capability
constraints during implementation; record changes explicitly, never silently
substitute a different model. Freeze resolved identities before a comparison.

| Condition | Starting model | API / primary source |
| --- | --- | --- |
| OpenAI generation | `gpt-6-luna` | [Model](https://developers.openai.com/api/docs/models/gpt-6-luna); Responses |
| Anthropic generation | `claude-haiku-5-5` | [Haiku overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview); Messages |
| Fireworks GLM | `accounts/fireworks/models/glm-5p3-flash` | [Model](https://fireworks.ai/models/fireworks/glm-5p3-flash); chat completions |
| Fireworks DeepSeek | `accounts/fireworks/models/deepseek-v4p1-flash` | [Model](https://fireworks.ai/models/deepseek-ai/deepseek-v4p1-flash); chat completions |
| OpenAI Decisions | `gpt-6-luna` | [Decisions guide](https://developers.openai.com/api/docs/guides/decisions); `/v1/decisions` |
| TypeSafe Jev | `jev-1.13.0` | [Models](https://docs.typesafe.ai/models), [API](https://docs.typesafe.ai/api); `https://api.typesafe.ai/v1/systemone` |
| Local Clef Flash | `clef-flash`, exact digest/quantization to pin | [Ollama](https://ollama.com/library/clef-flash), [model card](https://huggingface.co/Cloudflare/clef-flash/blob/main/README.md); local `/v1/systemone` |

Read maintained [Inspect provider guidance](https://inspect.aisi.org.uk/providers.html)
before selecting integrations. Prefer existing Inspect providers and official
SDKs where they fit; use a narrow native adapter for genuinely different decision
endpoints. Inspect installed dependencies before adding or upgrading packages.

Important research distinctions to preserve in a compact implementation spec:

- Decisions are typed classification requests, not chat requests with shorter
  completions. OpenAI offers predicate/choice/score; TypeSafe and Clef expose
  typed questions over state. Their numeric `score` is not our discrete rubric.
  Use binary judgments and aggregate in project code.
- Freeze probability-to-boolean rules, option ordering, exact-tie handling and
  refusal handling before evaluation. Do not fit thresholds to this panel.
  Native confidence is not calibrated correctness.
- Confirm structured-output support and reasoning settings separately for each
  generation provider. Record any schema adaptation; retain local validation.
  See [Anthropic structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
  and [Fireworks structured responses](https://docs.fireworks.ai/structured-responses/structured-response-formatting).
- Jev documents both a total-request and state-plus-longest-question limit.
  Clef's advertised local context limits are inconsistent across documentation;
  hosted Cloudflare limits do not establish local Ollama capacity. Qualify the
  actual endpoint, runtime and assets; never silently truncate.
- The [TypeSafe citation example](https://docs.typesafe.ai/cookbooks/citation_check)
  checks candidate quotes; that differs from requiring the judge to generate a
  new quote. Native decision APIs need no invented explanation channel.

## Outputs

1. A reviewed, behavior-preserving judge-code cleanup, followed by a versioned implementation specification and checked-in model/run configs.
2. Thin, typed provider integrations behind existing packet/transport boundaries,
   with offline fixtures and Inspect-owned stage results.
3. An immutable new experiment manifest binding code, SDKs, model identities,
   dataset/panel hashes, schemas, prompts, decision rules and provider settings.
4. An offline readiness report, prompt-prefix/cache audit and cost estimates.
5. A local Clef qualification and bounded Dev3 report, or a precise blocker.
6. A short cloud handoff: credential environment names, secret-safe setup,
   dry-run/smoke/run commands, budget controls and expected artifacts. Never
   print keys, persist authorization headers or require keys in tracked config.
7. A new result pointer and task outcome, distinguishing implemented, offline
   tested, locally measured, cloud measured, unsupported and blocked conditions.

## Plan / spec requirement

Write and independently review the compact implementation spec before coding.
Resolve the provider mapping, validation split, counting contract and caching
measurement design there. Routine implementation choices do not require repeated
permission; a scoring-policy change or weaker preflight does.

### 0. Clean up the existing judge code first

Before adding providers or changing the result contract, perform a bounded,
behavior-preserving cleanup of the existing judge implementation. Read the
current module boundaries and focused tests, identify duplication and confusing
ownership, then write a short refactor plan. Prioritize request construction,
stage validation, Inspect integration, token preflight and result persistence
where clearer boundaries directly simplify this task. Keep functions typed,
small and understandable; remove genuinely redundant internal paths only after
checking callers. Avoid a new framework or speculative provider abstractions.

Freeze representative offline request and result fixtures before refactoring.
Preserve current prompts, schemas, scoring, source visibility, error handling,
CLI behavior and saved-artifact compatibility during this phase. Do not mix the
new quotation policy or interstage projection into cleanup. Preserve historical
code/configuration identities and sealed results; a new implementation identity
must not masquerade as the old one. Keep any necessary legacy reader narrow and
explicit rather than introducing broad compatibility aliases.

Run focused offline regression tests and independently review the cleanup for
behavioral parity and maintainability. Record what changed and the evidence that
requests and results are unchanged. Complete this checkpoint before provider
implementation, then proceed without another approval request. Broader unrelated
cleanup is out of scope; discoveries belong in the backlog.

### 1. Freeze comparison and semantic contracts

Reuse **all 69 eligible answers for Dev3 C041/C037/C014**, with exactly the saved
answer IDs, bytes and source bindings. Do not regenerate, atomize or repair
answers. A point may combine assertions and citations; evidence may be reused.
Use `record_origins.jsonl` to resolve each record's original artifact root.
Supplement additions are described by `supplement_slots.jsonl`, not the original
batch's coverage files. Keep `expectations.jsonl` out of request construction;
load proposed expectations only in post-run analysis.

Preserve the staged process:

1. Clean-abstention gate sees the original answer and distinguishes a content-free
   abstention from an answer containing substantive assertions.
2. One support check per original non-conclusion point, with the original point,
   its actual cited evidence and allowed linked context. Judge support, not
   completeness against the question. Every substantive assertion must pass.
3. Conclusion review sees original content/evidence and prior point predictions
   as fallible observations. Preserve unsupported text. Require a review for
   every point; disagreement remains `unresolved_disagreement`, not an override.

With complete, agreeing decisions: unsupported conclusion -> 0; supported
conclusion with any unsupported point -> 1; supported conclusion with all points
supported -> 2. Clean abstention -> N/A. Preserve existing zero-point handling;
verify it explicitly in the spec. Do not add an all-points-failed shortcut.
Missing/invalid decisions, refusal, context failure or transport failure remain
unscored errors, never false judgments or clean abstentions.

Provider requests may differ syntactically but must preserve the same semantic
questions and evidence visibility. Decision questions may share a request only
when their visible context and stage dependency are identical; do not expose
other points' sources to a point check merely to batch it. Document every
provider-specific transformation and hash rendered requests.

Freeze a common interstage observation containing ordered point IDs and binary
verdicts only. Every condition's conclusion review receives this same projection,
alongside the unchanged original content/evidence. Keep explanations, probability
vectors, issue spans and quote diagnostics in separate analysis artifacts; never
fabricate them for native decision APIs or expose them selectively to conclusion
review. Adapt existing `PointAssessment`-dependent input construction and
revalidation explicitly. This change is another recorded difference from the
historical pipeline, not evidence of a model-only improvement.

### 2. Separate semantic validity and quotation diagnostics

Create a new versioned result contract; preserve historical strict results.
Valid decisions can advance to conclusion review even if an optional generated
quote is absent or nonliteral. Retain quote diagnostics independently: literal
match, source linkage, unsupported-claim span validity and missing quotation.
Native decision outputs have quotation diagnostics marked not applicable.
Malformed decisions, invalid point IDs, missing/duplicate reviews and invalid
required source identities still fail structural validation. Do not strip bad
IDs, invent valid output or convert malformed responses to negative judgments.

Use generation models' quote fields only as a secondary diagnostic. Report the
new semantic result separately from an old-style strict-validation view wherever
comparable. This is a pipeline change plus model comparison, not a pure matched
model swap against the old 9B result. Keep prompt semantics fixed across this
matrix; the may/will example remains [backlog item 09E-I01](../../docs/backlog.md).

### 3. Implement and qualify transport, counting and restart behavior

Inspect owns scheduling, native call receipts, samples, logs and aggregation,
including decision endpoint calls. Reuse packet construction, persistence and
source resolution. Do not create a second evaluation runner. Keep provider
formatting, semantic validation and final aggregation separate and readable.

Require exact model/endpoint-specific request-token preflight, including rendered
instructions, schemas/questions and all provider overhead that counts toward
context. Use qualified local assets or an authoritative counting endpoint. A
chat tokenizer estimate does not qualify a decision request. Record counter
provenance and parity checks against native usage where available. Honor every
provider limit and explicit output/reasoning reserves; do not inherit Qwen's 48K
limit or 3K output setting automatically. A provider lacking exact preflight is
blocked for inference pending a separately accepted contract change; complete
its offline integration and report the specific gap.

Use bounded concurrency, timeouts and retry counts. Retry transient transport
failures only; do not retry semantic judgments until they agree. Account for
possibly billed failed attempts and prevent blind replay after uncertain network
outcomes. Saved-result reuse requires matching request/configuration identities
and verified receipts. Keep that reuse distinct from provider prompt caching.

### 4. Audit caching and control cost

Research each exact model and endpoint against primary documentation:
[OpenAI](https://developers.openai.com/api/docs/guides/prompt-caching),
[Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
[Fireworks](https://docs.fireworks.ai/guides/prompt-caching), and
[TypeSafe](https://docs.typesafe.ai/api). General chat caching documentation does
not prove that a decision endpoint supports caching.

For actual rendered Dev3 requests, report reusable prefix lengths, eligibility
thresholds, supported cache controls/breakpoints, TTL, schema/reasoning effects,
cache write/read pricing and the native fields needed to verify hits. Put stable
instructions and genuinely shared evidence before varying claims where the API
permits. Remove volatile metadata from reusable prefixes. Never pad requests or
add unrelated evidence to chase cache hits. Group compatible requests within TTL
without changing stage dependencies or evidence visibility.

Provide conservative no-cache and plausible-cache estimates per condition, plus
worst-case request/retry/output budgets. Unknown pricing or unsupported caching
must be explicit; caching is an optimization, not a prerequisite for correctness.
Require a positive per-run currency cap, request cap and output cap before paid
calls; reserve worst-case cost before dispatch. Stop safely at the cap and retain
partial results. Use current dated provider pricing, not remembered rates.

After credentials are available, run a small controlled cold/warm cache probe
with identical and shared-prefix requests. Bound this probe separately and keep
its repeated samples outside evaluation denominators. Report native cache-read
and cache-write tokens, total usage, estimated charges and billed figures when
available. A first request is not guaranteed cold: inspect its receipt. Latency
alone does not prove caching. If an endpoint exposes no cache evidence, say that
savings are unverified rather than claiming a hit rate.

### 5. Complete offline work, then bounded local Clef

Offline tests must require neither keys nor inference. Implement all feasible
provider adapters/configs before declaring the overnight handoff complete.
Missing cloud credentials do not block fixtures, request rendering, validation,
cost accounting or failure-path tests.

The requested implementation task permits obtaining the **single Clef Flash
model** and required matching local tokenizer/runtime support for this bounded
trial. Inspect existing assets first; record download size, license, digest,
quantization and runtime. This exception does not authorize other model downloads
or unrelated environment upgrades. Keep assets outside Git and stop if the
required runtime cannot be qualified without a broader change.

Qualify endpoint behavior, exact counting and no-truncation handling with tiny
invented fixtures first. Then run the frozen 69-answer Dev3 panel once through
Inspect if preflight passes. Bound the request count from the frozen panel and
stage graph, set a finite wall-clock limit, and retain partial progress if blocked.
Stop after the result for review; do not tune repeatedly overnight.

### 6. Prepare the cloud session and report comparisons

Cloud execution requires available credentials, verified endpoint access and a
configured spending cap. Prepare separate selection commands so the user can
launch one condition or the six cloud conditions deliberately. Start with small
protocol/cache smoke checks, then run at most the frozen Dev3 panel once per
selected condition. A blocked provider does not trigger a substitute model.
No paid cloud calls belong to the credential-free overnight phase.

Report coverage on all 69 answers and matched-valid comparisons separately;
include abstention false exemptions/misses, point support confusion counts,
conclusion support, review disagreements, final score distributions, structural
failures, quotation diagnostics, truncation/refusal/transport errors, latency,
tokens, cache use and cost. Review source-linked disagreements, not just aggregate
agreement. Generated expectations are proposed labels, not calibrated accuracy;
probability diagnostics carry the same limitation. Do not select a judge solely
from agreement among survivors of validation.

## Validation

- Focused offline tests for all provider request/response mappings, strict boolean
  and probability handling, ties/refusals, missing/duplicate IDs, quotation-only
  failures, stage dependencies, aggregation and unresolved disagreements.
  Exercise quotation separation through conclusion-input construction and its
  downstream revalidation: optional quote failures cannot reappear as hidden
  semantic blockers. Verify identical interstage projections across providers.
- Leakage fixtures prove expectations, automatic metrics, reference answers and
  hidden source roles never enter requests; selected metadata reads must not
  decode mixed-split question containers.
- Counting tests cover exact render binding, limit boundaries and truncation;
  unsupported counters fail closed. Cache tests cover eligibility, stable prefix
  preservation, native usage parsing and distinction from saved-result reuse.
- Budget/retry/resume tests cover partial results, cache-write charges, uncertain
  billing, request caps and secret redaction. Invalid or unavailable credentials
  must fail clearly without fallback or logging secrets.
- Verify frozen panel/source hashes and preservation of previous experiment
  inventories. Run focused tests, `make fix`, `make check`, and `git diff --check`.
  Latest 09E baseline: 3,923 passed, one skipped, three historical Task 06G
  failures. Verify the failure identities; do not hide new failures as baseline.

## Acceptance criteria

- The initial judge cleanup passes focused regression checks and independent
  review before semantic or provider changes are introduced.
- Seven explicit conditions have implemented, offline-tested paths or precise
  documented capability blockers; no unsupported endpoint is represented as live
  tested. Clef has a bounded result or a demonstrated local qualification blocker.
- Common scoring and evidence contracts are reviewed, tested and versioned;
  quotations no longer suppress otherwise valid semantic decisions.
- Cache opportunities and cost limits are inspectable before credentials; live
  savings are claimed only with native evidence. Cloud setup is ready to use
  without additional architecture work, subject to listed access/counter blockers.
- A new manifest/result pointer preserves earlier runs, and the handoff states
  exactly which cloud calls have and have not run. Human maintainability is a
  separate acceptance gate from passing tests.

## Non-goals and stop boundary

No Dev6, full-19, reserved checks, test evaluation, target-answer generation,
09F–09G, Task 10, broad challenge sweeps, ensembles, fine-tuning, new labeling,
may/will prompt experiment, production orchestration, commits or pushes.
Preserve the frozen 19-development/30-test allocation and original 423 development
variants / 118 reserved checks / five exclusions alongside the newer 09A.3
publication. Do not inspect reserved answers or test questions/references.
Dev6 would add C001/C019/C056 while retaining Dev3, but requires later review.

## Review pass

Use bounded, independently scoped subagents for provider contracts, semantic and
leakage invariants, token/cache/cost qualification, and final maintainability
review. Integrate findings; do not delegate the entire ambiguous task to one
agent. Review the implementation spec before coding and the final diff/results
before handoff. Explain the important API and caching tradeoffs in plain language.

## Outcome

Pending implementation in a new chat. No models, downloads or cloud calls were
executed while writing this plan.
