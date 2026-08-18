"""Assign contiguous table families from explicit native evidence.

Family evidence is intentionally ordered:

       accepted reviewed continuation
                    |
                    v
       consecutive worksheet footer counters
                    |
                    v
          exact cleaned header match
                    |
                    v
             singleton family

Footer ownership is already resolved geometrically by the page extractor. This
module never guesses that a parser's last return is the footer owner.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class TableGroups:
    """Small union-find that forbids two tables from the same page."""

    def __init__(self, page_by_table: dict[str, int]) -> None:
        self.parent = {table_id: table_id for table_id in page_by_table}
        self.pages = {table_id: {page} for table_id, page in page_by_table.items()}
        self.evidence: dict[str, set[str]] = {table_id: set() for table_id in page_by_table}

    def find(self, table_id: str) -> str:
        """Return the canonical component root with path compression."""
        if self.parent[table_id] != table_id:
            self.parent[table_id] = self.find(self.parent[table_id])
        return self.parent[table_id]

    def union(self, left: str, right: str, evidence: str) -> bool:
        """Join two components if their physical-page sets do not overlap."""
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            self.evidence[left_root].add(evidence)
            return True
        if self.pages[left_root] & self.pages[right_root]:
            return False
        first, second = sorted((left_root, right_root))
        self.parent[second] = first
        self.pages[first] |= self.pages[second]
        self.evidence[first] |= self.evidence[second] | {evidence}
        return True


def footer_continues(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Return whether two page records form a consecutive worksheet run."""
    left_footer = left.get("footer")
    right_footer = right.get("footer")
    return bool(
        left_footer
        and right_footer
        and right["physical_pdf_page"] == left["physical_pdf_page"] + 1
        and left_footer["sheet_id"] == right_footer["sheet_id"]
        and left_footer["internal_total"] == right_footer["internal_total"]
        and right_footer["internal_page"] == left_footer["internal_page"] + 1
    )


def headers_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Require exact non-empty cleaned headers and effective column counts."""
    return bool(
        left["header_matrix"]
        and left["header_matrix"] == right["header_matrix"]
        and left["cleanup"]["effective_column_count"] == right["cleanup"]["effective_column_count"]
    )


def _union_accepted_continuations(
    groups: TableGroups,
    decisions: list[dict[str, Any]],
) -> None:
    """Apply only explicit accepted continuation evidence before heuristics."""
    for decision in decisions:
        if decision.get("status") != "accepted":
            continue
        joined = groups.union(
            str(decision["left_table_id"]),
            str(decision["right_table_id"]),
            "cross_page_continuation",
        )
        if not joined:
            raise ValueError("accepted continuation would place two tables from one page together")


def _explicit_continuation_pairs(
    decisions: list[dict[str, Any]],
) -> set[frozenset[str]]:
    """Return evaluated table pairs that older heuristics may not override."""
    return {
        frozenset((str(decision["left_table_id"]), str(decision["right_table_id"])))
        for decision in decisions
        if isinstance(decision.get("left_table_id"), str)
        and isinstance(decision.get("right_table_id"), str)
    }


def _is_explicit_pair(left: str, right: str, pairs: set[frozenset[str]]) -> bool:
    """Return whether continuation policy already disposed this table pair."""
    return frozenset((left, right)) in pairs


def assign_families(
    page_records: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    *,
    family_id_prefix: str = "g3_table",
    continuation_records: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Assign every logical table once using footer evidence before headers."""
    page_by_table = {str(table["table_id"]): int(table["physical_pdf_page"]) for table in tables}
    groups = TableGroups(page_by_table)
    table_by_id = {str(table["table_id"]): table for table in tables}
    footer_owned = {
        str(page["footer_owner_table_id"])
        for page in page_records
        if page.get("footer_owner_table_id")
    }

    decisions = continuation_records or []
    _union_accepted_continuations(groups, decisions)
    explicit_pairs = _explicit_continuation_pairs(decisions)

    ordered_pages = sorted(page_records, key=lambda item: item["physical_pdf_page"])
    for left_page, right_page in zip(ordered_pages, ordered_pages[1:], strict=False):
        if not footer_continues(left_page, right_page):
            continue
        left_owner = left_page.get("footer_owner_table_id")
        right_owner = right_page.get("footer_owner_table_id")
        if (
            left_owner
            and right_owner
            and not _is_explicit_pair(str(left_owner), str(right_owner), explicit_pairs)
        ):
            groups.union(str(left_owner), str(right_owner), "footer_run")

    # A page-local visual index is stable enough for exact-header continuation
    # but is never allowed to override footer ownership.
    by_visual_index: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for table in tables:
        if table["table_id"] not in footer_owned:
            by_visual_index[int(table["page_table_index"])].append(table)
    for candidates in by_visual_index.values():
        candidates.sort(key=lambda item: item["physical_pdf_page"])
        for left, right in zip(candidates, candidates[1:], strict=False):
            if (
                right["physical_pdf_page"] == left["physical_pdf_page"] + 1
                and headers_match(left, right)
                and not _is_explicit_pair(
                    str(left["table_id"]), str(right["table_id"]), explicit_pairs
                )
            ):
                groups.union(
                    str(left["table_id"]),
                    str(right["table_id"]),
                    "exact_cleaned_header",
                )

    components: dict[str, list[str]] = defaultdict(list)
    for table_id in page_by_table:
        components[groups.find(table_id)].append(table_id)
    ordered_components = sorted(
        components.items(),
        key=lambda item: min(
            (
                page_by_table[table_id],
                int(table_by_id[table_id]["page_table_index"]),
            )
            for table_id in item[1]
        ),
    )

    family_by_table: dict[str, str] = {}
    families = []
    for number, (root, members) in enumerate(ordered_components, start=1):
        family_id = f"{family_id_prefix}_family_{number:04d}"
        members.sort(
            key=lambda table_id: (
                page_by_table[table_id],
                int(table_by_id[table_id]["page_table_index"]),
            )
        )
        for table_id in members:
            family_by_table[table_id] = family_id
        pages = [page_by_table[table_id] for table_id in members]
        if len(pages) != len(set(pages)):
            raise ValueError(f"family contains two tables from one page: {family_id}")
        evidence = sorted(groups.evidence[groups.find(root)])
        families.append(
            {
                "family_id": family_id,
                "evidence": evidence or ["singleton"],
                "start_page": min(pages),
                "end_page": max(pages),
                "page_count": len(pages),
                "table_ids": members,
            }
        )

    assignments = [
        {
            "table_id": table["table_id"],
            "physical_pdf_page": table["physical_pdf_page"],
            "page_table_index": table["page_table_index"],
            "family_id": family_by_table[str(table["table_id"])],
            "footer_owned": table["table_id"] in footer_owned,
        }
        for table in tables
    ]
    return assignments, families
