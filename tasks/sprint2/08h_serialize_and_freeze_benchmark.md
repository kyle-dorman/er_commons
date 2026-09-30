# Task 08H — Serialize, select, and freeze the benchmark

Status: **Provisional contract; execution has not started.** Activate after the
complete authoring pool and 08G graph are accepted. Final size and split
allocation require an explicit user decision before freeze.

## Abstract

Assemble validated Task 08 authoring records and confirmed case clusters into a
reproducible benchmark release. Present the accepted pool, attrition, and feasible
cluster-preserving allocations for human review, then serialize and freeze the
agreed result without exposing curator-only reference material to target models.

## Goal

Publish a restartable, provenance-backed benchmark and split handoff. Twenty-five
cases is a flexible target, not a minimum or exact gate; a larger or smaller
release is possible by explicit agreement after reviewing the actual pool.

## Inputs

- [Task 08 umbrella](08_curate_grouped_benchmark.md), every group stage handoff,
  and the accepted [08G clustering graph](08g_review_case_clusters.md).
- [Sprint benchmark boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md),
  [artifact contract](../../docs/data_artifacts.md),
  [architecture](../../docs/architecture.md), and current source/inventory seals.
- All selection, skip, stopping-point, question, claim, evidence, eligibility,
  answer, and clustering decisions; approved versions; warnings and exclusions.

## Outputs

- A validated complete accepted-case pool, separate from final release selection.
- An attrition waterfall derived from authoritative stage decisions, with raw
  counts, denominators, stops/exclusions by reason, and untouched/unseen counts.
- A reviewable selection/split proposal, user-approved final size/allocation,
  confirmed cluster assignments, and cross-split leakage audit.
- A checksummed, completion-last release with cases, reference records, split
  manifest, source/version/license provenance, schemas/configuration identities,
  human decision provenance, and a compact downstream handoff.

## Research / learning checkpoint

Inspect official [JSON Schema guidance](https://json-schema.org/understanding-json-schema/reference)
and [scikit-learn grouped splitting guidance](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).
Explain why schema validity does not prove semantic approval, why the full
accepted pool remains distinct from split selection, and why whole clusters may
constrain feasible sizes. Inspect existing project publication helpers before
adding custom machinery; record the selected narrow approach and sources.

## Plan / spec requirement

Write a brief release spec before implementation. Define schemas, role-separated
views, exact upstream identity closure, counting rules, deterministic allocation
objective/tie-break/seed, and restartable publication behavior. Do not make a
proposal's initial size into an accepted policy without human agreement.

1. Verify every group has a terminal batch record, including empty groups and
   cases stopped downstream. Assemble only approved current versions. Preserve
   all partial-work and exclusion history separately from accepted cases.
2. Derive the audit waterfall from source inventory, prepared pool and group
   assignments, reviewed selections/skips/unseen candidates, first-pass
   eligibility, question approval, claims, evidence and second-pass eligibility,
   approved answers, accepted pool, and final selection. Report explicitly
   deferred unresolved cases separately from exclusions. Do not count unseen
   candidates as rejections or purposive browsing as an unbiased acceptance rate.
3. Validate exact one-comment/one-question identity and both human eligibility
   passes, approved answers, source usability, evidence and cluster closure.
   Reentering pilot cases must have fresh Task 08 review records; their historical
   Task 07 labels remain preserved and cannot substitute for current approvals.
4. Show the pool size, cluster sizes, coverage, and feasible allocations. Use 25
   as a target; 10 development / 15 test is a historical starting proposal only.
   Obtain the user's explicit final size and development/test allocation before
   locking anything, including agreement on what happens to extra accepted cases.
   Ordinary attrition is allowed; do not automatically reopen groups or backfill.
5. Produce a deterministic selection/split proposal for the agreed constraints,
   with objective, tie-breaks and any seed recorded. Prefer broader issue,
   source-document, and commenter coverage among valid allocations. Never split
   a confirmed cluster. If the agreed allocation is infeasible, present a new
   decision instead of silently changing sizes or weakening cluster rules.
6. Audit that no confirmed relationship/duplicate edge crosses development/test.
   Include duplicate-fixture results, every overlap warning and disposition,
   unresolved blockers, and selection reasons for retained/unselected cases.
7. Obtain human approval of the exact proposed case/split version. Serialize
   separate target-visible question/source references and curator-only reference
   claims, evidence, answers, labels, and response records. Targets must not
   receive reference labels, reference evidence IDs, or official response text.
8. Publish under the configured external artifact root using a new identity,
   exact managed-file inventory, hashes, and completion-last semantics. Preserve
   sealed upstreams and prior revisions. Update compact documentation routing and
   the downstream task handoff with precise limits and required next decisions.

Do not wait for a 35-candidate initial pool: the upstream process is rolling
single-group authoring. Do not invent retrieval/model/judge configurations that
belong to later tasks. Record the release configuration and downstream freeze
requirements; those configurations must be frozen before the primary test run.

## Review pass

Use independent bounded reviews for approval/provenance closure, cluster-safe
allocation and leakage, target/reference separation, and maintainable publication
logic. Reconcile findings before presenting the final freeze decision.

## Validation

- Validate schemas, stable IDs, exact upstream bindings, approved current text,
  nonempty records, citation anchors, and case/cluster/split membership closure.
- Recompute waterfall and split counts from records; confirm no silent losses,
  double-counts, inherited approvals, or implicit exclusions.
- Replay allocation on the same inputs and configuration; verify whole-cluster
  assignment and zero confirmed cross-split edges.
- Test that target-visible records exclude curator reference fields and response
  content; validate exact final human approval and release hashes/inventory.
- Use focused tests plus `make fix` / `make check` for implementation changes;
  inspect final docs/diff and run `git diff --check`.

## Acceptance criteria

- The user has approved final size, development/test allocation, and exact release
  selection; no rigid 25-case or 10/15 gate is imposed.
- Every included case passed the current authoring and two human eligibility
  reviews, and every confirmed cluster remains wholly within a split.
- Attrition and accepted-but-unselected cases are auditable, including the six
  reentered pilot cases' current dispositions and preserved historical identity.
- The release verifies and can be consumed without reconstructing chat history;
  target and curator-reference access are clearly separated.
- The completion record states remaining limitations and the next bounded task.

## Non-goals

Running retrieval/generation/judges, choosing later model configurations,
changing source extraction, repairing substantive labels during serialization,
automatic backfilling, or altering historical Task 07 releases.

## Outcome

Not started. Record final pool/release counts, agreed sizes, exact freeze identity,
validation, leakage audit, learning, limits, and downstream handoff on completion.
