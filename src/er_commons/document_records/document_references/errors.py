"""Context-rich failures raised by document-reference contracts."""

from __future__ import annotations

from pathlib import Path


class ContractViolation(ValueError):
    """One named invariant failed for a specific artifact or record."""

    def __init__(
        self,
        *,
        stage: str,
        invariant: str,
        path: Path | str | None = None,
        record_id: str | None = None,
        detail: str | None = None,
    ) -> None:
        context = [f"stage={stage}", f"invariant={invariant}"]
        if path is not None:
            context.append(f"path={path}")
        if record_id is not None:
            context.append(f"record_id={record_id}")
        if detail is not None:
            context.append(f"detail={detail}")
        super().__init__("document-reference contract violation [" + "; ".join(context) + "]")
        self.stage = stage
        self.invariant = invariant
        self.path = Path(path) if path is not None else None
        self.record_id = record_id
        self.detail = detail
