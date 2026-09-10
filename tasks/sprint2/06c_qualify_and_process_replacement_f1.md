# Task 06C: Qualify and Process Replacement F1

Status: **provisional and inactive; revise from accepted Tasks 06A and 06B
before implementation. Source acquisition and conversion require separate
future authorization. This document authorizes neither.**

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

Pending. Record reviewed specification, authorization boundaries, observed
source metadata, qualified evidence, exact sealed stage identities, validation,
resource use, unresolved issues, and Task 06G resume point here at closure.

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
