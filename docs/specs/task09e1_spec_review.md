# Task 09E.1 implementation-spec independent review

Reviewed October 11, 2026 against Task 09E.1, the existing abstention/stage
contracts, frozen panel metadata and the local endpoint qualification.

**Disposition: approved for implementation, subject to the explicit fail-closed
qualification gates already in the design.** This is a design review, not a
claim that provider access, token counting or final implementation has passed.

The comparison contract preserves original point granularity and source
visibility, keeps gate input answer-only, excludes proposed labels from request
construction and requires complete ordered conclusion reviews. Its binary-only
interstage observations remove provider-specific explanation leakage. The
zero-point behavior matches the historical aggregation contract. The three-way
gate preserves ambiguity. The reviewed native mapping uses two independent
predicates over identical answer-only state: whether any substantive assertion
is present, and whether the whole answer is a clean abstention. False/false maps
to ambiguous; true/false to substantive; false/true to clean abstention;
true/true is an unscored inconsistent response. Each predicate uses the frozen
0.5 threshold with exact ties unscored. This retains ambiguity without assuming
categorical API support. Require explicit paired-predicate fixtures, including
empty/unclear answers and contradictory classifications.

Separating optional quotation diagnostics from semantic progression is explicit
and versioned. Required source-identity checks remain structural; historical
strict validation is a separate view. The implementation must test that strict
quote checks do not reappear during conclusion-input validation.

Exact model/endpoint/render-bound counting, every independent provider limit,
output/reasoning reserves and no silent truncation are mandatory. Local Clef
has an established 64 KiB endpoint limitation and lacks a qualified exact
decision counter; it must remain blocked pending qualification. Published
context claims and a chat tokenizer cannot satisfy this gate.

The budget and restart design reserves before dispatch, treats uncertain
outcomes conservatively and requires verified matching receipts for reuse.
Zero automatic retries is a bounded safe default. Provider caching is correctly
separate from saved-result reuse, and byte prefixes are not presented as exact
token eligibility. Actual native usage is required before claiming savings.

Before closing implementation, independently check that all seven configured
wire paths preserve these questions, decisions reject malformed/tied outcomes,
provider limits and rates fail closed when unknown, and Inspect owns actual
samples, scheduling and call receipts. The Phase 0 behavior-preservation review
remains a separate required checkpoint before any new provider code.
