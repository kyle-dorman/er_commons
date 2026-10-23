# Task15Y — Judge required-point coverage in model support

Status: Complete and user-accepted after the code-quality pass on2026-10-23.
The [accepted judge handoff](../../docs/specs/task15y_judge_handoff_v1.md) selects
this judge and its evidence for downstream15AD. Known material-omission errors
remain accepted limitations. The user authorized a local closeout commit; no push
or additional model calls. Historical artifacts and liabilities remain preserved.

The sections below retain the completed development/authorization history.
Real-answer projection, execution and C/G report joins belong to15AD and were not
performed here.15Z is next and requires separate activation.

### Completed code-quality scope

Review the coverage core, native adapter, bounded runner, tests and CLI documentation.
Simplify duplicated validation/accounting and long orchestration functions without
changing prompt/schema, labels, provider requests, budgets or failure semantics.
Keep approved population identities explicit; do not turn this into a generic runner
framework. Independently review changes, replay saved inputs/outputs offline against
sealed source snapshots, and run `make fix`, `make check` and `git diff --check`.
Historical code hashes remain enforced; refactoring does not authorize replaying a
paid run or rewriting its sealed manifest. Report the changes and leave acceptance
to the user after this pass. Real-answer integration remains separately scoped.

### Completed all19 preparation boundary

Author the additional13 development questions against15AC, carry forward the six
with the approved adjudication overlay, and independently review every new variant.
Exclude the exact confusing C041/R2 distinguished-scenarios variant; accept the
C017/R1 subtraction variant as true and retain C041/R2 distributed-gap as false.
The reviewed suite is frozen and the user has approved the
[all19 execution contract](../../docs/specs/task15y_all19_preparation_v1.md). Neither
six-question Round2 nor real-answer diagnostics is authorized.

### Approved operational continuation

The user explicitly authorized fixing cache retention to24h and continuingRound1.
Use a linked sibling namespace with verified ancestor seal and byte-identical suite,
labels, reference identities and semantic prompt/schema. Retain the full conservative
liability of16 sent requests; reassign only provably unsent reservations. No fresh
budget is created. The continuation checkpoint uses at most one transport retry
(two new attempts), ensuring even previously attempted slots stay within three
total attempts. The remainder retains at most two retries. All other settings and
checkpoint/stop rules remain unchanged. Independent code/accounting review and
offline tests precede dispatch. The initial failure below remains historical evidence.

## Approved execution boundary (2026-10-23)

- Pin15AC; pilot C014, C017, C019, C037, C041, C056 (10 required points).
- One required point per request; only candidate supporting points enter coverage.
  Mixed unresolved conflicts are false. False outputs have empty supporting IDs.
- Luna `gpt-6-luna`, medium reasoning,4096 output tokens,16 concurrent requests,
  three independent judge repetitions; up to180 reviewed variants per round.
- Round1 cap $10; total six-question two-round ceiling $20. Round2 needs explicit
  review/agreement and is not authorized for dispatch by the current instruction.
- First20 variants span all10 points, both labels, distributed and mixed-conflict
  families:60 slots included in Round1. Inspect this checkpoint before continuing.
- Native timeouts120 seconds/request,45 seconds/attempt,150 seconds/sample;
  at most two transport retries; no semantic retries or replacement judgments.
- Pause after the checkpoint for at least two operational failures or the same
  clear rule failure on two distinct variants. Immediately stop new dispatch for
  isolation/identity defects, unsupported settings, accounting failures, inability
  to reserve liability, authentication or repeated run-level operational failures.
- Proposed expansion gates:98% valid slots;95% sensitivity and specificity among
  valid slots;95% variants with three valid agreeing judgments; no unresolved
  systematic distributed/omission/conflict error. Review every exception.
- No real-answer diagnostics, additional13 authoring, test tuning, reserved
  challenges, MiniMax, reference changes or historical rescoring in this run.
- [Pilot execution specification](../../docs/specs/task15y_pilot_v1.md) owns
  the agreed ablations, budget and provenance details.

## Abstract and goal

Add a separate diagnostic judge to distinguish required answer content absent
from the supporting points from content present there but omitted
from the conclusion. Each required reference point gets its own independent
binary judgment. This supplements C, S and G; it does not replace them or add an
overall benchmark pass requirement.

This is follow-up1 of3:15Y, then15Z citation review, then
[15AD final end-to-end run](15ad_final_end_to_end_run.md).

## Inputs

- Approved structured references: `docs/specs/task15ac_reference_result.json`.
- Selected saved answers: `docs/specs/task15t_retry_result.json`; high-reasoning
  experiment separately selected by `docs/specs/task15w_haiku_16k_retry_result.json`.
- Preserve canonical required-point IDs when joining diagnostics;15AC provides
  reversible sequential wire-ID mappings for C. C034 has a new question, so older
  answers must be labeled historical-question diagnostics, not current-version results.
- Current judge contracts and adapters via `docs/judge_maintainer_guide.md`.
- Task15X review and discussion: C032 Haiku repeat2 contains required detention
  replacement in S4, accepted by G, but omits it from its conclusion. S passes;
  G fails a separate qualification Q3. This is an exposed diagnostic example.

## Proposed contract and outputs

One request per required reference point, containing the shared project overview,
question, that one required point, and all candidate supporting points with IDs.
Do not expose the candidate conclusion, other judges' verdicts, source passages,
reference support prose or optional reference points. Supporting points may jointly
convey the required meaning. The initial scope is supporting_points only; separate
qualifications and optional_context do not silently enter this coverage check.

Return `covered: true/false`, supporting-point IDs and a concise reason. Binary
false includes missing, incomplete or incompatible coverage; do not introduce a
third semantic label. Accept equivalent meaning without incidental wording.
Mixed correct/conflicting support is false; false outputs have empty supporting IDs. Invalid
outputs and unavailable calls remain operational states, never false labels.

Produce a versioned general rule/prompt/schema, narrow existing-runner integration,
bounded development validation and an identity-bound diagnostic report. Join each
required point to C's corresponding point judgment, preserving C missing versus
contradicted, and to relevant G results without equating coverage with grounding.
Report support-covered/C-missing separately from support-not-covered/C-missing and
other combinations. Do not infer missing source knowledge merely from missing
response content. Keep candidate repeats distinct from judge repeats.

## Research / learning checkpoint and plan

Inspect maintained C/S/G contracts and native adapter reuse before selecting the
smallest implementation. Explain coverage versus source grounding, inference
support and conclusion adequacy. Review binary semantic-coverage evaluation
practice using primary documentation before implementing; record the chosen
approach without creating a new framework.

## Agreed development sequence

Start the new chat with contract discussion, then proceed through these stages.
Do not skip directly to implementation or synthetic generation.

1. **Establish inputs and outputs.** Confirm the one-required-point request,
   supporting-points-only boundary, binary result, supporting IDs and reason.
   Pin the approved reference version and distinguish semantic decisions from
   invalid or unavailable outputs.
2. **Establish judging rules.** Agree on equivalent meaning, partial coverage,
   coverage spread across supporting points, necessary scope/qualifications and
   mixed correct/conflicting claims. Keep coverage distinct from source grounding.
3. **Establish the prompt and schema.** Encode the agreed rules with the shared
   Baylands overview. Review them before implementing narrow existing-runner
   integration; keep real and synthetic input composition identical.
4. **Define synthetic ablation families.** Specify what each transformation tests
   and its expected binary result. Include complete coverage, paraphrase, split
   coverage across multiple supporting points, partial or removed coverage,
   unrelated supporting content, incompatible claims and mixed correct/conflicting
   support. Define combined defects explicitly where useful. Resolve ambiguous
   expectations before calls rather than assuming every mutation must fail.
5. **Create per-question/per-required-point ablations.** Keep each question and
   required reference point fixed; perturb only candidate supporting points.
   Preserve coherent point IDs and record source variant, transformation and
   expected label outside the judge payload. Cover each required point, with
   explicit exclusions for inapplicable transformations. Independently review
   expected positives and negatives; do not author labels from judge predictions.
   Start with the six-question pilot; author the additional13 after pilot review.
6. **Test on the six-question development subset.** Use C014, C017, C019, C037,
   C041 and C056 from the approved development split. Freeze the suite and exact
   rules/prompt/schema for each run. Record model, reasoning, judge repetitions,
   concurrency, output limits and numerical budget before dispatch.
7. **Review and cycle on the six.** Examine false positives, false negatives,
   invalid outputs and repeatability. Distinguish judge errors from ambiguous
   expectations or contract defects. Discuss substantive rule changes; version
   revisions and retain earlier results. Recheck unaffected controls as well as
   failures; do not silently relabel a completed run or optimize only pass rates.
8. **Expand to all19 development questions.** After the pilot is accepted for
   expansion, apply the agreed families to required points in the additional13,
   review and freeze those ablations, then test the19-question suite. Report the
   original six and additional13 separately as well as combined.
9. **Review and cycle on the19.** Repeat the same error analysis and versioned
   iteration process, then agree on remaining limitations and the selected judge.
   Publish the contract, reviewed synthetics and qualification results for15AD.
   Applying the judge to real saved answers is a separately declared diagnostic
   population; synthetic qualification does not implicitly authorize all49 runs.

Both stages are development: the six are a subset of the19, and neither is an
untouched validation set after iteration. Do not open reserved challenges or use
test questions to tune this judge. The goal is reliable semantic coverage
judgment, not a particular score. Retain clear remaining disagreements rather
than extending the cycle indefinitely without a selected next step.

Specify models, numerical budget, concurrency, population, repetitions and stopping
conditions before any paid dispatch, including the allowed iteration scope.
The explicit activation and approved settings above govern the six-question
Round1 only. Historical spending approvals do not extend this allowance.

## Validation, review and acceptance

- Verify one required point per request and isolation from C verdict/conclusion.
- Test schema, point IDs, semantic controls, exact identity joins and restartability.
- Conduct a bounded independent rule/implementation review; run appropriate
  `make fix`, `make check` and `git diff --check` after implementation.
- Save new artifacts beneath a fresh Task15 namespace, completion-last with
  provenance and a compact result pointer. Report disagreement and limitations.
- Overall scores remain unchanged. Coverage of a disputed required label does not
  settle whether that label should be mandatory.15AA resolved C017 storage as optional
  and removed VMT from C014; consume the published decisions, not older proposals.

## Non-goals

The initial task-writing and discussion turns authorized no implementation or calls;
the current activation above now authorizes the six-question Round1 work.
No label, C/S/G, target-prompt or historic-score changes; no new target generation,
MiniMax, reserved challenges, commits or pushes. Task16 remains separately gated.

## Outcome: initial Round1 checkpoint stopped (2026-10-23)

Implemented the approved core, native Inspect adapter and bounded six-question
runner.150 fixed-reference variants (70 positive/80 negative) cover all15 agreed
families across10 required points. Separate agents reviewed every expected label
and the implementation/runner before the inputs were frozen. The
[result pointer](../../docs/specs/task15y_round1_result.json) selects the stopped
attempt and its report; it is not a completed qualification result.

The first60-slot checkpoint sent16 requests before the first fatal400 response
stopped further dispatch. Luna rejected the runner's explicit
`prompt_cache_retention=in_memory`: the provider requires24h extended prompt caching.
All16 in-flight requests received that configuration error;44 further checkpoint
slots were blocked locally. The remaining390 Round1 slots were not started.
No semantic labels, false positives/negatives or sensitivity/specificity were obtained.
Inspect's native task status `success` means its logging loop ended, not that the
judge succeeded; the task result explicitly records operational failure.

The full conservative $6.413157 reservation remains held against Round1's $10 cap.
Provider usage was absent, so billed cost is unknown, not zero. No semantic or
operational retry, remainder or Round2 was dispatched. The exact code snapshot,
native logs,16 wire requests, planned-slot results and independent failure review
are retained beneath the fresh15Y external namespace. Frozen references/releases,
historical results and all original expected labels remain unchanged.

Validation: `make fix` and `make check` passed (4582 tests passed,1 skipped);
after final runner changes, all26 focused coverage tests, mypy and diff checks passed.
Mocks verified isolation/budget/stop behavior but did not establish live cache-mode
compatibility. Learning: pinning an optional provider control requires model-specific
live compatibility evidence; a correct request shape is not sufficient. The
fail-closed guard limited the incident to the already admitted16 requests.

Next review: use provider-required24h caching in a versioned operational continuation,
retain the same semantic prompt/schema/synthetics, and account for the original16
uncertain attempts within the existing dollar/attempt ceilings. Preserve this failed
checkpoint rather than overwrite it or reset budget in a fresh unlinked namespace.
No continuation or Round2 is authorized by this outcome record.

## Outcome: authorized continuation completed

The user subsequently authorized24h caching and continuation under the original
$10 cap. The [continuation result](../../docs/specs/task15y_round1_continuation_result.json)
selects the sealed successor; the stopped result above remains unchanged. All150
synthetics, labels, references and semantic prompt/schema are byte-identical.

The corrected checkpoint produced60 valid/correct judgments and passed independent
review. The390-slot remainder then completed without provider errors or retries.
Overall450/450 judgments were valid;442/450 matched frozen expectations (98.22%).
Sensitivity208/210=99.05%; specificity234/240=97.50%;149/150 variants had three
valid agreeing repetitions (99.33%). All numerical gates passed, but semantic
review remains unresolved for the following cases:

- C017/R1 distributed-gap: three false positives against the frozen negative;
  independent review identifies expectation/contract ambiguity. The subtraction is
  explicit, but the required net-grid-demand endpoint is not named. Discuss ordinary
  semantic implication versus a material omission before changing a future suite.
- C041/R2 distributed-gap: three false positives. Generic animal-control enforcement
  lacks the required deed-restriction instrument; the judge supplied that detail.
- C041/R2 distinguished-scenarios: two false negatives, one correct. The judge
  inconsistently treated a claim explicitly about a different development as conflicting.

All eight mismatches retain their original labels/scores. Independent review covered
every exception and correct controls from all15families. No semantic retries,
majority-vote repair, label changes, real-answer diagnostics or C/G joins were run.
The suite is formulaic exposed development material; do not claim held-out reliability.

Accounting:450 continuation wire attempts plus16 original rejected attempts=466,
with no continuation retries. The original54-file seal remains intact. Prior uncertain
liability$0.076253 is retained; provably unsent reservations were reassigned within
the unchanged$6.413157 total reserve, below$10. Conservative continuation usage
estimate$0.15529325 excludes prior uncertain charges; provider billing is not verified.
The accounting audit checks disjoint input/cache token counts and every wire payload.

Validation: `make fix`/`make check` passed (4588 tests passed,1 skipped),29 focused
tests passed, independent code/accounting/checkpoint/postrun reviews completed,
and diff checks passed. No commits/pushes. Round2 and all19 expansion have not started.
Next: discuss these three variants, then explicitly agree on any revised contract,
synthetics or further dispatch. Do not automatically expand based on pooled gates.

## User adjudication after Round1

[Approved adjudication overlay](../../docs/specs/task15y_post_round1_adjudications_v1.json)
records decisions for the next suite without modifying sealed Round1 inputs/results:

- `C017_R1__distributed_gap`: accept coverage=true; the stated subtraction conveys
  the required meaning without explicitly naming net grid demand.
- `C041_R2__distributed_gap`: retain coverage=false; the deed-restriction detail
  remains missing.
- `C041_R2__distinguished_scenarios`: remove from future qualification. The user
  rejected the unnamed different-development example as confusing. This excludes
  that exact variant, not the whole family. Do not use its two negative judgments
  as strong evidence of judge failure or silently substitute a new example.

No revised suite, replacement example, rescoring or Round2 dispatch has been made.
The next step requires agreement on any further authoring, prompt changes or run.


## Outcome: all19 synthetic preparation (2026-10-23)

The user accepted the six-question judge and authorized expansion authoring/review,
with a budget proposal before calls. The [all19 proposal](../../docs/specs/task15y_all19_preparation_v1.md)
records585 reviewed variants across19 questions/42 required points:436 additional
variants and149 carried with the exact adjudications. Cross-review removed six
ambiguous negatives and revised two others;44 new family exclusions plus the user's
one exclusion are explicit. The judge/prompt/schema remain unchanged.

The proposed single round contains1,755 judgments with three repetitions,
16 concurrency,4096 tokens,24h cache and a new$30 cap; exact conservative maximum
reservation$24.97518 includes all allowed retries. No model calls are authorized
or made during preparation. The six-only runner still needs a bounded extension,
independent review and validation after budget agreement and before dispatch.
No commits/pushes. Frozen references, failed attempt, continuation and original
budget/liabilities remain preserved. This suite is exposed development calibration.


## Outcome: approved all19 round completed

The [sealed result](../../docs/specs/task15y_all19_round1_result.json) records one
fresh585-variant round. Independent runner/input/budget review and `make fix` /
`make check` passed (4,593 tests passed,1 skipped) before dispatch. The252-judgment
checkpoint was fully valid and matching; independent semantic/wire review approved
continuing. The1,503-judgment remainder completed with no transport retries/errors.

All1,755 judgments are valid;1,749 match frozen expectations (99.66%). Sensitivity
786/786=100%; specificity963/969=99.38%;582/585 variants have three agreeing valid
repetitions (99.49%). Original six:444/447 match (99.33%); additional13:1,305/1,308
match (99.77%). No historical predictions are pooled into this fresh result.

All six errors are false positives on distributed-gap negatives: C041/R2 in all
three repetitions and C006/R3, C045/R2 and C050/R2 in one repetition each. Independent
review retains all four expected false labels. C006/R3 and C045/R2 return true while
their reasons acknowledge the missing material detail; they remain valid semantic
errors, not operational failures. The known C041 deed-restriction omission persists.
Negative distributed-gap specificity is105/111=94.59%, an unresolved material-omission
weakness despite passing aggregate gates. No prompt/label revisions were made.

All1,755 wire requests were independently audited against exact payloads, schemas
and settings. Conservative saved-usage estimate$0.60883875 is not provider billing;
full$24.97518 reservation remains under the approved$30 cap. The earlier$6.413157
pilot reserve, including$0.076253 uncertain liability, is separate and preserved.
The round is sealed and stopped for user review, with no second round or real-answer
diagnostics started. Coverage remains diagnostic, separate from grounding and
benchmark overall pass. No commits/pushes.

Learning: aggregate agreement can hide a focused omission weakness. Preserve
per-family results and verdict/reason inconsistencies, without silently correcting
model outputs or relabeling expectations after observing predictions.


## Outcome: code-quality pass

The user required a maintainability pass before final approval. The
[quality result](../../docs/specs/task15y_quality_result.json) binds the independent
review, offline equivalence audit and code snapshot. Core and native adapter remain
unchanged: they were already small and cohesive. The runner now shares seal checking
and request-budget arithmetic, separates population validation, phase authorization
and judgment-row normalization, and names fixed execution limits. `prepare` shrank
from125 to72 lines and `execute` from175 to82; no new modules, dependencies or generic
workflow abstractions were introduced. Make targets share one recipe per operation.
The maintainer guide maps each responsibility to its owning function.

One operational-record bug was corrected: a native failure with stale evaluated
score metadata now reports unavailable, with null coverage. Tests cover failed,
missing and duplicate result slots. This changes no saved valid judgment.

Independent review found no remaining blockers. Offline replay verified all585
inputs,1,755 parsed saved outputs,1,755 native request records and1,755 reconstructed
result rows against sealed snapshots;20 rejection controls and the$24.97518 budget
bound match. Both prepared/run inventories remain intact. The current runner
correctly rejects old manifests whose code hashes differ; historical snapshots
remain available for offline inspection, not renewed dispatch.

`make fix`, `make check` (4,594 passed,1 skipped), and `git diff --check` pass.
No model calls, commits or pushes. Task15Y remains open pending final user approval;
this pass neither changes the known omission limitation nor starts15Z/15AD.


## Final acceptance and handoff

The user accepted the completed code-quality pass and explicitly instructed marking
15Y complete, publishing the handoff and committing the code. The
[machine-readable handoff](../../docs/specs/task15y_judge_handoff_v1.json) pins exact
semantic/code hashes and the approved-reference, reviewed-suite, all19-result and
quality-audit completion seals. Its accepted status supersedes earlier pending
approval metadata; no historical result or frozen artifact was rewritten.

The diagnostic judge is selected with its documented omission limitations. Further
synthetic iteration is not required for this accepted task.15AD owns the remaining
real-answer execution/projection and C/G diagnostic report integration after15Z;
this closeout neither claims those integrations are implemented nor activates them.
Validation remains4,594 tests passed,1 skipped, independent review and full offline
saved-result equivalence; closeout also checks handoff hashes and documentation.
Next: separately activate15Z. A local commit is authorized; push remains unauthorized.
