# Task 15H — C001 structured-conclusion transformations and synthetic pilot

Status: complete (2026-10-22); judge execution not started.

## Goal and authorization

Write a consolidated transformations document using the eight agreed families,
then generate C001 candidate conclusions only. Fixed inputs: the exact question,
discussed required/optional reference, point IDs and Baylands overview. No judge
execution or provider calls. Reference perturbations are future work, not this task.

## Inputs and outputs

Inputs: accepted C rules and Task15G prompt/schema; the C001 two-list draft from
user discussion; source-only C001 packet selected by Task15F's sealed result.
Outputs: maintained transformation specification, a separately versioned C001
pilot reference (not a replacement benchmark release), candidate packets, expected
full R/O status vectors with overall decisions, independent reviews, coverage and
ambiguity exclusions, manifest/validation/completion seal and tracked result pointer.

## Plan and learning

Use the current strict Pydantic contract and existing external artifact conventions.
Reuse historical transformation concepts as provenance, not duplicate slots.
Author logically scoped changes; point-status expectations are judgments of actual
meaning, not automatic labels assigned by edit type. Preserve optional partial
coverage and the factual/relevance boundary. Avoid grey negatives from mere
qualifier deletion; prefer explicit same-scope incompatibility.

1. Publish the consolidated eight-family authoring contract before generation.
2. Pin the C001 discussion draft and canonical prompt/schema/context identities.
3. Author candidates with full proposed point-status expectations in bounded batches.
4. Independently review every candidate; repair clear defects with version history,
   exclude unresolved cases from scored inputs, retain exclusions with reasons.
5. Validate fixed inputs, exact inventory, deduplication, statuses and aggregation;
   seal external artifacts and update docs. Do not dispatch judges.

## Combined-defect coverage

Explicitly test two required omissions; required omission plus required
contradiction; required omission plus optional contradiction; two different-point
contradictions; a defect surrounded by correct content; and contradiction
precedence on one point plus a separate defect. Record actual multi-point effects
when reference meanings overlap. Do not force independent edits where C001 does
not support them cleanly. Compose from reviewed single-edit parents when possible.

## Validation and acceptance

All scored rows require independent review, complete status vectors, consistent
Booleans and fixed reference hashes. No duplicate model-visible payloads. Report
coverage exclusions and cross-point effects. Label status is independently
agent-reviewed, not human gold. This one-question familiar development pilot is
not held-out judge qualification. Validate artifacts and run git diff --check;
run package checks if package code changes. Review for ambiguity and leakage.

## Non-goals

No new questions, label/source perturbations, approved benchmark label edits,
reserved challenges, predictions, other questions, MiniMax, live provider calls,
commits or pushes. Frozen publications remain intact.

## Outcome

Published the consolidated [eight-family transformations contract](../../docs/specs/task15h_conclusion_transformations_v1.md)
and a sealed [C001 pilot dataset](../../docs/specs/task15h_c001_structured_synthetic_result.json).
There are 42 unique scored candidates: 20 expected pass and 22 expected fail,
with all eight expected R/O judgments per candidate (336 total). Every row has
an independent exact-hash review with full point rationales. These expectations
are agent-reviewed proposals, not human gold.

All eight families and six combined-defect objectives are covered. CD1 reuses
RC04 rather than duplicating its two-omission test. CD5 tests masking by correct
content with one actual defect. One isolated-R1-omission draft was excluded after
independent review because R2 can convey part of R1 implicitly; both competing
interpretations are retained. No required-reference wording was changed to make
that case easier to score. Cross-point effects are explicit, including O2/O4
partial overlap and no-added-risk contradictions of both R1 and O1.

The reference is the C001 discussion draft fixed for this pilot, not a replacement
approved benchmark label. Question, R/O text/IDs and exact Baylands-context prompt
are pinned across all inputs. Canonical source bindings, prompt/input/output schema
identities, authoring/review records, separate expected labels/statuses, coverage,
a read-only browser and completion inventory are included. Native samples are
ready for the explicit structured-C adapter; the historical prose loader is not
used. This is familiar single-question development material, not held-out testing.

Validation passed schema checks, complete/consistent vectors, fixed reference and
source hashes, payload deduplication, independent review hashes, all six combined
coverage mappings, excluded-draft review, and browser candidate coverage. The
completion seals 110 files. No runtime package code changed; artifact validation
and `git diff --check` are the appropriate checks. No provider/judge calls,
predicted-answer access, frozen-label edits, commits or pushes occurred.

Next: review or run this C001-only pilot with explicit model/repetition/budget
settings, keeping resulting execution artifacts outside the sealed dataset.
Judge semantic quality and stability have not yet been measured.
