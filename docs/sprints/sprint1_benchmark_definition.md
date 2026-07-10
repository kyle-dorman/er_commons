# Sprint 1: Define the First ER Bench Version

This sprint defines one clear, reviewable version of the first CEQA-oriented
benchmark. Read it when planning Sprint 1; use Task 01 for the detailed
execution contract and `benchmarks/er_bench/sprint1.md` for the specification
being completed.

## Outcome

Sprint 1 accepted `er_bench.sprint1.brisbane_draft_defense.v1`: the model uses
only the original Draft EIR to write a cited defense of a public comment. Final
EIR responses are curator-only candidate provenance. The specification is in
`benchmarks/er_bench/sprint1.md`; the durable decision is
`docs/decisions/001_brisbane_draft_eir_defense_benchmark.md`. Sprint 2 is now
current with an accepted sprint plan and no pre-created implementation tasks.

## Goal

Leave Sprint 1 with an implementable benchmark contract, not a broad research
report. The contract must define the user question, source-release boundary,
unit of evaluation, reference policy, anti-leakage split, metric, baseline
direction, artifacts, and acceptance gate.

## Required work

1. Read the drafted project plan and identify the one user question worth
   benchmarking first.
2. Research only the source, benchmark-design, and open-source-tool facts
   needed to choose that version.
3. Record the decisions and unresolved user choices in
   `benchmarks/er_bench/sprint1.md`.
4. Explain the best-practice rationale in Task 01's outcome or a focused
   decision note.
5. Write the smallest next task for the selected source contract or baseline.

## Boundary

Do not download a large corpus, build an ingestion system, implement models, or
turn the revision-family backlog item into active scope unless Sprint 1 selects
it with evidence. This sprint values a clear, narrow contract over premature
implementation.
