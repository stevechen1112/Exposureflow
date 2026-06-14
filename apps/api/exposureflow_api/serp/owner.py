"""Re-classify SERP slot ownership using competitor registry (EF-0505)."""

from __future__ import annotations

from exposureflow_api.exposure.owner_classification import OwnerClassification, classify_url_owner
from exposureflow_api.models import SerpSlot


def apply_owner_classification(
    slot: SerpSlot,
    *,
    site_domain: str,
    competitor_domains: set[str],
) -> OwnerClassification:
    owner = classify_url_owner(
        slot.url,
        site_domain=site_domain,
        competitor_domains=competitor_domains,
    )
    slot.is_own_site = owner.is_own
    slot.is_competitor = owner.is_competitor
    slot.is_third_party = owner.is_third_party
    if owner.domain and not slot.owner_domain:
        slot.owner_domain = owner.domain
    return owner
