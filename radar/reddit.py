from __future__ import annotations

import os

from apify_client import ApifyClient

from radar.models import RedditPost

DEFAULT_ACTOR_ID = "labrat011/reddit-scraper"


class RedditConfigError(ValueError):
    """Raised when required Apify settings are missing."""


def build_reddit_url(permalink: str) -> str:
    if not permalink:
        return ""
    if permalink.startswith("http"):
        return permalink.replace("https://www.reddit.com", "https://reddit.com")
    return f"https://reddit.com{permalink}"


def _map_apify_item(item: dict, subreddit: str) -> RedditPost | None:
    # labrat011/reddit-scraper output
    if item.get("type") == "post":
        post_id = item.get("id", "")
        url = build_reddit_url(item.get("url", ""))
        if not post_id or not url:
            return None
        return RedditPost(
            post_id=post_id,
            title=item.get("title", ""),
            body=item.get("selftext", "") or "",
            author=item.get("author", ""),
            subreddit=item.get("subreddit") or subreddit,
            url=url,
        )

    # trudax/reddit-scraper-lite output (legacy)
    if item.get("dataType") == "post":
        post_id = item.get("parsedId") or item.get("id", "").removeprefix("t3_")
        url = build_reddit_url(item.get("url", ""))
        if not post_id or not url:
            return None
        return RedditPost(
            post_id=post_id,
            title=item.get("title", ""),
            body=item.get("body", "") or "",
            author=item.get("username", ""),
            subreddit=item.get("parsedCommunityName") or subreddit,
            url=url,
        )

    return None


class RedditClient:
    def __init__(self) -> None:
        self._api_token = os.environ.get("APIFY_API_TOKEN", "").strip()
        self._actor_id = os.environ.get("APIFY_ACTOR_ID", DEFAULT_ACTOR_ID).strip() or DEFAULT_ACTOR_ID
        if not self._api_token:
            raise RedditConfigError(
                "Apify API token required. Set APIFY_API_TOKEN in .env. "
                "Get one at https://console.apify.com/account/integrations"
            )

    def _build_run_input(self, subreddit: str, limit: int) -> dict:
        proxy = {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        }

        if "openclawai" in self._actor_id:
            return {
                "action": "scrape_subreddit",
                "subreddit": subreddit,
                "sort": "new",
                "limit": limit,
                "includeComments": False,
                "proxyConfiguration": proxy,
            }

        if "trudax" in self._actor_id or self._actor_id.startswith("apify/"):
            return {
                "startUrls": [{"url": f"https://www.reddit.com/r/{subreddit}/new/"}],
                "sort": "new",
                "maxItems": limit,
                "maxPostCount": limit,
                "skipComments": True,
                "includeMediaLinks": True,
                "proxy": proxy,
            }

        return {
            "mode": "subreddit_posts",
            "subreddits": [subreddit],
            "sort": "new",
            "maxResults": limit,
            "includeComments": False,
            "proxyConfiguration": proxy,
        }

    def fetch_posts(self, subreddit: str = "UGCCreators", limit: int = 25) -> list[RedditPost]:
        client = ApifyClient(self._api_token)
        run = client.actor(self._actor_id).call(run_input=self._build_run_input(subreddit, limit))

        status = run.get("status")
        if status and status != "SUCCEEDED":
            run_id = run.get("id", "unknown")
            raise RuntimeError(
                f"Apify actor run failed with status {status}. "
                f"Check logs at https://console.apify.com/actors/runs/{run_id}"
            )

        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            raise RuntimeError("Apify actor run did not return a dataset ID")

        posts: list[RedditPost] = []
        for item in client.dataset(dataset_id).iterate_items():
            post = _map_apify_item(item, subreddit)
            if post is not None:
                posts.append(post)

        if not posts:
            run_id = run.get("id", "unknown")
            raise RuntimeError(
                "Apify actor returned no posts. Reddit may have blocked the scrape. "
                f"Check run logs at https://console.apify.com/actors/runs/{run_id}"
            )

        return posts
