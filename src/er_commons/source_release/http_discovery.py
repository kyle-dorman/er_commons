"""Bounded HTTP setup and authoritative landing-page reconciliation."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from er_commons.artifact_io import sha256_bytes
from er_commons.source_release.models import (
    DiscoveredLink,
    LandingPageRecord,
    RedirectRecord,
    ReleaseSpec,
)

ALLOWED_SOURCE_HOSTS = {"brisbaneca.gov", "www.brisbaneca.gov"}
HEADER_NAMES = (
    "Content-Type",
    "Content-Length",
    "Content-Encoding",
    "Content-Disposition",
    "ETag",
    "Last-Modified",
    "Date",
)


class HttpSession(Protocol):
    """Small session boundary needed by source acquisition."""

    def get(self, url: str, **kwargs: Any) -> requests.Response: ...

    def close(self) -> None: ...


def build_http_session() -> requests.Session:
    """Create the bounded, GET-only retrying HTTP session."""
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=(429, 500, 502, 503, 504),
        backoff_factor=1.0,
        backoff_jitter=0.25,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.headers["User-Agent"] = "er-commons-source-freeze/0.1"
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def selected_headers(response: requests.Response) -> dict[str, str]:
    """Preserve useful delivered HTTP response metadata."""
    return {name: response.headers[name] for name in HEADER_NAMES if name in response.headers}


def redirect_history(response: requests.Response) -> list[RedirectRecord]:
    """Preserve ordered HTTP redirect provenance."""
    return [
        RedirectRecord(
            status_code=item.status_code,
            url=item.url,
            location=item.headers.get("Location"),
        )
        for item in response.history
    ]


def ensure_allowed_url(url: str) -> None:
    """Reject unexpected schemes or redirect hosts."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
        raise ValueError(f"unexpected source URL: {url}")


def parse_document_links(content: bytes, page_url: str) -> list[DiscoveredLink]:
    """Parse ordered City Document Center links with Beautiful Soup."""
    links: list[DiscoveredLink] = []
    seen_ids: set[int] = set()
    soup = BeautifulSoup(content, "html.parser")
    for position, anchor in enumerate(
        soup.select('a[href*="/DocumentCenter/View/"]'),
        start=1,
    ):
        href = str(anchor.get("href", ""))
        match = re.search(r"/DocumentCenter/View/(\d+)", href)
        if not match:
            continue
        document_id = int(match.group(1))
        if document_id in seen_ids:
            raise ValueError(f"duplicate Document Center ID {document_id} on {page_url}")
        seen_ids.add(document_id)
        links.append(
            DiscoveredLink(
                document_center_id=document_id,
                label=" ".join(anchor.get_text(" ", strip=True).split()),
                linked_url=urljoin(page_url, href),
                position=position,
            )
        )
    return links


def fetch_and_reconcile_pages(
    session: HttpSession,
    spec: ReleaseSpec,
    data_root: Path,
    release_root: Path,
    *,
    clock: Callable[[], str],
) -> tuple[list[LandingPageRecord], dict[str, dict[int, DiscoveredLink]], dict[str, bytes]]:
    """Fetch pages and stop unless every live document link is accounted for."""
    records: list[LandingPageRecord] = []
    discoveries: dict[str, dict[int, DiscoveredLink]] = {}
    contents: dict[str, bytes] = {}
    selected_by_page = {
        page.key: {
            source.document_center_id
            for source in spec.sources
            if source.landing_page_key == page.key
        }
        for page in spec.landing_pages
    }
    for page in spec.landing_pages:
        ensure_allowed_url(page.url)
        response = session.get(page.url, timeout=(10, 60))
        response.raise_for_status()
        ensure_allowed_url(response.url)
        content = response.content
        links = parse_document_links(content, page.url)
        discovered_ids = {link.document_center_id for link in links}
        expected_ids = selected_by_page[page.key] | set(page.expected_excluded_document_ids)
        if discovered_ids != expected_ids:
            raise ValueError(
                f"landing-page inventory changed for {page.key}: "
                f"missing={sorted(expected_ids - discovered_ids)}, "
                f"unexpected={sorted(discovered_ids - expected_ids)}"
            )
        local_path = release_root / "landing_pages" / page.snapshot_filename
        records.append(
            LandingPageRecord(
                key=page.key,
                linked_url=page.url,
                final_resolved_url=response.url,
                access_timestamp_utc=clock(),
                http_status=response.status_code,
                response_headers=selected_headers(response),
                redirect_history=redirect_history(response),
                local_path=local_path.relative_to(data_root).as_posix(),
                sha256=sha256_bytes(content),
                byte_size=len(content),
                discovered_document_ids=sorted(discovered_ids),
                excluded_document_ids=page.expected_excluded_document_ids,
            )
        )
        discoveries[page.key] = {link.document_center_id: link for link in links}
        contents[page.key] = content
    _validate_labels(spec, discoveries)
    return records, discoveries, contents


def _validate_labels(
    spec: ReleaseSpec,
    discoveries: dict[str, dict[int, DiscoveredLink]],
) -> None:
    for source in spec.sources:
        discovered = discoveries[source.landing_page_key][source.document_center_id]
        if discovered.label != source.expected_label:
            raise ValueError(
                f"link label changed for {source.source_id}: "
                f"expected={source.expected_label!r}, found={discovered.label!r}"
            )


__all__ = [
    "HttpSession",
    "build_http_session",
    "ensure_allowed_url",
    "fetch_and_reconcile_pages",
    "parse_document_links",
    "redirect_history",
    "selected_headers",
]
