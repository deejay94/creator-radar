"""Import opportunities from a connector into SQLite."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from radar.connectors.base import OpportunityConnector
from radar.connectors.pipeline import run_connector_pipeline
from radar.connectors.types import Opportunity, RawListingRef, SearchParams
from radar.db.dedup import DedupSession, check_duplicate
from radar.db.repository import OpportunityRepository
from radar.opportunity_filters import get_male_only_creator_filter_reason

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    searched: int = 0
    imported: int = 0
    duplicates: int = 0
    filtered: int = 0
    extraction_errors: int = 0


def import_opportunities(
    connector: OpportunityConnector,
    params: SearchParams,
    repo: OpportunityRepository,
) -> ImportStats:
    stats = ImportStats()
    dedup_session = DedupSession(repo=repo)

    def on_extraction_error(ref: RawListingRef, exc: Exception) -> None:
        stats.extraction_errors += 1
        logger.warning(
            "Extraction error (%s %s): %s",
            connector.platform,
            ref.external_id,
            exc,
        )

    for opportunity in run_connector_pipeline(
        connector,
        params,
        on_extraction_error=on_extraction_error,
    ):
        stats.searched += 1

        filter_reason = get_male_only_creator_filter_reason(opportunity)
        if filter_reason:
            stats.filtered += 1
            logger.info(
                "Filtered (%s): %s — %s",
                filter_reason,
                opportunity.external_id,
                opportunity.title[:80],
            )
            continue

        dedup = check_duplicate(opportunity, dedup_session)
        if dedup.is_duplicate:
            stats.duplicates += 1
            matched = f" (matches {dedup.matched_external_id})" if dedup.matched_external_id else ""
            logger.info(
                "Duplicate skipped (%s)%s: %s — %s",
                dedup.reason,
                matched,
                opportunity.external_id,
                opportunity.title[:80],
            )
            continue

        row_id = repo.insert(opportunity)
        dedup_session.record(opportunity)
        stats.imported += 1
        logger.info(
            "Imported %s opportunity id=%d external_id=%s title=%s",
            opportunity.platform,
            row_id,
            opportunity.external_id,
            opportunity.title[:80],
        )

    return stats
