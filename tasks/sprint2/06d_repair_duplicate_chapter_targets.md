# Task 06D: Repair Duplicate Chapter Targets

Status: **complete and accepted after Astra's v6 re-review. Task 06E and
production replay remain separately gated**.

## Abstract

Represent a repeated chapter divider and opening-page heading as one logical
chapter, retaining both source blocks and the complete chapter contents. The
observed Appendix A Chapter 06 and 08 pairs motivate the work; they are not a
source-ID or page-number exception list in production code. Inspect their
children, siblings, and accepted TOC destinations before deciding that they
are duplicates. Unresolved structural ambiguity goes to human review.

This is a source-free implementation task. It prepares a tested repair and
replay instructions; Task 06G owns production replay and Task 06H owns terminal
review and handoff. No accepted artifact is modified.

## Goal

1. Identify the narrow stage that owns logical chapter identity.
2. Implement one bounded, source-general repeated-heading rule.
3. Preserve source evidence, substantive content, and truthful provenance.
4. Specify exact correspondence from old section targets to the new chapter.
5. Leave nonqualifying and ambiguous headings distinct and accounted for.

## Inputs and prerequisites

Read `AGENTS.md`, `docs/index.md`, `docs/todo.md`, the Task 06 umbrella,
`docs/architecture.md`, `docs/data_artifacts.md`, and this task first.
Then read:

- accepted Task 06A evidence/design packet, including exact heading and section
  IDs, surrounding child/sibling topology, and accepted TOC destinations;
- accepted Task 06B ownership/reuse changes and both gate outcomes; update the
  code pointers below if that task moved responsibilities;
- Task 03J canonical/hierarchy identity references and Task 04D correspondence
  supplied by 06A, without reconstructing them from historical commands;
- `docs/specs/semantic_structure_v2.md` and its executable schema at
  `benchmarks/er_bench/schemas/canonical_extraction/v2/semantic_structure.schema.json`;
- the exact 06A positive and negative control records, not source PDFs.

The starting observations are physical pages 311/312, `06 CIRCULATION` and
`06 | CIRCULATION`, and 479/480, `08 PUBLIC FACILITIES FINANCING` and
`08 | PUBLIC FACILITIES FINANCING`, in `deir_appendix_a`. Verify these against
06A's pinned records. Their text similarity alone does not establish a merge.

## Current ownership to trace

- `src/er_commons/hierarchy_inference/correction_policy.py:build_rule_decisions`
  owns deterministic corrected role/level decisions.
- `src/er_commons/document_records/document_structure/sections.py:build_document_sections`
  projects accepted headings and memberships into sections.
- `_build_heading_nodes` currently creates one node per accepted heading;
  `_parent_index`, `_membership_index`, and `_finalize_sections` preserve
  parentage, direct membership, and ordered children.
- `document_structure/aliases.py:build_target_aliases` groups aliases by target
  identity; it cannot establish that two semantic sections are one chapter.
- `document_structure/policies/sections.py` checks heading ownership and tree
  membership; update it alongside any changed semantic representation.
- `collection_processing/record_target_indexing.py` aggregates sealed aliases.
  It must not become a second duplicate detector or choose a winning target.

Use the existing hierarchy/semantic boundary selected by 06A. Do not implement
one merge in hierarchy and a second independent interpretation in linking.

## Outputs

- An accepted, versioned repeated-heading policy and focused fixtures.
- Narrow implementation and semantic validation changes in the owning stage.
- A compact qualification report with eligible, rejected, and review-required
  groups, including reason codes and stable evidence IDs.
- A correspondence contract identifying both old section targets, the retained
  source blocks, the future logical target, and affected descendants.
- Task 06G replay inputs and Task 06H targeted review selections.

Production artifacts are not outputs of this task. Any separately specified
bounded record qualification uses fresh working space under the external root
and cannot publish a collection or accepted handoff.

## Research / learning checkpoint

Explain why alias tie-breaking cannot repair a fragmented chapter subtree.
Read the existing heading-ownership and extent invariants before changing them.
The [W3C PROV data model](https://www.w3.org/TR/prov-dm/) distinguishes source
entities from derived entities and their derivation. Apply that principle to a
logical chapter derived from two retained headings; adopting RDF is unnecessary.
Record the tradeoff between repairing hierarchy and repairing its semantic
projection, using actual child and TOC evidence from 06A.

## Plan / spec requirement

Before implementation, record these decisions in the task's compact design
note or the existing owning specification:

1. Eligibility requires adjacent physical pages, body heading roles, compatible
   exact chapter marker/title under explicitly enumerated typography handling,
   and compatible parentage. Do not introduce general fuzzy matching.
2. Freeze how a separator such as `|` is parsed, retaining both raw spellings.
   Title disagreement or chapter-number disagreement rejects automatic repair.
3. Inspect all direct children and adjacent siblings of both headings. State
   whether the first is a divider and where substantive chapter content begins.
4. Inspect accepted TOC destinations to either heading and any contradictory
   destination. A TOC page number alone does not choose the winning target.
5. Select the retained anchor deterministically from structure; document how
   both heading blocks remain ordered in the repaired chapter.
6. Define reassignment of children, section paths, sibling order, and extent.
   Every original substantive record must retain exactly one direct owner.
7. Specify derivation evidence for both headings and many-to-one target
   correspondence. Distinguish source block identity from section identity.
8. Preserve a review-required outcome when topology or TOC evidence does not
   establish one interpretation. Do not discard the second target silently.

A logical-target-only designation is acceptable only if the approved contract
also supplies the complete chapter extent. An alias to the divider's empty
section is not a successful repair. If a schema addition is necessary, version
it, preserve readers of accepted evidence, and enumerate changed validators.

## Implementation sequence

1. Freeze inputs and owner decisions from 06A/06B; stop if prerequisites differ.
2. Build a pure classifier over the smallest typed record inputs needed for
   heading compatibility, topology, and TOC checks.
3. Implement the accepted repair in one owner, with a separate deterministic
   projection/accounting function rather than a new orchestration framework.
4. Carry preserved evidence through aliases and namespace correspondence.
5. Add semantic checks for content conservation, complete extent, parentage,
   uniqueness, and explicit unresolved cases.
6. Run focused synthetic tests, then required repository checks.
7. Obtain independent human code-quality review before handing off to 06G.

## Required fixtures and expectations

| Fixture | Expected result |
| --- | --- |
| Chapter 06 observed shape with approved topology | One complete logical chapter; both headings retained |
| Chapter 08 observed shape with approved topology | Same policy and outcome, no source-specific branch |
| Adjacent divider and opening heading with children under each | All children preserved in source order |
| TOC destinations to both physical headings, same chapter | Correspondence retains both destinations |
| Nonadjacent same-text headings | Remain distinct |
| Adjacent legitimate same-title sections with distinct scope | Remain distinct |
| Different parents or chapter markers | Remain distinct with diagnostic |
| Conflicting TOC destinations or overlapping child ranges | Review required; no automatic merge |
| TOC rows or furniture resembling a heading | Ineligible |
| Divider followed by another substantive chapter | No merge |
| Missing source heading or missing child record | Validation failure |
| Two/three-heading group or repeated execution | Explicit supported cardinality or review; never cascading guess |

Include controls outside Appendix A that satisfy and fail the same rule. Use
small synthetic records and approved record excerpts; do not add PDFs to Git.
The observed pair counts are regression expectations, not the selection rule.

## Invalidation and reuse matrix

| Evidence/product | Treatment |
| --- | --- |
| Source bytes, chunked conversion, producer evidence | Reuse exact sealed inputs |
| Existing extraction text, geometry, table/image content | Preserve semantically; namespace changes recorded |
| Affected hierarchy, if selected owner | Fresh decisions and descendants in 06G |
| Affected sections/membership/aliases | Fresh products from earliest changed owner |
| Printed-page labels | Reuse if their declared inputs remain identical |
| Affected document links/publication | Replay in 06G |
| Collection accounting/index/resolution/handoff | Replay in 06G |
| Unaffected documents | Explicit correspondence under 06B rules |
| Task 05D/05E and accepted 05F candidate | Preserve; no replay here |

If a supposedly reused stage depends on changed owned code or policy, use 06B's
validated reuse boundary for old upstream inputs. A stage whose semantic policy
changes must produce fresh output; old output cannot be declared the result of
the new policy. Do not copy records into incompatible identities.

## Human review fallback and handoff

Produce a small packet showing both headings, child/sibling ranges, accepted
TOC destinations, the proposed anchor, and changed membership. Reuse available
accepted render evidence where identity correspondence permits. New source
rendering is not authorized by this task.

Before closing 06D, use an early bounded human structural-decision checkpoint
for the observed pairs when code checks cannot decide. The checkpoint uses the
existing record packet and already accepted renders under the active task's
review authorization. If new rendering is necessary, specify and obtain its
bounded source gate before proceeding. Do not defer a blocking interpretation
to 06H, which starts only after 06G can materialize the selected policy.

Record the human disposition as an explicit input to the owning structural
projection and test its materialization. Broader nonqualifying cases retain
their original targets and documented unresolved status. Both observed pairs
must have an approved interpretation before 06G; a decision to retain either
as unresolved requires an explicit amendment to the umbrella acceptance scope.
06H verifies the materialized results. If that later review changes the
interpretation, return to 06D and fresh 06G replay, then re-review affected
evidence. A review label alone never repairs a machine product.

## Validation and review pass

- Verify one owner per content record, acyclic parents, exact child order,
  preserved heading blocks, and chapter extent ending at the correct sibling.
- Verify merged alias spellings deduplicate by logical target ID; legitimate
  collisions remain multi-target outcomes.
- Check deterministic output under repeated runs and stable input ordering;
  interrupted qualification must not masquerade as complete evidence.
- Check changed-policy/input identity rejection and no-clobber working output.
- Use `make fix`, `make check`, and `git diff --check`; report actual checks.
- Review readability, diagnostic specificity, typed boundaries, and whether a
  future agent can explain a merge from its evidence without re-running a PDF.

## Acceptance criteria and stops

The rule, fixtures, validators, provenance, and replay instructions pass review;
both observed pairs have approved structural dispositions ready for
materialization. Blocking review items leave this task incomplete until the
early human checkpoint resolves them. There is no Task 05F tie-breaker and no
content loss.
Stop on missing accepted topology, contradictory destinations, schema ambiguity,
or a required source/model rerun. Return that evidence for a bounded decision.
Passing this implementation task does not accept a replacement collection.

## Non-goals

Broad heading deduplication, fuzzy matching, source acquisition, PDF conversion,
cleanup, commit, push, Task 05G execution, and final inventory publication.

## Outcome

Task 06D implemented the source-general rule in the maintained semantic
projection boundary. `repeated_heading_policy.py` owns typed classification;
`repeated_heading_projection.py` owns frozen-evidence validation, projection,
idempotence, alias redirection, and many-to-one target correspondence; and
`repeated_headings.py` is the public facade. `repeated_heading_qualification.py`
publishes a deterministic,
schema-validated, no-clobber, completion-last packet. The document-structure v2
input and identity path verifies and binds the policy, schema, qualification,
inventory, completion, and eligible decision stream before construction.

The accepted 06A topology establishes two eligible groups and no
review-required group:

- Chapter 06: retain the p311 divider as logical anchor, preserve the p312
  opening heading and six child sections, and carry the full p311–449 extent.
- Chapter 08: retain the p479 divider as logical anchor, preserve the p480
  opening heading and four child sections, and carry the full p479–491 extent.

Both outcomes follow the same exact rule. The Chapter 08 token `447` remains an
unresolved physical TOC destination and selects neither heading; this does not
make the logical topology ambiguous. The two negative-control pairs are
explicitly rejected. The current fresh compact packet is
`pipelines/brisbane_baylands/task_06_recovery_v1/06d/qualification_v6/` under
the external root. The earlier `qualification_v1/` through `qualification_v5/`
attempts are preserved and superseded after review tightened sibling
adjacency, frozen-input validation, evidence locators, packet closure, boundary
drift checks, required extent evidence, all-decision accounting, and
canonical-v2 support compatibility. The v6 correction additionally requires
the complete descendant extent to end strictly before the next boundary,
freezes that boundary's stable key and raw text, fully validates an already
projected pair before accepting idempotent reapplication, isolates v1 from v2
repair execution, and preserves duplicate raw spellings in rejected controls.

Synthetic coverage exercises the observed shapes, content under both halves,
namespace-changing correspondence, exact TOC redirection, destination variants,
same-title and nonadjacent controls, changed topology/text, missing child
references, boundary-crossing extents, post-projection evidence drift, duplicate
raw spellings, v1 import isolation, overlap, cardinality, idempotence,
no-clobber publication, schema
validation, and consumer verification of packet seals. Independent reviews
identified no structural ambiguity. Astra's four material findings were
addressed in the implementation and tests. Qualification v6 binds policy
SHA-256 `49e6fa1baf4f04e227a9099720a52f95d16ea355e2f59a8e3b78104c7ace9f8f`,
decision-schema SHA-256
`7ff78138e6b79d5a60d7be112936f45b6ce6ba0ac736bb19b90164c4f4cb435f`,
and inventory SHA-256
`7ed69976d2c2c5a56f7d8e1481a6b8803531595e5329059421b018fd8752f2cc`.
The actual consumer accepted schema, closure, seals, counts, zero pending review,
the exact eligible subset, frozen boundary evidence, and strict extent
termination. Final validation passed `make fix`, `make check` (Ruff
format/check, mypy over 476 source files, and 1,692 pytest cases), and
`git diff --check`.

The earliest invalidated product is Appendix A semantic sections/membership and
aliases. Conversion, producers, accepted hierarchy evidence, content/geometry,
printed-page labels with unchanged inputs, and unrelated documents remain
reusable under 06B's boundaries. Task 06G must create a fresh policy-bound
candidate, then seal the build's compact repeated-heading correspondence beside
the 06G recovery handoff without changing canonical-v2's four support roles. It
then replays affected links, publication, collection target indexing/resolution,
and handoff. Task 06H must inspect both physical headings, all transferred children,
complete extents, both alias spellings, TOC evidence, and old-to-new target
correspondence. Astra accepted the corrected v6 implementation and packet with
no material blockers. The policy specification retains its publication-time
"acceptance pending" wording because v6 seals those exact bytes; this outcome
and the current routing docs are the authoritative acceptance record. No
production replay, PDF/render/model work, commit, push, or Task 06E work
occurred.

## Task 06B interface handoff

Both Task 06B gates now supply the maintained
[command map](../../docs/pipeline_commands.md) and
[executed owner map](../../docs/specs/task06b_gate2_executed_inventory.md).
Use explicit current requests with original per-source accepted manifests and
seals; historical recipe validation does not reopen removed implementation paths.
Document/collection v3 supports declared replacement membership. Compact checks
must retain the shared verification budget and must not claim new payload-byte
equality. This handoff updates interfaces only; the task's provisional policy and
separate source, conversion, replay or review authorization boundaries still apply.
