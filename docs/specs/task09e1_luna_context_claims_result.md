# Task 09E.1 — Contextual claims pilot outcome

The user-authorized [claims-only experiment](task09e1_luna_context_claims_v1.md)
is complete with a **failed expansion gate**. The contextual addition helped the
ambiguous pet-policy summaries but did not meet the fixed improvement criteria
and introduced observed regressions. No full Dev3 pass was dispatched, no prompt
was promoted, and no conclusion or abstention inference ran.

## What was tested

Two fresh Luna Responses arms used medium reasoning, the repaired cache layout,
unchanged source/question/claim payloads and the same semantic validation. The
baseline was the previous combined scope/absence/grammar prompt, not the original
low-reasoning full-panel configuration. The candidate appended a general instruction
to judge natural meaning in the question's context, accepting faithful summaries
while retaining factual, modality, condition and own-citation requirements.

Ten exact distinct inputs received nine repetitions per arm: four troublesome
inputs and six controls, 180 generations total. The troublesome inputs represent
three claim wordings and two semantic issue families; the short pet-policy claim
has two original citation-ID forms. The nine previously unstable answer-point slots
were deduplicated for this pilot. All ten inputs came from the previous eleven-answer
subset. Original labels, claims, questions, sources and prior artifacts were preserved.

The accepted policy-level enforcement reading reflects the user's stated preference
for ordinary evidence-grounded summaries. That development interpretation is not
proof that the competing narrower reading is impossible. The question already
reaches the claim judge; no new context or evidence was added.

## Results

| Metric | Previous combined prompt | Contextual addition |
| --- | ---: | ---: |
| Valid outputs | 90/90 | 90/90 |
| Trouble-input agreement | 28/36 (77.8%) | 31/36 (86.1%) |
| Control agreement | 53/54 (98.1%) | 52/54 (96.3%) |
| Overall agreement | 81/90 (90.0%) | 83/90 (92.2%) |
| False rejections relative to expected decisions | 8 | 5 |
| False acceptances relative to expected decisions | 1 | 2 |
| Inputs unanimous and correct across nine repeats | 6/10 | 5/10 |

| Input | Baseline correct /9 | Candidate correct /9 |
| --- | ---: | ---: |
| Short pet policy, original S2 form | 4 | 7 |
| Short pet policy, original S1 form | 7 | 8 |
| Expanded pet policy | 8 | 8 |
| Grading deadline qualification | 9 | 8 |
| Unsupported universal scope | 8 | 7 |
| Stronger modality, invented fine, uncited claim, preserved modality, bounded absence | 9 each | 9 each |

Pet-policy agreement improves from 19/27 to 23/27. The net trouble gain is only
three because grading loses one correct judgment. All four candidate trouble
inputs still vary across repetitions. Higher agreement did not establish better
unanimity: the baseline's stable grading result became unstable.

The frozen gate required at least 30/36 trouble agreement **and** a gain of four,
no per-input regression, at least 6/9 per troublesome input, 54/54 controls, valid
outputs and independent source review. The candidate failed the gain, per-input
nonregression and control requirements. Thresholds were not changed after results.

## Why the controls matter

The unsupported control says: “Every Baylands development must adopt the
wildlife-protective pet policy,” then specifies the deed/lease enforcement mechanisms.
The source distinguishes a construction-worker no-pets rule for all developments
from a broader resident pet policy for developments with a residential component.
The candidate twice accepted the control by combining those two scopes. In one
explanation it asserted that the point did not generalize the residential condition,
despite the explicit “Every” wording. The baseline made the same class of mistake
once. This is an observed regression in a small sample, not proof of its long-run
frequency, but it fails the expansion safeguard.

The candidate's remaining pet-policy rejections still apply the narrower
HOA/deed-versus-lease reading. Its grading rejection still overreads the deadline
qualification as excluding a relationship to wetland recovery. The new instruction
therefore neither resolves the ambiguity consistently nor cleanly separates
reasonable compression from an explicit change in scope.

Set this appended candidate aside. Keep the previous configuration available as
the comparison baseline; neither is a qualified judge. A subsequent experiment
would need a more precise contextual-meaning rule that preserves explicit
universals and subject/condition boundaries. No additional tuning or other-error
remediation was performed in this bounded run.

## Cost, validation and preservation

All 180 generations used Luna and have complete native receipts, exact count
parity, validated outputs and no replay. Standard-rate estimates are $0.025399875
baseline and $0.022554680 candidate, **$0.047954555 total**. Native payer metadata
reports developer for all 180 calls; invoice totals and promotional coverage are
not inferred. Conservative reservations totaled $0.680006250, within the $4
overall cap. The unused conditional full runs incurred no generation calls.

Focused tests: 210 passed. Eight offline launcher guard tests passed. `make fix`
passed; `make check` reported 4,259 passed, one skipped and only the three historical
Task 06G failures, with format/lint/types passing. Independent prompt, launcher,
analysis, native-result and source reviews are preserved. No package code or
default prompt changed, no new dependency, commits or pushes.

Fresh external namespace: `task_09/09e1_20261012_luna_context_claims_v1/`.
The [result pointer](task09e1_luna_context_claims_result.json) binds frozen prompts,
inputs, native receipts, the denied full-run gate, reviews and completion inventory.
All 48,998 checks against earlier inventories passed. Credential scans cover raw
artifacts and decoded Inspect logs. Results concern this selected pilot only;
the earlier 151/166 full-panel Luna baseline remains historical and unchanged.
