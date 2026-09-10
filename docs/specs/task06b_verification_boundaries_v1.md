# Task 06B Gate 1 verification boundary v1

Gate 1 starts at `257b562`. This specification supplements, without changing,
the sealed 06A recovery plan and inventories. Gate 2 remains unexecuted.

`artifact_verification.VerificationBudget` is the small invocation-owned enforcement seam.
Existing owners pass the same instance through nested accepted readers. It
checks containment and size before opening; only explicit compact seal roles
and current code/config/schema may be hashed (1 MiB/file, 32 MiB/invocation).
Selected evidence reads are separately bounded (512 MiB/file, 2 GiB/invocation).
Payload roles cannot be hashed through this interface, regardless of suffix or
size. Oversized metadata is read and reported as metadata checked. Stat checks
and stored digests never claim fresh payload equality. Deep validators retain
explicit byte-checking semantics and are used only with synthetic fixtures here.
No persistent cache, new dependency, or changed serialization is introduced.

Finite owner lists and the minimal collaborator extensions are frozen in the
conversion, publication, and response boundary specifications before their
respective edits. Shared `artifact_io.py` remains an actual behavior dependency.

The research checkpoint rechecked [DVC run-cache conditions](https://doc.dvc.org/user-guide/pipelines/run-cache),
[W3C entities and derivation](https://www.w3.org/TR/prov-o/), and
[pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html).
These support explicit stage inputs, preserved provenance, and executable
prohibited-I/O tests without adding a workflow framework.

Minimal source-reader extension: `content_parsing/sources.py` owns existing
source-manifest seal loading, so its named metadata reader must live there to
avoid duplicating release validation in collection/publication. It returns the
same source manifest model, without PDF access, and retains oversized manifest
digests as recorded claims. `document_publication/sources.py` selects each
source's original release override. Collection v3 records explicit ordered
logical-slot membership and validates each selection against its own release;
only the F1 slot can substitute a distinct physical source. Historical v2 stays
strict and unchanged in meaning.

Maintainability adjustment during Gate 1: the existing neutral `artifact_io.py`
has a 320-line ownership limit. Keep serialization there unchanged and place the
invocation budget in `artifact_verification.py` (standard-library dataclass,
explicitly passed state; no registry or cache). This is the minimum new owner
for the policy and keeps both modules independently readable. Callers import the
budget directly; no compatibility alias or serialization change is introduced.

## Implemented interfaces

- `artifact_verification.VerificationBudget`: one invocation's allowlisted
  hashes, selected reads, metadata observations, and pre-open ceilings.
- `content_parsing.conversion_seal.read_accepted_conversion`,
  `content_parsing.evidence.read_accepted_producer`, and
  `chunked_conversion.runtime.inputs.read_accepted_range`: historical readers.
  Supply the exact selected root/identity/source and the same budget instance.
- `document_publication.storage.verify_candidate_metadata` plus
  `candidate_identity_validation.verify_identity_and_upstreams`: compact
  document closure and recorded identity/upstream checks. `verify_candidate`
  remains an explicit byte audit; conversion uses `deep_audit_conversion_bundle`.
- `document_publication.accepted_inputs.prepare_publication_inputs`: verify the
  current writer recipe and original source manifests once. Prepared state pins
  spec, source membership and input metadata; it rejects changed inputs and a
  substituted invocation budget. It does not initialize source/model execution.
- `document_publication.downstream_replay.publish_downstream_replay`: source-free
  descendant publication using those inputs. Existing `documents relink`,
  `documents relink-and-replay`, and `collections relink-and-assemble` enter the
  compact path. Fresh `publish-document` is a separate execution boundary and
  is not a metadata-only qualification command.

The document v3 run spec permits paired per-source
`source_release_version`/`source_manifest_relative_path` overrides. Collection
v3 requires exact ordered `source_membership` mapping logical to physical IDs.
Only F1 may substitute a physical ID, with explicit original/replacement source
and original-release evidence. The 34 unchanged slots retain their original
release. Historical v2 specifications reject the new fields and remain unchanged.

Finite owner inventories and minimal scope adjustments are recorded in the
[conversion](task06b_conversion_boundaries_v1.md),
[publication](task06b_publication_boundaries_v1.md),
[response](task06b_response_boundaries_v1.md), and
[structure](task06b_structure_boundaries_v1.md) specifications. The frozen 06A
specifications and external packet are historical inputs and are not rewritten.
