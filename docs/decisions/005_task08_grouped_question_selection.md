# Decision 005: Grouped question selection for Task 08

Status: **Accepted by Kyle on 2026-09-29; amended 2026-09-30.**

## Decision

The 2026-10-01 closeout amendment below supersedes the original three-selection
ceiling for saved 08B labels; all explicit Selected records are retained.

Move directly into Task 08 preparation without another pilot round or a full
Task 07G retrospective. Use the prepared exclusive groups for human question
labeling and selection. Kyle reviews candidates within each group until he finds
up to **three reasonable questions**, then stops reviewing that group for this
pass. He can be selective, especially in large groups: three is a maximum,
not a quota that justifies accepting weak questions.

If a group is exhausted before three suitable questions are found, retain fewer
and record the shortfall. Candidates not reached when a group closes remain
unreviewed, not rejected. Save reviewed skips, selections, and reasons
so work can resume without repeating decisions. Reconcile saved annotations against
the full inventory and confirm review completion in chat at export; unanswered
candidates remain unreviewed and the form has no stopping control. Do not choose the three
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
ranking. Task 08A saves a model-proposed quality order within each group; human
selection remains separate.

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
acceptance-rate estimate. The [Task 08 umbrella](../../tasks/sprint2/08_curate_grouped_benchmark.md)
owns the bounded contracts. The [current queue](../todo.md) routes saved
health-risk handoffs and concurrent 08E work. The later 08A preparation amendment
authorizes remaining-group preparation only; all human gates remain explicit.


## Current sequencing and evidence-review amendment — 2026-10-01

Kyle approved completing one numbered task across all participating batches before
advancing to the next, superseding the rolling single-group sequence below.
Preserve completed health-risk work. Reconcile completed, stopped, zero-case and
explicitly deferred batches before advancing; do not infer missing approvals.

The 08E workflow paragraph below is superseded by the 2026-10-06
[question-by-question chat plan](../../tasks/sprint2/08e_review_group_evidence.md),
which removes source deduplication and expands research beyond claims.

At 08E, pool approved claims and bounded citation discovery across batches to
maximize shared-source review. The [v2 plan](../specs/task08e_shared_source_review_v2.md)
owns exact-source deduplication, editable Astra link proposals, explicit acceptance
of displayed/selected links, and preservation of existing labels. Group and claim
identities remain separate; similar claims do not inherit labels automatically.
No aggregate claim-adequacy pass is added; that ambiguity stays for drafting.
Human eligibility remains separate. This is planning authorization only.

The earlier single-group chat/project rule has an explicit exception for the
planned cross-batch evidence queue. Other stages retain their context boundaries.

## Accepted execution plan amendment — 2026-09-30

The initial first-pass eligibility requirement below is historical and superseded
by the explicit shared selection-gate amendment that follows. Other execution
boundaries remain in force.

Kyle approved a rolling, single-group workflow: save a ranking, select candidates,
then separately rewrite and review question wording, review claims, review
evidence, and approve answers. Take one group through authoring before the next
by default; no up-front 35-candidate requirement remains. Selection can use the
complete response context. The initial amendment required first-pass eligibility;
that requirement is superseded by `task08.selection_gate.v2` below. Wording
proposals and approval use only the original comment and comment-source warnings
in a fresh chat; exclude response-derived ranking reasons and prior answers.

Astra ranks candidates within a group for clear, faithful questions and substantive
rebuttals, deprioritizing rant-like or ambiguous asks, weak referrals, and material
revision dependence. Save all candidate IDs, order, inherited flags, prompt,
model, and input version. This fixed ranking can be revisited; a model rerun is
not presumed deterministic. Ranking does not reject candidates or assign
eligibility. The health-risk exception and all original provenance remain intact.

For future 08A groups, the accepted simplification removes generated ranking
reasons, explanatory quote anchors, and narrative source warnings/review
limitations. Keep complete original source context, inherited metadata, and
exact version bindings. Kyle assesses the source material directly. Qualify a
shared v2 interface before the next 08A batch; do not fabricate rationale fields
to satisfy v1. The completed health-risk v1 artifacts remain unchanged and usable
by 08B, with no reranking or migration. The
[08A contract](../../tasks/sprint2/08a_rank_group_candidates.md) owns this revision.

All labeling takes place in separate single-group, single-stage chats/projects,
not the main coordination chat. Each stage establishes a shared versioned
interface and data contract once, then batch chats supply data and use that
existing template. Template changes are explicit revisions with a decision about
whether earlier batches need follow-up. Question wording, answers and clustering use chat with
versioned saved decisions rather than mandatory Label Studio forms.

The six approved pilot comments reenter the new process in their exclusive
groups, under the same three-selection limit and all new human gates. Preserve
sealed Task 07 records; new Task 08 decisions do not migrate those records.
Verify group membership and resolve any mismatch explicitly before changing the
starting pool. The two previously stopped cases remain excluded.

Allow downstream attrition without automatic backfilling. Defer clustering until
all group authoring finishes, then review model-suggested similarities and
relationships across groups in chat, one at a time. Retain deterministic
relationship/duplicate checks, human edge decisions, and the leakage audit.
Three selections per group does not imply three independent cases.

Twenty-five is a flexible benchmark target, not a ceiling or a quota. Preserve
all accepted cases and agree final size and development/test allocation after
clustering, before final serialization. The previous exact 10/15 allocation is
no longer mandatory. Confirmed clusters must still remain intact; an infeasible
agreed allocation returns for a decision rather than weakening that rule.


## Accepted shared selection-gate amendment — 2026-09-30

Kyle requested `task08.selection_gate.v2` and shared template
`task08b.selection.v2` before saving any health-risk annotations. Selection with
a selection reason is now the only 08B human gate to 08C; no separate provisional
eligibility decision is required. Eligibility concerns may be recorded in the
selection reason. The later evidence-based human eligibility review remains at
08E. This supersedes the earlier two-pass eligibility requirement for Task 08;
sealed Task 07 decisions and the completed 08A outcome are unchanged.

The reusable form shows original comments and complete linked responses, then
selection and reason controls. Remove the displayed source warnings and review
limitations, saved advisory ranking reasons, and source-bound ranking record.
Preserve existing source limitations, ranking provenance, and O-Joint-44's
incidental-revision exception in underlying artifacts. Generate no additional
narrative for the removed sections, do not rerank, and do not prefill decisions.

Remove the continue/stop control. On an export request, confirm in chat that Kyle
is finished, then reconcile saved annotations against the complete inventory.
Preserve selected, reviewed skipped, excluded, unresolved, and unanswered statuses;
unanswered candidates remain unreviewed. The maximum remains three selections,
fewer are welcome, and downstream attrition never triggers automatic backfilling.
Only explicit selections with reasons advance to 08C; response context and screening
rationales remain outside its strictly comment-only wording packet.

Create a new health-risk project after qualifying the shared v2 queue, source
display, saved decisions and export with isolated synthetic fixtures. Mark the
v1 project superseded and retain its records: it has no submitted annotations
and one unsaved draft, which remains preserved. No annotation migration is needed. Bind the eventual coordination handoff to both the template and process
revisions. This amendment does not start 08C or authorize other groups.

## 08C chat-review amendment — 2026-09-30

Kyle explicitly replaced the mandatory 08C Label Studio review with reusable
`task08c.chat_review.v1`. Review each selected original comment separately in
the isolated wording chat, retain proposal versions and actual feedback, and
freeze only explicit approval of exact displayed wording. A null proposal is
unresolved pending discussion, not an automatic exclusion. Unsupported intent
from clarification must be flagged rather than added silently. Preserve existing
source/proposal bindings and historical project preparation. The
[shared process](../specs/task08c_chat_review_v1.md) owns records and validation.
This amendment changes no selection gate, eligibility rule or 08D authorization.

## Authorized 08A preparation amendment — 2026-09-30

Kyle authorized 08A preparation across all remaining accepted groups ahead of
human review. Preserve valid completed handoffs; do not regroup, refilter, omit
candidates or rerank completed groups. Qualify shared v2 before new execution.
Groups with at most three candidates require no model ranking: retain all source
context in stable comment-ID order and record “ranking not needed—group has at
most three candidates,” with no model invocation. Larger groups use Astra
(`gpt-6-astra`) and save only advisory order, without generated explanations.
Both paths preserve source/input bindings, inherited flags and version provenance.
This preparation exception changes no later human gate or stage authorization.
The rolling single-group selection/authoring workflow and concurrent health-risk
08E work remain intact. The [08A contract](../../tasks/sprint2/08a_rank_group_candidates.md)
owns execution and completion evidence.

## Authorized 08B project-setup amendment — 2026-09-30

Kyle authorized shared v2 intake qualification and separate review projects for
all remaining groups, with selections to follow later. Preserve completed
health-risk work, annotations and usable existing projects; create only missing
projects using the qualified shared template. This setup exception changes no
human gate, selection ceiling, completion-confirmation requirement or evidence
eligibility boundary. No automatic selections, reranking, 08C, duplicate
per-group contracts or other Codex chats are authorized. The
[08B task](../../tasks/sprint2/08b_select_group_candidates.md) owns execution.

## Accepted all-selected closeout amendment — 2026-10-01

Kyle explicitly confirmed all groups finished and authorized retaining every
saved Selected candidate, including groups with more than three. The historical
ceiling is not a truncation rule for this export. Under
`task08.selection_closeout.v1`, retain native Skip/cancelled records separately
without blocking closure or inventing exclusion reasons. Untouched candidates
remain unreviewed. Only saved, noncancelled Selected annotations advance; no
choice is inferred from order, draft state, or completeness of the queue.
Bind confirmation and the changed policy to exact full-inventory exports.
Historical health-risk exports, the original shared form and previous process
records remain preserved. This does not establish wording approval or eligibility
and does not authorize 08C execution.
