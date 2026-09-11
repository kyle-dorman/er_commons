"""Pure, fail-closed semantic qualification of bounded source observations."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PolicyText = Annotated[str, StringConstraints(min_length=1, max_length=256)]


class QualificationPolicy(BaseModel):
    """Reviewed source identity requirements; changes invalidate qualification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "source_qualification_policy_v1"
    advertised_label: PolicyText
    accepted_titles: tuple[PolicyText, ...] = Field(min_length=1, max_length=8)
    required_internal_phrases: tuple[PolicyText, ...] = Field(min_length=1, max_length=8)
    required_project_phrases: tuple[PolicyText, ...] = Field(min_length=1, max_length=8)
    edition: PolicyText
    edition_phrases: tuple[PolicyText, ...] = Field(min_length=1, max_length=8)
    expected_document_center_id: int = Field(gt=0)
    allowed_hosts: tuple[PolicyText, ...] = Field(min_length=1, max_length=8)
    max_pages: int = Field(gt=0, le=20)
    title_max_page: int = Field(default=3, gt=0, le=3)

    @model_validator(mode="after")
    def validate_policy(self) -> QualificationPolicy:
        """Reject empty identity requirements and ambiguous host declarations."""
        if self.schema_version != "source_qualification_policy_v1":
            raise ValueError("unsupported source qualification policy schema")
        for name in (
            "accepted_titles",
            "required_internal_phrases",
            "required_project_phrases",
            "edition_phrases",
        ):
            values = [normalize_title(value) for value in getattr(self, name)]
            if any(not value for value in values) or len(values) != len(set(values)):
                raise ValueError(f"{name} must contain distinct nonempty normalized text")
        if any(
            not host or host != host.lower() or re.fullmatch(r"[a-z0-9.-]+", host) is None
            for host in self.allowed_hosts
        ):
            raise ValueError("allowed_hosts must contain plain lowercase host names")
        if self.title_max_page > self.max_pages:
            raise ValueError("title page limit exceeds qualification page window")
        return self


class PageText(BaseModel):
    """Observed extractor text with its one-based physical PDF page."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    physical_page: int = Field(gt=0)
    text: str = Field(max_length=200_000)


class PageEvidence(BaseModel):
    """Exact observed text and the requirement it supports on a physical page."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    physical_page: int = Field(gt=0)
    observed_text: str
    expected_text: str


class QualificationEvidence(BaseModel):
    """Policy-bound semantic findings, independent of advertised metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "source_qualification_evidence_v1"
    policy_sha256: str
    detected_title: str
    edition: str
    title_page: int
    title_evidence: PageEvidence
    internal_evidence: tuple[PageEvidence, ...]
    project_evidence: tuple[PageEvidence, ...]
    edition_evidence: tuple[PageEvidence, ...]
    inspected_pages: tuple[int, ...]


def normalize_title(text: str) -> str:
    """Allow Unicode composition, case, whitespace and dash glyph variants only."""
    normalized = unicodedata.normalize("NFC", text).casefold()
    normalized = "".join("-" if unicodedata.category(char) == "Pd" else char for char in normalized)
    return " ".join(normalized.split())


def policy_sha256(policy: QualificationPolicy) -> str:
    """Bind every explicit semantic requirement without reading source bytes."""
    encoded = json.dumps(policy.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_document_url(url: str, policy: QualificationPolicy) -> None:
    """Require the selected HTTPS Document Center identity before following a hop."""
    if any(ord(char) < 32 for char in url) or "%" in url or "\\" in url:
        raise ValueError("document URL contains ambiguous escaped or control characters")
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError(f"invalid document URL port: {url}") from error
    if (
        parsed.scheme != "https"
        or parsed.hostname not in policy.allowed_hosts
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or parsed.params
        or any(part in (".", "..") for part in parsed.path.split("/"))
    ):
        raise ValueError(f"document URL violates allowed origin/identity policy: {url}")
    match = re.fullmatch(r"/DocumentCenter/View/([1-9][0-9]*)(?:/[^/]+)?/?", parsed.path)
    if match is None or int(match.group(1)) != policy.expected_document_center_id:
        raise ValueError(f"document URL changes selected Document Center identity: {url}")


def _observed_excerpt(text: str, phrase: str) -> str:
    """Retain a small exact source excerpt around the observed required phrase."""
    pieces = re.split(r"\s+", phrase.strip())
    pattern = r"\s+".join(re.escape(piece) for piece in pieces)
    pattern = pattern.replace(r"\-", "[-‐‑‒–—―]")
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        if len(text) <= 1000:
            return text
        raise ValueError("normalized evidence needs an explicit bounded textual disposition")
    if match.end() - match.start() > 800:
        raise ValueError("required evidence spans an excessive whitespace window")
    return text[max(0, match.start() - 100) : min(len(text), match.end() + 100)]


def _phrase_evidence(
    name: str, requirements: tuple[str, ...], pages: list[PageText]
) -> tuple[PageEvidence, ...]:
    """Require every phrase within one page with token boundaries and retain text."""
    findings: list[PageEvidence] = []
    for phrase in requirements:
        pattern = re.compile(r"(?<!\w)" + re.escape(normalize_title(phrase)) + r"(?!\w)")
        for page in pages:
            if pattern.search(normalize_title(page.text)):
                findings.append(
                    PageEvidence(
                        physical_page=page.physical_page,
                        observed_text=_observed_excerpt(page.text, phrase),
                        expected_text=phrase,
                    )
                )
                break
        else:
            raise ValueError(f"missing required {name} evidence: {phrase!r}")
    return tuple(findings)


def qualify_pages(policy: QualificationPolicy, pages: list[PageText]) -> QualificationEvidence:
    """Accept only explicit title, project, internal and edition text in the window."""
    numbers = [page.physical_page for page in pages]
    if (
        not pages
        or len(pages) > policy.max_pages
        or len(numbers) != len(set(numbers))
        or numbers != sorted(numbers)
        or any(number > policy.max_pages for number in numbers)
    ):
        raise ValueError("qualification pages must be ordered, unique and within the fixed window")
    accepted = {normalize_title(title): title for title in policy.accepted_titles}
    title_evidence = None
    for page in pages:
        if page.physical_page > policy.title_max_page:
            continue
        for line in page.text.splitlines():
            expected = accepted.get(normalize_title(line))
            if expected is not None:
                if len(line) > 1000:
                    raise ValueError("title line exceeds bounded evidence limit")
                title_evidence = PageEvidence(
                    physical_page=page.physical_page, observed_text=line, expected_text=expected
                )
                break
        if title_evidence is not None:
            break
    if title_evidence is None:
        raise ValueError(
            "title disagreement: no exact permitted title line in qualification window"
        )
    return QualificationEvidence(
        policy_sha256=policy_sha256(policy),
        detected_title=title_evidence.observed_text,
        edition=policy.edition,
        title_page=title_evidence.physical_page,
        title_evidence=title_evidence,
        internal_evidence=_phrase_evidence("internal", policy.required_internal_phrases, pages),
        project_evidence=_phrase_evidence(
            "project",
            policy.required_project_phrases,
            [page for page in pages if page.physical_page == title_evidence.physical_page],
        ),
        edition_evidence=_phrase_evidence("edition", policy.edition_phrases, pages),
        inspected_pages=tuple(numbers),
    )
