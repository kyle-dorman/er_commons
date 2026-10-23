# Task 09F — Adequacy perturbation additions and conclusion selection

Status: historical Task 09F conclusion-generation catalog. The tables and
expectations below preserve the original policy and authoring scope; they are
not a current authorization to generate examples or labels. The
[generation handoff](task09f_conclusion_synthesis_handoff.md) preserves that
historical input contract. This catalog extends the
[original 31-category catalog](task09a_perturbations.json) without changing its
historical bytes or score expectations. It is generator/planning material, not
judge-prompt content.

## Task 15 supersession — current C policy

The user-approved Task 15 revision of the maintained
[adequacy rules, section 3](adequacy_labeling_rules.md#3-conclusion-check-c)
supersedes conflicting C expectations below for future work. Historical labels,
examples and results remain unchanged. No replacement synthetic suite is
published or authorized by this note.

- **A02 is no longer an automatic failure.** An extra substantive item, even one
  absent from the reference, fails C only when it changes or contradicts required
  meaning or violates an explicit category, count or exclusive boundary established
  by the inputs. Compatible additions are not failures solely for being extra.
  Review actual meaning; do not mechanically flip historical A02 labels.
- **A03 is not the sole permitted addition.** Compatible additional answer facts
  can also be acceptable. Reference absence does not establish falsehood or certify
  source support; S/G responsibilities remain unchanged.
- **A01/O02/F07 remain material-omission checks.** Identify the requested meaning
  lost rather than requiring every reference detail. A concrete mechanism may
  convey an abstract purpose without repeating its wording.
- **F08 includes explanatory insufficiency.** A why/how conclusion must express
  the substantive reason, finding, mechanism or calculation and its connection to
  the outcome. Merely reporting that analysis or information warrants the outcome
  is insufficient. Supporting points cannot supply missing conclusion meaning.
- **F10 requires actual incompatibility.** Additional concurrent requirements or
  claims about different scenarios or times are not inherently contradictory.
  Classify missing required content as an omission unless an incompatible meaning
  is also asserted.
- **A09 still concerns replacement of required meaning.** It does not prohibit
  compatible additions or equivalent meaning conveyed through different wording.

Future authoring requires its own activated scope and reviewed expectations under
that policy. The old selected table and boundaries below describe Task 09F only;
reserved challenges remain unopened.

## Historical Task 09F catalog

## Added adequacy distinctions

| ID | Transformation or contrast | Primary purpose |
| --- | --- | --- |
| A01 | Omit a required substantive list item. | Conclusion completeness; list-specific O02. |
| A02 | Add an extra substantive list item, even if plausible or factually true. | Conclusion list boundary. |
| A03 | Add explanatory or implementation detail within an existing list item, without changing its meaning. | Passing conclusion control; distinguish detail from A02. |
| A04 | Replace a real supporting basis with a restatement of the conclusion. | Support failure. |
| A05 | Replace supporting reasoning with neutral background only. | Support failure. |
| A06 | Keep a complete conclusion but remove support for one of its claims. | Support coverage failure; targeted O01. |
| A07 | Replace sufficient support with an example or input/method names that do not establish the claimed result. | Support sufficiency failure; applicability depends on question. |
| A08 | Add neutral background alongside sufficient reasoning. | Passing support control; neutrality alone is not a penalty. |
| A09 | Substitute a substantively different, independently plausible answer for the approved answer. | Conclusion reference authority; not an equivalent paraphrase. |
| A10 | Replace a required list item with a duplicate or paraphrase of another item, preserving apparent bullet count. | Conclusion semantic coverage; list-specific A01. |

These are diagnostic distinctions, not a claim of ten independent failure families.
Retain overlapping historical IDs as lineage rather than generate redundant copies.
P03/P04 already cover combined/split support; explicitly test matched one-to-one
and grouped support. F10 already covers contradiction. New paired designs combine
O02/O04 with sufficient support (support must not rescue C), and A06/F10 with an
unchanged passing conclusion (support failure must not automatically fail C).

## Filter: adequacy conclusion judgment

C asks whether the conclusion conveys the approved substantive answer and covers
all question parts. Expected outcomes below assume the intended edit is achieved;
actual records still require review. Hold other fields fixed when possible and
record unavoidable secondary effects. Do not import historical aggregate scores.

### Passing controls

| IDs | Conclusion-focused variant | Expected C |
| --- | --- | --- |
| Unchanged reference | Retain the approved conclusion as a baseline. | Yes |
| P01 | Paraphrase the conclusion without changing meaning, scope or conditions. | Yes |
| P02 adaptation | Reorder required conclusion-list items, preserving all items. Original P02 reordered supporting points. | Yes |
| P03/P04 adaptation | Split or combine conclusion-list bullets while preserving every substantive item and adding none; assess semantic coverage rather than bullet count. | Yes |
| P05 | Shorten the conclusion while preserving the required answer and every requested part. | Yes |
| P06 | Change tone/formality without changing asserted certainty or substance. | Yes |
| A03 | Add explanatory detail within a required item, with no additional substantive item or changed scope. | Yes |

### Conclusion failures

| IDs | Conclusion-focused variant | Expected C |
| --- | --- | --- |
| O02 | Omit one requested part of a multipart answer. | No |
| O03 | Answer a neighboring question or provide background instead of the requested answer. | No |
| O04 | Use a non-answer conclusion that fails to resolve the question; exclude explicit insufficient-evidence abstentions. The historical support-retention edit is not part of this batch. | No |
| F03 | Reverse the required conclusion. | No |
| F04 | Change a material number, unit, direction or comparison in the conclusion so it disagrees with the required answer. | No |
| F05 / F09 | Replace required uncertainty or a conditional finding with an unwarranted definite answer. | No |
| F06 | Answer for the wrong scenario, entity, location, population or time period. | No |
| F07 | Omit an essential condition, exception, trigger or deadline from the conclusion. | No |
| F08 adaptation | For a why/how question, replace the required explanatory relationship in the conclusion with a different one. A support-only inference defect is not this C test. | No |
| F10, conclusion-only | Put mutually incompatible answers in the conclusion under the same conditions. Contradictory support alone does not fail C. | No |
| A01 | Omit a required list item. | No |
| A02 | Add an extra substantive list item. | No |
| A09 | Give a different plausible answer instead of the reference-equivalent answer. | No |
| A10 | Duplicate one item in place of another, without restoring complete semantic coverage. | No |

F04–F09 require a difference material to the approved answer; do not discover new
requirements by fact-checking sources. Do not require every reference number or
detail in a concise conclusion. A why/how conclusion can fail because the reason
it states is the wrong answer, separately from whether its supporting argument is
internally valid. F10 requires same-scope incompatibility, not different scenarios.

### Selected input boundary

The conclusion judge receives only question, candidate conclusion and approved
reference conclusion. No supporting points, citations, source passages, reference
explanation, expected labels or generation metadata are visible. This is the
user-selected initial system, not an unresolved interface choice.

Support-only changes produce identical requests and are excluded from this batch.
Verify exclusion mechanically instead of generating redundant independence variants.
R03 prompt injection remains a separate robustness check, outside this batch.

## Outside the core conclusion dataset

Source/citation-only defects (C01–C05), source substitutions (P08), and unsupported
premises/additions confined to supporting points (F01/F02) belong primarily to
grounding. Their factual unsupportedness alone is not a C failure. If an edit also
changes the substantive conclusion, classify that conclusion effect explicitly.

Restatement, neutral-only support, incomplete supporting coverage, insufficient
examples and grouped supporting explanations primarily belong to the S dataset.
They do not enter this conclusion-only batch. P07's historical
optional-context removal is not a new answer section; current context citations
are metadata only and their absence does not change C.

R01 clean abstention skips C. R02 mixed abstention/substantive text is a routing
check followed by normal assessment, not an automatic C=no. Neither is a fixed
semantic-negative category. Malformed fields remain mechanical fixtures.

## Boundaries

Author directly as the coding agent across the 19 development questions: one
example per applicable filtered table row, plus one unchanged reference per question.
Combined P03/P04 and F05/F09 rows each constitute one slot. Do not use provider
APIs or run judges. Do not force list-specific mutations onto non-list questions.
The handoff specifies coverage and review. Preserve historical artifacts and
reserved/test payloads; labels require checking the actual edited conclusion.
