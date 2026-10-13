# Task 09E.2 — Maintainable grounding judge cleanup

Status: complete, authorized and validated October 13, 2026. This cleanup covers both Task 09E
code introduced in `f0c57a0` and the current uncommitted Task 09E.1 implementation.
It does not create a commit or change branches.

## Abstract and goal

Make the existing judge implementation reusable, readable and reliably tested.
GLM remains the selected cloud judge; Luna and Haiku remain alternatives. Retain
Ollama and the small Qwen integration path for future code-path testing. Retire
Clef execution and its experiment-only exceptions. Preserve historical artifacts,
current scoring semantics, prompts, source visibility and dataset boundaries.

## Inputs and outputs

Read AGENTS.md, docs/index.md, docs/todo.md, docs/architecture.md,
docs/data_artifacts.md and docs/documentation.md. Task 09E and 09E.1 own historical
contracts and results. Output is maintained package code, focused regression tests,
a short maintainer guide and an independently reviewed cleanup outcome here.

## Plan and review

1. Independently audit core stages, cloud execution, and panel/command interfaces.
   Establish the focused offline baseline before editing.
2. Remove Clef dispatch, runtime probing and special uncounted execution. Keep
   historical specifications/configuration identities preserved; provide a fresh
   maintained configuration rather than rewriting sealed experiment evidence.
3. Simplify shared stage execution and configuration boundaries where there are
   actual duplicate callers. Fix concrete failure/recovery and input validation
   defects found by review. Avoid new orchestration frameworks or speculative APIs.
4. Exercise maintained local and cloud paths with invented offline fixtures,
   including failure, budget, identity and source-isolation checks. Independent
   review must cover all implementation changes, including inherited 09E code.
5. Run focused tests, make fix, make check and git diff --check. Record historical
   Task 06G failures separately from cleanup regressions.

## Research / learning checkpoint

Use the installed Inspect interfaces and existing fixture integration tests as the
compatibility baseline. Recheck primary Inspect/Python/HTTPX guidance for any
changed execution or resource-lifetime boundary. The key design rule is to keep
pure request/validation logic separate from transport and immutable persistence;
uncertain calls must retain their intent and cannot silently restart spending.
Record the concrete sources and tradeoffs in the outcome.

## Acceptance criteria and boundaries

- Clef is absent from the maintained dispatch surface; historical results remain.
- Ollama smoke infrastructure and the three selected cloud families remain tested.
- Shared helpers have clear ownership, typed interfaces and purpose/invariant docs.
- Regression tests establish unchanged score rules, information visibility and
  request rendering except explicitly documented retired modes or defect fixes.
- All useful audit findings are fixed or explicitly bounded with evidence.
- No inference, paid calls, model downloads, dataset changes, label/prompt tuning,
  later-task work, sealed-artifact mutation, commits or pushes.

## Outcome — October 13, 2026

Completed the combined 09E/09E.1 cleanup on the existing branch. GLM remains
selected. Removed Clef execution, runtime probing, special uncounted bypass and
Clef-only tests, while preserving historical config/specification/result files.
Ollama/Qwen commands, pinned counters and strict local evaluators remain tested.
No model inference, credentials display, downloads, dataset/label changes, external
artifact writes, commits or pushes occurred.

### Implementation

- Extracted pure saved-sample/summary contracts, source-text traversal and local
  native completion/retry policy from Inspect adapters. Maintained narrow imports
  used by saved experiment runners; published shared stage projection helpers.
- Froze seven cloud instruction strings byte-for-byte, independently of historical
  local prompts. Added pre-cleanup SHA-256 regression coverage. The maintained GLM
  override copies the accepted empty-review clarification exactly; no semantic
  appendix or new prompt experiment was introduced.
- Separated configuration validation from wire adapters. Supported subsets replace
  the seven-model execution requirement, with explicit three-model medium/cache
  profile and unknown-setting/endpoint validation. Historical v1 config is archival;
  six non-Clef adapters retain offline protocol tests.
- Split cloud stage execution into request preparation, qualification, reservation/
  dispatch and response validation. Uncertain transport, cancellation, storage and
  receipt errors halt shared reservations without replay, including requests already
  waiting on a counter. Corrupt/nonobject receipts fail predictably. Local malformed
  nonobject completions also retain controlled failure records without retry.
- Added explicit, provenance-bound development panel and prompt-file CLI inputs,
  Makefile routing and dotenv credential loading. Original source/answer projections
  must reproduce selected packet payloads/mappings. Identical source bindings are
  verified/decoded once per load; each answer is still checked independently.
- Added maintained coverage-aware accuracy/macro-F1 for original claims, independent
  reviews, conclusions and final scores. Missing/invalid outputs count as errors;
  valid-only metrics remain separately labeled. Labels enter post-run analysis only.
- Fixed cwd-dependent offline audit paths, empty cache-probe errors and unsuccessful
  command status after an operational halt. Configuration incompatibilities fail
  before dispatch. Simplified index/TODO routing and added the
  [maintainer guide](../../docs/grounding_judge_guide.md).

### Research and tradeoffs

The installed Inspect 0.3.278 remains the scheduler/scorer boundary; its
[scorer documentation](https://inspect.aisi.org.uk/scorers.html) supports retaining
structured diagnostic metadata alongside scores. Pure validation/metrics do not
need an execution-framework dependency. Frozen prompt ownership prevents a legacy
wording edit from silently changing cloud request identities.

[HTTPX async guidance](https://www.python-httpx.org/async/) recommends scoped client
reuse. Run-wide connection pooling is deferred: Inspect owns the event loop, and
this pass avoids a second resource-lifecycle framework. No network-speed improvement
is claimed. The concrete performance improvement is repeated source-load elimination,
verified by call-count tests. Existing exact/allowance policies stay explicit.

Historical monolithic local summaries still report their final attempt's usage;
complete attempt evidence remains on disk. The selected cloud path has separate
native receipts. No new live-resume API is promised: unused restoration machinery
was removed, and uncertain paid attempts cannot restart with a fresh budget.
The small selected-object streaming readers remain separate because labels and
packets have different contracts; a generic parser is not needed for this pass.
Generic exact invoice cost reporting remains unavailable where cache/rate evidence
is incomplete. Deferred Decisions/Jev/DeepSeek integrations are not selected or
newly qualified.

### Independent review and validation

Three bounded agents audited separate core, cloud and entrypoint areas, then
reviewed another owner's work. Review found and resolved malformed configuration
container validation, the counter-await halt race, packet/original consistency,
nonobject receipt failures and runtime error handling. Final independent reviews
found no blocking issues in core behavior, metrics, panel caching/projection or the
maintainer guide. Review evidence is reflected in focused regression tests rather
than relying only on narrative approval.

- Initial focused baseline: **672 passed**.
- Final focused suite: **694 passed** (same judge/counter/request selection, including
  retained Phase 0 golden parity and new failure/metric/configuration tests).
- `make fix`: passed. Formatting/lint and mypy passed (649 source files).
- Final `make check`: **4,346 passed, one skipped, three historical Task 06G failures**.
  Those failures are the two immutable-generation tests and template-validation test
  rejecting the repository base commit; no new failure was introduced.
- `git diff --check`: passed. Branch remains `codex/task09e1-cloud-decision-judges`
  at `f0c57a0`, with requested work uncommitted.

Prior Task 09E/09E.1 experiment artifacts, dataset boundaries and labels are
unchanged. This completes cleanup, not judge qualification or 09F/09G execution.
