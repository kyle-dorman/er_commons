# Task 03A: Validate the Document Parser and Extraction Configuration

Status: **active planning contract**.

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
