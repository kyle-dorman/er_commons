# Historical architecture notes

These notes preserve descriptions removed from the current architecture contract.
They describe completed experiments and superseded entry points, not authorization
to run them or a guide to current commands. Numbered task outcomes and sealed
specifications remain the evidence owners. Use [current architecture](../architecture.md)
and the [judge maintainer guide](../judge_maintainer_guide.md) for maintained interfaces.

## Judge development experiments

The following description records the Task 09E-era comparisons. Their staged
runners, cloud transports and experiment dispatch were later retired by 09F.2;
references to “live,” “maintained,” or “new” below describe that historical period.

For bounded point-prompt comparisons, `grounding_run --pipeline points` reuses the
staged Inspect adapter while skipping abstention/conclusion calls. It retains
zero-point samples, emits null answer scores, and aggregates validated point flags
without answer-level accuracy. The [v2 comparison contract](../specs/task09e_point_scope_v2.md)
owns the frozen inputs and source-review requirements.

The combined 09A.3 panel adapter (`grounding_dataset_panel`) verifies the new
publication, eligibility and record-specific origins independently of the preserved
four-answer panel loader. `grounding_run --dataset-version 09a3` selects it;
`dev6_additions` loads only the additional three cases. An explicit
`freeze_dataset_panel(..., full_dev=True)` publication and `full_dev` loader
selection support the user-authorized full development comparison; the default
stays at six cases and exact sealed development membership is required. Restricted stage expectations
are canonical-ID-mapped metadata, never model input. Inspect reports stage-level
agreement and coverage separately from final scores; missing/invalid predictions
are not false labels. The [combined rerun contract](../specs/task09e_09a3_small_v1.md)
owns authorized counts and experiment bounds.


Task 09E.1 retains historical strict judge behavior while extracting the shared
legacy stage executor into `grounding_stage_runtime`. New `grounding_comparison_*`
modules separately own sealed Dev3 loading, semantic/quotation validation, provider
wire mappings, exact preflight and budgets, Inspect execution, offline audits and
post-run proposed-label analysis. Binary-only observations cross stage boundaries.
The live CLI is create-only; incomplete attempts never trigger automatic replay.
See the [comparison contract](../specs/task09e1_comparison_v1.md) and
[cloud handoff](../specs/task09e1_cloud_handoff.md) for qualification gates and commands.
Clef execution and its uncounted local exception are retired. Historical receipts
remain unchanged. The maintained three-model profile selects GLM with Luna/Haiku
alternatives, while legacy Ollama paths remain for local integration checks.
See the [maintainer guide](../grounding_judge_guide.md) and
[09E.2 cleanup](../../tasks/sprint2/09e2_cleanup_grounding_judges.md).

Pure sample/metrics contracts live in `grounding_records` and `grounding_metrics`;
source-text traversal and local transport policy have separate owners. Cloud
prompts are frozen independently of legacy prompt wording. Provider configuration
is validated before rendering. The shared cloud budget stops further reservations
on transport uncertainty, cancellation, storage/receipt failures and native
identity/usage mismatch, including requests already waiting on token counting.
Explicitly pinned development panels are checked against original source/answer
projections without loading labels; post-run analysis alone consumes expectations.
Coverage-aware metrics separate original claims, reviews, conclusions and scores.

Bounded generation experiments may supply a nonempty per-stage prompt override;
its actual rendered request and configuration identity are preserved in receipts.
Default prompts remain unchanged. OpenAI sampling overrides are explicitly
validated against the selected reasoning mode, and cache controls are rendered
only when configured for that model. Exact counting omits generation-only
sampling fields while retaining the full generation request's hash binding.
See the [settings/prompt contract](../specs/task09e1_settings_prompts_models_v1.md).

The comparison evaluator accepts validated stage-specific prompt mappings, so
fresh point decisions flow into conclusions with independently selected review
instructions. Luna can opt into an evidence-prefix cache breakpoint: two text
blocks concatenate to the original JSON exactly, while implicit caching still
covers exact duplicates. The exact counter retains nested breakpoint markers.
Schema differences and short prefixes can still prevent reuse; neither provider
caching nor prompt overrides reuse saved judgments. See the
[bounded pipeline outcome](../specs/task09e1_luna_cache_pipeline_result.md).

The bounded [frozen-claims conclusion experiment](../specs/task09e1_luna_conclusion_blind_v1.md)
adds explicit Luna-only stage options. Blind review projects prior observations
to IDs before native rendering and counting; original observations remain offline
for validation and the unchanged disagreement gate. Conclusion-only mode has its
own genuine output schema without point reviews and a separate aggregator using
frozen point decisions directly. Default requests and scoring are unchanged;
the experimental paths do not invent reviews or silently suppress disagreements.

## Archived MiniMax side experiment

This code is retained for historical reproducibility, not active model work.
Its sealed outputs are excluded from presented benchmark results. The maintained
Task 13 result route selects Luna and Haiku only.


[Task 13A](../../tasks/sprint2/13a_minimax_cloud_comparison.md) adds a narrow
`minimax_provider` native-schema generation adapter, a separately bound
`minimax_run` roster/accounting wrapper and offline `minimax_reporting` replay.
The original evaluator and judges remain unchanged; explicit generation/delivery
hooks let the existing slot runner and observation replay consume actual Ollama
messages. The final publication retains all 90 attempted slots, including invalid outputs
and provider failures; no automatic continuation or retry is authorized.

`minimax_continue` binds the explicitly approved 90-minute active evaluation
deadline to a copied sealed ancestor, preserving original answer identities and
cumulative reservations. One answer worker finishes saved partial evaluations
before verified untouched slots, matching the retained rate-limit concurrency.
A durable global restart excludes only the sealed administrative pause; live
queueing and the original six-hour clock continue to count.
