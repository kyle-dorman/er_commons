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

- Sprint 1 is benchmark definition and specification, not benchmark
  implementation.
- The CEQA data source, benchmark task(s), labels, splits, metrics, and legal
  or licensing constraints are not yet accepted project policy.
- The project should integrate existing open-source tools wherever practical;
  custom code is limited to transparent glue and documented gaps.
- Learning is an explicit outcome: each planning and implementation task should
  explain the selected practice and tradeoff in plain language.

## Success criteria for the first benchmark

The first benchmark is ready to implement only when a task or decision record
defines:

1. the source dataset(s), access method, license, coverage, and retrieval or
   release version;
2. the exact prediction, retrieval, extraction, or comparison task;
3. the unit of evaluation, label or reference policy, and leakage controls;
4. a reproducible split and metrics suited to the task;
5. a minimal open-source baseline stack and the reason for any custom glue;
6. artifact and provenance outputs that allow another person to rerun it.

## Non-goals for Sprint 1

- Do not claim benchmark performance, data completeness, legal suitability, or
  model quality before the corresponding source and evaluation evidence exists.
- Do not build a general workflow platform or custom orchestration engine.
- Do not download or commit a large CEQA corpus without a source-contract task.
