# Task 13B — Locked evaluation maintenance and presentation scope

Status: closed (2026-10-21).

## Abstract and goal

Make the recent locked evaluation code easier to read, edit and maintain without
changing frozen requests, scoring or saved results. The user selected Luna and
Haiku as the presented benchmark models and ended MiniMax exploration. Task 13A
is an archived side experiment, excluded from presented benchmark results.

## Inputs and outputs

Use Task 13/13A outcomes, current reporting definitions, the reporting maintainer
guide and Sprint 2. Produce bounded code simplifications, focused regression
coverage, and current documentation that routes only Luna/Haiku as results.
Preserve the MiniMax code and sealed artifacts for historical reproducibility;
its existing gallery is an archive, not an endorsed results destination.

## Research / learning checkpoint

Inspect existing module responsibilities and installed APIs before introducing
helpers. Follow the repository architecture principle of small functions with
explicit contracts. Consult Python's standard-library guidance where relevant;
avoid new dependencies, frameworks or speculative generalization. Python's
[Decimal guidance](https://docs.python.org/3.12/library/decimal.html) supports
retaining decimal arithmetic for exact accounting rather than replacing the
existing string-based conversions with floats. Record concrete
tradeoffs in the outcome and maintainer guide.

## Plan and review

1. Independently inspect the recent runner, provider and reporting boundaries.
2. Simplify complex local functions and repeated bookkeeping where behavior can
   be checked against existing fixtures. Keep admission and reservation ordering.
3. Update current routing and future writeup scope; retain historical records.
4. Run focused fixtures, sealed offline reporting replay where affected, then
   make fix, make check and git diff --check. Obtain bounded independent review.

## Acceptance criteria and validation

- Presented results remain the complete 180 Luna/Haiku slots across all 30 cases.
- No MiniMax figures, tables or score claims enter the presented results.
- Exact model identities, prompts, budgets, retry policy and scoring are unchanged.
- Changed code is covered by appropriate existing or focused behavioral tests.
- Existing artifacts and unrelated documentation changes remain intact.

## Non-goals

No remote requests, new benchmark run, result tuning, artifact deletion, new
framework, commit or push. Tasks 14–15 remain provisional. This is a bounded
maintenance pass on the recent evaluation code, not a rewrite of the pipeline.

## Outcome

The cleanup keeps execution, native accounting and offline replay in their
existing modules. `locked_provider` now separates usage validation/pricing and
response settlement from the wire callback. `locked_reporting` separates judge
receipt verification from answer replay. Continuation/source loading and slot
orchestration avoid repeated settlement reads, pause calculations, provenance
assignments and dispatcher snapshots. No dependency or framework was added.

The practical maintenance lesson is to extract a coherent validation step while
preserving its order and side effects. In particular, native response bytes must
be saved before parsing, unknown usage must retain its reservation, and judge
identity/context checks must run before scoring. Decimal accounting, admission
locking and zero retries remain unchanged. Existing malformed-native-structure
exceptions retain their prior behavior; this pass does not redesign recovery.
The reporting maintainer guide now maps these module and helper responsibilities.

Luna and Haiku remain the only presented benchmark models. The index, queue,
sprint plan and provisional Tasks 14–15 now reflect that scope. Task 13A has an
explicit archive designation; its code, result pointer, gallery and sealed
receipts remain intact. No figures or scores were removed from historical seals.

### Validation

- `make fix` and `make check` passed: 4,392 tests passed, one skipped, 105 existing
  Inspect deprecation warnings; formatting, lint and strict typing passed.
- Independent maintenance review approved with no actionable findings after
  verifying the replay receipt, completion digests, source inventory count and
  documentation scope. `git diff --check` passed.

- Focused provider/dispatcher tests: 51 passed, including cache accounting and
  invalid-usage reservation coverage. Independent affected-module tests: 69 passed.
- Offline replay verified 44,804 sealed source files and recomputed all 180
  Luna/Haiku answers across 30 questions. All nine target report tables matched
  the accepted JSON and CSV bytes exactly. Network connections were disabled.
- Receipt: `pipelines/brisbane_baylands/task_13b/offline_replay_20261021.json`
  under the external artifact root. The first comparison mistakenly compared
  Python tuple IDs directly with JSON arrays; comparing actual publication bytes
  resolved that validation-script issue without changing production code.
- The existing final gallery contains no MiniMax reference. Its bytes and seals
  remain unchanged. Synthetic judge tables and development publications were
  not combined with the test report.

No remote inference, commit or push. Tasks 14–15 remain provisional.
