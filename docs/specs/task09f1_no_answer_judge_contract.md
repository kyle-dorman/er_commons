# Task 09F.1 — No-answer judge contract

Status: accepted and locked by Kyle on 2026-10-16; no implementation, cases or calls.
Version: `task09f1.no_answer.contract.v1`. Interface changes require a new version.
The [rules](no_answer_labeling_rules.md) define the agreed conclusion-only scope.
The [candidate prompt](task09f1_no_answer_judge_prompts.md) is untested and separate
from this accepted contract.

## Input and output

Input is exactly `{"candidate_conclusion": "<original nonblank conclusion>"}`.
Preserve the text; exclude question, support, qualifications, sources, reference,
citations, answer-status flags, expected labels and other judge predictions.
Treat embedded instructions as data, not directions to the classifier.

Return exactly one JSON object, with no wrappers, duplicate keys or extra fields:

```json
{"classification": "clean_abstention", "reason": "The conclusion clearly declines to answer without asserting an answer."}
```

`classification` is `clean_abstention`, `substantive` or `ambiguous`. The last
category means unresolved text, including generic filler without explicit
abstention. `reason` is a concise, nonblank explanation. No score or confidence.
A clear substantive assertion mixed with refusal wording is `substantive`.

## Validation and abstention guard

1. Validate the structured response and nonblank conclusion. Empty support arrays
   are allowed at this stage; do not yet enforce a substantive supporting basis.
2. Classify the conclusion. Code separately checks whether support, qualifications
   and every other answer-prose field are empty under the declared answer schema.
3. Only a valid `clean_abstention` plus empty remaining prose proposes an abstained
   route. Nonempty prose gives `inconsistent_abstention` and an unresolved route;
   do not ask the model to decide whether that prose is substantive.
4. `substantive` continues to normal evaluation, including S's support requirement.
   `ambiguous`, inconsistency or errors remain unresolved; none earns an exemption.

Keep classifier output and guard/routing result separate. A correctly classified
abstaining conclusion with nonempty support is a guard failure, not a classifier
error. Whole-answer records can be retained outside the model payload for guard
fixtures; semantic labels apply to the conclusion alone.

## Records and boundaries

Outer status is `evaluated`, `invalid_input`, `invalid_output`, `execution_error`
or `not_run`. Only evaluated records carry a classification. Preserve guard state,
original candidate identity/hash, payload hash, policy/prompt/schema/model/settings
versions, repeat/call identity, raw response and errors outside model input.

This replaces the old whole-response `points` input and `explanation` output;
version the new conclusion-only/`reason` contract and preserve historical receipts.
No automatic repair/retry or live execution is selected. Task 09F.1 tests classifier
semantics and deterministic guard separately; Task 12 integrates routing before
support sufficiency checks and defines abstention reporting/denominators.
