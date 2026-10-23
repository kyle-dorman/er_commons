# Task15V — High-reasoning six-question comparison

Status: complete; experimental comparison, no default promotion.

## Goal and authorization

User requests high reasoning for Luna and Haiku on the fixed six development
questions. Generate three fresh answers per model/question (36 total), using
high generation effort. Preserve the medium baseline, questions, evidence,
Task15R prompt, schema and model IDs. Full A/G/S/C evaluation retains the tested
judge models/effort and current C v6 with6144 output tokens; baseline C used4096,
so disclose that execution-limit difference. No other questions or reruns.

## Budget and boundaries

Count prior retained liability$2.629365365 against the existing$40 authorization.
Use a fresh ledger with at most$37.370634635 remaining, no automatic retries,
16 concurrency,12288 generation tokens and4096 A/G/S tokens. Preserve uncertain
charges and explicitly unknown token-count fees. No commits/pushes, no labels,
prompts or frozen artifacts changed; exclude MiniMax/reserved challenges.

## Plan / outputs

1. Verify official reasoning controls and native configuration; narrowly support
   explicit high generation effort without changing defaults or judge effort.
2. Bind six cases C014,C017,C019,C037,C041,C056,36 slots, source seals, prompts,
   schema, prices and implementation. Independent preflight before paid calls.
3. Execute once per slot with receipts, bounded ledger and complete evaluations.
4. Compare current medium versus high per-question and pooled C/A/G/S/joint,
   cost and latency; review changes/failures without tuning or rescoring.
5. Independent native/provenance/accounting review, checks, seal and result pointer.

## Research / learning and validation

OpenAI reasoning docs describe reasoning.effort; Anthropic effort docs describe
output_config.effort with adaptive thinking. High is a provider-specific setting,
not an equal reasoning budget across models. Retain output caps to isolate effort
and report truncations if any. This small reused development sample and historical
medium comparison cannot establish a broad or causal performance improvement.

Sources: https://developers.openai.com/api/docs/guides/reasoning and
https://platform.claude.com/docs/en/build-with-claude/effort . Verify exact native
requests, no label leakage, no judge-effort changes; focused tests, make checks,
independent preflight/results review and git diff --check.

## Outcome

The [result](../../docs/specs/task15v_high_reasoning_result.json) selects the sealed
36-attempt experiment and medium/high comparison.33 answers have complete A/G/S/C;
all three Haiku C014 answers reached the unchanged12288 generation-token cap.
They remain unavailable, not semantic failures or rerolled answers. All33 valid C
model/aggregate verdicts agree. No judge setting/prompt/reference was tuned.

Luna C and joint passes both improved11/18 to14/18; G improved15/18 to17/18.
C017 and C056 each improved1/3 to3/3, offset by C014 declining1/3 to0/3.
Haiku C was12/18 medium versus11/18 planned high (11/15 completed); its five
mutually completed questions tie11/15 at both settings. C056 gained one pass and
C041 lost one. Haiku joint passes increased4/18 to6/18 despite the truncations.

Higher Luna effort restored some required coverage and flood-baseline caution,
but did not repair C014's missing regional/local distinction. Haiku added some
self-conflicting qualifications; exact reasons and uncertainty are in the outcome
review. These are fresh random samples on six exposed development questions,
not a general or causal estimate. Baseline C cap4096 versus new6144 is disclosed.

New configured usage/liability$0.253339635; cumulative retained liability
$2.882705000 under40, plus accepted unknown counting fees (300 additional calls).
Generation-only costs: Luna$0.019840920 medium versus$0.033059355 high;
Haiku$0.056630940 versus$0.093952555. Median generation request time increased
11.62s to30.97s for Luna and15.91s to30.30s for Haiku. Timing includes returned
truncated attempts and excludes counting/judging; cache usage affects cost.

Validation:85 focused runtime tests; make fix/check passed4550 tests with1skip;
independent preflight/native/schema/payload/accounting/replay audit passed, all
source bindings unchanged, and documentation diff checks passed. Actual native
requests confirm high generation and medium judges. Original medium results and
all earlier artifacts remain immutable; no commits/pushes or Task16 activation.

Recommendation: Luna high is promising on this small set, with higher latency;
Haiku high has no conclusion gain on comparable completed questions and needs a
larger output budget to evaluate C014. Neither finding automatically promotes a
default or authorizes a broader run. No further calls selected.
