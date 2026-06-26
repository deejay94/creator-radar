"""Upwork Playwright authentication helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from radar.upwork.browser import BrowserChannel, launch_headless_context, launch_login_context
from radar.upwork.errors import PlaywrightNotInstalledError, UpworkAuthError
from radar.upwork.session import (
    UpworkSessionError,
    load_session_state,
    resolve_session_path,
    save_session_state,
    session_exists,
    validate_storage_state,
)

UPWORK_HOME_URL = "https://www.upwork.com/"
UPWORK_LOGIN_URL = "https://www.upwork.com/ab/account-security/login"
UPWORK_FIND_WORK_URL = "https://www.upwork.com/nx/find-work/"
LOGIN_TIMEOUT_SECONDS = 300
PAGE_TIMEOUT_MS = 60_000

AUTHENTICATED_URL_PREFIXES = (
    "/nx/find-work",
    "/nx/wm/",
    "/ab/messages/",
    "/freelancers/",
)

# Centralized selectors — update here when Upwork DOM changes.
USER_MENU_SELECTORS = [
    '[data-test="nav-user-menu"]',
    '[data-cy="nav-user-menu"]',
    'nav [data-test="dropdown-toggle"]',
]
LOGGED_OUT_SELECTORS = [
    'a[href*="/account-security/login"]',
    'a[href*="account-security/login"]',
    'button:has-text("Log in")',
    'a:has-text("Log In")',
    'a:has-text("Sign up")',
]
DISPLAY_NAME_SELECTORS = [
    '[data-test="nav-user-menu"] [data-test="user-name"]',
    '[data-cy="nav-user-menu"] [data-cy="user-name"]',
    'nav [data-test="user-name"]',
    'nav [data-cy="user-name"]',
]
LOGIN_FORM_SELECTORS = [
    'input[type="password"]',
    'form[action*="login"]',
    '[data-test="login-form"]',
]
CAPTCHA_SELECTORS = [
    'iframe[src*="challenges.cloudflare.com"]',
    'iframe[src*="turnstile"]',
    'iframe[src*="captcha"]',
    '[data-test="captcha"]',
    'text=/verify you.?re human/i',
    'text=/verify you are human/i',
]


@dataclass(frozen=True)
class UpworkAuthStatus:
    authenticated: bool
    display_name: Optional[str]
    message: str


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise UpworkAuthError(
            "Playwright is not installed. Run: pip install -r requirements.txt"
        ) from exc
    return sync_playwright


def _playwright_missing_browser_message(exc: Exception) -> Optional[str]:
    message = str(exc).lower()
    if "executable doesn't exist" in message or "please run the following command" in message:
        return "Playwright Chromium is not installed. Run: playwright install chromium"
    return None


def _url_looks_like_login(url: str) -> bool:
    path = urlparse(url).path.lower()
    return "/login" in path or "/account-security/login" in path


def _page_has_login_form(page) -> bool:
    for selector in LOGIN_FORM_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def _page_has_captcha(page) -> bool:
    for selector in CAPTCHA_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def _extract_display_name(page) -> Optional[str]:
    for selector in DISPLAY_NAME_SELECTORS:
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                text = locator.first.inner_text(timeout=2000).strip()
                if text:
                    return text
        except Exception:
            continue

    for selector in USER_MENU_SELECTORS:
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                text = locator.first.inner_text(timeout=2000).strip()
                if text and len(text) < 80:
                    return text.split("\n")[0].strip()
        except Exception:
            continue
    return None


def _url_looks_authenticated(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.startswith(prefix) for prefix in AUTHENTICATED_URL_PREFIXES)


def _page_looks_logged_out(page) -> bool:
    for selector in LOGGED_OUT_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def _has_user_menu(page) -> bool:
    for selector in USER_MENU_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def _is_authenticated_page(page) -> bool:
    if _url_looks_like_login(page.url):
        return False
    if _page_has_login_form(page):
        return False
    if _page_looks_logged_out(page):
        return False
    if _has_user_menu(page):
        return True
    if _url_looks_authenticated(page.url):
        return True
    return False


def _find_authenticated_page(context) -> Optional[object]:
    for page in context.pages:
        try:
            if _is_authenticated_page(page):
                return page
        except Exception:
            continue
    return None


def login_instructions(browser: BrowserChannel = "chrome") -> str:
    browser_name = "Google Chrome" if browser == "chrome" else "Chromium"
    return (
        f"Opening {browser_name} with a persistent profile.\n"
        "The browser stays open until you finish logging in (up to 5 minutes).\n"
        "1. Click Log In on Upwork and complete email/password + any CAPTCHA.\n"
        "2. Wait until you see your account menu or land on Find Work.\n"
        "3. The window closes automatically once signed in.\n"
        "If CAPTCHA keeps looping, use: python -m radar upwork import-session <file.json>"
    )


def login(browser: BrowserChannel = "chrome") -> str:
    """Open a headed browser for manual login and save session state."""
    sync_playwright = _import_playwright()
    session_path = resolve_session_path()

    try:
        with sync_playwright() as playwright:
            context = launch_login_context(playwright, browser=browser)
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(PAGE_TIMEOUT_MS)
            page.goto(UPWORK_HOME_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            deadline = time.monotonic() + LOGIN_TIMEOUT_SECONDS
            authenticated_page = None
            captcha_hint_printed = False

            while time.monotonic() < deadline:
                authenticated_page = _find_authenticated_page(context)
                if authenticated_page is not None:
                    break

                if not captcha_hint_printed:
                    for open_page in context.pages:
                        if _page_has_captcha(open_page):
                            captcha_hint_printed = True
                            break

                time.sleep(1)
            else:
                context.close()
                raise UpworkAuthError(
                    f"Login timed out after {LOGIN_TIMEOUT_SECONDS // 60} minutes. "
                    "Complete Upwork login in the browser window and try again. "
                    "If CAPTCHA keeps failing, use Google Chrome (default) or "
                    "python -m radar upwork import-session <file.json>"
                )

            state = context.storage_state()
            context.close()
    except UpworkAuthError:
        raise
    except Exception as exc:
        browser_hint = _playwright_missing_browser_message(exc)
        if browser_hint:
            raise PlaywrightNotInstalledError(browser_hint) from exc
        raise UpworkAuthError(f"Upwork login failed: {exc}") from exc

    saved_path = save_session_state(state, session_path)
    return str(saved_path)


def import_session(source: str | Path) -> str:
    """Import a Playwright storage_state JSON file exported from another browser."""
    path = Path(source).expanduser()
    if not path.is_file():
        raise UpworkAuthError(f"Session file not found: {path}")

    try:
        state = load_session_state(path)
    except UpworkSessionError as exc:
        raise UpworkAuthError(str(exc)) from exc

    validate_storage_state(state)
    saved_path = save_session_state(state)
    return str(saved_path)


def check_status() -> UpworkAuthStatus:
    """Validate saved session headlessly."""
    if not session_exists():
        return UpworkAuthStatus(
            authenticated=False,
            display_name=None,
            message="No Upwork session saved.",
        )

    sync_playwright = _import_playwright()
    session_path = resolve_session_path()

    try:
        state = load_session_state(session_path)
    except UpworkSessionError as exc:
        return UpworkAuthStatus(
            authenticated=False,
            display_name=None,
            message=str(exc),
        )

    try:
        with sync_playwright() as playwright:
            browser, context = launch_headless_context(playwright, state)
            page = context.new_page()
            page.set_default_timeout(PAGE_TIMEOUT_MS)
            page.goto(UPWORK_FIND_WORK_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

            if not _is_authenticated_page(page):
                browser.close()
                return UpworkAuthStatus(
                    authenticated=False,
                    display_name=None,
                    message="Upwork session expired.",
                )

            display_name = _extract_display_name(page)
            browser.close()
    except Exception as exc:
        browser_hint = _playwright_missing_browser_message(exc)
        if browser_hint:
            raise PlaywrightNotInstalledError(browser_hint) from exc
        raise UpworkAuthError(f"Upwork session check failed: {exc}") from exc

    return UpworkAuthStatus(
        authenticated=True,
        display_name=display_name,
        message="authenticated",
    )
