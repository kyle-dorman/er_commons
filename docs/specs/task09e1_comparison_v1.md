# Task 09E.1 comparison contract v1

Status: implemented and independently reviewed; offline validation complete. October 11, 2026.

## Sequence and ownership

Phase 0 moves the existing native stage executor to its own module, preserving
golden requests and terminal results. Complete its focused tests and independent
review before implementing this contract. Historical strict validators, prompts,
settings and result pointers remain available and unchanged.

New comparison modules own semantic results, provider wire mappings, exact
preflight/budgets, and an Inspect scorer. Reuse validated packet projection,
create-only persistence and Inspect scheduling rather than a second evaluation
loop. No new runtime dependency is needed for typed HTTP adapters; installed
Inspect owns samples, native call receipts, logs and aggregation. Provider research
records why an existing provider does or does not fit each native request.

## Inputs and semantic decisions

Bind the existing 09A.3 panel manifest and select only its 69 Dev3 IDs for
C041/C037/C014. Verify packet, source, original answer and origin bindings.
Request preparation never loads expectations or references. Read restricted
proposed labels only in a separate post-run analysis step. Stream selected records
where a container also contains other development selections. Never open mixed
test question/reference containers or reserved payloads.

The native gate uses two predicates on the same answer-only state: substantive
assertion present and entire answer clean abstention. True/false routes substantive;
false/true routes clean; false/false routes ambiguous; true/true is an error.
Either probability tie remains an error.

The answer-only gate retains three outcomes: clean abstention, substantive and
ambiguous. A native decision mapping must preserve ambiguity explicitly; it must
not turn low confidence, refusal or malformed data into clean abstention.
Substantive answers receive one check for each original nonempty non-conclusion
point with only its actual citations and linked textual context. The final review
receives the full original grounding payload and ordered observations containing
only `point_id` and strict boolean `supported`. All providers use this projection.

The conclusion reviews every point, in order. Duplicate, missing or unexpected
IDs fail validation. Any disagreement yields `unresolved_disagreement`, score
null. Otherwise an unsupported conclusion scores 0, a supported conclusion with
any unsupported point scores 1, and all supported scores 2. Zero-point substantive
answers still receive conclusion review and can score 2. Clean abstention is N/A;
failure and ambiguity are unscored errors. No all-points-failed shortcut.

Generation uses the same semantic instructions across providers with the output
instructions adapted to the new versioned schema. Quote and unsupported-span
fields are optional diagnostics. Invalid citation identities still fail structural
validation; missing/nonliteral excerpts and nonliteral assertion spans do not
block semantic progression. Preserve historical strict-validation results beside
the semantic result when comparable. Native decision outputs contain no invented
quotes or explanations; their quotation diagnostics are not applicable.

Decision probabilities must be finite, in [0,1], with complete expected option
coverage. Boolean predicates use probability > 0.5; exact ties remain unscored.
Categorical decisions use unique argmax over a frozen option order; exact ties
remain unscored. Refusals, absent decisions and provider errors remain errors.
Native confidence is diagnostic, never calibrated correctness or our 0/1/2 rubric.

## Transport and qualification

Seven separate configurations pin the requested model and endpoint. Never
substitute models. Provider-specific schema adaptation and decision question
ordering are explicit and hashed. Batch only questions sharing exactly the same
visible payload and dependency stage. Provider research owns current capabilities,
pricing, caching thresholds/TTL/controls and exact-counter gaps.

Every dispatch requires an exact count bound to the complete rendered request,
model, endpoint and counter provenance. Both total-request and any independent
state-plus-longest-question limits apply. Reserve explicit output/reasoning tokens.
Unknown limits, unqualified counters or unverified model access block inference,
but do not prevent offline rendering and response-fixture validation.

Run serially with finite timeout, wall-clock, request and output caps. Paid calls
add an explicit positive currency cap and verified dated rates. Reserve worst-case
uncached input, cache-write premium and output charges before dispatch. Keep
possibly billed uncertain failures reserved. Never automatically retry an uncertain
network outcome or semantic result. Zero automatic retries is the conservative
default; any proven safe transient retry must consume a separate reservation.

Persist request identity, preflight, dispatch intent, response and completion in
that order. Existing incomplete/uncertain attempts cannot be blindly replayed.
Reuse only completed, checksum-verified receipts with identical request and
configuration identities. Saved-result reuse is separate from provider caching.
Never persist credentials, authorization headers or raw transport exception text.

## Offline audit and execution handoff

Render all possible stage requests for Dev3. For a static conclusion audit use
explicitly labeled synthetic all-false/all-true observations, not proposed labels
or claimed predictions. Runtime conclusions always render actual predictions.
Report common prefix bytes separately from exact tokens; do not claim byte
measurements prove cache eligibility. Unknown prices/counts yield unavailable
currency estimates, never zero. Report no-cache and plausible-cache bounds where
verified inputs permit, including cache-write costs and worst-case calls/output.

The cache probe is a separate bounded protocol operation, excluded from evaluation
denominators. Identical and shared-prefix probes must retain native read/write
usage; latency cannot establish cache hits and the first call may already be warm.

The local Clef trial requires qualified endpoint, pinned digest/runtime/tokenizer,
exact counting and no truncation on invented fixtures before the single Dev3 run.
A demonstrated missing endpoint or counter is a valid local blocker; do not
download weights that cannot resolve that blocker. Cloud calls remain disabled
in this implementation session, regardless of environment credentials.

## Validation

Golden Phase 0 regressions; strict booleans/probabilities/ties/refusals; quotation
separation through final-input revalidation; original evidence isolation; complete
ordered reviews; scoring including zero points; all seven native wire fixtures;
exact render/count binding and limit boundaries; native cache usage; caps,
uncertain attempts, resume and secret redaction; real offline Inspect logs.
Independent spec and final code reviews, focused tests, `make fix`, `make check`
and `git diff --check` are required. Record the three historical Task 06G failure
identities separately from any new failures.

## Implementation and measured boundary

`grounding_comparison_panel` verifies the exact old panel and selected original
records without loading expectation files. `grounding_comparison_semantics` owns
the common decisions and generation-only diagnostics; `grounding_comparison_providers`
owns seven wire contracts, explicit schema adaptations and native usage.
`grounding_comparison_safety` owns exact-count bindings and conservative reservations.
`grounding_comparison_inspect` owns execution and receipts through an Inspect scorer.
Audit, CLI and post-run analysis are separate small owners. No new package was added.

Generation schema adaptations relax only wire constraints unsupported by providers:
OpenAI strict fields are required (empty diagnostics are permitted); positional
review arrays become item unions with local exact ordering checks. Anthropic
unsupported length constraints move to descriptions. Every output is revalidated
against the common local contract. Native prompts remove generation-only output
directions and use the same semantic questions. All transformations change the
request identity and are covered by offline tests.

Run caps cover paid inference requests; authoritative counting calls are separate
unbilled preflight operations and stop when inference caps are exhausted. No
automatic retry is enabled. Usage is parsed before semantic output so a refusal or
malformed decision cannot erase billed usage or conceal a counter/cap mismatch.
Identity/counter/usage mismatches halt later calls. Budget reservations remain
conservative; no refunds based on assumed caching are made.

The CLI rejects live continuation into existing directories, preventing budget
and deadline resets. Completed-receipt reuse is available to the tested internal
adapter for offline replay, never permission to blindly retry a partial live run.
Missing counter evidence remains a blocker even if a credential is present.

The [handoff](task09e1_cloud_handoff.md) owns current commands. The
[result pointer](task09e1_final_result.json) binds final audits, tests and preserved
artifacts. Offline fixtures do not measure judge accuracy or cloud cache savings.
