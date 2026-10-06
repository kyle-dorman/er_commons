"""Validate two-pass assertion coverage independently of model relevance choices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.group_ranking import digest, encoded, indexed

SCHEMAS = Path(__file__).resolve().parents[2] / "benchmarks/er_bench/schemas/task08d/v1"


def validate_inventory(
    packet: dict[str, Any], inventory: dict[str, Any], proposal: dict[str, Any]
) -> dict[str, Any]:
    """Require every exact passage and inventoried assertion to survive both passes.

    This verifies accounting, never semantic completeness or truth. Independent
    source coverage review remains necessary before human review.
    """
    for name, value in (("inventory", inventory), ("proposal", proposal)):
        Draft202012Validator(json.loads((SCHEMAS / f"{name}.schema.json").read_bytes())).validate(
            value
        )
        if value["packet_sha256"] != digest(encoded(packet)):
            raise ValueError("Two-pass input packet hash differs")
    if proposal["inventory_sha256"] != digest(encoded(inventory)):
        raise ValueError("Proposal does not bind the saved first-pass inventory")
    cases = indexed(packet["cases"], "case_id")
    inventories = indexed(inventory["cases"], "case_id")
    proposals = indexed(proposal["cases"], "case_id")
    if cases.keys() != inventories.keys() or cases.keys() != proposals.keys():
        raise ValueError("Two-pass case membership differs")
    counts = []
    for cid, case in cases.items():
        passages = indexed(case["passages"], "passage_id")
        assertions = indexed(inventories[cid]["assertions"], "assertion_id")
        coverage = indexed(inventories[cid]["passage_coverage"], "passage_id")
        claims = indexed(proposals[cid]["claims"], "claim_id")
        if passages.keys() != coverage.keys():
            raise ValueError("First pass must account for every response passage")
        for aid, assertion in assertions.items():
            refs = assertion["passage_ids"]
            if not refs or not set(refs) <= passages.keys():
                raise ValueError("Assertion requires exact known response passages")
            for pid in refs:
                if aid not in coverage[pid]["assertion_ids"]:
                    raise ValueError("Assertion and passage coverage disagree")
        for pid, item in coverage.items():
            if not set(item["assertion_ids"]) <= assertions.keys():
                raise ValueError("Unknown coverage assertion")
            for aid in item["assertion_ids"]:
                if pid not in assertions[aid]["passage_ids"]:
                    raise ValueError("Coverage and assertion passages disagree")
        mapped: set[str] = set()
        for claim in claims.values():
            aids = set(claim["assertion_ids"])
            if not aids or not aids <= assertions.keys():
                raise ValueError("Claim must map to first-pass assertions")
            mapped.update(aids)
            refs = set(claim["passage_ids"])
            if not refs or not refs <= passages.keys():
                raise ValueError("Claim requires known response passages")
            if not set(p for aid in aids for p in assertions[aid]["passage_ids"]) <= refs:
                raise ValueError("Claim dropped inventoried source qualifications")
        if mapped != assertions.keys():
            raise ValueError("Second pass silently omitted inventoried assertions")
        counts.append(
            {
                "case_id": cid,
                "passages": len(passages),
                "assertions": len(assertions),
                "claims": len(claims),
            }
        )
    return {"valid": True, "cases": counts, "semantic_coverage": "requires independent review"}
