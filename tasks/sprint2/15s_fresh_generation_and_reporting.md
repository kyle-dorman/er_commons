# Task15S — Fresh generation, full evaluation and reporting

Status: execution and reporting complete; results ready for user review.

## Abstract and goal

Run the revised generation prompt against the approved structured references,
then publish a fresh comparison. Preserve historical runs and distinguish
19 development questions from30 test questions; this is not pristine held-out
qualification because the reference cleanup exposed all49 labels.

## User decisions and inputs

The user authorized independent execution of steps8–9 with a separate **$40**
total budget (increased from the proposed $20). Generate three fresh answers per
question from Luna and Haiku across all49 questions:294 answer slots. Use medium
reasoning and high concurrency, up to16 per model. Evaluate full A/G/S/C using
the unchanged A/G/S selection and one Luna/v6 C judgment per answer.

Inputs: Task15R prompt and unchanged shared Baylands overview; Task15M approved
49-reference overlay (including revised C040 question and C054 research); existing
evidence-only target preparation and automatic/A/G/S contracts. Task15Q accepted
v6 qualification selects the C prompt/schema. No reference answers enter target
requests. The separate synthetic experiment budget is historical, not this cap.

## Outputs and plan

1. Audit approved inputs and existing native execution/reporting interfaces.
2. Prepare a fresh versioned run configuration and role-separated inputs. Pin
   questions, evidence, references, prompt/schema, models, reasoning and split.
3. Validate offline and independently review isolation, budget and integration.
4. Execute294 fresh answer slots, then full evaluation, with bounded concurrent
   dispatch, receipts, usage and conservative liability accounting before calls.
   Preserve invalid/error attempts; no semantic retries or prompt/label tuning.
5. Produce separate development/test tables, charts and review records. Report
   model-final and computed C, automatic/A/G/S/C and joint outcomes, cost, latency,
   repeatability and grouped failures; retain missing/invalid denominators.
6. Audit and seal new artifacts; update routing and report results in chat.

Generated artifacts belong in a fresh task15 external namespace; tracked task and
specification files route them. Native receipts and failure evidence remain
restartable. Never overwrite prior publications or silently rerun attempted keys.

## Research / learning checkpoint

Inspect maintained native projection, budget-dispatch and reporting APIs and their
contract tests before adding narrow integration glue. Reuse these interfaces; no
new dependencies or execution framework. Preserve the methodological distinction
between synthetic judge agreement and benchmark answer performance, and disclose
curation exposure and the combined prompt/reference/judge change when comparing
historical results. Unknown billing liabilities must not disappear from the cap.

## Validation and review

Verify49 cases and19/30 split,294 unique slots, approved source seals and changed
C040/C054 inputs, target/reference isolation, shared overview parity, frozen
A/G/S, explicit C v6 selection, no candidate IDs, model/computed diagnostics,
budget admission and no-retry behavior. Use focused integration checks, then
`make fix`, `make check` for implementation changes and `git diff --check`.
Independent bounded reviews cover input provenance, runtime/budget and reporting.
All slots must be accounted for, including failures and undispatched work if a
budget/integrity stop occurs. Seal only after workers drain and review finishes.

## Non-goals

No MiniMax, reserved challenges, agentic search, label edits, prompt tuning,
synthetic regeneration, Task16 writing, commits or pushes. Task16 requires
separate activation. Internal contradiction reasons are not separately graded.

## Prepared execution

Fresh artifact namespace: `pipelines/brisbane_baylands/task_15/fresh_generation_20261022_v1/`
under `ER_COMMONS_DATA_ROOT`. `prepare_inputs.py` is a run-specific snapshot using
maintained target projection APIs; `run.py` composes maintained provider,
dispatcher and evaluator APIs. No new dependencies. Offline reports use maintained
pure reductions and benchmark chart functions, omitting historical synthetic panels.

The prepared49 inputs contain212 passages (208 inherited and four approved C054
additions),128 required points and193 optional points. C040 uses its approved new
question. C054 reuses one existing canonical passage and adds three approved PDF
page-extract groups with explicit derivative identities and source/page provenance.
These are supplied evidence units, not claims of original canonical extraction;
their addition changes automatic citation denominators and limits historical
comparability. Targets receive question/passages only. Judges alone receive R/O
reference text; no citations, editorial explanations or human decisions leak into C.

The v6 transport/evaluator selection and larger dispatcher policy are explicit
opt-ins; default historical behavior remains frozen. The first full regression
run found a base/subclass budget-field collision; it was corrected before paid
execution. All calls use one shared ledger and16/provider gates. The existing
user-accepted OpenAI token-count fee uncertainty remains disclosed: the ledger
caps known/reserved generation/judge costs at $40, while unknown counting fees
cannot be represented as a guaranteed invoice total. No semantic retries.

## Concurrency correction and preserved interruption

The initial dispatch exposed an Inspect runtime limit: its per-model connection
semaphore was shared across model instances and inherited `max_connections=1`.
The outer16/provider gates alone did not achieve requested concurrency. Execution
was interrupted before any judge call, preserving17 completed generation records
and two uncertain in-flight generation attempts (Haiku C008 repeat1, Luna C011
repeat1). Their full reservations remain charged to the same ledger and these
slots remain unavailable; neither request is retried or replaced.

A separately reviewed `continuation_preflight.json` selects16 native connections
for Task15S only. Historical defaults remain1. The continuation preserves all
original slot identities, exact prompt/input bytes,17 completed answers and the
shared budget ledger; it attempts only275 previously untouched generation keys
and judges292 available answers. Archived observations and ledger snapshots are
hash-bound in `interruption.json`; original runtime bytes were reconstructed and
verified against the original preflight hashes in `historical_runtime/`.
This operational interruption is distinct from model/judge failures and must
remain visible in planned denominators, cost and repeatability reports.

## Localized truncated output and second resume

Luna's C judgment for Haiku C011 repeat2 exhausted the unchanged4096-token output
limit. The inherited error policy stopped unrelated work. The paid output remains
invalid/unavailable and is not retried. A separately reviewed `resume_run.py`
localizes future noncomplete model outputs while retaining stops for accounting,
integrity and transport errors. This is execution error handling, not prompt,
reasoning, output-limit or label tuning.

The sealed stopped snapshot is preserved in `stopped_phase1/`:131 completed
slots,19 existing generations with incomplete evaluation,142 untouched generation
slots (including6 locally denied before wire dispatch), and2 initial uncertain
generations. The new ledger carries all prior reservations and settlements,
including the two uncertain liabilities; only the archived global stop is lifted.
All1178 attempted judge receipts are retained.33 locally denied zero-wire judge
artifacts remain in the archive but do not count as paid attempts or prevent the
first actual dispatch. Four offline recovery tests verify these distinctions.

## Outcome

Completed steps8–9 with292 valid answers and291 complete evaluations across all294
planned slots. All150 pre-stop returned answers and every paid judgment were
preserved through recovery; no paid request was retried. The two interrupted
generation slots and one truncated C output remain unavailable.

Development C passes: Luna31/57, Haiku35/57; joint passes25/57 and13/57.
Test C passes: Luna44/90, Haiku53/90; joint passes39/90 and23/90. All291 valid C
outputs agree between model-final and deterministic point aggregation. This does
not establish semantic correctness. Review covers128 C rejections and3 unavailable
C slots, plus218 failed G-point/S judgments and4 unavailable G/S components.
Clear errors, disputed materiality and likely judge overstrictness remain distinct;
passing conclusions were not audited for false accepts and scores were unchanged.

Configured-price usage was$1.678363435; retained liability including two uncertain
charges was$2.605799435 under the separate$40 cap.2401 OpenAI counting fees remain
unknown under the existing accepted exception. Peak admitted liability was
$15.606395490 and observed peak concurrency16/provider. Total execution wall time
including recovery pauses was22.74minutes. Median successful generation wire
latency: Luna11.06seconds, Haiku13.61seconds.

Validation: make fix/check passed with4536 tests and one skip; focused orchestration
and recovery tests passed. Final independent audit verified every slot, native
payload/prompt/schema, retained byte inventory, request key, charge and offline
report replay. Representative figures were visually checked and git diff --check
passed. The offline reporter JSON-normalizes tuples for equality with saved arrays;
no scoring semantics changed.

The [sealed result](../../docs/specs/task15s_fresh_generation_result.json) binds109276
files and routes the summary, separate split charts/tables, cost/latency and
exhaustive failure inventories. Completion SHA-256:
`6b8715414e059a142f499dd65aa4731d51136ac71e58ba1bdc69ee0cbcf61430`.

Best-practice learning: Inspect connection limits are shared per model/account,
so an outer semaphore alone does not establish effective concurrency. Resume
classification must use actual wire reservations, preserving uncertain calls and
paid invalid outputs while allowing untouched work; neither an output truncation
nor a local denial should erase unrelated completed results.

Task16 remains unstarted pending separate activation. No commits or pushes.
