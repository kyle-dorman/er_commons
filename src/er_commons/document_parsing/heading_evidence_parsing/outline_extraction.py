"""Traverse embedded PDF outlines into deterministic hierarchy observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_cleanup import (
    clean_malformed_outline_tree,
    omit_transparent_filename_container,
    requires_technical_outline_cleanup,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_diagnostics import (
    missing_leaf_diagnostic,
    parentless_child_list_error,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_normalization import (
    normalize_malformed_filename_destinations,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_recovery import (
    RecoveryContext,
    recover_appendix_container,
    recover_visible_title_container,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_types import (
    JsonObject,
    OutlineExtraction,
    RawReferenceKey,
)
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem


@dataclass
class _OutlineWalker:
    """Stateful depth-first traversal of one validated pypdf outline forest."""

    reader: Any
    malformed_filename_containers: frozenset[RawReferenceKey]
    heading_features: list[ObservedItem]
    observations: list[JsonObject] = field(default_factory=list)
    diagnostics: list[JsonObject] = field(default_factory=list)

    def walk(self, nodes: list[Any], parent_id: str | None, depth: int, root_depth: int) -> None:
        previous_id: str | None = None
        pending_invalid: tuple[Any, str] | None = None
        for node in nodes:
            if isinstance(node, list):
                previous_id, pending_invalid = self._walk_children(
                    node,
                    previous_id=previous_id,
                    pending_invalid=pending_invalid,
                    parent_id=parent_id,
                    depth=depth,
                    root_depth=root_depth,
                )
                continue
            if pending_invalid is not None:
                self.diagnostics.append(missing_leaf_diagnostic(pending_invalid[1]))
            pending_invalid = None
            title = self._validated_title(node)
            page_index = self._destination_page_index(node)
            if page_index is None:
                pending_invalid = (node, title)
                previous_id = None
                continue
            previous_id = self._append_observation(
                title=title,
                physical_page=page_index + 1,
                parent_id=parent_id,
                depth=depth,
                root_depth=root_depth,
            )
        if pending_invalid is not None:
            self.diagnostics.append(missing_leaf_diagnostic(pending_invalid[1]))

    def _walk_children(
        self,
        children: list[Any],
        *,
        previous_id: str | None,
        pending_invalid: tuple[Any, str] | None,
        parent_id: str | None,
        depth: int,
        root_depth: int,
    ) -> tuple[str | None, tuple[Any, str] | None]:
        if previous_id is None:
            if pending_invalid is None:
                raise parentless_child_list_error(
                    stage="outline_walk",
                    reason="child list has no valid or destinationless preceding bookmark",
                    children=children,
                    depth=depth,
                    parent_id=parent_id,
                )
            if self._omit_transparent(pending_invalid, children):
                self.walk(children, parent_id, depth, root_depth)
                return None, None
            previous_id = self._recover_container(
                pending_invalid,
                children,
                parent_id=parent_id,
                depth=depth,
                root_depth=root_depth,
            )
            if previous_id is None:
                raise parentless_child_list_error(
                    stage="outline_recovery",
                    reason=(
                        "destinationless bookmark failed duplicate cleanup, transparent "
                        "filename omission, appendix recovery, and visible-title recovery"
                    ),
                    children=children,
                    title=pending_invalid[1],
                    depth=depth,
                    parent_id=parent_id,
                )
            pending_invalid = None
        self.walk(children, previous_id, depth + 1, root_depth)
        return previous_id, pending_invalid

    def _omit_transparent(self, pending_invalid: tuple[Any, str], children: list[Any]) -> bool:
        node, title = pending_invalid
        return omit_transparent_filename_container(
            reader=self.reader,
            node=node,
            title=title,
            children=children,
            malformed_filename_containers=self.malformed_filename_containers,
            diagnostics=self.diagnostics,
        )

    def _recover_container(
        self,
        pending_invalid: tuple[Any, str],
        children: list[Any],
        *,
        parent_id: str | None,
        depth: int,
        root_depth: int,
    ) -> str | None:
        _node, title = pending_invalid
        context = RecoveryContext(
            parent_id=parent_id,
            depth=depth,
            root_depth=root_depth,
            heading_features=self.heading_features,
            observations=self.observations,
            diagnostics=self.diagnostics,
        )
        recovered = recover_appendix_container(
            reader=self.reader, title=title, children=children, context=context
        )
        return recovered or recover_visible_title_container(
            reader=self.reader, title=title, children=children, context=context
        )

    def _validated_title(self, node: Any) -> str:
        title = getattr(node, "title", None)
        if not isinstance(title, str) or not normalize_text(title):
            raise HierarchyInferenceContractError("outline title is invalid")
        return title

    def _destination_page_index(self, node: Any) -> int | None:
        try:
            page_index = self.reader.get_destination_page_number(node)
        except Exception as error:
            raise HierarchyInferenceContractError("outline destination is malformed") from error
        return (
            page_index
            if isinstance(page_index, int) and 0 <= page_index < len(self.reader.pages)
            else None
        )

    def _append_observation(
        self,
        *,
        title: str,
        physical_page: int,
        parent_id: str | None,
        depth: int,
        root_depth: int,
    ) -> str:
        outline_id = f"outline-{len(self.observations):08d}"
        self.observations.append(
            {
                "outline_id": outline_id,
                "parent_outline_id": parent_id,
                "title": title,
                "normalized_title": normalize_text(title),
                "physical_page": physical_page,
                "raw_depth": depth,
                "source_root_depth": root_depth,
                "effective_level": min(6, depth - root_depth + 1),
            }
        )
        return outline_id


def extract_outline_observations(
    reader: Any, *, heading_features: list[ObservedItem] | None = None
) -> OutlineExtraction:
    """Flatten outline nodes and recover strictly evidenced appendix containers."""
    malformed_containers = normalize_malformed_filename_destinations(reader)
    outline = _read_outline(reader)
    if not outline:
        return OutlineExtraction((), ())
    features = heading_features or []
    cleanup_diagnostics: list[JsonObject] = []
    if malformed_containers or requires_technical_outline_cleanup(
        reader, outline, malformed_filename_containers=malformed_containers
    ):
        outline, cleanup_diagnostics = clean_malformed_outline_tree(
            reader=reader,
            outline=outline,
            malformed_filename_containers=malformed_containers,
            heading_features=features,
        )
    walker = _OutlineWalker(
        reader=reader,
        malformed_filename_containers=malformed_containers,
        heading_features=features,
        diagnostics=cleanup_diagnostics,
    )
    walker.walk(outline, None, 1, 1)
    return OutlineExtraction(tuple(walker.observations), tuple(walker.diagnostics))


def _read_outline(reader: Any) -> list[Any]:
    try:
        outline = reader.outline
    except Exception as error:  # pragma: no cover - pypdf exception types vary by defect
        raise HierarchyInferenceContractError("source PDF outline is malformed") from error
    if not outline:
        return []
    if not isinstance(outline, list):
        raise HierarchyInferenceContractError("source PDF outline is invalid")
    return outline
