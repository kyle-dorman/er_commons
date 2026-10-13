# Task 09E.1 — User-authorized Dev6 claims comparison

The user explicitly requests the larger Dev6 comparison despite the
[structured pilot's failed improvement criteria](task09e1_luna_structured_claims_result.md).
This instruction supersedes that pilot's no-expansion boundary for this new run.
Preserve the failed result and its frozen contract; do not retroactively pass its
gate. No new prompt tuning or automatic promotion is authorized.

## Exact population and comparison

Use the existing sealed [09A.3 six-case panel](task09e_09a3_small_v1.md), with
136 eligible answers and 323 original non-conclusion claims. Dev3 is C041/C037/
C014, 69 answers and 166 claims; the additions are C001/C019/C056, 67 answers and
157 claims. Twenty answers have no non-conclusion point inputs and require no
calls; this must not be reported as twenty clean abstentions. The panel contains
twelve clean abstentions. This is a claims-only comparison, not a new
abstention/conclusion run.

Read the 09A.3 result pointer and verify the panel manifest and consumed packet,
answer and expectation bindings before reuse. Build payloads through the maintained
point-stage projection. Prove exact parity for the existing 166 Dev3 payloads.
Only the selected six-case artifacts may be opened; no mixed-split reference
container, reserved answers, test content or other development cases. Keep all
expected labels and reasons in separate diagnostic artifacts, outside requests.

Run one fresh pass per arm over all 323 claim slots, at most 646 generations.
Copy the baseline and structured prompt strings byte-for-byte from the frozen
pilot. Retain Luna Responses, medium reasoning, 4,096 output allowance, native
exact-token preflight/parity, unchanged schema and qualified evidence-prefix
caching. No claim rewriting, truncation, added evidence, labels or examples.
The candidate still adds a structured explanation in the existing string field;
it is not a new claim decomposition stage.

Each arm has at most four concurrent samples, one shared $3 conservative
reservation cap, 323-request cap and 3,600-second wall cap. Total ceiling $6 and
646 generations. Verify synchronous shared-budget reservations before enabling
concurrency. On failure, halt subsequent scheduling, retain already in-flight
calls and all failures, and never retry or replace results. A partial run remains
partial. Separate arm cache keys and no saved-response reuse. Credentials load
inside code from `.env` without displaying values.

## Analysis fixed before dispatch

Report all-slot and valid-output agreement, false acceptances/rejections, invalid
coverage, paired improvements/regressions and per-question counts. Separate
Dev3 from the 157 added claim slots. Also separate exact-payload groups and claims
whose exact payload appeared in the small pilot. The additions provide a broader
development check, not an independent test set or human-calibrated accuracy.
One pass does not estimate repeated-request stability; duplicate input slots
remain visible instead of being treated as independent semantic evidence.

Source-review every baseline/candidate disagreement and every candidate false
acceptance relative to proposals. Review a deterministic correct-agreement
sample from each question as a check on explanation fidelity. Record defensible
alternative readings and suspected label problems without editing labels or
recalculating headline agreement to hide errors. Check candidate explanation
headings/length separately from source fidelity and literal quotation diagnostics.

No pilot thresholds are retrofitted onto the broader panel. Report the observed
tradeoffs and whether improvement spans the added cases or merely repeated
familiar claims. This run cannot qualify a judge or promote a default automatically.
Stop after the two passes and independent review, regardless of result. Full-19,
reserved/test work, later tasks, other models, commits and pushes remain excluded.

## Artifacts and validation

Fresh namespace: `task_09/09e1_20261012_luna_structured_dev6_v1/`. Freeze a manifest
binding preparation/launcher/analyzer code, inputs, prompt strings, configuration,
this contract and implementation identity before inference. Preserve all prior
namespaces and verify their completion bindings; prior negative results remain
historical evidence. Inspect owns samples, stage execution and logs.

Use bounded independent reviewers for input/provenance boundaries, launcher and
budget safety, native result reconciliation, and source interpretation. Run
focused regressions and offline launcher guards, `make fix`, `make check`, and
`git diff --check`. Current baseline: 4,259 passed, one skipped and three historical
Task 06G failures. No package/default changes are expected. Scan raw artifacts
and decoded Inspect logs for credentials, publish a completion inventory, and
bind the final evidence in a small tracked result pointer.
