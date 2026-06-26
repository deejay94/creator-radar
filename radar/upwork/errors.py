"""Upwork-specific errors."""


class UpworkAuthError(RuntimeError):
    """Raised when Upwork authentication fails."""


class PlaywrightNotInstalledError(UpworkAuthError):
    """Raised when Playwright browsers are missing."""


class ExtractionError(UpworkAuthError):
    """Raised when a single job listing cannot be extracted."""

    def __init__(self, message: str, *, url: str = "") -> None:
        super().__init__(message)
        self.url = url
