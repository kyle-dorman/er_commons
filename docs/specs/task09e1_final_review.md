# Task 09E.1 final provider and maintainability review

Independent review of the integration, October 11, 2026. The reviewer authored
provider mappings, so provider self-checks below are distinguished from independent
inspection of the runtime, safety, audit, panel loader and analysis modules.
No cloud calls were made.

## Findings and dispositions

1. **Schema portability — fixed in provider mapping.** The shared conclusion
   schema uses positional `prefixItems`. OpenAI's documented subset does not list
   this keyword; Anthropic explicitly disallows array constraints beyond
   `minItems` of zero or one. The provider transforms now use an `items.anyOf`
   union and an explicit original-ID order description; the local semantic
   validator still enforces exact ordered coverage and rejects duplicates.
   Zero-point arrays have an item schema. OpenAI retains supported min/max item
   bounds; Anthropic moves unsupported bounds to descriptions. OpenAI removes
   defaults and requires fields while allowing empty diagnostics. Anthropic
   explicitly supports defaults and retains them. This changes wire hashes;
   regenerate the offline audit after integration.
   [OpenAI supported schemas](https://developers.openai.com/api/docs/guides/structured-outputs),
   [Anthropic limitations](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).
2. **Native prompt semantics — verified integrated.** Both audit and runtime select
   `native_stage_prompt` for decision conditions. Generated-JSON and quotation
   directions no longer enter native decision state. All provider conditions
   still receive the same semantic stage payload and binary point projection.
3. **Restart budgets — verified corrected.** The CLI creates a new output
   namespace and native `evaluate_comparison` rejects a pre-existing request
   namespace. This avoids resetting currency, request, output and wall-clock caps
   during live continuation. Completed receipt reuse remains available for
   controlled offline fixture replay; uncertain attempts are not replayed.
4. **Jev's second context limit — verified corrected.** Runtime uses
   `condition.state_question_limit` (32,000), rather than a hardcoded 32,768.
   The endpoint remains blocked without a qualified exact renderer/counter.
5. **Live manifest coverage — verified corrected.** Offline and live identities
   now share `implementation_identity`, binding package source, `uv.lock`, and
   installed Inspect/httpx/Pydantic/ijson versions.
6. **Output cap receipt parity — verified added.** Native generation output above
   its configured cap is classified as `provider_usage_mismatch`, and the scorer
   halts further dispatch. Raw responses and worst-case reservations remain.
7. **Cap exhaustion — verified corrected.** Request, output and wall caps are
   checked before counting; exhausted cap outcomes halt further condition stages.
   Currency reservations still occur before inference, after exact counts exist.
8. **Usage before semantic parsing — verified corrected.** Runtime records native
   usage and checks input/output parity before parsing model decisions. Malformed
   judgments retain billed usage; counter mismatches halt subsequent dispatch.
   Missing or malformed usage becomes a halting provider-contract failure. Raw
   receipts and reserved cost remain preserved. Regression cases cover malformed
   decisions with valid usage and with mismatched input usage.

## Evidence and acceptance boundaries

Provider regression tests: **92 passed**, including all seven wire shapes,
strict probabilities/ties, refusals, missing/duplicate IDs, malformed envelope
shapes, native cache buckets, evidence-first serialization, exact count request
binding, strict-schema transformation, and zero/one/multiple review arrays.
Provider module passes strict mypy and Ruff.

The module split is understandable: panel binding, semantic validation, wire
mapping, budget/receipt safety, Inspect stage graph, offline audit and post-run
analysis have distinct responsibilities. No new workflow engine or runtime SDK
was added. Condition configuration exposes capability blockers and dated rates.
Native fixtures establish mapping behavior, not endpoint availability or accuracy.

The panel loader verifies the frozen manifest and selected records, preserves
original source/origin bindings and avoids loading expectations for request
construction. Post-run proposed-label analysis is a separate module; its outputs
must retain the warning that synthetic proposals are not ground truth. The cache
probe uses a separate protocol and excludes repeated samples from evaluation.

Five cloud conditions and local Clef remain counter/runtime blocked; OpenAI
Responses has a documented exact counter but still needs credentials and actual
endpoint qualification. Byte-prefix measurements do not prove token eligibility;
unknown offline cost estimates correctly remain unavailable. No live cache savings,
model-quality improvement or seven-provider cloud readiness is established by this
review. Regenerate code-bound audits after the final fixes, then run the required
repository validation and record remaining blockers in the task outcome.

Cross-module regression after the schema transformation: provider, Inspect, run
and safety suites **178 passed** after the final accounting changes. The cloud handoff's caps, environment names,
separate smoke/cache/run modes, and blocked-provider statements match the reviewed
interfaces. Integration review is approved within these offline acceptance
boundaries; no unresolved review findings remain. Repository-wide validation and
final audit regeneration remain the main agent's release checks.
