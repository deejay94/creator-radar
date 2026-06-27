"""Platform name → connector class registry."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from radar.connectors.errors import ConnectorError

if TYPE_CHECKING:
    from radar.connectors.base import OpportunityConnector


def get_connector(platform: str, **kwargs: Any) -> OpportunityConnector:
    key = platform.strip().lower()
    if key == "reddit":
        from radar.reddit_connector import RedditConnector

        return RedditConnector()
    if key == "upwork":
        from radar.upwork.connector import UpworkConnector

        return UpworkConnector(headed=bool(kwargs.get("headed", True)))

    known = "reddit, upwork"
    raise ConnectorError(f"Unknown platform {platform!r}. Known platforms: {known}")


def list_platforms() -> list[str]:
    return ["reddit", "upwork"]
