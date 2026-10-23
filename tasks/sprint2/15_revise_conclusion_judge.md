# Task 15 — Revise and qualify the conclusion judge

Status: closed at user request after the code-quality pass and final validation.
The conclusion-judge revision, reference cleanup/publication and saved-answer
comparison are complete. Current references: [15AC](15ac_publish_materiality_references.md).
Latest diagnostic comparison: [15AB](15ab_rejudge_approved_materiality_labels.md).
Remaining judge uncertainties are documented, not manually rescored.

Three separately activatable follow-ups remain; closing this parent does not
claim these are implemented or run:
1. [15Y — Required-support coverage judge](15y_required_support_coverage_judge.md).
2. [15Z — Required/context citation review](15z_required_context_citation_review.md).
3. [15AD — Final end-to-end run](15ad_final_end_to_end_run.md).

The accepted C configuration is Luna/v6, one judgment per answer. Task14 is complete;
Task16 writing remains separately activated. The user authorized committing this
Task15 work after quality checks, not pushing. No additional model calls, MiniMax
or reserved-challenge access are authorized by closeout.

## Abstract

Repair C's distinction between a directly responsive answer, its supporting
explanation, and compatible information absent from a concise reference. Update
the general labeling rules, perturbation catalog and C prompt together; regenerate
and review a synthetic C suite; iterate on the original six and then all nineteen
development questions; freeze the revision; reevaluate the full thirty-question
test population; and review selected conclusion outcomes before writing results.

The goal is better justified judgments, not a higher target-model pass rate.
Preserve the original judge, labels, answers and score publications. New results
are a versioned evaluation condition, never corrections silently applied to Task 13.

## Goal and scope

Keep C focused on whether the conclusion answers the question and preserves the
direct answer's key facts. Leave the validity of supporting reasoning to S and
source grounding of supporting/qualification points to G. Investigate a definition
of key fact through reviewed contrasts rather than adding an exhaustive list of
case-specific mandatory reference details.

The original bounded C revision retained question wording, source packets and
A/G/S semantics. The later user-authorized dependency reset above adds reference
adjudication and subsequent target-generation alignment. Each execution phase
needs its own recorded input versions and comparison condition.

### Meaning of the requested rerun

The user selected Luna with one judgment per answer and explicitly requested
saved-answer judging first as an educational comparison. [15E](15e_rejudge_saved_development.md)
completed all114 development answers with the revised C core and unchanged old
project overview, replacing only C for derived same-answer outcomes.

The user also stated that the target-generation prompt must reflect the new judge
rules and that a fresh end-to-end rerun is needed afterward. This intent replaces
the prior pending choice between saved-only and fresh generation. Preserve the
saved-answer comparison as attribution evidence, then separately specify the
aligned generation prompt, exact fresh population and numerical budgets before
dispatch. Fresh generations require all applicable judges and cannot reuse old
judgments. Their score changes mix target behavior with evaluator effects.

## Accepted inputs and implementation owners

- [Task 14 result pointer](../../docs/specs/task14_result.json) selects the accepted
  eight-answer synthesis, exact selection, current state, journals and quality
  receipts under the external Task 14 root. Follow those designated paths rather
  than older state/manifest revisions. The selected forms and
  `conclusion_judge_design_discussion.v2.md` preserve feedback and uncertainty.
- [General adequacy policy](../../docs/specs/adequacy_labeling_rules.md),
  [perturbation catalog](../../docs/specs/task09f_adequacy_perturbations.md),
  [historical C authoring handoff](../../docs/specs/task09f_conclusion_synthesis_handoff.md),
  [judge guide](../../docs/judge_maintainer_guide.md), and
  [09G freeze](../../docs/specs/task09g_judge_freeze_v1.json).
- `src/er_commons/adequacy_binary.py` owns C/S prompts, schema and parsing;
  `adequacy_inspect.py` owns the native adapter; `adequacy_binary_development.py`
  loads historical synthetic data. `configs/judges_selected_v1.json` records the
  original C Luna/v8 and unchanged A/G/S selections. The historical loader's C246
  population is not the new synthetic suite.
- [11E frozen configuration](../../docs/specs/task11e_frozen_generation_v1.json)
  and [development reporting pointer](../../docs/specs/task12_result.json) bind
  saved development answers; [Task 13 pointer](../../docs/specs/task13_result.json)
  binds the completed 180 test answers and original scores.
- [Reporting guide](../../docs/reporting_maintainer_guide.md) and Task 12's
  [definitions](../../docs/specs/task12_reporting_v1.md),
  [presentation](../../docs/specs/task12_presentation_v2.md),
  [repeatability](../../docs/specs/task12_judge_repeatability_v3.md) and
  [counting](../../docs/specs/task12_response_units_v4.md) amendments.

Use maintained package-backed interfaces and native Inspect; add narrow loaders
and comparison glue where needed. The existing `make evaluate-adequacy` default
reads the old synthetic development publication, not saved target answers.
Do not run it assuming it selects a Task 15 population.

## Findings motivating the revision

These are adaptively inspected examples, not an independent qualification set.
The selection manifest owns exact run/candidate/repeat/point IDs and frozen scores.

| Review | Frozen observation | Interpretation and remaining uncertainty |
| --- | --- | --- |
| U02: C003 Luna repeat 2, test | G/S pass, C fail; impact scope appears in S1 but not C1 | Task 14 deferred materiality. In Task 15 discussion the user judged the explanation insufficient: updated analysis/new information does not state the new/worsened-impact finding, and “call for additional mitigation” restates the need. Preserve that meaning without requiring the exact phrase. Frozen scores and Task 14 records stay unchanged. |
| U06: C002 Luna repeat 1, test | G/S pass, C fail | Judge misses “residential calm” and rejects comfort/privacy additions absent from reference. User distinguishes the intended outcome from its concrete noise/air-quality buffering mechanism. Source P2 explicitly mentions privacy and pedestrian comfort. Test semantic equivalence and reference coverage separately. |
| U07: C025 Haiku repeat 3, test | G/S pass, C fail | Both reference triggers are matched; judge rejects the additional any-district 50% occupancy deadline. P1 explicitly states that deadline alongside the commercial-district trigger. User agrees this appears to be what happened. It is a source-supported addition missing from the label, not demonstrated contradiction. |

Keep the broader Task 14 lessons as regression constraints:

- Correct conclusions can mask flawed supporting claims. Explicit points and
  owned citations expose those flaws; reducing C false failures must not hide G/S
  failures or certify hidden model reasoning.
- Haiku C037 repeats prose contradicted by supplied wetland tables in an
  unnecessary point. Appendix D's 0.00 values were visually verified. Source
  contradiction contributes; this is not clean evidence of fabricated content.
- Luna C042 makes a plausible scope qualification without citing the significance
  finding it qualifies. The user agrees with that G failure. Matched C003 S4 is
  ambiguous: Luna cites P1/P4; Haiku cites P4, which omits the exact MMRP name.
- Qualifications can help: Haiku C021 limits claims about present public-review
  status; C003 Q1 separates lighting effectiveness from bird-collision rationale.
- Test point counts: Luna support 15/284 failed and qualifications 3/60; Haiku
  support 54/408 and qualifications 46/234. These are frozen judge outcomes, not
  human error rates or proof that elaboration causes errors. Development stays
  separate. The later failure-analysis writeup should discuss volume and failure
  fractions alongside these qualitative distinctions.

## Proposed rule direction — resolve before implementation

### Independent component responsibilities

| Component | Responsibility retained |
| --- | --- |
| A | Classify substantive-answer versus abstention routing. |
| G | Ground each support/qualification point in its own cited evidence. |
| S | Check whether stated premises jointly justify every material conclusion claim, treating premises as given. |
| C | Check question fulfillment, directly responsive meaning and genuine contradictions against the approved answer. |

C continues to receive **question, candidate conclusion and reference conclusion
only**. It does not receive source passages, supporting points, G/S verdicts,
synthetic labels or reviewer notes. Requiring source verification would be a
different interface and is not the proposed repair. C never infers that an extra
claim is source-supported; it simply does not infer falsehood from reference
absence. G/S retain their independent duties and joint remains a downstream
same-answer conjunction. A passing S alone does not establish factual truth.

G does not directly check conclusion or optional-context prose. Include explicit
composition tests so unsupported conclusion-only additions fail S when no premise
justifies them, and unsupported premises fail G. If a material claim can escape
all components, document that gap instead of granting a G/S-pass override to C.

### Working definition of a directly responsive key fact

A fact is a candidate key fact when it fills something the question requests and
changing or removing it changes or leaves incomplete the substantive answer to
that request. Relevant entity, polarity, location, quantity, timing, exception,
condition and requested causal relationship may be key facts. Their role depends
on the question, not on appearing in the reference or having their own bullet.

Supporting detail explains, illustrates or substantiates the answer without
changing it. Context supplies background. Do not make every detail mandatory or
introduce a new per-question exhaustive fact inventory as the default solution.
For why/how questions, a substantive reason or mechanism is itself requested;
“because the old measures are insufficient” may be circular and cannot pass by
deferring the entire answer to S. Facts buried only in support do not rescue a
conclusion that leaves a requested dimension unanswered.

### Additions, omissions and contradictions

1. Accept semantic equivalence, including a concrete mechanism expressing the
   purpose named more abstractly in a reference. Explain the requested meaning
   lost before calling an omission material; a missing phrase alone is insufficient.
2. Distinguish additional compatible information from a changed answer. An extra
   deadline is not automatically a contradiction of another stated deadline.
   Require an actual incompatible meaning, polarity, threshold, condition or
   relationship to call it conflicting.
3. Do not reject explanatory or contextual additions solely because the reference
   omits them. Relevant additional answer facts may also be valid. Their logical
   basis belongs to S and their factual premises to G; C does not certify them.
4. Fail changed or missing directly requested facts, material reversals,
   unconditional guarantees replacing conditions, retractions of the answer,
   evasive nonanswers and material internal contradictions.
5. Do not infer exclusivity from bullet formatting. Exhaustive-list behavior is a
   protective contrast to test, not an established explanation of the observed
   failures, which concern interpretation within individual items. Decide how
   explicit “all/only/exactly” questions establish completeness without turning a
   concise reference into proof no other valid item exists.

Historical C v8 rules 3/6 constrain alternative answers and extra items; the old
catalog's A02 rejects extras even when true. Task 15A replaced that rule in a
versioned candidate and updated the maintained policy. Task 15B's new catalog
and independently reviewed expectations apply the accepted semantics without
changing the old labels. A cosmetic “be flexible” addition would be insufficient.
Keep S behavior unchanged; update shared documentation only where the C/S boundary
must be explained. Do not implicitly alter target-answer instructions.

## Research and learning checkpoint

Read the current code and historical authoring contracts before designing a new
runner. Record the policy delta, rejected alternatives and why the existing
standard-library JSON/CSV + Inspect boundary fits this task.

Primary sources checked during planning (2026-10-21):

- [G-Eval, Liu et al., EMNLP 2023](https://aclanthology.org/2023.emnlp-main.153/):
  structured evaluation criteria and form-based outputs; reported evaluator bias
  motivates independent expectations. It does not validate our revised rubric.
- [Zheng et al., 2023, v4](https://arxiv.org/abs/2306.05685v4): judge limitations
  including verbosity/self-enhancement biases motivate checking both false accepts
  and false rejects rather than rewarding higher pass rates.
- [Inspect datasets](https://inspect.aisi.org.uk/datasets.html) and
  [evaluation logs](https://inspect.aisi.org.uk/eval-logs.html): native sample IDs,
  separate labels/metadata and saved logs fit auditable, versioned comparisons.
- [DocScope §§4/B.5/F.6](https://arxiv.org/html/2605.08888v2) and
  [LongDocURL §5/Appendix G](https://arxiv.org/html/2412.18424v3): retain the Task 14
  distinction between source, answer and evaluation limitations. Do not transplant
  spatial grounding metrics or claim a selected review estimates error prevalence.

## Staged plan and decision gates

Treat this as an umbrella. At activation, create the first bounded implementation
subcontract; later subcontracts are provisional until their preceding gate passes.
Do not implement a whole new evaluator framework.

### 15A — Settle the rule and comparison contract

- Consume the accepted eight-answer Task 14 synthesis and completed quality pass;
  preserve unresolved judgments. No repeat confirmation of that outcome is needed.
- Write a versioned C rule specification, input/output projection, policy delta,
  general perturbation catalog and decision examples in unrelated invented domains.
- Discuss key-fact boundaries with the user using positive/negative contrasts.
  Resolve broad additions versus true answer changes without case-specific hacks.
- Pin the original C prompt/schema/model and all saved source publications.
  Freeze the unchanged A/G/S and target identities. Decide whether C diagnostic
  statuses/reason codes need a versioned schema change; retain strict parsing.
- Inventory legacy synthetic C labels that change meaning. Preserve the old suite
  and labels; do not mechanically turn previous failures into successes.
- Define finite candidate/iteration limits, repeated-judge policy, numeric budgets,
  acceptance metrics and the final-run type before dispatch. Proposed iteration
  ceiling: three synthetic/six-panel candidates, then at most two revisions on
  all nineteen; a further cycle requires a named failure and revised bound.

**Gate:** user-reviewed policy and concrete execution plan. Planning figures are
not inherited paid-call authorization or a reason to reuse Task 13's old budget.

### 15B — Regenerate and review synthetic C tests

The bounded [15B authoring outcome](15b_regenerate_conclusion_cases.md) and
[result pointer](../../docs/specs/task15b_conclusion_synthesis_result.json)
select the completed 340-case publication. It follows the development-derived
pattern below with 25 declared slots per question; the optional 120-item proposal
was not adopted. Tuning/audit groups contain 259/81 variants on 15/4 familiar
development questions. Source-grounding and full-answer composition diagnostics
remain outside this C-only publication.

Create a fresh C suite against the revised general rules. Start from the accepted
nineteen-development-question authoring pattern: regenerate applicable C variants
from approved question/reference inputs with newly justified expectations, rather
than editing old labels in place. Use the maintained tooling and general failure
catalog; historical labels and reserved payloads are not inputs to a new decision.
Invented unrelated scenarios may supplement coverage; do not copy
exposed test questions/references into prompt examples or supposedly independent
synthetic qualification items. Abstract failure mechanisms can motivate coverage.

An optional sizing proposal is **120 items**, 96 tuning and 24 separately frozen
audit items. This does not replace the existing development-derived regeneration
approach without the 15A design decision. Balance expected pass/fail and group by
scenario so paired or near-duplicate variants cannot cross partitions. An audit
of new variants on familiar questions is not unseen-question qualification.
Final counts and generator,
applicability rules, sampling seed and any costs are fixed at 15A, before authoring.
Represent at least these contrast families:

- Equivalent paraphrase versus missing requested fact.
- Concrete mechanism versus intended outcome; both adequate where equivalent.
- Substantive why/how explanation versus circular restatement.
- Compatible explanatory detail versus a contradictory addition.
- Relevant extra answer fact versus a changed entity, quantity, trigger or exception.
- Necessary scope/uncertainty retained versus a misleading guarantee.
- All requested dimensions versus one addressed only in supporting text.
- Helpful qualification versus a caveat that withdraws or changes the direct answer.
- Plain-language question versus a genuinely exhaustive or exclusive request.
- Verbose nonanswer versus concise sufficient answer; no length reward.
- Correct conclusion with unsupported added premise (C may pass; G must fail).
- Unsupported conclusion-only addition (S must fail when premises do not justify it).

Author full-answer composition fixtures where needed, but only regenerate C's
semantic dataset initially. Default composition checks are offline packet/role
fixtures and reuse existing A/G/S receipts where an exact applicable identity
exists; do not imply that deterministic fixtures demonstrate live judge behavior.
Any new A/G/S calls to test the composition require a separately itemized bounded
development diagnostic arm in 15A, not an implicit full requalification.
S/G/A models/prompts and historical data stay fixed.
For each example save scenario, perturbation, applicability, proposed C label,
reason, version, author/reviewer identity and separate expected component behavior.
Keep expected labels and source truth outside C's messages. Review for leakage,
ambiguity and negative-control strength. Independent agent checks supplement human
review; mark unresolved examples separately, never infer human gold from intention.

Create a new explicitly selected loader/publication; do not replace hardcoded
historical C246 bindings. Record whether old disclosed synthetic examples remain
applicable, need revised proposals, or are excluded. Original reserved challenge
payloads remain unopened. A newly frozen audit partition is separate from them.

**Gate:** reviewed dataset, label counts, ambiguity dispositions and sealed
partition before judging. Choose coverage/acceptance thresholds before results.

### 15C — Implement and iterate on synthetic data and original six

- Version the C prompt and necessary schema/adapter changes; keep the original
  executable path available for replay. Candidate selection is explicit, not an
  implicit overwrite of `judges_selected_v1.json` or old prompt constants.
  Current version checks accept the selected prompt only; extend candidate
  selection explicitly without monkeypatching globals or weakening identity checks.
- Evaluate positive/negative synthetic controls. Optional judge stability policy,
  to settle and budget at 15A rather than silently multiply requests:
  three calls per synthetic item, reporting each result and complete triples;
  no majority-vote relabeling or favorable repeat selection.
- On exact saved 11E answers, evaluate the original six development questions:
  **C041, C017, C019, C014, C037, C056**. These are question IDs, not Task 14's
  initial six answer instances. Two models × three saved answer repeats = **36
  candidate C slots per prompt version**. No new target generation is needed.
- Compare new C with frozen old C on the same candidate bytes; show changed and
  unchanged cases and G/S cross-patterns. Retain failures and invalid judgments.
  A comparison with one historical judgment does not isolate judge stochasticity.
- If needed, preselect a bounded same-candidate old/new repeated-judge control arm
  to measure that variability. Judge repeat IDs are separate from answer repeat
  IDs; these diagnostics cannot silently replace the canonical per-answer C result.
- Review bounded disagreements, revise within the iteration ceiling, and preserve
  negative results and policy changes. Better target pass rates alone cannot select
  a candidate. Do not inspect more test prose to guide these iterations.

**Gate:** improved agreement on intended semantic contrasts with protective
failures retained, stable valid output, and documented limitations. Freeze a
candidate before the broader development check.

### 15D — Expand to all nineteen development questions

Evaluate both models' three saved answers for all nineteen questions: **114 C
slots**, including the initial 36. If prompt, model, settings and input bytes
are identical, reference accepted first-stage receipts and add **78** slots;
otherwise run the full 114 under a fresh version. Never mix prompt versions.

Report new/old C transitions and reconstructed joint outcomes using unchanged
automatic/A/G/S. Assess per-model false-failure mechanisms, critical false accepts,
invalid outputs and affected questions without merging synthetic-label metrics
with target pass fractions. Review a bounded sample of changed and unchanged
judgments, including a negative control and G/S failures C must not excuse.
If a rule revision is needed, return to synthetic protective contrasts and the
six-panel regression checks. Record why; do not iterate to optimize these nineteen.

**Gate:** user-reviewed all-nineteen outcome, limited regressions explained, and
final candidate selected on rule adherence, not ranking or desired score uplift.

### 15E — Frozen audit and implementation preflight

Freeze policy, prompt/schema, model/settings, all sample/reference identities,
loader, reporting code, canonical judge-repeat policy and numerical run caps.
Evaluate the new audit partition only after this freeze. If its errors cause
further tuning, mark that partition exposed and create a separately frozen audit
set; never keep calling the same audit held out after tuning on it.

The proposed synthetic thresholds to settle at 15A are: at least 95% valid output,
at least 90% label agreement separately for expected-pass and expected-fail groups,
and zero observed accepts on predesignated critical contradiction/material-omission
controls across planned repeats. Also require no regression in critical-control
rejection versus the old C arm on comparable reviewed labels. These are proposed
engineering gates, not claims of calibration or guaranteed target accuracy.

Run meaningful parser/identity/input-isolation/replay tests, `make fix`, `make
check`, `git diff --check`, and an independent bounded review. Compute a request
and cost budget including authoring, all candidate versions, counts, diagnostics
and final runs; specify token/time/concurrency caps, retries and stop/resume rules.
Verify provider costs at execution time; unknown fees remain explicit.

**Gate:** accepted frozen revision and a fresh execution preflight. No original
reserved judge-challenge access or historical spending cap is inherited.

### 15F — Full thirty-question reevaluation

For the proposed C-only primary arm, evaluate **all 180 saved Task 13 answers**:
thirty questions × two models × three answer repeats, with one canonical revised
C judgment per applicable answer. Account for every planned slot and preserve
routing/N/A/unavailable cases. No new favorable answer selection or regeneration.

Recompute derived joint with the matching frozen automatic/A/G/S results, joining
by exact source run/candidate/answer-repeat identities. New evaluator run IDs and
prompt identity remain distinguishable. The revised C replaces only C in the
new reporting arm; it never changes original source files or historical tables.

If a fresh end-to-end arm was requested and budgeted, execute its separate 180
new answers and all applicable new judgments only after the saved-answer arm.
Keep target settings fixed. Report generator variance and new answer identities;
do not attribute a change in fresh-answer scores solely to the judge repair.

**Exposure limitation:** these thirty were already run, selectively inspected,
and used to motivate this policy revision. This is an **exposed-test retrospective
reevaluation**, not a fresh locked or untouched held-out test. Freeze before the
full run and do not change rules in response to its scores. Further tuning needs
a new version and an explicit exposure statement. Independent generalization
requires a future dataset; renaming this run cannot restore its held-out status.

### 15G — Repeat bounded conclusion-failure review

Select from completed C transitions before reading additional prose. Proposed
scope: six complete answer instances, expandable to eight for a named unresolved
question. Include fail→pass, retained fail, pass→fail if present, and a retained
pass; include both models and a C/G/S disagreement. Reuse diagnostic anchors when
useful and count them toward the bound. Report absent categories honestly.

Show question, exact conclusion, full model support/qualifications, labeled
reference, full relevant supplied sections/tables and old/new rationale. Save
user feedback one unit at a time; preserve disagreements and source limitations.
Assess whether revised decisions are better justified without new leniency on
material errors. Do not turn this into an exhaustive human-labeling audit.

**Gate:** confirmed synthesis of benefits, regressions and unresolved limitations.
If the repair is not convincing, report that and return to a separately bounded
development revision; do not proceed to writing as if success were established.

### 15H — Publish and hand off to Task 16

Seal accepted policy/prompt, synthetic publication, development comparison,
full-thirty reevaluation, costs, checks and user-confirmed review. Publish a new
Task 15 result pointer selecting exact artifacts and an explicit updated C freeze.
Update maintained guides to distinguish original and revised conditions. Retain
the original Task 13 pointer as authority for the original experiment.

Task 16 may be activated after acceptance to write the report using the designated
results, historical comparison and failure examples. Do not present a C pass-rate
increase as human accuracy improvement or mix old/new configurations in one arm.

## Outputs and provenance

Use a fresh root `ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_15/` with
versioned policy/prompt snapshots, synthetic cases/expectations/reviews, per-stage
selection manifests, exact input/output hashes, native logs, raw judgments,
cost/reservation records, comparison tables, review revisions and completion seals.
Track only small general specs/configs/code/tests and compact result pointers.
Source licenses/terms and authoring/model provenance remain discoverable.

One unchanged C-only pass over all nineteen plus thirty has **294 distinct target
answer slots** (114 + 180). The six-stage 36 is a subset of 114, not an additional
population. Extra candidate versions, synthetic repeats, count calls, control
arms and fresh target generation increase requests and must be budgeted separately.
Answer-repeat variability and same-answer judge-repeat variability stay distinct.

Comparison outputs retain model/question/answer-repeat/run/candidate/point IDs,
old/new C, unchanged automatic/A/G/S, old/new joint, rationale codes and availability.
Export pass→pass/pass→fail/fail→pass/fail→fail, valid/invalid/N/A and per-question
changes. Synthetic false accepts/rejects and label agreement use their own
populations and proposed/reference-label status, never target-model denominators.

## Validation and acceptance criteria

- General C rules, prompt and synthetic labels agree on direct-answer facts,
  compatible additions, real contradictions and reasoning delegation. Positive
  and negative controls demonstrate the boundary; no case-ID-specific rules.
- Why/how questions retain a real explanatory-answer requirement. Missing requested
  content cannot be rescued from unseen support, and material exceptions cannot
  be dropped merely to improve acceptance.
- Same-candidate comparisons verify unchanged target bytes and automatic/A/G/S.
  Reporting includes coverage and all repeats; no best-repeat selection or silent
  majority vote. Critical false accepts are inspected alongside false rejects.
- Synthetic data regenerates under versioned rules without rewriting old labels
  or opening reserved challenges. New audit exposure is honestly recorded.
- Development 6→19 stages and final30 identities are verified, numerical budgets
  fixed before calls, failures restartable, and original seals/pointers unchanged.
- Final full-thirty claims explicitly disclose adaptive exposure. Higher C or
  joint fractions alone do not establish that the evaluator improved.
- Bounded independent policy/data/implementation review, required project checks,
  exact excerpt/table verification and user-confirmed final failure analysis pass.
- Task 16 is activated only after the revised evaluation and limits are accepted.

## Non-goals

Changes to A/G/S, target prompts/models, question wording, source extraction,
benchmark splits or historical references as an unrecorded convenience; MiniMax;
reserved challenge inspection; hidden rescoring of Task 13; broad annotation
frameworks; model-wide causal claims about qualifications; unrelated retrieval
work; commit, push or external publication/submission without an explicit request.
Internal artifact sealing and result-pointer publication are required task outputs.

## Outcome

The accepted C rules and explicit candidate prompt have a separate reviewed
340-case synthetic suite. Both Luna and Haiku judged the original six questions'
106 candidates: 105/106 and 104/106 agreement respectively, with all outputs
valid. One Luna acceptance materially changes a scoped approximate flooding
prediction into an exact universal guarantee. Two Haiku disagreements concern
whether a specific future-land-use-input relationship is necessary beyond the
retained inventory/scenario mechanism; that label materiality remains unresolved.

[Task 15C](15c_run_conclusion_development.md) owns all three reviews and the
predeclared initial stop decision. The user subsequently authorized three-round
execution on the remaining thirteen; Task15D preserves that new decision and
combined results separately. No original
labels, prompt, frozen results or selected judge were changed by execution.
The prompt remains unqualified. Task 16 remains provisional.


## Current continuation — structured reference drafts

The user accepted the C001 judge pilot as sufficient for this stage, with the
point-level limitations in Task15K preserved. [Task15L](15l_draft_structured_reference_conclusions.md)
now drafts all49 required/optional conclusions from evidence and existing labels,
with independent review, before one-at-a-time human adjudication. This supersedes
the old prose-review queue as the next review format, not the original labels.
No prediction-driven label tuning, source-support edits or downstream reruns are
part of that batch. The final rules distinguish optional numerical coverage from
contradiction checking and qualification content from contextual restatements.


## Fresh generation and reporting completion

[Task15S](15s_fresh_generation_and_reporting.md) executed approved steps8–9 under
a separate $40 cap. The [result](../../docs/specs/task15s_fresh_generation_result.json)
selects292 valid answers,291 complete evaluations and all294 planned slots, with
separate development/test reports and exhaustive C/G/S failure inventories.
Two interrupted generations and one truncated C judgment remain unavailable;
no paid requests were retried. Model/computed C agree for all291 valid judgments.
Review uncertainty remains distinct from frozen scores; no new tuning cycle or
Task16 writing was activated. Earlier publications are preserved.

[Task15T](15t_retry_unavailable_slots.md) subsequently completed the user's three
explicitly authorized availability retries, with a6144-token C output cap. The
[selected result](../../docs/specs/task15t_retry_result.json) now has294 valid
answers and294 complete evaluations; all selected model/computed C verdicts agree.
Original attempts and their costs remain preserved, with cumulative retained
liability$2.629365365 plus accepted unknown counting fees. No additional tuning
or Task16 work is activated.

## Code quality and closeout

User requested maintainable, editable, simple and readable code, followed by
Task15 closure and a local commit. Three bounded reviews covered structured-C
contracts, native execution controls and projection/scoring integration.

Centralized the six structured prompt/input/output version mappings, eliminating
duplicated routing ladders. Simplified repeated policy checks without changing
authorization limits. Marked the old direct-answer synthetic loader explicitly
historical to avoid accidental reuse for v6. Preserved all historical/current
prompt bytes and input/output schemas; no scoring-rule changes or model calls.
Existing contract tests cover version routing, context parity, output validity
and aggregation. Kept historical policy serialization explicit rather than adding
a new framework. Final project-check results are recorded below.

Final validation: `make fix` and `make check` passed;4559tests passed,1skipped.
Formatting/lint clean; mypy found no issues in671source files. All changed/new
Markdown relative links and Git whitespace checks passed. Focused reviews also
verified byte-identical prompts and input/output schemas across all six structured
versions. Remaining warnings are the existing Inspect retry-library deprecation.
The authorized local commit includes Task15 code, tests, specifications, result
pointers and closeout documentation; large data and generated artifacts remain
outside Git. The three future subtasks remain unactivated.
