# Task 09F — Proposed binary adequacy contract

Status: **proposed for user review; not implemented or authorized for execution**.
The [approved rules](adequacy_labeling_rules.md) own semantics. This document
proposes interfaces and mechanical handling, without changing those rules.
The historical whole-answer judge remains unchanged.
[Exact proposed prompt text](task09f_binary_judge_prompts.md) includes the approved
benchmark-role openings for both components.

## 1. Separate decisions

C asks whether the candidate conclusion conveys the approved answer and covers
all requested parts. S asks whether the candidate's own supporting reasoning
sufficiently establishes its actual conclusion. Run and retain these independently;
neither consumes the other's prediction. Grounding owns source factuality.

C requires both completeness and substantive agreement with the reference.
Answering every part is insufficient if the conclusion changes a material claim,
condition or degree of certainty. This is reference comparison, not source fact checking.

The three answer formats are direct finding, explanation, and complete list.
They need no extra question-type field: assess the visible question and answer.
C matches substantive list items, not bullet count. S accepts grouped or separate
support and alternative sufficient explanations. Neutral content is neither a
basis nor an automatic penalty. Material contradiction or invalid inference
fails S even when other points are good.

## 2. Model-visible inputs

### Conclusion

Exactly three required, nonblank strings; no additional fields:

```json
{
  "question": "Which borrowing formats are offered?",
  "candidate_conclusion": "Physical books, e-books, and audiobooks.",
  "reference_conclusion": "Physical books, e-books, and audiobooks."
}
```

No support, separate qualifications, citations, source passages, expected labels,
mutation names, case IDs or diagnostic rationales. Material conditions must be
expressed in the conclusion itself to count for C. Support cannot repair it.

### Supporting reasoning: common input

Exactly these four fields:

```json
{
  "question": "Can this snapshot restore the file?",
  "candidate_conclusion": "No.",
  "candidate_supporting_points": [
    {"point_id": "P1", "text": "The file was created after this snapshot was taken."}
  ],
  "candidate_qualifications": []
}
```

Question and conclusion are nonblank strings. Points are ordered objects with
exactly `point_id` and nonblank `text`. IDs are nonblank strings, unique within the answer.
An empty support array is valid and fails S for lack of a basis.

Qualifications are an ordered list of nonblank text strings. An empty list is
valid. Preserve conditions in their wording and interpret them with the candidate
argument. No qualification IDs or explicit attachment mapping are required.

No citations, source passages, reference answer, C prediction, expected S label,
mutation name or provenance enters this common input. Treat factual premises as
given. Assess reasoning, not whether a source establishes those premises.

### Supporting reasoning: reference-example condition

For a later comparison, add exactly one `reference_example` object to the same
common input, containing:

- `reference_conclusion`: nonblank string.
- `reference_supporting_points`: ordered point objects using the same shape.
- `reference_qualifications`: an ordered list of nonblank text strings.

Introduce it as one sufficient example, not a required reasoning checklist.
Its conclusion travels with its support; never merge reference support into the
candidate's argument. Candidate payloads and expected S labels remain identical
between conditions. Reference sufficiency needs independent review; hold ambiguous
or insufficient references out of the paired comparison without changing labels
or silently repairing the reference. Reference mismatch alone cannot fail S.

The no-reference condition is the simpler starting condition. Preparing both
payloads does not authorize either run or select the eventual default.

## 3. Model outputs

One JSON object per call, without surrounding prose or extra fields:

```json
{"conclusion_adequate": true, "reason_codes": [], "explanation": "The conclusion includes all three required borrowing formats."}
```

```json
{"support_sufficient": false, "reason_codes": ["restatement"], "explanation": "The point repeats the conclusion without adding a basis."}
```

Each component returns its own boolean, `reason_codes`, and a nonblank concise
`explanation`. The explanation identifies the decisive comparison or reasoning
defect; no extended chain of reasoning is requested. Actual JSON booleans are
required; strings such as `"yes"` are invalid.

For a pass, `reason_codes` is empty. For a failure, it contains one or more unique
codes from the appropriate vocabulary. Multiple codes describe independent
material defects, not a mandatory exhaustive inventory.

| Component | Code | Meaning |
| --- | --- | --- |
| C | `non_answer` | The conclusion provides no substantive answer. |
| C | `incorrect_answer` | The substantive answer conflicts with the reference. |
| C | `incomplete_answer` | A requested part is missing, outside complete-list omissions. |
| C | `missing_list_item` | A required substantive list item is missing. |
| C | `extra_list_item` | An additional substantive list item is present. |
| C | `scope_or_condition` | A material scope, scenario, condition or certainty differs. |
| C | `contradictory_conclusion` | The conclusion materially contradicts itself. |
| S | `missing_basis` | No supporting points provide a substantive basis. |
| S | `restatement` | Support is circular or merely repeats the conclusion. |
| S | `neutral_only` | Support provides only background or unrelated material. |
| S | `incomplete_support` | A material part of the candidate's claim lacks a basis. |
| S | `invalid_inference` | The stated premises do not justify the inference. |
| S | `contradiction` | A material contradiction undermines the argument. |

Codes are diagnostics, not additional grading criteria. A mistaken diagnostic is
an assessable semantic error, not a parsing failure if its shape is valid. Evaluate
binary accuracy separately from diagnostic quality. Do not ask the model for the
combined score.

## 4. Routing and mechanical failures

Route clean explicit abstentions before projecting either component. Use the
whole structured target response for routing; the C projection alone cannot
establish that the whole answer abstained. A substantive assertion such as
“The policy specifies no deadline” is an answer, not an abstention. Ambiguous
mixed responses stay unresolved at routing and do not acquire invented labels.

Keep routing fixtures separate from semantic calibration. They must include a
clean abstention, a substantive negative answer and an ambiguous mixed response.
No model-based routing implementation or claim of perfect detection is made here.

Each component has an outer record, never included in the model payload:

| Status | Boolean value | Meaning |
| --- | --- | --- |
| `evaluated` | true or false | A structurally valid judgment was received. |
| `not_evaluated_abstention` | null | Clean abstention; skip both components. |
| `routing_unresolved` | null | Routing requires resolution. |
| `invalid_input` | null | Required field/type contract failed. |
| `invalid_output` | null | Returned output failed the output contract. |
| `execution_error` | null | Provider, timeout or execution failure. |
| `not_run` | null | Component has not been executed. |

Missing fields and blank required strings are invalid inputs. A nonblank generic
non-answer is a semantic C failure. An empty S support array is a semantic S
failure, not a malformed answer. Do not coerce missing or malformed values to no.

Preserve raw outputs, parse failures and attempt identities. No automatic semantic
repair, prompt retry, or model-based label repair is part of this first contract.
A later bounded retry policy must record every attempt, cost and selection rule.

## 5. Joining and reporting

Bind each outer record to candidate identity, component, exact payload hash,
reference version, policy/prompt version and execution configuration. Labels and
rationales remain separate from inputs. Match C and S only for the **same complete
candidate answer**; shared question IDs do not make separately generated mutations
the same answer.

When both judgments are valid, derive the approved score: C=no gives 0; C=yes and
S=no gives 1; both yes gives 2. Preserve both judgments. For this proposed first
implementation, incomplete or mechanically failed pairs have a null combined
score with explicit component statuses, even if a valid C=no already implies the
ultimate score would be 0. A C-only test has no combined adequacy score.

Later component reports should include accuracy and macro-F1 against proposed
labels, valid-output coverage, error counts, and per-question/failure-type results.
State whether metrics use valid judgments only and expose the eligible total so
errors cannot disappear. Do not call proposed-label agreement human-gold accuracy.
Preserve abstention counts separately; denominator policy remains deferred.

No metrics, caching result, repeatability claim or model comparison exists for
these proposed panels. Future runs require explicit model/sampling settings,
request/token/time/spending caps and recorded cache accounting before execution.
