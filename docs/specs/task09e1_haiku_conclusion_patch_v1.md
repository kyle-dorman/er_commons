# Haiku five-conclusion patched diagnostic

The user explicitly authorizes running the five conclusions previously skipped
because of invalid Haiku claims, using the five now-valid outputs from the
[locator retry](task09e1_haiku_locator_retry_result.md), and reporting updated
full-development results despite the mixed claims prompts.

Run exactly these five answer conclusions once. Keep the original visible-review
conclusion prompt, Haiku 5.5 native medium settings, structured schema, 4096 output
cap and cache configuration. Reconstruct each complete same-provider claim vector
from the original valid claims, replacing only the five failed claims with their
sealed retry decisions. No new claims or other conclusion retries. The two earlier
invalid conclusion outputs remain failures. GLM and cache investigation stay paused.

Freeze five payloads, vectors, scripts, prompt/model identities and prior artifact
bindings in new external namespace `09e1_20261012_haiku_conclusion_patch_v1`.
Use Inspect and the existing estimated-counter/conservative-allowance runtime.
Caps: five calls, $0.10 total reservation, 20,480 output tokens, 300 seconds.
No automatic retries. Read keys internally from `.env`, never `base.env`.
Independent review verifies exact selection, vectors, unchanged conclusion prompt
and caps before dispatch. Preserve prior artifacts; no imports into sealed script
directories. No runtime package changes, commits, pushes or reserved/test use.

Recompute the full-panel metrics as a separately named patched result: original
1,056-claim predictions with only five validated replacements, original 430-answer
conclusions with only five newly supplied results. Keep the same 392 substantive
and 38 clean-N/A denominators, coverage-aware and conditional class-macro F1,
accuracy, claim-review, numeric-score and unresolved-disagreement metrics. Compare
Luna, original Haiku and patched Haiku, preserving original results unchanged.
Labels are only for offline scoring, never model inputs. This is a selected repair
with mixed claims prompts, not a fresh controlled experiment or default promotion.
Audit native outputs and independently verify metric totals. Record focused tests,
cost, credential scan, prior preservation and completion-last pointer. Run
`git diff --check`; no broader tests required without maintained code changes.
