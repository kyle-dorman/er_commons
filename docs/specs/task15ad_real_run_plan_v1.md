# Task15AD real-answer run: authorized contract

Status: [round complete, awaiting user review](task15ad_real_run_result.json);
294 answers and3331 grading calls cost an estimated$1.776348480 under the$40 cap. S v9 is [accepted with the C028 limitation](task15ad_s_v9_acceptance.json).
No commit or push. The prior qualification caps do not authorize this new run.

## Inputs and scope

Use current15AC:49 questions,19 development/30 test,125 required and211 optional
reference points. The accepted15Z retrieval mapping remains a separate sidecar.
Reuse the sealed15S evidence packets (212 passages), including C054 supplements;
update C034's question to include construction and post-development scope. Existing
passages cover both. Preserve the existing neutral EIR question/locator projection.
Target packets contain only questions and passages; evaluator/reference mappings
remain separate. Preserve previous answers as historical comparisons only.

Generate294 fresh answers:49 questions × Luna/Haiku ×3 answer repeats. Medium
reasoning,12288 output tokens, concurrency16. Preserve baseline native generation
cache behavior (Luna cache key with default retention; Haiku5minute); result cache off.
No automatic SDK, transport or semantic retries. Do not promote the16K/high experiment.

## Grading

One judgment per eligible answer/component; answer repeats are not judge repeats.
Use accepted A/G unchanged, C Luna/v6 with6144 output tokens, S Haiku/v9 with4096,
and15Y Luna/medium/4096 diagnostic coverage. A/G retain Luna/medium/4096. Coverage
uses its accepted24h cache setting and default service tier.

A-first routing, invalid-answer handling and A/G/S/C overall gates stay unchanged.
S receives original conclusion plus supporting points and qualifications; optional
context excluded. C receives only the conclusion against current required/optional
references. G evaluates supporting/qualification points against their cited evidence.
Coverage gets one required point plus candidate supporting points, with conclusion,
qualifications and other verdicts hidden. It never adds an overall pass requirement.

Maximum fixed grading slots:294 A +294 C +294 S +750 coverage =1632, plus
answer-dependent G. Carry skipped/invalid slots explicitly. Do not fabricate labels
for synthetic scorers when dispatching real judgments. New coverage helpers bind
answer identity/hash and join C-missing/coverage/G-witness diagnostics independently
of benchmark pass status. Callers must supply validated same-answer C/G receipts.

## Authorized budget and admission

The user approved a$40 cap for this new run only. Track actual estimated charges
from returned usage, temporary holds for in-flight calls, and unresolved liabilities
separately. Settle each verified response and release its unused hold. Actual
charges plus outstanding holds must remain within$40 before admission. Prior
qualification reservations are historical accounting records, not new-run spending;
the earlier proposed cumulative$120/$90 caps are superseded for this run.

Reserve complete native JSON UTF-8 bytes plus1024 framing as an input-token upper
bound, plus the full output limit, before every wire call. Do not clip bounds.
Ceilings include framing:200000 for generation/A/G/C/coverage;100000 for S.
The largest prepared generation bound is132034. Use conservative per-million
input/output rates OpenAI .25/.75 and Anthropic .625/2.5, retaining full reservations
for failed or uncertain attempts. No remote token-count endpoint or new unknown
counting-fee exception. Earlier counting-fee liabilities remain historical.

This is a bounded pool, not a guarantee of completing arbitrary generated answers.
Stop before exceeding any cap or bound. Preserve the existing64 A/G/S/C request
ceiling per answer (at most61 G candidates); coverage has its separate required-point
slots. An oversized answer stops for review rather than silently dropping points.
Keep output/version/source/schema gates and record every admitted attempt. No
automatic retry, relabeling, prompt tuning or replenishment.

Fresh pricing verification: [OpenAI Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
and [Anthropic Haiku](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
Conservative rates cover documented long-context/cache-write rates; estimates are
not invoices. The external preparation's budget_proposal.json preserves the superseded proposal;
the new run's inputs/authorization.json owns current spending authorization.

## Execution and review gates

Preparation provides294 slots,98 exact native generation templates, source hashes,
reference mappings, strict grading/coverage projections and independent audits.
Judge packets are necessarily materialized after fresh answers exist. The old paid
runner's global reservations/count endpoint must not be used unchanged: activation
must bind this reviewed proposal to a fresh create-only runtime ledger with native
byte admission and unlabeled judge dispatch. Preparation itself did not authorize calls; the subsequent user instruction does.
Before the first paid call, verify its implementation and source/template hashes
against this plan; no further user decision is needed for routine faithful wiring
under the approved plan and$40 cap. Stop if substantive settings must change.

Generate once, freeze answers, then materialize and audit actual judge packets and
remaining budget before grading. Preserve invalid/failed answers and judgments;
never silently regenerate or repair them. Stop for integrity/accounting/provider
failures requiring review, and after the round for human acceptance.

Report19/30 separately, model/answer-repeat consistency, C model/computed agreement,
coverage/C omissions and witness grounding, invalid/skipped slots, costs and latency.
Review every failure plus12 deterministic pass controls: three distinct cases per
model/split, selected by sorted SHA256 of `15ad-pass-v1|slot_id` among passes.
If a stratum has fewer eligible cases, review all and report the shortfall. No
post-result reference changes. All49 references have curation exposure; no pristine
held-out claim. MiniMax, reserved challenges and agentic search remain excluded.
