from unittest.mock import MagicMock, patch

import pytest

from radar.reddit import (
    DEFAULT_FLAIR_FILTER,
    RedditClient,
    RedditConfigError,
    _map_apify_item,
    matches_flair,
)


SAMPLE_LABRAT_ITEMS = [
    {
        "type": "post",
        "id": "abc123",
        "title": "Looking for UGC creators",
        "selftext": "DM me for paid collab",
        "author": "brand",
        "subreddit": "UGCCreators",
        "flair": "Collab Request 🤝",
        "url": "https://www.reddit.com/r/UGCCreators/comments/abc123/test_post/",
    },
    {
        "type": "post",
        "id": "def456",
        "title": "General question",
        "selftext": "not a collab",
        "author": "user",
        "subreddit": "UGCCreators",
        "flair": "Question",
        "url": "https://www.reddit.com/r/UGCCreators/comments/def456/question/",
    },
    {
        "type": "comment",
        "id": "comment1",
        "body": "ignored",
    },
]


def test_default_flair_filter_is_exact_subreddit_tag():
    assert DEFAULT_FLAIR_FILTER == "Collab Request 🤝"


def test_matches_flair_case_insensitive_partial():
    assert matches_flair("Collab Request 🤝", DEFAULT_FLAIR_FILTER)
    assert matches_flair("collab request 🤝", DEFAULT_FLAIR_FILTER)


def test_matches_flair_rejects_non_matches():
    assert not matches_flair("Collab request", DEFAULT_FLAIR_FILTER)
    assert not matches_flair("Question", DEFAULT_FLAIR_FILTER)
    assert not matches_flair("", DEFAULT_FLAIR_FILTER)


def test_fetch_posts_requires_apify_token():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RedditConfigError, match="APIFY_API_TOKEN"):
            RedditClient()


def test_map_apify_item_skips_non_posts():
    assert _map_apify_item({"type": "comment", "body": "hi"}, "UGCCreators") is None


def test_map_apify_item_maps_flair():
    post = _map_apify_item(
        {
            "type": "post",
            "id": "abc123",
            "title": "Test",
            "selftext": "body",
            "author": "brand",
            "subreddit": "UGCCreators",
            "flair": "Collab Request 🤝",
            "url": "https://www.reddit.com/r/UGCCreators/comments/abc123/test/",
        },
        "UGCCreators",
    )
    assert post is not None
    assert post.flair == "Collab Request 🤝"


def test_map_apify_item_supports_legacy_trudax_format():
    post = _map_apify_item(
        {
            "dataType": "post",
            "parsedId": "abc123",
            "title": "Legacy post",
            "body": "body",
            "username": "brand",
            "parsedCommunityName": "UGCCreators",
            "flair": "Collab Request 🤝",
            "url": "https://www.reddit.com/r/UGCCreators/comments/abc123/test/",
        },
        "UGCCreators",
    )
    assert post is not None
    assert post.flair == "Collab Request 🤝"


def test_fetch_posts_parses_apify_dataset_and_filters_by_flair():
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
    assert posts[0].flair == "Collab Request 🤝"

    mock_client.actor.assert_called_once_with("labrat011/reddit-scraper")
    actor_call = mock_actor.call.call_args
    run_input = actor_call[1]["run_input"]
    assert run_input["mode"] == "search"
    assert run_input["searchQuery"] == 'flair:"Collab Request 🤝"'
    assert run_input["searchSubreddit"] == "UGCCreators"
    assert run_input["searchSort"] == "new"
    assert run_input["maxResults"] == 25
    assert run_input["includeComments"] is False
    assert run_input["proxyConfiguration"]["apifyProxyGroups"] == ["RESIDENTIAL"]

    mock_client.dataset.assert_called_once_with("dataset-123")


def test_fetch_posts_returns_empty_when_no_flair_matches():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = [
        {
            "type": "post",
            "id": "def456",
            "title": "General question",
            "selftext": "not a collab",
            "author": "user",
            "subreddit": "UGCCreators",
            "flair": "Question",
            "url": "https://www.reddit.com/r/UGCCreators/comments/def456/question/",
        }
    ]

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

    assert posts == []


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
