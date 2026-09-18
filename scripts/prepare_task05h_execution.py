"""Freeze a review selection and disabled execution request using accepted JSON only.

This Phase 2 planning helper writes only the three named repository metadata files.
It never executes a 05H stage or creates an external artifact directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from er_commons.response_inventory.release_inputs import load_release_inputs
from er_commons.response_inventory.release_review import build_selection, build_view_index
from er_commons.response_inventory.release_spec import (
    QUESTION_VERSION,
    SELECTION_POLICY,
    VERSION,
    VIEW_POLICY,
    ReleaseLimits,
    ReleaseSpec,
    current_runtime_versions,
    required_repository_paths,
)
from er_commons.response_inventory.release_views import estimate_review_cache_bytes

BINDINGS = "docs/specs/task05h_phase1_bindings.json"
SELECTION = "docs/specs/task05h_review_selection.json"
REQUEST = "configs/brisbane_baylands_2025_feir_task05h_review_v1.json"
PACKET = "docs/specs/task05h_execution_packet.json"


def main() -> None:
    """Prepare concrete approval material with every execution permission disabled."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    binding = json.loads((repository / BINDINGS).read_bytes())
    inputs = load_release_inputs(binding, args.data_root)
    selection = build_selection(inputs)
    (repository / SELECTION).write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n")

    def file_binding(name: str) -> dict[str, str]:
        """Bind an explicit existing repository file by bytes."""
        return {
            "path": name,
            "sha256": hashlib.sha256((repository / name).read_bytes()).hexdigest(),
        }

    request = {
        "schema_version": VERSION,
        "task_stage": "05h",
        "binding_freeze": file_binding(BINDINGS),
        "selection_freeze": file_binding(SELECTION),
        "selection_policy": SELECTION_POLICY,
        "question_version": QUESTION_VERSION,
        "view_policy": VIEW_POLICY,
        "runtime_versions": current_runtime_versions(),
        "repository_bindings": [
            file_binding(p) for p in sorted(required_repository_paths() | {BINDINGS})
        ],
        "output_relative_root": (
            "pipelines/brisbane_baylands/task_05_response_inventory/working/05h"
        ),
        "limits": ReleaseLimits().model_dump(),
        "authorization": dict.fromkeys(
            ("execution", "finalization", "publication", "acceptance"), False
        ),
        **dict.fromkeys(
            (
                "source_pdf_access",
                "image_access",
                "render_access",
                "model_access",
                "network_access",
                "hash_large_upstream_payloads",
            ),
            False,
        ),
    }
    ReleaseSpec.model_validate(request)
    request_path = repository / REQUEST
    request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n")
    from er_commons.response_inventory.release_launch import build_launch_packet

    packet = build_launch_packet(request_path, repository, args.data_root, operation="prepare")
    cache_estimate = estimate_review_cache_bytes(
        inputs, build_view_index(inputs), [row["subject_ref"] for row in selection["obligations"]]
    )
    # Allow two retained review attempts plus ample compact metadata, journals and logs.
    planning_allowance = 2 * cache_estimate + 128 * 1024 * 1024
    if (
        planning_allowance + sum(packet["prior_bytes"].values())
        > request["limits"]["max_output_bytes"]
    ):
        raise ValueError("estimated retained 05H output cannot fit the frozen cumulative limit")
    packet["output_estimate"] = {
        "review_cache_upper_bound_bytes_per_attempt": cache_estimate,
        "retained_review_attempts": 2,
        "compact_metadata_decisions_logs_allowance_bytes": 128 * 1024 * 1024,
        "total_planning_allowance_bytes": planning_allowance,
        "method": "bounded metadata and source interval lengths; no rendered review material",
        "measured_production_output": False,
        "runtime_cumulative_limit_still_enforced": True,
    }
    packet["review_operation_preview"] = build_launch_packet(
        request_path, repository, args.data_root, operation="review"
    )
    packet["phase2_review_selection"] = {
        "obligations": len(selection["obligations"]),
        "strata": len(selection["strata"]),
        "selection_digest": selection["selection_digest"],
        "input_semantic_digest": inputs.semantic_digest,
        "review_result": "not_started",
        "production_execution": "not_authorized",
    }
    (repository / PACKET).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "request": REQUEST,
                "selection": SELECTION,
                "packet": PACKET,
                "obligations": len(selection["obligations"]),
            }
        )
    )


if __name__ == "__main__":
    main()
