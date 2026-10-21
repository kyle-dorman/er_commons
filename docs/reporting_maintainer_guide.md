# Reporting maintainer guide

The reporting path is offline: saved observations → tables → figures/gallery.
The presented benchmark models are **Luna and Haiku only**, selected by the
[Task 13 result pointer](specs/task13_result.json). MiniMax's Task 13A outputs
are archived side-experiment material; do not merge them into result figures,
tables or the methods/results writeup. Keep their existing seals intact.
Current score definitions are [v1](specs/task12_reporting_v1.md), with
[pooled presentation](specs/task12_presentation_v2.md),
[judge repeatability](specs/task12_judge_repeatability_v3.md) and
[response-unit counting](specs/task12_response_units_v4.md) amendments.

## Where to edit

| Concern | Module | Boundary |
| --- | --- | --- |
| Accepted 11E input/replay | `reporting_inputs` | Historical development adapter; verifies seals and pure evaluator replay. Do not broaden it for Task 13. |
| Citation occurrences/response units | `reporting_counts` | Pure counts from canonical IDs and saved citation attempts; no source loading. |
| Component, joint, repeat, citation and complexity reductions | `reporting` | Pure reductions; keeps missing/invalid/N/A distinct and requires three planned slots. |
| Synthetic judge history | `reporting_judges` | Explicit 09G adapter and label-agreement/repeat reductions; separate from target results. |
| Table selection and gallery prose | `reporting_presentation` | Copies inputs, refreshes count views, selects pooled summaries; no artifact reads. |
| Figures | `reporting_charts` | Model roster from data; `primary_model` selects complexity. Style changes do not change metrics. |
| Saved-report export | `reporting_review` | Verifies all sealed files, stages outputs and writes sibling provenance. |
| Original development publication | `reporting_run` | Task 12-specific replay/manifest, not a generic run dispatcher. |
| Locked test replay/publication | `locked_reporting` | Verifies the complete sealed 180-slot roster. `_observation` replays one answer; `_replay_judgments` verifies saved judge identities, items and contexts before reduction. |

## Locked execution maintenance

Task 13 is closed. These boundaries explain the retained code; editing it does
not authorize another run or reuse a historical preflight with changed code.

| Concern | Module | Boundary |
| --- | --- | --- |
| Frozen source loading and planned slots | `locked_inputs` | Read only accepted split-specific inputs and verify provenance. |
| Preflight and answer orchestration | `locked_run` | Bind code/configuration, assemble one slot and call the provider/evaluator. |
| Durable admission and settlement | `locked_dispatch` | Own atomic reservations, request identity, shared concurrency and zero retries. |
| Native requests and receipts | `locked_provider` | Save wire bytes before `_response_cost`; `_generation_cost` validates usage and prices both generation and judge responses using Decimal. |
| Historical continuation | `locked_continue` | Verify ancestor receipts, preserve attempted requests and carry elapsed active time forward. |
| Independent ledger checks | `locked_audit` | Reconcile saved reservations and settlements without dispatch. |

Keep transport, admission and offline reporting separate. A small helper for a
coherent validation step is preferable to duplicating it or introducing a new
provider framework. Preserve receipt order and unknown-cost reservations when
editing accounting. Saved artifacts bind historical code hashes; changed code
requires fresh preflight/review for any separately authorized execution.

## Reuse and comparisons

`answer_tables(rows)` retains exact run, candidate, point and repeat identities.
Use a distinct `model` comparison label for each model/configuration arm, while
preserving its actual `model_id` and original run/candidate identities. Do not
concatenate different runs under the same arm/question/repeat key: duplicate
slots are rejected. Construct a complete three-slot roster for every question,
including unavailable observations. Do not merge development with test.

Keep configuration arms distinct even when the underlying model is the same.
The caller must establish a common eligible question roster and compatible
scoring definitions before comparing arms; these functions do not select runs,
relabel saved identities or infer experiment compatibility. No automatic merging
of historical publications is introduced by this cleanup.

`complexity_tables(answers, primary_model="luna")` and
`render_charts(tables, output, primary_model="luna")` take the same explicit
selection. Additional model labels appear in all comparison charts; a missing
primary or inconsistent model roster raises an error instead of silently dropping
results. Three repeats remain the benchmark contract, not a configurable plotting
shortcut. Changing that protocol requires a separate definition/schema update.
The established `luna_complexity` filename is retained for existing consumers;
the figure title and provenance identify the selected model.

## Exporting final figures and tables

For a self-contained sealed report containing judge repeatability:

```bash
uv run --offline python -m er_commons.reporting_review \
  --source /path/to/sealed-report \
  --completion-sha256 ACCEPTED_COMPLETION_HASH \
  --output /path/to/fresh-review-folder \
  --primary-model luna
```

Only the original Task 12 legacy publication needs `--judge-repo /path/to/checkout`
to explicitly load its separately sealed 09G synthetic records. Otherwise export
uses only the supplied publication: it does not discover a checkout or reload
unrelated judge results. Outputs must be under the external artifact root.
The folder and its sibling `_provenance.json` must both be fresh. API callers get
the same persisted receipt as CLI callers. Changed inputs/code use a fresh output;
old seals remain intact. Intermediates/provenance remain outside the gallery.

## Validation and tradeoffs

Run focused reporting tests, then `make fix`, `make check`, `git diff --check`.
Use invented fixtures for future models and failure paths. For scoring-neutral
changes, compare CSV values against the accepted publication and visually check
changed figures; image bytes may differ after layout edits.

The separation is intentionally functions and small modules, not a plugin system
or a workflow engine. Standard-library `tempfile.TemporaryDirectory`, exclusive
`Path.open("x")` and JSON/CSV keep publication reviewable; Matplotlib `rc_context`
contains style changes within rendering. Their installed APIs were inspected
locally for this offline maintenance pass. Two filesystem destinations cannot be
published in a single atomic operation: the receipt is reserved first and removed
on a caught publication failure. A process crash may leave a receipt-only orphan;
create-only checks deliberately require inspection rather than overwriting it.
