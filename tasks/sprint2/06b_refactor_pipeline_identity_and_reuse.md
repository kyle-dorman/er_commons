# Task 06B: Refactor Pipeline Identity, Reuse, and Maintained Entry Points

Status: **ready from completed Task 06A; inactive until source-free
implementation is authorized**. This is one task with two sequential gates,
not two independently activated tasks.

## Abstract

Make the second document-processing cycle understandable and affordable without
discarding accepted chunked-conversion evidence. Separate consuming an old
sealed artifact from deriving a new execution identity, narrow code ownership,
remove repeated verification, and replace task-era maintained entry points with
responsibility-based names. Remove proven one-off paths from the active code.

Gate 1 establishes and tests the reuse/identity boundary. Gate 2 applies the
enumerated cleanup and proves the whole maintained path still satisfies it.
Coupled implementation changes may cross those responsibilities inside this
task, but expensive processing cannot begin before both gates pass.

## Goal

1. Reuse accepted conversion, producer, document, and review evidence under its
   original identities without requiring historical code to match today's tree.
2. Give each future stage a complete, bounded set of behavior dependencies.
3. Ensure source-free downstream work neither opens source PDFs nor hashes
   preserved large payloads as routine preflight.
4. Give maintained scripts, modules, and operational variables clear names and
   explicit inputs; delete only the approved one-offs.
5. Preserve content, matching rules, human decisions, and accepted artifacts.
6. Supply documented interfaces and tests that 06C–06H can use directly.

## Inputs

06A qualification is complete. Start from its exact external packet and the
[recovery/reuse specification](../../docs/specs/task06_recovery_plan_v1.md) plus
[finite code inventory](../../docs/specs/task06a_code_inventory.md). The former
freezes verification budgets, per-source manifests and resource boundaries; the
latter freezes Gate 1 owner changes and Gate 2 migration scope. No 06B test or
implementation gate was executed by 06A. Treat oversized 06A enumerations as
metadata/read inputs through their compact packet inventory, not as permission
to exceed the accepted-input hash ceiling.

- [Task 06 umbrella](06_repair_reference_sources_and_target_index.md) and the
  accepted [06A packet](06a_freeze_recovery_and_cleanup_plan.md).
- Exact old conversion/range/producer/document/review seals and recipes selected
  by 06A, plus the new replay and code-ownership design.
- The 06A rename/remove/retain inventory and command/resource boundaries.
- `docs/architecture.md`, `docs/data_artifacts.md`, `configs/README.md`,
  `pipelines/README.md`, and the maintained specs named in 06A.

Current code landmarks, to be replaced by an explicit old/new map at closure:

| Concern | Existing owner under `src/er_commons/` |
| --- | --- |
| Conversion versus producer identity | `document_parsing/content_parsing/conversion_identity.py`, `identity.py` |
| Chunk identity and frozen plans | `chunked_conversion/runtime/inputs.py`, `planning.py` |
| Sealed conversion reuse/deep audit | `document_parsing/content_parsing/conversion_seal.py` |
| Historical versus live production recipe checks | `document_publication/production_identity.py`, `preflight.py` |
| Downstream source binding | `document_publication/downstream_replay.py`, `sources.py` |
| Repeated candidate hashing | `document_publication/storage.py` |
| Prepared relinking/review validation | `document_records/document_references/relink_publication.py`, `relink_replay.py`, `reviewed_navigation.py` |
| Response-stage inventories and dependencies | `response_inventory/code_inventory.py`, `run_spec.py`, `reference_baseline.py` |

## Research / learning checkpoint

- [DVC run cache](https://doc.dvc.org/user-guide/pipelines/run-cache): a stage's
  reuse decision depends on its actual execution conditions. Apply this to
  existing manifests; do not adopt DVC for this refactor.
- [W3C PROV-O](https://www.w3.org/TR/prov-o/): record new derivations from existing
  entities rather than relabeling earlier entities as freshly produced.
- [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html):
  test unexpected I/O and execution by patching project seams before calls.

Explain why code provenance can be retained without making every dispatcher,
review-page, or acquisition edit a conversion-cache dependency. Explain the
integrity limits of metadata-only accepted-input reuse. No semantic/AST-based
code hashing or automatic dependency graph framework is required.

## Plan / spec requirement

Freeze the 06A ownership and compatibility decisions in a short versioned spec
before changing inventories. Name each old-reader/new-writer boundary, the
accepted verification mode, and the finite code inventory per stage. Separate
this specification from historical production identity records.

Bind the 06A allowlisted hash-record roles and numerical per-file/per-invocation
byte ceilings. Enforce limits before payload access, with source/role/path in
the rejection. Do not classify all JSON records as small or waive the budget
because a legacy validator recursively reads them. Fixture tests may hash their
synthetic bytes; the production accepted-input policy remains explicit.

### Gate 1: establish safe sealed reuse and stage identities

#### A. Separate artifact consumption from new execution

An accepted-artifact reader verifies its recorded identity preimage, compact
completion/inventory seals, terminal status, required schema, source membership,
paths, sizes, and managed-file closure. It does not re-derive the old artifact
identity using the current checkout or demand that a renamed historical source
file still exists at its old path. Report the verification mode truthfully.

A new writer binds its current behavior code, policy, schema, runtime inputs,
and the exact old or new upstream seals it consumes. Changing a recipe must not
rewrite the original seal, invent a completion, or imply byte equivalence
between different production recipes. Existing typed namespaces remain unless
the accepted spec demonstrates a required version change.

Use explicit input selection in maintained specs, not a hidden fallback that
selects an arbitrary old cache when a new identity misses. Retain range plans
and receipts as immutable evidence. Reading completed ranges is distinct from
resuming incomplete ranges under a changed adapter: the latter must still prove
matching conversion behavior or stop. A source or model mismatch never becomes
an accepted cache hit through a rename map.

Keep unchanged documents bound to their original source manifest and conversion
seals. A replacement collection may reference mixed accepted source lineages
through explicit membership and correspondence. Do not recreate every producer
identity against a single new F1 manifest. Implement only the minimum spec and
validation changes required to express that input composition.

#### B. Define future behavior inventories

Use explicit paths grouped by stage responsibility. Hash small owned code and
contracts normally. Split modules only where the actual dependency boundary
cannot otherwise be expressed clearly. Do not use a package-wide glob merely
because it is convenient; do not omit a dependency merely to retain a hash.

The required cases are:

| Change | Required effect |
| --- | --- |
| CLI help, unrelated command, or review presentation | No conversion/producer/structure invalidation; affected presentation may change |
| Source acquisition/title check with unchanged accepted bytes | Future acquisition behavior changes; old document conversions remain consumable |
| F1 replacement bytes | New F1 source/conversion descendants; other sources' accepted conversions reused |
| Docling options, model, conversion adapter, or source bytes | Affected future conversion and descendants invalidate |
| Routing/table behavior | Affected producer and descendants invalidate; conversion remains reusable |
| Chapter structure policy | Structure and required descendants invalidate; sealed conversion/producer reused |
| Figure aliases/link policy | Linking/target descendants invalidate; canonical figure evidence reused |
| Task 05F or review code | No Task 05D source-producer invalidation |
| Shared `normalize_alias` behavior | Task 05F and every actual normalization consumer invalidate |
| Rename of a maintained wrapper | Future execution provenance records the new path; accepted upstream seals remain usable |

Cover dependencies across package boundaries, including alias normalization and
shared record/serialization helpers. Separate Task 05 source production,
relationship, reference, and presentation inventories. Preserve accepted 05D/E/F
records; do not rerun those stages or change their resolver behavior here.
Task 05G owns consuming the replacement handoff and its new binding contract.

#### C. Remove hidden expensive verification from replay

Provide a named accepted-input verification path and a deliberate deep-audit
path through existing owners. The first uses recorded large-file digests and
metadata; the second verifies bytes and remains explicit. Do not silently
weaken a function whose caller expects a deep verification result.

- Prepare shared run/source-manifest evidence once, then select each source.
- Downstream replay must not call fresh-source preparation that hashes PDFs or
  initializes conversion/model execution before it can reuse sealed inputs.
- Verify shared reviewed-navigation evidence once per prepared run; retain
  per-source coverage, policy, and correspondence checks.
- For a deliberate deep candidate audit, compare one observed inventory with
  the sealed inventory, rather than hashing the tree twice.
- For new authoritative output, compute required digests during publication
  where possible; do not remove exact closure or completion-last guarantees.
- Keep prepared state run-scoped. Reject changed specs and mismatched source
  membership; do not introduce a persistent global validation cache.

#### Gate 1 acceptance

Implement synthetic tests that consume a valid historical fixture even when its
recorded old implementation path is absent from the current fixture checkout.
Its recorded recipe and seals must still validate; it must not be accepted as
the output of the new recipe. A fresh descendant must reference the old seal.

Use project-level sentinels to fail unexpected source PDF reads, PDF/large-
payload hash calls, model loading, and converter invocation. Exercise both
relinking and downstream publication, including preserved-artifact validators.
Verify the identity matrix above with positive and negative perturbations.

Reject incomplete/ambiguous seals, wrong source/range coverage, extra or missing
managed files, metadata drift, changed spec bindings, and incompatible schemas.
Test same-size corruption only in explicit deep-audit mode; the compact mode
must not claim to detect an unread same-size mutation.

Bind the real 06A-selected accepted seals with the compact reader, without
production replay. Include unchanged large-document conversion evidence as well
as Appendix A and main-document evidence. Report actual reused identities and
verification limits. If this cannot be demonstrated, stop before Gate 2 and
before any source/model execution; a full conversion rerun is not a fallback.

### Gate 2: clean maintained interfaces and prove integrated reuse

Apply only the 06A-approved rename/remove/retain inventory. The gate begins
after Gate 1 passes; the task's explicit implementation authorization may cover
both gates, so the gate boundary does not inherently require another permission
round trip. A material expansion still requires revising the contract.

1. Rename maintained scripts/modules/operational variables by responsibility.
   Replace frozen one-off selections with explicit validated inputs where a
   reusable capability exists. Keep source-specific config as data.
2. Update runtime imports, CLI/Make entry points, config generators, tests,
   future owned-code inventories, and current documentation together.
3. Remove proven one-off executables and their isolated scaffolding/tests.
   Keep their historical outcome records. Preserve readers needed for accepted
   artifacts, even if the original execution workflow is retired.
4. Do not rewrite accepted generated configs, schema-version identifiers,
   artifact directory names, or old production recipes to make them look new.
   If current tests require historical code recreation, distinguish historical
   recipe validation from active generator tests; do not simply delete coverage.
5. Add source/role/path and bounded expected/observed differences to errors at
   touched preflight and reuse boundaries. Avoid a new diagnostic framework.
6. Publish a concise supported-command map explaining preparation, execution,
   validation, deep audit, and review consumption. No maintained command should
   require knowing the task number that originally introduced its capability.

Candidate removals are not predetermined. In particular, the unused v1 bundle
adapter still appears in old inventories; compatibility adapters with live
callers remain. Task03H-named generation supports Task03J and must be migrated
as a maintained capability if it remains needed, not deleted by filename.

Run the Gate 1 tests again through the renamed public interfaces. Compare
synthetic old/new semantic records and explicit ID correspondence, allowing
only declared provenance/identity changes. Prove no duplicate downloads,
conversions, payload-tree copies, or repeated review validations occur.

## Outputs

- The accepted identity/reuse specification and a compact compatibility record.
- Narrow current stage inventories, explicit old-input readers/new writers,
  source-free replay preparation, and bounded verification improvements.
- The executed rename/remove/retain inventory, with old/new names and callers.
- Updated maintained commands and architecture/config/pipeline documentation.
- Focused invalidation, preserved-input, I/O-sentinel, corruption, and restart
  tests plus a concise human code-quality review.
- A 06C–06H interface handoff resolving every old path named in their contracts
  to its maintained owner and documenting which commands may access sources.

Do not create a new production handoff or relabel an accepted artifact as a
06B product. Any real-input evidence consists of bounded bindings and comparison
metadata in the 06A-defined working namespace.

## Validation and review pass

Use existing test suites as starting points, verifying paths before execution:
`tests/test_content_parsing_identity.py`,
`tests/test_document_structure_inputs_identity.py`,
`tests/test_chunked_conversion_contract.py`,
`tests/test_document_publication_storage_process.py`,
`tests/test_document_relinking_stage.py`, and
`tests/test_response_inventory_run_spec.py`. Add focused tests where these do
not cover the new boundary; do not regenerate PDFs as a test prerequisite.

Run `make fix`, `make check`, and `git diff --check`. Scope explicit complexity
checks to changed code and review readability, editability, typing, diagnostics,
restart behavior, and deletion evidence. Existing optional whole-repository
complexity findings do not authorize a broad rewrite.

Independently review identity completeness, no-source replay, and the script
migration. Verify that conventional CLI dispatch remains thin, stable content
algorithms are untouched, and the cleanup adds no hidden artifact framework.

## Acceptance criteria and stops

Both gates pass. Accepted real conversion/producer seals remain consumable;
synthetic integrated replay preserves semantics; relevant changes invalidate
and unrelated changes do not; routine replay performs no source/model access
or preserved-large-payload hashing; every rename/removal has caller evidence;
and current docs explain the supported workflow without historical task lore.

Stop on a need to recompute accepted conversion just to accommodate new names,
unexplained semantic changes, invalidation gaps, or unproven deletion safety.
Do not create broad compatibility aliases to bypass a failed migration. Update
the explicit scope when a small coupled change is required for the reuse proof.

## Non-goals

Changing source/target matching rules, acquiring F1, altering chunk-conversion
algorithms, processing documents, Task 05G replay, removing accepted artifacts,
renaming historical evidence, a repository-wide style rewrite, or new workflow,
cache, identity, or review frameworks. Commit and push are separate actions.

## Outcome

Pending implementation. Neither reuse gate nor cleanup gate has run.
