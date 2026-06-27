import json
from unittest.mock import MagicMock, patch

from radar.connectors.types import Opportunity, SearchParams
from radar.fetch_service import fetch_eligible_opportunities
from radar.notify_cmd import opportunity_to_notify_json


def test_opportunity_to_notify_json_shape():
    opportunity = Opportunity(
        platform="reddit",
        external_id="abc123",
        title="Brand looking for UGC creator",
        url="https://www.reddit.com/r/UGCCreators/comments/abc123/test/",
    )
    payload = opportunity_to_notify_json(opportunity)

    assert payload == {
        "platform": "reddit",
        "external_id": "abc123",
        "title": "Brand looking for UGC creator",
        "url": "https://www.reddit.com/r/UGCCreators/comments/abc123/test/",
    }
    assert json.dumps(payload)


def test_fetch_eligible_opportunities_skips_filtered_posts():
    eligible = Opportunity(
        platform="reddit",
        external_id="abc123",
        title="Brand hiring creators",
        url="https://www.reddit.com/r/UGCCreators/comments/abc123/test/",
    )
    filtered = Opportunity(
        platform="reddit",
        external_id="def456",
        title="Male UGC creators needed",
        description="Looking for male content creators only",
        url="https://www.reddit.com/r/UGCCreators/comments/def456/test/",
    )

    connector = MagicMock()
    connector.platform = "reddit"

    with patch(
        "radar.fetch_service.run_connector_pipeline",
        return_value=[eligible, filtered],
    ):
        results = fetch_eligible_opportunities(connector, SearchParams())

    assert len(results) == 1
    assert results[0].external_id == "abc123"
