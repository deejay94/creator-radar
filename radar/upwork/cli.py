"""Upwork CLI commands."""

from __future__ import annotations

import argparse
import logging
import sys

from radar.connectors.errors import ConnectorUnhealthyError
from radar.connectors.pipeline import run_connector_pipeline
from radar.connectors.types import ConnectorHealth, SearchParams
from radar.upwork.auth import import_session, login, login_instructions
from radar.upwork.browser import BrowserChannel
from radar.upwork.config import DEFAULT_SEARCH_QUERIES
from radar.upwork.connector import UpworkConnector
from radar.upwork.errors import PlaywrightNotInstalledError, UpworkAuthError


def format_health_status(health: ConnectorHealth) -> str:
    lines: list[str] = []
    if health.healthy:
        lines.append("✔ Upwork session valid")
        if health.display_name:
            lines.append(f"User: {health.display_name}")
        lines.append(f"Status: {health.status}")
        return "\n".join(lines)

    lines.append("✗ Upwork session invalid")
    lines.append(f"Status: {health.status}")
    if health.message:
        lines.append(health.message)
    if health.status == "reauthentication required":
        lines.append("Run: python -m radar upwork login")
    return "\n".join(lines)


def cmd_login(browser: BrowserChannel = "chrome") -> int:
    print(login_instructions(browser=browser))
    try:
        saved_path = login(browser=browser)
    except PlaywrightNotInstalledError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UpworkAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("✔ Upwork session saved")
    print(f"Session file: {saved_path}")
    print("Run: python -m radar upwork status")
    return 0


def cmd_import_session(path: str) -> int:
    try:
        saved_path = import_session(path)
    except UpworkAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("✔ Upwork session imported")
    print(f"Session file: {saved_path}")
    print("Run: python -m radar upwork status")
    return 0


def cmd_status() -> int:
    try:
        health = UpworkConnector().health_check()
    except PlaywrightNotInstalledError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UpworkAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(format_health_status(health))
    return 0 if health.healthy else 1


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )


def cmd_search(query: str | None, limit: int, headed: bool, debug: bool) -> int:
    _configure_logging()

    queries = [query] if query else DEFAULT_SEARCH_QUERIES
    connector = UpworkConnector(headed=headed)
    params = SearchParams(
        queries=queries,
        limit_per_query=limit,
        extras={"debug": debug},
    )

    try:
        for opportunity in run_connector_pipeline(
            connector,
            params,
            on_extraction_error=lambda ref, exc: print(
                f"Extraction error ({ref.external_id}): {exc}",
                file=sys.stderr,
            ),
        ):
            print(opportunity.model_dump_json())
    except ConnectorUnhealthyError as exc:
        print(str(exc), file=sys.stderr)
        print("Run: python -m radar upwork login", file=sys.stderr)
        return 1
    except PlaywrightNotInstalledError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UpworkAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        connector.close()

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Upwork connector commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser("login", help="Open browser to log in and save session")
    login_parser.add_argument(
        "--browser",
        choices=["chrome", "chromium"],
        default="chrome",
        help="Browser to use (default: chrome — recommended to avoid CAPTCHA loops)",
    )

    import_parser = subparsers.add_parser(
        "import-session",
        help="Import a Playwright storage_state JSON file from another browser",
    )
    import_parser.add_argument("path", help="Path to storage_state JSON")

    subparsers.add_parser("status", help="Check whether the saved Upwork session is valid")

    search_parser = subparsers.add_parser(
        "search",
        help="Search Upwork jobs and print normalized opportunities as JSON lines",
    )
    search_parser.add_argument(
        "--query",
        help="Single search term (default: run all PRD default queries)",
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum jobs per query (default: 20)",
    )
    search_parser.add_argument(
        "--headless",
        action="store_true",
        help="Use headless browser (often returns 0 jobs on Upwork; default is visible Chrome)",
    )
    search_parser.add_argument(
        "--debug",
        action="store_true",
        help="Save screenshot/HTML to ~/.creator-radar/ when search returns 0 jobs",
    )

    args = parser.parse_args(argv)
    if args.command == "login":
        return cmd_login(browser=args.browser)
    if args.command == "import-session":
        return cmd_import_session(args.path)
    if args.command == "status":
        return cmd_status()
    if args.command == "search":
        return cmd_search(
            query=args.query,
            limit=args.limit,
            headed=not args.headless,
            debug=args.debug,
        )
    parser.print_help()
    return 1
