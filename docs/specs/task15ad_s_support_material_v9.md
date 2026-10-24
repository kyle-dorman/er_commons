# Task15AD S: conclusion target, joint supporting material — v9

Status: user-authorized offline revision. Independent review and offline validation
precede further calls. V9 is unmeasured; no production promotion, execution or
new spending allowance is implied. Historical contracts/results remain preserved.

## Input and output

The exact model-visible inputs are:

- `question`: interpretation context, not a completeness checklist.
- `candidate_conclusion`: the original conclusion, the sole judgment target.
- `candidate_supporting_points`: ordered objects with `point_id` and `text`.
- `candidate_qualifications`: an ordered list of qualification text strings.

Both supporting fields are material from which the conclusion's basis may be
drawn. Their field names do not determine their relevance or sufficiency. Strict
validation rejects optional context, source passages, citations, reference answers,
expected labels, authoring metadata and other judge verdicts. The output remains
`support_sufficient`, `reason_codes`, and `reason`.

Real projection copies conclusion, supporting points and qualifications separately;
it never appends qualifications to the conclusion. The prediction schema and G's
checks of factual qualifications remain unchanged. Preserve qualification ordering
and text; historical `applies_to` metadata is not newly exposed to S. Evaluate the
meaning and scope of the supplied prose without inventing relationships.

## Rules

1. Judge whether the joint supporting material provides a sufficient, logically
   valid basis for every substantive claim actually made in the conclusion.
   Omitted question/reference content is not an S failure.
2. Qualifications can supply facts, conditions or other explanatory premises.
   They are not additional conclusion claims to grade. A separately unsupported
   or unrelated qualification does not automatically fail S.
3. A qualification matters when it supplies a basis or reveals a material gap,
   invalid inference or contradiction undermining support for the conclusion.
   Source factuality belongs to G; S uses no sources or outside knowledge.
4. Qualifications cannot silently rewrite or repair conclusion scope. A basis
   that supports only a conditional result is insufficient for an unconditional
   conclusion. Assess conditions actually asserted in the conclusion normally.
5. Require at least one substantive basis across both supporting fields. Empty
   supporting points may pass if qualifications supply that basis. Merely
   restating the conclusion in either field is insufficient.
6. Retain v7/v8 whole-conclusion claim coverage, distributed support and reasonable
   inference. Numbers, timing, scope and exclusions asserted in the conclusion
   require a basis. No premises-as-given instruction. Do not turn a conclusion
   assertion into its own supporting premise.

## Synthetic preservation and review coverage

All304 successor examples retain the exact v8 question, conclusion and supporting
points. The18 earlier scope migrations stay inside their conclusion paragraphs.
Add empty qualification lists; do not restore those synthetic scope claims as
supporting premises, which would change the intended ablation. Keep all expected
labels:153true/151false, including biological recovery=true. Preserve the flagged
C008 road-antecedent ambiguity without silent repair.

The304 corpus therefore does not exercise nonempty qualifications. Prepare five
separate invented offline review fixtures to make the rule boundary concrete:
qualification-only support, joint distributed support, irrelevant qualification,
conditional support for an unconditional conclusion, and a qualification that
materially contradicts the conclusion's necessary basis. These fixtures are not
part of the19-question corpus, do not add scored observations, and are not
implicitly authorized for paid dispatch. Independent semantic review is not a
measurement of judge performance.

## Versioning, review and execution

Explicit prompt and input versions must identify the new role semantics despite
its field shape resembling legacy S. Preserve v6/v7/v8 bytes, projections and
scores. No cross-version score reuse. Core/native and context-envelope execution
must select the same prompt, validate the input boundary and bind version identity.
Test real projection without merging, joint-material field delivery, extra-field
rejection, frozen version preservation and the final native request body offline.

Independently review the code, maintained rules, exact304 preservation and the
five role-boundary fixtures before sealing the preparation result. Full project
checks and hashes accompany the result. No model calls, new paid runner or new
budget claim now; retain the$66.896754975 conservative reservation and prior
liabilities under the existing$70 cap. A later retest needs an explicit roster,
exact native requests and cumulative budget reconciliation before authorization
is exercised. No commits or pushes.
