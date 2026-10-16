# Task 09F — Supporting-reasoning synthetic authoring handoff

Status: ready for direct authoring in a separate chat. The user accepts testing
reference visibility during judge evaluation rather than making it a prerequisite
for synthesis. This handoff documents generation only; it does not run judges or
change the concurrent conclusion-generation task.

## Goal and inputs

Create a separate dataset for adequacy support (S): whether the candidate's own
supporting reasoning sufficiently and logically establishes its actual conclusion.
Use the 19 development questions bound by the
[current release pointer](task09f_question_publication_v2_result.json),
`task09f_20261014_v2`, the [official rules](adequacy_labeling_rules.md), and the
[extended catalog](task09f_adequacy_perturbations.md). Read AGENTS.md and entry docs,
then the current section of [09F](../../tasks/sprint2/09f_implement_adequacy_judge.md).

The coding agent authors examples directly, using bounded subagents for separate
case batches and independent review. Carry forward the user's one-example-per-
applicable-type allocation. No provider APIs, judge runs or credential access.
Read only the allowlisted development references for this synthesis. Do not inspect
test records, reserved challenges, historical judge outputs or the concurrent
conclusion dataset. No dependency on that dataset or its predictions is required.

## Two later judge conditions, one fixed set of labels

Prepare a common candidate payload containing only:

- `question`: question text.
- `candidate_conclusion`: candidate conclusion text.
- `candidate_supporting_points`: ordered point IDs and text.
- `candidate_qualifications`: qualification IDs/text and explicit attachment to
  the candidate conclusion, named supporting points, or the whole argument, as
  warranted by the qualification. Preserve scope when projecting original IDs;
  do not force a conclusion-level condition onto a supporting point.

Keep citation IDs and source passages out of these payloads. Preserve canonical
reference/source bindings in separate provenance, not judge input. Do not include
expected labels, mutation names, explanations of edits or C predictions.

Store a separate reference supplement: approved reference conclusion, supporting
point texts and material qualifications with their attachments. No citation IDs,
source passages or label metadata in this supplement. Preserve reference scope;
never attach its explanation to the candidate as if it were the candidate's support.

Later compare the same cases, labels and candidate payloads under:

1. **No reference:** common candidate payload only.
2. **Reference example:** common payload plus reference supplement, introduced as
   an illustrative sufficient explanation, not a mandatory reasoning checklist.

Include reference conclusion with reference support so its argument's target is
explicit. Verify reference sufficiency under the current S rules during authoring;
reference approval alone is not an S label. Flag apparent reference insufficiency
or ambiguity rather than silently repairing it or calling it a sufficient example.
Hold such cases out of the paired comparison pending resolution, retaining them
in coverage records. Fix labels before judge outputs are available; visibility
must not change the expected S judgment.

## Selected slots

One example per applicable row per question. These are target effects, not labels
established by an ID. Combined IDs form one slot unless distinct rows appear below.
Do not force a failure family onto an unsuitable question or force class balance.

### Passing transformations

| Slot | Lineage | Target transformation | S |
| --- | --- | --- | --- |
| BASE | Unchanged control | Keep reference conclusion/support, after independent sufficiency review. | Yes |
| P01 | P01 | Paraphrase support without changing reasoning. | Yes |
| P02 | P02 | Reorder support while preserving a coherent argument. | Yes |
| P03 | P03 | Group related support for multiple conclusion claims. | Yes |
| P04 | P04 | Separate grouped support into one point per claim where meaningful. | Yes |
| P05 | P05 | Compress support without losing a necessary basis. | Yes |
| P06 | P06 | Change tone/formality without changing substance or certainty. | Yes |
| P07 | P07 | Remove neutral background while retaining sufficient reasoning; not citation metadata. | Yes |
| P09 | P09 | Use a different logically sufficient supporting argument. | Yes |
| A08 | A08 | Add neutral background alongside sufficient reasoning. | Yes |

P03/P04 should supply matched layouts for equivalent reasoning where applicable.
Each layout is one slot, not an invitation to produce many grouping combinations.
If a baseline already provides a layout, record explicit shared coverage rather
than duplicate it as another independent example.

### Support failures

| Slot | Lineage | Target transformation | S |
| --- | --- | --- | --- |
| O01 | O01 | Remove the necessary basis, including zero supporting points where appropriate. | No |
| A06 | O02/A06 | Keep a complete conclusion but explain only some of its claims. | No |
| A05 | O03/A05 | Replace reasoning with neutral background or discussion of another issue. | No |
| A04 | A04 | Replace the basis with restatement or circular reasoning. | No |
| A07-example | A07 | Give an example insufficient to establish the conclusion's breadth. | No |
| A07-method | A07 | Name inputs/methods without explaining the relationship or result needed. | No |
| F03 | F03 | Reverse the conclusion while retaining reasoning for the incompatible original. | No |
| F04 | F04 | Change a number/unit/direction/comparison so the visible inference no longer works. | No |
| F05-F09 | F05/F09 | Claim a definite outcome from explicitly tentative or inconclusive support. | No |
| F06 | F06 | Use premises about a different scenario/entity/time without a valid connecting argument. | No |
| F07 | F07 | Remove a necessary logical condition or connecting premise. | No |
| F08 | F08 | Introduce an invalid inferential step. | No |
| F10 | F10 | Add a material contradiction of the conclusion or a necessary part of its argument. | No |

F04–F07 must fail from the candidate's stated reasoning, not from disagreement
with hidden source facts. The generator must not conflate a source-unsupported
premise with an invalid inference. A factual premise may be treated as given for
S while grounding would reject it. Other good points do not cancel material
contradiction; different scenarios are not automatically contradictory.

### Boundary controls

| Slot | Lineage | Target contrast | S |
| --- | --- | --- | --- |
| B01 | O02/A01 | Incomplete conclusion relative to reference, but sufficient support for all candidate claims. | Yes |
| B02 | A02 | Extra substantive conclusion item, with sufficient support for all candidate claims. | Yes |
| B03 | A04 contrast | Support overlaps with the conclusion but adds a real basis. | Yes |
| B04 | F10 contrast | Apparently conflicting statements are consistent under their explicit different conditions. | Yes |
| B05 | Joint sufficiency | Several points jointly establish the conclusion; no point must establish it alone. | Yes |
| B06 | A06/A10 adaptation | Duplicate supporting material while leaving a necessary part unestablished. | No |

Boundary controls are tests of approved policy, not additional grading rules.
B01/B02 explicitly test S independence from reference-answer correctness. Do not
use an invented reference-required item to make them applicable. Record label
rationales about the actual argument, not about whether the approved answer matches.

## Generation and review rules

Usually hold the conclusion fixed and mutate support. Conclusion edits for F03,
F05/F09 or boundary controls are intentional and must be recorded. Qualifications
are part of the reasoning; do not remove a condition from one place while leaving
an equivalent basis elsewhere and then force a failure label.

This table defines 29 slots per question, at most 551 slot outcomes across 19
questions. It is not a quota of unique accepted answers: inapplicable/ambiguous
slots and deduplication reduce the count. Record one generated, inapplicable or
unresolved disposition for every slot. Candidates shared across overlapping slots
need explicit shared-ID coverage, not inflated sample counts. Preserve drafts and
review corrections as separate versions where relevant.

Inspect every candidate independently against the question, candidate conclusion,
support and qualifications under S rules. Separately check reference supplement
quality and its preservation. Ensure reviewers accept concise/alternative reasoning,
reject mere repetition and material gaps, and do not redo source factuality or C.
Labels are agent-authored, independently reviewed proposals, not human gold.

Exclude citation-only changes P08/C01–C05, factual defects F01/F02 lacking a separate
logical defect, O04 non-answer conclusions, clean abstentions, routing cases,
malformed outputs and R03 prompt injection. No automatic S failure for A09 or
reference-list disagreement. Formal logical completeness is not required beyond
the substantive reasoning standard in the approved policy; do not invent a new
requirement to spell out every obvious inferential step.

## Artifacts, validation and finish

Use a fresh support-specific namespace under ER_COMMONS_DATA_ROOT and maintained
artifact I/O/validation where applicable. Keep payloads, reference supplements,
labels/rationales, exact edits, coverage, review and provenance separately
identifiable. Bind release, rules, this handoff and reference versions. Payload
IDs and manifest mappings must reconnect inputs and expectations without exposing
the expectations. Preserve all existing artifacts, including concurrent conclusion
outputs; coordinate no shared writes with that chat.

Validate all 19 dev IDs, complete slot accounting, unique IDs, duplicate handling,
reference bindings, point/qualification attachments, leakage exclusions, and exact
candidate equality across the two potential judge conditions. Check hashes and
inventory closure; publish completion last and a compact repository result pointer.
Run appropriate artifact validation and git diff --check; no commit or push.

Report paths, counts by question/slot/label, applicability and ambiguity,
independent review findings, representative successes/failures and limitations.
Stop after synthesis publication. No judge evaluation, prompt tuning, grounding
work or changes to the conclusion dataset. Actual judge model/settings and test
budgets will be selected separately when evaluation is requested.
