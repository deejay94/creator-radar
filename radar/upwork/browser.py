"""Playwright browser launch helpers tuned for Upwork bot detection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from radar.upwork.errors import UpworkAuthError

BrowserChannel = Literal["chrome", "chromium"]

DEFAULT_SESSION_DIR = Path.home() / ".creator-radar"
DEFAULT_PROFILE_DIRNAME = "upwork-browser-profile"

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
"""

LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
]


def resolve_browser_profile_dir() -> Path:
    configured = os.environ.get("UPWORK_BROWSER_PROFILE", "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_SESSION_DIR / DEFAULT_PROFILE_DIRNAME


def launch_login_context(playwright: Any, browser: BrowserChannel = "chrome") -> Any:
    """Launch a persistent, headed browser context for manual Upwork login."""
    profile_dir = resolve_browser_profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)

    kwargs: dict[str, Any] = {
        "user_data_dir": str(profile_dir),
        "headless": False,
        "viewport": None,
        "ignore_default_args": ["--enable-automation"],
        "args": LAUNCH_ARGS,
    }
    if browser == "chrome":
        kwargs["channel"] = "chrome"

    try:
        context = playwright.chromium.launch_persistent_context(**kwargs)
    except Exception as exc:
        if browser == "chrome":
            raise UpworkAuthError(
                "Could not launch Google Chrome for Upwork login. "
                "Install Chrome from https://www.google.com/chrome/ "
                "or retry with: python -m radar upwork login --browser chromium"
            ) from exc
        raise UpworkAuthError(f"Could not launch browser for Upwork login: {exc}") from exc

    context.add_init_script(STEALTH_INIT_SCRIPT)
    return context


def launch_headless_context(playwright: Any, storage_state: dict[str, Any]) -> Any:
    """Launch a headless context using a saved session."""
    browser = playwright.chromium.launch(
        headless=True,
        args=LAUNCH_ARGS,
        ignore_default_args=["--enable-automation"],
    )
    context = browser.new_context(storage_state=storage_state)
    context.add_init_script(STEALTH_INIT_SCRIPT)
    return browser, context
