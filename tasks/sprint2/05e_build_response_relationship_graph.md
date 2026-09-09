# Task 05E: Build the Response Relationship Graph

Status: **complete and accepted after the post-candidate human code-quality
gate**.

## Abstract

Resolve explicit relationships among the accepted Volume 4 comments,
individual responses, and General Responses without reopening the source PDF or
changing source transcription. Start with one exact-only, source-free pass over
the complete accepted Task 05D records. Account individually for every raw
intra-Volume mention and every General Response membership claim, then stop and
review the observed nonmatches before proposing any bounded normalization or
sub-answer rule.

Task 05E produces one accepted working graph revision for Task 05F. It does not
resolve Draft EIR targets or publish the final `inventoryv1` release.

## Goal

Produce a deterministic, bidirectionally valid intra-Volume graph and compact,
provenance-preserving review indexes while keeping exact source identity,
resolver policy, human review, and derived display material separate.

## Authorization gates

The user accepted this revised contract and authorized source-free Gate 1 on
2026-09-09. On 2026-09-09 the user separately authorized bounded Gate 2 review
replays containing only the amendments recorded below, then authorized the
source-free terminal-candidate gate after all review cases closed. The user
then accepted the graph substance, required a deeper human code-quality gate,
and authorized any source-free reruns needed by repairs. Acceptance was written
only after that gate passed.

1. **Gate 1 - source-free exact baseline:** after explicit authorization,
   implement the 05E activity, strict input binding, exact-only resolver,
   individual terminal diagnostics, graph validator, review-view recipes,
   fixtures, focused tests, and maintained command. Consume only the accepted
   Task 05D candidate and compact acceptance metadata. Do not open, render,
   extract, hash, or copy the source PDF. Run the complete exact-only census,
   write a nonterminal baseline report, and stop before promoting any
   normalization or sub-answer rule.
2. **Gate 2 - reviewed bounded resolution:** only after Gate 1 findings are
   presented and the user separately accepts any proposed rule amendments,
   implement those exact amendments and replay the graph from the unchanged
   accepted 05D input. If no amendment is accepted, an explicitly accepted
   exact-only policy may proceed instead. Close every in-scope mention and
   membership individually, run graph and maintainability review, and present
   one terminal working candidate for separate acceptance.

Neither gate authorizes source-PDF access, mutation of Task 05D, Draft EIR
resolution, cleanup, commit, push, formal candidate acceptance, Task 05F, or
later work.

## Accepted input binding

Task 05E binds the accepted Task 05D working revision:

- candidate
  `revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030`;
- activity
  `activityv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030`;
- completion
  `completionv1-82d534e4e3cc7db7275892690fe4d357540131c9477775d5ebf1d54ad6ab555f`;
- managed inventory
  `fileinventoryv1-a04c715a6dff6bdfe6d28eaed9b40211382d60a74d540cdf46cd3b2c993c60a0`;
- semantic digest
  `f7aa9fd6e6d4e464b27b270e6f61a8dcbfb0d998dc44e7eda84abd07db5d9247`;
  and
- adjacent acceptance
  `acceptancev1-7edf64ffd5e283c736e9980c79f682997ce06c135038d4ceb3ecbc496ce6c027`.

The candidate and acceptance pointer are respectively:

```text
working/05d/revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030/
working/05d/revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030.acceptance.json
```

Preflight must verify the adjacent acceptance pointer, its exact named
activity, completion, managed inventory, semantic digest, accepted downstream
consumer, terminal completion state, and managed-file closure. It must not
recursively rehash accepted payloads or copy 05D records into the 05E candidate.
The 05E activity and managed-file inventory must carry identical ordered
dependency references to the accepted 05D input.

## Observed source-free census

The accepted 05D record population contains:

- 2,029 source units: 1,011 comments, 1,010 responses, and 8 General Responses;
- clean, unique official labels that exactly match all accepted unit-start
  markers;
- 1,270 raw reference mentions, of which 759 are `intra_volume`, 509 are
  `draft_eir`, and 2 are `appendix_q`;
- exactly one target occurrence in each of the 759 intra-Volume mentions;
- 101 General Response membership claims; and
- intra-Volume mention sources comprising 10 comments, 675 responses, and 74
  General Responses.

The accepted exploratory audit of the 759 intra-Volume targets found 245 exact
unit-label matches, 8 candidates recoverable through bounded whitespace
normalization, and 506 non-exact targets. The non-exact population includes 227
obvious prose-like strings such as `response is`, `Response to`, and
`Response\r\nThe`. These are raw mention evidence, not presumed links.

`Comment SA-CHSRA-29` has no source-authored response heading and remains an
expected source-authored orphan. `Comment SA-Caltrans-48` versus
`Response SA-Caltrans-48a` is a known review case. Letter-suffixed response
labels may represent legitimate sub-answers where one comment contains
multiple questions, but that possibility does not authorize automatic pairing.

## Frozen Gate 1 resolution policy

- Build a unique endpoint index from accepted 05D `source_unit.official_label`
  values. Never infer an endpoint from source text, semantic similarity, or
  neighboring order.
- For direct comment-to-response pairing, remove only the fixed record-kind
  prefix (`Comment ` or `Response `) and require the remaining official label
  to match byte-for-byte and uniquely. Retain both accepted start-marker IDs as
  edge evidence.
- For raw intra-Volume mentions, require the target label to match one existing
  official unit label byte-for-byte and require the source and target kinds to
  fit a relation type already allowed by the accepted v1 contract.
- For General Response membership claims, require the claim's target label to
  match one existing comment label byte-for-byte and uniquely.
- Do not normalize whitespace, punctuation, case, prefixes, ranges, or
  letter-suffixed labels in Gate 1. The 8 whitespace candidates and all
  parent/sub-answer cases remain explicit nonmatches for review.
- Emit at most one normalized edge for one relation type and endpoint pair.
  Multiple supporting mentions or memberships attach as ordered evidence to
  that edge rather than creating duplicates.
- Every intra-Volume mention and every membership claim receives an individual
  outcome: supporting evidence on one exact edge or one terminal diagnostic
  naming that exact input record. Nothing is silently filtered because it looks
  prose-like or repetitive.
- Gate 1 diagnostics are terminal under the frozen exact-only policy, but the
  entire Gate 1 namespace remains a nonaccepted baseline. Gate 2 regenerates
  affected outcomes under the separately accepted amended policy; it does not
  mutate or present the baseline as the terminal 05E candidate.
- `draft_eir` and `appendix_q` mentions remain unchanged for Task 05F. Gate 1
  must prove that it neither resolves nor terminally closes them.

## Post-baseline rule-amendment policy

Gate 1 groups nonmatches only for human comprehension; grouping never replaces
individual accounting. Its report must separate at least exact target misses,
unsupported endpoint-kind combinations, whitespace or line-break variants,
punctuation variants, range-like targets, prose-like targets, ambiguous exact
identities, parent/sub-answer suffix patterns, orphans, and cycles.

Any Gate 2 normalization must be narrow, deterministic, provenance-preserving,
and independently tested against positive and negative controls. The amendment
must name the exact observed class it addresses, retain the raw target and
mention evidence, and prove that it yields one unique compatible endpoint.
Near matches do not become links merely because they are plausible.

Parent/sub-answer patterns such as `SA-Caltrans-48` and `SA-Caltrans-48a` must
be reviewed after the exact pass. Review should determine whether the suffix
represents source-authored decomposition of multiple questions, an unrelated
unit, or an unresolved case. No generalized suffix rule may be promoted from a
single example or without collision and negative-control tests.

## Outputs

- A source-free, package-backed 05E producer under the existing `er-responses`
  interface, with a strict portable run specification and structured logging.
- One replaceable Gate 1 baseline under `working/05e/` containing the complete
  exact-match census, individual outcomes, rule-level summaries, graph
  accounting, and proposed bounded amendments. It is not a terminal candidate.
- After separately authorized Gate 2, one `working/05e/<revision-id>/` candidate
  containing only 05E-owned activity, semantic-edge, diagnostic, review-view,
  managed-file-inventory, completion, and compact report records.
- Normalized `comment_response`, `response_response`,
  `response_general_response`, `general_response_membership`, and
  `general_response_response`, and `general_response_general_response` edges
  only where endpoint kinds and evidence satisfy the accepted schema.
- Raw-mention-to-edge and membership-to-edge provenance without copied source
  text.
- Individual orphan, dangling, ambiguous, unsupported-form, and cycle
  diagnostics with deterministic explanatory messages.
- A bidirectional graph-closure report and compact
  `comment -> direct response -> linked response/General Response` review-view
  indexes retaining ordered unit IDs, edge IDs and types, anchors, and rendering
  recipes that retrieve text from the accepted 05D source-unit store.
- A human code-quality report and, after explicit user acceptance, one compact
  adjacent acceptance pointer designating the unchanged 05E candidate for Task
  05F.

No joined text, HTML, source records, PDF bytes, or 05D caches belong in 05E's
authoritative managed closure. Materialized joined views remain regenerable
working cache.

## Research / learning checkpoint

Confirm the accepted response-inventory graph and diagnostic semantics before
implementation. Census actual source/target kinds and target-label forms before
defining a rule beyond exact identity. Explain why normalized edges and derived
views coexist: a General Response may serve many cases, and copying its text
into each source unit would erase provenance and create inconsistent
duplicates. Explain why exact matching is the baseline and why observed
failures, collision tests, and negative controls must precede normalization.

Reopen the v1 record schema only if the exact baseline proves that an observed
relationship cannot be represented or individually closed. A noisy mention or
unsupported relation is not by itself evidence that a new edge type is needed.

## Plan

1. In Gate 1, validate the accepted 05D pointer and candidate closure without
   source access or recursive rehashing.
2. Implement the exact unit index, direct-pair policy, mention and membership
   resolution, individual terminal diagnostics, deterministic aggregation, and
   source-free validators against fixtures.
3. Run the exact policy over the full accepted record population. Reconcile all
   source units, 759 intra-Volume mentions, and 101 membership claims. Produce
   the nonterminal failure census and stop.
4. Present every observed failure class, exact examples, collision risks,
   negative controls, and proposed rule amendments. Obtain separate
   authorization before changing matching behavior.
5. In Gate 2, implement only accepted amendments, replay from unchanged 05D
   records, and preserve raw evidence plus the exact resolver rule on every
   edge or terminal outcome.
6. Build forward and reverse adjacency, cycle and orphan diagnostics, compact
   review indexes, count reconciliation, repeatability evidence, managed-file
   closure, and completion-last publication.
7. Perform the human code-quality gate and present the unchanged terminal 05E
   candidate for separate acceptance. Do not activate Task 05F implicitly.

## Validation

- Reject any 05D candidate or acceptance-pointer mismatch before reading source
  records.
- Account exactly and individually for all 759 intra-Volume mentions and all
  101 membership claims; no input may be both resolved and terminally
  unresolved or receive more than one terminal outcome.
- Account for all 2,029 source units through graph participation or an explicit
  orphan/non-applicable determination without turning ordinary unreferenced
  content into an error.
- Require one unique compatible endpoint for every edge and exact accepted
  evidence for its relation type.
- Preserve `Comment SA-CHSRA-29` as an expected source-authored orphan unless a
  later source-owning task changes the accepted 05D input.
- Keep `SA-Caltrans-48` versus `SA-Caltrans-48a`, all whitespace variants, and
  all other near matches unresolved in Gate 1.
- Validate forward adjacency against reverse derivation, one-to-many and
  many-to-one cardinalities, duplicate-edge aggregation, cycles, dangling
  references, ambiguous identities, and General Response membership closure.
- Prove identical semantic output under input reordering, clean repetition, and
  a no-input reuse invocation.
- Verify every authoritative review view retains ordered unit IDs, edge IDs and
  types, and anchors. Retrieve joined text only from the accepted 05D store as
  regenerable cache.
- Confirm Task 05D files and records are unchanged and no PDF, source payload,
  upstream cache, or joined text is copied or rehashed.
- Run focused positive, negative, ambiguity, suffix, whitespace, range,
  prose-like, cardinality, cycle, dependency, and corruption tests; the
  maintained response-inventory contract; `make check`; and `git diff --check`.

## Human code-quality gate

Before recommending a Gate 2 candidate for acceptance, review the 05E code as
a person-maintained workflow rather than only as passing behavior:

- **Readability:** Are exact matching, endpoint compatibility, aggregation, and
  terminal-outcome rules obvious from short named functions and fixtures?
- **Editability:** Can one bounded rule be added or removed without changing
  source records, unrelated relation types, or orchestration?
- **Debugging:** Do diagnostics identify the mention or membership, raw target,
  attempted rule, candidate endpoints, and terminal reason?
- **Operations:** Is the source-free run restartable, completion-last,
  deterministic, and clear about baseline versus accepted-rule output?
- **Testing:** Do positive and negative controls independently exercise every
  promoted rule, especially whitespace and letter-suffix behavior?

Material maintainability findings must be repaired and replayed before
candidate acceptance; a green test suite alone does not close this gate.

## Acceptance criteria

- Both execution gates remain source-free and bind exactly the accepted 05D
  candidate and acceptance pointer.
- Gate 1 completes the exact-only population census and stops before any
  normalization or suffix rule is promoted.
- Every intra-Volume mention and membership claim has one provenance-preserving
  edge or one explicit individual terminal outcome under the accepted policy.
- No prose-like, range-like, whitespace-normalized, fuzzy, semantic, or
  suffix-derived edge is created without an explicit reviewed Gate 2 rule.
- Every edge targets existing, uniquely compatible source units and validates
  in both graph directions.
- Orphans, dangling references, ambiguities, unsupported forms, and cycles
  remain discoverable without forcing graph closure.
- Review views are deterministic derivatives and never become canonical source
  units or copied source text.
- The implementation passes focused, contract, repository, repeatability, and
  human code-quality gates.
- One explicitly accepted 05E working revision can be consumed by Task 05F
  without changing Task 05D or this graph.

## Review pass

- **Graph integrity:** Are forward/reverse edges, cardinalities, aggregation,
  cycles, and diagnostics internally consistent?
- **Provenance:** Can every edge or terminal outcome be traced to one exact raw
  mention, membership, or accepted marker pair without copied text?
- **Resolution precision:** Could any rule promote ordinary prose, a range, a
  parent label, or a plausible but wrong letter-suffixed target?
- **Completeness:** Does every in-scope input have exactly one individual
  outcome, including repetitive nonmatches?
- **Maintainability:** Can a future curator understand, test, diagnose, and
  safely amend one rule through the documented interface?

## Non-goals

- Reopening or visually reviewing the source PDF, changing 05D transcription,
  segmentation, labels, anchors, or accepted diagnostics.
- Draft EIR target resolution, Appendix Q extraction, Final EIR or external
  reference resolution, or mutation of out-of-scope mentions.
- Fuzzy matching, edit-distance matching, embeddings, semantic inference, or
  response-outcome and substantive-answer judgment.
- Treating a parent/sub-answer suffix as a relationship without post-baseline
  human review and an accepted bounded rule.
- Response classification, benchmark eligibility, clustering, split selection,
  evidence authoring, final `inventoryv1` publication, cleanup, commit, push,
  Task 05F, or later work.

## Gate 1 outcome

The revised contract was accepted and source-free Gate 1 was explicitly
authorized on 2026-09-09. The implementation adds a strict v3 05E run
specification and schema, exact accepted-05D preflight, package-backed
`er-responses build` dispatch, exact-only resolver, individual terminal
outcomes, edge aggregation, cycle detection, deterministic comment-rooted
review indexes, a nonterminal baseline receipt, and focused positive and
negative tests.

The final baseline is:

```text
working/05e/baselinev1-50ae2f7de5f28e882e62627db103e03f0059677fcdfc1e1f8be3a9bf5232b778/
```

Its activity is
`activityv1-50ae2f7de5f28e882e62627db103e03f0059677fcdfc1e1f8be3a9bf5232b778`,
its semantic digest is
`27ebe74712ea556ee66d2343e7228e2007c49d5f882aa834ba09d1ee517ec71e`,
and its census digest is
`ff509e0a5434b7a4e41a83ac94b950c3a70a84f99f954aca57d1fd0f087ff246`.
Two invocations returned the same activity, counts, semantic digest, census,
and file bytes. The baseline contains no managed inventory, stage completion,
acceptance record, copied 05D records, joined text, or source payload. The
source PDF was not opened, imported through the 05E path, rendered, extracted,
hashed, or copied. That Gate 1 outcome did not itself authorize Gate 2.

The exact pass produced 1,243 unique edges: 1,009 direct
`comment_response` edges and 234 `response_response` edges. All 2,021 comment
and response units received direct-pair outcomes: 2,018 unit outcomes resolve
to the 1,009 paired edges, while these three labels remain unpaired:

- `Comment SA-CHSRA-29`;
- `Comment SA-Caltrans-48`; and
- `Response SA-Caltrans-48a`.

The first is the accepted source-authored missing-heading orphan. The latter
two remain the known parent/sub-answer review case; Gate 1 created no suffix
edge.

Of 759 intra-Volume mentions, 245 had byte-exact target identities. Four of
those exact identities originate in `GENERAL RESPONSE 6` and target response
units, an endpoint-kind pair absent from the v1 edge vocabulary. Gate 1
therefore resolved 241 mentions and closed 518 individually with terminal
diagnostics. Repeated evidence was aggregated, so 241 resolved mention records
support 234 unique response-to-response edges. The 518 unresolved mention
outcomes are:

| Exact-pass class | Occurrences | Gate 1 disposition |
| --- | ---: | --- |
| General Response case variant | 224 | unresolved |
| General Response whitespace plus case variant | 4 | unresolved |
| response-label whitespace variant | 8 | unresolved |
| trailing-punctuation variant | 15 | unresolved |
| reviewed obvious prose-like form | 227 | terminal unsupported form |
| other nonexact form | 36 | unresolved |
| exact identity with unsupported endpoint kinds | 4 | terminal unsupported form |

The 227 obvious prose-like occurrences reproduce the reviewed families
`response is`, `Response to`, and `Response` followed by `The` across line
breaks and case variants. The 36 other nonexact occurrences remain visible
individually; the largest repeated forms are `response times`, `response
vehicles`, `response actions`, `response and`, `Response M`, `response access`,
and `response regarding`. Gate 1 did not treat the census classifier as a
matching rule.

All 101 General Response membership claims remain unresolved in the exact
baseline because their source-authored targets are suffix labels such as
`O-GA-9`, while comment-unit official labels include the fixed `Comment `
prefix. A source-free counterfactual check found that adding only that typed
record-role prefix would select one unique comment for 95 claims. Six would
remain unresolved: General Response 4 claims `O-OSEC-106`, `O-OSEC-370`,
`O-OSEC-371`, `O-OSEC-375`, and `O-OSEC-379`, while General Response 8 has the
truncated claim `M-CSSC`.

The exact graph contains two response-response cycles:

- `Response SA-CHSRA-5` and `Response SA-CHSRA-12`; and
- `Response SD-BSD-4` and `Response SD-BSD-5`.

They remain explicit review diagnostics rather than automatic failures.

### Proposed Gate 2 amendments - not accepted or authorized

The source-free counterfactual census supports presenting these amendments for
review, one rule at a time:

1. Interpret a membership claim's `target_label` according to its typed schema
   role by comparing it byte-for-byte with the suffix of a unique `Comment `
   official label. This would resolve 95 claims and preserve the six misses.
2. Canonicalize only the fixed phrase `General Response` for case when the
   result selects one unique General Response. Of 224 case-only occurrences,
   170 are representable `response_general_response` links. The remaining 54
   originate in General Responses and require separate endpoint-type review.
3. Collapse only source line-break whitespace when the result selects one
   unique compatible endpoint. This would resolve seven response-to-response
   mentions and four response-to-General-Response mentions. One additional
   whitespace case originates in a General Response and requires endpoint-type
   review.
4. Remove exactly one terminal sentence period when the result uniquely names
   a compatible response. This would resolve all 15 observed punctuation
   variants.
5. Review the 59 potential General-Response-origin relationships before
   changing the v1 schema: 54 General-Response-to-General-Response case
   variants and five General-Response-to-response references, four byte-exact
   and one whitespace variant. If these are genuine source relationships, new
   `general_response_general_response` and `general_response_response` relation
   types may be needed; Gate 1 did not invent them.
6. Review `SA-Caltrans-48` versus `SA-Caltrans-48a` as a document-specific
   parent/sub-answer case before proposing any suffix rule. The exact baseline
   supplies no evidence for a general automatic suffix policy.
7. Keep the 227 obvious prose-like mentions terminally unsupported. Review the
   36 other nonexact forms before deciding whether any class merits a rule;
   none is promoted by this outcome.

Prepublication validation first caught an incorrect review-view field name and
then rejected an attempted implicit `Comment ` membership prefix. Both runs
stopped before writing a baseline. A later valid baseline under the earlier,
broader census classifier is preserved as replaceable nonaccepted working
evidence at `baselinev1-7ee7a075a23e8597b4796cd38a0ffec989264a525f0a0342327084e085120527`;
the final identity above supersedes it for Gate 1 review. Cleanup remains
separately gated.

Validation evidence:

- 65 focused response-inventory and relationship tests passed;
- the maintained response-inventory contract accepted all 8 fixtures;
- `make validate-response-relationship-exact-spec` passed with final run-spec
  SHA-256
  `1f873a0d7b8f869c669bcbdc927619892b8ec774a9a2cd5245122e6b05ae06e2`;
- Ruff formatting and lint, strict mypy, and complexity checks passed;
- `make check` passed all 1,360 repository tests; and
- `git diff --check` passed.

The next action is user review of the exact failure population and the proposed
Gate 2 amendments. This outcome does not authorize any matching change, schema
change, Gate 2 execution, baseline cleanup, commit, push, Task 05F, or later
work.

### Read-only Gate 1 review aid

A separately generated review cache at
`working/05e/review_tool_gate1_v1/` presents the bounded pre-Gate-2 population:
59 General-Response-origin references, 36 residual nonexact mentions, six
membership claims that remain absent after the typed-prefix counterfactual, and
the grouped `SA-Caltrans-48` / `SA-Caltrans-48a` parent/sub-answer case. This is
102 unique review cases.

The page initially loads only a 27,073-byte compact index and its small static
shell. Selecting a case fetches one JSON shard, currently no larger than 4,937
bytes. Full accepted unit text is split into 33 separately fetched shards, and
an existing accepted 05D page render receives an image URL only after the
reviewer explicitly requests it. The page contains no feedback controls,
decision persistence, copied renders, or source PDF. It is a regenerable review
cache, not an authoritative 05E output or a Gate 2 decision.

### Bounded Gate 2 review replay

The user authorized one source-free replay limited to these reviewed rules:

- compare official mention labels case-insensitively only when exactly one
  accepted endpoint remains;
- collapse source line-break and ordinary whitespace only when the result is
  one unique endpoint;
- classify a normalized mention whose endpoint is its own General Response as
  `self_mention` without creating an edge;
- add directional `general_response_response` edges for explicit General
  Response references to accepted individual responses;
- create soft `general_response_membership` edges by adding only the typed
  `Comment ` role prefix;
- apply the visually confirmed General Response 4 source typo aliases from
  `O-OSEC-{106,370,371,375,379}` to their corresponding `M-OSEC-*` comments;
  and
- recover U+0002 only when it interrupts a reference mention after a single
  organization-prefix letter and replacing it with a hyphen yields one unique
  endpoint. This applies to reference mentions, not membership claims.

No terminal-punctuation rule, parent/sub-answer rule, edit-distance matching,
or semantic matching was authorized. The replay is nonterminal and retained at:

```text
working/05e/reviewpassv1-955065a590ee273054549cae4ecdeae59b070b99c33b8dc0b28c0d482f80b23d/
```

It resolves 429 of 759 intra-Volume mentions and 100 of 101 General Response
membership claims, producing 1,521 unique edges: 1,009 `comment_response`, 243
`response_response`, 166 `response_general_response`, 100
`general_response_membership`, and 3 `general_response_response`. The U+0002
rule recovered `Response M-OSEC-173` and `Response M-OSEC-265`. Forty-four
General Response self-mentions now close explicitly without edges.

The remaining mention outcomes are 227 accepted prose-like forms, 44 explicit
self-mentions, 34 residual nonexact forms, 15 terminal-punctuation variants,
and 10 unsupported General-Response-to-General-Response references. The sole
remaining membership miss is the malformed General Response 8 `M-CSSC` claim;
per user direction it is preserved but omitted from further review. Direct-pair
orphans remain unchanged.

Cycle detection now reports four strongly connected components. Two are the
unchanged reciprocal response pairs from Gate 1. The other two are expected
compositions created by viewing typed membership, direct comment-response, and
normalized response-to-General-Response edges in one directed graph: a
21-unit component centered on General Response 4 and a 172-unit component that
connects General Responses 1, 3, 5, 6, 7, and 8 through member
comment/response paths. They are topology diagnostics, not evidence of fuzzy
endpoint selection.

A refreshed read-only review cache at `working/05e/review_tool_gate2_v1/`
contains 60 cases: the 10 cross-General-Response references, 34 residual forms,
15 punctuation variants, and the grouped Caltrans parent/sub-answer case. It
keeps the same one-case-at-a-time text and explicit-click render loading policy.
The replay was byte-identical on a second invocation, accessed no source PDF,
and wrote no stage completion or acceptance record. The v4 run-spec binding,
focused tests, Ruff, strict mypy, `git diff --check`, and all 1,366 repository
tests pass.

### Refined bounded Gate 2 review replay

Subsequent case review authorized six additional bounded behaviors: classify
the known top breadcrumb line as `running_header`; classify the eight
`b. Response` labels plus their following word as `response_section_heading`;
classify unresolved `response` plus an alphabetic word of at least two
characters as `ordinary_prose`; strip exactly one terminal period before a
unique endpoint lookup; add directional `general_response_general_response`
edges; and allow the U+0002 separator rule to compose with case normalization.
No parent/sub-answer, edit-distance, arbitrary punctuation, or semantic rule
was added.

The fresh nonterminal replay is:

```text
working/05e/reviewpassv1-beb0801712d3a921226201aa437133ae0d3459d510603b54f34a2f6f072fd593/
```

Its activity is
`activityv1-beb0801712d3a921226201aa437133ae0d3459d510603b54f34a2f6f072fd593`
and its semantic digest is
`5843fe1e6f1dcee608d0575668841cc7e173975e083ea5a20cff8c9bc9212a05`.
Two invocations produced byte-identical files and counts.

The replay resolves 448 of 759 intra-Volume mentions and 100 of 101
memberships into 1,538 unique edges: 1,009 `comment_response`, 257
`response_response`, 166 `response_general_response`, 100
`general_response_membership`, 3 `general_response_response`, and 3
`general_response_general_response`. The no-edge terminal populations are 44
running headers, eight response-section headings, 251 ordinary-prose mentions,
seven genuine self-mentions, and one reviewed source-label typo. The lowercase
separator case now resolves
`response M\u0002OSEC-119` to the unique `Response M-OSEC-119` endpoint.

The final two reviewed cases create no edges. `Comment SA-Caltrans-48` and
`Response SA-Caltrans-48a` are retained as `reviewed_non_pair_source_form`
direct-pair outcomes because the source form does not justify inventing a
comment-response relationship. `Response OSEC-21` is retained as
`reviewed_source_label_typo_unresolved` because the omitted organization prefix
has no safe general repair rule.

Five cycle diagnostics remain explicit. They comprise the two original
response pairs, the two expected General-Response membership/reference
components described above, and a newly complete reciprocal pair between
`Response M-OSEC-196` and `Response M-OSEC-173` after the reviewed terminal
period is removed.

The refreshed read-only cache at `working/05e/review_tool_gate2_v4/` contains
zero remaining cases. It retains the lazy loading and no-feedback contract.
The replay accessed no source PDF and wrote no stage completion or acceptance
record. The v4 run-spec binding, focused tests, Ruff, strict mypy, all 1,370
repository tests, and
`git diff --check` pass.

### Terminal candidate outcome

The separately authorized terminal-candidate gate formalized the
human-maintainability assessment without repeating the completed rule review.
Readability, editability, debugging, operations, and testing each pass with no
material findings. The report is bound to the exact final review activity and
semantic digest and checksums every reviewed repository file, so later code
drift cannot silently reuse the assessment.

The package-backed `er-responses finalize-05e` transition validates the closed
review receipt and all of its files, revalidates the accepted Task 05D records
and complete 05E graph together, and atomically publishes completion last. It
copies only the unchanged small 05E review payloads, receipt, and quality
report. It does not copy source records, joined text, renders, caches, or PDF
bytes.

The validated candidate is:

```text
working/05e/revisionv1-beb0801712d3a921226201aa437133ae0d3459d510603b54f34a2f6f072fd593/
```

Its identities are:

- activity
  `activityv1-beb0801712d3a921226201aa437133ae0d3459d510603b54f34a2f6f072fd593`;
- managed inventory
  `fileinventoryv1-6cc2c9ef2d2f1b4d216478cbb49bb03a81281e4a9452c7f9cf25cbb0bea3ac30`;
- completion
  `completionv1-3727484678b44b896b82e038deb2bd73ac5d9f910c81a7065877d7a319c005e7`;
  and
- semantic digest
  `5843fe1e6f1dcee608d0575668841cc7e173975e083ea5a20cff8c9bc9212a05`.

The completion is `complete_with_warnings`. Its four warnings preserve the one
malformed General Response membership target, the reviewed `Response OSEC-21`
source-label typo, the source-authored `SA-CHSRA-29` orphan, and the reviewed
unpaired `SA-Caltrans-48` source form. These are terminal graph outcomes, not
open review cases.

The candidate has seven managed payloads and exactly preserves the reviewed
1,538-edge graph, 320 diagnostics, 1,011 derived review views, complete
759-mention accounting, and complete 101-membership accounting. A second
source-free invocation validated and reused the same candidate, completion,
inventory, semantic digest, and file closure. Seventeen focused tests and all
1,373 repository tests pass with formatting, linting, strict typing, and
`git diff --check`. No source PDF was accessed. No acceptance pointer, cleanup,
commit, push, Task 05F work, or later work was performed.

This first terminal candidate is retained as pre-quality-gate evidence. It was
not accepted after the deeper review identified implementation-quality repairs.

### Post-candidate code-quality gate and accepted outcome

The required human code-quality gate reviewed readability, editability,
debuggability, operations, and testing across the complete changed code surface.
It found and repaired four material implementation concerns before acceptance:

- the mention resolver exceeded the explicit complexity threshold and was split
  into named normalization helpers;
- whitespace collapse composed with terminal-period stripping without an
  independently named and validated provenance rule;
- the review page retained stale Gate 1 terminology and could display a stale
  asynchronous case response after a newer selection; and
- candidate publication and acceptance needed stronger staged validation and a
  dedicated adjacent-pointer transition.

After repair, explicit Ruff C90 analysis, formatting, linting, strict mypy, 21
focused relationship tests, and all 1,377 repository tests passed. The complete
file-checksummed quality report records no remaining material findings.

The required source-free replay produced the same 1,538-edge topology, census,
terminal outcomes, and zero-case review set under the fresh activity
`activityv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1`.
Its semantic digest is
`3a6f5b0f4f116b2800e0a8b02bb98fde9d37a48ccc0baff321fd484f2489e71b`.
Two invocations were byte-repeatable and accessed no source PDF.

The accepted terminal candidate is:

```text
working/05e/revisionv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1/
```

Its completion is
`completionv1-867b3e6f9d9cc1e2666cb184523590c2fd02154347ea9787144e61bb43851555`
with status `complete_with_warnings`, and its managed inventory is
`fileinventoryv1-924533bd3c59160bd0853aa38dc095965b07b2d4bf2d78a5ad9431cd2836f667`.
The same four terminal warnings remain; no matching outcome changed.

The user's acceptance was recorded in the adjacent pointer
`acceptancev1-4b8a13393c57660fdb0a6b303912150ca9d1380688a86a6728267a4c79aacac5`
at `2026-09-09T20:21:46Z`. Repeating the transition returned the same pointer,
and the candidate closure remained unchanged. Task 05E is complete and
accepted. Task 05F was not activated; cleanup, commit, and push remain outside
this outcome.
