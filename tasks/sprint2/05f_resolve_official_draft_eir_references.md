# Task 05F: Resolve Official Draft EIR References

Status: **complete with an accepted partial outcome; further replay and linking
iterations move to Task 05G after the Task 06 repair umbrella**.

## Goal

Resolve official-response references to exact Draft EIR targets through Task
04D's designated handoff, annotate Task 04A usability, and preserve complete
mention provenance. Begin with a source-free exact baseline and stop with its
failure census before proposing any broader rule.

This is an MVP stage. It must be precise, restartable, and reviewable, but it
must not create a new resolver framework, workflow engine, artifact system, or
review application.

## Fixed boundaries

- Final EIR Volume 4 remains curator-only and outside the Task 03 model corpus.
- Task 03J, Task 04A, Task 04D, Task 05D, and Task 05E are immutable inputs.
- Task 04D is the only target/alias view; do not compose Task 03J links with the
  superseded Task 04C overlay.
- Appendix Q is separate from Draft EIR resolution and is not extracted here.
- No PDF may be opened, rendered, extracted, copied, or hashed.
- No accepted large source-record, graph, target-index, or upstream payload may
  be rehashed. Trust its accepted identity, inventory, recorded checksum, path,
  size, and terminal metadata.
- No fuzzy, substring, embedding, page-only, neighboring-order, semantic, or
  LLM-selected matching is permitted.

## Exact accepted inputs

Preflight must read and validate the compact acceptance, completion, and
inventory records. Caller-supplied identity strings are not proof of acceptance.

### Task 05D

- candidate/activity:
  `revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030` /
  `activityv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030`;
- completion:
  `completionv1-82d534e4e3cc7db7275892690fe4d357540131c9477775d5ebf1d54ad6ab555f`;
- inventory:
  `fileinventoryv1-a04c715a6dff6bdfe6d28eaed9b40211382d60a74d540cdf46cd3b2c993c60a0`;
- semantic digest:
  `f7aa9fd6e6d4e464b27b270e6f61a8dcbfb0d998dc44e7eda84abd07db5d9247`;
- acceptance:
  `acceptancev1-7edf64ffd5e283c736e9980c79f682997ce06c135038d4ceb3ecbc496ce6c027`.

### Task 05E

- candidate/activity:
  `revisionv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1` /
  `activityv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1`;
- completion:
  `completionv1-867b3e6f9d9cc1e2666cb184523590c2fd02154347ea9787144e61bb43851555`;
- inventory:
  `fileinventoryv1-924533bd3c59160bd0853aa38dc095965b07b2d4bf2d78a5ad9431cd2836f667`;
- semantic digest:
  `3a6f5b0f4f116b2800e0a8b02bb98fde9d37a48ccc0baff321fd484f2489e71b`;
- acceptance:
  `acceptancev1-4b8a13393c57660fdb0a6b303912150ca9d1380688a86a6728267a4c79aacac5`,
  designating Task 05F as downstream consumer.

### Task 04A and Task 04D

- Task 04A review: `reviewv1-task03j-final-c17/gate_d/`;
- Gate D completion SHA-256:
  `d480aa903d7ae65e7a4b1b6de93ad4cdebe6963e6fd724873ade548790712826`;
- usability registry SHA-256:
  `0453aaf13cb7762e7718ce869ee3f1521a67625224bd35c83b641cc5ae8d47e1`;
- ambiguous dispositions SHA-256:
  `9d3b8ac7c9fea34ecada607c99b96376d648c2ab419bfa381abbf30f4b2e3366`;
- unresolved-risk report SHA-256:
  `b6ac41902ffdfc6c93b13c0be93af5d071f3811334a27367fc2ccdacf2f7a5ca`;
- Task 04D handoff:
  `handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`;
- handoff completion SHA-256:
  `387a07d62d96e4c5aba6f1f3d51f7f9026719b0d7de1b4eece06bed9fd78bc81`;
- production/scope:
  `exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3` /
  `scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da`;
- target index:
  `idxv1-31a3eacee1d03001d44f79d2fa15563cfd416b9a80c02e8d178d0843e4bb4a00`,
  completion SHA-256
  `a661cfefed67927b7536fe791eb6f6dcfe705dc044e4e4dc9867977790cdfa31`;
- exact source-family catalog referenced by the accepted Task 04D collection
  specification.

Preflight verifies these recorded bindings without rehashing their payloads.
Read only the accepted source records, graph records, registry records,
source-family catalog, and target-index rows required by resolution.

## Observed population

The accepted Task 05D records contain:

- 509 `draft_eir` references: 456 from responses, 42 from General Responses,
  and 11 from comments;
- 2 `appendix_q` references; and
- no `final_eir`, `external`, or `unknown` references.

Gate 1 must reproduce these counts exactly or fail closed.

## Authorization gates

1. **Contract:** accept this revised contract.
2. **Gate 1:** separately authorize source-free implementation and the exact
   baseline run.
3. **Gate 2:** after reviewing Gate 1 failures, separately accept any bounded
   rule amendments and authorize replay.
4. **Terminal candidate:** after validation and human code-quality review,
   separately authorize terminal publication and later acceptance.

No gate implicitly authorizes cleanup, commit, push, Task 05G, or source access.

## Gate 1 exact policy

### Query projection

- Preserve raw target label, mention ID, span ID, source unit ID, raw-text
  checksum, authorship, and domain.
- Remove only an enumerated Draft EIR domain qualifier already observed in the
  accepted records. Preserve the qualifier and derived target phrase separately.
- Apply only Task 04D's accepted exact alias canonicalization to that target
  phrase. Record raw, projected, and canonical values.
- Do not add synonym, suffix, punctuation, abbreviation, typo, or semantic
  recovery. Unsupported forms close individually.

### Source compatibility before uniqueness

- Chapter, main section, table, figure, and page references may query only
  `deir_main` targets.
- Appendix references first map by exact source-family-catalog alias to one
  appendix source or multipart family, then query only that source or family.
- Exact aliases found only outside the routed source are negative controls, not
  candidates.
  `Draft EIR Chapter 8`, for example, cannot resolve to `deir_appendix_e`
  merely because that is its only corpus-wide exact match.
- Missing, ambiguous, or unsupported source routing closes explicitly before
  target selection.

### Target compatibility and cardinality

- Require a compatible Task 04D target type.
- Deduplicate alias rows by target ID before measuring cardinality.
- Resolve only one unique source-compatible, type-compatible target ID.
- Report zero targets, true collisions, aliases found only outside the routed
  source, incompatible types, and unsupported forms separately.
- Every `exact_target_collision` outcome must retain the complete deduplicated
  `compatible_target_ids` candidate set in deterministic target-ID order. A
  compact collision report may dereference labels, pages, and headings from the
  bound Task 04D index; individual outcomes must not copy that target content.
- A later human selection, if any, must be a separate review or override record
  that preserves the original collision outcome and candidate set.
- Never create a target or alias from mention text.

### Required closures

- Preserve all 11 comment-authored references and close them without links as
  `comment_authored_reference_no_official_response_link`.
- Close both Appendix Q references as `appendix_q_verification_required`.
- Unexpected Final EIR, external, or unknown domains fail the frozen population
  check and remain separate terminal classes.

## Usability mapping

Structural resolution, Task 04A usability, and visual usability are independent.

| Evidence | Link usability |
| --- | --- |
| Task 04A source is `eligible` and no applicable exclusion exists | `usable` |
| An explicit applicable Task 04A limitation exists | `usable_with_warning` |
| Applicable evidence is ineligible, repair-required, unresolved for trusted use, or excluded | `unusable` |
| Task 04A does not govern the outcome | `not_applicable` |

Join Task 04A dispositions only through explicit identities. Its 725 unresolved
source-link dispositions do not make every target in those sources unusable.

For exact figure targets, record `visual_evidence_usability` separately as
`usable`, `usable_with_warning`, `unusable`, `not_reviewed`, or
`not_applicable`. Figure type alone does not create a warning. The designated
index currently has zero figure targets, so Gate 1 must report zero explicitly
and close figure references under a specific absent-target reason.

## MVP implementation and outputs

- Extend the existing `response_inventory` package and `er-responses build`
  dispatch; do not add a second CLI or general framework.
- Reuse existing run-spec, identity, validation, JSONL, and atomic-write helpers.
- Add one small 05F run-spec variant and at most one narrow Gate 1 outcome schema
  if the accepted record union cannot represent complete accounting.
- Use a few typed resolver functions with clear source-routing, compatibility,
  and cardinality boundaries.
- Do not build HTML or a review application for Gate 1.

Write one activity-derived `working/05f/baselinev1-<identity>/` baseline. The
identity uses recorded upstream identities/checksums plus small checked-in
config, schema, and implementation digests; it does not hash upstream payloads.
The CLI derives the output path. Use existing atomic writes and write one compact
baseline receipt last. Identical valid output may be reused; changed policy or
code gets a fresh identity. Gate 1 does not add an acceptance command.

The baseline contains:

- activity and dependency references;
- one schema-valid outcome per mention;
- schema-valid Draft EIR links and nonlink diagnostics;
- collision, outside-routed-source, incompatibility, usability, visual-status,
  and failure censuses with explicit zero classes;
- mention-to-link and derived target-to-link ID indexes without copied text;
- compact output inventory, semantic digest, and baseline receipt.

Hash only newly authored compact 05F files and small checked-in code, config, or
schema inputs. Do not copy or hash accepted large upstream payloads.

## Validation and review

- Reconcile every mention to exactly one outcome and every nonlink to one
  diagnostic.
- Prove source filtering precedes cardinality and retain exact aliases found
  only outside the routed source as negative controls.
- Validate target-ID deduplication, type compatibility, schemas, provenance,
  forward/reverse index closure, identity invalidation, deterministic shuffled
  input, clean reuse, and partial-state rejection.
- Prove no PDF access, large upstream hashing, or upstream mutation.

Focused tests cover exact aliases found only outside the routed source, true
collisions, same-target multi-alias rows, type conflicts, appendix-family
routing, comment and Appendix Q closures, figure visual separation, all
usability mappings, accepted-pointer binding, schema rejection, provenance,
identity changes, ordering, and receipt reuse.

After Gate 1, present complete counts, collisions, outside-routed-source
controls, unsupported forms, figure outcomes, usability counts, and proposed
amendments.
Grouping never replaces individual accounting. Stop for user review before Gate
2.

Before a terminal candidate, perform a human code-quality gate focused on
readability, editability, debugging, tests, and avoiding unnecessary framework
code. Formatting, linting, strict typing, focused tests, all repository tests,
and `git diff --check` must pass.

## Gate 1 outcome

The user accepted this revised MVP contract and authorized source-free Gate 1.
The designated exact baseline is
`baselinev1-ab5bedfb5990b90cec279abb7a9f07b1f47ea433f434eb4ececcbc3b4bcff62d`
with semantic digest
`11d6cb0b2dc69fcedf21d4219c2b2339674ebb28f9bec4846882f7caea83a5d9`.
An identical second invocation reused its bytes. No PDF was accessed, no large
upstream payload was hashed, no stage completion was written, and Gate 2
remains unauthorized.

All 511 in-scope mentions have one individual outcome: 27 exact Draft EIR
links and 484 terminal nonlinks. The frozen population reproduced exactly:
509 Draft EIR mentions (456 response, 42 General Response, and 11 comment) and
2 Appendix Q mentions, with zero Final EIR, external, or unknown mentions. All
27 links target exact `deir_main` chapter sections and map to Task 04A `usable`;
none is a figure, so visual usability is `not_applicable` for every Gate 1
outcome.

The failure census is:

- 282 `exact_target_absent`;
- 79 `exact_figure_target_absent` (the accepted target index contains zero
  figure targets);
- 76 `appendix_source_route_absent`;
- 34 `wrong_source_exact_match`, retained as negative controls under the Gate 1
  schema; later candidates rename this class
  `exact_alias_only_outside_routed_source` without changing its meaning;
- 11 `comment_authored_reference_no_official_response_link`;
- 2 `appendix_q_verification_required`; and
- zero exact collisions, target-type incompatibilities, or unsupported forms.

## Upstream recovery pause

Rule qualification established that accepted `deir_appendix_f1` is a 75-page
Bayshore Mobility Study rather than the advertised Transportation Impact
Assessment. All 66 F1 mentions are therefore provisionally closed as
`upstream_source_identity_repair_required`; no current F1 match or absence may
become terminal.

Qualification also found duplicate logical chapter targets in
`deir_appendix_a`: `06 CIRCULATION` / `06 | CIRCULATION` and `08 PUBLIC
FACILITIES FINANCING` / `08 | PUBLIC FACILITIES FINANCING`. Task 05F must retain
these as collisions rather than choose a target.

[Task 06](06_repair_reference_sources_and_target_index.md) owns the fresh F1
source substitution, source-general target repairs, minimum upstream replay,
targeted usability review, and replacement handoff. The accepted Task 05D and
Task 05E records remain fixed. Task 05G will consume that handoff and replay
these source-free rules.

A strict source-free trial of the unique direct appendix-document rule and its
subsequent maintained implementation resolve 23 non-F1 mentions. Six apparent
document cases are more-specific references—Appendix A Chapters 06 and 08,
Appendix D Figure 3 and page 2-21, Appendix F2 Figure 4, and multipart Appendix
K1 Figure 4a—and are not downgraded to document links.

## Implemented Gate 2 exact rules

The following source-free rules are implemented and replayed in a nonterminal
working candidate:

1. For a direct chapter, section, or table mention whose exact short identifier
   is absent, derive identifier aliases only from the leading identifier of
   accepted Task 04D aliases in the same source and target type. Keep chapter
   identifiers distinct from section identifiers. Resolve only a unique target;
   otherwise retain the complete exact candidate set as a collision.
2. Before closing an identifier collision, test an immediately attached,
   comma-delimited title against the accepted full aliases for those candidates.
   Task 04D whitespace normalization, including source line wraps, is allowed;
   word deletion, substitution, reordering, or semantic comparison is not. The
   extended alias must resolve to exactly one compatible target.
3. The attached-title rule takes precedence over the identifier-only collision.
   A number-only mention remains `exact_target_collision`; another mention in
   the same response cannot supply its title or resolution.
4. For a top-level appendix designator, normalize only an optional period or
   hyphen between one appendix letter and its numeric suffix. Query only the
   independently accepted source-family catalog and preserve all physical
   sources when a multipart appendix remains plural.
5. After routing an outer-only appendix mention, link one unique existing
   document target. If the same sentence attaches a chapter, section, table,
   figure, or page target, retain a specific terminal outcome rather than
   replacing it with the broader document link.
6. Close every F1-routed mention as
   `upstream_source_identity_repair_required` until Task 06 supplies the
   replacement handoff.
7. For a numeric section identifier ending in one alphabetic designator, compose
   an exact subsection candidate only from the accepted numeric parent target,
   its accepted direct-child hierarchy edges, and a child alias beginning with
   that same alphabetic designator. An optional dot before the designator is
   equivalent. One target resolves, multiple targets collide, and no target
   remains absent. Do not descend beyond direct children or substitute the
   parent when the child is absent.
8. Extend direct section identifiers to the literal `ES` prefix while retaining
   the same source, target-type, and candidate-cardinality controls used for
   numeric identifiers.
9. For a three-part numeric table mention written with two periods, normalize
   only the final separator to the published table hyphen; for example,
   `Table 4.3.2` queries `Table 4.3-2`. Do not alter any other components.
10. For a two-part section mention using a hyphen, normalize only that separator
    to the published section period; for example, `Section 4-11` queries
    `Section 4.11`. Preserve every candidate if the normalized identifier
    collides.

Qualification of the 36 identifier collisions found 29 exact attached-title
resolutions and 7 remaining collisions:

- Section 4.5: 2 resolved, 1 collision;
- Section 4.6: 12 resolved, 3 collisions;
- Section 4.11: 6 resolved, 0 collisions;
- Section 4.12: 2 resolved, 1 collision;
- Section 4.13: 7 resolved, 1 collision; and
- Section 8.5: 0 resolved, 1 collision.

The maintained source-free replay is
`rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83`
with semantic digest
`8dcd3af81b10003c49ee0588bd01a5ce8f5e778f41159bdf8b3769794dbf80ac`.
It produces 295 links and 216 terminal nonlinks. Link rules account for 27
original exact matches, 179 unique leading-identifier matches, 29 exact
attached-title matches, 23 unique outer appendix-document matches, and 30
exact hierarchical-subsection compositions, 5 exact ES-identifier matches, and
2 table-separator normalizations. All 295 links map to Task 04A `usable`.

The current failure census is 79 `exact_figure_target_absent`, 66
`upstream_source_identity_repair_required`, 19
`exact_alias_only_outside_routed_source`, 19 `exact_target_absent`, 12
`exact_target_collision`, 11
`comment_authored_reference_no_official_response_link`, 6
`more_specific_appendix_target_requires_resolution`, 2
`appendix_source_route_absent`, and 2 `appendix_q_verification_required`, with
zero target-type incompatibilities or unsupported forms. The twelve collisions
comprise the seven accepted main-document number-only collisions, the new
seven-option `ES.6` collision, the new three-option normalized `Section 4-11`
collision, two K1 mentions with four candidate part-document targets, and one
K2 mention with five candidate part-document targets.

Figure targets remain deferred to Task 06's upstream target-index work.
The 19 outside-routed-source controls are the 8 Chapter 8 and 11 Chapter 9
mentions now explicitly assigned to Task 06. The same-source exact leading
chapter-identifier rule resolves both Chapter 2 mentions; it does not substitute
Section 8.1 or 9.1 for the missing whole-chapter targets.

## Human code-quality gate

A renewed review of all Task 05F implementation, schemas, configuration, and
focused tests initially failed. The target-index builder exceeded the explicit
complexity threshold; the resolver mixed candidate discovery, link creation,
and outcome construction while passing eight loosely related arguments; one
Task 05E-derived repository role name remained in the 05F run specification;
inventory lookup failures could surface as unhelpful iterator errors; and exact
candidate reuse did not reject unexpected files.

The repair introduces small typed records for shared resolution resources,
candidate rows, and complete results; separates candidate discovery, link
construction, record-shape validation, and provenance validation; isolates
hierarchical-subsection indexing; validates publication-layout assumptions;
uses explicit cardinality errors for activity, inventory, and repository
bindings; names the 05F run-spec schema role directly; and requires exact file
closure before candidate reuse. These are local responsibility splits, not a
resolver framework.

The repaired implementation passes formatting, linting, explicit complexity
and excessive-argument/statement checks, strict typing, 47 focused 05F and
run-spec tests, all 1,410 repository tests, deterministic candidate reuse, and
`git diff --check`. Comparison with the pre-repair candidate proves identical
mention outcomes and link targets after excluding identity-derived IDs. No PDF
was accessed and no large upstream payload was hashed. The human code-quality
gate is therefore passed for the current nonterminal implementation.

## Partial closure

On 2026-09-10, the user accepted this maintained candidate as Task 05F's partial
MVP outcome and closed the task without terminal inventory publication. The
working candidate remains explicit evidence rather than an immutable Task 05
release. Its 295 links and all 216 nonlinks transfer unchanged to Task 05G;
Task 06 owns the upstream repair inputs needed before replay.

Generic `Appendix F` remains unrouteable rather than being guessed as F1 or F2.
Outside-routed-source controls, comment-authored closures, and Appendix Q
closures are not candidates for automatic promotion. Closure authorizes this
documentation transition and repository commit only; it does not authorize
source access, cleanup, Task 06 execution, Task 05G replay, or Task 05H
publication.

## Non-goals

- Source/PDF access or large upstream-file hashing.
- Fuzzy or semantic matching and invented targets or aliases.
- Upstream Task 03/04 repair inside Task 05F.
- Evidence sufficiency, response outcomes, case eligibility, clustering,
  reference-defense authoring, or Task 05H publication.
- A workflow engine, rule framework, graph platform, artifact store, service, or
  production-general abstraction.
