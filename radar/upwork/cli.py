"""Upwork CLI commands."""

from __future__ import annotations

import argparse
import sys

from radar.connectors.types import ConnectorHealth
from radar.upwork.auth import import_session, login, login_instructions
from radar.upwork.browser import BrowserChannel
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

    args = parser.parse_args(argv)
    if args.command == "login":
        return cmd_login(browser=args.browser)
    if args.command == "import-session":
        return cmd_import_session(args.path)
    if args.command == "status":
        return cmd_status()
    parser.print_help()
    return 1
