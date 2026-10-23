# Task15Y accepted judge handoff

Task15Y is complete. The user accepted the all19 results and subsequent code-quality
pass, and explicitly approved closeout and a local commit on2026-10-23.
The [machine-readable handoff](task15y_judge_handoff_v1.json) selects the judge,
code hashes, reviewed synthetics, results and validation evidence. This acceptance
supersedes pending-approval statuses in historical result pointers without rewriting
their sealed evidence.

## Selected judge

Use `gpt-6-luna`, medium reasoning, with
`task15y.required_support_coverage.v1` and the unchanged shared Baylands overview.
One request contains the exact question, one canonical required reference point,
and candidate supporting-point IDs/text. Return `covered`, `supporting_point_ids`
and a brief `reason`. True requires sufficient supplied supporting IDs; false
requires an empty list. Equivalent and jointly distributed meaning counts; missing
material content or unresolved conflicting claims does not.

The judge sees no conclusion, other verdicts, other reference points, source evidence,
citation metadata or separate qualifications. Coverage remains distinct from grounding
and **does not add an overall pass requirement**. Invalid or unavailable outputs
remain operational non-decisions.

## Implementation and evidence

- `required_support_coverage.py`: prompt/schema and strict input/output validation.
- `required_support_coverage_inspect.py`: native isolated request/scorer integration.
- `required_support_coverage_run.py`: bounded synthetic execution, identity checks,
  checkpoint approval and accounting; not a general real-answer runner.
- [Maintainer guide](../judge_maintainer_guide.md): ownership and editing instructions.
- [Approved references](task15ac_reference_result.json): exact questions/canonical IDs.
- [Reviewed suite](task15y_all19_preparation_result.json):585 variants,42 points,19 development questions.
- [All19 result](task15y_all19_round1_result.json):1,755 valid judgments,1,749 matches,
  sensitivity100%, specificity99.38%, repeat agreement99.49%.
- [Quality audit](task15y_quality_result.json): independent review,4,594 tests passed,
  one skipped, and offline equivalence for every saved judgment and request.

The successful qualification used4096 output tokens,16 concurrency, three judge
repetitions, explicit24h caching, default service tier,120-second native timeout,
45-second attempt timeout and150-second sample limit; SDK retries disabled and at
most two transport retries. These settings describe the selected qualification.
Future run population, repetition policy, pricing and budget need explicit activation.

## Accepted limitations

Six false positives remain across four distributed-gap variants: C006/R3, C041/R2,
C045/R2 and C050/R2. Missing material details can be overlooked; negative
distributed-gap specificity is94.59%. Two true verdicts acknowledge the omission in
their reasons. Retain those errors and labels; acceptance does not repair or rescore
them. The suite is exposed, partly formulaic development material, not evidence of
held-out reliability. All49 references have curation exposure.

## Downstream ownership

Task15Z is next, separately activated. Task15AD consumes this accepted judge after
pinning15Z's approved successor references (or explicitly retaining15AC). Revalidate
coverage synthetics affected by reference changes.15AD owns real-answer projection,
execution and report joins to corresponding C/G results, including
support-covered/C-missing versus support-not-covered/C-missing. Preserve canonical
point IDs, candidate identity and answer repeats separately from judge repeats.
Those end-to-end integrations and real-answer diagnostics were not executed in15Y.

Do not rerun sealed experiments: their manifests bind their original code snapshots.
The quality-refactored runner correctly rejects changed historical code hashes.
Prior spending and uncertain liabilities remain preserved; no allowance transfers
into15Z/15AD. MiniMax stays excluded and reserved challenges unopened. This handoff
authorizes no further model calls or push.
