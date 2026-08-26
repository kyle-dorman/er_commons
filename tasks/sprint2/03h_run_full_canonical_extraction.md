# Task 03H: First Full End-to-End Extraction Attempt

Status: **complete as the first full-corpus end-to-end attempt; superseded for
final publication by Tasks 03I and 03J**. The v3 attempt exercised the complete
production path, exposed source-general correctness and scaling defects, and
landed their maintained repairs. It did not publish the final 35-document corpus:
the final code-quality and behavior-identity corrections intentionally invalidate
the retained v3 work. Those artifacts remain diagnostic evidence only and must not
be reused by Task 03J.

Completed [Task
03H.2](03h2_build_restartable_chunked_docling_conversion.md) is closed and its v2
artifacts remain immutable evidence. Task 03H.3 completed the deferred-reading-order
implementation and qualification. The v3 run was designed to process all 35 documents serially
from shortest to longest by physical page count, with source ID as the tie-breaker.
Task 03H was originally activated by user direction on 2026-08-18. Tasks 03G.1,
03G.2, all observed-failure remediation, and the [Task
03G.3](03g3_align_pipeline_responsibilities_and_names.md) architecture and
naming refactor are accepted and closed. The conversion restart boundary is now
implemented and offline-validated. The checkpoints below preserve the actual
first-attempt history. No further source, model, or publication work belongs to
Task 03H.

## New-chat entrypoint: 2026-08-20

## v3 clean-run preparation: 2026-08-21

Task 03H.2 is closed. The v2 namespace and its nine completed documents remain
historical evidence and are not inputs to this run. A distinct v3 namespace was
generated without reading source PDFs or model files:

- run root: `pipelines/brisbane_baylands/task_03h_clean_full_v3/`;
- document spec: `configs/brisbane_baylands_2025_deir_task03h_document_v3.json`;
- collection spec: `configs/brisbane_baylands_2025_deir_task03h_collection_v3.json`;
- source catalog: `configs/brisbane_baylands_2025_deir_task03h_v3_source_family_catalog_v1.json`;
- identity: `exv1-8843a1278c820d7b4b9cc2e04d80685ddb03897166a55c2520530604d70ef6d3`;
- external v3 root: verified absent before preparation; and
- ordering policy: ascending physical page count, then ascending source ID.

The v3 source order is fixed as follows:

| # | Source | Pages |
| ---: | --- | ---: |
| 1 | `deir_appendix_k4` | 4 |
| 2 | `deir_appendix_n1` | 8 |
| 3 | `deir_appendix_k5` | 10 |
| 4 | `deir_appendix_n2` | 14 |
| 5 | `deir_appendix_f2` | 16 |
| 6 | `deir_appendix_k6` | 20 |
| 7 | `deir_appendix_m3` | 32 |
| 8 | `deir_appendix_l` | 36 |
| 9 | `deir_appendix_o` | 54 |
| 10 | `deir_appendix_f1` | 75 |
| 11 | `deir_appendix_c` | 86 |
| 12 | `deir_appendix_j` | 188 |
| 13 | `deir_appendix_p` | 222 |
| 14 | `deir_appendix_m1` | 246 |
| 15 | `deir_appendix_b` | 258 |
| 16 | `deir_appendix_d` | 356 |
| 17 | `deir_appendix_e` | 362 |
| 18 | `deir_appendix_a` | 514 |
| 19 | `deir_appendix_k1_part_1_of_4` | 732 |
| 20 | `deir_appendix_m2` | 1,042 |
| 21 | `deir_appendix_k2_part_2_of_5` | 1,048 |
| 22 | `deir_appendix_k3` | 1,250 |
| 23 | `deir_appendix_k1_part_2_of_4` | 1,422 |
| 24 | `deir_appendix_k2_part_1_of_5` | 1,454 |
| 25 | `deir_main` | 2,092 |
| 26 | `deir_appendix_k2_part_5_of_5` | 2,328 |
| 27 | `deir_appendix_i` | 2,408 |
| 28 | `deir_appendix_g1` | 2,488 |
| 29 | `deir_appendix_k1_part_4_of_4` | 2,558 |
| 30 | `deir_appendix_h` | 2,572 |
| 31 | `deir_appendix_k1_part_3_of_4` | 2,790 |
| 32 | `deir_appendix_g2` | 3,736 |
| 33 | `deir_appendix_k2_part_4_of_5` | 3,882 |
| 34 | `deir_appendix_g3` | 6,104 |
| 35 | `deir_appendix_k2_part_3_of_5` | 7,934 |

The generated v3 policy retains one document worker, one-page overlap, 225-page
cores, a 275-page hard maximum, 20 GiB range RSS, 16 GiB aggregate RSS, and a
14,400-second per-process wall limit. The source-free preparation command is:

```bash
uv run python scripts/prepare_task03h.py
```

It stages only the checked-in v3 catalog and readiness report under the external
v3 root. It must be run and reviewed before the first production document command.
No PDF/model-capable command is authorized until the user explicitly approves the
v3 execution wave. After approval, process the table above serially, verify each
document's completion and reuse checkpoint, and stop on any resource, identity,
publication, or semantic-loss anomaly.

The source-free preparation completed on 2026-08-21. The readiness report is
`pipelines/brisbane_baylands/task_03h_clean_full_v3/inputs/task03h_preparation_readiness.json`
under the external data root. It reports all 35 sources, 48,341 pages, 1,519,926,399
source bytes, no completed-candidate markers, and `false` for both source-PDF and
model-file reads. The v3 root contains only the staged catalog and readiness report;
the next step is the user's explicit approval for the first PDF/model execution.

Start the new chat from local `main` after the fresh-lineage preparation commit. The
new run root is `pipelines/brisbane_baylands/task_03h_clean_full_v2/`. The previous
`task_03h_clean_full_v1` tree and all earlier Task 03H artifacts are historical
evidence only: preserve them physically, but do not reference, import, or reuse any
conversion, producer, downstream, document, or collection completion from them.
The generated v2 production identity is
`exv1-035d99c459c7cc6d2eb7ac3977ead85ca799e425318de282953bbf49963a95e3`.
The external v2 root was verified absent before current-run input staging on
2026-08-20. It now contains the source-free inputs, nine terminal document
completions through `deir_appendix_g1`, twelve sealed G1 ranges, and retained G2
range failure evidence. No G2 range seal, downstream G2 artifact, or collection
artifact exists.

“Restart from scratch” means process all 35 ordered sources again, beginning with
`deir_main`, under the new v2 namespace and newly generated production identity. Reuse
is allowed only among attempts created inside this new v2 run after its first command.
The main report and every document above 300 pages use the generated chunk policy:
225-page cores, a 275-page hard maximum, one-page overlap, one worker, a 20 GiB range
RSS limit, a 16 GiB aggregate RSS limit, and a 14,400-second (4-hour) per-process wall limit.

The first new-chat turn is source-free orientation only: read `AGENTS.md`,
`docs/index.md`, `docs/todo.md`, this task, the completed Task 03H.2 record, the
chunked-conversion specification, `docs/architecture.md`, and
`docs/data_artifacts.md`; verify Git and generated-identity state; verify that the new
v2 namespace has no completion markers; then present the exact 35-source order,
per-source chunk selection, duration forecast, disk and memory guards, collection
target, and stop/resume behavior. Do not run `make publish-document` or any other
PDF/model-capable command until the user explicitly approves it. After approval,
complete `deir_main` end to end and verify exact within-v2-run reuse before starting
the second source, then continue serially through all 35 sources.

### Source-free activation outcome: 2026-08-20

The new-chat activation found and repaired one source-free freshness defect before
running the readiness preflight: the preparation owner still scanned the historical
v1 namespace for completion markers while staging inputs under v2. The corrected
owner scans only `task_03h_clean_full_v2`; a focused regression proves historical v1
completions are ignored and any v2 completion is detected. Regenerating the code-bound
specification produced the v2 identity above.

Before staging current-run inputs, the external v2 root was absent with zero completion
markers. The source-free preparation then staged only the checked-in source-family
catalog and `task03h_preparation_readiness.json` below the v2 `inputs/` directory. The
readiness record reports 35 sources, 48,341 pages, 210 unique process configs, no
completed candidate markers, no historical lineage pins, and false values for PDF
bytes, model files, and producer identity derivation. At that checkpoint, PDF/model
execution remained pending explicit user approval.

### Fresh main-report execution blocker: 2026-08-20

The user authorized the fresh `deir_main` run and serial continuation only if the main
checkpoint worked. All ten deterministic main-report ranges converted and published
completion-last seals under v2. Their largest process-tree peak was 6,285,180,928
bytes, below the 8 GiB range limit; every recorded range observed zero swap growth.

The aggregate worker then failed before semantic assembly with `FileNotFoundError`
while creating `document_parse_evidence/docling_conversions/attempts`: on the genuinely
empty v2 namespace, its parent `docling_conversions/` did not yet exist and the
publisher called `attempts.mkdir(exist_ok=True)` without parent creation. The bounded
automatic retry deep-verified and reused all ten sealed ranges, made no new range
Docling/model calls, and reproduced the same aggregate failure after 22.80 seconds.
Both document attempts and the aggregate failure are retained. No aggregate conversion,
derived producer, downstream process, document completion, Appendix A attempt, or
collection artifact exists.

This is a fresh-root aggregate-publication defect rather than a conversion, source,
memory, or retry-reuse failure. Task 03H is stopped at its material main-report gate.
Repair and offline regression require explicit authorization before another aggregate
or PDF/model-capable invocation.

The user authorized that repair. Aggregate staging now creates the absent conversion
root and `attempts/` parent chain. A fresh-root regression reaches child verification,
retains staged failure evidence, and proves the original `FileNotFoundError` cannot
recur. Independent identity review confirms the aggregate-only change preserves the
existing child plan and all ten range IDs while rebinding the aggregate, coordinator,
producer, and downstream identities. Deterministic regeneration produced the current
production identity above. Offline validation must pass before resuming the aggregate.

Offline validation passed Ruff, strict mypy across 337 source files, all 811 tests,
deterministic Task 03H generation, and `git diff --check`. The resumed main invocation
selected zero child executions, verified and reused all ten range seals, and recorded
zero Docling calls for reused children. The repaired aggregate then sealed as
`dconv1-d25473dc456d8227942978e07be19e099d8a35735d136ace4480b00c8850c1b0`.
Derived content parsing completed in 675.64 seconds and published producer
`prv1-042ed6a96725fd5cb663b382b3b633dca23052c739bf455dc1839aa334257729`;
heading-evidence parsing reused it in 2.78 seconds.

Record mapping then failed before candidate publication because the chunked aggregate
asset inventory records figure paths such as `assets/figures/figure-0003.png`, while
the mapping contract resolves inventory paths from the conversion root. The exact
figure exists instead at
`documents/deir_main/assets/figures/figure-0003.png`; its byte size and SHA-256 match
the inventory, and the same is structurally true for the 274 aggregate figure records.
The automatic document retry reused the aggregate and producer, reached record mapping
in 7.54 seconds, and failed identically without PDF, Docling, model, aggregate, or
table recomputation. No record-mapping candidate or later process exists.

This second blocker is a relative-path contract defect in chunked aggregate asset
publication, not missing asset bytes. Task 03H remains stopped at the material main
gate. Repair requires a reviewed aggregate-only path change, a downstream integration
regression, deterministic identity regeneration, and proof that the ten child seals
remain reusable before another main invocation.

The user authorized this second repair. Chunked aggregate publication now records each
figure crop at its conversion-root-relative path,
`documents/<source_id>/assets/figures/<name>.png`, while preserving the same contained
output file and bytes. The aggregate path helper is shared by a focused aggregate test
and the record-mapping asset fixture, closing the producer/consumer integration gap.
The change is aggregate-only: it preserves the child plan and range IDs, but correctly
rebinds aggregate and downstream identities. Deterministic regeneration produced the
current production identity above; full offline validation must pass before resuming.

### Fresh serial execution through Appendix G1: 2026-08-20

Full offline validation passed Ruff, strict mypy across 337 source files, all 812
tests, deterministic Task 03H generation, and `git diff --check`. The resumed main
run checksum-reused all ten ranges with zero child executions and zero Docling calls,
then sealed corrected aggregate
`dconv1-cda47e4ab95030472dcaeae2afee943fdb3a13fe78f9cc1460c587f49fbfba36`.
Real record mapping successfully resolved all corrected aggregate asset paths, and the
complete main document published as
`docv1-e7e3bc478725f651fd4355cf124b597a3885181e8421adc6f20490a689b89d97`.
Its mandatory identical invocation returned the same completion in 0.88 seconds
without rerunning conversion or downstream work.

Serial execution then published Appendix A as `docv1-ac9af86a...ba3ebf`, B as
`docv1-e1d43296...716253d`, C as `docv1-7a75c266...38cf02`, D as
`docv1-f14ef303...5c34bf9`, E as `docv1-fd133262...000abd`, F1 as
`docv1-3d3a618a...5413dc`, and F2 as `docv1-3838e4ed...68c5cf`. These are the first
eight ordered v2 terminal documents; no historical Task 03H artifact contributed to
them.

Appendix G1 then sealed all twelve deterministic ranges for its 2,488 pages. Aggregate
publication exceeded the former fixed 10 GiB RSS limit twice: the first attempt reached
10,778,853,376 bytes, 41,435,136 bytes above the limit, and the bounded retry reached
10,768,334,848 bytes, 30,916,608 bytes above it. The retry checksum-reused all twelve
range seals and launched only the aggregate worker, with no range Docling/model
execution. Both failures are retained; no G1 aggregate conversion or downstream stage
sealed. The user then authorized a corpus-wide increase to the generated 16 GiB
aggregate RSS limit. Deterministic regeneration produced the current identity above;
the retained range seals remain eligible for operational-limit reuse.

### Appendix G2 range resource blocker: 2026-08-20

After the user authorized the corpus-wide 16 GiB aggregate policy, G1 resumed under
the regenerated identity and completed as
`docv1-7d7dfb47e425df05680c03b91cfc2abd0299352b9f739c842658a2a77ea230be`. Its twelve
sealed ranges were reused, aggregate RSS peaked at roughly 10 GiB, and all downstream
stages including record mapping completed successfully.

G2 then began fresh chunk conversion. Its first 225-page range exceeded the former
8 GiB range RSS guard twice: the first attempt reached 8,596,865,024 bytes, and the
bounded retry reached 8,590,131,200 bytes against an 8,589,934,592-byte limit. No G2
range seal was published and no later G2 stage ran. Both attempts are retained. The
user then authorized the corpus-wide range RSS increase to 16 GiB; regenerated configs
and identity now carry matching 16 GiB range and aggregate limits. G2 resumed under
that policy, but its bounded retry tripped the separate swap-growth guard described
below.

### Appendix G2 range swap-growth blocker: 2026-08-21

G2 was retried twice under the regenerated 16 GiB range and aggregate RSS policy.
Both attempts stayed below the new RSS ceiling, but the second attempt reached
541,917,184 bytes of swap growth against the unchanged 512 MiB safety guard
(536,870,912 bytes). No range seal was published and no downstream stage ran. After
the worker exited, the machine reported only 514.44 MiB of free swap, so the swap
guard was then authorized for a corpus-wide increase to 1 GiB. Configs and identity
were regenerated; G2 may retry under the new guard after the failed attempt remains
retained.

### Appendix G2 range RSS blocker after swap-policy retry: 2026-08-21

The 1 GiB swap-growth policy was regenerated and G2 was retried twice. Neither attempt
exceeded the new swap guard, but both exceeded the unchanged 16 GiB range RSS cap:
17,213,833,216 bytes on the first attempt and 17,204,510,720 bytes on the bounded
retry. No G2 range seal or downstream stage exists. The run is paused pending explicit
authorization for a separate range-RSS increase. The user then authorized the
corpus-wide range-RSS increase to 20 GiB; configs and identity were regenerated before
retrying G2 again. The second range then hit the former 2,700-second wall limit once;
the user authorized a corpus-wide increase to 14,400 seconds (4 hours), and configs
and identity were regenerated before the next retry.

### Appendix G2 deferred-reading-order repair: 2026-08-25

The four-hour second-range failure exposed that the Task 03H.3 implementation moved
routing and table evidence ahead of aggregate interpretation but still delegated each
range to Docling's standard `_assemble_document()`. Range workers therefore ran
reading order and heading hierarchy on unreduced page evidence before the intended
single aggregate pass. The range pipeline now captures exact pages and outline,
returns the unchanged conversion result, and skips document enrichment; aggregate
interpretation remains the sole reading-order and heading pass. Successful conversion
validation no longer creates a second full copy of every captured page.

The original failing read interval, physical pages 225--451, completed under the
production resource guards in 1,139.20 supervised wall seconds instead of terminating
at 14,400 seconds. Adapter conversion took 1,050.67 seconds, peak process-tree RSS was
14,726,774,784 bytes, minimum system-available memory was 8,286,683,136 bytes, and
swap growth was zero. All 227 pages completed; range-local page 227, physical PDF page
451, retained all 12,051 assembled elements. The range emitted zero warnings. This was
a bounded diagnostic and did not publish a reusable range seal.

A controlled current-code comparison on Appendix D pages 225--356 produced identical
semantic hashes for all 132 pages and identical outline, alignment, and routing
projection evidence. Runtime fell from 42.09 to 35.87 seconds. The bypass intentionally
removed 199 child-range warnings created by the discarded range-level reading-order
pass; the canonical aggregate pass independently emits the corresponding global
warnings. Aggregate document construction occurs before warning-evidence accounting,
so canonical document, heading-overlay, alignment, table, and asset inputs are
unchanged while duplicated child warning diagnostics are removed.

## Historical Appendix G2 chunked-production handoff: 2026-08-20

Task 03H.2 closed on the complete G1 proof rather than spending another PDF/model run
on a G2 rehearsal. Its maintained path sealed 12 G1 ranges independently, reused a
retained child without recomputation, reproduced the stable monolithic aggregate bytes,
and passed the isolated downstream pipeline. Measured 7.17 GB range and 8.89 GB
aggregate peaks select one worker; projected two-worker memory exceeds the accepted
concurrent ceiling.

This was the intended next action before the later decision to restart all 35 sources
from scratch. It remains evidence for the accepted chunk policy and resource bounds,
but it is not the current execution queue and does not authorize reuse of the v1 G1
or G2 artifacts. The authoritative v2 restart boundary is the new-chat entrypoint
above.

## Restart activation checkpoint: 2026-08-19

The user reactivated Task 03H for source-free restart preparation and orientation.
The reviewed post-Task-03H.1 plan starts from the exact 35-source order and writes the
serial run plan from `deir_main`, the first ordered source. By user decision on
2026-08-19, the run must also start clean at the Docling boundary. It must not
continue the historical first-wave or remaining-source queue and must not reuse any
historical Docling bundle. All stages and all 35 terminal document records belong to
the new run.

This checkpoint authorizes no source-PDF read, Docling/model construction, document
publication, collection assembly, artifact deletion, or reuse claim. After the
source-free preparation and offline validation are complete, report the regenerated
identity, ordered work plan, resource bounds, and clean-build decisions,
then obtain separate user approval before the first PDF/model-capable command.

The clean run uses
`pipelines/brisbane_baylands/task_03h_clean_full_v1/`. Deterministic source-free
generation owns that namespace in all 210 process configurations, the document and
collection specifications, and the production identity. The readiness preflight
inspects only the clean root and ignores the retained historical Task 03H tree. Its
exact 35-source order begins with `deir_main`.

Source-free regeneration and readiness validation completed on 2026-08-19. The clean
production identity is
`exv1-9bac33fc761a60ef98b09a708299d9bfe32be36b97bfbb1c7a265eb891293e70`.
The readiness record at
`pipelines/brisbane_baylands/task_03h_clean_full_v1/inputs/task03h_preparation_readiness.json`
reports `ready_for_user_authorized_clean_run`, zero clean-run completion markers,
zero historical lineage pins, and false for both source-PDF and model-file reads.
Only the catalog and readiness record exist below the clean external root.

## Clean main-report execution checkpoint: 2026-08-19

The user approved fresh PDF/model execution and continued serial processing unless a
major blocker appeared. The first `deir_main` attempt built and sealed a new 2,092-page
Docling conversion, one shared routing/table producer, canonical record mapping, and
hierarchy inference entirely below the clean namespace. Content parsing took
1,057.30 seconds; heading-evidence parsing reused the common conversion and shared
producer in 0.60 seconds; record mapping took 26.86 seconds; and hierarchy inference
took 28.42 seconds. Peak process RSS was 12,517,179,392 bytes, below the 16-GiB bound.
The shared producer records 1,551 no-table pages, 541 layout-region pages, 513 logical
tables, and 388 families. No second Docling conversion ran.

Document structure then failed closed before publication with
`CompletedRunInvariantError: completed-run invariant failed
[conversion_document_views]: one base and one heading view are required`. The common
`prv1-4673283f...5f046` routing/table bundle contains only one
`records/conversion_input.json`, written by the first base-view caller. The heading
caller correctly reuses that same producer identity but receives the same base-view
reference. Document structure therefore sees base plus base rather than the required
base plus heading pair. The earlier hierarchy stage also loaded the base view through
that shared reference, so its completion is retained failure-context evidence and
must not be promoted as the clean-run hierarchy result.

The automatic second attempt made zero Docling or table calls, reused parsing,
mapping, and hierarchy seals in 8.19 seconds, and reproduced the same failure. It is
retained as terminal attempt evidence. No document completion, second source, or
collection work existed at that checkpoint.

The user approved a bounded repair and resume on 2026-08-19. The repair makes document
view an explicit consumer role: record mapping requests `base`, hierarchy inference
requests `heading`, and document structure treats its ordered inputs as base and
heading while verifying that both resolve to the same sealed conversion owner. The
legacy `document_view` value in the shared producer reference remains readable
provenance about the caller that first published the shared bundle, but it no longer
overrides the downstream stage's semantic role. This keeps the sealed conversion and
shared `prv1-4673283f...5f046` routing/table bundle immutable and reusable. A direct
regression passes the exact same base-tagged reference for both roles and proves one
raw document load plus a detached overlay-derived heading view. Record-mapping and
hierarchy input regressions independently prove their explicit selections.

The regenerated production identity is
`exv1-66de7f37f3bfce8832e350d73537d65f04b608fbf51bff6cf2c0b13960fdf405`.
Ruff, strict mypy across 316 source files, all 733 tests, deterministic Task 03H
generation, and `git diff --check` pass before resumed execution.

## Appendix A execution blocker: 2026-08-19

The repaired `deir_main` transaction reused the clean conversion and shared producer,
then rebuilt only the corrected downstream stages. It published complete-with-warnings
document candidate `docv1-aea7f7e...69543` for all 2,092 pages. The corrected record
mapping, hierarchy, document structure, and document-reference stages took 26.11,
29.49, 29.89, and 5.05 seconds, respectively.

Serial execution then started Appendix A. Its fresh 514-page conversion and shared
producer sealed as `dconv1-3dc176e9...e6603b` and `prv1-914a26ff...f5a59` in 294.23
seconds at 10,932,436,992 bytes peak RSS. The producer records 374 no-table pages, 140
layout-region pages, 167 logical tables, and 162 families. Record mapping sealed as
`exv1-76dc6235...9e3e2`. Hierarchy inference failed twice during semantic cross-record
validation on stable item key `fdbda7ff...7c81` with `R05 role differs`.

The failure exposes a source-independent contradiction already visible between the
written R05 policy, rule application, and validator. R05 intentionally emits terminal
ambiguity with role `content`, null level, and conflict code
`NUMBERING_JUMP_UNSUPPORTED` when a numbering proposal jumps forward by more than one;
the direct decision-builder regression requires exactly that result. The independent
R05 cross-record validator instead unconditionally requires role `heading` and the
proposed level for every R05 decision. Appendix A is the first clean heading-view
source to exercise that valid ambiguity through full candidate validation.

Visual inspection changed the repair scope before implementation. The source page
shows `3.6.3 A-3: MULTI-FAMILY LOW` as an unambiguous peer of the identically styled
`3.6.2 A-2: MULTI-FAMILY MID`, followed by subordinate `DESCRIPTION`. Intervening
numbered rows such as `5.2 Residential Building ID Sign` and `6. Sustainability` are
inside the A-2 required-standards sequence but some are attached to `#/body` by the
raw conversion, so table ancestry is not a reliable general filter. Their unrelated
numbering caused the jump check to compare inferred level 3 with A-3's level 5.

The user approved the semantic repair on 2026-08-19. For a multi-part decimal marker,
R05 now prefers the nearest earlier same-regime peer with the same depth and parent-
number prefix before falling back to the nearest unrelated numbered heading. A-3
therefore compares with A-2 through shared prefix `3.6`, remains a heading at level 5,
and carries no numbering-jump ambiguity. R05's independent validator also now accepts
its separately documented fail-closed ambiguity branch for genuine unsupported jumps.
Focused regressions cover both behaviors. A live Appendix A semantic rebuild gives
A-3 `corrected_role=heading`, `corrected_level=5`, and `outcome=applied`; the rule and
hierarchy validators pass. The regenerated production identity is
`exv1-f0c129adff879e7c345a76b1d5418293f4872e3d270bb8cc220d6b5ae8df66d7`.
Ruff, strict mypy across 316 source files, all 735 tests, deterministic generation,
and `git diff --check` pass before resuming Appendix A. Its clean conversion, shared
producer, and mapping artifacts remain immutable reusable inputs; Docling must not
rerun.

The resumed Appendix A hierarchy sealed with the peer-numbering correction, but
document structure then failed because seven genuine fifth-depth headings under
`6.5.2.2` had corrected level 7 while the semantic-structure contract permits levels
1 through 6. Visual inspection of physical pages 355, 357, 359, and 361 confirmed
that `6.5.2.2.1` through `6.5.2.2.7` are real headings and that the base conversion
already represents them at raw level 6. The mismatch was source-independent: R03
outline evidence already caps effective levels at 6, while R05 numbering calibration
did not.

The user approved clipping inferred heading levels to 6 on 2026-08-19. R05 now
applies `min(6, proposed_level)` for both calibrated and fallback numbering; anchor
and TOC applications use the same maximum; and the hierarchy decision schema rejects
corrected levels above 6 so this boundary fails in its owning stage rather than later
document structure. A direct Appendix A-shaped regression proves the sequence
`3, 4, 5, 6, 6`, retains the fifth-depth item as an applied heading, and independently
recomputes the same validator levels. The regenerated production identity is
`exv1-1027d4c6fdc86b8d8d2fa90680bd66b49079884bd9f31b6612d44ccabccd3d84`.

Full source-free validation passed Ruff, strict mypy across 316 source files, all 737
tests, deterministic Task 03H generation, and `git diff --check`. Appendix A then
reused its sealed conversion, shared producer, and mapping, rebuilt hierarchy as
`hcorv1-88c700e2...e8a71`, and published all 514 pages as
`docv1-7c030772...e64bc` with raw Docling status `SUCCESS`.

## Appendix B outline-container blocker: 2026-08-19

Appendix B began next in manifest order. Its fresh 258-page Docling conversion sealed
as `dconv1-427645ba...b6ffc`; the shared routing/table producer sealed as
`prv1-6b4a7297...1653` after 66.64 seconds at 7,355,318,272 bytes peak RSS. It records
253 no-table pages, five layout-region pages, three logical tables, and three table
families. Record mapping also sealed. The configured retry reused all sealed work and
both hierarchy attempts failed identically during outline observation with
`UNKNOWN_REFERENCE: outline child list has no parent`. No Appendix C work started.

Read-only outline inspection found that the source PDF uses destinationless `.pdf`
filename bookmarks as grouping nodes. Under `2020 NOP`, the first is `TRT.pdf`; it
has no destination and owns three valid child bookmarks on physical pages 166, 170,
and 172. Physical page 165 is the end of the previous attachment, while page 166
begins the Tuolumne River Trust letter, so the filename is not a visible heading that
the existing adjacent-page recovery may synthesize. The same outline contains seven
more destinationless filename groups under `2020 NOP` and one under the valid
`Roland Lebrun` bookmark in `2023 NOP (Revised)`.

The user approved a separate transparent-container rule on 2026-08-19. A plain
destinationless `.pdf` filename with neither an appendix nor distinctive numeric
identifier is omitted only when its nonempty direct-child list has valid nondecreasing
destinations; its children traverse under the current valid parent at flattened depth
and `OUTLINE_FILENAME_CONTAINER_OMITTED` records the omission. Appendix-labeled,
distinctively numbered, non-filename, empty, invalid-child, and unordered containers
retain the earlier visible-evidence recovery or fatal rejection. Focused regressions
preserve both earlier rejection cases. Read-only execution against Appendix B retains
63 outline observations and emits exactly nine named filename-container omissions.
Ruff, strict mypy across 316 source files, all 740 tests, deterministic Task 03H
generation, and `git diff --check` pass under regenerated production identity
`exv1-fb4f9bb94aa1f648756b75979a976722f7164836c654c06d187065deb88c6b68`.

## Clean serial publication through Appendix G1: 2026-08-19

The repaired Appendix B published as `docv1-46bf7426...1624`. The same validated
identity then published Appendix C as `docv1-144895ad...cd4f`, Appendix D as
`docv1-ced2e404...fd54`, Appendix E as `docv1-68759f7f...162`, Appendix F1 as
`docv1-324cb098...2332`, and Appendix F2 as `docv1-acf75493...1631b`.

Appendix G1 next completed fresh content parsing for all 2,488 pages. Its routing
manifest records 412 no-table pages, 2,060 layout-region pages, and 16 full-page
numeric pages; all 2,076 routed pages completed table reconstruction. The shared
producer sealed as `prv1-159379eb...1b74`, and record mapping sealed after projecting
52,012 records. Peak attempt RSS was 12,653,035,520 bytes, below the 16 GiB policy.

Hierarchy inference then failed before outline traversal. The source contains one raw
outline node titled `Appendix_071024.pdf` whose malformed destination array is
`[null, 0.0, 0.0, 1]`; pypdf interprets the numeric second element as a fit type and
raises `PdfReadError: Unknown Destination Type: '0.0'` while constructing the entire
outline. The automatic retry reused sealed upstream work and failed identically, so
Appendix G1 is terminal under the current identity and Appendix G2 has not started.
Read-only raw-object inspection confirms that this node owns ten children, two of
which also lack valid destinations. This differs from Appendix B's bounded transparent
container case, which requires every direct child destination to be valid and ordered.
Any tolerant raw-outline adapter or new omission/recovery rule therefore requires a
separate review before implementation.

The user approved retaining the eight valid children of `Appendix_071024.pdf` and
omitting only its two invalid child bookmarks. A focused in-memory adapter and
regressions pass, but the first live outline traversal exposed an earlier defect that
pypdf's original construction failure had masked. Destinationless `Binder4.pdf` owns
seven direct groups. `_BuildingConst_Appendix_Complete_091423` is itself
destinationless and owns one invalid plus 29 valid child bookmarks;
`_Sustainability_Appendix_Complete_091323` is destinationless and all nine of its
children are invalid. The later `Appendix_071024.pdf` subtree duplicates most of the
Sustainability navigation, while visible Battery Storage and Water Recycling headings
remain in the sealed conversion. Resolving or omitting this earlier nested subtree is
materially broader than the approved two-leaf omission, so execution remains paused
before G1 hierarchy publication and Appendix G2.

The user approved the expanded evidence-backed cleanup and outline deduplication on
2026-08-20. The tolerant adapter modifies only pypdf's in-memory view of the exact
null-page/numeric-fit destination; source bytes remain immutable. Within that activated
outline, technical filename folders may flatten only across a nonempty ordered set of
valid descendants. Broken duplicate subtrees may disappear only when every invalid
leaf has a valid bookmark elsewhere or one unique visible body heading; same-titled
valid bookmarks on different pages remain distinct. A fully broken technical child of
an already valid parent retains the parent anchor and explicit missing-leaf diagnostic.

Actual G1 inspection now exhausts all five invalid parents in one pass. It retains 66
ordered descendants from `Binder4.pdf`, including 29 from the Building group; omits
the one invalid Building placeholder; removes the nine-leaf broken Sustainability
duplicate in favor of eight later valid bookmarks plus the unique visible Water
Recycling heading; omits the broken `EmissionMatrix_Pages` child below its valid parent;
and retains eight ordered children from `Appendix_071024.pdf` while omitting its two
invalid leaves. The resulting outline has 162 observations and ten diagnostics.
Ruff, strict mypy across 316 source files, all 743 tests, deterministic Task 03H
generation, and `git diff --check` pass under production identity
`exv1-cf06856763a69d67205f5b44d79b189b9f0ea4e54d7363bce8651eaa535442d3`.

## Restart boundary after Task 03H.1

The next Task 03H execution is a new full-corpus run, not a continuation of the
historical "remaining 29" or "remaining 30" queue below. Before execution, regenerate
and validate the production identity and all run specifications from the accepted
Task 03H.1 code, reconcile the exact 35-source manifest order, write a new serial run
plan beginning with the first source, and check in with the user before any PDF/model
work. Historical first-wave and K2 results remain diagnostic evidence only; they do
not count toward the new run's 35 terminal records.

Starting clean means recomputing Docling conversion for every required source and
configuration in the new run namespace. The first pass may not resolve or copy a
conversion, producer, document, or collection completion from the historical Task
03H root, even when its content identity matches. After a fresh conversion seals in
the clean namespace, interruption/resume and downstream retries may reuse that exact
new-run seal. All post-Docling stages are also regenerated under the current compact
schemas. No compatibility reader or historical downstream bundle is maintained.

The new Task 03H owns corpus execution, all 35 terminal document records, collection
assembly and validation, and the eventual deletion manifest for superseded
non-Docling artifacts. Before collection handoff, it must run the explicit deep audit
over every hierarchy candidate selected for the collection; ordinary restart lookup
trusts completion-sealed inventories and immutable published files without rehashing
large semantic payloads. None of this work is required to close Task 03H.1.

## Accepted execution DAG for the clean full run

The clean `task_03h_clean_full_v2` run uses the following source-free orchestration
plan. Routing and project table extraction remain separate responsibilities; the
existing Camelot/OpenCV and low-level TableFormer fallback implementation is not
changed by this plan.

```text
[1] Verify source manifest, models, configs, and identities
                         |
                         v
[2] Build deterministic page-range plan
                         |
                         v
[3] Per-range Docling conversion group
    +----------------------------------------------+
    | Docling PDFium native text/cells             |
    | Docling Heron layout detection               |
    | Capture lossless raw range evidence          |
    +----------------------------------------------+
                         |
                         v
[4] Per-range project routing
    +----------------------------------------------+
    | Source-native full_page_numeric routing      |
    | Heron-region layout_regions routing          |
    +----------------------------------------------+
                         |
                         v
[5] Per-range project table extraction
    +----------------------------------------------+
    | Camelot/OpenCV extraction                    |
    | Low-level TableFormer fallback if unmatched |
    | Preserve explicit success/failure evidence   |
    +----------------------------------------------+
                         |
                         v
[6] Seal each range bundle
    +----------------------------------------------+
    | Raw Docling evidence                         |
    | Heron layout evidence                        |
    | Routing decisions                             |
    | Page-local table artifacts                    |
    +----------------------------------------------+
                         |
                         v
[7] Aggregate all verified range evidence
                         |
                 +-------+------------------+
                 v                          v
[8] Build reduced reading-order      [9] Reconcile tables globally
    projection                            +------------------------+
    +----------------------------+        | Continuation seams    |
    | Suppress known table text  |        | Table families        |
    | only in ordering view      |        | Logical table manifests|
    | Keep raw evidence intact  |        +------------------------+
    +----------------------------+
                 |
                 v
[10] Aggregate Docling interpretation group
     +--------------------------------------------+
     | Docling reading_order once                  |
     | Docling heading hierarchy once             |
     | No TableFormer PDF stage                    |
     +--------------------------------------------+
                 |
                 +-------------------+--------------+
                                     v
[11] Merge and publish canonical document package
     +--------------------------------------------+
     | Ordered non-table Docling content           |
     | Canonical custom tables                     |
     | Explicit table failures/fallbacks           |
     | Raw evidence references                     |
     | Final validation and collection sealing     |
     +--------------------------------------------+
```

The reduced projection is an ordering input only: it may suppress text confirmed
by page-local table artifacts, but it never deletes or rewrites raw Docling
evidence. A routing decision alone is not sufficient to suppress text. If table
extraction fails or is incomplete, the range bundle retains the failure and the
ordering projection retains the unresolved source text (or an explicitly bounded
fallback representation); no table content may disappear silently. Global table
continuation and family reconciliation consume the existing page-local artifacts
and remain independent of the single aggregate Docling interpretation pass.

## Preparation checkpoint: 2026-08-18

The preparation-only implementation blocker is cleared in code, subject to the full
repository validation recorded at handoff. Content parsing now publishes a separately
identified `dconv1-` bundle before derived routing and tables. Reuse verifies the
identity derivation, exact managed file set, every checksum, completion-to-inventory
seal, source and release linkage, terminal status, full expected/converted/document
page lists, raw success, zero conversion errors, and asset accounting. Only a cache
miss constructs `DocumentConverter`. The derived `prv1-` identity names the exact raw
conversion ID and persists its completion and inventory checksums. Offline tests cover
reuse, routing-only invalidation, interruption after raw publication, corrupted or
logically incomplete raw evidence, and non-duplicated failure retention. No source PDF
or model has been invoked during this checkpoint.

The frozen Task 02 model-corpus scope contains 35 sources and 48,341 pages. Task 03G
measurements support a conservative planning rate of 0.55 seconds per page per
producer configuration. Two required conversion configurations therefore imply
96,682 page-passes and about 14.8 conversion-hours at concurrency one. Concurrency two
would have a theoretical 7.4-hour conversion floor, but two observed large-document
peaks could exceed 30 GB on this approximately 36 GiB host. The launch default is
therefore document concurrency one until the first wave supplies Task 03H measurements.
About 1 TiB is currently free. Prior producer evidence suggests roughly 170-200 GB for
two full producer views; retaining both independently sealed conversion bundles and
compatibility views could raise conversion-plus-producer use to roughly 300-400 GB
before downstream artifacts. These are capacity estimates, not reservations. A
complete validated candidate and handoff is not credibly promised in one overnight
window until the first wave measures the new boundary and downstream critical path.

The proposed first wave is the following five-source, 554-page set:

- `deir_appendix_f2` (16 pages), covering an accepted continuation boundary;
- `deir_appendix_l` (36 pages), covering a learned-fallback positive;
- `deir_appendix_o` (54 pages), an ordinary mixed figure and wind-analysis control;
- `deir_appendix_c` (86 pages), covering several learned-fallback positives; and
- `deir_appendix_e` (362 pages), covering hierarchy complexity and the prior nested-
  regime risk.

The known rotated-page positive occurs in the 2,328-page K2 part 5 source, so it is not
misrepresented as a small or medium first-wave member. It is the first post-wave risk
source if the five-source gate passes. Reserve one to two hours for the first wave,
including all document processes and exact reuse checks; update the forecast from its
observed critical path before scheduling the other sources.

The configuration gate is complete. The checked-in production-full inputs are:

- document spec: `configs/brisbane_baylands_2025_deir_task03h_document_v2.json`,
  SHA-256 `1271011c66d62173d8a29b7a7deb5b56c991f47302510762642a9d8c8371b716`;
- collection spec: `configs/brisbane_baylands_2025_deir_task03h_collection_v2.json`,
  SHA-256 `ca2d4f9ca6caadfac5a6a8847c39ff37b54344a4b8e6b09f02f0fadde7dfc60d`;
- full source-family catalog:
  `configs/brisbane_baylands_2025_deir_task03h_source_family_catalog_v1.json`,
  SHA-256 `dabdc76d765859c59b8e90cc9681f394362dbbb0e4b5683bb073be067cefacff`;
- 210 unique source-specialized templates below `configs/task03h/`; and
- native-v2 production identity
  `exv1-2062cbc522311109775485bd6b816c030b601f65abbb404514b36c3526aad332`.

These were the historical preparation values used before the stopped run. They are
not the clean-run identity inputs or approval to execute.

The source-free readiness report is
`pipelines/brisbane_baylands/task_03h/inputs/task03h_preparation_readiness.json`
under the external artifact root. It records 35 sources, 48,341 pages,
1,519,926,399 source bytes, 6,389 preserved manifest warning entries, no existing
Task 03H completion marker, and false values for both source-PDF and model-file reads.
The complete catalog is staged beside it with exact checked-in bytes. Multipart K1/K2
aliases are part-specific; a bare logical-appendix reference is not silently assigned
to one file.

Reproduce the source-free preparation with:

```bash
uv run python scripts/prepare_task03h.py
```

The exact first-wave execution commands are:

```bash
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_f2
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_l
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_o
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_c
make publish-document DOCUMENT_SPEC=configs/brisbane_baylands_2025_deir_task03h_document_v2.json SOURCE_ID=deir_appendix_e
```

The five commands will run serially and then repeat for each source to prove
zero-Docling reuse. The collection command remains withheld
until all eligible document terminal states exist; its later exact interface is:

```bash
make assemble-collection-handoff COLLECTION_SPEC=configs/brisbane_baylands_2025_deir_task03h_collection_v2.json
```
The user granted that PDF/model approval on 2026-08-18; the execution result is
recorded below.

## First-wave execution checkpoint: 2026-08-18

The user approved the five-source PDF/model wave. Initial execution started serially
and stopped fail-closed at Appendix C before Appendix E or any collection work; the
wave later resumed after the bounded remediations below.

- Appendix F2, Appendix L, and Appendix O published complete document candidates and
  identical invocations returned the same completion paths in 0.73, 0.85, and 0.85
  seconds, respectively. Their first complete runs took 39.37 seconds for L and 47.23
  seconds for O; F2's initial timing was interrupted by the remediations below.
- The first F2 attempt exposed two source-independent stale paths from the accepted
  responsibility rename: hierarchy code inventory still named `configuration.py`,
  and final-source lineage validation still read `record_mapping/documents.jsonl`
  instead of `canonical/documents.jsonl`. Both failures were retained, fixed with
  direct regression tests, and the sealed F2 Docling conversions were reused.
- Appendix C's source-release repair warning exposed a projection defect: canonical
  conversion observations retained Python warnings but not source-manifest warnings.
  The mapping now retains both warning classes and passes the schema with focused
  regression coverage. C's two Docling conversions and producer publications remain
  sealed and reusable.
- After that repair, Appendix C reached hierarchy inference and failed terminally
  because its PDF outline has two non-clickable grouping bookmarks that each own a
  child subtree: `Appendix A Exhibits.pdf` owns 25 valid ordered children and
  `Appendix B Exhibits.pdf` owns four. Inspection confirmed matching visible body
  headings on the immediately preceding pages 52 and 81. The user authorized a
  bounded extension: fuzzy-match the appendix identifier only, require one unique
  body heading on the immediately preceding page plus wholly valid ordered child
  destinations, retain the original parent-child structure, and emit
  `OUTLINE_CONTAINER_RECOVERED`. Any non-match remains fatal.
- The code fixes and bounded outline-container recovery advanced the production
  identity to
  `exv1-b894b665a8f4809edc9d0ceaec1628839d7e6ffd3beb7e2934c2717694625cbd`.
  The successful earlier document completions remain valid immutable evidence under
  their earlier identities, while all conversion and producer stages remained
  reusable during the final-identity rebuilds.
- Appendix E exposed one source-independent contradiction in the frozen hierarchy
  implementation: a verified picture caption inside a detected TOC region was
  selected for R01 exclusion even though the written policy and validator require
  all verified picture captions to reach R08 as content. The R01 builder and both
  validator paths now apply the documented caption exception, with a direct
  `toc_region=true` regression test. E then completed without rerunning either
  Docling producer.
- F2, L, O, C, and E are all sealed under the current production identity. Their
  final-identity downstream rebuilds took 9.39, 10.05, 11.46, 20.06, and 37.25
  seconds, respectively; identical invocations reused the same completion paths in
  0.72, 0.74, 0.74, 0.78, and 0.97 seconds. All five terminal states are
  `complete_with_warnings`. C records exactly two `OUTLINE_CONTAINER_RECOVERED`
  diagnostics, binding Appendix A and B to visible headings on pages 52 and 81.

The final repository gate passes Ruff formatting and lint, strict mypy across 290
source files, all 615 tests, deterministic Task 03H generation, and
`git diff --check`. No collection work has started; the remaining 30 document
sources are the next execution boundary.

## K2 part 5 execution checkpoint: 2026-08-19

The user approved `deir_appendix_k2_part_5_of_5` as the first post-wave risk
source. Its first attempt exposed excessive peak memory while serializing Docling's
embedded page and picture rasters. The approved source-independent repair now saves
all 111 figure crops as managed assets, removes 2,328 page rasters and 111 picture
rasters from the durable JSON, and streams both large JSON records atomically. The
conversion identity binds this externalization policy, and bundle verification
rejects embedded rasters or inconsistent externalization accounting.

The repaired run completed and sealed both 2,328-page Docling conversions and both
derived routing/table producers. Each raster-free `document.json` is 1,471,964,647
bytes and each streamed `conversion_pages.json` is 22,514,010,872 bytes. The two
producer configurations agree on 693 no-table pages, 802 full-page-numeric pages,
833 layout-region pages, and 1,819 clean tables. The production identity is now
`exv1-b1a340675b1a871baa3a17732df4a5649df9dd4973671373ba9f7ddb20644b28`;
the repository gate passed Ruff, strict mypy across 290 source files, all 618 tests,
deterministic Task 03H generation, and `git diff --check` before execution.

K2 did not publish a complete document candidate. Record mapping failed on
`appendix_k2_part_5_of_5_p00233_t001` because it requires every clean table to name
a Docling layout-region ID. Full-page-numeric tables are intentionally extracted
from the complete page rather than from a Docling layout region, so they have no
truthful region ID. This affects all 819 Camelot Stream tables produced through that
route, not only the first table reported on page 233. The automatic retry proved
restart isolation: it reused both exact producer seals without Docling or table
reconstruction, then reproduced the same mapping failure. Both failed attempts are
retained; no hierarchy, document-structure, reference-linking, or collection stage
ran for K2.

The next approval boundary is a source-independent mapping-contract correction:
allow an absent region ID only for full-page-numeric tables, continue requiring a
region ID for layout-region tables, and require layout-region mappings to cover
exactly the layout-derived clean tables. Do not invent a synthetic Docling region for
a full-page extraction. After focused regression coverage and identity regeneration,
resume K2 from its sealed producer evidence before starting another source.

## Performance halt checkpoint: 2026-08-19

Subsequent source-independent mapping and hierarchy work advanced K2 beyond the
failure described above, but exposed an unacceptable full-document critical path.
Corrected record mapping took 1,875.85 seconds, used about 16 GB peak RSS, and wrote
an approximately 4.6 GB candidate. Hierarchy inference then ran for 5,681.90 seconds
before a terminal outline invariant failed. A later hierarchy/bookmark-owned identity
change invalidated the baseline derived producer and caused another 5,626.79-second
routing/table rebuild. The heading producer was stopped at the user's direction.

Profiling identified a quadratic-like per-page alignment: every traversed text scans
and renormalizes every parsed text-line cell on that page. Hierarchy also constructs
the complete feature seeds twice. Separately, each raw conversion view contains a
1,471,964,647-byte `document.json` and a 22,514,010,872-byte
`conversion_pages.json`; those payloads are physically repeated in derived
compatibility views and reread for hashing. The size, copying, invalidation, whole-
object JSON, late-validation, and observability problems are coupled rather than a
bounded K2 exception.

The user stopped K2 and split all performance and storage remediation into active
[Task 03H.1](03h1_profile_and_repair_full_document_scaling.md). No further Task 03H
source or collection work may start until Task 03H.1 profiles the sealed evidence,
repairs the source-general boundaries, passes its offline budgets, and the user
explicitly approves resumption. Existing sealed K2 conversions/producers and retained
attempt evidence remain immutable and reusable; incomplete workspaces are not
authorized for deletion.

## Abstract

Run the frozen document and collection workflow across all 35 checksum-pinned
model-collection PDFs without treating document parsing as one restart boundary. For
each required source/configuration pair, publish the expensive Docling
conversion as independently sealed immutable evidence before routing, table
reconstruction, record mapping, or later processes consume it. Prove that boundary
on a small, diverse full-document wave before scheduling the remaining corpus;
afterward, pipeline work as capacity allows while retaining the stage seals.

Publish immutable per-document candidates, seal the collection
target/alias index, publish cross-document resolution records, and account
explicitly for every source and terminal state. Produce a candidate handoff and
machine integrity evidence for Task 04. Task 04 independently decides
usability and freezes the accepted extraction release; Task 03H does not
silently represent a failed source as a successful extraction.

## Goal

Produce a reproducible, internally consistent candidate corpus whose successes,
failures, lineage, hierarchy, labels, aliases, and cross-references can be
independently validated before benchmark use.

## Inputs

- user-approved Task 03G umbrella outcome and strict Task 03G.3 v2 configuration,
  identity, and capacity settings
- the sealed Task 02 manifest filtered to its 35 ordered, checksum-pinned
  `model_corpus` records
- responsibility-oriented packages and commands accepted in Task 03G.3, plus the
  behavioral contracts accepted in Tasks 03C.1 and 03D.1, the
  Task 03E.2d correction acceptance, and Tasks 03E.3–03F
- accepted pilot evidence and `/Volumes/x10pro/er_commons` capacity
- measured Task 03G conversion and downstream timings sufficient to forecast
  the first full-corpus execution window

## Outputs

- one immutable, completion-last Docling conversion bundle for every required
  successful source/configuration pair, including source checksum, conversion
  configuration, model/package/runtime identity, managed-file inventory,
  checksums, warnings, and an explicit success seal
- derived routing and table evidence that names its exact sealed Docling input
  and can be rebuilt without rerunning conversion when that input remains valid
- immutable parser evidence, canonical records, inferred hierarchy,
  printed-label evidence and resolutions, aliases, reference mentions,
  within-document resolutions, content assets, and mappings for every
  successful stage-one document
- one explicit terminal success or failure record for every required source
- a sealed target/alias index over terminal stage-one results
- immutable cross-document-resolution records, including explicit unresolved
  reasons for unavailable or ambiguous targets
- separate target-index, resolution, all-source-accounting, and candidate-
  handoff completion records
- collection manifest, machine report, checksums, warnings, configuration, and
  software/model/runtime identities
- producer-side completeness, schema, referential-integrity, coordinate,
  asset, stage-immutability, and rerun reports
- page-, table-, table-family-, hierarchy-, label-, alias-, mention-, and
  resolution-level machine observations for Task 04, with no human-review
  fields
- an exact Task 04 input path and review-cache recipe

Page renders are not canonical outputs. Generate only the predeclared Task 04
review sample as regenerable cache, outside extraction identity and
completeness.

## Research / learning checkpoint

The outcome must explain:

- **A zero exit code is not a release proof.** Source accounting, artifact
  integrity, schema validity, referential integrity, stage immutability,
  rerun checks, and warning visibility are separate layers.
- **Accounting is not success.** Every source can have a terminal record even
  when policy blocks candidate handoff or later acceptance.
- **Machine handoff is not Task 04 freeze.** Task 03H reports exactly what was
  produced; Task 04 determines what is usable for the benchmark.
- **The corpus pass cannot rewrite documents.** Cross-document resolutions are
  new records over a sealed target index.
- **Extraction recall bounds retrieval recall.** Later analysis must distinguish
  absent/unusable evidence from ranking and synthesis failures.
- **Extraction changes invalidate anchors.** A new parser, hierarchy,
  configuration, schema, or resolution policy creates a new identity and
  requires explicit benchmark migration.
- **Warnings and failures are release data.** Parser anomalies, source
  exceptions, partial outcomes, and unresolved references must remain
  queryable.
- **Expensive inference and deterministic interpretation have different
  restart boundaries.** A routing, table, canonical, hierarchy, resolution, or
  reporting correction must not rerun valid Docling conversion merely because
  the old parsing lifecycle sealed them together. Only a source-byte,
  Docling/model/configuration, conversion-adapter, or conversion-contract
  change can invalidate the corresponding conversion bundle.
- **An overnight target requires an honest forecast.** Pilot timings, source
  pages, model multiplicity, concurrency, memory, free space, and downstream
  throughput must support the intended window before launch. Missing the
  forecast is reported as operational variance; it is never hidden by calling
  incomplete work successful.

## Plan / spec requirement

Write a short run plan immediately before execution. Confirm:

1. all source, corpus, parser, model, configuration, schema, hierarchy, and
   resolution identities;
2. a preparation phase that implements and offline-validates the split
   conversion identity, raw seal, derived-stage consumer, and no-converter
   reuse path before any Task 03H PDF allocation;
3. that Docling conversion has its own content-bound identity, managed-file
   inventory, completion-last publication, checksum-verifiable reuse path, and
   consumer validation independent of routing/table policy identity;
4. exact commands, bounded concurrency, memory/disk limits, interruption
   behavior, and retry settings;
5. a conservative wall-clock and capacity forecast from Task 03G evidence for
   the intended first execution window selected in the run plan. State whether
   a complete validated candidate and handoff can credibly finish within that
   window; if not, report the estimate and revised schedule before allocating
   the corpus run;
6. the exact manifest order for one serial clean-build queue beginning with
   `deir_main`, with no historical completion eligible as a queue result;
7. that `deir_main` passes fresh conversion sealing, derived producer stages, all
   document processes, and an exact within-run reuse invocation before the second
   ordered source starts;
8. after the main-report checkpoint passes, a serial work queue that completes each
   source through the document pipeline before starting the next source, without
   weakening resource limits. For Appendix G2, replace the failed monolithic boundary
   with Task 03H.2's accepted chunk contract: deterministic fixed-size ranges, one worker,
   independently verified child seals, one whole-document aggregate pass, and no
   downstream stage before aggregate completion verifies;
9. stage-specific invalidation and restart behavior:
   - record-mapping or later-process changes reuse sealed Docling and derived parsing
     evidence when their identities still verify;
   - routing or table changes reuse sealed Docling evidence and rebuild the
     affected derived parsing and downstream stages;
   - source bytes, Docling/model/configuration, conversion-adapter, or
     conversion-contract changes invalidate only the affected conversion
     identity and require an explicit scope decision before rerun;
   - an operational retry or resource-setting change that leaves all
     output-affecting inputs unchanged resumes or checksum-reuses the existing
     identity rather than inventing a new semantic version;
   - a source-specific failure retries only that source, while a shared-stage
     change invalidates only that stage and its descendants;
10. stage-one monitoring, interruption, atomic publication, terminal-state,
   and all-source-accounting requirements;
11. target-index sealing and second-pass no-mutation checks;
12. candidate-handoff policy for failures, including the hard stop for a
   material main-report failure;
13. fixed-subset rerun checks;
14. Task 04 machine-record and review-cache handoff; and
15. retention and isolation of failed or rejected versions.

If the maintained runtime cannot seal and reuse Docling conversion separately
from routing and tables, that is a pre-execution implementation blocker. Do
not compensate by launching a monolithic 35-document parsing run.

Do not change accepted parser, Task 03E.2d hierarchy, schema, or resolution
policy during the run. A material new failure mode stops the candidate for an
explicit Task 03G or owning earlier-task revision.

### G2 post-processing performance repair: 2026-08-26

The successful 3,736-page G2 logs showed two avoidable full-range reads: aggregate
assembly deep-verified every range before reopening the same ranges for ordering,
and derived publication reopened every range again even though the aggregate had
sealed the complete ordering projection. The maintained path now deep-verifies and
restores each aggregate range in one streaming pass, releases decoded range payloads
immediately, and rebuilds derived routing from the aggregate's compact sealed
projection. Aggregate table and structural-marker references are indexed once rather
than rescanning the aggregate document for every page.

The new derived path reproduced all 3,736 published G2 page-route records exactly,
with zero mismatches, in 0.225 seconds. It does not change routing thresholds, table
outputs, reading order, process concurrency, or the one-range-at-a-time memory shape.
The producer code identity now includes the derived route, table-reuse, and reference-
rebinding helpers. No source PDF or model ran for this validation. Focused tests,
Ruff over `src` and `tests`, strict mypy over 347 source files, all 867 tests,
deterministic Task 03H generation, and `git diff --check` passed. The repository-wide
`make check` remains blocked only by pre-existing line-length violations in the
untracked `scripts/classify_volume4.py`, which this repair did not modify.

### Human-maintainability gate: 2026-08-26

The long-running v3 repair arc received a separate code-quality pass before any
further source processing. The pass corrected incomplete behavior-identity
inventories and a partial-table-directory restart wedge; added typed adaptive-plan
profiles and exact page-evidence consistency checks; split the Region Stream fallback
into parser, geometry, text, and typed-record owners; and consolidated all private
Docling aggregate integration behind `DoclingAdapter`. Aggregate publication now
retains explicit lightweight range summaries instead of hollow verified-range
objects, and its document, ordering/table, observation, and completion-last writes
have named responsibility boundaries.

The downstream audit also separated table-label eligibility from mention-source
eligibility, made ambiguous visible-title recovery abstain, restored fail-closed
handling for unanchored broken outline trees, required complete no-table handoffs,
bounded table-geometry clipping to 1.5 points, and persists unterminated TOCs under
their stable fatal code with start-page context. New ownership gates cover the active
chunked, aggregate-memory, ordering-projection, PDFium, and derived-reuse modules and
limit production functions to 80 lines.

Source-free validation passed Ruff, strict mypy over 367 source files, all 905 tests,
deterministic Task 03H generation, and `git diff --check`. No PDF, model, or production
artifact ran. The refreshed production identity is
`exv1-42295c40af2f58c313201140f340bd18e090fb136d6f06ac10b25ccd2882866e`.
Because the repaired range behavior identity now includes the PDFium and routing-
geometry modules that were previously omitted, existing ranges created under the
incomplete identity are not eligible for reuse. The repository-wide `make check`
continues to be blocked only by the unrelated untracked
`scripts/classify_volume4.py` line-length violations.

The final maintainability follow-up removed the remaining broad ordering-projection
dictionaries and machine-local table path. Ordering pages, routing measurements,
table decisions, and table-stage observations are now strict immutable records. The
table-stage reference stores a contained relative path and verifies its completion
marker plus either the complete table inventory or every required no-table handoff
file. Aggregate publication relocates that reference to its own `tables/` child, and
derived reuse resolves the persisted reference rather than maintaining a second path
convention.

The 882-line PDF-outline owner is now a 52-line public facade over separate native-
PDF, traversal, cleanup, normalization, and recovery owners. The 922-line table-page
owner is now a 181-line coordinator over content, geometry, parser, persistence,
routing, and typed-record modules. Ownership tests bound the new modules and functions,
and an integration regression freezes the Lattice, Region Stream, then TableFormer
fallback order. Scratch inspection outputs, repository caches, and Task 03H-labeled
system temporary items were moved to Trash; production artifacts were not touched.
This follow-up intentionally invalidates prior generated identities and confirms that
one final full-corpus run is required.

## Review pass

- **Source accounting:** all and only the 35 model-corpus sources have terminal
  records.
- **Candidate integrity:** every published artifact is checksummed, contained,
  referenced, and covered by the appropriate completion record.
- **Restart isolation:** downstream identities reference exact Docling seals,
  and invalidation tests prove which stage must rebuild for each change class.
- **Stage isolation:** target-index and cross-document passes preserve
  stage-one bytes.
- **Structural consistency:** IDs, hierarchy, labels, aliases, references,
  coordinates, assets, and mappings satisfy the frozen contracts.
- **Warning visibility:** no failure, warning, anomaly, or source exception is
  erased by aggregation.
- **Independent freeze:** the candidate does not claim Task 04 acceptance.

## Validation

- Reconcile inputs against all 35 ordered manifest records and checksums.
- Validate every Docling conversion bundle independently before a derived
  producer consumes it; reject missing, partial, stale, or checksum-mismatched
  conversion evidence.
- Reconcile expected pages for every successful extraction; preserve explicit
  failure coverage rather than fabricating page success for failed sources.
- Validate every artifact role, schema, checksum, contained path, and identity.
- Validate global ID uniqueness and all document, page, block, section, table,
  table-family, figure, image, asset, mapping, alias, mention, and resolution
  relationships.
- Validate bounding boxes against page dimensions and coordinate frames.
- Validate every referenced content asset.
- Verify the target index contains exactly the eligible terminal stage-one
  outputs.
- Verify cross-document resolution leaves stage-one checksums unchanged.
- Recompute aggregate counts instead of trusting separately maintained totals.
- Reinvoke completed clean-run sources under the Task 03H contract and verify exact
  within-run reuse without consulting historical Task 03G or Task 03H roots.
- Exercise the invalidation matrix without rerunning PDFs: a downstream-only
  identity change must reuse sealed Docling evidence, a routing/table identity
  change must rebuild from it, and a conversion-owned change must refuse reuse.
- Interrupt a bounded fixture workflow and verify it resumes from the first
  missing or incomplete source while preserving earlier valid seals.
- Require the checksum-reuse invocation to make zero Docling calls for every
  verified raw conversion candidate and zero model calls for every other
  verified reusable model-owned artifact.
- Compare observed wave and full-run timings against the preflight forecast and
  report the critical path, idle time, retries, and completion variance.
- Verify human-review fields are absent and all Task 02 warnings propagate,
  including K2's `source_edition_override`.
- Verify requested review renders are reproducible cache and excluded from
  completeness.
- Verify Git contains no bulk source or generated extraction artifacts.
- Run:

```bash
make check
git diff --check
```

## Acceptance criteria

- All 35 sources have explicit terminal records under one corpus identity.
- Every successful document has a verified immutable stage-one candidate;
  failures remain failures with deterministic reasons.
- Every successful required Docling conversion has its own verified immutable
  completion, and routing/table or downstream remediation can reuse it without
  model execution when conversion-owned inputs are unchanged.
- Appendix G2 uses the accepted chunked path rather than repeating the failed
  monolithic conversion; interruption retains every verified range and aggregate
  publication remains completion-last.
- The main report completes end to end from a fresh Docling conversion and passes an
  exact within-run reuse invocation before the second ordered source starts.
- No completed main-document raw conversion runs twice under the same frozen
  raw-conversion identity.
- A material native-extraction failure in the main report blocks candidate
  handoff and requires a new decision.
- The target index and cross-document resolution are complete under the frozen
  policy and do not mutate document candidates.
- All-source accounting, candidate handoff, and the later Task 04 freeze are
  represented by distinct records.
- Schemas, IDs, coordinates, checksums, assets, references, and fixed-subset
  rerun checks pass for published candidates.
- Task 04 receives complete machine observations and source-failure records
  without prefilled human dispositions.
- Page renders are absent from canonical completeness claims.
- Generated bulk artifacts remain outside Git.
- The outcome reports exact success/failure counts, pages, bytes, timings,
  warnings, unresolved references, validation commands, forecast variance,
  and Task 04 input.
- For the first execution window, “done by morning” means a complete validated
  candidate and handoff, not merely finished Docling conversions. Elapsed time
  is an operational target rather than a corpus-validity acceptance criterion;
  if only an earlier phase fits the window, the run plan must say so before
  launch.
- The candidate is not called accepted or frozen until Task 04 independently
  validates it.

## Non-goals

- assigning final usability or document dispositions
- reviewing every page or table semantically
- OCR, LLM repair, or visual-question answering
- extracting Final EIR Volume 4 comments and responses
- case screening, evidence authoring, retrieval, generation, or scoring
- changing parser, hierarchy, schema, or resolution policy during the run

## Outcome

Task 03H began as the production full-corpus run intended to publish and validate
one complete 35-document candidate for Task 04. In practice, it became the first
full end-to-end attempt: it drove the production workflow far enough across the
corpus to expose previously unseen fresh-root, no-table, outline, reading-order,
rotation, table-reconstruction, memory, restart, aggregation, and downstream
performance cases. The task repaired those cases as source-general behavior,
added restartable content-aware chunking and compact downstream reuse, and ended
with a separate human-maintainability pass over the accumulated implementation.

The task closes without claiming its original final-publication acceptance
criteria. Its most important product is the maintained, source-free-validated
pipeline and the evidence needed to make the next run trustworthy. The final
typing, ownership, and identity corrections require every source to run again
under a new identity, so no retained Task 03H conversion, producer, downstream,
document, or collection completion may satisfy Task 03J.

The next sequence is explicit:

1. Task 04 performs the user-led review of available Task 03H evidence.
2. [Task 03I](03i_remediate_task04_review_findings.md) dispositions only accepted
   review findings and may close with no code changes.
3. [Task 03J](03j_run_final_canonical_extraction.md) performs a new full-corpus
   end-to-end attempt under a fresh namespace and identity.
4. Task 04 retains ownership of the final usability decision and extraction-release
   freeze after Task 03J hands off its candidate.

Final source-free validation passed Ruff, strict mypy over 367 source files, all
905 tests, deterministic Task 03H generation, and `git diff --check`. No PDF,
model, or production artifact ran during the closing maintainability pass. The
last prepared Task 03H identity was
`exv1-42295c40af2f58c313201140f340bd18e090fb136d6f06ac10b25ccd2882866e`;
it is historical evidence, not the Task 03J production identity.
