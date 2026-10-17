# Task 11C.1 — Make development evaluation maintainable

Status: Complete (2026-10-17); requested cleanup of completed 11C.

## Abstract and goal

Make the 11C evaluation code easier to understand and change while preserving its
saved artifacts, exact projections, routing, judgments and command behavior.
This is a bounded maintenance follow-up, not Task 11D.

## Inputs and outputs

Use the [11C outcome](11c_integrate_development_evaluation.md), its sealed result,
`development_evaluation.py`, `development_evaluation_run.py` and their tests.
Produce focused modules and readable functions, clearer types at stable boundaries,
a compact maintainer map, and offline verification evidence.

## Plan and learning checkpoint

1. Review responsibilities and dependencies before edits. Favor ordinary functions
   and explicit data contracts; avoid a framework or one-file-per-helper design.
2. Separate source loading, provider receipt mechanics and orchestration where they
   change independently. Break long projection/report functions into named steps;
   make routing branches and failure states easy to inspect.
3. Preserve JSON formats and identity recipes. Bind any newly extracted source
   modules in the execution manifest; source-change replay must still reject every
   non-implementation difference. Do not weaken seals to make cleanup pass.
4. Retain existing meaningful regression fixtures. Verify complete saved report and
   plan equivalence with provider construction disabled, then run `make fix`,
   `make check` and `git diff --check` and a bounded independent review.

Use Python's standard typing and module facilities; no new dependencies. Read the
[typing guidance](https://docs.python.org/3/library/typing.html) for practical type
boundaries. Explain ownership and where to edit in the outcome and architecture
notes. Clarity and limited coupling matter more than minimizing line count.

## Acceptance and review

The entrypoint should read as orchestration, provider-specific counting should
have one owner, and core routing should be straightforward to follow. Existing
fixtures and the sealed three-case replay must retain exact results. Independent
review covers maintainability and accidental behavior/provenance changes.

## Non-goals

No provider calls, regenerated targets, prompt changes, judge changes, new benchmark
policy, locked-test/reserved content, 11D, commits or pushes. Preserve all existing
working changes and sealed 10/11B/11C evidence. Cleanup validation uses a fresh
external directory and does not rewrite prior result pointers.

## Outcome

Split the runner into clear input, provider and orchestration owners, and made core
preparation/report routing readable as named stages. The unchanged Make command
continues to evaluate or explicitly replay saved candidates. No provider calls or
new evaluation results were produced. The [cleanup result](../../docs/specs/task11c1_cleanup_result.json)
binds the before/after source and verification evidence; the original 11C result
pointer and sealed artifacts remain unchanged.

| Owner | Maintainer entry points |
| --- | --- |
| `development_evaluation_inputs.py` | `load_plans`: verify seals, candidates, delivery receipts and development references. |
| `development_evaluation.py` | `prepare_candidate`, `build_report`, `pending_items`, `readable_report`: validation, isolated projections, routing and reports. |
| `development_evaluation_provider.py` | `component_settings`, `ReceiptHooks`, `execute_item`: frozen settings, counting, transport guards and accounting receipts. |
| `development_evaluation_run.py` | `run_manifest`, `replay_run`, `run`, `main`: provenance, replay, orchestration and command line. |

The core's former large preparation function now names identity validation, source
verification, answer parsing, automatic checks and component projection. Explicit
branches replace nested routing expressions. Typed answer/point records and a small
verified-source context document stable data; typed limits and `GenerateConfig`
make the provider contract easier to edit. Arbitrary provider/persisted JSON remains
at existing validated boundaries rather than duplicating every upstream schema.
Types clarify expected fields but do not replace runtime validation.

The request hook names its count-recording, native-control validation and exact-count
phases. Counter timing, failure capture, sealed publication and conservative stop
behavior are unchanged. Tests import and patch the actual module owner; no temporary
compatibility reexports or new dependencies were added. All four source modules now
appear in implementation provenance, with a focused regression assertion protecting
that inventory. The source-change replay exception still applies only to code hashes.

Independent review found no correctness or maintainability issues. Verification
reconstructed identical plans and byte-identical JSON and Markdown reports for all
three saved cases with provider construction/dispatch disabled. The CLI replay also
passed with zero calls. All previous identity, routing, failure and native SDK
fixtures remain; the only new test covers the extracted module inventory.

`make fix`, `make check` and `git diff --check` passed. Detailed check counts and
hashes live in the cleanup result. Before/after source archives, review and replay
receipts, and validation logs are stored in the fresh external
`pipelines/brisbane_baylands/task_11/validation_11c1_20261017/` directory.

Next remains refreshing provisional 11D; it has not begun. This cleanup makes
future edits local and reviewable without changing the accepted evaluation policy.
