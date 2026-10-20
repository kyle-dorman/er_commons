# Reporting presentation v2

User-approved presentation amendment after Task 12, before locked evaluation.
This supersedes v1's six/thirteen **reporting views**, not its scoring rules.

- Report all 19 development questions as one group, with both models and three
  repeats per question. Do not split figures or presentation tables into the
  original six and additional thirteen. Retain exposure identities only in the
  sealed technical provenance.
- Development results demonstrate the reporting workflow. The 30 locked test
  questions in Task 13 will supply the main target-model results, in a second
  separate folder using the same definitions and figures. Never pool development
  and test.
- Historical judge accuracy remains separate, using its own recorded evaluation
  populations and calibration partitions. It is not a target-model pass rate and
  does not become a 19-question or 30-question accuracy estimate.
- A review folder contains final PNG/SVG figures, relevant CSV tables and a
  `START_HERE.html` gallery. Input receipts, raw judgments, intermediate outputs
  and provenance manifests remain outside this folder.

`reporting_review` verifies the accepted source completion and every sealed output,
selects pooled summaries, preserves historical judge partitions, and renders a
fresh folder. `reporting_charts` now shows pooled model results and an ungrouped
question overview. Metric reductions, fixed complexity bins, missing/error rules
and frozen generation/judges are unchanged. Original Task 12 artifacts remain
sealed and historical.

Current review folder, relative to `ER_COMMONS_DATA_ROOT`:
`pipelines/brisbane_baylands/task_12/development_19_review/`.
The adjacent `development_19_review_provenance.json` binds its source and outputs.
Tasks 13–15 remain provisional; this presentation change authorizes no calls or
locked-content access.
