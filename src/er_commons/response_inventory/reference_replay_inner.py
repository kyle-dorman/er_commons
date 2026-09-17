"""Conservative compound appendix references using existing exact target aliases only."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from er_commons.document_records.document_structure.normalization import normalize_alias

type JsonObject = dict[str, Any]

# A whole identifier token is essential: ordinary prose such as "table are"
# must never become "Table A". Numbering punctuation stays significant.
_IDENTIFIER = r"(?:[a-z]-)?\d+[a-z]?(?:[.\-][a-z0-9]+)*|[a-z](?:[.\-]\d+)*"
_IDENTIFIER_END = r"(?![\w\-]|\.[\w])"
_REFERENCE = re.compile(
    rf"\b(?P<kind>chapter|section|table|figure|page|appendix)\s+"
    rf"(?P<identifier>{_IDENTIFIER}){_IDENTIFIER_END}",
    re.I,
)
_NAMED_SECTION = re.compile(r'\bsection\s+titled\s+[“"](?P<title>[^”"]+)[”"]', re.I)
_RELATION = re.compile(
    r"^(?:,\s*)?(?:(?:which\s+)?was\s+(?:included\s+in|provided\s+as)|"
    r"(?:of|to|in)(?:\s+the\s+[^(),;]+)?)\s*\(?\s*$",
    re.I,
)
_TYPES = {
    "chapter": "section",
    "section": "section",
    "appendix": "section",
    "table": "table",
    "page": "page",
}


class MentionContext(Protocol):
    """Structural interface to bounded same-sentence mention context."""

    @property
    def before(self) -> str:
        """Read context before the mention."""
        ...

    @property
    def after(self) -> str:
        """Read context after the mention."""
        ...


@dataclass(frozen=True)
class InnerProposal:
    """Return exact options; only one distinct target is eligible for selection."""

    specific: bool
    requested_type: str | None = None
    candidates: tuple[JsonObject, ...] = ()
    rule: str | None = None
    evidence: tuple[str, ...] = ()
    unverified_page_qualifier: bool = False

    @property
    def selected(self) -> JsonObject | None:
        """Never choose one member of an ambiguous candidate population."""
        return self.candidates[0] if len(self.candidates) == 1 else None


def _normalize_title(value: str) -> str:
    """Ignore title boundary punctuation, retaining words and internal punctuation."""
    return normalize_alias(value).strip(' \t.,:;|–—-"“”')


def _unique(rows: Iterable[JsonObject]) -> tuple[JsonObject, ...]:
    """Collapse alternate aliases for the same target without collapsing identities."""
    by_id: dict[str, JsonObject] = {}
    for row in sorted(rows, key=lambda row: (str(row["target_id"]), str(row["lookup_key"]))):
        by_id.setdefault(str(row["target_id"]), row)
    return tuple(by_id[key] for key in sorted(by_id))


def _alias_parts(row: JsonObject, kind: str) -> tuple[str, str] | None:
    """Read a published leading identifier and title without manufacturing aliases."""
    key = normalize_alias(str(row["lookup_key"]))
    prefix = r"(?:chapter\s+|section\s+)?" if kind in {"chapter", "section"} else kind + r"\s+"
    match = re.match(rf"^{prefix}(?P<identifier>{_IDENTIFIER}){_IDENTIFIER_END}(?P<title>.*)$", key)
    # A title delimiter period ("5. Project Demand") is not subsection numbering.
    if match is None:
        match = re.match(rf"^{prefix}(?P<identifier>{_IDENTIFIER})\.(?=\s)(?P<title>.*)$", key)
    if match is None:
        return None
    return match["identifier"], _normalize_title(match["title"])


def _attached_tail(tail: str) -> tuple[bool, str | None]:
    """Recognize direct source attachment, optionally through one complete title."""
    if _RELATION.fullmatch(tail.strip()):
        return True, None
    # Exact comma-delimited titles, including the ordinary "which was provided"
    # construction, can disambiguate numbered sections without semantic guessing.
    match = re.fullmatch(r",\s*(?P<title>[^,;]+),\s*(?P<relation>.+)", tail.strip())
    if match and _RELATION.fullmatch(match["relation"]):
        title = match["title"]
        # A page qualification is evidence to preserve, not an inferred page alias.
        title = re.sub(r"\s*\(page\s+[^)]+\)\s*$", "", title, flags=re.I)
        return True, _normalize_title(title)
    return False, None


def _separately_qualified(text: str, match: re.Match[str]) -> bool:
    """Recognize an independently edition-qualified citation before another target."""
    return (
        re.search(r"\b(?:draft|final)\s+(?:eir|report)\s*$", text[: match.start()], re.I)
        is not None
    )


def propose_inner(
    context: MentionContext,
    routed_sources: Iterable[str],
    target_rows: Sequence[JsonObject],
) -> InnerProposal:
    """Resolve explicit attached inner references; unsupported specificity stays blocked.

    Only exact source-scoped published section/table aliases participate. Figures,
    unqualified pages, range references, and compound targets stay unresolved.
    A named section can be identified independently of an accompanying page claim;
    that claim is returned as unverified and must not be represented as verified.
    """
    before = " ".join(context.before.split())
    after = " ".join(context.after.split())
    before_refs = list(_REFERENCE.finditer(before))
    after_refs = list(_REFERENCE.finditer(after))
    references = before_refs + after_refs
    named = list(_NAMED_SECTION.finditer(before))
    named_after = list(_NAMED_SECTION.finditer(after))
    plural = re.search(
        rf"\b(?:chapters|sections|tables|figures|pages|appendices)\s+(?:{_IDENTIFIER}){_IDENTIFIER_END}",
        before + " " + after,
        re.I,
    )
    specific = bool(references or named or named_after or plural)
    if plural or named_after:
        return InnerProposal(True, evidence=("unsupported_compound_specificity",))
    sources = set(routed_sources)
    scoped = [row for row in target_rows if row.get("source_id") in sources]
    if named:
        if len(named) != 1:
            return InnerProposal(True, evidence=("multiple_named_sections",))
        name = named[0]
        tail = before[name.end() :].strip()
        page = re.fullmatch(r",?\s*on\s+page\s+\d+(?:-\d+)?\s+of", tail, re.I)
        if not page and not _RELATION.fullmatch(tail):
            return InnerProposal(True, evidence=("unattached_named_section",))
        # Additional non-page citations cannot be silently discarded.
        expected_pages = 1 if page else 0
        if (
            after_refs
            or len(before_refs) != expected_pages
            or any(
                match["kind"].lower() != "page" or match.start() < name.end()
                for match in before_refs
            )
        ):
            return InnerProposal(True, evidence=("multiple_inner_references",))
        named_title = _normalize_title(name["title"])
        candidates = _unique(
            row
            for row in scoped
            if row.get("target_type") == "section"
            and _normalize_title(str(row["lookup_key"])) == named_title
        )
        return InnerProposal(
            specific=True,
            requested_type="section",
            candidates=candidates,
            rule="task05g_exact_inner_title_v1",
            evidence=(name.group(),),
            unverified_page_qualifier=bool(page),
        )
    # A following explicit page citation uses only a pre-qualified exact page alias.
    if (
        len(after_refs) == 1
        and after_refs[0]["kind"].lower() == "page"
        and not list(_REFERENCE.finditer(before))
    ):
        page_ref = after_refs[0]
        prefix = after[: page_ref.start()]
        if re.fullmatch(r",(?:[^,;]+,)?\s*", prefix):
            key = "page " + page_ref["identifier"].lower()
            candidates = _unique(
                row
                for row in scoped
                if row.get("target_type") == "page"
                and normalize_alias(str(row["lookup_key"])) == key
            )
            return InnerProposal(
                specific=True,
                requested_type="page",
                candidates=candidates,
                rule="task05g_exact_inner_page_v1",
                evidence=(page_ref.group(),),
            )
    # Numbered tables inside a named nested appendix require explicit ancestry.
    nested = re.search(
        rf"\btable\s+(?P<table>{_IDENTIFIER})\s+of\s+appendix\s+(?P<appendix>[a-z])\s+to\s*$",
        before,
        re.I,
    )
    if nested:
        if after_refs or any(
            match.start() < nested.start() and not _separately_qualified(before, match)
            for match in before_refs
        ):
            return InnerProposal(True, evidence=("multiple_inner_references",))
        candidates = _unique(
            row
            for row in scoped
            if row.get("target_type") == "table"
            and (
                row.get("inner_appendix_identifier") == nested["appendix"].lower()
                or str(row.get("inner_appendix_identifier", "")).startswith(
                    nested["appendix"].lower() + "."
                )
            )
            and (parts := _alias_parts(row, "table")) is not None
            and parts[0] == nested["table"].lower()
        )
        return InnerProposal(
            specific=True,
            requested_type="table",
            candidates=candidates,
            rule="task05g_exact_nested_table_v1",
            evidence=(nested.group(),),
        )
    attached: list[tuple[re.Match[str], str | None]] = []
    for match in _REFERENCE.finditer(before):
        valid, title = _attached_tail(before[match.end() :])
        if valid:
            attached.append((match, title))
    if len(attached) != 1:
        return InnerProposal(
            specific, evidence=("no_unique_attached_reference",) if specific else ()
        )
    match, title = attached[0]
    kind = match["kind"].lower()
    if after_refs or any(
        other.start() != match.start() and not _separately_qualified(before, other)
        for other in before_refs
    ):
        return InnerProposal(True, evidence=("multiple_inner_references",))
    requested = _TYPES.get(kind)
    # "Table X of Appendix Y to <outer>" refers to the table, not Appendix Y.
    preceding = before[: match.start()]
    if kind == "appendix" and re.search(
        r"\b(?:table|figure|section|chapter|page)\s+.*\bof\s*$", preceding, re.I
    ):
        return InnerProposal(True, evidence=("nested_specific_target_requires_resolution",))
    if requested is None:
        return InnerProposal(True, evidence=("unsupported_inner_target_type", match.group()))
    identifier = match["identifier"].lower()
    numbered_candidates: list[JsonObject] = []
    for row in scoped:
        if row.get("target_type") != requested:
            continue
        parts = _alias_parts(row, kind)
        if parts is not None and parts[0] == identifier and (title is None or parts[1] == title):
            numbered_candidates.append(row)
    return InnerProposal(
        specific=True,
        requested_type=requested,
        candidates=_unique(numbered_candidates),
        rule="task05g_exact_inner_identifier_v1",
        evidence=(match.group(),) + ((title,) if title else ()),
    )
