# Task 13A — MiniMax cloud compatibility and locked comparison

Status: closed with all 90 slots attempted (2026-10-20). Final publication
preserves 54 complete evaluations, 29 invalid outputs and seven original request
failures. Task 13 remains closed; Tasks 14–15 provisional.

## Archive designation (2026-10-21)

The user ended MiniMax exploration and designated this as a side experiment.
Its code, receipts, sealed reports and galleries are historical audit material,
excluded from presented benchmark results, model comparisons and the Task 15
writeup. Luna and Haiku remain the presented models. Nothing below authorizes
further dispatch, continuation or function-calling work. Historical outcomes
remain intact; the archive designation does not revise their measurements.

## Abstract and goal

The user authorized trying Ollama Cloud `minimax-m3.1-flash` on the same 30
questions, three fresh answers each (90 slots), as a separate model condition.
First check the installed Inspect path and output compatibility on invented and
development-only inputs. If the format cannot be made usable through a narrow,
explicit transport adapter, preserve the blocker for a function-calling followup
tomorrow; do not silently transform prose into substantive answers.

## Inputs and outputs

Reuse Task 13's sealed inputs, 11E target prompt/context, 09G judges and current
Task 12 reporting definitions. Preserve all earlier artifacts. Fresh artifacts
belong under `pipelines/brisbane_baylands/task_13a/`; development probes and final
90-slot test publication stay separate. Do not read reserved judge challenges.
Actual model identity, native requests/responses, usage, settings and any output
format difference must be explicit. No claim that the new provider reproduces
Luna/Haiku reasoning settings exactly.

## Limits and authorization

The original $10 cumulative monetary ceiling includes Task 13's known
$1.004175550 plus accepted unknown OpenAI count fees. New work must reserve
against the remaining known allowance ($8.995824450), including probes. Ollama
lists this model as free through 2026-10-22 23:59 UTC; also reserve at its posted
ordinary rates ($0.15/M input, $0.60/M output) conservatively. Stop before the
promotion expires. Retain the specific OpenAI count-fee exception only.

Use at most 10 concurrent requests globally, zero retries/replacements,
100,000 input tokens, 12,288 target output tokens, 4,096 judge output tokens,
900-second request timeout, 30 judge items per answer and 5,400 seconds active
evaluation per answer. New condition has a six-hour dispatch window; original
Task 13 clock and receipts are unchanged. Preserve all 90 planned slots if
execution stops. Unknown attempts are never automatically replayed.

Compatibility stage: at most two invented protocol probes and one predetermined
development question (C041), no judges, serial requests, at most $0.10 reserved.
Do not inspect test answers to choose formatting or model settings. Any extension
beyond that stage needs its own validated frozen preflight, independent review,
and cumulative accounting before test dispatch.

## Research and plan

1. Inspect the installed Inspect AI Ollama provider and official cloud/API docs.
2. Check native JSON-schema support with an invented fixture. If unsupported,
   test the unchanged answer schema delivered explicitly on development C041;
   validate exactly, retaining malformed output. No semantic repair or retries.
3. If compatible, implement narrow provider/runner integration with durable
   request reservations, frozen settings, exact identities and offline fixtures.
4. Run focused tests, make fix, make check, diff checks and bounded independent
   preflight review before the 90-slot run. Publish sealed report/gallery and
   independent final audit. If incompatible, record a concrete restart handoff.

Sources: https://ollama.com/library/minimax-m3.1-flash,
https://docs.ollama.com/cloud,
https://docs.ollama.com/api/openai-compatibility,
https://docs.ollama.com/capabilities/structured-outputs.
Cloud docs currently say structured outputs are unsupported; installed Inspect
support alone does not establish endpoint support. Validate the actual wire.

## Acceptance and non-goals

Either publish all 90 accounted slots under a separately frozen compatible
condition, or preserve a concrete compatibility blocker and tomorrow's next step.
No benchmark prompt tuning, favorable repeat selection, judging changes,
function-calling implementation tonight if compatibility fails, commit or push.

## Compatibility checkpoint

Both live requests succeeded through Inspect's public OpenAI-compatible provider:
an invented schema fixture, followed by predetermined development C041 using the
unchanged target prompt, payload and full native answer schema. C041 passed strict
answer/citation validation without repair. The cloud documentation's generic
unsupported-structured-output statement differs from this observed endpoint
behavior; this establishes tested compatibility, not proof of server-side schema
enforcement. Preserve malformed answers if they occur in the test run.

The tested format uses native `response_format` (`json_schema`), schema name
`compatibility`, and default strict flag, with `reasoning_effort=medium` and
12,288 output tokens. Freeze these exact settings before test. No schema-in-prompt
fallback or function call was needed. Probe artifacts and original no-wire
Inspect-construction failure are sealed separately under `task_13a/`.

The provider has no exact input-count route. Use a conservative serialized UTF-8
byte bound plus 4,096 bytes of template allowance, reject above 100,000, reserve
100,000 input tokens at ordinary rates, and verify returned usage. This is an
explicit conservative proxy rather than a verified provider tokenizer count; it
can reject inputs unnecessarily and does not prove the provider's hidden template
size. Preserve this comparability limitation. Native prompt/context and semantic
answer schema remain unchanged.

The additional condition reserves from $8.995824450 remaining known allowance;
compatibility requests settled at promotional zero with verified usage. Global
remaining ceilings are 1,354 judge requests and 1,354 count requests after prior
Task 13 usage; 90 new target generations are explicitly authorized. All requests
share the dispatcher. No prior ledger or six-hour clock is reset.

## Execution preflight

The new adapter is limited to Ollama generation; unchanged native judge execution
and the durable shared dispatcher handle scoring. The existing slot and reporting
functions gained explicit delivery/generation injection points without changing
score definitions. A separate runner binds all 90 slots and the cumulative budget;
a separate reporting adapter verifies the new model's actual native delivery.

Full validation passed: 4,366 tests, one skipped, 105 upstream warnings; make fix,
make check and whitespace checks passed. Offline cases cover native delivery,
invalid output, rate limits, usage/accounting failures, zero retries, model-client
isolation, concurrent cap admission and exact evaluation/report replay. Independent
review caught and resolved a waiting-worker cap race and a report byte-comparison
error before dispatch.

The frozen preflight is `task_13a/locked_test_20261020_v1/preflight.json`, SHA-256
`c449247bdbd54d00ee22b145440090065c49a387723a3f9b8b894549a2f91cf7`.
It binds the complete original Task 13 accounting, successful development probe,
implementation and all input projections. Maximum conservative input bound is
98,434 against 100,000. Exact review and validation receipts remain with the run.

## Outcome — sealed incomplete checkpoint

Native JSON compatibility succeeded; no function-calling workaround was needed.
The run stopped at **Per-answer evaluation deadline exhausted** after Ollama
concurrency rejections reduced the shared dispatcher from ten to one. Live queue
time remained counted; no deadline, prompt, output limit or score was changed.
This is an incomplete test publication, not a completed model comparison.

All 90 planned slots remain: **15 completed, 14 evaluation-incomplete, nine
generation-failed and 52 not dispatched**. The 36 actual generation requests
produced 29 HTTP 200 responses and seven HTTP 429 concurrency errors. Of the
29 delivered answers, 23 passed strict validation and six were invalid or
truncated. Two generation-failed labels were blocked before any wire request;
they are not additional provider failures. No attempted request was retried,
replaced or selected away. All in-flight requests settled before sealing.

The [result pointer](../../docs/specs/task13a_result.json) binds the sealed run,
preflight, development compatibility check, offline reporting and independent
audits. Under the external Task 13A root, `locked_test_20261020_v1/` preserves
raw receipts and all slots, `locked_reporting_20261020_v1/` holds replayed tables,
and `test_30_review/START_HERE.html` presents seven PNG/SVG figure pairs and eleven
CSV tables with incomplete-coverage disclosure. All 30 questions stay together;
original Luna/Haiku results, development and synthetic judge diagnostics remain
separate. The offline publication replayed all 29 delivered answers with network
connections disabled; principal figures were visually checked.

There were 154 judge requests and 154 count requests. Additional known cost is
**$0.075034840**, plus 138 accepted unknown OpenAI count fees. The seven rejected
generation requests retain **$0.156609600** conservative liability rather than
assuming free failures. Cumulative known cost including original Task 13 is
**$1.079210390**; cumulative planning liability is **$1.235819990** within the
original $10 allowance. Unknown counting fees remain explicitly excluded from
verified totals.

### Historical checkpoint handoff — superseded by continuation below

The blocker is execution throughput and expired active evaluation deadlines,
not inability to produce the answer schema. Before continuation, define and
validate provider-specific concurrency and queue scheduling under the global
ceiling. Any relaxation of expired per-answer time limits needs explicit user
authorization; do not silently reset clocks or exclude live queue time. Reuse
saved answers/judgments and dispatch only verified untouched requests. Keep the
seven attempted failures and six invalid outputs, unless a separately authorized
new experimental condition explicitly changes the no-replacement protocol.
The remaining $10 allowance and original six-hour clock must carry forward for
a continuation; do not treat a fresh directory as fresh spending authorization.
No further remote calls, commit or push were performed after the stop.

## Authorized deadline continuation

The user explicitly approved tripling the per-answer deadline from 1,800 to
5,400 seconds and continuing. The continuation preserves consumed evaluation
time, every attempted request, cumulative liability and the original six-hour
dispatch clock. Frozen prompts, settings, judges and scoring remain unchanged.
A fresh linked snapshot and independent preflight bind this operational change.
Saved partial evaluations run before untouched slots, with one answer worker
matching the dispatcher's retained concurrency of one after rate-limit events.
This prevents new generations from filling the queue ahead of saved judgments.

The previously approved administrative-pause exclusion applies to active evaluation
time: carry each partial answer's elapsed time through the later of the sealed
stop and last settled request, then exclude only the interval to one durable
global continuation restart. Waiting after that restart counts, including time
queued behind other partial answers. This exclusion never extends the original
six-hour dispatch window.

## Final continuation outcome

The approved 5,400-second active evaluation deadline completed the remaining
work without another stop. All eight saved partial evaluations finished; all
54 verified untouched generation slots were attempted once. Final accounting is
**90 planned/attempted slots: 54 completed evaluations, 29 invalid or truncated
outputs and seven original HTTP 429 failures**. No untouched slots remain.
Invalid outputs remain automatic failures under the frozen rules; they are not
repaired, replaced or silently treated as valid judge inputs.

The continuation is `task_13a/locked_test_continue_20261020_v2/`, completion SHA-256
`ab07460228fedad691586a1cca2d2defb15ee624f08db98d77b6af38458a52f2`.
Its preflight is `d21d962e04b100ce28f3ed1fad9b3fec197027f09bbb25a3351f068245a9c7b2`.
The original preflight and run identities remain unchanged inside the linked
snapshot. Independent preflight and final native audits verify all prior request
bytes, original six-hour dispatch clock, copied liabilities, zero retries and
serial continuation admission. The administrative pause excluded 4,156.808
seconds; live elapsed time carried forward. Last admission was 14,331.873 seconds
after the original first dispatch, within 21,600 seconds.

Final Task 13A requests total **90 generation, 468 judge and 468 count**. All
682 new continuation requests succeeded at the transport level, with a peak of
one concurrent request. The full ledger has 1,019 successful native responses
and seven preserved 429 responses; no unsettled attempts remain. Known Task 13A
charges total **$0.215831260**; the seven original failures retain **$0.156609600**
planning liability. Including original Task 13, known charges are **$1.220006810**
and cumulative planning liability is **$1.376616410**, below the $10 ceiling.
Task 13A adds 414 unknown OpenAI count fees under the accepted exception.

The [current result pointer](../../docs/specs/task13a_result.json) binds the final
sealed run, native audit, report and reporting review. The separate final report
is `task_13a/locked_reporting_20261020_v2/`; the gallery is
`task_13a/continued_publication_20261020_v2/test_30_review/START_HERE.html`.
It contains seven PNG/SVG figure pairs and eleven CSV tables covering all 30
questions and all three planned repeats. The original stopped run, report,
gallery and result pointer snapshot are preserved. Development and synthetic
judge diagnostics remain separate from test outcomes.

Offline publication replayed all 83 delivered answers with network access
blocked. The frozen joint outcome is **26 pass, 57 fail and seven unavailable**
out of 90 planned slots; invalid outputs contribute automatic failures. This
publication does not imply 90 fully evaluated valid answers or establish a
ranking against the separately published Luna/Haiku conditions.

Validation passed: **4,383 tests, one skipped**, make fix, make check and whitespace
checks. Eight continuation fixtures cover attempted-failure preservation,
zero-wire eligibility, inherited clocks, partial-first dispatch, immutable
history and duplicate-claim rejection. Principal final figures were visually
checked; independent reporting review verifies the complete denominator and
unchanged reductions. No commit or push. Tasks 14–15 remain provisional.

The operational lesson is to retain admission history and active time when
resuming, while preventing queued fresh generations from starving saved judges.
A larger deadline alone must not reset spending, request identity or elapsed
work. This narrow continuation is deliberately fail-closed after an interruption;
a further recovery would require a separately audited snapshot, never replay of
an uncertain request.
