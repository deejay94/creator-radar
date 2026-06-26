"""Platform name → connector class registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from radar.connectors.errors import ConnectorError

if TYPE_CHECKING:
    from radar.connectors.base import OpportunityConnector


def _connector_classes() -> dict[str, type[OpportunityConnector]]:
    from radar.upwork.connector import UpworkConnector

    return {
        "upwork": UpworkConnector,
    }


def get_connector(platform: str) -> OpportunityConnector:
    connectors = _connector_classes()
    key = platform.strip().lower()
    connector_cls = connectors.get(key)
    if connector_cls is None:
        known = ", ".join(sorted(connectors)) or "(none)"
        raise ConnectorError(f"Unknown platform {platform!r}. Known platforms: {known}")
    return connector_cls()


def list_platforms() -> list[str]:
    return sorted(_connector_classes())
