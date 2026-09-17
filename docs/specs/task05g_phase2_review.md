# Task 05G Phase 2 implementation review

Scope: source-free implementation and synthetic validation only, authorized by
“run phase 2 and stop.” The accepted repository base remains `6c95803`.
The [task contract](../../tasks/sprint2/05g_replay_and_extend_official_reference_links.md)
owns policy and future authorization gates; the
[resolved packet](task05g_phase2_launch_packet.json) is a read-only preview,
not an execution receipt or acceptance.

## Review and remediation

An independent review examined versioned consumer bindings, resolver semantics,
comparison closure, checkpoint restart, resource supervision, publication gates
and maintainability. Material findings were remediated:

- Normalize the accepted physical Final F1 catalog entry to the logical Draft
  identity only after exact handoff/registry substitution verification. Positive
  physical/logical catalog controls agree; mismatched bindings fail.
- Route all public v6 prepare/build/compare/validate commands through the
  supervisor; return a nonzero CLI exit status for terminal execution failure.
- Exercise later finalization/acceptance gates with synthetic successful,
  conflicting, incomplete and idempotent cases. Independently test verification
  of original launch request bytes, command, resource bounds and terminal receipt.
- Exercise actual harmless subprocess timeout and output-cap termination, plus
  a synthetic 511-reference resource probe.
- Document one all-stage launch, explicit attempt/resume selection, disjoint
  supervisor logs counted within the cumulative cap, validation's operational
  writes, and separate Phase 5 publication/resource review.

Final independent verdict: **PASS, no open material findings**. The reviewer
regenerated the resolved packet read-only and confirmed an exact match, current
code/schema bindings, false authorization flags and absent output namespaces.
The minor packet-key documentation correction (`launch_command`) is applied.
This verdict covers Phase 2 only and does not authorize replay.

## Validation and limits

All **152 focused Task 05G tests pass**. `make fix` passes. `make check` passes formatting, Ruff and mypy (538 source
files); pytest reports **2,257 passed, three failed**. All three failures reproduce
from an isolated export of accepted commit `6c95803`, with that export's source
and tests and the same HEAD identity:

- `test_collection_generator_preserves_historical_v38_owner_packet`
- `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`
- `test_task06g_templates_are_executable_and_source_free`

These tests expect `generator differs: ...finaliz`; the historical recipe first
rejects `Task 06G repository base commit differs from the accepted basis`.
Preserve that historical recipe, code and evidence; Phase 2 does not rewrite
them to turn the existing failure green.

The checked-in v6 request passes `er-responses validate-spec`; its behavior
SHA-256 is `b1b2faa1d3c0d43aa0b6af18266487b27deda8fc0150d8101c87a78a994aefff`.
The resolved preview is 23,262 bytes, below the 64-KiB launch-packet bound.
All three authorization flags remain false. Neither external `working/05g`
nor `working/05g_execution_attempts` exists after validation.

Synthetic results establish implementation behavior, not successful corpus
replay or substantive Draft/Final equivalence. Phase 3 requires separate user
authorization and a refreshed exact prelaunch packet. Before Phase 5, separately
review publication commands and their resource packet; the Phase 3 receipt
cannot attest to resources used by later recomputation/publication.
