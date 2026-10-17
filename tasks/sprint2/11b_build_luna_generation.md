# Task 11B — Build the Luna generation runner

Status: Provisional; refresh from accepted 11A before execution.

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

## Research / learning checkpoint

Inspect the existing provider implementation, then current maintained structured-output and logging documentation if needed. Explain schema validation versus semantic correctness and why a saved packet is not proof of delivery.

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
