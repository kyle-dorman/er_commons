# Task 11D.5 — Triple Haiku output allowance

Status: Complete with limitations (2026-10-18); truncation resolved, no selection.

## Goal and hypothesis

The user authorized tripling the 4,096-token output cap and trying Haiku again.
Run the same fixed six questions twice with a 12,288-token generation allowance,
including reasoning. Hypothesis: the larger allowance lets Haiku finish C014,
which exhausted both previous allowances, and may change quality on other cases.
A larger cap is a compute intervention, not a new prompt or stronger model.

## Inputs and fixed conditions

Use accepted 11A panel C041, C017, C019, C014, C037, C056 in that order for repeat
1 and then repeat 2. Use original questions, Task 10 evidence/metadata, exact
V6b prompt/examples, Haiku `claude-haiku-5-5`, medium adaptive thinking and native
structured schema from 11D.4. No generation reference or judge feedback. Keep
09G judges and their 4,096 output caps unchanged. The only generation-request
change from saved Haiku requests must be `max_tokens`: 4096 to 12288. Use fresh
run/candidate identities and compare all twelve old Haiku outputs with all twelve
new outputs. Retain Luna's twelve saved V6b results as separate coverage context;
never pool favorable repeats or the separate 11D.3 C014 experiment.

Read 11D.4 outcome/result, 11D.2 manual review contract, architecture and artifact
contracts. Preserve every prior sealed artifact and repository binding. Since
11D.4 binds its adapter source, use a new narrow Haiku adapter reusing immutable
helpers instead of modifying it. Use a fresh external namespace
`pipelines/brisbane_baylands/task_11/validation_11d5_20261018`.

## Predispatch limits and stopping

One fixed revision, 12 generations, 192 judgments maximum (16 per candidate),
204 count calls maximum. Zero retries, repairs, replacement outputs, further
repeats or adaptive prompt changes. Generation output 12,288 including reasoning;
judge output remains 4,096. Native input count and actual cache-inclusive usage
must remain <=100,000. Check native count plus output reserve against context;
never truncate evidence. Preserve count estimates versus actual usage distinctly.

Reserve USD 7, keeping all prior USD 58.740432 reservations, for combined liability
USD 65.740432 within the existing USD 100 ceiling. A conservative reserve using
200K input/12288 output for 12 generations and 100K/4096 for 192 judges at
USD .25/.75 per million is USD 6.100416. Counting allowance remains zero under the
user's planning assumption; actual count billing is unknown. Do not refund old
reservations. Maximum one working day, 15 minutes per generation and 30 minutes
per candidate evaluation. Persist dispatch intent before every call.

Invalid or output-limited answers are failures and do not stop other planned
questions. Transport, context, accounting, integrity or input-isolation failure
stops remaining generation; retain all twelve planned slots. A frozen judge
execution error stops further judging but independent target generation may
finish. If a candidate exceeds sixteen judge items, retain its full plan and
record evaluator-limit failure; never drop points to fit. No extra calls to
compensate for failures.

## Plan, review and validation

1. Record provider capability and hypothesis; implement only the new output-cap
   boundary and actual-native-request equivalence checks.
2. Offline tests cover exact 12288 request and usage gate, count/context reserve,
   native isolation, SDK retries disabled, raw failed responses, unchanged judge
   settings and complete scheduling. Run make fix, make check, git diff --check.
3. One independent preflight review plus bounded repair recheck. Freeze contract,
   native settings, full slots, prior seals and implementation before dispatch.
4. Generate/evaluate once per slot. Independently review complete source packets
   and valid answers before seeing judge verdicts, using the 11D.2 contract.
5. Replay without providers, compare all old/new repeats, audit accounting and
   protected bindings; preserve raw scores and disagreements separately. Publish
   result pointer, task outcome and current routing.

## Reporting and decision rule

Show schema validity/output-limit counts, generation reasoning/output usage,
complete A/G/S/C point denominators, per-case 0/2–2/2 diagnostic passes, repeat
stability and cost. Diagnostic pass requires valid schema/resolved citations,
complete applicable coverage, substantive A and every applicable G/S/C passing.
Invalid/missing/unjudged observations are never passes. Preserve manual
conclusion-source and whole-answer findings separately; no retrospective
rescoring of the old baseline. Compare 4096 versus 12288 as separate conditions,
not a pooled best-of-four. Report whether the new condition adds C014 coverage
and whether it passes all six twice without unresolved material manual defects.
No baseline promotion from occasional passes or union coverage alone; a selected
candidate would require all-six repeat and manual acceptance. 11E stays unstarted.

## Research and learning

Verified 2026-10-18: the [official Haiku overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview)
lists 128K maximum output, 1M context, adaptive thinking and medium effort. The
requested 12,288 cap fits; up to 100K-input pricing remains .10/.50 USD per million
input/output (cache writes separately priced). Use actual native receipts and
usage instead of assuming a larger maximum means all tokens are consumed.
Hold all other settings fixed to separate a budget failure from answer quality;
two repeats on exposed questions cannot establish a causal/general model ranking.

## Non-goals

No GLM/Luna regeneration, stronger model, revised question, metadata activation,
reference change, judge tuning or judge budget increase. No other thirteen
development cases, locked test or reserved content, Task 10 changes, or 11E.

## Outcome

Tripling Haiku generation output from 4,096 to 12,288 resolved both C014
output-limit failures. All twelve new answers were valid and received complete
frozen evaluation. Diagnostic passes increased from 1/12 to 3/12, but no question
passed both new repeats and C014 remained 0/2 under frozen scoring. No candidate
was selected and 11E remains unstarted. The [result pointer](../../docs/specs/task11d5_result.json)
binds the experiment, independent reviews, raw receipts and replay under the
external namespace named above.

### Complete comparison

| Question | Old Haiku 4,096 | New Haiku 12,288 | Saved Luna V6b |
| --- | --- | --- | --- |
| C041 animal controls | 0/2 | 1/2 | 2/2 |
| C017 energy assumptions | 0/2 | 0/2 | 2/2 |
| C019 landfill infiltration | 0/2 | 1/2 | 2/2 |
| C014 cumulative transportation | 0/2 | 0/2 | 0/2 |
| C037 temporary wetland loss | 0/2 | 0/2 | 2/2 |
| C056 residual flooding | 1/2 | 1/2 | 2/2 |
| Total diagnostic passes | 1/12 | 3/12 | 10/12 |

Old Haiku had 10/12 valid answers; new Haiku has 12/12. Old invalid C014 outputs
remain in the denominator. Luna-inclusive observed and repeat-stable unions
remain five of six; the new condition adds no frozen-score question coverage.
These exposed cases and two repeats do not establish a general model ranking or
a causal quality improvement. Do not pool old/new answers into a best-of-four.

### C014 completion versus quality

Repeat 1 completed with 5,739 output tokens including 3,710 reasoning tokens.
Repeat 2 completed with 6,545 output tokens including 4,512 reasoning tokens.
Both exceed the old output allowance and fit comfortably within the new one.
All other new answers stayed below 4,096 output tokens.

The first answer still called TRA-4 emergency-response analysis list-based when
P3 says projections-based: independent source review and G S3 agree on that real
error. S and C passed. Its Q3 and repeat 2's Q2 failed grounding for Final EIR
edition/qualified-substitute assertions that are visible in generation metadata
but absent from G's passage projection. Preserve these visibility failures without
silently activating the staged metadata correction or changing scores.

The second answer avoided the methodology error and passed blind source/logic
review. Its frozen C judgment still required clearer regional-growth and Final
future-land-use coverage within the conclusion itself; related information in
other answer fields does not change that frozen projection. This is a
conclusion-specific completeness disagreement, not a failure to finish or proof
that the evidence packet lacks the information. The final audit preserves exact
claim/point identities and rationales separately from the original scores.

### Manual findings, validation and accounting

Both independent reviewers locked source-first findings before judge inspection.
All twelve valid substantive conclusions were reviewed: nine conclusion-source
passes and three material defects. Whole-answer review additionally records
C017 storage/battery premise omissions and component-accounting or denominator
problems; C019 repeat 2 has an owned-citation defect for unfinished design status.
Manual acceptance never overwrites the frozen scores or validates all fields by
implication. Eight answers were acceptable on material whole-answer review and
four had a material finding.

`make fix`, `make check` (4,137 passed, one skipped), and `git diff --check` passed.
Independent predispatch review passed after extending native-delta replay to
invalid outputs as well as valid plans. Thirteen adapter tests and five runner
tests passed. Provider-disabled replay verified all twelve new requests differ
from their sealed Haiku predecessors only in `max_tokens`; all new reports and
24 historical comparator plans/reports reproduce exactly. All 284 protected
bindings and previous sealed inventories remain unchanged.

Actual calls: 12 generations, 123 judgments, 135 native counts, 270 total requests;
zero retries, replacements or additional repeats. Known usage: 617,960 input
tokens including cache, 75,765 output tokens including reasoning. Estimated token
cost is USD 0.104980235, excluding unknown count charges; this is not an invoice.
There is no missing total input/output usage, but two generation responses omit
a separate reasoning-token subtotal; do not interpret those as zero reasoning.
Retain the USD 7 reservation and USD 65.740432 combined liability.

### Decision and learning

The larger maximum successfully removed truncation and did not force every
answer to use more tokens. It exposed a complete, manually acceptable second
C014 answer, but the fixed evaluator still reports no C014 pass and the new
condition does not meet repeat/manual selection criteria. Keep the outcome as a
separate diagnostic condition, retain V6b and original publication, and stop at
the declared twelve attempts. No stronger model, GLM repair, judge change,
metadata activation, other development cases or locked evaluation was attempted.
