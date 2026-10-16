# Task 09F — Adequacy labeling and scoring, discussion history

Status: historical discussion and approval trail. The maintained
[adequacy labeling rules](adequacy_labeling_rules.md) own the consolidated approved
policy. Early open questions below are superseded by later recorded decisions.
Case-specific calibration examples are historical evidence, not judge-prompt text.

Original resume: 2026-10-14 after approved C002/C007 question publication.
**The rules below distinguish accepted direction from remaining decisions.**
They are not an implemented replacement rubric or new synthetic gold labels.
Prior prompt runs and labels remain historical under their original versions.
The [earlier draft](history/task09f_adequacy_redesign_draft_pre_resume_20261014.md)
is retained for provenance; its open questions and old C007 wording are superseded.

## Where the work stands

The three-model failure review exposed ambiguity in both answer requirements and
0/1/2 scoring. Kyle then labeled examples to clarify what counts as a substantive
basis for an answer. The old rebuttal questions complicated that calibration.
Rather than propagate a rebuttal-intent field through generation and judging,
C002 and C007 were rewritten as document-explanation questions. Their approved
answers are now published in `task09f_20261014_v1`; the other 47 case records,
19-development/30-test allocation, and 35-document corpus are unchanged. See the
[publication result](task09f_question_publication_result.json).

C007 is now a development **how/mechanism** question connecting design speed to
local safety and regional through traffic. C002 remains test and asks for
roadside/rail-side planting locations and purposes. Its authorized question and
reference review is recorded as design-time exposure, not test evaluation.
Use development questions, not C002, for the next rubric calibration panel.
No new per-question intent field is needed in target payloads. Demand types below
are discussion aids, not an approved runtime classification scheme.

## Accepted direction — do not reopen by default

- **Grounding owns source factuality.** Adequacy checks whether the answer addresses
  the question and whether its own reasoning supports its conclusion. It must not
  independently recheck factual premises against sources. A coherent argument
  with a false premise can fail grounding while satisfying reasoning adequacy.
- **The conclusion field must answer the question.** Correct information elsewhere
  does not rescue an empty, non-answer or wrong-question conclusion. The conclusion
  need not duplicate the entire supporting explanation.
- **Every substantive answer needs at least one real supporting basis.** Repeating
  the conclusion is insufficient. Overlap is acceptable when the point adds a
  fact, comparison, mechanism or other explanatory substance: show your work.
- **Judge support jointly.** A point can contribute without independently proving
  the whole conclusion. Conversely, individually useful points can still leave a
  material gap. One example is not automatically proof of a general claim.
- **Neutral content is not itself a failure and supplies no basis.** A materially
  contradictory or invalid inferential step cannot be diluted by many good points.
  Factual unsupportedness alone belongs to grounding, not this reasoning check.
- **Credit concise answers and valid alternatives.** Reference wording, ordering,
  citation count and every reference detail are not mandatory answer requirements.
- **Preserve the stated scope.** Different scenarios/times are not automatically
  contradictory. A condition visible in the question/answer matters to reasoning;
  a missing condition discoverable only by source verification belongs to grounding.
- **Citation context is metadata.** In the two revised references, context-only
  sources do not support answer points. C002-S031/S040 stay outside all answer
  links and are neutral for citation false-positive accounting. This is distinct
  from neutral prose in an answer. Older optional-context fields remain historical;
  their existence does not authorize adding such prose to these approved revisions.

## Human example judgments already recorded

These are conversational judgments about sufficiency, not newly published numeric
labels. Preserve them when preparing the next panel.

| Demand / development example | Accepted basis | Rejected or insufficient basis |
| --- | --- | --- |
| Yes/no — residual flooding | A remaining modeled depth explains why flooding is not eliminated. | Merely repeating that flooding remains; unrelated causes/background. |
| Why / finding — cumulative health risk | A comparison of the assessed result with its threshold explains the finding. | Repeating the finding or describing methods without what the numbers show. A single example may contribute without proving every comparison. |
| Enforcement — construction equipment | Explain the obligation, responsible actor, implementation/inspection and documentation relevant to compliance. | Benefits of maintenance or descriptions that fail to establish enforcement. |
| Accounting — electricity emissions | Explain how onsite generation and grid supply assumptions enter the calculation. | Merely saying they are included, or generic electricity background. |
| Modeled outcome — landfill groundwater | State what the scenario comparison showed (lower modeled levels relative to the relevant baseline); exact numbers need not always be included. | Physical mechanism alone, or saying a model exists without its result. This corrects the earlier draft's overly generic mechanism requirement. |
| Measures and purposes — trail wayfinding | Explain how signs/maps provide destination, distance or route information; even a single cited section can supply a basis. | Repeating the measure list or adding neutral trail context. |

The selected C007 revision supplies a new how/mechanism control with two requested
objectives. Multimodal details appear in the approved reference; their inclusion
alone does not establish that each detail is essential for an adequate response.
The other ordinary development demand types remain covered by the inventory in
the historical draft, except its obsolete qualified-feasibility C007 category.

## Remaining decisions, in order

### 1. Conclusion completeness versus supporting sufficiency

Settle how much must be explicit in the conclusion and what may be established
in supporting points. Review paired development examples that:

- name both requested objectives in a concise conclusion and explain them below;
- omit one objective entirely versus omit only a supporting detail;
- give a valid alternate mechanism instead of the reference's preferred explanation;
- supply one relevant example but leave a broader comparison incomplete;
- list some measures and purposes while omitting an essential requested group.

Candidate questions: C007 (two objectives), C017 (two accounting inputs), C001
(comparison coverage), and C036/C050 (measures/purposes). Do not equate full credit
with reproducing every reference point. The panel should yield an operational rule
for identifying essential requirements from the question rather than a gold-list
matching rule. These examples have not yet been labeled under a final C/S contract.

### 2. Contradiction and aggregate score

The proposed components are:

- **C:** Does the conclusion directly answer the requested question at the right
  scope, without using supporting text as a substitute for the answer field?
- **S:** Is there at least one substantive basis, and do the points jointly provide
  sufficient, internally valid reasoning for the conclusion?

These are working descriptions, not final schemas. Settle C/S labels first, then
select aggregation. A proposed gated ordinal mapping is C=false → 0;
C=true/S=false → 1; both true → 2. It is **not yet approved**. In particular,
correct/responsive conclusion plus directly contradictory support would score 1
under that mapping. Giving it 0 requires an explicit contradiction veto or another
mapping. Single pass/fail with diagnostics is also still a possible design.

Kyle's early B=0 judgment was subsequently questioned; it is not a settled veto.
Do not silently restore it. Review contradiction versus merely absent support,
and a successful qualified answer as a control. For false premises, keep grounding
separate rather than redefining “invalid” to mean source-unsupported.

### 3. Abstention and invalid output

Decide the component/result treatment for a clean abstention versus a substantive
but unsupported answer. Do not invent a supporting point to make abstention fit
an answered-question rubric. Also distinguish abstention from malformed output,
missing fields and invalid judge diagnostics. Define whether C/S are false,
not-applicable or accompanied by a separate status in this branch.

### 4. Freeze diagnostics and verify rule coverage

After the decisions above, settle a compact contract that preserves reasons such
as missing basis, restatement, incomplete support, neutral-only support,
contradiction and invalid inference. Avoid prematurely assuming these must be a
single exclusive point-role enum. Keep substantive accuracy/adequacy, citation
roles, and mechanical validity separate.

Check the agreed decision table against a small panel containing failures and
working controls. Derive aggregate labels mechanically from accepted components
and the chosen mapping; preserve uncertain examples rather than force them into
an ambiguous label. Include conditions and different-scenario apparent conflicts
as controls, not a renewed source-factuality debate.

## Recommended next labeling round

Prepare roughly 8–12 development-only variants organized as boundary pairs, with
concise working controls. Show one small group at a time and ask Kyle to label
conclusion responsiveness/completeness and joint supporting sufficiency separately.
Do not display historical judge predictions or demand a 0/1/2 choice first.
Start with the C/S completeness boundary, then contradiction, then abstention.
This is the recommended next action, not an inference authorization or completed
labeling exercise. Do not sample reserved challenges or use C002 as a test-derived
calibration example.

## After agreement

1. Freeze a versioned rubric and reconcile Decision006, answer instructions,
   judge contract and diagnostic schemas explicitly.
2. Write a bounded regeneration contract tied to the new question release and
   revised rules, preserving old answers, labels, splits and record lineage.
3. Review a small development calibration batch before expanding. Set provider,
   spending, execution and retry caps before any model-backed work.
4. Implement and evaluate the revised judge with component accuracy, aggregate
   results, successful controls, validity and repeatability reported separately.

The question publication alone does not migrate old synthetic labels, qualify a
judge or authorize prompt experiments. No provider calls were made in this resume.

## Recorded labeling round 1 — 2026-10-14

C007 manual development variants: A complete conclusion/both supporting mechanisms
received C=yes/S=yes; B safety-only conclusion with identical complete support
received C=no/S=yes; C complete conclusion with safety-only support received
C=yes/S=no. Supporting text does not rescue an incomplete conclusion, and support
is evaluated separately rather than automatically failed when C fails. Both
explicitly requested objectives need conclusion coverage and sufficient supporting
basis. No aggregate labels assigned. Exact variants and feedback are preserved in
`pipelines/brisbane_baylands/task_09/09f_20261014_human_calibration_v1/`.
Round2 uses C050 to examine essential measure coverage versus a concise answer;
labels are pending. No inference or reserved/test access.

## List-question wording audit — 2026-10-14

Kyle requests a full-dataset count after finding C050 completeness ambiguous.
Read only target question text for all49 current-release cases, including the30
test questions with explicit authorization. No new reference/evidence or model
output access. Independent wording review agrees on five clear open inventories:
C002, C016, C031, C036, C050 (2dev/3test). Four more have bounded inventory/checklist
wording: C011, C020, C025, C043 (alltest). Thus5 narrowly, or9 including bounded
lists; this is a discussion taxonomy, not published question-type metadata.
Mechanism/process questions can invite multiple measures without necessarily
requiring an exhaustive inventory. Exact counts beyond these categories depend
on the definition. Evidence and provisional classifications are saved in
human_calibration_v1/list_question_wording_review.json. C050 round2 labels remain
unresolved; no category checklist or coverage threshold is approved by this audit.

## List-rule first pass and C050 wording selection — 2026-10-14

Kyle accepts as a first-pass plan: review list questions individually, use explicit
bulleted items, require all agreed substantive items and no additional substantive
items, while allowing explanations and implementation details. Item boundaries
must be reviewed; this does not yet settle partial-credit aggregation.

For C050, Kyle identifies speed-adapted lettering/message complexity as
implementation rather than a distinct type of information. He selects:
“What wayfinding information does the Baylands project propose to provide to
bicyclists and pedestrians using its trails?” Proposed categories are directional/
trail-identification information, distance/travel-time information, and navigational
maps. Their exact completeness and the full revised answer remain pending review.
Only wording is approved; no automatic publication or synthetic relabeling.
External human_calibration_v1/C050_wording_selection_001.json preserves the decision.

### C050 list accepted; C036 next

Kyle says “ok done. next”, approving C050's selected wayfinding-information wording
and three-category list. Implementation details remain supporting explanation;
no new release was published in this review. C036's existing reference is now
being reviewed as an eight-category lighting-measure list, with thresholds,
exceptions and implementation examples kept in supporting material. Category
boundaries remain pending human review; no generated labels or inference.

### C036 list accepted; C016 reference review

Kyle approves C036's eight categories and supporting explanation (“no i think
thats good”). Record: human_calibration_v1/C036_list_approval_001.json. Next is
C016, under the requested one-at-a-time review of list questions. This explicitly
expands design exposure to C016's test reference and cited passages; it is not a
judge calibration/evaluation or access to test predictions. Its six-category
proposal remains unapproved; Final F.1 source qualification is retained. No new
publication or inference.

### C016 accepted; C031 proposed

Kyle approves C016's clarified question asking for physical safety features and
design-review requirements, and its six-category answer. The final category names
City-standard compliance and sight-distance demonstration before construction
permits. Exact decision is saved in C016_list_approval_001.json.

Next, C031's approved reference and full cited TDM section were reviewed under the
user's sequential list-review request. This expands test reference design exposure
to C031, not test predictions or judge calibration. A narrower financial/parking
incentive question and seven categories are proposed, including preferential
parking and promotional rewards from the existing source. Wording and answer
remain pending; no publication or inference.

### C031 accepted; C011 checklist review

Kyle approves C031's financial-incentive/parking-pricing question, eight-item
conclusion, six supporting points and applicability qualification. Separate parking
rental and unsubsidized market-rate parking are distinct items. Approval record:
human_calibration_v1/C031_list_approval_001.json. No publication yet.

C011 is next in the bounded-checklist group. Its test reference and cited passages
are reviewed under the user-authorized sequential list-review scope; no test
predictions are inspected. Four model-component categories are proposed, retaining
the documented employee/guest table-label inconsistency as a qualification.
The exact category/detail boundary awaits human review.

### C011 modeling answer accepted; C020 reporting review

Kyle approves C011's modeling-explanation question and answer, including its
employee/guest inconsistency qualification. It is no longer a strict-list task;
record: C011_modeling_approval_001.json. C020 now has a proposed two-action
reporting checklist with four written-report content requirements in support.
O008 remains citation context only, with no answer-point use. C020 test reference
and cited text are exposed under the user-directed sequential review; no predictions,
inference or publication. The exact required checklist remains pending review.

### C020 accepted; C025 shuttle checkpoints

Kyle approves C020's reporting checklist and support. Record:
C020_reporting_approval_001.json. C025 is next: a proposed two-checkpoint answer
with plan approval before the first qualifying occupancy permit and actual service
before either named district's50% commercial occupancy threshold. The exception
for existing-use improvement/relocation remains attached to the planning trigger.
Broader TDM monitoring is citation context only. C025 test reference design exposure
is recorded under the sequential-review request; no model outputs or inference.

### C025 accepted; final checklist candidate C043

Kyle approves C025's question, two checkpoints, support and context citation role;
record: C025_shuttle_approval_001.json. C043 is the last of the original nine
list/checklist candidates. Its proposed five conditions retain three different
triggers: preparation before construction in potentially lead-affected areas,
conditional remediation before relocation, and operational readiness before
required vacation of the existing nursery. Appendix A remains citation context.
C043 test reference/cited text exposure is recorded under the sequential review;
no predictions, scoring, inference or new publication.

### C043 cleanup scope approved; list review complete

Kyle approves the narrowed C043 question: “What site-investigation and cleanup
requirements must be met to relocate Mission Blue Nursery to the former shooting
range on Icehouse Hill?” Four required items: identify/approve affected areas,
sift fragments, layered soil testing, and conditional remediation. C043-S009
(MM HAZ-1e, PDF1307–1308) is the sole supporting section. BIO-5 findings and
continuity requirement (S002/S003) and Appendix A relocation description remain
context-only, with no answer-point reliance. Preserve preconstruction versus
prerelocation timing and the conditional lead-limit trigger. Approval record:
human_calibration_v1/C043_cleanup_approval_001.json.

The nine original list/checklist candidates have now been reviewed: C002 was
already approved/published; C050, C036, C016, C031, C020, C025 and C043 have approved
list/checklist revisions, while C011 was approved as a modeling explanation instead.
The subsequent eight case revisions have not yet been published as a new release.
No automatic synthetic label migration, model inference or scoring-rule freeze.
Remaining rubric work still includes contradiction aggregation, abstention and
final component/diagnostic coverage; approved reference lists do not themselves
resolve partial-credit treatment for missing or extra items.

## Answer-layout rules approved — 2026-10-14

Kyle approves putting the complete required list in the conclusion as bullets,
with supporting points separately below. Both one-support-point-per-item and
grouped support for multiple related items are valid layouts. Judge joint coverage
and reasoning; do not require positional matching, equal point counts or a fixed
partition of the explanation. This does not relax complete substantive-item
coverage or permit additional substantive list items.

Required future judge tests: matched sufficient one-to-one/grouped layouts must
receive equivalent component judgments; include missing-basis and invalid-reasoning
controls in both layouts. These are planned tests, not executed or proven behavior.
C011's prose conclusion and separate supporting paragraphs are also approved,
with its existing qualification/citations; it remains a modeling explanation.
Exact decisions are recorded in human_calibration_v1/answer_layout_rules_approval_001.json.
No new publication, provider call or runtime change.

## Explanation-support boundary labeled — 2026-10-14

Kyle labels the C011 explanation variants S(A)=yes, S(B)=no, S(C)=no because C
omits retail-space sales. A explains each calculation relationship without exact
numeric assumptions; B merely names inputs; C explains spending but not sales.
This establishes a sufficient concise modeling basis and rejects both generic
method naming and missing a requested calculation. Exact examples/feedback are
recorded in human_calibration_v1/explanation_support_labels_001.json (variant
summaries; exact wording remains in chat).

Exposure correction: C011 is a test case and was used in this explicit human
rubric discussion following its authorized reference rewrite. This is additional
design/calibration exposure, not a clean held-out test or model evaluation. Prior
plans to use development-only panels were not followed for this example; preserve
that disclosure and use development cases for subsequent panels. No inference,
new synthetic gold publication or aggregate scores.

## Missing/extra list boundary labeled — 2026-10-14

C050 panel: Kyle rejects A for missing maps, rejects B for an extra substantive
bicycle-repair item, and accepts C with lettering/message implementation detail
inside an existing category. This confirms missing/extra substantive categories
fail list completeness while explanatory details are allowed. The short reply did
not separately label support; do not invent those binaries or aggregate scores.
Exact feedback is recorded in human_calibration_v1/list_boundary_labels_001.json.

### Separate support judgments confirmed

Kyle confirms support=yes for both C050 A (missing maps) and B (extra repair
facilities). Both therefore have C=no/S=yes. List completeness/relevance errors
belong to the conclusion check and do not automatically fail support that explains
the asserted items. This extends the earlier C007 incomplete-conclusion precedent.
No aggregate score is yet assigned. Record: list_support_labels_001.json.

## Contradiction aggregation resolved — 2026-10-14

Kyle confirms A (missing basis)=Cyes/Sno, B (directly contradictory basis)=Cyes/Sno,
and C (sufficient basis)=Cyes/Syes. A and B must receive the same aggregate score.
Do not introduce a contradiction-specific veto or additional override in the
planned split judges. Retain distinct failure diagnostics and acknowledge the
edge-case limitation in the writeup. This supersedes earlier suggestions to
consider a veto; the complete aggregation table and abstention branch still need
confirmation. Record: human_calibration_v1/contradiction_labels_001.json.

## Abstention routing resolved — 2026-10-14

Kyle treats explicit abstention as reporting, not a semantic judge question.
Detect it before judging and skip both adequacy judges. Record not-evaluated
component status rather than inventing false component labels. Whether abstentions
enter an aggregate metric denominator is a later explicit reporting decision;
retain counts needed to report either treatment.

For the specific B example (documents specify no requirements, supported only by
failure to find passages), Kyle proposes C=no/S=no. Encourage target generation
to use explicit abstention when evidence is insufficient, not infer document-wide
absence from failed retrieval. This does not turn all negative findings into
abstentions or failures. Preserve the source-factuality boundary when defining the
operational conclusion check; this one example is not permission to add source
fact-checking to adequacy. Exact feedback: abstention_decision_001.json.
No runtime changes, provider calls or denominator policy selected.

## First-pass aggregation approved; denominator choice deferred — 2026-10-14

Kyle selects the gated mapping: C=no/S=no ->0; C=no/S=yes ->0;
C=yes/S=no ->1; C=yes/S=yes ->2. No contradiction-specific override.
This supersedes prior open aggregation choices; retain both binary decisions
alongside the derived score. Explicit abstentions skip judging and have
not-evaluated components, not an invented semantic0. Retain response status and
counts so denominator choices can be made later; reporting policy is deliberately
deferred and is not a blocker for rubric consolidation.

Abstention detection is expected to be perfect as a prerequisite routing check,
not a semantic judge model-selection dimension. Verify that routing expectation;
do not describe it as an observed model result without testing. Raw status and
judge-component outputs must permit either later denominator convention.
Decision: human_calibration_v1/score_mapping_approval_001.json. No inference or
runtime migration performed.

## Reference-answer authority clarified — 2026-10-14

Kyle fixes the remaining conclusion-correctness boundary: the provided approved
reference answer is the required substantive answer in every case. The candidate
conclusion must convey that answer and cover all parts of the question. Equivalent
wording is allowed; a substantively different answer is not accepted merely because
it could be independently valid. This supersedes any broad earlier suggestion to
accept alternative conclusions.

Alternative supporting reasoning is permitted when it logically and sufficiently
justifies the same required conclusion. Do not require reproduction of reference
support wording, order or grouping. Grounding remains responsible for source
factuality. The conclusion judge compares to the approved answer and requested
coverage; it does not adjudicate new possible answers by researching sources.
Record: human_calibration_v1/reference_answer_authority_001.json.
