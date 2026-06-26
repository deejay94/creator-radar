"""OpportunityConnector interface for all platform sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from radar.connectors.types import (
    ConnectorHealth,
    Opportunity,
    RawListing,
    RawListingRef,
    SearchParams,
)


class OpportunityConnector(ABC):
    @property
    @abstractmethod
    def platform(self) -> str:
        """Platform identifier, e.g. upwork, reddit."""

    @abstractmethod
    def health_check(self) -> ConnectorHealth:
        """Validate credentials, session, or API keys."""

    @abstractmethod
    def search(self, params: SearchParams) -> list[RawListingRef]:
        """Discover listing stubs for the given queries."""

    @abstractmethod
    def extract(self, ref: RawListingRef) -> RawListing:
        """Fetch full listing detail for one search result."""

    @abstractmethod
    def normalize(self, raw: RawListing) -> Opportunity:
        """Map platform-specific raw data to the shared Opportunity schema."""
