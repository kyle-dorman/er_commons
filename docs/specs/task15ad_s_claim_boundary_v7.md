# Task15AD S conclusion-claim boundary — v7 retest

Status: user-authorized four-question retest, not production promotion.

## Rules and prompt

The maintained [S rules](adequacy_labeling_rules.md#4-support-check-s) now
explicitly require a basis for each substantive conclusion claim. The exact
prompt is [support_claims.py](../../src/er_commons/support_claims.py), version
`task15ad.binary_adequacy.support_claims.v7`. Both occurrences of the instruction
to treat factual premises as given are removed in this candidate. Frozen v6 and
production defaults remain unchanged and reproducible.

Claims about outcome, magnitude, timing, scope or conditions require an explicit
basis or straightforward inference from candidate supporting points. This
includes negative statements about excluded benefits and optional details that
the answer chooses to assert. The conclusion cannot establish its own factual
basis. Pure transitions and redundant wording need no additional support.
Evaluate supplied facts, relationships, calculations and internal consistency;
source verification remains G's responsibility. S sees no sources, references,
required/optional checklist or other judge verdicts. The output schema is unchanged.

This clarifies the existing whole-conclusion requirement without demanding a
point per claim or spelling out obvious inferential steps. References used in
authoring do not become judge inputs. No case-specific examples are added to the
prompt. Earlier calibration tested partial-support failures, but this pilot
exposed a repeated interpretation that waived additional conclusion assertions.

## Authorized retest

Use the same 64 candidate payloads for C014, C017, C019 and C037, three fresh
judgments each (192 total). Apply the discussed successor adjudication
`15AD-S-C037-additional_claim-N = true`; retain the original false label and raw
results in their frozen publication. Biological monitoring can reasonably follow
from the stated biological recovery lag. All other expectations remain unchanged.
Compare both versions using the same adjudicated expectations and distinguish
that comparison from the originally published scores.

Haiku, medium reasoning, 4096 output tokens, concurrency16 and the existing
transport/invalid-output policy remain unchanged. Keep the prior full
$56.643960600 reservation under the existing $70 cap; reserve the retest's full
conservative liability before dispatch. No budget reset. Exact native request
rendering, receipts and independent review bind the successor external manifest.

Complete this bounded four-question retest unless a transport, accounting or
integrity issue requires stopping. Then stop for review regardless of scores;
no automatic prompt iteration, remaining pilot/all19 expansion or final benchmark
execution. No MiniMax, reserved challenges, commits or pushes.

## Validation

Independent semantic and execution review, frozen-default/schema isolation tests,
project make checks, request/response audit and original-publication preservation
checks precede publication of the retest outcome. Synthetic agreement is a
small, adaptively reviewed development diagnostic, not benchmark accuracy.
