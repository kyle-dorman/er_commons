"""Pure assessment of a reviewed exception against retained PDF observations.

The caller verifies the compact evidence references before supplying observations.
This module never opens source bytes, repairs a PDF, or publishes a completion.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from er_commons.source_release.qualification import PageText, PolicyText, normalize_title

Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class _Record(BaseModel):
    """Reject undeclared fields in immutable disposition inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ThumbnailException(_Record):
    """One reviewed failing stream and its exact thumbnail reference path."""

    object_id: int = Field(gt=0)
    generation: int = Field(ge=0)
    physical_page: int = Field(gt=0)
    reference_path: PolicyText


class RetainedQualificationPolicy(_Record):
    """Versioned exception bound to one source and finite retained evidence."""

    schema_version: Literal["retained_qualification_policy_v1"]
    source_sha256: Digest
    page_count: int = Field(gt=0)
    exceptions: tuple[ThumbnailException, ...] = Field(min_length=1, max_length=8)
    diagnostic_refs: tuple[PolicyText, ...] = Field(min_length=1, max_length=16)
    cover_page: int = Field(gt=0)
    cover_title: PolicyText
    project_phrase: PolicyText
    edition_phrase: PolicyText
    corroboration_page: int = Field(gt=0)
    corroboration_title: PolicyText
    memo_phrase: PolicyText
    memo_heading_page: int = Field(gt=0)
    memo_body_page: int = Field(gt=0)
    memo_body_phrases: tuple[PolicyText, ...] = Field(min_length=1, max_length=8)
    allowed_pages: tuple[int, ...] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def validate_scope(self) -> RetainedQualificationPolicy:
        """Keep page scope finite, unique and sufficient for declared title checks."""
        if tuple(sorted(set(self.allowed_pages))) != self.allowed_pages or any(
            page < 1 or page > self.page_count for page in self.allowed_pages
        ):
            raise ValueError("allowed pages must be ordered, unique and within source")
        if any(
            page not in self.allowed_pages
            for page in (
                self.cover_page,
                self.corroboration_page,
                self.memo_heading_page,
                self.memo_body_page,
            )
        ):
            raise ValueError("title evidence pages must belong to allowed pages")
        keys = [(item.object_id, item.generation) for item in self.exceptions]
        if len(set(keys)) != len(keys) or any(
            item.physical_page > self.page_count for item in self.exceptions
        ):
            raise ValueError("exception streams must be unique and within source")
        if len(set(self.diagnostic_refs)) != len(self.diagnostic_refs):
            raise ValueError("diagnostic references must be unique")
        for text in (
            self.cover_title,
            self.project_phrase,
            self.edition_phrase,
            self.corroboration_title,
            self.memo_phrase,
            *self.memo_body_phrases,
            *self.diagnostic_refs,
        ):
            if not normalize_title(text):
                raise ValueError("evidence requirements must not be blank")
        return self


class RetainedQualificationObservations(_Record):
    """Observed retained facts; no assertion here changes the original failure."""

    source_sha256: Digest
    page_count: int = Field(gt=0)
    diagnostic_refs: tuple[PolicyText, ...]
    structural_failures: tuple[ThumbnailException, ...]
    non_thumbnail_references: tuple[PolicyText, ...]
    rendered_body_pages: tuple[int, ...]
    pages: tuple[PageText, ...]


class QualificationDimension(_Record):
    """A separately reportable acceptance dimension with physical-page evidence."""

    status: Literal["pass", "fail"]
    reason: str
    physical_pages: tuple[int, ...] = ()


class RetainedQualificationDisposition(_Record):
    """Policy-bound result; qualification requires every independent check to pass."""

    schema_version: Literal["retained_qualification_disposition_v1"] = (
        "retained_qualification_disposition_v1"
    )
    policy_sha256: Digest
    source_sha256: Digest
    qualified: bool
    dimensions: dict[str, QualificationDimension]
    limitation: str = (
        "The reviewed thumbnail exception and bounded observations "
        "do not establish all-page decoder completeness."
    )


def _contains(text: str, phrase: str) -> bool:
    """Match normalized phrases with word boundaries, including split-line titles."""
    return (
        re.search(
            r"(?<!\w)" + re.escape(normalize_title(phrase)) + r"(?!\w)",
            normalize_title(text),
        )
        is not None
    )


def _dimension(passed: bool, reason: str, pages: tuple[int, ...] = ()) -> QualificationDimension:
    """Make status explicit without throwing away other independent findings."""
    return QualificationDimension(
        status="pass" if passed else "fail", reason=reason, physical_pages=pages
    )


def assess_retained_qualification(
    policy: RetainedQualificationPolicy,
    observed: RetainedQualificationObservations,
) -> RetainedQualificationDisposition:
    """Assess exact reviewed exceptions and text without source or filesystem access."""
    numbers = tuple(page.physical_page for page in observed.pages)
    scope_ok = numbers == policy.allowed_pages
    pages = {page.physical_page: page.text for page in observed.pages}
    cover = pages.get(policy.cover_page, "")
    corroboration = pages.get(policy.corroboration_page, "")
    identity_ok = (
        observed.source_sha256 == policy.source_sha256 and observed.page_count == policy.page_count
    )
    structure_ok = (
        observed.structural_failures == policy.exceptions
        and observed.diagnostic_refs == policy.diagnostic_refs
        and not observed.non_thumbnail_references
        and set(observed.rendered_body_pages) == {item.physical_page for item in policy.exceptions}
    )
    title_ok = (
        any(
            normalize_title(line) == normalize_title(policy.cover_title)
            for line in cover.splitlines()
        )
        and _contains(cover, policy.project_phrase)
        and _contains(corroboration, policy.corroboration_title)
    )
    memo_ok = _contains(pages.get(policy.memo_heading_page, ""), policy.memo_phrase) and all(
        _contains(pages.get(policy.memo_body_page, ""), phrase)
        for phrase in policy.memo_body_phrases
    )
    memo_pages = (policy.memo_heading_page, policy.memo_body_page) if memo_ok else ()
    dimensions = {
        "identity": _dimension(
            identity_ok, "Exact retained stream digest and page count must match."
        ),
        "evidence_scope": _dimension(
            scope_ok, "Observed pages must equal the frozen ordered page set.", numbers
        ),
        "structure": _dimension(
            structure_ok,
            "Exact thumbnail failures, diagnostic references and rendered bodies required.",
        ),
        "title": _dimension(
            title_ok,
            "Exact cover line, same-page project and split-line report title required.",
            (policy.cover_page, policy.corroboration_page),
        ),
        "edition": _dimension(
            _contains(cover, policy.edition_phrase),
            "Cover must contain the declared edition.",
            (policy.cover_page,),
        ),
        "internal": _dimension(
            bool(memo_pages),
            "Required memo phrase must be observed; absence is not waived.",
            memo_pages,
        ),
    }
    encoded = json.dumps(policy.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return RetainedQualificationDisposition(
        policy_sha256=hashlib.sha256(encoded.encode()).hexdigest(),
        source_sha256=observed.source_sha256,
        qualified=all(item.status == "pass" for item in dimensions.values()),
        dimensions=dimensions,
    )
