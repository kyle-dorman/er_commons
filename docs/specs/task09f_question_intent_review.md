# Task 09F — Development question intent review

Status: **intent labels confirmed by Kyle**, 2026-10-14. These are accepted
planning metadata, not yet integrated into runtime or a regenerated publication.
No reference answer, synthetic answer, score expectation or held-out record changed.

## Accepted mapping

| Intent | Development case IDs | Count |
| --- | --- | --- |
| Rebuttal / challenge | C007 | 1 |
| Document explanation | C001, C006, C008, C014, C017, C019, C027, C028, C029, C036, C037, C041, C042, C045, C050, C051, C054, C056 | 18 |

Kyle's correction: “i think only C007 is a rebuttal. sadly.” This supersedes the
original six/thirteen proposal. All accepted assignments are user-confirmed;
original model confidence rankings below are historical, not confidence in the
confirmed labels.

- **Rebuttal / challenge:** seek an evidence-supported objection to an external
  proposal. A qualified or unresolved conclusion is allowed; the label does not
  mean the correct answer must be no.
- **Document explanation:** retrieve and explain what the documents establish,
  without an argumentative agenda. Skeptical wording, apparent contradictions,
  and an expected negative answer do not by themselves imply rebuttal intent.

Development coverage is predominantly document explanation (18/19). C007 is a
single rebuttal example, insufficient for broad claims about rebuttal performance.
Keep both task instructions explicit without forcing explanation questions into
an adversarial role or expanding the dataset without a new scope decision.

## Historical proposal, superseded

The exact questions and original reasoning are retained below for traceability.
They are not the active intent assignments.

Confidence concerns inferred **task intent**, not answer correctness, source
quality or answerability. High/Medium/Low are qualitative judgments, not calibrated
probabilities. Within each label, rows sort High → Medium → Low, then case ID for
ties. Intent is distinct from the seven answer-demand types in the
[redesign discussion draft](task09f_adequacy_redesign_draft.md).

Assignments use exact question wording and explicit user context (particularly
C007). They do not use the reference answer's polarity or judge results to decide
intent. A bounded independent review flagged C008/C056's similar ambiguity and
C051's explanatory reading; those findings are reflected below.

### Original rebuttal / challenge proposals — 6

| ID | Confidence | Exact question | Reason / ambiguity |
| --- | --- | --- | --- |
| C007 | High | Could Bayshore Boulevard be reduced to three lanes to improve connectivity for residents while retaining its role as a regional through-traffic artery, using either a movable median adjusted to commute-hour traffic flows or overhead signals directing lane flow? | Explicit external proposal; the user has confirmed rebuttal intent for this case. |
| C029 | High | Does the three-year fencing or marking period mean habitat protection around trails on Icehouse Hill ends after three years? | Tests the premise that a limited marking period means protection ends; a counterargument is the likely task. |
| C037 | High | Does the proposed increase in wetland acreage mean the project will avoid temporary losses of wetland function during construction? | Challenges the inference from more final acreage to avoiding temporary functional losses. |
| C001 | Medium | Why does the DEIR consider cumulative health risks less than significant even though Baylands development adds to existing pollution? | The even-though clause presents an apparent objection to the finding; could also be a neutral request for its rationale. |
| C045 | Medium | Why does the Baylands Draft EIR classify the proposed community sports fields as “open space” rather than “open area” when they would be developed recreation facilities rather than natural, unimproved land? | Contrasts developed facilities with natural land to challenge the classification; a neutral definitions question is also plausible. |
| C054 | Medium | Why does the Draft EIR conclude that Alternative 5 would have less-than-significant vehicle miles traveled impacts despite placing some development farther from transit? | The despite clause presents a counterargument based on distance from transit; explanatory intent remains plausible. |

### Original document explanation proposals — 13

| ID | Confidence | Exact question | Reason / ambiguity |
| --- | --- | --- | --- |
| C006 | High | How would the Baylands project make proper maintenance and tuning of construction equipment a binding requirement and demonstrate compliance with it? | Requests the binding mechanism and compliance demonstration without proposing an alternative or demanding opposition. |
| C014 | High | How does the DEIR account for the Quarry and Candlestick Point developments when evaluating the Baylands’ cumulative transportation impacts? | Requests how two developments enter the analysis. |
| C017 | High | How does the DEIR account for planned onsite solar generation and renewable grid electricity when estimating the Baylands’ future electricity-related GHG emissions? | Requests treatment of two electricity inputs in the emissions calculation. |
| C019 | High | Under the modeled sea-level-rise scenario, how would groundwater levels beneath the Brisbane Landfill change with the proposed closure measures in place? | Asks for the modeled outcome under specified conditions. |
| C027 | High | How would the proposed Bay Trail connection along Sierra Point Parkway address conflicts between people walking or cycling and motor vehicles? | Requests how the proposed connection addresses user/vehicle conflicts. |
| C036 | High | What measures will the Baylands project take to reduce the impacts of artificial lighting at night on wildlife and people? | Requests the proposed mitigation measures. |
| C041 | High | How would the Baylands enforce its controls on domestic and feral animals to protect native wildlife? | Requests the enforcement mechanism. |
| C050 | High | What measures does the Baylands project propose to help bicyclists and pedestrians navigate its trails? | Requests proposed navigation measures. |
| C028 | Medium | How will Baylands residents be adequately protected from noise generated by rail operations within the Caltrain right-of-way if that noise cannot be eliminated? | Asks how protection works given persistent noise; could also express a challenge to adequacy of mitigation. |
| C042 | Medium | How does the Draft EIR’s assessment of park and recreational facilities support its conclusion that increased use from the Baylands project will not cause substantial physical deterioration? | Explicitly requests the assessment-to-conclusion reasoning; may also express skepticism, without a clear proposal to counter. |
| C051 | Medium | Why does the Draft EIR call for additional building height limits west of the Caltrain tracks to protect views of San Francisco Bay and San Bruno Mountain beyond the height restriction near US 101? | Requests the rationale for an additional restriction; could be a challenge that the existing restriction should suffice. |
| C008 | Low | Would reducing through traffic on Bayshore Boulevard prevent traffic problems on surrounding streets? | Plain outcome question; may instead be intended to challenge the premise that reduced corridor traffic solves nearby problems. |
| C056 | Low | Would the Baylands drainage improvements eliminate existing flooding at Bayshore Boulevard and Industrial Way? | Plain outcome question; may instead challenge an assumption that drainage improvements eliminate flooding. |

## Review and downstream use

Kyle confirmed the intended labels on 2026-10-14. A label
is a task instruction supplied to the search/answer model and both judges after
the revised contract is agreed and implemented. Grounding retains the same source
support standard for both types. Adequacy checks fulfillment of the specified
intent and the answer's internal reasoning; it must not impose rebuttal behavior
on an explanation request. The user's latest direction excludes source factuality
checks from adequacy. No accepted intent label encodes a desired factual answer.

This review is development-only. Held-out questions must not be inspected for
rubric tuning; any later intent annotation needs a separate controlled process.
Existing questions retain their exact wording. A human correction to intent is
recorded explicitly rather than inferred from whether a judge happens to agree.

## Provenance and validation

All 19 unique case IDs and exact questions were read from the development-only
`exact_reference_controls.json` binding in the [09A.3 publication pointer](task09a3_final_result.json).
Its SHA-256 was verified: `d5d1b0d57d3416bba70bda8a4f88eaa3314c1ef93fe2ec67f7cd94d0f13dcc74`.
Every question occurs once in the original inventory; the accepted mapping covers all
19 IDs. Synthetic adequacy/grounding score labels were not changed,
no provider inference ran and no reserved/test payloads were accessed. The original
proposal received an independent wording-based review; Kyle’s correction supersedes
those inferred assignments. Documentation diff
validation uses `git diff --check`.
