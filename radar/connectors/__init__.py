"""Platform connector interface and registry."""

from radar.connectors.base import OpportunityConnector
from radar.connectors.errors import ConnectorError, ConnectorNotReadyError, ConnectorUnhealthyError
from radar.connectors.registry import get_connector, list_platforms
from radar.connectors.types import (
    ConnectorHealth,
    Opportunity,
    RawListing,
    RawListingRef,
    SearchParams,
)

__all__ = [
    "ConnectorError",
    "ConnectorHealth",
    "ConnectorNotReadyError",
    "ConnectorUnhealthyError",
    "Opportunity",
    "OpportunityConnector",
    "RawListing",
    "RawListingRef",
    "SearchParams",
    "get_connector",
    "list_platforms",
]
