"""Tests for Upwork search query configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from radar.upwork.config import (
    DEFAULT_LIMIT_PER_QUERY,
    DEFAULT_SEARCH_QUERIES,
    resolve_limit_per_query,
    resolve_search_queries,
)


def test_resolve_search_queries_cli_overrides_env(monkeypatch):
    monkeypatch.setenv("RADAR_UPWORK_SEARCH_QUERIES", "Env Query")
    assert resolve_search_queries("CLI Query") == ["CLI Query"]


def test_resolve_search_queries_from_env(monkeypatch):
    monkeypatch.delenv("RADAR_UPWORK_QUERIES_FILE", raising=False)
    monkeypatch.setenv("RADAR_UPWORK_SEARCH_QUERIES", "UGC, Content Creator")
    assert resolve_search_queries(None) == ["UGC", "Content Creator"]


def test_resolve_search_queries_from_file(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("RADAR_UPWORK_SEARCH_QUERIES", raising=False)
    query_file = tmp_path / "queries.txt"
    query_file.write_text(
        "# comment\n\nTikTok Creator\n\n# another comment\nProduct Video\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RADAR_UPWORK_QUERIES_FILE", str(query_file))
    assert resolve_search_queries(None) == ["TikTok Creator", "Product Video"]


def test_resolve_search_queries_env_overrides_file(monkeypatch, tmp_path: Path):
    query_file = tmp_path / "queries.txt"
    query_file.write_text("From File\n", encoding="utf-8")
    monkeypatch.setenv("RADAR_UPWORK_QUERIES_FILE", str(query_file))
    monkeypatch.setenv("RADAR_UPWORK_SEARCH_QUERIES", "From Env")
    assert resolve_search_queries(None) == ["From Env"]


def test_resolve_search_queries_defaults(monkeypatch):
    monkeypatch.delenv("RADAR_UPWORK_SEARCH_QUERIES", raising=False)
    monkeypatch.delenv("RADAR_UPWORK_QUERIES_FILE", raising=False)
    assert resolve_search_queries(None) == DEFAULT_SEARCH_QUERIES


def test_resolve_limit_per_query_cli(monkeypatch):
    monkeypatch.delenv("RADAR_UPWORK_LIMIT_PER_QUERY", raising=False)
    assert resolve_limit_per_query(5) == 5


def test_resolve_limit_per_query_from_env(monkeypatch):
    monkeypatch.setenv("RADAR_UPWORK_LIMIT_PER_QUERY", "15")
    assert resolve_limit_per_query(None) == 15


def test_resolve_limit_per_query_default(monkeypatch):
    monkeypatch.delenv("RADAR_UPWORK_LIMIT_PER_QUERY", raising=False)
    assert resolve_limit_per_query(None) == DEFAULT_LIMIT_PER_QUERY


def test_resolve_limit_per_query_cli_minimum(monkeypatch):
    monkeypatch.delenv("RADAR_UPWORK_LIMIT_PER_QUERY", raising=False)
    assert resolve_limit_per_query(0) == 1
