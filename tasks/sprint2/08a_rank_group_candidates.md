# Task 08A — Prepare and rank one group's candidates

Status: **All 42 accepted groups have validated 08A handoffs (2026-09-30).
Health-risk v1 is preserved; 41 remaining groups use qualified shared v2.** Parent: [Task 08](08_curate_grouped_benchmark.md).

## Abstract

Prepare a complete, revisitable browsing order for one accepted exclusive group.
For groups with more than three candidates, Astra ranks question and response
quality. Groups with at most three use deterministic comment-ID order. Kyle alone
selects candidates in 08B and judges eligibility later in 08E. Preparation may
cover all remaining accepted groups ahead of human review, with isolated group
artifacts and bounded one-group subagent assignments.

## Goal

Give the reviewer a useful order and faithful source context
without hiding candidates or converting model preferences into eligibility.

## Inputs

- [Decision 005](../../docs/decisions/005_task08_grouped_question_selection.md):
  accepted group assignment, hashes, exceptions, and priority group.
- [Human review process](../../docs/response_comment_human_review_process.md),
  [Sprint 2 eligibility boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#task-08-eligibility-clustering-and-split-boundary),
  and the umbrella's batch/provenance contract.
- Current [response inventory](../../docs/specs/task07a1_final_result.json),
  exact original comments, complete linked response closure, source warnings,
  and one explicitly identified group.
- [Data/artifact rules](../../docs/data_artifacts.md); read
  [architecture](../../docs/architecture.md) before any later implementation.

## Outputs

- A fresh external Task 08 group/stage artifact containing all group candidates,
  their exact source bindings, complete resolved responses, retained flags,
  and saved rank. Do not generate per-candidate ranking rationales, quote-anchor
  explanations, or narrative source warnings and review limitations.
- A manifest binding group/input hashes, prompt version, actual model identity,
  proposal versions, ranking policy, and deterministic tie-break rules.
- A validated handoff to [08B](08b_select_group_candidates.md), with no human
  decisions inferred from rank. No Label Studio project is required here.

## Research / learning checkpoint

Inspect the accepted inventory's closure contract and Decision 005's distinction
between assignment and quality order. Explain why saved model ordering is
revisitable but rerunning a model is not guaranteed to reproduce that order.
Before implementation, inspect existing package-backed preparation helpers and
preserve their source/link validation rather than build a new workflow engine.
Record the narrow reuse decision and limits in the outcome.

## Plan / spec requirement

Write a brief ranking/input specification before first execution. Define once
and version the reusable record schema, ranking prompt, validation, and handoff.
Each later group uses these components and generates data only. A proposed
change requires an explicit shared version revision and an assessment of prior
batches; do not customize the policy privately for one group.

### Authorized remaining-group execution — 2026-09-30

Prepare all remaining groups in the accepted 42-group assignment before human
review as explicitly authorized. Inspect completion records and the batch register
first; validate and preserve completed outputs, including health-risk v1. Never
rerank or overwrite completed outputs automatically. Retain every candidate,
complete source context, inherited flags and exact bindings. Small groups still
require explicit 08B human selection; no candidate is selected or eligible by default.
Track pending, running, completed and blocked groups. A source-integrity failure
blocks its group, not independent groups. Centralize shared-file/register writes,
preserve preceding register bytes and concurrent health-risk 08E updates.

### Accepted simplification for future groups — 2026-09-30

Future 08A proposals save the order without question/response-quality reasons,
explanatory quote anchors, or generated concerns/limitations narratives. Retain
exact original comments, complete linked responses, source IDs, inherited flags,
and input/output version bindings as provenance. Source integrity checks remain;
this change removes explanatory output, not source context or validation.

The [shared v2 specification](../../docs/specs/task08a_ranking_v2.md), prompt,
schema and adapter are qualified for remaining groups. Historical v1 requires
rationale fields and must not be used by filling them with dummy text or
generating reasons only to satisfy validation. Preserve the completed health-risk v1 packet and its
prompt/schema snapshots unchanged; no reranking or migration is required. Its
existing handoff remains usable by 08B. V1 remains a separate historical validation path.

The tradeoff is deliberate: Kyle assesses the original sources directly, so
per-candidate explanatory output is unnecessary. A saved order with exact input
bindings remains revisitable without a narrative ranking record.

1. Verify the accepted grouping identity and select exactly one group. Retain
   all group members and inherited flags; do not silently regroup or refilter.
2. Resolve complete response closure and source text before ranking. Missing or
   unusable sources remain flagged and block unsupported quality assertions.
3. If the group has at most three candidates, skip model ranking entirely, use
   stable comment-ID order and record “ranking not needed—group has at most three
   candidates,” with null ranking model and no invocation. Otherwise have Astra
   (`gpt-6-astra`) read original comments and complete responses.
   Favor clear, independently answerable concerns and substantive rebuttals;
   deprioritize rant-like material, revision-dependent answers, empty referrals,
   and nonanswers. Preserve difficult qualifications and distinguish an awkward
   writing style from a substantive concern. Do not rewrite questions here.
4. Record a total order, breaking residual ties by stable comment
   ID. Retain every candidate; model ranking is advice, not an eligibility label.
   Preserve O-Joint-44's incidental-revision exception and the health-risk
   group's potential-table status; never invent a calculation requirement.
5. Save and validate the order once for this group. Reranking creates a new
   version with a reason; it never overwrites reviewed order or decisions.

The six approved pilot cases reenter from original source material with fresh
Task 08 histories wherever their accepted groups place them. Do not import old
approvals, claims, or answers as new labels. Preserve the sealed pilot, its
limitations, and existing I-CJ-4/I-EA-2 stops.

## Validation

Verify exact group coverage with no omissions/duplicates; source/link closure;
stable IDs, input hashes, rank uniqueness, retained inherited flags; and
manifest-to-output closure. Check the four named priority candidates against
Decision 005. Inspect saved data for invented rewrites or model eligibility
labels. For implementation use targeted meaningful tests and `make fix` /
`make check`; for documentation only, inspect the diff and `git diff --check`.

## Acceptance criteria

- One group's full ordered packet and provenance validate, with no hidden drops.
- A future chat can resume 08B from the handoff without the ranking conversation.
- Ranking is explicitly advisory and no selection or labeling has occurred.
- Completion is recorded for this group only; the reusable stage remains
  available for later groups under the umbrella's batch registry.

## Review pass

Use bounded independent checks for source/closure integrity and ranking-policy
faithfulness. Reconcile concerns before handing the packet to the human reviewer.

## Non-goals

Human selection, eligibility decisions, question rewriting, evidence discovery,
clustering, final split allocation, or starting 08B or later stages.


## Outcome — health-risk group only

Established the [shared v1 contract](../../docs/specs/task08a_ranking_v1.md),
[prompt](../../docs/prompts/task08a_ranking_v1.md), strict schemas and package-backed
prepare/publish/validate adapter. The saved group packet retains all four original
comments, eleven distinct source units, complete directed response closure,
seven reference outcomes and four separately anchored supplemental footnotes.
The initial Label Studio selection template remains 08B work.

The exact external handoff is:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_08/health_risk/08a/ranking_v1/handoff.json
```

Its directory contains original-source input, advisory proposal, ranked records,
shared interface/code snapshots, validation, manifest and completion. The
[compact result](../../docs/specs/task08a_health_risk_result.json) binds its hashes,
independent reviews and batch register. Accepted grouping SHA-256 remains
`fb24092981fdb14d910b5a0485095ff45c5b25cfef5670712ea96809f753d632`;
the accepted inventory remains the 07A.1 replacement. Metadata checks verify
42 exclusive groups, 606 candidates, ceiling 96, six pilot memberships and both
stopped-case exclusions; no other group was ranked or processed.

Actual ranking model: `gpt-6-astra`, proposal version 1, no residual ties.
Proposed browsing order and principal reasons:

1. **M-OSEC-241:** clearest focused combined-source concern; direct quantitative
   rebuttal with receptor, construction-period maximum and cited thresholds.
2. **O-Joint-44:** concrete setback/barrier request with a detailed response
   distinguishing regional emissions and localized health risks; broader scope
   and qualifications than 241.
3. **M-OSEC-243:** actionable mitigation concern and substantive linked context,
   but conditional elevated-risk locations/receptors are less specified.
4. **M-OSEC-244:** substantive future-resident/environmental-justice concern;
   response relies on shared referrals and does not separately develop the
   seniors or broader environmental-justice issues.

These are comparative ranking reasons, not rewritten questions, selections or
eligibility findings. Every candidate remains available. O-Joint-44 retains
`actual_revision` and its accepted RA-Caltrain-9 → RA-Caltrain-8 incidental
60-to-30-minute service exception. No calculations were added. The possible
need for table analysis remains unproven.

### Limits and learning

Reuse of `pilot_context_repair.refresh_cases` preserved source/link logic;
`read_container` checked the accepted compact release rather than re-extracting
source files. Independent graph traversal checked direct and transitive response
membership. Four footnotes (62, 84, 85 and 26) lay outside accepted response
spans; separately verified page slices restore reading context without changing
upstream records. Saved JSON and exact byte seals make this order revisitable,
not a guarantee of identical model reruns. First-use research checked Python
JSON and JSON Schema primary documentation linked in the shared specification.

Preserved caveats include sampled source review, incomplete reference metadata,
filtration/maintenance assumptions, passenger electrification versus remaining
freight, 243/244 overlap, and broader scope than some threshold-based responses.
The sources also contain differing mitigation lists (AQ-1a/b versus
AQ-1c/e/f/h/j/k/l), daily roadway versus hourly CO-screening language, and merged
`6030` revision extraction. These are retained concerns, not silently corrected
claims. Original Draft EIR evidence and numerical calculations have not been
independently established; later human eligibility and evidence review remain
necessary. No PDF visual reassessment or external citation verification occurred.

### Validation and next action

Independent source and implementation reviews passed after strengthening direct
response/edge checks, manifest policy/version checks and reranking-reason checks.
Source-free negative controls cover omitted candidates, duplicate/rank errors,
forbidden rewrite/eligibility fields, incorrect/cross-context quotes, stale
versions, unstable ties, missing closure, supplemental-source mutation,
no-clobber behavior and output tampering. Actual source preparation and saved
output replay passed. Repository validation is recorded in the compact result.

Ready as input to a separate health-risk **08B first-use preparation** chat.
08B must qualify its shared selection interface before human review. It has not
started; no Label Studio project, human selection, eligibility label, question
rewrite, commit or push was created.

## Outcome — remaining accepted groups

Completed the authorized preparation pass: preserved the one valid health-risk
v1 handoff, model-ranked 18 groups (559 candidates) with actual `gpt-6-astra`, and
prepared 23 groups (43 candidates) deterministically with no ranking invocation.
No groups are blocked, pending or running. Together the handoffs retain all 606
candidates in the unchanged 42-group assignment. No selection, eligibility,
question rewriting, clustering, Label Studio project or later-stage work occurred.

The [compact result](../../docs/specs/task08a_remaining_groups_result.json) binds
the full handoff index, qualification and register snapshot. Exact absolute
handoff paths, hashes, model identities and reading receipts are in:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_08/preparation_20260930_v2/handoff_index.json
```

Each new handoff is saved separately under
`task_08/<group-slug>/08a/ranking_v2/handoff.json`. The shared output interfaces
are `task08a.ranking.v2`, `task08a.proposal.v2` and `task08a.handoff.v2`; the
source-packet shape remains `task08a.ranking.v1`. Historical v1 code, schemas,
prompt snapshots and artifacts remain unchanged and validate through their
original adapter. The v2 [specification](../../docs/specs/task08a_ranking_v2.md)
and [prompt](../../docs/prompts/task08a_ranking_v2.md) own future preparation.

The source audit identified a v1 validation limitation in general-response
groups: accepted membership links supply additional response roots. V2 validates
those accepted roots and their complete directed closure, retaining every link.
Exact complete-page supplements preserve footnotes outside unit spans; adjacent
page text is context, never additional candidates. Existing source warnings and
unresolved Appendix Q routing remain inherited metadata, without new ranking
narratives. Exact-text deduplication of already read source bytes reduced repeated
reading while keeping all previously unread page text and group coverage recorded.

Qualification passed 33 focused v1/v2 tests and bounded independent review.
`make fix` passed; `make check` passed format, lint and type checks and reported
3,087 passing tests, one skip and the same three historical Task06G commit-pin
failures. No new failures were found. Final source replay, source-reading receipts,
complete population coverage and saved output closure passed for all handoffs.
The external progress ledger records all 41 as completed; central register updates
saved preceding bytes and preserved all existing health-risk stage rows, including
concurrent 08E. Shared files were edited centrally; no commit or push was made.

Learning: strict schemas distinguish deterministic preparation from model advice
without inventing rationale placeholders. Saved model order is revisitable, but
model reruns are not guaranteed to repeat it. Narrow v2 separation protects the
historical validator's exact code seals while correcting the next interface.
The [shared specification](../../docs/specs/task08a_ranking_v2.md) records the
primary JSON Schema and Python exclusive-file-creation references.

Next: wait for a separate 08B request. Its existing adapter expects v1 rationale
fields, so qualify explicit v2 intake and page-based supplemental-context display
before creating review queues. This compatibility work must preserve all human
selection and later eligibility gates; no further decision is needed for 08A.
