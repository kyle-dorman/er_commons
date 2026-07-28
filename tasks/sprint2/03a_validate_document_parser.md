# Task 03A: Validate the Document Parser and Extraction Configuration

Status: **completed and accepted 2026-07-28; Task 03B remains inactive**.

## Abstract

Validate Docling as the canonical-extraction engine on a small, deliberately
heterogeneous set of Brisbane Draft EIR pages before defining the project's
canonical schema or attempting full-document conversion. Compare Docling's
native-text, layout, table, figure, and provenance output with a transparent
native-PDF baseline, inspect representative failure modes, and freeze a
preliminary parser choice and configuration. Do not use OCR, a VLM pipeline,
an LLM repair step, or a remote parsing service.

## Goal

Establish evidence that the selected parser can expose the structural and
provenance primitives needed by the benchmark, and identify the configuration
and known limitations that the remaining Task 03 subtasks must preserve.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `docs/sprints/sprint2_brisbane_draft_eir_defense.md`
- `tasks/sprint2/02_freeze_sources_and_provenance.md`
- the sealed `records/source_manifest.json` from
  `brisbane_baylands_2025_deir_sources_v1`
- the 35 checksum-pinned `model_corpus` PDFs named by that manifest
- current primary Docling documentation, technical reports, model cards, and
  release metadata

## Outputs

- a tracked, reviewable pilot specification identifying the selected source
  documents and page ranges, selection rationale, and expected stressors
- small checked-in synthetic fixtures only where they are needed to test
  project-owned assumptions; real converted pages remain outside Git
- raw external pilot outputs sufficient to inspect text, reading order, block
  labels, tables, figures, bounding boxes, and page provenance
- a compact comparison matrix between Docling and one maintained native-PDF
  baseline
- a pinned exploratory Docling dependency/model set and explicitly recorded
  candidate configurations, or a documented stop decision if Docling does not
  expose the required primitives
- measured runtime, memory, and artifact-size observations for the pilot

## Research / learning checkpoint

Read the [Docling technical report](https://arxiv.org/abs/2408.09869), current
[architecture](https://docling-project.github.io/docling/concepts/architecture/),
[document model](https://docling-project.github.io/docling/concepts/docling_document/),
and [pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/).
Inspect the exact layout and table-model identities selected by the installed
version rather than treating `docling` as one indivisible parser. Use
[pypdf's explanation of PDF text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
and the selected baseline's primary documentation to distinguish native glyph
recovery from learned document-structure inference.

The outcome must explain these document-AI concepts at a senior-engineer level:

- A PDF content stream encodes rendering operations, not a canonical semantic
  tree. Text recovery, reading-order inference, region classification, table
  reconstruction, and hierarchy induction are distinct estimators with
  different failure modes.
- Layout detection metrics such as region-level precision, recall, or mAP do
  not directly measure whether the serialized reading order or downstream
  evidence anchors are correct. Evaluate the task-facing composition, not only
  a model card's component score.
- Table detection, cell matching, spanning-cell reconstruction, and conversion
  to text or HTML are separate problems. A visually plausible table can still
  have incorrect topology that changes the meaning of rows and columns.
- Native-only extraction does not mean rule-only extraction. Docling can use
  learned layout and table models while OCR remains disabled; the text tokens
  still originate from the embedded PDF text layer.
- Parser comparison without complete ground truth should use a designed stress
  sample, explicit error dimensions, and preserved raw evidence. It should not
  collapse heterogeneous failures into an unsupported aggregate accuracy
  number.
- Parser errors become retrieval and evaluation errors later. Reading-order
  corruption changes passages, missing headings remove retrieval terms, and
  bad bounding boxes make otherwise correct citations unverifiable.

The comparison must include at least:

- ordinary single-column narrative;
- multi-column or side-by-side layout;
- repeated headers, footers, and page numbers;
- nested headings and lists;
- a structured table with merged or multi-line cells where available;
- a figure, caption, and surrounding prose;
- a page dominated by visual material;
- a long or structurally difficult appendix page; and
- at least one source carrying a Task 02 parser warning.

## Plan / spec requirement

Write a brief pilot plan before installing or running Docling. It must specify:

1. the page-selection matrix and why each page probes a distinct failure mode;
2. the native baseline and the narrow question it answers;
3. the structural-fidelity dimensions to inspect;
4. how raw outputs, renders, timings, and observations will be stored;
5. the preliminary Docling options, with OCR, remote services, VLM conversion,
   picture description, chart interpretation, and LLM repair explicitly off;
6. the exact dependency and model versions to record;
7. the `accept`, `revise configuration`, and `reject/split` decision criteria;
   and
8. how experimental dependencies will be retained or removed after the
   decision.

Do not tune against many pages until the selected sample looks good. A single
configuration should be evaluated across the fixed pilot set so configuration
changes cannot quietly chase each document.

## Pilot specification

Accepted for implementation planning on 2026-07-27, before adding Docling or
downloading model artifacts. The machine-readable selection is
`configs/brisbane_baylands_2025_deir_task03a_pilot_v1.json`.

### Decision boundary

The pilot asks whether one local, native-text-only Docling configuration
exposes enough raw document structure and provenance for Tasks 03B through
03E. It does not ask whether Docling's Markdown looks polished or whether the
parser can recover pages that require OCR. Inspect the `DoclingDocument` and
raw conversion objects directly; serialized Markdown or HTML may be useful
diagnostics but cannot be the canonical evidence.

The transparent baseline is the already locked `pypdf==6.14.2`. For each pilot
page, save its ordinary and layout-mode native-text extraction. This baseline
answers whether embedded PDF text can be recovered and gives a second view of
text order. It is not a competing layout, hierarchy, figure, or table model and
must not be scored as one.

### Fixed page-selection matrix

All `pdf_page` values are one-based physical PDF page numbers. Printed labels
are observations to verify from the page render, not input coordinates.
Together the selections contain ten physical pages from four
checksum-pinned `model_corpus` sources.

| Source ID | PDF pages | Printed label | Stressors and pilot question |
| --- | ---: | --- | --- |
| `deir_main` | 44 | ES-2 | Figure ES-1 followed by nested headings and three-level lists, with repeated furniture. Are the figure, caption, source, headings, and list nesting distinct and ordered? |
| `deir_main` | 45 | ES-3 | A list continued from the prior page, followed by narrative and another nested list. Does cross-page reading order preserve the list and paragraph associations without carrying furniture into the body? |
| `deir_main` | 46 | ES-4 | Figure ES-2 dominates the page, with a caption, source, and little narrative. Is a visual-dominated page represented explicitly without inventing chart or map content? |
| `deir_main` | 1500 | 4.16-44 | Wide water-demand table with multi-row headers, many numeric columns, and footnotes. Are row, column, span, and footnote relationships preserved rather than merely rendered plausibly? |
| `deir_main` | 2000 | 8-146 | Ordinary single-column narrative control with subsections and repeated furniture. Does the candidate avoid introducing errors on a straightforward page? |
| `deir_appendix_a` | 20 | 12 | Two-column narrative with an image and caption. Is reading order column-aware, and are the image, caption, and surrounding text distinct and linked? |
| `deir_appendix_b` | 107 | verify in pilot | Email header fields, attachment names, contact block, and the start of a forwarded message on a page with a Task 02 content-stream warning. Are field/value associations and native characters preserved? |
| `deir_appendix_b` | 108 | verify in pilot | Dense continuation prose, a wrapped hyperlink, and paragraph boundaries on a warned page. Does conversion preserve line joining and reading order without silent loss? |
| `deir_appendix_b` | 109 | verify in pilot | Formal letter body, closing, and a printed `Page 3 of 3` label on a warned page. Are body, signature, and page furniture separated and anchored? |
| `deir_appendix_g3` | 1000 | verify in pilot | Extremely dense emissions table with roughly 30 columns from a long appendix whose source carries a Task 02 resource-repair warning. Can the parser expose difficult table structure and report limitations without corrupting neighboring content? |

Before conversion, verify the four selected source IDs, roles, page counts, and
SHA-256 values against the sealed manifest. Apply the same candidate
configuration to every selected page. Use the original PDFs and a supported
page-range interface; do not publish cropped PDFs as new source artifacts. If
the installed API cannot preserve original physical page numbers when
selecting ranges, stop and revise the execution method before conversion.

### Structural-fidelity observations

Record one row per page and, where useful, one child row per affected element.
Preserve the raw evidence supporting every observation. The observation
records must distinguish:

- native-text presence and character loss from layout-region detection;
- region labels from serialized reading order;
- body content from repeated headers, footers, and page labels;
- heading detection from hierarchy-level inference;
- figure detection, caption association, and image export;
- table-region detection, cell matching, row/column topology, spanning cells,
  footnotes, and text/HTML serialization;
- bounding-box presence from bounding-box accuracy;
- parser failure or partial status from downstream serialization loss; and
- semantic differences from incidental paths, timestamps, timings, or object
  ordering.

For each issue, record severity, evidence path, likely cause, and consequence
for retrieval, evidence verification, human review, or presentation only. Do
not calculate a corpus-accuracy percentage from this designed sample.

An issue is **material** when it changes which heading, list, caption, figure,
table row, table column, or footnote a statement belongs to; loses or reorders
substantive evidence; removes a distinctive term needed for retrieval; assigns
an element to the wrong source page; or makes a visible source element
unverifiable from its anchor. Whitespace, cosmetic line wrapping, and
serialization style are presentation-only unless they change one of those
associations. A bounding box is unreliable when it points to the wrong page,
does not overlap the visible source element, or merges distinct semantic
elements so the evidence cannot be checked. The task lead adjudicates raw
output against the deterministic render and baseline text; an unresolved
render-versus-record discrepancy blocks acceptance.

### External artifact layout

Task 03A owns this new external subtree relative to
`ER_COMMONS_DATA_ROOT`; none of it belongs in Git:

```text
pipelines/brisbane_baylands/task_03a_docling_native_pilot_v1/
  pilot_manifest.json
  environment.json
  model_inventory.json
  logs/
  reference_renders/
  baseline/
    pypdf/
  runs/
    <configuration_id>/
      configuration.json
      timings.jsonl
      artifact_inventory.json
      raw_docling/
      page_images/
      picture_images/
      table_images/
      observations.jsonl
      comparison_matrix.csv
  reruns/
```

`pilot_manifest.json` must identify the sealed source release and manifest
checksum, selected source checksums and physical pages, command, Git commit,
configuration ID, and all relative output paths. `environment.json` records
the OS, architecture, Python, package lock, backend, accelerator, thread
settings, and relevant environment settings without secrets.
`model_inventory.json` records every downloaded model's purpose, package,
repository, resolved revision or commit, local relative path, file inventory
or snapshot checksum, license reference, and byte size. Reference renders use
a recorded Poppler version and deterministic resolution; Docling-generated
images remain separate so visual QA does not depend on one renderer.

Time conversion only after model acquisition completes. Capture wall time,
CPU time, peak resident memory, status, warnings, and output bytes for each
selected range. Report measured totals and an explicitly labeled rough
48,341-page capacity projection; the stress sample is not a representative
throughput benchmark.

For the Task 03A operational gate, peak resident memory must remain below the
smaller of 75 percent of physical memory or physical memory minus 8 GiB. The
projected pilot-derived artifact footprint must use no more than half of the
free external-disk space measured at run start. A stress-sample
single-process projection of at most 14 days is acceptable for continued
design; 14 to 30 days requires an explicit operational revision and user
review; more than 30 days rejects the current operational fit. These are
safety and feasibility gates, not production capacity promises; Task 03G will
measure the representative full-document workflow.

### Preliminary candidate configuration

Begin with one configuration, `docling_native_heron_tableformer_accurate_cpu`.
The implementation must express and serialize every setting explicitly rather
than rely on mutable library defaults:

- package candidate: exact `docling==2.115.0`, resolved and locked by `uv`;
- local standard PDF pipeline, with the concrete installed pipeline and PDF
  backend classes recorded after resolution;
- layout model: `docling-project/docling-layout-heron`, with the downloaded
  model revision resolved to an immutable commit or equivalent snapshot
  identity;
- table structure: TableFormer accurate mode with cell matching enabled; verify
  the installed model specification, expected to resolve through
  `docling-project/docling-models` revision `v2.3.0`, and record its immutable
  snapshot identity plus the locked `docling-ibm-models` package;
- accelerator: CPU for the first fixed comparison, avoiding a mixed MPS/CPU
  path and Docling's implicit TableFormer CPU fallback when MPS is selected;
- OCR off;
- remote services and external plugins off;
- the standard PDF pipeline class asserted so the VLM conversion pipeline is
  not selected;
- picture description and picture classification off;
- chart extraction, code enrichment, and formula enrichment off;
- no project-owned LLM repair or post-conversion generative step;
- table-structure extraction on;
- page and picture image generation on, with table crops exported from raw
  `TableItem` records into `table_images/`; and
- only the layout and TableFormer artifacts pre-downloaded into the task-owned
  external subtree, then supplied through Docling's `artifacts_path`, rather
  than invoking the broad default downloader or relying on an unrecorded user
  cache.

Before the first conversion, inspect the installed option model and serialize
the effective configuration. Fail closed if a forbidden path is enabled,
unavailable options are silently ignored, or a model cannot be tied to a
resolved identity. Do not add OCR or a generative path as a fallback.

The current primary sources for this candidate are the
[Docling technical report](https://arxiv.org/abs/2408.09869),
[architecture](https://docling-project.github.io/docling/concepts/architecture/),
[document model](https://docling-project.github.io/docling/concepts/docling_document/),
[model catalog](https://docling-project.github.io/docling/usage/model_catalog/),
[pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/),
[2.115.0 release](https://github.com/docling-project/docling/releases/tag/v2.115.0),
and
[pypdf text-extraction guidance](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).
The Docling codebase is MIT-licensed, but each resolved model license must be
checked independently.

### Configuration-change rule

Run the fixed set once before changing the candidate. A configuration revision
must cite a concrete preserved failure, receive a new configuration ID, change
only the smallest relevant option, and rerun all ten pages. The only
predeclared first revisions are:

- disable TableFormer cell matching if the raw table structure is sound but
  embedded PDF cells are consistently mapped to the wrong columns; or
- evaluate one documented higher-accuracy non-generative layout model if
  Heron materially corrupts regions or reading order outside the specifically
  difficult Appendix G3 page 1000 or one of the warned Appendix B pages
  107-109.

Any other material change requires updating this specification first. A
revision may not introduce OCR, VLM conversion, remote services, picture
description, chart interpretation, or LLM repair.

#### Evidence-triggered PDF-backend revision

The first fixed-set run completed on 2026-07-27 with the current
`DoclingParseDocumentBackend`, but its preserved parsed-page records exposed a
material native-text failure on Appendix B pages 107-109. The deterministic
renders contain substantive email and letter text, while the backend returned
only 2, 1, and 1 text lines respectively, and Docling nevertheless reported
`success` without a conversion error. The locked pypdf baseline also reported
its explicit content-stream limit error on these pages, consistent with their
Task 02 warnings. This is silent native-text loss and therefore rejects the
first candidate under the criteria below.

Authorize one smallest-relevant revision,
`docling_native_pypdfium2_heron_tableformer_accurate_cpu`: replace only
`DoclingParseDocumentBackend` with Docling's maintained
`PyPdfiumDocumentBackend`. Keep the package and model pins, standard pipeline,
Heron layout model, TableFormer accurate mode and cell matching, CPU settings,
native-only policy, forbidden-path assertions, fixed ten-page selection, raw
diagnostics, and review dimensions unchanged. Rerun all ten pages and preserve
the first candidate beside the revision. This backend substitution tests
whether a different maintained native glyph-recovery implementation repairs
the concrete warned-page failure without composing multiple parser outputs.
If the revision still silently loses text or causes a required control page to
fail, stop with `reject/split`; do not add OCR or a custom text-fusion layer.

### Decision criteria

**Accept** the candidate only when the main-report pages 44-46, 1500, and 2000
and Appendix A page 20 all produce structured raw output with original physical
page provenance and bounding boxes. At most one of Appendix B pages 107-109 or
Appendix G3 page 1000 may have an explicit, recoverable conversion failure.
Ordinary and multi-column text must have no material reading-order corruption;
headings, furniture, lists, figures, captions, and tables must remain
distinguishable; the main-report table must preserve the semantic association
of values with row and column headers and footnotes; raw evidence must make
every observed failure classifiable; and the measured resource gates above
must pass. Acceptance may include documented presentation-only defects and
the single bounded hard-page failure.

**Revise configuration** when Docling exposes the required primitives but one
bounded option plausibly causes a repeatable table-matching or layout failure.
Apply the revision to the complete fixed set and compare it with the original
run without replacing the original evidence.

**Reject or split the parser role** when native text is silently lost; source
page identity or bounding boxes are absent or unreliable; required structure
is available only by scraping a lossy serialization; ordinary pages show
material reading-order corruption; table meaning cannot be recovered from the
raw model; forbidden OCR, remote, or generative paths cannot be disabled and
verified; semantic output is unstable on rerun; warning-bearing pages fail
without an observable status; more than one selected page fails; any required
control or coverage page fails; or the measured resource gates above reject
the current operational fit. A split decision must name the maintained
alternative and the exact role it would replace rather than silently compose
multiple parsers.

Rerun the main-report table page after the comparison run. Compare normalized
raw semantic content, structure, labels, provenance, and coordinates while
excluding declared incidental run metadata. Any unexplained semantic
difference blocks acceptance.

### Dependency lifecycle

Add the exact Docling candidate first in a temporary `task03a` uv dependency
group so the exploratory environment is explicit. If accepted, promote the
exact direct requirement to project runtime dependencies and retain the
resolved lock for Task 03B. If rejected, remove the group and refresh the lock
while preserving the external run evidence and decision record. If the result
is `revise configuration` or `reject/split` pending another maintained parser,
retain the temporary group only until that bounded comparison is reviewed.
Downloaded model artifacts always remain external and are removed only after
their recorded run evidence is no longer needed.

## Review pass

Review the pilot through these lenses:

- **Representation sufficiency:** can every required canonical entity be
  derived without scraping Markdown or throwing away provenance?
- **Error observability:** can a later task tell the difference between missing
  native text, layout misclassification, reading-order error, table-structure
  error, and serialization loss?
- **Downstream consequence:** would each observed failure corrupt retrieval,
  evidence verification, human review, or only presentation?
- **Operational fit:** are dependencies, model downloads, runtime, memory, and
  output size credible for a 48,341-page local corpus?
- **License and maintenance:** are the code and model licenses, release cadence,
  and pinning surface acceptable for this local learning benchmark?

## Validation

- Reproduce the pilot from the sealed source manifest and page-selection spec.
- Verify OCR and every remote or generative enrichment path are disabled.
- Record package, model, backend, device, and configuration identities.
- Confirm the raw structured output retains page provenance and bounding boxes.
- Compare reading order, headings, tables, figures, and captions against page
  renders for every selected page.
- Rerun at least one page and distinguish stable semantic output from incidental
  serialization metadata.
- Run:

```bash
make check
git diff --check
```

## Acceptance criteria

- The pilot selection covers the required structural stressors and is
  reproducible from checksum-pinned sources.
- The parser decision is based on preserved outputs and task-facing error
  dimensions, not feature claims alone.
- Each evaluated configuration is explicit, local, native-text-only, and
  records its package, model, backend, and device identities.
- Docling exposes sufficient raw structure and provenance to support the
  canonical entities required by Sprint 2, or the task stops with a concrete
  alternative decision.
- Known limitations and their likely downstream effects are recorded.
- No full document or corpus conversion begins.
- The outcome recommends a candidate configuration but leaves the production
  configuration hash unfrozen until the Task 03G end-to-end pilot.
- The outcome explains the evidence and asks for user review before Task 03B.

## Non-goals

- freezing the canonical schema or ID design
- building production conversion or canonicalization code
- evaluating every PDF or estimating final parser correctness
- OCR, VLM conversion, chart interpretation, picture description, or LLM repair
- retrieval chunking, embedding, BM25, or question answering
- human page-usability dispositions
- selecting cases, evidence, prompts, target models, or judges

## Outcome

Completed 2026-07-27. The pilot accepts the revised configuration
`docling_native_pypdfium2_heron_tableformer_accurate_cpu` as the preliminary
canonical-extraction candidate for Tasks 03B-03G. It rejects the original
`docling_native_heron_tableformer_accurate_cpu` candidate because
`DoclingParseDocumentBackend` silently lost nearly all substantive text on
warned Appendix B pages 107-109 while reporting `success`. Replacing only the
PDF backend with Docling's documented `PyPdfiumDocumentBackend` recovered 42,
39, and 17 native text lines on those pages, with original page numbers and
bounding boxes, while leaving every other parser and model setting unchanged.

The accepted exploratory stack is:

- exact `docling==2.115.0`, now promoted from the temporary Task 03A group to
  the project runtime dependencies;
- `StandardPdfPipeline` with
  `docling.backend.pypdfium2_backend.PyPdfiumDocumentBackend`;
- Heron layout snapshot
  `docling-project/docling-layout-heron@8f39ad3c0b4c58e9c2d2c84a38465abf757272d8`
  under Apache-2.0;
- TableFormer accurate cell matching through
  `docling-project/docling-models@fc0f2d45e2218ea24bce5045f58a389aed16dc23`
  under CDLA-Permissive-2.0;
- CPU with four threads, OCR off, remote services and external plugins off,
  and every VLM, picture-description, chart, code, formula, and generative
  enrichment path off.

Both configurations and the exact model file inventories remain preserved
below:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a_docling_native_pilot_v1/
```

The reviewed manifest is `pilot_manifest.json`; `review_decision.json` records
the decision and Task 03B constraints. The original candidate manifest is
archived inside its configuration directory rather than overwritten. The
review covers all ten fixed physical pages. Every range converted with a
`success` status under the revised backend, all required control pages retain
native text, page provenance, and bounding boxes, and the main-report table
preserves the semantic association of its five drought rows with eleven leaf
columns and footnotes a-h. The rerun of main-report page 1500 produced the same
normalized semantic SHA-256,
`a0df728b025d0ea31ce761353f15b70a288ce0f46c4866f906113b2f16a2cd87`.

The review records four limitations that later tasks must not hide:

1. Multi-level lists on main-report pages 44-45 are ordered, but Docling
   flattens child depth and labels the top bullet as a section header. Bullet
   glyphs and horizontal bounding-box geometry preserve the evidence needed
   for conservative project-owned hierarchy inference.
2. Main-report page 2000 contains one visible subheading labeled as ordinary
   text. Its text, position, order, and box remain intact.
3. The page 1500 table keeps leaf-column meaning, values, and footnote letters,
   but visually row-spanning headers are serialized as fragments across three
   header rows. Task 03B must preserve raw spans and treat direct footnote
   relationships as unverified unless they are explicitly derived.
4. Appendix G3 page 1000 is the one bounded hard-page failure. Docling detects
   and anchors the table region and retains 11,162 native text lines, but its
   31-by-27 TableFormer grid compresses at least 176 visible lookup rows into
   28 modeled data-row indices and merges many values into single cells. Those
   cells are not semantically usable evidence even though Docling reports
   `success`.

The fourth result is why raw conversion evidence matters: a pipeline-level
success is not a table-quality result. Task 03B must represent conversion
status separately from table-extraction status. A materially incomplete table
must preserve its raw native lines, geometry, source page, and review evidence,
but it must expose no canonical cells. This turns the pilot's silent partial
table into an explicit machine observation without introducing OCR, a
generative repair, or an unvalidated second parser. The production
configuration identity remains unfrozen until Task 03G.

The reviewed comparison also demonstrates the component boundaries described
in the task. PDF native glyph recovery, learned region detection, reading
order, hierarchy inference, and table reconstruction fail independently.
Heron's region labels do not prove correct serialized hierarchy, and
TableFormer can detect the correct table box while producing unusable cell
topology. Conversely, OCR can remain off while learned layout and table models
operate on tokens recovered from the embedded text layer. This is consistent
with Docling's
[architecture](https://docling-project.github.io/docling/concepts/architecture/),
[document model](https://docling-project.github.io/docling/concepts/docling_document/),
documented
[alternative PDF backend](https://docling-project.github.io/docling/_generated/examples/run_with_formats/),
and [pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/),
as well as
[pypdf's text-extraction guidance](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).

Measured revised-candidate conversion time was 112.03 seconds for ten stress
pages, with 2,899,836,928 bytes peak RSS. The explicitly rough 48,341-page
stress-sample projections are 6.27 days and 148,215,202,769 bytes of durable
candidate output. These pass the 28,991,029,248-byte memory limit and the
562,583,713,792-byte disk-projection limit. Full parsed-page traces, diagnostic
HTML/Markdown, pypdf comparisons, and reference renders are retained only as
Task 03A evidence; projecting those pilot-only diagnostics would be roughly
1.02 TB and is not the downstream artifact contract. Task 03G still owns a
representative capacity measurement.

The implemented workflow validates the sealed release and source checksums,
verifies every downloaded model file, fails closed on forbidden Docling
options, renders deterministic 150-DPI references with Poppler, records
pypdf's explicit errors without aborting, exports raw structured records and
images, samples peak RSS, refuses to mix partial runs, preserves candidate
manifests, and seals reviewed observations plus an artifact inventory. The
initial pypdf-aborted attempt is retained under `failed_attempts/` with its own
record rather than erased.

Validation passed:

```text
make fix
make check
git diff --check
make finalize-task03a-pilot
```

No full document or corpus conversion began. Stop here for user review. Before
Task 03B is activated, revise its provisional contract to make parser labels
and parents observational, preserve raw text and geometry, separate
conversion/table status, and forbid canonical cells for materially failed
tables.

### Closure update: Task 03A.15

User review accepted the ten-page native text, layout, image, and provenance
outputs, then Task 03A.15 replaced the proof-of-concept implementation and
corrected the table ownership boundary. TableFormer is disabled globally.
Content-based PDFium signals route dense numeric pages to the clean Stream
path; Heron table regions provide the fallback evidence for bounded Lattice;
pages with neither signal skip table reconstruction.

The final v4 run passed. All non-table ranges matched this accepted pilot
exactly, both routed pages completed the full clean table pipeline, and every
table received cleanup evidence and a family assignment. Appendix G3 page
1000 now has a usable 183-by-34 cleaned table, parsed footer metadata, footer
ownership, and a family assignment rather than the unusable TableFormer grid
described above. The historical TableFormer result remains preserved as
evidence; it is no longer the accepted table implementation.

Task 03A is closed. Before Task 03B begins, revise its provisional contract to
consume this accepted boundary without restoring TableFormer cells or
bypassing table cleanup, footer ownership, or family assignment.
