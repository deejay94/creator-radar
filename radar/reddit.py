from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from apify_client import ApifyClient

from radar.models import RedditPost

DEFAULT_ACTOR_ID = "labrat011/reddit-scraper"
DEFAULT_FLAIR_FILTER = "Collab Request 🤝"


class RedditConfigError(ValueError):
    """Raised when required Apify settings are missing."""


def build_reddit_url(permalink: str) -> str:
    if not permalink:
        return ""
    if permalink.startswith("http"):
        return permalink.replace("https://www.reddit.com", "https://reddit.com")
    return f"https://reddit.com{permalink}"


def _parse_created(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def matches_flair(flair: str, filter_text: str) -> bool:
    return filter_text.lower() in flair.lower()


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
            flair=item.get("flair", "") or "",
            created_at=_parse_created(item.get("created", "")),
        )

    # trudax/reddit-scraper-lite output (legacy)
    if item.get("dataType") == "post":
        post_id = item.get("parsedId") or item.get("id", "").removeprefix("t3_")
        url = build_reddit_url(item.get("url", ""))
        if not post_id or not url:
            return None
        created_raw = item.get("createdAt") or item.get("created", "")
        return RedditPost(
            post_id=post_id,
            title=item.get("title", ""),
            body=item.get("body", "") or "",
            author=item.get("username", ""),
            subreddit=item.get("parsedCommunityName") or subreddit,
            url=url,
            flair=item.get("flair", "") or "",
            created_at=_parse_created(created_raw),
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

    def _build_run_input(self, subreddit: str, limit: int, flair_filter: str) -> dict:
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
            "mode": "search",
            "searchQuery": f'flair:"{flair_filter}"',
            "searchSubreddit": subreddit,
            "searchSort": "new",
            "maxResults": limit,
            "includeComments": False,
            "proxyConfiguration": proxy,
        }

    def fetch_posts(
        self,
        subreddit: str = "UGCCreators",
        limit: int = 25,
        flair_filter: str = DEFAULT_FLAIR_FILTER,
    ) -> list[RedditPost]:
        client = ApifyClient(self._api_token)
        run = client.actor(self._actor_id).call(
            run_input=self._build_run_input(subreddit, limit, flair_filter)
        )

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

        raw_posts: list[RedditPost] = []
        for item in client.dataset(dataset_id).iterate_items():
            post = _map_apify_item(item, subreddit)
            if post is not None:
                raw_posts.append(post)

        if not raw_posts:
            run_id = run.get("id", "unknown")
            raise RuntimeError(
                "Apify actor returned no posts. Reddit may have blocked the scrape. "
                f"Check run logs at https://console.apify.com/actors/runs/{run_id}"
            )

        return [post for post in raw_posts if matches_flair(post.flair, flair_filter)]
