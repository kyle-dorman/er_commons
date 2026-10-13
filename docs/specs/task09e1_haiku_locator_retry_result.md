# Haiku five-claim locator retry result

All **five of five** previously invalid claims now produce valid outputs after
one locator clarification. Every result retains `supported: false`, returns
`locators: []`, and explains that its cited source text is unavailable. Strict
validation is unchanged. This fits the diagnosis: the original semantic decisions
recognized missing evidence, but the optional locator fields were invalid.

| Original failed claim | New output | Support | Locators |
| --- | --- | --- | --- |
| C001 C05 P2 | Valid | Unsupported | Empty |
| C056 C05 P2 | Valid | Unsupported | Empty |
| C027 C05 P2 | Valid | Unsupported | Empty |
| C029 C05 P3 | Valid | Unsupported | Empty |
| C050 C05 P4 | Valid | Unsupported | Empty |

The exact prompt addition was:

> Locator diagnostics must refer only to an actual resolved citation in this input with available, nonempty source text. Do not emit a locator for an unresolved or missing citation, or for empty source text. If no valid supporting source is available, return "locators": [] and explain the missing evidence in the existing explanation field. Do not invent a citation or quotation. These diagnostic instructions do not change the support criteria or require a particular supported value; judge support under the original rubric.

The original input text, Haiku 5.5 native medium settings, output schema,
4,096-token cap and cache settings were preserved. Five calls ran once each,
with no automatic retries. The reservation was $0.019276 under the $0.10 cap;
actual native usage cost is estimated at **$0.00255**, about a quarter of one cent.
Independent postrun review verifies all five native receipts and decisions;
credential scans passed and all 16,500 files in the prior run remain unchanged.
Five focused offline checks passed before dispatch, and an independent reviewer
verified exact input and prior-request identities.

This is a selected-failure diagnostic, not a new full-panel score. Without an
unchanged-prompt control, it cannot isolate the prompt effect from sampling
variation or establish general accuracy/stability gains. The original Haiku/Luna
comparison and its failure penalties remain unchanged. No conclusions, GLM calls,
cache investigations, default changes, commits or pushes.

See the [frozen contract](task09e1_haiku_locator_retry_v1.md) and
[result pointer](task09e1_haiku_locator_retry_result.json) for the exact inputs,
request/output receipts, prompt difference, validation and independent review.
