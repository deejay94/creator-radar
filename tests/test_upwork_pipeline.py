from unittest.mock import MagicMock, patch

import pytest

from radar.connectors.errors import ConnectorUnhealthyError
from radar.connectors.pipeline import run_connector_pipeline
from radar.connectors.types import Opportunity, RawListing, RawListingRef, SearchParams
from radar.upwork.connector import UpworkConnector


def test_run_connector_pipeline_yields_normalized_opportunities():
    connector = MagicMock()
    connector.platform = "upwork"
    connector.health_check.return_value = MagicMock(healthy=True, message="ok")
    connector.search.return_value = [
        RawListingRef(external_id="1", url="https://www.upwork.com/jobs/~1", title="Job 1"),
    ]
    connector.extract.return_value = RawListing(
        platform="upwork",
        external_id="1",
        url="https://www.upwork.com/jobs/~1",
        title="Job 1",
        description="desc",
        payload={"skills": []},
    )
    connector.normalize.return_value = Opportunity(
        platform="upwork",
        external_id="1",
        title="Job 1",
        url="https://www.upwork.com/jobs/~1",
    )

    results = list(run_connector_pipeline(connector, SearchParams(queries=["UGC"])))
    assert len(results) == 1
    assert results[0].title == "Job 1"


def test_run_connector_pipeline_unhealthy():
    connector = MagicMock()
    connector.platform = "upwork"
    connector.health_check.return_value = MagicMock(healthy=False, message="session expired")

    with pytest.raises(ConnectorUnhealthyError, match="session expired"):
        list(run_connector_pipeline(connector, SearchParams(queries=["UGC"])))


@patch("radar.upwork.connector.search_jobs")
@patch("radar.upwork.connector.extract_job")
def test_upwork_connector_search_and_extract(mock_extract, mock_search):
    mock_search.return_value = [
        RawListingRef(
            external_id="job1",
            url="https://www.upwork.com/jobs/~job1",
            title="UGC job",
            source_query="UGC",
        )
    ]
    mock_extract.return_value = RawListing(
        platform="upwork",
        external_id="job1",
        url="https://www.upwork.com/jobs/~job1",
        title="UGC job",
        description="desc",
        payload={"skills": ["TikTok"], "budget": "$100"},
    )

    connector = UpworkConnector()
    connector._browser_session = MagicMock()
    connector._browser_session.context = MagicMock()

    refs = connector.search(SearchParams(queries=["UGC"], limit_per_query=5))
    assert len(refs) == 1
    raw = connector.extract(refs[0])
    opp = connector.normalize(raw)
    assert opp.title == "UGC job"
    assert opp.budget == "$100"
