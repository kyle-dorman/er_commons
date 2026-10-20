# Task 11D.7 — Citation clause-check prompt preparation

Status: Prepared (2026-10-19); not evaluated.

## Scope and hypothesis

The user accepted the exact clause-check sentence proposed after 11D.6.
Create V9 from sealed V8 by appending only that sentence to claim-local evidence.
Hypothesis: an explicit check catches partially cited compound points that the
existing declarative citation rule did not prevent. Preserve the field contract,
examples, shared summary and edition-neutral condition. Do not change the
conclusion rule while its intended behavior remains under discussion.

## Limits and validation

This step prepares the prompt only: zero generation, judge or counting calls,
zero retries and spending. A live comparison needs a recorded dispatch contract
binding the new 11D.6 contexts, final labels and fixed six before execution.
Do not evaluate held-out or remaining development cases, change judges or start
11E. Preserve all sealed prior prompt/result bindings.

## Outcome and remaining discussion

[Target V9](../../docs/prompts/task11d7_target_v9.md) differs from V8 by exactly:
“Check that each point’s cited passages support every clause; add the missing
citation or remove the unsupported clause.” Exact single-addition verification
and git diff --check passed. No performance result is claimed.

The user's separate issue is conclusion completeness: material answer facts may
appear in support yet be omitted from the conclusion. Qualification relevance is
a different issue and does not resolve that failure. Existing rule 1 already says
supporting fields do not repair an incomplete conclusion. A possible next revision
would turn that into a concrete check: after drafting support, move each fact
needed to answer a requested part into the conclusion as well. Do not copy every
supporting detail. This suggestion is not included in V9.

## Accepted conclusion check

The user subsequently approved the proposed supporting-points check. V10 adds
exactly this sentence to V9's conclusion requirement:
“After drafting the supporting points, check that every fact needed to answer a
requested part also appears in the conclusion.”

[Target V10](../../docs/prompts/task11d7_target_v10.md) is the current prepared
revision. V9 remains preserved. Hypothesis: an explicit support-to-conclusion
check reduces omitted material answer facts without requiring every supporting
detail in the conclusion. The citation clause check, examples, field contract and
all other instructions are unchanged. Exact single-addition verification and
git diff --check passed. No live calls or performance claim; existing limits apply.
