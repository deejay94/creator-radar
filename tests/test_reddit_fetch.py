from unittest.mock import MagicMock, patch

import pytest

from radar.reddit import RedditClient, RedditConfigError, _map_apify_item


SAMPLE_LABRAT_ITEMS = [
    {
        "type": "post",
        "id": "abc123",
        "title": "Looking for UGC creators",
        "selftext": "DM me for paid collab",
        "author": "brand",
        "subreddit": "UGCCreators",
        "url": "https://www.reddit.com/r/UGCCreators/comments/abc123/test_post/",
    },
    {
        "type": "comment",
        "id": "comment1",
        "body": "ignored",
    },
]


def test_fetch_posts_requires_apify_token():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RedditConfigError, match="APIFY_API_TOKEN"):
            RedditClient()


def test_map_apify_item_skips_non_posts():
    assert _map_apify_item({"type": "comment", "body": "hi"}, "UGCCreators") is None


def test_map_apify_item_supports_legacy_trudax_format():
    post = _map_apify_item(
        {
            "dataType": "post",
            "parsedId": "abc123",
            "title": "Legacy post",
            "body": "body",
            "username": "brand",
            "parsedCommunityName": "UGCCreators",
            "url": "https://www.reddit.com/r/UGCCreators/comments/abc123/test/",
        },
        "UGCCreators",
    )
    assert post is not None
    assert post.title == "Legacy post"


def test_fetch_posts_parses_apify_dataset():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = SAMPLE_LABRAT_ITEMS

    mock_actor = MagicMock()
    mock_actor.call.return_value = {"defaultDatasetId": "dataset-123", "status": "SUCCEEDED", "id": "run-1"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    env = {"APIFY_API_TOKEN": "apify_api_test_token"}
    with patch.dict("os.environ", env, clear=True):
        with patch("radar.reddit.ApifyClient", return_value=mock_client):
            client = RedditClient()
            posts = client.fetch_posts(subreddit="UGCCreators", limit=25)

    assert len(posts) == 1
    assert posts[0].title == "Looking for UGC creators"
    assert posts[0].author == "brand"
    assert posts[0].url == "https://reddit.com/r/UGCCreators/comments/abc123/test_post/"

    mock_client.actor.assert_called_once_with("labrat011/reddit-scraper")
    actor_call = mock_actor.call.call_args
    run_input = actor_call[1]["run_input"]
    assert run_input["mode"] == "subreddit_posts"
    assert run_input["sort"] == "new"
    assert run_input["maxResults"] == 25
    assert run_input["subreddits"] == ["UGCCreators"]
    assert run_input["includeComments"] is False
    assert run_input["proxyConfiguration"]["apifyProxyGroups"] == ["RESIDENTIAL"]

    mock_client.dataset.assert_called_once_with("dataset-123")


def test_fetch_posts_raises_when_actor_returns_no_posts():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = []

    mock_actor = MagicMock()
    mock_actor.call.return_value = {"defaultDatasetId": "dataset-123", "status": "SUCCEEDED", "id": "run-1"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    env = {"APIFY_API_TOKEN": "apify_api_test_token"}
    with patch.dict("os.environ", env, clear=True):
        with patch("radar.reddit.ApifyClient", return_value=mock_client):
            client = RedditClient()
            with pytest.raises(RuntimeError, match="returned no posts"):
                client.fetch_posts(subreddit="UGCCreators", limit=25)
