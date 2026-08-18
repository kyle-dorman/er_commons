# Task 03G.2f: Repair Cross-Document Resolution

Status: **completed and accepted on 2026-08-18**. The maintained
downstream-only replay reproduced the required behavior, exact pilot controls,
sealed handoff, aggregate report, and identical reuse proof without running an
upstream content owner or allocating a document attempt.
Do not run a PDF reader, Docling, Camelot, TableFormer, another model, or any
producer stage. Reuse every checksum-valid completion through semantic
materialization.

## Abstract

Repair the empty cross-document result exposed by review of the completed
three-document Task 03G.2 pilot. The corpus resolution stage sealed correctly
but received zero eligible mentions, even though the main Draft EIR contains
at least eight references to Appendix D and ten references to Appendix P. The
local stage classifies these as unresolved appendix mentions, while corpus
resolution accepts only `deferred_cross_document` document mentions. A second
exact-match mismatch separates short reviewed source aliases such as
`appendix d` from the indexed document title
`appendix d - biological resources technical report (pdf)`.

Define one source-family catalog used consistently by local deferral and corpus
resolution, preserve within-document resolution as the first choice, and join
an externally deferred mention to a document target through the sealed source
identity rather than repeated display-title equality. In the same downstream
rebuild, implement the user-approved change from a five- to ten-physical-page
table-mention window and prove its exact effects. Preserve every prior pilot
candidate and the empty-resolution result as immutable evidence.

## Why this is a separate remediation

Task 03G.2 already owns a completed fresh execution, five bounded remediations,
sealed producer and downstream candidates, a ready handoff, an identical reuse
result, and an aggregate report. Rewriting that contract would obscure the
observed failure. This task follows Tasks 03G.2a-03G.2e: retain the completed
attempt, repair the responsible policy boundary, publish new downstream
identities, and then amend the parent outcome.

Task 03G.2 remains execution-complete but cannot close while this task is open.
Neither task may close merely because code and fixtures pass. Closure requires
the ten-page table-link policy to run on the preserved three-document scope and
the repaired cross-document stage to publish and validate a nonempty result.

## Observed evidence

The retained Task 03G.2 scope is:

```text
scopev1-2096b371305552b6ec927bda3d5f6ff8285dd40bd5e9b168747f39cad21b6a95
```

Its sealed target index is:

```text
idxv1-d6d4132b1442794e198b063faa061c1be8fb3e37cc7c59e79f05c2085b94513a
```

The index contains 4,893 verified alias-target entries: 3 document, 4,634
section, 12 table, 244 page, and zero figure entries. The retained resolution
candidate is:

```text
resv1-9f53bdde1e9c27d4147ac0d1c45147e472dd503df5c0740432582d5efb69521a
```

Its completion record is valid but reports zero eligible mentions and zero
resolved, ambiguous, or unresolved corpus records. This proves lifecycle and
empty-input behavior, not useful cross-document resolution.

The completed document candidates expose these relevant local observations:

- `deir_main`: zero `document` mentions; 187 `appendix` mentions, all
  unresolved with `no_local_alias`, including 8 `appendix d` and 10
  `appendix p` mentions;
- `deir_appendix_d`: zero `document` mentions; two internal `appendix b`
  mentions resolve locally and two `appendix a` mentions remain locally
  unresolved; and
- `deir_appendix_p`: one named external-document mention remains
  `external_document_outside_corpus`; its internal appendix mentions include
  two `appendix d` mentions that already resolve locally and must continue to
  do so.

Current stage-one document-name keys are derived conservatively from the
source manifest, while stage two consumes a separate reviewed scope catalog.
The local resolver emits `deferred_cross_document` only for `document`
mentions whose exact key is in its catalog; unresolved `appendix` mentions
fall through to `no_local_alias`. Stage two then filters exclusively for
`deferred_cross_document`, hard-codes the derived mention class and target
type to `document`, and requires the mention lookup key to equal an indexed
document alias. The short scope alias `appendix d` therefore never enters the
stage and would not equal the indexed official-title alias even if it did.

## Goal

Demonstrate useful, precision-first cross-document resolution over the fresh
main, Appendix D, and Appendix P candidates without changing their source,
producer, canonical, hierarchy, or semantic evidence. Resolve verified sibling
documents through source identity, preserve genuine local appendix ownership,
make all uncertainty explicit, and publish a new ready pilot handoff whose
ten-page table-link outcomes are exact and whose identical invocation reuses
the completed result.

## Inputs

- active parent [Task 03G.2](03g2_run_three_document_full_pilot.md);
- retained Tasks 03G.2a-03G.2e outcomes and failed/completed attempt evidence;
- the three latest checksum-valid Task 03G.2 document candidates and their
  six owner-stage completion seals;
- the sealed Task 02 source manifest and the three-document scope catalog;
- `docs/specs/cross_references_v3.md` and
  `docs/specs/restartable_corpus_extraction_v1_1.md`;
- maintained `cross_reference_enrichment`, `corpus_resolution`, document
  publication, scope indexing/resolution, handoff, and reporting owners; and
- the retained five-page replay evidence summarized below.

Before allocating new work, the executing chat must verify every referenced
completion seal and inventory and reuse all valid inputs. The latest accepted
upstream candidates must be discovered from their completion records rather
than copied from this prose when identities differ.

## Required policy decisions

### One source-family catalog

Replace the split stage-one/stage-two alias understanding with one checksummed,
reviewable catalog contract. For every in-scope source it must identify:

- sealed source identity and checksum;
- source-family/root ownership;
- document role, including root report, top-level appendix, or appendix part;
- explicit parent source when applicable; and
- reviewed reference aliases used to map source text to intended source IDs.

Both local deferral and corpus resolution must consume the same semantic
catalog bytes or a mechanically verified projection of them. Do not derive
different alias vocabularies independently in the two stages. Do not add
source-specific `if source_id == ...` branches or a correction table keyed to
the reviewed mentions.

### Local first, corpus second

For an appendix or named-document mention:

1. attempt the maintained exact within-document resolution first;
2. preserve any unique local target, including Appendix P's internal
   `Appendix D` targets;
3. only after local failure, use source-family role and explicit source text
   evidence to determine whether the mention names a sibling corpus source;
4. allow the main/root EIR to refer to its cataloged top-level appendices;
5. from a nested appendix, do not reinterpret an unqualified internal
   `Appendix X` as an EIR sibling unless an explicit `EIR`, `DEIR`, full-title,
   or equivalent reviewed family qualifier supports that traversal; and
6. keep external named documents outside the sealed family unresolved.

The persisted local mention must retain its original class, text, span,
source record, page, and local outcome. Cross-document eligibility and
catalog evidence must be explicit and independently verifiable; do not mutate
source text or fabricate a local target.

### Source identity selects the document target

The catalog maps a normalized mention alias to one or more intended source
IDs. Corpus resolution then joins each intended source ID to that successful
source's unique sealed document record. It must not require the mention alias
to equal the extracted official-title alias a second time.

- one intended successful source with one document record: `resolved`;
- multiple intended sources or document targets: `ambiguous`;
- successful intended source without a document target: `target_unavailable`;
- failed intended source: `target_source_failed`; and
- cataloged intended source outside the run scope: `target_not_in_scope`.

Stage two remains append-only over immutable stage-one candidates. It may
publish new resolution records but must not rewrite document content.

### Ten-page exact-table window

Change the exact table-mention window from physical-page distance 0-5 to 0-10.
Distance continues to filter independently verified exact aliases; it never
creates an alias. Qualified external table references remain unresolved, and
multiple distinct in-window targets remain ambiguous.

The preserved three-document replay predicts exactly these changes:

- six Appendix P mention records become resolved: two `Table 2` mentions on
  physical page 24 to the target on page 30; `Table 6` on page 55 to page 61;
  `Table 7` on page 55 to page 63; `Table 8` on page 58 to page 65; and
  `Table 13` on page 91 to page 84;
- two `Table 9` mentions on page 58 become ambiguous because distinct verified
  targets occur on pages 67 and 68;
- twelve records remain outside the ten-page window, at nearest exact-target
  distances 19, 25, 25, 36, 38, 41, 44, 47, 49, 51, 53, and 79;
- no previously resolved table mention changes target or becomes ambiguous;
  and
- main and Appendix D table-link outcomes do not change because their reviewed
  failures lack exact table aliases rather than nearby eligible targets.

These are acceptance expectations for the retained pilot, not universal
corpus counts. Any mismatch must stop publication and be explained before the
parent task can close.

## Outputs

- a reviewed source-family catalog contract and three-source catalog instance;
- updated cross-reference and corpus-resolution specs, schemas, policy inputs,
  identity coverage, and source-general implementation;
- synthetic and retained-evidence tests covering positive, negative,
  ambiguous, failed-source, out-of-scope, and local-ownership cases;
- a candidate-neutral before/after report over all affected pilot mentions;
- refreshed cross-reference candidates for the affected sources;
- refreshed document candidates using every valid upstream completion;
- refreshed exact scope accounting, target index, nonempty corpus resolutions,
  handoff, aggregate report, and request-only render recipe;
- one identical invocation proving checksum reuse without new PDF, model,
  producer, canonical, hierarchy, semantic, or document attempt allocation;
  and
- completed Outcome updates for this task and Task 03G.2 when all gates pass.

## Plan

1. Verify the three selected sources, current completion seals, inventories,
   owner-stage IDs, and empty-resolution evidence without reading source PDFs.
2. Inventory all local mentions that may identify another source. Freeze a
   review table containing source, text, qualifier context, local outcome,
   proposed intended source IDs, and expected cross-document disposition.
3. Amend the cross-reference and corpus-resolution contracts and their
   executable schemas/fixtures before changing runtime behavior.
4. Implement one shared source-family catalog boundary, local-first deferral,
   and source-ID-to-document-target resolution with responsibility-oriented
   modules and explicit diagnostics.
5. Change the exact table window to ten and add exact boundary tests at
   distances 5, 6, 10, and 11, plus multiple-target and qualified-external
   controls.
6. Run focused and full offline tests. Perform a separate maintainability
   review of catalog ownership, resolver responsibilities, error messages,
   identity inputs, and fixture independence.
7. Build a candidate-neutral replay from sealed semantic and local
   cross-reference inputs. Confirm the required local/cross-document controls
   and exact table-window deltas before publication.
8. Reuse every valid completion through semantic materialization and publish
   only the invalidated cross-reference, document, scope-index, resolution,
   handoff, and reporting descendants.
9. Validate the new handoff, run the identical scope invocation once, and
   prove exact checksum reuse with no new upstream or document attempts.
10. If every closure gate passes, write this task's Outcome, amend Task 03G.2's
    outcome and status, update `docs/index.md` and `docs/todo.md`, and close
    both Task 03G.2f and Task 03G.2 in the same execution chat. If any gate
    fails, preserve the attempt and leave both tasks open.

## Required controls

- every reviewed main-report `Appendix D` reference intended for the
  Biological Resources Technical Report resolves to `deir_appendix_d`;
- every reviewed main-report `Appendix P` reference intended for the Water
  Supply Assessment resolves to `deir_appendix_p`;
- at minimum, the retained 8 main-to-Appendix-D and 10
  main-to-Appendix-P mentions enter corpus resolution with explicit outcomes;
- Appendix P's two currently local `Appendix D` mentions remain locally
  resolved and do not enter corpus resolution;
- Appendix D's unqualified, locally unresolved `Appendix A` mentions do not
  automatically resolve to a top-level EIR Appendix A source;
- the named Genentech Draft EIR remains
  `external_document_outside_corpus`;
- source absence, source failure, multiple catalog owners, and missing document
  targets retain their exact reason-specific outcomes;
- catalog aliases cannot target an unsealed source or a target outside the
  source's verified document stream;
- the before/after candidate inventories prove stage-one immutability during
  corpus resolution; and
- the ten-page table outcomes match the exact replay expectations above.

## Validation

Before publication:

```bash
make fix
make validate-extraction-contract
make check
git diff --check
```

Also require:

- focused contract and implementation tests for the shared catalog, local
  disposition, target-index construction, corpus resolution, identity, and
  publication boundaries;
- a no-PDF assertion covering the entire task attempt;
- exact verification of all reused completion seals and managed inventories;
- zero mutation of any retained Task 03G.2 candidate;
- exact affected-mention accounting before and after the policy change;
- nonempty published corpus-resolution records with exact mention coverage;
- read-only handoff validation and report validation;
- an identical scope invocation returning the same bundle and handoff bytes;
  and
- no new producer, canonical, hierarchy, semantic, or document attempt.

## Closure criteria

Task 03G.2f closes only when all validation passes, the repaired pilot publishes
and validates, the corpus-resolution result is nonempty, every required local
ownership control passes, the ten-page table-link policy has actually run with
the expected exact outcomes, and an identical invocation proves reuse.

Task 03G.2 cannot close before Task 03G.2f. Passing fixtures, producing a new
identity, or preparing a replay is insufficient. The executing chat may close
both tasks only after the newly published handoff and report satisfy every
criterion above. Task 03H remains provisional and must not activate in this
task.

## Non-goals

- rerunning or reading source PDFs;
- Docling, Camelot, TableFormer, OCR, learned-model, producer, canonical,
  hierarchy, or semantic execution;
- lowering the 90 percent learned-table native-text coverage threshold;
- accepting Appendix D Table 1 as a canonical table without that threshold;
- figure aliasing or figure-link resolution;
- implementing heading/caption retrieval or the later BM25/model search layer;
- resolving every long-range table mention beyond ten physical pages;
- full-35-source execution or claiming corpus-wide recall;
- activating Task 03H or freezing the extraction release in Task 04;
- editing historical Appendix P lineage; or
- commit or push unless separately authorized.

## Handoff to the executing chat

Start from `AGENTS.md`, `docs/index.md`, `docs/todo.md`, this task, and the
parent Task 03G.2. Read the directly named cross-reference and restartable
corpus specs plus the maintained catalog, local-resolution, target-index,
corpus-resolution, publication, and reporting owners. Verify current
completion seals before allocating work. Historical Appendix P lineage remains
forbidden; use only the fresh Task 03G.2 lineage and its valid descendants.

The user has authorized implementation, offline validation, the downstream
three-document replay, one identical reuse invocation, and the documentation
needed to close Task 03G.2f and Task 03G.2 after success. The user has not
authorized PDF/model/producer reruns, Task 03H, a commit, or a push.

## MVP execution evidence, not closure

Completed one checksum-bound source-family catalog shared by local enrichment
and corpus resolution. Local exact resolution remains first; nested traversal
requires adjacent EIR-family evidence; and literal mention evidence remains
immutable. The corpus index now binds an independently derived
`document_targets.jsonl` stream and joins intended source IDs to sealed
document records rather than comparing display titles twice.

The ten-page replay produced exactly six newly resolved Appendix P table
mentions at distances 6, 6, 6, 7, 7, and 8; two `Table 9` mentions became
ambiguous at distances 9 and 10; and twelve remained outside at nearest
distances 19, 25, 25, 36, 38, 41, 44, 47, 49, 51, 53, and 79. No previously
resolved table changed. Appendix P's two local Appendix D mentions remained
local, Appendix D's two unqualified Appendix A mentions remained
local-unresolved, and the Genentech Draft EIR remained outside the family.

Final production identity
`exv1-d508a2d557b04b8d0542dc11531d85f16ce3020599019d69611646fc8fb72cac`
published replay-only documents
`docv1-8b32d1948c0c8d1dc2054eeb1b5c920b527deb80bb79a44d94b612bd51bd05e0`,
`docv1-f65036ab6a9fe0a9a2377d39465592864c099c22532e450e888f0df87abaf169`,
and
`docv1-e2047e1570be5a0d0ea4dd60c138f4c0997fecb1259b20268c458a615a4bd336`.
Scope
`scopev1-45e05f55179892400e842c3de1726aa8b7c63e47571509648c378ce99aa64771`
sealed index
`idxv1-a6f48afb078c8397f80657bb9f134a2e7922aa7a4746d01a8fc3711fce5682f4`,
resolution
`resv1-9ef0065d21337c21e9159a18c37e6594bd6bad8691e2d961c87148dabe9e1be5`
with 18 eligible and 18 resolved records, and ready handoff
`handoffv1-4c7f5b1fac7b529b3e0bf1ca941d21b2100e23b7d492d760e4b26c9ace3ea663`.
The identical invocation reused bundle SHA-256
`2a9add5c931d138ad2971a6e6e2e8719b9900835d7d8acbe3faa9af28f3c2383`
and handoff SHA-256
`d8082bfaf275f698c645eb62047ab1a39cefdab814442ee070307f4b6b6df50f`.
Forbidden attempt-path snapshots were unchanged; no PDF, parser, model,
producer, semantic, or document attempt ran.

MVP validation: Ruff clean, mypy clean, 513 tests passed, restartable
extraction contract v1.1 valid, read-only handoff validation passed for all
three documents, aggregate reporting and the request-only recipe completed,
and `git diff --check` passed. These gates establish behavior, not
maintainability acceptance. No commit or push was made.

## Human-maintainability refactor

The 2026-08-18 offline refactor replaced the 364-line task runner with a
45-line CLI and responsibility-owned modules for explicit path policy,
retained-source verification, source replay, attempt-inventory isolation,
candidate-neutral mention auditing, table-window auditing, and scope
publication. The downstream document publisher now separates verified input
loading, candidate construction, atomic publication, and seal validation.
Typed immutable records carry replay paths, outcomes, source lineage, and
attempt inventories. Replay invariant failures carry stable codes plus useful
expected, observed, source, operation, and path context.

The new offline maintainability suite prevents replay modules from growing
beyond 220 lines or individual functions beyond 60 lines, requires the CLI to
remain portable and under 60 lines, and directly tests intended-source
evidence, local-versus-external ownership, attempt-isolation diagnostics, and
the named table delta. The complete offline project gate now passes 520 tests,
Ruff formatting and lint, mypy over 260 source files, restartable extraction
contract validation, and `git diff --check`.

No replay or pipeline stage ran during the refactor itself. The refreshed
checked production recipe is
`exv1-ca6cafcb781e5e0ae87defbf7746ac088ef9369f493c75605fee9744d8f4a0d9`;
the maintained bounded replay executed it only from the three sealed semantic
owners. The prior MVP candidate and handoff IDs above remain immutable
execution evidence.

## Maintained replay acceptance and closure

The user authorized the bounded maintained replay on 2026-08-18. It published
cross-reference candidates
`exv1-1901756eb37990b35b8414fb816091c6c0cabd68aad82a4067ed645e97626d73`,
`exv1-782d87914d3a64d274e0e3425481cd7a4d749073b4d84be0e9b8b7705181f0d7`,
and
`exv1-09a0ba74461aca9e3e4304504e3099003636b4c07b61100093b5b48be56cdd05`,
then downstream-only document candidates
`docv1-df061971dfe4f9fc93cfb41ec595e797c794c3fe2faeb0266968c59c24156f87`,
`docv1-54c180d7b26a5b2fb14dd4e9c822dcb14d568791a948dbe973c44f283538388e`,
and
`docv1-c50e373901049e68dce923bd6eedaa5977387e8c6c24a4997078d9b99b9a1e37`.

Scope
`scopev1-c52bba178cf47e9338bae9f200c31f4a0e4c135d8b0a8154535b7b0357beb6a8`
sealed index
`idxv1-266e8801add2ffe2f158f033ad00677b0e64e74a3a3bf1991734b5f812b1d5b1`,
resolution
`resv1-5c30b44d9be2b8e6b2ba11afc1cb1f85595b2e72106172df72a7704e13396c5a`
with 18 eligible and 18 resolved records, and ready handoff
`handoffv1-78262d2ea1f47faa0c1c6c6e6c3479e86a408f9c32d442cc708c20d5306582`.
The identical invocation reused bundle SHA-256
`1bda361b3c28efa4d1715a8378d74366024160c3542325bdd462c2483bf5d14e`
and handoff SHA-256
`a83908ed4f4e4e8719a0c9740117f7cc4a040e9cde1bbbc6b5891c342f7d5dcd`.

Independent handoff validation verified all three documents and retained
`task04_status: not_evaluated`. The refreshed aggregate report exactly matches
the prior accepted document totals, anomaly counts, resource extrema, 4,893
target-index entries, and 18/18 resolution outcome. Its completion SHA-256 is
`049ba8f7db093fd8ab0817188ba2a01d4901cb5625fe0e9e6543c9a7872bda5c`.
The refreshed request-only recipe has request SHA-256
`7f64cb256eded40cf0bae7d1fde7d8b855efaef66e4c031a2d4a1bd310e4d082`
and generated no renders.

All exact table-window and local-ownership controls passed. The producer,
canonical, hierarchy-correction, semantic, and document-attempt directory
inventories were byte-identical before and after replay. Final offline gates
passed 520 tests, Ruff, mypy over 260 source files, restartable extraction
contract validation, and `git diff --check`. Task 03G.2f is closed together
with Task 03G.2. No commit or push was made, and Task 03H was not activated.
