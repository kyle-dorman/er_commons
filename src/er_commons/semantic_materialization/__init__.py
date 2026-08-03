"""Task 03E.4 semantic canonical materialization boundaries."""

from er_commons.semantic_materialization.config import (
    SemanticMaterializationConfig,
    load_semantic_materialization_config,
)
from er_commons.semantic_materialization.identity import (
    build_semantic_candidate_identity,
    normalized_bridge_preimage_sha256,
)
from er_commons.semantic_materialization.inputs import (
    SemanticMaterializationInputs,
    load_semantic_materialization_inputs,
)
from er_commons.semantic_materialization.workflow import run_semantic_materialization

__all__ = [
    "SemanticMaterializationConfig",
    "SemanticMaterializationInputs",
    "build_semantic_candidate_identity",
    "load_semantic_materialization_config",
    "load_semantic_materialization_inputs",
    "normalized_bridge_preimage_sha256",
    "run_semantic_materialization",
]
