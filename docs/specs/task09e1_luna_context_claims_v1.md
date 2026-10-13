# Task 09E.1 — Contextual claim interpretation experiment

The user authorizes testing natural question-context interpretation on the
problematic claims, then the existing Dev3 claims if the pilot improves. Luna
Responses only, medium reasoning, repaired evidence-prefix caching, unchanged
4,096 output reserve and exact counter gates. No conclusion or abstention calls,
new models, truncation, Dev6/full-19, reserved/test access, commits or pushes.

## Inputs and prompt

Use the original 69-answer Dev3 packets and all 166 original point inputs. Preserve
the question, point, own cited sources, original IDs and optional linked context
exactly. The question already reaches the judge; this experiment changes its
interpretation instructions, not the evidence boundary. Labels never enter
requests, Inspect targets or inference metadata.

The baseline is the previous combined scope/absence/grammar point prompt. The
candidate appends a general contextual interpretation rule: assess the natural
meaning in the question's context, accept faithful ordinary summaries, and do not
reject solely on a possible alternative grammatical reading. Retain substantive
support, explicit conditions, modality and own-citation requirements. Question
context may resolve referents and geography but cannot establish facts. Freeze
both complete strings in `prompts.json` before dispatch; no target-specific
examples, expected decisions or iterative tuning after results.

The user's discussion accepts a natural policy-level reading for the pet-policy
claim in this development experiment. This is an explicit evaluation-policy
interpretation, not new factual evidence or a claim that the competing narrow
reading is impossible. Preserve original labels and source text.

## Pilot and fixed expansion gate

Pilot: four exact distinct troublesome inputs (short pet-policy S1 and S2 forms,
expanded policy, grading qualifier) represent the nine previously identified
unstable slots under the improved prompt. This is two semantic issue families,
not four independent questions. Six original controls cover strengthened modality,
invented fine amount, absent citations, universal scope, preserved modality and
bounded absence. All ten come from the existing eleven-answer subset. Freeze
their selection, aliases, expected decisions and rationales separately in
`pilot_diagnostics.json`; the launcher does not load that file's contents.

Each baseline/candidate arm gets nine fresh repetitions per input: 90 calls each.
Use identical input order and settings in concurrently dispatched arms; report
provider variation without treating arm scheduling as a randomized causal design.
No historical outputs substitute for fresh observations and no failure is replaced.

Expansion requires all of the following, evaluated only after both pilots finish:

- All 180 pilot outputs valid, exact count/identity checks passed, no replay.
- Candidate trouble agreement at least 30/36 and at least four more correct than
  the fresh baseline. Each trouble input at least 6/9 and no worse than baseline.
- Candidate controls 54/54 correct; no consistently wrong trouble input.
- Independent source review finds no new acceptance of concrete unsupported
  assertions under the user's contextual interpretation standard.

These thresholds are a conservative dispatch screen, not significance or promotion
criteria. If the baseline ceiling makes the improvement threshold unattainable,
record inconclusive and stop; do not relax it. Preserve a failed pilot without
expanding. The full launcher requires a create-only approved gate binding both
pilot summaries, analysis and predispatch identity.

If qualified, run one fresh baseline and one candidate pass on all 166 original
Dev3 claims, including pilot aliases, with matching model/settings. Report the
full panel and non-pilot-payload subset separately. This is development evaluation,
not held-out accuracy or a repeat-stability qualification. No automatic default
prompt promotion; classify remaining label disagreements for the next discussion.

## Bounds, analysis and review

Maximum 512 generations: 180 pilot + 332 full. Each of four phase/arm runs has a
$1 conservative reservation cap, at most 90 or 166 requests, 4,096 output tokens
per request, and 1,800 pilot / 3,600 full seconds. Overall maximum $4. No retries
or cap resets. Standard-rate native usage estimates are separate from invoice
charges and promotional eligibility. Load credentials only within code from `.env`.

Primary metrics: label agreement across every scheduled claim (invalids cannot
improve the denominator), false positives/negatives, valid coverage, per-input
repeat stability, and source-based regression review. Show repeated-slot and exact
payload deduplicated results separately where relevant; do not let duplicate pet
claims masquerade as independent evidence. Report actual cache buckets and payer
metadata. A gain in support rate alone is not success.

Fresh external namespace: `task_09/09e1_20261012_luna_context_claims_v1/`.
Preserve frozen inputs/prompts/code identities, native receipts, Inspect logs,
pilot gate, both positive/negative results and independent reviews. Verify prior
sealed artifacts, scan raw and decoded logs for credentials, and seal a completion
inventory. Use the existing package stage runner without changing defaults.
Run focused checks, `make fix`, `make check` and `git diff --check`; the known full
suite has three historical Task 06G failures. Review launcher/gate before dispatch
and results/source interpretation before closeout.

Research: [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
supports task-specific tests with typical, edge and adversarial cases, explicit
metrics and human calibration. Here the controls prevent contextual leniency from
turning into acceptance of unsupported facts; a matched fresh baseline separates
the prompt change from the earlier reasoning-setting change.
