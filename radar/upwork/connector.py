"""Upwork OpportunityConnector implementation."""

from __future__ import annotations

from radar.connectors.base import OpportunityConnector
from radar.connectors.errors import ConnectorNotReadyError
from radar.connectors.types import (
    ConnectorHealth,
    Opportunity,
    RawListing,
    RawListingRef,
    SearchParams,
)
from radar.upwork.auth import check_status
from radar.upwork.errors import UpworkAuthError

_STEP2_MESSAGE = "Upwork search/extract/normalize are available in Step 2."


class UpworkConnector(OpportunityConnector):
    @property
    def platform(self) -> str:
        return "upwork"

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
        raise ConnectorNotReadyError(_STEP2_MESSAGE)

    def extract(self, ref: RawListingRef) -> RawListing:
        raise ConnectorNotReadyError(_STEP2_MESSAGE)

    def normalize(self, raw: RawListing) -> Opportunity:
        raise ConnectorNotReadyError(_STEP2_MESSAGE)
