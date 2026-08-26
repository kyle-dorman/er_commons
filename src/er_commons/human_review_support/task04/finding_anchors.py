"""Typed evidence anchors derived from immutable Task 04 selection records."""

from __future__ import annotations

import math

from er_commons.human_review_support.task04.anchor_models import (
    CanonicalBlockAnchor,
    CanonicalTableAnchor,
    FailureAnchor,
    FindingAnchor,
    FindingSelectors,
    ObservationAnchor,
    PageAnchor,
    SourceAnchor,
    TableFamilyAnchor,
    WarningAnchor,
)
from er_commons.human_review_support.task04.json_io import (
    optional_string,
    require_integer,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonValue


def derive_evidence_anchors(
    item: dict[str, JsonValue],
    inventory_source: dict[str, JsonValue],
    *,
    item_path: str,
    source_path: str,
    selectors: FindingSelectors | None = None,
) -> tuple[FindingAnchor, ...]:
    """Derive the only valid anchors for one selected item and source inventory row."""
    binding = _source_anchor(item, inventory_source, item_path=item_path, source_path=source_path)
    queue = require_string(item.get("queue"), path=f"{item_path}.queue")
    pages = _physical_pages(item.get("physical_pages"), path=f"{item_path}.physical_pages")
    anchors: list[FindingAnchor]
    if queue == "valid_page":
        if not pages:
            raise ValueError(f"valid-page anchor requires pages at {item_path}.physical_pages")
        anchors = [PageAnchor(binding, page) for page in pages]
    elif queue == "table":
        family = require_string(item.get("table_family_id"), path=f"{item_path}.table_family_id")
        anchors = [TableFamilyAnchor(binding, family, pages)]
    elif queue == "warning":
        warning = require_mapping(item.get("warning"), path=f"{item_path}.warning")
        fingerprint = require_string(
            warning.get("fingerprint"), path=f"{item_path}.warning.fingerprint"
        )
        anchors = [WarningAnchor(binding, fingerprint, pages[0] if pages else None)]
    elif queue == "failure":
        failure = require_mapping(item.get("failure"), path=f"{item_path}.failure")
        attempts = require_list(failure.get("attempts"), path=f"{item_path}.failure.attempts")
        attempt_ids = tuple(
            require_string(
                require_mapping(value, path=f"{item_path}.failure.attempts[{index}]").get(
                    "attempt_id"
                ),
                path=f"{item_path}.failure.attempts[{index}].attempt_id",
            )
            for index, value in enumerate(attempts)
        )
        anchors = [FailureAnchor(binding, attempt_ids)]
    else:
        raise ValueError(f"unsupported review queue at {item_path}.queue: {queue!r}")
    anchors.extend(
        _selected_exact_anchors(
            item,
            binding,
            selectors or FindingSelectors(),
            queue=queue,
            selected_pages=pages,
            item_path=item_path,
        )
    )
    return tuple(anchors)


def _selected_exact_anchors(
    item: dict[str, JsonValue],
    binding: SourceAnchor,
    selectors: FindingSelectors,
    *,
    queue: str,
    selected_pages: tuple[int, ...],
    item_path: str,
) -> tuple[FindingAnchor, ...]:
    """Resolve explicit canonical-object selectors against retained exact evidence."""
    requested = selectors.normalized()
    evidence_path = f"{item_path}.exact_evidence"
    evidence = require_mapping(item.get("exact_evidence"), path=evidence_path)
    object_rows = require_list(
        evidence.get("canonical_objects"), path=f"{evidence_path}.canonical_objects"
    )
    observation_rows = require_list(
        evidence.get("observations"), path=f"{evidence_path}.observations"
    )
    anchors: list[FindingAnchor] = []
    anchors.extend(
        _canonical_selector_anchors(
            object_rows,
            binding,
            requested,
            selected_pages=selected_pages,
            selected_family=optional_string(
                item.get("table_family_id"), path=f"{item_path}.table_family_id"
            ),
            path=f"{evidence_path}.canonical_objects",
        )
    )
    anchors.extend(
        _observation_selector_anchors(
            observation_rows,
            binding,
            requested,
            queue=queue,
            path=f"{evidence_path}.observations",
        )
    )
    return tuple(anchors)


def _canonical_selector_anchors(
    rows: list[JsonValue],
    binding: SourceAnchor,
    selectors: FindingSelectors,
    *,
    selected_pages: tuple[int, ...],
    selected_family: str | None,
    path: str,
) -> tuple[FindingAnchor, ...]:
    requested = {
        "canonical_table": set(selectors.table_ids),
        "canonical_block": set(selectors.block_ids),
    }
    found: dict[str, set[str]] = {kind: set() for kind in requested}
    anchors: list[FindingAnchor] = []
    for index, value in enumerate(rows):
        row_path = f"{path}[{index}]"
        row = require_mapping(value, path=row_path)
        kind = require_string(row.get("kind"), path=f"{row_path}.kind")
        object_id = require_string(row.get("object_id"), path=f"{row_path}.object_id")
        if kind not in requested or object_id not in requested[kind]:
            continue
        found[kind].add(object_id)
        physical_page = require_integer(
            row.get("physical_page"), path=f"{row_path}.physical_page", minimum=1
        )
        coordinate_space = require_string(
            row.get("coordinate_space"), path=f"{row_path}.coordinate_space"
        )
        if coordinate_space != "displayed_page":
            raise ValueError(
                f"unsupported canonical bbox coordinates at {row_path}.coordinate_space: "
                f"{coordinate_space!r}"
            )
        if physical_page not in selected_pages:
            raise ValueError(
                f"canonical selector resolves outside selected pages at {row_path}.physical_page: "
                f"{physical_page} not in {list(selected_pages)}"
            )
        bbox = _bbox(row.get("bbox"), path=f"{row_path}.bbox")
        if kind == "canonical_table":
            table_family = optional_string(
                row.get("table_family_id"), path=f"{row_path}.table_family_id"
            )
            if selected_family is not None and table_family != selected_family:
                raise ValueError(
                    f"canonical table selector has wrong family at {row_path}.table_family_id: "
                    f"selected={selected_family!r}, object={table_family!r}"
                )
            anchors.append(
                CanonicalTableAnchor(
                    binding,
                    object_id,
                    physical_page,
                    bbox,
                    table_family,
                )
            )
        else:
            anchors.append(CanonicalBlockAnchor(binding, object_id, physical_page, bbox))
    _require_all_selectors(requested, found, path=path)
    return tuple(anchors)


def _observation_selector_anchors(
    rows: list[JsonValue],
    binding: SourceAnchor,
    selectors: FindingSelectors,
    *,
    queue: str,
    path: str,
) -> tuple[FindingAnchor, ...]:
    requested = set(selectors.observation_ids)
    found: set[str] = set()
    anchors: list[FindingAnchor] = []
    for index, value in enumerate(rows):
        row_path = f"{path}[{index}]"
        row = require_mapping(value, path=row_path)
        observation_id = require_string(
            row.get("observation_id"), path=f"{row_path}.observation_id"
        )
        if observation_id not in requested:
            continue
        found.add(observation_id)
        observation_kind = require_string(row.get("kind"), path=f"{row_path}.kind")
        expected_kind = {
            "warning": "warning_observation",
            "failure": "failure_observation",
        }.get(queue)
        if expected_kind is None or observation_kind != expected_kind:
            raise ValueError(
                f"observation selector kind does not match review queue at {row_path}.kind: "
                f"queue={queue!r}, kind={observation_kind!r}"
            )
        anchors.append(
            ObservationAnchor(
                binding,
                observation_kind,
                observation_id,
            )
        )
    missing = requested - found
    if missing:
        raise ValueError(f"unknown or stale observation selectors at {path}: {sorted(missing)!r}")
    return tuple(anchors)


def _require_all_selectors(
    requested: dict[str, set[str]], found: dict[str, set[str]], *, path: str
) -> None:
    for kind, identifiers in requested.items():
        missing = identifiers - found[kind]
        if missing:
            label = "table" if kind == "canonical_table" else "block"
            raise ValueError(
                f"unknown or stale canonical {label} selectors at {path}: {sorted(missing)!r}"
            )


def _bbox(value: JsonValue, *, path: str) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    values = require_list(value, path=path)
    if len(values) != 4 or any(
        not isinstance(number, int | float) or isinstance(number, bool) for number in values
    ):
        raise ValueError(f"expected four-number bbox or null at {path}")
    numbers: list[float] = []
    for number in values:
        if not isinstance(number, int | float) or isinstance(number, bool):
            raise ValueError(f"expected four-number bbox or null at {path}")
        numbers.append(float(number))
    bbox = (numbers[0], numbers[1], numbers[2], numbers[3])
    if not all(math.isfinite(number) for number in bbox) or not (
        bbox[0] <= bbox[2] and bbox[1] <= bbox[3]
    ):
        raise ValueError(f"expected finite ordered bbox at {path}")
    return bbox


def _source_anchor(
    item: dict[str, JsonValue],
    source: dict[str, JsonValue],
    *,
    item_path: str,
    source_path: str,
) -> SourceAnchor:
    item_source = require_string(item.get("source_id"), path=f"{item_path}.source_id")
    inventory_source = require_string(source.get("source_id"), path=f"{source_path}.source_id")
    if item_source != inventory_source:
        raise ValueError(
            f"selection/inventory source mismatch at {item_path}.source_id: "
            f"selection={item_source}, inventory={inventory_source}"
        )
    item_candidate = optional_string(item.get("candidate_id"), path=f"{item_path}.candidate_id")
    inventory_candidate = optional_string(
        source.get("selected_candidate_id"), path=f"{source_path}.selected_candidate_id"
    )
    if item_candidate != inventory_candidate:
        raise ValueError(
            f"selection/inventory candidate mismatch at {item_path}.candidate_id: "
            f"selection={item_candidate}, inventory={inventory_candidate}"
        )
    completion = optional_string(
        source.get("selected_completion_sha256"),
        path=f"{source_path}.selected_completion_sha256",
    )
    inventory = optional_string(
        source.get("selected_inventory_sha256"),
        path=f"{source_path}.selected_inventory_sha256",
    )
    if item_candidate is not None and (completion is None or inventory is None):
        raise ValueError(f"selected candidate lacks terminal checksums at {source_path}")
    return SourceAnchor(
        source_id=item_source,
        catalog_sha256=require_string(source.get("sha256"), path=f"{source_path}.sha256"),
        source_pdf_sha256=optional_string(
            source.get("source_pdf_sha256"), path=f"{source_path}.source_pdf_sha256"
        ),
        candidate_id=item_candidate,
        candidate_completion_sha256=completion,
        candidate_inventory_sha256=inventory,
    )


def _physical_pages(value: JsonValue, *, path: str) -> tuple[int, ...]:
    """Read sorted unique selected pages from a validated selection item."""
    pages = tuple(
        require_integer(page, path=f"{path}[{index}]", minimum=1)
        for index, page in enumerate(require_list(value, path=path))
    )
    if pages != tuple(sorted(set(pages))):
        raise ValueError(f"expected sorted unique physical pages at {path}")
    return pages


def anchor_records(anchors: tuple[FindingAnchor, ...]) -> list[JsonValue]:
    """Serialize typed anchors for finding identity and persisted records."""
    return [anchor.to_record() for anchor in anchors]


def selectors_from_anchor_records(records: list[JsonValue], *, path: str) -> FindingSelectors:
    """Recover exact selectors so persisted anchors can be re-resolved and checked."""
    table_ids: list[str] = []
    block_ids: list[str] = []
    observation_ids: list[str] = []
    for index, value in enumerate(records):
        row_path = f"{path}[{index}]"
        row = require_mapping(value, path=row_path)
        kind = require_string(row.get("kind"), path=f"{row_path}.kind")
        if kind == "canonical_table":
            table_ids.append(require_string(row.get("table_id"), path=f"{row_path}.table_id"))
        elif kind == "canonical_block":
            block_ids.append(require_string(row.get("block_id"), path=f"{row_path}.block_id"))
        elif kind == "observation":
            observation_ids.append(
                require_string(row.get("observation_id"), path=f"{row_path}.observation_id")
            )
    return FindingSelectors(tuple(table_ids), tuple(block_ids), tuple(observation_ids)).normalized()


__all__ = [
    "FailureAnchor",
    "FindingAnchor",
    "FindingSelectors",
    "CanonicalBlockAnchor",
    "CanonicalTableAnchor",
    "ObservationAnchor",
    "PageAnchor",
    "SourceAnchor",
    "TableFamilyAnchor",
    "WarningAnchor",
    "anchor_records",
    "derive_evidence_anchors",
    "selectors_from_anchor_records",
]
