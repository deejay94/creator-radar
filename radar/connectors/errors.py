"""Shared connector exceptions."""


class ConnectorError(Exception):
    """Base error for connector operations."""


class ConnectorNotReadyError(ConnectorError):
    """Raised when a connector method is not yet implemented."""


class ConnectorUnhealthyError(ConnectorError):
    """Raised when health_check fails before ingestion."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
