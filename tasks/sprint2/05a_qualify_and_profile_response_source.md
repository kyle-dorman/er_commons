# Task 05A: Qualify and Profile the Response Source

Status: **complete and accepted; Task 05B activated**.

Activated 2026-09-08. The source-free gate was completed first, and the user
then separately authorized the exact 195-page source-read plan. No unlisted page
content, page labels, outlines, source hashes, source copies, or Volume 5 content
were read.

Accepted 2026-09-08. The acceptance is bound to the completed record set in
`records/task05a_acceptance.json` and authorizes source-free Task 05B contract
work only. It does not authorize another PDF read, the Task 05C pilot, or Volume
5 access.

## Abstract

Bind Task 05 to its exact upstream records and inspect a bounded, representative
set of Final EIR Volume 4 pages to learn the source grammar before designing the
inventory contract. Select the smallest maintained extraction or transcription
route that preserves exact text and anchors.

## Goal

Replace placeholder assumptions with a source-grounded structural-regime profile,
route decision, representative pilot set, and realistic workload estimate.

## Inputs

- [Task 05 umbrella](05_build_curator_only_response_inventory.md).
- Frozen Task 02 record for `feir_volume_4`.
- Task 03J extraction completion, Task 04A usability freeze, and Task 04D
  designated handoff named by the umbrella.
- Existing exploratory Volume 4 outputs as diagnostic evidence only; they are not
  production inputs or accepted counts.

## Outputs

- compact prerequisite-binding record using upstream identities and manifests;
- bounded structural-regime profile covering contents, the advertised General
  Responses 1-9 placement, agency and organization letters, public comments,
  Planning Commission material, continuation pages, multi-part units, and
  apparent exceptions;
- bounded representative page/range selection with an explicit selection reason;
- examples of comment, response, membership, and reference markers;
- extraction-versus-transcription route decision and reusable-component audit;
- estimated page, unit, review, runtime, and temporary-storage workload; and
- proposed 05B amendments based on observed source structure.

## Research / learning checkpoint

Compare maintained native-PDF extraction options already available in the
project. Explain why the selected route is sufficient for this structured
source and which information still requires human review. Record why reusing a
component does not make Volume 4 part of the Task 03 corpus.

## Plan

1. Validate compact upstream completion and identity metadata without recursively
   hashing large payloads.
2. Present the exact page/range read plan before opening the source PDF.
3. After explicit source-read authorization, inspect only the bounded selection.
4. Record structural regimes, ambiguities, extraction risks, and storage/runtime
   estimates.
5. Select the route and revise provisional Task 05B; do not implement it.

## Source-free gate outcome

Completed 2026-09-08. The source-free gate created working revision
`working/05a/source_free_v1/` beneath the Task 05 artifact root. Its compact
records are:

- `records/prerequisite_binding.json`; and
- `records/source_read_plan.json`.

This is a mutable Task 05 working revision, not an accepted release or a
production identity. No source PDF was opened, rendered, extracted, copied, or
rehashed, and no upstream payload tree was recursively hashed.

### Prerequisite binding

The compact binding closed without a mismatch:

- Task 02 release `brisbane_baylands_2025_deir_sources_v1` contains exactly one
  `curator_only_response_source`, `feir_volume_4`. Its recorded and observed size
  is 9,217,817 bytes, its recorded page count is 744, and it occurs zero times in
  the Task 03J model corpus. The recorded source checksum was not recomputed.
- Task 03J handoff
  `handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325`
  is `ready`, completion-last, and unblocked. Its accounting closes all 35 model
  sources as `complete_with_warnings` with zero terminal failures.
- Task 04A review `reviewv1-task03j-final-c17` is complete and frozen. Its
  approved usability registry covers the same 35 Task 03J sources and records
  zero unresolved material findings.
- Task 04D handoff
  `handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`
  is `ready`, completion-last, and unblocked. Its source membership equals Task
  03J exactly.
- Neither Task 04C nor the earlier superseded Task 04D handoff is selected.

Both machine handoffs retain their contractual
`task04_status: not_evaluated`. This is expected: Task 04D's downstream
designation is external to the machine completion, and Task 04A remains the
separate source of accepted human usability.

### Tooling decision

The source-free gate provisionally selected a narrow page-local `pypdfium2`
producer for native-extracted text and PDF-point geometry. Use Poppler
`pdftotext -bbox-layout` as an
independent text/box diagnostic and `pdftoppm` renders as the visual ground
comparison. Reserve `pypdf` for possible later page-label and outline metadata;
the 05A source profile did not read those document-wide structures. The bounded
profile confirmed this route subject to the requirements in the outcome below.

This choice is smaller than reusing the Task 03 Docling producer. PDFium already
provides bounded Unicode text, page boxes, rotation, character boxes, text
rectangles, search, and rendering. Task 05 still needs source-specific unit and
relationship rules, so Docling's model-backed semantic document pipeline would
add runtime, model identity, and an additional interpretation layer without
owning the required comment-response grammar. Reusing the project's PDFium
access and coordinate-transform components does not add Volume 4 to the Task 03
corpus: the Task 05 source role, configuration, activities, records, and
acceptance remain separate.

The primary alternatives are bounded as follows:

| Option | Task 05A disposition |
| --- | --- |
| `pypdfium2==5.12.1` | Provisional primary: model-free, page-local text and geometry with low restart state. |
| Poppler 26.07.0 | Independent extraction and visual-QA diagnostic; record the system version because it is outside the `uv` lock. |
| `pypdf==6.14.2` | Possible later page-label/outline metadata and disagreement checks only; it is not part of the 05A source read, and its maintainers warn that visitor coordinates can be wrong in complicated PDFs. |
| Docling 2.115.0 | Reject as primary unless the sample proves semantic layout recovery is necessary; otherwise it is operational and semantic overreach. |
| Camelot 2.0.0 | Reject as primary because it owns table extraction, not comment-response structure; reconsider only for an observed true table regime. |
| pikepdf 10.10.0 | Structural/integrity diagnostics only; it does not implement text extraction. |

The future text contract must not assume that PDFium character indexes map
one-to-one to Python string offsets. Preserve unnormalized full-Unicode text
from `get_text_bounded()`, physical page, page box and rotation basis, PDF-point
bounds, and a verbatim-text digest. Treat character spans and boxes as spatial
evidence, keep normalized matching text separate, and record manual
transcription as a distinct method when native text disagrees with the render.
In particular, audit rather than directly reuse the existing table-oriented
`native_word_tokens()` helper because it calls `get_text_range(index, 1)`.

Relevant maintained guidance:

- [pypdfium2 text and geometry API](https://pypdfium2.readthedocs.io/en/stable/python_api.html)
- [Docling PDF options and native pipeline](https://docling-project.github.io/docling/usage/advanced_options/)
- [pypdf text extraction limitations](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [pikepdf content-stream boundary](https://pikepdf.readthedocs.io/en/latest/topics/content_streams.html)
- [Camelot scope and long-document guidance](https://camelot-py.readthedocs.io/en/latest/user/faq.html)
- [Poppler `pdftotext` options](https://manpages.debian.org/testing/poppler-utils/pdftotext.1.en.html)
- [Poppler `pdftoppm` options](https://manpages.debian.org/trixie/poppler-utils/pdftoppm.1.en.html)

Reusable project components are limited to bounded native-text access and
handle closure in
`document_parsing/heading_evidence_parsing/native_pdf_observations.py`, displayed
page transforms and geometry measurement in `document_parsing/content_parsing/`,
PDFium rasterization conventions in `document_parsing/table_reconstruction/`,
and the general completion-last/restart pattern. Task 05 will not reuse Task 03
records or producer identity.

### Diagnostic-only exploratory evidence

The ignored `output/pdf/volume4_comment_response_categories.csv` is retained only
as a page-selection aid. Its deleted exploratory script flattened page text with
`pypdf`, paired markers greedily, and applied heuristic semantic labels. The
1,017 rows are not an accepted count. Known failures include blank responses,
misclassified commenter groups, split records, and an over-paired record spanning
pages 370 through 553. The CSV has no production schema, manifest, source-unit
anchors, or acceptance status. Neither it nor its generated report is a Task 05
input.

### Authorized source-read plan and execution

After separate authorization, the pass inspected exactly these one-based
physical PDF pages, totaling 195 of 744 pages (26.2%):

```text
1-84, 85-92, 154-158, 171-175, 179-185, 192-197, 273-276,
368-372, 551-555, 560-563, 568-570, 575-577, 584-586, 594-601,
668-671, 675-681, 684-691, 694-700, 709-713, 720-726, 738-744
```

Pages 1-84 are deliberately contiguous. The diagnostic rows begin at page 85
and did not preserve trustworthy internal boundaries for contents and the
advertised General Responses 1-9. Reading the entire prefix avoided choosing
only easy interiors or guessing the general-response boundaries. The later
ranges cover ordinary and anomalous state, regional, municipal, organization,
individual, and Planning Commission material; letter and commenter transitions;
separator and continuation pages; multipart and short units; general-response,
response-to-response, and Draft EIR references; both ends of the known
over-pairing failure; and the terminal page.

The document container was opened only to address these pages. Content streams,
text extraction, and rendering remained restricted to the enumerated pages;
the pass did not traverse document-wide page-label or outline metadata. Poppler
automatically emitted basic document fields in each bbox-layout XHTML header;
those incidental fields were recorded and excluded from analysis.

## Validation

- Confirm path, recorded byte size, source ID, source-release membership, and
  terminal upstream states without recomputing the source PDF checksum.
- Ensure the representative selection covers every known structural regime and
  records what remains unobserved.
- Compare extracted text and anchors visually on the selected pages.
- Confirm the route decision has explicit rejection reasons for alternatives.
- Run `git diff --check` for documentation-only changes.

## Acceptance criteria

- Upstream identities are exact and no superseded linking view is selected.
- The source grammar is understood well enough to define stable source-unit and
  anchor contracts.
- The proposed pilot is bounded but structurally varied.
- Runtime and storage estimates distinguish working, pilot, and final output.
- Task 05B can proceed without reopening basic source-boundary questions.

## Non-goals

- Production code, schemas, a full-page scan, or a complete inventory.
- Rehashing the source PDF or upstream Task 03/04 payload trees.
- Appendix Q extraction, response classification, or eligibility review.

## Outcome

Task 05A completed its bounded profile. All 195 authorized pages have an
explicit primary regime or non-content disposition in
`records/structural_regime_profile.json`. PDFium 5.12.1 extracted 514,805 text
characters with zero extraction failures, and all 514,815 inspected character
boxes were finite and within page tolerance. Poppler recovered materially the
same tokens (minimum token-multiset F1 0.98163), and all pages rendered cleanly.
Physical pages 2 and 4 are the only native-text-empty pages and are visually
blank. A repeated PDFium diagnostic completed in 1.03 seconds with a measured
maximum resident set of 179,798,016 bytes; these timings exclude unit review.

The route decision is confirmed: Task 05B should define a page-local PDFium
text-and-geometry producer with Poppler/render disagreement checks. Unit
boundaries require line-initial markers, geometry and style evidence, and
cross-page continuation state. Broad substring or greedy comment-to-response
pairing is invalid. Raw Unicode text, normalized text, PDFium character slots,
and underline/strikethrough revision evidence must remain separate.

The largest source correction is that Volume 4 physically contains General
Responses 1-8, not 1-9. Physical page 38 announces nine, physical page 39 lists
only eight, pages 39-83 contain those eight, and page 84 begins the federal
agency section. The Volume 4 contents route the ninth advertised topic to
Chapter 16 in Volume 5. Task 05 must represent this as a cross-volume placement
exception and may not invent a ninth Volume 4 unit or open Volume 5 without a
separate scope decision.

The completion evidence is under
`working/05a/source_free_v1/records/`. Disposable PDFium, Poppler, render, and
contact-sheet diagnostics remain under its `cache/`. The proposed Task 05C pilot
is 89 pages across 14 bounded ranges; full details and linear runtime, storage,
unit-count, and curator-workload estimates are in
`records/route_and_workload_decision.json`. The user accepted this outcome, and
Task 05B is now active for source-free contract definition.

Validation included exact selected-page closure, JSON parsing, independent
native-text comparison, visual review of every selected render, page-regime
accounting, source-access boundary checks, and `git diff --check`. No unlisted
page content, source hash, source copy, page-label/outline traversal, or Volume 5
read occurred.
