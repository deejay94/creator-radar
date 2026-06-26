"""Platform name → connector class registry."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from radar.connectors.errors import ConnectorError

if TYPE_CHECKING:
    from radar.connectors.base import OpportunityConnector


def _connector_classes() -> dict[str, type[OpportunityConnector]]:
    from radar.reddit_connector import RedditConnector
    from radar.upwork.connector import UpworkConnector

    return {
        "reddit": RedditConnector,
        "upwork": UpworkConnector,
    }


def get_connector(platform: str, **kwargs: Any) -> OpportunityConnector:
    connectors = _connector_classes()
    key = platform.strip().lower()
    connector_cls = connectors.get(key)
    if connector_cls is None:
        known = ", ".join(sorted(connectors)) or "(none)"
        raise ConnectorError(f"Unknown platform {platform!r}. Known platforms: {known}")

    if key == "upwork":
        return connector_cls(headed=bool(kwargs.get("headed", True)))
    return connector_cls()


def list_platforms() -> list[str]:
    return sorted(_connector_classes())
