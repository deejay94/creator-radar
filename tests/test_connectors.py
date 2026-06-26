import pytest

from radar.connectors import (
    ConnectorError,
    OpportunityConnector,
    RawListing,
    RawListingRef,
    SearchParams,
    get_connector,
    list_platforms,
)
from radar.upwork.connector import UpworkConnector


def test_registry_contains_upwork():
    assert "upwork" in list_platforms()


def test_get_connector_returns_upwork_instance():
    connector = get_connector("upwork")
    assert isinstance(connector, UpworkConnector)
    assert connector.platform == "upwork"


def test_get_connector_unknown_platform():
    with pytest.raises(ConnectorError, match="Unknown platform"):
        get_connector("linkedin")


def test_opportunity_connector_is_abstract():
    with pytest.raises(TypeError):
        OpportunityConnector()  # type: ignore[abstract]


def test_upwork_normalize_is_pure():
    raw = RawListing(
        platform="upwork",
        external_id="1",
        url="https://www.upwork.com/jobs/~1",
        title="Test",
        description="Body",
        payload={"skills": [], "budget": "$50.00"},
    )
    opportunity = UpworkConnector().normalize(raw)
    assert opportunity.platform == "upwork"
    assert opportunity.budget == "$50.00"
