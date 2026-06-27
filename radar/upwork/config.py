"""Upwork connector configuration."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_SEARCH_QUERIES = [
    "UGC",
    "User Generated Content",
    "TikTok Creator",
    "TikTok Content",
    "Instagram Creator",
    "Content Creator",
    "Product Video",
    "Product Review",
    "Video Testimonial",
    "Social Media Content",
]

DEFAULT_LIMIT_PER_QUERY = 20
PAGE_TIMEOUT_MS = 60_000
SEARCH_BASE_URL = "https://www.upwork.com/nx/search/jobs/"


def _parse_query_list(value: str) -> list[str]:
    return [query.strip() for query in value.split(",") if query.strip()]


def _load_queries_from_file(path: Path) -> list[str]:
    queries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        queries.append(stripped)
    return queries


def resolve_search_queries(cli_query: str | None = None) -> list[str]:
    """Resolve search queries with precedence: CLI > env list > env file > defaults."""
    if cli_query and cli_query.strip():
        return [cli_query.strip()]

    env_queries = os.environ.get("RADAR_UPWORK_SEARCH_QUERIES", "").strip()
    if env_queries:
        parsed = _parse_query_list(env_queries)
        if parsed:
            return parsed

    file_path = os.environ.get("RADAR_UPWORK_QUERIES_FILE", "").strip()
    if file_path:
        path = Path(file_path).expanduser()
        if path.is_file():
            loaded = _load_queries_from_file(path)
            if loaded:
                return loaded

    return list(DEFAULT_SEARCH_QUERIES)


def resolve_limit_per_query(cli_limit: int | None = None) -> int:
    """Resolve per-query job limit: CLI > RADAR_UPWORK_LIMIT_PER_QUERY > default."""
    if cli_limit is not None:
        return max(1, cli_limit)

    env_limit = os.environ.get("RADAR_UPWORK_LIMIT_PER_QUERY", "").strip()
    if env_limit:
        try:
            return max(1, int(env_limit))
        except ValueError:
            pass

    return DEFAULT_LIMIT_PER_QUERY
