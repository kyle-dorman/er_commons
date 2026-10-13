# Task 09E.1 — Frozen-claims conclusion comparison

The user authorizes one bounded comparison of the existing conclusion reviewer
with prior claim verdicts hidden, then explicitly adds a conclusion-only arm and
comparison of its claim reviews against the original claim judge. Claims are
frozen at the selected simple Dev6 baseline. Existing conclusion grounding,
necessary-premise checks, separation from completeness, and coverage reporting
are already part of our approach; they are not new interventions in this test.

## Fixed inputs and three arms

Use the eleven original inconsistent answers from the preserved cache/pipeline
experiment, plus the lexicographically first remaining answer in each of the six
Dev6 cases. This gives seventeen answers and 59 original claim judgments. Keep
the original answer, question, citations and evidence unchanged. Resolve the
fixed judgments from the sealed Dev6 baseline's actual successful claim results;
verify exact claim-input parity and ordered IDs. Do not regenerate claims, run
the abstention gate, rewrite answers, truncate evidence or access other cases.
Read the 09A.3 pointer before artifacts and verify all consumed bindings.

| Arm | Prior claim predictions in request | Requested judgments | Final aggregation |
| --- | --- | --- | --- |
| `visible` | Ordered IDs and Boolean values, as today | Conclusion and every claim review | Existing disagreement gate and rubric |
| `blind` | Ordered IDs only | Same conclusion and claim reviews | Identical existing gate and rubric |
| `conclusion_only` | No prior-assessment field | Conclusion support and clean-abstention status only | Frozen original claims plus genuine conclusion; no second-review gate |

Visible and blind have identical existing conclusion instructions and output
schema. Strip only prior Boolean observations before rendering the blind native
request, exact counting, caching and generation. The original validated vector
remains offline for genuine output validation and aggregation; do not substitute
dummy observations or fabricate matching reviews.

The conclusion-only prompt removes the prior-prediction/review instructions and
review output requirements, retaining the same conclusion-support rubric and
original evidence. Its schema genuinely omits claim reviews. This arm changes
both the reviewer task and the disagreement gate; it is a deliberate pipeline
ablation, not a pure test of verdict visibility. Offline aggregation preserves
0 for unsupported conclusion, 1 for supported conclusion with any frozen
unsupported claim, 2 for supported conclusion with all frozen claims supported,
and N/A only for validated clean abstention. Malformed output remains unscored.
No package default changes or automatic promotion are authorized.

## Execution and stops

Run three fresh repetitions of every answer in each arm: 51 calls per arm,
153 total. Use only `gpt-6-luna`, Responses generation, medium reasoning,
4,096 output allowance, qualified evidence-prefix caching and exact native
token preflight/parity. Each arm has four concurrent samples, a shared $1
conservative reservation cap and 1,800-second wall limit. Total ceiling is $3.
Each arm has a separate cache key; saved-response reuse is forbidden.

On failure, halt new scheduling, preserve already in-flight calls and all
failures, and do not retry or replace a judgment. Partial runs remain partial.
Load credentials inside code from `.env` without printing or serializing them.
No other models, broader panel, reserved/test content, later tasks, commits or
pushes. Stop after these three passes and their analysis/review.

## Analysis fixed before dispatch

Keep expected labels and their reasons outside preparation and model requests.
Load the maintained Dev6 expectations only after all three arm summaries exist.
Report separately, overall and for trouble/control subsets:

- Conclusion-support agreement with proposed labels, false acceptances and
  false rejections, with valid-output and all-slot denominators.
- Claim-review agreement versus the frozen original claim judge on the exact
  same 59 claims: unique original accuracy, repeated comparable denominator,
  paired corrections and damaging reversals. No review accuracy exists for the
  conclusion-only arm; do not count copied original values as new reviews.
- Existing aggregate numeric coverage and accuracy, status counts, clean
  abstention behavior, and fixed-input repeatability across three fresh calls.
- Same-input visible/blind comparisons; separate the conclusion-only coverage
  benefit of removing the disagreement gate from actual conclusion accuracy.
- Per-question results, exact duplicate groups where present, quotation
  diagnostics, native input/output/cache tokens, estimated cost and latency.

Independently inspect changed conclusion decisions, false acceptances and claim
corrections/reversals against the original source. Preserve defensible alternative
readings and label ambiguity without modifying labels or replacing headline
agreement. This is a small deliberately difficult development set, not an
independent test or human-calibrated accuracy estimate. Three repeats measure
observed repeatability only. Do not promote merely for improved coverage.

## Artifacts and validation

Fresh namespace:
`task_09/09e1_20261012_luna_conclusion_blind_v1/`. Bind this contract, launcher,
analyzer, preparation, input packets, frozen claim results, condition, exact
prompts and implementation identity before inference. Preserve earlier sealed
namespaces and their bindings. Inspect owns execution, samples and logs.

Use a narrow opt-in adapter with default request/identity parity, focused tests
for hidden native payloads, common schema, exact-counter parity, genuine review
validation and conclusion-only score boundaries. Independently review adapter,
launcher, label isolation and budget guards before dispatch. Run focused tests,
`make fix`, `make check` and `git diff --check`; historical baseline is 4,259
passed, one skipped and three Task 06G failures. Scan raw and decoded Inspect
artifacts for credentials, publish completion last, and bind final evidence in
a small tracked pointer. Record any partial execution or validation limits.
