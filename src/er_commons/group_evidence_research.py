"""Question-specific Task08E research contracts; proposals never become decisions."""

import copy
import json
from pathlib import Path
from typing import Any

from er_commons.pilot_citation_records import bound_bytes
from er_commons.pilot_citation_units import validate_units
from er_commons.pilot_evidence import SCHEMA, digest, validate_candidates

TRACKS = (
    "direct_claims",
    "question_gaps",
    "definitions_methods",
    "broader_context",
    "counterevidence",
)
RELATIONSHIPS = {"Support", "Partial", "Context", "Not support", "Contradicts"}
VERSION = "task08e.research_packet.v1"
PLAN_VERSION = "task08e.research_plan.v1"


def create_plan(
    case: dict[str, Any], budgets: dict[str, dict[str, int]], rationale: str
) -> dict[str, Any]:
    """Bind an explicit complexity-based five-track budget before any searches."""
    plan = {
        "schema_version": PLAN_VERSION,
        "case_id": case["case_id"],
        "input_sha256": digest(case),
        "rationale": rationale,
        "tracks": copy.deepcopy(budgets),
        "revision": 1,
        "predecessor_sha256": None,
    }
    validate_plan(plan, case)
    return plan


def validate_plan(plan: dict[str, Any], case: dict[str, Any]) -> None:
    """Reject input drift, missing tracks and implicit unlimited search budgets."""
    if (
        plan.get("schema_version") != PLAN_VERSION
        or plan.get("case_id") != case["case_id"]
        or plan.get("input_sha256") != digest(case)
        or not plan.get("rationale")
    ):
        raise ValueError("Research plan must bind exact input and complexity rationale")
    if set(plan.get("tracks", {})) != set(TRACKS):
        raise ValueError("Every research track requires a saved budget")
    for budget in plan["tracks"].values():
        if not budget.get("objective"):
            raise ValueError("Each track needs a question-specific objective")
        for key in ("queries", "follow_up_queries"):
            if type(budget.get(key)) is not int or budget[key] < 1:
                raise ValueError("Each track needs positive initial and follow-up budgets")
    if type(plan.get("revision")) is not int or plan["revision"] < 1:
        raise ValueError("Positive plan revision required")
    if plan["revision"] > 1 and not plan.get("predecessor_sha256"):
        raise ValueError("Budget revisions must preserve preceding plan binding")


def save_plan(path: Path, plan: dict[str, Any]) -> None:
    """Save a new plan exclusively; callers execute only after this succeeds."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(plan, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def new_packet(case: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Create a blank working packet retaining all frozen input without inference."""
    validate_plan(plan, case)
    return {
        "schema_version": VERSION,
        "case_id": case["case_id"],
        "frozen_input": copy.deepcopy(case),
        "plan_sha256": digest(plan),
        "status": "working",
        "sources": [],
        "claim_findings": [],
        "beyond_claim_findings": [],
        "track_results": {},
        "model_provenance": {},
        "human_decisions": [],
        "eligibility": None,
        "disposition": None,
        "table_render_checks": [],
        "remaining_gaps": [],
        "limitations": [],
    }


def _validate_tracks(packet: dict[str, Any], plan: dict[str, Any]) -> None:
    """Account for every bounded query and inspection, including failures and stops."""
    results = packet.get("track_results", {})
    if set(results) != set(TRACKS):
        raise ValueError("All five research tracks must be accounted for")
    query_ids: set[str] = set()
    for track, result in results.items():
        receipts = result.get("query_receipts", [])
        if not receipts and not result.get("not_applicable_reason"):
            raise ValueError("Unsearched track needs an explicit applicability reason")
        if len(receipts) > sum(plan["tracks"][track][k] for k in ("queries", "follow_up_queries")):
            raise ValueError("Query budget exceeded; save a justified revision first")
        if not result.get("stop_reason") or "remaining_leads" not in result:
            raise ValueError("Search stop and remaining leads must be explicit")
        for receipt in receipts:
            identity = receipt.get("query_id")
            if not identity or identity in query_ids:
                raise ValueError("Unique query receipt identity required")
            query_ids.add(identity)
            if not all(receipt.get(k) for k in ("expression", "purpose", "index_identity")):
                raise ValueError("Exact query and search index bindings required")
            if receipt.get("status") not in {"completed", "error"}:
                raise ValueError("Unfinished query cannot seal")
            hits = receipt.get("hits")
            inspections = receipt.get("inspected_hits")
            if not isinstance(hits, list) or not isinstance(inspections, list):
                raise ValueError("Hits and explicit inspection dispositions required")
            keys = {(h["source_id"], h["record_id"]) for h in hits}
            inspected_keys = [(h.get("source_id"), h.get("record_id")) for h in inspections]
            if len(inspected_keys) != len(set(inspected_keys)) or set(inspected_keys) != keys:
                raise ValueError(
                    "Every returned hit needs an inspection or explicit uninspected disposition"
                )
            for inspected in inspections:
                if (
                    (inspected.get("source_id"), inspected.get("record_id")) not in keys
                    or not inspected.get("disposition")
                    or not inspected.get("reason")
                ):
                    raise ValueError("Inspected hit must bind a returned record and disposition")


def _validate_citations(finding: dict[str, Any], sources: dict[str, Any]) -> None:
    """Require exact verbatim source excerpts alongside separately identified proposals."""
    for citation in finding.get("citations", []):
        source = sources.get(citation.get("occurrence_id"))
        if (
            source is None
            or citation.get("candidate_id") != source["candidate_id"]
            or citation.get("relationship") not in RELATIONSHIPS
        ):
            raise ValueError("Finding citation needs exact candidate and proposed relationship")
        excerpt = citation.get("excerpt")
        if not excerpt or excerpt not in source["quote"] or not citation.get("reason"):
            raise ValueError("Citation excerpt must be verbatim within the validated source")
    if "limitations" not in finding:
        raise ValueError("Every finding must retain explicit limitations")


def _validate_table_renders(packet: dict[str, Any], data_root: Path) -> None:
    """Require agent comparisons with byte-bound renders for every table page."""
    tables = {
        s["occurrence_id"]: s
        for s in packet["sources"]
        if s.get("citation_unit", {}).get("kind") == "table"
    }
    checks = packet.get("table_render_checks", [])
    if len(checks) != len(tables) or {c.get("occurrence_id") for c in checks} != set(tables):
        raise ValueError("Every table occurrence requires its own render check")
    for check in checks:
        source = tables[check["occurrence_id"]]
        if (
            check.get("candidate_id") != source["candidate_id"]
            or check.get("status") != "agent_checked"
            or not check.get("actor")
            or not check.get("comparison")
            or "limitations" not in check
            or check.get("human_usability_decision") is not None
        ):
            raise ValueError("Table checks require agent comparison and blank human usability")
        renders = check.get("renders", [])
        if (
            len(renders) != len(source["physical_pages"])
            or sorted(r["physical_page"] for r in renders) != source["physical_pages"]
        ):
            raise ValueError("Every table-family page needs an exact render binding")
        for render in renders:
            bound_bytes(render["ref"], data_root)


def validate_packet(
    packet: dict[str, Any], case: dict[str, Any], plan: dict[str, Any], data_root: Path
) -> dict[str, Any]:
    """Validate prepared source-bound proposals, coverage and blank human decisions.

    Semantic correctness still requires independent coverage/export review. This
    validator checks machine-verifiable bindings, never human evidence acceptance.
    """
    validate_plan(plan, case)
    if (
        packet.get("schema_version") != VERSION
        or packet.get("frozen_input") != case
        or packet.get("case_id") != case["case_id"]
        or packet.get("plan_sha256") != digest(plan)
    ):
        raise ValueError("Packet must retain exact frozen context and saved plan")
    if (
        packet.get("human_decisions") != []
        or packet.get("eligibility") is not None
        or packet.get("disposition") is not None
    ):
        raise ValueError("Phase A must not contain human decisions or eligibility")
    if packet.get("status") != "prepared, awaiting human review":
        raise ValueError("Only explicitly prepared packets may seal")
    _validate_tracks(packet, plan)
    provenance = packet.get("model_provenance", {})
    if not all(
        provenance.get(k) for k in ("model", "input_sha256", "prompt_sha256", "output_sha256")
    ):
        raise ValueError("Exact advisory model input, prompt and output provenance required")
    if provenance["input_sha256"] != digest(case) or provenance["model"] != "gpt-6-astra":
        raise ValueError("Research requires Astra and exact case input")
    for key in ("input", "prompt", "output"):
        reference = provenance.get(key + "_ref")
        if not isinstance(reference, dict):
            raise ValueError("Actual saved model input, prompt and raw output bindings required")
        payload = bound_bytes(reference, data_root)
        if key == "input" and json.loads(payload) != case:
            raise ValueError("Model input file differs from frozen case")
        if key != "input" and reference["sha256"] != provenance[key + "_sha256"]:
            raise ValueError("Model provenance checksum differs from saved file")
    candidates = packet.get("sources", [])
    # Dispatches maintained section, visual, audited-section and table-family checks.
    occurrences = [c.get("occurrence_id") for c in candidates]
    if not all(occurrences) or len(occurrences) != len(set(occurrences)):
        raise ValueError("Distinct source occurrences required; never deduplicate sources")
    validate_units(candidates, data_root)
    for candidate in candidates:
        canonical_candidate = {k: v for k, v in candidate.items() if k != "occurrence_id"}
        validate_candidates(
            {"schema_version": SCHEMA, "candidates": [canonical_candidate]}, data_root
        )
    _validate_table_renders(packet, data_root)
    sources = {c["occurrence_id"]: c for c in candidates}
    claims = {c["claim_id"]: c for c in case["approved_claims"]}
    findings = packet.get("claim_findings", [])
    if len(findings) != len(claims) or {f["claim"]["claim_id"] for f in findings} != set(claims):
        raise ValueError("Every approved claim needs exactly one research finding")
    all_findings = findings + packet.get("beyond_claim_findings", [])
    ids = [f.get("finding_id") for f in all_findings]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError("Distinct finding identities required")
    for finding in findings:
        if finding["claim"] != claims[finding["claim"]["claim_id"]]:
            raise ValueError("Claim text, version and support targets must remain exact")
        if not finding.get("citations") and not finding.get("remaining_gaps"):
            raise ValueError("Uncited claims require an explicit bounded-search gap")
    for finding in packet.get("beyond_claim_findings", []):
        if (
            finding.get("track") not in TRACKS[1:]
            or not finding.get("summary")
            or not finding.get("citations")
            or "claim" in finding
        ):
            raise ValueError("Beyond-claim findings need separate grounded summaries")
    for finding in all_findings:
        _validate_citations(finding, sources)
    occurrence_owner: dict[str, str] = {}
    for finding in all_findings:
        for citation in finding.get("citations", []):
            occurrence = citation["occurrence_id"]
            if (
                occurrence in occurrence_owner
                and occurrence_owner[occurrence] != finding["finding_id"]
            ):
                raise ValueError("Source occurrences cannot be pooled across findings")
            occurrence_owner[occurrence] = finding["finding_id"]
    if not isinstance(packet.get("remaining_gaps"), list) or not packet.get("limitations"):
        raise ValueError("Packet must explicitly preserve remaining gaps and search limitations")
    return {
        "status": "valid",
        "packet_sha256": digest(packet),
        "case_id": case["case_id"],
        "claims": len(claims),
        "sources": len(candidates),
        "human_decisions": 0,
    }
