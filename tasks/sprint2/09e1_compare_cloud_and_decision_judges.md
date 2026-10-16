# Task 09E.1 — Compare cloud and decision-model grounding judges

Status: **complete** — closed by the user on October 13, 2026.

For a consolidated account of successful and unsuccessful techniques, start with
the [grounding experiment record](../../docs/grounding_experiment_record.md).
The historical entries and linked reports below retain detailed evidence.

Implemented and evaluated the authorized provider comparisons, semantic/quotation
separation, cache repairs and cost checks. The user selects **GLM Flash**, medium
reasoning, the simple claims prompt and original conclusion semantics with the
empty-review clarification. Luna and Haiku remain alternatives. Clef is retired;
DeepSeek and the rejected semantic appendix are set aside.

The [accepted result](../../docs/specs/task09e1_glm14_conditions_dev6_result.md)
reports patched full-development GLM original-claims/conclusion/numeric macro-F1
of **97.50% / 97.57% / 93.46%**. These include targeted repairs with mixed prompt
provenance, not a fresh uniform full-panel run. Missing/invalid outputs count as
failures. Remaining semantic errors and disagreements are accepted development
limitations, not unfinished prompt-tuning work.

[09E.2 cleanup](09e2_cleanup_grounding_judges.md) is complete. Current configurations
and commands are in the [maintainer guide](../../docs/grounding_judge_guide.md).
Exact preflight for unused providers, connection pooling and further model tuning
are deferred rather than closeout requirements. No new inference or dataset
expansion is part of this closeout. 09F implements adequacy; 09G owns the final
challenge/freeze. The user now authorizes the local commit/merge and removal of
the merged parent checkpoint branch.

## Historical planning and experiment updates

The records below retain their original execution boundaries and result links.
References to paused providers, pending cloud tests or no commits describe those
historical runs; the current task status and selection are stated above.


Completed engineering follow-up: [09E.2 cleanup](09e2_cleanup_grounding_judges.md)
covers this implementation and inherited Task 09E code. The experiment records
below remain historical; Clef execution is retired by the user's October 13
instruction. Use the [maintainer guide](../../docs/grounding_judge_guide.md) for
current commands. No prior result or artifact is replaced.

Current selection (user, October 13): use GLM for subsequent judge work, retaining the original semantic prompt and empty-list clarification. Set aside the semantic appendix and DeepSeek. This records the selected configuration; no new inference, default code changes or judge-qualification claim follows.

Latest follow-up complete: [fourteen GLM repairs and three-model Dev6 prompt test](../../docs/specs/task09e1_glm14_conditions_dev6_result.md). Thirteen repairs succeed; one remains invalid. Patched full-panel GLM conclusion/numeric macro-F1 is 97.57%/93.46%. The semantic candidate fails the frozen improvement gate for Luna, Haiku and GLM; retain the original semantic prompt and empty-list clarification. No Dev6 expansion, defaults, labels, commits or pushes. DeepSeek remains set aside. [Result pointer](../../docs/specs/task09e1_glm14_conditions_dev6_result.json).

Current follow-up complete with partial DeepSeek coverage: [updated GLM repair and cross-model failure analysis](../../docs/specs/task09e1_fireworks_repair_8192_result.md). All nine GLM retries validate and match labels; updated conclusion/numeric macro-F1 is 95.67%/91.76%. DeepSeek retains 822 valid claims, nine failures and 225 undispatched claims after a second uncertain transport timeout; no conclusions ran. Exact-item analysis distinguishes semantic disagreement from invalid/missing outputs. The [result pointer](../../docs/specs/task09e1_fireworks_repair_8192_result.json) preserves contracts, native audits, overlap/source review and all prior artifacts. No further inference, default promotion, label changes, commits or pushes.

Prior follow-up complete: the [five-conclusion Haiku patch](../../docs/specs/task09e1_haiku_conclusion_patch_result.md) adds five valid, label-matching numeric scores. Patched conclusion/numeric macro-F1 is 96.05%/89.05%. Preserve original comparison and separate mixed-prompt results. No further inference; GLM remains paused.

Prior follow-up complete: the [five-claim Haiku locator diagnostic](../../docs/specs/task09e1_haiku_locator_retry_result.md) produces five valid unsupported judgments with empty locators. Prior full-panel metrics stay frozen; no prompt default change. GLM and cache investigation remain paused.

Status: **Authorized GLM Flash and Haiku comparison complete with limitations.**
The [result](../../docs/specs/task09e1_glm_haiku_full_dev_result.md) records a complete
Haiku pass and full GLM claims, with GLM conclusions stopped on HTTP 412. All missing
outputs remain in coverage-aware metrics. No further inference or default promotion.
The [new contract](../../docs/specs/task09e1_glm_haiku_full_dev_v1.md) tests each
provider on the selected simple claims and original conclusion prompts, with
native medium effort and the same full-development metrics. It separately
records provider counting and reasoning differences. The
[validation-error continuation](../../docs/specs/task09e1_glm_json_continuation_v1.md)
preserves initial strict-parser failures, recovers single GLM JSON wrappers,
and retains genuine model-output errors as unscored without paid retries.
No reserved/test use,
other models, later tasks, commits or pushes.

The prior full-development Luna conclusion comparison is complete.
The [result](../../docs/specs/task09e1_luna_conclusion_full_dev_result.md) covers
430 eligible answers and 1,593 valid new generations. Conclusion macro-F1 is
92.93% original versus 92.97% clarified; the added thirteen questions and claim
reviews show no gain. Keep the simpler original; no package default or label
changes. The new contract's explicit full-19 authorization applied only to this
experiment. That completed run authorized no further inference; the new user request above
authorizes only the two additional provider comparisons.

The prior Dev6 comparison is complete.
The [result](../../docs/specs/task09e1_luna_conclusion_evidence_dev6_result.md)
records 272 valid judgments with 323 frozen original claims. Overall conclusion
agreement remains 117/124; outside C041 it rises 100/104 to 103/104, and claim
reviews rise 317/323 to 320/323. The original overall-gain criterion is unmet.
No default or label changes, commits or pushes follow from the prior result.
Earlier failed experiments remain preserved.
See the [Dev6 outcome](../../docs/specs/task09e1_luna_structured_dev6_result.md).
The user's later instruction explicitly permits this expansion despite the
[structured pilot's failed criteria](../../docs/specs/task09e1_luna_structured_claims_result.md).
Historical stop boundaries below describe their respective completed runs.
The prior
[cache/pipeline outcome](../../docs/specs/task09e1_luna_cache_pipeline_result.md)
preserves the cache improvement and full-pipeline prompt arms.
Both contextual claim additions are set aside; no larger Dev3 pass was triggered.
Other cloud conditions and exact-counter gaps remain pending; no judge is qualified.
The October 12 user instruction permits trying unchanged inputs that fit without
advance exact counting, for local Clef only. See the additive
[exploratory contract](../../docs/specs/task09e1_clef_exploratory_v1.md).
Implemented October 11, 2026 on
`codex/task09e1-cloud-decision-judges` from `f0c57a0`, under the user's explicit
implementation authorization. The October 11 offline result made no paid calls,
model downloads, commits or pushes; the separate October 12 trial downloads only Clef.
See the [result pointer](../../docs/specs/task09e1_final_result.json) and
[current cloud handoff](../../docs/specs/task09e1_cloud_handoff.md).

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

## October 11 offline outcome (preserved)

Completed the credential-free implementation and independent reviews. Phase 0
preserves legacy judge behavior; the new version implements seven provider wire
paths, binary-only observations, quotation diagnostics, exact-preflight guards,
conservative budgets and Inspect-owned execution. No model has been qualified by
this work. The local trial stopped at demonstrated endpoint/counting blockers;
no inference or downloads were needed to establish them.

### Implementation and reviews

- [Phase 0](../../docs/specs/task09e1_phase0.md): unchanged stage-executor body
  extracted to its own owner; five invented golden scenarios passed before and
  after, 254 focused regressions passed, and independent review verified AST parity.
- [Comparison specification](../../docs/specs/task09e1_comparison_v1.md) and
  [spec review](../../docs/specs/task09e1_spec_review.md): native paired predicates
  preserve the three-way gate; generation fields are diagnostic; exact ordered
  binary predictions alone enter conclusion review. Zero-point, disagreement,
  missing decisions and structural source-identity behavior are preserved.
- [Provider research](../../docs/specs/task09e1_provider_research.md) and
  [final review](../../docs/specs/task09e1_final_review.md): all seven configurations
  are explicit, endpoint-specific schema adaptations are documented, and local
  strict validation remains authoritative. No new runtime dependency was added.
- Seven actual Inspect runs with invented provider responses each completed all
  three stages and scored the invented supported example 2. Network and credential
  access were forbidden in this fixture execution. These are plumbing results,
  not model judgments or Dev3 performance.

### Local qualification and offline audit

The unchanged selected panel contains 69 answers (C041 22, C037 27, C014 20),
166 original non-conclusion points, and a maximum of 304 stage calls. Each
condition's final audit contains 373 rendered shapes: every gate and point plus
all-false/all-true synthetic conclusion observations. Those synthetic observations
are explicitly audit-only; actual execution uses validated model predictions.
Original source, answer, origin and panel hashes were verified without loading
expectation files for request construction. All 34,055 previous Task 09 files
remained byte-identical.

[Clef qualification](../../docs/specs/task09e1_clef_qualification.md) found Ollama
0.40.2 installed, daemon stopped and Clef absent. The local System One endpoint
has a 65,536-byte limit and no qualified exact preflight counter. Twenty original
point payloads alone exceed that ceiling. Final rendering rejects 54 audit shapes:
20 point calls and 34 alternate conclusion shapes (17 possible conclusion calls).
Thus 37 of the maximum 304 actual-stage shapes exceed the limit; this is not a
measured failure count. Largest rendered Clef body: 113,727 bytes. No source
truncation, point splitting, other-model download or runtime upgrade was attempted.

### Caching and cost findings

Stable evidence precedes changing point text. Adjacent same-stage visible prefixes
reach roughly 111–115 KB, depending on provider; these are **bytes, not exact token
counts or eligible cache boundaries**. OpenAI implicit caching's message boundaries
mean an intra-message shared-evidence prefix alone does not prove savings.
No native cache hits, writes, latency improvement or billed savings were measured.
Exact offline request totals and plausible-cache currency estimates remain unknown.
Dated rates, thresholds, TTL/controls, write premiums and native usage fields are
recorded for inspection. Full-context worst-case ceilings are available where
context limits are known; these loose upper bounds are not expected Dev3 spend.

The runner reserves worst-case input/write/output cost before inference, retains
possibly billed failed reservations, enforces cumulative request/output/wall caps,
and stops on native count or output-usage mismatches even when semantic output is
malformed. No automatic retry is enabled. The live CLI refuses an existing run
namespace; verified receipt reuse is separately tested and never described as a
provider cache hit. Protocol/cache probes are excluded from evaluation denominators.

### Validation and remaining gates

`make fix` passed. `make check` passed format/lint/types and reported **4,155 passed,
one skipped, three unchanged historical Task 06G failures**, with no new failures:

- `test_collection_generator_preserves_historical_v38_owner_packet`
- `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`
- `test_task06g_templates_are_executable_and_source_free`

The new comparison suite has 227 tests; the final focused selection has 262 passing
tests. `git diff --check` passed. Final artifacts and their independent integrity
review are bound by the new result pointer; prior result pointers are unchanged.

OpenAI Responses can perform credentialed exact counting and bounded protocol
qualification using the [handoff commands](../../docs/specs/task09e1_cloud_handoff.md).
The other five cloud conditions lack qualified exact preflight (and Decisions'
endpoint context limit is unresolved). Credentials alone cannot unblock them.
Cloud testing has therefore **not** produced coverage, confusion counts, model
comparisons or source-linked model disagreements. The separate post-run analyzer
implements those reports with all-69 denominators and matched-valid comparisons,
retaining the proposed-label limitation.

No Clef/cloud inference, reserved/test content, Dev6/full-19 expansion, later-task
work, commits or pushes occurred. Stop here for credential setup and deliberate
bounded cloud testing; do not infer authorization to weaken any counting gate.

## October 12 user-authorized local exploratory outcome

The later explicit request authorized trying original fitting Clef inputs without
exact advance counting, with no truncation. The independently reviewed local-only
exception leaves cloud/default gates intact. See the additive
[contract and full outcome](../../docs/specs/task09e1_clef_exploratory_v1.md) and
[result pointer](../../docs/specs/task09e1_clef_exploratory_result.json).

Downloaded only Clef Flash and completed a three-stage invented native smoke,
then the unchanged 69-answer Dev3 pass once through Inspect in 915 seconds.
All 258 dispatched requests returned valid structures; 21 reached stages exceeded
the byte ceiling and were skipped. Final outcomes: 22 numeric scores, seven
abstention classifications (including one proposed-label false exemption), 23
review disagreements, 16 size-blocked answers and one ambiguous gate. Nothing was
truncated, regenerated, split or retried. The runtime's enforced 16K context did
not reject any dispatched request; the largest used 10,238 native input tokens.

Local native receipts report 600,847 input tokens and 246,313 cache-read tokens;
cache writes and latency savings remain unmeasured. This is local prefix reuse,
not cloud cache evidence or saved-result replay. Model/runtime/code identities
and all prior artifact hashes remained unchanged. Clef remains unqualified.

Focused tests: 268 passed; independent bounded review selection: 151 passed.
`make fix` and format/lint/types passed; final `make check` produced 4,191 passed,
one skipped and only the three historical Task 06G failures. An inference-time
timing-test failure cleared on the full post-inference rerun without a code change.
`git diff --check` passed. No paid cloud calls, broader panels, later tasks, commits
or pushes occurred. Stop after this single trial; truncation was not authorized.

## October 12 authorized Luna generation outcome

The user supplied OpenAI credentials in `.env` and explicitly requested Luna
generation next. A code-only loader kept key values out of messages and artifacts.
The account also lists GPT-5.4 and GPT-5.4-mini, requested follow-up candidates;
no substitution or extra model/provider run occurred.

One smoke exposed and fixed a narrow parser defect rejecting successful
`error: null` responses. The original response was revalidated offline without
another generation. Three cache probes then qualified count parity and confirmed
identical-request reuse. The unchanged 69-answer panel ran once through Inspect:
298 successful generations, 52 numeric scores, six clean abstentions and 11
unresolved disagreements, in 1,254 seconds. All input counts matched native usage;
there were no context, truncation, schema, transport or output-cap failures.

Agreement with proposed labels was 151/166 point decisions, 56/63 conclusions
and 47/52 numeric scores. The gate made no false exemptions or misses. This is
better measured coverage than historical Qwen 9B (12 scores, six matching), but
the model and quotation/observation pipeline both changed. Synthetic proposals
are not calibrated truth. C041 review inconsistency and quotation defects persist.

Panel reservations stayed at $1.441928950 under the $2 cap. Measured token buckets
imply $0.233855565 at standard list rates; all 302 generation receipts across
smoke/cache/panel report OpenAI as payer. No invoice or future-free guarantee is
inferred. The [full outcome](../../docs/specs/task09e1_luna_generation_v1.md) and
[result pointer](../../docs/specs/task09e1_luna_generation_result.json) preserve
cache writes/reads, source-linked review, cost estimates and exact setup commands.

Independent code and artifact reviews passed. Focused provider tests: 109 passed.
`make fix`, format/lint/types and `git diff --check` passed. Full tests: 4,197
passed, one skipped and only the three historical Task 06G failures. All prior
artifacts remained unchanged. No Decisions, other-provider calls, expanded panels,
prompt tuning, later tasks, commits or pushes occurred. Stop after this trial.

## Shared-evidence prompt caching — authorized follow-up

The subsequent user-authorized [settings, prompt and two-model comparison](../../docs/specs/task09e1_settings_prompts_models_v1.md)
uses only the inconsistent claims and existing Dev3 panel. Its bounded contract
superseded the previous stop for those experiments. The newer user request now
authorizes the [Luna-only cache and complete-pipeline follow-up](../../docs/specs/task09e1_luna_cache_pipeline_v1.md).

- [x] Investigate and improve provider prompt-cache reuse when the cited evidence
  stays the same but the target claim changes. The Luna shared-evidence probe
  reported zero cache-read tokens, whereas exact duplicate panel requests reused
  about 99.7% of input tokens after the first call. Inspect serialized prefix
  order, changing schema/point IDs, cache settings and native diagnostics before
  attributing the miss to a specific cause. Keep evidence visibility and judge
  semantics unchanged; record a bounded before/after comparison of native token
  buckets and costs in a fresh namespace. Distinguish provider input caching
  from application-level reuse of completed judgments. The later user request activates this work only in the fresh Luna follow-up
  namespace; the sealed earlier runs remain unchanged.

## October 12 authorized settings, prompts and two-model outcome

All three requested phases are complete in a fresh external namespace. The
[full outcome](../../docs/specs/task09e1_settings_prompts_models_result.md) records
every arm, the negative results, source review, billing limitations and exact
historical invocations; the [result pointer](../../docs/specs/task09e1_settings_prompts_models_result.json)
binds the sealed evidence.

On eight inconsistent requests with three fresh repetitions each, medium reasoning
improved clear-review agreement from 7/12 to 10/12. Temperature zero was more
consistent but much less aligned with those interpretations (3/12); the no-reasoning
temperature-one arm stopped after an output-cap failure. Of five frozen prompt
additions, the combined scope/absence/grammar clarification reached 12/12 clear
comparisons and seven unanimous claims; the checklist reached 12/12 and six.
Standalone variants failed the frozen selection rule. A fixed-context conclusion
check improved one clearer interpretation but left ten of eleven answers unresolved
in both arms. No prompt or setting was promoted.

Both original-prompt, low-reasoning 69-answer passes finished with exact input
counts and unchanged panel boundaries. GPT-5.4 produced 54 scores, 52 matching
proposals; mini produced 55, 44 matching. Each had six clean abstentions and seven
unresolved disagreements; two GPT-5.4 and one mini outputs failed citation-locator
validation. GPT-5.4 leads the observed comparison but still accepts cross-citation
support in a source-reviewed case, even where the proposal agrees. No model is
qualified. Shared-evidence cache optimization was subsequently completed in the Luna follow-up below.

All 831 generations, including diagnostics and two protocol smokes, imply $4.886705
at recorded standard rates. Native payer metadata splits into 311 developer,
519 OpenAI and one unreported response; promotional coverage and invoice totals
are not inferred. Actual usage stayed within all predeclared bounds. Failed
count attempts are preserved; a narrow sampling-counter repair dispatched only
previously unrun trials. No automatic retries, truncation, later-task work,
expanded datasets, commits or pushes occurred.

Independent settings, prompt, review-stage, model, identity and artifact audits
completed. Focused tests: 181 passed. `make fix` passed; `make check` reported
4,230 passed, one skipped and only the three historical Task 06G failures, with
format/lint/types passing. Prior inventory and all three older sealed namespaces
remained byte-identical. See the result pointer for final scan and seal evidence.


## Completed Luna-only follow-up

The user selected **Luna only for subsequent inference** because of cost and
authorized cache repair followed by complete-pipeline prompt experiments on the
eleven original inconsistent answers. Follow the [bounded contract](../../docs/specs/task09e1_luna_cache_pipeline_v1.md):
cache qualification first, then four prompt combinations with fresh point
predictions entering fresh conclusions. Other provider implementations and prior
results remain historical; no further GPT-5.4/mini or other-provider calls.


The [full outcome](../../docs/specs/task09e1_luna_cache_pipeline_result.md) and
[result pointer](../../docs/specs/task09e1_luna_cache_pipeline_result.json) record
twelve successful cache probes and four complete three-repeat passes of eleven
original inconsistent answers. Changed-claim cache reads improved from zero to
1,303 tokens in both tested pairs; full-pipeline cache reads were 75.75% of input.
Numeric coverage was 18/33 original, 18/33 claims-only, 22/33 both-stage and 26/33
with the stronger conclusion addition. C/D achieved 15/15 clearer diagnostics
at both stages, but matched fresh point vectors showed equal numeric coverage
between arms. D also rejected a nonfactual procedural conclusion once for lacking
citations. Claims-only is set aside; C remains a development candidate, and D is
not promoted despite ranking first quantitatively. No default prompt changes.

All 768 Luna generations validated, with a $0.223372 standard-rate estimate and
complete developer-payer receipts. No invoice or promotional-credit claim.
Focused tests: 210 passed; make fix passed; make check: 4,259 passed, one skipped,
three historical Task 06G failures only. Independent code, cache, source, result,
identity and preservation audits are retained. All 45,712 prior file checks match.
No later-task work, expanded panel, other model calls, commits or pushes.

## Completed contextual claim interpretation experiment

The user now prioritizes individual claim accuracy and accepts natural summaries
in question context rather than the strictest possible grammatical reading.
The [new bounded contract](../../docs/specs/task09e1_luna_context_claims_v1.md)
authorizes one contextual prompt candidate against the previous combined prompt:
four distinct troublesome inputs and six controls, nine repetitions per arm.
A frozen numerical and independent source-review gate controls expansion to two
fresh claims-only passes over the existing 166 Dev3 claims. No conclusion or
abstention inference, new model or panel expansion is authorized by this follow-up.

The [pilot outcome](../../docs/specs/task09e1_luna_context_claims_result.md) records
180 valid Luna generations: contextual instructions improved trouble agreement
28/36 to 31/36, but grading fell 9/9 to 8/9 and controls fell 53/54 to 52/54.
The candidate accepted an explicitly overbroad resident pet-policy claim twice.
The frozen expansion gate failed; no full Dev3 pass, conclusion/gate calls or
further tuning followed. The appended candidate is set aside without changing
defaults. Standard-rate estimate: $0.047954555; all native payer fields developer.
Independent reviews completed; all 48,998 prior inventory checks passed. Focused tests
210 passed; eight launcher guard tests passed; make fix passed; make check retained
only the three historical Task 06G failures (4,259 passed, one skipped).

## Completed scope-preserving replacement pilot

The user authorizes replacing the failed broad contextual addition with a rule
that checks subject, requirement and condition together while preserving explicit
scope boundaries. Follow the [new contract](../../docs/specs/task09e1_luna_scope_claims_v1.md):
same ten pilot inputs, nine repetitions per arm, fresh combined-prompt baseline,
and unchanged source/numeric gate for conditional claims-only Dev3. Preserve the
previous negative result; no additional conclusion work or default promotion.

The [outcome](../../docs/specs/task09e1_luna_scope_claims_result.md) records another
180 valid Luna calls. Candidate agreement fell to 79/90 from fresh baseline 83/90:
trouble 29→26/36 and controls 54→53/54. Stable correct inputs fell 8→5/10. The same
unsupported universal-policy control was accepted once, and grading regressed.
The unchanged numerical/source gate denied expansion; no full Dev3 calls or
prompt promotion. Standard-rate estimate $0.052901555, native payer developer.
Independent reviews completed; all 49,934 prior checks match. Focused 210 and
launcher eight tests passed; make fix/check retained 4,259 passed, one skipped,
three historical Task 06G failures. No package changes, extra models, commits or pushes.

## October 12 research pause

The user requested best-practice research before further experiments. The
[research synthesis](../../docs/llm_judge_learning_notes.md#research-review--2026-10-12)
revisits the original EMNLP survey and primary work on contextual judgments,
factual decomposition, citation verification, rubric design and calibration.
Three bounded research reviewers examined separate areas; a separate synthesis
review checks the recommendation and transfer limits.

The proposed next experiment compares direct support judging with a compact
evidence-linked relationship representation, preserving qualifiers and evaluating
intermediate fidelity separately. This is a hypothesis, not an adopted protocol
or a claimed accuracy improvement. Repeated agreement, proposed-label agreement
and independently established correctness remain distinct. Calibrated abstention
requires representative independent labels; Decision 006 keeps human calibration
optional and separately authorized.

No inference, implementation, label change or artifact mutation occurred during
this research phase. Luna-only, claims-only and existing dataset boundaries remain.
Further execution needs a bounded experiment contract; neither failed prompt is
promoted. Documentation diff inspection and `git diff --check` are the validation
for this documentation-only follow-up.

## Authorized focused structured-explanation pilot

The user now requests the small test. Follow the [bounded contract](../../docs/specs/task09e1_luna_structured_claims_v1.md):
the same ten development inputs, two Luna prompt arms, five fresh repetitions
each, no full-panel expansion. Existing judging already operates per claim; this
candidate exposes claim/evidence interpretation and material mismatch in the
existing explanation field. No new decomposition stage or package default is
introduced. Source fidelity, control errors and repeatability remain separate
from raw agreement with proposed labels.

The [completed outcome](../../docs/specs/task09e1_luna_structured_claims_result.md)
records 100 valid generations: agreement 44/50 baseline versus 45/50 structured,
controls 30/30 each, unanimous-correct inputs 7/10 versus 8/10. Grading improves
3/5 to 5/5, but short-policy S1 regresses 5/5 to 2/5. The candidate fails its
predeclared gain/nonregression criteria and is set aside, without expansion.
All candidate explanations use the requested headings and stay below 200 words;
format compliance does not establish semantic correctness. Total standard-rate
estimate $0.030897840, with developer-payer receipts and exact native parity.
Focused 275 and offline guard 11 tests pass; make fix/check retain 4,259 passed,
one skipped and the three historical Task 06G failures. Prior 50,869 inventory
checks match. No default changes, additional model runs, commits or pushes.

## Completed user-authorized Dev6 claims comparison

The user explicitly requested expansion despite the failed structured pilot.
The [new contract](../../docs/specs/task09e1_luna_structured_dev6_v1.md) superseded
that pilot's stop boundary for two fresh claims-only passes; its failed outcome
and original criteria remain unchanged. Both arms completed all 323 original
claim slots, retaining the exact 166 Dev3 payloads and adding 157 from C001/C019/
C056. No conclusion or abstention inference ran.

The [outcome](../../docs/specs/task09e1_luna_structured_dev6_result.md) records
313/323 baseline agreement versus 315/323 structured. Added cases tie 153/157;
non-pilot payload slots tie 290/294. Nine improvements and seven regressions leave
a net gain of two, which disappears under equal exact-payload-group weighting.
No default is promoted. Source review retains concrete scope omissions and
over-rejection of contextually bounded summaries without changing labels.

All 646 generations validated with exact count parity, no replay/retries and
intact budget caps. Estimated cost $0.312412950, native payer developer. Focused
281 and offline guard 13 tests pass; make fix/check retain 4,259 passed, one
skipped and only three historical Task 06G failures. Prior pilot seal and earlier
preservation audit remain intact. No full-19/test/later-task work, commits or pushes.
