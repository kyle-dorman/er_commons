# Structured C candidate-conclusion transformations v2

Accepted refinement: 2026-10-22. Supersedes v1 for new datasets; the sealed
Task15H dataset retains its original guidance and expectations. This authoring contract supersedes the overlapping
Task09F/Task15B generation slots for new structured-C datasets. Historical catalogs,
labels and results stay unchanged. Transform only candidate conclusions; keep the
question, R/O reference text and IDs, and Baylands overview fixed. Reference
perturbation is a separate future exploration.

## Eight families

| ID | Family | Tests and expected distinctions |
| --- | --- | --- |
| RC | Required coverage | Complete required answer; one or several required meanings absent. Includes incomplete lists, neighboring answers, and duplicate replacement. Missing wording is not missing meaning when conveyed elsewhere. |
| ME | Meaning-preserving expression | Paraphrase, compression, order, split/combine and tone. Preserve the full point-status vector where meaning is unchanged; no separate slots merely for legacy IDs. |
| EX | Required explanation | Substantive why/how connection versus circular outcome repetition, naming an analysis without its finding, or an explicitly wrong explanation. Attribute missing or contradicted required meaning. |
| CT | Reference contradiction | Explicit conflict with an R or O point: outcome, number/unit/comparison, relationship, scope or condition. Optional numeric facts may be omitted but not substantively contradicted. Include equivalent numeric expressions and compatible different-scope controls when applicable. |
| OC | Optional coverage | No optional content; one or several optional points; meaningful partial optional coverage without contradiction. Numerical details require relevant values; qualifications require their limitation, not contextual restatement. Optional bullets are not all-or-nothing completeness checklists. |
| CP | Contradiction precedence | Correct and incompatible claims about the same point, in either order. Contradicted wins; correct statements elsewhere do not cancel it. |
| CA | Compatible additions | Additional claims absent from both lists, including unrelated content, without contradiction. No separate additions judgment or relevance penalty. A pass does not certify added claims as true. |
| CD | Combined defects | Multiple clear, independently identifiable failures; identify each affected point and its proper status without averaging. |

Baseline is a reviewed natural-language candidate satisfying all R points, not a
copy of the structured reference. A single candidate may cover several concepts;
assign one primary family and secondary tags, without duplicating its payload.
Each family is a coverage goal, not a universal quota per question.

## Explicit combined-defect objectives

| Subtype | Required check |
| --- | --- |
| CD1 | Two required omissions: identify both Missing points. |
| CD2 | Required omission plus required contradiction: distinguish Missing from Contradicted on the right points. |
| CD3 | Required omission plus optional contradiction: identify both; optional elaboration cannot restore missing required meaning. |
| CD4 | Two contradictions on distinct reference points: detect both, not only the first. |
| CD5 | A defect surrounded by accurate required/optional content: extensive correct material cannot compensate for that defect. |
| CD6 | Correct-plus-contradictory claims on one point plus another defect: apply contradiction precedence and detect the separate defect. |

Build combinations from clear single-edit cases when possible and record parent
IDs. Reassess the entire resulting conclusion; edits may overlap, cancel or alter
other point statuses. Do not inherit expected vectors mechanically. If the question
cannot instantiate a subtype cleanly, record an explicit exclusion instead of
forcing a contrived case. CD5 is a masking/compensation stress test; it can contain
only one actual defect and must not be reported as two independent errors.

## Clear-label boundary

Prefer explicit incompatible assertions under the same circumstances. Dropping a
qualifier, hedge or explanatory clause is not automatically a contradiction. A
clearly absent required meaning is Missing; an optional partial meaning remains
acceptable unless an actual claim conflicts. Do not infer universality merely
from shorter wording. Keep compatible alternate times/populations/scenarios
separate from same-scope conflicts. Reasonable rounding and exact unit conversion
are meaning-preserving controls, not numerical errors.

Exclude unresolved cases from scored inputs. Preserve the candidate, intended
transformation and competing interpretations in an exclusion record. Difficult
phrasing with clear expectations is useful; debatable labels are not a target.
Explicit clean abstention remains a separate routing concern, not an automatic
C semantic-negative category. Citation defects, S-only edits, reference mutations,
provider-output/schema corruption and prompt-injection robustness are outside
this semantic pilot. Mechanical parser tests already cover output structure.

## Expected-data contract and review

For every candidate store the full expected status vector for all R/O IDs, the
consistent overall Boolean, and a brief per-point rationale, separate from model
inputs. Record primary family, subtype/tags, target IDs, actual affected IDs and
any parent candidates. Expected explanations/excerpts are review aids, not exact
strings the judge must reproduce. Judge semantic statuses and Boolean separately;
structural validity and quote fidelity are distinct diagnostics.

Do not assume only the targeted point changes. Distinctive reference meanings can
legitimately affect several points, but shared contextual wording is insufficient.
For numerical details, require relevant modeled values with identifiable scope;
thresholds alone and generic below-threshold claims do not address modeled results.
Partial numerical coverage and equivalent units remain valid controls. For a
qualification, require its limitation rather than the underlying claim or a
contextual comparison. Include paired controls for these boundaries where useful.
Explicit conflicting claims remain Contradicted even without positive coverage.
Review actual candidate meaning independently.
A reviewer must be different from the author and bind the exact candidate and
expectation bytes. Expectations are agent proposals, not human gold. Reference
content is fixed during this pilot; discovering a defect triggers discussion and
a new version rather than silently editing labels to fit generated candidates.

## Historical consolidation

P01–P06 and equivalent-mechanism controls become ME; O02/O03/O04/A01/A09/A10
become RC when they remove required meaning. F08/F11/F12 become EX.
F03–F07/F09 and explicit-boundary A02 become CT when they actually contradict;
condition omissions belong to RC instead. F10 becomes reference-bound CP/CT,
not a catch-all internal-conflict failure. A03 and known optional additions become
OC; additions outside both lists become CA. BASE is replaced by RC's minimal
reviewed candidate. These mappings preserve provenance, not duplicate generation
slots. The same legacy label may map differently depending on its actual edit.
