# Adequacy labeling rules

Status: structured-reference C policy user-approved in Task15 (2026-10-22);
S conclusion-target/supporting-material boundary user-approved in Task15AD (2026-10-23).
This maintained document defines labeling semantics; it does not
certify that a judge implementation satisfies them. Frozen historical prompts,
labels and results retain their original policy and are not relabeled by this
revision.

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

These describe candidate answer formats. The reference conclusion is a judging
guide with numbered required and optional points (section 3); it need not look
like the candidate conclusion. Reference supporting points remain separate as
the evidence-labeling record.

There are three candidate answer formats.

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

The conclusion must contain every requested substantive item and dimension.
Equivalent wording is allowed. Implementation details and explanations may
appear within an item. Compatible additional information is not a failure merely
because it is absent from the reference; apply section 3 for material changes,
contradictions and explicit category, count or exclusive boundaries.

Match substantive items, not literal words or bullet counts. Splitting or
combining wording does not change coverage; repetition cannot supply a missing
item. Do not infer exclusivity from bullet formatting or reference brevity.

Supporting points may explain one list item each or several related items
together. Do not require equal numbers of conclusion bullets and supporting
points, positional correspondence, or one citation per item. Assess their
joint explanatory coverage.

## 3. Conclusion check (C)

Pass C when every required reference point is satisfied and no required or
optional reference point is substantively contradicted, and no internal
contradiction is detected. Task15P implements the current paragraph-input and
internal-contradiction contract as explicit v6. Production promotion remains pending.
Historical runs retain their old contract.

### 1. Use the supplied conclusion inputs only

Evaluate the question, candidate conclusion, and numbered reference points.
The candidate conclusion is its original prose, without added statement IDs or
a segmented duplicate. Only the reference points have identifiers.
Required points use R1, R2, ...; optional points use O1, O2, ... . Supporting points
and source documents are outside C's inputs. Candidate support cannot repair
missing conclusion content. S assesses supporting reasoning; G assesses source
support within its supplied inputs. C must not infer their judgments.

The reference has two lists. Either list may contain answer facts, details,
explanations or qualifications. Each bullet is a logically complete, self-contained
point. Keep related facts together when needed for an explanation; restate enough
scope within qualifications to make them understandable. Do not introduce point
dependency links. Optional quantitative details should supply modeled values and
relevant comparisons, not just thresholds. Preserve source citation IDs separately
from R/O judgment IDs; use S identifiers inline and source links below review text.

### 2. Require every required meaning

The required list defines completeness. Do not invent requirements or promote
optional content into requirements. Label authors decide which facts, explanations,
list items and conditions are necessary to answer the question. A defective
reference requires label review, not silent repair by the judge.

### 3. Accept equivalent expression

Match meaning, not wording, ordering, formatting or sentence count. One sentence
may satisfy several points; several statements may jointly satisfy one point.
Preserve relationships, negation, scope, quantities, conditions and uncertainty
when they affect meaning. Do not supply unstated premises or reinterpret an
explicitly changed claim as what the candidate probably intended.

### 4. Require the specified why/how explanation

The candidate must convey the required reason, finding, mechanism or calculation
and its connection to the outcome. Naming topics or repeating the outcome is
insufficient. Do not require deeper explanations found only in optional points.

### 5. Allow optional points to be omitted

Any or all optional points may be omitted. Their absence never causes an omission
failure. Including optional content does not compensate for missing or
contradicting required content.

### 6. Do not allow contradictions of optional points

A candidate discussing an optional point must not contradict it. It need not
reproduce the whole point. Missing detail, different emphasis or a shorter
explanation is not itself a contradiction. Check the actual claims and retain
conditions needed to interpret them correctly.

For numerical details, Addressed requires relevant numerical values with enough
scope to identify what they describe. A generic below-threshold statement does
not address modeled numerical values. Meaningful partial numerical coverage is
allowed; every listed value need not be repeated. Equivalent units are acceptable.
For a qualification, Addressed requires conveying the qualification or limitation
itself. Restating the underlying claim or contextual comparison alone is Not
addressed. Shared context does not automatically address multiple reference points.
First check for contradictions, regardless of whether the candidate supplies
numbers or otherwise addresses the point. The numerical-coverage requirement
applies only when choosing between Not addressed and Addressed without
contradiction; it must never prevent Contradicted. Only after finding no
contradiction should the judge decide whether the point is addressed.

### 7. Check reference conflicts and explicit internal conflicts separately

Check additional content against required and optional reference points and flag
conflicts on the affected R/O points. Also return `internal_contradictions`, a list
of objects containing a brief `reason` identifying incompatible claims in the
candidate and explaining why they cannot both hold in the same circumstances.
Use an empty list when none are detected. Scan the entire conclusion, including
claims after an otherwise correct answer. No candidate IDs or pair matching.

An internal contradiction may overlap a reference-point contradiction; report
both where applicable. It may also occur outside both reference lists. Do not
force it onto an unrelated R/O point. A claim that contradicts only a reference
still fails that reference point but is not an internal contradiction by itself.
Do not reject an addition merely because neither reference list mentions it.
Absence establishes neither truth nor falsehood; compatible additions receive
no separate factual-support or relevance judgment.

### 8. Identify the actual incompatibility

A contradiction requires meanings that cannot both hold under the same relevant
circumstances. Different times, scenarios, populations or concurrent requirements
are not inherently contradictory. Distinguish missing required meaning from an
explicitly incompatible claim. Do not infer exclusivity from bullet formatting
or brevity; explicit category, count or exclusive boundaries must be preserved.
If the candidate both conveys and contradicts a reference point, mark that point
Contradicted. Correct wording elsewhere does not cancel the conflict.

### 9. Return point-level judgments and an overall judgment

Return exactly one judgment per numbered reference point, including every optional
point even when Not addressed. Also return `internal_contradictions` as
`[{"reason": "..."}]` (or `[]` when none are detected):

| Reference point | Statuses |
| --- | --- |
| Required (R1, R2, ...) | Satisfied; Missing; Contradicted |
| Optional (O1, O2, ...) | Not addressed; Addressed without contradiction; Contradicted |

Each judgment contains the reference point ID, status, relevant candidate
excerpt(s) if present, and a brief reason. Preserve relevant relationships,
negation and conditions in excerpts. An absent phrase alone is not a failure. Missing and Not addressed judgments may
quote incomplete or related candidate content to explain the gap; otherwise use
no excerpts. Other statuses require relevant excerpts. Before returning, check
that each status agrees with its explanation, then derive the overall judgment.
Addressed without contradiction does not certify factual support for added claims.

Overall pass requires every required point to be Satisfied, no required or
optional point to be Contradicted, and an empty `internal_contradictions` list.
Do not average judgments, count matched words, or award extra credit for length
or optional content. Correct statements never cancel incompatible statements.

Retain the model's overall Boolean and compute the rule above independently from
its complete per-point predictions and the contradiction list. Report both against
the same expected labels and report their agreement. A nonempty contradiction
list with an overall pass is a logical consistency failure. Keep this separate
from structural invalidity so both verdicts remain available for analysis; never
silently repair the model's prediction or reroll it. An empty list alone does not
require a pass. Missing, duplicate or unknown reference IDs make the aggregate
unavailable; never infer missing optional rows as Not addressed.

Internal-contradiction explanations support the model's judgment and overall
reason; they are not separately scored, string-matched, or semantically reviewed.
There is no exhaustive expected list, expected pair inventory, or explanation
accuracy metric. Validate the list/object/nonempty-reason structure and consistency
with the overall prediction. Raw Booleans from structurally incomplete outputs may
be reported separately, not as valid results. Historical versions retain their
original validation contracts and scores.

### 10. Preserve the coverage boundary

A C pass does not certify factual support or relevance of content outside the
reference's coverage. Such additions can be supported or unsupported without
contradicting any listed point. Conclusion-only claims may fall outside G's inputs
and may not be caught by S. A complete, supported answer with unrelated extras may
pass; C is not a relevance or concision judge. Retain these factual-coverage and
relevance limitations in Task16 discussion. No model-training claim follows from
this evaluation contract.

## 4. Support check (S)

Pass S when the answer contains at least one substantive supporting basis and
its supporting points and qualifications jointly provide sufficient, logically
valid reasoning for the candidate's original conclusion.

### S input boundary

S receives the question as context, the candidate's original conclusion,
supporting points with IDs, and qualification text. The conclusion is the sole
judgment target. Supporting points and qualifications are supporting material:
assess their facts, conditions and relationships jointly as a basis for that
conclusion. The question clarifies meaning; it does not impose completeness
requirements on S.

Do not append qualifications to the conclusion or grade them as additional
conclusion claims. A qualification may supply a necessary premise or condition;
it need not independently prove the entire conclusion. An unrelated or separately
unsupported qualification does not itself fail S. It matters when it reveals a
material gap, invalid inference or contradiction that undermines the conclusion's
supporting basis. Source factuality remains G's responsibility.

Qualifications cannot silently rewrite or repair the conclusion's scope. If the
supporting material justifies only a conditional outcome while the conclusion
asserts an unconditional result, S fails for that unsupported conclusion claim.
If an essential condition is already expressed in the conclusion, evaluate its
basis normally. An empty supporting-points array may pass when qualifications
provide a substantive basis; material with no substantive basis fails S.

Optional context remains excluded. Real projection preserves the original
conclusion and the separate supporting fields without merging text. Generation's
schema and G's treatment of factual qualifications remain unchanged.

For synthetic scope tests, write the intended scope change directly into the
single coherent conclusion paragraph and preserve supporting points. Do not hide
the tested claim in a separate field. Historical qualification-field tests retain
their old contracts and results; they are not qualification evidence for this input
boundary without new evaluation.

### Conclusion claims and supporting facts

Assess every substantive claim actually asserted in the conclusion, including
quantities, timing, conditions and what an analysis includes or excludes.
Substantive claims add factual content about outcome, magnitude, timing, scope
or conditions. Support for the main claim does not excuse an unsupported
additional claim. Pure transitions and redundant wording need no separate basis.

An assertion appearing only in the conclusion does not establish its own basis.
Evaluate the facts and relationships supplied in the supporting material, including
internal consistency and calculations. A basis may be explicit or follow through
a straightforward inference; one supporting item may support multiple claims and
multiple items may jointly support one claim. Do not require obvious inferential steps
to be spelled out. Source verification remains G's responsibility; S does not
consult source documents or outside knowledge.

Reference optionality does not excuse unsupported claims that the candidate
chooses to include. Omitted reference content creates no S failure. Reference
points and their required/optional labels are not supplied to S.

### Independence from C

Evaluate the candidate's actual conclusion. A conclusion can fail C by omitting
a required item or adding an incompatible claim while its support adequately
explains the claims it actually makes. Conversely, a complete conclusion can pass C
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
Interpret conditions and scope within the conclusion with the claims they constrain.

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
