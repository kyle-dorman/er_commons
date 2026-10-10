# Task 09D — Implement automatic retrieval and citation metrics

Status: **closed with limitations; implementation and quality pass accepted.**
The October 10 start request authorized the refreshed plan; no inference was run.

## Abstract

Implement deterministic reference-set matching with auditable denominators and
edge cases. Keep retrieval discovery and final citation selection separate from
semantic judgments. The [Task 09 umbrella](09_build_evaluation_and_qualify_judges.md)
owns sequence and [the sprint](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#automatic-citation-metrics)
owns exact formulas; this task implements, rather than redesigns, those rules.

## Goal

Produce reproducible per-case and aggregate metrics from saved answer citations,
frozen reference roles and actual retrieval receipts when available, using Inspect
for evaluation execution and reporting and canonical unit IDs for matching.

## Inputs

- [08H release](../../docs/specs/task08h_final_result.json), case/split membership,
  canonical citation units and approved support/context pools.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  accepted [09A](09a_create_synthetic_challenges.md) answers and
  [09C](09c_build_judge_evidence_packets.md) resolution diagnostics and restricted
  raw-ID mappings. Read their outcomes/result pointers: 09A `eee4edc`, 09B
  `c2dba5f`, and 09C including its code-quality pass `756f6d3`.
- [09B](09b_choose_harness_and_qualify_local_judge.md) Inspect integration and
  [09C result](../../docs/specs/task09c_final_result.json). Reuse their interfaces;
  prototype semantic rubrics are not automatic metric implementations.
- [Architecture](../../docs/architecture.md), [artifact rules](../../docs/data_artifacts.md)
  and invented retrieval receipts for fixtures. Production retrieval starts in
  Task 10; synthetic answers do not establish which passages a target received.

## Outputs

- Pure typed metric functions called by thin Inspect scorers, with Inspect metric
  aggregation that implements the project formulas and availability rules.
- A small package-backed entrypoint invoking Inspect on saved-answer samples;
  Inspect evaluation logs/results and compact reconstructable metric records.
  Do not introduce a parallel custom evaluation runner.
- Versioned per-case records with canonical sets, invalid tokens, raw hits,
  denominators, neutral-context counts, validity/N/A status and separate metrics.
- Macro/micro summaries with explicit eligible counts and complete-case recall;
  inspectable fixtures and a compact explanation of reference-match limitations.

## Research / learning checkpoint

Read the sprint formula/edge-case contract and the released role projections.
Inspect existing canonical citation resolution rather than inventing text matching.
[ALCE](https://arxiv.org/abs/2305.14627), linked by Decision 006, motivates separating
answer and citation quality; it does not define this project's support/context
formulas. Consult [Inspect scorers](https://inspect.aisi.org.uk/scorers.html) and
its custom-scorer/metric guidance against the installed version. Built-in
text-overlap F1 is not this project's canonical citation-set F1. Explain why
correct alternate evidence may lose matching credit and why
correct citation IDs do not establish a sound argument.

## Plan / spec requirement

Write a compact test table and metric-record specification before implementation.

### Inspect ownership

Inspect owns evaluation execution, sample results, logs and reported aggregates.
Ordinary project functions own source preparation, ID resolution and deterministic
calculations. Implement separate automatic scorer outputs for retrieval and final
citations, preserving the four-result benchmark boundary. Custom aggregation must
retain raw counts and eligible denominators: micro F1 is derived from pooled
precision/recall, not a mean of per-case F1. Missing inputs/N/A must not silently
become zero through framework defaults. Keep reference roles and automatic results
out of model-visible inputs and both judge payloads.

Exercise the complete Inspect path with saved fixtures and a solver that loads
saved answers; do not invoke a target or judge model. Reuse the 09B saved-answer
integration pattern without applying its prototype rubric or local model checks.
No new serving stack or semantic token-counter integration is needed for 09D.

### Canonical ID matching and BM25 handoff

Match stable, unique canonical section/table identities, never heading text,
section names, title similarity or fuzzy text matches. Reuse existing extraction
identities with their frozen source/extraction namespace; do not invent a second
canonical numbering system. If unit IDs are only locally unique, use the explicit
source/extraction/unit tuple. Different units with the same heading must remain
distinct; a display-label change must not change a match.

Task 10 BM25 records must retain these identities. A separate search-record or
fragment ID requires an explicit deterministic mapping to the canonical unit.
Retrieved evidence, saved answer citation tokens and reviewed reference evidence
must resolve into the same namespace before set arithmetic. Treat 09C's neutral
`S1`/`P1` labels as packet-local display IDs, not global matching keys; use its
restricted mappings and verified source locators to recover actual identity.
Collapse aliases only through existing verified mappings. Unknown or ambiguous
IDs remain explicit diagnostics; never repair them by matching a section name.
Missing mapping/source infrastructure remains distinct from an invalid citation.

Specify a compact retrieval receipt with condition/budget, rank, delivered status,
search-record ID if present, canonical source/unit identity and delivered anchors.
Task 10 supplies the actual mapping and completeness evidence. Do not infer delivery
from the search index or a deeper ranked hit; do not grant whole-section credit
merely because a fragment carries its parent's ID. No BM25 implementation occurs
here. This interface is a requirement for the later Task 10 contract refresh.

### Calculations and edge cases

Use per-case sets of canonical section/table units:

- `S`: reviewed support. `C`: reviewed context-only, disjoint from `S`; any
  reviewed support use wins over context use for that unit.
- `R`: distinct units actually returned within the recorded condition/budget.
- `A`: distinct resolvable units explicitly cited by the final answer's links.
- `U`: distinct invalid/unresolvable attempts as stable raw identifier tokens.

Implement these formulas without substituting one set for another:

- Retrieval recall: `|R ∩ S| / |S|`.
- Final-citation recall: `|A ∩ S| / |S|`.
- Final-citation precision: `|A ∩ S| / (|A \ C| + |U|)`.
- Final-citation F1: `2 * precision * recall / (precision + recall)`.

Known context is neutral; unmatched valid citations and invalid attempts remain
in precision's denominator. Deduplicate valid and invalid repeated IDs while
retaining original point links for audit. With nonempty `S` and an empty scored
final set, including context-only output, all three final-citation metrics are
zero. Empty `S` makes required-reference metrics N/A and excludes the case from
applicable aggregates; report it separately. F1 is zero when precision and recall
are both zero. Compute micro scores from summed applicable raw counts, then micro
F1 from micro precision/recall; compute macro means over eligible case scores.

Do not fabricate `R` for synthetic variants or report absent receipts as zero
retrieval performance. Mark retrieval unavailable for such records. Distinguish
unavailable inputs from measured empty retrieval. Fixture receipts must be labeled
invented and cannot be published as target-run evidence. Preserve malformed-answer
diagnostics and raw citation attempts; never silently drop invalid rows to inflate
aggregates. Resolve any extraction ambiguity explicitly before freezing that rule.

Specify the receipt interface now; Task 10 owns the final fragment-to-canonical
anchor projection. A fragment inheriting a section ID cannot earn full-unit credit
without the required anchors actually being present. Exercise this with fixtures
and leave production projection qualification to Task 10/12.

For eventual retrieval receipts, retain the top-five primary condition, diagnostic
recall at 1/3/5/10/20, and complete-case recall. A deeper ranked hit is not a passage
delivered to the model. Record budget-achievable recall ceilings where `|S|` exceeds
the unit budget, without changing the reference denominator. Multi-query unions
apply only to separately approved conditions, not the baseline.

### Execution boundaries

Preserve the frozen 19-development/30-test split and 09A's 423 development
variants, 118 reserved final checks and five exclusions. Use deterministic invented
fixtures first; any bounded real-data check may load only explicitly selected
eligible development records through the existing verified routing. Never inspect
reserved answer payloads or test questions/references, infer retrieval receipts
from synthetic answers, or run a broad challenge. Keep implementation readable
and maintainable beyond the initial MVP without adding production orchestration,
a new framework or elaborate provenance. No model calls or downloads are needed.

## Validation

Use hand-calculated fixtures for perfect/empty/partial results, context-only sets,
support/context overlap, repeated IDs, invalid attempts, unmatched valid sources,
empty `S`, missing versus empty retrieval, citation/retrieval divergence, abstention,
and macro/micro differences. Confirm extra repeated citations cannot improve scores
and reversed answer text with unchanged links leaves automatic metrics unchanged.
Add ID fixtures for identical headings on distinct units, changed labels on the
same ID, cross-document local-ID collisions, verified aliases, packet-local ID
collisions, unknown/ambiguous mappings and fragments missing required anchors.
Require an offline Inspect integration test that exercises actual scorer and
aggregation execution, checks saved logs against hand-calculated results, and
proves missing retrieval remains unavailable while measured empty retrieval is
zero. Use multiple cases that distinguish micro from macro; model calls must be
zero. Direct function tests alone do not complete this task.

Run `make fix`, `make check` and `git diff --check`. The 09C baseline is 3,535
passed, one skipped and three documented historical Task 06G failures; distinguish
these unchanged failures from regressions.

## Acceptance criteria

- Formula and edge-case fixtures match the sprint contract exactly.
- Every summary can be reconstructed from per-case counts and eligibility states.
- Retrieval availability and actual receipt provenance remain explicit.
- Automatic outputs stay outside both judge packets and remain separate results.
- Canonical IDs determine matches; display labels and packet-local IDs cannot
  create false matches. The Task 10 receipt/mapping/completeness contract is explicit.
- Inspect is the maintained evaluation path, with an offline end-to-end fixture
  proving scorer outputs, logs, aggregation and unavailable/N/A handling.

## Review pass

Use a bounded independent arithmetic/edge-case review and check maintainability of
pure functions, thin Inspect adapters and source identity reuse. Independently
review ID collisions/fragment completeness and Inspect denominator handling.

## Non-goals

No BM25 implementation, target inference, judge scoring, blended benchmark score,
new support labels, alternative-evidence promotion or held-out test evaluation.

## Outcome

Implemented the refreshed plan with Inspect owning execution, sample results,
logs and aggregate reporting. The [metric/receipt specification](../../docs/specs/task09d_automatic_metrics_v1.md)
records the test table, exact input/record interfaces and Task 10 requirements.
The [result pointer](../../docs/specs/task09d_final_result.json) binds external
qualification and validation evidence. No real challenge records were evaluated.

### Implementation and maintained use

- `automatic_metric_inputs.py` resolves verified occurrence locators into existing
  source/extraction/kind/unit tuples, preserving raw attempts and distinguishing
  invalid IDs from unavailable infrastructure. Support roles take precedence over
  context. Packet-local labels require a scoped mapping; they never become global
  IDs. Receipt resolution requires explicit search-record maps and complete anchor
  delivery. Missing ranking evidence leaves diagnostic cutoffs unavailable.
- `automatic_metrics.py` contains ordinary typed functions for the exact set
  formulas and macro/micro aggregation. Versioned Pydantic records retain canonical
  sets, raw counts, eligibility, links, receipts and null scores. Micro F1 comes
  from pooled precision and recall, not an average of case F1 values.
- `automatic_metric_inspect.py` loads saved answers with an offline solver and
  exposes independent citation and retrieval scorers. Custom Inspect metrics call
  the pure aggregator. Undefined aggregate numbers are omitted by Inspect while
  null per-sample values and explicit eligibility counts stay in the log. No
  separate evaluator, new dependency, server or model call was introduced.

Maintained entrypoint (use an external log directory):

```bash
make evaluate-automatic-metrics \
  METRIC_SAMPLES=tests/fixtures/automatic_metrics/saved_samples.json \
  METRIC_LOG_DIR="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/09d_example/inspect"
```

The command consumes an explicit prepared sample array. For future real data,
callers must prepare verified development projections through existing release
routing; the CLI does not discover partitions or certify self-declared source
provenance. No general corpus loader is claimed. Restricted reference metadata
and automatic results stay out of both judge payloads.

### Qualification and review

The external namespace is `task_09/09d_20261010_v1/`. Four invented saved cases
exercise actual Inspect scorers, aggregation and persisted `.eval` logs. Citation
macro precision/recall/F1 are 7/9; pooled micro values are 2/3. Retrieval macro recall
is 1/2 and micro recall is 2/5, with two eligible, one unavailable and one N/A
case. An explicit empty receipt scores zero while an absent receipt stays null.
The integration test blocks `Model.generate` and verifies empty model usage.
An initial CLI wiring failure is preserved beside the successful log; neither
made a model call. Only the successful log is the qualification result.

Independent arithmetic, identity and Inspect review accepted the implementation
after fixes for unobserved diagnostic ranking depths, missing mapped source
infrastructure, malformed unextractable citation rows, and mixed unknown reference
roles. A declared packet-local answer without its map is explicitly unavailable.
The code remains three small modules with pure functions, dataclasses and thin
Inspect adapters, without production orchestration.

- Focused tests: **45 passed**, including three actual offline Inspect tests.
- `make fix`: passed; formatting, lint and strict type checks passed.
- `make check`: **3,580 passed, one skipped, three historical Task 06G failures**.
  These are the same two v38 immutability checks and source-free template check,
  each encountering the historical repository-base-commit mismatch. Their tests
  and implementation files remain unchanged from `756f6d3`. No regressions.
- `git diff --check`: passed. Independent final review accepted all fixes.
- Final saved Inspect log: four invented cases, zero model usage; schemas,
  source/implementation hashes and exact validation logs are bound by the result.

### Learning, limitations and next task

[Inspect custom scorers](https://inspect.aisi.org.uk/scorers.html) separate
sample scoring from aggregation, but default numeric averaging cannot preserve
this project's eligibility and micro denominators. Explicit raw counts and custom
metrics keep those choices reviewable. The installed Inspect 0.3.278 behavior was
verified against actual saved logs. [ALCE](https://arxiv.org/abs/2305.14627)
motivates separating citation and answer quality; the sprint formulas remain the
authority. Alternate valid evidence can lose reference credit, and matching IDs
do not establish sound reasoning or answer adequacy.

Task 10 must supply and qualify real search-record/fragment-to-canonical mappings,
complete canonical anchor inventories and actual delivery receipts. A parent ID
alone earns no full-section credit. Ranked depth/exhaustion and candidate anchors
are separate from delivered anchors; deeper ranked diagnostics cannot inflate
primary top-five recall. Task 12 must check the eventual production chain.
Invented receipts do not establish baseline retrieval performance, and no real
fragment projection was qualified here.

The frozen 19-development/30-test split and 423 development variants, 118 reserved
final checks and five exclusions remain unchanged. No reserved payloads, test
questions/references or real answer payloads were opened; no inference, downloads,
broad challenge, later-task implementation, commit or push occurred. 09E is next
for a separately authorized contract refresh; 09E–09G and Task 10 remain unstarted.

## Authorized code-quality pass

The user requested a bounded pass above MVP quality without production-system
scope. Review identity/receipt validation, readable ownership, saved-sample
identity and Inspect aggregation failure modes. Fix demonstrated issues with
focused regressions; preserve the accepted formulas and existing successful
fixture results. Keep Inspect as execution/logging owner and avoid new orchestration,
dependencies or a general release loader. Preserve previous external evidence;
write new validation to a separate quality-pass namespace. No model calls, source
payload access, later-task work, commits or pushes. Validate with independent
review, focused tests, `make fix`, `make check` and `git diff --check`.

### Code-quality outcome

The pass retains the three-module design and the exact metric formulas. Alias
resolution now uses the original occurrence inventory, making results independent
of alias-map insertion order; conflicting occurrence shadowing and alias chains
are rejected. Receipt validation is split into small named helpers for metadata,
canonical inventories, ranked rows and observed depth. Malformed shapes and
unknown mapping targets fail explicitly; rank validation precedes sorting, and
checking declared depth allocates only in proportion to actual hits. Incomplete
unit diagnostics have stable ordering.

Prepared saved samples now support an explicit `sample_id`, allowing distinct
variants of one benchmark case to run together without changing `case_id` or
merging observations. Existing one-answer-per-case inputs retain their IDs.
Strict envelope types and concise CLI input errors make mistakes easier to locate
before Inspect starts. The maintained `*_cases` aggregate counters describe
selected answer observations, not unique underlying benchmark cases; callers must
choose consistent populations. This clarification does not change weighting or
any existing formula.

Metric records now validate strict nonnegative counts, finite bounded scores,
eligibility/null coherence, denominator bounds and exact paired cutoff fields.
The calculator still owns arithmetic; validation does not duplicate the evaluator
or claim to detect arbitrary tampering. No caching layer, new dependency,
transaction protocol, general source loader or additional runner was added.

Independent final review accepted the changes. A new offline Inspect run under
`task_09/09d_20261010_code_quality_v1/` reproduced all four original per-sample
metric records and aggregate values exactly, with zero model usage. The original
qualification namespace and result bindings remain preserved. Regression tests
cover alias order/collisions, malformed receipts, stable diagnostics, strict
metric invariants, multiple variants sharing a case ID and expected CLI errors.

Quality-pass validation: **103 focused tests passed**, including **58 added
regressions**. `make fix` passed, and formatting, lint and strict types passed.
`make check` reports **3,638 passed, one skipped and the same three historical
Task 06G failures**, with no regressions. Historical Task 06G tests and
implementation remain unchanged from `756f6d3`. `git diff --check` passed.

Task 09D remains complete with its existing production-retrieval qualification
limits. No source, reserved or test payloads were accessed; no model calls,
downloads, later-task work, commits or pushes occurred. The
[result pointer](../../docs/specs/task09d_final_result.json) preserves the original
execution evidence and separately binds this quality pass.

## Closeout acceptance

The user accepted Task 09D and its code-quality pass and authorized a local
commit of the implementation, tests and documentation. Earlier no-commit
statements describe execution before this closeout authorization. Task 09D is
closed with the documented Task 10/12 retrieval-qualification limits. Task 09E
remains provisional and unstarted; explaining its scope does not activate it.
No push is authorized.
