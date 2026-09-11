"""Source-free semantic identity and pre-request redirect boundary tests."""

from __future__ import annotations

import pytest

from er_commons.source_release.qualification import (
    PageText,
    QualificationPolicy,
    policy_sha256,
    qualify_pages,
    validate_document_url,
)


@pytest.fixture
def policy() -> QualificationPolicy:
    """Declare exact title variants without observing or fetching a source."""
    return QualificationPolicy(
        advertised_label="Appendix F1 - Transportation Impact Assessment (PDF)",
        accepted_titles=(
            "Transportation Impact Assessment",
            "Appendix F1 - Transportation Impact Assessment",
        ),
        required_internal_phrases=("Existing Traffic Conditions Memo",),
        required_project_phrases=("Brisbane Baylands",),
        edition="final_eir",
        edition_phrases=("Final EIR",),
        expected_document_center_id=2972,
        allowed_hosts=("www.brisbaneca.gov", "brisbaneca.gov"),
        max_pages=20,
    )


def observed_pages(title: str = "Transportation Impact Assessment") -> list[PageText]:
    """Supply bounded observations carrying independent identity requirements."""
    return [
        PageText(physical_page=1, text=f"{title}\nBrisbane Baylands\nFinal EIR"),
        PageText(physical_page=3, text="Contents\nExisting Traffic Conditions Memo"),
    ]


def test_explicit_title_variant_retains_observations(policy: QualificationPolicy) -> None:
    """Typography is allowed while the original observed evidence remains intact."""
    title = " APPENDIX  F1 – Transportation Impact Assessment "
    result = qualify_pages(policy, observed_pages(title))
    assert result.detected_title == title
    assert result.title_page == 1
    assert result.internal_evidence[0].physical_page == 3
    assert result.edition == "final_eir"
    assert result.policy_sha256 == policy_sha256(policy)
    assert result.inspected_pages == (1, 3)


@pytest.mark.parametrize(
    "title",
    [
        "Bayshore Mobility Study",
        "Revised Transportation Impact Assessment",
        "Transportation Impact Assessment Addendum",
        "Not Transportation Impact Assessment",
    ],
)
def test_unapproved_title_is_not_fuzzy_matched(policy: QualificationPolicy, title: str) -> None:
    """A similar phrase or advertised label cannot excuse a different title."""
    with pytest.raises(ValueError, match="title disagreement"):
        qualify_pages(policy, observed_pages(title))


@pytest.mark.parametrize(
    ("removed", "diagnostic"),
    [
        ("Existing Traffic Conditions Memo", "internal"),
        ("Brisbane Baylands", "project"),
        ("Final EIR", "edition"),
    ],
)
def test_each_required_observation_is_mandatory(
    policy: QualificationPolicy, removed: str, diagnostic: str
) -> None:
    """The same title from another project or uncertain edition fails closed."""
    pages = [
        PageText(physical_page=page.physical_page, text=page.text.replace(removed, ""))
        for page in observed_pages()
    ]
    with pytest.raises(ValueError, match=f"missing required {diagnostic}"):
        qualify_pages(policy, pages)


def test_phrase_requires_token_boundaries(policy: QualificationPolicy) -> None:
    """Similar project names cannot satisfy the selected project requirement."""
    pages = observed_pages()
    pages[0] = PageText(physical_page=1, text=pages[0].text.replace("Baylands", "BaylandsExtra"))
    with pytest.raises(ValueError, match="project"):
        qualify_pages(policy, pages)


def test_changed_policy_has_new_identity(policy: QualificationPolicy) -> None:
    """Reuse must bind policy content, including evidence and window changes."""
    changed = QualificationPolicy.model_validate({**policy.model_dump(), "max_pages": 19})
    assert policy_sha256(changed) != policy_sha256(policy)
    assert policy_sha256(QualificationPolicy.model_validate_json(policy.model_dump_json())) == (
        policy_sha256(policy)
    )


@pytest.mark.parametrize("numbers", [[], [1, 1], [3, 1], [21]])
def test_invalid_page_window_rejected(policy: QualificationPolicy, numbers: list[int]) -> None:
    """A caller cannot expand the frozen observation window or duplicate pages."""
    pages = [PageText(physical_page=number, text="") for number in numbers]
    with pytest.raises(ValueError, match="fixed window"):
        qualify_pages(policy, pages)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.brisbaneca.gov/DocumentCenter/View/553/Transportation-Impact-Assessment",
        "http://www.brisbaneca.gov/DocumentCenter/View/2972",
        "https://evil.example/DocumentCenter/View/2972",
        "https://www.brisbaneca.gov:444/DocumentCenter/View/2972",
        "https://user@www.brisbaneca.gov/DocumentCenter/View/2972",
        "https://www.brisbaneca.gov/DocumentCenter/View/29720",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972?documentId=553",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972/../553",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972;id=553",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972/..",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972/.",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972/%2e%2e%2f553",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972/\\553",
        "https://www.brisbaneca.gov/DocumentCenter/View/2972/\n553",
    ],
)
def test_redirect_identity_rejected_before_request(policy: QualificationPolicy, url: str) -> None:
    """Hosts, ports, credentials and document IDs cannot silently change."""
    with pytest.raises(ValueError, match="document URL"):
        validate_document_url(url, policy)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.brisbaneca.gov/DocumentCenter/View/2972",
        "https://brisbaneca.gov/DocumentCenter/View/2972/Transportation-Impact-Assessment-PDF",
    ],
)
def test_same_identity_slug_or_allowed_host_change(policy: QualificationPolicy, url: str) -> None:
    """Slug changes preserve the selected explicit numeric document identity."""
    validate_document_url(url, policy)


def test_title_reference_beyond_cover_window_does_not_qualify(policy: QualificationPolicy) -> None:
    """A later bibliography or TOC title cannot establish the document title."""
    pages = [PageText(physical_page=4, text=observed_pages()[0].text), observed_pages()[1]]
    with pytest.raises(ValueError, match="title disagreement"):
        qualify_pages(policy, sorted(pages, key=lambda page: page.physical_page))


def test_project_must_be_observed_on_title_page(policy: QualificationPolicy) -> None:
    """An unrelated cover cannot borrow project identity from internal references."""
    pages = observed_pages()
    pages[0] = PageText(
        physical_page=1, text=pages[0].text.replace("Brisbane Baylands", "Other Town")
    )
    pages[1] = PageText(physical_page=3, text=pages[1].text + "\nBrisbane Baylands")
    with pytest.raises(ValueError, match="project"):
        qualify_pages(policy, pages)


def test_dense_pages_keep_compact_exact_evidence(policy: QualificationPolicy) -> None:
    """Dense text cannot duplicate full pages into every qualification requirement."""
    text = observed_pages()[0].text + "\n" + "x" * 180_000 + "\nExisting Traffic Conditions Memo"
    result = qualify_pages(policy, [PageText(physical_page=1, text=text)])
    for finding in (*result.internal_evidence, *result.project_evidence, *result.edition_evidence):
        assert finding.observed_text in text
        assert len(finding.observed_text) <= 1000
    assert len(result.model_dump_json()) < 5000


def test_policy_rejects_unbounded_requirements(policy: QualificationPolicy) -> None:
    """The compact receipt contract bounds count and length before acquisition."""
    with pytest.raises(ValueError):
        QualificationPolicy.model_validate({**policy.model_dump(), "accepted_titles": ["x" * 257]})
    with pytest.raises(ValueError):
        QualificationPolicy.model_validate(
            {**policy.model_dump(), "edition_phrases": list("abcdefghi")}
        )
