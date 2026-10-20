# Task 12 reporting contract v1

Frozen for the accepted Task 11E development evidence before any locked results.
The Task 12 result pointer binds the exact implementation, runtime, inputs and
output seal. This specification governs aggregation; it does not authorize runs.

## Population and identities

Luna (`gpt-6-luna`) and Haiku (`claude-haiku-5-5`), each with three planned
repeats of 19 questions: 57 answers/model, 114 total. Preserve original-six and
additional-thirteen exposure groups from the frozen 11E configuration. Both are
development; the additional thirteen have prior judge-development exposure.
Never pool development with test. A later test adapter must supply its explicit
planned 30-question × two-model × three-repeat roster, including missing slots.

Each answer retains model, run, case, repeat, attempt, request hash, candidate
hash and candidate ID. Each G observation also retains point ID, sample ID,
group, citation IDs and payload hash. Source verification follows the tracked
11E pointer to its completion inventory, then verifies every consumed file.
Reconstruct plans from exact candidate bytes, delivery, mapping and reference;
reconstruct judgments from saved raw outputs; require equality to sealed plans
and reports. Duplicate, orphan, altered, cross-answer and cross-repeat joins
are integrity errors, never silently dropped observations.

## Outcomes and automatic checks

| Result | Pass definition |
| --- | --- |
| A | `substantive` routing for this answerable-case benchmark |
| G | Every required support/qualification point passes; substantive answers require a nonempty support basis |
| S | Frozen `support_sufficient=true`, from all original support/qualifications |
| C | Frozen `conclusion_adequate=true`, from its independent frozen projection |
| Automatic | Valid schema, exact payload delivery, resolved citation IDs, and no uncited points anywhere in the complete answer |
| Joint | All applicable automatic/A/G/S/C results pass on the identical answer |

Automatic validity preserves the accepted 11E scope: conclusion and optional
context citations count too, although neither is a required G point. Reference
citation recall/F1 is diagnostic and has no new threshold in joint success.
G missing/unresolved owned citations fail mechanically before any semantic call;
these failures remain distinct from semantic false and evaluator errors.

A classifies conclusion prose, not the candidate's status flag. Clean abstention
also requires empty support, qualifications and optional prose. It fails A and
joint for these answerable cases, while G/S/C are N/A; no semantic judgments are
invented. The uncited-conclusion check is exempted only for guarded clean
abstention. Mixed abstention and ambiguous routing remain unresolved, with known
automatic/G failures retained. Missing/invalid judgments and evaluator errors are
unavailable, never ordinary false labels. Invalid answer schema is an automatic
failure; an undispatched A remains unavailable, not a measured routing failure. Missing source files or seal mismatch fail publication, not scoring.

Conjunction is failure-dominant: a known failure plus unknowns remains failed;
otherwise unknown required results remain unavailable. This outcome resolution
does **not** establish complete evaluation. Tables separately count complete
component evaluations and complete-evaluation triples. Empty G sets never grant
substantive success. Historical 0/1/2 grounding scores are not converted.

## Denominators and repeats

Every model/component table reports planned, applicable, observed pass/fail,
unavailable and N/A counts. Planned pass fraction is passes/all planned slots;
observed pass fraction is passes/(pass+fail). `outcome_coverage` is resolved
pass/fail over applicable slots; `complete_evaluations` counts receipt-complete
evaluations separately. Point tables use point units and name their answer
count; points are not independent answer samples. Missing required points retain
unavailable rows; absent candidate rosters have a separate unknown-roster count. Repeat `0` means pooled
observations; `1`, `2`, `3` are actual repeats.

Question rows retain each of the three outcomes. A complete applicable triple
has no unknown or N/A outcome: count 0/1/2/3 passes, at least once (>=1/3) and
every time (3/3). Unknown triples retain observed pass counts and enter an
unresolved bucket, with nullable complete-triple success. N/A-only and mixed
applicability triples have separate buckets and no 0-pass interpretation.
Unique-question planned and complete-triple denominators are exported. Known
failure can resolve an outcome while its evaluation is still incomplete.
These are observed repeat summaries, not independent-sample estimates or a
deployment output selector. Never combine passing components across repeats.

## Citation and delivery metrics

Use [09D](task09d_automatic_metrics_v1.md) canonical matching and eligibility:
support wins over neutral context; repeated canonical units and invalid tokens
are deduplicated; context does not penalize precision. Empty scored citations
with nonempty support measure zero; empty support is N/A; missing infrastructure
is unavailable. Eligible-only macro means average answer observations. Micro
precision pools hits/precision-denominator; micro recall pools hits/support;
micro F1 is recomputed from those pooled ratios. No eligible observations means
null. Answers retain the original automatic counts, attempts and diagnostics.

Verified delivery coverage is the fraction of supplied canonical units in an
exact verified full payload (1.0 for these 114 receipts), with numerator and
denominator exported. It is an input audit, not proof of attention or discovery.
Retrieval recall, read-evidence recall and ranked diagnostics stay schema-visible
but N/A/null in this evidence-only condition. No historical five-unit search
budget applies; no retrieval precision/F1 is invented.

## Complexity associations

Count distinct resolved canonical tuples `(source, extraction, kind, unit_id)`
across conclusion, support, qualifications and optional context. Distinct
documents use source IDs. Sections use stable canonical section IDs; where any
table lacks a stable parent-section mapping, the answer's section count is
unavailable. Never use headings as section identity. Invalid IDs are separate.
Supplied-evidence counts are distinct input covariates with the same rules.

Freeze bins at `0`, `1–2`, `3–5`, `6–10`, `11+`, plus unavailable. Keep Luna
primary. Export every component's bin pass/observed/planned counts, unique
questions, repeat counts and range of within-bin question pass fractions.
Charts show joint fractions and that range; it is spread, not a confidence
interval. Answer rows preserve grouping and permit exact reconstruction.
No fitted trends, causal claims or difficulty interpretation: output counts
are model behavior. Sparse and unavailable bins remain visible.

## Historical judge agreement

Use only the 09G-selected historical development summaries/records:
A v2 (three-class), G v3, S v6, C v8. A classes are clean abstention,
substantive answer and ambiguous conclusion. Publish per-class precision,
recall, F1, one-vs-rest TP/FP/FN/TN, full confusion and macro-F1.
G positive means supported by owned evidence; S means sufficient support;
C means adequate conclusion. Publish binary positive-class precision/recall/F1
and confusion counts. Undefined denominators produce null, not perfect scores.

Valid-only accuracy is correct/valid; failure-inclusive accuracy is
correct/planned; coverage is valid/planned. Invalid output is outside ordinary
negative labels. Preserve exact available calibration partitions, selected
versions, evaluation units, panel/run identities and label provenance. A/G
full observations are not reconstructed from summary counts; A flagged/unflagged
confusion metrics are unavailable. S/C retained records preserve sample,
case and repeat identities. Model-proposed/agent-reviewed labels are **not human
gold**. Historical agreement is neither target-model success nor fresh held-out
validation. Different evaluation populations and correlated errors forbid
multiplying component accuracies into joint accuracy.

## Maintained implementation and replay

`reporting_inputs` verifies and replays the accepted development source.
`reporting` owns pure reductions and denominators; `reporting_judges` owns
historical agreement. `reporting_charts` renders static PNG/SVG from exported
tables. `reporting_run` publishes JSON/CSV, provenance and a completion seal
under the external Task 12 root. Identical replay verifies output bytes; changes
require a fresh namespace. Sealed upstream artifacts are never rewritten.

```bash
UV_OFFLINE=1 make report-development REPORT_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_12/reporting_20261020_v1"
```

The root is configured by `.env`; pass an absolute output path when the invoking
shell has not exported the variable. No provider/counting mode exists here.
CSV nested cells are JSON; blank nullable scalars mean unavailable, not zero.
JSON is the lossless format. Manifest/completion inventory includes source hashes,
frozen configuration, reporting implementation and package versions.

## Research, choices and readiness

The task's offline boundary takes precedence over its web-reading checkpoint.
Consulted the installed Inspect 0.3.278 scoring/metric interfaces and existing
09D/11C interfaces, preserving saved generation, scoring and aggregation as
separate stages. The upstream references are [Inspect scorers](https://inspect.aisi.org.uk/scorers.html)
and [custom metrics](https://inspect.aisi.org.uk/metrics.html); no web fetch or
API call was made. Independent judge inputs reduce information leakage but do
not imply independent errors on shared questions, models or labels.

Matplotlib is the maintained static plotting dependency, installed from the
local package cache with networking disabled and locked in `uv.lock`. Its
installed `Figure.savefig`/Axes interfaces supply PNG and SVG, avoiding a bespoke
renderer or dashboard. Standard-library JSON/CSV handle small tables; existing
pure evaluator and metric models retain policy ownership.

Reporting readiness means the definitions, offline replay and provenance are
validated. It does not mean model quality is perfect or execution authorized.
Task 13 must be separately activated, bind its locked-only input adapter and
180 planned slots, then use these unchanged reducers/definitions and primary
plots. A new adapter needs equivalent seal, identity and routing checks; it
must not reuse this development-only loader or inspect test content early.
Tasks 13–15 remain provisional. Existing 11E manual reviews and calibration
records remain evidence; Task 14 owns selective follow-up, not a new full review.
