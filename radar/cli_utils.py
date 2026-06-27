"""Shared CLI helpers for import and notify commands."""

from __future__ import annotations

import argparse
import logging
import sys

from radar.connectors.errors import ConnectorError
from radar.connectors.types import SearchParams
from radar.upwork.config import resolve_limit_per_query, resolve_search_queries


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )


def build_search_params(platform: str, args: argparse.Namespace) -> SearchParams:
    if platform == "upwork":
        return SearchParams(
            queries=resolve_search_queries(args.query),
            limit_per_query=resolve_limit_per_query(args.limit),
            extras={"debug": args.debug},
        )

    if platform == "reddit":
        return SearchParams(
            queries=[],
            limit_per_query=resolve_limit_per_query(args.limit),
            extras={
                "subreddit": args.subreddit,
                "flair": args.flair,
            },
        )

    raise ConnectorError(f"Unsupported platform for import: {platform}")
