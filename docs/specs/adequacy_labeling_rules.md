# Adequacy labeling rules

Status: approved first-pass policy. This maintained document defines labeling
semantics; it does not certify that a judge implementation satisfies them.

Examples here are invented illustrations in unrelated contexts. They are not
benchmark cases or human-labeled calibration records. Per-question requirements,
calibration examples, and experiment results belong in separate artifacts and
must not be appended to this general policy for inclusion in judge prompts.

## 1. Scope and two checks

Adequacy consists of two independent binary checks:

- **Conclusion (C):** Does the conclusion give the approved answer and answer
  all parts of the question?
- **Support (S):** Do the supporting points provide a sufficient, logically
  valid basis for the candidate's conclusion?

Grounding owns source factuality. Adequacy does not independently verify whether
factual premises are true or supported by source documents.

- Whether a source establishes a factual claim belongs to grounding.
- Whether the stated premises support the conclusion belongs to S.
- Whether the conclusion conveys the answer required by the approved reference
  belongs to C.

A logically coherent argument with a false factual premise can pass S and fail
grounding. This separation is intentional. Reference-answer comparison under C
does not authorize an independent source-factuality investigation.

## 2. Answer structure

A substantive answer contains a conclusion, supporting points, qualifications
when needed, and citations attached to the relevant claims. Every substantive
answer requires at least one real supporting basis; an unsupported yes/no is
insufficient.

There are three answer formats.

### Direct answer or finding

The prose conclusion states the answer, outcome, or finding, preserving its
essential scope and conditions. Supporting points establish why it follows,
using an appropriate result, comparison, decisive fact, or explanatory
relationship.

### Explanation

The prose conclusion states the overall reason, mechanism, or calculation.
Supporting points explain the relationships needed to establish it. These may
describe why a finding follows, how a requirement is implemented or enforced,
how inputs enter a calculation, or how an action advances an objective.

Several supporting points do not, by themselves, make an explanation a
complete-list answer. The explanation may use separate supporting paragraphs.

### Complete list

The conclusion contains the complete required list as bullets. Supporting
points follow separately.

The conclusion must contain every approved substantive item and no additional
substantive items. Equivalent wording is allowed. Implementation details and
explanations may appear within an item without becoming additional items.

Match substantive items, not literal words or bullet counts. Splitting,
combining, or repeating wording does not create a missing substantive item or
remove an extra one.

Supporting points may explain one list item each or several related items
together. Do not require equal numbers of conclusion bullets and supporting
points, positional correspondence, or one citation per item. Assess their
joint explanatory coverage.

## 3. Conclusion check (C)

Pass C only when the conclusion conveys the approved substantive answer and
answers all parts of the question.

### Reference authority

The provided approved answer determines the required answer in every case.

- Accept paraphrases and equivalent wording.
- Do not accept a substantively different answer merely because it could be
  independently valid.
- Permit alternative supporting reasoning, not alternative substantive answers.
- Do not research other possible answers or adjudicate new source interpretations.

### Completeness

The conclusion must cover every requested part of the question. Supporting text
does not repair a missing, incorrect, incomplete, or non-answer conclusion.

For example, if a question asks how a recipe change affects both sweetness and
texture, a conclusion addressing only sweetness is incomplete even when the
support discusses texture.

The conclusion need not reproduce the entire supporting explanation or every
reference detail.

### Complete-list boundaries

C fails if the conclusion omits a required substantive item, adds an extra
substantive item, or changes an item's essential meaning, scope, trigger, or
condition.

For example, suppose the approved answer to a question about library borrowing
options is physical books, e-books, and audiobooks. Omitting audiobooks or adding
room reservations changes the required list. Mentioning adjustable text size
within the e-book item is an explanatory detail, not a fourth borrowing option.

### Scope and conditions

Preserve material distinctions in the approved answer, including relevant
scenarios, timing, conditions, and uncertainty. Do not turn a conditional or
modeled finding into an unconditional guarantee.

For example, “The backup can restore files if a usable snapshot exists” is not
equivalent to “The backup always restores files.”

This is reference-answer comparison. Do not search source evidence for additional
conditions and silently add them to the grading requirements.

## 4. Support check (S)

Pass S when the answer contains at least one substantive supporting basis and
its supporting points jointly provide sufficient, logically valid reasoning
for the candidate's conclusion.

### Independence from C

Evaluate the candidate's actual conclusion. A conclusion can fail C by omitting
a required item or adding an extra item while its support adequately explains
the claims it actually makes. Conversely, a complete conclusion can pass C
while the support fails to establish one of its claims.

Support does not rescue a failed conclusion. A failed conclusion does not
automatically fail support.

### A basis must add explanatory substance

A supporting point must add a fact, comparison, mechanism, calculation, or other
reason that helps establish the conclusion. Some overlap is acceptable when it
adds that basis.

For the conclusion “The file cannot be restored from this snapshot”:

- “The file was created after the snapshot was taken” supplies a basis.
- “This snapshot cannot restore the file” merely repeats the conclusion.
- “The backup application has a blue icon” supplies neutral background.

One cited section can provide sufficient support. Citation count does not
measure explanatory sufficiency.

### Joint sufficiency

Each point need not prove the entire conclusion independently. Several points
may establish different parts of the argument. However:

- Individually relevant points may still leave a material gap.
- One example does not automatically establish a broader claim.
- Repetition does not supply missing support.
- Many good points do not cancel a material contradiction or invalid inference.

The necessary basis depends on the question. For a calculation, merely naming
inputs is not necessarily enough: “Multiply batches by servings per batch”
explains a relationship; “Use batch and serving data” only names inputs.

### Alternative supporting explanations

Accept an explanation different from the reference when it logically and
sufficiently supports the candidate's conclusion. For an answer to receive full
credit, that conclusion must also pass C.

Do not require the reference's exact wording, point order, grouping, citation
count, every illustrative detail, or every numerical assumption. This
flexibility does not permit substitution of a different substantive answer
under C.

### Neutral content

Neutral content neither establishes nor undermines the conclusion. It does not
count toward the required basis, but its presence does not itself cause failure.
An answer containing only neutral support fails S. Relevance depends on the
question; the same fact may be decisive in a different context.

### Invalid reasoning and contradictions

S fails for a material contradiction of the conclusion, a contradiction within
the reasoning needed to establish it, an unsupported inferential leap, circular
reasoning, or a material gap in support for a claimed part of the conclusion.

“Unsupported inference” means the conclusion does not follow from the stated
premises. It does not mean a factual premise lacks source support; grounding
handles that.

For example, “This snapshot can restore the file because the file is absent
from it” does not establish the claimed restore capability. This is a reasoning
problem without checking whether the file is actually absent.

Different scenarios, times, or conditions are not automatically contradictory.
Interpret qualifications together with the claims they constrain.

## 5. Combined score

| C | S | Score |
| --- | --- | ---: |
| No | No | 0 |
| No | Yes | 0 |
| Yes | No | 1 |
| Yes | Yes | 2 |

Retain both component judgments alongside the derived score.

There is no contradiction-specific override. A correct conclusion with
contradictory support and a correct conclusion with insufficient support both
receive 1. Their diagnostic explanations should distinguish the failure types;
the aggregate score deliberately does not.

## 6. Abstention and invalid output

### Explicit abstention

Detect explicit abstention before semantic judging and skip both adequacy
checks. Record abstention status, C and S as not evaluated, and no invented
semantic score.

For example, “I do not have enough evidence to determine the return deadline”
offers no substantive answer and is an abstention.

Metric-denominator treatment is deferred. Preserve response statuses, component
judgments, and counts so reporting can include or exclude abstentions later.

Reliable abstention detection is a routing prerequisite, not a semantic
judge-comparison dimension. Perfect detection is an expectation to verify, not
an observed result asserted by this policy.

### Substantive negative answers

“The policy specifies no return deadline” is a substantive answer, not an
abstention. Judge it normally against the approved answer.

Failure to retrieve a relevant passage does not establish document-wide absence.
Target-answer instructions should encourage explicit abstention when evidence
is insufficient, rather than treating retrieval failure as proof of absence.

### Invalid output

Malformed output, missing required fields, and invalid judge output must remain
distinguishable from explicit abstention and validly structured answers receiving
C=no or S=no. A mechanical failure must not silently become a semantic label.
Exact status fields and mechanical handling are implementation work, not additional
semantic rules defined here.

## 7. Citations and context

Citation evaluation and grounding remain separate from adequacy.

- Supporting citations support claims used in the answer.
- Context-only citations remain citation metadata.
- A context-only citation cannot justify a conclusion, supporting point, or
  qualification.
- Do not add an answer section called “Additional context.”
- Context-only citations are not citation false positives merely because they
  are not answer support.

Neutral prose and a context-only citation are different concepts. A citation's
metadata role does not determine whether a sentence contributes to the argument.
