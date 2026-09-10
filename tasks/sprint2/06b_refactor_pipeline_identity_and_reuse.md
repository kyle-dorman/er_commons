# Task 06B: Refactor Pipeline Identity, Reuse, and Maintained Entry Points

Status: **Complete: Gates 1 and 2 independently reviewed (2026-09-10).** This is one task with two sequential gates,
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

## Gate 1 outcome

Gate 1 was authorized on 2026-09-10 from clean commit
`257b5620dfcb8f31d0af8f7faf21d54262834341`. Implementation, synthetic proof,
compact real-input qualification, and independent review were performed within
the source-free boundary. This section records Gate 1; the separately authorized
Gate 2 outcome is recorded below.

### Implemented boundary

The [Gate 1 verification specification](../../docs/specs/task06b_verification_boundaries_v1.md)
routes the finite conversion, publication, response, and structure inventories.
Historical readers verify recorded preimages and terminal seals without requiring
old implementation paths to exist. Current writers verify current code/contracts
and ordered physical source identities. Completed range consumption is separate
from incompatible incomplete execution resume. Historical recipes and generated
accepted configurations were not rewritten.

The document/collection v3 input models add per-source original manifest selection
and explicit logical-to-physical membership. Synthetic 35-slot coverage retains
34 original releases while substituting only F1 with explicit old/new evidence.
Membership, source digests, original release, order, and missing/duplicate slots
are checked. Existing v2 schemas retain their original closed-object meaning.

One invocation budget enforces the 06A semantic hash-role allowlist and numerical
ceilings before opening files. Prepared publication/relink state loads each
source manifest and shared navigation once, retains per-source coverage checks,
and rejects altered specs, roots, source selections, current recipes, or budget
replacement. Metadata snapshots also reject changes during preparation. New
output publication preserves recorded digests for unchanged inherited support;
explicit deep audits hash synthetic payload bytes and detect same-size corruption.

The small new owners `artifact_verification.py`,
`document_publication/accepted_inputs.py`,
`document_publication/candidate_identity_validation.py`, and
`collection_processing/source_membership.py` keep existing maintainability
limits. Additional touched shared inventory/publication helpers are listed in
the boundary specifications. These are Gate 1 responsibility splits; no Gate 2
rename/remove inventory item was executed.

### Real-input qualification

The exact 06A packet inventory was authenticated against its recorded SHA-256.
Oversized packet/source metadata retained recorded digests and was read within
its separate ceiling. Two bounded qualification invocations wrote new evidence
beneath `pipelines/brisbane_baylands/task_06_recovery_v1/06b/`:

| Evidence | Qualified inputs | Compact hash bytes | Selected read bytes |
| --- | --- | ---: | ---: |
| `gate1_qualification_v1/qualification.json` | 35 conversions and producers; 20 chunked sources, 318 completed ranges | 30,008,564 | 149,614,204 |
| `gate1_document_qualification_v1/qualification.json` | All 70 accepted 03J/04D document publications, identity preimages and upstream completions | 1,757,612 | 2,503,643 |

Both invocations stayed below 1 MiB per hashed file and 32 MiB total; combined
compact hashing was 31,766,176 bytes. Both include main and Appendix A; chunk
qualification also covers G1, G2, G3 and all other large selected documents.
Each result lists actual unchanged conversion/producer/document/range IDs,
source bindings, verification observations and limits. No production replay or
new production handoff was created. Wrong F1 remains historical evidence only.

These are compact integrity and compatibility observations, **not fresh
payload-byte equality**. Stored payload digests, sizes and exact file closure
cannot detect an unread same-size mutation. That behavior is deliberately proved
only by explicit synthetic deep-audit tests.

### Validation and independent review

`make fix` and final `make check` passed: formatting, lint, mypy (457 source
files), and **1,479 tests**. `git diff --check` passed. The independent
[Gate 1 review](../../docs/specs/task06b_gate1_review.md) has no unresolved
actionable finding. Review covered identity completeness, source-free publication,
shared budgets, schema compatibility and human maintainability. Findings were
fixed rather than waiving the existing ownership tests: missing shared code
inputs, raw downstream read/hash calls, prepared source/recipe consistency,
repeated reviewed-navigation reads, and rehashing unchanged copied support.

A changed-file complexity check at McCabe threshold 15 found only the unchanged
`record_mapping.publication.validate_inventory_metadata` function (16); its AST
was verified unchanged from the starting commit. Changed functions passed that
check, and existing function/module ownership tests passed without relaxing them.

The final compact output inventory and qualification reproduction scripts are
under `06b/gate1_outcome_v1/`; these are bounded evidence tools, not production
entry points. It references both qualification results and final check/review
records. Real qualification preceded final helper extraction; final synthetic
and whole-repository checks cover the final implementation.

The learning checkpoint applied [DVC stage conditions](https://doc.dvc.org/user-guide/pipelines/run-cache)
and [W3C derivation](https://www.w3.org/TR/prov-o/) without adopting a new workflow
system. Code provenance explains the historical entity; a new descendant pins
that entity and its own current behavior. Metadata qualification explicitly
trades deep corruption detection for bounded, source-free reuse.

### Gate 1 stopping boundary (historical)

No Gate 1 blocker remains. Gate 2 is ready for its separately scoped execution;
it was explicitly excluded from this run. Gate 2 may use the new readers and synthetic regression tests to execute only
the frozen 06A rename/remove/retain inventory. Accepted artifact names, recipes,
source manifests and human decisions remain fixed. No source PDF acquisition or
opening, page rendering, model loading, conversion, extraction, production
replay, artifact deletion, commit or push was performed. F1 processing remains
behind the later task gates.

## Gate 2 outcome

Gate 2 was authorized on 2026-09-10 by the subsequent instruction, “ok execute
gate 2 end to end.” It builds on the uncommitted Gate 1 changes at base commit
`257b5620dfcb8f31d0af8f7faf21d54262834341`. No commit or push was performed.

### Implemented migration

The [executed inventory](../../docs/specs/task06b_gate2_executed_inventory.md)
accounts for every one of the frozen table's 90 rows: 73 migrated, 15 retired,
and 2 retained. Generation, input preparation, the serial collection runner,
review, navigation, relink preparation, diagnostics and policy imports now use
responsibility owners. The first two preparation wrappers share one maintained
input-preparation owner. The isolated pilot replay and unused v1 bundle adapter
were removed after caller inspection; active historical readers remain.
Maintained replay ownership assertions were transferred before isolated tests
were retired.

All current commands take explicit requests/roots/selections; the
[command map](../../docs/pipeline_commands.md) covers preparation, execution,
compact validation, deliberate deep audit and review. Make mutation/review roots
are required inputs. New request schemas and the separate navigation Gate A v2
command schema leave all accepted JSON configs, fixture recipes and old schemas
unchanged. The 06C–06H contracts now point to the maintained command/owner maps.

Generation validates all six process owners, document/collection v3, catalog and
identity proposals before writes. It preserves original per-source manifests,
explicit replacement membership and the accepted chunk threshold of 300.
Preparation shares one invocation budget and verifies source/digest controls.
The runner binds one spec digest to its progress and rejects mutation before
recording success. Review assets and historical human-decision semantics remain
unchanged; the final review profile remains explicit until later policy work.

### Evidence and integrity limits

Post-migration qualification reused the exact Gate 1 source/range/document ID
rows through compact historical readers with the old implementation paths absent:

| Qualification | Accepted population | Hash bytes | Read bytes |
| --- | --- | --- | --- |
| Conversion, producer and completed ranges | 35 conversion/producer pairs; 20 chunked documents; 318 completed ranges | 30,008,564 | 149,614,204 |
| Document publications | 70 Task 03J/04D publications, including main and Appendix A | 1,757,612 | 2,503,643 |

The new qualification files are under the external 06B root:
`gate2_conversion_qualification_v1/qualification.json` and
`gate2_document_qualification_v1/qualification.json`. Their ID rows and byte
budgets match Gate 1. Metadata observations are not a new payload-byte equality
claim. No accepted large payload was rehashed; same-size corruption is covered
by explicit synthetic deep-audit tests. No unchanged conversion was needed.

The external `gate2_outcome_v1/` packet records final checks, compact qualification
references, complete ID correspondence, the executed inventory and review. It
is diagnostic evidence, not a new production extraction or handoff.

### Final validation

`make fix` and `make check` passed after the final code changes: Ruff formatting
and lint, mypy over 462 source files, and **1,541 tests**. `git diff --check`
passed. All 18 maintained wrappers in the finite inventory passed `--help`.
The full synthetic relink/publication path retains its PDF/model/conversion/
preserved-payload-hash sentinels. The positive preparation integration validates
and reloads all four outputs, preserves v3 membership/original manifests and
proves no-clobber retries. No test threshold was relaxed.

### Review and next boundary

The [independent Gate 2 review](../../docs/specs/task06b_gate2_review.md) records
resolved identity, v3 schema, exact-closure, budget and proposal-validation
findings. Separate reviewers cover generation/runner, navigation/preparation,
root diagnostics/retirements and extraction review. All maintained wrappers pass
help smoke checks; a built wheel contains the four byte-identical review assets
under the new package and no old review package.

Task 06C is the next contract to revalidate against the accepted outcomes. Its
Final F1 acquisition/qualification and conversion authorizations remain separate.
No source acquisition, accepted PDF opening, rendering, model loading, extraction,
production replay, accepted artifact deletion, commit or push was performed.
Tasks 06C–06H have not executed.

Both gates are complete. No Gate 2 blocker remains. Stop here before Task 06C execution.
