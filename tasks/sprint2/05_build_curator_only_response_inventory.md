# Task 05: Build the Curator-Only Response Inventory

## Abstract

Build a complete, separately identified inventory of the comment and response
units in Final EIR Volume 4. Preserve the source structure and provenance
needed to review whether each response defends existing Draft EIR evidence,
acknowledges a concern, redirects it, or produces a Final EIR revision.

This is a curator-only artifact. Final EIR Volume 4 is not part of the Task 03
model corpus and must not be added to the accepted Draft EIR extraction
release. The exploratory `classify_volume4.py` script and its heuristic labels
are not production inputs; rebuild this task from the authoritative source and
the contract below.

## Goal

Create a restartable, auditable inventory for every identifiable comment,
individual response, general response, and relationship in Volume 4, including
cross-references and source page anchors. Make linked-response cases reviewable
without losing the original response text or the source of incorporated text.

## Inputs

- Frozen source release record for the Brisbane Baylands project.
- Final EIR Volume 4, `Responses to Comments on the DEIR (Chapters 11 through
  13)`, source ID `feir_volume_4`.
- The existing Sprint 2 plan and the Task 03 target/alias index, used only to
  resolve Draft EIR references after Task 04 usability is available.

The current local source is the 744-page PDF at:

```text
datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_deir_sources_v1/
  sources/curator_only_response_source/feir_volume_4.pdf
```

Appendix Q, `DEIR Comments and Public Meeting Transcript`, is a separate Final
EIR appendix. Volume 4 contains organized comment excerpts and responses and
often provides enough context for issue/response extraction, but it does not
replace Appendix Q when exact full-letter context, attachments, or complete
oral testimony is required.

## Outputs

Publish an immutable, checksum-inventoried inventory under the Task 05
curator-only namespace. At minimum, preserve:

- stable comment, response, and general-response IDs;
- commenter, organization/agency, or meeting identity;
- commenter class and source-letter membership;
- Volume 4 PDF start page and text anchors;
- original comment and direct-response text;
- explicit Draft EIR, Final EIR, appendix, chapter, section, table, figure,
  page, and mitigation-measure references;
- direct response-to-response links;
- direct response-to-general-response links;
- one-to-many and many-to-one relationships;
- orphan and unresolved-link diagnostics; and
- source, extraction, schema, and artifact checksums.

For every linked case, also publish a derived review view containing:

```text
comment -> direct response -> linked response(s) and/or general response(s)
```

The derived view must retain each incorporated unit's ID and source anchor. A
linked response can support a classification but must not be silently merged
into the original response.

## Provisional response-outcome policy

Use four compact outcome classes for exploratory and later curator review:

1. **Defense**: the response answers the concern using existing Draft/Final EIR
   analysis, a cited section, appendix, table, figure, or existing mitigation
   measure, with no substantive new Final EIR change.
2. **Acknowledge**: the response recognizes, records, introduces, or declines
   to substantively answer the concern without defending it with existing
   evidence.
3. **Outside scope/deferred**: the response genuinely redirects the issue to a
   separate process, later approval, permitting action, future project, or
   other decision boundary.
4. **Revision**: the response produces or identifies a substantive Final EIR
   change, including revised text, analysis, table, figure, mitigation, or a
   new/revised appendix.

Clarification and mitigation/action are not separate final classes. A
clarification is `Defense` only when it supplies an existing-document answer.
An existing mitigation measure supports `Defense`; a new or changed measure is
`Revision`; a later permitting action is `Outside scope/deferred`.

## Required linked-response review

Run this as two stages:

1. **Deterministic resolution:** detect and resolve explicit references such as
   `Refer to Response SA-CDFW-10`, `As stated in Response M-CSSC-39`, and
   `Refer to General Response 5`. Preserve unresolved references rather than
   dropping them. Extract the full General Response 1 through General Response
   9 units before classifying dependent individual responses.
2. **Human semantic disposition:** review the original comment together with
   the direct response and resolved linked text. Confirm whether the linked
   material answers this specific comment. A cross-reference alone never proves
   `Defense`.

Use a temporary review flag for mixed, partial, or unclear cases. In
particular, a response such as `O-GA-8`, which says only `Refer to General
Response 5`, should not be accepted as a defense merely because General
Response 5 discusses enforceability. Its comment alleges that mitigation could
make the project infeasible; the linked response discusses implementation and
enforcement but does not directly analyze project feasibility.

## Known source findings to preserve

- Volume 4 is separate from Appendix Q and is part of the Final EIR response
  package.
- Its contents identify General Response 1 through General Response 9 and say
  that individual responses may refer to general or other responses.
- The current exploratory parse found approximately 1,017 identifiable
  comment/response units. This count is diagnostic only until the structural
  inventory and relationship validation are complete.
- The City’s Final EIR package identifies Appendix F3 as new and identifies a
  revised greenhouse-gas package as H1/H2. These are Final EIR package changes,
  not evidence that the original Draft EIR corpus was incomplete.
- Existing exploratory outcome counts are not acceptance evidence. They changed
  substantially when cross-referenced general responses were resolved, which
  demonstrates that linked context must be part of review.

## Research / learning checkpoint

Before implementation, inspect the existing Task 03 inventory and response
section structure, then document the best-practice choice of a normalized
relationship graph plus a provenance-preserving materialized review view.
Explain plainly why this is preferable to flattening linked responses: the
same general response can answer many comments differently, and reviewers must
see both the incorporated text and where it came from.

## Validation

- Verify every identifiable comment, direct response, and General Response 1–9
  has a stable record or an explicit diagnostic.
- Verify every relationship resolves to an existing record or is retained as an
  unresolved link with a reason.
- Verify source PDF page anchors and text checksums against the frozen input.
- Verify one-to-many and many-to-one relationships without synthetic one-to-one
  duplication.
- Verify linked review views retain original IDs, text, pages, and relationship
  type.
- Verify repeated construction produces byte-identical inventory and review
  artifacts.
- Inspect a varied manual sample, including direct answers, general-response
  links, response-to-response links, Planning Commission comments, and apparent
  orphans.

## Acceptance criteria

- Complete inventory and relationship graph are published atomically under the
  Task 05 namespace.
- No source unit is silently dropped because it lacks a detected response or
  reference target.
- General responses are separately identified and resolvable.
- Every linked case has an independently reviewable combined view.
- The four outcome labels, if produced, are marked provisional until human
  disposition; deterministic cues do not accept or reject a case.
- The artifact identity binds the exact Volume 4 source, extraction contract,
  schema, configuration, and implementation inputs.

## Non-goals

- Adding Volume 4 or Appendix Q to the Task 03 model corpus.
- Replacing Appendix Q with Volume 4 for exact comment-letter or transcript
  provenance.
- Automatically accepting a defense because a response cites another response
  or General Response.
- Manually comparing every possible pair for duplicate clustering; Task 07 owns
  reviewed clustering for benchmark cases.
- Benchmark retrieval, response generation, model evaluation, or final human
  evaluation.
