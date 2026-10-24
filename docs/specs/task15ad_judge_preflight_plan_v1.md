# Task15AD judge preflight plan v1

Status: paragraph representation and $70 qualification cap user-approved2026-10-23.
Authoring, independent review and checkpointed qualification are authorized.
Synthetic authoring is underway; no paid dispatch before independent review and
input/budget preflight. The S pilot remains a mandatory user-review checkpoint.

## Scope and decisions

Use the approved15AC references and separate accepted15Z retrieval sidecar.
Retain accepted Luna C/v6, Haiku S/support_basis.v6, A, G and15Y contracts.
Refresh S synthetics to exercise the revised conclusion style. Refresh only C
synthetics affected by reference changes; this is compatibility qualification,
not a judge-selection experiment. A/G/15Y need offline identity, projection and
integration checks, not blanket synthetic regeneration or paid requalification.
Any discovered substantive incompatibility returns for discussion.

S assesses every material claim actually asserted in the candidate conclusion,
including optional and additional claims, interpreted with qualifications. It
requires substantive, jointly sufficient reasoning. Omitted reference content
creates no S failure. Factual premises are given; G owns source grounding.
S sees question, candidate conclusion, supporting points and qualifications.
References, evidence packets, expected labels and other verdicts stay hidden.
Keep the existing support_sufficient/reason_codes/reason schema and prompt.
C keeps its existing approved required/optional rules and v6 schema; select the
accepted configuration explicitly rather than a legacy default.

## Offline C compatibility audit

The [sealed offline audit](task15ad_c_compatibility_result.json)
compared the382 Task15Q development examples against current15AC judge inputs.
Twelve questions/242 examples have identical reference inputs and need no new
qualification calls. Seven questions/140 examples changed: C006, C014, C017,
C027, C036, C045 and C050. C034's question change is outside the development
suite; propagate it to fresh generation/evaluation without using it for tuning.

Independent primary and crossreviews agree on all140 dispositions:

- 123 retain their Boolean expectation (some metadata/family-purpose repairs).
- C027-Q-RC-02 changes false to true: omitted stop/turn-pocket detail is optional.
- Eight C045 former positives change to false: they lack the now-required
  Specific Plan classification of community sports as active-recreation open
  space. General public-recreation eligibility alone does not convey that claim.
- Eight C014 former positives are ambiguous: they explicitly name Quarry and
  Candlestick for future forecasts but leave their inclusion in local/access
  analysis implicit. Quarantine these originals; do not force a new gold label.

These are proposed expectations for a successor suite, not edits to frozen15Q
or changes to approved reference meaning. Keep the C014 originals in the audit;
author explicit positive and clear omission-negative replacements for review.
Repair C045 positive bases and dependent negatives so each family tests its
intended defect. Preserve changed originals as explicit compatibility examples
where useful. Repair stale target IDs and combined-defect labels, including
C027 CD-01/CD-04, whose omitted detail is no longer required. Add omission-pass
versus contradiction-fail contrasts for newly optional content in C006, C017,
C027, C036 and C050. Budget up to180 reviewed examples total:140 affected slots
including replacements, plus at most40 controls. Freeze the exact roster before
calls; unresolved expectations remain excluded. Do not change references.

## Proposed S synthetic design

The user approved this representation: **one coherent conclusion paragraph**,
paired with candidate supporting points and qualifications. Compose the paragraph
naturally from selected reference ideas; combine related claims in sentences.
Do not serialize required/optional points as a checklist, bullet list, numbered
list, or R/O-labeled clauses. Required/optional points guide authoring only and
are never supplied to S as reference fields or disguised candidate support.
Candidate supporting points must state the answer's premises and reasoning;
they are not an automatic copy of the reference checklist.

Author the natural paragraph first, then a substantive supporting basis. For
support ablations, hold the paragraph and qualifications fixed and perturb only
the supporting points. For conclusion-scope or qualification contrasts, explicitly
record the necessary paragraph/qualification change and keep other material
fixed. Preserve paragraph form in every variant, including multi-claim and
complete-list coverage cases (list content is expressed in prose).

Keep a reviewer-only claim map from paragraph spans to their intended support
and reference provenance where applicable. This map is never a judge input.
Reviewers check that composition preserves the intended meaning, introduces no
accidental claims, and leaves each expected label justified by the actual
paragraph, support and qualifications. Reject checklist-like prose or labels
that rely on hidden reference obligations. Validate the exact rendered S request
contains only the approved candidate fields; no claim map, R/O lists or verdicts.


Author eight matched pairs per development question:304 examples,152 intended
true and152 intended false. Each pair isolates one support boundary. Questions
and references remain fixed; candidate conclusions/support/qualifications may
vary as the specified boundary requires. Record exactly what changed. Reference
R/O membership is authoring metadata only. Independent reviewers read every
candidate and rationale before expectations are frozen; unresolved examples are
excluded or replaced before calls, never silently relabeled after predictions.

Six core pairs per question:

| Family | True | False |
| --- | --- | --- |
| Substantive/overlapping basis | Concise basis adds a decisive reason, even with wording overlap | Mere restatement, empty or neutral-only support |
| Distributed support | Multiple points jointly establish claims | Remove a necessary link or one claim's basis |
| Included optional claim | Actually asserted optional claim has a basis | Same claim lacks support |
| Additional claim | Material claim outside reference lists has a basis | Same extra claim lacks support |
| Omitted reference content | Partial conclusion is adequately supported despite omitted required/optional reference content | Same conclusion loses support for a claim it actually asserts |
| Qualification scope | Conclusion and qualifications fit scoped premises | Conclusion overclaims those premises |

Two rotating pairs per question cover scenario consistency/material conflict,
premise truth versus inference validity, calculation/mechanism, complete-list
coverage, and representation invariance. Allocate each rotating boundary to at
least four questions and include every boundary in the six-question pilot.
Use only applicable mechanisms/lists; document substitutes. Cross-cutting tags
cover paraphrases, reordered/merged points, neutral additions, duplicates and
omitted optional details. The premise-truth control must include logically
sufficient but deliberately factually altered support (S true, potential G false).
The omitted-required control must include S true despite potential C false.
No C/G calls are needed to establish those authoring controls.

Pilot: C014, C017, C019, C037, C041, C056;96 examples and288 judgments.
Then remaining13:208 examples and624 judgments. Total912, not pilot plus912.
Use three independent judgments per example with result caching disabled.
The reviewed coverage matrix must show every family, expected label and case
before dispatch. Label provenance remains agent-authored/independently reviewed,
not human gold and not evidence of benchmark answer quality.

## Proposed execution settings and budget

| Setting | C compatibility | S qualification |
| --- | --- | --- |
| Model/prompt | gpt-6-luna / accepted C v6 | claude-haiku-5-5 / support_basis.v6 |
| Maximum examples |180 |304 |
| Repetitions |3 |3 |
| Logical judgments |540 |912 |
| Reasoning |medium |medium |
| Output cap |6144 tokens |4096 tokens |
| Provider cache |24h |5m |
| Proposed hard cap |$15 |$55, including $20 pilot subcap |

Combined proposed qualification cap: **$70**. Approved2026-10-23 as a new
qualification allowance, not a transfer from past tasks. No real-answer generation, A/G/15Y
grading or final reporting calls are covered; price those separately after the
qualified setup and exact294-answer projection are frozen.

Use concurrency16 total, SDK retries0, at most two transport retries (three
attempts per logical judgment), no semantic retries and no result reuse between
repetitions. Verify maintained-adapter timeout semantics before dispatch:
proposed request120s, attempt45s, sample150s. Preserve every failed attempt and
reserve uncertain usage at its full bound. Retry only eligible transport errors;
schema/semantic failures remain recorded non-decisions. Do not retry just to
obtain a preferred verdict.

The initial estimate used12,000 input tokens per attempt. Execution instead
reserves each exact offline-rendered request byte as one token plus1024 framing
tokens, including system/schema/overview overhead. Recompute the full reservation
from these conservative per-request bounds and require it to fit the approved
caps before dispatch; never truncate to fit. Conservative planning envelope from
configs/adequacy_binary_models_v2.json: C input$0.275/output$0.825 per million;
S input$0.625/output$2.50. The original12,000-token estimate with full outputs and three attempts gives:

- C:540 ×3 ×(12000 ×0.275 +6144 ×0.825)/1e6 = $13.557456.
- S:912 ×3 ×(12000 ×0.625 +4096 ×2.50)/1e6 = $48.537600.
- S pilot:288 ×3 ×same per-attempt reserve = $15.327360.

Reserve every attempt before dispatch; stop if the remaining cap cannot cover
it. No automatic increase. Expected current-price costs are lower: the native judge configuration
uses standard input$0.10/output$0.50, cache write$0.125 per million for both.
Treating every input token at that cache-write rate, full outputs and maximum
retries yields C$7.406640 and S$9.707328. These are bounds under stated token/rate
assumptions, not predicted bills. Retain conservative admission reservations;
use actual native usage separately for spend and reconcile unknown liabilities.

Pricing sources checked2026-10-23: [Luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
and [Haiku model documentation](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
Historical conservative accounting rates are not current native billing rates.
Verify applicable price/cache behavior and immutable rendered payload bounds
before approval is exercised. Any counting fees must fit the same cap; do not
make credentialed counting or probe requests before approval.

## Checkpoints and stopping

Before calls: approve settings/caps; independently review all labels and exact
rosters; freeze hashes; verify request isolation, model identity, token/rate and
budget reservation bounds. Review the first24 C examples (at least two per
affected case, both expected labels) before continuing C. S stops after its
six-question pilot for user review before the remaining13. Checkpoints count
within totals. Do not combine pilot edits with continuation silently.

Pause dispatch for unexpected inputs/model/settings, a budget reservation
failure, two operational failures, or the same clear semantic defect on two
independent examples. Drain in-flight requests and preserve liabilities. Review
all mismatches, invalid outputs and repeat disagreements, plus two unanimously
correct examples per case (one per label, chosen by sample ID before calls).

Proposed qualification gates: at least99% valid outputs, at least95% sensitivity
and specificity on valid judgments, and at least95% unanimous three-repeat
agreement over all examples (missing/invalid repeats do not count as agreement).
Report all-slot accuracy and denominators as well. Check C computed/model-final
agreement and per-family results. Global scores cannot waive systematic boundary
failures. Stop for review after the round regardless of scores. No automatic
Round2, prompt changes, label tuning or model reselection.

## Integration and final run still required

Validate A/G/S/C and15Y input projections, implement real-answer coverage execution
and C/G diagnostic joins, retain15Y omission limitations, and rebuild reports.
Pin15AC; keep15Z curator-only. Later fresh Luna/Haiku generation is49 questions
×3 answer repeats ×2 models =294 answers, separately approved and budgeted.
Maintain19/30 reporting and disclose curation exposure. Preserve frozen results,
exclude MiniMax and reserved challenges, and do not commit or push.
