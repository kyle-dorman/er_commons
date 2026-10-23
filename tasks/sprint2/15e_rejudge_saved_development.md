# Task 15E — Educational comparison on saved development answers

Status: educational comparison complete (2026-10-21).

## Goal and authorization

The user selected Luna with one judgment per answer, authorized judging existing
answers first, and clarified high concurrency (not higher reasoning effort).
This is an educational comparison, not final qualification. The user intends
to align the answer-generation prompt with the new rules and rerun end-to-end
afterward; record that as subsequent work, not replace it with saved-answer scores.

## Inputs, execution and outputs

Use `reporting_inputs.load_development` to replay and verify the accepted Task11E
114 saved answers:19 questions ×2 answer models ×3 answer repeats. Reuse exact C
packets and original identities. Retain the frozen project-context wrapper; change
only the C core to the accepted Task15 candidate. A/G/S/automatic outcomes remain
unchanged. Old C decisions are comparison metadata, not human-gold labels.

Use one Luna judgment per answer, medium reasoning,16 connections,4,096 output
tokens,150-second sample limit and at most one native transport retry. Maximum
114 logical judgments/228 generation attempts; compute a dated-price estimate
before dispatch. No semantic retries. Run original-six36 first, validate technical
coverage and review changes/failures, then add the remaining78 under identical
settings. Educational disagreements do not themselves forbid expansion; stop on
identity, isolation, execution or validity problems requiring repair.

Write a fresh `task_15/saved_development_20261021_v1` artifact publication with
verified input provenance, exact old/new judgments, transitions, unchanged
component outcomes and reconstructed joint, full review and completion seal.

## Plan, learning and validation

Reuse native Inspect and the existing sealed development loader; no new provider
executor. Preserve the historical overview wrapper so a context change does not
confound the judge-policy comparison. Keep answer-repeat and judge-repeat distinct.
Verify exact packets/identities, prompt/context bindings and original seals.
Independently review projection and all failures/changed judgments; distinguish
rule improvements, regressions and uncertainties. Recompute aggregate transitions
and joint outcomes offline, retaining invalids without imputation. Diff-check docs.

## Non-goals

No new answers, generation-prompt changes, A/G/S reruns, labels rewritten,
thirty-question test reevaluation, reserved challenges, MiniMax, commits or pushes.
Fresh end-to-end execution follows separately after generation-prompt alignment.

## Outcome

The [result pointer](../../docs/specs/task15e_saved_development_result.json)
selects the sealed 114-judgment publication and full review. All 36 original-six
and 78 remaining judgments are valid. Luna-generated answer C passes change
37→45/57; Haiku-generated 35→39/57. Same-answer joint passes change 29→36 and 6→8,
using unchanged automatic/A/G/S. There are 71 pass→pass, 29 fail→fail, 13 fail→pass
and one pass→fail. These are outcome shifts, not measured judge accuracy.

All 43 distinct changed or newly/retained failing instances received independent
semantic review (21 Luna targets, 22 Haiku targets). Review groups distinguish
apparent semantic-equivalence benefits, defensible failures, disputed materiality
and possible judge errors. The lone regression, C027 Luna repeat3, demands a
separate intersection-control item despite detailed crossing treatments; it is
disputed. Similar C029 qualifications and C050 modal wording receive differing
decisions. C041 Haiku repeat3 may conflate unspecified enforcement procedures
with missing designated enforcement responsibility. Full exact packets and
old/new rationales are in `review.html`; no reviewed judgment is silently replaced.

Independent validation verifies all 114 planned IDs exactly once, actual native
wire prompt/context and packet bytes without labels, original identities and
judgments, unchanged components and reconstructed joint. The runner's initial
result loop lacked an exact returned-ID assertion; an explicit post-run check
and independent audit enforced full 36/78 identity coverage before acceptance.
No missing or invalid observations occurred. Source snapshot and execution-plan
hashes were rechecked before continuation. All 43 review IDs are covered exactly.
No package code changed; artifact checks and `git diff --check` passed.

Execution took 32+49 seconds excluding analysis; dated-price estimate $0.0596,
not a billing receipt. Luna remained medium reasoning with 16 concurrent requests.
The old shared project overview was retained exactly. Original frozen results
and selected configuration remain intact; no commits or pushes.

Next align the target-generation prompt with the new rules and prepare the fresh
end-to-end rerun the user requested. This saved-answer diagnostic does not replace
that work or claim a final fair comparison. Fresh run population, prompt and
execution budget must be recorded before dispatch; no fresh/test calls occurred here.
