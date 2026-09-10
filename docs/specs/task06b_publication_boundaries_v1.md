# Task 06B publication boundaries v1

Frozen before implementation. Historical document readers validate recorded
identity preimages and completion/inventory bindings without deriving current
production recipes. Explicit accepted metadata mode checks exact managed path
membership and sizes, retaining recorded payload digests; deep verification
remains the default for existing deep-audit callers. Metadata mode cannot detect
same-size payload corruption.

The source-free publication entry point selects the historical source identity
from the explicitly selected sealed document. It must match the original
per-source manifest binding; fresh-source preparation remains a separate writer
entry point. Replacement collection members retain explicit original manifest
and physical source bindings. Prepared relink state owns one invocation budget,
all shared reference checks, and reviewed-navigation validation. Reuse checks
reject spec/reference drift and per-source coverage mismatches.

Necessary collaborators are candidates.py (recorded identity preimage checking),
downstream_replay_validation.py (compact lineage references), relink_preflight.py
(mixed collection membership), and reviewed_navigation.py (compact bundle reader).
Existing content algorithms and schema identifiers of accepted records stay fixed.
New authoritative output uses existing completion-last publication. Current code
inventories are finite per stage and are independent of historical recipes.

Hash roles and limits are the 06A allowlist, 1 MiB per record, shared 32 MiB per
invocation. Oversized metadata is read under the shared 512 MiB/file, 2 GiB/run
read limits without a fresh digest claim. Preserved payloads are never eligible
compact hash roles. Synthetic integration tests guard source access, conversion,
model loading and historical payload hashing, and separately test deep corruption.

Integration ownership refinements: `accepted_inputs.py` prepares current writer
controls and each original release once, while `candidate_identity_validation.py`
validates recorded candidate/control identities independently of byte auditing.
`collection_processing/source_membership.py` validates replacement composition.
These named helpers keep the existing module/function maintainability limits.
`record_mapping/publication.py` receives an optional sealed-file inventory for
unchanged copied support: it preserves recorded digests rather than rehashing
those payloads. New records retain normal output hashing and completion-last
closure. These are Gate 1 verification/publication boundaries, not Gate 2 renames.

Gate 1 current-writer provenance also updates the existing production recipe
generators in `scripts/prepare_task04d_gate_c_specs.py` and
`scripts/task03h_generation/production_identity.py`: their future inventories
include the new budget, prepared-input, candidate-validation and collection
membership owners. This is necessary dependency completeness, with no wrapper
rename/removal and no edit to accepted generated recipes or configurations.

## Gate 1 implementation evidence

`storage.verify_candidate_metadata` checks the typed completion/identity,
recomputes the recorded control and candidate identity, reconstructs content
identity from the sealed inventory, and checks exact managed membership and
sizes. `candidate_identity_validation.verify_identity_and_upstreams` checks
upstream completion bindings. Existing `verify_candidate` remains a deep audit
and now builds one observed inventory rather than hashing it twice.

`accepted_inputs.prepare_publication_inputs` prepares current writer controls
and every distinct original manifest once. `prepare_accepted_document_run`
selects a source without PDF access. Prepared state is invocation-local, retains
its budget, and rejects changed controls and source bindings. Document run spec
v3 adds paired per-source `source_manifest_relative_path` and
`source_release_version`; historical v2 inputs remain readable.

Linked publication retains recorded digests for inherited support copies.
Downstream publication composes its content inventory from the selected linked
seal and carries those digests through the new content copy, hashing only newly
owned control records. This is digest propagation from explicitly consumed
entities, not fresh payload-byte equality.

`tests/test_task06b_publication_reuse.py` executes real synthetic relinking and
publication twice under PDF-open, model/converter-import, converter-execution,
and preserved-payload hash sentinels. The opaque preserved-support sentinel also
applies at copied destinations. It tests deep-only same-size corruption,
extra/duplicate managed membership, historical missing implementation paths,
prepared specification drift, invocation-budget replacement rejection, and v3
manifest pairs. Review/navigation tests independently cover prepared bundle
reuse and its historical recipe boundary.
