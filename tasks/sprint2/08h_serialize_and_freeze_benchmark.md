# Task 08H — Serialize and freeze the approved benchmark

Status: **Complete — 49 cases frozen, 19 development and 30 test.**

## Goal and authority

Publish all 49 approved Task 08 cases with the user-approved **19 development /
30 test** allocation. Kyle approved the topic-balanced proposal with C002 in
test, then explicitly authorized packaging, validation, sealing and documentation
closeout. No additional case approval is required to serialize unchanged records.

The [08G amendment](08g_review_case_clusters.md) replaces the provisional
keep-together graph policy. Twenty-five cases and a 10/15 allocation are
historical proposals, not release requirements. Preserve the
[provisional 08H contract](history/08h_serialize_and_freeze_benchmark_provisional_20261009.md)
as history; do not claim its unperformed graph or fixture procedures passed.

## Inputs

- [Consolidated 08F result](../../docs/specs/task08f_combined_review_result.json):
  49 approved current answers, exact citation/input bindings and prior histories.
- [08G topic review](../../docs/specs/task08g_topic_review_result.json): accepted
  similarities and shared-evidence limits.
- Approved split at
  `pipelines/brisbane_baylands/task_08/08h_approved_split_20261009_v1/split.json`
  beneath `ER_COMMONS_DATA_ROOT`, including its exact approval binding.
- Upstream stage results for selection, questions, eligibility and attrition;
  [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
  for reference roles and later evaluation, and the
  [artifact contract](../../docs/data_artifacts.md) for publication.

## Release contract

1. Reuse exact approved questions, structured answers and citations. Verify the
   source handoff and every current case binding; preserve upstream seals.
2. Reproduce the approved allocation, without rerunning optimization or silently
   adjusting memberships. Keep all 49 cases; no accepted case is unselected.
3. Check C002 and every appendix cited by only one case remain in test. Citation
   balancing counts distinct cited section/table units per answer, including
   optional context; it does not change support/context evaluation roles.
4. Retain the 13 topic families and record their presence across both splits.
   Shared evidence is permitted. Describe observed overlap without claiming
   exhaustive independence or a graph-based no-leakage proof.
5. Serialize target-facing question records separately from curator references.
   Target inputs must exclude reference answers, gold evidence IDs/roles,
   reviewed claims, official response text and review rationales. Document the
   role boundary so later loaders need not reconstruct chat history.
6. Preserve auditable stage accounting and dispositions. Deferred questions,
   evidence-stage skips and unreviewed candidates are distinct from rejections;
   purposive selection is not an unbiased acceptance-rate estimate.
7. Publish a fresh external release under
   `benchmarks/er_bench/releases/task08_20261009_v1`, with schemas, exact managed
   file inventory, hashes, source/provenance bindings, validation, independent
   review and a completion-last seal. Preserve failed attempts and old versions.
8. Update the [final result pointer](../../docs/specs/task08h_final_result.json)
   and task routing only after successful verification.

## Validation and acceptance

Validate record schemas, case membership, exact approved text/version bindings,
source citations, 49/19/30 counts and exact allocation equality. Recompute
citation and appendix counts from the authoritative cases. Verify target/reference
separation by an explicit field allowlist and content checks, and inspect the
independent audit before publication. Recompute the sealed inventory and hashes.
Inspect documentation diffs and run `git diff --check`; implementation changes
also require focused tests and the applicable repository checks.

Schema validity does not establish human approval: both must be bound separately.
The accepted pool and release selection happen to be identical here, but their
roles remain distinct. Saved allocation replay is the correct reproducibility
check after human approval; rerunning an optimizer could change the decision.

## Non-goals and downstream boundary

No new question/evidence research, answer revisions, extraction, retrieval,
target generation, judge runs, model selection, commit or push. Task 09 must be
separately authorized. Later retrieval, target and judge configurations must be
frozen before the test run; Task 08 does not certify or execute them. Human
reference approval does not calibrate an automated judge.

## Outcome

The [final result](../../docs/specs/task08h_final_result.json) binds the complete
release, exact inventory, approved split, validation and independent audit. All
49 approved 08F case records are preserved byte-for-byte. The target JSONL files
contain only case ID and exact question; full references, approval history,
case/comment mapping and derived citation roles remain curator-only. The full
35-document corpus is bound separately for later retrieval, preserving the
qualified Final F.1 substitution and accepted usability registry.

The release derives 201 case-level cited section/table units: 172 required and
29 optional-context units. There are 77 in development and 124 in test. The
accounting records 606 candidates, 57 selections, 53 approved questions and 49
approved answers, separating exclusions, native skips, unreviewed candidates,
question deferrals and evidence skips. All six pilot reentry outcomes remain
recorded; only two advanced into this release.

Validation passed for exact source/approval identities, schema and target-field
separation, 49/19/30 membership, citation roles, corpus bindings, topic coverage
and singleton-appendix placement. Eleven synthetic negative checks reject extra
curator fields, altered questions, duplicate rows and omissions. Independent audit
verified 1,461 bound references; the final seal and verifier check exact managed
file closure. This artifact/docs closeout changes no production package code and
does not claim a rerun of the repository-wide test suite.

The exporter snapshot reuses maintained artifact I/O and answer validation, plus
installed JSON Schema validation. The release keeps its narrow export and verify
scripts for reproducibility rather than introducing a publication framework.
[JSON Schema guidance](https://json-schema.org/understanding-json-schema/reference/object)
informs the closed target-field allowlist. Version approval and schema validity
remain separate checks.

This is a local research release referencing existing sources; source access and
terms are bound without inferring an affirmative redistribution license. No
benchmark, retrieval, target or judge runs occurred. Task 09 contract preparation
and execution require separate authorization; no further Task 08 human decisions
are pending.
