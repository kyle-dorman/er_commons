"""Frozen identifiers and publication paths for hierarchy inference v1."""

RULE_ORDER = (
    "R01_EXCLUDE_NON_BODY_OR_TOC",
    "R02_DEMOTE_BULLET_HEADING",
    "R03_APPLY_EXACT_OUTLINE_ANCHOR",
    "R04_APPLY_EXACT_TOC_ANCHOR",
    "R05_APPLY_NUMBERING_REGIME",
    "R06_FLAG_STRUCTURAL_AMBIGUITY",
    "R07_TRANSFER_LOCAL_HEADING_LEVEL",
    "R08_DEFAULT_PRESERVE",
)

MANAGED_PAYLOAD_PATHS = (
    "records/identity.json",
    "records/input_inventory.json",
    "records/environment.json",
    "artifacts/item_features.jsonl",
    "artifacts/visible_toc_entries.jsonl",
    "artifacts/toc_reconciliation.jsonl",
    "artifacts/regimes.jsonl",
    "artifacts/decisions.jsonl",
    "artifacts/hierarchy.json",
    "artifacts/ambiguities.jsonl",
    "artifacts/warnings.jsonl",
    "records/summary.json",
    "records/metrics.json",
)

REQUIRED_ARTIFACT_PATHS = frozenset(MANAGED_PAYLOAD_PATHS)

FATAL_CODES = frozenset(
    {
        "INPUT_COMPLETION_INVALID",
        "INPUT_INVENTORY_MISMATCH",
        "SOURCE_CHECKSUM_MISMATCH",
        "STABLE_KEY_COLLISION",
        "UNKNOWN_REFERENCE",
        "READING_ORDER_CYCLE",
        "PICTURE_CAPTION_RELATION_MISMATCH",
        "TOC_REGION_UNTERMINATED",
        "DECISION_COVERAGE_MISMATCH",
        "CORRECTED_LEVEL_INVALID",
        "HIERARCHY_CYCLE",
        "HIERARCHY_ORDER_INVALID",
        "MEMBERSHIP_NOT_INVERTIBLE",
        "PUBLICATION_COLLISION",
        "QUALITY_GATE_REJECTED",
        "REPEAT_BUILD_MISMATCH",
    }
)

ANCHOR_RULES = {
    "R03_APPLY_EXACT_OUTLINE_ANCHOR",
    "R04_APPLY_EXACT_TOC_ANCHOR",
}
