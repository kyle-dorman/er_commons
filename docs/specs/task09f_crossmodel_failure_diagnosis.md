# Task 09F — Offline cross-model failure diagnosis

The main shared problem is translating a recognized defect into a whole-answer
score. False omissions and factual reading mistakes also occur, but more elaborate
requirements/coverage output has not resolved the score boundaries. Some synthetic
expectations need policy adjudication before treating them as judge mistakes.
No prompt, model setting, expected label or selected default changes in this review.

## Scope and evidence

The fair comparison is the aligned-v3 Dev6 experiment: 136 identical answers,
three models and two passes each (816 judgments). Three bounded reviewers examined
all 48 answers with any disagreement, plus 21 successful counterexamples, using
complete candidates, questions, references, supplied sources, expected-label
rationales and all six judgments. Exact evidence and all per-answer reviews live
under the external artifact root identified by the [result pointer](task09f_crossmodel_failure_diagnosis.json).
Later Haiku-only runs are separate historical evidence, not matched tests of the
current consolidated contract across all three models.

| Model | Agreement with proposed labels, pooled | Answers changing score/validity between passes | Answers receiving the same wrong score in both passes | Invalid outputs |
| --- | --- | --- | --- | --- |
| GLM | 222/272 (81.62%) | 7/136 | 21/136 | 0 |
| Luna | 231/272 (84.93%) | 13/136 | 14/136 | 0 |
| Haiku | 216/272 (79.41%) | 11/136 | 22/136 | 1 |

Of 147 disagreements, 72 are expected 0 / predicted 1; 47 are 1 / 2;
three are 0 / 2; 24 are under-credit; one is invalid. Thus 122/147 (83.0%)
award more credit than the proposed label. These are disagreement directions,
not 122 independently established model errors. Eight answers disagree in all
six judgments, and six of those receive the same wrong score throughout.
Eighty-eight answers agree in all six judgments. Two repetitions and six related
questions do not support broad model rankings or causal claims about randomness.

## What the failures actually look like

Scores below show first/second pass; expected scores remain proposals.

| Answer | Expected | GLM | Luna | Haiku | Observed distinction |
| --- | --- | --- | --- | --- | --- |
| C014 F10, transportation inclusion contradiction | 0 | 1/1 | 1/1 | 1/1 | All six notice that a point denies the inclusion asserted elsewhere, yet retain partial credit. |
| C056 F10, flooding elimination contradiction | 0 | 1/1 | 1/1 | 1/1 | All six notice opposing answers to the central question, yet retain partial credit. |
| C001 F08, wrong reason for health-risk finding | 0 | 1/1 | 0/0 | 1/1 | GLM/Haiku preserve credit for the reported finding even though the question asks why. |
| C056 O04, sufficient supporting facts | 2 | 0/0 | 2/2 | 1/0 | GLM/Haiku require an explicit conclusion despite acknowledging residual flooding. |
| C019 F05, modeled outcome becomes guaranteed | 0 | 2/2 | 1/1 | 1/1 | Severity of an acknowledged certainty error needs policy adjudication. |
| C041 C04, invented $500 fine | 1 | 1/2 | 2/2 | 2/2 | All six detect the unsupported amount; five treat it as incidental. |

**Central-answer versus conclusion-field confusion.** C056 F10 says the drainage
improvements would not eliminate flooding, then says they would “completely
eliminate” it during the same storm. The judges identify this contradiction.
Their partial credit cannot be explained by missing the false statement. The
same pattern appears in C014 F10 and, less uniformly, C019/C037 F10.

C001 F08 answers why cumulative health risks are less than significant by saying
the project contribution is smaller than background pollution, “regardless of
the combined total.” The actual reason is that combined totals remain below
thresholds. GLM and Haiku explicitly reject the reason but retain credit for the
correct headline finding; Luna gives 0. For a why-question, that headline was
already given: the explanation is the central answer.

The refreshed rule permits 1 for a correct central conclusion with a materially
incorrect essential explanation or secondary component, while 0 applies to a
materially wrong central answer. These can overlap unless “central” is defined
by what the question asks, across the complete answer. The outputs are consistent
with this ambiguity; they do not prove one sentence caused the failures.

**Correct content rejected because of its location or implicit conclusion.**
C056 O04's conclusion field is generic, but its supporting point says the
improvements leave approximately “1.2 feet for 109 minutes” of 100-year-storm
flooding. That answers whether flooding is eliminated. GLM acknowledges that the
facts imply no, then gives 0 twice for lacking a direct conclusion. Haiku gives
1 then 0; Luna gives 2 twice. This is observable field/formality weighting,
not evidence that the content was unavailable. O04's authoring rule explicitly
makes adequacy depend on whether the remaining answer still resolves the question.

**Actual reading errors and false omissions.** Haiku says C014 F05 lacks
proration/reallocation that is present in its supporting points, and C019 R03
lacks barriers/pumping explicitly present in P2. Some false reasons occur even
when the numerical score matches. GLM misses the change from possible to certain
in C037 F05 and the residential-component restriction in C041 F07. Luna sometimes
rejects valid alternative reasoning (C037 P09, C056 P09). These are distinct from
a judge correctly detecting a defect and disagreeing about its severity.

**Essentiality and proposed-label disputes.** C041 C04 invents a fixed $500 fine
while retaining the correct enforcement instruments, authorities and monitoring.
Is the fine amount material to a question about enforcement, or incidental to a
sufficient account? All models notice it; their centrality decisions differ.
C019 F05 upgrades a modeled lower-groundwater outcome to a guarantee while
retaining the modeled scenario and drainage mechanism. The proposed 0 and the
judges' 1/2 reflect different severity boundaries. Neither majority vote nor the
synthetic author's label settles that policy.

The authoring prompt originally described 1 in terms of missing essential
substance; the refreshed judge also permits materially incorrect essential
substance. Existing zero labels involving defective explanations therefore
warrant selective review. This is not evidence that all such labels are wrong.
The external reviews identify candidates and rationales without relabeling them.
Concise enforcement answers also suffer occasional penalties for omitting pet-rule
details, while closely matched successful answers show those details are not
consistently required. This is another 1/2 boundary problem.

**Output validity is a separate, smaller issue here.** There is one strict invalid
output among 816: Haiku C014 F05 repeat 2 has an empty issue explanation. In
addition, reviewers found schema-valid literal `placeholder` issue explanations
in Haiku C019 F08 repeat 2, C041 F07 repeat 2 and C056 F10 repeat 1. A full-corpus
check found 12 such schema-valid outputs in total; the other nine have matching
scores. A nonblank schema does not ensure a meaningful diagnostic. These findings concern the
matched aligned-v3 runs; the later formatting failure did not reproduce and all
outputs in the later full-Dev6 requirements and small coverage experiments were
strictly valid.

## What the surrounding checks explain—and what they do not

All 816 native responses finished normally: GLM `stop`, Luna `completed`,
Haiku `end_turn`. Maximum reported output use was 1,742 tokens, below the 4,096
cap. Supplied payloads and prior request audits provide no evidence of missing
candidate content or response truncation. They cannot establish internal attention
or reasoning. Provider settings also differ: GLM used temperature 0, top-p 1,
seed 0; Luna/Haiku omitted unsupported sampling controls. “Medium” reasoning
settings do not imply equal compute. Repeat variation remains real, but eight
answers disagreeing in all six judgments cannot be explained away as rare flips.

The later Haiku consolidated runs had more full-credit-answer penalties than
aligned-v3; the full-Dev6 inventory runs had the same pooled agreement as their
consolidated baseline (214/272 each) and worse repeatability. The small coverage
test sometimes found missing content but still withheld credit for an implicit
conclusion; it also produced mistaken omissions and quote/point associations.
These historical runs are not a randomized causal test of consolidation. They
show that requiring a requirements list or evidence map is insufficient to fix
score aggregation and can introduce new errors. They do not establish that the
same interventions would affect GLM or Luna identically.

## Recommended next decision, before another model run

First adjudicate a small set of existing anchors, without looking at which model
wins: a direct central contradiction (C056 F10), a false answer to why (C001 F08),
a complete answer outside the conclusion field (C056 O04), a certainty error
(C019 F05), and an invented enforcement amount (C041 C04). Specify what preserves
partial credit, what invalidates the central answer and what is incidental.
Retain disputed labels as unresolved until that policy is explicit.

Then, if approved, test a minimal clarification of whole-answer scoring and
question-dependent centrality against the retained baseline on a fixed diagnostic
slice with successful concise/alternative answers and abstentions. Keep extraction
structure and model settings fixed to isolate the change. Measure target fixes,
new control failures, strict validity and repeat consistency separately. Do not
promote from aggregate improvement alone or fit labels to model consensus.

A separate candidate-blind requirements call is still a later option: it can test
whether seeing the candidate changes the required components. It will not by
itself resolve whether a recognized central contradiction deserves 0 or 1.
No such call or experiment was executed here.

This review used zero model calls and USD 0. Previous artifacts and reserved/test
boundaries remain preserved. No implementation changes, commit or push.
