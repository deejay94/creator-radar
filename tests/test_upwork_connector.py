from unittest.mock import MagicMock, patch

import pytest

from radar.connectors.types import ConnectorHealth
from radar.upwork.auth import (
    UpworkAuthStatus,
    _extract_display_name,
    _is_authenticated_page,
    _url_looks_like_login,
    check_status,
)
from radar.upwork.cli import cmd_status, format_health_status
from radar.upwork.connector import UpworkConnector


def test_url_looks_like_login():
    assert _url_looks_like_login("https://www.upwork.com/ab/account-security/login")
    assert not _url_looks_like_login("https://www.upwork.com/nx/find-work/")


def test_is_authenticated_page_detects_login_redirect():
    page = MagicMock()
    page.url = "https://www.upwork.com/ab/account-security/login"
    page.locator.return_value.count.return_value = 0
    assert _is_authenticated_page(page) is False


def test_is_authenticated_page_homepage_logged_out_is_false():
    page = MagicMock()
    page.url = "https://www.upwork.com/"

    def locator_side_effect(selector):
        locator = MagicMock()
        if selector in (
            'a[href*="/account-security/login"]',
            'a[href*="account-security/login"]',
            'a:has-text("Log In")',
        ):
            locator.count.return_value = 1
        else:
            locator.count.return_value = 0
        return locator

    page.locator.side_effect = locator_side_effect
    assert _is_authenticated_page(page) is False


def test_is_authenticated_page_detects_user_menu():
    page = MagicMock()
    page.url = "https://www.upwork.com/nx/find-work/"

    def locator_side_effect(selector):
        locator = MagicMock()
        locator.count.return_value = 1 if selector == '[data-test="nav-user-menu"]' else 0
        return locator

    page.locator.side_effect = locator_side_effect
    assert _is_authenticated_page(page) is True


def test_extract_display_name_from_selector():
    page = MagicMock()

    def locator_side_effect(selector):
        locator = MagicMock()
        if selector == '[data-test="nav-user-menu"] [data-test="user-name"]':
            locator.count.return_value = 1
            locator.first.inner_text.return_value = "Dee Jay"
        else:
            locator.count.return_value = 0
        return locator

    page.locator.side_effect = locator_side_effect
    assert _extract_display_name(page) == "Dee Jay"


def test_check_status_without_session(monkeypatch):
    monkeypatch.setattr("radar.upwork.auth.session_exists", lambda path=None: False)
    status = check_status()
    assert status.authenticated is False
    assert "login" in status.message.lower() or status.message == "No Upwork session saved."


@patch("radar.upwork.auth.launch_headless_context")
@patch("radar.upwork.auth.load_session_state")
@patch("radar.upwork.auth.session_exists", return_value=True)
@patch("radar.upwork.auth._import_playwright")
def test_check_status_authenticated(
    mock_import_playwright,
    _mock_session_exists,
    mock_load_state,
    mock_launch_headless,
):
    mock_load_state.return_value = {"cookies": []}

    page = MagicMock()
    page.url = "https://www.upwork.com/nx/find-work/"

    def locator_side_effect(selector):
        locator = MagicMock()
        if selector == '[data-test="nav-user-menu"]':
            locator.count.return_value = 1
        elif selector == '[data-test="nav-user-menu"] [data-test="user-name"]':
            locator.count.return_value = 1
            locator.first.inner_text.return_value = "Dee Jay"
        else:
            locator.count.return_value = 0
        return locator

    page.locator.side_effect = locator_side_effect

    context = MagicMock()
    context.new_page.return_value = page
    browser = MagicMock()
    mock_launch_headless.return_value = (browser, context)

    playwright = MagicMock()
    mock_import_playwright.return_value.return_value.__enter__.return_value = playwright

    status = check_status()
    assert status.authenticated is True
    assert status.display_name == "Dee Jay"


@patch("radar.upwork.connector.check_status")
def test_upwork_connector_health_check_healthy(mock_check_status):
    mock_check_status.return_value = UpworkAuthStatus(
        authenticated=True,
        display_name="Dee Jay",
        message="authenticated",
    )
    health = UpworkConnector().health_check()
    assert health == ConnectorHealth(
        healthy=True,
        status="authenticated",
        display_name="Dee Jay",
        message="authenticated",
    )


@patch("radar.upwork.connector.check_status")
def test_upwork_connector_health_check_expired(mock_check_status):
    mock_check_status.return_value = UpworkAuthStatus(
        authenticated=False,
        display_name=None,
        message="Upwork session expired.",
    )
    health = UpworkConnector().health_check()
    assert health.healthy is False
    assert health.status == "reauthentication required"


def test_format_health_status_success():
    health = ConnectorHealth(
        healthy=True,
        status="authenticated",
        display_name="Dee Jay",
        message="authenticated",
    )
    output = format_health_status(health)
    assert "✔ Upwork session valid" in output
    assert "User: Dee Jay" in output
    assert "Status: authenticated" in output


def test_format_health_status_invalid():
    health = ConnectorHealth(
        healthy=False,
        status="reauthentication required",
        display_name=None,
        message="Upwork session expired.",
    )
    output = format_health_status(health)
    assert "✗ Upwork session invalid" in output
    assert "Run: python -m radar upwork login" in output


@patch("radar.upwork.cli.UpworkConnector")
def test_cmd_status_exit_code(mock_connector_cls):
    mock_connector_cls.return_value.health_check.return_value = ConnectorHealth(
        healthy=True,
        status="authenticated",
        display_name="Dee Jay",
        message="authenticated",
    )
    assert cmd_status() == 0

    mock_connector_cls.return_value.health_check.return_value = ConnectorHealth(
        healthy=False,
        status="reauthentication required",
        display_name=None,
        message="expired",
    )
    assert cmd_status() == 1
