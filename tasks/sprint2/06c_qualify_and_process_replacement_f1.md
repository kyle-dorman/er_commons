# Task 06C: Qualify and Process Replacement F1

Status: **Gates 1–4 complete. The selected 756-page Final F1 is qualified
with the explicitly approved thumbnail/title disposition and verified internal
memo. Fresh conversion and producer evidence is sealed for reuse; Gate 4
validated the compact handoff. Original failed acquisition evidence and the
preserved first conversion attempt remain immutable. Tasks 06D–06H are inactive.**

## Abstract

Acquire the selected Final EIR Appendix F1 Transportation Impact Assessment,
prove its delivered identity, and create reusable conversion/producer evidence
through the maintained pipeline. The accepted Draft F1 URL delivered the wrong
75-page Bayshore Mobility Study. Its successful PDF validation did not establish
that the advertised document was delivered.

The user has selected Final F1 as the substitute. Do not reopen that choice.
Preserve Final edition and substitution provenance throughout processing and
handoff. Do not describe the substitute as original Draft text. Publish reusable
upstream evidence so final Task 06 repair policies can run without converting
this PDF again.

## Goal

- Retrieve exactly the approved Final F1 into a fresh no-clobber namespace.
- Verify advertised identity against response metadata and bounded document
  evidence before accepting the substitute.
- Extend the existing acquisition boundary with the smallest source-general
  identity qualification contract selected by Task 06A.
- Produce sealed F1 conversion and producer evidence with explicit resource
  accounting and resumable maintained stages.
- Preserve the incorrect accepted source and every accepted descendant.
- Hand reusable evidence and unresolved qualification issues to Task 06G.

## Inputs and prerequisite gate

Read the umbrella, Tasks 06A and 06B outcomes, `docs/architecture.md`,
`docs/data_artifacts.md`, the source-free impact census, and the accepted source
and document specifications selected there. Task 06B must have closed both its
reuse/identity gate and its cleanup gate, including its old-to-new filename map.
Resolve the owners below through that map before editing.

The baseline source is Task 02's immutable release:
`brisbane_baylands_2025_deir_sources_v1`, beneath
`datasets/ceqa/raw/brisbane_baylands/`. Its `deir_appendix_f1` entry advertises
Transportation Impact Assessment, Document Center ID 553, but records
8,223,907 bytes and 75 pages. Those are wrong-source evidence, not expectations
for the substitute.

The selected replacement is Final EIR Document Center ID 2972:
`https://www.brisbaneca.gov/DocumentCenter/View/2972/Appendix-F1---Transportation-Impact-Assessment-PDF`.
The accepted landing-page inventory advertises it as
`Appendix F1 - Transportation Impact Assessment (PDF)`.
The URL is a future acquisition input; reading this task is not permission to
open it, probe it, or retrieve its PDF.

Task 05F's accepted partial candidate is
`rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83`.
Its 66 F1 mentions occur in 58 official-response units: 61 mentions in 56
responses and 5 in 2 General Responses. Preserve the exact mention IDs and
source-unit IDs from the Task 06A census; do not reconstruct them from counts.
`Response SA-Caltrans-6` revises Table 6; `Response SA-Caltrans-9` revises the
Muni section. The 06A census records three F1 mention IDs across those two
units; the two revision contexts are not a two-mention population. No general
Draft/Final edition equivalence is established.

## Current implementation owners

- `source_release/models.py`: source specification and manifest records.
- `source_release/http_discovery.py`: allowed URLs, discovery, labels, headers,
  and redirect provenance.
- `source_release/pdf_download.py`: streaming digest, PDF checks, no-clobber
  publication, and delivered filename.
- `source_release/publication.py` and `records.py`: resume and source seals.
- `document_publication/sources.py`: manifest selection and source identity.
- `document_publication` and `document_parsing`: maintained document execution
  and conversion/producer boundaries.

Existing discovery checks exact landing labels, and structural PDF checks
validate a readable nonempty PDF. Neither proves semantic document identity.
Existing source selection also couples processing with `MODEL_CORPUS` role.
Apply Task 06A's accepted explicit substitute-processing contract; do not label
Final evidence as original Draft merely to pass that check. Honor the user's
selected F1 substitution exception in the processing and downstream handoff
contracts, and update affected current policy documentation to record that
bounded exception. Do not require the user to select Final F1 again. Preserve
separate case-level evidence decisions without using them to block this source
replacement or extend the exception to other Final EIR documents.

## Outputs

1. A small reviewed acquisition specification and source-general qualification
   policy, with bounded synthetic tests.
2. One fresh source record and compact substitution record binding advertised
   Draft source, incorrect accepted bytes, and selected Final source.
3. Exact HTTP, edition, qualification, structural, and acquisition accounting.
4. Sealed conversion and producer identities, completions, inventories, paths,
   and actual resource usage for Task 06G reuse.
5. A compact outcome explaining what was qualified, which stages completed,
   which downstream policies remain pending, and the precise next gate.

Large evidence stays under the configured external root. Do not copy the source
PDF into a Task 05 working tree or a tracked fixture.

## Research / learning checkpoint

Before implementation, inspect the current maintained downloader and the
installed PDF tools. Record primary documentation for Requests streaming,
redirect behavior, and timeouts; pikepdf structural checking; and the installed
Docling conversion options actually used by the accepted pipeline. Research
public tool documentation only, not live source pages before authorization.

Explain why a correct checksum proves delivered bytes, not the advertised
identity; why a server filename is useful disagreement evidence but insufficient
alone; and why Final F1 requires new conversion while later target policies can
reuse that sealed conversion. Do not add a second PDF extractor or an LLM-based
identity classifier.

## Plan / spec requirement

### Gate 1: freeze a source-free execution specification

Before any source access, record and review:

- exact URL, Document Center ID, accepted landing-page evidence, and allowed
  redirect behavior preserving document identity;
- a fresh contained destination, logical source routing key, explicit Final
  edition, and source/qualification schema versions;
- advertised label and expected title evidence; expected internal material,
  including Existing Traffic Conditions Memo; permitted title normalization;
- required response fields, tolerated absent optional headers, and conditions
  requiring a stop rather than an inferred value;
- extraction method and maximum page window for title/internal qualification;
- connection/read timeouts, total elapsed bound, retry count, maximum streamed
  bytes, maximum qualification pages, and process memory/thread limits;
- disk floor, maximum temporary-plus-final bytes, conversion output budget,
  and cleanup-free handling of a failed or partial attempt;
- exact conversion options, installed tool/model versions and existing model
  locations, network/model-download policy, and conversion chunk limits;
- digest policy: compute SHA-256 once during the acquisition stream, seal the
  resulting record, and use accepted metadata/receipt verification thereafter;
- exact package command, configuration bindings, restart command, expected
  artifacts, and the condition separating acquisition from conversion.

Do not guess page count, byte size, runtime, or delivered title. Freeze finite
resource ceilings before acquisition; replace unknown observations only with
actual evidence. If conversion sizing cannot be set responsibly before the
source is qualified, stop after acquisition and present the measured page/byte
counts with a separately bounded conversion proposal.

Implement and test the qualification boundary source-free before requesting
the acquisition gate. This prevents acquiring first and discovering afterward
that the planned validator does not exist.

### Gate 2: separately authorized acquisition and qualification

Use the maintained streaming/no-clobber path. Verify allowed destination and
free space before the request. Record access time, original and final URL,
redirects, status, selected headers, delivered filename, bytes, stream digest,
PDF signature, page count, detected title, and edition evidence.

Reject a redirect that changes the selected document identity. Stop on a
resource overrun, transport truncation, structural failure, title disagreement,
missing required internal evidence, or uncertain edition. Retain a bounded
failure record; do not publish an accepted source completion.

Qualification evidence must distinguish observed text from the advertised
label. Preserve physical page references for reviewed title and internal
material. A title mismatch must not be downgraded to an ordinary parser warning.
Human review may qualify a documented variant only through an explicit revised
policy/disposition, never an unrecorded exception.

### Gate 3: separately authorized conversion and producer execution

Bind the exact qualified source record and approved resource specification.
Run the maintained conversion/producer stages in a new lineage. Do not reuse
conversion or records from the wrong 75-page source. Reuse existing installed
models only as declared; stop before an unapproved model download or network
fallback.

Record all-page accounting, stage completions, inventories, warnings, elapsed
time, peak resource observations when available, and disk use. Conversion
success does not authorize source substitution acceptance, target promotion,
or collection publication by itself.

When Tasks 06D-06F policies are not yet accepted, stop at reusable sealed
conversion/producer evidence. Task 06G must apply the final policies without
redoing conversion. If a task outcome also supplies provisional downstream
records, label them provisional and exclude them from the replacement handoff.

### Gate 4: close the reusable evidence handoff

Validate compact source and stage seals, exact paths/file sets/sizes, identity
bindings, terminal state, and declared resource accounting. Use the Task 06B
sealed reuse path; do not run a standalone full-PDF hash to close this gate.
Name the exact stage at which Task 06G resumes and any unresolved qualification
or extraction issue. No automatic Task 06G execution follows.

## Stop and resume policy

- Never overwrite an existing namespace or mutate an accepted manifest.
- Retain failed attempt evidence with explicit nonterminal status.
- Reuse only completed matching stages with valid seals and exact membership.
- A changed source, policy, model, schema, or owned implementation invalidates
  only the descendants named by the accepted impact table.
- Resume interrupted conversion through maintained chunk/stage receipts.
- Do not redownload or reconvert completed evidence to resolve a metadata issue.
- Stop on ambiguous identity, damaged seals, or unexpected files and report the
  exact source, stage, expected field, observed field, and permitted next step.
- A necessary exceptional deep audit requires an explicit bounded proposal.

## Validation

Synthetic tests must reject a structurally valid wrong-title PDF, changed
Document Center identity, missing qualification evidence, malformed PDF,
truncated transfer, oversized stream, wrong destination, conflicting existing
file, stale receipt, and changed qualification policy. Include a valid title
variant expressly allowed by the source-general policy and an unrelated
similarly named document that must fail.

Instrument tests so ordinary receipt reuse cannot read/hash the source PDF or
invoke conversion. Verify a stream digest matches fixture bytes and is reused
without a second digest pass. Check interruption/restart and deterministic
source identity. Run focused tests, `make fix`, `make check`, and
`git diff --check`; no production extraction is needed for implementation tests.

## Review pass

Review source claims, no-clobber containment, resource enforcement, edition
provenance, semantic qualification, readable diagnostics, and minimal stage
ownership. Independently inspect the specification before the source gate and
the measured qualification evidence afterward. Source qualification and human
code-quality review are separate dispositions.

## Acceptance criteria

- Exact selected Final source qualified with explicit substitution provenance.
- Both known revisions remain named; the other mentions imply no equivalence.
- Stream-only digest policy and bounded resource behavior are demonstrated.
- Fresh conversion/producer evidence is sealed, reusable, and fully accounted.
- The wrong source and all accepted artifacts remain unchanged.
- Task 06G has explicit resume inputs without a promised count of resolved F1
  mentions. Missing or ambiguous specific targets may remain unresolved.

## Non-goals

Task 05 resolver replay, source-site redesign, generalized acquisition
frameworks, fuzzy identity matching, broad corpus extraction, cleanup, commit,
push, or final inventory publication.

## Outcome

### Gate 1 outcome

Gate 1 revalidated the provisional contract against both completed 06B gates
and their maintained owners. The [execution specification](../../docs/specs/task06c_source_qualification_v1.md)
and [checked acquisition request](../../configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json)
freeze the selected source, qualification policy, explicit F1 substitution
provenance, finite acquisition limits and maximum conversion envelope. The
selected Final source has not been contacted; delivered title, bytes, pages and
edition observations remain unknown. The checked request SHA-256 is
`ba082e8bd012af8b0b244bceb6484e7cc40a05db34f7ad8a3b46195bcd8c8dde`.

The 06A packet inventory matched its recorded SHA-256
`83c314339a05a86abb433874b9d7ff82833696ff065451812be7b8937dfb34e7`.
The compact F1 census also matched its recorded digest, and the original manifest
seal/path/size matched the reviewed request without reading its payload. The
06B Gate 2 qualification records still report 35 conversion/producer pairs,
318 ranges and 70 document publications. These are inspected prior qualification
records, not a repeated deep audit or newly computed payload equality. All
original per-source manifests, accepted artifacts and historical configurations
remain unchanged.

### Source-free implementation and provenance

`source_release/qualification.py` owns pure semantic and URL qualification.
`qualified_acquisition.py` owns streaming digest, manually checked redirects,
strict structure and supervised existing pypdf text extraction beside the
preserved historical downloader. `acquisition_limits.py` owns finite budgets;
`qualification_receipts.py` owns exclusive publication, bounded failure evidence
and compact receipt reuse. A fresh spawned worker avoids inheriting HTTP/parser
thread state. `qualification_request.py`
and `substitution_evidence.py` bind portable limits and the exact accepted
census/source references. Thin command services expose validation, acquisition
and reuse separately. No new runtime dependency, extractor or model classifier
was introduced.

The three package commands are `sources validate-qualification-spec`,
`sources acquire-qualified`, and `sources reuse-qualified`, each requiring
`--spec`. Only the validation command and compact accepted-evidence preflight
ran against the real request. Synthetic acquisition tests use generated PDFs and
fake HTTP sessions. Receipt reuse checks current policy/owned implementation/tool
bindings, compact seals, exact managed membership and payload stat observations;
it does not open/hash PDFs or invoke conversion. Changed or incomplete receipts
stop rather than redownloading silently.

The source-processing exception is explicit `final_eir` / `f1_only`, with
logical `deir_appendix_f1` and physical `feir_appendix_f1` identities and
`edition_equivalence: not_established`. Current product policy and Decision 001
now record that accepted exception. The immutable census preserves all 66
mention IDs and 58 units; Table 6 in SA-Caltrans-6 and the Muni section in
SA-Caltrans-9 remain the two named revision contexts, containing three mentions.
No case acceptance or Draft/Final equivalence follows from substitution.

### Validation and independent review

The [independent review](../../docs/specs/task06c_gate1_review.md) has no
unresolved blocking findings. The qualification author reviewed acquisition,
requests and the execution specification; the specification author separately
reviewed semantic qualification. Their final focused suite passed **66 tests**.
Review resolved URL normalization and dot-segment escapes, missing validator/tool
bindings, bounded failure records, optional filename provenance and storage/tool
specification mismatches.

Final `make fix` and `make check` passed: formatting, lint, mypy across
469 source files and **1,607 tests** (37.73 seconds), with no test warnings.
`git diff --check` passed. The first broad check exposed the new module exceeding the existing 360-line owner limit. The
implementation was split without relaxing tests; functions remain within the
100-line limit. Fresh spawned worker startup replaced fork after the suite
exposed inherited-thread warnings. Source-release McCabe checks at threshold 15
and current documentation link checks pass.

### Concrete Gate 2 proposal and subsequent stopping points

Authorize only the checked `sources acquire-qualified --spec
configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json` request.
It makes one GET sequence for Document Center 2972, with at most three
identity-preserving redirects and no retry, HEAD, range probe or landing refresh.
The fresh root-relative destination is
`datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_feir_f1_qualified_v1`;
its absence was checked source-free. Ceilings are 511 MiB streamed PDF,
512 MiB whole namespace, 64 GiB free disk plus attempt reservation, 15/60-second
connect/read timeouts, 900 seconds overall, 300 seconds qualification, 20 physical
pages, 5,000 total pages and 2 GiB sampled worker RSS with one thread. On macOS
RSS supervision is sampled at 50 ms, not an instantaneous hard allocation cap;
Linux additionally uses address-space limits. The specification owns exact
required title/project/internal/edition text, normalization and stop behavior.

On success publish only `source.pdf`, `source_record.json`, and `completion.json`,
then validate their compact receipt and report measured bytes/pages, qualification
and the separately bounded conversion proposal. On failure retain the bounded
partial and nonterminal failure record. Do not change policy or redownload to
make a disagreement pass without a revised disposition and fresh authorization.

The maximum conversion envelope is frozen, but an executable Gate 3 request
requires measured source binding, a qualified-source-to-maintained-manifest
adapter preserving the explicit processing exception, and a verified installed
model inventory. The historical configured model inventory is absent locally;
installed packages alone do not establish model readiness. This is a concrete
Gate 3 precondition, not a reason to reopen Final F1 selection. No conversion,
producer, downstream replay, artifact cleanup, commit or push ran. Task 06C
remains open for Gates 2–4; Task 06G has no new sealed F1 stage input yet.


### Gate 2 outcome: structural stop with retained bytes

The user authorized Gate 2 with “ok continue thru gate 2.” The exact frozen
request above was revalidated, including its SHA-256 and compact accepted
provenance. One maintained acquisition invocation ran, with no retry, probe,
landing refresh or redirect. It exited with code 1 because strict PDF structure
checking failed. This is a completed bounded attempt, **not successful source
qualification**; Task 06C cannot advance to conversion.

| Observation | Actual result |
| --- | --- |
| Access timestamp | `2026-09-10T22:57:53.787405+00:00` |
| HTTP response | 200, `application/pdf`, original selected URL unchanged |
| Content-Length / streamed bytes | 68,389,743 / 68,389,743 |
| Delivered filename | `ApxF1_TranportationImpactAssessment_OCR_REVISED_202605201828511148.pdf` |
| Stream SHA-256 | `e13c5b53f0f4da6a91f52ac784acce06619eeffd3fe053542d7ce1593b957e5e` |
| Attempt elapsed | 11.096243334 seconds |
| Peak observed worker RSS | 295,616,512 bytes, sampled at 50 ms |
| Retained namespace bytes | 68,394,156, including the 4,413-byte failure record |
| Free disk before / after | 740,468,031,488 / 740,399,603,712 bytes |

Pikepdf reported `incorrect header check` while decoding stream objects
`12649 0` (offset 68,354,632) and `12168 0` (offset 65,962,963), followed by
warnings that streams would be reprocessed without filtering. These are actual
structural warnings under the frozen stop policy, not ordinary parser warnings
to waive. Stderr also warned that some specialized decoders, probably
`jbig2dec`, are unavailable, limiting complete stream testing. That environment
warning does not explain away the two observed inflate errors.

The check stopped before returning page count or semantic qualification.
Observed title, required internal material and edition therefore remain
unverified. The server filename and matching HTTP length establish neither
semantic identity nor complete PDF validity. Final F1 selection remains settled;
this failure does not authorize switching sources.

The original acquisition namespace is preserved exactly with `source.part`
and `failure.json`. There is no `source.pdf`, `source_record.json` or
`completion.json`. The failure record retains the stream digest, HTTP metadata,
request/implementation bindings and resource observations. Its SHA-256 is
`9bd38ad81a7d86f92190a83047d15e37bdfecbb07d94fd0b2ec8e1f803ea1ae1`.
No payload was rehashed, repaired, renamed or downloaded again.

A fresh compact execution packet is root-relative:
`pipelines/brisbane_baylands/task_06_recovery_v1/06c/gate2_attempt_v1/`.
Its `execution.json` is 3,909 bytes, SHA-256
`bd4d87ba9a0411182f86062d2410d4769b9ddfdbfb5b2605dce18c3adfd4bc65`;
`inventory.json` seals that diagnostic record only. It is not a source completion.
The [independent Gate 2 review](../../docs/specs/task06c_gate2_review.md)
verified the compact failure record, retained size and exact failed namespace
membership without opening the PDF. Compact accepted provenance still verifies.
No execution code changed in this gate; `git diff --check` and documentation
link checks passed. Gate 1's 1,607-test result remains the implementation evidence.

### Next proposal: bounded local structural diagnosis

The frozen Gate 2 contract explicitly requires a stop on structural failure.
Propose a separate read-only diagnostic using the retained bytes, under a fresh
`06c/gate2_structural_diagnosis_v1/` evidence directory: 300 seconds total,
2 GiB sampled worker RSS, one thread, 64 GiB starting disk floor and at most
8 MiB new reports. Inspect the two named objects and their page/resource
relationships, record the page count, and inspect at most physical pages 1–20
for the frozen semantic requirements using the existing tools. Determine whether
the errors affect visible/textual content and distinguish the missing-decoder
limitation. No network, model execution, PDF repair/rewrite, standalone source
hash or conversion belongs to that diagnostic.

Its result must support an explicit structural/qualification disposition before
local requalification. Retain the acquired bytes and original failure unchanged;
never redownload to resolve a policy or metadata question. A revised policy is
not accepted by this outcome. Gate 3 still requires successful qualification,
measured processing bindings and a verified model inventory; no executable
conversion proposal can yet be approved. No accepted artifacts, original
per-source manifests, conversion ranges or human review were modified. No commit
or push occurred.


### Authorized local diagnosis outcome

The user authorized the proposed checks with “ok run the checks i guess.”
The read-only diagnosis found **756 physical pages**. Object `12649 0` is a
76-by-99-pixel indexed thumbnail referenced only by physical page 28's `/Thumb`.
Object `12168 0` is its color palette, reached through the thumbnail's
`/ColorSpace` array. A scan of indirect objects and their nested dictionary/array
references found no page-body use of either bad stream. Both still fail their
declared Flate decoder; no PDF bytes or filter declarations were changed.
The evidence supports a narrow thumbnail-only structural disposition, not a
blanket waiver of future stream errors or proof that every page renders correctly.
Page 28 was not rendered because the authorized visual/text window was 1–20.
The separate missing-specialized-decoder warning remains an integrity limitation.

Existing pypdf extracted the first 20 pages without exceptions. Poppler rendered
pages 1–3 with no stderr; visual inspection confirmed page 2 is blank and page 3
reads `APPENDIX F.1 TRANSPORTATION IMPACT ASSESSMENT [REVISED]`, with
`Baylands Specific Plan Final EIR`, `City of Brisbane`, and `May 2026` in its
footer. Page 5 text has `Brisbane Baylands`, the split title `Transportation` /
`Impact Assessment`, `Final`, and `December 2024`. The wrapper edition and
underlying report date are distinct observations and must remain explicit.

The frozen semantic policy still fails: its allowed title lines omit the
observed `[REVISED]` and `F.1` form, and its page-1–3 same-page project phrase
expects `Brisbane Baylands` rather than the observed `City of Brisbane` footer.
Applying the unchanged pure qualifier to retained diagnostic text rejected the
title without another PDF read. The exact `Existing Traffic Conditions Memo`
phrase was not observed in pages 1–20. The TOC does list `Existing Traffic
Conditions` at printed page 26 and `Appendices` at printed page 120; that does
not establish that the required memo is present or absent elsewhere.

Evidence is preserved under root-relative
`pipelines/brisbane_baylands/task_06_recovery_v1/06c/`:

- `gate2_structural_diagnosis_v1/`: 5,627 bytes before inventory; initial helper
  stopped after 0.914 seconds on a scalar-object handling error, before text or
  rendering. It remains preserved as a failed diagnostic attempt.
- `gate2_structural_diagnosis_v2/`: 109,909 bytes before inventory; corrected
  helper completed in 2.690 seconds with peak sampled process-tree RSS
  270,680,064 bytes. It contains the reproducible diagnostic script, object/page
  relationships, first-20-page text, three renders, execution observations and
  frozen-policy rejection. Its inventory seals only these new diagnostic files.

The two runs together remained below 300 seconds, 2 GiB RSS and 8 MiB output.
Source size, modification time and inode were unchanged. The original failure
and all accepted artifacts remain unchanged. No source rehash, network call,
PDF repair, model execution, conversion, commit or push occurred. The
[independent diagnostic review](../../docs/specs/task06c_structural_diagnosis_review.md)
reviews the retained evidence without another source read. Documentation links
and `git diff --check` pass; no maintained implementation changed.

### Proposed qualification follow-up

Preserve the original PDF and failure. Record a reviewed exception limited to
these two thumbnail-only streams and explicit observed title/edition evidence;
other structural failures must still stop. A new qualification policy should
permit the observed revised Appendix F.1 heading and project/footer wording,
with the report title on page 5 as corroboration. Do not silently update the
frozen v1 request or declare it passed.

Before resolving the internal-evidence requirement, propose a new bounded local
check of physical pages 39–41 and 133–139, selected from the observed TOC and
page-14/printed-page-1 offset, plus one render of page 28 to confirm its body
renders independently of the thumbnail. These are candidate destinations, not
verified page-label matches. Reuse cached pages 1–20 without source rereads.
Use the same 300-second, 2 GiB RSS, one-thread, 8 MiB new-output and 64 GiB disk
limits. If the memo remains unlocated, report that result rather than expanding
the search or waiving it. This follow-up and policy disposition are proposed,
not executed or accepted. Conversion remains a separate gate afterward.


### Approved retained-source qualification outcome

The user approved proceeding with the narrow thumbnail exception, actual title
policy and targeted memo check, then requested a check-in before more work.
The follow-up read only physical pages 39–41 and 133–139 and rendered page 28;
previous pages 1–20 were reused from sealed diagnostic text. It found the
`Appendix A: Existing Traffic Conditions Memo` heading on page 136 and the
actual memorandum on page 137, headed `MEMORANDUM` and `Subject: Baylands
Specific Plan: Existing Traffic Conditions`. Page 133's TOC independently names
the memo. This is body-backed qualification, not acceptance from a TOC mention
alone. The memo cover and continuation headers retain their observed April 13
and April 14, 2023 dates without normalization or a claim of consistency.

Page 28 rendered without stderr. Root and an independent reviewer inspected
Figure 7, `Allowed Off-Street Parking and Driveway Locations`; its map, legend
and source caveat are visible. The reviewed structural exception is limited to
object `12649 0` through page 28 `/Thumb` and object `12168 0` through
`/Thumb/ColorSpace/3`, bound to the exact retained source digest and prior
object-reference evidence. Other object failures or body references do not
qualify for that exception. Specialized-decoder coverage remains an explicit
limitation; this source-identity decision is not an all-page usability review.

The new [retained qualification policy](../../configs/brisbane_baylands_2025_feir_task06c_retained_qualification_v1.json)
has file SHA-256
`6fb229182b7e77ea406c3436caf4a5dca10039fb3211ed36cd8cc21c61534e8f`.
It requires the exact revised Appendix F.1 cover line, same-page City of Brisbane
and Final EIR evidence, corroborating split report title on page 5, and the memo
heading plus actual body on pages 136–137. The original acquisition request and
its failed result are unchanged. `source_release/local_qualification.py` supplies
a pure, typed evaluator of retained facts and exact policy/evidence bindings;
it neither opens PDFs nor alters the maintained strict acquisition path.

All six dimensions passed: identity, evidence scope, structure, title, edition
and internal material. Fresh records are under root-relative:

```text
pipelines/brisbane_baylands/task_06_recovery_v1/06c/
  gate2_qualification_followup_v1/
  gate2_local_qualification_v1/
```

The follow-up evidence inventory seals 867,997 bytes before its own inventory.
The supervised source check completed in 1.288 seconds, with peak sampled
process-tree RSS 170,360,832 bytes, inside the 300-second/2-GiB/8-MiB limits.
No new source download, repair or hash occurred.

The local qualification directory contains `policy.json`, `observations.json`,
`disposition.json`, `source_record.json`, the reproducible `publication_script.py`
and a completion-last `completion.json`. The completion is 1,197 bytes,
SHA-256 `8d277ed8d8b8aeba800a591bfdc21bd88d4b3dd66936a62e4ff4d65cd2fbf1d2`,
with schema `er_commons.recovery.retained_source_completion.v1` and status
`qualified_with_reviewed_exceptions`. It references the original `source.part`
using its stream SHA-256 and unchanged size/mtime/inode snapshot. The original
failed namespace still contains exactly `source.part` and `failure.json`.
No source bytes were copied, renamed or rewritten, and the prior failure record
still verifies against its original digest.

The source-free reproduction/verification command is:

```bash
uv run python /Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06c/gate2_local_qualification_v1/publication_script.py --verify
```

It verifies compact receipts, source metadata and recomputed disposition, not
fresh source-byte equality. Independent review additionally verified the recorded
evaluator implementation digest. Future Gate 3 preparation must validate that
recorded implementation provenance/compatibility as well as the new receipt
schema; it must not treat the old acquisition's `completion.json` as present or
run the old `reuse-qualified` command against its failed namespace.

`make fix` and `make check` passed, including mypy across 470 source files and
**1,623 tests** (40.03 seconds). Sixteen new evaluator tests cover source, page,
reference, exception, body-use, render, title, edition and memo mismatches. The
[independent local qualification review](../../docs/specs/task06c_local_qualification_review.md)
found no blocking issue and verified the published receipt and original source
snapshot without opening the PDF. `git diff --check` and documentation link
checks passed. No accepted artifacts, original per-source manifests, chunked
conversion evidence or human review were changed; no commit or push occurred.

### Check-in before Gate 3

Gate 2 is now closed through the new reviewed qualification receipt, not by
rewriting the failed strict attempt. The next work is the separately authorized
Gate 3: bind this receipt into the maintained source/manifest processing adapter,
verify an installed local model inventory, freeze the measured 756-page chunk
plan, and execute fresh conversion/producer evidence within the already stated
resource envelope. Models remain unverified; cached directories alone are not
readiness evidence. No conversion or model loading has begun. Task 06G must
reuse the resulting sealed stages after that later gate; it has no new F1
conversion input yet.

### Gate 3 authorization and model-readiness stop

The user approved Gate 3 and requested background execution in a persistent
session. `tmux` is installed. The required inventory is absent; metadata-only
inspection found the accepted Heron cache snapshot but only a stale TableFormer
revision pointer with no weights. A filename scan of the external root and user
caches found neither a replacement inventory nor the required TableFormer files.
No PDF or model payload was opened for these checks.

The [Gate 3 preparation record](../../docs/specs/task06c_gate3_preparation.md)
owns the exact findings, four-range policy, future background resource limits,
and bounded model-remediation proposal. New configs preserve the qualified Final
source, 200-page core targets, one-page overlap, four CPU threads including
fallback, and a fresh processing lineage. The source adapter validates the
retained receipt and evaluator implementation before granting only the explicit
F1 processing exception. The background supervisor retains logs and resource
accounting and stops descendants across session boundaries.

The [independent preparation review](../../docs/specs/task06c_gate3_review.md)
closed both supervisor findings and passed 25 focused tests. `make fix` and
`make check` passed with mypy over 472 source files and **1,648 tests** in
38.98 seconds. Both prepared configs validate without opening source/model
payloads; documentation links and `git diff --check` pass.

The frozen contract requires a separate model-remediation proposal before any
download. No conversion, model loading, tmux production session, external source
manifest publication, model inventory publication, commit or push occurred.
Gate 3 remains approved but blocked on that prerequisite; it does not need to
be authorized again after approved remediation passes. Gate 4 and Tasks 06D–06H
remain inactive.

### Gate 3 model restoration and background launch

The user approved downloading the missing files. Restoration copied six cached
Heron files and downloaded only the two accurate TableFormer files at their
original immutable revisions. All eight match retained v4 file digests and
sizes. The [preparation record](../../docs/specs/task06c_gate3_preparation.md)
owns inventory/plan digests, restoration metrics, and the resolved cleanup cause.
The prior missing-model stop is resolved; no additional Gate 3 approval is due.

Fresh source-manifest and model bindings passed maintained validators without
rehashing the PDF or loading a model. Independent subagent review verified the
compact seals, installed model-folder expectations, all 756 page bindings,
launch script and resource controls. The prior 1,648-test implementation result
still applies: no maintained Python code changed during restoration/launch.

At 2026-09-10 21:15 PDT, launched tmux session `er-commons-06c-gate3` using
`06c/gate3_inputs_v1/launch.sh`. `caffeinate -i` prevents idle sleep while the
supervised command runs. The source, model, plan and launch records remain
under the fresh Gate 3 namespaces; accepted artifacts are unchanged.

Live status and logs, relative to the recovery root:

```text
06c/gate3_execution_attempt_v1/status.json
06c/gate3_execution_attempt_v1/command.log
06c/gate3_execution_attempt_v1/execution.json  # written when the command exits
06c/gate3_processing_v1/document_parse_evidence/
```

Attach with `tmux attach -t er-commons-06c-gate3`. The session may disappear
when its command exits; durable status/execution records remain authoritative.
Startup status was `running`. Conversion/producer completions are not yet
claimed. No recurring agent polling or automatic assistant follow-up was
scheduled. On return, inspect status and compact completions before choosing a
resume; never rerun a successful conversion merely to close Gate 4. No commit
or push occurred. Gate 4 closure and later tasks remain inactive.

### Gate 3 table-manifest failure and authorized resume

The first background invocation exited after 334.096 seconds with all four
range completions preserved. It failed before table-page processing because the
table resolver inferred the historical raw-release path rather than receiving
the explicit qualified processing manifest. Peak process-tree RSS was
7,182,811,136 bytes, with zero swap growth; this was an integration failure,
not a resource stop or source/model failure.

The user authorized correcting routing and resuming. The table request now
carries the producer's explicit manifest path. The table stage verifies the
manifest seal, source membership, digest/page expectations and qualified-source
receipt before using source metadata; it does not rehash the PDF. Historical
requests without an explicit path retain their existing behavior.

The original failed `pre_aggregate` directory is preserved at
`06c/gate3_processing_v1/attempt_diagnostics/attempt_v1_pre_aggregate/`,
including its old request, routing and table configuration. All completed range
directories are unchanged. The original supervisor failure remains under
`06c/gate3_execution_attempt_v1/`.

The resume preflight independently checks all four compact range seals and
requires the same conversion and plan identity after the code correction.
Records and a copied preflight script are under `06c/gate3_resume_inputs_v1/`.
The retry retains the same processing output root, uses a fresh supervisor
attempt, and has 86,065 seconds remaining from the original 24-hour execution
allowance. Prior attempt-log bytes are reserved against the total 32-GiB output
ceiling. No source, models or completed range conversion need to run again for
input verification; table reconstruction and aggregation still execute.

The [independent resume review](../../docs/specs/task06c_gate3_resume_review.md)
passed 29 focused tests, both fresh-process import orders, and the actual
source-free range/identity preflight. A circular import exposed by the cold
production startup check was corrected before launch. `make fix` and `make check`
passed: mypy over 472 source files, **1,658 tests** in 40.08 seconds. Documentation
links and `git diff --check` pass.

Relaunched at 2026-09-11 05:24 PDT in tmux session `er-commons-06c-gate3`, using
`06c/gate3_resume_inputs_v1/launch.sh`. The current durable status/log paths are
`06c/gate3_execution_attempt_v2/status.json` and `command.log`; its
`execution.json` is written on exit. These replace attempt v1 as the live
status location, while the earlier failure remains preserved. The resumed range
execution report confirms **4 reused ranges and 0 executed ranges**. At relaunch,
Gate 3 was running; its later terminal outcome is recorded below. No commit or
push occurred.

### Gates 3–4 outcome: sealed reusable handoff

The resumed Gate 3 supervisor completed successfully. It reused all four
accepted ranges and executed none, then completed the aggregate conversion and
producer stages. The sealed conversion is
`dconv1-b6c5f62355c98d7ad588c455caaa987f7c7d99f896a86a219f2b0821c5693356`
under `06c/gate3_processing_v1/document_parse_evidence/docling_conversions/`;
its `complete_with_warnings` completion has inventory SHA-256
`05c555fb3fb4cbf0e049312fc0bbda8eb7f5c38c8ec979b64e831c90a8b3c441`.
The sealed producer is
`prv1-01c8e77c10303f8d54d4a34ebe38b489699386897a8d4c78a931f371bafbcb36`
under `06c/gate3_processing_v1/document_parse_evidence/`; publication is
complete and its inventory SHA-256 is
`a2150e2473e2dbd4d73aff1a036625d4ce58da3a1ae46f4820da228f27f17211`.

Gate 4 reran the Task 06B metadata-only reuse readers for those stages and all
four ranges of plan
`dplan1-dc4cd61060268d03034abe695115c3365db5a74f1029c39be5feb0f72f808b43`.
It verified compact identity and inventory bindings, source membership, exact
managed-file accounting, terminal states, and the final resource record without
opening or rehashing the 68,389,743-byte PDF or any model payload. The
[independent Gate 4 review](../../docs/specs/task06c_gate4_review.md) found no
blocker. The final attempt completed in 494.955 seconds with 4,939,513,856-byte
peak RSS, 1,433,393,901-byte peak output, and zero swap growth. The first failed
attempt and its diagnostics remain preserved; they are not a reason to rerun
accepted ranges.

Task 06G resumes from these exact conversion and producer directories using the
Task 06B sealed reuse path and the original per-source manifests. It must retain
the Final-only substitution limitation: the receipt does not establish general
Draft/Final equivalence. It must also carry forward the documented qualification
limits and conversion warnings, including 85 Docling list-parent repairs and
zero reconstructed tables on pages 1, 6, 7, 9, 133, 135, 436, and 732. No
Task 06D–06F policy, Task 06G replay, collection publication, commit, or push
was performed.

## Task 06B interface handoff

Both Task 06B gates now supply the maintained
[command map](../../docs/pipeline_commands.md) and
[executed owner map](../../docs/specs/task06b_gate2_executed_inventory.md).
Use explicit current requests with original per-source accepted manifests and
seals; historical recipe validation does not reopen removed implementation paths.
Document/collection v3 supports declared replacement membership. Compact checks
must retain the shared verification budget and must not claim new payload-byte
equality. This handoff updates interfaces only; the task's provisional policy and
separate source, conversion, replay or review authorization boundaries still apply.
