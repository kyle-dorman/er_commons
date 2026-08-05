# Task 03G: Test Extraction Breadth and a Representative Full Pilot

Status: **open umbrella; Tasks 03G.1 and 03G.1a are complete and accepted**.
Task 03G.2 is active for no-PDF preparation only. Source verification and PDF
processing require a separate user approval after preparation is reviewed.

## Abstract

Test the maintained extraction path in two deliberately small steps. Task
03G.1 runs a fresh diagnostic smoke over at most ten deterministic physical
pages from each of the 35 model-corpus PDFs. Task 03G.2 then runs the real
complete two-stage workflow from fresh inputs on three full documents: the main
Draft EIR, Appendix D, and Appendix P. If either subtask exposes a material
failure, add the smallest remediation subtask and rerun the affected check.
Task 03G closes only after the user accepts the smoke, full pilot, and any
required fixes. Task 03H remains provisional until then.

## Goal

Get broad, inexpensive evidence that every model-corpus PDF can enter the
maintained parser path, then get complete-workflow evidence from a small varied
pilot. This is POC validation, not a production reliability program: use
simple deterministic checks, investigate failures that actually occur, and do
not add speculative failure exercises or per-document human acceptance systems.

## Subtasks

1. [Task 03G.1](03g1_smoke_all_model_corpus_sources.md): run a fresh bounded-
   page diagnostic smoke across all 35 model-corpus sources. Partial-page
   artifacts are diagnostic evidence only and cannot impersonate a complete
   `docv1-` candidate, corpus index, resolution pass, or Task 04 handoff.
2. [Task 03G.1a](03g1a_remediate_smoke_extraction_failures.md): after Task
   03G.1 closes, remediate the four selected warning, rotated-geometry,
   zero-output table-region, and continuation failures behind separate review
   and execution gates.
3. [Task 03G.2](03g2_run_three_document_full_pilot.md): after the smoke and
   required remediation are accepted, run a fresh complete two-stage pilot over
   `deir_main`, `deir_appendix_d`, and `deir_appendix_p`; then invoke it again
   to verify checksum reuse.
4. Add further Task 03G.x contracts only for concrete failures or policy
   questions exposed by Tasks 03G.1 or 03G.2. Do not prebuild hypothetical
   recovery machinery.

## Accepted decisions

- The smoke covers every `model_corpus` source with at most ten physical pages
  chosen by one corpus-wide deterministic rule; it is not a truncated
  complete-document extraction.
- Smoke and pilot start fresh in new task-owned artifact namespaces. Historical
  Appendix P candidates remain immutable evidence and are not reused as the
  first pilot build.
- The full pilot contains exactly three model-corpus documents: the complete
  main report, Appendix D, and Appendix P. Final EIR Volume 4 and standalone
  comment PDFs retain their curator-only and QA-only roles outside Task 03.
- Every selected source runs the same automatic machine contracts. There is no
  separate human validation or acceptance record per file. Appendix P's old
  bounded authorization remains historical, source-specific evidence and does
  not authorize the fresh pilot candidate.
- Do not simulate a failure. If a real failure occurs, retain its ordinary
  diagnostics, stop at the declared subtask boundary, and write a bounded
  follow-up task.
- Task 03G.2 proves one fresh build and one checksum-reuse invocation. It does
  not require repeated isolated rebuilds or a production-grade reliability
  study.
- Requested visual evidence stops at a checksummed render request and recipe.
  Task 03G does not have to generate or review the renders.
- Task closure and permission to proceed are distinct. A well-documented
  failed subtask may be complete as an experiment while Task 03G remains open
  and Task 03H remains blocked.

## Inputs

- accepted Tasks 03A through 03F.4 and current production code;
- the non-executed post-03G.1a production recipe
  `exv1-a0908c8fad342acde9d195a4223391bef29884cea1711c66d611f13fa995adee`
  as predecessor evidence only; Task 03G.2 must derive a new pilot recipe that
  binds its three fresh source-specialized owner plans and downstream lineage;
- the sealed ordered 35-source `model_corpus` manifest;
- maintained `extraction run-document`, `extraction run-scope`, and
  `extraction validate-handoff` interfaces;
- candidate-neutral comparison and render-request support in
  `er_commons.extraction_review`; and
- existing attempt, timing, peak-memory, output-size, warning, and machine-
  observation records.

## Outputs

- accepted Task 03G.1 smoke evidence or a concrete remediation subtask;
- accepted Task 03G.2 complete pilot evidence or a concrete remediation
  subtask;
- explicit identity/configuration handling for new smoke and pilot inputs,
  without rebinding historical candidates;
- one combined pilot-level structural and resource summary rather than 35
  separate human validations;
- a candidate-neutral render request and reproducible recipe only;
- POC-sized Task 03H settings supported by the observed smoke and pilot; and
- an explicit user decision to close Task 03G and revise Task 03H, or to keep
  Task 03G open for another bounded fix.

## Research / learning checkpoint

Use the maintained interfaces and accepted Task 03F.4 boundaries as the primary
technical references. Preserve these explanations in the outcomes:

- Partial-page breadth testing answers whether varied PDFs enter the parser and
  routing path; it does not prove complete-document publication.
- A fresh complete pilot answers a different question from checksum reuse. The
  first checks construction; the second checks safe restart/reuse.
- Corpus-wide automatic invariants scale better than separate human acceptance
  records. Human judgment is reserved for aggregate pilot sufficiency and
  concrete anomalies.
- A POC should expose real failure mechanisms without implementing recovery
  cases that have not occurred.

## Review pass

- **Scope honesty:** smoke artifacts cannot claim complete-document or corpus
  completion; the pilot uses the complete production path.
- **Freshness:** first smoke and pilot invocations do not checksum-reuse old
  Appendix P or Task 03F candidates.
- **Identity:** new code/configuration is either included in the appropriate
  identity or explicitly proven diagnostic and outside production identity.
- **Scalability:** automatic validation is corpus-wide and aggregate; no
  per-file human acceptance workflow is introduced.
- **Task boundaries:** comments remain outside Task 03, Task 03G review remains
  non-authoritative, and Task 03H alone owns all-35 complete extraction and
  terminal accounting.

## Validation

Each execution subtask owns its exact runtime checks. Across the umbrella:

```bash
make validate-extraction-contract
make check
git diff --check
```

Task 03G.2 must also run the maintained read-only `extraction
validate-handoff` command on its published pilot scope. No task may call a
partial-page smoke artifact a valid complete-document handoff.

## Closure criteria

- Task 03G.1 has an accepted outcome after any required smoke remediation.
- Task 03G.2 has an accepted outcome after any required full-pilot remediation.
- The first complete pilot build is fresh and its second invocation verifies
  checksum reuse.
- No known failure that the user considers material remains unresolved.
- The user explicitly accepts the Task 03G outcome and authorizes revising Task
  03H.

## Non-goals

- production-grade fault injection, chaos testing, or reliability engineering;
- complete extraction or corpus accounting for all 35 PDFs;
- separate human validation or acceptance records for every source;
- generated review renders or authoritative Task 04 dispositions;
- Final EIR response/comment extraction;
- OCR fallback, generative repair, or document-specific silent correction;
- benchmark case selection, retrieval, generation, judging, or evaluation; or
- claiming corpus-wide accuracy from the smoke or three-document pilot.
