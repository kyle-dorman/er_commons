# Shared Task 08A v2 interface

Version: `task08a.ranking.v2`. This shared revision permits independent 08A
preparation across remaining accepted groups ahead of human review. Each group
has its own immutable publication. No later stage is authorized by preparation.

## Source contract and compatibility

The unchanged `task08a.ranking.v1` input schema and source-supplement schema remain
the exact source-packet contracts. V2 records `input_version` explicitly. The
v2 proposal, handoff, manifest and validation interfaces are versioned v2.
`group_ranking_v2` reuses the maintained `refresh_cases` source resolver and v1
byte-binding helpers. Its local preparation/replay preserves v1 input fields
and validations, with one qualified closure correction: accepted view
`general_response_membership` provenance may supplement the full directed
response closure only when its target is the current comment. Membership-source general
responses are additional accepted roots; their complete directed closure is
required along with direct-response closure. Such edges must be present in the accepted view; they cannot introduce
another comment or excuse a missing directed edge. Every source page touched by
a mapped source unit is retained once as a separately anchored, exact full-page
supplement so omitted footnotes remain available. Nearby text does not expand
group membership or mapped response identity. Include supplements by source
page, not only by their anchor unit ID: a shared page is anchored to the first
unit using it. Ranking agents must receive all packet supplements. V1 source, schema, prompt and
published artifacts remain unchanged and validate through `group_ranking`.

V2 handoffs require later 08B version dispatch to `group_ranking_v2.validate`
and a selection display that does not require rationale fields. This is a
recorded compatibility boundary, not execution or qualification of 08B. All
candidates still require human selection and eligibility decisions. Neither
small-group preparation nor model order automatically selects a candidate.

## Ordering and publication

For one to three candidates, `small_group_proposal` deterministically sorts exact
comment IDs using Python lexicographic string order. It invokes no model and
records `preparation_mode: deterministic`, `model: null`, empty tie groups and
`ranking_not_needed_reason: ranking not needed—group has at most three candidates`.

Larger groups require `preparation_mode: model_ranked`, actual model identity
`gpt-6-astra`, a null bypass reason, and a complete consecutive advisory order.
The proposal contains only comment ID and rank per candidate. Strict schemas
reject generated reasons, explanatory anchors, narrative warnings, rewritten
questions and eligibility labels. Inherited source flags and limitations stay
in the original input packet. Residual ties must be contiguous and ordered by
stable comment ID. Proposal versions above one require a reranking reason and a
new directory; completed output is never overwritten or automatically reranked.
The saved output records an order, not a guarantee of repeatable model inference.

`prepare`, `prepare-small-order`, `publish`, and `validate` are exposed through
`python -m er_commons.group_ranking_v2`. Publication replays source bindings and
validates proposal coverage before creating a fresh directory. It writes exclusive
files, snapshots exact schemas, prompt, specification, source resolver and both
adapter versions, then validates complete file closure before writing completion
last. Validation repeats exact source replay, checks all snapshot bytes and hashes,
and reconstructs ranked records without changing candidates or flags. Interrupted
incomplete directories are evidence, not completed handoffs; use a new explicit
attempt directory rather than clobber them.

## Qualification and learning

Focused negative controls cover small-group model refusal, stable ordering,
large-group model identity, omission and duplicate rejection, forbidden rationale
fields, stale input/prompt bindings, residual ties, inherited membership closure,
no-clobber publication, tampering and completion-last behavior. Current source
replay and bounded independent review remain required before batch completion.

Primary references: [JSON Schema 2020-12 validation](https://json-schema.org/draft/2020-12/json-schema-validation)
supports explicit strict record interfaces; Python's
[exclusive file creation](https://docs.python.org/3/library/functions.html#open)
supports fail-on-existing publication. Existing JSON Schema and standard-library
facilities are sufficient; no new dependency or workflow engine is needed.
