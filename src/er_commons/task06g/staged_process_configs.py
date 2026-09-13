"""Stage Task 06G document-process configs behind sealed runtime checkpoints."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import cast

from er_commons.artifact_io import sha256_file
from er_commons.document_publication.fresh_lineage import _validate_effective_config
from er_commons.document_publication.process_inputs import ProcessConfigs
from er_commons.task06g.core import (
    JsonObject,
    canonical_bytes,
    content_reference,
    load_object,
    pointer_value,
    publish_directory_no_clobber,
    reference,
    set_pointer,
)

STAGE_ORDER = (
    "content_parsing",
    "heading_evidence_parsing",
    "record_mapping",
    "hierarchy_inference",
    "document_structure",
    "document_reference_linking",
)


class Task06GProcessConfigResolver:
    """Sole publisher for one source's immutable Task 06G process-config phases."""

    def __init__(
        self,
        *,
        data_root: Path,
        project_root: Path,
        source_id: str,
        templates: ProcessConfigs,
        resolved_specs_root: Path,
        generation_spec: Path,
        reused_completions: dict[str, Path],
    ) -> None:
        self.data_root = data_root.resolve()
        self.project_root = project_root.resolve()
        self.source_id = source_id
        self.templates = templates
        self.resolved_specs_root = resolved_specs_root.resolve()
        self.generation_spec = generation_spec.resolve()
        self.reused_completions = reused_completions
        self._definition = self._load_definition()
        self._configs: dict[str, Path] = {}
        self._checkpoints: dict[str, Path] = {}
        self._publish_reused_checkpoints()

    def config_for(self, role: str) -> Path:
        """Publish or exactly reuse the predetermined phase for one process role."""
        if role in self._configs:
            return self._configs[role]
        entry = self._entry(role)
        template = self.templates.as_dict()[role].resolve()
        self._verify_template(entry, template)
        value = copy.deepcopy(load_object(template))
        sources: list[JsonObject] = []
        predecessor_refs: list[JsonObject] = []
        ordinal = STAGE_ORDER.index(role)
        if ordinal:
            predecessor = STAGE_ORDER[ordinal - 1]
            predecessor_path = self._checkpoints.get(predecessor)
            if predecessor_path is None:
                raise ValueError(
                    f"Task 06G config requires unpublished checkpoint: {role} <- {predecessor}"
                )
            self._verify_checkpoint(predecessor, predecessor_path)
            predecessor_refs.append(
                {
                    "authority": "artifact_root",
                    **reference(predecessor_path, root=self.data_root),
                }
            )
        for raw in cast(list[object], entry.get("resolutions", [])):
            if not isinstance(raw, dict):
                raise ValueError(f"invalid Task 06G process resolution: {role}")
            resolution = cast(JsonObject, raw)
            source_role = str(resolution["source_stage"])
            checkpoint_path = self._checkpoints.get(source_role)
            if checkpoint_path is None:
                raise ValueError(
                    f"Task 06G config requires unpublished checkpoint: {role} <- {source_role}"
                )
            checkpoint = self._verify_checkpoint(source_role, checkpoint_path)
            resolved = pointer_value(checkpoint, str(resolution["source_pointer"]))
            set_pointer(value, str(resolution["pointer"]), resolved)
            sources.append(
                {
                    "pointer": resolution["pointer"],
                    "value": resolved,
                    "checkpoint": {
                        "authority": "artifact_root",
                        **reference(checkpoint_path, root=self.data_root),
                    },
                    "source_pointer": resolution["source_pointer"],
                }
            )
        content = canonical_bytes(value)
        directory = self.resolved_specs_root / self._phase_directory(role)
        config_name = f"{role}.json"
        receipt_name = f"{role}.receipt.json"
        receipt: JsonObject = {
            "schema_version": "er_commons.task06g.process_config_receipt.v1",
            "source_id": self.source_id,
            "stage": role,
            "template": {
                "authority": "repository",
                **reference(template, root=self.project_root),
            },
            "generator": {
                "authority": "repository",
                **reference(self.generation_spec, root=self.project_root),
            },
            "populated_pointers": sources,
            "resolved": content_reference(config_name, content),
            "validation": {"loader": entry["loader"], "passed": True},
        }
        receipt_bytes = canonical_bytes(receipt)
        manifest: JsonObject = {
            "schema_version": "er_commons.task06g.process_config_phase.v1",
            "source_id": self.source_id,
            "stage": role,
            "generation_spec": {
                "authority": "repository",
                **reference(self.generation_spec, root=self.project_root),
            },
            "external_checkpoints": [
                *predecessor_refs,
                *[
                    item["checkpoint"]
                    for item in sources
                    if item["checkpoint"] not in predecessor_refs
                ],
            ],
            "managed_files": [
                content_reference(config_name, content),
                content_reference(receipt_name, receipt_bytes),
            ],
            "completion_last": True,
        }
        files = {
            config_name: content,
            receipt_name: receipt_bytes,
            "phase_manifest.json": canonical_bytes(manifest),
        }
        if directory.exists():
            self._verify_phase(directory, files)
        else:
            publish_directory_no_clobber(directory, files)
            self._verify_phase(directory, files)
        config_path = directory / config_name
        _validate_effective_config(role, config_path)
        self._configs[role] = config_path
        return config_path

    def record_completion(self, role: str, completion: Path, *, reused: bool = False) -> Path:
        """Seal and independently recompute one stage identity before dependents run."""
        completion = completion.resolve()
        value = load_object(completion)
        derived_id = completion.parents[1].name
        identity_field = {
            "content_parsing": "producer_run_id",
            "heading_evidence_parsing": "producer_run_id",
            "record_mapping": "candidate_id",
            "hierarchy_inference": "candidate_id",
            "document_structure": "extraction_id",
            "document_reference_linking": "extraction_id",
        }.get(role)
        if identity_field is None:
            raise ValueError(f"unsupported Task 06G process identity owner: {role}")
        if value.get(identity_field) != derived_id:
            raise ValueError(f"Task 06G stage completion identity differs: {role}")
        inventory = completion.parents[1] / "records/artifact_inventory.json"
        if not inventory.is_file():
            raise FileNotFoundError(inventory)
        config_path = self.config_for(role)
        recomputed_id = self._verify_owner_identity(role, completion, config_path, reused=reused)
        if recomputed_id != derived_id:
            raise ValueError(f"Task 06G stage identity recomputation differs: {role}")
        config_ref = {
            "authority": "artifact_root",
            **reference(config_path, root=self.data_root),
        }
        checkpoint: JsonObject = {
            "schema_version": "er_commons.task06g.process_identity_checkpoint.v1",
            "source_id": self.source_id,
            "stage": role,
            "resume_reuse": reused,
            "stage_completion": {
                "authority": "artifact_root",
                **reference(completion, root=self.data_root),
            },
            "stage_inventory": {
                "authority": "artifact_root",
                **reference(inventory, root=self.data_root),
            },
            "resolved_config_ref": config_ref,
            "derived_id": derived_id,
            "recomputed_id": recomputed_id,
            "outputs": self._checkpoint_outputs(role, completion, derived_id),
            "verified": True,
        }
        path = self._checkpoint_path(role)
        content = canonical_bytes(checkpoint)
        if path.exists():
            if path.read_bytes() != content:
                raise FileExistsError(f"Task 06G stage checkpoint collision: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(content)
        self._verify_checkpoint(role, path)
        self._checkpoints[role] = path
        return path

    def _verify_owner_identity(
        self, role: str, completion: Path, config_path: Path, *, reused: bool
    ) -> str:
        """Invoke each stage owner's compact verifier and derive its ID from identity bytes."""
        root = completion.parents[1]
        derived_id = root.name
        if role in {"content_parsing", "heading_evidence_parsing"}:
            return self._verify_producer_identity(root, derived_id, config_path, reused=reused)
        if role == "record_mapping":
            from er_commons.document_records.record_mapping.identity import (
                extraction_identity_sha256,
            )
            from er_commons.document_records.record_mapping.publication import (
                verify_completed_candidate as verify_record_mapping_candidate,
            )

            verify_record_mapping_candidate(root, derived_id)
            identity = load_object(root / "records/extraction_identity.json")
            identity_digest = extraction_identity_sha256(identity)
            if identity.get("identity_sha256") != identity_digest:
                raise ValueError("record-mapping identity digest differs")
            return f"exv1-{identity_digest}"
        if role == "hierarchy_inference":
            from er_commons.hierarchy_inference.candidate_verification import (
                verify_completed_candidate as verify_hierarchy_candidate,
            )
            from er_commons.hierarchy_inference.digests import (
                canonical_json_sha256 as hierarchy_digest,
            )

            config = load_object(config_path)
            schema = (self.project_root / str(config["schema_relative_path"])).resolve()
            if not schema.is_relative_to(self.project_root):
                raise ValueError("hierarchy schema escapes repository authority")
            verify_hierarchy_candidate(root, derived_id, schema)
            identity = load_object(root / "records/identity.json")
            payload = {key: item for key, item in identity.items() if key != "candidate_id"}
            return f"hcorv1-{hierarchy_digest(payload)}"
        if role == "document_structure":
            from er_commons.document_records.document_structure.publication import (
                verify_completed_document_structure,
            )
            from er_commons.document_records.record_mapping.identity import (
                extraction_identity_sha256,
            )

            verify_completed_document_structure(root, derived_id)
            identity = load_object(root / "records/extraction_identity.json")
            identity_digest = extraction_identity_sha256(identity)
            if identity.get("identity_sha256") != identity_digest:
                raise ValueError("document-structure identity digest differs")
            return f"exv1-{identity_digest}"
        if role == "document_reference_linking":
            from er_commons.document_records.document_references.publication import (
                verify_completed_candidate as verify_linked_candidate,
            )
            from er_commons.document_records.record_mapping.identity import (
                extraction_identity_sha256,
            )

            verify_linked_candidate(root, derived_id)
            identity = load_object(root / "records/extraction_identity.json")
            if not isinstance(identity.get("cross_reference_contract"), dict):
                raise ValueError("linked-document identity lacks its cross-reference contract")
            identity_digest = extraction_identity_sha256(identity)
            if identity.get("identity_sha256") != identity_digest:
                raise ValueError("linked-document identity digest differs")
            return f"exv1-{identity_digest}"
        raise ValueError(f"unsupported Task 06G process identity owner: {role}")

    def _verify_producer_identity(
        self,
        root: Path,
        derived_id: str,
        config_path: Path,
        *,
        reused: bool,
    ) -> str:
        """Verify producer terminal metadata without hashing preserved image payloads."""
        from er_commons.document_parsing.content_parsing.evidence import (
            verify_inventory_metadata,
        )
        from er_commons.document_parsing.content_parsing.identity import (
            canonical_json_sha256 as producer_digest,
        )
        from er_commons.document_parsing.content_parsing.records import (
            CompletionRecord,
            ProducerSummary,
        )

        records = root / "records"
        identity_path = records / "producer_identity.json"
        inventory_path = records / "artifact_inventory.json"
        summary_path = records / "producer_summary.json"
        identity = load_object(identity_path)
        inventory = load_object(inventory_path)
        completion = CompletionRecord.model_validate_json(
            (records / "completion_record.json").read_bytes()
        )
        summary = ProducerSummary.model_validate_json(summary_path.read_bytes())
        recomputed = f"prv1-{producer_digest(identity['identity'])}"
        recorded_config_sha = identity.get("configuration_sha256")
        config_binding_valid = (
            isinstance(recorded_config_sha, str)
            and len(recorded_config_sha) == 64
            and (reused or recorded_config_sha == sha256_file(config_path))
        )
        if (
            identity.get("producer_run_id") != recomputed
            or not config_binding_valid
            or completion.producer_run_id != recomputed
            or summary.producer_run_id != recomputed
            or completion.source_id != self.source_id
            or summary.source_id != self.source_id
            or completion.artifact_inventory_sha256 != sha256_file(inventory_path)
            or completion.producer_status != summary.producer_status
        ):
            raise ValueError("producer identity or terminal metadata differs")
        verify_inventory_metadata(root, inventory)
        if recomputed != derived_id:
            raise ValueError("producer identity differs from candidate namespace")
        return recomputed

    def effective_configs(self) -> ProcessConfigs:
        """Return the exact six staged configs after the sequence completes."""
        missing = [role for role in STAGE_ORDER if role not in self._configs]
        if missing:
            raise ValueError(f"Task 06G staged process configs are incomplete: {missing}")
        return ProcessConfigs(**self._configs)

    def config_references(self) -> dict[str, JsonObject]:
        """Return authority-aware refs proven by receipts and completed phase manifests."""
        configs = self.effective_configs()
        return {
            role: self.verify_resolved_config(role, path)
            for role, path in configs.as_dict().items()
        }

    def verify_resolved_config(self, role: str, path: Path) -> JsonObject:
        """Reject artifact-root configs lacking their exact receipt and phase entry."""
        expected_directory = self.resolved_specs_root / self._phase_directory(role)
        if path.resolve() != (expected_directory / f"{role}.json").resolve():
            raise ValueError(f"Task 06G config is outside its predetermined phase: {role}")
        receipt = load_object(expected_directory / f"{role}.receipt.json")
        manifest = load_object(expected_directory / "phase_manifest.json")
        if (
            receipt.get("schema_version") != "er_commons.task06g.process_config_receipt.v1"
            or receipt.get("source_id") != self.source_id
            or receipt.get("stage") != role
            or manifest.get("schema_version") != "er_commons.task06g.process_config_phase.v1"
            or manifest.get("completion_last") is not True
        ):
            raise ValueError(f"Task 06G config receipt/phase is invalid: {role}")
        resolved = cast(JsonObject, receipt["resolved"])
        observed = reference(path, root=expected_directory)
        if resolved != observed:
            raise ValueError(f"Task 06G config receipt seal differs: {role}")
        managed = cast(list[object], manifest["managed_files"])
        if not any(isinstance(item, dict) and item == observed for item in managed):
            raise ValueError(f"Task 06G config lacks phase-manifest entry: {role}")
        return {"authority": "artifact_root", **reference(path, root=self.data_root)}

    def _load_definition(self) -> JsonObject:
        generation = load_object(self.generation_spec)
        raw = generation.get("document_process_templates")
        if not isinstance(raw, dict):
            raise ValueError(
                f"generation recipe lacks Task 06G process templates: {self.source_id}"
            )
        sources = raw.get("sources")
        resolutions = raw.get("runtime_resolutions")
        if (
            raw.get("stage_order") != list(STAGE_ORDER)
            or raw.get("phase_root") != "document_stages"
            or not isinstance(sources, dict)
            or not isinstance(sources.get(self.source_id), dict)
            or not isinstance(resolutions, dict)
        ):
            raise ValueError(
                f"generation recipe lacks Task 06G process templates: {self.source_id}"
            )
        definition = cast(JsonObject, copy.deepcopy(sources[self.source_id]))
        if set(definition) != set(STAGE_ORDER) or set(resolutions) != set(STAGE_ORDER):
            raise ValueError(f"Task 06G process template closure differs: {self.source_id}")
        for role in STAGE_ORDER:
            cast(JsonObject, definition[role])["resolutions"] = resolutions[role]
        return definition

    def _entry(self, role: str) -> JsonObject:
        if role not in STAGE_ORDER or not isinstance(self._definition.get(role), dict):
            raise ValueError(f"Task 06G process template is not declared: {role}")
        return cast(JsonObject, self._definition[role])

    def _verify_template(self, entry: JsonObject, template: Path) -> None:
        expected = (self.project_root / str(entry["template"])).resolve()
        if template != expected or not template.is_relative_to(self.project_root):
            raise ValueError("Task 06G runtime template differs from frozen path")
        if sha256_file(template) != entry["template_sha256"]:
            raise ValueError("Task 06G runtime template digest differs")
        if template.stat().st_size != entry["template_byte_size"]:
            raise ValueError("Task 06G runtime template size differs")

    @staticmethod
    def _verify_phase(destination: Path, expected: dict[str, bytes]) -> None:
        observed = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        if observed != expected:
            raise ValueError(f"Task 06G process-config phase differs: {destination}")

    def _publish_reused_checkpoints(self) -> None:
        for role in STAGE_ORDER:
            completion = self.reused_completions.get(role)
            if completion is None:
                continue
            self.config_for(role)
            self.record_completion(role, completion, reused=True)

    def _checkpoint_path(self, role: str) -> Path:
        return (
            self.resolved_specs_root
            / "document_stage_checkpoints_v1"
            / self.source_id
            / f"{STAGE_ORDER.index(role) + 1:02d}_{role}.json"
        )

    def _phase_directory(self, role: str) -> Path:
        return Path(
            "document_stages",
            self.source_id,
            f"{STAGE_ORDER.index(role) + 1:02d}_{role}",
        )

    def _verify_checkpoint(self, role: str, path: Path) -> JsonObject:
        checkpoint = load_object(path)
        if (
            checkpoint.get("schema_version") != "er_commons.task06g.process_identity_checkpoint.v1"
            or checkpoint.get("source_id") != self.source_id
            or checkpoint.get("stage") != role
            or checkpoint.get("verified") is not True
            or checkpoint.get("derived_id") != checkpoint.get("recomputed_id")
        ):
            raise ValueError(f"Task 06G process checkpoint is invalid: {role}")
        completion_ref = cast(JsonObject, checkpoint["stage_completion"])
        completion = (self.data_root / str(completion_ref["path"])).resolve()
        if (
            completion_ref.get("authority") != "artifact_root"
            or not completion.is_relative_to(self.data_root)
            or reference(completion, root=self.data_root)
            != {key: completion_ref[key] for key in ("path", "sha256", "byte_size")}
        ):
            raise ValueError(f"Task 06G process checkpoint completion differs: {role}")
        derived_id = str(checkpoint["derived_id"])
        if derived_id != completion.parents[1].name:
            raise ValueError(f"Task 06G process checkpoint identity differs: {role}")
        inventory_ref = cast(JsonObject, checkpoint["stage_inventory"])
        inventory = completion.parents[1] / "records/artifact_inventory.json"
        if inventory_ref.get("authority") != "artifact_root" or reference(
            inventory, root=self.data_root
        ) != {key: inventory_ref[key] for key in ("path", "sha256", "byte_size")}:
            raise ValueError(f"Task 06G process checkpoint inventory differs: {role}")
        config_ref = cast(JsonObject, checkpoint["resolved_config_ref"])
        config = (self.data_root / str(config_ref["path"])).resolve()
        if (
            config_ref.get("authority") != "artifact_root"
            or self.verify_resolved_config(role, config) != config_ref
        ):
            raise ValueError(f"Task 06G process checkpoint config differs: {role}")
        if checkpoint.get("outputs") != self._checkpoint_outputs(role, completion, derived_id):
            raise ValueError(f"Task 06G process checkpoint outputs differ: {role}")
        return checkpoint

    def _checkpoint_outputs(self, role: str, completion: Path, derived_id: str) -> JsonObject:
        candidate_root = completion.parents[1]
        outputs: JsonObject = {
            "candidate_id": derived_id,
            "candidate_root": candidate_root.relative_to(self.data_root).as_posix(),
            "artifact_root": candidate_root.parent.relative_to(self.data_root).as_posix(),
        }
        if role in {"content_parsing", "heading_evidence_parsing"}:
            outputs["producer_root"] = completion.parents[2].relative_to(self.data_root).as_posix()
        return outputs

    @staticmethod
    def generation_spec_for_run(
        run_spec_path: Path, data_root: Path, project_root: Path
    ) -> Path | None:
        """Find the sole frozen recipe whose namespace owns this resolved run spec."""
        run_spec_path = run_spec_path.resolve()
        data_root = data_root.resolve()
        if not run_spec_path.is_relative_to(data_root) or not run_spec_path.is_file():
            return None
        run = load_object(run_spec_path)
        artifact_relative_root = run.get("artifact_relative_root")
        if not isinstance(artifact_relative_root, str):
            return None
        publication_root = (data_root / artifact_relative_root).resolve()
        expected = publication_root.parent / (
            "resolved_specs_v1/00_initial/task06g_document_v1.json"
        )
        if run_spec_path != expected:
            return None
        matches: list[Path] = []
        candidates = (project_root / "configs/task06").glob("v*/task06g_generation_v1.json")
        for candidate in sorted(candidates):
            generation = load_object(candidate)
            phases = generation.get("phases")
            recipe = generation.get("production_identity_recipe")
            if not isinstance(phases, dict) or not isinstance(recipe, dict):
                continue
            initial = phases.get("initial")
            if not isinstance(initial, dict):
                continue
            specs = initial.get("specs")
            if not isinstance(specs, list):
                continue
            template_rows = [
                row
                for row in specs
                if isinstance(row, dict) and row.get("destination") == "task06g_document_v1.json"
            ]
            if len(template_rows) != 1:
                continue
            template = candidate.parent / str(template_rows[0].get("template"))
            if not template.is_file():
                continue
            template_value = load_object(template)
            if template_value.get("artifact_relative_root") == artifact_relative_root:
                matches.append(candidate.resolve())
        if len(matches) != 1:
            return None
        return matches[0]


def task06g_resolver(
    *,
    data_root: Path,
    project_root: Path,
    source_id: str,
    templates: ProcessConfigs,
    run_spec_path: Path,
    reused_completions: dict[str, Path],
) -> Task06GProcessConfigResolver:
    """Construct the exact Task 06G resolver after recognizing its run-spec authority."""
    generation_spec = Task06GProcessConfigResolver.generation_spec_for_run(
        run_spec_path, data_root, project_root
    )
    if generation_spec is None:
        raise ValueError("Task 06G resolver received another run spec")
    resolved_specs_root = run_spec_path.resolve().parents[1]
    return Task06GProcessConfigResolver(
        data_root=data_root,
        project_root=project_root,
        source_id=source_id,
        templates=templates,
        resolved_specs_root=resolved_specs_root,
        generation_spec=generation_spec,
        reused_completions=reused_completions,
    )


__all__ = ["Task06GProcessConfigResolver", "task06g_resolver"]
