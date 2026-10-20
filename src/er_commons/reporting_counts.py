"""Pure citation-occurrence and canonical response-unit counts from saved records."""

from __future__ import annotations

from typing import Any

# Public per-answer columns also let normalized saved reports render without raw attempts.
COUNT_FIELDS = (
    "response_units",
    "sections",
    "tables",
    "figure_captions",
    "documents",
    "input_response_units",
    "input_sections",
    "input_tables",
    "input_figure_captions",
    "input_documents",
    "citation_occurrences",
    "resolved_citation_occurrences",
    "unresolved_citation_occurrences",
    "invalid_citation_occurrences",
    "ambiguous_citation_occurrences",
    "unavailable_citation_occurrences",
    "citation_occurrence_status",
    "unextractable_citation_fields",
    "observed_citation_occurrences",
    "observed_resolved_citation_occurrences",
    "canonical_units",
    "input_canonical_units",
    "input_citations",
    "invalid_ids",
    "invalid_id_count",
)


def response_unit_counts(
    canonical_units: list[Any],
    input_canonical_units: list[Any],
    citation_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Separate citation uses from distinct canonical response units without parent inference."""
    units = {tuple(unit) for unit in canonical_units}
    supplied = {tuple(unit) for unit in input_canonical_units}
    invalid = sorted({a["token"] for a in citation_attempts if a["status"] == "invalid"})

    def counts(values: set[tuple[Any, ...]]) -> dict[str, Any]:
        """Count tables independently of sections; preserve every existing unit identity."""
        return {
            "response_units": len(values),
            "sections": sum(unit[2] == "section" for unit in values),
            "tables": sum(unit[2] == "table" for unit in values),
            "figure_captions": sum(unit[2] == "figure_caption" for unit in values),
            "documents": len({unit[0] for unit in values}),
        }

    attempts = [a for a in citation_attempts if not a.get("unextractable")]
    unextractable = len(citation_attempts) - len(attempts)
    resolved = sum(a["status"] == "resolved" for a in attempts)
    occurrence_counts = {
        "citation_occurrences": len(attempts),
        "resolved_citation_occurrences": resolved,
        "unresolved_citation_occurrences": len(attempts) - resolved,
        **{
            f"{status}_citation_occurrences": sum(a["status"] == status for a in attempts)
            for status in ("invalid", "ambiguous", "unavailable")
        },
    }
    return {
        **counts(units),
        **{f"input_{key}": value for key, value in counts(supplied).items()},
        **{key: None if unextractable else value for key, value in occurrence_counts.items()},
        "citation_occurrence_status": "unavailable_unextractable" if unextractable else "available",
        "unextractable_citation_fields": unextractable,
        "observed_citation_occurrences": len(attempts),
        "observed_resolved_citation_occurrences": resolved,
        "canonical_units": sorted(units),
        "input_canonical_units": sorted(supplied),
        "input_citations": len(supplied),
        "invalid_ids": invalid,
        "invalid_id_count": len(invalid),
    }


def citation_complexity(automatic: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    """Count each citation attempt and distinct resolved units from the saved mapping."""
    passages = {row["citation_id"]: tuple(row["canonical_unit"]) for row in mapping["passages"]}
    if len(passages) != len(mapping["passages"]):
        raise ValueError("Duplicate citation mapping")
    attempts = automatic.get("citation_attempts", [])
    units = [passages[a["raw"]] for a in attempts if a["status"] == "resolved"]
    counts = response_unit_counts(units, list(passages.values()), attempts)
    return {
        **counts,
        "delivery_coverage": 1.0 if automatic.get("delivery") == "exact_payload_verified" else None,
        "delivered_citations": counts["input_response_units"]
        if automatic.get("delivery") == "exact_payload_verified"
        else None,
    }
