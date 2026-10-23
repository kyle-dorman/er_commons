# Task 15C — Run and review revised conclusion judging

Status: six-question run and review complete; expansion stopped by the predeclared gate (2026-10-21).

## Goal and authorization

The user requested the six-question suite with Haiku and Luna, high concurrency,
then the other thirteen if the first results look good, and review/grouping of
all failures. The user clarified both models are judges on the new synthetic
set. This replaces the earlier
discussion-only prohibition for the requested run, not for unrelated experiments.

## Inputs and outputs

Use the accepted Task 15 C prompt, explicit native Inspect adapter selection and
the relevant verified development publication. Preserve frozen defaults, all
historical results and original case bytes. Write fresh external Task 15 run
artifacts with exact inputs, configuration, logs, all failures and review results.

## Plan and learning checkpoint

1. Add explicit candidate prompt selection to the native adapter and verify that
   its system message, schema, scorer and metadata use the same version.
2. Resolve the requested population; record request counts, concurrency, token,
   retry and cost estimates and the continuation gate before making calls.
3. Execute the original six, inspect every disagreement/invalid judgment, and
   apply the predeclared gate before continuing to the remaining thirteen.
4. Preserve all outputs and group failure rationales with representative exact
   examples and uncertainty. Do not equate higher pass rate with better judging.

Inspect's installed API and maintained provider configuration are the execution
references. Reuse native scheduling, logs and bounded retries; no custom HTTP
runner or silent semantic rerolls. Expected synthetic labels remain proposals
outside model messages, and saved target results are a different population.

## Validation and review

Execution is one judgment per sample per model: 212 on the original six,
conditionally 468 on the other thirteen, 680 total maximum logical judgments.
Use sixteen connections per model, two parallel native tasks, 4,096 output
tokens, 150 seconds per sample and at most one native transport retry (1,360
maximum generation attempts). No semantic retries or prompt/label tuning.
Costs use dated configured token prices as estimates, not current billing
guarantees; compute a conservative byte-based input estimate before dispatch.

Continuation gate fixed before results: at least 95% valid responses and 90%
agreement in each expected-pass/expected-fail group for each model, plus no
confirmed critical false accepts after reviewing all disagreements. Distinguish
questionable proposed labels from judge errors without rewriting either. If
either model fails the gate, stop expansion and report the reasons. This is an
engineering screen, not human-gold qualification. The remaining thirteen include
the four familiar-development audit questions; freeze this unchanged candidate
before expansion, preserve partition reporting and do not tune from outcomes.

Focused offline adapter tests must verify candidate dispatch and unchanged frozen
defaults. Run project checks after implementation. Independently review input
selection, identity propagation and grouped failure interpretations. Save the
run decision before dispatch and the continuation decision before stage two.

## Non-goals

No target regeneration, prompt tuning, label rewrites, production promotion,
MiniMax, reserved challenges, thirty-question test execution, commits or pushes.

## Outcome

The native adapter now accepts the explicit Task 15 C prompt across request,
schema, parsing and metadata while preserving default selection checks. Thirty-five
focused adapter tests passed, including offline provider request rendering for
both models. `make fix` and `make check` passed (4,437 passed, one skipped;
105 dependency deprecation warnings). Lead review and `git diff --check` passed.

The [result pointer](../../docs/specs/task15c_synthetic_judging_result.json) selects
212 completed judgments on 106 synthetic cases, one each from Luna and Haiku.
Luna agrees with 105/106 proposals and Haiku 104/106; both have 106/106 valid
outputs and 42/42 expected-pass agreements. Expected-fail agreements are 63/64
and 62/64 respectively. Six-question native execution took about 45 seconds;
Inspect estimates $0.0872 using dated configured prices, not a billing receipt.

All three disagreements received lead and independent review. Luna C056 accepts
an exact every-storm guarantee where the reference predicts approximate flooding
for a 100-year storm: a confirmed critical scope/certainty error. Haiku C014 A01
and A10 omit the explicit future-land-use-input channel but retain inventory,
transportation scopes and regional futures. Whether the omitted channel is
additionally necessary remains disputed; these are not confirmed judge errors.
The external review preserves both arguments and every original judgment.

The critical-negative gate failed, so the remaining thirteen (468 judgments)
were not dispatched. No prompt, labels, selected judge, historical results or
reserved payloads changed. The four synthetic audit questions remain unjudged.
Next discuss the material-scope error and two disputed labels before separately
scoping any revision or expanded execution. No automatic tuning is authorized.

Execution artifacts are sealed under
`pipelines/brisbane_baylands/task_15/judge_synthetic_20261021_v1`.
`review.md` and `review.html` group all disagreements; the latter also shows all
212 exact inputs and judgments. Native logs, input/label sidecars, preflight,
independent review, gate and completion inventory remain together. An initial
unsupported display option failed in local initialization before dispatch;
its failed-stage claim and diagnostic log are retained with a recovery receipt.
The completed run used sixteen connections per model and one bounded transport
retry, without semantic rerolls. Inputs were checked by the sealed loader;
independent preflight confirmed version isolation, concurrency and disjoint stages.

## Authorized repeatability extension (2026-10-21)

The user requested two more rounds on the same six-question synthetic set.
Run two native epochs for each model (424 new judgments), retaining original
round one for 636 combined observations. Preserve the same candidate prompt,
106 input packets, settings, sixteen connections per provider, 4,096 output
limit, 150-second sample limit and one transport retry (848 attempts maximum).
Dated-price conservative estimate is $2.89; no additional population is enabled.

Compare first-round agreement with agreement at least once, all three times and
by majority. Report critical false accepts across rounds as well; any-success
must not hide inconsistent failures. New epochs map to rounds two and three.
Keep all outputs and proposed labels unchanged. Review new disagreements and
recurrence of the previous three. Artifacts use a fresh sibling namespace
`judge_synthetic_repeats_20261021_v1`; the original seal remains immutable.

### Repeatability outcome

The [repeatability result](../../docs/specs/task15c_synthetic_repeatability_result.json)
selects the completed424-call extension and combined636-observation review.
Luna agrees105/106,106/106,106/106 across rounds; Haiku104/106 in each.
Empirical single-call agreement pooled over three rounds is317/318 (99.7%)
for Luna and312/318 (98.1%) for Haiku. At-least-once agreement is106/106 and
104/106; all-three agreement is105/106 and104/106. All outputs are valid.
Luna's C056 critical false accept occurs only in round1; both new rationales
correctly identify changed scope/certainty. Haiku repeats the two disputed C014
labels every round. All four new disagreements were reviewed; no new mechanism
appeared. Repeats do not erase the observed error or enable the other thirteen.

Independent verification confirms636 unique model/sample/round observations,
exact input/label and configuration equality, recomputed metrics and preservation
of the original completion hash. Extension runtime was78 seconds; estimated
cost $0.1658 using dated prices. Artifacts retain all triples, raw logs,
independent review and every rationale in `review.html`. No package code changed
for this extension; validation was artifact/metric verification and diff checking.
