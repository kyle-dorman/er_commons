# Task 07A.1: Repair Explicit Response-List Links

Status: **Complete; replacement inventory published and accepted, all 50 decisions
verified in separate project 2. Task 07A is ready for example selection.**

## Abstract and goal

Repair missed individual-response citations before returning to 07A example
selection. Recognize explicit lists such as “Refer to Responses O-Joint-63,
O-Joint-64, and O-Joint-66”, resolve each named response, and carry the additional
context into a replacement review project without requiring Kyle to relabel.
Keep this one bounded repair across the existing stage owners, not a reopening
of unrelated extraction or review work. Screening checkpoint: `4f8a4cf`.

## Inputs and confirmed finding

- [07A completed export](07a_screen_pilot_candidates.md#completed-human-screening-export)
  and [05H accepted input](../../docs/specs/task05h_final_result.json).
- Under `ER_COMMONS_DATA_ROOT`, the immutable decision backup is
  `pipelines/brisbane_baylands/task_07_pilot/07a/label_exports/20260924T171009Z/`.
  Verify its manifest before use. It holds 50 completed labels: 20 Great, 6 OK,
  24 Skip, plus exact reasons, reviewer and timestamps.
- The same parent contains `sample_20260923_v1/` (fixed selection/context) and
  `label_studio_trial/` (completed project 1). Preserve both and all global
  Label Studio projects. [Operation notes](../../configs/label_studio/README.md).
- `response_inventory/producer.py` recognizes singular `Response ...` but not
  plural/shared-prefix lists. O-Joint-74 has no outgoing links for the three
  named responses, although all target units exist. Singular shared-prefix
  lists currently match only the first item; repeated singular prefixes work.
- `relationship_baseline.py` already supports `response_response` edges and
  requires one target per mention. `contract.py` validates evidence and allowed
  label normalization. `pilot_screening.py` already renders individual context.
- A preliminary scan found plural forms in three saved context units used by
  five sampled cases. This is not the full affected-population census.

Read the current architecture and artifact contract. Use the 05D, 05E, 05F,
05G and 05H task outcomes only for the relevant execution and identity bindings;
[Task 05](05_build_curator_only_response_inventory.md) routes those owners.

## Plan and execution boundaries

1. **Bound the grammar and affected population.** Define explicit full-ID lists
   with singular/plural prefixes, commas, conjunctions and wrapped lines.
   Identify affected mentions against saved source text; do not infer targets
   from bare numbers or nearby comments. Account for unsupported forms.
2. **Repair and qualify the code.** Produce one mention per item, preserving
   exact raw-text spans/hashes and evidence for the shared prefix. Declare the
   normalization rule in the resolver and evidence validator. Require unique
   official-label matches; retain diagnostics for missing/ambiguous targets.
3. **Plan the minimal replay.** Identify concrete runnable commands, changed
   bindings and fresh artifact roots before execution. Missing mentions belong
   to 05D, new relationships/views to 05E. Establish whether existing page text
   can be reused by the maintained runner without reopening PDFs. Do not claim
   reuse until supported by that runner and the artifact contracts.
4. **Revalidate descendants.** Check 05F/05G bindings and report-link population;
   reuse unchanged results and review evidence only when their identity rules
   permit it. Recompose/review/publish a replacement through 05H. Review added
   links and changed context, with mechanical comparisons for unchanged data.
   Preserve the original accepted inventory. Use the current repair scope to
   determine necessary gates rather than blindly repeating historical phases.
5. **Transfer completed decisions.** Keep the existing project unchanged. Build
   a new project for the same 50 comments with repaired context. Match by stable
   comment ID, never Label Studio task ID or row order. Import human decisions
   as annotations, not predictions. Preserve original annotation/task IDs,
   reviewer and timestamps in migration provenance even if Label Studio assigns
   new IDs or timestamps. Test one migrated case before importing the rest;
   confirm retry behavior cannot duplicate tasks or annotations.
6. **Verify and hand back to 07A.** Export the replacement and compare all 50
   rating/reason sets exactly with the protected backup. Produce a small list
   of cases whose response context changed. Retain original decisions; optional
   follow-up review is separate and must not reset completion or replace labels.
   Resume selection of 6–10 authoring cases in 07A only after this handoff.

Creating this contract does not run the repair. At execution, resolve necessary
approval boundaries from the user's then-current authorization. Do not mutate
sealed inputs or the completed screening project. No need for a new user decision
at every internal stage when that stage is already covered by authorized scope.

## Outputs

Maintainable parser/resolver/validator changes with focused fixtures; a fresh
verified source/graph/release chain or an explicit unresolved publication blocker;
a compact added-link/context comparison; a separate migrated review project and
export; and a migration map binding old/new task IDs, stable comment IDs,
original annotations and old/new inventory identities. Records stay external.

## Research / learning checkpoint

Use Python's [match spans](https://docs.python.org/3/library/re.html#match-objects)
to preserve raw evidence when expanding a list. Compare the proposed records
with existing normalization and one-target-per-mention contracts before coding.
Review Label Studio's [annotation import](https://labelstud.io/guide/tasks) and
[task format](https://labelstud.io/guide/task_format) against installed 1.23.0.
Its import supports annotations, but exact reviewer/timestamp handling must be
verified locally. Explain why adding `s?` alone cannot recover trailing targets
and why original human decisions remain separate from changed evidence context.

## Validation and review pass

- Test plural and singular lists, repeated prefixes, conjunctions, wrapped lines,
  exact item/prefix spans, punctuation, missing/ambiguous IDs and prose false
  positives. Keep ranges/abbreviations unresolved rather than guessing.
- O-Joint-74 must gain the three expected distinct response edges. Verify that
  ordinary singular links remain unchanged and no unrelated comments enter
  review context. Test cycles/deduplication in context traversal; the 07A adapter
  already follows response-directed edges to closure, while baseline views are
  bounded. Make the intended review-context closure explicit.
- Compare source text, unit boundaries and IDs before/after. Unexpected changes
  stop promotion for investigation. Do not silently remap changed comment IDs.
- Run appropriate `make` checks with bounded resource usage; do not rerun large
  extraction/model workloads or install packages merely to test this parser.
- Independently review parser readability, evidence correctness, replay scope,
  and label-transfer safety. Check every export checksum and all 50 decisions.

## Acceptance criteria and non-goals

The explicit list resolves correctly, added relationships are reviewed, the
replacement inventory has a valid accepted handoff, and all 50 human ratings
and skip-reason sets survive a verified migration. The original project/export
remain unchanged. Record any follow-up candidates without requiring a new pass
through the batch. Update 07A routing to resume example selection.

No new sampling, model screening, automatic GR6/Chapter 14–16 labels, general
range inference, UI redesign, unrelated Task 06 fixes, fresh Draft EIR extraction,
blanket substantive re-review, or authoring-case selection within this task.

## Execution notes

The execution instruction authorized repair, affected replay, acceptance,
replacement-project creation, annotation transfer and a local commit, with no
push or example selection. Evidence is retained below
`pipelines/brisbane_baylands/task_07_pilot/07a1/` under `ER_COMMONS_DATA_ROOT`.
The original 05H result and designation bytes are preserved in `preflight/`.

The parser adds one mention per explicit full-ID item, with separate exact
prefix/item fragments and a hash of their concatenated raw text. Adding `s?`
alone would recognize the prefix but still lose trailing items. A shared grammar
checks both production and resolution evidence; bare numbers, abbreviations and
ranges do not supply inferred targets. Existing singular mention records remain
unchanged. The corpus census found 89 new mentions across 41 units, all uniquely
resolvable, and 11 excluded plural ranges.
Wrapped whitespace within a page is supported; cross-page lists, hyphen-split
IDs and abbreviated IDs remain unsupported. Historical singular range-prefix
behavior is preserved; this repair adds no range inference.

The maintained saved-evidence adapter validated the historical source candidate,
observations and rendered qualification evidence before creating fresh producer
receipts. It reopened no PDF, installed no package and ran no model. All 744 page
evidence rows matched; 676 existing visual decisions were renewed on that exact
evidence. All original text, unit IDs/boundaries and 1,270 mentions were preserved.
The new graph retains all 1,538 original relationships and evidence and adds 87
relationships from 89 mentions. Four additions are general-response-to-response
links and 83 are response-to-response links. O-Joint-74 has all three required
targets. Directed review context follows links to closure with cycle deduplication
and never traverses back to unrelated comments.

The reference baseline remains valid because the report-reference population is
identical. The fresh 05G replay verifies all 511 outcomes against the accepted
predecessor, allowing only the explicitly verified source/graph provenance
replacement: 468 links, 43 nonlinks and all target evidence/limitations remain.
The unchanged 06H handoff continues to describe its historical inputs; the new
request separately binds the replacement pair and proves source compatibility.

Python's [match spans](https://docs.python.org/3/library/re.html#match-objects)
provide exact source offsets. Label Studio's [import guidance](https://labelstud.io/guide/tasks)
and [task format](https://labelstud.io/guide/task_format) distinguish human
annotations from predictions. Installed 1.23.0 preserves the reviewer but assigns
new annotation timestamps during import; full original annotations and decision
times are therefore retained separately in migration provenance. Changed response
context does not change a human rating or create a new human decision.

Release review closed 121 obligations with no pending or conflicting decisions:
four byte-identical cards, 57 provenance-only renewals, 54 cards with explicitly
reviewed graph/context additions, and six new graph/cycle obligations. All old
source slices remain. The new M-OSEC-2/34 cycle is explicitly supported; the
existing 172-unit component expands to 175 through three explicit GR6 referrals.
Cycles remain informational. Independent review verified the assembled payload
digest, exact decision/card membership, evidence references, publication controls
and maintainability; these are AI-assisted composition checks, not new human
screening decisions or a substantive re-review of entire response components.


## Accepted outcome and handoff

The [final result](../../docs/specs/task07a1_final_result.json) binds the complete
replacement chain and checksummed external evidence. Accepted inventory:
`inventoryv1-8b566f29a89653e202c67c1aa3c83616d03ce40ae9f9fe70c8329ca00a1e6696`.
The standard 05H designation points to it; the original inventory, acceptance
record, original 07A sample, protected export and completed project 1 remain
unchanged. Publication bytes match the finalized container exactly.

The replacement is [Label Studio project 2](http://127.0.0.1:8097/projects/2/data?tab=1&labeling=1),
`Task 07A.1 · Repaired links · 50 saved decisions`. All 50 comments and annotations
are complete: 20 Great, 6 OK, 24 Skip. One changed-context case was imported and
verified first; export/reconciliation then identified exactly 49 missing cases.
The remaining import was followed by separate reads of all 50 tasks, two equal
exports, exact result/rating/reason/reviewer comparison, and verification of all
13 migration artifact checksums. The original project/export and global Label
Studio database metadata/project settings remain unchanged.

Under the external `07a1/` root, `sample_repaired_v1/` retains fixed selection
provenance and refreshed context. `migration/label_studio_export.json` and
`migration/migration_map.json` preserve new and original task/annotation IDs,
original annotations/reviewer/timestamps, and both inventory identities.
`migration/manifest.json` seals the export, map, canary and final verification.

| Case with new response context | Preserved rating |
| --- | --- |
| O-Joint-74 | Great |
| O-YIMBY-8 | Skip |
| M-OSEC-50 | Skip |
| RA-Caltrain-6 | Skip |
| O-SAMCEDA-6 | Skip |

Exact added unit/relationship IDs are in
`sample_repaired_v1/context_changes.jsonl`. These are optional follow-up cases;
no decisions were reset or automatically changed. Task 07A may now select 6–10
examples, but this task selected none.

Validation: `make fix` passed without additional changes. Final `make check`
passed formatting, lint and typing, with **2,549 passing tests** and the same
three documented historical Task 06G generation tests failing because the current
repository base differs from their frozen accepted basis. Their code/fixtures
were not changed. Focused parser/evidence tests (119), final H tests (57), and
migration/context/screening tests (19) passed. The final full run includes the
new replacement-census regression. `git diff --check` passed.

Independent review covered parser/evidence correctness, source reuse, all added
links and changed cycles, reference outcome equivalence, assembled release,
human maintainability, and migration safety. Source and graph replay, reference
replay, prepare/review/finalize/publish/accept all completed. Supervised runs
reported zero swap growth. Recoverable preparation attempts are retained as
nonterminal evidence; an overlong Label Studio title was shortened after a
rejected create request was verified to have created no project. No extraction,
package installation, destructive cleanup, push, or example selection occurred.
