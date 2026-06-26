"""Upwork-specific errors."""


class UpworkAuthError(RuntimeError):
    """Raised when Upwork authentication fails."""


class PlaywrightNotInstalledError(UpworkAuthError):
    """Raised when Playwright browsers are missing."""
