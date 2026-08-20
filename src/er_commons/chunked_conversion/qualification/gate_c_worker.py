"""One independently retryable Gate C range-conversion worker."""

from __future__ import annotations

from er_commons.chunked_conversion.qualification.contracts import RangeWorkerSpec
from er_commons.chunked_conversion.qualification.converted_range_store import ConvertedRangeStore
from er_commons.chunked_conversion.qualification.docling_adapter import DoclingAdapter
from er_commons.chunked_conversion.qualification.gate_c_inputs import verify_g1_inputs
from er_commons.chunked_conversion.range_contract import RangePlan


class RangeWorker:
    """Convert and completion-seal one planned range, or deep-verify its reuse."""

    def __init__(self, adapter: DoclingAdapter | None = None) -> None:
        self.adapter = adapter or DoclingAdapter()

    def run(self, spec: RangeWorkerSpec) -> None:
        """Execute the typed worker request without owning coordinator policy."""
        plan = RangePlan.model_validate_json(spec.plan_path.read_bytes())
        store = ConvertedRangeStore(spec.run_root, plan)
        planned = next((item for item in plan.ranges if item.range_id == spec.range_id), None)
        if planned is None:
            store.verify(spec.range_id)
            return
        final = store.final_root(spec.range_id)
        if final.exists():
            store.verify(spec.range_id)
            return
        verified = verify_g1_inputs(spec.source_root, spec.config_path, spec.data_root)
        conversion = self.adapter.convert_range(
            verified.prepared,
            planned.read,
            data_root=spec.data_root,
            log_path=spec.run_root / "logs" / planned.range_id / "worker.log",
        )
        store.publish(planned, conversion)


__all__ = ["RangeWorker"]
