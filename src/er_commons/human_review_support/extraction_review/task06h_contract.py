"""Frozen source-free bindings and questions for the Task 06H review."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class AcceptedSeal:
    """One metadata seal resolved below a caller-supplied accepted root."""

    name: str
    root: str
    path: str
    sha256: str
    verification: Literal["hash", "completion_reference"] = "hash"
    completion_path: str | None = None


SEALS = (
    AcceptedSeal(
        "readiness_inventory",
        "candidate",
        "artifact_inventory.json",
        "c7cfa65479c3a3ef787617f4461176e1ce7582633aeeceb6dabc977400edff49",
    ),
    AcceptedSeal(
        "readiness",
        "candidate",
        "readiness.json",
        "3bd11f48e75ed4e1078eaacf89c4adf6edaaf64c39cab4f55911973c19bfd057",
    ),
    AcceptedSeal(
        "handoff_completion",
        "handoff",
        "records/completion_record.json",
        "aceb25700dc329ad0d3a1949202fdb027e3502833f5c45278654ae9ed53b2bca",
    ),
    AcceptedSeal(
        "finalization_receipt",
        "task06g",
        "finalization_attempt_v3/validation_receipt.json",
        "d1ec807d2333bc84a435b53cdccc725e7f8de6a30a874df1c9c21a3dc1104369",
        "completion_reference",
    ),
    AcceptedSeal(
        "finalization_amendment",
        "repo",
        "configs/task06/v4/task06g_finalization_amendment_v2.json",
        "79793f06cdac949d34db004b3c3b4e5898e97aa82eda0510b9567e2ab9dd7c75",
        "completion_reference",
    ),
    AcceptedSeal(
        "execution_spec",
        "replay",
        "resolved_specs_v1/00_initial/task06g_execution_v1.json",
        "ff50306b713384aaaae525d8c356af7ed9d228ffc8f8ae6412762952594167fa",
    ),
    AcceptedSeal(
        "selected_execution",
        "task06g",
        "execution_attempt_v20/execution.json",
        "102f6e23b9ec54213d62ef6919e12086395649e500ed854af8054ae53c7a32c0",
        "completion_reference",
        "execution.json",
    ),
    AcceptedSeal(
        "launch_intent",
        "task06g",
        "initial_launch_v38/launch_intent.json",
        "83a225a990312a3ada1e4050be0f219fe0f99a6feaf52aff899d56bd4f1851e4",
        "completion_reference",
    ),
    AcceptedSeal(
        "correspondence_completion",
        "correspondence",
        "completion.json",
        "57aeec4ebf63f996f13e392df8643899c6103c6a9673b5b96c480ed08965f9ed",
    ),
    AcceptedSeal(
        "review_correspondence",
        "correspondence",
        "review_correspondence.json",
        "b7aead4175c725ba0df6a24d48caf63f7ced6264ec9b622894aa99155f357122",
    ),
    AcceptedSeal(
        "source_correspondence",
        "correspondence",
        "source_correspondence.json",
        "b5faf915fa6ca655b116cc7dc7dcb9728700971248c69a7e2df9ef72784b23be",
    ),
    AcceptedSeal(
        "target_correspondence",
        "correspondence",
        "target_correspondence.json",
        "2774d1f6bb2d869b5a807a7efbb8e80b7470a8a28b10d171b0f7ee374dbecbe1",
    ),
    AcceptedSeal(
        "comparison_completion",
        "comparison",
        "completion.json",
        "2b2e76a7b645468a78f4f7bbe0b97185a671911a7c01323d378941ae09134b51",
    ),
    AcceptedSeal(
        "reference_comparison",
        "comparison",
        "reference_comparison.json",
        "dfd44c73ed73f32770603517192e4ef75ba07122c5e8f5a9eb0eb97abb4a311e",
    ),
    AcceptedSeal(
        "resolution_comparison",
        "comparison",
        "resolution_comparison.json",
        "9cc58c286be8cc74118b70b540a3fedd33ab9e3201ddd76d997a0a72e7434ac3",
    ),
    AcceptedSeal(
        "link_population_comparison",
        "comparison",
        "link_population_comparison.json",
        "b7655ffefe2e7b333849e3178a8a41969edfcf83a1b3064402fda4d31ec99941",
    ),
    AcceptedSeal(
        "repair_checks",
        "comparison",
        "repair_checks.json",
        "940b4d45d73ecaf301facaae9d8dd00f99702ee2e8844aa2d1cb7a1f43c4f940",
    ),
    AcceptedSeal(
        "06d_completion",
        "task06d",
        "completion.json",
        "c5c6a2b7f2196dd1d3f49c8ab47fe5dd61f1a55013980112b92211591b644ebd",
    ),
    AcceptedSeal(
        "06d_qualification",
        "task06d",
        "qualification.json",
        "20148e6a030f243dc76c85575d5654df0f2ff0a892c6c764598daa760d0d7574",
    ),
    AcceptedSeal(
        "06d_decisions",
        "task06d",
        "eligible_decisions.jsonl",
        "7706c1968e973660ccb417d610dd34d2a4be3c8f3844cf421ed3f88bb0996b69",
    ),
    AcceptedSeal(
        "06e_completion",
        "task06e",
        "completion.json",
        "0e68f116c5f8f0c0ec6b45c32d351a9ce94326eed39d00e0936c345e9895c7a6",
    ),
    AcceptedSeal(
        "06e_qualification",
        "task06e",
        "qualification.json",
        "144ae24ad12481f795e929e1af70cf632e373fa3e13503a6e2e38336e2e66cee",
    ),
    AcceptedSeal(
        "06e_decisions",
        "task06e",
        "eligible_decisions.jsonl",
        "b70a12df368c74fd814a88085b7e802afc8ecb295300c56d7bd5dfc1f890b4ce",
    ),
    AcceptedSeal(
        "06f_completion",
        "task06f",
        "completion.json",
        "f6420863cc1e62de6cc82867f01af0d22d9086504b52cd4c3ab7f390dcdd50b6",
    ),
    AcceptedSeal(
        "06f_qualification",
        "task06f",
        "qualification.json",
        "1b2eaa6f6f594fbdb743b9d91fcc7a3379b782992683539634885a5d1c29f667",
    ),
    AcceptedSeal(
        "06f_aliases",
        "task06f",
        "figure_aliases.jsonl",
        "87cffe4c7f448d8cf824cae4918028508aa5f95564b16d7106142579b84834ae",
    ),
    AcceptedSeal(
        "06f_targets",
        "task06f",
        "target_index_entries.jsonl",
        "1ecc7d803e5419b5ca443803e102b44d9bb6a671cfe8a875629ad20e32c3597b",
    ),
    AcceptedSeal(
        "task04_gate_d_completion",
        "task04_gate_d",
        "gate_d_completion.json",
        "d480aa903d7ae65e7a4b1b6de93ad4cdebe6963e6fd724873ade548790712826",
    ),
    AcceptedSeal(
        "task04_registry",
        "task04_gate_d",
        "usability_registry.json",
        "0453aaf13cb7762e7718ce869ee3f1521a67625224bd35c83b641cc5ae8d47e1",
    ),
    AcceptedSeal(
        "task04_exclusions",
        "task04_gate_d",
        "ambiguous_link_dispositions.json",
        "9d3b8ac7c9fea34ecada607c99b96376d648c2ab419bfa381abbf30f4b2e3366",
    ),
    AcceptedSeal(
        "task04_task03i",
        "task04_gate_d",
        "task03i_recheck_disposition.json",
        "5c8bd876b89067ce5b8ede0d2fa6a6b1b4984c74bef6978b82813df93f9514fa",
    ),
    AcceptedSeal(
        "task04_risk",
        "task04_gate_d",
        "unresolved_risk_report.json",
        "b6ac41902ffdfc6c93b13c0be93af5d071f3811334a27367fc2ccdacf2f7a5ca",
    ),
    AcceptedSeal(
        "task04_freeze",
        "task04_gate_d",
        "release_freeze.json",
        "9a018e1802ad40d65b742b0a2e954333582c80415f7d9688e9b54e7b1b04a1a3",
    ),
    AcceptedSeal(
        "task02_manifest",
        "task02",
        "source_manifest.json",
        "fede3e4af815378b77a7f7f54c863ef095328da789859d4f4b25a524f3408f38",
    ),
    AcceptedSeal(
        "task02_completion",
        "task02",
        "completion_record.json",
        "d1175d6bf54d2c557293cb7bb0e1191250a9b5db2aef5c9e563ebe01e58767a6",
    ),
    AcceptedSeal(
        "final_f1_manifest",
        "final_f1",
        "source_manifest.json",
        "99ccc11d5229bb67f591a0fbce82934d04e6d6e4ba4b8dc84eacfc59ab0ac593",
    ),
    AcceptedSeal(
        "final_f1_completion",
        "final_f1",
        "completion_record.json",
        "f29ebf55265062b157ba7248dd70a8d397321c8b57074afabbcaa4148f9a71c0",
    ),
    AcceptedSeal(
        "page28_inventory",
        "page28",
        "inventory.json",
        "004519865b858458ce1ab21410029ed2ac1aacecab3837ca5cc673a4701c2f9e",
    ),
    AcceptedSeal(
        "page28_review",
        "page28",
        "render_review.json",
        "85bb90c45d592a9d084a085f61eb872f050af16e5a73e634824f2038e7ef6a20",
    ),
)

HANDOFF_ID = "handoffv1-3603a7974be9b9dc7471dfd9a64e27468a2bdc67d44cef4944b8c24a5d60f8b9"
PAGE28_SHA256 = "5bcef150d4b81f3d86992c843c2b34dc4faced780ca7ef3272913017f29dcea7"
FINAL_F1_SHA256 = "e13c5b53f0f4da6a91f52ac784acce06619eeffd3fe053542d7ce1593b957e5e"


def verify_accepted_input_closure(roots: Mapping[str, Path]) -> dict[str, Any]:
    """Verify metadata seals while never hashing a preserved PDF or image payload."""
    missing_roots = sorted({seal.root for seal in SEALS} - roots.keys())
    if missing_roots:
        raise ValueError(f"missing Task 06H accepted roots: {', '.join(missing_roots)}")
    completion = _read_object(roots["candidate"] / "completion.json")
    references = _digest_references(completion)
    verified: list[dict[str, Any]] = []
    for seal in SEALS:
        path = roots[seal.root] / seal.path
        if seal.verification == "hash":
            if _sha256_file(path) != seal.sha256:
                raise ValueError(f"accepted input digest differs: {seal.name}")
        elif (seal.completion_path or str(path), seal.sha256) not in references:
            raise ValueError(f"accepted completion reference differs: {seal.name}")
        verified.append(asdict(seal))
    _validate_page28_records(
        _read_object(roots["page28"] / "inventory.json"),
        _read_object(roots["page28"] / "render_review.json"),
    )
    return {
        "schema_version": "er_commons.task06h.accepted_input_closure.v1",
        "mechanical_handoff_id": HANDOFF_ID,
        "verified_seals": verified,
        "preserved_pdf_payloads_hashed": False,
        "preserved_image_payloads_hashed": False,
    }


def exact_questions() -> dict[str, tuple[str, ...]]:
    """Return the complete frozen human question set without terminal answers."""
    return {
        "final_f1": (
            "Is this the selected Final edition?",
            "Do the cited pages show the named material in the named response context?",
            "Is the substituted evidence human-usable, and with what edition/revision limitation?",
            "No answer may assert general Draft/Final equivalence.",
        ),
        "appendix_a_each_group": (
            "Is there one logical chapter target?",
            "Are both physical heading blocks retained?",
            "Are children complete and ordered?",
            "Is the extent and next boundary truthful?",
            "Do both accepted spellings map to the same target without inventing a "
            "destination from TOC text?",
        ),
        "chapters_8_9_each": (
            "Is the chapter title truthful?",
            "Is the chapter represented by its own target rather than Section 8.1 or 9.1?",
            "Is the target provenance truthful?",
            "Is child closure complete?",
            "Is the chapter extent truthful?",
            "Is the transition to the next chapter truthful?",
        ),
        "fresh_navigation": (
            "Under the accepted Task 04 navigation-page policy, is the complete visible "
            "page a canonical TOC/navigation page or not_toc?",
            "Do the mapped text, tables, page placement, and surrounding context match "
            "the displayed selected-source page?",
            "Is the resulting toc or not_toc disposition supported without relying on "
            "the old namespace?",
        ),
        "sampled_reuse": (
            "Does the displayed selected-source page substantively match the sealed old "
            "evidence and still support the inherited toc/not_toc disposition under the "
            "same policy?",
        ),
        "caption_backed_figure": (
            "Does the visible figure match the exact complete marker?",
            "Is the visual evidence legible enough for human use?",
            "Does the caption/text alone state the substantive evidence required by a "
            "text-only model?",
        ),
    }


def final_f1_warnings() -> dict[str, Any]:
    """Bind general and response-specific warnings without widening equivalence."""
    return {
        "general_warning": (
            "Final EIR Appendix F1 substituted for the incorrectly selected Draft source; "
            "use with edition warning"
        ),
        "mention_count": 66,
        "response_specific": (
            {
                "response": "Response SA-Caltrans-9",
                "unit_id": (
                    "unitv1-d9083d932344bd002a2cdeb4114a81a1bebb50e40305fd93b28ad578fca1d3c7"
                ),
                "material": "Muni section revision",
                "mention_ids": (
                    "mentionv1-6bcb657e7dc49c498c2d6064db85520d7dca10af31ac395a48de46eb59cb8d84",
                ),
            },
            {
                "response": "Response SA-Caltrans-6",
                "unit_id": (
                    "unitv1-1e79142bf469b6088f841e051ab9994140342fd80048925c1b0bf9a6c8d83380"
                ),
                "material": "Table 6 revision",
                "mention_ids": (
                    "mentionv1-ac50aff61440bfad9555171a6701c1d4836d8a66c35b3ddd963342f093329cbc",
                    "mentionv1-a0735cfe682e27ceb3fa2c68c2d909f5ea60af84f4ec07c00b4ab9844b5e6e26",
                ),
            },
        ),
        "other_mentions_not_proven_draft_final_equivalent": 64,
        "named_response_location_count": 2,
        "named_mention_id_count": 3,
        "caption_alias_implies_text_only_support": False,
        "accepted_limitations": (
            "wrapper says revised Appendix F.1 / Final EIR / May 2026; underlying "
            "transportation report says Final / December 2024",
            "memo cover and continuation headers retain April 13 and April 14, 2023 respectively",
            "thumbnail exception is only objects 12649 0 and 12168 0 through physical "
            "page 28 /Thumb",
            "specialized-decoder coverage remains incomplete",
            "conversion completed with 85 Docling list-parent repairs",
            "pages 1, 6, 7, 9, 133, 135, 436, and 732 have zero reconstructed tables",
        ),
    }


def task05g_handoff() -> dict[str, Any]:
    """Return the frozen downstream contract; this record grants no execution."""
    return {
        "task05d_revision": (
            "revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030"
        ),
        "task05e_revision": (
            "revisionv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1"
        ),
        "task05f_rules": "rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83",
        "task05f_semantic_digest": (
            "8dcd3af81b10003c49ee0588bd01a5ce8f5e778f41159bdf8b3769794dbf80ac"
        ),
        "outcomes": {"total": 511, "links": 295, "explicit_nonlinks": 216},
        "required_reconciliation": {
            "draft_response_mentions": 509,
            "appendix_q_outcomes": 2,
            "f1_mentions": 66,
            "figure_mentions": 79,
            "chapter_8_9_mentions": 19,
            "appendix_a_impacts": 2,
            "collision_sets": 12,
            "comment_authored_exclusions": 11,
        },
        "only_source_free_invalidated_resolver_descendants": True,
        "specific_target_downgrade_allowed": False,
        "image_dependent_figure_is_text_only_evidence": False,
        "execution_authorized": False,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _digest_references(value: Any) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            found.add((value["path"], value["sha256"]))
        for child in value.values():
            found.update(_digest_references(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_digest_references(child))
    return found


def _validate_page28_records(inventory: dict[str, Any], review: dict[str, Any]) -> None:
    rows = [row for row in inventory.get("files", []) if row.get("name") == "page-028.png"]
    if len(rows) != 1 or rows[0].get("sha256") != PAGE28_SHA256:
        raise ValueError("accepted page-28 inventory reference differs")
    if review.get("physical_page") != 28 or review.get("render_sha256") != PAGE28_SHA256:
        raise ValueError("accepted page-28 review reference differs")


__all__ = [
    "AcceptedSeal",
    "FINAL_F1_SHA256",
    "HANDOFF_ID",
    "PAGE28_SHA256",
    "SEALS",
    "exact_questions",
    "final_f1_warnings",
    "task05g_handoff",
    "verify_accepted_input_closure",
]
