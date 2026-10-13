# Luna generation trial — October 12, 2026

The user authorized the next experiment with `gpt-6-luna` through Responses,
using credentials loaded in code from the local untracked `.env`. No credential
values are displayed or saved. Anthropic and Fireworks credentials are present
but are not used in this trial. No Decisions requests are authorized by this run.

Preserve the original 69-answer Dev3 panel, prompts, semantic/quotation separation,
binary observations and aggregation. Run one protocol smoke, three cache probes,
then one panel attempt after qualification. Limits: $0.10/one call for smoke,
$0.25/three calls for cache, $2.00/304 calls for the panel; total reservation caps
$2.35. Panel output allowance is 4,096 per stage, 1,245,184 globally, with a
3,600-second wall limit and no automatic retries. Exact count/native usage parity
and disabled truncation remain required. Original artifacts are preserved.

## Availability and setup

An authenticated model-list check confirmed `gpt-6-luna`, `gpt-5.4` and
`gpt-5.4-mini` on this account. The user's listed daily token promotion does not
name Luna; do not infer promotion eligibility or invoice charges from that list.
GPT-5.4 and mini are requested follow-up candidates, not substitutions in this run.
No calls to those models have been made by this experiment.

Current [Luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
confirms the configured model, context and standard rates. The existing configuration
uses low reasoning effort and conservative rate ceilings. The official
[counting endpoint](https://developers.openai.com/api/docs/guides/token-counting)
counts the rendered request before each generation. Native receipts must agree.

The external namespace is `task_09/09e1_20261012_luna_generation_v1/`.
Its `launch.py` uses the installed dotenv parser to load only `OPENAI_API_KEY` and
`ER_COMMONS_DATA_ROOT` into the process environment, then invokes the existing
comparison CLI. Headers and dotenv contents are not artifact fields. Each mode
uses a fresh directory; repeated calls cannot reset an existing namespace's caps.

## Protocol qualification

The first smoke generation completed successfully with exactly 498 input tokens,
matching preflight. It exposed an adapter defect: the parser rejected a successful
response containing `error: null`. The narrow fix accepts absent/null errors while
rejecting every non-null error, including falsey values. Six focused regression
cases were added. The original receipt/result remain unchanged; offline
`smoke_revalidation.json` validates the saved response without repeating inference.

All three cache probes passed structural validation and count parity. The first
original point used 1,041 input tokens with 1,038 cache-write tokens and no reads;
the identical repeat read 1,038 tokens with no writes. A different original claim
sharing evidence used 1,051 input tokens, wrote 1,048, and read zero. Thus identical
request reuse is measured, but shared evidence alone did not give that probe a hit.
These probes remain outside the evaluation denominator.

The smoke receipt reports `billing.payer: openai`. Record per-call billing evidence
separately from rate-based estimates; it does not establish a future free allowance
or replace the configured spending cap.

## Outcome

The single Dev3 pass completed in **1,254 seconds (20.9 minutes)**. All 298
generations completed and passed semantic structure checks, exact input-count
parity and output limits. No truncation, context blocks, transport failures,
automatic retries or saved-result reuse occurred. Largest input: 30,235 tokens;
largest output: 741. Runtime model identity, code, config and lockfile remained
unchanged during the panel pass.

| Case | Numeric scores | Clean abstentions | Unresolved point/review disagreement |
| --- | ---: | ---: | ---: |
| C041 (22 answers) | 10 | 2 | 10 |
| C037 (27 answers) | 24 | 2 | 1 |
| C014 (20 answers) | 18 | 2 | 0 |
| All 69 | **52** | **6** | **11** |

Scores were fourteen 0s, seventeen 1s and twenty-one 2s. All six proposed clean
abstentions were recognized, with no false exemptions, misses or ambiguous gates.
All unresolved answers remain unscored in the 69-answer denominator.

| Diagnostic | Historical Qwen 9B | Luna generation |
| --- | ---: | ---: |
| Numeric scores | 12/69 | 52/69 |
| Numeric scores matching proposals | 6/12 | 47/52 |
| Valid point decisions | 93/166 | 166/166 |
| Point decisions matching proposals | 62/93 | 151/166 |
| Valid conclusion decisions | 12/63 | 63/63 |
| Conclusion decisions matching proposals | 7/12 | 56/63 |
| Substantive answers falsely exempted | 1 | 0 |

These are conditional diagnostics against uncalibrated synthetic proposals, not
ground-truth accuracy. The comparison changes both model and pipeline: optional
quotation errors no longer block semantics, and only ordered binary observations
enter conclusion review. Different validated populations must remain visible.
Historical Qwen evidence is preserved in its [outcome](task09e_09a3_qwen9b_v1.md).

Point confusion against proposals: 120 true-positive, 31 true-negative, one
false-positive, 14 false-negative. Conclusion confusion: 44 true-positive,
12 true-negative, one false-positive, six false-negative. Five final numeric
scores disagree with proposals; their exact IDs and values are preserved in
`score_comparison.json`. Eleven other answers remain unresolved rather than
having inconsistent judgments overridden.

The post-run Luna/Clef comparison retains all 69 answers. It has 23 matched-valid
answers, including 16 matched numeric scores; all 16 numeric scores agree.
That small selected overlap does not establish equal quality: Luna scores 52
answers versus Clef's 22 and evaluates the large C014 inputs Clef could not send.

## Source-linked review and remaining limitations

Independent review checked previously observed failures against saved Dev3 inputs:

- C037-F05: Luna rejects the change from source “may/could” to answer “will”;
  point and review agree on lack of support, while the independently supported
  conclusion yields score 1.
- C041-F05: Luna also rejects guaranteed trapping where the source says it may
  be necessary. Another point's enforcement-scope verdict changes during review,
  so the answer correctly remains unresolved.
- C014-R02: Luna treats the document-omission claims as substantive, recognizes
  contrary table evidence naming Guadalupe Quarry and Hunters Point
  Shipyard-Candlestick, and returns score 0. Qwen and Clef had falsely exempted it.

Quotation defects persist: 45 nonliteral excerpts and 34 missing-quotation
diagnostics. The strict historical-style view rejects 35 point stages and 24
conclusion stages, across 40 answers; the semantic view validates all 298 stages.
This is a diagnostic view, not a rerun of the old pipeline. Eleven review
disagreements, five numeric proposal disagreements and synthetic-label uncertainty
prevent qualification of a production judge. No prompts, thresholds or labels
were tuned in response to these results.

## Usage, caching and cost

Panel native usage: **1,581,554 input tokens**, **81,268 output tokens** (including
reported reasoning use), **30,654 cache-read tokens** and **1,513,001 cache-write
tokens**. The cache probe proves identical-request reuse, but changing claims with
shared evidence did not hit the cache. Reads were only about 1.9% of panel input;
write premiums therefore matter, and large savings are not established.

At the verified standard list rates, measured token buckets imply **$0.233855565**
for the panel and **$0.234519395** including the smoke and three probes. This
includes cache-write premiums. Conservative reservations were $1.441928950 for
the panel and $1.456444275 overall, below the chosen caps.

Every one of the **302 native generation receipts** reports `billing.payer: openai`.
This is per-receipt evidence, not an invoice total or a guarantee about future
promotion eligibility. No invoice was retrieved. Counting requests and the model
availability lookup are separate from the 302 generation calls.

## Validation, preservation and rerun setup

The nullable-error fix passed 109 focused provider tests and independent review.
`make fix` and format/lint/types passed; `make check` reported **4,197 passed, one
skipped, and only the three historical Task 06G failures**. `git diff --check`
passed. The independent artifact audit verified every seal, native count,
reservation, output limit and unchanged execution identity.

All 34,055 earlier Task 09 files, 5,352 sealed offline-preparation files and 1,135
sealed Clef files passed preservation checks. A code-driven scan of artifacts,
including decoded Inspect logs, found no configured API-key values. No additional
model/provider runs, dataset changes, reserved/test reads, Dev6/full-19 expansion,
later tasks, commits or pushes occurred.

The [result pointer](task09e1_luna_generation_result.json) binds the reports and
validation. To reproduce deliberately with a fresh namespace, run from the repo
with keys in `.env` and use the preserved loader:

```bash
uv run python /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09e1_20261012_luna_generation_v1/launch.py \
  --mode run --condition openai_generation --execute-paid \
  --output /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/FRESH_LUNA_RUN \
  --currency-cap 2.00 --request-cap 304 --output-cap 1245184 --wall-seconds 3600
```

This command may incur charges despite this run's payer metadata. The completed
trial stops here. GPT-5.4 and GPT-5.4-mini remain the user's next comparison
candidates; they have not been run or silently substituted for Luna.
