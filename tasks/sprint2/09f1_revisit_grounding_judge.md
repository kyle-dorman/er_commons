# Task 09F.1 — Establish no-answer and support-point grounding judges

Status: **complete with documented limitations, including 09F.2 cleanup**.
Kyle selected Luna for A v2 and G v3 on 2026-10-16. Both independent components
have completed prompt calibration, full-development three-model comparisons,
offline validation and handoffs: [A](../../docs/specs/task09f1_a_inspect_handoff.md),
[G](../../docs/specs/task09f1_point_grounding_handoff.md). Full-pool labels remain
reviewed agent proposals. The subsequent user-requested
[production cleanup](09f2_cleanup_production_judges.md) passed independent review and full offline validation (3,975 tests
passed, one skipped), completing closeout of 09F and 09F.1. Task 12 owns integration; 09G owns challenge/freeze.

## Historical development contract

The original contract below records initial inputs and milestones. Its untested
and pending-selection statements describe that starting point; the current status
and component handoffs above supersede them.

## Abstract

Establish two independently testable judge components: conclusion-only no-answer
classification and cited supporting-point grounding. Identify success/failure
families, build small reviewed edge-case sets, iterate on prompts, then compare
GLM, Luna and Haiku on frozen full-development datasets before model selection.
Existing adequacy S/C remain unchanged. Combined benchmark reporting belongs to
[Task 12](12_integrate_evaluation_and_reporting.md), not this judge-development task.

## Goal and boundaries

| Component | Question | Model-visible material |
| --- | --- | --- |
| No-answer classifier | Does the conclusion clearly abstain, make an answer assertion, or remain unresolved? | Original conclusion text only; code separately requires empty support, qualifications and other prose before accepting abstention |
| Grounding, per point or factual qualification | Do this item's own citations establish its factual assertions? | Original item text, its own cited passages and question; no attached answer text or model-visible point ID |

No-answer classification is a routing prerequisite, not another grounding score.
Use clean_abstention / substantive / ambiguous for the conclusion. Only clear
abstention plus empty other prose may skip semantic judges. A declining conclusion
with nonempty other prose is inconsistent/unresolved. Validate structure before
classification, but enforce required substantive support afterward. No category
asserts correctness or evidence sufficiency. Version this change from the legacy
whole-response classifier; malformed/blank conclusions are mechanical failures.

Grounding checks sources against premises. Adequacy S checks whether the original
premises jointly establish the whole candidate conclusion, taking factual premises
as given. C compares the conclusion with the approved answer. Grounding and S/C
consume no other semantic judge's verdicts or explanations. The no-answer route
must be tested independently before it controls whether those calls run.

The accepted replacement has no conclusion-grounding call, point re-review,
review-disagreement gate, support filtering or prediction forwarding. Supporting
points carry citations; the replacement answer contract does not require conclusion
citations. A claim introduced only in the conclusion must be caught by unchanged
S's whole-conclusion sufficiency criterion; this is not a direct conclusion audit.

The strict all-grounding-pass AND S-pass AND C-pass design remains accepted, but
its joins, aggregate statuses, score denominators and real-answer composition
checks are deferred to Task 12. This task retains the IDs, versions, raw outcomes
and statuses that integration will need. Component-development metrics remain here.

## Inputs

- Accepted [no-answer rules](../../docs/specs/no_answer_labeling_rules.md)
  and [no-answer contract](../../docs/specs/task09f1_no_answer_judge_contract.md).
  They now record conclusion-only detection and the deterministic empty-field guard.
  The [first candidate prompt](../../docs/specs/task09f1_no_answer_judge_prompts.md)
  is untested; accepting rules does not select or qualify a prompt/model.
- Accepted [grounding rules](../../docs/specs/grounding_labeling_rules.md) and
  [grounding contract](../../docs/specs/task09f1_grounding_judge_contract.md).
  Qualifications use the same independent G call as points. The
  [locked starting G prompt](../../docs/specs/task09f1_grounding_judge_prompts.md)
  adapts C/S JSON hints to the two-field output and is not yet tested.
- [Historical probe-catalog review](../../docs/specs/task09f1_grounding_probe_review.md)
  maps the original 31 categories and adequacy additions to the new G boundary.
  Use it to consider edge coverage, not to inherit old scores or expand the prompt.
- Accepted 09F outcome, current C/S selections from [the index](../../docs/index.md),
  [adequacy rules](../../docs/specs/adequacy_labeling_rules.md) and
  [binary contract](../../docs/specs/task09f_binary_judge_contract.md).
- [Current question release](../../docs/specs/task09f_question_publication_v2_result.json),
  `task09f_20261014_v2`, with 19 development questions. Bind any approved successor
  explicitly before execution; do not access the 30 benchmark test questions.
- [Grounding guide](../../docs/grounding_judge_guide.md),
  [experiment record](../../docs/grounding_experiment_record.md), existing answer-only
  abstention classifier and point-grounding projection/validation/provider code.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [sprint boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary),
  and [artifact rules](../../docs/data_artifacts.md).
- Historical abstention and grounding trials as design evidence, not current
  qualification. Reuse failure examples/methods only with explicit lineage and
  new review; build a separately identified no-answer set rather than relying on
  a few abstention controls embedded in grounding experiments.

## Outputs

- Maintained no-answer and grounding policies/prompts plus versioned component
  input/output/routing contracts, with unrelated invented policy illustrations.
- A reviewed success/failure catalog and independently identified small calibration
  dataset for each component, including expected labels and applicability records.
- Broader development datasets with reviewed labels across applicable coverage of
  all 19 development questions: conclusion-only no-answer and per-point grounding,
  with separate whole-answer fixtures for the deterministic abstention guard.
- Bounded small-panel prompt-cycle records, frozen prompts, then full-development
  GLM/Luna/Haiku comparison and explicit component selection/limitations.
- Replacement point-only execution and isolated no-answer execution through existing
  Inspect/provider infrastructure, offline tests, receipts and replay support.
- A 09G judge-freeze handoff and Task 12 integration handoff. No combined-reporting
  implementation or conclusion-grounding dataset is required for completion.

## Research / learning checkpoint

[Inspect scorers](https://inspect.aisi.org.uk/scorers.html) support custom component
scoring, separate metrics and offline analysis. Reuse the current evaluator.
[Autoevals Faithfulness](https://github.com/braintrustdata/autoevals/blob/16074252ff5d0a9422f1bf572768afa93c11b8f6/py/autoevals/ragas.py#L948)
illustrates source checks, but its statement extraction and averaging are not this
rubric. Our answers already have points and restricted citation ownership.

Review prior abstention false exemptions and false rejections, and negative richer-
explanation trials. Explain why a false clean-abstention result can hide substantive
errors, why source-supportedness differs from logical sufficiency, and why valid
JSON/exact quotation does not establish a correct judgment. More diagnostic
structure needs a concrete purpose, not library parity.

## Plan / spec requirement

### 1. Define policies and identify success/failure families

Write the two compact policies and input/output contracts before generating labels.
For no-answer, follow the short rules/contract: classify conclusion text, then code
requires empty other prose before accepting abstention. Distinguish clear declines,
negative/hedged/partial answers, mixed conclusions and unresolved filler. Test the
guard separately; status flags and keywords alone cannot decide the route.

For grounding, accept paraphrases and jointly sufficient cited passages while
preserving quantities, negation, scope, timing and uncertainty. A compound point
fails if a material assertion is unsupported. Missing an unasserted answer part
belongs to C. Define eligibility before predictions. Code fails required points
with missing citations or any unresolved candidate ID before a G call; retain
precheck failures in accounting rather than silently excluding them. Only nonempty,
resolved owned evidence reaches the model. Valid artifact-loading failures remain
evaluator errors. Clean abstention is checked before the support requirement.

Treat material factual qualifications, including ones attached to the conclusion,
as individual G points with their own original text and owned citations. Keep IDs
and attachment links outside model input; do not attach qualification text to another
point's G request or show the conclusion. Do not leave unchecked
premises in a separate field or allow essential premises to evade grounding through
an optional-context label. Distinguish nonfactual limitations and context-only citation
metadata. Existing legacy projection includes optional-context points; review it
instead of silently inheriting that scope. No linked answer prose enters G.

Version the new projection/schema and identify affected producer/consumer migration.
Do not rewrite approved references, erase legacy conclusion citations or relabel old
0/1/2 results. Distinguish mechanical citation errors from semantic unsupportedness.
Leave automatic-metric policy and combined-reporting migration to their owning tasks.

### 2. Build small reviewed edge-case sets

Turn the catalogs into two small, separately frozen datasets, with passing controls
paired with failures wherever feasible. Choose counts, generator, allocation and
review workload at activation. Review labels before predictions. Record original
text, exact edits, evidence for grounding, versions, category, applicability and
rationale; keep expected labels and category hints outside judge requests.

Use explicit reviewed three-way conclusion labels, independent of grounding scores
or legacy N/A expectations. An ambiguous prediction must remain in coverage/error
accounting rather than silently disappearing from accuracy. Mixed abstention and
clear assertions are substantive. Ambiguous includes unclear intent and generic
filler without explicit abstention. Reconcile this versioned boundary with legacy
routing documentation.

No-answer semantic coverage includes clear declines, negative/hedged/partial
answers, mixed refusal/assertion conclusions, long conclusions, unresolved filler
and embedded instructions. Separate guard/validation fixtures cover misleading
status flags, abstaining conclusions with prose in other fields, empty support,
and blank/malformed conclusions. Generic failure to answer is not clean abstention.

Grounding coverage should include paraphrases; contradictions/unsupported additions;
changed numbers, units and entities; conditions/modality; missing/wrong/insufficient
citations; joint evidence; mixed-support compound points; qualifications; and
incomplete but fully grounded assertions. Record ambiguous/inapplicable slots rather
than forcing every family onto every question. Existing examples may inform this
work but do not replace independent review of the new sets.

### 3. Implement isolated calls and cycle on the small sets

Reuse maintained providers, budgets, receipts, caching, strict parsing and Inspect.
Prepare both component requests independently. Grounding development must run on
known substantive examples without relying on a model-predicted no-answer route;
otherwise a routing error could remove its hardest cases from evaluation.

Start with concise outputs: no-answer category/reason and per-point boolean/reason.
No new mandatory extraction or inventory is required. Preserve raw responses,
mechanical failures and quotation diagnostics separately. Verify that S/C receive
all original support and no source evidence or grounding predictions. No conclusion
or re-review call should be emitted by the replacement path.

Run bounded prompt cycles on the small reviewed sets. Inspect failures by family,
retain controls, and change one declared factor at a time. Fix label/data defects
only with explicit versions and source/text-based rationale. Record the prompt
revision budget and practical exit criteria before cycles; do not invent a perfect-
accuracy threshold or silently continue tuning. Use the same intended semantics
across models and document provider-specific formatting differences.

### 4. Freeze prompts, compare full development sets, select models

Once the small-set prompts are satisfactory, freeze their exact bytes and schemas.
Build/review the broader sets using the accepted catalogs across applicable coverage
of the 19 development questions; freeze labels before prediction. The full no-answer
set contains conclusion inputs; retain complete answers separately for guard checks.
Grounding contains point-level items. Declare counts
and exclusions explicitly. Broader sets remain development data, not untouched
benchmark test data; disclose overlap with small-panel examples/base questions.

Compare GLM, Luna and Haiku on the same frozen dataset and repeat count within each
component. Bind exact model/settings and declare k, concurrency, retry policy,
currency/request/token/wall-time caps before dispatch. Fresh runs preserve all
attempts and uncertainty; old authorizations or saved-result replay are not fresh
inference. Do not silently tune prompts separately on full-set errors. Any needed
post-comparison repair is a newly scoped development experiment with controls.

Report per-component accuracy/agreement, macro-F1, confusion counts, valid-output
coverage, category/failure-family breakdowns, control regressions, cost and latency.
For no-answer, highlight substantive conclusions misclassified as abstention and
clear abstentions missed; retain ambiguous cases distinctly. Actual exemption also
requires the guard. For grounding, highlight false
acceptances/rejections. Declare failure-inclusive and valid-only conventions.
Report observed correct-across-all-k pass^k, all-k-valid and same-label agreement;
invalid/missing judgments prevent an all-correct pass. Do not exponentiate pooled
accuracy or treat correlated variants as independent questions.

Select the best-supported configuration for each component after the complete
comparison. The same model need not win both. Preserve adequacy selections and
record ties/limitations instead of expanding beyond these three models.

### 5. Hand off the established judges

Give 09G the frozen component prompts/configurations, policies, schemas, data
identities, replay instructions, comparison results and unresolved weaknesses.
Give [Task 12](12_integrate_evaluation_and_reporting.md) saved component records,
answer/point identity requirements and routing semantics. Task 12 owns actual
route integration, aligned G/S/C joins, strict all-checks-pass reporting, aggregate
availability/denominators and real-answer composition tests. Task 13 publishes the
locked results using that frozen integration. These are not 09F.1 completion gates.

## Validation

- Verify development membership, text/evidence ownership, source/answer/policy/
  prompt/schema/label identities and no test/reserved access or label leakage.
- Independently review both catalogs, small sets, broader labels, qualification
  eligibility and controls. Proposals are not automatically human gold.
- Test conclusion-only no-answer projection, empty-field guard, missing-support
  check ordering, misleading flags, mechanical failures,
  isolated grounding with fixed applicability, no conclusion/review calls, unchanged
  S/C inputs, no filtering/prediction leakage and historical replay.
- Recompute component comparisons/reliability from saved observations; retain raw
  errors, unknowns and all eligible counts. Do not build combined benchmark scores.
- Implementation: focused offline tests, `make fix`, `make check`, `git diff --check`.
  Planning: inspect Markdown, local links and whitespace.

## Review pass and acceptance criteria

Use bounded independent policy/data and evaluation-accounting reviews. Finish with
two explicit policies, independently reviewed small/broader datasets, preserved
prompt-cycle evidence, full three-model comparisons and explicit no-answer/grounding
selections ready for 09G. Disclose routing risk, proposed-label status, correlated
examples and remaining weaknesses. Combined reporting is not an acceptance criterion.

## Non-goals

Combined reporting/strict-score implementation; conclusion grounding; re-review;
support filtering or prediction forwarding; changing S/C prompts/policy; generation
agents/retrieval experiments; installing another framework; mandatory extraction;
test/reserved access; incidental automatic-metric/reference changes; models beyond
GLM/Luna/Haiku; rewriting historical scores; commit or push.

## Outcome

No-answer rules and contract are locked around conclusion-only classification
and a deterministic empty-field guard. Only clear abstentions qualify; generic
filler stays unresolved. Abstention precedes substantive-support requirements.
The first prompt is proposed but untested. No cases or runtime were created.
Grounding rules and contract are now locked around the maintained per-point
criterion, with the question used only for interpretation. Qualifications are
ordinary independent G items; other answer context and point IDs are excluded from
model input/output. The starting G prompt is now locked, with C/S JSON-format
guidance; this acceptance does not qualify a model or authorize calls.

The plan now establishes no-answer and supporting-point grounding through explicit
success/failure catalogs, small reviewed edge-case sets and bounded prompt cycles,
then frozen full-development three-model comparisons and selection. Combined
reporting and composition are assigned to provisional Task 12, with final publication
in Task 13. No judge implementation, dataset generation or provider calls ran here.

Planning validation: bounded independent review found no blockers; local links,
Markdown fences and `git diff --check` passed across the updated planning files.
