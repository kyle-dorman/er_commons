# Provider validation-error continuation

This is a protocol-only continuation of the user-authorized [same-prompt model
comparison](task09e1_glm_haiku_full_dev_v1.md). Its original frozen contract,
requests, native responses and parser failures remain unchanged. No labels are
inspected to choose this continuation policy.

The first four GLM claim responses arrived successfully. The strict parser
accepted one and rejected three wrapped in one Markdown `json` code fence.
Independent offline inspection confirms that removing exactly that outer fence
makes all four responses valid JSON and valid under the existing semantic schema.
No escaping repair, value change or additional inference is needed. Preserve the
original three failures as format-compliance diagnostics.

Haiku stopped after 179 claim responses: 178 valid and one invalid because it
cited a source ID that was not resolved in the input. Preserve that invalid
judgment; do not repair its source ID or regenerate the answer. A whole-run stop
on this ordinary model-output error prevents the requested population comparison.
This continuation separates model-output errors from execution safety failures.

## Explicit parser and error policy

Use a small parser adapter in an isolated continuation process and bind its
source in a new manifest. For the pinned GLM prompt-schema condition only, it
may remove one complete outer JSON fence and surrounding whitespace. Retain
strict JSON and semantic schema validation; reject commentary, multiple fenced
blocks and malformed contents. No prompt, schema, medium effort, input text or
output-cap changes. No repository module or previously frozen script changes.
The original imported parser remains the validator after the wrapper is removed.
This experimental adapter is not a package-default promotion.

Continue after a model parse/schema error only when there is a completed,
checksummed native response with the correct model identity, normal completion,
and validated token usage within its input allowance and output reservation.
Retain its invalid status and count it as unscored. Clear only this explicitly
classified semantic halt synchronously; never clear a transport, uncertain
receipt, refusal/truncation, context, identity, usage, cost, or budget failure.
There are no retries or replacements for model-output errors.

## Bounded continuation

Derive separately checksummed records from all four saved GLM responses and all
179 saved Haiku responses. Carry every existing reservation into its provider's
original graph budget: at most 1,486 main generations, $15 GLM / $25 Haiku reserved,
and 4,096 output tokens per request. Generate only the remaining 1,052 GLM and
877 Haiku original claims, once each. Preserve all previous records in place.

After the claims finish, freeze actual same-provider decisions. Run a conclusion
only when every original claim for that answer has a valid decision; zero-point
answers remain eligible. Explicitly mark answers with missing valid claim
judgments as unscored, without fabricating a replacement value. At most 430
conclusion calls per provider; skipped conclusions do not trigger replacement
calls. Use fresh continuation directories. No labels are used in dispatch.

Independently review and test fence rejection, error classification, budget
restoration, uniqueness and incomplete-vector handling before dispatch. Freeze
all source/input/receipt bindings. Metrics keep the full development denominators
and separately report valid-output coverage, raw format compliance and recovered
responses. Compare to Luna under the same unchanged semantic rules and labels;
missing judgments stay visible rather than silently becoming false labels.

Stop after these two provider comparisons. No additional model/prompt arms,
reserved/test data, later tasks, commits or pushes. The original strict-stop
attempts remain inspectable alongside this explicitly versioned continuation.
