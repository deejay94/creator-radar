"""Upwork OpportunityConnector implementation."""

from __future__ import annotations

import logging

from radar.connectors.base import OpportunityConnector
from radar.connectors.types import (
    ConnectorHealth,
    Opportunity,
    RawListing,
    RawListingRef,
    SearchParams,
)
from radar.upwork.auth import check_status
from radar.upwork.browser_session import UpworkBrowserSession
from radar.upwork.config import DEFAULT_SEARCH_QUERIES
from radar.upwork.errors import UpworkAuthError
from radar.upwork.normalize import normalize_upwork_listing
from radar.upwork.scraper import extract_job, search_jobs

logger = logging.getLogger(__name__)


class UpworkConnector(OpportunityConnector):
    def __init__(self, *, headed: bool = True) -> None:
        self._headed = headed
        self._browser_session: UpworkBrowserSession | None = None

    @property
    def platform(self) -> str:
        return "upwork"

    def _context(self):
        if self._browser_session is None:
            self._browser_session = UpworkBrowserSession()
            self._browser_session.open(headed=self._headed)
        return self._browser_session.context

    def close(self) -> None:
        if self._browser_session is not None:
            self._browser_session.close()
            self._browser_session = None

    def health_check(self) -> ConnectorHealth:
        try:
            status = check_status()
        except UpworkAuthError as exc:
            return ConnectorHealth(
                healthy=False,
                status="error",
                display_name=None,
                message=str(exc),
            )

        if status.authenticated:
            return ConnectorHealth(
                healthy=True,
                status="authenticated",
                display_name=status.display_name,
                message=status.message,
            )

        return ConnectorHealth(
            healthy=False,
            status="reauthentication required",
            display_name=None,
            message=status.message,
        )

    def search(self, params: SearchParams) -> list[RawListingRef]:
        queries = params.queries or DEFAULT_SEARCH_QUERIES
        debug = bool(params.extras.get("debug"))
        all_refs: list[RawListingRef] = []
        seen_ids: set[str] = set()

        for query in queries:
            refs = search_jobs(
                self._context(),
                query,
                params.limit_per_query,
                debug=debug,
            )
            logger.info("Search query %r: %d jobs found", query, len(refs))
            for ref in refs:
                if ref.external_id in seen_ids:
                    continue
                seen_ids.add(ref.external_id)
                all_refs.append(ref)

        logger.info("Total unique jobs across queries: %d", len(all_refs))
        return all_refs

    def extract(self, ref: RawListingRef) -> RawListing:
        return extract_job(self._context(), ref)

    def normalize(self, raw: RawListing) -> Opportunity:
        return normalize_upwork_listing(raw)
