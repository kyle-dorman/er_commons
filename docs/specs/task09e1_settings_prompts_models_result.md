# Task 09E.1 — settings, prompt and model results

The October 12 user-authorized experiments preserve the original 69-answer Dev3
panel and all earlier artifacts. The [predeclared contract](task09e1_settings_prompts_models_v1.md)
owns selection rules, budgets and primary API sources. No Dev6, full-19, reserved
or test expansion occurred. Synthetic expectations and the source-review
interpretations below are diagnostics, not adjudicated ground truth.

## Settings on inconsistent claims

Eight distinct original requests, covering fourteen reversal instances in eleven
Luna answers, received three fresh generations per condition. Four clearer claims
supply twelve source-review comparisons; four ambiguous pet-policy formulations
contribute only consistency diagnostics. Caching never substitutes a saved answer.

| Luna settings | Valid / 24 | Clear-review agreement / 12 | Unanimous claims / 8 |
| --- | ---: | ---: | ---: |
| Low reasoning, default sampling | 24 | 7 | 3 |
| Medium reasoning, default sampling | 24 | 10 | 4 |
| No reasoning, temperature 1 | 21 | 7 | 3 |
| No reasoning, temperature 0 | 24 | 3 | 6 |

Medium wins the frozen selection rule. Temperature zero is more consistent but
worse on the clearer interpretations, and still varies on two claims. Four of
its unanimous claims are ambiguous; two consistently reject bounded-absence
claims supported by the source review. Temperature one without reasoning hit the
4,096-token output cap once and stopped its final two planned calls. Reasoning
and sampling cannot be conflated: the temperature pair disables reasoning, while
the low/medium pair uses default sampling (native temperature 1, top-p .98).

The first temperature arms were rejected by the count-only endpoint for an
unknown `temperature` parameter, before any generation or reservation. A narrow
counter repair strips generation-only sampling fields from counting while binding
the full generation request hash. Fresh repair directories preserve both failed
attempts; low/medium were not repeated. The entire settings phase, including
repair, finished before its original deadline.

## Five prompt ideas

All five additions were frozen before dispatch, appended independently to the
original prompt, and tested at medium reasoning with the same three repetitions.

| Addition | Clear-review agreement / 12 | Unanimous claims / 8 | Decision |
| --- | ---: | ---: | --- |
| None: medium baseline | 10 | 4 | Comparator |
| Preserve scope and qualifications | 11 | 3 | Abandon: item regression and less consistency |
| Distinguish bounded absence | 10 | 4 | Abandon: item regression, no consistency gain |
| Clarify grammatical attachment | 10 | 3 | Abandon: no improvement |
| Combine those three rules | 12 | 7 | Selected diagnostic candidate |
| Balanced assertion checklist | 12 | 6 | Improved, secondary candidate |

All 120 prompt trials returned valid judgments. The combined addition helps, but
its explanations are imperfect: one grading rationale overstates what the source
establishes, and one policy rationale invents an outside-area scope problem.
Otherwise equivalent policy claims with different original citation IDs still
show different patterns. This does not establish that IDs caused the difference.
Seven unanimous claims therefore do not establish seven correct interpretations.

A follow-up compared original versus combined prompts on the eleven original
conclusion/review requests at medium reasoning, holding original binary point
observations fixed. Both produced ten unresolved answers and one numeric score
(the same C041-C01 score of zero). Clearer review interpretations improved from
4/5 to 5/5, solely on F07/P4's bounded absence. The grading review was supported
in both arms. This fixed-context test cannot demonstrate an end-to-end gain;
no prompt or setting was promoted into the default judge or full-panel runs.

## Full-panel comparison

Both new runs use original prompts, low reasoning, exact token counting, no
truncation, and pinned available snapshots: `gpt-5.4-2026-03-05` and
`gpt-5.4-mini-2026-03-17`. Each completed all 69 answers once after a successful
protocol smoke. No automatic retries or saved-result replay occurred.

| Model | Numeric / 69 | Numeric matching proposals | Clean N/A | Unresolved | Invalid output | Panel minutes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original Luna | 52 | 47/52 | 6 | 11 | 0 | 20.9 |
| GPT-5.4-mini | 55 | 44/55 | 6 | 7 | 1 | 13.8 |
| GPT-5.4 | 54 | 52/54 | 6 | 7 | 2 | 30.3 |

| Model | Point agreement (valid / 166 population) | Conclusion agreement (valid / 63 population) |
| --- | ---: | ---: |
| Original Luna | 151/166 | 56/63 |
| GPT-5.4-mini | 146/165 | 58/62 |
| GPT-5.4 | 156/164 | 60/61 |

All three classify the six clean abstentions without false exemptions or misses.
GPT-5.4 has the strongest observed proposed-label agreement and is the leading
model candidate. Mini's small coverage gain does not offset its weaker score and
point agreement. Scored subsets differ; these are developmental comparisons, not
calibrated accuracy or held-out qualification. On samples jointly scored with
Luna, GPT-5.4 agrees with Luna on 41/48, mini on 38/46.

GPT-5.4 scores six of Luna's eleven formerly unresolved answers, while mini scores
nine; neither eliminates inconsistency. Both reject an unresolved citation but
emit an invalid locator for C041-C05. GPT-5.4 repeats that formatting failure on
C037-C05. These are invalid source-identity diagnostics, not semantic acceptance
of missing evidence; no offline reclassification or retry was applied.

Mini's source review identifies three important problems: accepting Final EIR
metadata as Draft EIR in C014-F07; borrowing other points' citations for C037-C01's
conclusion; and overrejecting bounded procedural absence in C041-P05. The
C037-C01 concern also occurs in GPT-5.4: its explanation explicitly recognizes
that the conclusion's own S1 citation lacks the Appendix D support supplied by
S3 elsewhere, yet still accepts the conclusion. Both models match the proposal
there, illustrating why proposal agreement alone cannot qualify a judge.
GPT-5.4's only two numeric proposal mismatches are C037-P05/P06 (score 1 versus
proposed 2): it rejects a scoped statement about an unestablished post-mitigation
gap as requiring an explicit negative statement. Contextual source review favors
support, but this remains an interpretation rather than adjudicated truth.
Neither new model is promoted.

Quotation diagnostics remain separate from semantic scoring: nonliteral excerpts
occur 285 times for GPT-5.4 and 186 for mini. These are diagnostic-event counts,
not answer failures. Invalid source identities remain blocking. All 595 new-model
generations (including two smokes) matched exact input counts and pinned model
identity; no context, truncation, transport or output-cap failure occurred in
these two model passes. The largest native input was 30,235 tokens.

## Caching and cost

| Work | Native generations | Standard list-rate estimate |
| --- | ---: | ---: |
| Four settings arms | 94 | $0.021265 |
| Five prompt arms | 120 | $0.044993 |
| Two fixed-context review arms | 22 | $0.020370 |
| GPT-5.4 panel + smoke | 297 | $3.774370 |
| GPT-5.4-mini panel + smoke | 298 | $1.025707 |
| Total this experiment | 831 | $4.886705 |

The incomplete temperature trial's usage is included. Initial count failures
made no generation reservations. Every phase remained within the frozen request,
output, currency and wall-clock bounds; no cap was relaxed. The $69 combined cap
is a conservative authorization ceiling, not measured expenditure.

GPT-5.4 panel usage: 1,572,887 input, 115,775 output, 843,008 cache-read tokens
(53.6% of input). Mini: 1,579,990 input, 104,102 output, 931,072 cache-read tokens
(58.9%). Their native cache-write counters are zero. Original Luna's panel read
rate was 1.9%, with 1,513,001 separately reported writes. These uncontrolled
aggregate differences do not isolate the cause of shared-evidence reuse.
Temperature-zero and other later diagnostic arms also benefit from warmer caches;
arm cost differences are not a clean model-efficiency experiment.

Of the 831 responses, 311 report developer as payer, 519 OpenAI, and one omits
payer metadata. Their respective standard list-rate estimates are $3.365291,
$1.511654 and $0.009760. Earlier free-looking receipts did not guarantee continued
promotional coverage. Invoice cost remains unknown; consult the provider billing
dashboard. All Luna diagnostic receipts report OpenAI. The original Luna panel's
approximately $0.234 estimate is prior work, excluded from this experiment total.

The user-requested shared-evidence cache optimization remains an unchecked TODO
in Task 09E.1. These runs measure existing caching behavior without changing the
prompt layout for cache optimization.

## Validation and reproducibility

Narrow changes expose validated optional sampling parameters, model-compatible
cache controls, and a generation-only prompt override without mutating defaults.
Focused regression tests: 181 passed. `make fix` passed. `make check` passed
format/lint/types and reported 4,230 passed, one skipped, and the same three
historical Task 06G failures. `git diff --check` passed. Independent settings,
prompt, fixed-review, model and report audits completed. All 653 frozen identity
bindings remained unchanged after the documented counter repair. The credential
scan checked 3,858 files and 574 decoded evaluation entries with no matches.
Prior inventory (34,055 files) and sealed offline/Clef/Luna namespaces
(5,352/1,135/1,309 files) remained byte-identical. The
[result pointer](task09e1_settings_prompts_models_result.json) binds the final
completion inventory and detailed reports. No commits or pushes were made.

The external namespace is
`task_09/09e1_20261012_settings_prompts_models_v1/`. It retains frozen inputs,
launchers, configurations, native receipts, Inspect logs, initial and repaired
code identities, all failed attempts, comparisons and independent reviews.
`launch_v2.py` contains the exact bounded invocation paths and loads credentials
from the local `.env` without printing them. Completed directories are create-only;
do not rerun into them. Further experiments require a fresh bounded namespace.
The [cloud handoff](task09e1_cloud_handoff.md) retains other-provider setup gates.

Exact full-panel invocations used from the repository (historical commands;
existing run directories deliberately refuse another dispatch):

```bash
EXPERIMENT=/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09e1_20261012_settings_prompts_models_v1
uv run python "$EXPERIMENT/launch_v2.py" full --model gpt54
uv run python "$EXPERIMENT/launch_v2.py" full --model gpt54mini
```

Required local `.env` entries are `ER_COMMONS_DATA_ROOT` and `OPENAI_API_KEY`;
keep values untracked. No shell sourcing or printed environment dump is needed.
The launcher requires the frozen panel already on disk, lists no secrets, runs
one exact-count protocol smoke, then dispatches the original panel with the
recorded model-specific caps. For a later authorized replication, copy the
launcher and the two model config files into a fresh experiment directory and
bind their hashes before invoking the same modes; never remove prior receipts.
The diagnostic modes additionally require the frozen claims, prompt additions,
and interpretation files and their sequential selection artifacts. Do not reuse
this tuned suite as an independent evaluation.
