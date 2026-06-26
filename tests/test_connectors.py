import pytest

from radar.connectors import (
    ConnectorError,
    ConnectorNotReadyError,
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


def test_upwork_unimplemented_methods_raise_not_ready():
    connector = UpworkConnector()
    params = SearchParams(queries=["UGC"])
    ref = RawListingRef(external_id="1", url="https://www.upwork.com/jobs/1", title="Test")

    with pytest.raises(ConnectorNotReadyError, match="Step 2"):
        connector.search(params)

    with pytest.raises(ConnectorNotReadyError, match="Step 2"):
        connector.extract(ref)

    with pytest.raises(ConnectorNotReadyError, match="Step 2"):
        connector.normalize(
            RawListing(platform="upwork", external_id="1", url="https://www.upwork.com/jobs/1")
        )
