# Task 05C: Build and Qualify the Response Inventory Pilot

Status: **complete and accepted**.

Accepted 2026-09-08. Acceptance is bound to
`completionv1-5853fa56753aa6e032687cdd727c72bac1c8cec0abf34cc6d2fac1e9b358e571`
and its managed inventory. It authorizes revision of the provisional Task 05D
contract from this outcome, but not the 744-page source run, Volume 5 access,
cleanup, or push.

## Abstract

Implement the smallest maintainable producer satisfying the accepted Task 05B
contract, then qualify it on the accepted 89-page vertical slice covering every
observed Volume 4 structural regime. Keep the MVP narrow: one isolated command,
one portable run specification, operational range checkpoints, one completed
pilot candidate, and explicit diagnostics instead of speculative repair.

## Goal

Expose structural, scaling, recovery, and usability failures before committing
to the 744-page run.

## Authorization gates

The source-free implementation gate is complete. Source access remains inactive.

1. **Source-free implementation gate:** after explicit authorization, implement
   the command, run-spec/config, parser rules, fixtures, validators, tests, and
   restart simulation without opening, rendering, extracting, hashing, or
   copying the source PDF. Use checked-in fixtures and compact accepted Task 05A
   metadata only. Stop and present the gate outcome.
2. **Pilot source-read gate:** only after a second explicit authorization, open
   the source container and extract, compare, or render exactly the physical
   pages listed below. Do not traverse document-wide page-label or outline
   metadata, access Volume 5, add context pages, or recompute the source hash.

Authorization of either gate does not authorize the full-volume Task 05D run,
cleanup, commit, push, or any later Task 05 stage.

## Inputs and binding

- Accepted Task 05B specification, schema, fixtures, validator, and identity
  recipe at repository commit `c90d846`. The 05C activity binds the checked-in
  schema, run configuration, and producer code through their required digests;
  no new Task 05B dependency role is needed for the MVP.
- Accepted Task 05A completion under
  `working/05a/source_free_v1/records/task05a_completion.json`. The
  `task05a_completion` dependency identity is the SHA-256 recorded for that
  exact path and byte size by `task05a_acceptance.json`, not an invented typed
  completion ID.
- Frozen `feir_volume_4` source record. Preflight checks its source ID, release
  membership, expected path, recorded byte size, and terminal source-release
  state without rereading the PDF solely to hash it.

The activity and its managed-file inventory must carry identical ordered
dependency references. The source-free validator must reject a mismatch.

## Exact bounded pilot

The proposed Task 05A selection is adopted as the Task 05C pilot: 89 one-based
physical pages in 14 ordered, non-overlapping ranges.

```text
1-5, 23-25, 31-44, 82-92, 154-158, 171-175, 179-185,
368-372, 551-555, 575-577, 668-671, 684-691, 720-726, 738-744
```

These ranges cover front matter and blanks; contents and General Response
boundaries; representative General Response starts and ends plus the advertised
General Response 9 placement exception; section openers and rosters;
zero-comment, ordinary, cross-linked, multi-page, revision, figure/table,
meeting, continuation, mixed, and ambiguous structures; known greedy-pairing
failures; and terminal behavior. They are a subset of the 195 pages profiled in
Task 05A, but that earlier read does not authorize reopening them for this task.

Range `368-372` deliberately retains a right-censored boundary from the accepted
profile. Validate the observed comment start and continuation through page 369
and the response start on page 370, but do not guess, bridge to range `551-555`,
or read pages `373-550` to close the response. Preserve the complete comment,
the response-start evidence, and a terminal `unit_boundary_ambiguous` warning
for the open response tail; do not publish a complete response unit. This
expected bounded-scope warning is not by itself a material contract failure.

## Outputs

- A typed package-backed producer exposed through
  `er-responses build --run-spec <path>`, with structured logging and bounded
  restart behavior. The adapter must not modify the sealed Task 04D central CLI
  module.
- One checked-in portable run-spec schema and pilot configuration naming the
  exact inputs, ranges, output namespace, cache policy, digests, and stop rules.
- One bounded `pilots/<pilotv1-id>/` candidate without source bytes or copied
  upstream payloads. For this MVP, `pilotv1-id` reuses the canonical hash suffix
  of the final combined 05C `activity_id`; it is a namespace label, not a new
  record type or final publication identity.
- Activity, page, page-continuation, marker-candidate, source-span, commenter,
  submission, source-unit, membership-claim, raw reference-mention,
  source-placement-exception, diagnostic, managed-file-inventory, and
  stage-completion records for the selected ranges. Task 05C emits no semantic
  relationship edges or Draft EIR links.
- Compact per-range checkpoint receipts, a fixture/evidence comparison,
  repeatability report, error register, runtime and storage observations, and a
  bounded human visual-review packet.
- Proposed Task 05D amendments based only on observed failures. Do not silently
  change policy during the source run.

## MVP restart and completion contract

The final pilot uses one 05C activity declaring all 14 ranges and one terminal
managed inventory and completion record. Each contiguous range is only an
operational restart unit, not a separately accepted semantic activity:

- write one range into temporary working space;
- check its exact page count, parseability, internal references, and deterministic
  digest before writing a compact receipt;
- reuse a receipt only when the run-spec digest, code/schema/config digests,
  range, source binding, file sizes, and semantic digest still match; and
- after all receipts close, assemble and validate the combined candidate, then
  write its managed inventory and completion record last.

An interrupted or invalid range is regenerated without rerunning valid ranges.
Range receipts and temporary shards cannot impersonate the completed pilot and
may remain replaceable working evidence. This deliberately avoids adding a
checkpoint record type or workflow framework for the MVP. Cross-page
continuation may connect only adjacent pages inside one declared range; no unit
or continuation may bridge a gap between pilot ranges.

A successful 05C completion records and reconciles exact counts for declared
and completed ranges; declared and emitted pages; marker candidates; spans;
commenters; submissions; source units in total and by comment, response, and
General Response kind; membership claims; reference mentions; placement
exceptions; diagnostics; and open range-boundary diagnostics. Acceptance
requires 14/14 completed ranges, 89/89 pages, and zero failed ranges, but it does
not require all eight General Response units. Every selected page has one page
record and primary state; every accepted or rejected marker has a disposition;
non-unit content is explained by page state or an explicit diagnostic. The
validator must also require General Response 9's placement exception to cite
nonempty same-source evidence from the selected pages and must reject an
activity/inventory dependency mismatch.

## Research / learning checkpoint

Confirm the maintained `pypdfium2` page-local text and geometry boundary and the
Poppler comparison/render interfaces already selected by Task 05A. Record exact
tool versions and explain why the source-specific parser remains narrow glue.
Explain the operational range receipt and combined completion behavior in plain
language. Reopen package selection only if implementation evidence reaches one
of Task 05A's recorded escalation triggers.

## Plan

1. After source-free authorization, finalize the run-spec schema, source-access
   adapter, deterministic parser, record materializer, range-receipt behavior,
   and validators against fixtures only.
2. Prove source-free determinism, interruption/restart behavior, completion-last
   publication, count reconciliation, dependency closure, and expected failure
   paths. Run the source-free and repository gates, then stop.
3. Present the exact 89-page plan and source-free results for separate pilot
   source-read authorization.
4. If authorized, process only the accepted ranges in order. Stop on a material
   contract failure rather than adding pages or repairing policy in place.
5. Compare native extraction with Poppler, render the selected pages, perform
   the bounded visual review below, record findings and resource use, and
   propose bounded 05D amendments.

A material failure is a source-binding mismatch, invalid anchor or schema,
unclassified page, new structural regime that the contract cannot represent,
non-deterministic semantic output, unsafe restart behavior, or extraction/render
disagreement that cannot be resolved by an explicit diagnostic. Recognized
ambiguity, the declared page-372 censoring, and isolated non-material warnings
may close as `complete_with_warnings` when fully accounted for.

## Validation

- Validate the source-free fixtures before any PDF access.
- Account exactly for all 89 selected pages and all 14 declared ranges.
- Cover observed start/end boundary forms without extracting all eight General
  Responses merely to satisfy the pilot.
- Require General Response 9 placement evidence from the selected Volume 4
  pages without opening or synthesizing a Volume 5 unit.
- Compare PDFium and Poppler tokens on all selected pages. Treat token-multiset
  F1 below `0.98` as a review trigger, not an automatic transcription; every
  material disagreement requires a visual disposition.
- Render all 89 pages once at a recorded fixed setting into replaceable cache.
  Visually review the first and last page of each range; all pages in ranges
  `368-372`, `551-555`, and `668-671`; pages 2, 4, 38, 39, 83, 84, 721, 722,
  and 744; and every page flagged for disagreement, invalid geometry, revision
  markup, layout exception, ambiguous marker, or range-edge continuation. Expand
  review only to implicated pages already in the authorized pilot.
- Prove identical combined semantic output on a clean repeat and after at least
  one simulated interruption with completed-range reuse.
- Measure runtime, maximum resident memory, and peak Task-05-owned working space;
  verify no source or upstream payload copying.
- Complete maintainability review before recommending the producer for 05D.
- Run focused tests, `make validate-response-inventory-contract`, `make check`,
  and `git diff --check`.

## Review pass

- **Architecture:** Is the producer thin glue over maintained PDF access, with
  the isolated CLI and source boundary obvious?
- **Maintainability:** Are parsing rules, failures, diagnostics, range receipts,
  and fixtures readable and independently testable?
- **Operations:** Are runtime, working-space use, logging, stop behavior, and
  recovery bounded enough for the complete run?
- **Source fidelity:** Do selected text, boundaries, marker evidence, and page
  anchors match every reviewed render?

## Acceptance criteria

- The source-free gate closes before any PDF access, and the separately
  authorized pilot accesses only the 89 listed pages.
- The pilot accounts for every selected page, range, marker disposition, and
  structural gap through a valid record or explicit diagnostic.
- Known regimes produce correct units or explicit diagnostics; no material
  contract failure remains open.
- Repeated and interrupted construction produces the same combined semantic
  digest, and completion cannot be published from partial range receipts.
- The producer is readable, typed, testable, restartable, and operationally
  bounded without a new framework or unnecessary abstraction.
- The accepted pilot candidate has matching activity/inventory dependencies,
  reconciled counts, nonempty General Response 9 evidence, and no copied source
  or upstream payload.
- Every output-affecting repair needed for 05D is explicit in the proposed
  amendment; none is hidden inside the full run.

## Source-free gate outcome

The MVP producer, strict run specification, exact-range authorization check,
range receipts, source-record materializer, PDFium adapter, Poppler comparison
and render plan, visual-review gate, completion-last workflow, CLI, schemas,
fixtures, and tests are implemented. Synthetic interruption tests prove that
closed ranges are reused and cannot publish a terminal pilot by themselves.
Unknown nonempty layouts stop rather than being silently classified; General
Response contents entries require body-heading evidence; General Response 9 is
always an exception rather than a unit; and the expected open tail is limited
to `Response M-OSEC-137` in the exact pilot.

The source PDF was not opened, rendered, extracted, hashed, or copied during
this gate. The next action, if separately authorized, is to run only the 14
declared ranges. The first pass produces a nonterminal review packet. A terminal
candidate can be written only after every required selected-page render has an
explicit accepted visual disposition.

## Pilot outcome

The separately authorized source run accessed exactly the 89 declared physical
pages and completed all 14 ranges. It published
`activityv1-5ef86aaad50e772cf07b9153e333e36672c503b3ab1c922a0290be9fb8a6df85`
and
`completionv1-5853fa56753aa6e032687cdd727c72bac1c8cec0abf34cc6d2fac1e9b358e571`
with semantic digest
`ac874b8671ea40a07d76602d35c404dc641bb2fd7338178eb838b5ff2af145d3`.
The completion status is `complete_with_warnings`; its only diagnostic is the
predeclared open `Response M-OSEC-137` tail at the right-censored page-372
boundary.

The reconciled inventory contains 89 page records, 448 marker candidates, 381
source spans, 40 commenters, 13 submissions, 185 source units (91 comments, 91
responses, and General Responses 1-3), 16 membership claims, 124 raw reference
mentions, and the one General Response 9 placement exception. Every selected
page was rendered at 96 DPI. The corrected required 58-page visual-review set was
accepted; the minimum PDFium/Poppler token-multiset F1 was `0.98316498`, with no
page below the `0.98` trigger.

The final fresh source pass took 20.43 seconds and reached about 103 MiB maximum
resident memory. The completed cache occupied about 21 MiB and the published
candidate about 956 KiB. No source or upstream payload was copied. A clean
repeat reused 14/14 range receipts and reproduced the same activity,
completion, and semantic digest. The run used `pypdfium2 5.12.1` for bounded
page-local text and geometry and Poppler `pdftotext`/`pdftoppm 26.07.0` for the
independent comparison and rendering boundary.

The source evidence justified a small set of reusable parser rules rather than
document-name exceptions: structural headings require layout evidence or a
numbered all-uppercase form; EIR title pages require generic title and
preparer/addressee signals; contents/table listings, image-dominant pages,
running-header continuation pages, labeled blanks, rosters, official letter
codes, and General Response membership lists each have narrow observable
criteria. Ambiguous marker evidence is added to the visual-review set before a
terminal candidate can publish. These rules and their focused tests are the
proposed Task 05D baseline; no further policy expansion is warranted by this
pilot.

## Human code-quality gate

The reopened gate found and repaired real closure blockers. Missing character
geometry now triggers visual review, which expanded the formal set from 48 to
58 pages; the ten newly implicated pages were inspected and accepted. A strict
qualification validator now requires exact ordered page coverage, settings,
observation identity, safe nonempty renders, and reconciled review counts before
fresh or cached evidence can publish. Failed range work writes an atomic
diagnostic receipt and retains its traceback, Poppler calls have bounded
page-specific failures, and the CLI exposes range progress at INFO level.

For human editability, exact pilot and qualification constants now have one
documented policy owner. Cached observations reject coercible booleans, invalid
intervals, malformed boxes, and nonfinite geometry. General Response fallbacks
use complete heading evidence, reject contents rows, tolerate nonprinting PDF
hyphen controls without changing raw text, and require contextual evidence for
the General Response 9 routing exception. Page-state precedence is a pure,
table-tested classifier. The contract validator is split from one 236-line,
complexity-64 dispatcher into six named phases with a shared immutable index;
all response-inventory functions pass the explicit Ruff `C901` complexity gate.

The repaired producer regenerated the exact pilot with General Responses 1-3,
the same 185-unit accounting, 58 accepted visual dispositions, and the expected
single range-boundary warning. A clean repeat reused all 14 receipts and
reproduced the activity, completion, and semantic digest above. This closes the
maintainability, editability, readability, and debugging gate without expanding
the authorized page scope or building a new framework.

Final verification passed formatting, lint, full-package typing, the explicit
Ruff `C901` complexity check, all 1,261 repository tests, run-spec binding,
managed-file closure, and validation of the 1,359-record published bundle.
Three independent read-only reviews found no remaining architecture,
operations, parser-editability, or human-maintainability closure blocker.

## Non-goals

- Processing all 744 pages, reading unlisted context or Volume 5, resolving
  semantic relationships or Draft EIR targets, outcome classification, or final
  publication.
- Global commenter deduplication, fuzzy or model-based parsing/linking, rich
  checkpoint orchestration, a new provenance ontology, or perfection beyond the
  observed MVP regimes.
- Preserving unlimited working attempts or turning pilot files into the
  canonical inventory by renaming them.
