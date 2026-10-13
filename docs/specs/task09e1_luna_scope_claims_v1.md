# Task 09E.1 — Scope-preserving contextual claims experiment

The user authorizes a replacement prompt after the [contextual pilot](task09e1_luna_context_claims_result.md)
failed: distinguish natural interpretation from changes to explicit subject,
requirement and condition relationships. The earlier authorization remains for a
conditional claims-only return to the existing Dev3 panel. Luna Responses only;
no conclusion/gate inference, model changes, dataset expansion, commits or pushes.

## Frozen design

Reuse the exact ten pilot payloads and 166 full Dev3 claim payloads from the prior
experiment. Keep their original question, own cited evidence, point IDs and linked
context. Preserve all prior namespaces and proposed labels. Baseline remains the
previous combined scope/absence/grammar prompt at medium reasoning. Candidate
appends the replacement relationship/scope instruction to that baseline; it does
not include the failed broad contextual addition. Freeze both full strings before
dispatch, with no target-specific examples or expected answers in either prompt.

The question supplies interpretive context, not facts. The replacement checks
whether the cited evidence supports the actual combination of subject, requirement
and condition. Explicit quantifiers, modality, populations, restrictions and
exceptions remain binding. Ordinary coordinated meanings may resolve grammatical
ambiguity without inventing narrow restrictions or combining different policies.
The output schema, evidence boundary and package defaults remain unchanged.

Four distinct trouble payloads cover short pet-policy S1/S2 forms, the expanded
policy and grading qualification. They represent three wordings/two issue families,
not four independent questions. Six controls cover stronger modality, invented
fine amount, missing citations, universal scope, preserved modality and bounded
absence. All ten are unchanged from the earlier eleven-answer subset. Frozen
pilot interpretations follow the user's accepted natural policy-level reading;
this does not adjudicate every alternative reading. Diagnostic labels/rationales
are hash-bound separately and never enter inference.

Each arm receives nine fresh repetitions per input (90 calls); launch the two
arms concurrently with identical ordered inputs and settings, not as a claim of
randomized causal identification. Preserve every failure, with no replacement,
replay or automatic retry. Medium reasoning, repaired evidence-prefix cache,
4,096 output reserve, exact count/model/identity checks remain fixed.

## Unchanged expansion gate

Apply the same predeclared conjunction as the previous attempt after both pilots:

- All 180 outputs valid, with exact counts/identity and no replay or halt.
- Candidate trouble agreement at least 30/36 and at least four more correct than
  the fresh baseline; each trouble input at least 6/9 and no worse than baseline.
- Candidate controls 54/54 correct and no consistently wrong trouble input.
- Independent source review finds no new acceptance of concrete unsupported
  assertions under the accepted contextual reading standard.

No threshold relaxation if a baseline ceiling makes qualification impossible.
Failure stops expansion; preserve the negative result. Success authorizes a
create-only approved gate bound to the manifest, both summaries, analysis and
independent source review, then one fresh baseline and candidate pass over all
166 original Dev3 claims. Labels are loaded only after the relevant runs finish.
Report all claims plus non-pilot-payload and exact-payload grouped views. Full
one-pass results do not establish repeat stability, held-out accuracy or automatic
prompt promotion. Later inaccuracies and conclusion work remain deferred.

## Bounds and evidence

Fresh namespace: `task_09/09e1_20261012_luna_scope_claims_v1/`. Maximum 512 generations
(180 pilot +332 conditional full), $4 conservative reservations overall, $1 per
phase/arm, 90/166 requests and 1,800/3,600 seconds respectively. Each arm uses one
shared budget across repetitions. No truncation or resetting caps. Native token
cost estimates remain separate from actual invoices/promotional credits.
Credentials load only inside code from the untracked `.env`.

Reuse the reviewed package stage runner and external launcher/analyzer with fresh
input/code identities. Independently review the replacement prompt, preserved
inputs, gates, native receipts, metrics and source interpretations. Run focused
tests, `make fix`, `make check`, and `git diff --check`; expect only the known three
historical Task 06G failures. Verify prior inventories, scan raw/decoded logs for
credentials, record positive and negative outcomes, and seal a completion inventory.

Following [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices),
retain a fresh matched baseline and adversarial controls rather than judging the
candidate only on the ambiguous examples it was designed to improve. This is a
second development attempt; preserve the first failed attempt when reporting it.
