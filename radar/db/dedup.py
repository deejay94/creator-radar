"""Deduplication checks before inserting opportunities."""

from __future__ import annotations

from dataclasses import dataclass, field

from radar.connectors.types import Opportunity
from radar.db.repository import OpportunityRepository
from radar.db.similarity import descriptions_are_similar, titles_are_similar


@dataclass(frozen=True)
class DedupResult:
    is_duplicate: bool
    reason: str = ""
    matched_external_id: str = ""


@dataclass
class DedupSession:
    """Tracks opportunities seen in the current import run and the database."""

    repo: OpportunityRepository
    _batch_ids: set[tuple[str, str]] = field(default_factory=set)
    _batch_urls: set[str] = field(default_factory=set)
    _batch_opportunities: list[Opportunity] = field(default_factory=list)

    def record(self, opportunity: Opportunity) -> None:
        self._batch_ids.add((opportunity.platform, opportunity.external_id))
        if opportunity.url:
            self._batch_urls.add(opportunity.url)
        self._batch_opportunities.append(opportunity)

    def _check_batch(self, opportunity: Opportunity) -> DedupResult | None:
        key = (opportunity.platform, opportunity.external_id)
        if key in self._batch_ids:
            return DedupResult(True, "batch:platform+external_id", opportunity.external_id)

        if opportunity.url and opportunity.url in self._batch_urls:
            return DedupResult(True, "batch:url")

        for existing in self._batch_opportunities:
            if existing.platform != opportunity.platform:
                continue
            if titles_are_similar(opportunity.title, existing.title):
                return DedupResult(True, "batch:title_similarity", existing.external_id)
            if descriptions_are_similar(opportunity.description, existing.description):
                return DedupResult(
                    True,
                    "batch:description_similarity",
                    existing.external_id,
                )

        return None

    def _check_database(self, opportunity: Opportunity) -> DedupResult | None:
        if self.repo.exists_by_platform_id(opportunity.platform, opportunity.external_id):
            return DedupResult(True, "platform+external_id", opportunity.external_id)

        if opportunity.url and self.repo.exists_by_url(opportunity.url):
            existing = self.repo.get_by_url(opportunity.url)
            matched_id = existing.external_id if existing else ""
            return DedupResult(True, "url", matched_id)

        for existing in self.repo.iter_by_platform(opportunity.platform):
            if titles_are_similar(opportunity.title, existing.title):
                return DedupResult(True, "title_similarity", existing.external_id)
            if descriptions_are_similar(opportunity.description, existing.description):
                return DedupResult(True, "description_similarity", existing.external_id)

        return None


def check_duplicate(opportunity: Opportunity, session: DedupSession) -> DedupResult:
    batch_result = session._check_batch(opportunity)
    if batch_result is not None:
        return batch_result

    database_result = session._check_database(opportunity)
    if database_result is not None:
        return database_result

    return DedupResult(False)


# Backward-compatible helper for tests that only pass a repository.
def check_duplicate_in_repo(opportunity: Opportunity, repo: OpportunityRepository) -> DedupResult:
    return check_duplicate(opportunity, DedupSession(repo=repo))
