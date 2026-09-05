# Reusable Document Linking Contract v1

Status: **accepted, implemented, and published by Task 04D; the Gate D handoff
is the designated downstream replacement for Task 03J linking-dependent
records**.

## Purpose

This contract defines one reusable document-linking stage for any conforming
canonical document collection. It replaces neither extraction nor human
review. It consumes sealed structured documents, constructs only authorized
body-evidence aliases, links ordinary references and effective navigation
claims through one resolver, and publishes a fresh linked-document product.

Task-specific code may select inputs and compare a migration. It may not own a
production resolver, publisher, identity recipe, or corpus-specific rule.

## Maintained interfaces

Gate C provides this package-backed interface:

```text
er-commons documents relink --link-spec <path> --source-id <source-id>
```

When reviewed evidence is supplied, Gate C first uses the generic
package-owned materializer:

```text
er-commons documents materialize-reviewed-navigation --review-spec <path>
```

Its maintained owner is
`document_records.document_references.reviewed_navigation`; Task 04D code may
prepare a corpus-specific input spec but cannot publish the bundle itself.

The interface calls maintained owners in this order:

1. verify the selected published document and its five reusable upstream
   product completions;
2. verify the linking policy, source-family catalog, and optional reviewed
   navigation bundle;
3. build accepted body-derived aliases;
4. link ordinary references and effective-navigation entries through the
   shared exact resolver;
5. validate and completion-last publish one linked-document candidate; and
6. call the existing downstream document replay publisher without allocating a
   document attempt.

The existing collection interface remains:

```text
er-commons collections assemble-handoff --collection-spec <path>
```

Its replacement collection specification must use
`document_evidence_mode: downstream_replay_only`.

## Input contract

`er_commons.document_link_run_spec.v1` is a closed JSON object validated by
`document_link_run.schema.json`. It binds:

- one contained output root;
- the sealed base collection handoff and contract bundle;
- the base and fresh production-identity recipes;
- the document-publication specification;
- the exact linking-policy bytes;
- the source-family catalog;
- an ordered, unique source list;
- for every source, its sealed published document plus its sealed structured
  document completion and inventory;
- role-keyed output schema references; and
- either `null` reviewed navigation or one sealed, generic reviewed-navigation
  bundle.

Every external artifact reference declares `authority: repository` or
`authority: artifact_root` in addition to relative path, digest, and byte size.
The validator resolves the path only beneath that named root. Output-schema
references cover identity, manifest,
inventory, completion, aliases, ordinary references, navigation entries,
relations, decisions and links, and support records. Runtime validation must
also require the ordered `selected_source_ids` to equal the document source
IDs, reject duplicate sources, enforce `docv1-` for source documents and
`exv1-` for structured products. Collection execution is deliberately
sequential and reports per-source progress; resource policy remains owned by
the downstream document-publication specification where it is actually used.
Owned reviewed-navigation payloads instead use `authority: bundle`, with paths
relative to the candidate bundle root. Keeping the future `navreviewv1-`
directory name out of its own identity preimage avoids a hash fixed-point while
the payload digests still determine the identity.

Reviewed navigation is optional. Gate C first materializes any reviewed input
as a generic sealed bundle whose identity binds the human decision record,
semantic view, reconstructed text entries, dispositions, and derived explicit
parent relations. That materialization is source-free and is not a link or
document publication. Its closed
`reviewed_navigation_bundle.schema.json` contract requires a `navreviewv1-`
identity derived from source coverage, all five evidence references, schema
digest, and materializer-code digest. Runtime validation must prove ordered
unique coverage, exact identity-preimage derivation, equality between preimage
and payload references, upstream checksum validity, managed-file inventory
closure, and completion-last publication before the linker accepts the bundle.
Reviewed coverage must be a subset of the selected link-run sources. When
reviewed navigation is absent, canonical machine
navigation is effective. When present, sparse reviewed dispositions replace machine
navigation only inside their declared coverage; machine navigation remains
effective elsewhere. A reviewed bundle must independently seal its completion,
inventory, dispositions, text entries, and explicit parent-entry relations.
Source TOC or mention text may query body evidence but may never create an
alias.

For the Task 04D migration, the generic reviewed input binds Task 04A's
accepted decisions and Task 04C's semantic dispositions, reconstructed TOC
text, and explicit effective-navigation relations. Task 04C's existing 28
links are comparison evidence, not link authority.

## Shared resolution boundary

The machine-reference and navigation adapters independently parse claims, then
submit the same neutral query:

```text
lookup text
target type
authorized fallback profile
eligible alias evidence
optional destination-page IDs
optional resolved-parent target IDs
```

The resolver returns target-ID-deduplicated candidates, supporting alias IDs,
target page IDs, match bases, pre/post-parent candidate counts, scope flags,
and one typed outcome. Alias rows are evidence, not separate candidates.
Parent scope requires an explicit resolved relation and never infers a parent
from the preceding navigation row. Zero and multiple candidates fail closed.

The ordinary machine-reference adapter preserves the v3 mention parser,
structural or caption lookup keys, and table mention-window policy. It uses no
R2 section-title fallbacks; missing destination evidence maps to `null`, while
explicitly computed empty evidence remains an empty set. The effective-
navigation adapter parses complete headings or captions and alone activates
R2a/R2b/R5 section fallbacks after an exact miss. Both adapters may use the
R6a table-caption profile and submit identical candidate evidence to the shared
resolver. This separation preserves ordinary `Section N` mention behavior
while sharing target selection rather than claim parsing.

## Accepted policy

The checked-in `er_commons.document_linking_policy.v1` instance is the sole
Gate B policy authority. Its human rule IDs map as follows:

- **R1:** intersect textual targets with destination-page candidates when page
  evidence exists; never resolve from a page alone.
- **R2:** query the complete section heading; a destination page is optional.
- **R2a:** after an exact miss, permit only the strict
  `GOAL <decimal marker>: <title>` body projection.
- **R2b:** after an exact miss, allow the six accepted whole-string mechanical
  transforms and the accepted apostrophe-plus-terminal-period composition.
- **R3:** retain the letter marker in complete child-heading lookup.
- **R4:** scope repeated lettered children only through an explicit resolved
  parent relation, including a validated continuation relation.
- **R5:** after an exact miss, remove whitespace adjacent to a retained ASCII
  hyphen. This is distinct from R2b's alphabetic-hyphen-as-word-separator rule.
- **R6:** derive a complete-caption table alias only when the body caption or
  heading is immediately followed in canonical page order by one table on the
  same page and in the same section, below the caption, with positive
  horizontal overlap.
- **R6a:** table-caption fallback profiles add R5, straight/curly apostrophe
  equivalence, whitespace-before-comma removal, and an optional digit-letter
  hyphen.

All textual profiles are exact-first, whole-string, deterministic, union all
authorized fallback evidence before target-ID deduplication, and fail closed
on multiple targets. R6 is target construction and does not belong inside the
resolver. Existing canonical alias generation remains frozen; R6/R6a are the
only accepted derived-alias extension.

After a complete exact miss, the navigation section profile unions each
individually authorized fallback with the strict GOAL projection composed with
at most one accepted mechanical transform. That explicit composition is
required for the accepted 80-of-87 no-page result; rule ordering may not hide a
collision.

Figure linking, footer-derived printed-page aliases (R7/R7a), fuzzy matching,
stemming, page-only linking, and every additional repair for the frozen 150
unresolved TOC entries are absent from the policy.

## Linked-document output

For each source, the stage publishes a complete linked-document candidate with:

- effective `canonical/target_aliases.jsonl`, preserving every upstream alias
  and appending only accepted R6/R6a aliases;
- recomputed `canonical/cross_references.jsonl` for ordinary references;
- effective navigation entries and explicit parent-entry relations;
- navigation-link records and one disposition per effective entry;
- target-index support, policy-application accounting, alias preservation and
  extension proof, and all unresolved outcomes; and
- identity preimage, manifest, managed-file inventory, and completion record.

The output must conform to a new schema. Task 04C's v1 reconciliation schema
cannot represent no-page links or multiple aliases supporting one target and
must not be republished or extended in place.

The normal document publication must import this complete product so model
exploration can read effective navigation links. Collection processing must
continue reading effective canonical aliases and ordinary cross-references
from the published document candidate; a separate overlay that is invisible to
normal terminal evidence is not a valid replacement.

## Identity recipes

Gate C creates a fresh production identity. Reusing Task 03J's production
identity would falsely attribute changed linker code and policy to old bytes.
The fresh `exv1-` production preimage binds:

```text
schema version
sealed base production identity reference
link-run contract/schema SHA-256
linking-policy SHA-256
owned linker, alias-builder, adapter, validator, publisher, and CLI code digest
output-schema bundle digest
downstream-only reuse authorization
```

The actual run specification checksum cannot also be part of this production
preimage because the run contains a sealed reference back to the production
recipe. That would create a checksum fixed point. The actual run instead binds
the production recipe, and each linked-document identity binds the complete
run-spec checksum. This preserves the same change propagation without a cyclic
identity definition.

Each linked-document candidate identity additionally binds its source identity,
sealed source document completion and inventory, sealed structured-document
completion and inventory, source-family catalog, optional reviewed-navigation
references or explicit `null`, configuration, policy, schemas, and owned code.

Every republished `docv1-` identity then binds the fresh production identity,
the replacement linked-document completion, the five checksum-reused upstream
product completions, the imported content digest, and the new run-spec digest.
A changed policy, reviewed input, code bundle, schema, or upstream seal must
therefore produce a new linked-document and document identity.

The collection run uses the fresh production identity and a changed run-spec
digest, forcing a fresh `scopev1-`. Its existing identity chain remains:

```text
scopev1 -> accounting -> idxv1 -> resv1 -> handoffv1 -> contract bundle
```

No final IDs are assigned in Gate B because the implementation, schemas, and
real run specifications are output-affecting inputs finalized in Gate C.

## Exact replay boundary

All 35 successful Task 03J documents enter one coherent replacement lineage.
Replaying only the three documents with reviewed TOC entries would mix old and
new linker-policy identities.

Checksum-reuse exactly, for every source:

- stable content evidence;
- heading evidence;
- mapped records;
- hierarchy decisions; and
- structured document.

Rebuild under fresh identities:

- R6/R6a derived table aliases;
- local target index;
- ordinary-reference and effective-navigation links;
- linked-document completion;
- all 35 downstream-only document publications;
- collection accounting;
- collection target index;
- cross-document resolution;
- handoff and contract bundle; and
- any report whose identity consumes a rebuilt descendant.

Source PDFs, Docling, table reconstruction, record mapping, hierarchy
inference, section mapping, figures, printed-page observations, Task 04A,
Task 04C, and every existing Task 03J artifact remain immutable. No document
attempt is allocated.

## Replacement comparison

Publication must stop unless comparison proves:

1. all five reused completion references and their inventories are unchanged;
2. canonical extraction streams other than aliases and cross-references are
   semantically identical, allowing only the fresh enclosing identity namespace
   required by the maintained candidate format;
3. the alias delta equals the complete accepted R6/R6a extension and no
   upstream alias is removed or retargeted;
4. every ordinary or navigation link delta names R1-R6a evidence;
5. the original 28 Task 04C links retain their targets;
6. the accepted TOC accounting is exactly 410 resolved and 150 unresolved;
7. all 725 inherited ambiguous links remain explicitly represented unless an
   accepted R1-R6a rule independently resolves one, with every delta enumerated;
8. all changed document and collection records are descendants of the replaced
   link product; and
9. a second identical invocation reuses identical bytes and allocates no PDF,
   producer, semantic, or document attempt.

## Portability and maintainability gates

Gate C includes generic machine-only and reviewed-navigation fixtures. They
contain no Brisbane names, Task IDs, production artifact hashes, or local
absolute paths. Together they cover unique, ambiguous, page-conflicting,
parent-conflicting, fallback-collision, excluded-navigation, derived-table,
unresolved-figure, shuffled-order, changed-policy-identity, changed-review-
identity, and corrupt-seal cases.

The production path must remain package-owned, typed, logged, completion-last,
no-clobber, and restartable. Task-specific scripts may audit or compare it but
cannot publish production outputs.
