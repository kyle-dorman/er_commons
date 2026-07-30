"""Frozen identifiers and publication paths for hierarchy correction v1."""

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

REQUIRED_ARTIFACT_PATHS = {
    "records/identity.json",
    "records/input_inventory.json",
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
}

ANCHOR_RULES = {
    "R03_APPLY_EXACT_OUTLINE_ANCHOR",
    "R04_APPLY_EXACT_TOC_ANCHOR",
}
