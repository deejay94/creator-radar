from unittest.mock import MagicMock, patch

import pytest

from radar.reddit import (
    DEFAULT_FLAIR_FILTER,
    DEFAULT_SUBREDDITS,
    RedditClient,
    RedditConfigError,
    _map_apify_item,
    _read_apify_run,
    get_subreddit_scrape_config,
    matches_flair,
    resolve_subreddits,
    resolve_subreddits_from_env,
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


def test_default_subreddits_include_ugc():
    assert DEFAULT_SUBREDDITS == ["UGCCreators", "ugc"]


def test_resolve_subreddits_defaults():
    assert resolve_subreddits(None) == ["UGCCreators", "ugc"]


def test_resolve_subreddits_single_override():
    assert resolve_subreddits("ugc") == ["ugc"]


def test_resolve_subreddits_comma_separated():
    assert resolve_subreddits("UGCCreators, ugc") == ["UGCCreators", "ugc"]


def test_resolve_subreddits_strips_r_prefix():
    assert resolve_subreddits("r/ugc") == ["ugc"]


def test_resolve_subreddits_from_env():
    with patch.dict("os.environ", {"RADAR_REDDIT_SUBREDDITS": "UGCCreators,ugc"}, clear=True):
        assert resolve_subreddits_from_env() == ["UGCCreators", "ugc"]
    with patch.dict("os.environ", {}, clear=True):
        assert resolve_subreddits_from_env() == ["UGCCreators", "ugc"]


def test_ugc_subreddit_uses_new_posts_mode_not_flair_search():
    config = get_subreddit_scrape_config("ugc")
    assert config.use_flair_search is False
    assert config.apply_flair_filter is False


def test_ugccreators_subreddit_uses_flair_search():
    config = get_subreddit_scrape_config("UGCCreators")
    assert config.use_flair_search is True
    assert config.apply_flair_filter is True


def test_fetch_posts_ugc_uses_subreddit_posts_mode():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = [
        {
            "type": "post",
            "id": "ugc001",
            "title": "Brand looking for creators",
            "selftext": "Paid UGC opportunity",
            "author": "brand",
            "subreddit": "ugc",
            "flair": "",
            "url": "https://www.reddit.com/r/ugc/comments/ugc001/test/",
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
            posts = client.fetch_posts(subreddit="ugc", limit=25)

    assert len(posts) == 1
    assert posts[0].title == "Brand looking for creators"
    run_input = mock_actor.call.call_args.kwargs["run_input"]
    assert run_input["mode"] == "subreddit_posts"
    assert run_input["subreddits"] == ["ugc"]
    assert run_input["sort"] == "new"


def test_default_flair_filter_is_exact_subreddit_tag():
    assert DEFAULT_FLAIR_FILTER == "Collab Request 🤝"


def test_matches_flair_case_insensitive_partial():
    assert matches_flair("Collab Request 🤝", DEFAULT_FLAIR_FILTER)
    assert matches_flair("collab request 🤝", DEFAULT_FLAIR_FILTER)


def test_matches_flair_rejects_non_matches():
    assert not matches_flair("Collab request", DEFAULT_FLAIR_FILTER)
    assert not matches_flair("Question", DEFAULT_FLAIR_FILTER)
    assert not matches_flair("", DEFAULT_FLAIR_FILTER)


def test_read_apify_run_from_dict():
    status, run_id, dataset_id = _read_apify_run(
        {"status": "SUCCEEDED", "id": "run-1", "defaultDatasetId": "dataset-123"}
    )
    assert status == "SUCCEEDED"
    assert run_id == "run-1"
    assert dataset_id == "dataset-123"


def test_read_apify_run_from_typed_model():
    class Run:
        status = "SUCCEEDED"
        id = "run-2"
        default_dataset_id = "dataset-456"

    status, run_id, dataset_id = _read_apify_run(Run())
    assert status == "SUCCEEDED"
    assert run_id == "run-2"
    assert dataset_id == "dataset-456"


def test_fetch_posts_accepts_typed_apify_run():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = [
        {
            "type": "post",
            "id": "ugc001",
            "title": "Brand looking for creators",
            "selftext": "Paid UGC opportunity",
            "author": "brand",
            "subreddit": "ugc",
            "flair": "",
            "url": "https://www.reddit.com/r/ugc/comments/ugc001/test/",
        }
    ]

    class Run:
        status = "SUCCEEDED"
        id = "run-typed"
        default_dataset_id = "dataset-123"

    mock_actor = MagicMock()
    mock_actor.call.return_value = Run()

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    env = {"APIFY_API_TOKEN": "apify_api_test_token"}
    with patch.dict("os.environ", env, clear=True):
        with patch("radar.reddit.ApifyClient", return_value=mock_client):
            client = RedditClient()
            posts = client.fetch_posts(subreddit="ugc", limit=25)

    assert len(posts) == 1
    mock_client.dataset.assert_called_once_with("dataset-123")


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


def test_fetch_posts_default_scrapes_both_subreddits():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = [SAMPLE_LABRAT_ITEMS[0]]

    mock_actor = MagicMock()
    mock_actor.call.return_value = {"defaultDatasetId": "dataset-123", "status": "SUCCEEDED", "id": "run-1"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    env = {"APIFY_API_TOKEN": "apify_api_test_token"}
    with patch.dict("os.environ", env, clear=True):
        with patch("radar.reddit.ApifyClient", return_value=mock_client):
            client = RedditClient()
            posts = client.fetch_posts(limit=10)

    assert len(posts) == 1
    assert mock_actor.call.call_count == 2
    ugccreators_call = mock_actor.call.call_args_list[0].kwargs["run_input"]
    ugc_call = mock_actor.call.call_args_list[1].kwargs["run_input"]
    assert ugccreators_call["mode"] == "search"
    assert ugccreators_call["searchSubreddit"] == "UGCCreators"
    assert ugc_call["mode"] == "subreddit_posts"
    assert ugc_call["subreddits"] == ["ugc"]


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


def test_fetch_posts_returns_empty_when_actor_returns_no_posts():
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
            posts = client.fetch_posts(subreddit="UGCCreators", limit=25)

    assert posts == []


def test_fetch_posts_continues_when_one_subreddit_returns_no_posts():
    empty_dataset = MagicMock()
    empty_dataset.iterate_items.return_value = []

    ugc_dataset = MagicMock()
    ugc_dataset.iterate_items.return_value = [
        {
            "type": "post",
            "id": "ugc123",
            "title": "Looking for creators on ugc",
            "selftext": "paid work",
            "author": "brand",
            "subreddit": "ugc",
            "flair": "",
            "url": "https://www.reddit.com/r/ugc/comments/ugc123/test/",
        }
    ]

    mock_actor = MagicMock()
    mock_actor.call.side_effect = [
        {"defaultDatasetId": "dataset-empty", "status": "SUCCEEDED", "id": "run-1"},
        {"defaultDatasetId": "dataset-ugc", "status": "SUCCEEDED", "id": "run-2"},
    ]

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.side_effect = [empty_dataset, ugc_dataset]

    env = {"APIFY_API_TOKEN": "apify_api_test_token"}
    with patch.dict("os.environ", env, clear=True):
        with patch("radar.reddit.ApifyClient", return_value=mock_client):
            client = RedditClient()
            posts = client.fetch_posts(limit=10)

    assert len(posts) == 1
    assert posts[0].subreddit == "ugc"
    assert mock_actor.call.call_count == 2
