from unittest.mock import MagicMock, patch

from radar.connectors.types import SearchParams
from radar.db.import_service import import_opportunities
from radar.db.repository import OpportunityRepository
from radar.reddit_connector import RedditConnector
from radar.models import RedditPost


def test_reddit_connector_health_check_missing_token(monkeypatch):
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    health = RedditConnector().health_check()
    assert health.healthy is False


def test_reddit_connector_search_normalize_extract(monkeypatch):
    monkeypatch.setenv("APIFY_API_TOKEN", "test-token")
    post = RedditPost(
        post_id="abc123",
        title="Looking for creators",
        body="DM for collab",
        author="brand",
        subreddit="UGCCreators",
        url="https://reddit.com/r/UGCCreators/comments/abc123/test/",
        flair="Collab Request 🤝",
    )

    with patch.object(RedditConnector, "_get_client") as mock_get_client:
        mock_get_client.return_value.fetch_posts.return_value = [post]
        connector = RedditConnector()
        refs = connector.search(
            SearchParams(limit_per_query=5, extras={"subreddit": "UGCCreators"})
        )
        assert len(refs) == 1
        raw = connector.extract(refs[0])
        opp = connector.normalize(raw)

    assert opp.platform == "reddit"
    assert opp.external_id == "abc123"
    assert opp.description == "DM for collab"
    assert opp.metadata["subreddit"] == "UGCCreators"


def test_import_opportunities_dedupes(tmp_path):
    repo = OpportunityRepository(tmp_path / "import.db")
    connector = MagicMock()
    connector.platform = "upwork"
    connector.health_check.return_value = MagicMock(healthy=True, message="ok")

    from radar.connectors.types import Opportunity

    opp = Opportunity(
        platform="upwork",
        external_id="job1234567890",
        title="First",
        url="https://www.upwork.com/jobs/~job1234567890",
    )

    def pipeline(_connector, _params, on_extraction_error=None):
        yield opp
        yield opp

    with patch("radar.db.import_service.run_connector_pipeline", side_effect=pipeline):
        stats = import_opportunities(connector, SearchParams(queries=["UGC"]), repo)

    assert stats.imported == 1
    assert stats.duplicates == 1
    assert repo.count("upwork") == 1
    repo.close()
