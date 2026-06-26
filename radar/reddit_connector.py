"""Reddit OpportunityConnector adapter."""

from __future__ import annotations

from radar.connectors.base import OpportunityConnector
from radar.connectors.types import (
    ConnectorHealth,
    Opportunity,
    RawListing,
    RawListingRef,
    SearchParams,
)
from radar.models import RedditPost
from radar.reddit import DEFAULT_FLAIR_FILTER, RedditClient, RedditConfigError


class RedditConnector(OpportunityConnector):
    def __init__(self) -> None:
        self._client: RedditClient | None = None
        self._cache: dict[str, RedditPost] = {}

    @property
    def platform(self) -> str:
        return "reddit"

    def close(self) -> None:
        self._cache.clear()

    def _get_client(self) -> RedditClient:
        if self._client is None:
            self._client = RedditClient()
        return self._client

    def health_check(self) -> ConnectorHealth:
        try:
            self._get_client()
        except RedditConfigError as exc:
            return ConnectorHealth(
                healthy=False,
                status="misconfigured",
                display_name=None,
                message=str(exc),
            )
        return ConnectorHealth(
            healthy=True,
            status="configured",
            display_name=None,
            message="Apify Reddit client configured",
        )

    def search(self, params: SearchParams) -> list[RawListingRef]:
        subreddit = str(params.extras.get("subreddit", "UGCCreators"))
        flair_filter = str(params.extras.get("flair", DEFAULT_FLAIR_FILTER))
        limit = params.limit_per_query

        posts = self._get_client().fetch_posts(
            subreddit=subreddit,
            limit=limit,
            flair_filter=flair_filter,
        )
        self._cache = {post.post_id: post for post in posts}
        return [
            RawListingRef(
                external_id=post.post_id,
                url=post.url,
                title=post.title,
                source_query=flair_filter,
            )
            for post in posts
        ]

    def extract(self, ref: RawListingRef) -> RawListing:
        post = self._cache.get(ref.external_id)
        if post is None:
            raise ValueError(f"Reddit post {ref.external_id} not found in search cache")

        return RawListing(
            platform="reddit",
            external_id=post.post_id,
            url=post.url,
            title=post.title,
            description=post.body,
            payload={
                "author": post.author,
                "subreddit": post.subreddit,
                "flair": post.flair,
                "created_at": post.created_at.isoformat() if post.created_at else "",
                "source_query": ref.source_query,
            },
        )

    def normalize(self, raw: RawListing) -> Opportunity:
        payload = raw.payload
        return Opportunity(
            platform="reddit",
            external_id=raw.external_id,
            title=raw.title,
            description=raw.description,
            url=raw.url,
            posted_at=_parse_created(payload.get("created_at")),
            metadata={
                "author": payload.get("author", ""),
                "subreddit": payload.get("subreddit", ""),
                "flair": payload.get("flair", ""),
                "source_query": payload.get("source_query", ""),
            },
        )


def _parse_created(value: object):
    from datetime import datetime

    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
