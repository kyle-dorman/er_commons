# Task 06C source qualification v1

Gate 1 is source-free. This specification freezes the proposal for the selected
Final F1; it does not authorize source access or conversion. The owning
[Task 06C](../../tasks/sprint2/06c_qualify_and_process_replacement_f1.md) records
validation and independent review. Gate 2 acquisition and Gate 3 conversion
remain separate user authorizations.

## Evidence and identity

Start from commit `6a292a4` and the completed 06A/06B outcomes. The
[maintained command map](../pipeline_commands.md) and
[executed owner map](task06b_gate2_executed_inventory.md) replace historical
script names. Preserve original per-source manifests, all accepted artifacts,
318 completed conversion ranges, and the wrong F1 as evidence.

The compact source-free input is root-relative
`pipelines/brisbane_baylands/task_06_recovery_v1/06a/f1_substitution_evidence.v1.json`:
62,021 bytes; SHA-256
`38e44259c3aec3fd5867fdd1eb601139bfa74591ecef9a5111b2c78d4c01052c`, as recorded
by the adjacent `packet_inventory.json`. Its stored landing-page inventory
entry position 11 names Document Center 2972 and the advertised title below.
No live landing-page check is needed or authorized in Gate 1.

| Binding | Frozen value |
| --- | --- |
| Selected URL | `https://www.brisbaneca.gov/DocumentCenter/View/2972/Appendix-F1---Transportation-Impact-Assessment-PDF` |
| Advertised label | `Appendix F1 - Transportation Impact Assessment (PDF)` |
| Logical membership | `deir_appendix_f1` |
| Physical replacement | `feir_appendix_f1` |
| Edition | `final_eir` |
| Wrong source | `brisbane_baylands_2025_deir_sources_v1`, source `deir_appendix_f1`, Document Center 553 |
| Wrong-source observations | 8,223,907 bytes; 75 pages; SHA-256 `dd51b7e5f0d511abc34617c10afde270e27d5dfe5df7ae9b7048cc206528ac78` |
| Edition equivalence | `not_established`; substitution exception is F1 only |

The census preserves all 66 mention IDs and 58 source-unit IDs. Table 6 revision
context `Response SA-Caltrans-6` and Muni revision context
`Response SA-Caltrans-9` contain three mention IDs together. These exceptions
remain explicit; other mentions imply no Draft/Final equivalence. Do not assign
Final source bytes the Draft edition or reopen the selected replacement.

## Qualification contract

The checked request is
`configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json`.
Its source-general policy version is `source_qualification_policy_v1`.
Only HTTPS on `www.brisbaneca.gov`, retaining `/DocumentCenter/View/2972/`, is
permitted. Check each redirect before following it; reject identity changes,
userinfo, unapproved hosts or ports, and ambiguous URL components. At most
three redirects and one active request are permitted. No preliminary HEAD,
range probe, landing-page refresh, or alternative-source search is part of the
proposal.

Require status 200, PDF content type/signature, positive byte/page observations,
original/final URLs, UTC access time, full redirect observations, stream SHA-256,
and structural validation. Record Content-Type, Content-Length,
Content-Disposition, Content-Encoding, Date, ETag and Last-Modified when
present. Optional absent values remain absent; a missing server filename is
not inferred from the URL. A declared length must match the completed stream;
reject malformed, truncated or encoded transfers that defeat byte accounting.
A filename supplies useful disagreement evidence, but cannot override observed
title evidence or prove identity on its own.

Use the already installed `pypdf.PdfReader` and `page.extract_text()`, with
physical pages 1 through
`min(page_count, 20)`: first ten pages plus the fixed ten-page extension 11–20.
Do not scan the rest, follow an inferred page destination, use OCR, run Docling,
or add a second extractor. Save page references and observed text separately
from expected labels. Accept only explicit normalized title variants
`Transportation Impact Assessment` and
`Appendix F1 - Transportation Impact Assessment`; qualification also requires
`Brisbane Baylands`, `Existing Traffic Conditions Memo`, and `Final EIR`.
The title must occur on physical pages 1–3, with the project phrase on that
same page. Normalization is deterministic and conservative; full-line title comparison
must not accept an unrelated similarly named title. Exact normalization is
owned by `source_release/qualification.py` and its synthetic tests.

These strings are qualification requirements, not claims about unseen PDF
contents. Missing evidence, an unlisted title variant, or uncertain edition
stops qualification. Review of a documented variant requires a revised policy
and disposition; no silent waiver or fuzzy match is allowed.

## Finite resource contract

Limits narrow the 06A planning envelope. They are ceilings, never estimates of
the unseen PDF. Exceeding one retains nonterminal evidence and stops; do not
remove old or failed artifacts to make space.

| Resource | Gate 2 ceiling |
| --- | --- |
| Connect / read timeout | 15 / 60 seconds |
| Whole acquisition | 900 seconds |
| Automatic retries | 0; interruption/failure does not silently redownload |
| Stream and partial-plus-final PDF storage | 535,822,336 bytes (511 MiB) |
| Structural page count | 5,000 pages |
| Qualification pages | 20 physical pages, bounded above |
| Qualification elapsed / worker memory / threads | 300 seconds / 2,147,483,648 bytes RSS / 1 thread |
| Whole attempt namespace including metadata | 536,870,912 bytes (512 MiB) |
| Initial free disk | 68,719,476,736 bytes (64 GiB) |

The 1 MiB metadata allowance is separate from the 511 MiB retained PDF ceiling.
The supervisor samples worker RSS every 0.05 seconds and terminates on the
2 GiB ceiling. This is a sampled process bound, not a guaranteed instantaneous
peak bound. RLIMIT_AS adds an address-space bound off macOS; macOS uses the RSS
supervisor because its address-space limiting differs. The 900-second outer
deadline includes qualification; qualification also receives its own shorter
300-second deadline. Each extracted page is capped at 200,000 characters.

The source digest is updated once in the acquisition stream. Qualification may
read bounded PDF evidence and structural metadata; it does not compute another
source digest. Completion seals bind the request, qualification, observations,
source digest, file metadata and managed membership. Ordinary receipt reuse
checks compact seals and source metadata without opening/hashing the PDF or
invoking conversion. It proves receipt integrity and correspondence, not a new
byte-for-byte audit. A checksum alone establishes which bytes were delivered,
not whether those bytes are the advertised document.

## Commands and restart

From the repository, the source-free validation command is:

```bash
uv run er-commons sources validate-qualification-spec --spec configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json
```

Only after acquisition authorization:

```bash
uv run er-commons sources acquire-qualified --spec configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json
```

The fresh destination is root-relative
`datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_feir_f1_qualified_v1`.
The configured data root must exist, and destination creation must fail closed
on traversal, symlinks, existing conflicts or insufficient disk.

A qualified destination contains `source.pdf`, `source_record.json` and
`completion.json`. The source record contains the substitution binding and
semantic observations; no new release-wide manifest is synthesized. A failure
retains `source.part` or any published payload plus `failure.json`, without an
accepted completion. Compact metadata has a separate 1 MiB allowance.

For a completed source, the source-free reuse command is:

```bash
uv run er-commons sources reuse-qualified --spec configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json
```

A conflicting existing destination or partial attempt must never be overwritten.
An incomplete transfer requires an explicitly reviewed fresh namespace and the
same bounded acquisition scope; do not silently resume an unverified partial
stream. If a complete stream fails semantic qualification, retain its bytes and
transport digest for a separately proposed local requalification under a revised
policy. Do not redownload merely to repair metadata or accept a title variant.
The current command does not automatically requalify failed attempts. A completed
qualified receipt is reused with the third command. Gate 2 ends at the
qualified source and measured conversion proposal; it cannot launch conversion.

## Conversion envelope and unresolved measured binding

Freeze the maximum Gate 3 envelope now: one worker/document, CPU four threads
(including learned-table fallback), at most 5,000 physical pages, 10 GiB
process-tree RSS, 32 GiB total new conversion/producer output including partials,
64 GiB initial disk floor, 200-page target ranges, 250-page hard range maximum,
one overlap page, 3,600 seconds per range and 86,400 seconds for the entire
conversion/producer invocation including at most one retry. Cancellation grace
is 15 seconds; positive swap growth stops execution. Completed matching range
receipts remain reusable; a failed range never invalidates earlier completions.

This envelope is not yet an executable conversion request. After qualification,
use measured pages/bytes to prepare the maintained content parsing and explicit
chunk policy, then separately review the bounded request. The current maintained
chunk-policy dispatcher requires sources above 300 pages; if the replacement is
smaller, its measured proposal must name the bounded nonchunked route or a
separately tested adjustment. Do not fabricate page counts to satisfy selection.

Use maintained `document_parsing/content_parsing/runtime.py` options:
`StandardPdfPipeline`, `ThreadedPdfPipelineOptions`, rotation-normalized PDFium
backend, Heron layout, CPU, local artifacts, no OCR, no remote services/plugins,
no Docling table structure, no chart/picture/code/formula enrichment; page and
picture images and parsed pages enabled at scale 2.0. The separate existing
clean-table producer retains its declared TableFormer fallback, limited to four
threads. Docling's internal document timeout remains null per the maintained
config; outer process/range deadlines enforce finite wall time.

Source-free inspection on 2026-09-10 found Requests 2.34.2, pikepdf 10.10.0,
Docling 2.115.0, docling-core 2.88.0, docling-ibm-models 3.13.3, torch 2.13.0 and
pypdf 6.14.2. Poppler pdftotext 26.09.0 is also installed, but the qualification
boundary uses pypdf only. No model was loaded. Historical configs name
`pipelines/brisbane_baylands/task_03a_docling_native_pilot_v1/model_inventory.json`
and sibling `models/`, but that inventory is absent at the configured external
root. The expected maintained model references are
`docling-project/docling-layout-heron` at `main` and
`docling-project/docling-models` at `v2.3.0`; these are expected references,
not verified installed snapshot identities. Gate 3 must bind an existing valid
inventory with immutable snapshot/file identities and compatible package versions.
Missing models or inventory stop before conversion; network/model download and
fallback are prohibited. Model remediation needs its own concrete proposal.

The exact qualified source seal, processing exception and current source adapter
must be bound before a conversion command can be executable. Publish only fresh
conversion/producer evidence for Final F1. Tasks 06D–06F can change target policy
without converting these same qualified bytes again. Gate 06G resumes from
sealed conversion/producer evidence under the 06B reuse contract; collection
publication and case-level evidence acceptance remain later work.

## Primary references and learning

- [Requests advanced usage](https://requests.readthedocs.io/en/latest/user/advanced/):
  streaming and explicit response closure bound storage; connection/read timeouts
  are not an overall download deadline, so an outer deadline is required.
- [pikepdf main objects](https://pikepdf.readthedocs.io/en/latest/api/main.html):
  opening and syntax checks establish structural properties, not semantic title
  or edition. A readable wrong PDF must fail the separate qualification policy.
- [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html):
  text extraction parses page content streams and can consume substantial memory;
  supervised time and memory ceilings are required even for a small page window.
  No OCR or alternative extraction fallback is introduced.
- [Docling advanced options](https://docling-project.github.io/docling/usage/advanced_options/):
  explicit local artifacts and disabled remote services support controlled model
  use. Installed maintained adapter code, rather than evolving documentation
  defaults, determines the actual future conversion options.

Only tool documentation was researched. No selected PDF, source page, existing
source PDF, conversion payload or model payload was opened for this specification.
