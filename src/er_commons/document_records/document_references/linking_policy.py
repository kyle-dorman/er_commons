"""Load the sealed, reusable document-linking policy into typed caller profiles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.document_records.document_references.exact_resolution import TextMatchRule


class LinkingPolicyError(ValueError):
    """Raised when policy bytes are valid JSON but not an executable v1 policy."""


class LinkCaller(StrEnum):
    """Adapters authorized to submit neutral queries to the shared resolver."""

    MACHINE_REFERENCE = "machine_reference"
    EFFECTIVE_NAVIGATION = "effective_navigation"


@dataclass(frozen=True)
class CallerProfile:
    """Executable resolution behavior for one claim-producing adapter."""

    caller: LinkCaller
    section_fallback_rules: tuple[TextMatchRule, ...]
    table_fallback_rules: tuple[TextMatchRule, ...]
    allow_goal_prefix: bool


@dataclass(frozen=True)
class DocumentLinkingPolicy:
    """Validated policy plus its two explicit caller profiles."""

    schema_version: str
    policy_name: str
    machine_reference: CallerProfile
    effective_navigation: CallerProfile

    def profile(self, caller: LinkCaller) -> CallerProfile:
        """Return the exact profile for a known caller without implicit defaults."""
        if caller is LinkCaller.MACHINE_REFERENCE:
            return self.machine_reference
        if caller is LinkCaller.EFFECTIVE_NAVIGATION:
            return self.effective_navigation
        raise LinkingPolicyError(f"unsupported document-link caller: {caller!r}")


_SECTION_FALLBACKS = (
    TextMatchRule.TERMINAL_PERIOD,
    TextMatchRule.AMPERSAND_AND,
    TextMatchRule.ALPHABETIC_HYPHEN,
    TextMatchRule.SLASH_WHITESPACE,
    TextMatchRule.SPLIT_FI_LIGATURE,
    TextMatchRule.OPTIONAL_COMMA_BEFORE_AND,
    TextMatchRule.APOSTROPHE_AND_TERMINAL_PERIOD,
    TextMatchRule.RETAINED_HYPHEN_WHITESPACE,
)
_TABLE_FALLBACKS = (
    TextMatchRule.RETAINED_HYPHEN_WHITESPACE,
    TextMatchRule.STRAIGHT_CURLY_APOSTROPHE,
    TextMatchRule.WHITESPACE_BEFORE_COMMA,
    TextMatchRule.OPTIONAL_DIGIT_LETTER_HYPHEN,
)
_SECTION_RULE_IDS = ("R1", "R2", "R2a", "R2b", "R3", "R4", "R5")


def load_document_linking_policy(policy_path: Path, *, schema_path: Path) -> DocumentLinkingPolicy:
    """Validate policy bytes strictly and map every accepted rule to executable behavior."""
    policy = _read_object(policy_path, label="linking policy")
    schema = _read_object(schema_path, label="linking policy schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(policy),
        key=lambda item: tuple(str(part) for part in item.path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "$"
        raise LinkingPolicyError(f"linking policy violates schema at {location}: {first.message}")
    _validate_executable_policy(policy)
    return DocumentLinkingPolicy(
        schema_version=str(policy["schema_version"]),
        policy_name=str(policy["policy_name"]),
        machine_reference=CallerProfile(
            caller=LinkCaller.MACHINE_REFERENCE,
            section_fallback_rules=(),
            table_fallback_rules=_TABLE_FALLBACKS,
            allow_goal_prefix=False,
        ),
        effective_navigation=CallerProfile(
            caller=LinkCaller.EFFECTIVE_NAVIGATION,
            section_fallback_rules=_SECTION_FALLBACKS,
            table_fallback_rules=_TABLE_FALLBACKS,
            allow_goal_prefix=True,
        ),
    )


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise LinkingPolicyError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise LinkingPolicyError(f"{label} must be a JSON object: {path}")
    return value


def _validate_executable_policy(policy: dict[str, Any]) -> None:
    """Reject schema-valid rearrangements that would silently alter rule ownership."""
    rule_ids = tuple(rule["rule_id"] for rule in policy["section_rules"])
    if rule_ids != _SECTION_RULE_IDS:
        raise LinkingPolicyError(
            f"section rules must appear exactly once in accepted order {_SECTION_RULE_IDS!r}"
        )
    section_transforms = tuple(rule.value for rule in _SECTION_FALLBACKS)
    if tuple(policy["section_fallback_transforms"]) != section_transforms:
        raise LinkingPolicyError("section fallback transforms do not match executable v1 rules")
    table_transforms = tuple(rule.value for rule in _TABLE_FALLBACKS)
    if tuple(policy["table_caption_fallback_rule"]["transforms"]) != table_transforms:
        raise LinkingPolicyError("table fallback transforms do not match executable R6a rules")


__all__ = [
    "CallerProfile",
    "DocumentLinkingPolicy",
    "LinkCaller",
    "LinkingPolicyError",
    "load_document_linking_policy",
]
