"""Run search → extract → normalize for any connector."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator

from radar.connectors.base import OpportunityConnector
from radar.connectors.errors import ConnectorUnhealthyError
from radar.connectors.types import Opportunity, RawListingRef, SearchParams

logger = logging.getLogger(__name__)


def run_connector_pipeline(
    connector: OpportunityConnector,
    params: SearchParams,
    *,
    on_extraction_error: Callable[[RawListingRef, Exception], None] | None = None,
) -> Iterator[Opportunity]:
    health = connector.health_check()
    if not health.healthy:
        raise ConnectorUnhealthyError(
            health.message or f"{connector.platform} connector is not healthy"
        )

    refs = connector.search(params)
    logger.info("%s search returned %d listing refs", connector.platform, len(refs))

    imported = 0
    skipped = 0
    for ref in refs:
        try:
            raw = connector.extract(ref)
            opportunity = connector.normalize(raw)
            imported += 1
            yield opportunity
        except Exception as exc:
            skipped += 1
            if on_extraction_error is not None:
                on_extraction_error(ref, exc)
            else:
                logger.warning("Skipped %s (%s): %s", ref.external_id, ref.url, exc)

    logger.info(
        "%s pipeline complete: %d imported, %d extraction errors",
        connector.platform,
        imported,
        skipped,
    )
