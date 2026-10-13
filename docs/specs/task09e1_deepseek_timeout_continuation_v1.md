# DeepSeek undispatched continuation with a longer request timeout

Operational addendum to the user-authorized
[8,192-token experiment](task09e1_fireworks_repair_8192_v1.md), to finish its
remaining requested evaluation. The first DeepSeek phase dispatched 20 requests:
19 validated and one ended without a response at the existing 60-second transport
deadline. That uncertain request is a retained failure, not permission to replay it.
The other 988 planned claim slots were never dispatched.

Freeze fresh scripts under the current experiment's `timeout_continuation/`
directory. Preserve all initial manifests, outputs and scripts. Bind exactly the
988 `run_halted` claim slots with no native intent, retaining the 47 original valid
claims, original invalid locator, 19 new valid claims and one uncertain transport
failure. The earlier 4,096-token truncation remains in history; its pending retry
is eligible only if it was still undispatched in the 8,192-token phase.

Use a finite 180-second native request timeout, bounded by the remaining stage
wall allowance. Permit 14,400 seconds per new stage to avoid treating verbose
model throughput as permission to drop the rest of the requested panel. Keep
the 8,192-token output ceiling, medium effort, same pinned identity, prompts,
schemas, evidence-prefix caching and four-prefix concurrency. No changes to model
input or semantic validation. Correctly accounted output exhaustion remains a
failed individual output without retries; other infrastructure failures still halt.

Carry forward all 20 paid reservations, including the uncertain request, into the
original repair experiment's cumulative 1,438-call/$35 cap. Do not raise that cap.
The 49 attempts preceding this repair remain separately bound historical cost.
Only complete valid same-provider vectors proceed to conclusions; failed claims
cause explicit dependent skips. Never resend the uncertain request.

The initial analysis is superseded for execution by a separately frozen analyzer
that merges both phases. Keep the same 1,056/392/38 denominators, latest-only
comparison and item-matched failure analysis. Do not compute new accuracy results
until this continuation is terminal. Record runtime-setting mixture and the
unknown charge separately from measured native usage, preserve all failures,
independently review selection/accounting/transport guards, then scan and seal
the complete experiment. No additional model, data, prompt or budget expansion.
