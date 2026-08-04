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

Start each pipeline as the smallest restartable sequence of existing
open-source tools. Add project code only for an adapter, provenance manifest,
or stable integration boundary that cannot be expressed cleanly otherwise.
