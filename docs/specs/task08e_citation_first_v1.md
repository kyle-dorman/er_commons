# Task08E citation-first review v1

Status: qualified and published; labeling reported complete, export validation pending for
M-OSEC-241 and O-Joint-44. This is a presentation and review-unit
revision over existing exact source packets. No new discovery or model run.

## Successor plan

Kyle reports v1 labeling complete on 2026-10-01; export verification and separate
eligibility are pending. The accepted [shared-source v2 plan](task08e_shared_source_review_v2.md)
will pool source passages across cases and batches, propose editable relationships
and permit scoped batch acceptance. It is not yet implemented. This v1 record and
its saved human decisions remain preserved.

## Plan

1. Preserve old project configurations, task data, saved annotations and drafts.
2. Transpose the existing citation-to-claim proposals into one task per citation
   within each case: 20 citations / 6 claims for M-OSEC-241 and 23 citations /
   14 claims for O-Joint-44. Keep exact approved claims, sources and support chains.
3. Implement a shared, versioned form and export adapter. Qualify actual saved
   choices, edits, optional additional links, blank relationships and exports in
   an independent fixture project. Review source identity and layout independently.
4. Create a fresh live project and inspect its actual source and claim sections.
5. Delete old 08E projects and projects titled `SYNTHETIC QA ONLY`, as explicitly
   requested, after preserving their complete review records. Preserve all other
   projects. Record exact deleted IDs and update current routing and the register.

## Review contract

One task contains one exact citation and its proposed associated approved claims.
For each displayed claim, the reviewer may choose Supports, Partially supports,
Context only, Does not support, or Contradicts. An unchosen relationship remains
unreviewed, never a negative judgment. Optional notes explain a qualification or
conflict. Other approved claims in the same case are accessible through a
collapsed "Link another claim" section; choosing a relationship creates an
explicit human link without revising the approved claim or source.

There is **no claim-wide outcome control, aggregate support judgment, or second
claim-by-claim evidence review**. Save the explicit citation–claim relationships
and unresolved/partial states. Collective support and answer wording are handled
in the later authorized drafting chat. Separate human eligibility remains a gate
before 08F; this revision neither starts drafting nor resolves the eight upstream
question parts. Export validation checks identity and completeness mechanically;
it does not decide evidential adequacy or eligibility.

The initial queue has 43 citation tasks and 113 proposed citation–claim links.
Citations are deduplicated within each case. Case-specific review identities remain
separate even where the same canonical source occurs in both cases. A new project
starts without inferred labels. Existing explicit pair choices and pair notes may
be carried into unsubmitted drafts after exact source/claim-version matching;
record every mapping and original annotation ID. Legacy `no_support` maps to
`not_support` without changing its meaning. Never migrate old aggregate outcomes,
fill blank relationships or mark a new citation task completed. Full prior
annotations and drafts remain archived.

## Exact task-page content

Visible, in this order:

1. Compact case and citation identifier.
2. **Summary**: the existing concise source summary.
3. **Why retrieved**: the existing retrieval reason.
4. **Source**: readable title and pages, PDF link, a horizontal divider, complete
   parsed passage or table family including its captions and notes, then another
   divider. Use comfortable paragraph spacing and full available width.
5. Substantive source limitations when they affect interpretation (for example,
   a different scenario, receptor, period, edition, contradictory value, missing
   continuation or unavailable figure). These remain distinct from source text.
6. **Claims**: exact approved wording for each proposed claim, five relationship
   choices and an optional short note. Separate claims with generous spacing and
   horizontal rules. Additional approved claims are collapsed below this list.

Excluded from the page:

- "Astra proposal; verify against the source below."
- Generic extraction/review history such as "fresh Task 06H review was a bounded
  sample" and unchanged accepted-strata boilerplate.
- Raw hashes, JSON anchors, pipeline filenames, model provenance and test history.
- Repeated full comments, responses, frozen questions and support-chain diagrams.
- Overall claim outcomes, overall reviewer essays, automatic support scores or
  another claim-focused review queue.

Exclusion from the page is not deletion from evidence. Complete warnings, raw
anchors, discovery receipts, question scope, support chains and provenance stay
in the bound source packets and exports. Only specifically identified process
boilerplate is hidden; substantive limitations are not discarded. Original source
text is never rewritten to make the page shorter.

## Binding, qualification and learning

Interface version: `task08e.citation_review.v1`. Exact task data, form, project,
reviewer, candidate, claim version and external packet checksums bind each saved
relationship. Reuse maintained source rendering, canonical validation and compact
packet transport. Prior form versions remain replayable from archived exports.
A citation-first record is not a legacy aggregate claim record and must not be
passed to that normalizer by inventing claim outcomes.

The maintained [Label Studio Choices documentation](https://labelstud.io/tags/choices)
specifies independent named controls bound to an object and optional choices;
[View documentation](https://labelstud.io/tags/view) supports grouping and spacing.
Keep semantic identity independent of visual placement. Real queue/save/edit/
reload/export checks are required because a syntactically valid form does not
prove the saved relationships bind the intended source and claim.

Validate proposed and manually added links, untouched relationships, contradiction,
partial support, changed task/form/packet identities, table content and old-project
backup closure. Run focused checks and `make fix` / `make check`. Carry forward
exactly the three historical Task06G commit-pin failures in the validation record.

## Published result

The [current record](task08e_health_risk_investigation_result.json) binds project
105, its exact form and 43 tasks. Twenty-five prior explicit relationships are
preserved in ten unsubmitted drafts. Separate project 104 proved save/edit/reload,
optional added links, draft restoration and native export; live read-only checks
verified paragraph and continued-table layout, unchanged tasks and draft choices.
Eleven independent invalid-export probes were rejected. The 22 old 08E and
`SYNTHETIC QA ONLY` projects were deleted after complete checksummed backups;
all other project IDs were preserved. Current records and cleanup receipts live
under `health_risk/08e/citation_first_v1/` in the external artifact root.

Full validation passed 3,124 tests with one skip and the same three historical
Task06G commit-pin failures; final focused and static checks passed after the
visual refinements. Human eligibility remains undecided, and no 08F work started.
