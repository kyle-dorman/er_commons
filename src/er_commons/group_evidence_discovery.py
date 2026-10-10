"""Thin saved-query and canonical-section access for question research workers."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from er_commons.group_claims_batch import read_reference, reference, write_new
from er_commons.pilot_citation_records import bound_bytes, index_records
from er_commons.pilot_citation_visual_sections import assemble_visual_section
from er_commons.pilot_evidence_search import assemble_section, search


def native_printed_label(text: str) -> str | None:
    """Read a unique printed label from native page furniture, never infer an offset."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    found = []
    for line in lines[-8:]:
        found.extend(re.findall(r"(?<![\w.])(?:\d+(?:\.\d+)*-\d+|[A-Za-z]-\d+)(?![\w.])", line))
        if re.fullmatch(r"\d+|[ivxlcdm]+", line):
            found.append(line)
    for line in lines[:8]:
        match = re.fullmatch(r"Page (\d+) of \d+", line)
        if match:
            found.append(match[1])
    distinct = set(found)
    return next(iter(distinct)) if len(distinct) == 1 else None


def resolve_printed_labels(candidate: dict[str, Any], data_root: Path) -> dict[str, Any]:
    """Return a new citation with source-native footer proof for unresolved labels."""
    result = copy.deepcopy(candidate)
    proof = result.setdefault("printed_label_proof", [])
    for index, label in enumerate(result["printed_labels"]):
        if not label.startswith("printed label unverified"):
            continue
        page = result["physical_pages"][index]
        pdf = (data_root / result["source_pdf_path"]).resolve()
        if not pdf.is_relative_to(data_root.resolve()):
            raise ValueError("Source PDF escapes data root")
        raw = subprocess.check_output(
            ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"]
        )
        text = raw.decode("utf-8")
        resolved = native_printed_label(text)
        if resolved is not None:
            result["printed_labels"][index] = resolved
        lines = [line for line in text.splitlines() if line.strip()]
        proof.append(
            {
                "physical_page": page,
                "label": resolved,
                "method": "native_pdf_furniture_unique_label",
                "source_sha256": result["source_sha256"],
                "native_text_sha256": hashlib.sha256(raw).hexdigest(),
                "header_lines": lines[:8],
                "footer_lines": lines[-8:],
            }
        )
    if "citation_unit" in result:
        result["citation_unit"]["citation_label"] = (
            result["title"] + " (pp. " + ", ".join(result["printed_labels"]) + ")"
        )
    from er_commons.pilot_evidence import candidate_id

    result["candidate_id"] = candidate_id({k: v for k, v in result.items() if k != "occurrence_id"})
    return result


def run_query(
    case_dir: Path,
    index_path: Path,
    track: str,
    query: dict[str, Any],
    *,
    plan_path: Path | None = None,
) -> dict[str, Any]:
    """Save exact query intent before execution and safely resume a completed receipt."""
    plan_path = plan_path or case_dir / "plan.json"
    if not plan_path.is_file():
        raise ValueError("Save the case plan before live search")
    plan = json.loads(plan_path.read_bytes())
    if track not in plan["tracks"]:
        raise ValueError("Unknown search track")
    if query.get("source_filter") is not None and not isinstance(query["source_filter"], str):
        raise ValueError("source_filter must be one source ID string or null")
    identity = query["query_id"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", identity):
        raise ValueError("Query identity must be a safe filename")
    directory = case_dir / "queries" / track
    planned = directory / f"{identity}.plan.json"
    output = directory / f"{identity}.receipt.json"
    budget = plan["tracks"][track]
    if not planned.exists() and len(list(directory.glob("*.plan.json"))) >= (
        budget["queries"] + budget["follow_up_queries"]
    ):
        raise ValueError("Track budget exhausted; justify and save a plan revision first")
    write_new(
        planned,
        {
            "track": track,
            "plan": reference(plan_path),
            "index_path": str(index_path),
            "query": query,
        },
    )
    if output.exists():
        saved: dict[str, Any] = read_reference(
            json.loads((directory / f"{identity}.binding.json").read_bytes())
        )
        return saved
    receipt = search(index_path, **query)
    write_new(output, receipt)
    write_new(directory / f"{identity}.binding.json", reference(output))
    return receipt


def assemble_source(
    source: dict[str, Any],
    section_id: str,
    data_root: Path,
    raw_source: dict[str, Any],
    raw_manifest: dict[str, str],
) -> list[dict[str, Any]]:
    """Reuse complete ordinary/visual units; complex table layouts fail explicitly.

    Printed labels use exact canonical footer text only. Ambiguous labels remain
    visibly unverified, never guessed from PDF offsets. Table render inspection
    remains a separate required worker receipt before packet validation.
    """
    blocks = index_records(bound_bytes(source["files"]["blocks"], data_root))
    sections = index_records(bound_bytes(source["files"]["sections"], data_root))
    pages = index_records(bound_bytes(source["files"]["pages"], data_root))
    labels: dict[int, str] = {}
    proof = []
    footers: dict[int, list[dict[str, Any]]] = {}
    for block in blocks.values():
        if block.get("content_layer") == "footer":
            for region in block.get("regions", []):
                page_number = int(region["page_id"].rsplit("/p", 1)[-1])
                footers.setdefault(page_number, []).append(block)
    for page in pages.values():
        number = page["physical_page_number"]
        found = []
        for footer in footers.get(number, []):
            for line in footer["canonical_text"].splitlines():
                line = line.strip()
                found.extend(
                    re.findall(r"(?<![\w.])(?:\d+(?:\.\d+)*-\d+|[A-Za-z]-\d+)(?![\w.])", line)
                )
                if re.fullmatch(r"\d+|[ivxlcdm]+", line):
                    found.append(line)
        distinct = set(found)
        label = next(iter(distinct)) if len(distinct) == 1 else None
        labels[number] = label or f"printed label unverified; PDF {number}"
        proof.append(
            {
                "physical_page": number,
                "label": labels[number],
                "footer_record_ids": [b["id"] for b in footers.get(number, [])],
            }
        )
    metadata = {
        "document_title": raw_source["official_title"],
        "edition": (
            "2026 Final EIR Appendix F.1 (accepted qualified substitute)"
            if source["source_id"] == "feir_appendix_f1"
            else "2025 Draft EIR"
        ),
        "source_url": raw_source["final_resolved_url"],
        "pdf_url": raw_source["final_resolved_url"],
        "source_sha256": raw_source["sha256"],
        "source_manifest": raw_manifest,
        "source_pdf_path": raw_source["local_path"],
        "limitations": source["eligibility"].get("limitations", [])
        + ["Text evidence only; source usability retains accepted sampled-review limits."],
    }
    kwargs: dict[str, Any] = dict(
        source=source,
        section_id=section_id,
        data_root=data_root,
        printed_labels_by_page=labels,
        metadata=metadata,
    )
    section = sections[section_id]
    if any("/figure/" in member for member in section["ordered_child_ids"]):
        candidates = assemble_visual_section(**kwargs)
    else:
        candidates = assemble_section(**kwargs)
    for candidate in candidates:
        candidate["printed_label_proof"] = [
            row for row in proof if row["physical_page"] in candidate["physical_pages"]
        ]
    # Candidate IDs bind all material fields, including added label provenance.
    from er_commons.pilot_evidence import candidate_id

    for candidate in candidates:
        candidate["candidate_id"] = candidate_id(candidate)
    return [resolve_printed_labels(candidate, data_root) for candidate in candidates]
