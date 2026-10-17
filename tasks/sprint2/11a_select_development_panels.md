# Task 11A — Select development panels and success criteria

Status: Complete (2026-10-17); development panels fixed before target generation.

## Abstract

Select a small, fixed development panel for prompt iteration before observing Luna outputs.

## Goal

Choose three initial questions and a nested six-question panel, with explicit review criteria.

## Inputs

[Task 10 result](../../docs/specs/task10_final_result.json), its development packets and mappings; the frozen development membership; [judge guide](../../docs/judge_maintainer_guide.md).

## Outputs

A small panel manifest containing exact IDs, 3-of-6 nesting, the remaining 13 IDs, selection reasons and packet bindings. A compact run/comparison checklist and proposed iteration/call budget.

## Plan / spec requirement

Use this contract as the brief plan; record concrete interfaces and limits before implementation.

1. Inspect development-only question/evidence characteristics. Choose varied reasoning, evidence length and table/multiple-source challenges where available; do not claim statistical representativeness.
2. Fix all six IDs now, with three identified as the first cycle. Explain coverage and any shared-evidence overlap. Do not select by favorable model or judge outcomes.
3. Define criteria for schema validity, resolved citations, complete requests, A/G/S/C outcomes, answer usefulness and visible evaluator failures. Specify how manual answer inspection informs prompt decisions.
4. Propose bounded cycles, calls/cost and stopping rules for 11D; concrete values must be recorded before runs, not inferred from a timebox. Preserve the sprint's three-day working timebox as a planning target and report overruns.
5. Record that all six are tuning examples. The remaining 13 are a broader development check, not an independent held-out benchmark, especially given prior development use and shared evidence.

## Research / learning checkpoint

Use the Inspect dataset guidance linked in the umbrella for explicit sample-ID selection. Explain why nested panels make comparisons interpretable and why repeated prompt selection makes their scores optimistic.

## Validation

Check unique IDs, exact 3/6/13 counts, first-three subset of six, six and remaining-13 disjoint, and union equal to frozen development membership. Review selection rationale without opening test content.

## Acceptance criteria

The manifest and criteria are sufficient for 11B–11E to select cases without guessing. No model runs occur.

## Review pass

Independent bounded review of split membership, selection bias and panel coverage.

## Non-goals

No generation, judge calls, reference editing, prompt experiments or test selection.

## Shared boundaries

Follow the [Task 11 umbrella](11_build_and_freeze_target_generation.md). Use only
the 19 development cases; no locked-test or reserved judge-challenge access.
Preserve Task 10 packets and frozen A/G/S/C judge policies. Keep references and
judge feedback outside target requests. Generated runs and reports belong under
`ER_COMMONS_DATA_ROOT`, with exact input/configuration hashes and fresh namespaces.

## Outcome

Completed development-only panel selection. The [manifest](../../docs/specs/task11a_development_panels_v1.json)
binds initial **C041, C017, C019**, expanded with **C014, C037, C056**, and the
remaining thirteen to exact Task 10 v4 files, completion and individual records.
The [protocol](../../docs/specs/task11a_panel_protocol.md) owns coverage rationale,
success criteria, manual/automatic comparison checklist and proposed bounded
iteration, call and spending ceilings. No model or judge ran; no locked-test or
reserved judge-challenge content was opened. Existing Task 10 artifacts are unchanged.

Validation checked unique 3/6/13 counts, nesting, disjointness and exact union with
the checksum-verified frozen 19-case development target file; target/mapping IDs
agree and input bytes match the published hashes. Per-record hashes exclude JSONL
line terminators. Exact canonical-unit overlap is zero across selected cases and
between the six and thirteen, without implying independence of shared documents
or previous development exposure. C014 retains both approved scopes of its table.

A bounded independent read-only reviewer verified development membership, Task 10
hashes, coverage and overlap. Its qualifications are incorporated: purposive
biology/water emphasis, no statistical representativeness or established genuine
no-answer coverage, and the thirteen remain development checks. Nested panels
make paired regressions visible; repeated selection makes tuning scores optimistic.
Primary-source Inspect dataset guidance was checked on 2026-10-17 and linked in
the protocol. A final independent review also verified all 38 record hashes/joins, file bindings,
set invariants and budget arithmetic, with no blockers. Manifest assertions and
git diff --check passed.

Next: refresh the provisional 11B contract using these bindings and criteria before
execution. **11B has not begun.** 11C must settle actual evaluation routing/fan-out;
11D must finalize proposed budgets and prices before any prompt cycle. This outcome
does not authorize model calls or change frozen judge policies.
