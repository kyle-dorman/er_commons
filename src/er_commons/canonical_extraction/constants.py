"""Stable paths and vocabulary shared by the canonicalization application."""

from pathlib import Path

SCHEMA_VERSION = "er_commons.canonical_extraction.v1"
PROJECT_ROOT = Path(__file__).parents[3]
SCHEMA_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "er_bench"
    / "schemas"
    / "canonical_extraction"
    / "v1"
    / "records.schema.json"
)
MAPPING_POLICY_PATH = PROJECT_ROOT / "docs" / "specs" / "task03d_appendix_p_mapping_v1.md"

BLOCK_TYPE_BY_LABEL = {
    "caption": "caption",
    "footnote": "footnote",
    "list_item": "list_item",
    "page_footer": "page_footer",
    "page_header": "page_header",
    "section_header": "heading",
    "text": "paragraph",
    "title": "title",
}
