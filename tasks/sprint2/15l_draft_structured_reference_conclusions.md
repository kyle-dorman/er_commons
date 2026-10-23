# Task15L — Batch structured reference-conclusion drafts

Status: batch and all49 individual human adjudications complete (2026-10-22).
Task15M owns validation/publication and downstream conclusion retesting.

## Goal and authorization

The user accepts the C001 judge pilot as good enough for this stage and authorizes
all49 reference conclusions to be drafted in the required/optional format, then
reviewed one at a time. Preserve existing labels, supporting points, original
results and all prior discussion. These are proposals, not a published release.

Use question/evidence/labels only, never predicted answers, judge decisions or
performance-selected cases. Reuse the exact evidence-only projections sealed in
Task15F and verify their hashes. C001 carries forward its discussed pilot text as
the format baseline, with citations restored from original support/evidence. No
other draft is implicitly approved. No provider calls, synthetic generation,
reserved challenges, MiniMax, commits or pushes.

## Authoring and review

Write all49 in fixed case order, with R1.. required and O1.. optional points.
Keep logically complete groups; separate optional detail from necessary answer
meaning. Why/how questions retain the necessary finding/mechanism and outcome
connection. Preserve material scopes, conditions and uncertainty. Optional numerical
details state modeled values; qualifications clearly state their limitation.
Citations use original S occurrence IDs inline, with source links below. Supporting
points remain separate provenance, not an automatic checklist for conclusions.

Every point has source anchors, a necessity/optionality rationale and source IDs.
Each case records changes, materiality notes, unresolved questions, evidence
limitations and a focused human-review question. An evidence-limited question must
remain flagged, not receive an invented sufficient answer. Respect the distinction
between evidence support and answer necessity in the accepted C policy.

Use three bounded fresh-context author batches, plus C001 integration. Independently
cross-review every proposal against evidence and the policy. Preserve initial
versions and review findings when repairing clear mistakes. Preserve substantive
materiality disagreements for human adjudication. Automated checks verify coverage,
IDs, exact quotes, input immutability and independent review hashes; human/agent
reasoning review checks meaning. Reuse existing JSON/Markdown/HTML conventions.

## Deliverables and validation

Fresh external structured_reference_review_20261022_v1 contains fixed inputs,
49 proposals and case-readable Markdown, independent reviews, review browser,
summary, methods/exposure note and pitfalls appendix. Seal the immutable batch;
keep the human queue/decision journal in a separate mutable sibling directory.
Publish a small tracked result pointer and current routing. Preserve source links,
fixed case order, one-at-a-time review and explicit pending status.

Validate all49 cases, sequential R/O IDs, nonempty required list, citation inventory,
verbatim source anchors, source/published-label hashes, full independent coverage,
HTML escaping and all49 browser entries. Run git diff --check for docs-only changes.
No runtime package changes or unrelated tests are needed.

## Limitations and downstream work

This is prediction-excluded curation, not a blind audit: the lead has prior model
exposure and general issues were motivated by earlier experiments. It includes
all30 originally designated test references; disclose their additional curation
exposure. Accepting the judge pilot does not imply perfect point-level judging.
Task16 retains these limitations. After individual approval, publish versioned
labels, regenerate synthetics, retest judges, align generation prompts and rerun
applicable downstream stages. None of those later actions occurs in this task.

## Outcome

The [result pointer](../../docs/specs/task15l_structured_reference_review_result.json)
selects a sealed49-case review batch, one-case-at-a-time browser, readable case
files, methods note, pitfalls appendix and separate mutable queue/journal.
There are97 required and83 optional points with323 exact source anchors. All49
proposals received an independent hash-bound review; 12 retain materiality/scope
questions. Six have explicit source/necessity uncertainty notes (overlapping that
set). No human approval or label publication is inferred.

C001's discussed point text is unchanged. Five drafts were repaired or clarified
with prior versions preserved: C011 restores a source-discrepancy qualification;
C012 makes a three-trait necessity question explicitly unresolved; C022 preserves
the construction-and-progress conjunction; C027 moves incidental location names
out of required wording; C035 separates hydrology and water-independence details.
Legacy citation IDs are preserved with an explicit presentation-only S mapping.

Validation passed exact49 coverage, sequential R/O IDs, citation membership,
all323 source-anchor matches, original input/published-case hashes, independent
review coverage/current hashes and unchanged prior review seal. All49 browser
views/navigation executed in a DOM check; a Chrome screenshot was visually
inspected. The completion seals227 files. git diff --check passed. No runtime
code changed, predictions opened, judge/provider runs made, reserved challenges
opened, labels changed, commits or pushes. Next: individual review in the new
queue; downstream regeneration follows approved versioned labels.
