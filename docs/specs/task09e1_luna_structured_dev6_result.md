# Task 09E.1 — Luna structured-explanation Dev6 outcome

The user-authorized [Dev6 comparison](task09e1_luna_structured_dev6_v1.md) is
complete. **Structured explanations match 315/323 proposed labels (97.5%), versus
313/323 (96.9%) for the direct baseline.** The net gain is two judgments; the
157 added claims tie, and exact-payload weighting does not favor the candidate.
This is a modest observational difference, not demonstrated general improvement.
No default is promoted and no further inference follows this run.

The user's explicit expansion request superseded the earlier pilot's stop boundary
for this separate experiment. The [failed pilot](task09e1_luna_structured_claims_result.md)
and its criteria remain unchanged; this outcome does not retroactively pass them.

## Population and results

Two fresh single-pass arms judged all 323 original non-conclusion claim slots
from the sealed six-case panel. The 166 Dev3 inputs are exactly unchanged; the
three added questions contribute 157. The panel has 136 answers, of which twenty
have no point-stage inputs. Those twenty are not all clean abstentions. No
abstention or conclusion calls were made. Both prompt strings and Luna settings
match the small pilot; only population, repetitions and concurrency changed.

| Measure | Direct baseline | Structured explanation |
| --- | ---: | ---: |
| Valid outputs | 323/323 | 323/323 |
| All-slot / valid-output agreement | 313/323 (96.9%) | 315/323 (97.5%) |
| Original Dev3 | 160/166 (96.4%) | 162/166 (97.6%) |
| Added three questions | 153/157 (97.5%) | 153/157 (97.5%) |
| False acceptances against proposals | 3 | 2 |
| False rejections against proposals | 7 | 6 |

| Question | Claim slots | Baseline correct | Structured correct |
| --- | ---: | ---: | ---: |
| C041: animal controls | 53 | 47 | 50 |
| C037: wetland mitigation | 59 | 59 | 58 |
| C014 | 54 | 54 | 54 |
| C001: cumulative health risk | 70 | 66 | 68 |
| C019: groundwater | 35 | 35 | 35 |
| C056: drainage/flooding | 52 | 52 | 50 |

Sixteen decisions differ: nine candidate improvements and seven regressions
against the frozen proposals. The candidate gains two on C001 but loses two on
C056, leaving the additions tied. On the original questions, it gains three on
C041 and loses one on C037.

The 29 slots whose exact payload appeared in the small pilot improve 23/29 to
25/29. The other 294 slots tie at 290/294. There are 287 distinct exact payload
groups; averaging agreement within each group and then weighting groups equally
gives 98.24% baseline versus 98.14% structured. Both have 281 groups with every
observed slot correct. This descriptive grouping is not an independent-case
confidence interval: related claims still share evidence and questions.

All 323 candidate explanations use the requested headings and remain under
200 whitespace-delimited words (maximum 127). Formatting compliance does not
establish evidence fidelity. A single pass per slot cannot measure repeat
stability across the whole panel; repeated exact payloads are retained visibly.

## Source review

Independent review covers every changed verdict, every candidate false acceptance
and the lexicographically first both-correct claim per question. These targeted
reviews diagnose failure modes; they are not an exhaustive human accuracy audit.
The reviewers inspected 23 slots in total: thirteen Dev3 and ten added-case slots.

On Dev3, nine changed verdicts involve repeated pet-policy attachment ambiguity.
The remaining change is a grading regression: the candidate overreads the
deadline contrast as excluding any relationship to functional recovery. One
policy rejection also demands that the claim restate Baylands despite the
question supplying that context. No candidate false acceptance against proposals
occurs in Dev3; three deterministic correct-agreement checks are source-faithful.

On the added cases, the candidate's two false acceptances are substantive:

- C001 F08/P2 asserts an unsupported general rule about a smaller project
  contribution not making cumulative risk significant. The explanation replaces
  that rule with a supported finding about this modeled impact, then accepts it.
- C001 P02/P3 includes a development-plus-buildout coverage assertion. Its own
  source supports buildout only; the candidate explanation omits that second
  assertion. Both arms accept this claim.

The candidate correctly rejects similar unsupported coverage in two other C001
claims and accepts a reasonable summary of incomplete cumulative accounting.
The two C056 regressions reject reasonable geographic scope supplied by the
question, effectively demanding that the claim restate it. Neither rejected
claim explicitly broadens the scope universally. The independent review favors
the baseline under the contextual rubric on those two cases. Thus the additions
have three improvements and three regressions, with no net agreement gain.

## Interpretation boundary

The structured instruction bundle produces a small higher raw count here, but
does not improve net agreement on the added cases or on the non-pilot payloads.
Its narrower advantage disappears when repeated exact payloads receive equal
weight. Neither arm is qualified, and the results do not justify treating a
generated explanation or unanimous duplicate verdict as verified truth.

Expectations are frozen synthetic proposals, not independent human calibration.
No labels were revised or headline errors removed after source review. The added
questions were outside the recent prompt pilots, but remain development cases;
reserved/test questions and the other thirteen development cases were untouched.
Comparison with old model runs would also mix prompt/settings and validation
differences. This fresh two-arm comparison is the relevant evidence here.

## Cost, caching and validation

All 646 generations were valid and fresh with exact native input-count parity,
unique response identities, no retries, replay, truncation, output-cap failures or
halts. Four samples ran concurrently per arm, with atomic shared reservations.
Observed arm durations were 377 seconds baseline and 431 seconds structured,
running concurrently; this is not a controlled latency benchmark.

| Native usage | Baseline | Structured |
| --- | ---: | ---: |
| Input tokens | 1,343,115 | 1,406,423 |
| Cache-read tokens | 749,964 | 784,656 |
| Cache-write tokens | 587,520 | 620,798 |
| Ordinary input tokens | 5,631 | 969 |
| Output tokens | 130,819 | 159,915 |
| Standard-rate estimate | $0.146912240 | $0.165500710 |

Total estimated cost **$0.312412950**; all native payer fields report developer.
Actual invoices and promotional-credit treatment remain unknown. Conservative
reservations totaled $2.939086150 below the $6 combined cap. Cache reads are
55.84% and 55.79% of input respectively. This broader single pass includes more
new prefixes than the repeated pilot; concurrency and input composition prevent
attributing the changed reuse rate to a single cause. Cache processing does not
reuse completed judgments.

Focused regressions: 281 passed. Thirteen offline launcher/analyzer guards passed;
their code and outputs are preserved. `make fix` passed with 982 files unchanged.
`make check` passed format/lint/types and retained 4,259 passed, one skipped and
only the three historical Task 06G failures. Independent input, launcher/budget
and native metrics/security reviews passed. The prior pilot's 533 files were
reverified, including its sealed successful earlier 50,869-file audit.

The [result pointer](task09e1_luna_structured_dev6_result.json) binds the fresh
`task_09/09e1_20261012_luna_structured_dev6_v1/` evidence, reviews and completion
inventory. Previous artifacts and hash-bound contracts remain unchanged. No
package/default changes, full-19, reserved/test, later-task work, commits or pushes.
