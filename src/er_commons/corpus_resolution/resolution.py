"""Build immutable corpus-resolution artifacts from independently derived inputs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.outcomes import DocumentTerminalEvidence
from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256
from er_commons.corpus_extraction_contract_v1_1.identity import build_resolution_id
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.catalog import CorpusCatalog, ScopeInputStore
from er_commons.corpus_resolution.domain import PublishedStage, StageBuild, StageName
from er_commons.corpus_resolution.mentions import MentionManifestBuilder
from er_commons.corpus_resolution.resolver import CorpusMentionResolver
from er_commons.corpus_resolution.storage import bytes_ref, inventory_ref, json_bytes, jsonl_bytes


@dataclass(frozen=True)
class ResolutionInputs:
    """Verified index, candidate evidence, and controls for resolution."""

    extraction_root: Path
    data_root: Path
    catalog_relative_path: Path
    production_extraction_id: str
    scope_id: str
    index: JsonObject
    index_stage: PublishedStage
    evidence: tuple[DocumentTerminalEvidence, ...]
    resolution_policy_sha256: str


class ResolutionBuilder:
    """Derive mention coverage, resolve it once, and close the identity."""

    def build(self, inputs: ResolutionInputs) -> StageBuild:
        """Return complete deterministic resolution bytes for publication."""
        catalog = CorpusCatalog.load(inputs.data_root, inputs.catalog_relative_path)
        input_store = ScopeInputStore(inputs.extraction_root, inputs.scope_id)
        catalog_ref = input_store.publish("corpus_catalog", catalog.raw_bytes)
        manifest = MentionManifestBuilder(inputs.extraction_root, catalog.lookup).build(
            inputs.evidence
        )
        manifest_record = manifest.as_record(
            index_id=str(inputs.index["index_id"]), catalog_ref=catalog_ref
        )
        manifest_ref = input_store.publish("mention_input_manifest", json_bytes(manifest_record))
        resolutions = CorpusMentionResolver(
            index=inputs.index,
            evidence=inputs.evidence,
            catalog_lookup=catalog.lookup,
            catalog_ref=catalog_ref,
            scope_id=inputs.scope_id,
        ).resolve_all(manifest.mentions)
        return self._stage_build(inputs, manifest_record, manifest_ref, resolutions)

    def _stage_build(
        self,
        inputs: ResolutionInputs,
        manifest: JsonObject,
        manifest_ref: JsonObject,
        resolutions: list[JsonObject],
    ) -> StageBuild:
        resolution_bytes = jsonl_bytes(resolutions)
        counts = Counter(row["status"] for row in resolutions)
        count_record: JsonObject = {
            "total": len(resolutions),
            "resolved": counts["resolved"],
            "ambiguous": counts["ambiguous"],
            "unresolved": counts["unresolved"],
        }
        snapshots = self._candidate_snapshots(inputs.evidence)
        semantic_payloads = {"resolutions.jsonl": resolution_bytes}
        preimage = self._preimage(
            inputs, manifest_ref, resolution_bytes, count_record, snapshots, semantic_payloads
        )
        resolution_id = build_resolution_id(preimage)
        final_relative = f"scopes/{inputs.scope_id}/resolutions/{resolution_id}"
        payloads = {
            **semantic_payloads,
            "records/identity_preimage.json": json_bytes(preimage),
        }
        refs = {
            name: bytes_ref(f"{final_relative}/{name}", value) for name, value in payloads.items()
        }
        completion: JsonObject = {
            "record_type": "resolution_completion",
            "schema_version": "er_commons.resolution_completion.v1_1",
            "resolution_id": resolution_id,
            "index_id": inputs.index["index_id"],
            "identity_preimage": preimage,
            "identity_preimage_ref": refs["records/identity_preimage.json"],
            "index_completion_ref": inputs.index_stage.completion_ref,
            "mention_input_manifest": manifest,
            "mention_input_manifest_ref": manifest_ref,
            "resolutions": resolutions,
            "resolutions_ref": refs["resolutions.jsonl"],
            "counts": count_record,
            "candidate_inventories_before": snapshots,
            "candidate_inventories_after": snapshots,
            "artifact_inventory": inventory_ref(final_relative, payloads),
            "completion_last": True,
            "status": "complete",
        }
        return StageBuild(StageName.RESOLUTION, resolution_id, payloads, completion)

    @staticmethod
    def _preimage(
        inputs: ResolutionInputs,
        manifest_ref: JsonObject,
        resolution_bytes: bytes,
        counts: JsonObject,
        snapshots: list[JsonObject],
        payloads: dict[str, bytes],
    ) -> JsonObject:
        return {
            "schema_version": "er_commons.corpus_resolution_identity.v1_1",
            "production_extraction_id": inputs.production_extraction_id,
            "scope_id": inputs.scope_id,
            "index_completion_sha256": inputs.index_stage.completion_ref["sha256"],
            "mention_input_manifest_sha256": manifest_ref["sha256"],
            "resolutions_sha256": bytes_ref("unused", resolution_bytes)["sha256"],
            "counts_sha256": canonical_sha256(counts),
            "before_after_inventories_sha256": canonical_sha256(
                {"before": snapshots, "after": snapshots}
            ),
            "resolution_policy_sha256": inputs.resolution_policy_sha256,
            "managed_inventory_sha256": inventory_ref("unused", payloads)["sha256"],
        }

    @staticmethod
    def _candidate_snapshots(
        evidence: tuple[DocumentTerminalEvidence, ...],
    ) -> list[JsonObject]:
        return [
            {"candidate_id": item.candidate_id, "inventory_ref": item.candidate_inventory_ref}
            for item in evidence
            if item.candidate_id is not None
        ]
