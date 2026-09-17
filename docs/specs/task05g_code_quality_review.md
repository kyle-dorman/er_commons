# Task 05G human-maintainability review

**Outcome: passed for the bounded MVP scope.** The current code is easier to
trace and edit, and full-population verification found no changed link behavior.
This is a code-quality review, not finalization or acceptance of Task 05G.

## Changes made

- Split resolver routing, guarded candidate selection and header qualification
  into named responsibilities. The main function now presents rule order before
  record construction. Preserve inherited matching semantics and authorship gates.
- Replace positional resource/candidate/proposal construction with named fields,
  making source, evidence, rule and warning arguments explicit.
- Extract selected-index verification and section-child loading from the long
  mechanical reader. Share canonical stream loading at one documented inventory
  verification boundary rather than duplicate it for table/page and header rules.
- Isolate source qualification selection from matching, and centralize the policy
  set that enables the existing inner rules. A source selected for I/O does not
  thereby become eligible for a link.
- Add stage start/completion/failure and checkpoint reuse logs. Errors identify
  malformed JSONL file/line, missing canonical stream, checkpoint root/mismatched
  fields, or changed mention/fields rather than requiring a maintainer to guess.
- Add a bounded read-only refactor verifier and a
  [maintainer guide](task05g_maintainer_guide.md) covering code ownership, one-mention
  diagnosis, restart failures and identity handling.

No dependencies, generic rule framework, new linking policy or document-specific
exceptions were added. Accepted Task 05F/06G/06H code and evidence remain intact.
The pure inner parser, header/table/page qualification, comparison and acceptance
modules were inspected; no broader restructuring was justified for this MVP.
JSON remains at artifact boundaries; narrow existing dataclasses carry runtime
resources instead of adding another schema framework.

## Review and verification

Bounded agents implemented the resolver and input-reader refactors; the parent
integrated and inspected both. A separate pass by `maintain_resolver` reviewed
the input/mechanical refactor and parent workflow/spec/storage/cycle changes,
returning PASS. It identified one gap in the new audit script: payload roots
were not explicitly tied to the checkpoint seal paths. The script now verifies
root association, candidate ID, each stage/request identity and dependencies
before comparing bytes. Follow-up independent review confirmed the finding
closed, with no material issues outstanding.

The [equivalence report](task05g_quality_equivalence.json) binds the exact current
code hashes and the historical candidate/checkpoint seals. Under the resource
supervisor, current readers and resolver reproduced byte-identical outcomes,
links, diagnostics, both link indexes, census and full 05F comparison for all
511 mentions. The result remains **468 links and 43 explicit nonlinks**. This
also preserves every F1 warning and sampled-review/figure limitation. Parent
verification confirmed every original checkpoint's bytes and modification time
remained unchanged.

The final read-only audit, `05g_quality_attempts/attempt-002`, succeeded in
2.868 seconds with peak RSS 695,009,280 bytes and zero swap growth. Attempt 001
also succeeded; its evidence is preserved. The second run adds the reviewed
root-binding checks. A setup invocation before attempt 001 stopped because its
supervisor parent directory did not yet exist; no worker or attempt was created.
The final audit uses one worker/two threads, 4-GiB RSS, zero swap, 1,800 seconds,
8-GiB minimum free space and a conservative output cap below the existing 2-GiB
cumulative allowance. No source PDFs/images/models were accessed.

All 272 focused Task 05G tests pass. `make fix` passes. Full `make check` passes
formatting, lint and mypy, with 2,377 pytest passes and the same three previously
reproduced historical failures:

- `test_collection_generator_preserves_historical_v38_owner_packet`
- `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`
- `test_task06g_templates_are_executable_and_source_free`

The standalone audit script additionally passes Ruff and mypy. `git diff --check`
passes. The historical failures concern accepted-base/generator expectations;
no tests were weakened to suppress them.

## Next boundary

The result report intentionally compares using the historical activity ID while
binding current code separately. It does not misrepresent refactored code as the
producer of attempt 7. Historical run requests and launch packets remain unchanged
and their old code pins are now stale for current-writer execution. A fresh
current-code request and authorized supervised replay/comparison are required
before finalizing that implementation. Finalization/acceptance, Task 05H, commit
and push remain unperformed. No remaining link recovery is proposed.
