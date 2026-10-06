# Task08D investigation policy v1

Status: authorized by Kyle on 2026-09-30; qualified; health-risk claim review exported for investigation.
Policy identifier: `task08d.investigation.v1`.

## Contract and short implementation plan

The user explicitly authorized 08E investigation with unresolved question scope
and supporting claims that support other supporting claims. This replaces the
one-hop and fully-resolved-scope gate only for explicitly opted-in exports.
Claim approval still establishes the reviewed response assertion and relevance,
not evidence support, truth, eligibility, or an obligation to produce a rebuttal.

1. Add an explicit, versioned export policy with a user-authorization receipt
   bound to the exact project and native saved export. Preserve the old default
   behavior and all prior snapshots, forms, annotations and exports.
2. Validate support chains as an acyclic graph: each approved supporting claim
   has one approved direct/supporting target and a material contribution rationale.
   Each chain must reach an approved usable direct claim bound to a frozen question
   part. Reject cycles, dangling targets, invalid ancestors and rejected/unresolved
   targets; bind immediate targets and the full chain to exact content/versions.
3. Permit Ready with explicitly Unresolved question gaps for 08E investigation
   only. Carry exact question parts and uncertainty forward. Missing decisions,
   unresolved claims/relationships, invalid source bindings and whole-case holds
   still block. Final eligibility and answer adequacy remain undecided.
4. Qualify source-free saved-native fixtures, independently review graph/export
   fidelity, then export the already-saved health-risk decisions to a fresh
   namespace. Update current records without altering historical artifacts.

## Existing batch impact

Project49 keeps `task08d.claim_review.v2` and its original instructions as a
historical UI snapshot. Kyle's subsequent explicit policy authorization supersedes
its one-direct-target wording and Ready/scope interpretation for this batch.
The receipt records this interpretation; no labels, source anchors, frozen
questions, claim wording or saved relationships are rewritten. No new review
project or re-labeling is required to record the exact already-approved chain.
Future interfaces must display the revised policy before new reviews begin;
this export policy is not an unannounced change to the shared v2 form.

## Learning and boundary

Response completeness and readiness to investigate evidence are different
judgments. Explicit gaps can be investigation inputs without being resolved or
silently dropping part of a question. A support chain represents layered
reasoning; requiring every edge to materially contribute and reach a direct
claim avoids topic-only chains. Acyclic reachability can be checked with standard
Python traversal without a graph dependency. Semantic strength remains human
reviewed. Evidence search may support, limit, contradict or fail to establish an
assertion. Neither this gate nor 08E authorizes a predetermined refutation.

## Qualification outcome

89 targeted tests passed. Independent implementation and saved-export fidelity
reviews passed. Synthetic project54 exercised actual service save/reload/export
for a two-edge support chain with unresolved scope. Existing browser qualification
remains applicable to the unchanged v2 controls. Full `make check`: format, lint
and types passed; 3,033 tests passed, one skipped, the same three historical
Task06G commit-pin failures. Health-risk exports 20 claims for investigation only;
all 31 saved approvals and eight unresolved question parts remain preserved.
