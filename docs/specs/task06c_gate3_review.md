# Task 06C Gate 3 preparation review

Independent source-free review covered the retained-source processing adapter,
source-role and resolver integration, background supervisor, prepared Final F1
configuration, chunk policy, tests, and model-remediation proposal.

## Result

No outstanding blocking implementation findings in the prepared scope. Gate 3
execution remains blocked by the missing verified model inventory and missing
TableFormer payload at the inspected locations. No conversion, model loading,
source-PDF reading or hashing, network request, or production launch was
performed by this review. This is preparation review, not Gate 4 acceptance.

The retained adapter checks the externally pinned completion digest, exact
receipt membership and member seals, evaluator implementation digest, reproduced
disposition, diagnostic references, acquisition snapshot and unchanged source
metadata. The new manifest keeps the physical Final F1 source and the F1-only
substitution provenance explicit. Both maintained source resolver families route
the qualified substitute through this verification without a source-PDF hash;
ordinary model-corpus behavior remains unchanged. These are compact evidence
checks, not fresh byte-equality claims.

The fixed-size policy matches the maintained planner: four contiguous core
ranges covering all 756 pages, target 200, hard maximum 250, one boundary overlap,
four CPU threads including TableFormer fallback, and 10 GiB / 3,600-second child
limits. The outer supervisor supplies total runtime, output and swap ceilings,
initial disk checks, durable status, and cleanup of observed descendants even
when workers start separate process sessions. Model readiness and final
identity-bound plan publication must precede launch.

## Findings resolved before close

- Final output-accounting errors could previously prevent terminal status and
  leave signal handlers altered. Final accounting now records a failure and
  restores handlers after terminal publication.
- Blanket rejection of output symlinks conflicted with maintained chunk-range
  links. Contained links are now allowed without double-counting their targets;
  links escaping the accounting root fail with retained terminal evidence.

Independent validation after these changes:

```text
uv run pytest tests/test_retained_processing.py tests/test_background_execution.py -q
25 passed in 1.71s
```

The synthetic coverage includes forbidden PDF reads, damaged receipt seals and
closure, evaluator changes, source metadata changes, source-role isolation,
resource stops, detached descendant cleanup, contained range links, and external
link accounting failure. Full repository checks belong to the task outcome.
