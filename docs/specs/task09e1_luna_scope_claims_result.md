# Task 09E.1 — Scope-preserving claims pilot outcome

The user-authorized [replacement prompt experiment](task09e1_luna_scope_claims_v1.md)
is complete. **The candidate performed worse and failed the unchanged expansion
gate.** No larger Dev3 pass, conclusion/gate calls or further tuning followed.
Set the replacement aside; package defaults and prior artifacts remain unchanged.

## Design

The failed broad contextual addition from the [previous attempt](task09e1_luna_context_claims_result.md)
was replaced, not retained. The new addition checks subject, requirement and
condition together, keeps explicit quantifiers/modality/conditions binding, and
uses the question to resolve ordinary meaning without supplying facts. Baseline
remains the previous combined scope/absence/grammar prompt. Both use Luna Responses,
medium reasoning and repaired caching with unchanged source/claim/question inputs.

Same ten exact pilot inputs, nine fresh repetitions each per arm: four trouble
payloads (three wordings/two issue families), six controls, 180 generations.
Expected pet-policy support follows the user's accepted natural coordinated
reading; it is not adjudicated proof against the alternative narrow interpretation.
Source text, labels and own-citation boundaries were not changed.

## Results

| Metric | Fresh combined-prompt baseline | Replacement scope prompt |
| --- | ---: | ---: |
| Valid outputs | 90/90 | 90/90 |
| Trouble agreement | 29/36 (80.6%) | 26/36 (72.2%) |
| Control agreement | 54/54 (100%) | 53/54 (98.1%) |
| Overall agreement | 83/90 (92.2%) | 79/90 (87.8%) |
| False rejections relative to expectations | 7 | 10 |
| False acceptances relative to expectations | 0 | 1 |
| Inputs unanimous and correct across nine repeats | 8/10 | 5/10 |

| Trouble input | Baseline correct /9 | Candidate correct /9 |
| --- | ---: | ---: |
| Short pet policy, original S2 form | 4 | 7 |
| Short pet policy, original S1 form | 7 | 6 |
| Expanded pet-policy wording | 9 | 7 |
| Grading deadline qualification | 9 | 6 |

Pet-policy agreement overall is unchanged at 20/27. The S2 improvement is offset
by regressions in the S1 and expanded forms. Grading loses three correct judgments.
The unsupported universal-scope control falls 9/9 to 8/9; all other controls remain
9/9. All four candidate trouble inputs still vary across repetitions.

The frozen gate fails minimum trouble agreement (26<30), required gain (minus
three rather than plus four), per-input nonregression and perfect controls. No
threshold was relaxed and no full-panel generation was dispatched. There is no
new full-panel accuracy estimate. The earlier 151/166 Luna result remains a
historical different-prompt/settings comparison, not this candidate's result.

## Source review and interpretation

The seven candidate pet-policy rejections still favor a narrower HOA/deed versus
lease reading. Three grading rejections again treat the deadline qualification
as an unsupported exclusion of any relationship to wetland recovery. The new
relationship wording did not resolve these readings consistently.

Candidate repetition six also accepts the explicit claim “Every Baylands development
must adopt the wildlife-protective pet policy,” joining the all-development
construction-worker no-pets requirement with the residential-component pet-policy
and deed/lease mechanisms. This is the same concrete scope-confusion class that
the replacement was intended to prevent. The baseline made no such acceptance
in this fresh pilot. Nine repetitions do not determine long-run error frequencies,
but the observed result clearly fails the development safeguard.

The independent source review denies expansion. These two appended-prompt attempts
have not established a reliable accuracy/stability improvement. Retain both
negative results and the existing baseline. Any further approach, such as a
structured representation of the source's relationships, would be a separately
specified experiment rather than another unrecorded prompt revision. No such
change was implemented here.

## Cost, validation and preservation

All 180 calls passed exact count/native usage parity, model/request identity,
output-cap, semantic validation and no-replay checks. Standard-rate estimates:
baseline $0.025267375, candidate $0.027634180, **total $0.052901555** (about 5.3 cents).
All native payer fields report developer; actual invoices and promotional credits
are unknown. Conservative reservations totaled $0.680501250 under the $4 cap.
The unused conditional full passes incurred no generation calls.

Focused tests: 210 passed; eight offline launcher guards passed. `make fix` passed.
`make check`: 4,259 passed, one skipped and only the three historical Task 06G
failures; format/lint/types passed. Independent prompt, launcher/analyzer, native
result, source and documentation reviews are retained. No package code/default
prompt changes, dependencies, commits or pushes.

The [result pointer](task09e1_luna_scope_claims_result.json) binds the fresh
`task_09/09e1_20261012_luna_scope_claims_v1/` namespace: frozen inputs/prompts,
native receipts, Inspect logs, denied gate, reviews and completion inventory.
All 49,934 prior inventory checks passed. Credential scans include raw artifacts
and decoded Inspect logs. No reserved/test, Dev6 or full-19 expansion occurred.
