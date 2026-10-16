# LLM-as-a-judge: learning notes for future calibration

For completed experiments and their positive and negative results, start with the
[grounding experiment record](grounding_experiment_record.md). These notes retain
the research rationale and proposed adaptations; the record distinguishes what
was actually tested and selected.

Recorded 2026-09-25 after discussing Li et al.,
[From Generation to Judgment: Opportunities and Challenges of LLM-as-a-judge](https://aclanthology.org/2025.emnlp-main.138.pdf)
(EMNLP 2025).

These are design questions and proposed development experiments for Tasks 09
and 12, not a new evaluation contract or authorization to run a judge. The
[Sprint 2 evaluation boundary](sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
continues to own the rubric, staged information access, judge input boundaries and labeling budget.

## Current decision — 2026-10-08

[Decision 006](decisions/006_structured_answers_four_part_evaluation.md) supersedes
conflicting suggestions below: two automatic results and two separate LLM answer
judgments, one structured cited reference answer, and no mandatory labeling after
08F. Human calibration is optional and separately authorized; without it report
uncalibrated automated judgments. Earlier calibration ideas are possible future
experiments, not prerequisites. Grounding includes the question but hides the
reference; adequacy adds the reference and accepts substantively valid alternatives.

## Research review — 2026-10-12

The user requested a research pause after the two unsuccessful claims-only
prompt pilots. This review revisits the survey and primary papers on contextual
faithfulness, decomposition, rubric design and uncertainty. It proposes a next
experiment; it does not authorize inference, change labels or qualify Luna.

### What our experiments establish

The [context pilot](specs/task09e1_luna_context_claims_result.md) improved selected
trouble judgments but regressed on controls. The [scope replacement](specs/task09e1_luna_scope_claims_result.md)
regressed overall. Both failed their frozen expansion gates. The troublesome
requests largely reuse pet-policy and grading relationships; repetitions and
citation aliases are not independent semantic benchmark cases. These negative
results reject those additions, not every possible prompting method.

Keep four questions separate: does Luna repeat its answer; does it agree with
the proposed label; is that label/source interpretation defensible; and does an
improvement generalize beyond the examples used to develop it? Our current
results establish neither calibrated correctness probabilities nor broad
reliability. Existing synthetic expectations remain proposals, not an independent
human calibration set.

### Closest primary evidence

| Research | Finding relevant to this project | Transfer limit |
| --- | --- | --- |
| [ContextualJudgeBench, ACL 2025](https://aclanthology.org/2025.acl-long.470.pdf), §4.3 and Appendix C.3 | Separates contextual faithfulness from completeness. GPT-4o verification of criteria use lowers consistent verdict accuracy by roughly 20 percentage points across the tested subset; structured faithfulness prompting has marginal effects, and self-consistency/juries rarely help in its tests. | Pairwise comparisons differ from our binary claims, and model verification is not human-established explanation correctness. A plausible explanation or correct verdict alone cannot establish correct evidence use. |
| [RefChecker, EMNLP 2024](https://aclanthology.org/2024.emnlp-main.395.pdf), §6.1 and Limitations | Triple-level checking improves macro-F1 by about ten points over response-level checking on average across tested checkers. Authors warn that triples can lose complex and temporal semantics. | Our inputs are already claims. This does not establish a ten-point gain from decomposing them again; bare triples risk discarding mitigation conditions. |
| [VeriScore, Findings EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.552.pdf), §3.3 | Distinguishes evidence supporting individual components from evidence supporting their connection, and warns against atomization that loses necessary context. | Its web-search verification is outside our citation-only evidence boundary. The relationship-preservation lesson is directly relevant to combining worker and residential rules. |
| [ALCE, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398.pdf), §6 and Appendix G.5 | Citation-recall and citation-precision judgments achieve 85.1% and 77.6% accuracy against human judgments; partial support is a documented difficulty. | Those are specific citation-evaluation results, not our claim accuracy. Entailment, citation attribution and literal quotation checks remain distinct. |
| [EvalLM, CHI 2024](https://arxiv.org/html/2309.13633) | Specific criteria produce higher human agreement than general criteria in its study; its workflow supports inspecting examples and refining evaluation criteria. | Agreement with human preference is not proof of factual support. Useful for clarifying what counts as a reasonable summary, not evidence that more rubric text always helps. |
| [Trust or Escalate, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf) | Calibrates confidence thresholds against human labels and accepts only a subset of judgments, trading coverage for agreement. | Guarantees depend on representative calibration data and assumptions. Our selected trouble repeats cannot provide them; a single-model adaptation would need validation. |
| [Principles and Guidelines for the Use of LLM Judges, ICTIR 2025](https://www.cs.unh.edu/~dietz/papers/dietz2025principles.pdf), §2 | Warns about circular evaluation and aggregate agreement hiding item-level disagreements. | IR system rankings are different from claim support, but the need for independent validation and item-level diagnostics transfers. |

Additional checks prevent misleading imports from popular factuality methods:
[FActScore](https://aclanthology.org/2023.emnlp-main.741.pdf)'s headline low error
concerns aggregate factual-precision estimation, not 98% individual-claim
accuracy. [SAFE](https://arxiv.org/html/2403.18802v3)'s search-based verification
changes the evidence universe; its selected disagreement adjudication is not an
overall accuracy estimate. [RAGChecker](https://arxiv.org/html/2408.08067v2)
separates faithfulness from reference-dependent correctness, but its reported
response-preference correlations are not claim accuracies. None licenses showing
our grounding judge ideal answers or proposed labels.

### Recommended next experiment, not an adopted protocol

**Compare direct support judging with a compact, evidence-linked intermediate.**
Keep the original claim, question and full allowed cited passages visible in both
arms. For the candidate, make Luna expose the asserted relationship: who it applies
to, what is required, and any modality, quantifier, condition, exception or timing.
Then identify the source span(s) supporting that relationship as a whole, or
explicitly identify missing support, and return
the existing whole-claim decision. Do not substitute a fraction of supported
fragments for the current scoring rule.

For the pet-policy example, this should distinguish an acceptable scoped summary
from combining an all-development worker rule with a residential-only pet policy.
For grading, it should distinguish a deadline for an action from a guarantee of
ecological recovery. These are illustrations of the intended diagnostic, not
examples to silently embed in a prompt and then count as independent validation.

This richer representation is **our hypothesis**, informed by RefChecker and
VeriScore, not an externally demonstrated fix. The experiment must check that the
intermediate faithfully preserves the original claim; an omitted condition is an
extraction error, not evidence for support. Keeping the representation within one
structured response would limit extra calls, but output cost and correlated
reasoning errors still need measurement. No implementation choice is made here.

Before any run, specify a compact rubric that accepts reasonable paraphrases in
question context while rejecting material strengthening. Preserve disputed source
readings separately from unambiguous errors; do not silently relabel historical
results. Optional human adjudication would improve interpretability but remains
separately authorized under Decision 006.

Evaluate both meaning-preserving changes and changes that should alter support:
consistent citation-ID renaming, scoped paraphrases, wrong population, removed
condition, stronger modality, changed deadline/outcome, and recombination of two
individually supported rules. Citation-ID invariance is our proposed diagnostic,
not a result demonstrated by the papers above. Keep related claims and aliases
together when separating development from validation; do not treat nine repeats
as nine new cases. Use only the authorized development boundary, with reserved
and test content untouched and any expansion separately gated.

Report label agreement, false acceptances/rejections, invalid-output coverage,
per-input stability, irrelevant-change invariance and intermediate fidelity
separately. Audit source ownership and reasons as well as the Boolean result.
Freeze the candidate and selection rule before evaluation; keep a disjoint set
of semantic families for validation where the authorized panel permits it.
Otherwise explicitly retain the limitation that this is a failure-panel pilot.

### What to defer

- **More voting as a correctness fix.** Repeats estimate response variability;
  agreement can preserve the same mistaken scope interpretation. Majority voting
  may be a future uncertainty signal, not a calibrated truth probability.
- **Confidence-based acceptance guarantees.** Trust or Escalate offers a useful
  later protocol, but requires independent calibration. Judge uncertainty must
  also remain distinct from a target answer's abstention. No new uncertainty gate
  or labeling requirement is adopted here.
- **Fine-tuning, multi-model juries and open-web verification.** They add data,
  cost or evidence-boundary changes without demonstrating a remedy for our small
  set of source-scope failures. Luna-only remains the inference constraint.
- **Another long prompt addition.** A balanced, disjoint few-shot rubric could
  still be a future comparator, but these papers do not establish its superiority
  for our task. First test a method that makes the failure location observable.

Research and recommendation review used three bounded independent readers.
No model inference, implementation, label edits or artifact changes accompanied
this review. Adoption belongs in a new bounded Task 09E.1 experiment contract.

## Applying the research to the conclusion stack — 2026-10-12

After the Dev6 comparison, the user accepts the simpler Luna claims configuration
as good enough for continued development and selects it over the structured
explanation candidate. This means the frozen Dev6 **baseline** prompt (combined
scope/absence/grammar clarification), medium reasoning and qualified cache layout.
It is a selected development configuration, not calibrated judge qualification
or an implicit edit to package defaults. Further general claims prompt tuning
is deferred; the current focus is conclusion-stage design.

### Existing behavior matters more than another wording change

The comparison conclusion call receives the original question, complete answer,
allowed evidence and ordered point ID/Boolean predictions. It does not receive
the first judge's explanations or expected labels. It re-reviews every point
against its own citations and independently judges the conclusion, including
premises on which that conclusion depends. Those are two responsibilities in one
call. The prompt already says predictions are fallible and unrelated unsupported
assertions do not automatically invalidate an independently supported conclusion.

Aggregation first blocks on any claim/review disagreement. If reviews agree,
unsupported conclusion yields 0; supported conclusion with any unsupported point
yields 1; supported conclusion with all points supported yields 2. Genuine clean
abstention is separate. Therefore better correction can reduce numeric coverage;
agreement can also preserve the same mistake. Neither direction establishes
conclusion accuracy. The earlier [pipeline comparison](specs/task09e1_luna_cache_pipeline_result.md)
found no net coverage gain after matching complete initial point vectors, despite
apparent gains across full arms whose initial judgments differed.

### Paper-supported principles and proposed adaptations

- [VeriScore](https://aclanthology.org/2024.findings-emnlp.552.pdf) warns that
  supported components do not establish their connection and preserves necessary
  qualifications. Applied here: correct facts about mitigation do not establish
  an asserted guarantee that an impact is eliminated. Conversely, an erroneous
  peripheral detail need not defeat a conclusion independently supported by the
  allowed evidence. Checking that dependency is our adaptation, not a method
  validated by the paper for this stack; its open-web evidence must not be imported.
- [ContextualJudgeBench](https://aclanthology.org/2025.acl-long.470.pdf) separates
  faithfulness from completeness, detects verdicts reached using wrong criteria,
  and finds limited benefits from voting/juries in its setting. Applied here:
  keep adequacy out of grounding, inspect the reason for reversals and test prior
  prediction visibility. Anchoring by the visible Boolean vector is a hypothesis
  about our implementation, not a demonstrated cause or a result from that paper.
- [Trust or Escalate](https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf)
  separates accepted coverage from calibrated agreement. Applied here: report
  conclusion agreement, claim-review agreement, final-score agreement and numeric
  coverage separately. Do not optimize away unresolved cases or treat model
  confidence/votes as calibrated correctness. Human calibration remains optional
  and separately authorized under Decision 006.

### Controlled comparison and what changed

Dependency checking, separating grounding from completeness, and reporting
accuracy separately from coverage were already implemented. The new intervention
was prior-verdict visibility; the user subsequently added a conclusion-only arm
that also deliberately removes the claim-review disagreement gate.

The [completed frozen-claims comparison](specs/task09e1_luna_conclusion_blind_result.md)
finds that visible review improves claim agreement and hiding verdicts damages
correct control judgments. Conclusion-only increases coverage and slightly improves
conclusion agreement, with no net conclusion gain on the original eleven trouble
answers. Source review identifies two ownership boundaries: a conclusion can use
the full answer's cited evidence, while a point review must retain that point's
own citations. Review instructions sometimes over-restrict the former; blind
review sometimes relaxes the latter. These are observed policy-application issues,
not proof of a general anchoring mechanism.

Pet-policy conclusions also expose ambiguous grammatical scope in proposed
labels. Preserve source interpretation alongside label agreement. Do not equate
more numeric scores with better judgments or infer that rejudging is useless:
most visible-arm withheld scores involve proposal-aligned corrections to the
original claims. The experiment does not promote a default or authorize another
run. Claims remain frozen at the selected simpler configuration.

The subsequent [structured conclusion assessment pilot](specs/task09e1_luna_structured_conclusion_result.md)
adds an evidence-linked written assessment to the existing JSON explanation.
It improves repeatability but reduces conclusion agreement and introduces a
point-citation borrowing regression. Structured explanations make interpretation
choices easier to inspect; correct final labels can still accompany flawed
rationales. The candidate is set aside. Further work needs to resolve concrete
evidence-ownership and interpretation boundaries, rather than presume that more
explicit explanations improve accuracy.

## Earlier plan amendment (2026-09-29)

The adopted plan now separates automatic retrieval recall and final-citation
precision/recall/F1 from two answer judgments: grounded correctness and answer
adequacy. It replaces the earlier three judged dimensions. The reference answer
is reviewed once with its reasoning in combined 07E/07F, not as an outline and a
separate polished answer. Both judges use the same frozen scoped question as the
target. The sprint plan owns the exact formulas, reference visibility and gates.

This design follows the practical distinction between deterministic checks and
rubric-based judgments, while retaining human calibration and room for valid
alternative solutions; see [Anthropic's evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
The choice of two dimensions and our support/context policy are project decisions,
not claims that this particular benchmark design has been externally validated.

## What the paper contributes

The survey maps judging attributes, methods, and benchmarks. Useful entry
points are rule augmentation (§4.2.2), evaluating judges (§6), presentation
biases (§7.1), and human–LLM co-judgment (§7.4). It is more useful as a
literature map than as a procedure for deciding whether a particular judge is
trustworthy for our task. The project implications below are our extrapolations,
not findings demonstrated by the paper.

## What a successful judgment establishes

Keep agency-response similarity, support from cited Draft EIR evidence,
responsiveness to the comment, and substantive adequacy of the underlying
analysis distinct. A response can accurately cite the Draft EIR while evading
a criticism of its assumptions. Even perfect rubric agreement establishes only
the capabilities that the rubric measures.

Grounded correctness checks claims and conclusions against cited source text.
Answer adequacy checks responsiveness and essential substance together. Automatic
citation matching measures source selection, not either of those qualities.
Check adequacy judgments and citation precision for penalties against valid
alternative arguments or sources missing from the authored reference. An official response is a curation lead, not proof of truth.

Case selection further limits interpretation: results on comments answerable
from the allowed evidence universe do not establish competence at evaluating
environmental-review adequacy generally.

## Evidence access is part of the evaluation

A judge can assess supplied passages correctly while missing a decisive
qualification or contradiction outside its context. For example, dropping
“if mitigation M is implemented” from an evidence packet can make an
overstated answer appear supported.

Distinguish two proposed development experiments:

- Judge capability with complete, human-reviewed evidence supplied.
- End-to-end evaluation behavior with evidence supplied by the pipeline.

Track context or extraction failures separately from interpretation failures.
“Unsupported by these passages” and “no support found in this search” do not
establish absence of support throughout the corpus. More reasoning cannot
recover evidence the judge never receives.

## Human agreement and disagreement

Agreement with Kyle's locked labels measures agreement with that curator under
the stated rubric; it does not measure agreement among independent reviewers.
When a judge disagrees, distinguish evidence misunderstanding, rubric ambiguity,
reference incompleteness, and defensible differences in interpretation. Ask:
what evidence would persuade us that the judge is right?

Do not conceal ambiguity by repeatedly revising development prompts solely to
match every label. Keep disagreements and reasons visible. Preserve the
existing development/test boundary and report raw counts as well as rates;
a small development set cannot establish broad reliability. The current plan
requires human review of every locked-test prediction even if the judge passes
its provisional gate.

## Proposed controlled challenge set

Use reviewed development answers to create paired variants. Have a human verify
that each variant changes only the intended property and that its expected
judgment follows from the rubric before testing the judge.

| Change | Expected behavior |
| --- | --- |
| Paraphrase while preserving meaning | Both answer scores and citation metrics remain stable when cited IDs are unchanged. |
| Change formatting or add authoritative language without changing substance | Both answer scores remain stable. |
| Remove an essential qualification from the answer | Grounded correctness falls if the conclusion becomes overstated; adequacy may also fall for omission. |
| Replace a citation with a real but irrelevant passage | Grounded correctness falls; automatic final-citation precision may also fall. |
| Omit an essential part of the scoped answer while preserving supported factual claims | Adequacy falls; grounded correctness can remain high if the remaining conclusion stays qualified. |
| Substitute a different valid supporting argument | Grounded correctness stays high; check adequacy and citation-matching penalties for reference incompleteness. |
| Keep every correct citation but reverse the answer's conclusion | Citation scores stay unchanged; grounded correctness falls. |
| Keep citation IDs but substitute an explanation that avoids the question | Citation scores stay unchanged; adequacy falls. |

The question is whether the judge responds to changes in evidence and meaning
while remaining insensitive to presentation. Compare failure types by dimension
before considering a more complex judging architecture. These experiments
supplement, rather than replace, calibration on naturally occurring outputs.

## Revisit when writing Tasks 09 and 12

Use these notes to refine rubric examples and choose a bounded development
challenge set. Decide how to record ambiguous labels and valid alternate
answers, and how to separate judge errors from evidence-packet errors. Any
adopted protocol or gate changes belong in the future task contract and the
sprint evaluation boundary, not implicitly in this note.
