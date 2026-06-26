"""Shared Playwright browser session for Upwork search and extraction."""

from __future__ import annotations

from typing import Any, Optional

from radar.upwork.auth import _import_playwright, _playwright_missing_browser_message
from radar.upwork.browser import STEALTH_INIT_SCRIPT, launch_headless_context
from radar.upwork.errors import PlaywrightNotInstalledError, UpworkAuthError
from radar.upwork.session import UpworkSessionError, load_session_state, session_exists


class UpworkBrowserSession:
    def __init__(self) -> None:
        self._playwright_cm: Any = None
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._headed: bool = False

    @property
    def context(self) -> Any:
        if self._context is None:
            raise UpworkAuthError("Upwork browser session is not open.")
        return self._context

    def open(self, *, headed: bool = False) -> None:
        if self._context is not None:
            return

        if not session_exists():
            raise UpworkAuthError(
                "No Upwork session saved. Run: python -m radar upwork login"
            )

        self._headed = headed
        try:
            state = load_session_state()
        except UpworkSessionError as exc:
            raise UpworkAuthError(str(exc)) from exc

        sync_playwright = _import_playwright()
        self._playwright_cm = sync_playwright()
        self._playwright = self._playwright_cm.__enter__()

        try:
            if headed:
                self._browser = self._playwright.chromium.launch(
                    headless=False,
                    channel="chrome",
                    args=["--disable-blink-features=AutomationControlled"],
                    ignore_default_args=["--enable-automation"],
                )
                self._context = self._browser.new_context(storage_state=state)
                self._context.add_init_script(STEALTH_INIT_SCRIPT)
            else:
                self._browser, self._context = launch_headless_context(self._playwright, state)
        except Exception as exc:
            self.close()
            browser_hint = _playwright_missing_browser_message(exc)
            if browser_hint:
                raise PlaywrightNotInstalledError(browser_hint) from exc
            if headed:
                raise UpworkAuthError(
                    f"Could not open headed Chrome for search: {exc}. "
                    "Retry without --headed or reinstall Chrome."
                ) from exc
            raise UpworkAuthError(f"Could not open browser for Upwork search: {exc}") from exc

    def close(self) -> None:
        if self._context is not None and not self._headed:
            try:
                if self._browser is not None:
                    self._browser.close()
            except Exception:
                pass
        elif self._context is not None and self._headed:
            try:
                if self._browser is not None:
                    self._browser.close()
            except Exception:
                pass

        self._context = None
        self._browser = None

        if self._playwright_cm is not None:
            try:
                self._playwright_cm.__exit__(None, None, None)
            except Exception:
                pass
            self._playwright_cm = None
            self._playwright = None
