# Task 09A.2 — Fresh development synthesis with point expectations

Status: complete with limitations, October 11, 2026. All 19 development cases
generated and published; 12 proposed expectations remain excluded from comparison.

## Abstract and goal

Regenerate the existing development synthetic slots from approved references and
source packets, producing answers and point/conclusion expectations together.
Preserve v1, its reserved variants and the frozen benchmark split. No retroactive
labeling of saved synthetic answers and no judge execution.

## Inputs and outputs

Use the sealed 09A result pointer, reservation metadata, original development
reference/source packets and the current two-stage grounding semantics. Read no
old synthetic answer payloads, reserved payloads or test content. Metadata IDs
identify the 423 eligible development slots across 19 cases; excluded and reserved
slots are not regenerated. Bind predecessor identities but assign fresh variant
IDs. Retain original reference/control bytes and source evidence.

Publish a new external task_09 namespace with immutable attempts, full new answers,
separate expectations, exact edits, adequacy proposals, source-linked rationales,
slot mappings, explicit ambiguity/failure accounting and checksummed completion.
The original 118 reserved IDs remain external, unchanged and unannotated; do not
create a replacement reservation or claim this version contains final-check labels.

## Plan and semantics

1. Verify metadata boundaries and approved source packets; preserve unrelated 09E
   work. Implement a versioned schema/prompt and narrow validation extension.
2. Cover every non-conclusion supporting, qualification and context point once.
   A point passes only when all substantive assertions have actual cited support
   and proper qualification; completeness relative to the question is separate.
3. Retain compound points and shared/multiple sources. Failed points include exact
   unsupported assertion substrings and reasons; source locators use literal spans.
4. Generate clean_abstention and conclusion_supported with conclusion rationale and
   unsupported premise IDs. Scores: unsupported conclusion0; supported conclusion
   plus any failed point1; otherwise2; clean abstention N/A. No averaging or labels
   for centrality/confidence. No-points substantive conclusions still require checking.
5. Reuse global verification_status/ambiguity. Unknown decisions remain explicit
   nulls under unresolved status, excluded from comparison; false is not unknown.
6. Include a separate not_supported annotation for unsupported substantive content,
   plus an insufficient-evidence-response annotation to distinguish abstention intent.
   Record both meanings separately: unsupported substantive content versus an
   answer explicitly reporting insufficient evidence.
7. Qualify offline and small fresh authoring smoke, then use established Astra route
   for all allowed slots. Two infrastructure retries and one named correction remain
   bounded; preserve attempts and continue unaffected cases. Full point-annotated
   jobs use a recorded 60-minute timeout after the original 20-minute window
   timed out on all first three cases; historical callers retain 20 minutes.
8. Independently review schemas/boundaries and stratified generated source evidence,
   verify restart and publication, report all failed/unresolved slots honestly.

## Research / learning checkpoint

The current staged-grounding specification owns evaluator semantics; this request
supersedes old materiality-based synthetic G1 wording. JSON Schema's
[null guidance](https://json-schema.org/understanding-json-schema/reference/null)
distinguishes explicit null from missing data. Reuse the existing JSON Schema
library and whole-answer evidence fields; literal linkage checks do not prove
semantic correctness. Generated expectations remain uncalibrated proposals.

## Validation and acceptance

Test exact point-ID coverage, assertion/source substrings, citation ownership,
all score branches, conclusion-only and substantive abstention, compound points,
unknown decisions, metadata-only partition intake, preserved reservation identity,
restart and no-clobber publication. Run focused tests, make fix/check and diff
checks; disclose existing baseline failures. Every requested slot has an explicit
terminal outcome. Source/reference and prior publication identities remain intact.

## Review and non-goals

Use bounded independent schema, boundary and sample reviews. Do not run any judge,
read reserved/test payloads, amend references, change partitions, commit or push.
Keep existing 09E uncommitted changes intact. Retain adequacy semantics and existing
provenance/edit structures rather than inventing a claim-decomposition framework.

## Outcome

The [new result pointer](../../docs/specs/task09a2_final_result.json) binds the
published version at:

```text
/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09a2_20261011_v1/batch_v2/published
```

All **19 cases** completed. The **423 inherited development slots** account for
**419 fresh variants**, **four inapplicable slots** and no failed cases. The new
variants contain **1,107 non-conclusion point expectations**. Independent review
excluded 12 proposals, leaving **407 comparison-eligible variants** with 1,056
point expectations. All 31 perturbation categories are represented. No duplicate
variants or author-declared unresolved labels were produced; review exclusions
remain explicit despite the author's original `model_verified` status.

The prior publication and result pointer remain unchanged. Its 118 reserved IDs
and five excluded IDs are preserved as metadata, without reading or regenerating
their payloads. Approved questions, references, source packets and the frozen
19-development/30-test split remain unchanged. No judge, target generation or test
evaluation ran. No commit or push was made; unrelated 09E changes were preserved.

### Schema and interpretation

The versioned schema adds `grounding.point_expectations`: one row for each actual
non-conclusion point, with its ID, support decision, rationale, source evidence
and exact unsupported assertion spans/reasons. Compound points remain intact.
It also adds `clean_abstention`, `conclusion_supported` and
`unsupported_premise_point_ids`, reusing the existing grounding rationale/evidence
for the conclusion decision. Adequacy, exact edits, source evidence and full
input/output/model provenance remain separate from model-visible answers.

Point checks use each point's actual citations. The conclusion uses the union of
actual answer citations and cannot borrow an unsupported premise. Thus a citation
failure can coexist with an independently established conclusion. Grounding is
0 for an unsupported conclusion, 1 for a supported conclusion with any failed
point, 2 when both stages pass, and N/A for clean abstention; point counts do not
weight the result.

`not_supported` identifies any unsupported substantive point or conclusion;
**237 of 419 proposals** are marked true. The separate
`insufficient_evidence_response` flag identifies explicit insufficient-evidence
language (**50 proposals**). These are different from clean abstention
(**15 proposals**). Grounding proposals are 98 zeros, 139 ones, 167 twos and
15 N/A. These are proposed expectations, not human-calibrated truth.

### Coverage limits and unresolved labeling issues

Four slots were inapplicable within the allowed packets: C017/C042 C01 lacked a
genuinely irrelevant real passage; C017/C028 P08 lacked a distinct, sufficiently
complete alternative passage. These are bounded discovery results, not claims
that no alternative exists anywhere in the corpus.

The twelve excluded records retain their original answers and labels:

- C006/C050 F10: an unsupported qualification explicitly attached to the
  conclusion makes the claimed independence of conclusion support uncertain.
- C028 P02/P04/P06/P07: a reference to a previously stated noise threshold may be
  context rather than a new unsupported assertion; the proposed false point label
  and G1 are uncertain.
- C008 F05, C028 F01, C041 F01/F08 and C042 F01: invented access, inspection,
  reporting, compliance or maintenance guarantees may materially affect adequacy;
  the proposed A2 is uncertain.
- C041 P06: the intended presentation-only edit changed meaning. Its negative
  labels are plausible, but it does not establish successful invariance coverage.

`expectations.jsonl` records `comparison_eligible=false` and the exact review reason.
`coverage.jsonl` records 407 generated, 12 ambiguous and four inapplicable slots;
`development_slots.jsonl` preserves the predecessor-to-new-ID mapping. Use these
eligibility fields rather than interpreting `model_verified` as acceptance.

### Execution and validation

Astra generated each answer and its expectations together from approved packets.
The initial two-case smoke and one bounded corrective C001 smoke are preserved.
They exposed point-specific citation borrowing and conclusion citation-pool
confusion; the final prompt makes both boundaries explicit. No old synthetic
answers were labeled or reused. The initial full batch hit its 20-minute timeout
on three cases; those failures and interrupted retries are preserved separately.
The fresh full batch used an independently reviewed 60-minute limit and completed
every case without a corrective attempt. Historical transport callers retain their
original timeout. The exact CLI requested `gpt-6-astra`; the backend did not
independently report its model identity.

All 419 proposals passed schema, point-ID coverage, literal assertion/source span,
citation ownership, edit reconstruction and score-consistency checks. Independent
source review examined **232 complete variants and 632 point expectations** across
all 19 cases and all 31 categories, plus every disposition, discovery record and
uncertainty flag. Semantic review is sampled; mechanical checks do not prove
entailment or establish judge reliability.

All **73 focused tests** passed, as did formatting, lint and type checks. The full
suite produced **3,897 passes, one skip and three existing Task 06G historical
commit-pin failures**; their tests and generator were unchanged. Completed-batch
replay made **zero model calls** and left its inventory unchanged. Publication,
input bindings and both batch/namespace inventories verified successfully. Full
logs, code snapshots, failed attempts and review receipts are sealed in the new
external namespace. The result pointer binds the checksums and detailed counts.

### Next step

Review the proposed expectations and retained exclusions before selecting this
version for downstream judge development. Existing 09E run state is unchanged;
this task does not authorize or execute a judge comparison.
