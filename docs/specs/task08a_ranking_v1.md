# Task 08A ranking/input contract v1

First-use plan (2026-09-30): inspect Task 07 helpers; reuse
`pilot_context_repair.refresh_cases` for directed closure and exact span text;
add a narrow package adapter for accepted-input checks, one-group preparation,
proposal validation and no-clobber publication. Use source-free positive and
negative fixtures before the real packet. Independently review closure and
ranking faithfulness, then run `make fix` and `make check`.

## Shared boundary

Version: `task08a.ranking.v1`. One accepted group per invocation. No Label Studio
interface, human labels, rewritten question, or automatic eligibility exists in
this format. The initial selection template belongs to 08B. Saved rankings are
revisitable; model reruns need not reproduce them. Reranking requires a fresh
proposal version, reason and output directory; never overwrite an earlier packet.

Prepare inputs from the accepted grouping (pinned SHA-256), current inventory
result and its pinned acceptance/completion/managed inventory/components/handoff/
limitations. Check the exact release file set and sizes, verify consumed component
bytes, and verify all group members against source IDs and labels. Retain original
planning rows/flags, filter exceptions and complete reference outcomes. Seed the
maintained response closure helper from accepted views, then independently check
reachability from the comment's direct responses, including cycles. Reject other
comments in context and unresolved source/span/edge IDs. Never truncate context.

The packet contains one group record; candidates with exact IDs, direct response
IDs, complete context membership, relationship and reference IDs, warnings and
original planning metadata; deduplicated source units with original text, span IDs
and physical pages; relevant full edge and outcome records; inventory limitations;
and checked input references. Separately verified source-page footnotes may supplement
accepted response spans: retain their page IDs, exact offsets, text and associated
response ID without changing any accepted unit. No historical Task 07 review
state is imported.
Keep source provenance and rights references through the accepted inventory
handoff, rather than declaring a new source license.

## Proposal and handoff

Each proposal binds the exact input packet hash, prompt version/hash, actual model
identity and proposal version. Supply a complete total order with consecutive
ranks, one row per candidate. Each row has separate nonempty question-quality and
response-quality reasons, exact source-unit/quote anchors for both, and retained
concerns. Evaluate clarity/independent answerability and substantive rebuttal
jointly; do not use a score as an eligibility threshold. For a residual quality
tie, order by stable comment ID (lexicographic); record tie groups explicitly.
No tie is presumed merely because candidates share responses.

Missing or unusable sources block unsupported quality assertions; do not hide the
candidate. Preserve possible table-analysis status without claiming a calculation
or CSV requirement. Apply documented group exceptions explicitly. Human selection
and both eligibility passes remain pending even for rank 1.

The output seals the prepared input, proposal, ranked candidates, handoff and
validation report under a manifest. The manifest records input/output checksums,
shared prompt/spec/schema/code identities, actual model, proposal version and
policy. Write completion last, with the manifest hash. Verify exact managed-file
closure, hashes, membership, ranks, rationales, quote anchors and reproduction
against the accepted source inputs before reporting readiness. Reject unknown
proposal fields, invented question/selection/eligibility fields, stale hashes,
missing warnings and unresolved anchors. Semantic reasons still require source
review; syntactic validation cannot prove model judgments.

08B receives full original comments and responses plus advisory ranking. It must
qualify its own shared selection interface, then obtain human decisions. This
packet must not become the comment-only 08C wording input: response text and
response-derived reasons must be excluded from that later packet.

## Learning / reuse

The existing helper already handles directed links and deduplicates cycles; the
08A adapter adds group identity and advisory-ranking boundaries, not a new link
resolver or review engine. Plain JSON with the project's existing JSON Schema
validator supports explicit versioned contracts and rejects unexpected fields.
Canonical sorted JSON and SHA-256 bind exact saved bytes, not deterministic model
behavior. Primary references: Python's
[JSON documentation](https://docs.python.org/3/library/json.html) and JSON Schema's
[object-property contract](https://json-schema.org/understanding-json-schema/reference/object).

## Maintained commands

`make prepare-group-ranking` takes explicit `GROUPING_DIR`, `GROUPING_SHA256`,
`GROUP`, and a fresh `RANKING_INPUT` file. Optional `SOURCE_SUPPLEMENTS` supplies
exact source-page supplements when needed. `make publish-group-ranking` takes
`RANKING_INPUT`, `RANKING_PROPOSAL`, and a fresh `RANKING_OUTPUT` directory.
`make validate-group-ranking RANKING_OUTPUT=...` rechecks the sealed packet and
its original input bindings. Validation requires the recorded shared code and
schemas; an explicit interface revision must assess existing batches.
