# Sprint 2: Brisbane Draft-EIR Defense Vertical Slice

Sprint 2 implements the accepted Sprint 1 contract as the smallest end-to-end
benchmark run. It is deliberately one project, one target model, and one
auditable evaluation path—not a general CEQA platform.

## Goal

Produce a rerunnable evaluation of one fixed local model answering locked,
comment-derived questions with evidence-grounded defenses from the original
2025 Brisbane Baylands Draft EIR.

## Accepted execution decisions

### Source corpus boundary

The model-facing source corpus includes the complete 2025 Draft EIR main-report
PDF and every appendix published on the City's official 2025 Draft EIR page.
Choosing relevant evidence from that full source set is part of the benchmark
challenge. The separately published chapter PDFs duplicate the main report and
are not additional corpus documents; retain them only as source-recovery or QA
aids if needed.

Freeze the official landing-page and file URLs, access timestamps, checksums,
byte sizes, MIME types, and PDF page counts before annotation. Candidate
inventory must identify at least 35 plausible cases before full annotation
begins, leaving room for later evidence review, exclusions, and cluster-safe
splitting while preserving the minimum 25 accepted cases.

### Canonical extraction boundary

Retain Docling's original structured output and the clean table pipeline's raw
and cleaned outputs, and materialize a stable canonical interface with page,
structural-block, table, and table-family records. Page records preserve
document identity, PDF page number, printed page label when present, canonical
text, and conversion provenance. Structural blocks preserve headings,
paragraphs, list items, captions, Docling table-region observations, and other
detected elements with stable links to their source page and location. Clean
table-pipeline records supply canonical table content; TableFormer remains
disabled and Docling table regions do not supply canonical cells.

Preserve explicit mappings between Docling table-region observations and clean
logical tables. One observed region may map to zero, one, or several clean
tables; do not force a one-to-one relationship or collapse separately
reconstructed tables. Represent related tables as first-class, machine-derived
table families where the reviewed footer and header evidence supports reading
them together. Finalize deterministic family membership and IDs only over a
complete document and scope those IDs to one extraction version; pilot and
partial-run family numbers are not canonical identities.

Save extracted images and their source-page and bounding-box metadata as part
of the conversion artifacts, even though first-pass retrieval and generation
remain text-only. Do not silently discard figures or other visual elements;
represent them in the structural record and link them to the saved image
artifact. Full-page renders, overlays, diagnostic HTML and Markdown, ruling
masks, and table-debug images are reproducible review-cache derivatives, not
canonical extraction artifacts. Generate and checksum them only for requested
review or labeling pages. Retrieval passage size, overlap, and heading
composition are later BM25 decisions and must not be fixed by the extraction
task.

Use native PDF text and layout extraction only in this sprint; do not apply
OCR. Task 03 canonical page, table, and table-family records contain
machine-derived content, provenance, and stage statuses only. Conversion,
routing, table-stage, and canonicalization statuses remain distinct and do not
constitute usability judgments.

Task 04 maintains separate linked page, table, and table-family usability
records for every source document, keyed by Task 03 canonical IDs. Each review
record identifies its entity type and records human review status, exclusion
reason when present, reviewer, review date, and links to the applicable
canonical content and requested review-cache render. This granularity permits
one table in a family to pass while another does not. Task 04 rolls page
statuses up into document dispositions such as `usable`,
`usable_with_exclusions`, and `skipped_no_ocr`; reviewer fields and human
dispositions do not enter immutable Task 03 machine records.

An isolated failed page does not require excluding an otherwise usable
appendix. Mark failed pages unusable and retain the appendix as
`usable_with_exclusions` when the missing material does not make the remaining
content or its cross-references unreliable. Skip the entire appendix when
failure is widespread or affects essential context. A human must review every
excluded page and wholly skipped document against requested review-cache
renders. Make the usability registry available to curator-only response
inventory and screening so response references can be resolved against usable
parts of each appendix. Exclude candidate cases whose required evidence
depends on unusable pages. The complete main report is mandatory and cannot be
silently skipped under this policy; a material native-extraction failure there
is a stop condition requiring a new decision.

First-pass retrieval and generation may use a table only when the clean table
pipeline produces a canonical structured or textual representation and Task 04
human review verifies it against a corresponding review-cache render. For a
multi-table family, review must make the family membership, per-table content,
and any one-to-many Docling-region mapping visible; verification of one member
does not silently verify every member. Figure captions and surrounding prose
may serve as text evidence. Exclude any candidate whose defense requires the
target model to interpret a chart, map, photograph, diagram, or other visual
content that it will not receive. Record these cases as
`excluded_requires_visual_evidence` so they remain discoverable for a later
multimodal benchmark rather than disappearing from the inventory.

### Curator-only response inventory boundary

Enumerate every identifiable comment and response unit in Final EIR Volume 4
before eligibility screening. Preserve comment and response IDs, exact source
pages and text anchors, commenter letter or organization, cross-references,
and stated Draft EIR chapter, appendix, or page references. Represent
one-to-many and many-to-one comment-response relationships explicitly rather
than forcing each source unit into an artificial one-to-one row.

Preserve general responses as canonical source units with their own IDs and
anchors. For every response that refers to a general response, also produce a
derived resolved review view that includes the referenced general-response
text, ID, and source anchor with the individual comment-response pair. This
view must be independently reviewable without erasing where the incorporated
text came from or altering the canonical source transcription.

Validate the relationship graph in both directions. Flag every identifiable
comment with no response as an orphan for human review, and flag every general
response that is not linked to at least one comment or individual response.
Record whether each apparent orphan is a source omission, extraction failure,
unresolved cross-reference, or legitimate document structure. Do not silently
drop unmatched units.

Construct the inventory deterministically from document structure, source IDs,
headings, and explicit cross-reference patterns, with manual resolution of
ambiguous cases. Do not use an LLM to create, segment, link, or triage the
inventory in this sprint. Model assistance for inventory work is out of scope
for now; it may be evaluated later against the completed human-reviewed
inventory as a QA reference.

Human reviewers alone determine candidate eligibility. Deterministic checks
may flag language, source references, or missing links for reviewer attention,
but they do not accept or reject cases. Exclude an entire comment-response case
when any material part of the response depends on a later revision, new
Final-EIR analysis, external evidence, a mitigation change, unusable source
content, or visual evidence unavailable to the target model. Do not rewrite a
question to isolate only its convenient answerable portion unless the source
itself clearly separates independent issues into distinct response units.

Use a two-pass single-curator workflow because this sprint has one available
human reviewer. In the first pass, the curator reviews the resolved
comment-response pair, including linked general responses, and assigns
provisional eligibility with a reason code. In the later evidence-verification
pass, the curator reviews the original comment, resolved response, exact Draft
EIR evidence spans, requested review-cache renders, source-usability status,
and relevant cross-references, then reapplies the eligibility criteria. A case
becomes accepted only after passing both reviews.

Preserve every inventory, screening, evidence-verification, acceptance, and
selection decision as a versioned record rather than overwriting earlier
dispositions. Each decision records the stable source or case ID, review stage,
disposition, reason code, reviewer, timestamp, and the input artifact version
that was reviewed. Produce an annotation attrition waterfall with raw counts at
each stage—from the complete response inventory through plausible candidates,
first-pass eligibility, evidence verification, accepted cases, and final split
selection—and report exclusions by reason code. The waterfall is an audit
summary derived from the decision records, not a separately maintained count.

Where practical, the second-pass interface should not emphasize the first-pass
rationale until the verification decision is made, reducing anchoring without
claiming reviewer independence. Report this as repeated single-curator review,
not inter-reviewer agreement. Model eligibility QA remains out of scope for
Sprint 2 and cannot substitute for either human pass.

During accepted-case review, build split-clustering candidates
deterministically from commenter-letter membership, explicit response and
general-response links, cross-references, and duplicate or near-duplicate
source text. The curator does not manually compare every inventory pair. For
each general-response link attached to a provisionally accepted case, the
review form asks whether the linked general response contributes substantively
to the defense or is merely administrative. Confirmed substantive links create
clustering edges; administrative links remain recorded but do not join cases.
The human curator owns this classification, while code owns candidate-link
enumeration and connected-component construction.

Shared Draft EIR evidence or source-section overlap creates a cluster-review
warning but not an automatic edge. Broad sections may support distinct issues,
so the curator confirms whether the cases are substantively duplicative before
they are joined. Preserve the overlap signal and disposition for audit even
when no edge is created.

Before freezing the split, validate duplicate and near-duplicate candidate
generation against a small deterministic fixture containing representative
positive and negative pairs. Cover exact duplicates, harmless formatting or
preamble changes, paraphrased duplicates, and distinct issues that share
boilerplate. Report misses and false-positive candidates; do not select a fuzzy
threshold by intuition alone. Also produce a split-leakage audit showing that
no confirmed relationship or duplicate-cluster edge crosses the proposed
development/test boundary and listing every warning and curator disposition.
This fixture validates candidate enumeration only; it does not replace human
authority over substantive clustering edges.

Never split a confirmed cluster. Select 25 cases from the larger accepted pool
so whole clusters produce exactly 10 development and 15 test cases, preferring
broader issue, source-document, and commenter diversity when several valid
allocations exist. Generate the proposed selection and split with a
deterministic algorithm, recorded objective, and seed, then require curator
review before locking it. If no exact cluster-preserving allocation exists,
stop for a new decision rather than weakening the cluster rules or silently
changing the split sizes.

Keep test locking lightweight for the MVP. Save and hash the accepted cases,
split manifest, and frozen retrieval, prompt, model, and judge configurations
before the primary test run. Keep test-reference fields out of target-model
inputs through the artifact schema, but do not build a permissions system,
special access workflow, or elaborate CLI lock. Record later configuration
changes as new named runs rather than replacing the primary result.

### Model-assisted reference-case authoring

After a candidate passes initial human screening, a curation model may use the
original comment, resolved individual and general responses, and candidate
Draft EIR evidence to propose three distinct artifacts in order:

1. **Relevant citations:** canonical Draft EIR evidence spans with source IDs
   and provenance distinguishing references explicitly identified by the
   official response from evidence found through additional corpus retrieval.
2. **Evidence summary:** a concise synthesis of what the proposed evidence
   establishes, with every substantive statement linked to the proposed
   citations.
3. **Reference defense:** a concise answer to the original comment using only
   the proposed Draft EIR evidence, with sentence-level citations.

Treat these as three separate review levels, similar to the staged DocScope
review pattern, rather than one opaque generated answer. Preserve the model's
proposal and the curator-edited result at every level, along with prompt
version, model tag and resolved digest, settings, and input artifact IDs. The
single human curator reviews and edits all three levels before the case can be
finalized. Model output never establishes evidence validity or case acceptance
without that review.

Human approval is a gate between authoring levels. The curation model first
proposes citations; only the curator-approved citation set may be passed to the
summary call. Only the curator-approved citations and summary may be passed to
the defense call. Each case therefore uses three separately recorded model
calls and three curator review states. A rejected or unresolved level stops the
case from advancing rather than allowing downstream prose to conceal an
upstream evidence problem.

Build the proposed citation pool through a reproducible high-recall curator
search that is separate from the later top-five benchmark retriever. Resolve
the official response's explicit Draft EIR references first, then search the
full usable corpus from the comment and resolved response. Preserve distinct
provenance for response-explicit and search-discovered evidence, along with
which model call proposed each span and the curator's disposition.

The citation-proposal call is closed over that supplied candidate pool. Its
schema may select only canonical evidence IDs present in the input; it may not
invent page references, quote unseen passages, or request arbitrary source
IDs. For each selected span, require a short relevance explanation and a
classification of direct support versus contextual material. The schema must
also permit an explicit `insufficient_evidence` result. Validate all returned
IDs mechanically before presenting the proposal for curator review.

Contextual spans may remain in the curation packet to explain terminology,
scope, or cross-references, but they do not count as reference evidence and
cannot independently justify a claim. Every substantive sentence in both the
curator-approved evidence summary and curator-approved reference defense must
cite at least one direct-support span. Retrieval coverage metrics score only
against curator-approved direct-support spans, not contextual material.

Represent evidence hierarchically rather than treating a PDF page as the
semantic citation unit. Preserve the source's own document or appendix,
section, table, and figure references as semantic evidence units, including
units that span multiple pages. Attach one or more exact canonical page,
block, table, or visual-asset anchors beneath each unit for verification,
retrieval scoring, and review-cache rendering. A response-level reference to
an entire section or appendix seeds search within that unit; the accepted
evidence retains both the original semantic reference and the exact supporting
anchors found within it. Human-readable citations should follow the source's
naming conventions while remaining mechanically resolvable through the
internal anchors.

Create reviewed reference-evidence records during case authoring as the bridge
between canonical extraction records and curator-approved citations. Each
record has a stable evidence ID, semantic source-unit ID, one or more exact
canonical anchor IDs, display citation, evidence text, support/context
classification, discovery provenance, and curator disposition. A record may
combine multiple blocks within one semantic evidence unit without weakening
their exact source traceability.

Require curation and target models to return structured statement-to-evidence
mappings using only IDs supplied in their respective inputs. Render those IDs
deterministically into human-readable Draft EIR citations; do not rely on a
model to reproduce section names, page labels, or citation formatting. Keep
curator-approved reference evidence separate from target retrieval records:
the target receives only the top-five passage records produced by its frozen
retriever and may cite only those passage IDs. Reference and retrieval records
share the same canonical-anchor and display-citation conventions but use
distinct artifact roles and namespaces. Judging and evaluation may compare the
two after prediction; the target never receives the reference-evidence IDs,
labels, or dispositions. The accepted Docling-plus-clean-table pipeline
supplies canonical source entities and anchors, case authoring owns reviewed
reference evidence, and the retrieval stage owns target passage records.

Canonical source and anchor IDs are deterministic within a frozen extraction
version, not promised to survive a materially different conversion. Record the
source checksums, Docling and table-pipeline versions, complete configuration
hash, and corpus version that define each extraction. An identical rerun must
reproduce the same IDs; a
changed converter or configuration creates a new corpus version and new
low-level anchors. Pin reviewed evidence and benchmark cases to the exact
extraction version. Human-readable document and section slugs may remain
recognizable across versions, but they do not replace content and configuration
checksums.

Present the target model's five retrieved passages in BM25 rank order. Each
record includes an anonymous passage ID, human-readable document or appendix
and section metadata, printed and PDF page locations when available, and the
passage text. Do not expose numeric retrieval scores, gold-evidence overlap,
curator labels or dispositions, official-response discovery provenance, or QA
notes. Unusable source content is excluded before retrieval rather than marked
for the target. Rank conveys ordering; the model receives no gold annotations.

Pre-register two secondary oracle scaffold diagnostics using the three-stage
reference artifacts. The primary baseline remains the scoped comment plus five
BM25 passages and must run first. In the `A` condition, give the same target the
comment plus curator-approved reference citations and evidence, but neither the
reviewed summary nor reference defense. In the `A+B` condition, also provide
the reviewed evidence summary, but never provide the reference defense. Store
each condition under a separate anonymous run ID and evaluate predictions in
blinded randomized order.

Do not mix oracle-condition results into the primary baseline score. Interpret
baseline-to-`A` improvement as evidence of retrieval or evidence-selection
limitations, `A`-to-`A+B` improvement as evidence of synthesis limitations,
and failure under `A+B` as evidence of defense-writing or instruction-following
limitations. These conditions change the supplied scaffold, not the target
model's weights.

Do not freeze a 200-word defense limit before the annotation and target pilots.
Test at least 200- and 400-word limits against varied reviewed reference cases,
including long official responses, and select the smallest limit that permits
a complete concise Draft-EIR-only defense without forced omission. Apply the
same frozen word and statement limits to the primary baseline and both oracle
conditions; exclude deterministically rendered citations from the word count.
If 400 words is still inadequate for a complete pilot case, stop for a new
length decision rather than silently truncating the answer or reference.

Use a zero-shot fixed prompt for the initial target baseline. It contains the
task instruction, structured output schema, citation and abstention rules,
scoped original comment, and the five retrieved passages. Do not include
completed development reference defenses or other benchmark cases as few-shot
examples. Any later few-shot prompt is a separately named secondary condition
and cannot replace or retroactively modify the primary baseline.

Run the target at temperature `0` with a fixed seed where supported and record
the model digest, prompt hash, schema version, context, and runtime settings.
Generate three baseline repeats for each of the 10 development cases and
compare them mechanically before human review. Human-review repeats only when
they differ substantively. If differences are limited to harmless formatting,
use one generation per locked-test condition. If claims, citations,
abstention, or resulting scores vary materially, stop and decide whether the
locked test requires repeated runs rather than selecting a favorable output.

Retry only infrastructure failures such as an unavailable Ollama service,
timeout, or interrupted process, using a fixed attempt and backoff policy with
identical model inputs and settings. Record every attempt. Do not use a model
repair call or repeated generation to replace schema-invalid or semantically
invalid output. Preserve such output as an invalid prediction and score it
under the frozen evaluation contract rather than selecting a later
valid-looking answer.

Use whole leaf sections—the smallest heading-defined sections in the canonical
hierarchy—as the preferred BM25 retrieval units. Preserve paragraph and
list-item boundaries within them, keep verified tables as distinct structured
units, carry the full heading path as metadata, and retain exact canonical
anchors. Before building the development index, analyze and report the leaf
section length distribution by source document, including outliers and the
combined size of five large results relative to the target context budget.

Proceed with whole leaf sections only if that analysis shows usable and
reasonably bounded units. If lengths are too variable, appendices lack useful
heading structure, or large sections would exceed the context budget, pilot a
fixed-length structure-preserving fallback within section boundaries. Do not
split all sections by default, cross semantic boundaries, or choose a fallback
size without recording the length evidence that required it.

Index each retrieval unit's full canonical heading path together with its body
text because section and appendix headings may contain important topic terms
that are not repeated in every paragraph. Show the same heading path to the
target as source metadata. Exclude repeated page headers, footers, page
numbers, and generic document boilerplate from indexed text.

Use only the exact scoped original comment text as the primary BM25 query. Do
not include the official individual or general responses, reviewed citations,
evidence summary, reference defense, curator labels, or model-generated query
expansion. The separate high-recall curation search may use curator-only
response material because it constructs reviewed references; the benchmark
retriever may not.

On development cases, compare two frozen lexical preprocessing candidates. The
plain candidate applies Unicode normalization, lowercasing, and
punctuation-aware token splitting without stemming or stopword removal. The
normalized-English candidate adds English stemming and a versioned English
stopword list that explicitly retains negations such as `no`, `not`, and
`without`. Select using direct-support evidence coverage at five; if results
are effectively tied, prefer the simpler plain candidate. Save the tokenizer
configuration, vocabulary, stemmer package and version when used, and exact
stopword list with the index artifacts.

Define evidence coverage at five as the fraction of curator-approved
direct-support evidence records whose exact canonical anchors are contained in
the five retrieved leaf sections or table units. Context-only records do not
count, and semantic similarity without anchor overlap is not a hit. Also report
complete-case coverage at five: the count and fraction of cases for which all
approved direct-support evidence records are present in the top five. Preserve
raw numerators, denominators, per-case results, and the matched anchor IDs.

Save the top 20 ranked BM25 results and scores for each query as diagnostic
artifacts, while exposing only ranks one through five to the target model.
Report evidence-coverage curves at `1`, `3`, `5`, `10`, and `20`, but retain
coverage at five as the primary retrieval metric. Use the deeper list only to
distinguish evidence that was missed entirely from evidence ranked below the
target cutoff; it does not expand target context.

Use BM25S's maintained default Lucene-style scoring method and default scoring
parameters. Record the exact BM25S version, method, and parameters with the
index, but do not run a parameter sweep on the 10 development cases. Restrict
development comparison to the already defined retrieval-unit fallback when
needed and the plain-versus-normalized-English preprocessing pilot.

Build the indexed corpus in canonical retrieval-unit ID order. Rank results by
BM25 score descending and break exact score ties by canonical retrieval-unit ID
ascending. Save raw scores in retrieval artifacts for diagnostics even though
the target does not receive them. An identical frozen corpus, tokenizer, index
configuration, and query must reproduce the same ranked IDs.

The curator reviews, narrows, corrects, accepts, or rejects the proposed spans
but is not expected to conduct open-ended manual corpus research. If the
automated process does not surface sufficient Draft EIR support, flag the case
as insufficient evidence found or exclude it under the applicable rule. During
the annotation pilot, measure how often explicit response references are
sufficient by source document; the frozen workflow may reduce additional
search where the evidence shows it is unnecessary. Do not tune the later
top-five benchmark retriever on this curation search configuration or report
the curation search as baseline retrieval performance.

For the initial pilot, construct curation-search queries deterministically from
the original comment, individual response, incorporated general-response text,
and explicit section, appendix, page, or named-topic references. Run and log
the component lexical searches separately, then merge and deduplicate their
results before the citation-proposal model sees them. Model-generated query
expansion is out of scope for the initial pilot and may be tested later only if
the recorded evidence shows inadequate recall.

Also build a deterministic section-reference graph from explicit references
within the Draft EIR corpus. Graph nodes identify canonical document sections
and graph edges retain the source span containing each cross-reference. Use
bounded graph traversal to add explicitly referenced neighboring sections to
the curator evidence pool. Preserve the complete discovery path for every
graph-expanded span, deduplicate cycles, and record any configured traversal or
result limit rather than silently truncating the expansion.

For the pilot, traverse at most two explicit-reference edges from each seed
section. This permits paths such as a response-cited section referring to a
second section that in turn refers to an appendix, without unbounded graph
expansion. Report how often curator-accepted evidence originated at hop zero,
one, or two. The annotation workflow may reduce the depth before it is frozen
if second-hop evidence does not contribute.

### Model roles

Keep curation, target generation, and automated judging as distinct model
roles. Use pinned `gpt-oss:20b` as the initial local curation model for citation
proposals, evidence summaries, and reference-defense drafts. Use pinned
`qwen3:4b-instruct-2507-q4_K_M` as the intentionally small initial target
baseline. Use pinned `gemma3:12b` as the initial local judge candidate; compare
`gemma3:4b` on the same human-scored development records only if a smaller,
faster judge is useful, and adopt it only if calibration shows little material
loss.

Resolve and record the exact model digest for every run rather than relying on
mutable tags. Local inference avoids per-token API charges but does not remove
the requirement to record runtime, structured-output failures, and human
calibration. A later target-model comparison may test other model sizes or
families against the same frozen benchmark without changing the reference
cases.

The canonical case preserves the exact original comment text or an explicitly
identified source span with its provenance. It does not add a curator-written
neutral question or a separate material-concerns field. The target model
receives that scoped original comment, not the official response, curation
model drafts, reviewed evidence summary, or reviewed reference defense.

## Provisional execution sequence

Sprint 2 is current, but it has no active numbered task at promotion. Create
each detailed task contract immediately before executing that bounded stage,
using the prior outcome and current artifacts as its inputs. The numbers below
are provisional routing labels, not a promise that the sprint will contain
only 11 tasks. Split a stage further whenever its implementation contract is
too large or new evidence creates a distinct decision or validation boundary.

1. **Task 02 — Freeze sources and provenance.** Inventory, acquire, checksum,
   validate, and manifest the complete Draft EIR main report, all official
   appendices, curator-only Final EIR Volume 4, and duplicate chapter files used
   only for recovery or QA. Record URL, checksum, page count, and source role
   per file. For this local MVP, use one corpus-level visible-terms note with a
   per-file override only when a source differs; do not require a separate
   per-PDF legal matrix or make a reuse determination.
2. **Task 03 — Build the canonical Draft EIR extraction.** Pin the accepted
   Docling-plus-clean-table configuration; produce canonical document, section,
   page, block, table, table-family, figure, image, asset, and cross-reference
   records with version-scoped deterministic IDs. At the user's request, this
   large stage is split into bounded stop-and-review contracts:
   - [Task 03A](../../tasks/sprint2/03a_validate_document_parser.md): validate
     Docling, the native-only configuration, and structural failure modes;
   - [Task 03B](../../tasks/sprint2/03b_define_canonical_extraction_contract.md):
     define extraction versioning, schemas, provenance, coordinates, and IDs;
   - [Task 03C](../../tasks/sprint2/03c_build_single_document_conversion.md):
     promote the accepted producer stack into one atomic complete-document run;
   - [Task 03D](../../tasks/sprint2/03d_materialize_canonical_records.md):
     materialize core canonical records from preserved raw output;
   - [Task 03E](../../tasks/sprint2/03e_build_hierarchy_and_cross_references.md):
     derive hierarchy and printed-page labels;
   - **planned Task 03E.1:** extract cross-reference mentions and resolve
     candidates against the accepted Task 03E hierarchy, labels, and aliases;
     write its detailed contract only after Task 03E is accepted;
   - [Task 03F](../../tasks/sprint2/03f_make_extraction_restartable.md): add
     restartable, resource-bounded corpus orchestration;
   - [Task 03G](../../tasks/sprint2/03g_run_representative_extraction_pilot.md):
     run the full-document production pilot, rehearse the human-usability
     review, and freeze its configuration and review method; and
   - [Task 03H](../../tasks/sprint2/03h_run_full_canonical_extraction.md): run
     all 35 sources and publish the candidate extraction for Task 04.
   Tasks 03A through 03D are complete. Task 03C published the checksum-verified
   222-page Appendix P producer run with 19 clean tables and 19
   complete-document families. [Task
   03C.1](../../tasks/sprint2/03c1_rewrite_complete_document_producer.md)
   subsequently replaced the reference orchestrator with the accepted
   human-owned implementation and proved semantic equivalence through a second
   complete Appendix P run. Task 03D then materialized its schema-valid,
   checksum-verified canonical candidate and preserved the observed producer
   anomalies. Task 03D.1 replaced the MVP materializer with a human-owned
   implementation and passed a record-level equivalence gate with zero
   mismatches. Task 03E now points to that accepted candidate and remains
   inactive pending user review. Tasks 03F through 03H remain provisional and
   must be revised from each accepted preceding outcome before activation.
3. **Task 04 — Review usability and freeze extraction v1.** Run automated
   integrity checks and representative visual QA; review every excluded page
   or document and every table proposed for retrieval; inspect per-table
   content, table-family membership, and Docling-region-to-clean-table mappings;
   publish the separate page/table usability registry and frozen extraction
   manifest without adding reviewer fields to Task 03 machine records or using
   OCR.
4. **Task 05 — Build the complete curator-only response inventory.** Enumerate
   every comment, individual response, general response, relationship, and
   orphan in Volume 4; produce provenance-preserving resolved review views.
5. **Task 06 — Pilot reference-case authoring.** Implement and test the
   deterministic high-recall curator search, two-hop section-reference graph,
   three approval-gated GPT-OSS authoring calls, evidence registry, and
   Label Studio review flow on a small varied pilot.
6. **Task 07 — Curate, cluster, split, and freeze the benchmark.** Identify at
   least 35 plausible cases, finish two-pass single-curator review, accept at
   least 25 cases, form reviewed clusters, and materialize the deterministic
   10-development/15-test split. Preserve versioned decisions throughout and
   publish the derived annotation attrition waterfall with exclusion counts by
   reason code. Validate duplicate candidate generation on the small adversarial
   fixture and publish the final cross-split leakage audit.
7. **Task 08 — Build and freeze human evaluation.** Implement the staged,
   blinded evidence-support, responsiveness, and reference-coverage forms and
   anchored `0`/`1`/`2` rubric before target-model development.
8. **Task 09 — Build and freeze BM25 retrieval.** Analyze leaf-section lengths,
   choose whole sections or the documented fallback, run the small lexical
   preprocessing pilot, freeze the index, and report evidence-coverage curves.
9. **Task 10 — Build and freeze target generation.** Implement the zero-shot
   Qwen3 4B structured-output prompt, abstention and citation validation,
   output-length pilot, and development stability check.
10. **Task 11 — Calibrate the automated judge.** Run the three staged Gemma 3
    12B judge calls against locked human development scores and either freeze
    the judge or retain it as diagnostic-only under the accepted gate.
11. **Task 12 — Run the locked test and close Sprint 2.** Execute the primary
    baseline first, then the pre-registered `A` and `A+B` oracle diagnostics;
    human-review every test prediction, preserve automated scores separately,
    analyze errors by stage, and make the second-project decision.

## UI and artifact boundary

Docling Serve's UI is a convenience for conversion spot checks. Canonical
extraction evidence is the saved Docling outputs and page-level QA log. Label
Studio is the human-review surface; a deterministic export converter produces
canonical benchmark JSONL. Raw PDFs, converted text, indices, local models,
and runs remain under `ER_COMMONS_DATA_ROOT`, not Git.

## Human evaluation boundary

Define and freeze the human evaluation contract before implementing benchmark
retrieval or target generation. Keep three review dimensions separate:

1. **Evidence support:** at the statement level, determine whether the cited
   Draft EIR evidence directly supports the generated statement and identify
   substantive unsupported statements.
2. **Responsiveness:** at the case level, determine whether the defense answers
   the original scoped comment without changing or evading the issue.
3. **Reference coverage:** at the case level, compare with the reviewed
   reference defense and determine whether the generated defense captures the
   important Draft-EIR-supported answer. Do not create a separate
   material-concerns field for this purpose.

Allow the target output schema to return either `answered` with structured
statement-to-evidence mappings or `insufficient_evidence` with no substantive
defense claims. Treat abstention as structurally valid but not successful:
evidence support is not applicable, responsiveness is `0`, and reference
coverage is `0`. Report abstentions separately. Attribute an abstention to a
retrieval limitation when the required reviewed evidence was absent from the
top-five context, and to a generation limitation when sufficient reviewed
evidence was present but the target still abstained.

Treat output-schema validity, citation syntax, evidence-ID existence,
allowed-corpus membership, and mechanical citation resolution as deterministic
checks rather than human scores. Preserve the three human dimensions
separately even if a later report also presents an overall summary.

Use an anchored `0`/`1`/`2` human rubric. Score evidence support for each
generated statement: `2` when fully supported by its cited evidence, `1` when
partially supported, overstated, or requiring qualification, and `0` when
unsupported, contradicted, or paired with irrelevant evidence. Score
responsiveness per case: `2` when the defense directly and adequately addresses
the comment, `1` when it does so only partially or indirectly, and `0` when it
does not address or materially misframes the comment. Score reference coverage
per case: `2` when the defense captures the important supported answer, `1`
when it captures some but omits an important part, and `0` when it misses the
central supported answer.

Report statement-level counts and all three dimensions separately. Do not use
a composite score as the primary result; with a 15-case test set, retain raw
counts and per-case records alongside any summary statistics.

Stage human evaluation to reduce reference-answer bias. First run mechanical
validation. Next score evidence support while showing each generated statement,
its cited evidence, and requested review-cache links but hiding the reviewed
evidence summary and reference defense. Then score responsiveness from the
original comment and complete generated defense while the reference remains
hidden. Only after those decisions are saved should the interface reveal the
reviewed evidence summary and reference defense for reference-coverage
scoring. Preserve the saved result and timestamp from each stage rather than
allowing later reference exposure to silently rewrite earlier judgments.

Blind the human evaluator to target-model identity and size, experiment labels
that reveal the condition, automated-judge scores and explanations, and
aggregate results from previously evaluated cases until the human record is
locked. Reveal model and judge metadata only afterward. When comparing multiple
target models, present predictions in randomized order under anonymous run IDs
and record the randomization seed and concealed mapping in the run artifacts.

Mirror the human stages with three separate structured automated-judge calls.
The evidence-support call receives generated statements and their cited
evidence but no reviewed reference. The responsiveness call receives the
original comment and generated defense but no reviewed reference. The
reference-coverage call receives the comment, generated defense, reviewed
evidence summary, and reference defense. Use the same anchored `0`/`1`/`2`
definitions as the human rubric and retain criterion-level explanations as
audit evidence. Do not use a single all-information call whose access to the
reference could influence support or responsiveness judgments.

Calibrate each judge dimension against the locked human development records.
The provisional usability gate is at least 80 percent exact agreement, no
severe endpoint disagreement (`0` versus `2` in either direction), and 100
percent flag recall for human-scored `0` records. Calculate evidence-support
agreement across scored statements and responsiveness and reference-coverage
agreement across development cases. Report raw numerators, denominators, the
full confusion matrix, and every disagreement alongside percentages.

Judge prompts or schemas may be revised only from development evidence. If the
judge still fails after documented development-only revision, do not treat it
as trusted triage: freeze the target system, retain human evaluation as
authoritative, and report judge results as diagnostic. Passing this gate does
not replace the already required human review of every locked-test prediction.

## Completion gate

Sprint 2 is ready for a second-project decision only after a locked 15-case
test run is reproducible, citations resolve, judge-to-human audit agreement is
reported, and the error analysis identifies the limiting stage.
