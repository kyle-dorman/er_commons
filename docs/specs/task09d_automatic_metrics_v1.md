# Automatic metrics v1

Task 09D implements the sprint formulas. Inspect owns execution, sample results,
logs and aggregation. The ordinary Python calculation functions have no framework,
model, filesystem or network dependency.

## Record and aggregation contract

`task09d.metric_record.v1` records case ID; canonical support/context/cited/returned
sets; distinct invalid tokens; original point-link attempts; diagnostics; receipt;
and separate citation/retrieval counts, eligibility and scores. Canonical keys
reuse `(source_id, extraction_id, kind, unit_id)` from existing source locators.
Support wins over context. Display headings and packet-local S1/P1 labels are not
identity. Exact verified aliases may collapse; unknown/ambiguous attempts remain
invalid. Missing source/mapping infrastructure makes affected scores unavailable.

Each metric family has `eligible`, `not_applicable` (empty support), or
`unavailable` status. Scores are JSON null outside eligibility. Counts remain
visible for audit but only eligible records contribute to macro/micro totals.
Citation counts include hits, support denominator, precision denominator and
neutral-context count. Retrieval includes hits, support denominator, complete-case
indicator, budget ceiling and ranked recall diagnostics at 1/3/5/10/20. Missing
receipts are unavailable; an explicit empty receipt is a measured zero.

Macro means use eligible cases. Micro recall pools hits/support; citation micro
precision pools hits/(non-context valid citations + invalid tokens); micro F1
uses those two pooled scores. Empty scored citation sets have zero precision,
recall and F1 for nonempty support. With no eligible cases aggregates are null,
not zero. Inspect omits undefined aggregate numeric values and retains explicit
population counts and null per-sample values in its log.

## Test table written before implementation

| Fixture | Expected behavior |
| --- | --- |
| Perfect / empty / partial support | Exact hand-calculated recall, precision, F1 |
| Context-only / overlapping support-context | Context neutral; support wins |
| Repeated IDs / aliases / repeated invalid tokens | Deduplicate sets, preserve point links |
| Unmatched valid / unknown / ambiguous | Precision penalties; explicit diagnostics |
| Empty support / missing sources | N/A / unavailable, excluded with counts |
| Missing / explicitly empty receipt | Unavailable / measured zero |
| Retrieval versus citation divergence | Independent sets and scores |
| Abstention / reversed prose with same links | Automatic metrics depend on actual links |
| Same headings / different sources / changed labels | Only canonical tuple matches |
| Packet-local S1 collision | Scoped mapping only; no global equivalence |
| Fragment missing anchors / deeper ranked hit | No primary full-unit delivery credit |
| Unequal support sizes | Macro differs from micro; pooled F1 is recomputed |
| Offline saved-answer Inspect task | Actual scorers, metrics and logs; zero model calls |

## Task 10 receipt boundary

A receipt must record schema, condition, unit budget, provenance (invented fixtures
explicitly labeled), ranked hits, delivered status, optional search-record ID,
canonical tuple and delivered anchor IDs. Required anchors come from a verified
complete canonical source inventory, not from a fragment's claimed parent ID.
Search-record IDs require an explicit exact mapping to canonical units. Missing
mapping infrastructure is unavailable, not measured failure. Contradictory receipt
structure fails validation. Only actual delivered evidence within the recorded
budget earns primary recall. Deeper ranked results are explicitly diagnostics.
The primary baseline has a five-unit budget; multi-query conditions require
separate approval. Reference denominators never shrink to the budget; report the
upper bound `min(budget, |S|) / |S|` separately.

Task 10 must qualify fragment/anchor projection and completeness against the
frozen extraction, including tables and continuations. Task 12 must verify actual
delivery receipts end to end. 09D fixtures do not certify production projection,
implement BM25, or invent retrieval histories for synthetic answers.

## Sources and interpretation

The [sprint formulas](../sprints/sprint2_brisbane_draft_eir_defense.md#automatic-citation-metrics)
are authoritative. [Inspect scorers](https://inspect.aisi.org.uk/scorers.html)
and [custom metrics](https://inspect.aisi.org.uk/metrics.html) motivate thin scorers
and explicit aggregation; installed Inspect 0.3.278 is the compatibility target.
[ALCE](https://arxiv.org/abs/2305.14627) motivates separating answer and citation
quality, not substituting its formulas. Correct alternate evidence can lose
reference-match credit; correct citation IDs cannot establish sound reasoning.

## Exact prepared-input interface

`SavedMetricSample` is a strict envelope: `case_id`, `scope` (`invented_fixture`
or `development`), `saved_answer`, `sources`, optional `verified_aliases`,
`packet_mapping`, `packet_local` and `retrieval_receipt`. `sources` uses existing
09A/09C verified source projections: `occurrence_id`, `source_id`, `extraction_id`,
`canonical_target.unit_type` (or `kind`) and `canonical_target.unit_id`.
`approved_roles` retains released `required`/`required_support` and
`optional_context` roles. Other roles fail closed. An empty role list is a valid
unreviewed alternative source. This adapter does not authorize source claims;
callers must verify source seals and development membership through existing
release routing before constructing inputs. No general release loader is added.

Raw answer citation links resolve occurrence IDs using that catalog. Neutralized
09C answers require their own raw-to-local `packet_mapping`; `packet_local=true`
without a map is unavailable. The map is never shared across packets. Explicit
verified occurrence aliases are accepted; inferred heading/text aliases are not.
Unknown links are invalid tokens; known mapped sources with missing locators are
unavailable. Scalar/non-string citation fields retain invalid raw tokens.
Unextractable malformed answer/point containers (including missing citation lists)
retain raw audit attempts and make citation scores unavailable, rather than dropping
uncertain links and inflating precision. Valid abstention remains measured from
its actual citation links. Answer prose has no effect on reference matching.

The receipt schema is `task09d.retrieval_receipt.v1`:

| Field | Meaning |
| --- | --- |
| `condition`, `unit_budget`, `provenance`, `invented` | Explicit condition, positive budget, provenance and fixture flag |
| `required_anchor_ids` | Rows of `canonical_unit` and nonempty complete `anchor_ids` |
| `search_record_mapping` | Exact rows of `search_record_id` and `canonical_unit` |
| `hits` | Ordered-by-rank evidence with unique positive `rank`, `canonical_unit`, optional `search_record_id`, boolean `delivered`, `delivered_anchor_ids`, and candidate `anchor_ids` |
| `ranked_depth`, `ranking_exhausted` | Optional diagnostic coverage declaration; both are required for ranked diagnostics |

The declared ranked depth must describe a contiguous recorded prefix and every
hit must have explicit candidate anchors. Cutoffs beyond observed depth are null
unless ranking is explicitly exhausted. Missing candidate-anchor evidence makes
ranked diagnostics unavailable while actual delivery can remain measured.
Candidate `anchor_ids` are not proof of delivery: only `delivered_anchor_ids` on
hits actually delivered within budget enter primary recall. Anchor unions may
complete a unit, but credit begins only at the rank at which all required anchors
are present. Unknown/contradictory maps or anchor inventories make the receipt
unavailable with diagnostics. The saved receipt remains in the metric record.

`retrieval.hits_at` retains nullable raw counts per cutoff. Aggregation reports
cutoff-specific eligible cases, hits and support denominators, as well as macro
and micro diagnostic recall. These populations can differ from primary delivery
eligibility. N/A and unavailable scores are JSON null; Inspect's aggregate results
omit undefined numeric fields while retaining explicit counts. Complete-case
recall is the fraction of eligible retrieval cases with all support delivered.

## Quality-pass clarifications

Saved inputs may supply a nonblank `sample_id` for a variant or control. Inspect
uses that ID and retains the original benchmark `case_id` in the metric record.
When omitted, the existing one-answer-per-case interface uses `case_id` as the
sample ID. Duplicate effective sample IDs are rejected. Aggregates describe the
explicitly selected answer observations: the existing `*_cases` counters count
scored observations, not distinct benchmark cases or a mean across case-level
variant averages. Callers select a consistent population before comparing runs.
The sample ID is retained in Inspect's sample envelope and scoring-input metadata.

Prepared envelope fields use strict types and nonblank identities; malformed answer
content remains available to citation diagnostics. Persisted metric measurements
validate nonnegative integer counts, bounded finite scores, eligibility/null
consistency, denominator bounds and paired cutoff availability before aggregation.
These checks validate structure and invariants; the pure calculator remains the
single owner of arithmetic. No duplicate evaluator or tamper-proof log protocol
is introduced.

Verified aliases target the original occurrence inventory, not other aliases.
An alias cannot incompatibly shadow a canonical occurrence token. Alias-map order
must never change resolution. Receipt condition and provenance are nonblank
strings; every search mapping names a known canonical unit, including unused
mapping entries. Validation and diagnostic order are deterministic.
