"""Reddit connector normalization parity checks."""

from __future__ import annotations

from datetime import datetime, timezone

from radar.connectors.types import RawListing
from radar.reddit_connector import RedditConnector


def test_reddit_normalize_populates_shared_top_level_fields():
    raw = RawListing(
        platform="reddit",
        external_id="t3_abc123",
        url="https://reddit.com/r/UGCCreators/comments/abc123/test/",
        title="Looking for UGC creator",
        description="Need short videos for skincare brand.",
        payload={
            "author": "creator_user",
            "subreddit": "UGCCreators",
            "flair": "Collab Request 🤝",
            "created_at": "2026-06-20T12:00:00+00:00",
            "source_query": "Collab Request 🤝",
        },
    )
    opportunity = RedditConnector().normalize(raw)
    assert opportunity.platform == "reddit"
    assert opportunity.external_id == "t3_abc123"
    assert opportunity.title == "Looking for UGC creator"
    assert opportunity.description == "Need short videos for skincare brand."
    assert opportunity.url.startswith("https://reddit.com")
    assert opportunity.posted_at == datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc)
    assert opportunity.budget == ""
    assert opportunity.hourly is None
    assert opportunity.skills == []
    assert opportunity.metadata["author"] == "creator_user"
    assert opportunity.metadata["subreddit"] == "UGCCreators"
