# Task 08E — Review one group's evidence and eligibility

Status: **Provisional contract; execution has not started.** Revise from the first
accepted 08D batch before activation. This reusable task runs separately for each
group; finishing one batch does not close the stage for all groups.

## Abstract

Discover and review Draft EIR evidence for the approved claims in one group's
cases, then conduct the second human eligibility review. Reuse a shared,
versioned review interface while preserving exact sources, bounded search gaps,
and human decisions. Valid citations alone do not establish a valid rebuttal.

## Goal

Produce a source-grounded, human-reviewed evidence handoff for each surviving
case, or an explicit stop with its reason and preserved partial work.

## Inputs

- [Task 08 umbrella](08_curate_grouped_benchmark.md) and the named group's
  accepted [08D claims handoff](08d_review_group_claims.md).
- [Human review process](../../docs/response_comment_human_review_process.md),
  [sprint eligibility and evidence boundaries](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md),
  [artifact contract](../../docs/data_artifacts.md), and
  [architecture](../../docs/architecture.md) before changing maintained helpers.
- Exact original comments, frozen questions, complete linked responses, reviewed
  direct/supporting claims, first-pass eligibility records, accepted extraction,
  source-usability registry, and response-inventory identities.
- [07D search protocol](../../docs/specs/task07d_search_protocol_v1.md),
  [claim search prompt](../../docs/prompts/task07d_claim_citation_search_v1.md),
  [export contract](../../docs/specs/evidence_review_v1.md), and
  [maintainer guide](../../docs/task07d_maintainer_guide.md), as reusable precedent.

## Outputs

- A versioned, per-group evidence-search packet with query receipts, candidate
  dispositions, exact canonical anchors, warnings, and bounded search gaps.
- A separate Label Studio project using the shared 08E template; validated
  decisions exported against the exact proposal and template versions.
- Reviewed evidence records and case-level support/context citation lists,
  including source summaries, discovery provenance, and rejected candidates.
- Second-pass human eligibility records and an immutable batch handoff for 08F,
  with stopped/unresolved cases accounted for and no automatic replacements.

Generated records remain under `ER_COMMONS_DATA_ROOT`; only maintained templates,
small schemas, prompts, fixtures, and helpers belong in Git. The umbrella owns
batch identity, manifests, model provenance, and no-clobber requirements.

## Research / learning checkpoint

Before first-stage setup, inspect the maintained 07D boundaries and official
[Label Studio labeling configuration](https://labelstud.io/guide/setup),
[task import](https://labelstud.io/guide/tasks), and
[annotation export](https://labelstud.io/guide/export) guidance. Explain how
stable source IDs, reviewed relationships, and a real save/export test prevent
plausible-looking but unusable review data. Record verified sources and the
chosen adapter boundary; do not rebuild the evidence workflow without cause.

## Plan / spec requirement

Write a brief setup spec before implementation, then use the accepted setup for
ordinary batches. The spec defines the shared versioned 08E template, schemas,
search budget and expansion/stopping rules, evidence aggregation, and export
validation. Review it before generating live proposals.

1. Start a separate 08E chat for one named group. Load only its approved packet
   and required stage instructions; do not inherit the main planning chat or
   unrelated groups' labels. Six reentering pilot cases use fresh Task 08 inputs
   and decisions; sealed Task 07 labels are not defaults.
2. Resolve explicit response references and run bounded curator search over
   usable sources for each approved claim. Seek core/questioned passages,
   supporting material, counterevidence, and limiting conditions. Preserve
   explicit-reference, lexical, and any permitted graph-search provenance.
3. Use Astra (`gpt-6-astra`) for proposals. Restrict selected evidence IDs to
   supplied canonical candidates; preserve subject, units, dates, and exact
   scope. Allow `insufficient_evidence`. Do not introduce a source-count cap
   that hides relevant counterevidence or confuse search gaps with absence.
4. Show full citable units and focused summaries with source anchors. Human
   review decides each claim-source relationship and its support/context role.
   Deduplicate case citations by canonical section/table identity, retaining
   support over context across reviewed uses without losing relationship history.
5. Conduct the second human eligibility pass using original comment, complete
   response, evidence, usability information, and relevant cross-references.
   Where practical, do not emphasize first-pass rationale before the decision.
   Exclude cases materially dependent on later revisions, new Final-EIR analysis,
   external evidence, mitigation changes, unusable text, or unavailable visuals.
   Required tables must have a canonical structured/text representation and
   human usability verification against the corresponding render, including
   each required family member. The health-risk group does not itself authorize
   CSV tools or calculations absent from the original question.
6. Validate and save decisions before advancing. Changes to approved question
   or claims return to the owning stage as explicit revisions and invalidate
   affected downstream approvals. Do not silently repair scope in evidence review.

Create/adapt the shared template once, prove real queue/save/export behavior,
and then create each group's project from it using data only. Any interface or
schema change is a named shared revision with an explicit decision about earlier
batches; batch chats must not write bespoke template code.

## Review pass

Use bounded independent reviews for source/anchor closure, support/context
semantics, and maintainability of any adapted helpers. Integrate findings before
human review begins. Human semantic and eligibility decisions remain human-only.

## Validation

- Verify upstream identity closure, selected case/claim membership, exact question
  versions, complete response closure, and canonical evidence ID resolution.
- Exercise the actual Label Studio queue and export with a representative record;
  check saved roles, edits, nonempty approvals, and version bindings.
- Check excluded/unresolved claims do not advance, all source gaps are reported,
  and both eligibility passes exist for every accepted evidence handoff.
- Run focused tests and `make fix` / `make check` for implementation changes;
  inspect the diff and run `git diff --check` for docs-only updates.

## Acceptance criteria

- Every input case has a saved advance, stop, or unresolved disposition.
- All advancing cases have explicit human evidence and second-pass eligibility
  decisions; exact sources and approval versions resolve mechanically.
- No context-only evidence substitutes for required support; counterevidence and
  limits remain visible in the handoff.
- The accepted batch can restart or feed 08F without relying on chat memory.

## Non-goals

Answer drafting, whole-pool clustering, target retrieval or benchmark runs,
automated eligibility, reopening sealed pilot results, or filling lost selections.

## Outcome

Not started. On execution, record setup qualification once and link per-group
completion manifests, counts, exclusions, learning, checks, and the 08F handoff.
