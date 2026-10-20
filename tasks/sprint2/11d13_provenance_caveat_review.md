# Task 11D.13 — Provenance-caveat occurrence and failure review

Status: Complete (2026-10-19); offline analysis and requested working-prompt promotion.

## Abstract, goal and inputs

The user accepts the 11D.12 focused conclusion check as the working prompt and
requests a deep dive into provenance-caveat occurrence and related failures.
Record the acceptance without rewriting sealed experimental results, then audit
saved answers and actual input/judge visibility. No new model calls or prompt
changes are authorized by this analysis.

Inputs: accepted 11D.12 prompt/outcome and result pointer; sealed 11D.9 baseline,
qualification, summary and conclusion arms; 11D.10 qualification examples and
11D.12 focused check for C041, both models twice (24 answers). Scan only existing
fixed-six candidates in 11D.9–11D.12 for non-C041 provenance doubts, distinguishing
those from ordinary uncertainty, implementation status and input-layout issues.
Read C041 source packets, neutral locators, summary envelopes and frozen judge
rules as needed. Do not inspect other development or held-out/reserved content.

## Plan and research / learning checkpoint

Publish a hash-bound working-prompt selection referencing exact 11D.12 text and
its historical result; retain the previous no-promotion recommendation as dated
experiment history. This selection does not invent an all-19 validation or begin
11E. Qualification and citation rewrites stay set aside.

Define provenance caveat before counting: an explicit doubt that supplied material
belongs to, governs or applies to the requested project. Record source-authority
or applicability doubts separately from geographic scope, forecast uncertainty,
implementation uncertainty and table-reading issues. Count occurrences by answer,
field and condition, not merely failed judges. Audit whole answers, exact identities
and original C/S/G decisions. Verify source visibility and distinguish a supported
observation about excerpt text from an unsupported inference about applicability.

The learning question is whether trusted input context, passage-level source
metadata or generation instruction should own this ambiguity. Assess the already
run summary intervention before proposing more prompt rules. Do not change judge
policy or dismiss a model concern solely because a reference answer omits it.

## Outputs, validation and review

Tracked: working-prompt selection, task outcome and current routing. External
analysis: pipelines/brisbane_baylands/task_11/provenance_review_20261019, with full
coverage/identities, exact quotations, source/judge comparisons and limitations.
Two bounded independent reviews cover occurrences and source/judge semantics; a
third checks whether the phenomenon extends beyond C041 within the fixed panel.
Verify counts and quoted spans against saved candidates and source bindings.
Docs-only validation uses git diff --check. No paid calls, costs or retries.

## Acceptance and non-goals

Record requested promotion and report where provenance doubts occur, how they
interact with C/S/G, what the summary experiment changed, and minimal next options.
Keep observed associations distinct from causal claims from two unseeded repeats.
No automatic next experiment, new examples, evaluator changes, Task10 edits,
held-out maintenance, new questions/models or11E.

## Outcome (2026-10-19)

The user-selected 11D.12 focused conclusion check is now the working prompt,
bound by docs/specs/task11_working_prompt.json. This supersedes the earlier
experimental no-promotion recommendation without changing its sealed evidence.
Qualification/citation additions remain excluded. No all-19 qualification or11E
is claimed. This follow-up used no provider calls.

Reviewed all24 C041 answers across six conditions and scanned all84 other fixed-
panel outputs from 11D.9–11D.12. Core project/document applicability doubts were
found only in C041: Luna0/12 and Haiku7/12. Outside-C041 findings concern related
but distinct verification, adoption, source-scope or unsupported-inference issues.

| Condition | Haiku provenance caveats | Haiku C passes |
| --- | --- | --- |
| V6b baseline | 2/2 | 1/2 |
| Qualification rewrite | 0/2 | 1/2 |
| Generic project summary | 1/2 | 1/2 |
| Previous conclusion check | 2/2 | 1/2 |
| Qualification examples | 0/2 | 2/2 |
| Accepted focused check | 2/2 | 0/2 |

Luna has zero provenance caveats and C2/2 in every condition. The qualification
variants' local success does not reverse the user's decision to set them aside;
their other questions had documented regressions. Two unseeded repeats cannot
establish causal occurrence rates or prove the focused check created the caveat.
It already appears in both baseline Haiku answers; its field location changes.

All seven provenance qualification points pass G: P1 actually does not name
Baylands. Five answers also place this doubt in the conclusion; four fail C for
withholding the feeding-station measure's project applicability. Both answers with
provenance caveats only in qualifications pass C. These are field-specific results,
not evidence that moving a problem out of C makes an answer correct. Six of the
seven caveat-bearing answers pass S; both accepted-prompt Haiku answers pass S
while failing C. Support can establish the model's qualified claim while C finds
it inconsistent with the reference's substantive project answer.

One exception matters: shared-summary repeat2 notes non-naming in the conclusion
and says applicability relies on passage context rather than an explicit statement;
C passes. Stronger doubts in other outputs fail. This is a materiality/wording
threshold issue, not a uniformly scored binary provenance error. Preserve original
judgments; do not silently relabel them.

Actual input visibility explains the model concern. P1 title is generic EIR
Appendix A: FEEDING STATIONS; its text specifies occupant restrictions, MPOA
monitoring and fines, but does not name the project. P2 explicitly names Baylands.
The generic project summary describes Baylands' location and uses but never binds
the supplied appendix to that project. It therefore does not directly resolve the
provenance question. The source catalog identifies deir_appendix_a, document559,
with expected label Appendix A - 2025 Baylands Specific Plan (PDF), and main
source530 as Complete 2025 Baylands Specific Plan DEIR (PDF). This is verified
repository-catalog linkage, not a newly verified PDF/download-content claim.
Neutralized passage titles omit that project name. No source text or metadata was
changed in this task.

Related failures are distinct: shared-summary repeat1 has no provenance caveat
but asserts enforcement responsibility is unresolved because HOA and MPOA are
not shown identical, despite separately specified responsibilities. Other outputs
question adoption or actual enforcement, claim lack of independent verification,
or infer that closure-design review makes modeled groundwater results preliminary.
A common-project statement addresses document identity, not these substantive
claims. Legitimate agency requirements, scenario distinctions and source conflicts
must remain available as qualifications.

Preferred next option, not implemented: test minimal explicit provenance context
with the accepted prompt, such as "The supplied passages are from the Baylands
project's environmental-review documents." Bind it to verified source membership;
apply the same context to relevant judge envelopes without retuning judge cores.
For future retrieval with mixed documents, per-document project provenance is more
precise than assuming all retrieved documents share a project. Do not restore
edition/finality claims or imply every provision is adopted, implemented or
universally applicable. The alternative is preserving project identity in neutral
source titles. Avoid changing both mechanisms in one test.

Validation: exact quoted occurrence spans checked against all24 saved candidates;
working-prompt and historical-result hashes verified; independent occurrence,
source/judge and outside-case reviews retained. Docs-only git diff --check passes.
External detailed artifacts live under provenance_review_20261019 and are bound by
[the result pointer](../../docs/specs/task11d13_result.json). No paid calls, retries,
judge changes, other13 cases, held-out content, Task10 edits or11E.
