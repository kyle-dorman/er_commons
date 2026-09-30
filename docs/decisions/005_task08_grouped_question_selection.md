# Decision 005: Grouped question selection for Task 08

Status: **Accepted by Kyle on 2026-09-29; amended 2026-09-30; selection has not started.**

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

1. Explicitly named health-risk table-analysis priority group below.
2. Otherwise, linked eligible general response.
3. Otherwise, cited appendix.
4. Otherwise, comment source, combining main-report citations and comments with
   no recorded citation into the same source groups.

Do not subdivide general-response or appendix groups by comment source. Within
a tier, use the saved deterministic tie-break: lowest general-response number,
then natural appendix order. Keep all original links as provenance even though
the comment has only one review-group assignment. The tie-break is not a quality
ranking, and review order within a group remains to be specified in Task 08.

| Group type | Nonempty groups | Candidate comments | Maximum selections |
| --- | ---: | ---: | ---: |
| Health-risk table analysis | 1 | 4 | 3 |
| General response | 5 | 101 | 15 |
| Appendix | 11 | 63 | 20 |
| Comment source | 25 | 438 | 58 |
| Total | 42 | 606 | 96 |

Eleven groups have one candidate, eight have two, and 23 have at least three.
Thus 96 is the starting pool's selection ceiling, not an expected yield or a
new final benchmark size. The sprint's later eligibility, evidence review,
clustering, and split requirements remain separate.

## Health-risk table-analysis priority group

On 2026-09-30, Kyle requested a separate labeling group for these candidates:

| Comment | Review lead |
| --- | --- |
| M-OSEC-241 | Combined health risks from existing sources and project emissions; G2 receptor maxima and contributing sources |
| M-OSEC-243 | Additional mitigation or land-use placement where risks are elevated; receptor results and filtration assumptions |
| M-OSEC-244 | Exposure of future residents, including children and seniors; overlaps with 243 |
| O-Joint-44 | Highway 101/Caltrain exposure, setbacks and barriers; cumulative receptor results in G2 |

Review this group before the ordinary metadata groups, with the same ceiling of
three reasonable questions. These are possible table-analysis cases, not proven
CSV-tool requirements; do not add calculations absent from the original comment.
Move 241, 243 and 244 out of the G2 group; M-OSEC-245 remains there. Restore
O-Joint-44 as an explicit exception to the linked-response revision filter,
retaining its original flags. Each comment still appears in exactly one group.
No other filtered comments are restored by this amendment.

O-Joint-44's flag was traced before retaining this exception: O-Joint-44 links
to RA-Caltrain-9, which links to RA-Caltrain-8. The latter corrects Caltrain
service at Bayshore in Table 4.8-3 (Draft EIR page 4.8-14) from 60-minute to
30-minute intervals. It states that this correction does not change the analysis
or conclusions. O-Joint-44 itself does not announce a revision, and the flag is
not a GHG-analysis change. Kyle retained it because the transit-frequency
correction is incidental to its health-risk rebuttal.

The supporting table/citation analysis is saved under
`pipelines/brisbane_baylands/task_08_preparation/long_tables_20260930/`, relative
to `ER_COMMONS_DATA_ROOT`. Its `long_tables_report.html`, `report_data.json`,
`unit_texts.jsonl`, and `manifest.json` retain the inventory, citing units, source
text, and analysis boundaries. Parsed row counts include headers; appendix
parser groups need not equal whole printed tables.

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
pipelines/brisbane_baylands/task_08_preparation/exclusive_groups_20260930T160957Z/
```

`groups.json` owns the 606 exact comment assignments; `summary.json` owns the
counts, and `manifest.json` binds the prior grouping, exception, and output hashes.
The `groups.json` SHA-256 is
`fb24092981fdb14d910b5a0485095ff45c5b25cfef5670712ea96809f753d632`.
Its upstream planning records retain response-filter explanations and flags.
The original `exclusive_groups_20260929T230754Z` version remains preserved.
Any later regrouping must be explicit.

The rationale is practical coverage with bounded review effort: compare related
questions, favor good examples over filling quotas, and prevent repeat labeling.
This is purposive human selection, not a representative sample or a measured
acceptance-rate estimate. Task 08 starts in a new chat with planning: define its
umbrella contract and bounded subtask contracts before implementation. Keep later
subtasks provisional and activate only the first, following `tasks/README.md`.
The first execution stage should use these groups for question review; this
decision does not itself create review tasks or select questions.
