# Task 09F.1 — Haiku boolean diagnostic

Authorized by Kyle on 2026-10-16: investigate Haiku on examples where explanations
are right but the supported boolean is wrong. Leave the recreation failure aside.
This bounded diagnostic runs **24 new judgments**: the locked thistle contrast
G-C029-014 (supported) and G-C029-015 (unsupported), three repetitions in each of
four fixed arms. Both labels/text/evidence remain unchanged. Stop after these arms;
no automatic full-panel expansion, further prompt search or model selection.

## Question and design

The v2 prompt already explicitly names units, before/after/until/unless, arithmetic
direction and boolean/reason consistency. In the v2 Haiku thistle outputs, supported
appears before reason. Several explanations conclude the opposite of the boolean.
This suggests two testable possibilities, not established diagnoses: confusion
between whether a restrictive statement is evidenced and whether an action is
permitted, or committing to the boolean before writing the evidence assessment.

| Arm | Clarification | Output order |
| --- | --- | --- |
| baseline | Exact existing v2 | supported, reason |
| polarity | Explicit truth mapping below | supported, reason |
| reason_first | Existing v2 semantics | reason, supported |
| combined | Explicit truth mapping | reason, supported |

The polarity addition is generic, without thistle names, facts or expected labels:

> The supported field answers only this question: Does the supplied evidence establish the candidate point as written? true means yes, the point is supported. false means no, at least one material assertion is unsupported or contradicted. A statement about a prohibition or restriction can itself be supported; judge whether the evidence establishes that statement, not whether the underlying action is permitted.

Reason-first arms change the prompt's field listing/order instruction and the native
schema's property/required order, preserving exactly the same keys and types. They
add: “Write reason first, then supported. Assess the evidence in reason before
choosing the Boolean verdict.” This is a joint presentation/order treatment; it does
not isolate prompt order from schema order. Observe actual returned field order,
rather than assuming schema order guarantees it. The strict parser remains unchanged.

The positive and negative pair prevents a constant boolean from looking successful.
Repetition measures observed consistency only. These are deliberately selected known
failures, not independent or representative test cases. A successful arm is a lead
for later validation, not evidence of general grounding improvement.

## Execution and validation

Use `src/er_commons/point_grounding_boolean_probe.py@haiku_boolean` with one of the
four fixed arm names. It uses native Inspect and the current Haiku profile, 4,096
output tokens, medium reasoning, three epochs, one sample/connection, 150-second
sample time limit, two Inspect transport retries, zero whole-sample retries and
response-result caching off. Retain the $0.10 per-sample soft cost limit; no hard
aggregate invoice cap is claimed. Native logs replace custom execution receipts.
The 24 planned generations are distinct from possible transport attempts.

Keep all original outputs, including contradictions and invalid results. Score the
boolean as emitted; never override it from the explanation. Independently inspect
reason/verdict agreement after the run. Keep full payloads, prompts, schemas,
configuration, labels and reports in a fresh external namespace:
`pipelines/brisbane_baylands/task_09/09f1_g_haiku_boolean_probe_v1/`.

Before dispatch: offline tests verify exact selected cases, generic-only prompt
changes, baseline equality, both schema orders, native request serialization and
no extra generation. Run formatting/lint/type checks and bounded independent review.
Afterward: validate 6 observations per arm, identities, field order, native scores,
errors, cost and source-grounded explanation consistency. Preserve v1/v2 defaults,
other model runs, A/C/S work and all earlier artifacts.

This composes the current G implementation with native Inspect's
[structured-output controls](https://inspect.aisi.org.uk/structured.html) and
[custom scoring](https://inspect.aisi.org.uk/scorers.html); it adds no transport,
re-review model call, new label schema or answer-routing logic.

## Outcome

The [saved result](task09f1_haiku_boolean_probe_result.json) records all 24 fresh
judgments. All outputs were valid, and returned field order matched each arm.

| Arm | Correct / 6 | Cases correct in all three repetitions | Boolean/reason contradictions |
| --- | --- | --- | --- |
| Existing v2 | 3 | 1 / 2 cases | 1 |
| Explicit boolean meaning | 3 | 1 / 2 cases | 1 |
| Explanation first | 5 | 1 / 2 cases | 0 |
| Both changes | 6 | 2 / 2 cases | 0 |

Every arm accepted the supported thistle statement three times. The remaining
errors were false accepts of the reversed timing statement. Baseline and polarity
each had one explanation ending in contradiction while emitting true, plus two
explanations that misread the candidate's before condition as after. Explanation
first eliminated observed verdict/reason contradictions but still made one timing
error. The combined arm got both timing directions right on every repetition.

The useful lead is to assess evidence before emitting the verdict, together with
an explicit definition that supported concerns whether the statement is evidenced,
including statements about restrictions. Clarification alone did not improve this
pair. These observations do not establish the model's internal cause or a reliable
general fix: only two selected known failures were tested. Reason-first also changes
both prompt presentation and provider schema order. No default or model selection
changes, further iterations, or broader run follow automatically from this result.

Validation: six dedicated offline tests and full `make check` passed (4,881 tests
passed, one skipped; formatting, lint and type checks passed). Independent reviewers
checked implementation and all 24 explanations. Estimated native usage cost was
$0.02197545 at the recorded profile rates, not an invoice reconciliation.
