"""Tests for Reddit scan without AI classification."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from radar.models import RedditPost
from radar.__main__ import run_reddit


def _sample_post(post_id: str = "abc123") -> RedditPost:
    return RedditPost(
        post_id=post_id,
        title="Looking for UGC creators for skincare brand",
        body="Paid collab, DM for details.",
        author="brand_user",
        subreddit="UGCCreators",
        url=f"https://reddit.com/r/UGCCreators/comments/{post_id}/test/",
        flair="Collab Request 🤝",
        created_at=datetime.now(timezone.utc),
    )


def test_run_reddit_skips_classify_when_ai_disabled(capsys, monkeypatch):
    monkeypatch.delenv("RADAR_AI_ENABLED", raising=False)
    monkeypatch.delenv("RADAR_AI_CLASSIFICATION", raising=False)

    with patch("radar.__main__.RedditClient") as mock_client:
        mock_client.return_value.fetch_posts.return_value = [_sample_post()]
        with patch("radar.__main__.classify_post") as mock_classify:
            exit_code = run_reddit([])

    assert exit_code == 0
    mock_classify.assert_not_called()

    captured = capsys.readouterr()
    assert "Title: Looking for UGC creators for skincare brand" in captured.out
    assert "Link: https://reddit.com/r/UGCCreators/comments/abc123/test/" in captured.out
    assert "AI classification disabled" in captured.out


def test_run_reddit_classifies_when_ai_enabled(capsys, monkeypatch):
    monkeypatch.setenv("RADAR_AI_ENABLED", "true")

    from radar.models import ClassificationResult

    fake_result = ClassificationResult(
        title="Looking for UGC creators for skincare brand",
        subreddit="UGCCreators",
        url="https://reddit.com/r/UGCCreators/comments/abc123/test/",
        niche="Skincare",
        nicheTier=1,
        isOpportunity=True,
        opportunityTier="A",
        reason="Brand hiring UGC creators.",
    )

    with patch("radar.__main__.RedditClient") as mock_client:
        mock_client.return_value.fetch_posts.return_value = [_sample_post()]
        with patch("radar.__main__.classify_post", return_value=fake_result) as mock_classify:
            exit_code = run_reddit([])

    assert exit_code == 0
    mock_classify.assert_called_once()

    captured = capsys.readouterr()
    assert "TIER A OPPORTUNITY" in captured.out
