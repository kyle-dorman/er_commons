# Task 03A.1: Validate Fast Native-PDF Table Extraction

Status: **completed 2026-07-28; closed as evidence, not the production contract**.

## Abstract

Test a faster, table-specialized extraction path before Task 03B freezes the
canonical contract. The completed Task 03A found that TableFormer consumed
106.86 seconds on Appendix G3 page 1000 and produced materially unusable cell
topology. Compare maintained, non-generative Camelot heuristics on a fixed set
of dense native-PDF tables, export reviewable CSV and cell geometry, and
measure a composed workflow in which Docling retains page/layout ownership but
does not run TableFormer. Benchmark Heron-only Docling on CPU and Apple MPS,
because TableFormer itself explicitly falls back from MPS to CPU.

## Goal

Choose a reproducible table route that is materially more faithful and faster
than the Task 03A TableFormer result, or stop with evidence that these tables
need another bounded parser investigation. Define which table artifacts Task
03B must preserve without freezing the production extraction configuration.

## Inputs

- `AGENTS.md`
- `docs/architecture.md`
- `docs/data_artifacts.md`
- `tasks/sprint2/02_freeze_sources_and_provenance.md`
- the completed `tasks/sprint2/03a_validate_document_parser.md`
- its reviewed external manifest, observations, renders, configurations, and
  resource measurements
- `configs/brisbane_baylands_2025_deir_task03a1_table_pilot_v1.json`
- the sealed main-report and Appendix G3 PDFs named by the source manifest
- current primary Camelot and Docling documentation and installed source

## Outputs

- a tracked fixed table-pilot specification
- an exact Camelot dependency pin and separate lock
- explicit Camelot candidate configurations
- raw external CSV, cell, geometry, parsing-report, overlay, timing, warning,
  and error artifacts for every fixed page/configuration
- a compact human comparison matrix and machine-check results
- CPU-versus-MPS Docling-without-TableFormer timings and semantic comparison
- a composed runtime and artifact-size projection clearly labeled as a
  stress-sample estimate
- an accept, revise, or reject decision and precise Task 03B constraints

## Research / learning checkpoint

Use Camelot's current
[parser documentation](https://camelot-py.readthedocs.io/en/latest/user/how-it-works.html),
[API](https://camelot-py.readthedocs.io/en/latest/api.html), and
[2.0.0 release](https://github.com/camelot-dev/camelot/releases/tag/v2.0.0).
Inspect the installed Docling source that selects accelerator devices and
constructs Heron and TableFormer rather than inferring stage placement from a
top-level `device` option.

The outcome must explain:

- table detection, grid reconstruction, text-to-cell assignment, header
  interpretation, and CSV serialization are separate operations;
- ruled-line, text-alignment, hybrid, and learned table parsers fail
  differently, so a router must be driven by observable page/table features
  and validated output rather than parser confidence alone;
- CSV is a useful rectangular derivative but cannot be the sole canonical
  table record because it discards cell spans, geometry, raw text assignment,
  footnotes, and source provenance;
- accelerator choice is stage-specific: MPS can accelerate a supported layout
  model while an adjacent table model still runs on CPU;
- repeated scientific tables support strong structural invariants, such as one
  coordinate key per data row and stable column headers, even without
  hand-labeling every numeric value; and
- a fast wrong CSV is worse than an explicit failed table record.

## Fixed pilot specification

The machine-readable selection is
`configs/brisbane_baylands_2025_deir_task03a1_table_pilot_v1.json`. All page
numbers are one-based physical PDF pages. Verify source role, page count,
SHA-256, and bytes against the sealed manifest before parsing.

| Source ID | PDF pages | Purpose |
| --- | ---: | --- |
| `deir_main` | 124 | Conventional borderless report table: grouped emissions headers, three data rows, and notes a-d. |
| `deir_main` | 1500 | Required ruled report-table control: multi-row and spanning headers, eleven leaf columns, five data rows, and footnotes a-h. |
| `deir_appendix_g3` | 999-1001 | Three consecutive instances of the extremely dense wide scientific table. Test repeated-schema consistency and row preservation rather than tuning one page. |
| `deir_appendix_g3` | 2000 | A different wide DPM/risk schema whose right-side result columns remain row-aligned with the primary columns. |
| `deir_appendix_g3` | 4000 | A narrower toxic-air-contaminant schema with scientific notation and receptor classification. |

The seven pages are fixed before installing or running Camelot. Do not add
pages to rescue a candidate. Deterministic renders used for selection are
orientation evidence only; publish fresh recorded renders inside this task's
external artifact root.

## Candidate configurations

Pin exact `camelot-py==2.0.0` in a small separate uv project owned by this
pilot. Do not install it into the main er-commons environment: Camelot requires
`opencv-python-headless`, while Docling currently requires `opencv-python`, and
the OpenCV packages publish the same `cv2` namespace and should not coexist in
one environment. Do not install the optional ML, OCR, or plotting extras.
Record Camelot, OpenCV, playa, pdfium, pandas, and relevant system-library
versions and licenses. Invoke the isolated runner through a narrow,
JSON-producing subprocess boundary.

Apply each candidate to all seven pages:

1. `camelot_lattice_vector`: line-ruled parser using native vector rules only;
2. `camelot_lattice_combined`: raster line detection unioned with native vector
   rules;
3. `camelot_stream`: whitespace and text-row parser with no OCR;
4. `camelot_network`: native-text alignment parser with no OCR;
5. `camelot_hybrid_vector`: network structure augmented by native vector rules;
6. `camelot_hybrid_combined`: network structure augmented by raster and native
   vector rules as the higher-cost reference; and
7. `camelot_hybrid_combined_150dpi`: the same combined method at a fixed lower
   raster resolution to test whether it retains topology while reducing the
   concrete page-1000 raster cost.

Use documented defaults initially, except for the named parser/engine,
one-based page selection, adaptive `edge_tol=None` for Network/Hybrid, explicit
`line_scale=15` for Lattice, and explicit `suppress_stdout=False`. Serialize
every effective option. Do not use manually drawn table areas or column
coordinates. Use table-region bounding boxes emitted by the paired Heron-only
Docling run as candidate `table_areas`; record the source object and any
coordinate conversion. If Docling fails to detect a visible table region, that
is an explicit composed-pipeline failure rather than permission to draw an
area manually. A revision may introduce one fixed page-independent tolerance
only when a preserved failure identifies that exact cause; rerun the complete
seven-page set under a new configuration ID.

Camelot owns table grid reconstruction and cell text assignment only. It must
not become the source for document hierarchy, narrative reading order,
figures, or page identity.

## Composed Docling and accelerator comparison

Create a Task 03A-derived Docling configuration with the accepted
PyPdfium2/Heron native-text path but `do_table_structure=False`. Keep OCR,
remote services, plugins, VLM conversion, enrichment, and generative repair
off. Run the same seven pages once on CPU and once on Apple MPS, using identical
model snapshots, page ranges, image settings, and thread settings.

Record per-page stage timings where Docling exposes them, wall time, CPU time,
peak RSS, warnings, errors, device resolution, raw table-region labels, and
normalized semantic output. Do not claim MPS acceleration merely because the
top-level option says `mps`; record the actual stage devices. The installed
Docling 2.115.0 TableFormer implementations force MPS to CPU because it is
slower, so do not run another MPS TableFormer comparison.

Accept MPS for the composed candidate only if it is available, produces no new
material semantic or geometric defect, and reduces median Heron-only wall time
by at least 20 percent. Otherwise retain CPU. Device-dependent incidental
floating-point differences are acceptable only when element identity, labels,
reading order, page provenance, and visibly checkable boxes remain equivalent.

## Artifact and provenance contract

Write all real outputs outside Git below:

```text
pipelines/brisbane_baylands/task_03a1_table_pilot_v1/
  pilot_manifest.json
  environment.json
  reference_renders/
  candidates/
    <configuration_id>/
      configuration.json
      timings.jsonl
      parsing_reports.jsonl
      raw/
      csv/
      cells/
      overlays/
      observations.jsonl
  docling_no_tableformer/
    cpu/
    mps/
  comparison_matrix.csv
  capacity_observation.json
  review_decision.json
```

For each detected table preserve:

- source release, source ID, source checksum, physical page, table index, and
  parser/configuration identity;
- table bounding box and coordinate convention;
- CSV with no synthetic pandas index or header;
- lossless cell records with row/column indices, spans or edge flags,
  bounding boxes, raw text, and assignment metadata available from the parser;
- parser report, warnings, errors, and detection order;
- a rendered crop and grid/text overlay; and
- hashes and byte sizes for every output.

CSV is a derived convenience artifact. The cell/geometry record and provenance
sidecar are required even when the CSV passes.

## Fidelity and failure checks

Human-review every selected page against its deterministic render. For all
candidate outputs distinguish table detection, grid topology, text assignment,
header semantics, and serialization.

At minimum, enforce:

- logically row-aligned columns remain one table even when a large visual gap
  separates a right-side result group;
- the main-report control preserves the eleven leaf columns, five drought
  rows, grouped headers, values, and footnote markers;
- each G3 primary-table data row contains exactly one coordinate/lookup key,
  and no extracted cell contains multiple coordinate keys from different
  visible rows;
- the number of extracted primary-table keys matches the native keys found
  inside the reviewed table region;
- repeated pages 999-1001 have compatible primary-table schemas;
- fixed first, middle, and last visible rows on every G3 page retain their
  coordinate key and values under the correct headers;
- native table text is not silently discarded or assigned to a neighboring
  table;
- every accepted CSV cell traces to cell geometry and the checksum-pinned
  source page; and
- parsing scores are recorded but never override a failed invariant or visual
  discrepancy.

A detected table with failed topology or assignment checks must produce an
explicit failed observation and no accepted CSV. Preserve its raw candidate
output for diagnosis.

## Operational decision criteria

Report Camelot-only, Heron-only, and composed timings separately. The composed
stress-sample projection assumes the selected Heron device plus selected table
route on every one of 48,341 pages; it is intentionally conservative because a
future router should invoke table extraction only on detected table pages.

- **Accept:** all seven pages satisfy the checks above; no required table is
  silently lost; the composed all-page stress projection is at most 48 hours;
  peak RSS remains below the Task 03A limit; and projected durable output
  remains below half of free external disk.
- **Revise:** one documented, page-independent parser option plausibly fixes a
  bounded repeated failure without page-specific coordinates or manual rules.
- **Reject:** no candidate preserves required row/column meaning, any candidate
  needs OCR or learned/generative repair for these native-text pages, failures
  cannot be detected mechanically, the composed projection exceeds 72 hours,
  or resource gates fail.
- **User review required:** a 48-to-72-hour composed projection or a proposed
  table-type split not already represented by the fixed candidates.

If multiple candidates pass, prefer the simplest maintained configuration with
the strongest invariant results, then lower runtime and artifact size. Do not
average heterogeneous failures into an unsupported accuracy score.

## Dependency lifecycle

If accepted, retain the separate exact Camelot project and lock and carry the
subprocess table boundary into the Task 03B contract. Do not promote Camelot
into the main runtime while the two OpenCV distributions conflict. If rejected,
remove the isolated project while preserving external evidence. Keep the
accepted Docling pin from Task 03A regardless; this task changes only whether
Docling or Camelot owns table structure.

## Validation

- Verify the sealed source manifest and selected source checksums.
- Confirm all Camelot candidates are native-text-only and non-ML.
- Confirm the Docling comparison has TableFormer off and all forbidden paths
  off.
- Verify source page and coordinate provenance in every accepted cell record.
- Rerun one dense page under the selected candidate and compare normalized CSV
  and cell geometry.
- Verify candidate failure checks using tiny synthetic ruled and aligned-table
  fixtures, including a deliberately merged-row failure.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- The table decision is reproducible from fixed source pages and explicit
  configurations.
- Accepted CSVs are backed by source-linked cell geometry and passed
  invariants, not parser confidence alone.
- The selected route materially improves both dense-table fidelity and the
  Task 03A runtime bottleneck.
- MPS is selected only from measured stage-relevant evidence.
- Task 03B receives an explicit table artifact/status contract.
- No full document or corpus extraction begins.
- The outcome asks for user review before Task 03B is revised or activated.

## Non-goals

- full-document or corpus conversion
- freezing the production extraction/configuration hash
- OCR, VLM conversion, LLM repair, or Camelot's ML parser
- manual per-page table areas, columns, or cleanup rules
- hand-correcting table values
- assigning human page usability
- defining the complete canonical schema, retrieval chunks, or evaluation data

## Outcome

Completed 2026-07-27. The formal decision is **reject** under this task's
operational gates, but the pilot found a much faster and materially more useful
dense-table extraction path. No single Camelot configuration passed all seven
fixed pages. The reviewed evidence instead supports a provisional table-type
split:

- `camelot_lattice_vector` preserves both main-report controls, including the
  5-by-7 emissions table and the ruled 8-by-11 water-demand table; and
- `camelot_stream` preserves the five dense Appendix G3 tables as 183-by-34,
  183-by-34, 183-by-34, 196-by-38, and 120-by-15 rectangular records.

Stream recovered all 176, 176, 176, 191, and 116 visible coordinate-aligned
data rows on G3 pages 999, 1000, 1001, 2000, and 4000. Every reviewed data row
has one lookup key, matching X and Y columns, a complete rectangular width,
and no blank cell. The three repeated pages have identical raw header schemas.
The page-1000 Stream result is 183 rows by 34 columns and took 3.74 seconds,
compared with Task 03A's 106.86-second TableFormer result whose usable topology
collapsed the visible rows. An independent rerun produced byte-identical CSV
and cell-geometry SHA-256 digests.

The result does not justify a universal parser. Lattice detects the dense
table's rules but returns only its three header rows. Stream preserves the
dense data but splits the ruled main-report control into 16 rather than 8
rows. Network and vector Hybrid collapse dense columns. Combined Hybrid
recovers the same dense data rows as Stream at about twice the total table
runtime, and lowering its raster resolution to 150 DPI produces no meaningful
gain. Parser-reported confidence does not override these observable failures.

The dense raw CSVs also expose an important remaining limitation. Their leaf
columns and numbered lookup columns are aligned, but several multi-level area
labels are concatenated at a span anchor rather than normalized across their
child columns. The CSV is therefore a useful rectangular derivative, not a
standalone canonical table. The retained `cells.json` and `table.json` records
preserve cell geometry, edge flags, raw assignments, parser identity, source
checksum, and physical page so later span-aware header work remains auditable.
A fast wrong or context-free CSV is still a failed extraction.

This separation reflects the parser architecture documented in Camelot's
[parser guide](https://camelot-py.readthedocs.io/en/latest/user/how-it-works.html)
and [API](https://camelot-py.readthedocs.io/en/latest/api.html). Heron detects
the table region. Camelot separately reconstructs a grid and assigns native
PDF text to cells. Header interpretation and CSV serialization are later
operations. Ruled-line, whitespace, alignment, hybrid, and learned parsers
fail differently, so Task 03B must not treat one parser's success or confidence
as proof of table meaning. Camelot 2.0.0 remains isolated behind a subprocess
and exact lock because its headless OpenCV distribution conflicts with
Docling's OpenCV distribution in one environment; see the maintained
[2.0.0 release](https://github.com/camelot-dev/camelot/releases/tag/v2.0.0).

Apple MPS is not selected. Heron-only CPU and MPS outputs were semantically
equal on all seven pages, with maximum box-coordinate differences below
0.00013 PDF points. Median wall time changed from 5.317 to 5.184 seconds, only
a 2.5 percent improvement and well below the required 20 percent. Installed
Docling source also confirms that this accelerator choice is stage-specific:
Heron can use MPS while TableFormer explicitly falls back to CPU.

The reviewed split took 25.08 seconds for Heron-only Docling and 17.39 seconds
for table extraction across seven stress pages. The deliberately pessimistic
projection that applies both stages to all 48,341 pages is 81.47 hours, or
3.39 days. That is a large reduction from Task 03A's 6.27-day projection, but
it exceeds this task's 72-hour rejection threshold by 9.47 hours. The
arithmetic projection falls below 72 hours if table extraction is invoked on
no more than about 71.6 percent of pages, but this pilot did not measure a
representative table-page fraction or a concurrent production runner.

Projected durable output is about 393.0 GB when retaining Heron document and
table-region records plus the selected CSV, cell, table, result, and
configuration records on every page. This remains below the 562.3 GB disk
gate. Peak measured RSS was 1.57 GB, below the 29.0 GB memory gate. Reference
renders, overlays, logs, and failed-candidate outputs are pilot evidence and
are not included in that durable projection.

The sealed external evidence is:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/
  task_03a1_table_pilot_v1/
```

`review_decision.json` records the rejection and Task 03B constraints;
`comparison_matrix.csv` contains all 49 page/configuration comparisons;
`observations.jsonl` records the seven reviewed split-route pages; and
`reruns/rerun_comparison.json` records the byte-identical dense-page rerun.
The first interrupted attempt is retained under `failed_attempts/` with an
attempt record rather than erased.

Task 03B must not promote these results to one universal parser or canonical
normalized headers. It must keep conversion, table extraction, and invariant
status separate; preserve CSV only with source-linked cells and geometry; and
carry Lattice and Stream only as diagnostic candidates for a bounded router
and concurrency benchmark. No full document or corpus conversion began. Stop
here for user review before revising or activating Task 03B.
