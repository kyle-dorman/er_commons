"""Collection-wide aggregation over per-document report records."""

from __future__ import annotations

from collections import Counter

from er_commons.extraction_reporting.inputs import JsonObject


def sum_source_metrics(sources: list[JsonObject]) -> JsonObject:
    """Aggregate candidate metrics and resource observations."""
    totals: Counter[str] = Counter()
    wall_seconds = 0.0
    output_bytes = 0
    peak_rss_bytes = 0
    for source in sources:
        for name, value in source.get("metrics", {}).items():
            totals[name] += value
        resources = source.get("resources", {})
        wall_seconds += float(resources.get("wall_seconds", 0))
        output_bytes += int(resources.get("output_bytes", 0))
        peak_rss_bytes = max(peak_rss_bytes, int(resources.get("peak_rss_bytes") or 0))
    return {
        **dict(sorted(totals.items())),
        "wall_seconds": wall_seconds,
        "output_bytes": output_bytes,
        "peak_rss_bytes_max": peak_rss_bytes,
    }


def resource_extrema(sources: list[JsonObject]) -> JsonObject:
    """Select deterministic per-metric minima and maxima across successful sources."""
    successful = [source for source in sources if "metrics" in source]
    definitions = {
        "tables": ("metrics", "tables"),
        "table_families": ("metrics", "table_families"),
        "wall_seconds": ("resources", "wall_seconds"),
        "peak_rss_bytes": ("resources", "peak_rss_bytes"),
        "output_bytes": ("resources", "output_bytes"),
    }
    extrema: JsonObject = {}
    for metric, (group, field) in definitions.items():
        values = [
            {
                "source_id": source["source_id"],
                "candidate_id": source["candidate_id"],
                "metric": metric,
                "value": source[group][field],
            }
            for source in successful
        ]
        if values:
            ordered = sorted(values, key=lambda row: (row["value"], row["source_id"]))
            extrema[metric] = {"minimum": ordered[0], "maximum": ordered[-1]}
    return extrema


__all__ = ["resource_extrema", "sum_source_metrics"]
