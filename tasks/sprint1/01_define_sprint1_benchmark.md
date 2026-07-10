# Task 01: Define the Sprint 1 Benchmark

## Abstract

Define one small, reviewable version of `er_bench` in
`benchmarks/er_bench/sprint1.md`. This task narrows the drafted project plan to
one user question and a benchmark contract with clear source, evaluation, and
reproducibility boundaries. It performs only the research needed for that
choice; it does not build ingestion, download a large corpus, or implement a
baseline.

## Goal

Complete the Sprint 1 specification so a future source-contract or baseline task
can begin without redoing broad project discovery.

## Inputs

- The drafted project plan and any supplied problem statement.
- `benchmarks/er_bench/sprint1.md`.
- `AGENTS.md`, `docs/product.md`, `docs/architecture.md`, and
  `docs/data_artifacts.md`.
- Primary documentation for only the CEQA source and benchmark methodology
  under consideration.

## Outputs

- A completed, decision-ready `benchmarks/er_bench/sprint1.md`.
- A compact source and open-source-tool evidence note in the task outcome or a
  focused decision note.
- A precise next task: either selected-source contract work or a constrained
  baseline implementation, depending on the decisions.

## Research and learning checkpoint

Research only what is necessary to make Sprint 1's decisions. Prefer primary
sources: data owner documentation and terms, official CEQA material, original
benchmark methods, and maintainers' documentation for candidate tools. Explain
plainly why the selected evaluation unit and split prevent project/document/time
leakage, why the metric serves the user question, and why existing open-source
components beat custom code.

Use small bounded subagents where available for non-overlapping questions:
source/terms, benchmark-methodology, and maintained-tool evidence. The lead
agent verifies and reconciles their findings.

## Plan / spec requirement

Start by listing confirmed facts, working assumptions, and user choices. Do not
make a durable source, benchmark, or dependency decision until the supporting
evidence is in the specification. Write a decision note if a conclusion should
constrain subsequent work.

## Validation

- Check source and terms claims against authoritative material.
- Confirm the sprint specification has no unresolved placeholder in a required
  decision field unless it is explicitly marked as a user question.
- Run `git diff --check` for documentation-only work.
- Run `make check` if code or tests change.

## Acceptance criteria

- `benchmarks/er_bench/sprint1.md` states one concrete benchmark version.
- The task, source release, evaluation unit, reference policy, split, metrics,
  baseline direction, and artifact manifest are clear enough to implement.
- The split names concrete anti-leakage boundaries.
- The selected tools are maintained open-source packages or formats, with any
  required glue code named and justified.
- The next task is smaller than this definition task.

## Non-goals

- Do not implement ingestion, annotation, models, or evaluation.
- Do not select the revision-family backlog item by default.
- Do not download or commit a large CEQA corpus.
- Do not create a workflow engine or general-purpose framework.

## Outcome

Completed 2026-07-10. The project selected
`er_bench.sprint1.brisbane_draft_defense.v1`: given a public comment and the
original Brisbane Baylands Draft EIR, produce a concise Draft-EIR-only defense
with citations. May 2026 Final EIR Volume 4 responses identify candidate
no-change cases but are never model input. The accepted source, label, split,
metric, UI, baseline, and artifact policies are in
`benchmarks/er_bench/sprint1.md`; the durable rationale is in
`docs/decisions/001_brisbane_draft_eir_defense_benchmark.md`.

Learning notes: an agency response is a discovery and reference aid, not proof
of correctness. The no-change rule makes a Draft-EIR-only evidence task
possible. A transparent Docling + BM25 + pinned local-model baseline separates
extraction, retrieval, and generation failures; a separate local judge is a
calibrated triage aid, not ground truth.

Validation: primary source pages and maintainer documentation were reviewed;
documentation validation is recorded with this change.

Sprint 2 is promoted with an accepted sprint plan and no pre-created numbered
task. Its next action is to write the bounded source-freeze task immediately
before execution.
