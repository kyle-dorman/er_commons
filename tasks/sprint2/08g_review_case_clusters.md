# Task 08G — Review similarities across the completed case pool

Status: **Complete — approved topic review and overlap audit published.**

## Goal and accepted amendment

Retain all 49 approved cases as separate questions and use their similarities to
balance topic coverage across development and test. Kyle approved this approach
in the current review chat, then approved the exact 19-development / 30-test
allocation and authorized closeout on 2026-10-09.

The whole 49-question pool and the closest answers were reviewed. No questions
were identified as needing merger. Thirteen overlapping topic families guide
the split; they are balancing groups, not connected components that must remain
together. Shared citations and related reasoning are allowed across splits.
This is a bounded review, not proof of exhaustive semantic independence.

This explicit user amendment supersedes the provisional mandatory deterministic
relationship graph, duplicate fixture, Astra relationship proposals, separate
clustering chats and keep-together rule for this release. Those procedures were
not performed and are not represented as passing. The
[historical provisional contract](history/08g_review_case_clusters_provisional_20261009.md)
remains preserved. No answer or evidence is relabeled by this amendment.

## Inputs and outputs

- The [consolidated 08F result](../../docs/specs/task08f_combined_review_result.json)
  supplies 49 current approved question/answer records and their histories.
- The [08G topic-review result](../../docs/specs/task08g_topic_review_result.json)
  binds the reviewed pool, topic families, overlap limits and user authority.
- [08H](08h_serialize_and_freeze_benchmark.md) owns the approved allocation and
  final role-separated release; no benchmark runs occur here.

## Review, validation and acceptance

Verify that all topic-family members belong to the exact approved pool, retain
all 49 cases, and bind the saved user policy and exact allocation approval.
Check that every recorded topic family occurs in both splits. Preserve the
strongest answer overlaps, especially drainage/flooding, bicycle safety and
traffic diversion, as limitations rather than silently claiming independence.
An independent closeout review verifies record consistency and the declared
scope. It does not substitute for a missing exhaustive duplicate investigation.
For documentation changes, inspect the diff and run `git diff --check`.

## Learning and limitations

Topic balancing distributes coverage; grouped splitting holds dependent units
together. They answer different evaluation questions. This release deliberately
uses the former: test questions can require applying evidence or reasoning also
seen during development. It is not an unseen-topic or unseen-evidence test.
The [sprint boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#task-08-eligibility-clustering-and-split-boundary)
owns this durable distinction. Future findings of duplication require a named
revision rather than silent changes to the frozen allocation.

## Outcome

The [completed result](../../docs/specs/task08g_topic_review_result.json) binds
all 49 reviewed questions, the 13 topic families and the exact approval. No merge
or keep-together cluster was adopted. Deterministic canonical unit/member checks
found 24 overlapping case pairs, including 15 across the approved split; these
are permitted under the accepted policy, not individually adjudicated graph edges.
The independent release audit passed. The [08H release](../../docs/specs/task08h_final_result.json)
retains this record and the limitations above.
