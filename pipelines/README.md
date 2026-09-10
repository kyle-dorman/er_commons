# Pipelines

This tracked directory owns human-readable pipeline specifications, small
wrappers, and reusable configuration that a later task explicitly promotes.
Generated pipeline manifests and outputs belong under:

```text
/Volumes/x10pro/er_commons/pipelines/
```

Task 03G.1 bounded diagnostics use
`pipelines/brisbane_baylands/task_03g1_model_corpus_smoke/<smokev1-id>/`.
That namespace contains smoke identity and retained `attempts/<attempt-id>/`
with per-range parser evidence, per-page routes and table outcomes, resource
observations, and inventories. One completed attempt publishes a no-clobber
`diagnostic_summary.json` at the `smokev1-` root. The namespace must never
contain complete-document, corpus accounting, target-index, resolution, or
handoff completion artifacts.

The maintained diagnostic entry point is `python -m er_commons.parser_smoke`.
The historical `smokev1-` namespace and completed diagnostic bytes are retained; the
module rename changes only future code-bound identities.

For future production work, `document_parsing` produces parser evidence,
`document_publication` publishes one complete document, and `collection_processing`
assembles collection accounting, indexes, cross-document links, and handoffs. Independently sealed content conversion and completed ranges are reused through
the historical compact readers; fresh execution has separate current identities.

Maintainer route: begin with `er_commons.cli`, enter the public facade exported by
`er_commons.document_publication` or `er_commons.collection_processing`, and then read
that package's `workflow.py` application shell. The v2 run-spec model is in `config.py`;
checked examples and schemas are under `benchmarks/er_bench/{fixtures,schemas}/`; the
matching end-to-end behavior is in `tests/test_{document_publication,collection_processing}_workflow.py`.
Machine-only reporting follows the same pattern through
`er_commons.extraction_reporting` and its short `reporting.py` shell.

Start each pipeline as the smallest restartable sequence of existing
open-source tools. Add project code only for an adapter, provenance manifest,
or stable integration boundary that cannot be expressed cleanly otherwise.

The [maintained command map](../docs/pipeline_commands.md) separates preparation,
execution, compact validation, deep audit, and review. Historical task names remain
in accepted artifact paths and record contracts; maintained wrappers use explicit
request files and responsibility names. Task 06B does not authorize a production run.
