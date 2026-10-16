# No-answer labeling rules

Status: accepted and locked by Kyle on 2026-10-16; runtime not implemented.
Version: `task09f1.no_answer.rules.v1`. Later semantic changes require a new version.
The [contract](task09f1_no_answer_judge_contract.md) owns fields and error handling.

Detect clear abstention in the **conclusion**, not whether abstention is justified.
The classifier receives conclusion text only, without the question or sources.

1. **Clear abstention:** the conclusion explicitly declines to answer or states
   inability/insufficient information, without also making an answer assertion.
   “I cannot determine the deadline” qualifies; “There is no deadline” does not.
2. **Other conclusions:** a partial, negative, hedged or conditional answer is
   substantive. Generic filler or unclear intent is unresolved, not abstention.
   A clear assertion takes precedence over refusal wording in the same conclusion.
3. **Empty-field guard:** code accepts an abstention only when supporting points,
   qualifications and any other answer-prose fields are empty. A declining
   conclusion with other prose is inconsistent/unresolved, never automatically
   exempt. Generation instructions must require abstention in the conclusion and
   empty remaining prose fields; answer-status flags are not authoritative.
4. **Order:** validate structure, classify the conclusion, apply the guard, then
   enforce substantive-answer support requirements. Clean abstention may have no
   support; a substantive answer without support still fails S. Blank/malformed
   conclusions, classifier errors and missing results are not clean abstentions.

No-answer detection assesses neither correctness, grounding nor completeness.
Task 12 owns routing integration and reporting. Existing whole-response classifier
prompts and receipts retain their historical contract; this is a new version.
