"""Import command: connector pipeline → dedup → SQLite."""

from __future__ import annotations

import argparse
import logging
import sys

from radar.connectors.errors import ConnectorError, ConnectorUnhealthyError
from radar.connectors.registry import get_connector
from radar.connectors.types import SearchParams
from radar.db.import_service import import_opportunities
from radar.db.repository import OpportunityRepository
from radar.reddit import DEFAULT_FLAIR_FILTER
from radar.upwork.config import DEFAULT_SEARCH_QUERIES
from radar.upwork.errors import PlaywrightNotInstalledError, UpworkAuthError


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )


def _build_search_params(platform: str, args: argparse.Namespace) -> SearchParams:
    if platform == "upwork":
        queries = [args.query] if args.query else DEFAULT_SEARCH_QUERIES
        return SearchParams(
            queries=queries,
            limit_per_query=args.limit,
            extras={"debug": args.debug},
        )

    if platform == "reddit":
        return SearchParams(
            queries=[],
            limit_per_query=args.limit,
            extras={
                "subreddit": args.subreddit,
                "flair": args.flair,
            },
        )

    raise ConnectorError(f"Unsupported platform for import: {platform}")


def cmd_import(argv: list[str] | None = None) -> int:
    _configure_logging()

    parser = argparse.ArgumentParser(description="Import opportunities into SQLite")
    parser.add_argument(
        "--platform",
        required=True,
        choices=["upwork", "reddit"],
        help="Connector platform to import from",
    )
    parser.add_argument("--limit", type=int, default=20, help="Max listings per query/fetch")
    parser.add_argument("--query", help="Upwork search term (default: all PRD queries)")
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
    parser.add_argument("--subreddit", default="UGCCreators", help="Reddit only: subreddit")
    parser.add_argument(
        "--flair",
        default=DEFAULT_FLAIR_FILTER,
        help="Reddit only: flair filter",
    )
    args = parser.parse_args(argv)

    platform = args.platform.strip().lower()
    connector = get_connector(platform, headed=not args.headless)
    repo = OpportunityRepository()
    params = _build_search_params(platform, args)

    try:
        stats = import_opportunities(connector, params, repo)
    except ConnectorUnhealthyError as exc:
        print(str(exc), file=sys.stderr)
        if platform == "upwork":
            print("Run: python -m radar upwork login", file=sys.stderr)
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

    total = repo.count(platform)
    db_path = repo.db_path
    repo.close()

    print(
        f"Import complete ({platform}): "
        f"{stats.imported} imported, {stats.duplicates} duplicates skipped, "
        f"{stats.filtered} filtered, {stats.extraction_errors} extraction errors, "
        f"{total} total in database"
    )
    print(f"Database: {db_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return cmd_import(argv)
