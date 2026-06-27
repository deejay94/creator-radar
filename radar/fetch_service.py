"""Fetch eligible opportunities for worker notifications."""

from __future__ import annotations

import logging

from radar.connectors.base import OpportunityConnector
from radar.connectors.pipeline import run_connector_pipeline
from radar.connectors.types import Opportunity, RawListingRef, SearchParams
from radar.opportunity_filters import get_male_only_creator_filter_reason

logger = logging.getLogger(__name__)


def fetch_eligible_opportunities(
    connector: OpportunityConnector,
    params: SearchParams,
) -> list[Opportunity]:
    opportunities: list[Opportunity] = []

    def on_extraction_error(ref: RawListingRef, exc: Exception) -> None:
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
        filter_reason = get_male_only_creator_filter_reason(opportunity)
        if filter_reason:
            logger.info(
                "Filtered (%s): %s — %s",
                filter_reason,
                opportunity.external_id,
                opportunity.title[:80],
            )
            continue
        opportunities.append(opportunity)

    return opportunities
