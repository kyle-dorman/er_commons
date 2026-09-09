"""Build a lazy, read-only browser view of Task 05E relationship-review cases."""

from __future__ import annotations

import re
from collections import Counter
from importlib.resources import files
from pathlib import Path
from typing import Any

from er_commons.artifact_io import json_bytes, read_json_object, read_jsonl

type ReviewObject = dict[str, Any]

_GENERAL_RESPONSE_ORIGIN_REASONS = {
    "case_variant",
    "whitespace_case_variant",
    "whitespace_variant",
    "unsupported_endpoint_kinds",
}
_STATIC_PACKAGE = "er_commons.response_inventory.review_tool_static"
_CONTEXT_CHARACTERS = 650


def build_relationship_review_tool(
    *,
    relationship_root: Path,
    source_records_path: Path,
    qualification_path: Path,
    render_root: Path,
    output_root: Path,
    served_root: Path,
) -> ReviewObject:
    """Materialize one source-free, lazy review bundle without copying page renders."""
    paths = _validated_paths(
        relationship_root=relationship_root,
        source_records_path=source_records_path,
        qualification_path=qualification_path,
        render_root=render_root,
        output_root=output_root,
        served_root=served_root,
    )
    census_path = _review_census_path(paths["relationship_root"])
    census = read_json_object(census_path)
    records = read_jsonl(paths["source_records_path"])
    qualification = read_json_object(paths["qualification_path"])
    store = _RecordStore(records, qualification, paths["render_root"], paths["served_root"])

    items = _select_review_items(census, store)
    categories = Counter(str(item["category"]) for item in items)
    index_items: list[ReviewObject] = []
    unit_ids: set[str] = set()
    for position, item in enumerate(items, start=1):
        item_id = f"case-{position:03d}"
        detail = _build_item_detail(item_id, item, store)
        _publish(paths["output_root"] / f"data/items/{item_id}.json", detail)
        for unit in detail["units"]:
            assert isinstance(unit, dict)
            unit_ids.add(str(unit["unit_id"]))
        index_items.append(_index_item(detail))

    for unit_id in sorted(unit_ids):
        _publish(
            paths["output_root"] / f"data/units/{unit_id}.json",
            store.full_unit_payload(unit_id),
        )

    index: ReviewObject = {
        "schema_version": "er_commons.task05e.review_tool.v1",
        "title": (
            "Task 05E bounded-rule review"
            if census.get("status") == "bounded_review_complete_review_required"
            else "Task 05E exact-pass review"
        ),
        "description": "Read-only relationship review. No decision or feedback is stored.",
        "relationship_activity_id": census["activity_id"],
        "case_count": len(items),
        "category_counts": dict(sorted(categories.items())),
        "items": index_items,
        "loading_contract": {
            "initial": "compact index only",
            "selection": "one case shard",
            "full_text": "one unit shard after an explicit click",
            "page_image": "one existing cached render after an explicit click",
        },
    }
    _publish(paths["output_root"] / "data/index.json", index)
    _publish_static(paths["output_root"])
    return {
        "status": "review_tool_complete",
        "case_count": len(items),
        "category_counts": dict(sorted(categories.items())),
        "output_root": str(paths["output_root"]),
        "served_root": str(paths["served_root"]),
        "start_path": "/" + paths["output_root"].relative_to(paths["served_root"]).as_posix() + "/",
        "source_pdf_accessed": False,
        "feedback_controls": False,
    }


def _validated_paths(**paths: Path) -> dict[str, Path]:
    """Resolve paths and enforce the external-artifact containment boundary."""
    resolved = {name: path.resolve() for name, path in paths.items()}
    served_root = resolved["served_root"]
    for name, path in resolved.items():
        if name != "served_root" and not path.is_relative_to(served_root):
            raise ValueError(f"{name} escapes served root: {path}")
    required_files = {
        "source_records_path": resolved["source_records_path"],
        "qualification_path": resolved["qualification_path"],
    }
    for name, path in required_files.items():
        if not path.is_file():
            raise ValueError(f"required {name} is absent: {path}")
    if not resolved["render_root"].is_dir():
        raise ValueError(f"render root is absent: {resolved['render_root']}")
    return resolved


def _review_census_path(relationship_root: Path) -> Path:
    """Select the exact or bounded-review census from one explicit relationship root."""
    candidates = [
        relationship_root / "diagnostics/review_census.json",
        relationship_root / "diagnostics/exact_baseline_census.json",
    ]
    existing = [path for path in candidates if path.is_file()]
    if len(existing) != 1:
        raise ValueError(
            f"relationship root must contain exactly one review census: {relationship_root}"
        )
    return existing[0]


class _RecordStore:
    """Index accepted 05D records and render metadata for review-only lookup."""

    def __init__(
        self,
        records: list[ReviewObject],
        qualification: ReviewObject,
        render_root: Path,
        served_root: Path,
    ) -> None:
        self.pages = _index(records, "page", "page_id")
        self.spans = _index(records, "source_span", "span_id")
        self.units = _index(records, "source_unit", "unit_id")
        self.mentions = _index(records, "reference_mention", "mention_id")
        self.memberships = _index(records, "membership_claim", "membership_id")
        self.labels: dict[str, list[str]] = {}
        for unit_id, unit in self.units.items():
            self.labels.setdefault(str(unit["official_label"]), []).append(unit_id)
        page_rows = qualification.get("pages")
        if not isinstance(page_rows, list):
            raise ValueError("qualification report lacks page rows")
        self.qualification = {
            int(row["physical_page"]): row for row in page_rows if isinstance(row, dict)
        }
        self.render_root = render_root
        self.served_root = served_root
        self.unit_order = sorted(self.units, key=self._unit_sort_key)
        self.unit_positions = {
            unit_id: position for position, unit_id in enumerate(self.unit_order)
        }

    def span_fragments(self, span_id: str) -> list[ReviewObject]:
        """Return text-bearing fragments with page and source offsets attached."""
        span = self.spans[span_id]
        raw_fragments = span.get("fragments")
        if not isinstance(raw_fragments, list):
            return []
        fragments: list[ReviewObject] = []
        for raw_fragment in raw_fragments:
            if not isinstance(raw_fragment, dict):
                continue
            page = self.pages[str(raw_fragment["page_id"])]
            text = str(page["raw_text"])
            start = int(raw_fragment["text_start"])
            end = int(raw_fragment["text_end"])
            fragments.append(
                {
                    "page_id": page["page_id"],
                    "physical_page": page["physical_page"],
                    "text_start": start,
                    "text_end": end,
                    "text": text[start:end],
                    "page_text": text,
                }
            )
        return fragments

    def unit_pages(self, unit_id: str) -> list[int]:
        """Return ordered physical pages touched by one source unit."""
        pages: list[int] = []
        for span_id in self.units[unit_id]["span_ids"]:
            for fragment in self.span_fragments(str(span_id)):
                page = int(fragment["physical_page"])
                if page not in pages:
                    pages.append(page)
        return pages

    def unit_summary(self, unit_id: str, role: str) -> ReviewObject:
        """Build compact metadata plus a deferred full-text URL for one unit."""
        unit = self.units[unit_id]
        return {
            "role": role,
            "unit_id": unit_id,
            "official_label": unit["official_label"],
            "unit_kind": unit["unit_kind"],
            "physical_pages": self.unit_pages(unit_id),
            "full_text_url": f"data/units/{unit_id}.json",
        }

    def full_unit_payload(self, unit_id: str) -> ReviewObject:
        """Build a separately fetched full-text shard for one accepted source unit."""
        unit = self.units[unit_id]
        sections: list[ReviewObject] = []
        for span_id in unit["span_ids"]:
            for fragment in self.span_fragments(str(span_id)):
                sections.append(
                    {
                        "physical_page": fragment["physical_page"],
                        "text": fragment["text"],
                    }
                )
        return {
            "unit_id": unit_id,
            "official_label": unit["official_label"],
            "unit_kind": unit["unit_kind"],
            "sections": sections,
        }

    def context_for_span(self, span_id: str) -> list[ReviewObject]:
        """Return bounded accepted text around a raw mention and lazy render metadata."""
        contexts: list[ReviewObject] = []
        for fragment in self.span_fragments(span_id):
            page_text = str(fragment["page_text"])
            start = int(fragment["text_start"])
            end = int(fragment["text_end"])
            page_number = int(fragment["physical_page"])
            contexts.append(
                {
                    "physical_page": page_number,
                    "before": page_text[max(0, start - _CONTEXT_CHARACTERS) : start],
                    "match": page_text[start:end],
                    "after": page_text[end : end + _CONTEXT_CHARACTERS],
                    "page_image": self._page_image(page_number),
                }
            )
        return contexts

    def unit_start_context(self, unit_id: str) -> ReviewObject:
        """Return bounded start context without eagerly embedding full unit text."""
        unit = self.units[unit_id]
        for span_id in unit["span_ids"]:
            fragments = self.span_fragments(str(span_id))
            if not fragments:
                continue
            fragment = fragments[0]
            page_text = str(fragment["page_text"])
            start = int(fragment["text_start"])
            end = min(int(fragment["text_end"]), start + 350)
            page_number = int(fragment["physical_page"])
            return {
                "physical_page": page_number,
                "before": page_text[max(0, start - _CONTEXT_CHARACTERS) : start],
                "match": page_text[start:end],
                "after": page_text[end : end + _CONTEXT_CHARACTERS],
                "page_image": self._page_image(page_number),
            }
        raise ValueError(f"source unit lacks text-bearing spans: {unit_id}")

    def nearby_units(self, unit_id: str) -> list[ReviewObject]:
        """Identify the two preceding and following units in accepted source order."""
        position = self.unit_positions[unit_id]
        nearby: list[ReviewObject] = []
        for index in range(max(0, position - 2), min(len(self.unit_order), position + 3)):
            neighbor_id = self.unit_order[index]
            if neighbor_id == unit_id:
                continue
            neighbor = self.units[neighbor_id]
            nearby.append(
                {
                    "relative_position": index - position,
                    "official_label": neighbor["official_label"],
                    "unit_kind": neighbor["unit_kind"],
                    "physical_pages": self.unit_pages(neighbor_id),
                }
            )
        return nearby

    def exact_label_units(self, label: str) -> list[str]:
        """Return exact accepted endpoint identities for a label."""
        return sorted(self.labels.get(label, []))

    def _unit_sort_key(self, unit_id: str) -> tuple[int, int, str]:
        """Sort units by first accepted page/text position, then stable identity."""
        unit = self.units[unit_id]
        for span_id in unit["span_ids"]:
            fragments = self.span_fragments(str(span_id))
            if fragments:
                first = fragments[0]
                return int(first["physical_page"]), int(first["text_start"]), unit_id
        return 10**9, 10**9, unit_id

    def _page_image(self, physical_page: int) -> ReviewObject | None:
        row = self.qualification.get(physical_page)
        if row is None or not isinstance(row.get("render_path"), str):
            return None
        render_path = self.render_root / str(row["render_path"])
        if not render_path.is_file():
            return None
        disposition = row.get("visual_disposition")
        status = disposition.get("status") if isinstance(disposition, dict) else None
        return {
            "url": "/" + render_path.relative_to(self.served_root).as_posix(),
            "byte_size": render_path.stat().st_size,
            "review_status": status,
            "load_policy": "explicit_click_only",
        }


def _index(records: list[ReviewObject], record_type: str, key: str) -> dict[str, ReviewObject]:
    selected = {
        str(record[key]): record for record in records if record.get("record_type") == record_type
    }
    if len(selected) != sum(record.get("record_type") == record_type for record in records):
        raise ValueError(f"duplicate or missing {key} in {record_type} records")
    return selected


def _select_review_items(census: ReviewObject, store: _RecordStore) -> list[ReviewObject]:
    """Select only the four bounded populations proposed for pre-Gate-2 review."""
    mention_outcomes = _object_list(census, "mention_outcomes")
    membership_outcomes = _object_list(census, "membership_outcomes")
    policy = census.get("policy")
    items: list[ReviewObject] = []
    for outcome in mention_outcomes:
        source_kind = outcome.get("source_kind")
        reason = outcome.get("reason")
        if source_kind == "general_response" and reason in _GENERAL_RESPONSE_ORIGIN_REASONS:
            items.append({"category": "general_response_origin", "outcome": outcome})
        elif reason == "other_nonexact":
            items.append({"category": "other_nonexact", "outcome": outcome})
        elif reason == "punctuation_variant":
            items.append({"category": "punctuation_variant", "outcome": outcome})
    memberships_are_reviewed = isinstance(policy, dict) and policy.get("typed_membership_suffix")
    if not memberships_are_reviewed:
        for outcome in membership_outcomes:
            target_label = str(outcome["target_label"])
            if len(store.exact_label_units(f"Comment {target_label}")) != 1:
                items.append({"category": "membership_miss", "outcome": outcome})
    terminal_unpaired = (
        policy.get("terminal_unpaired_source_labels", []) if isinstance(policy, dict) else []
    )
    if terminal_unpaired != ["Comment SA-Caltrans-48", "Response SA-Caltrans-48a"]:
        items.append(
            {
                "category": "parent_subanswer",
                "source_label": "Comment SA-Caltrans-48",
                "target_label": "Response SA-Caltrans-48a",
            }
        )
    category_order = {
        "parent_subanswer": 0,
        "membership_miss": 1,
        "general_response_origin": 2,
        "punctuation_variant": 3,
        "other_nonexact": 4,
    }
    return sorted(
        items,
        key=lambda item: (
            category_order[str(item["category"])],
            str(_item_sort_label(item)),
            str(_item_input_id(item)),
        ),
    )


def _object_list(payload: ReviewObject, key: str) -> list[ReviewObject]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"relationship census {key} must be an object array")
    return value


def _item_sort_label(item: ReviewObject) -> str:
    outcome = item.get("outcome")
    if isinstance(outcome, dict):
        return str(outcome.get("target_label", ""))
    return str(item.get("source_label", ""))


def _item_input_id(item: ReviewObject) -> str:
    outcome = item.get("outcome")
    if isinstance(outcome, dict):
        return str(outcome.get("input_id", ""))
    return "caltrans-48"


def _build_item_detail(item_id: str, item: ReviewObject, store: _RecordStore) -> ReviewObject:
    category = str(item["category"])
    if category == "parent_subanswer":
        return _parent_subanswer_detail(item_id, store)
    outcome = item["outcome"]
    assert isinstance(outcome, dict)
    if category == "membership_miss":
        return _membership_detail(item_id, outcome, store)
    return _mention_detail(item_id, category, outcome, store)


def _mention_detail(
    item_id: str, category: str, outcome: ReviewObject, store: _RecordStore
) -> ReviewObject:
    mention_id = str(outcome["input_id"])
    mention = store.mentions[mention_id]
    source_unit_id = str(mention["source_unit_id"])
    target_label = str(outcome["target_label"])
    candidate_ids = _candidate_ids(category, outcome, target_label, store)
    reason = str(outcome["reason"])
    return {
        "item_id": item_id,
        "category": category,
        "category_label": _category_label(category),
        "question": _review_question(category),
        "current_outcome": "Unresolved under the current bounded resolution policy",
        "reason": reason,
        "resolver_rule": outcome["rule"],
        "input_id": mention_id,
        "target_label": target_label,
        "target_label_visible": target_label.replace("\r", "↵").replace("\n", "↵"),
        "source_kind": outcome["source_kind"],
        "contexts": store.context_for_span(str(mention["mention_span_id"])),
        "units": [
            store.unit_summary(source_unit_id, "mention source"),
            *(store.unit_summary(unit_id, "deterministic candidate") for unit_id in candidate_ids),
        ],
        "candidate_summary": _candidate_summary(candidate_ids, category),
        "nearby_units": store.nearby_units(source_unit_id),
        "provenance": {
            "mention_id": mention_id,
            "mention_span_id": mention["mention_span_id"],
            "source_unit_id": source_unit_id,
        },
    }


def _membership_detail(item_id: str, outcome: ReviewObject, store: _RecordStore) -> ReviewObject:
    membership_id = str(outcome["input_id"])
    membership = store.memberships[membership_id]
    source_unit_id = str(membership["general_response_unit_id"])
    target_label = str(outcome["target_label"])
    typed_label = f"Comment {target_label}"
    return {
        "item_id": item_id,
        "category": "membership_miss",
        "category_label": _category_label("membership_miss"),
        "question": _review_question("membership_miss"),
        "current_outcome": (
            "Unresolved under both exact identity and the proposed typed-prefix rule"
        ),
        "reason": outcome["reason"],
        "resolver_rule": outcome["rule"],
        "input_id": membership_id,
        "target_label": target_label,
        "target_label_visible": target_label,
        "source_kind": "general_response",
        "contexts": store.context_for_span(str(membership["mention_span_id"])),
        "units": [store.unit_summary(source_unit_id, "membership source")],
        "candidate_summary": f"No unique accepted comment has official label {typed_label!r}.",
        "nearby_units": store.nearby_units(source_unit_id),
        "provenance": {
            "membership_id": membership_id,
            "mention_span_id": membership["mention_span_id"],
            "general_response_unit_id": source_unit_id,
            "typed_label_tested": typed_label,
        },
    }


def _parent_subanswer_detail(item_id: str, store: _RecordStore) -> ReviewObject:
    comment_ids = store.exact_label_units("Comment SA-Caltrans-48")
    response_ids = store.exact_label_units("Response SA-Caltrans-48a")
    if len(comment_ids) != 1 or len(response_ids) != 1:
        raise ValueError("Caltrans 48/48a review endpoints are not unique")
    comment_id, response_id = comment_ids[0], response_ids[0]
    return {
        "item_id": item_id,
        "category": "parent_subanswer",
        "category_label": _category_label("parent_subanswer"),
        "question": _review_question("parent_subanswer"),
        "current_outcome": "Both units are unpaired; the current policy inferred no relationship",
        "reason": "letter_suffix_requires_human_review",
        "resolver_rule": "exact_typed_label_suffix_v1",
        "input_id": "caltrans-48-parent-subanswer",
        "target_label": "Response SA-Caltrans-48a",
        "target_label_visible": "Response SA-Caltrans-48a",
        "source_kind": "comment",
        "contexts": [
            store.unit_start_context(comment_id),
            store.unit_start_context(response_id),
        ],
        "units": [
            store.unit_summary(comment_id, "unpaired comment"),
            store.unit_summary(response_id, "possible sub-answer"),
        ],
        "candidate_summary": (
            "The labels differ only by the response's trailing 'a', but no general suffix rule "
            "is accepted. Compare the complete units and source pages."
        ),
        "nearby_units": store.nearby_units(comment_id),
        "provenance": {"comment_unit_id": comment_id, "response_unit_id": response_id},
    }


def _candidate_ids(
    category: str, outcome: ReviewObject, target_label: str, store: _RecordStore
) -> list[str]:
    """Expose only deterministic counterfactual identities, never fuzzy suggestions."""
    if outcome.get("reason") == "unsupported_endpoint_kinds":
        return store.exact_label_units(target_label)
    if category != "general_response_origin":
        return []
    collapsed = re.sub(r"\s+", " ", target_label).strip()
    if collapsed.lower().startswith("general response "):
        collapsed = "GENERAL RESPONSE " + collapsed[len("general response ") :]
    return store.exact_label_units(collapsed)


def _candidate_summary(candidate_ids: list[str], category: str) -> str:
    if not candidate_ids:
        return "No deterministic exact or bounded counterfactual endpoint is shown for this case."
    if category == "general_response_origin":
        return (
            "A deterministic endpoint identity exists, but the source/target kind pair is not "
            "represented by the accepted v1 edge vocabulary."
        )
    return "One exact endpoint identity exists but is not compatible with the accepted edge types."


def _category_label(category: str) -> str:
    return {
        "parent_subanswer": "Parent / sub-answer",
        "membership_miss": "Membership miss",
        "general_response_origin": "General Response origin",
        "punctuation_variant": "Punctuation variant",
        "other_nonexact": "Residual nonexact mention",
    }[category]


def _review_question(category: str) -> str:
    return {
        "parent_subanswer": (
            "Does the letter-suffixed response answer the parent comment, and is this only a "
            "document-specific relationship or evidence for a bounded general rule?"
        ),
        "membership_miss": (
            "Is the source membership label truncated or absent, or can it be reconciled to an "
            "accepted comment through a narrow source-supported rule?"
        ),
        "general_response_origin": (
            "Is this a genuine relationship originating in a General Response, and if so which "
            "endpoint kinds must the graph represent?"
        ),
        "punctuation_variant": (
            "Does this single terminal punctuation mark belong outside the response label, and "
            "should that exact punctuation rule be added?"
        ),
        "other_nonexact": (
            "Is this ordinary prose that should remain terminal, or a recurring bounded label "
            "form worth a separately tested rule?"
        ),
    }[category]


def _index_item(detail: ReviewObject) -> ReviewObject:
    source_label = ""
    units = detail["units"]
    assert isinstance(units, list)
    if units and isinstance(units[0], dict):
        source_label = str(units[0]["official_label"])
    contexts = detail["contexts"]
    assert isinstance(contexts, list)
    pages = sorted(
        {int(context["physical_page"]) for context in contexts if isinstance(context, dict)}
    )
    return {
        "item_id": detail["item_id"],
        "category": detail["category"],
        "category_label": detail["category_label"],
        "source_label": source_label,
        "target_label": detail["target_label_visible"],
        "reason": detail["reason"],
        "physical_pages": pages,
        "detail_url": f"data/items/{detail['item_id']}.json",
    }


def _publish(path: Path, payload: ReviewObject) -> None:
    """Write generated cache bytes, refusing to clobber a differing bundle."""
    from er_commons.artifact_io import publish_bytes_no_clobber

    publish_bytes_no_clobber(path, json_bytes(payload))


def _publish_static(output_root: Path) -> None:
    """Copy the small static shell from package resources with no-clobber semantics."""
    from er_commons.artifact_io import publish_bytes_no_clobber

    package = files(_STATIC_PACKAGE)
    for name in ("index.html", "app.js", "styles.css"):
        publish_bytes_no_clobber(output_root / name, package.joinpath(name).read_bytes())


__all__ = ["build_relationship_review_tool"]
