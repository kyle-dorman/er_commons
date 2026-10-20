# Task 11D — Iterate the prompt on three then six questions

Status: Complete after authorized 100K continuation (2026-10-17); no acceptable candidate within the revision budget.

## Abstract

Improve the Luna prompt through bounded comparisons on the fixed nested panels.

## Goal

Select a candidate prompt using three questions first, then six, with traceable reasons for every change.

## Inputs

Accepted panel/criteria and budgets from 11A, runner from 11B and integrated reports from 11C.

## Outputs

Versioned prompts and configurations, saved candidate/evaluation artifacts, compact comparison and decision record, selected candidate and remaining issues.

## Plan / spec requirement

Use this contract as the brief plan; record concrete interfaces and limits before implementation.

1. Freeze the initial prompt and declare concrete revision, call/cost, repeat and stopping limits before dispatch. Hold model, evidence and judges fixed so prompt effects remain interpretable.
2. Run the first three cases; inspect answers, source fidelity, automatic checks and judge explanations together. Record a specific hypothesis for each revision and preserve rejected versions.
3. Compare revisions on identical cases/settings; label retries and repeats. Do not cherry-pick favorable stochastic answers or suppress invalid outputs.
4. Once a candidate meets the recorded criteria or the first-cycle budget ends, expand to the fixed six (the original three plus three). Apply the same bounded comparison process and record regressions as well as gains.
5. Select a candidate with a rationale and disclosed failures, or explicitly report no acceptable candidate within budget. Manual review may disagree with a judge; preserve both without modifying frozen judge policy.
6. Keep reference answers and evaluator feedback out of individual generation requests. This is global prompt development, not a per-answer judge-feedback repair loop. Do not copy case-specific answers into the prompt.

## Authorized 100K continuation

The user explicitly authorized resuming with **100,000 input tokens** and assumes
counting is free. This section supersedes the earlier operational cap and stop for
new runs only. Preserve the [original result](../../docs/specs/task11d_final_result.json),
all sealed attempts and original reservations. Publish a separate continuation
result and fresh external namespaces; never overwrite the stopped run.

Start with unchanged v3 on the complete fixed six: C041, C017, C019, C014, C037,
C056. This replacement expansion is a fresh full-panel observation; the first
three from the stopped run remain visible and are not mixed into it. Model,
medium reasoning, 4,096 output cap, schema, complete Task10 packets, frozen judge
prompts/models and zero retries remain fixed. Raise the operational exact-input
cap to 100,000 for both target and judges; do not truncate or alter evidence.
The 100K correction is operational, not a new prompt hypothesis: v3 retains its
recorded conclusion-coverage hypothesis. Evaluate all six before selection.

Permit at most one generic six-case revision if review finds a material defect;
record its specific hypothesis before dispatch and compare all six. Then run
exactly one full-six repeat of the chosen incumbent (repeat 2), if complete valid
primary evaluation supports continuing. No repair rerolls or further repeats.
Keep incumbent on ties and reject a revision with a new material defect. Manual
and judge disagreements stay visible; select with documented limitations or
report no acceptable candidate. A failed stability check is reported, not retried.
No remaining 13, test/reserved content, Task10 changes, judge tuning or 11E.

Continuation ceilings: **18 target generations, 216 judge calls, 234 counts**,
zero retries, at most three six-case arms, three working days. This explicitly
adds a replacement expansion allowance after the previous cap stop; combined
actual maximum is 27 target generations, 261 judges, 289 counts including prior
work. Per arm caps remain 6 target/count calls, 72 judge/count calls, 15-minute
generation and 30-minute evaluation timeboxes, USD 2 generation and USD 24 evaluation
ceilings. Required fan-out is planned before judges; never omit points to fit.
Stop all further live work on count/context/integrity/provider failure, exhausted
limits, or two successive prompt revisions without material improvement.

Use zero count-cost allowance prospectively under the user's assumption. Anthropic
[documents counting as free](https://platform.claude.com/docs/en/build-with-claude/token-counting#pricing-and-rate-limits);
OpenAI's [counting guide](https://developers.openai.com/api/docs/guides/token-counting)
does not establish billing, so preserve that uncertainty rather than claiming a
verified price. Historical USD 0.30 allowances stay preserved, not charged or
refunded. Token reserve rates remain USD 0.25/M input including cache writes and
USD 0.75/M output. A call reserves at most USD 0.028072; each generation/evaluation
arm reserves USD 0.168432 / USD 2.021184. Maximum continuation liability USD 6.568848,
plus preserved earlier ledger USD 26.146176 = USD 32.715024, within the unchanged
USD 100 overall accounting ceiling. This is not a provider-enforced invoice cap.

Before dispatch, test that operational judge limits reach actual provider hooks,
keep original default replay unchanged, verify protected hashes and exact requests,
run make fix/check and independent review. Native requests still use the same
model settings; 100K is a local admission limit. Save per-arm reservations before
calls and retain all failures/unknown usage. Replay all completed evaluations
without providers; review every generated answer against selected evidence.
V4 hypothesis (recorded after complete V3 fixed-six review): systematic coverage
across all passages, balancing exclusions and corrective measures and linking each
conclusion clause to stated premises, will reduce selective omissions and unsupported
document-status commentary. V3 retains C017/C014 judge failures and a manual C037
completeness defect. V4 is the sole six-case revision; its prompt contains no case
facts or evaluator outputs. Compare all six before selecting the repeat prompt.

No new dependency is needed: pass a validated per-run limits object through the
existing native Inspect receipt hooks. This keeps old runs' defaults intact and
makes the executed limit match the manifest.

## Original execution contract (preserved)

Use the sealed 11B candidates and 11C reports as the initial v1 baseline, with
C017 C=false and C019 S=false preserved. The 11C.1 cleanup replay establishes
unchanged reports; it supplies maintained input/provider/run boundaries. No
baseline reroll is authorized to replace these observations.

Hold Luna `openai/gpt-6-luna`, medium reasoning, default tier, 4,096 output tokens
including reasoning, strict answer schema, complete Task 10 packets and frozen
09G A v2/G v3/C v8 Luna and S v6 Haiku fixed. Operational execution is sequential,
with zero transport retries and zero semantic rerolls. Keep raw failures and
uncertain spending. Only prompt text varies; panel, repeat and operational budget
metadata are recorded separately from model settings.

The fixed initial panel is C041/C017/C019; expanded panel adds C014/C037/C056 in
that order. At most two generic initial-panel revisions are allowed. Expand after
an initial candidate meets the protocol quality gate, or after the initial
revision allowance ends, unless a global stop has fired. Compare the incumbent
on all six, permit at most one further six-panel revision, and one repeat of the
selected prompt on all six (repeat=2). Each arm covers its entire declared panel;
no picking outputs across runs. The six-panel incumbent run is a fresh observation
on all six and does not overwrite the saved three-panel observations. Retain the
incumbent on ties; require material improvement without a new material defect to
replace it. Stop prompt revisions after two successive non-improvements. If this
stop fires before expansion, report no acceptable candidate rather than extend
calls. A stability failure is reported, never followed by another repeat.

Concrete total caps: **24 new target calls, 288 judge calls, 312 count calls,
zero retries, USD 100 reserved liability, and three working days**. Saved baseline
reuse is separately reported and consumes no new calls. Per initial arm: 3 target
calls/counts (USD 1 cap, 15 minutes), up to 36 judge calls/counts (USD 12 cap,
30 minutes). Per six arm: 6 target calls/counts (USD 2 cap, 15 minutes), up to
72 judge calls/counts (USD 24 cap, 30 minutes). Exact required G fan-out is computed
before any judge dispatch; excess blocks that arm, never drops points. Max input
is 32,768 exact provider-counted tokens per call; max output is 4,096. A count or
context/integrity/provider failure stops further live dispatch. Invalid target
outputs stay in coverage; no promotion or evaluation that silently drops them.

Reserve USD 0.25/M input including cache writes and USD 0.75/M output for either
provider, plus USD 0.30 per count. Maximum total prospective liability is
312 × USD 0.311264 = **USD 97.114368**, below USD 100 even without reclaiming any
uncertainty. Count prices remain unknown; this is an accounting allowance, not a
provider-enforced invoice guarantee. Actual generation/judge token usage and dated
price estimates are reported separately. Each arm's manifest and a task-level
pre-dispatch ledger reserve its exact worst-case call liability before calls
(USD 0.933792/11.205504 for three-case generation/evaluation;
USD 1.867584/22.411008 for six), within the rounded per-arm caps; no unrecorded probes.

Write each revision hypothesis and preserve its exact prompt/configuration before
dispatch. v2 hypothesis: explicit coverage of the question's comparison and a
self-contained, qualified conclusion will reduce unsupported inference and loss
of material conditions during summary, without adding case-specific facts.
v3 hypothesis (after completed v2 three-case review): an explicit multi-sentence
conclusion coverage audit will prevent necessary assumptions from being lost during
summary compression. v2 improved the comparison basis but retained a material
conclusion omission. This is the second and last initial-panel revision; its prompt
contains no case-specific condition or answer. Future revisions must name observed
generic failure mechanisms before dispatch.
References and evaluator feedback remain evaluation-only; generation receives
only the generic prompt, schema, question and complete evidence. No reference
answer, case ID, selected-panel rationale or judge explanation enters its request.

Offline checks and independent review precede live calls. Verify source bindings,
sealed baseline replay, selected packet equality, exact identities, complete panel
coverage and schema/native request fixtures. Preserve source snapshots, review,
raw responses/counts/receipts, per-point reports, rejected revisions and a no-call
replay of every completed evaluation in fresh external Task 11 namespaces.
Manually inspect every candidate against supplied evidence; disagreements remain
explicit. A selected prompt with limitations or a bounded no-selection outcome
closes 11D; neither starts 11E nor establishes benchmark performance.

## Research / learning checkpoint

Reviewed 2026-10-17: [Inspect scorers](https://inspect.aisi.org.uk/scorers.html) and
[logs](https://inspect.aisi.org.uk/eval-logs.html) support separate saved-output
scoring and retained attempt records. Rechecked [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
and [Haiku pricing](https://platform.claude.com/docs/en/about-claude/pricing) before dispatch.
Reuse the installed native SDK/Inspect adapters; no new dependency or workflow engine. Explain adaptive selection bias and distinguish a prompt hypothesis from evidence of broad performance.

## Validation

Check complete declared panel coverage per revision, unchanged packet/judge identities, retained failures and budget accounting. Inspect prompt diffs and replay reports. Apply make checks if code changes; otherwise git diff --check.

## Acceptance criteria

A selected candidate, exact configuration and honest comparison record are ready for 11E, or the bounded failure is recorded without claiming completion of a baseline freeze.

## Review pass

Bounded review of comparison fairness, evidence fidelity, selection rationale and tuning exposure.

## Non-goals

No remaining-13 evaluation during cycling, test access, model sweep, evidence edits or judge optimization.

## Shared boundaries

Follow the [Task 11 umbrella](11_build_and_freeze_target_generation.md). Use only
the 19 development cases; no locked-test or reserved judge-challenge access.
Preserve Task 10 packets and frozen A/G/S/C judge policies. Keep references and
judge feedback outside target requests. Generated runs and reports belong under
`ER_COMMONS_DATA_ROOT`, with exact input/configuration hashes and fresh namespaces.

## Original stopped outcome

Completed two bounded three-case prompt comparisons and attempted the fixed-six
expansion. **No acceptable six-case candidate was selected within the recorded
limits.** V3 passed the initial three, but C014's complete serialized request
counted **33,922 tokens**, exceeding the predeclared 32,768 input cap. Its generation
was blocked; C037/C056 were not dispatched. The global context stop ended all live
work, including six-case evaluation and stability repetition. The model's larger
context capacity does not override this task's deliberately smaller operational cap.
No evidence was shortened and no case was substituted. The
[result pointer](../../docs/specs/task11d_final_result.json) binds all attempts,
reviews, accounting and replay evidence.

| Observation | Complete panel accounting | Decision |
| --- | --- | --- |
| Sealed v1 baseline | Three saved candidates; C017 C=false, C019 S=false | Reused unchanged; no calls |
| v2 initial three | All3 valid; all12 G true; S true; C017 C=false | Improved comparison reasoning and grid characterization; residual conclusion omission |
| v3 initial three | All3 valid; all15 G true; S/C true; manual acceptable | Provisional incumbent; explicit conclusion coverage improved C017 |
| v3 fixed six | Three valid, C014 input-cap failure, C037/C056 unattempted; all6 evaluation unavailable | Global stop; no selection or stability claim |

Every generated answer was manually reviewed against its complete supplied packet.
The stopped six run's first three remain distinct candidates: C041 acceptable,
C017 acceptable with less explicit source-inconsistency disclosure, C019 factually
acceptable but with weaker reasoning detail and unresolved support sufficiency.
Their earlier judgments were not copied across identities. These observations
show sampling variation even with the same prompt/settings. Full per-case and
point identities, raw text, native requests/responses, counts, errors and missing
coverage remain in the external comparison; no favorable outputs were mixed.

The task used **9 target generations, 45 judge calls, 55 counts and zero retries**.
The pre-dispatch ledger reserved **USD 26.146176** without refunds, below the
USD 100 ceiling. Counting cost is unknown: **USD 16.50** of count allowances remain
associated with actual count attempts; the larger ledger reservation also retains
unused/uncertain arm liability. Token-price estimates and usage are in the result
pointer, not claimed as an invoice or provider-enforced cap. Neither the spending
nor elapsed-time ceiling was exhausted; the explicit input boundary stopped work.

Narrow runner extensions expose fixed3/fixed6 panels, versioned prompt/config and
repeat1/2, plus sealed-generation-run evaluation and bounded operational limits.
They keep the frozen semantic provider code and policies unchanged. Existing
11B/11C receipts and result pointers remain sealed. The maintained Make commands
accept GENERATION_OPTIONS and EVALUATION_OPTIONS; the exact commands and source
snapshot are preserved externally. Do not rerun sealed generation with changed
source hashes; use the saved evaluation replay path.

Offline tests and independent reviews preceded dispatch. `make fix`, `make check`
(**4,067 passed, one skipped**) and `git diff --check` passed. Baseline and both
new complete evaluations recomputed with zero calls; the new-run replay audit
disabled provider construction/dispatch. Receipt checks verified complete payloads
for every rendered request, raw-answer/candidate equality and exact input counts
against cache-inclusive usage for delivered generations. All five run inventories,
fixed panel, Task10 and sealed baseline bindings remain unchanged. The stopped
six-case summary preserves every planned case; absence is not a semantic failure
or a passing score. Bounded independent reviews covered code, leakage, paired
fairness, source fidelity, accounting and the no-selection decision.

Learning: explicit inference and conclusion-coverage instructions helped on tuning
cases, but do not establish broad performance or repeatability. Serialized table
representations can exceed a conservative input cap despite modest prose length;
the exact provider count, including schema and framing, is authoritative. Fixed
panels expose this failure honestly. All six remain tuning cases; the other13 and
locked30 remain unassessed here. Frozen judges retain development-selection and
correlated-error limitations, and provider aliases are not immutable snapshots.

Next: a separately refreshed bounded contract must decide whether to correct the
operational input budget and rerun the complete fixed six with full evaluation and
stability evidence. Do not silently enlarge this completed task's budget. **11E is
not ready and was not begun.** No remaining 13, locked-test or reserved-challenge
content was evaluated or inspected; no Task10 artifacts or judges changed.

## 100K continuation outcome

Resumed under the user-authorized **100,000-token input cap** and zero-cost
counting assumption. The cap correction worked: complete V3 and V4 runs each
covered all six fixed cases, with valid outputs, exact delivery receipts and full
frozen evaluation. No context, transport or accounting-validation failure occurred.
**No candidate was selected within the recorded revision budget.** V4 repaired
some omissions but introduced a new material error, so it could not replace V3
under the no-new-defect rule. Neither primary candidate qualified for the
conditional stability repeat; it was not run. The
[continuation result](../../docs/specs/task11d_resume_100k_result.json) preserves
both complete arms and the decision. The original result and stopped run remain
unchanged.

| Case | V3 frozen results | V4 frozen results | Manual comparison |
| --- | --- | --- | --- |
| C041 | G5/5, S/C true | G5/5, S/C true | Acceptable in both |
| C017 | G6/6, S true, C false | G5/5, S/C true | V4 restores excluded battery benefits; source-footnote inconsistency still undisclosed |
| C019 | G3/3, S/C true | G4/4, S/C true | V4 improves physical mechanism and approval scope |
| C014 | G4/5, S/C false | G3/6, S/C true | V4 newly mislabels TRA-4 as list-based in conclusion; source and own supporting point say projections-based |
| C037 | G4/4, S/C true | G6/6, S/C true | V4 restores two-year grading/City exception in support; conclusion remains less explicit |
| C056 | G3/3, S/C true | G4/4, S/C true | V4 implies matched storm baselines not established by source; V3 explicitly preserved uncertainty |

A classified all twelve candidates substantive. All outputs met structural and
citation-resolution gates. Canonical citation precision was 1 throughout; recall
was 0.75 for C014 and 0.5 for C056 in both arms, and 1 for the other cases. Exact
per-point failures, component reasons, source-linked manual reviews and candidate/
run/repeat IDs are preserved, not collapsed into an aggregate ranking. In C014,
V4 G rejected two edition/provenance assertions not established by the isolated
owned excerpts and a project-inclusion claim missing its project-list citation.
Some metadata-based manual observations differ; no frozen judgment was changed.

The manual C014 conclusion error blocks promotion even though V4 S/C passed.
Similarly, V3 C037 passed the judges despite its manual completeness defect.
These disagreements demonstrate why judge agreement alone is insufficient. V4's
extra coverage also creates additional claims and citation responsibilities;
improving a conclusion on one case does not justify a new error elsewhere.
No outputs were mixed, and previous initial-three successes were not substituted
for new six-case failures.

The continuation used **12 target generations, 92 judgments and 104 counts**, with
zero retries. V3 required 44 judges and V4 required 48, covering every required
point. All twelve target requests and 92 judge requests had exact count/usage
agreement. Maximum target input was 34,122 tokens, below 100K. The first four V3
requests matched the previous stopped run byte-for-byte: changing admission limits
did not change model input. Models, reasoning, 4096 output cap, schema, evidence
and frozen semantic configurations remained fixed.

Reported continuation usage: 399,854 input tokens including cache and 42,420 output
tokens including reasoning. Dated token-price estimate: **USD 0.06342049**. Counting
has a zero planning allowance under the user's assumption; OpenAI counting billing
is still unverified, while Anthropic documents counting as free. The new ledger
reserved USD 4.379232 without refunds; with preserved prior reservations the total
is USD 30.525408, within USD 100. These are accounting estimates, not invoices. Across
both original and resumed 11D: 21 target generations, 137 judgments, 159 counts.

The evaluator now passes validated operational limits from its manifest through
execution into native receipt hooks. Defaults preserve old runs' 32,768 cap and
historical counting allowance; 100K and zero allowance are explicit new-run
configuration. Offline native SDK fixtures verify both providers accept 100,000
and block 100,001 before generation. Frozen judge logic was not retuned.

`make fix`, `make check` (**4,071 passed, one skipped**) and `git diff --check`
passed before calls. Baseline and both earlier evaluations replayed without calls;
both new evaluations also replayed exactly with provider construction/dispatch
disabled. Independent reviews checked the code, prompt isolation, complete panels,
source fidelity, budgets, seals and no-selection decision. All 40 protected bindings
remain unchanged, including the original 11D result and prior run seals. Fresh
validation artifacts retain the source snapshot, reviews, command logs, full
comparison, failures and task-level reservations.

Next: no automatic further prompt cycles. A different prompting strategy requires
a new bounded task and its own comparison criteria. **11E remains unready and was
not begun.** No remaining 13, locked-test or reserved-challenge content was inspected
or evaluated; Task 10 artifacts and all frozen semantic judges remain unchanged.
