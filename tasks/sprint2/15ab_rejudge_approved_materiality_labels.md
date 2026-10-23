# Task15AB — Rejudge saved conclusions against approved materiality revisions

Status: complete; paired rejudging experiment ready for discussion, not promoted.

## Goal and scope

Measure paired conclusion-score changes on saved Luna/Haiku answers for questions
whose required/optional reference text changed in15AA. Exclude C034 because its
question changed. Include all repeats and previous passes for each affected case,
not only reviewed failures. Report baseline15T and high-generation15W separately.
No fresh answer generation, A/G/S reevaluation, synthetic generation, prompt tuning,
benchmark publication, MiniMax, reserved challenges, commits or pushes.

## Inputs and outputs

Use latest approved records selected by15AA progress_queue, comparing point_id/text
against frozen15M references. Bind exact15T/15W selections, candidate conclusions,
old judgments and new packets. Preserve all upstream bytes. Write a fresh external
`pipelines/brisbane_baylands/task_15/materiality_rejudge_20261023_v2` experiment.
This experiment consumes approved reference overlays without publishing a release.

## Execution and budget

Use unchanged Luna C v6, shared Baylands overview, medium reasoning,6144 output
cap, one new judgment per answer and concurrency16. Reuse the maintained native
executor and task15w dispatch limits with a narrower144-call experiment roster;
no automatic retries. Supplemental configured liability cap$6; prior retained
liability$2.996619885 remains counted under the existing$40 authorization. Retain
the previously accepted unknown OpenAI token-count fees disclosure. No other runs.

## Plan, learning and validation

1. Verify approved references, unchanged questions and selected saved candidates.
2. Prepare hashed packets/lineage and independently review the preflight.
3. Dispatch once; save native requests, replies, costs and validation diagnostics.
4. Compare model and computed C, paired transitions and per-model/split scores;
   separately report any unavailable output and review remaining failures and
   regressions. Explain that adaptive label changes plus single judge sampling
   prevent interpreting score increases as independent accuracy improvements.
5. Save result/limitations and update task routing. Do not silently promote results.

Use existing package contracts and prior native-run patterns, avoiding new runtime
code. Validate point inventories, exact candidate/question preservation, selected
retry lineage, prompt/settings, source hashes and native replay. Review output
schema, aggregate consistency and quote diagnostics separately. Documentation
checks and independent artifact review complete acceptance.

## Prepared roster

22 changed-label questions,132 baseline answers and12 high-generation answers
(C014/C017),144 new C calls. C034 excluded. Saved question wording is retained
exactly, including existing EIR name normalization. The input schema requires
sequential point IDs; packet-local IDs are mapped back to stable approved IDs in
each input record. Reference text and stored canonical IDs are unchanged by this
transport mapping. Historical baseline C caps were mostly4096; this experiment
uses the already accepted6144 cap throughout, disclosed as an execution difference.

Initial v1 dispatch stopped before any judge calls: the reused15S guard limits
judges to4096 tokens. Sixteen count calls occurred (unknown fees retained), zero
generation/judge calls. Preserve v1 and use a fresh v2 namespace with the existing
15W6144-token operational envelope; its narrower192-judge cap covers144 calls.
The actual prior liability remains$2.996619885; legacy policy metadata is not a
new budget grant or a replacement for this experiment's cumulative accounting.

## Outcome

The [result](../../docs/specs/task15ab_materiality_rejudge_result.json) selects
144 saved-answer C judgments:132 baseline and12 high-generation.143 valid; one
high Haiku C014 repeat3 omitted optional rows and remains unavailable. All valid
model/aggregate verdicts agree. No answer generation or A/G/S changes.

Affected baseline22 questions improved44/132 to69/132: Luna16/66 to34/66,
Haiku28/66 to35/66.31 failures became passes;6 passes became failures. Full49
overlay with untouched decisions retained: Luna75/147 to93/147; Haiku89/147 to96/147.
High affected12: Luna3/6 unchanged, Haiku1/6 to5/6 plus1 unavailable.

All63 baseline failures reviewed:45 reasonable/defensible overall (some qualified),
11 disputed and7 likely judge errors. These are review interpretations, not manual
rescoring. Remaining required omissions and overly literal judging both persist.
One questionable new pass also demonstrates sampling variability on unchanged
content. See review_synthesis.md and per-model reviews for exact cases.

Native delivery, sealed inputs, schema replay, accounting and paired comparison
audits passed.17 quote-diagnostic calls retained separately. Configured usage
$0.119641410; cumulative retained liability$3.116261295 under$40 plus accepted
unknown count fees.144 judges,160 counts including stoppedv1; no generation.
Successful dispatch137.9seconds. Historical artifacts and benchmark designation
remain unchanged. No further calls, label edits or publication selected.
