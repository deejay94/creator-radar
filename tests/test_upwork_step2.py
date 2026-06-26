import pytest

from radar.upwork.errors import UpworkAuthError
from radar.upwork.connector import UpworkConnector
from radar.upwork.normalize import normalize_upwork_listing
from radar.connectors.types import RawListing, SearchParams


def test_normalize_does_not_require_browser():
    raw = RawListing(
        platform="upwork",
        external_id="abc123",
        url="https://www.upwork.com/jobs/~abc123",
        title="UGC Creator Needed",
        description="Create TikTok videos for our brand.",
        payload={
            "job_id": "abc123",
            "budget": "$500.00",
            "hourly": False,
            "skills": ["Video Editing", "TikTok"],
            "posted_time": "2 days ago",
            "experience_level": "Intermediate",
            "search_query": "UGC",
        },
    )
    opportunity = UpworkConnector().normalize(raw)
    assert opportunity.platform == "upwork"
    assert opportunity.external_id == "abc123"
    assert opportunity.budget == "$500.00"
    assert opportunity.hourly is False
    assert opportunity.skills == ["Video Editing", "TikTok"]
    assert opportunity.metadata["search_query"] == "UGC"
    assert opportunity.posted_at is not None


def test_search_requires_session(monkeypatch):
    monkeypatch.setattr(
        "radar.upwork.browser_session.session_exists",
        lambda path=None: False,
    )
    connector = UpworkConnector()
    try:
        with pytest.raises(UpworkAuthError, match="No Upwork session saved"):
            connector.search(SearchParams(queries=["UGC"], limit_per_query=1))
    finally:
        connector.close()
