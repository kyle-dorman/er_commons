"""Candidate-neutral assertions for the reviewed table-link change window."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from er_commons.task03g2f_replay.errors import ReplayValidationError
from er_commons.task03g2f_replay.io import JsonObject, read_json


@dataclass(frozen=True)
class TableDelta:
    """Candidate-neutral table-link changes caused by the ten-page window."""

    newly_resolved_distances: tuple[int, ...]
    newly_ambiguous_distances: tuple[tuple[int, ...], ...]
    outside_nearest_distances: tuple[int, ...]
    previously_resolved_changed: int

    @classmethod
    def expected(cls) -> TableDelta:
        """Return the reviewed retained-pilot expectation."""
        return cls(
            newly_resolved_distances=(6, 6, 6, 7, 7, 8),
            newly_ambiguous_distances=((9, 10), (9, 10)),
            outside_nearest_distances=(19, 25, 25, 36, 38, 41, 44, 47, 49, 51, 53, 79),
            previously_resolved_changed=0,
        )


def validate_table_changes(
    old_rows: dict[str, list[JsonObject]],
    new_rows: dict[str, list[JsonObject]],
    appendix_p_cross_root: Path,
) -> TableDelta:
    """Require the exact Appendix P delta and no changes in other sources."""
    delta = compute_table_delta(
        old_rows["deir_appendix_p"],
        new_rows["deir_appendix_p"],
        appendix_p_cross_root,
    )
    if delta != TableDelta.expected():
        raise ReplayValidationError(
            "TABLE_WINDOW_DELTA",
            "ten-page table-link changes differ from reviewed evidence",
            expected=asdict(TableDelta.expected()),
            observed=asdict(delta),
        )
    for source_id in ("deir_main", "deir_appendix_d"):
        if _table_outcomes(old_rows[source_id]) != _table_outcomes(new_rows[source_id]):
            raise ReplayValidationError(
                "UNAFFECTED_TABLE_OUTCOME",
                "table outcomes changed in an unaffected source",
                source_id=source_id,
            )
    return delta


def compute_table_delta(
    old: list[JsonObject], new: list[JsonObject], cross_root: Path
) -> TableDelta:
    """Compute a namespace-independent before/after summary for table mentions."""
    old_by_key = _table_mentions_by_key(old)
    new_by_key = _table_mentions_by_key(new)
    if set(old_by_key) != set(new_by_key):
        raise ReplayValidationError(
            "TABLE_MENTION_COVERAGE",
            "table mention identities changed beyond candidate namespaces",
            missing=sorted(set(old_by_key) - set(new_by_key)),
            added=sorted(set(new_by_key) - set(old_by_key)),
        )
    target_pages = _target_pages(cross_root)
    resolved: list[int] = []
    ambiguous: list[tuple[int, ...]] = []
    outside: list[int] = []
    changed = 0
    for key, before in old_by_key.items():
        after = new_by_key[key]
        if before["resolution_status"] == "resolved" and _candidate_ids(before) != _candidate_ids(
            after
        ):
            changed += 1
        if before["resolution_status"] != "unresolved":
            continue
        if after["resolution_status"] == "resolved":
            resolved.append(int(after["candidates"][0]["page_distance"]))
        elif after["resolution_status"] == "ambiguous":
            ambiguous.append(
                tuple(sorted(int(item["page_distance"]) for item in after["candidates"]))
            )
        elif after.get("unresolved_reason") == "outside_table_page_window":
            mention_page = _page_number(str(after["regions"][0]["page_id"]))
            distances = [
                abs(mention_page - target_page)
                for target_page in target_pages.get(str(after["lookup_key"]), ())
            ]
            if distances:
                outside.append(min(distances))
    return TableDelta(
        tuple(sorted(resolved)),
        tuple(sorted(ambiguous)),
        tuple(sorted(outside)),
        changed,
    )


def _target_pages(cross_root: Path) -> dict[str, tuple[int, ...]]:
    index = read_json(cross_root / "support/cross_reference_target_index.json")
    pages: dict[str, list[int]] = {}
    for entry in index["entries"]:
        page_id = entry.get("evidence_page_id")
        if entry.get("target_type") == "table" and page_id:
            pages.setdefault(str(entry["lookup_key"]), []).append(_page_number(str(page_id)))
    return {alias: tuple(sorted(values)) for alias, values in pages.items()}


def _table_mentions_by_key(rows: list[JsonObject]) -> dict[tuple[object, ...], JsonObject]:
    return {_mention_key(row): row for row in rows if row.get("mention_class") == "table"}


def _mention_key(row: JsonObject) -> tuple[object, ...]:
    return (
        row["raw_text"],
        row["lookup_key"],
        tuple(row["source_charspan"]),
        _namespace_suffix(str(row["source_record_id"])),
        _namespace_suffix(str(row["regions"][0]["page_id"])),
    )


def _candidate_ids(row: JsonObject) -> tuple[str, ...]:
    return tuple(
        sorted(_namespace_suffix(str(item["target_record_id"])) for item in row["candidates"])
    )


def _table_outcomes(rows: list[JsonObject]) -> list[tuple[object, ...]]:
    return sorted(
        (
            _mention_key(row),
            row["resolution_status"],
            row.get("unresolved_reason"),
            _candidate_ids(row),
        )
        for row in rows
        if row.get("mention_class") == "table"
    )


def _page_number(page_id: str) -> int:
    try:
        return int(page_id.rsplit("/p", 1)[1])
    except (IndexError, ValueError) as error:
        raise ReplayValidationError(
            "PAGE_ID",
            "page ID lacks the expected physical-page suffix",
            page_id=page_id,
        ) from error


def _namespace_suffix(value: str) -> str:
    return value.split("/", 1)[1] if "/" in value else value
