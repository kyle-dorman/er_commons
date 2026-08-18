"""Candidate-neutral evidence audit for the retained Task 03G.2f pilot."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from er_commons.task03g2f_replay.errors import ReplayValidationError
from er_commons.task03g2f_replay.io import JsonObject, read_jsonl
from er_commons.task03g2f_replay.table_audit import TableDelta, validate_table_changes

EXPECTED_MAIN_COUNTS = {"appendix d": 8, "appendix p": 10}
EXPECTED_TARGETS = {
    "appendix d": ["deir_appendix_d"],
    "appendix p": ["deir_appendix_p"],
}


@dataclass(frozen=True)
class ReplayAuditReport:
    """Reviewed behavioral evidence independent of candidate namespaces."""

    old_candidates: dict[str, str]
    new_cross_reference_candidates: dict[str, str]
    new_document_candidates: dict[str, str]
    main_deferred_counts: dict[str, int]
    appendix_p_local_appendix_d: int
    appendix_d_local_appendix_a: int
    external_named_documents: int
    table_delta: TableDelta

    def as_json(self) -> JsonObject:
        """Serialize the report without leaking runtime paths."""
        return asdict(self)


class PilotReplayAuditor:
    """Check the finite reviewed pilot controls against sealed JSONL streams."""

    def audit(
        self,
        *,
        old_candidates: dict[str, Path],
        new_candidates: dict[str, Path],
        new_cross_reference_roots: dict[str, Path],
    ) -> ReplayAuditReport:
        """Validate all local, cross-document, and table-window expectations."""
        old_rows = _cross_references(old_candidates)
        new_rows = _cross_references(new_candidates)
        main_counts = validate_main_deferrals(new_rows["deir_main"])
        local_d, local_a, external = validate_local_ownership(new_rows)
        table_delta = validate_table_changes(
            old_rows,
            new_rows,
            new_cross_reference_roots["deir_appendix_p"],
        )
        return ReplayAuditReport(
            old_candidates={source: root.name for source, root in old_candidates.items()},
            new_cross_reference_candidates={
                source: root.name for source, root in new_cross_reference_roots.items()
            },
            new_document_candidates={source: root.name for source, root in new_candidates.items()},
            main_deferred_counts=main_counts,
            appendix_p_local_appendix_d=local_d,
            appendix_d_local_appendix_a=local_a,
            external_named_documents=external,
            table_delta=table_delta,
        )


def _cross_references(candidates: dict[str, Path]) -> dict[str, list[JsonObject]]:
    return {
        source: read_jsonl(root / "content/canonical/cross_references.jsonl")
        for source, root in candidates.items()
    }


def validate_main_deferrals(rows: list[JsonObject]) -> dict[str, int]:
    """Check source identity evidence on every deferred main-report appendix mention."""
    deferred = [
        row
        for row in rows
        if row.get("unresolved_reason") == "deferred_cross_document"
        and row.get("lookup_key") in EXPECTED_MAIN_COUNTS
    ]
    counts = {
        alias: sum(row["lookup_key"] == alias for row in deferred) for alias in EXPECTED_MAIN_COUNTS
    }
    if counts != EXPECTED_MAIN_COUNTS:
        raise ReplayValidationError(
            "MAIN_DEFERRED_COUNTS",
            "main-report appendix deferrals differ from reviewed evidence",
            expected=EXPECTED_MAIN_COUNTS,
            observed=counts,
        )
    for row in deferred:
        alias = str(row["lookup_key"])
        evidence = row.get("cross_document_evidence")
        observed = (
            evidence.get("intended_target_source_ids") if isinstance(evidence, dict) else None
        )
        if observed != EXPECTED_TARGETS[alias]:
            raise ReplayValidationError(
                "MAIN_INTENDED_SOURCE",
                "main-report deferral names the wrong source identity",
                mention_id=row.get("id"),
                alias=alias,
                expected=EXPECTED_TARGETS[alias],
                observed=observed,
            )
    return counts


def validate_local_ownership(
    rows: dict[str, list[JsonObject]],
) -> tuple[int, int, int]:
    """Check that local-first and external-document dispositions remain distinct."""
    observed = (
        _count(
            rows["deir_appendix_p"],
            mention_class="appendix",
            lookup_key="appendix d",
            resolution_status="resolved",
        ),
        _count(
            rows["deir_appendix_d"],
            mention_class="appendix",
            lookup_key="appendix a",
            unresolved_reason="no_local_alias",
        ),
        _count(
            rows["deir_appendix_p"],
            unresolved_reason="external_document_outside_corpus",
        ),
    )
    expected = (2, 2, 1)
    if observed != expected:
        raise ReplayValidationError(
            "LOCAL_OWNERSHIP",
            "local-first or external-document controls differ",
            expected=expected,
            observed=observed,
        )
    return observed


def _count(rows: list[JsonObject], **conditions: object) -> int:
    return sum(all(row.get(field) == value for field, value in conditions.items()) for row in rows)
