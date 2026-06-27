from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from apify_client import ApifyClient

from radar.models import RedditPost

DEFAULT_ACTOR_ID = "labrat011/reddit-scraper"
DEFAULT_FLAIR_FILTER = "Collab Request 🤝"
DEFAULT_SUBREDDITS = ["UGCCreators", "ugc"]
DEFAULT_SUBREDDITS_CSV = ",".join(DEFAULT_SUBREDDITS)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubredditScrapeConfig:
    """How to fetch posts for a given subreddit."""

    use_flair_search: bool = True
    apply_flair_filter: bool = True


# r/UGCCreators tags collab posts with a specific flair; r/ugc does not.
SUBREDDIT_SCRAPE_CONFIG: dict[str, SubredditScrapeConfig] = {
    "ugccreators": SubredditScrapeConfig(use_flair_search=True, apply_flair_filter=True),
    "ugc": SubredditScrapeConfig(use_flair_search=False, apply_flair_filter=False),
}


def get_subreddit_scrape_config(subreddit: str) -> SubredditScrapeConfig:
    known = SUBREDDIT_SCRAPE_CONFIG.get(subreddit.lower())
    if known is not None:
        return known
    return SubredditScrapeConfig(use_flair_search=False, apply_flair_filter=True)


def resolve_subreddits(subreddit: str | None = None) -> list[str]:
    """Resolve subreddits to scrape. CLI value may be comma-separated; default is both defaults."""
    if subreddit and subreddit.strip():
        return [name.strip().removeprefix("r/") for name in subreddit.split(",") if name.strip()]
    return list(DEFAULT_SUBREDDITS)


def resolve_subreddits_from_env() -> list[str]:
    env_value = os.environ.get("RADAR_REDDIT_SUBREDDITS", "").strip()
    if env_value:
        return resolve_subreddits(env_value)
    return list(DEFAULT_SUBREDDITS)


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


def _read_apify_run(run: object) -> tuple[str | None, str | None, str | None]:
    """Read status, run id, and dataset id from Apify actor.call() result.

    apify-client v1 returns dicts; v3 returns Pydantic Run models with snake_case fields.
    """
    if isinstance(run, dict):
        return run.get("status"), run.get("id"), run.get("defaultDatasetId")

    status = getattr(run, "status", None)
    run_id = getattr(run, "id", None)
    dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
    return status, run_id, dataset_id


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

    def _build_run_input(
        self,
        subreddit: str,
        limit: int,
        flair_filter: str,
        config: SubredditScrapeConfig,
    ) -> dict:
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

        if config.use_flair_search:
            return {
                "mode": "search",
                "searchQuery": f'flair:"{flair_filter}"',
                "searchSubreddit": subreddit,
                "searchSort": "new",
                "maxResults": limit,
                "includeComments": False,
                "proxyConfiguration": proxy,
            }

        return {
            "mode": "subreddit_posts",
            "subreddits": [subreddit],
            "sort": "new",
            "maxResults": limit,
            "includeComments": False,
            "proxyConfiguration": proxy,
        }

    def fetch_posts(
        self,
        subreddit: str | None = None,
        limit: int = 25,
        flair_filter: str = DEFAULT_FLAIR_FILTER,
    ) -> list[RedditPost]:
        subreddits = resolve_subreddits(subreddit)
        combined: list[RedditPost] = []
        seen_ids: set[str] = set()

        for name in subreddits:
            try:
                posts = self._fetch_posts_single(name, limit, flair_filter)
            except RuntimeError as exc:
                logger.warning("Skipping r/%s after scrape failure: %s", name, exc)
                if len(subreddits) == 1:
                    raise
                continue
            logger.info("Fetched %d posts from r/%s", len(posts), name)
            for post in posts:
                if post.post_id in seen_ids:
                    continue
                seen_ids.add(post.post_id)
                combined.append(post)

        return combined

    def _fetch_posts_single(
        self,
        subreddit: str,
        limit: int,
        flair_filter: str,
    ) -> list[RedditPost]:
        config = get_subreddit_scrape_config(subreddit)
        client = ApifyClient(self._api_token)
        run = client.actor(self._actor_id).call(
            run_input=self._build_run_input(subreddit, limit, flair_filter, config)
        )

        status, run_id, dataset_id = _read_apify_run(run)
        if status and status != "SUCCEEDED":
            raise RuntimeError(
                f"Apify actor run failed with status {status} for r/{subreddit}. "
                f"Check logs at https://console.apify.com/actors/runs/{run_id or 'unknown'}"
            )
        if not dataset_id:
            raise RuntimeError("Apify actor run did not return a dataset ID")

        raw_posts: list[RedditPost] = []
        for item in client.dataset(dataset_id).iterate_items():
            post = _map_apify_item(item, subreddit)
            if post is not None:
                raw_posts.append(post)

        if not raw_posts:
            logger.info("No posts returned for r/%s", subreddit)
            return []

        if config.apply_flair_filter and flair_filter:
            return [post for post in raw_posts if matches_flair(post.flair, flair_filter)]
        return raw_posts
