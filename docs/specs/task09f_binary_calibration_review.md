# Task 09F — Small binary calibration review

Status: both small suites accepted by Kyle for calibration. No judges run and no runtime changes.
Acceptance of these selections does not approve the full synthetic datasets.

Review the proposed labels and rationales; these panels are not a request to label
every example from scratch. Start with the contract, then discuss any examples
whose proposed judgment is unclear or seems wrong.

The current v3 panel retains the accepted 24-example conclusion selection and
replaces the separately authored support panel with 12 examples selected from the
[published support synthesis](task09f_support_synthesis_result.json). Candidate
and reference qualifications use plain text. Earlier packages remain unchanged.
Read the [proposed contract](task09f_binary_judge_contract.md) alongside these panels.
The [general policy](adequacy_labeling_rules.md) remains the semantic authority.

## Conclusion panel

24 unchanged examples selected from the [published conclusion synthesis](task09f_conclusion_synthesis_result.json):
six each from C056 (direct finding), C007 (explanation), C017 (modeling explanation),
and C050 (complete list). Each question has three proposed yes and three proposed
no labels. This is a purposive diagnostic panel, not a representative accuracy set.

The full review text, with question, candidate, reference and proposed rationale,
is in `conclusion/selection.md` under the external artifact directory below.
Coverage includes passing baseline/paraphrase/compression, missing or extra list
items, equivalent grouping, within-item details, duplicate-item omission,
incomplete multipart answers, incorrect mechanisms, scope and condition changes,
certainty, reversal and contradiction.

The three-field inputs and existing labels are copied unchanged. Selection is
fixed before judge outcomes. S is not labeled for these conclusion-only records:
they contain no candidate supporting argument to evaluate.

## Support panel

Twelve published examples over C056, C007 and C050 exercise the same three
formats. All selected records are independently reviewed and paired-comparison
eligible. C051 and unresolved slots are excluded.

Review `support/review.md` for full candidate arguments, source example IDs and
published proposed S labels/rationales. Coverage targets sufficient controls,
restatement, neutral-only or absent basis, incomplete support, contradiction,
grouped/separate support, alternative reasoning, and missing/extra-conclusion
boundary controls. Selection uses original published examples, not newly written
substitutes. Qualification metadata is projected to exact text strings; all other
candidate content and the published S labels are preserved.

Common S inputs and reference supplements are separate. Labels are fixed across
reference conditions. Source synthesis provides S labels; do not treat the
boundary-control descriptions as independently approved C labels or infer combined
scores. The panel is not exhaustive across diagnostic families. No reference
example becomes a required checklist.

## Routing and mechanical review fixtures

These invented examples are separate from semantic label accuracy:

| Fixture | Expected handling |
| --- | --- |
| “I cannot determine the return deadline from the available material,” with no substantive answer elsewhere | Skip C/S as explicit abstention; null score. |
| “The policy specifies no return deadline,” with a supporting point | Substantive answer; route to C/S, without assuming it is correct. |
| “I cannot determine the deadline,” followed by “It is definitely 30 days” | Routing unresolved; do not silently classify the whole response as clean abstention. |
| Missing `candidate_conclusion` field | Invalid input, not C=no. |
| Nonblank conclusion “This question concerns borrowing,” for a question asking which formats are offered | Semantic C failure, not malformed input. |
| Empty `candidate_supporting_points` array | Evaluate S=no for missing basis. |
| Qualification value is an object rather than a text string | Invalid S input under the revised proposed contract. |
| Judge returns `"true"` instead of JSON `true`, or omits its explanation | Invalid output, not a semantic no. |
| Judge returns a valid boolean and diagnostics that misread the answer | Validly formatted semantic error; keep separate from parsing failures. |

These are expected handling examples for contract review, not executed tests or
an implemented abstention detector.

## Artifact location and boundaries

Artifact directory relative to `ER_COMMONS_DATA_ROOT`:

```text
pipelines/brisbane_baylands/task_09/09f_20261014_binary_contract_calibration_v3/
```

Keep model payloads, labels/rationales, provenance, human review text and hashes
separate. The [repository result pointer](task09f_binary_calibration_result.json) binds the
finished review package. The enclosing completion records the new selection review;
the conclusion manifest is retained unchanged from its original preparation.
Kyle accepted both the 24-example C suite and the 12-example S suite for
calibration. Published label sidecars retain their original proposed-label status;
this selection acceptance does not approve either full synthesis dataset.
Four base questions do not constitute 36 independent questions.

No provider calls, judge outputs, measured accuracy, costs or caching claims exist
for this panel. No test/reserved cases, historical judge outcomes, or concurrent
unpublished support data are used. Prior releases and synthesis remain unchanged.
Stop for user review before implementation or evaluation.

## Human review decisions — 2026-10-14

Kyle confirmed the following three C=no labels. This approval is limited to these
records. Kyle subsequently accepted the full 24-example suite for calibration;
that acceptance does not extend to the entire synthetic dataset.
The sealed artifacts retain their original proposed-label status. This section
records the subsequent human decisions without rewriting those artifacts.

| Candidate | Confirmed C | Reason |
| --- | --- | --- |
| C056-F05_F09 | No | It answers the question, but turns an approximate modeled prediction into an exact universal guarantee. Completeness alone does not establish agreement with the reference. |
| C017-F07 | No | Sufficient distributed solar storage is essential to the planned onsite solar accounting described by the reference; omitting it removes a material assumption. This storage is distinct from the uncertain regional battery facility, whose benefits the answer excludes. |
| C050-A10 | No | The third bullet repeats directional information rather than supplying the required broader navigational-map concept. The failure is missing substantive coverage, not omission of the word “map.” |

The C017 decision resolves the earlier discussion uncertainty about whether the
storage assumption belongs in the conclusion. No candidate text or label value
changed. The contract now explicitly states that completeness and substantive
reference agreement are both required; this clarifies the existing approved rule.
The v3 completion binds the clarified contract.

Kyle subsequently approved both benchmark-role prompt openings. The current
contract links their exact text; the sealed v3 contract hash predates that link-only
addition. Panel payloads and labels remain unchanged.
