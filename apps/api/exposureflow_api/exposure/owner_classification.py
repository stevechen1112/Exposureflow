"""Classify URL ownership against site domain and competitor registry."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

FORUM_DOMAINS = {
    "reddit.com",
    "quora.com",
    "dcard.tw",
    "ptt.cc",
    "mobile01.com",
    "stackexchange.com",
    "stackoverflow.com",
}


@dataclass(frozen=True)
class OwnerClassification:
    owner_type: str
    domain: str | None
    is_own: bool
    is_competitor: bool
    is_third_party: bool


def _normalize_domain(domain: str) -> str:
    return domain.lower().removeprefix("www.").strip()


def _url_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    return host or None


def _matches_domain(host: str, registered: str) -> bool:
    reg = _normalize_domain(registered)
    return host == reg or host.endswith(f".{reg}")


def classify_url_owner(
    url: str | None,
    *,
    site_domain: str,
    competitor_domains: set[str] | None = None,
) -> OwnerClassification:
    """Return owner_type: owned | competitor | third_party | unknown."""
    host = _url_domain(url)
    if host is None:
        return OwnerClassification(
            owner_type="unknown",
            domain=None,
            is_own=False,
            is_competitor=False,
            is_third_party=False,
        )

    site = _normalize_domain(site_domain)
    if _matches_domain(host, site):
        return OwnerClassification(
            owner_type="owned",
            domain=host,
            is_own=True,
            is_competitor=False,
            is_third_party=False,
        )

    competitors = competitor_domains or set()
    for competitor in competitors:
        if _matches_domain(host, competitor):
            return OwnerClassification(
                owner_type="competitor",
                domain=host,
                is_own=False,
                is_competitor=True,
                is_third_party=False,
            )

    if host in FORUM_DOMAINS or any(host.endswith(f".{d}") for d in FORUM_DOMAINS):
        return OwnerClassification(
            owner_type="third_party",
            domain=host,
            is_own=False,
            is_competitor=False,
            is_third_party=True,
        )

    return OwnerClassification(
        owner_type="unknown",
        domain=host,
        is_own=False,
        is_competitor=False,
        is_third_party=False,
    )


async def load_competitor_domains(
    db,
    workspace_id,
    site_id,
) -> set[str]:
    from sqlalchemy import select

    from exposureflow_api.models import Competitor

    result = await db.execute(
        select(Competitor).where(
            Competitor.workspace_id == workspace_id,
            Competitor.site_id == site_id,
            Competitor.active.is_(True),
        )
    )
    domains: set[str] = set()
    for row in result.scalars().all():
        domains.add(_normalize_domain(row.domain))
        for alias in row.aliases_json or []:
            if isinstance(alias, str) and alias.strip():
                domains.add(_normalize_domain(alias))
    return domains
