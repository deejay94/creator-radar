"""Notify command: fetch opportunities and expose JSON for the worker."""

from __future__ import annotations

import argparse
import json
import os
import sys

from radar.cli_utils import build_search_params, configure_logging
from radar.connectors.errors import ConnectorError, ConnectorUnhealthyError
from radar.connectors.registry import get_connector
from radar.connectors.types import Opportunity
from radar.fetch_service import fetch_eligible_opportunities
from radar.reddit import DEFAULT_FLAIR_FILTER, DEFAULT_SUBREDDITS_CSV, resolve_subreddits
from radar.upwork.config import resolve_search_queries
from radar.upwork.errors import PlaywrightNotInstalledError, UpworkAuthError


def opportunity_to_notify_json(opportunity: Opportunity) -> dict[str, str]:
    return {
        "platform": opportunity.platform,
        "external_id": opportunity.external_id,
        "title": opportunity.title,
        "url": opportunity.url,
    }


def _log_fetch_start(platform: str, args: argparse.Namespace) -> None:
    if platform == "reddit":
        subreddit = args.subreddit or os.environ.get("RADAR_REDDIT_SUBREDDITS") or DEFAULT_SUBREDDITS_CSV
        subreddits = resolve_subreddits(subreddit)
        print(
            f"Notify fetch ({platform}): scraping {', '.join(f'r/{name}' for name in subreddits)}",
            file=sys.stderr,
        )
        return

    if platform == "upwork":
        queries = resolve_search_queries(args.query)
        preview = ", ".join(queries[:3])
        if len(queries) > 3:
            preview = f"{preview}, … (+{len(queries) - 3} more)"
        print(f"Notify fetch ({platform}): searching {preview}", file=sys.stderr)


def cmd_notify_fetch(argv: list[str] | None = None) -> int:
    configure_logging()

    parser = argparse.ArgumentParser(description="Fetch opportunities and list them as JSON")
    parser.add_argument(
        "--platform",
        required=True,
        choices=["reddit", "upwork"],
        help="Connector platform to fetch from",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max listings per query/fetch (default: RADAR_UPWORK_LIMIT_PER_QUERY or 20)",
    )
    parser.add_argument("--query", help="Upwork only: search term (default: env or PRD queries)")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Upwork only: use headless browser instead of visible Chrome",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Upwork only: save debug artifacts when search returns 0 jobs",
    )
    parser.add_argument(
        "--subreddit",
        default=None,
        help=(
            f"Reddit only: subreddit(s), comma-separated "
            f"(default: {DEFAULT_SUBREDDITS_CSV} or RADAR_REDDIT_SUBREDDITS env)"
        ),
    )
    parser.add_argument(
        "--flair",
        default=DEFAULT_FLAIR_FILTER,
        help="Reddit only: flair filter",
    )
    args = parser.parse_args(argv)

    platform = args.platform.strip().lower()
    connector = get_connector(platform, headed=not args.headless)
    if platform == "reddit":
        subreddit = args.subreddit or os.environ.get("RADAR_REDDIT_SUBREDDITS") or DEFAULT_SUBREDDITS_CSV
        args.subreddit = subreddit
    params = build_search_params(platform, args)

    try:
        _log_fetch_start(platform, args)
        opportunities = fetch_eligible_opportunities(connector, params)
        payload = [opportunity_to_notify_json(opportunity) for opportunity in opportunities]

        print(f"Fetched {len(payload)} opportunities", file=sys.stderr)
        print(json.dumps(payload))
    except ConnectorUnhealthyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except PlaywrightNotInstalledError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UpworkAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ConnectorError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if hasattr(connector, "close"):
            connector.close()

    return 0


def main(argv: list[str] | None = None) -> int:
    return cmd_notify_fetch(argv)
