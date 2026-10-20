# Task 11D.4 — Alternative-model coverage on the fixed six

Status: Complete with limitations (2026-10-18); no additional coverage or selection.

## Abstract and goal

The user authorized trying the other two configured models, including explicit
JSON wording for GLM, to learn whether models succeed on different questions and
whether at least one can pass each question. Run Haiku 5.5 and GLM-5.3-Flash on the
fixed six with V6b. Stronger models are explicitly deferred. Cross-model failure
is a diagnostic to investigate, not proof that a question is defective.

## Inputs and outputs

Use accepted 11A fixed panels, sealed 11D.1 V6b Luna repeats, 11D.2 manual review
contract and known metadata limitations, 11D.3 original-question decision, frozen
09G judges, original Task 10 evidence and approved references. Output native
requests/raw responses/counts/usage, complete identities and coverage, independent
source review, replayable reports, model-by-question matrix and explicit union
coverage. Detailed artifacts live in a fresh external Task 11 validation namespace.

Main comparison has 36 observations: twelve saved Luna V6b outputs plus 24 new
outputs. Keep the four C014-only 11D.3 observations separate as historical context;
do not add a favorable C014 sample to the main panel. No changes to sealed runs.

## Design and hypothesis

Fixed order C041, C017, C019, C014, C037, C056. Run Haiku r1, GLM r1, GLM r2,
Haiku r2, all six per run. Model IDs are `claude-haiku-5-5` and
`accounts/fireworks/models/glm-5p3-flash`, using maintained Inspect providers.
Hypothesis: different model errors may complement Luna's coverage, with some
questions passed consistently by at least one model. No prompt tuning after
observing outputs. Retain original questions, evidence metadata and V6b examples;
do not activate 11D.2 metadata projection or 11D.3 revised question.

Haiku uses native structured output. GLM receives the same V6b obligations plus
explicit JSON-only wording and the exact answer schema in its system prompt,
without response_format if that disables reasoning. Record this provider-format
difference rather than claim identical on-wire prompts. Request medium effort
with provider-native settings; equal labels are not equal compute budgets. Keep
frozen A/G/C Luna and S Haiku judges unchanged. Reference answers, case diagnoses
and evaluator feedback never enter generation.

## Limits and stopping rules — before dispatch

At most 24 new generations, 384 judgments (16 per candidate), 408 count calls,
zero retries, repairs, replacement outputs or additional repeats. Generation and
judge output cap 4,096 including reasoning under their existing settings. Record
all 24 planned slots even if execution stops. A malformed model answer is an
observed failure and may be followed by the next planned question; it is never
repaired or omitted. Stop affected-provider scheduling on transport, context or
accounting failure; stop globally on integrity or isolation failures. Do not omit
points to fit judgment fan-out; record an evaluator limit failure. An independent
unaffected provider may complete its own predeclared slots.

Maintain the 100,000 native-input-token ceiling. Anthropic uses its native count
endpoint with actual input/schema; documented estimates are not mislabeled exact.
Fireworks lacks a verified exact preflight counter: use a separately named
exploratory allowance of serialized native request UTF-8 bytes plus 8,192 for
framing, capped at 200,000 and fitting the documented model context with output
reserve. This is a conservative assumption, not a tokenizer guarantee or an
exact 100K preflight gate. Require reported native input usage <=100K after each
call; otherwise stop and retain the uncertainty. Never truncate evidence.

Reserve **USD 13** for this task, retaining prior USD 45.740432 liability for a
combined USD 58.740432 under the USD 100 ceiling. This covers 24 generations at
200K input/4096 output and 384 judges at100K/4096 using conservative inherited
USD .25/.75 per-million reserves (USD12.053376), with remaining headroom. Counting
allowance is zero under the user's prior assumption; actual count charges remain
unknown. Price estimates are dated, not invoices; do not refund reservations.
Maximum one working day, 15 minutes per generation, 30 minutes per candidate's
judging. Save dispatch intents before calls and disable SDK and Inspect retries.

## Plan and research / learning checkpoint

1. Verify official provider JSON/reasoning/count/context behavior and installed
   Inspect interfaces. Prefer maintained provider clients and existing project
   evaluation routines. Save sources and provider-specific limitations.
2. Implement narrow alternative-generation adapter with tests. Preserve native
   hashes; explicitly derive and hash a canonical delivery projection for the
   existing evaluator, never mislabeling it a native request.
3. Freeze configuration, prompts, limits and preflight bindings; independently
   review once plus a repair recheck. Validate offline before dispatch.
4. Generate all predeclared observations, evaluate all eligible answers, and
   independently review complete source evidence before inspecting judge verdicts.
5. Replay without providers, audit identities/receipts/accounting/protected files,
   produce per-model and cross-model coverage and update routing.

## Reporting and acceptance

A frozen diagnostic pass requires valid schema/resolved citations, complete
applicable coverage, substantive A, every required G pass, and S/C pass. Errors,
missing judgments and invalid answers are never passes. Show each repeat and
point denominator; do not construct a composite answer from multiple outputs.

Report per-question model counts, observed union (some model passed at least
once) and repeat-stable union (some single model passed both repeats). The former
is optimistic hindsight, not a deployable model selector. Keep manual material
source/logic/completeness findings and judge disagreements separate from frozen
scores. Reuse exact baseline reviews with their scope limits; do not silently
mix old and new acceptance criteria. No automatic promotion from union coverage.
A question with no pass calls for diagnosis of model, evidence, specification and
judge limitations; it does not automatically justify weakening the benchmark.

## Validation and review

Read architecture/data/documentation contracts. Offline tests cover provider
native input isolation, schema handling, no retries, count/usage boundaries,
receipt capture, invalid-output retention, canonical delivery and replay. Run
make fix, make check and git diff --check for code changes. Independent review
covers provider boundaries and budget/coverage before calls, then source quality
and accounting afterward. Preserve rejected preflight versions and failures.

## Non-goals

No stronger model, remaining 13 development, locked test or reserved content;
no 11E, model router implementation, judge retuning, reference revision, metadata
intervention, evidence truncation, changed question publication or prompt cycling.

## Provider research recorded before dispatch

Verified official sources on 2026-10-18:

- [Haiku 5.5 overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview):
  exact configured model, 1M context, adaptive medium effort and no sampling
  overrides; <=100K tier USD .10/.50 input/output per million.
- [Anthropic token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)
  and [count endpoint](https://platform.claude.com/docs/en/api/messages/count_tokens):
  retain native system/messages/schema fields; preserve estimate versus usage.
- [Fireworks GLM model](https://fireworks.ai/models/fireworks/glm-5p3-flash):
  exact configured ID, 1,040K context and USD .15/.50 input/output per million.
- [Fireworks structured output](https://docs.fireworks.ai/structured-responses/structured-response-formatting):
  explicit JSON and schema-in-prompt guidance; schema-enforced response formatting
  disables reasoning, motivating the user-requested JSON wording instead.
- [Fireworks chat API](https://docs.fireworks.ai/api-reference/post-chatcompletions):
  request context-overflow errors; do not use prompt truncation. No standalone
  exact count endpoint was verified. Retain that limitation rather than inventing
  an exact counter or issuing undocumented zero-output generation probes.

The USD .25/.75 reserve rates exceed these verified <=100K input/output prices
and known cache-write rates. Final cost is still an estimate rather than billing.
The two providers' native envelopes differ, so replay must independently derive
and bind canonical delivery from the actual request; merely constructing an
expected delivery fixture does not prove what was sent.

## Outcome

All 24 planned new generations ran exactly once. Sixteen valid answers received
complete frozen evaluation; eight invalid outputs remain failures. Compare them
with the twelve sealed Luna V6b observations, without pooling 11D.3's separate
C014 experiment. The [result pointer](../../docs/specs/task11d4_result.json) binds
raw responses, native requests, receipts, exact candidate/run/repeat/point
identities, both blind reviews, final audit and replayable reports under
`pipelines/brisbane_baylands/task_11/validation_11d4_20261018`.

### Fixed-six coverage

Entries are frozen diagnostic passes out of two planned observations, including
invalid outputs in the denominator. A pass requires valid schema and citations,
complete coverage, substantive A and every applicable G/S/C judgment passing.

| Question | Luna V6b saved | Haiku 5.5 | GLM-5.3-Flash |
| --- | --- | --- | --- |
| C041 animal controls | 2/2 | 0/2 | 1/2 |
| C017 energy assumptions | 2/2 | 0/2 | 0/2 |
| C019 landfill infiltration | 2/2 | 0/2 | 0/2 |
| C014 cumulative transportation | 0/2 | 0/2 | 0/2 |
| C037 temporary wetland loss | 2/2 | 0/2 | 1/2 |
| C056 residual flooding | 2/2 | 1/2 | 0/2 |
| Total observations | 10/12 | 1/12 | 2/12 |

Both observed union and repeat-stable union cover five of six questions; Luna
already supplies all five. Neither alternative expands coverage. These are
adaptively exposed diagnostic cases, not an estimate of general model quality
or evidence for a deployable model router. No candidate is selected.

### Failure mechanisms and manual review

Haiku exhausted the 4,096 output-token allowance on both C014 observations;
reasoning consumed essentially the entire allowance. This is an output-budget
failure, not evidence that Haiku cannot answer that question at another budget.
GLM produced five Markdown-fenced JSON outputs despite the explicit no-fences
instruction, and one otherwise JSON answer omitted required `applies_to`.
Those six outputs were retained without repairs or semantic judgments.

Both valid GLM C014 answers misclassified TRA-4 emergency-response analysis as
list-based; the supplied table says projections-based. This is a concrete model
reading error. Its metadata-related grounding failure is separately constrained
by the inherited edition-projection mismatch. Shared C014 nonpasses do not prove
the question is defective: model reading, output limits, reference completeness
and evaluator visibility remain distinct explanations.

Independent reviewers read all sixteen valid new answers against complete source
packets before seeing scores. Conclusion-source review found ten passes and six
material defects; eight invalid outputs remain outside that substantive review
denominator. Separate whole-answer findings include conclusion qualifications,
missing stated premises, unsupported wording and citation ownership. A raw G/S/C
pass does not certify conclusion-source correctness: GLM C037 repeat 1 passed
judges while its conclusion omitted the owned citation for named mitigation
measures. Conversely, manual source acceptance does not overwrite frozen scores.
The final independent audit preserves representative disagreements separately.
Haiku C037 failures include a proposed-status visibility sensitivity and likely
overstrict rejection of an excerpt-scoped absence claim. Haiku C019 qualification
failures have a more defensible own-citation limitation: the cited agency letter
alone does not establish the asserted modeled-outcome connection. GLM C014 also
omits its owned project-name-to-number mapping citation. These diagnoses do not
change scores or authorize another judge pass.

### Validation and accounting

`make fix`, `make check` (4,124 passed, one skipped) and `git diff --check` passed.
The independent predispatch review passed after repairing global stopping on
unexpected native request shape; 21 adapter tests and three scheduling tests
passed. All 24 new slots and twelve historical plans/reports replay without
providers. All 255 protected bindings remain unchanged. No SDK retries,
replacement outputs, extra repeats or additional model calls were used.

Actual calls: 24 generations, 152 judgments, 164 counts; 340 total requests.
Known usage: 728,153 input tokens including cache and 99,337 output tokens
including reasoning. The dated-rate token estimate is USD 0.125187775 for the
whole new comparison, excluding unknown count billing; it is not an invoice.
Retain the USD 13 reservation and USD 58.740432 combined liability. Fireworks
used the documented exploratory byte allowance, not a claimed exact counter.
No usage records are missing.

### Decision and learning

Retain original questions and V6b; the explicit JSON wording alone did not make
GLM formatting reliable. Native format enforcement and a larger Haiku output
allowance would be separately versioned interventions, because they change
reasoning or compute conditions. They were not attempted here. Do not infer that
question weakening or a stronger model is necessary from this run. Stronger
models remain deferred, the metadata correction remains staged, and 11E remains
unready and unstarted. Locked test, reserved challenges and the other thirteen
development cases were not inspected or evaluated.
