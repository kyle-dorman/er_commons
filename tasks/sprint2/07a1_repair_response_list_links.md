# Task 07A.1: Repair Explicit Response-List Links

Status: **Next task; contract prepared, implementation and replay not started.**

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
