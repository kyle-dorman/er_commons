# Task 11B — Build the Luna generation runner

Status: Complete with documented limitations (2026-10-17); refreshed from accepted 11A before implementation.

## Abstract

Build one reproducible Luna target runner that answers from complete supplied evidence.

## Goal

Generate schema-valid cited reasoning and conclusions while retaining invalid outputs and exact delivery evidence.

## Inputs

Accepted [11A panel](11a_select_development_panels.md), Task 10 packets/schema, existing structured-answer contract and native Inspect/provider interfaces in the judge guide.

## Outputs

A narrow package-backed runner and command; initial prompt and output schema; pinned Luna provider/model identifier and generation settings; saved raw responses, parsed candidates, request receipts and explicit failures.

## Plan / spec requirement

Use this contract as the brief plan; record concrete interfaces and limits before implementation.

1. Resolve Luna to an exact available provider/model identifier; record it separately from judge models. Reuse the maintained provider adapter and native Inspect rather than adding a runner framework.
2. Render only the question and complete supplied passages into a zero-shot request. Request supporting points, applicable qualifications, citations and conclusion using the accepted answer contract; include abstention behavior.
3. Validate schema and citation IDs and render readable citation labels deterministically. Keep raw malformed/truncated responses; do not repair answers invisibly or silently drop failures.
4. Verify full rendered request plus output reserve against the selected model context. No truncation, compaction or evidence omission to force a fit; record counting limitations explicitly and block unverified dispatch.
5. Bind prompt, model/settings, schema, packet, request, answer, run and repeat identities. Make retries explicit, bounded and restartable; distinguish transport retries from fresh answer attempts.
6. Run offline fixtures first. Any live smoke run uses only the first three IDs with declared call/output limits. Prompt iteration begins only after 11C evaluation is ready.

## Accepted execution contract

11A fixes C041, C017 and C019 in that order for this smoke run. Its six-question
panel and all Task 10 artifacts remain immutable. Verify the panel manifest's
Task 10 completion, development file and selected record hashes before rendering;
read only the development target file, never evaluator/reference or test content.
Only the strict payload (question and every complete passage/table) enters messages.

Use Inspect 0.3.278's native OpenAI Responses provider and the existing provider
adapter with a separately bound target configuration: `openai/gpt-6-luna`, medium
reasoning, no reasoning summary, standard/default service tier, no tools, no
storage, no truncation, no result cache. The official model page exposes this
alias, not an immutable dated snapshot; retain the returned model identifier and
state that reproducibility limitation. Freeze a generic v1 prompt and the existing
structured-answer shape before offline fixtures; no prompt changes after smoke.

The prospective smoke ceiling is **three generation attempts and three token-count
requests**, one of each per selected case, **zero transport retries and zero fresh
answer retries**, sequential dispatch, and **4,096 output tokens per generation
including reasoning**. A request has a 120-second timeout; the smoke timebox is
15 minutes. Maximum spending is **USD 1.00**. Before each dispatch reserve its
worst-case liability, including failed/uncertain attempts; do not reclaim uncertain
spend. With an input ceiling of 32,768 tokens and conservative rates of USD 0.25/M
input (including cache-write liability) and 0.75/M output, the three generation
attempts reserve at most USD 0.033792. These rates exceed the verified standard
short-context prices; tools and premium service tiers are disabled. Official docs
do not publish count-endpoint billing. Do not call it free: reserve USD 0.30 per
count (USD 0.90 total), exceeding a full 1.05M-token context at the conservative
input rate. Total reserved liability is USD 0.933792. This is an explicit accounting
allowance, not a provider-enforced billing guarantee; actual count cost remains
unknown and must be reported separately. The endpoint performs counting only and
cannot generate an answer. Never refund that allowance based on absent usage.

Count the actual native request, including schema and message framing, using the
provider-supported count endpoint. Bind the count request to the generation body,
then check input plus output reserve against the documented 1,050,000-token
context and the stricter smoke input cap. Unsupported counting, mismatched requests
or missing credentials are explicit provider blockers; never use character counts
as proof. Preserve native request/response bodies, raw text, parsed candidates,
usage, failures, and checksummed request/candidate/run identities. A saved request
is preparation evidence; a successful provider response is delivery evidence.

Write the run manifest and limits before any network dispatch. Resume reuses exact
completed artifacts only; a dispatch with uncertain completion stays failed/unknown
and is never silently resubmitted. Keep every selected case in the summary,
including blocked or unattempted cases. Offline fixtures precede live execution.
No judges, prompt cycling, locked-test/reserved access, or 11C work is authorized.

## Research / learning checkpoint

Reviewed installed Inspect 0.3.278 and OpenAI SDK interfaces before implementation.
The native Inspect counter can omit structured-output configuration and fall back
to a local estimate. Use a narrow SDK HTTP hook to capture the native outgoing
body and call the maintained count endpoint with equivalent input-bearing fields;
Inspect still owns generation and the SDK owns transport. This avoids a duplicate
request renderer or a custom HTTP executor. SDK response hooks retain raw failures.

Primary sources reviewed 2026-10-17:
[Luna model](https://developers.openai.com/api/docs/models/gpt-6-luna),
[token counting](https://developers.openai.com/api/docs/guides/token-counting),
[count API](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count),
[Inspect models](https://inspect.aisi.org.uk/models.html).
Structural validation establishes shape and resolvable citation IDs, not factual
support or answer quality. An input file proves preparation only; exact request
and response receipts establish what crossed the provider boundary. The model
alias and undocumented counting charges limit exact reproducibility and billing
claims even when local identities and call counts are fixed.

## Validation

Cover target/reference isolation, citation resolution, context overflow, malformed/truncated output, identity preservation and resume behavior. Run make fix, make check and git diff --check.

## Acceptance criteria

One bounded smoke run or explicit provider blocker is recorded; successful completion requires reproducible saved candidates and receipts consumable by 11C, without silently excluding failures.

## Review pass

Bounded review of prompt isolation, complete evidence delivery and replay identities.

## Non-goals

No provider/model search, retrieval, judge-policy changes, six-question prompt cycling or locked-test calls.

## Shared boundaries

Follow the [Task 11 umbrella](11_build_and_freeze_target_generation.md). Use only
the 19 development cases; no locked-test or reserved judge-challenge access.
Preserve Task 10 packets and frozen A/G/S/C judge policies. Keep references and
judge feedback outside target requests. Generated runs and reports belong under
`ER_COMMONS_DATA_ROOT`, with exact input/configuration hashes and fresh namespaces.


## Outcome

Completed the narrow native Inspect/OpenAI Luna runner and one frozen three-case
smoke. All three candidates passed the pinned output schema and case-local citation
checks; complete request bodies, exact provider counts, raw responses, candidates,
failures/recovery fixtures and identities are preserved. The
[result pointer](../../docs/specs/task11b_final_result.json) binds the run, source
snapshot, review and validation evidence. No provider blocker occurred.

Current command (same namespace performs verified replay without calls):

```bash
make generate-luna-smoke \
  GENERATION_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_11/11b_smoke_20261017_v1"
```

`target_generation.py` owns the runner, `configs/task11b_luna_v1.json` its settings,
and `docs/prompts/task11b_luna_v1.md` the unchanged initial prompt. The strict schema
reuses the established answer fields, excludes model-authored source locators, and
is saved and hashed per run. Readable labels are derived from supplied passage
metadata without altering the candidate. Native SDK hooks count the exact
serialized request before generation and preserve full HTTP response bodies.
Both retry layers are disabled. Atomic attempt claims and checksummed completion
inventories prevent duplicate dispatch; interrupted attempts remain explicit.

| Case | Exact input tokens | Output tokens including reasoning | Result |
| --- | --- | --- | --- |
| C041 | 1,149 | 944 | Structurally valid; citations resolved |
| C017 | 3,026 | 1,040 | Structurally valid; citations resolved |
| C019 | 6,508 | 411 | Structurally valid; citations resolved |

The smoke used **three generation calls, three count calls, zero retries and zero
judge calls**. Provider input usage, including cache-write tokens, exactly matches
each preflight count. Generation cost estimated from reported usage and dated
standard rates is **USD 0.00253265**; this is not a billing invoice. Counting cost
remains unknown, with USD 0.90 reserved. Total prospective reservation was
USD 0.933792 against the USD 1 accounting ceiling; no provider-enforced total
billing guarantee is claimed. Returned model IDs were `gpt-6-luna`; the documented
alias does not guarantee an immutable backend revision.

Validation: fifteen invented offline fixtures passed before dispatch, including
real native serialization through a mocked SDK transport, complete text/table
preservation, schema/citation/reference checks, unavailable counting, overflow,
malformed/truncated output, transport failures, deadline and resume behavior.
`make fix`, `make check` (**4,021 passed, one skipped**) and `git diff --check`
passed. A second invocation reused the sealed smoke with zero new HTTP calls.
The offline smoke audit verified complete payload/schema equality, count/usage
agreement, hashes, limits and raw-answer/candidate equality.

Bounded independent reviews covered native interoperability and the request,
context, citation, reference and restart boundaries. Missing schema import,
Inspect-added control fields, pre-count deadline, provenance hashes, failure
causes, global preflight stop and atomic attempt claims were resolved before
live dispatch. The remaining counting-price uncertainty is recorded explicitly.
The external validation directory preserves the pre-dispatch source/contract
snapshot and detailed logs; frozen Task 10 inputs and the six-question panel are
unchanged. No locked-test or reserved-challenge content was opened.

This is a runner/delivery qualification, not a semantic or baseline-quality claim.
No judges, prompt iteration or 11C work ran. Next: refresh provisional 11C using
these exact saved candidates and receipts before evaluation integration.
