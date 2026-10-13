# Updated GLM repair, partial DeepSeek run and failure patterns

All nine targeted GLM conclusions now validate and match the proposed labels,
including their numeric scores. DeepSeek used the doubled 8,192-token output
allowance, but stopped on an uncertain 180-second transport timeout. Its final
claims population has 822 valid outputs, nine failures and 225 undispatched
items; no conclusions ran. This follow-up is complete with a partial DeepSeek
evaluation, not a completed four-model pipeline comparison.

## Current results only

The unchanged population is 19 development questions, 1,056 claims and claim
reviews, 392 substantive conclusions/numeric targets, and 38 separate clean N/A
answers. Luna is the retained original configuration; Haiku includes its accepted
selective repair; GLM includes the nine new repairs. No original/stale alternative
rows are included.

| Configuration | Claims macro-F1 | Claim-review macro-F1 | Conclusion macro-F1 | Numeric macro-F1 | Numeric outputs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna retained | 93.46% | 96.96% | 92.93% | 88.51% | 350/392 |
| Haiku updated | 93.23% | 94.84% | 96.05% | 89.05% | 354/392 |
| GLM Flash updated | 97.50% | 94.64% | 95.67% | 91.76% | 352/392 |

These are coverage-aware class-macro F1 scores: missing/invalid predictions remain
false negatives for their true class, without fabricating a predicted class.
They are distinct from conventional F1 conditional on a usable output. Every
failure also counts as wrong in the full-denominator correct counts below.
Claim reviews are the conclusion judge's reassessment of the individual claims.

| Configuration | Claims correct / 1,056 | Claim reviews correct / 1,056 | Conclusions correct / 392 | Numeric correct / 392 | N/A correct / 38 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna retained | 1,012 | 1,037 | 370 | 328 | 38 |
| Haiku updated | 1,011 | 1,018 | 379 | 331 | 38 |
| GLM Flash updated | 1,037 | 1,007 | 364 | 341 | 38 |

GLM's substantive conclusions comprise 364 correct, three incorrect and 25
missing/invalid outcomes: twenty older invalid conclusions and five dependent
skips from invalid claims. The nine repaired answers had empty claim lists, so
their repair changes conclusion/numeric results but not claim-review metrics.
Numeric outcomes comprise 341 correct, eleven incorrect and forty missing:
the twenty-five missing conclusions plus fifteen unresolved claim/review
disagreements. Conditional conclusion/numeric F1 is 98.90%/96.92%; those higher
values must not replace the full-denominator results.

DeepSeek has **808 correct of 1,056 planned claims** (76.52% full-denominator
accuracy), with 822 usable outputs (77.84% coverage). Fourteen usable judgments
disagree with labels. Coverage-aware claim F1 is 84.83%; conditional F1 on the
822 usable outputs is 97.15%. That selected, scheduling-dependent subset is not
a full-panel model ranking. Downstream coverage is zero; the machine-readable
report retains zero full-denominator downstream scores as missing coverage,
not observed wrong conclusion judgments.

## Are the models failing on the same things?

Mostly different exact claims, with some recurring question-level patterns.
To distinguish semantics from output failures, the matched comparison below uses
only the 819 original claims with valid judgments from all four models. It is
descriptive and does not replace the full denominators above.

| Matched original claims | Luna | Haiku | GLM | DeepSeek |
| --- | ---: | ---: | ---: | ---: |
| Label disagreements / 819 | 34 | 42 | 13 | 14 |
| Disagreements unique to that model | 20 | 30 | 1 | 2 |

Only **one exact claim** disagrees with the label across all four. Pairwise shared
disagreements are Luna/Haiku 8, Luna/GLM 6, Luna/DeepSeek 8, Haiku/GLM 8,
Haiku/DeepSeek 5 and GLM/DeepSeek 6. Models can struggle with the same question
while rejecting different claims within it.

Examples of question concentration, counting valid semantic disagreements and
showing output failures separately:

| Question | Claims | Luna wrong | Haiku wrong | GLM wrong | DeepSeek wrong |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cumulative health risks (C001) | 70 | 4 | 4 | 3 | 3 |
| Bayshore lane reduction (C007) | 65 | 7 | 6 | 0 | 4 + 1 invalid |
| Diverted traffic (C008) | 63 | 1 | 8 | 0 | 0 |
| Artificial lighting (C036) | 41 | 5 | 4 | 4 | 2 |
| Temporary wetland function (C037) | 59 | 0 | 6 | 1 | 0 |
| Animal controls (C041) | 53 | 6 | 3 | 2 | 0 + 2 failed |
| Park deterioration (C042) | 73 | 1 | 4 | 4 + 1 invalid | 3 + 3 failed + 8 unsent |

The construction-equipment question (C006) has 64/64 correct claims for every
model. DeepSeek did not attempt four complete questions (C045, C050, C051,
C054), so absence of errors there says nothing about its ability. The full
external analysis contains all nineteen question denominators and outcomes.

Bounded source review identifies several different mechanisms:

- **Shared scope extension:** all four accept C001-P06/P5, which extends a
  buildout-only health-risk table to both development and buildout. This is a
  concrete evidence-scope concern, not just literal quotation wording.
- **Summary versus attribution sensitivity:** DeepSeek rejects a rail-noise
  claim's use of “setback” for a source's “buffer distance.” It also rejects a
  wildlife-lighting claim over attribution to a “biological report,” despite
  acknowledging the substantive effects. These are plausible over-literal
  rejections or attribution-policy disagreements, rather than fabricated facts.
- **Timing inference:** GLM and DeepSeek accept park claims that add “At full
  buildout” to the source's total park provision. The cited text supports the
  quantities, reciprocal access and overuse assessment, but does not state that
  timing qualification. Whether the addition is a reasonable summary or an
  unsupported temporal restriction is a label-boundary issue needing adjudication.
- **Specific identity and conflation errors:** historical Haiku examples overlook
  BIO-1f versus BIO-1b and merge building-height and view-corridor benefits.
  These require preserving which measure supports which statement.
- **Validation is a separate shared weakness:** DeepSeek fails the exact
  unresolved-citation claims previously repaired for Haiku, including C029-C05/P3,
  which remains invalid in GLM. Haiku's current advantage on those items includes
  a selective prompt repair; it is not a clean model-only difference.

For conclusions, DeepSeek cannot participate. On 365 substantive conclusions
with valid outputs from Luna, Haiku and GLM, their semantic disagreements are
22, 11 and 3 respectively. Only one exact conclusion is shared by all three;
all three GLM semantic disagreements also occur in Haiku. Luna's animal-control
question contributes six of its 22 conclusion disagreements; Haiku has one
there, while GLM has no semantic disagreement but four invalid outputs.
On 1,021 mutually valid claim reviews, disagreements are 18/28/22, with nine
shared by all three. Thus shared trouble is more evident in reassessing claims
than in the final conclusion verdict alone.

The shared conclusion error is especially informative: C029-F07 states a
five-year program followed by ongoing management without preserving the source's
condition. All three models flag that omission in claim P3 but accept the same
omission in the conclusion, emphasizing its main “no” answer. This is inconsistent
application of the scope rule across stages, not missing source information.
The other two GLM/Haiku shared conclusion disagreements (C008-C03 traffic diversion
and C051-C01 scenic views) have support in the full-answer evidence and disputed
attribution or inferred premises; they should not be described as clear fabrication.

The practical lesson is to separate evidence-scope mistakes, reasonable-summary
disputes, and response-contract failures. A single broader prompt adjustment
would target different problems across models. These findings support a small
source-adjudicated error set before further prompt tuning; they do not authorize
label changes or establish that every synthetic proposed label is correct.

## Runtime, caching and cost

GLM received only the explicit empty-list instruction in the
[frozen contract](task09e1_fireworks_repair_8192_v1.md), with its prior 4,096-token
allowance. All nine retries succeeded. Twenty older invalid conclusions remain,
including fourteen older empty-list failures outside the nine-item retry scope.
Other retained GLM errors include invented extra reviews, extra fields and JSON
syntax failures. Haiku retains two invalid conclusions that omit a required
qualification claim review.

DeepSeek retained the original semantic prompts and used 8,192 output tokens.
The first twenty new attempts included one uncertain 60-second timeout. The
[runtime addendum](task09e1_deepseek_timeout_continuation_v1.md) then ran only
previously undispatched requests with a 180-second timeout, retaining that failure
and the original cumulative spending cap. A second uncertain timeout stopped
this continuation after 763 attempts. Neither uncertain request was replayed.

Across the two new DeepSeek phases, 781 responses have known usage and two
requests have unknown outcomes. Fifty completed responses exceeded 4,096 output
tokens; twenty-nine completed requests exceeded sixty seconds. Three responses
still exhausted 8,192 tokens and remain individual failures. The other completed
new failures were two unresolved locators and one extra-field schema error.
The earlier invalid locator remains in the merged population. The final stop
was transport uncertainty, not another automatic stop on an individual length
failure. No further timeout/output escalation or conclusion inference followed.

| New work in this follow-up | Known native-token cost estimate | Cached-input share |
| --- | ---: | ---: |
| Nine GLM retries | $0.00437090 | 0% |
| Both DeepSeek 8,192-token phases | $1.619348076 | 68.81% |
| Total | $1.623718976 | — |

DeepSeek's known usage is 2,528,018 input and 1,143,641 output tokens. Output
accounts for 84.75% of its estimated cost, so strong input caching cannot remove
most of this run's expense. Its $13.110138 reservation is a conservative bound,
not spending; it includes $0.0146046 and $0.0191679 reserved for uncertain
requests. Charges for those requests are unknown. The prior 49-attempt DeepSeek
phase cost $0.088671180 separately; including it gives $1.708019256 known
evaluation cost, excluding earlier cache probes. Estimates use the frozen native
rates and are not provider invoices. GLM's small changed-prompt retry batch had
no observed cache reads; the previously established cache gate remains preserved.

## Verification and limits

The package change narrowly permits the pinned DeepSeek condition to use 4,096
or 8,192 output tokens; other providers remain at their authorized limits.
Thirty-five focused package tests passed, as did `make fix`. `make check` returned
4,324 passed, one skipped and the same three historical Task 06G failures.
Twenty-two final offline analysis/timeout tests passed. Independent verification
checked 1,920 confusion/F1 calculations, eight direct metric recomputations,
native usage/stop accounting and source examples. All 26,632 predecessor artifact
files remain unchanged. Final report review, credential scan, diff check and
completion seal are recorded in the result pointer.

The comparison mixes retained runs, selective prompt repairs and output/runtime
settings; provider-owned claim vectors differ. Fireworks maps DeepSeek's requested
medium effort to native high, so “medium” is not equal compute. Labels remain
synthetic proposals, repeated variants are correlated, and single passes do not
measure stability. No defaults, labels, reserved/test data, later tasks, commits
or pushes changed. See the [result pointer](task09e1_fireworks_repair_8192_result.json)
for the frozen analysis, complete per-case metrics, overlap IDs and audit receipts.
