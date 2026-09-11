# Figure-caption alias policy v1

Status: **implemented, qualified, and accepted in Task 06F remediation attempt
v10; production replay remains gated to Task 06G**.

This specification owns the source-general `figure_caption_alias_v1` policy.
It publishes exact structural figure targets from canonical attachment evidence;
it does not establish what an image depicts or whether a text-only model can use
the figure as substantive evidence.

## Authority and scope

The builder enumerates every canonical figure in the selected, sealed document.
Task 05 mentions, nearby prose, navigation text, list-of-figures tables, page
furniture, and image interpretation are never alias sources. Selection of a
document is configuration; no source ID, mentioned-label list, or target
allowlist is part of the rule.

For each figure, the canonical `image_ids` and `caption_block_ids` relationships
are the sole attachment authority. IDs are joined exactly against the selected
canonical image, block, and page streams. Records are never paired by geometry,
proximity, text similarity, or page coincidence alone.

## Exact eligibility joins

One figure is structurally eligible only when all of these conditions hold:

1. The figure ID is in the canonical figure family and belongs to the selected
   extraction namespace.
2. The figure has exactly one distinct `image_id` and exactly one distinct
   `caption_block_id`. Repeated references to either same ID are deduplicated
   and counted; two different IDs are not reduced to a preferred attachment.
3. Both attachments exist in their declared canonical families. The figure,
   image, caption, and page share the selected extraction and document identity.
4. The figure and caption share one section. The figure is `body`, explicitly
   non-TOC, and `inherited_nontext`; the attached block is a `caption`, is
   `body`, and is explicitly non-TOC.
5. The figure, image, and caption each resolve to exactly one distinct page ID,
   all three page IDs are equal, and that canonical page exists in the same
   document.
6. The caption text satisfies the complete leading-marker grammar below.

A missing or dangling attachment is rejected. More than one distinct image or
caption is `review_required` and publishes no alias. One image or caption shared
by different figures is rejected for every affected figure. These rules preserve
the observed qualified cardinality without inventing a preferred-item heuristic.

## Leading marker and alias form

Eligibility is evaluated on a trimmed caption. `Figure` is ASCII
case-insensitive and is followed by one or more ASCII spaces or tabs. The
identifier:

- consists of one or more ASCII alphanumeric components separated only by `.`
  or `-`;
- contains at least one digit; and
- is consumed completely before optional ASCII spaces or tabs and a required
  colon.

In regular-expression notation, the operative shape is:

```text
^(?P<marker>figure[\t ]+(?P<identifier>(?=[a-z0-9.-]*\d)[a-z0-9]+(?:[.-][a-z0-9]+)*))[\t ]*:
```

Matching is case-insensitive. A marker later in the caption is ineligible.
Period, comma, dash, or whitespace alone is not an accepted caption delimiter.
The parser publishes only the normalized marker, using
`nfc_nbsp_ascii_whitespace_casefold_v1`; it does not publish the full caption as
an alias. Thus `Figure 4.8-5:` creates only `figure 4.8-5`, never `figure 4.8`.
Forms such as `ES-1`, `9-1a`, and `4.8-10a` remain intact.

The colon boundary and marker-only alias match the accepted source evidence and
the existing exact figure-query form. A broader delimiter or identifier grammar
requires a new policy version.

## Decisions, collisions, and order

Every canonical figure receives exactly one qualification decision. Eligibility
is one of `eligible`, `rejected`, or `review_required`. The closed reasons are:

```text
eligible_attached_body_caption
wrong_figure_record_family
figure_document_identity_mismatch
figure_extraction_identity_mismatch
figure_not_body
figure_toc_or_unclassified
figure_semantic_placement_unqualified
missing_caption
multiple_captions
missing_image
multiple_images
caption_attachment_wrong_record_family
image_attachment_wrong_record_family
caption_attached_to_multiple_figures
image_attached_to_multiple_figures
dangling_caption_attachment
dangling_image_attachment
attachment_extraction_identity_mismatch
cross_document_attachment
cross_section_attachment
attached_block_not_caption
caption_not_body
caption_toc_or_unclassified
attachment_page_cardinality_unqualified
attachment_page_mismatch
dangling_page_attachment
page_record_namespace_mismatch
cross_document_page_attachment
page_extraction_identity_mismatch
figure_marker_not_leading
leading_figure_marker_absent_or_invalid
```

Eligible evidence is grouped by normalized marker. Targets are deduplicated by
figure target ID, ordered by canonical figure sequence and then ID, and emitted
in one alias record. One target is `unique`; two or more targets are
`ambiguous`. Alias groups are ordered by normalized marker, then appended after
preserved and table-derived aliases with contiguous sequences.

The shared exact resolver unions existing and FC1 alias evidence before
deduplicating by target ID. Existing and new evidence for the same marker and
target remains one logical candidate while retaining both alias evidence IDs.
The same marker on a different target remains an explicit collision; neither
the existing nor the new target is preferred. No matching alias yields zero
targets.

## Provenance and accounting

`FC1` aliases use origin `linking_v2_fc1_body_figure_caption` and evidence kind
`attached_body_figure_caption`. Each target preserves the local and upstream
figure IDs, caption ID, image ID, page ID and physical page number, attachment
IDs and repeated-reference counts, figure/caption classification, section IDs,
structural status, and text-only status. Validators reconstruct the exact join
against the preserved canonical records and reject missing, contradictory, or
cross-scope evidence.

Qualification accounting includes candidate, eligible, rejected, and
review-required figure counts; rejected/review-required counts by reason; alias
and target-edge counts; unique and ambiguous aliases; and collision groups.
Linked-document support separately reports preserved aliases, replayed table
aliases, FC1 figure aliases, and the allowed derived rule IDs. Counts describe
the bound input and must not be treated as source-independent constants.

## Structural identity and text-only usability

Structural eligibility answers only whether an exact reference can identify a
canonical figure. Every 06F target therefore carries
`structural_target_status: eligible` independently of
`text_only_evidence_status: not_evaluated_pending_task06h`. Caption text is
label metadata unless a separate review determines that it states the cited
substantive evidence. Task 06F never invents an image description or clears the
text-only exclusion.

This separation follows the W3C PROV distinction between a derived entity and
the source entities that support its derivation: figure, image, caption, page,
and attachment provenance remain available without asserting that the alias
contains the image's meaning.

## Qualification, reuse, and downstream handoff

Source-free qualification reads only the sealed canonical figures, images,
blocks, and pages plus compact manifest, inventory, and completion records. It
uses a fresh no-clobber namespace, binds policy/schema/code and selected input
identity, writes managed records atomically with completion last, and preserves
failed or superseded attempts. It does not open PDFs, render images, load
models, rerun extraction, hash preserved PDF/image payloads, or execute document,
collection, or reference replay.

Conversion, producers, canonical content, accepted seals, and the Task 06B
identity/reuse boundaries remain unchanged. Task 06G must bind this policy and
qualification, replay the affected linked-document and collection descendants,
and reproduce comparison queries without treating planning counts as truth.
Task 06H must review each prospective target's image/caption/page/classification
evidence and decide text-only usability, reusing existing renders only under its
accepted correspondence policy. Task 05G alone owns response-reference replay.
