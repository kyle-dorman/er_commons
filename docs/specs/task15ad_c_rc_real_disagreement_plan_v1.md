# C/RC comparison on unchanged real answers

Status: historical executed plan; candidate changes subsequently
[abandoned by the user](task15ad_c_rc_experiment_disposition.md). Do not resume.
This diagnostic round did not replace the sealed real-run grades.

## Selection and exact inputs

Select rows from the sealed original RC/C comparison where RC `covered` differs
from C `status == satisfied`. This yields **116 required-point disagreements**
across **87 original generated answers** and **32 questions**:

| Original result | Points |
| --- | ---: |
| RC covered, C missing | 74 |
| RC not covered, C satisfied | 39 |
| RC covered, C contradicted | 3 |

The two original RC-not-covered/C-contradicted rows are not binary disagreements:
both judges reject coverage. Preserve the distinction between missing and
contradicted when reporting; do not silently combine their reasons.

Reuse the exact original saved judge packets, without rewriting any answer:

- C: 87 conclusions, each with its original question and complete required/optional
  reference lists. Judge each answer once per version/repeat even when it has
  multiple disagreeing points.
- RC: 116 original packets, each with one required point and the unchanged candidate
  supporting points. No conclusion, qualifications or other verdicts are supplied.

These are actual real answers, not synthetic perturbations. No new predictions
are generated. Prompt versions are the accepted C v6/RC v1 and the exact candidate
prompts from the completed paired regression. Native schemas retain the maintained
normalization and strict local output validation used in that round.

## Recommended comparison and budget

Run both accepted and candidate prompts three times on the same packets:
**522 C calls + 696 RC calls = 1,218 calls**. A new round of accepted-prompt calls
provides a matched variability comparison; the original one-shot verdicts alone
cannot distinguish a prompt effect from ordinary variation after selecting cases
because they disagreed.

Proposed **fresh $6 cap**. The offline reservation envelope is **$4.963051125**,
using every serialized request byte plus 1,024 as an input-token allowance, all
input charged at the cache-write rate, and full output limits. Exact native
delivery and cost bounds must be checked before dispatch. This is a conservative
reservation calculation, not a tokenizer-certified prediction of actual charges.

Extrapolating the last round's observed mean cost separately for C and RC gives
approximately **$0.28**. Actual answer lengths, reasoning output and cache reuse
will differ. The previous $0.047775430 charge is separate and has zero unresolved
liabilities. This proposal authorizes no spending by itself.

Candidate-only alternative: 609 calls with an offline reservation envelope below
$3. It answers how the new prompts grade these inputs, but offers a weaker comparison
against historical single judgments. The primary proposal is the matched $6 round;
do not run both alternatives.

Settings: GPT-6 Luna, medium reasoning, concurrency 16, C maximum output 6,144,
RC 4,096, 24-hour prompt caching, standard service, storage off, truncation disabled,
no tools or source retrieval. No SDK, transport or semantic retries. Use the frozen
interleaved schedule and preserve every request, response, usage record and failure.
Track actual estimated charges plus in-flight/unknown liabilities. Stop admission
on cap risk, settings/source drift or uncertain billing. Stop for user review after
one round; no automatic promotion, extension or real-run regrading.

## What the results can establish

Report old/new C statuses and RC labels for the 116 selected point pairs, separately
by original disagreement direction, with repeat agreement and text/reason changes.
C also returns 179 other required-point statuses within those full answer packets;
label them incidental observations, not additional selected disagreements or a
reason to expand RC calls. Preserve optional statuses separately.

Do not assign gold labels from either original judge or use increased C/RC agreement
as accuracy. C judges the conclusion; RC judges supporting points, so some genuine
differences should remain. Review changes against the actual texts and distinguish
clear errors, real differences between fields, and ambiguities. Historical verdicts
and selection metadata stay outside model inputs. This selected exposed subset
cannot establish overall benchmark accuracy or held-out reliability.

Preparation and independent review are recorded in the
[result pointer](task15ad_c_rc_real_disagreement_preparation_result.json).
Rates follow the [Luna pricing used for the preceding round](https://developers.openai.com/api/docs/models/gpt-6-luna):
$0.10 input, $0.01 cached input, $0.125 cache writes and $0.50 output per million
tokens below the long-context threshold. Maximum prepared input allowance is18,400.
