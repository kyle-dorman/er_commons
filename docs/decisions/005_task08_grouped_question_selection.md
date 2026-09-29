# Decision 005: Grouped question selection for Task 08

Status: **Accepted by Kyle on 2026-09-29; selection has not started.**

## Decision

Move directly into Task 08 preparation without another pilot round or a full
Task 07G retrospective. Use the prepared exclusive groups for human question
labeling and selection. Kyle reviews candidates within each group until he finds
up to **three reasonable questions**, then stops reviewing that group for this
pass. He can be selective, especially in large groups: three is a maximum,
not a quota that justifies accepting weak questions.

If a group is exhausted before three suitable questions are found, retain fewer
and record the shortfall. Candidates not reached when a group closes remain
unreviewed, not rejected. Save reviewed skips, selections, and the stopping point
so work can resume without repeating decisions. Do not choose the three
automatically or require review of every candidate first.

## Exclusive group assignment

Each comment appears in exactly one group, in this priority order:

1. Linked eligible general response.
2. Otherwise, cited appendix.
3. Otherwise, comment source, combining main-report citations and comments with
   no recorded citation into the same source groups.

Do not subdivide general-response or appendix groups by comment source. Within
a tier, use the saved deterministic tie-break: lowest general-response number,
then natural appendix order. Keep all original links as provenance even though
the comment has only one review-group assignment. The tie-break is not a quality
ranking, and review order within a group remains to be specified in Task 08.

| Group type | Nonempty groups | Candidate comments | Maximum selections |
| --- | ---: | ---: | ---: |
| General response | 5 | 101 | 15 |
| Appendix | 11 | 66 | 22 |
| Comment source | 25 | 438 | 58 |
| Total | 41 | 605 | 95 |

Ten groups have one candidate, eight have two, and 23 have at least three.
Thus 95 is the starting pool's selection ceiling, not an expected yield or a
new final benchmark size. The sprint's later eligibility, evidence review,
clustering, and split requirements remain separate.

## Starting pool and limits

Carry forward the prepared rebuttal-priority pool: deprioritize responses that
announce or rely on current Draft EIR changes, including Chapters 14/15, and
responses saying no substantive response is required or giving only an
introductory referral. Historical project changes, regulatory revisions, and
statements that no revision is needed do not by themselves trigger the change
filter. GR1, GR5, and GR8 remain available; mixed linked-change cases retain
their review flags rather than being represented as change-free. Preserve the
existing stops for I-CJ-4 and I-EA-2 and all sealed pilot artifacts.

These are browsing and prioritization groups, not model-approved eligibility
labels or split clusters. Citation metadata is incomplete: a missing recorded
citation does not establish that the response lacks citations or useful evidence.
The unresolved Appendix Q group remains flagged. A selection must still be a
faithful, independently answerable question under the
[human review process](../response_comment_human_review_process.md).

## Reproducible starting point

Relative to `ER_COMMONS_DATA_ROOT`, the accepted starting grouping is:

```text
pipelines/brisbane_baylands/task_08_preparation/exclusive_groups_20260929T230754Z/
```

`groups.json` owns the 605 exact comment assignments; `summary.json` owns the
counts, and `manifest.json` binds the preceding filtered pool and output hashes.
The `groups.json` SHA-256 is
`b3ff269c9819bdef665aa0258988cc5e656c92522c0e38b3c4025bdc9c0f2bb6`.
Its upstream planning records retain response-filter explanations and flags.
Preserve this starting version; any later regrouping must be explicit.

The rationale is practical coverage with bounded review effort: compare related
questions, favor good examples over filling quotas, and prevent repeat labeling.
This is purposive human selection, not a representative sample or a measured
acceptance-rate estimate. The immediate next step is a bounded Task 08
question-review contract and interface using these groups; this decision records
the plan and does not itself create review tasks or select questions.
