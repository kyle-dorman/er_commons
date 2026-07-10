# Product Contract

This file owns project framing, scope, claim boundaries, and success criteria.
Read it when work may change what ER Commons is for; skip it for a narrow
mechanical edit that does not affect those questions.

## Purpose

ER Commons is a learning-oriented, reproducible workspace for environmental
review data and workflows. Its first capability, `er_bench`, will be a
CEQA-oriented benchmark and evaluation harness. The benchmark should establish
sound data provenance, a reviewable task definition, and reproducible baselines
before the project expands into broader data or workflow products.

## Current scope

- Sprint 1 accepted one benchmark contract:
  `er_bench.sprint1.brisbane_draft_defense.v1`. Its task is Draft EIR + public
  comment -> concise defense with Draft-EIR citations.
- Sprint 2 is the current single-project vertical slice. The complete original
  Brisbane Baylands Draft EIR main report and official appendices are the
  model-facing evidence universe; Final EIR responses are curator-only
  candidate provenance. See `benchmarks/er_bench/sprint1.md` and Decision 001.
- Source reuse/redistribution is intentionally unassessed for the local learning
  pilot. Do not publish or bulk-redistribute the source or derived corpus until
  a later decision records the applicable terms.
- The project should integrate existing open-source tools wherever practical;
  custom code is limited to transparent glue and documented gaps.
- Learning is an explicit outcome: each planning and implementation task should
  explain the selected practice and tradeoff in plain language.

## Success criteria for the first benchmark

The first benchmark is ready to implement only when a task or decision record
defines:

1. the source dataset(s), access method, visible license or terms reference,
   coverage, and retrieval or release version;
2. the exact prediction, retrieval, extraction, or comparison task;
3. the unit of evaluation, label or reference policy, and leakage controls;
4. a reproducible split and metrics suited to the task;
5. a minimal open-source baseline stack and the reason for any custom glue;
6. artifact and provenance outputs that allow another person to rerun it.

## Non-goals for the current vertical slice

- Do not claim cross-project benchmark performance, data completeness, legal
  suitability, model quality, or the substantive correctness of an agency
  defense before corresponding evidence exists.
- Do not build a general workflow platform or custom orchestration engine.
- Do not download or commit a large CEQA corpus without a source-contract task.
