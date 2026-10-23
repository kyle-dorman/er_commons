# Task15O — Candidate IDs without explicit contradiction-pair output

Status: complete; awaiting user discussion (2026-10-22).

## User request and scope

The user asks whether numbered candidate statements alone explain the observed
improvement. Keep candidate A IDs, remove `contradicting_points` instructions and
output, and rerun only contradicting candidates. Use all65 Task15N candidates
whose reviewed expected pair list is nonempty; selection is independent of model
success/failure. Both judges, three rounds each, concurrency16/model, medium
reasoning:390 planned calls. Every selected candidate is expected to fail, so this
bounded diagnostic measures contradiction detection, not specificity or general
accuracy on compatible answers. Preserve original candidate text, numbered spans,
questions, R/O references, original statuses/Booleans and historical results.

## Plan

1. Publish a hash-bound subset of the sealed Task15N suite; no new synthetic text.
2. Add opt-in v5 using the same input as v4 but no pair-output field or pair-reporting
   instructions. Retain whole-answer scanning, contradiction precedence, every
   optional judgment, shared overview and independent model-final/point aggregate.
   Reference-point contradiction checks remain; content outside R/O coverage is
   not given a new catch-all judgment. Preserve v1–v4 and frozen defaults.
3. Validate schemas/native parity and predecessor stability, review code and runner
   independently, and run make fix/check plus offline execution/accounting tests.
4. Run the390 slots under the original shared$20 cap. Prior cumulative conservative
   liability is$15.1200905; available liability is$4.8799095. Bind the prior seal,
   reserve before each chunk and stop rather than exceed the cap. No semantic retry.
5. Compare saved v3/v4 and fresh v5 on precisely these65 candidates: model-final,
   deterministic point aggregation, reference contradiction recall, full vectors,
   validity, repeated outcomes, costs and latency. V3 final-consistency rejection
   is separated from structural validity for the comparison, with old scores intact.
   Review every new failure and changed verdict; seal a report with honest limits.

## Interpretation and boundaries

This ablates explicit pair reporting/instructions relative to v4. It is not a pure
v3-versus-v5 statement-ID-only causal test, because v4/v5 also retain clearer scan
and completeness instructions introduced after v3. Runs are stochastic and historical
comparison calls are not newly randomized simultaneous controls. No pair metric is
computed for v5. Ten selected candidates had ambiguous exhaustive pair inventories
in Task15N but each has at least one reviewed definite pair; all65 retain their
original reference/overall labels.

No production promotion, A/G/S changes, reference edits, fresh generation, MiniMax,
reserved challenges, commits or pushes. Task15N's broader findings and disputed
interpretations remain separately recorded. Review is based on existing maintained
Inspect adapter/schema contracts; prefer narrow versioned changes and artifact glue.

## Outcome

All390 calls completed with no retries, invalid outputs, or model-final/point-aggregate disagreements. Luna and Haiku each correctly rejected195/195, matching v4 on the exact65 selected candidates. Thus explicit pair reporting showed no overall benefit on this subset. It does not isolate IDs as the causal improvement over v3 or establish false-rejection performance.

Point-level effects were mixed: Luna detected309/327 expected contradicted reference points versus316/327 with pairs; Haiku detected307/327 versus301/327. Complete-vector agreement was161/195 Luna and164/195 Haiku. All68 exceptions (65 vector mismatches plus3 quote-only diagnostics) are reviewed in the result publication; no expected labels were changed. The flooding C056-CP-01 failure stayed fixed, while a secondary numerical contradiction was still missed in Haiku C056-CD-04 round3 despite a correct overall rejection.

Configured cost estimate$0.256519055; conservative new liability$1.493130675, cumulative$16.613221175/$20. Runtime189.36seconds. make fix/check:4517passed,1skipped;12 offline runner tests and independent dataset/runtime/runner/result audits passed. The [result pointer](../../docs/specs/task15o_structured_judging_result.json) selects the sealed report, comparison and exhaustive exception review.

No default promotion, further calls, commits or pushes. Discuss whether the simpler representation should receive a broader compatible-answer check before adoption. Task15N's full-suite findings remain authoritative for its separate experiment.
