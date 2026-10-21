# Task 13 — Run the frozen locked-test evaluation

Status: closed, complete (2026-10-20). All 180 planned slots are generated,
evaluated, sealed and reported after the user-approved operational amendments.
Tasks 11, 12 and 12A remain closed; Tasks 14–15 remain provisional.

## Authorized continuation amendment

The user instructed: “lets just make that 30 … change that and keep goinf”. This
raises only the per-answer judge ceiling from 16 to **30** and reactivates Task 13.
Global request ceilings (2,880 judges and 3,060 counts), the cumulative $10 cap,
shared concurrency ≤10, frozen prompts/settings/scoring and zero actual-request
retries remain unchanged. The six-hour dispatch window starts at the original
first request. The accepted OpenAI counting-fee exception remains in force.

Continuation must use a fresh snapshot linked to the sealed source, preserving
original run/candidate/point IDs and every paid receipt. Carry all historical
reservations and settlements into the cumulative ledger; no budget or request
counter resets. Reuse the 97 generated answers and saved judgments. Only requests
with no prior reservation may be sent, including the slot blocked before wire
and missing evaluations. Preserve original stopped summaries and prior gallery.
No semantic failure is replaced or selected away. The larger operational limit
is a disclosed user amendment after observing a capacity stop, not prompt tuning.

Before further paid requests, validate continuation with synthetic fixtures,
`make fix`, `make check`, `git diff --check`, and independent review binding the
source seal, current code, carried ledger and continuation work inventory.
The user subsequently answered **“yes exclude and continue”**, explicitly
approving exclusion of administrative implementation/review pauses from each
answer's 1,800-second evaluation budget. Carry forward elapsed active evaluation
time; do not reset it. Deduct verified paused intervals across the sealed run
chain, preserve every prior receipt, and resume only unattempted requests.
The original six-hour overall dispatch window is unchanged. This approval also
supersedes the pending-decision language in the historical checkpoint below.

### Historical continuation validation — before pause exclusion

The linked continuation is prepared at
`task_13/locked_test_continue_20261020_v2/` beneath the external pipeline root.
Its separate preflight hash is
`9449329d71997412a0f00af60f037b965a8d1948f0b79d7158015bd1f88a64cc`.
It preserves the original preflight for exact IDs, raises only the operational
per-answer limit to 30, and carries the complete ledger. Independent verification
checks all 19,177 ancestor files and current implementation hashes. `make fix`,
`make check` and `git diff --check` passed: 4,338 tests passed, one skipped.
The original per-answer wall-clock deadlines remain in use; no pause exclusion
has been applied. Any expired partial slots are retained, never replaced.

### Pause-excluded continuation preflight

The fresh continuation is `task_13/locked_test_continue_20261020_v4/`, linked
to the sealed deadline-stopped snapshot. Preflight SHA-256:
`cf56c816a55084b2de64aed12209116c652221eba8df23625b29d98dbfd90a3f`.
It binds explicit user approval, 103 preserved complete slots, 10 partial
saved-answer evaluations and 67 never-attempted generations. Verified active
evaluation time ranges from about 19 to 720 seconds for partial slots. Only
administrative pause intervals are excluded; live queueing and the original
six-hour global clock remain counted. Full validation: 4,340 tests passed,
one skipped; formatting, lint, typing and diff checks passed. Independent
preflight review binds the exact implementation, source chain and ledger.

## Abstract and goal

Evaluate both frozen target models, Luna and Haiku, on all 30 locked questions,
with three fresh answers per question/model. These 30 questions supply the main
target-model results. Report all 30 together in a second clean figures/tables
folder, following the [presentation amendment](../../docs/specs/task12_presentation_v2.md);
judge accuracy and [repeatability](../../docs/specs/task12_judge_repeatability_v3.md)
retain their own synthetic datasets and same-item triples. Use Task 12's frozen reporting rules
and export its tables/charts without selecting favorable repeats or retuning.

## Inputs and outputs

Use the [reporting maintainer guide](../../docs/reporting_maintainer_guide.md)
and [12A closeout](12a_reporting_code_quality.md) for the maintained implementation.

Inputs: [Task 12](12_integrate_evaluation_and_reporting.md) reporting/readiness
handoff ([accepted result](../../docs/specs/task12_result.json) and
[frozen definitions](../../docs/specs/task12_reporting_v1.md)),
[11E configuration](../../docs/specs/task11e_frozen_generation_v1.json),
accepted Task 10 input publication and 09G judges. Preserve the accepted prompt,
examples, focused conclusion check, shared overview and neutral input projection.

Outputs: a new sealed run containing all 180 planned target-answer slots, raw
requests/responses, generation and judge receipts, failures, accounting, exact
identities and replayable result tables/charts. Development and test reports stay
separate. Provide a compact handoff to [Task 14](14_selective_failure_review.md).

## Authorized spending ceiling

The user set a **$10 total Task 13 spending cap** after reviewing the Task 11E
estimate of $0.651832465 for generation and judging. This sets the monetary cap;
it does not by itself activate locked evaluation. Before dispatch, specify
reserve for in-flight requests and accounting for counting charges under the
limits below. Stop dispatch before the cap could be exceeded;
unknown charges must remain explicit rather than being assumed free. No automatic
budget expansion. Task 11E ran serially.

**User clarification, 2026-10-20:** “i dont care if it charges. im 99% sure it
doesnt” (referring to OpenAI token counting). The user accepts possible charges
from that endpoint and explicitly removes its unverified fee as a reason to
block Task 13. This supersedes the requirement for an authoritative counting-fee
bound before proceeding. Keep the fee labeled unverified, rather than claiming
that the provider confirmed it is free. The $10 budget and all other execution
limits remain unchanged; this is acceptance of that specific billing uncertainty,
not a general budget increase. Carry the exception into fresh execution accounting
and preflight review; preserve the earlier sealed blocked preflight as history.

## Concurrency plan

Use a global maximum of **10 in-flight remote requests**, shared across target
generation, judge evaluation and token-count requests. This is not ten answers
with unrestricted judge fanout. Maintain a bounded work queue and preserve the
required per-answer dependency order; independent ready work may overlap.

The dispatcher must reserve estimated maximum request liability before admission,
including all in-flight work against the $10 cap. Preserve exact slot/item IDs
regardless of completion order. On a budget stop, admit no new work and retain
receipts for work already dispatched. Lower effective concurrency on rate-limit
pressure; define any retry policy explicitly before execution rather than silently
adding retries. Ten is a ceiling, not a required utilization target or an assumed
provider allowance. Validate these controls offline before live dispatch.

## Execution limits

The monetary and concurrency limits are user-selected. The remaining conservative
limits carry forward the accepted 11E execution policy, scaled to 180 answers.
They are ceilings, not targets; the $10 admission check may stop work earlier.

| Control | Limit |
| --- | --- |
| Target generations | 180: two models × 30 questions × three fresh repeats |
| Judge requests | At most 30 per answer under the continuation amendment, 2,880 globally |
| Token-count requests | At most one per admitted generation/judge request, 3,060 globally |
| Global remote concurrency | 10, shared across generation, judges and counters |
| Spending | $10 total; settled charges plus reserved in-flight liability |
| Effective input tokens | 100,000 per request |
| Target output allowance | 12,288 tokens, including reasoning where applicable |
| Judge output allowance | 4,096 tokens |
| Per-request timeout | 900 seconds |
| Per-answer evaluation deadline | 1,800 active seconds; verified administrative pauses excluded by user amendment |
| Global dispatch window | Six hours from first live dispatch |
| Automatic retries, repairs, replacements, extra repeats | Zero |

Over-limit answers remain intact: do not trim their points or substitute another
answer. Stop new dispatch and preserve the reason and all remaining planned slots.
Timeouts, rate limits and uncertain attempts are recorded, not retried silently.
Lower concurrency on rate-limit pressure for remaining undispatched work. An HTTP
429 halves the effective ceiling (minimum one); retain that failed request without
retry and continue eligible untouched work. Other execution errors still stop new
dispatch. Honor
SDK retry settings explicitly so hidden transport retries cannot defeat the cap.
On stop, let already-dispatched requests settle within their timeouts and preserve
all receipts; the global window controls new dispatch, not deletion of in-flight
results. Resume only verified undispatched work under the same cumulative ledger;
never replay a request with an uncertain outcome automatically.

## Preflight implementation and activation gate

This task was explicitly activated on 2026-10-20. Complete implementation and
execute within these limits only after the checks pass. Activation permits the sealed
30-test input adapter for this run; it does not permit inspecting reserved judge
challenge content, semantic scouting of test answers, or using test outcomes to
tune any component. Do not ask for the already-recorded $10/10 approval again.

Before any paid request:

1. Read and bind exact accepted configuration, input release, judge and current
   reporting identities. The baseline implementation is commit `ab38a3c`; bind
   any new Task 13 code separately. Preserve the original prompt and projections.
2. Implement a separate locked-only adapter with strict split/roster validation,
   reference-free generation projections and full exact identities. Test with
   invented fixtures and development-only replay first. Do not redirect the
   Task 12 development loader to test paths or load whole mixed-split datasets.
3. Implement bounded dependency-aware work scheduling with one shared request
   semaphore, atomic budget/call reservations and restartable per-slot receipts.
   Generation must finish before its evaluation; preserve the existing route and
   judge prerequisites. Completion order must not affect identity joins or scores.
4. Verify current provider pricing and whether count calls are chargeable using
   available provider/account metadata. Record the pricing basis. An unknown fee
   is not verified zero. The user clarification above permits proceeding despite
   the unverified OpenAI counting fee; record that exception explicitly. Other
   unbounded charges remain blockers. Do not substitute the old $60 planning reserve.
5. Test concurrency ≤10, simultaneous budget admission, deadline/stop behavior,
   malformed/over-limit answers, interruptions and uncertain-request resume.
   Run appropriate offline tests, `make fix`, `make check`, `git diff --check`,
   then a bounded independent preflight review. Save the preflight manifest.

Do not expand limits automatically. A genuine validation failure, unbounded
billing exposure outside the accepted OpenAI counting-fee exception, or a required
change to frozen evaluation definitions stops live execution pending resolution; ordinary implementation choices do not require a
new user approval.

## Artifact and reporting handoff

Use a fresh run directory under
`ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_13/`, with create-only
artifacts, a manifest and completion seal. Keep an explicit 180-slot roster,
including unattempted and failed slots, plus model/run/repeat/candidate/point IDs,
request hashes, token usage, costs, reservation reconciliation and stop reasons.
Do not overwrite Task 11/12 publications.

Export final figures and relevant tables into a separate `test_30_review/`
folder with `START_HERE.html`; keep raw runs, intermediates, provenance and logs
outside that folder. Report all 30 test questions together and keep development
separate. Reuse current reporting reducers and bins, optional/neutral context
citation rules, distinct response-unit versus citation-occurrence counts, and
same-answer joint success. Reuse synthetic judge diagnostics without rerunning
or recalibrating judges on synthetic/reserved datasets. Task 14 owns subsequent
selective human review; Task 15 owns the writeup.

## Plan and research checkpoint

1. Accept Task 12 readiness and freeze model/prompt/schema/input/judge/reporting
   identities and three-repeat policy before reading test outcomes. Resolve any
   projection/readiness gap explicitly rather than adapting it after results.
2. Record concrete generation, judge, count, retry, time, token and spending caps
   before dispatch. 180 target slots are the planned denominator, not an inherited
   budget authorization. Judge fanout depends on generated points; set conservative
   bounds and stopping policy before calls. Preserve interrupted/uncertain attempts.
3. Validate using offline fixtures and development-only replay. Preserve source
   separation: no references or evaluator feedback enter generation requests.
4. Run complete planned coverage under the fixed policy. Every repeat is a new
   answer, not an independent rejudging of a saved answer. Never replace a semantic
   failure or choose the best output. Account for every unattempted/error slot.
5. Reuse Task 12 reporting for both models, per-component/automatic/joint outcomes,
   at-least-once/every-time results and Luna associations with citation occurrences,
   distinct response units and documents.
   Reuse frozen bins/denominators; do not optimize plots or model choice on test.
6. Seal artifacts, verify no-network replay and document costs and limitations.
   Task 14 handles selective manual diagnosis; Task 15 writes the short report.

Use Task 12's researched reporting definitions. Explain that repeats expose
observed variability but do not provide independent questions or isolate judge
variance from generation variance. The source project remains a limited setting.

## Validation, review and acceptance

Bounded independent review of preflight identities/budgets and final coverage,
receipt joins and reporting. All 180 slots accounted for, each result replayable,
no unreported retries or silent exclusions. Follow repository code checks if code
changes; otherwise verify artifact seals and `git diff --check` for documentation.

## Non-goals

Prompt or judge tuning, reference correction based on test success, new models,
search-agent evaluation, broad human annotation, methods/results writeup, commit
or push. Changes motivated by locked outcomes require a new future condition and
cannot retroactively improve this run's frozen results.

## Final outcome — complete execution

All **180 planned answers** are generated and fully evaluated: Luna and Haiku,
30 test questions each, three fresh answers per question. No slot is unavailable,
no actual remote request was retried, and no answer or semantic failure was
replaced. The frozen prompts, examples, settings, exact model identities, judges,
scoring rules and input projections remain unchanged.

The final [result pointer](../../docs/specs/task13_result.json) selects, beneath
`ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_13/`:

- `locked_test_continue_20261020_v4/`: final sealed run with cumulative receipts,
  exact identities and preserved ancestor history.
- `locked_test_reporting_20261020_v4/`: complete offline replay and sealed tables.
- `test_30_review/START_HERE.html`: seven PNG/SVG figure pairs and eleven CSV tables.
- `locked_test_continue_20261020_v4_audit/`: independent final audit and reporting
  review receipts.

| Model | Same-answer joint passes | Passes / planned answers | Questions passing at least once | Questions passing every time |
| --- | ---: | ---: | ---: | ---: |
| Luna | 39 / 90 | 43.3% | 17 / 30 | 8 / 30 |
| Haiku | 16 / 90 | 17.8% | 10 / 30 | 1 / 30 |

These are frozen evaluator outcomes in one source-project setting, not independent
question samples across repeats or human-adjudicated truth. Reporting retains all
30 questions together. Synthetic judge accuracy/repeatability use their separate
historical 09G datasets; development remains a separate publication. Reserved judge
challenges were not opened. Task 14 may review bounded disagreements and failure
examples using the saved identities; Task 15 may write up these complete results
with the operational amendments and limitations. Neither task is activated here.

Cumulative execution used **180 generations, 1,526 judge requests and 1,706 count
requests**. Known usage charges are **$1.004175550**. Fees for **1,436 OpenAI
counting requests** remain unknown under the user's accepted exception, not claimed
free. Every remote attempt settled; the final ledger has no stop condition or
uncertain attempt. The $10 reservation cap, global concurrency ≤10 and original
six-hour dispatch window stayed in force.

The user explicitly amended the per-answer item limit from 16 to 30, then approved
excluding verified administrative implementation/review pauses from per-answer
evaluation time. The remaining active time was carried forward, not reset; live
queue time stayed counted. These were operational amendments after the preserved
stops, not prompt or score tuning. Original outputs and paid receipts were reused
unchanged, and only never-attempted requests were dispatched. Earlier partial
publications remain preserved in `initial_policy_stop_publication/`,
`deadline_stop_publication/` and their sealed reporting namespaces.

Full validation passed: **4,340 tests passed, one skipped**, plus final formatting,
lint, typing and `git diff --check`. Independent preflight checked the full source
chain, claims, copied receipts and active-time calculations. Final publication ran
with network connections disabled and replayed all 180 answers; principal figures
were visually inspected. Exact final independent audit bindings and charges are
recorded in the result pointer. No commit or push was performed.

## Historical continuation checkpoint — deadline stop

The user-authorized 30-item ceiling was implemented and dispatched after the
4,338-test validation and independent preflight approval. The original per-answer
wall-clock deadline remained unchanged because no pause-exclusion approval was
received. The continuation stopped on `Per-answer evaluation deadline exhausted`.

All 180 slots remain sealed: **103 completed, 10 evaluation-incomplete and
67 not dispatched**. Cumulative requests are **113 generations, 786 judges and
899 counts**, with known charges **$0.480622800**, plus accepted unknown OpenAI
count fees. All in-flight requests settled. Prior answers, judgments, identities
and ledger entries remain preserved; no actual request was retried.

Independent audit passed: all 23,966 continuation files and all 1,798 unique
native receipts reconcile, with no unsettled requests or admissions after the
stop. All 19,177 original files remain unchanged. Report replay and the gallery
verify all 180 slots and 30 questions. The 771 OpenAI count fees remain unknown.

At this checkpoint the deadline decision was pending; the later explicit approval
and completed run above supersede that state. The original wall-clock interval includes
the administrative pause between the initial stop and continuation. Further
execution cannot silently reset or relax that separate task limit. That checkpoint was published with incomplete-coverage disclosure. Its pointer
and gallery are preserved in `deadline_stop_publication/`; the current result
pointer selects the completed run. Tasks 14–15 remain provisional.

## Historical outcome — initial policy-stopped execution

The locked run stopped at the agreed **16 judge items per answer** limit: Haiku
repeat 1, C011 produced a valid answer requiring 17 items. Its raw output and
candidate remain intact and it received no judge calls. No answer was trimmed,
replaced or retried. All in-flight work settled, and all **180 planned slots**
remain in the sealed result and report. This is **not a complete Luna–Haiku
comparison**; the stop left strongly unequal model coverage.

| Model | Planned | Fully evaluated | Evaluation incomplete | Blocked generation label | Not dispatched |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna | 90 | 88 | 2 | 0 | 0 |
| Haiku | 90 | 0 | 7 | 1 | 82 |

The one `generation_failed` label is the SDK wrapping `DispatchStopped` before
any remote attempt for that slot; it is not a provider failure or retry.
There were **97 generation, 622 judge and 719 count requests**, each with a
unique native request ID and HTTP 200 response. Known generation/judging charges
are **$0.362787295**. Charges for 624 OpenAI count calls remain unknown under the
user's explicit exception; they are not asserted free. Peak recorded concurrency
was **2**, peak reserved liability **$1.276132500**, and no attempts remain
unsettled. No request was admitted after the stop.

The [sealed result pointer](../../docs/specs/task13_result.json) owns exact
publication identities. Under `ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/`:

- `task_13/locked_test_20261020_v1/`: sealed run and all planned outcomes.
- `task_13/locked_test_reporting_20261020_v2/`: offline replay and sealed tables.
- `task_13/initial_policy_stop_publication/`: preserved initial-stop gallery
  and result pointer, with incomplete-coverage disclosure and all 30 questions.
- `task_13/locked_test_20261020_v1_audit/`: independent native/ledger/coverage and
  reporting review, final validation receipts.

Luna has 38 joint passes, 51 known joint failures and one unavailable joint
outcome across its 90 planned slots. Haiku has zero joint passes, two known joint
failures and 88 unavailable outcomes; this cannot support a model ranking.
Partial component outcomes remain visible without pretending that evaluation
finished. Synthetic judge diagnostics reuse the separate historical 09G datasets;
development results stay separate. Repeats expose observed variability but are not
independent questions and do not isolate judge variance from generation variance.

### Validation and publication corrections

Before dispatch, offline fixtures, exact development replay, independent review,
`make fix`, `make check` and `git diff --check` passed: 4,329 tests passed, one
skipped. Fresh preflight SHA-256:
`e60f028f23014e1d1cd43783bcbf84404fe7b9de2eec3ecfdafa086ac1bc9bdc`.
It explicitly records accepted OpenAI count-fee uncertainty. The earlier blocked
preflight remains intact as historical evidence.

Final independent audit verifies all 19,177 sealed files, all 180 slot identities,
all 1,438 native receipts, exact Decimal usage costs, atomic reservations and stop
admission. Offline replay reconstructs all 97 delivered answers. Network access
was prohibited during publication.

After sealing, publication exposed an insertion-order-sensitive roster comparison.
Sorting by canonical JSON hash fixes that structural comparison; a canonicalized
synthetic fixture reproduces the issue. No frozen input or scoring rule changed.
The final gallery adds execution-status disclosure from sealed outcomes/accounting.
Its answer table is byte-identical to the initial publication. The initial report
and gallery are preserved (`locked_test_reporting_20261020_v1/` and
`initial_publication/`). Final `make fix`, `make check` and `git diff --check` passed: **4,330 tests
passed, one skipped, 96 upstream warnings**; six focused reporting tests passed.
Exact validation receipts are recorded in the result pointer.

### Provisional Task 14 handoff

Any later selective review should begin with the stop and unequal coverage, then
use the saved answer/point identities for bounded examples. Do not infer Haiku
quality from unavailable slots. No automatic continuation, replacement, new repeat
or cap increase is authorized by this closeout. Any changed experimental condition
requires separately scoped work; it cannot retroactively improve this run. Task 15
must retain these limitations. Neither Task 14 nor Task 15 is activated here.

### Implementation and learning

- `locked_inputs` reads only the selected split and individually sealed reference
  publications. Generation receives only the reference-free neutral record.
  `reporting_inputs.load_development` remains development-only.
- `locked_dispatch` uses standard-library locks, exclusive process ownership,
  durable create-only receipts and Decimal accounting. Reservations include
  in-flight and uncertain liabilities. All three remote request kinds share the
  same gate; zero SDK/http transport retries are explicit.
- `locked_provider` retains 11E native prompts, models, reasoning, schemas and
  caching. It reserves worst-context liability, then reconciles ordinary/read/
  write/output usage. Raw wire bytes survive malformed response parsing. A count
  hook cannot hold a remote permit while waiting for its own count request.
- `locked_run` schedules at most ten answer workers, preserves per-answer judge
  dependencies, drains workers before releasing process ownership, and binds a
  task-wide paid-run claim so a new namespace cannot reset spending. Partial
  slots are never automatically repeated; verified untouched slots may resume
  with the same cumulative ledger.
- The pure evaluator now accepts an explicit expected split, defaulting to `dev`;
  only the locked callers pass `test`. This changes source validation, not scores.
  Malformed candidates retain their raw-byte identity and automatic failure.
- Structural preflight discovered the multipart source identifier
  `deir_appendix_k1_part_1_of_4`. The source catalog identifies it as a physical
  part of Appendix K.1. A validated multipart suffix extends the same neutral
  appendix label rule; original source IDs, canonical mappings, text and headings
  remain intact. No test outcomes exist or informed this mechanical correction.
- `locked_reporting` replays complete, interrupted and invalid observations into
  the existing reducers. All 180 slots stay in denominators. Synthetic judge
  diagnostics remain separate; no reserved judge challenges were opened.

### Historical preflight validation and evidence

The preflight namespace relative to `ER_COMMONS_DATA_ROOT` is
`pipelines/brisbane_baylands/task_13/locked_preflight_20261020_v1/`.
Its `preflight.json` SHA-256 is
`b2f37086987883db90025d3093d1ab9a072185f97a3c33451bede887e4bcbee8`.
It binds baseline commit `ab38a3c` separately from all new implementation hashes.
That historical independent receipt records implementation approval and the
then-unresolved billing blocker. The later user clarification superseded the
blocking policy and was recorded in the refreshed preflight. Validation logs and the development replay
receipt are under its `validation/` folder; `preflight_completion.json` seals
preflight evidence only and is not an evaluation completion seal.

Development replay checks all 19 accepted records, mappings, reference projections
and source hashes (76 exact comparisons), and replays all 114 saved observations
without score changes or network calls. Fixtures cover concurrency, atomic budget
admission, limits/deadlines, interrupted/uncertain resume, count nesting, malformed
answers/responses, all six native provider routes, cache-write accounting, roster
preservation and source isolation. Final `make fix`, `make check` and
`git diff --check` pass: **4,317 tests passed, one skipped, 96 upstream warnings**.
Their final results are saved with the preflight.

The fully offline publication fixture is separately labeled **SYNTHETIC NOT
RESULTS** under `task_13/offline_gallery_validation_20261020_114054/`. Its receipt
records 30 invented questions, 180 unavailable slots, seven PNG/SVG figure pairs,
eleven CSV tables and `START_HERE.html`, with network connections forbidden during
publication. It is not the requested test-results gallery.

Existing artifacts and unrelated local documentation changes are preserved.
Tasks 14–15 remain provisional. No commit or push was performed.
