# Task 11D.2 bibliographic metadata correction

Status: implemented and staged offline; not integrated into live dispatch.

Task 10 delivers `edition` to generation. The legacy development evaluation
projection omits it from G. All 23 passages in the fixed six have edition labels;
C014 P4/P5 combine the bibliographic label with curator approval language.
Titles and headings alone do not reliably identify the supplied edition.

## Correction and separation

The opt-in `development_edition_projection` adapter verifies an audited mapping
against each original Task 10 record and every passage hash. It reconstructs the
original edition exactly from typed bibliographic fields and a separately retained
curator annotation. No heuristic stripping or arbitrary metadata forwarding occurs.

For C014 P4/P5 the model-visible locator is `2026 Final EIR Appendix F.1`.
The annotation `accepted qualified substitute; no Draft-equivalence assumed`
remains audit provenance. Other passages retain `2025 Draft EIR`. Neither label
proves substantive Draft/Final equivalence. The Final wrapper date is not a claim
that its underlying transportation report was authored in 2026.

`project_item(saved_g_item, original_target_record, audited_mapping)` adds only
`canonical_target.edition`, an existing locator field accepted by frozen G's
validator. Candidate claims, owned evidence, full text, tables, question and all
other locators remain unchanged. New sample identity binds the original item,
projection version, mapping and new payload hash. Candidate/run/repeat/point IDs
remain available for paired analysis. New projections have no model verdict.

The audit also stages six generation records with the same bibliographic labels;
curator annotations are excluded from their model-visible payloads. These are new,
undispatched condition artifacts, not replacements for Task 10. C014's question
remains unchanged in these records pending exact-text approval. No reference or
case-specific evaluator requirement is copied into generation.

Old candidate prose that mentions curator approval remains unchanged. Adding
bibliographic edition cannot establish those assertions; the annotation is not
silently added as evidence to make them pass. This correction addresses document
identity visibility, not substantive inference or missing citations.

## Version and execution boundary

Projection: `task11d2.g.edition_projection.v1`.
Mapping: `task11d2.bibliographic_mapping.v1`.
Staged generation condition: `task11d2.target.bibliographic_only.v1`.

The adapter deliberately has no provider or dispatch integration. Legacy callers,
09G prompts/models/policies, Task 10 publication and historical plans are unchanged.
A future bounded comparison must explicitly integrate the new condition into
fresh generation/evaluation manifests and native request counts, bind approved
question wording if used, and revalidate dispatch and offline replay. Existing
source-change replay overrides must not reinterpret old packets as new ones.

Offline validation covers the full 23-passage inventory and every G item in both
V6b repeats (47 distinct projections). It checks frozen input validation, exact
source preservation, distinct identities and original artifact hashes. This
establishes interface fidelity only; improved judge agreement or prompt performance
requires a separately recorded live comparison and is not claimed here.

The [11D.2 task](../../tasks/sprint2/11d2_resolve_evaluation_contract.md) and result
pointer own exact artifacts, tests, review and pending question approval.
