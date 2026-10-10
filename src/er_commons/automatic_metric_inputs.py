"""Resolve automatic metric inputs using frozen source identities, never display text.

Callers verify source seals before building a catalog. Retrieval anchor inventories and
search mappings are Task 10 inputs; this module checks their explicit delivery claims.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

CanonicalUnit = tuple[str, str, str, str]


@dataclass(frozen=True)
class SourceCatalog:
    """Verified occurrence/alias lookup; missing infrastructure is not an invalid ID."""

    mappings: dict[str, frozenset[CanonicalUnit]]
    unavailable: frozenset[str] = frozenset()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class CitationResolution:
    """Canonical final links plus lossless raw attempts and separate availability."""

    units: frozenset[CanonicalUnit]
    invalid_tokens: frozenset[str]
    attempts: tuple[dict[str, Any], ...] = ()
    diagnostics: tuple[str, ...] = ()
    available: bool = True


@dataclass(frozen=True)
class ReferenceResolution:
    """Disjoint reviewed role sets; support wins over context on the same unit."""

    support: frozenset[CanonicalUnit]
    context: frozenset[CanonicalUnit]
    available: bool = True
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResolution:
    """Actual delivery and separate anchor-complete ranked diagnostic candidates."""

    units: frozenset[CanonicalUnit]
    available: bool
    diagnostics: tuple[str, ...] = ()
    receipt: dict[str, Any] | None = None
    ranked_units: tuple[tuple[int, CanonicalUnit], ...] = ()
    unit_budget: int | None = None
    ranked_depth: int = 0
    ranking_exhausted: bool = False


def canonical_unit(value: Any) -> CanonicalUnit:
    """Validate an existing extraction identity without assigning new identifiers."""
    if (
        not isinstance(value, (tuple, list))
        or len(value) != 4
        or any(not isinstance(part, str) or not part for part in value)
        or value[2] not in {"section", "table"}
    ):
        raise ValueError("Expected source/extraction/section-or-table/unit identity")
    return value[0], value[1], value[2], value[3]


def source_unit(source: Mapping[str, Any]) -> CanonicalUnit:
    """Read 09A/09C locators and cross-check their source document namespace."""
    target = source.get("canonical_target")
    if not isinstance(target, dict):
        raise ValueError("Missing canonical source locator")
    if "unit_type" in target and "kind" in target and target["unit_type"] != target["kind"]:
        raise ValueError("Conflicting canonical unit_type and kind")
    unit = canonical_unit(
        (
            source.get("source_id"),
            source.get("extraction_id"),
            target.get("unit_type", target.get("kind")),
            target.get("unit_id"),
        )
    )
    if target.get("document_id", f"{unit[1]}/document/{unit[0]}") != (
        f"{unit[1]}/document/{unit[0]}"
    ):
        raise ValueError("Canonical document/source/extraction mismatch")
    return unit


def build_catalog(
    sources: Iterable[Mapping[str, Any]],
    verified_aliases: Mapping[str, str] | None = None,
) -> SourceCatalog:
    """Index verified locators; aliases target original occurrences, never other aliases."""
    mappings: dict[str, set[CanonicalUnit]] = {}
    unavailable: set[str] = set()
    diagnostics = []
    for source in sources:
        raw = source.get("occurrence_id")
        if not isinstance(raw, str) or not raw:
            raise ValueError("Source occurrence ID missing")
        mappings.setdefault(raw, set())
        try:
            mappings[raw].add(source_unit(source))
        except ValueError as error:
            unavailable.add(raw)
            diagnostics.append(f"{raw}: {error}")
    original = {raw: frozenset(units) for raw, units in mappings.items()}
    original_unavailable = frozenset(unavailable)
    for alias, raw in (verified_aliases or {}).items():
        if not isinstance(alias, str) or not alias or raw not in original:
            raise ValueError("Alias requires a verified occurrence target")
        if alias in original and (
            original[alias] != original[raw]
            or (alias in original_unavailable) != (raw in original_unavailable)
        ):
            raise ValueError("Alias conflicts with an existing occurrence")
        mappings[alias] = set(original[raw])
        if raw in original_unavailable:
            unavailable.add(alias)
    return SourceCatalog(
        {raw: frozenset(units) for raw, units in mappings.items()},
        frozenset(unavailable),
        tuple(diagnostics),
    )


def _raw_token(value: Any) -> str:
    """Keep string IDs verbatim and type-tag malformed JSON attempts for deduplication."""
    if isinstance(value, str):
        return "str:" + value
    return "json:" + json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _answer_attempts(answer: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Preserve malformed citation fields without inventing links from prose or locators."""
    attempts: list[dict[str, Any]] = []
    diagnostics: list[str] = []
    if not isinstance(answer, dict):
        return [
            {
                "path": "answer",
                "raw": answer,
                "token": _raw_token(answer),
                "malformed": True,
                "unextractable": True,
            }
        ], ["malformed_answer: expected object"]
    rows: list[tuple[str, Any]] = [("conclusion", answer.get("conclusion"))]
    for key in ("supporting_points", "qualifications", "optional_context"):
        group = answer.get(key, [])
        if not isinstance(group, list):
            diagnostics.append(f"malformed_answer: {key} must be an array")
            group = [group]
        rows.extend((f"{key}/{index}", row) for index, row in enumerate(group))
    for path, row in rows:
        if not isinstance(row, dict):
            diagnostics.append(f"malformed_answer: {path} must be a point")
            attempts.append(
                {
                    "path": path,
                    "raw": row,
                    "token": _raw_token(row),
                    "malformed": True,
                    "unextractable": True,
                }
            )
            continue
        if "citation_ids" not in row:
            diagnostics.append(f"malformed_answer: {path} missing citation_ids")
            attempts.append(
                {
                    "path": path,
                    "raw": row,
                    "token": _raw_token(row),
                    "malformed": True,
                    "unextractable": True,
                }
            )
            continue
        values = row["citation_ids"]
        malformed = not isinstance(values, list)
        if malformed:
            diagnostics.append(f"malformed_answer: {path}/citation_ids must be an array")
            values = [values]
        for value in values:
            attempts.append(
                {
                    "path": path,
                    "point_id": row.get("point_id"),
                    "raw": value,
                    "token": _raw_token(value),
                    "malformed": malformed or not isinstance(value, str) or not value,
                }
            )
    return attempts, diagnostics


def resolve_citations(
    answer: Any,
    catalog: SourceCatalog,
    packet_mapping: Mapping[str, str] | None = None,
    *,
    packet_local: bool = False,
) -> CitationResolution:
    """Resolve actual links; a 09C raw-to-local mapping belongs to this packet only."""
    attempts, diagnostics = _answer_attempts(answer)
    if packet_local and packet_mapping is None:
        for attempt in attempts:
            attempt["status"] = "unavailable"
        return CitationResolution(
            frozenset(),
            frozenset(),
            tuple(attempts),
            (*diagnostics, "missing_packet_local_mapping"),
            False,
        )
    units: set[CanonicalUnit] = set()
    invalid: set[str] = set()
    available = True
    reverse: dict[str, set[str]] = {}
    for raw, local in (packet_mapping or {}).items():
        reverse.setdefault(local, set()).add(raw)
    for attempt in attempts:
        raw = attempt["raw"]
        candidates = (
            reverse.get(raw, set())
            if packet_mapping is not None and isinstance(raw, str)
            else {raw}
            if isinstance(raw, str)
            else set()
        )
        if attempt.get("unextractable"):
            status = "unavailable"
            available = False
        elif attempt["malformed"]:
            status = "invalid"
        elif any(
            candidate in catalog.unavailable
            or (packet_mapping is not None and candidate not in catalog.mappings)
            for candidate in candidates
        ):
            status = "unavailable"
            available = False
        else:
            resolved = set().union(*(catalog.mappings.get(c, frozenset()) for c in candidates))
            # An unknown raw member of a packet mapping cannot be silently discarded.
            unknown = any(c not in catalog.mappings for c in candidates)
            if len(resolved) == 1 and not unknown:
                units.update(resolved)
                status = "resolved"
            else:
                status = "ambiguous" if len(resolved) > 1 else "invalid"
        attempt["status"] = status
        if status in {"invalid", "ambiguous"}:
            invalid.add(attempt["token"])
        if status != "resolved":
            diagnostics.append(f"{status}_citation: {attempt['token']}")
    return CitationResolution(
        frozenset(units), frozenset(invalid), tuple(attempts), tuple(diagnostics), available
    )


def resolve_references(
    sources: Iterable[Mapping[str, Any]],
    catalog: SourceCatalog,
) -> ReferenceResolution:
    """Read approved released roles, with support precedence and no inferred approval."""
    support: set[CanonicalUnit] = set()
    context: set[CanonicalUnit] = set()
    diagnostics = []
    for source in sources:
        roles = source.get("approved_roles", [])
        if not isinstance(roles, list) or any(not isinstance(role, str) for role in roles):
            diagnostics.append("malformed approved reference roles")
            continue
        if set(roles) - {"required", "required_support", "optional_context"}:
            diagnostics.append(f"unknown approved reference roles: {roles}")
            continue
        is_support = bool(set(roles) & {"required", "required_support"})
        is_context = bool(set(roles) & {"optional_context"})
        if not is_support and not is_context:
            continue
        raw = source.get("occurrence_id")
        if not isinstance(raw, str):
            diagnostics.append("missing reference occurrence ID")
            continue
        matches = catalog.mappings.get(raw, frozenset())
        if raw in catalog.unavailable or len(matches) != 1:
            diagnostics.append(f"unavailable reference identity: {raw}")
        else:
            (support if is_support else context).update(matches)
    return ReferenceResolution(
        frozenset(support), frozenset(context - support), not diagnostics, tuple(diagnostics)
    )


def _anchor_ids(value: Any) -> set[str]:
    """Require an explicit list of canonical anchor IDs, never text-based overlap."""
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        raise ValueError("Missing or malformed anchor IDs")
    return set(value)


def resolve_receipt(receipt: dict[str, Any] | None, catalog: SourceCatalog) -> RetrievalResolution:
    """Check Task 10 mappings and anchor coverage, separating ranked from delivered units.

    Required anchors must describe complete canonical units, verified by the caller.
    Ranked diagnostics use each hit's ``anchor_ids``; actual credit uses only
    ``delivered_anchor_ids`` from delivered hits within the declared unit budget.
    """
    if receipt is None:
        return RetrievalResolution(frozenset(), False, ("missing_retrieval_receipt",))
    try:
        return _resolve_receipt(receipt, catalog)
    except (KeyError, TypeError, ValueError) as error:
        return RetrievalResolution(
            frozenset(), False, (f"invalid_retrieval_receipt: {error}",), receipt
        )


def _receipt_budget(receipt: dict[str, Any]) -> int:
    """Require a versioned receipt with explicit condition, provenance and budget."""
    if not isinstance(receipt, dict):
        raise ValueError("Retrieval receipt must be an object")
    if receipt.get("schema_version") != "task09d.retrieval_receipt.v1":
        raise ValueError("Unsupported retrieval receipt schema")
    budget = receipt["unit_budget"]
    if type(budget) is not int or budget < 1:
        raise ValueError("Positive integer unit budget required")
    if (
        any(
            not isinstance(receipt.get(field), str) or not receipt[field].strip()
            for field in ("condition", "provenance")
        )
        or type(receipt.get("invented")) is not bool
    ):
        raise ValueError("Condition, provenance and invented flag required")
    return budget


def _receipt_rows(value: Any, field: str) -> list[dict[str, Any]]:
    """Reject malformed receipt containers before interpreting row fields."""
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{field} must be an array of objects")
    return value


def _receipt_inventory(
    receipt: dict[str, Any], catalog: SourceCatalog
) -> tuple[dict[CanonicalUnit, set[str]], dict[str, CanonicalUnit]]:
    """Check complete anchor inventories and every declared search-record mapping."""
    known = set().union(*catalog.mappings.values())
    required: dict[CanonicalUnit, set[str]] = {}
    for row in _receipt_rows(receipt["required_anchor_ids"], "required_anchor_ids"):
        unit = canonical_unit(row["canonical_unit"])
        anchors = _anchor_ids(row["anchor_ids"])
        if unit in required or unit not in known or not anchors:
            raise ValueError("Ambiguous, unknown or empty required-unit anchor inventory")
        required[unit] = anchors
    mappings: dict[str, CanonicalUnit] = {}
    for row in _receipt_rows(receipt.get("search_record_mapping", []), "search_record_mapping"):
        identity = row["search_record_id"]
        if not isinstance(identity, str) or not identity or identity in mappings:
            raise ValueError("Ambiguous search-record mapping")
        unit = canonical_unit(row["canonical_unit"])
        if unit not in known:
            raise ValueError("Unknown canonical unit in search-record mapping")
        mappings[identity] = unit
    return required, mappings


def _ranked_hits(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate rank types and uniqueness before sorting the recorded hit rows."""
    hits = _receipt_rows(receipt["hits"], "hits")
    ranks: set[int] = set()
    for hit in hits:
        rank = hit["rank"]
        if type(rank) is not int or rank < 1 or rank in ranks:
            raise ValueError("Ranks must be positive and unique")
        ranks.add(rank)
    return sorted(hits, key=lambda hit: hit["rank"])


def _ranking_observation(
    receipt: dict[str, Any], hits: list[dict[str, Any]]
) -> tuple[bool, int, bool]:
    """Require an observed contiguous prefix without allocating by claimed depth."""
    depth = receipt.get("ranked_depth", 0)
    exhausted = receipt.get("ranking_exhausted", False)
    if type(depth) is not int or depth < 0 or type(exhausted) is not bool:
        raise ValueError("Invalid ranking observation metadata")
    diagnostic_available = (
        "ranked_depth" in receipt
        and "ranking_exhausted" in receipt
        and depth == len(hits)
        and all(hit["rank"] == rank for rank, hit in enumerate(hits, start=1))
        and all("anchor_ids" in hit for hit in hits)
    )
    return (True, depth, exhausted) if diagnostic_available else (False, 0, False)


def _resolve_receipt(receipt: dict[str, Any], catalog: SourceCatalog) -> RetrievalResolution:
    """Project validated ranked and delivered anchors into complete canonical units."""
    budget = _receipt_budget(receipt)
    required, mappings = _receipt_inventory(receipt, catalog)
    hits = _ranked_hits(receipt)
    diagnostic_available, depth, exhausted = _ranking_observation(receipt, hits)
    diagnostics = [] if diagnostic_available else ["ranked_diagnostics_unavailable"]
    delivered: dict[CanonicalUnit, set[str]] = {}
    ranked: dict[CanonicalUnit, set[str]] = {}
    completed: dict[CanonicalUnit, int] = {}
    for hit in hits:
        rank = hit["rank"]
        unit = canonical_unit(hit["canonical_unit"])
        if unit not in required:
            raise ValueError("Missing complete canonical anchor inventory")
        search = hit.get("search_record_id")
        if search is not None and mappings.get(search) != unit:
            raise ValueError("Search-record ID lacks exact canonical mapping")
        if type(hit["delivered"]) is not bool:
            raise ValueError("Delivered flag must be boolean")
        actual = _anchor_ids(hit["delivered_anchor_ids"])
        candidate = _anchor_ids(hit.get("anchor_ids", []))
        if not actual <= required[unit] or not candidate <= required[unit]:
            raise ValueError("Unknown anchors for canonical unit")
        ranked.setdefault(unit, set()).update(candidate)
        if required[unit] <= ranked[unit]:
            completed.setdefault(unit, rank)
        if hit["delivered"] and rank <= budget:
            delivered.setdefault(unit, set()).update(actual)
        elif actual:
            raise ValueError("Undelivered or out-of-budget hit claims delivered anchors")
    units = frozenset(unit for unit, anchors in delivered.items() if required[unit] <= anchors)
    for unit in sorted(delivered.keys() - units):
        diagnostics.append(f"incomplete_delivered_unit: {unit}")
    return RetrievalResolution(
        units,
        True,
        tuple(diagnostics),
        receipt,
        tuple(sorted((rank, unit) for unit, rank in completed.items()))
        if diagnostic_available
        else (),
        budget,
        depth,
        exhausted,
    )
