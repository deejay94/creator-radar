"""Deduplication checks before inserting opportunities."""

from __future__ import annotations

from dataclasses import dataclass

from radar.connectors.types import Opportunity
from radar.db.repository import OpportunityRepository


@dataclass(frozen=True)
class DedupResult:
    is_duplicate: bool
    reason: str = ""


def check_duplicate(opportunity: Opportunity, repo: OpportunityRepository) -> DedupResult:
    if repo.exists_by_platform_id(opportunity.platform, opportunity.external_id):
        return DedupResult(True, "platform+external_id")

    if opportunity.url and repo.exists_by_url(opportunity.url):
        return DedupResult(True, "url")

    return DedupResult(False)
