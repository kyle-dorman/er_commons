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
byte sizes, MIME types, and PDF page counts before annotation. Task 08 uses
task-by-task authoring across all participating batches; the accepted release
retains 49 cases with 19 development and 30 test cases. The [08E plan](../../tasks/sprint2/08e_review_group_evidence.md) prepares research
in batch and reviews each question in chat, without source deduplication.
There is no up-front 35-candidate gate; retain normal attrition and agree final
size and topic-balanced split after all group batches finish.

### Canonical extraction boundary

Retain Docling's original structured output and the clean table pipeline's raw
and cleaned outputs, and materialize a stable canonical interface with page,
structural-block, semantic-section, printed-label, alias, table, table-family,
and cross-reference records. Page records preserve document identity, PDF page
number, printed-label evidence and resolution when present, canonical text,
and conversion provenance. Structural blocks preserve headings, paragraphs,
list items, captions, Docling table-region observations, and other detected
elements with stable links to their source page and location. Semantic
sections retain ordered block membership beneath separate body and furniture
roots. Visible table-of-contents entries may supply hierarchy evidence and
aliases, but are not body-section starts. Clean table-pipeline records supply
canonical table content; TableFormer remains disabled and Docling table
regions do not supply canonical cells.

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

Task 04A maintains a separate usability registry for every Task 03 source,
including sources whose terminal failure leaves no canonical document ID.
Registry rows therefore retain the corpus candidate and source IDs and add
canonical IDs only when those entities exist. Page, table, and table-family
records identify their entity type, human review status, exclusion reason when
present, reviewer, review date, and links to applicable canonical content and
requested review-cache renders. This granularity permits one table in a family
to pass while another does not. Task 04A also records sampled or
anomaly-triggered observations for body/furniture classification, hierarchy,
printed labels, aliases, and cross-references. It rolls page statuses up into
document dispositions such as `usable`, `usable_with_exclusions`, and
`skipped_no_ocr`; reviewer fields and human dispositions never enter immutable
Task 03 machine records.

Task 04A's registry is the original accepted usability review over Task 03J;
Task 04B closed as a no-op. Task 06H accepted the repaired review and handoff
with sampled-coverage limitations. Downstream work pins the matching extraction,
review, and handoff identities rather than combining parts from different
lineages. [Task 06H](../../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
owns the exact replacement correspondence.

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
pipeline produces a canonical structured or textual representation and the
accepted review registry's
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

Preserve general responses as canonical units only within the curator-only Task
05 namespace, with their own IDs and anchors. Final EIR Volume 4 is not part of
the Task 03 model corpus or accepted Draft EIR extraction release. Task 05 may
reuse maintained producer components where suitable, but its bounded extraction
or transcription route, identities, and acceptance records remain separate.
For every response that refers to a general response, also produce a derived
resolved review view that includes the referenced general-response text, ID,
and source anchor with the individual comment-response pair. This view must be
independently reviewable without erasing where the incorporated text came from
or altering the curator-only source transcription.

Validate the relationship graph in both directions. Flag every identifiable
comment with no response as an orphan for human review, and flag every general
response that is not linked to at least one comment or individual response.
Record whether each apparent orphan is a source omission, extraction failure,
unresolved cross-reference, or legitimate document structure. Do not silently
drop unmatched units.

Construct the Task 05 inventory deterministically from document structure,
source IDs, headings, and explicit cross-reference patterns, with manual
resolution of ambiguous cases. No LLM creates, segments, links, or triages
that accepted inventory. Task 07A uses direct human review of accepted
comment-rooted cases for pilot fit; screening does not change Task 05 records.

Task 05's accepted curator-only inventory is owned by the
[Task 05 umbrella](../../tasks/sprint2/05_build_curator_only_response_inventory.md)
and [Task 05H outcome](../../tasks/sprint2/05h_review_and_freeze_response_inventory.md).
Its source, relationship, linking, review, and publication details live in those
completed task records. The [accepted release](../specs/task05h_final_result.json)
is the Task 07/08 input; it does not itself establish case eligibility or
evidence sufficiency.

Use replaceable working space and bounded pilots for iteration; do not seal
every experiment. Routine Task 05
validation pins the Task 02 source checksum and Task 03J/04A/04D identities
through compact completion metadata without rehashing or copying their large
payloads. Hash newly authored authoritative Task 05 records once at final
publication, preferably while writing them, and reserve a full byte audit for a
specific integrity concern or separately approved archival boundary.

### Task 08 eligibility, clustering, and split boundary

Begin question selection with the exclusive groups in
[Decision 005](../decisions/005_task08_grouped_question_selection.md). Kyle reviews
under the amended all-selected 08B policy, which permits more than three
questions per group. This purposive selection retains the subsequent human
eligibility requirements. The
2026-09-30 amendment makes the final size and split flexible, with explicit
agreement before freezing. See the [Task 08 umbrella](../../tasks/sprint2/08_curate_grouped_benchmark.md)
for reusable stages, context boundaries and question-by-question 08E chat review.
08A preparation may cover all remaining accepted groups ahead of review under
the explicit preparation amendment. Groups with at most three candidates use
stable comment-ID order without model ranking; larger groups use saved advisory
Astra order. This does not advance selection, authoring or eligibility gates.

Human reviewers alone determine candidate eligibility. Deterministic checks
may flag language, source references, or missing links for reviewer attention,
but they do not accept or reject cases. Exclude an entire comment-response case
when answering its scoped question materially depends on a later revision, new
Final-EIR analysis, external evidence, a mitigation change, unusable source
content, or visual evidence unavailable to the target model.

For the next authoring pass, one original comment yields at most one case with
one independently answerable, human-approved question. Distill or rewrite only
when the question faithfully preserves the comment's central issue, scope and
qualifications. If it contains multiple independent asks that cannot naturally
be expressed as one question, leave the proposal unresolved and discuss the
obstacle before the human decides. Do not split it into several cases or hide
the multiple asks in a compound sentence. No automatic exclusion or forced rewrite.
Do not remove a difficult qualification merely to make the case answerable.
Preserve the original comment, the exact question, source IDs and the rewrite/skip
reason. Freeze that same question as retrieval, generation and evaluation input.
The six pilot comments reenter this process with new Task 08 decisions, including
selection and separate comment-only wording review. Their sealed Task 07
questions, claims, and answers remain unchanged; no old approval substitutes
for a current gate.

Use the shared `task08.selection_gate.v2` process. During 08B, the curator
reviews the original comment and complete linked responses and saves a selection
decision and reason; explicit selection is the sole 08B human gate to 08C.
Eligibility concerns may go in the reason, without a separate provisional label.
The `task08b.selection.v2` form omits warning, advisory-reason and ranking-record
panels while underlying artifacts retain all source limitations and exceptions.
It has no stopping control: confirm review completion in chat at export and
reconcile saved annotations against the full inventory, leaving unanswered
candidates unreviewed. Preserve skips, exclusions, unresolved decisions and
reasons; at most three selections are permitted, and fewer are welcome.
Question rewriting and exact wording approval follow in a separate comment-only
chat using [task08c.chat_review.v1](../specs/task08c_chat_review_v1.md). Preserve
displayed versions and feedback; a null proposal remains unresolved pending human
discussion. Only explicit approval of the exact displayed version can freeze text.
Flag unsupported user-added intent; no automatic exclusions or backfill. Astra may rank original candidates beforehand, but saved advice neither
selects nor rejects cases. At 08E, the curator conducts evidence-based eligibility
review using the original comment, resolved response, exact Draft EIR evidence,
requested review-cache renders, source usability and relevant cross-references.
Selection alone never establishes final eligibility or acceptance.

Preserve every screening, evidence-verification, acceptance, and selection
decision as a versioned record rather than overwriting earlier
dispositions. Each decision records the stable source or case ID, review stage,
disposition, reason code, reviewer, timestamp, and the input artifact version
that was reviewed. Produce an annotation attrition waterfall with raw counts at
each stage—from the complete response inventory through plausible candidates,
explicit selection, question/claim review, evidence-based eligibility, accepted
cases, and final split
selection—and report exclusions by reason code. The waterfall is an audit
summary derived from the decision records, not a separately maintained count.

Selection reasons remain provenance and do not substitute for the later
evidence-based decision. Report this as single-curator review, not inter-reviewer
agreement. Model eligibility QA remains out of scope for Sprint 2 and cannot
substitute for human eligibility review.

Accepted 2026-10-09 amendment: Kyle approved retaining all 49 reviewed cases
separately and distributing related topics across a 19-development / 30-test
split. The whole question pool and the closest answers were reviewed; none were
identified as needing merger. Thirteen overlapping topic families guide coverage.
C002 remains in test, as does every appendix cited by only one case. Citation
balancing uses distinct cited section/table units per answer, including optional
context. This counting choice does not change support/context scoring roles.

The [08G contract](../../tasks/sprint2/08g_review_case_clusters.md) owns the bounded
similarity review and its limitations; [08H](../../tasks/sprint2/08h_serialize_and_freeze_benchmark.md)
owns exact approved allocation and final publication. The user's amendment
supersedes mandatory relationship enumeration, duplicate fixtures, Astra cluster
proposals and keep-together connected components for this release. Those
provisional procedures were not performed; their contracts remain preserved as
history. No exhaustive semantic-independence claim follows from this review.

Shared sections and related reasoning may cross development/test. The strongest
recorded overlaps include drainage/flooding, bicycle safety and traffic diversion.
Topic balancing improves coverage but can test application of familiar evidence
to different questions; it is not an unseen-topic or unseen-evidence evaluation.
Preserve these limitations in the release and downstream reports. Later discovery
of duplication requires a named revision, not an implicit split change.

Task 03 source cross-references and Task 05 curator-only response relationships
remain separate provenance structures. Neither shared targets nor graph proximity
creates an automatic Task 08 dependency or merger. No new authoring or evidence
approval is inferred from the allocation decision.

Keep test locking lightweight for the MVP. Save and hash the accepted cases,
split manifest, and frozen retrieval, prompt, model, and judge configurations
before the primary test run. Keep test-reference fields out of target-model
inputs through the artifact schema, but do not build a permissions system,
special access workflow, or elaborate CLI lock. Record later configuration
changes as new named runs rather than replacing the primary result.

### Model-assisted reference-case authoring

Task 07 first screens **at least 50 distinct comment-response pairs** from the
accepted Task 05H inventory for pilot fit. In a focused Label Studio project,
the curator reviews every pair and assigns `great_fit`, `ok_fit`, or
`skip_for_pilot`, with multiple reason codes where useful. Codex may propose
ratings, but only the human disposition counts. Preserve selection coverage,
ranking or priority groups, reasons, and counts. Select a small, varied set of
great fits (initial target 6–10) for exploratory authoring; expand the screened
batch if it yields too few. Pilot fit does not establish Task 08 eligibility or
replace its fresh selection, authoring and evidence-based eligibility reviews.

Each selected case then passes through four authoring reviews:

1. **One comment question:** approve a faithful single question or skip the case.
2. **Claims and relevance:** state substantive response claims clearly and review
   whether they answer or materially support an answer to that question. Preserve
   excluded claims in history rather than carrying them into evidence discovery.
3. **Evidence:** review source sections/tables and retain separate deduplicated
   support/context citation pools, source judgments and explicit gaps.
4. **Reference answer, including reasoning (combined 07E/07F):** review one concise
   answer that gives the conclusion, necessary supporting explanation, conditions
   and limitations. An internal draft outline is optional; there is no separately
   approved outline, reasoning map or subsequent polished-answer labeling pass.

The final answer and reviewed source pool provide the reference for later answer
adequacy judgments. They are not exposed to the target and do not establish truth
merely by being authored. Retain exact source provenance and point-to-citation
links in the structured answer under Decision 006; no duplicate claim inventory.
For each stage, prepare a bounded input batch and prompt for a separate Codex
task. The user starts that task through existing app access. Small code helpers
validate and import its proposals, export human annotations, and prepare only
approved outputs for the next stage. There is no paid API integration or live
model backend requirement for this pilot. Preserve source and case IDs, prompt
and form versions, selected model, input batch, model proposal, and curator
edits. A stage may repeat under a new named revision as its review criteria
improve. A rejected or unresolved stage never advances silently.

Build candidate evidence through reproducible curator search, separate from
the later top-five benchmark retriever. Resolve the official response's
explicit Draft EIR references first, then search usable corpus text using the
comment, response, and reviewed assertions. Search may fan out by assertion;
merge candidates for case-level review. Preserve distinct provenance for
response-explicit, lexical, and any graph-discovered evidence, along with
which Codex task proposed a span and the curator's disposition.

The evidence proposal is closed over that supplied candidate pool. Its schema
may select only canonical evidence IDs present in the input; it may not
invent page references, quote unseen passages, or request arbitrary source
IDs. For each selected span, require a short relevance explanation and a
classification of direct support versus contextual material. The schema must
also permit an explicit `insufficient_evidence` result. Validate all returned
IDs mechanically before presenting the proposal for curator review.

Contextual spans may remain in the curation packet to explain terminology,
scope, or cross-references, but they do not count as reference evidence and
cannot independently justify a claim. Every substantive step in the
curator-approved answer logic and reference defense must be supported by the
reviewed evidence, with explicit point-to-citation output links under Decision 006. Retrieval coverage metrics score only
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

Require curation and target models to return one structured answer with explicit
point-to-citation links, using only citation IDs supplied in their respective
inputs. No duplicate claims list or parallel prose answer is required. Deduplicate reference
citations within each case by canonical section/table identity and retain
`support` over `context` across reviewed uses. Direct and supporting claim roles
do not create different citation levels. Context-only citations remain optional
for required coverage. The [07D export contract](../specs/evidence_review_v1.md#case-level-citation-export-decision-2026-09-28)
owns exact aggregation and review-provenance rules. Render those IDs
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
accepted Task 03 extraction identity, accepted review-registry version,
Task 05 inventory version, and Task 08 case/split versions. Human-readable
document and section slugs may remain recognizable across versions, but they
do not replace content and configuration checksums.

Present the target model's five retrieved passages in BM25 rank order. Each
record includes an anonymous passage ID, human-readable document or appendix
and section metadata, printed and PDF page locations when available, and the
passage text. Do not expose numeric retrieval scores, gold-evidence overlap,
curator labels or dispositions, official-response discovery provenance, or QA
notes, printed-label confidence, unresolved candidates, or usability
diagnostics. Unusable source content is excluded before retrieval rather than
marked for the target. Rank conveys ordering; the model receives no gold
annotations.

Retain the secondary evidence-only oracle `A`: the same scoped question plus
curator-approved source citations/text, without the reference answer or authoring
notes. Run the primary question-plus-five-BM25-passages baseline first; preserve
anonymous condition IDs and blinded evaluation. Do not blend oracle results into
the primary score. Baseline-to-A differences diagnose retrieval/evidence-selection
limits, without claiming a clean causal separation of every failure mode.

The previously proposed `A+B` reasoning-summary diagnostic is deferred. Combined
07E/07F no longer produces an independently approved non-answer summary, and
supplying its reference answer as B would leak the answer. A replacement scaffold
requires a separate explicit design decision; this plan creates no additional
outline review to preserve that diagnostic.

Do not freeze a 200-word defense limit before the annotation and target pilots.
Test at least 200- and 400-word limits against varied reviewed reference cases,
including long official responses, and select the smallest limit that permits
a complete concise Draft-EIR-only defense without forced omission. Apply the
same frozen word and statement limits to the primary baseline and the evidence-only oracle
condition; exclude deterministically rendered citations from the word count.
If 400 words is still inadequate for a complete pilot case, stop for a new
length decision rather than silently truncating the answer or reference.

Use a zero-shot fixed prompt for the initial target baseline. It contains the
task instruction, structured output schema, citation and abstention rules,
frozen human-approved single question, and the five retrieved passages. Do not include
completed development reference defenses or other benchmark cases as few-shot
examples. Any later few-shot prompt is a separately named secondary condition
and cannot replace or retroactively modify the primary baseline.

Run the target at temperature `0` with a fixed seed where supported and record
the model digest, prompt hash, schema version, context, and runtime settings.
Generate three baseline repeats for each case in the Task 08 development split and
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
anchors. Build units only from accepted-review-registry body content and tables;
never span excluded content. Before building the development index, analyze and
report the leaf-section length distribution by source document, including
outliers and the combined size of five large results relative to the target
context budget.

Proceed with whole leaf sections only if that analysis shows usable and
reasonably bounded units. If lengths are too variable, appendices lack useful
heading structure, or large sections would exceed the context budget, pilot a
fixed-length, contiguous, structure-preserving fallback within section
boundaries. Do not split all sections by default, cross semantic or excluded
content boundaries, or choose a fallback size without recording the length
evidence that required it.

Index each retrieval unit's full canonical heading path together with its body
text because section and appendix headings may contain important topic terms
that are not repeated in every paragraph. Show the same heading path to the
target as source metadata. Exclude repeated page headers, footers, page
numbers, and generic document boilerplate from indexed text.

Use only the exact frozen single question as the primary BM25 query. Do
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
`without`. Select using support-unit retrieval recall at five; if results
are effectively tied, prefer the simpler plain candidate. Save the tokenizer
configuration, vocabulary, stemmer package and version when used, and exact
stopword list with the index artifacts.

Define retrieval recall at five over the distinct reference supporting citation
units actually returned to the target in its five-passage context. A searched
file, corpus membership or a hit elsewhere in the document is not a retrieval hit.
Match frozen document/extraction/section-or-table identities and their canonical
anchors, not titles or semantic similarity. A fragment cannot claim a whole section
solely by inheriting its parent ID: required reference anchors must be present in
the returned material; Task 10 freezes the deterministic projection for fallback
fragments. Keep section and table units distinct and deduplicate repeated hits.
The metric definitions below own support/context handling and final-answer scoring.

Save the top 20 ranked results/scores as diagnostics; only ranks 1–5 reach the target.
Report recall at 1/3/5/10/20, with recall at 5 primary. Deeper-list recall is diagnostic,
not credit for material the target saw. If future multi-query retrieval is approved,
log and score the union actually returned within that condition's fixed budget;
this does not authorize query expansion in the current single-query baseline.
Report complete-case recall, raw hits/denominators and per-case results. When a
reference pool exceeds the unit budget, report its achievable recall ceiling;
do not silently increase the budget or treat a ceiling as reasoning failure.

Use BM25S's maintained default Lucene-style scoring method and default scoring
parameters. Record the exact BM25S version, method, and parameters with the
index, but do not run a parameter sweep on the development cases. Restrict
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

Start with recorded lexical searches from the original comment, resolved
response, reviewed assertions, and explicit source references. Merge and
deduplicate candidate IDs before Codex evidence proposals. If reviewed gaps
show that these searches missed needed evidence, a named revision may add
recorded query expansion or a deterministic traversal/index view over accepted
Task 03 cross-references. Task 07 does not re-extract or re-resolve references.
Any traversal uses only resolved edges to usable targets, records its full
path and limits, and stops at two explicit-reference hops. Unresolved mentions
remain search or manual-review signals, not graph edges. Accepted evidence
always needs exact canonical anchors, regardless of how it was discovered.

### Model roles

Keep curation, target generation, and automated judging as distinct model
roles. Use Astra (`gpt-6-astra`) through the user's existing app allowance for
all model-assisted dataset-label authoring, including proposal drafting and
revisions. Record the actual model, task, prompt and input/output provenance;
human review determines label acceptance. Human-only stages remain human-only.
Kyle removed the local/no-extra-cost authoring-model comparison from Task 07G;
Kyle then closed 07G and accepted grouped Task 08 question selection without
another pilot round or a full retrospective. No LLM judge is
part of Task 07. Use pinned
`qwen3:4b-instruct-2507-q4_K_M` as the intentionally small initial target
baseline in later tasks. Use `gemma3:12b` through Ollama as the initial local judge
candidate, subject to Task 09B qualification and exact digest pinning. Any smaller-judge comparison is optional development work; it does
not authorize a new human-labeling pass. Under Decision 006, report uncalibrated
automated judgments unless a separate human calibration is actually completed.

Resolve and record the exact local-model digest for every local run rather than
relying on mutable tags. Local inference avoids per-token API charges but does
not remove the need to record runtime, structured-output failures, and evaluation
limitations. A later target-model comparison may test other model sizes or
families against the same frozen benchmark without changing the reference cases.

The canonical case preserves the exact original comment and its provenance,
alongside the frozen human-approved single question. The target, primary retriever,
human evaluator and automated judge receive that same scoped question. The original
comment remains available for authoring/provenance checks, not additional unasked
requirements in answer scoring. Do not expose official responses, reference answers,
reviewed claims/citations, relevance labels or curator rationales to the target.
Existing multi-concern MVP records remain unchanged until explicitly migrated;
do not mix question versions across target and judge inputs.

## Execution sequence

### Accepted inputs

- [Task 03J](../../tasks/sprint2/03j_run_final_canonical_extraction.md)
  owns the immutable 35-source machine extraction.
- [Task 04A](../../tasks/sprint2/04a_regenerate_review_and_freeze_release.md)
  owns the original usability review; [Task 04D](../../tasks/sprint2/04d_relink_frozen_extraction.md)
  owns the original linking handoff.
- [Task 06H](../../tasks/sprint2/06h_review_and_accept_replacement_handoff.md)
  owns the accepted repaired handoff and sampled-review limitations;
  [Task 06](../../tasks/sprint2/06_repair_reference_sources_and_target_index.md)
  routes its completed subtasks.
- [Task 05G](../../tasks/sprint2/05g_replay_and_extend_official_reference_links.md)
  owns the accepted reference replay; [Task 05H](../../tasks/sprint2/05h_review_and_freeze_response_inventory.md)
  owns the sole immutable curator-only response inventory and its
  [Task 07/08 handoff](../specs/task05h_final_result.json).

All of these tasks and Tasks 07–08 are complete. The
[frozen Task 08 release](../specs/task08h_final_result.json) contains the approved
49-case pool and exact 19/30 allocation.
Exact identities, negative results and validation evidence remain in the numbered
task records. Later tasks require separate authorization.

### Remaining task sequence

1. **Task 07 — Pilot reference-case authoring (closed).** Screen at least 50 accepted
   comment-rooted cases with complete response context through human-only review,
   then take a small varied subset through reviews for
   one scoped question, claims/relevance, evidence, and a combined reference answer
   with its reasoning (07E absorbs 07F). For those later authoring
   stages, Codex proposes bounded batches in separate tasks; the curator reviews
   each stage. Astra supplies model-assisted proposals; Kyle closed 07G and
   chose to proceed to Task 08 without another pilot round or full retrospective. The
   [Task 07 umbrella](../../tasks/sprint2/07_pilot_reference_case_authoring.md)
   records the closed pilot's outcomes and handoff.
2. **Task 08 — Curate, balance, split and freeze the benchmark.** The
   [umbrella](../../tasks/sprint2/08_curate_grouped_benchmark.md) routes completed
   authoring and the amended 08G/08H closeout. Retain all 49 approved cases in the
   exact approved 19/30 allocation. Validate provenance, source and role separation,
   approved split membership and documented overlap limits before sealing. No
   retrieval, generation or judge run belongs to this task.
3. **Task 09 — Evaluation components and judge freeze: complete.** Automatic
   retrieval/citation metrics and independent A/G/S/C judges are established.
   Luna A v2 / G v3 / C v8 and Haiku S v6 are selected through native Inspect.
   [09F.2](../../tasks/sprint2/09f2_cleanup_production_judges.md) completed code
   consolidation; [09G](../../tasks/sprint2/09g_challenge_and_freeze_judges.md)
   freezes the committed configuration and existing evidence as documentation only.
   Kyle explicitly replaced the provisional extra challenge/rerun requirement.
   No new reserved-development check or held-out qualification is claimed.
   Keep proposed-label uncertainty and known failures explicit. Task 12 owns
   whole-answer routing, aligned joins and strict combined reporting.
4. **Task 10 — Build and freeze BM25 retrieval and evidence presentation.** Build
   units from accepted hierarchy and accepted-review-registry body content and
   tables. Analyze lengths, choose whole sections or a documented contiguous
   fallback that never spans excluded content, run the lexical preprocessing pilot,
   freeze the index, and report development-only evidence-coverage curves. Pass
   the top five results directly to the target with actual section/table content,
   citation IDs, document titles and heading paths; retain table headers, units
   and footnotes. No generated section summaries or model result-selection call.
   Agentic search remains a later separately scoped condition.
5. **Task 11 — Build and freeze target generation.** Pin the full extraction,
   usability, case, split, index, prompt, model, and schema identity chain.
   Implement the zero-shot Qwen3 4B prompt, abstention and citation validation,
   deterministic source-label rendering, output-length pilot, and development
   stability check without exposing curator-only or QA metadata. Timebox this
   work to three days around one baseline, not open-ended model optimization.
6. **[Task 12 — Integrate evaluation and reporting](../../tasks/sprint2/12_integrate_evaluation_and_reporting.md).** Apply the existing
   evaluator and judge to real development target outputs, verify the complete
   identity chain and input separation, and confirm the final configuration freeze.
   Define no-answer routing integration, exact G/S/C joins, aggregate statuses and
   denominators, and strict all-grounding-pass AND S-pass AND C-pass reporting.
   This is a small integration check, not a second judge-development project.
   Record any substantive fixes and repeat affected development checks before
   test use. No additional full labeling pass is required.
7. **Task 13 — Run the locked test and close Sprint 2.** Verify the complete
   identity chain before execution. Run the primary baseline first, then the
   pre-registered evidence-only `A` oracle diagnostic; preserve all four results
   separately, report automated-judge limitations, analyze errors by stage,
   and make the second-project decision.

### Task 09 synthetic challenge scope

[09A](../../tasks/sprint2/09a_create_synthetic_challenges.md) owns the complete
perturbation catalog, record schema requirements, bounded alternative-argument
discovery, restartable generation plan and coverage acceptance. Use only the
19 development cases; retain positive invariance checks, meaningful partial-credit
and central failures, and as many applicable perturbations as useful without
contrived combinations or a fixed eight-variant cap. Preserve exact edits,
intended effects, proposed G/A scores and evidence-based justifications separately
from judge-visible answers. These are model-proposed expectations, not human gold.
09A reserved final-check variants before prototype tuning. Those historical
reservations remain preserved; the documentation-only 09G freeze does not evaluate
them or claim an untouched final check. Existing development results remain
uncalibrated automated judgments; the benchmark test cases stay untouched.

## UI and artifact boundary

Docling Serve's UI is a convenience for conversion spot checks. Keep three
artifact layers explicit: preserved producer output, immutable canonical
records, and regenerable review cache. Canonical extraction evidence is the
saved producer and canonical output plus machine validation records, not the
presence of renders. Task 04 and Task 04A use the small read-only local
HTML workspace and durable finding register. Label Studio remains the planned
human-review surface for the later benchmark annotation/evaluation contract; it
does not replace their extraction-review workspace. A deterministic export
converter produces benchmark JSONL pinned to accepted artifact identities. Raw
PDFs, converted text, renders, indices, local models, and runs remain under
`ER_COMMONS_DATA_ROOT`, not Git.

## Benchmark evaluation boundary

The accepted [2026-10-16 grounding simplification](../decisions/006_structured_answers_four_part_evaluation.md#grounding-simplification--2026-10-16)
supersedes the conclusion-grounding, conclusion-citation requirement and grounding
0/1/2 rules below. The completed 09F/09F.1 components use a three-way no-answer
classifier and binary G/S/C decisions; the 09G manifest owns their frozen identities.
The earlier ordinal judge rubrics below are historical. Supporting-point grounding,
S and C run independently; reporting adds their strict conjunction while preserving
the separate results. Legacy results/releases remain preserved; obsolete
execution paths were retired in 09F.2. [09F.1](../../tasks/sprint2/09f1_revisit_grounding_judge.md)
establishes no-answer and grounding components; [Task 12](../../tasks/sprint2/12_integrate_evaluation_and_reporting.md)
owns routing integration and combined reporting. No automatic-metric change or
provider run follows this plan update.

Accepted revision 2026-10-08: [Decision 006](../decisions/006_structured_answers_four_part_evaluation.md)
locks four separate results: automatic retrieval recall, automatic final-citation
precision/recall/F1, LLM grounded correctness and LLM answer adequacy. Use one
structured, cited reference answer, approved in 08F, as both the answer and the
adequacy guide. No duplicate prose answer or later essential-points labeling.
Task 09 implements and freezes this design before benchmark execution.

### Structured answer output

For `answered`, return a direct conclusion, essential supporting points and
material qualifications attached to the points they constrain, each with citation
links. Optional context is separate. Derive the citation set from those links;
do not require a duplicate model claims list or flowing-text answer. The reference
and target use this general structure, not identical point counts or wording.
Use `insufficient_evidence` for abstention; unsupported substantive assertions
cannot be shielded from grounding evaluation by an abstention status.

### Automatic citation metrics

Use sets of canonical section/table units within each case; keep invalid citation
attempts in a separate set:

- `S`: reviewed support units; `C`: reviewed context-only units, disjoint from `S`.
  A unit used as support anywhere in the reviewed case belongs to `S`.
- `R`: units actually returned to the target within the recorded retrieval budget.
- `A`: units explicitly cited by the final model output, not everything retrieved.
  Point-to-citation links declare sources used by the structured answer; repeated
  IDs count once for these metrics while their individual links remain auditable.
- `U`: distinct invalid/unresolvable citation attempts, represented by stable raw
  identifier tokens. They cannot match support/context units.

**Retrieval recall** is `|R ∩ S| / |S|`. It measures whether supporting sources
reached the model, including results across queries only in a separately approved
multi-query condition. Searching a document does not count as retrieving every
reference unit inside it. Keep the existing top-five baseline and report deeper
ranked results as diagnostics only.

**Final-citation recall** is `|A ∩ S| / |S|`.
**Final-citation precision** is `|A ∩ S| / (|A \ C| + |U|)`.
**Final-citation F1** is `2 × precision × recall / (precision + recall)`,
using the final-citation metrics above, not the retrieved-unit set `R`.
Known context citations are neutral: they neither satisfy required recall nor
count as false positives. Valid but unmatched citations stay in the precision denominator; invalid attempts
enter through `U` and are flagged by mechanical validation, never silently
discarded to improve precision. Deduplicate
invalid repeated identifiers as well. If `S` is nonempty but the scored final
citation set is empty (`A \ C` and `U` both empty, including context-only
output), define precision/recall/F1 as `0`. If `S` is empty, required
citation metrics are not applicable; report that case separately. F1 is `0` when
precision and recall are both `0`. Record numerators, denominators, optional-context
counts and per-case scores; aggregate as separate macro/micro reports with explicit
eligible case counts rather than a single blended benchmark score.

These are reference-set matching metrics, not proof of correctness. Alternative
valid evidence missing from the authored reference can lower measured precision;
preserve it for error analysis or separately authorized human review without
silently editing the frozen test reference. Likewise, all right citations can accompany a reversed conclusion or
unsupported inference. Automatic citation scores do not establish logical use.
Canonical-ID/anchor projection, schema validity, allowed corpus and citation
resolution remain deterministic checks independent of the two judgments below.

### LLM answer judgments

**Adequacy update (2026-10-14):** The maintained
[adequacy labeling rules](../specs/adequacy_labeling_rules.md) now own adequacy
semantics and supersede conflicting adequacy text below, including abstention=0,
partial conclusion credit and alternative substantive answers. The historical
runtime has not migrated. The rules retain separate conclusion/support decisions,
derive 0/1/2, and skip semantic judging for explicit abstentions; denominator policy
is deferred. Grounding and automatic metrics remain unchanged. The new adequacy
request/diagnostic schema must be specified before implementation.

Score both dimensions per complete answer on an anchored `0`/`1`/`2` rubric.
Statement-level observations remain diagnostic explanations, not a third score.

1. **Grounded correctness:** do the cited sources justify the claims, conclusion
   and visible reasoning, with their essential qualifications? `2`: supported,
   logically justified and appropriately qualified; `1`: partly supported or
   contains a material overstatement/unsupported step; `0`: central conclusion
   contradicted, unsupported, or not established by the cited material. Do not
   infer hidden reasoning or trust a citation merely because its ID matches.
2. **Answer adequacy:** does the whole answer address the exact scoped question
   and include the essential findings/conditions needed for a complete answer?
   `2`: substantively correct, direct and complete; `1`: partial, indirect or missing an
   important element; `0`: misses or materially misframes the central question.
   The reviewed reference guides substantive expectations, not wording, order,
   length or exhaustive citation reuse. Accept valid alternative explanations.

These are whole-answer partial-credit scores, not fractions of correct points.
A wrong central citation with no remaining cited justification can earn grounding
0 even for a true conclusion; an unsupported secondary point generally earns 1
when the remaining citations independently establish the conclusion. Never repair
the answer by substituting the source it should have cited. A correct conclusion
missing essential explanation generally earns adequacy 1; missing optional context
has no penalty. Follow [Decision 006](../decisions/006_structured_answers_four_part_evaluation.md#partial-credit-and-wrong-citations).
Report mean scores and 0/1/2 distributions with applicable denominators.

One omission can affect both dimensions for different reasons: removing a critical
condition can make the conclusion unsupported and the answer incomplete. Explain
both judgments rather than forcing mutually exclusive error categories. Neither
judgment requires every reference citation to appear in the answer.

Target output follows the structured format above. On the answerable
benchmark, abstention has grounded correctness not applicable and adequacy `0`;
report it separately. Automatic retrieval/citation metrics still reflect what was
actually returned/cited. Attribute abstention to retrieval or generation limits
using the recorded evidence context; do not call unsupported absence claims a
successful abstention.

### Two judge calls and diagnostic output

Grounded correctness receives the scoped question, model structured answer and
actual cited passages. Hide the reference answer, gold support/context roles,
citation matching scores and target identity. The question is necessary to check
application to the right scenario; this is not an essential-point coverage check.
Save this judgment independently before revealing reference material.

Answer adequacy receives the same question and model answer, structured reference
answer and reviewed source pool, plus the model's cited evidence for assessing
alternatives. Check essential substance and necessary qualifications, not wording,
point count or exhaustive citation reuse. Neither judge may use official-response
claims as evidence. Do not overwrite the grounding result with reference-based
judgments. Keep automatic matching scores and target identity hidden from both.

Both dimensions can fail for the same false explanation. A true but incomplete
answer can pass grounding and fail adequacy. Missing scope conditions can affect
both; merely missing an additional useful point does not make an otherwise
supported assertion ungrounded. Statement-level diagnostics identify exact model
points, source passages, unsupported or contradicted steps, and omitted material
qualifications. Adequacy also identifies missing essential reference points.
These are automated explanations, not further gold labels or primary scores.

### Judge qualification and labeling budget

08F is the last planned substantive case-labeling pass. No mandatory human
prediction-labeling or human calibration pass follows it. The earlier 80-percent
agreement/endpoint/flag-recall gate and mandatory human review of all test outputs
are superseded by Decision 006, not silently considered satisfied.

Without separately authorized human calibration, report the two judge scores as
**uncalibrated automated judgments**. Pin model, prompts, schemas and exact inputs;
run bounded automated development checks for evidence sensitivity, reversed
conclusions, dropped conditions and valid paraphrases. Such checks do not measure
human agreement. Do not tune on locked-test outputs. Preserve every judgment and
its dimension-specific evidence explanation, uncertainty and execution failures.
Any future human calibration requires separate authorization and its own real
labels before agreement statistics can be reported. Reference incompleteness and
judge error remain explicit limits; reference-answer approval is not judge validation.

## Completion gate

Sprint 2 is ready for a second-project decision only after the Task 08-agreed
locked test run is reproducible, citations resolve, automated-judge qualification
and its uncalibrated status (unless separately calibrated) are reported, and error
analysis identifies the limiting stage.
