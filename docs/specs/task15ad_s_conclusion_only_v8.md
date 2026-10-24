# Task15AD S conclusion-only input — v8

Status: user-authorized offline revision; independently reviewed preparation is
required before any further model calls. No execution authorization or promotion
is implied by this contract. Historical v6/v7 remain reproducible.

## Contract

Prompt version: `task15ad.binary_adequacy.support_conclusion.v8`.
Input version: `support_conclusion.input.v1`. Exact prompt source:
[support_conclusion.py](../../src/er_commons/support_conclusion.py).

S asks: do the candidate supporting points jointly provide a sufficient, logically
valid basis for the claims actually asserted in the candidate conclusion?

The only model-visible input fields are:

- `question`: context for interpreting the candidate, not a completeness checklist.
- `candidate_conclusion`: the original conclusion paragraph.
- `candidate_supporting_points`: ordered objects with `point_id` and `text`.

Separate qualifications, optional context, citations, sources, reference answers,
required/optional labels, expected labels and other judge verdicts are excluded.
The strict v8 input validator rejects extra fields, including an empty
`candidate_qualifications` list. Input projection removes excluded answer sections
before validation; the validator does not silently discard supplied fields.

Real-answer projection preserves the conclusion verbatim. Do not append separate
qualifications or optional context to make new S claims. A separate qualification
cannot repair or invalidate the conclusion in S. Generation still requests essential
scope in the conclusion and its basis in supporting points. Generation's answer
schema and G's factual-qualification checks are outside this change.

Retain the v7 whole-conclusion support rules: numerical, temporal, scope and
exclusion claims need a basis; conclusion assertions do not establish themselves.
Allow straightforward inference and distributed support. Check scope and conditions
actually written in the conclusion against support; do not require omitted
reference content. No premises-as-given wording. G owns external source verification.
The output stays `support_sufficient`, `reason_codes`, and `reason`.

## Synthetic workflow

Publish a successor of all304 reviewed examples across19 development questions.
Remove the separate qualifications field from every packet. For the18 examples
that used it, put the scope statement directly into the same coherent conclusion
paragraph. Deliberately overbroad statements stay overbroad in negative examples.
The other286 conclusions remain unchanged. Question text and supporting points
remain unchanged for every example. Keep the existing synthetic family names and
record exact before/after transformations as reviewer-only provenance.

Retain expected labels, including true for biological-recovery tracking. Preserve
the C008 road-antecedent ambiguity without unrequested text or expectation changes.
No reference checklists or authoring metadata enter judge payloads. Native payload
validation and independent review must cover the changed paragraphs and role boundary.

Historical qualification-field failures describe the older contract. They do not
show whether S succeeds on these rewritten conclusion claims. V7 scores cannot be
reused as v8 qualification scores, including for packets whose conclusions did not
change: the input/prompt contract is different. Do not mix versions in aggregates.

## Execution and budget gate

This revision makes zero paid calls and creates no new spending allowance.
Preserve the$66.896754975 existing conservative reservation, its prior liabilities
and the stopped v7 records. Before any v8 retest, explicitly select the reviewed
successor corpus and prompt, render exact requests offline, reconcile any unattempted
slot substitutions without releasing attempted liabilities, and confirm numerical
budget coverage under the existing cap or obtain approval for a changed budget.
No automatic retest, remaining-all19 dispatch, real-benchmark generation, commit or push.

## Review and validation

Require independent semantic review of all18 migrated paragraphs and labels;
strict3-field input/native request isolation; real-answer projection that neither
leaks nor merges excluded fields; explicit version-bound item/packet identities;
legacy default/schema preservation; and appropriate offline tests/project checks.
Publish hashes and a review result pointer only after validation. The result is an
unmeasured revised contract and corpus, not a qualified judge.
