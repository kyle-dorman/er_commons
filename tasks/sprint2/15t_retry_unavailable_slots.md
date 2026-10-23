# Task15T — Authorized retries of three unavailable results

Status: complete.

## Goal and authorization

The user explicitly authorized retrying the two interrupted generations (Haiku
C008 repeat1 and Luna C011 repeat1), and increasing the conclusion judge output
limit to about6K to retry the truncated Luna C judgment of Haiku C011 repeat2.
Use6144 output tokens for these new C calls; keep generation and A/G/S settings,
inputs, labels, prompts and model reasoning unchanged. Evaluate the two returned
answers fully. No other answer or judgment is rerolled.

## Inputs, outputs and boundaries

Consume the sealed Task15S result and its exact selected inputs/identities.
Write fresh Task15T retry artifacts and a selected-results overlay. Preserve all
Task15S bytes and original failure records. Link each new attempt to its parent;
use new dispatch identities so the prior no-retry ledger stays intact. This user
request supersedes the prior no-retry restriction only for these three results.
Retain the prior$2.605799435 liability, including uncertain calls, within the same
$40 total budget; new-call cap is at most$37.394200565. Unknown counting fees remain
explicit under the previously accepted exception. No commits or pushes.

## Plan and validation

1. Inspect exact inputs, unavailable parent calls and maintained native APIs.
2. Add explicit6144-token C support without changing historical4096 defaults.
3. Prepare/check fresh retry identities, inputs and cumulative-budget reservation.
4. Dispatch two fresh generations plus full A/G/S/C and the one saved-answer C
   retry. One authorized attempt each; preserve any remaining failure.
5. Replay outputs, report per-slot results and incremental/cumulative costs,
   publish a compact294-slot selected-result overlay and updated totals.

Use focused runtime tests, routine make checks, independent preflight/result
review, exact native delivery/schema checks and git diff --check. Keep invalid
outputs unavailable; do not change rules in response to results. The6K output
budget is a disclosed execution-condition change, not a semantic prompt revision.
Task16 remains separately activated work; MiniMax/reserved challenges excluded.

## Outcome

All three authorized retries completed. The selected overlay now contains294 valid
answers and294 complete evaluations. C passed Haiku C008 repeat1 and failed both
C011 retries; model/computed C agree for all294 selected judgments. No other
answer or judgment was replaced. The C-only retry preserved its original candidate
and A/G/S exactly. The original Task15S publication remains immutable.

The [retry result](../../docs/specs/task15t_retry_result.json) selects the report,
parent-linked294-slot selection, audit and compact failure review. The latter
retains uncertainty about annualization materiality and reporting source-discrepant
numbers versus making an internal contradiction; neither interpretation rescored
any result. All three repaired answer slots fail joint evaluation.

New calls:2 generations,19 judges and21 counts. Incremental configured usage is
$0.023565930; cumulative known usage is$1.701929365 and retained liability is
$2.629365365 under the$40 cap.18 additional token-count calls have accepted unknown
fees, bringing that cumulative count to2419. Prior uncertain charges remain held.

Validation: independent preflight and final native/replay/accounting audits passed;
make fix and make check passed (4540 tests passed,1 skipped), with focused runtime
coverage for the6144 C cap and authorized attempt2 identities. Offline reporting
normalizes JSON array/tuple representation before comparing replayed plans; this
changes no evaluated output. Documentation diff checks passed.

Learning: preserve failed attempts and select their authorized replacements through
an explicit overlay. A larger output cap is an execution-condition change even
when prompt semantics stay fixed; disclose the three6144 C calls alongside the
291 retained4096 calls. Completion and model/aggregate agreement establish usable,
consistent outputs, not semantic correctness. No new tuning, calls, commits or
pushes; Task16 still requires separate activation.
